"""Legal guide generation service."""
from __future__ import annotations

from typing import Dict, Any, List, Optional

from .. import schemas
from ..clients import llm_client


class LegalGuideService:
    """Create a four-block LegalGuide DTO from simplified content."""

    def __init__(self, client: llm_client.LLMClient):
        self._client = client

    def buildGuide(self, simplification_result: schemas.SimplificationResult) -> schemas.LegalGuide:
        """
        Call LLMClient.callGuideGenerator with structured context.

        - Usa simplifiedText como base.
        - Añade contexto de docType / docSubtype.
        - Pasa las importantSections como pista de secciones clave.
        - Mapea el JSON del LLM al modelo LegalGuide (camelCase).
        """

        # 1) Texto simplificado base
        simplified = (simplification_result.simplifiedText or "").strip()

        if not simplified:
            # Fallback: no hay nada que explicar
            return schemas.LegalGuide(
                meaningForYou="No se ha podido generar la guía jurídica porque falta texto simplificado.",
                whatToDoNow=None,
                whatHappensNext=None,
                deadlinesAndRisks=None,
            )

        # 2) Contexto de tipo de documento
        doc_type = simplification_result.docType or "DESCONOCIDO"
        doc_subtype = simplification_result.docSubtype or "DESCONOCIDO"

        # 3) Construimos un "super texto" para el LLM, con algo de contexto
        #    (aunque LLMClient.callGuideGenerator solo recibe un string, aquí
        #     le pasamos docType/docSubtype arriba y luego el texto).
        text_for_llm = (
            f"Tipo de documento: {doc_type} / {doc_subtype}\n\n"
            f"TEXTO SIMPLIFICADO PARA EL CIUDADANO:\n{simplified}"
        )

        # 4) Secciones importantes (pueden venir de SimplificationResult)
        sections: Optional[List[str]] = simplification_result.importantSections or None

        # 5) Llamamos al LLM y manejamos errores
        try:
            guide_dict: Dict[str, Any] = self._client.callGuideGenerator(
                simplified_text=text_for_llm,
                sections=sections,
            )
        except Exception as e:
            # Fallback si algo peta en la llamada al LLM
            return schemas.LegalGuide(
                meaningForYou="Ha ocurrido un error al generar la guía jurídica.",
                whatToDoNow=f"Detalle técnico: {e}",
                whatHappensNext=None,
                deadlinesAndRisks=None,
            )

        # 6) Mapeo snake_case → camelCase con un poco de tolerancia
        meaning_for_you = (
            guide_dict.get("meaning_for_you")
            or guide_dict.get("meaningForYou")
            or "No se ha podido generar la explicación principal."
        )
        what_to_do_now = (
            guide_dict.get("what_to_do_now")
            or guide_dict.get("whatToDoNow")
            or None
        )
        what_happens_next = (
            guide_dict.get("what_happens_next")
            or guide_dict.get("whatHappensNext")
            or None
        )
        deadlines_and_risks = (
            guide_dict.get("deadlines_and_risks")
            or guide_dict.get("deadlinesAndRisks")
            or None
        )

        # 7) Devolvemos el DTO de dominio
        return schemas.LegalGuide(
            meaningForYou=meaning_for_you,
            whatToDoNow=what_to_do_now,
            whatHappensNext=what_happens_next,
            deadlinesAndRisks=deadlines_and_risks,
        )
