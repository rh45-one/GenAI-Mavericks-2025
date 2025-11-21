"""Safety verification service to ensure meaning preservation."""
from __future__ import annotations

from typing import Any, Dict, List

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..utils import date_amount_parsing
from ..prompt_templates import verifier as verifier_prompt
import re


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

        # Check: guide should not claim victory when whoWins is desconocido
        decision = getattr(simplification, "decisionFallo", None)
        who = ""
        try:
            who = (decision.whoWins if decision else "") or ""
        except Exception:
            who = ""
        if who.lower() == "desconocido":
            text_all = ((legal_guide.meaningForYou or "") + " " + (legal_guide.whatToDoNow or "")).lower()
            if (
                "has ganado" in text_all
                or "has perdido" in text_all
                or "ganado" in text_all
                or "te devolver" in text_all
                or "el banco debe" in text_all
            ):
                rule_flags.append("GUIDE_ASSERTS_VICTORY_WITHOUT_FALLO")

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

    def _rule_based_flags(
        self,
        original: schemas.SegmentedDocument,
        simplification: schemas.SimplificationResult,
    ) -> List[str]:
        flags: List[str] = []

        fallo_literal = None
        if original.metadata and getattr(original.metadata, "extra", None):
            fallo_literal = original.metadata.extra.get("falloLiteral")
        if not fallo_literal:
            flags.append("MISSING_FALLO_LITERAL")

        orig_text_full = (original.normalizedText or "").upper()
        simp_text = (simplification.simplifiedText or "").upper()
        orig_text_fallo = (fallo_literal or "").upper()

        def _detect_winner_from_text(t: str) -> str:
            if re.search(r"\b(SE\s+DESESTIMA|DESESTIMA|NO\s+HA\s+LUGAR)\b", t, re.IGNORECASE):
                return "parte demandada"
            if re.search(r"\b(SE\s+ESTIMA|ESTIMAR|SE\s+ACUERDA\s+ESTIMAR|FALLA\s+A\s+FAVOR)\b", t, re.IGNORECASE):
                return "parte demandante"
            return "desconocido"

        def _detect_costs_from_text(t: str) -> str:
            if re.search(r"\b(IMPONER|CONDENA|CONDENANDO)\s+EN\s+COSTAS\b", t, re.IGNORECASE) or re.search(r"\bCOSTAS\b.*\bIMPONEN\b", t, re.IGNORECASE):
                return "completo"
            if re.search(r"\b(SIN\s+COSTAS|NO\s+CONDENAR\s+EN\s+COSTAS)\b", t, re.IGNORECASE):
                return "ninguno"
            if re.search(r"\bCOSTAS\b.*\bPARCIAL\b", t, re.IGNORECASE) or re.search(r"\bPARCIALMENTE\b.*\bCOSTAS\b", t, re.IGNORECASE):
                return "parcial"
            return "desconocido"

        orig_winner = _detect_winner_from_text(orig_text_fallo)
        orig_costs = _detect_costs_from_text(orig_text_fallo)

        decision = getattr(simplification, "decisionFallo", None)

        if decision:
            simp_winner = (getattr(decision, "whoWins", "") or "").strip().lower() or "desconocido"
            if simp_winner and simp_winner != "desconocido" and orig_winner and orig_winner != "desconocido":
                norm_map = {
                    "parte demandante": "parte demandante",
                    "demandante": "parte demandante",
                    "actora": "parte demandante",
                    "parte demandada": "parte demandada",
                    "demandada": "parte demandada",
                    "demandado": "parte demandada",
                    "parcial": "parcial",
                }
                simp_norm = norm_map.get(simp_winner, simp_winner)
                orig_norm = norm_map.get(orig_winner, orig_winner)
                if simp_norm != orig_norm:
                    flags.append("FALLO_POLARITY_MISMATCH")

            simp_costs = (getattr(decision, "costs", "") or "").strip().lower() or "desconocido"
            if simp_costs and simp_costs != "desconocido" and orig_costs and orig_costs != "desconocido":
                if simp_costs != orig_costs:
                    flags.append("FALLO_COSTS_MISMATCH")

        try:
            orig_amounts = set(date_amount_parsing.extract_amounts(orig_text_full))
            simp_amounts = set(date_amount_parsing.extract_amounts(simp_text))
            for amount in orig_amounts:
                if amount not in simp_amounts:
                    flags.append(f"MISSING_AMOUNT:{amount}")

            orig_dates = set(date_amount_parsing.extract_dates(orig_text_full))
            simp_dates = set(date_amount_parsing.extract_dates(simp_text))
            for date in orig_dates:
                if date not in simp_dates:
                    flags.append(f"MISSING_DATE:{date}")

            orig_deadlines = set(date_amount_parsing.extract_deadlines(orig_text_full))
            simp_deadlines = set(date_amount_parsing.extract_deadlines(simp_text))
            for d in orig_deadlines:
                if d not in simp_deadlines:
                    flags.append(f"WARNING_MISSING_DEADLINE:{d}")
        except Exception:
            pass

        return flags

    def _call_verifier(
        self,
        original: schemas.SegmentedDocument,
        simplification: schemas.SimplificationResult,
        legal_guide: schemas.LegalGuide,
    ) -> Dict[str, Any] | None:
        try:
            if hasattr(self._client, "verify_safety") and callable(getattr(self._client, "verify_safety")):
                result = self._client.verify_safety(original.normalizedText[:5000], simplification.simplifiedText[:5000], legal_guide)
                if isinstance(result, dict):
                    warnings = result.get("warnings") or result.get("alerts") or []
                    if not isinstance(warnings, list):
                        warnings = [str(warnings)]
                    return {
                        "is_safe": bool(result.get("is_safe", result.get("safe", False))),
                        "warnings": warnings,
                        "verdict": result.get("verdict") or result.get("summary") or None,
                        "raw_response": result.get("raw_response") or str(result),
                    }
                if hasattr(result, "isSafe"):
                    return {
                        "is_safe": bool(getattr(result, "isSafe")),
                        "warnings": [i.message for i in getattr(result, "issues", [])],
                        "verdict": getattr(result, "llmVerdict", None),
                        "raw_response": str(result),
                    }

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
