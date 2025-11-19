"""Safety verification service to ensure meaning preservation."""
from __future__ import annotations

from typing import Any, Dict, List

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..utils import date_amount_parsing
from ..prompt_templates import verifier as verifier_prompt
import json


class SafetyCheckService:
    """Combine deterministic rules with LLM verification calls."""

    def __init__(self, client: BaseLLMClient):
        self._client = client

    def evaluate(
        self,
        original: schemas.SegmentedDocument,
        simplification: schemas.SimplificationResult,
        legal_guide: schemas.LegalGuide,
    ) -> schemas.SafetyCheckResult:
        """Run rule-based checks and optionally call the verifier model."""
        rule_flags = self._rule_based_flags(original, simplification)

        llm_output = self._call_verifier(original, simplification, legal_guide)
        issues = [schemas.SafetyIssue(code=flag, message=flag) for flag in rule_flags]

        if llm_output:
            issues.extend(
                schemas.SafetyIssue(code="LLM_WARNING", message=warning)
                for warning in llm_output["warnings"]
            )

        is_safe = not issues
        llm_verdict = None
        if llm_output:
            is_safe = is_safe and bool(llm_output["is_safe"])
            llm_verdict = llm_output.get("verdict") or llm_output.get("raw_response")

        return schemas.SafetyCheckResult(
            isSafe=is_safe,
            issues=issues,
            ruleBasedFlags=rule_flags,
            llmVerdict=llm_verdict,
        )

    # ------------------------------------------------------------------
    # Rule-based comparison
    # ------------------------------------------------------------------
    def _rule_based_flags(
        self,
        original: schemas.SegmentedDocument,
        simplification: schemas.SimplificationResult,
    ) -> List[str]:
        flags: List[str] = []
        orig_text = (original.normalizedText or "").upper()
        simp_text = (simplification.simplifiedText or "").upper()

        orig_amounts = set(date_amount_parsing.extract_amounts(orig_text))
        simp_amounts = set(date_amount_parsing.extract_amounts(simp_text))
        for amount in orig_amounts:
            if amount not in simp_amounts:
                flags.append(f"MISSING_AMOUNT:{amount}")

        orig_dates = set(date_amount_parsing.extract_dates(orig_text))
        simp_dates = set(date_amount_parsing.extract_dates(simp_text))
        for date in orig_dates:
            if date not in simp_dates:
                flags.append(f"MISSING_DATE:{date}")

        deadlines = set(date_amount_parsing.extract_deadlines(orig_text))
        simplified_deadlines = set(date_amount_parsing.extract_deadlines(simp_text))
        for deadline in deadlines:
            if deadline not in simplified_deadlines:
                flags.append(f"MISSING_DEADLINE:{deadline}")

        return flags

    # ------------------------------------------------------------------
    # LLM verifier wrapper
    # ------------------------------------------------------------------
    def _call_verifier(
        self,
        original: schemas.SegmentedDocument,
        simplification: schemas.SimplificationResult,
        legal_guide: schemas.LegalGuide,
    ) -> Dict[str, Any] | None:
        try:
            # Prefer the high-level verify_safety method if available (test fakes)
            if hasattr(self._client, "verify_safety") and callable(getattr(self._client, "verify_safety")):
                result = self._client.verify_safety(original.normalizedText[:5000], simplification.simplifiedText[:5000], legal_guide)
                # Expect dict-like result
                if isinstance(result, dict):
                    # normalize fields
                    warnings = result.get("warnings") or result.get("alerts") or []
                    if not isinstance(warnings, list):
                        warnings = [str(warnings)]
                    return {
                        "is_safe": bool(result.get("is_safe", result.get("safe", False))),
                        "warnings": warnings,
                        "verdict": result.get("verdict") or result.get("summary") or None,
                        "raw_response": result.get("raw_response") or str(result),
                    }
                # If client returned a SafetyCheckResult, extract fields
                if hasattr(result, "isSafe"):
                    return {
                        "is_safe": bool(getattr(result, "isSafe")),
                        "warnings": [i.message for i in getattr(result, "issues", [])],
                        "verdict": getattr(result, "llmVerdict", None),
                        "raw_response": str(result),
                    }

            # Otherwise use chat-based verifier and parse strictly via client
            system = verifier_prompt.system_prompt()
            user = verifier_prompt.user_prompt(
                original.normalizedText[:5000],
                simplification.simplifiedText[:5000],
                legal_guide.model_dump() if hasattr(legal_guide, "model_dump") else str(legal_guide),
            )
            raw = self._client.chat(system, user, temperature=0.0)
            try:
                data = self._client._parse_json(raw)
            except LLMClientError:
                return {"is_safe": False, "warnings": ["No se ha podido verificar correctamente el significado."], "raw_response": raw}

            # normalize fields
            warnings = data.get("warnings") or data.get("alerts") or []
            if not isinstance(warnings, list):
                warnings = [str(warnings)]

            result = {
                "is_safe": bool(data.get("is_safe", data.get("safe", False))),
                "warnings": warnings,
                "verdict": data.get("verdict") or data.get("summary") or None,
                "raw_response": raw,
            }
            return result
        except LLMClientError:
            return None
