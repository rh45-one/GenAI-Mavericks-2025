"""LLM-based simplification with deterministic fallo coherence."""
from __future__ import annotations

from typing import Dict, Any, List, Tuple
import re

from .. import schemas
from ..clients.llm_client import BaseLLMClient, LLMClientError
from ..prompt_templates import simplification as simplification_prompt


class SimplificationService:
    """
    Build a structured simplification using falloLiteral as the single source of truth
    for the outcome, while preserving backward compatibility via simplifiedText.
    """

    MAX_CHARS = 12000
    HARD_LIMIT = 16000

    def __init__(self, client: BaseLLMClient):
        self._client = client

    def simplify(
        self,
        document: schemas.SegmentedDocument,
        classification: schemas.ClassificationResult,
    ) -> schemas.SimplificationResult:
        doc_type = classification.docType or "OTRO"
        doc_subtype = classification.docSubtype or "DESCONOCIDO"
        strategy = self._select_strategy(doc_type, doc_subtype)

        fallo_literal = getattr(document, "falloLiteral", None) or getattr(document, "fallbackFallo", None)
        metadata = self._collect_metadata(document)
        parties = self._collect_parties(document)

        payload = self._call_llm(document, doc_type, doc_subtype, fallo_literal, metadata, parties)
        structured = self._normalize_payload(payload, fallo_literal)

        simplified_text = self._render_simplified_text(structured, doc_type, doc_subtype)

        important_sections = self._important_sections(document)

        # Map structured decision to dict for schema
        decision_dict = {
            "whoWins": structured["decisionFallo"]["whoWins"],
            "costs": structured["decisionFallo"]["costs"],
            "plainText": structured["decisionFallo"]["plainText"],
            "falloLiteral": structured["decisionFallo"]["falloLiteral"],
        }

        warnings: List[str] = []

        return schemas.SimplificationResult(
            simplifiedText=simplified_text,
            docType=doc_type,
            docSubtype=doc_subtype,
            headerSummary=structured["headerSummary"],
            partiesSummary=structured["partiesSummary"],
            proceduralContext=structured["proceduralContext"],
            decisionFallo=decision_dict,
            importantSections=important_sections,
            strategy=strategy,
            provider=self._client.provider_name,
            truncated=False,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # LLM wrapper
    # ------------------------------------------------------------------
    def _call_llm(
        self,
        document: schemas.SegmentedDocument,
        doc_type: str,
        doc_subtype: str,
        fallo_literal: str | None,
        metadata: Dict[str, str],
        parties: Dict[str, str],
    ) -> Dict[str, Any]:
        text = document.normalizedText or document.rawText or ""
        if len(text) > self.HARD_LIMIT:
            text = text[: self.HARD_LIMIT]

        system = simplification_prompt.system_prompt()
        user = simplification_prompt.user_prompt(
            text,
            doc_type=doc_type,
            doc_subtype=doc_subtype,
            fallo_literal=fallo_literal,
            metadata=metadata,
            parties=parties,
        )

        try:
            raw = self._client.chat(system, user, temperature=0.1)
            return self._client._parse_json(raw)
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_payload(self, data: Dict[str, Any], fallo_literal: str | None) -> Dict[str, Any]:
        """Ensure the JSON structure and enforce determinism from fallo_literal."""
        if not isinstance(data, dict):
            data = {}

        header = data.get("headerSummary") or {}
        parties = data.get("partiesSummary") or {}
        procedural = data.get("proceduralContext") or ""
        decision = data.get("decisionFallo") or {}

        # Override whoWins / costs deterministically from fallo_literal
        who, costs = self._derive_decision_from_fallo(fallo_literal)

        decision_struct = {
            "whoWins": who,
            "costs": costs,
            "plainText": decision.get("plainText") or (fallo_literal or ""),
            "falloLiteral": fallo_literal or "",
        }

        return {
            "headerSummary": {
                "court": header.get("court", ""),
                "date": header.get("date", ""),
                "caseNumber": header.get("caseNumber", ""),
                "resolutionNumber": header.get("resolutionNumber", ""),
                "procedureType": header.get("procedureType", ""),
                "judge": header.get("judge", ""),
            },
            "partiesSummary": {
                "plaintiff": parties.get("plaintiff", ""),
                "plaintiffRepresentatives": parties.get("plaintiffRepresentatives", ""),
                "defendant": parties.get("defendant", ""),
                "defendantRepresentatives": parties.get("defendantRepresentatives", ""),
            },
            "proceduralContext": procedural,
            "decisionFallo": decision_struct,
        }

    def _derive_decision_from_fallo(self, fallo_literal: str | None) -> Tuple[str, str]:
        if not fallo_literal:
            return "desconocido", "desconocido"

        upper = fallo_literal.upper()
        who = "desconocido"
        if "SE ESTIMA PARCIAL" in upper or "ESTIMA PARCIAL" in upper:
            who = "parcial"
        elif "SE ESTIMA" in upper or "ESTIMA LA DEMANDA" in upper:
            who = "actora"
        elif "SE DESESTIMA" in upper or "DESESTIMA LA DEMANDA" in upper or "RECHAZA COMPLETAMENTE" in upper:
            who = "demandado"

        costs = "desconocido"
        if "COSTAS A LA PARTE ACTORA" in upper or "COSTAS A LA ACTORA" in upper:
            costs = "actora"
        elif "COSTAS A LA PARTE DEMANDADA" in upper or "COSTAS A LA DEMANDADA" in upper:
            costs = "demandado"
        elif "SIN ESPECIAL PRONUNCIAMIENTO" in upper:
            costs = "sin_costas"

        return who.lower(), costs.lower()

    def _render_simplified_text(self, data: Dict[str, Any], doc_type: str, doc_subtype: str) -> str:
        h = data.get("headerSummary", {})
        p = data.get("partiesSummary", {})
        d = data.get("decisionFallo", {})

        lines = []
        lines.append("[1] Datos del caso")
        lines.append(f"- Fecha: {h.get('date','')}")
        lines.append(f"- Juzgado: {h.get('court','')}")
        lines.append(f"- Jueza/Juez: {h.get('judge','')}")
        lines.append(f"- Numero de caso: {h.get('caseNumber','')}")
        lines.append(f"- Numero de resolucion: {h.get('resolutionNumber','')}")
        lines.append(f"- Tipo de documento: {doc_type} - {doc_subtype}")
        lines.append("")

        lines.append("[2] Partes involucradas")
        lines.append(f"- Demandante: {p.get('plaintiff','')}")
        if p.get("plaintiffRepresentatives"):
            lines.append(f"  Representantes: {p.get('plaintiffRepresentatives','')}")
        lines.append(f"- Demandado: {p.get('defendant','')}")
        if p.get("defendantRepresentatives"):
            lines.append(f"  Representantes: {p.get('defendantRepresentatives','')}")
        lines.append("")

        lines.append("[3] Lo que paso antes (contexto procesal)")
        lines.append(data.get("proceduralContext") or "")
        lines.append("")

        lines.append("[4] Resultado del caso (segun el FALLO)")
        lines.append(f"- Quien gana: {d.get('whoWins','desconocido')}")
        lines.append(f"- Costas: {d.get('costs','desconocido')}")
        lines.append(f"- Resumen breve: {d.get('plainText','')}")
        if d.get("falloLiteral"):
            lines.append("- Fallo literal:")
            lines.append(d.get("falloLiteral"))
        lines.append("")

        # Resource info if present
        return "\n".join(line for line in lines if line is not None).strip()

    # ------------------------------------------------------------------
    # Strategy + important sections
    # ------------------------------------------------------------------
    @staticmethod
    def _select_strategy(doc_type: str, doc_subtype: str) -> str:
        doc_type_u = (doc_type or "").upper()
        doc_subtype_u = (doc_subtype or "").upper()

        if doc_type_u == "RESOLUCION_JURIDICA":
            if doc_subtype_u in {"SENTENCIA", "AUTO", "DECRETO"}:
                return "resolution"
            return "resolution_generic"

        if doc_type_u == "ESCRITO_PROCESAL":
            if doc_subtype_u in {"DEMANDA", "RECURSO"}:
                return "procedural_filing"
            return "procedural_generic"

        return "generic"

    @staticmethod
    def _important_sections(document: schemas.SegmentedDocument) -> List[schemas.DocumentSection]:
        if not document.sections:
            return []

        sections = document.sections
        name_to_sections = {}
        for sec in sections:
            name_to_sections.setdefault((sec.name or "").upper(), sec)

        priority = [
            "ENCABEZADO",
            "ANTECEDENTES DE HECHO",
            "FUNDAMENTOS DE DERECHO",
            "FUNDAMENTOS JURIDICOS",
            "FALLO",
            "PETICIONES",
        ]

        selected: List[schemas.DocumentSection] = []

        for key in priority:
            sec = name_to_sections.get(key)
            if sec and sec not in selected:
                selected.append(sec)
            if len(selected) >= 4:
                break

        if len(selected) < 3:
            for sec in sections:
                if sec not in selected:
                    selected.append(sec)
                if len(selected) >= 3:
                    break

        return selected

    # ------------------------------------------------------------------
    # Metadata grabbers
    # ------------------------------------------------------------------
    def _collect_metadata(self, document: schemas.SegmentedDocument) -> Dict[str, str]:
        meta = {}
        try:
            extra = getattr(document.metadata, "extra", {}) if document.metadata else {}
            meta["courtName"] = extra.get("courtName", "")
            meta["city"] = extra.get("city", "")
            meta["decisionDate"] = extra.get("decisionDate", "")
            meta["caseNumber"] = extra.get("caseNumber", "")
            meta["resolutionNumber"] = extra.get("resolutionNumber", "")
            meta["procedureType"] = extra.get("procedureType", "")
            meta["judgeName"] = extra.get("judgeName", "")
        except Exception:
            pass
        return meta

    def _collect_parties(self, document: schemas.SegmentedDocument) -> Dict[str, str]:
        parties: Dict[str, str] = {
            "plaintiffName": "",
            "plaintiffRepresentatives": "",
            "defendantName": "",
            "defendantRepresentatives": "",
        }
        try:
            extra = getattr(document.metadata, "extra", {}) if document.metadata else {}
            parties["plaintiffName"] = extra.get("plaintiffName", "")
            parties["plaintiffRepresentatives"] = extra.get("plaintiffRepresentatives", "")
            parties["defendantName"] = extra.get("defendantName", "")
            parties["defendantRepresentatives"] = extra.get("defendantRepresentatives", "")
        except Exception:
            pass
        return parties
