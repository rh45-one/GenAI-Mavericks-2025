"""Safety verification service to ensure meaning preservation."""
from __future__ import annotations

from typing import List, Dict, Any

from .. import schemas
from ..clients import llm_client
from ..utils import date_amount_parsing


class SafetyCheckService:
    """Combine deterministic rules with LLM verification calls."""

    def __init__(self, client: llm_client.LLMClient):
        self._client = client

    # -----------------------------------------------------------
    # 1) REGLAS DETERMINISTAS (DETECTAN ERRORES DUROS)
    # -----------------------------------------------------------
    def ruleBasedCheck(
        self,
        original: schemas.SegmentedDocument,
        simplified: schemas.SimplificationResult,
    ) -> schemas.SafetyCheckResult:
        """
        Detecta:
        - Cantidades económicas que desaparecen o cambian.
        - Fechas/plazos que se pierden.
        - Menciones claras a demandante/demandado que no aparecen.
        """
        warnings: List[str] = []

        orig_text = (original.normalizedText or "").upper()
        simp_text = (simplified.simplifiedText or "").upper()

        # ---- 1) IMPORTES ----
        orig_amounts = set(date_amount_parsing.extract_amounts(orig_text))
        simp_amounts = set(date_amount_parsing.extract_amounts(simp_text))

        for amount in orig_amounts:
            if amount not in simp_amounts:
                warnings.append(f"Posible pérdida o alteración del importe '{amount}'.")

        # ---- 2) FECHAS / PLAZOS ----
        orig_dates = set(date_amount_parsing.extract_dates(orig_text))
        simp_dates = set(date_amount_parsing.extract_dates(simp_text))

        for d in orig_dates:
            if d not in simp_dates:
                warnings.append(f"Posible omisión del plazo o fecha '{d}'.")

        # ---- 3) PARTES ----
        parties_keywords = ["DEMANDANTE", "DEMANDADO", "ACTOR", "DEMANDADA", "RECURRENTE", "RECURRENTE"]
        for kw in parties_keywords:
            if kw in orig_text and kw not in simp_text:
                warnings.append(f"El simplificado no menciona la parte '{kw.lower()}' detectada en el texto original.")

        return schemas.SafetyCheckResult(
            warnings=warnings,
            ruleBasedFindings=warnings.copy(),
            llmFindings=[],
        )

    # -----------------------------------------------------------
    # 2) VERIFICACIÓN POR LLM
    # -----------------------------------------------------------
    def llmVerification(
        self,
        original: schemas.SegmentedDocument,
        simplified: schemas.SimplificationResult,
        legal_guide: schemas.LegalGuide,
    ) -> schemas.SafetyCheckResult:
        """
        Usa LLMClient.callVerifier para comprobar pérdida de información crítica.
        Luego fusiona los hallazgos con ruleBasedCheck.
        """
        orig_text = original.normalizedText or ""
        simp_text = simplified.simplifiedText or ""
        guide_dict = legal_guide.model_dump()

        # ---- 1) Llamada al LLM: ¿mantiene el significado clave? ----
        try:
            llm_res: Dict[str, Any] = self._client.callVerifier(
                original_text=orig_text,
                simplified_text=simp_text,
                legal_guide=guide_dict,
            )

            llm_ok = llm_res.get("is_safe", False)
            llm_warnings = llm_res.get("warnings", [])
        except Exception as e:
            # Si el LLM falla, lo tratamos como advertencia
            llm_ok = False
            llm_warnings = [f"Error en verificación LLM: {e}"]

        # ---- 2) Reglas deterministas ----
        rules = self.ruleBasedCheck(original, simplified)

        # ---- 3) Fusión ----
        merged_warnings = list(rules.warnings)
        merged_warnings.extend(llm_warnings)

        return schemas.SafetyCheckResult(
            warnings=merged_warnings,
            ruleBasedFindings=rules.ruleBasedFindings,
            llmFindings=llm_warnings,
        )
