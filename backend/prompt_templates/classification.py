"""Prompt templates for document classification."""
from __future__ import annotations

from typing import List


def system_prompt() -> str:
    return (
        "Eres un asistente LEGAL EXPERTO en documentos judiciales de ESPAÑA.\n"
        "Debes CLASIFICAR el documento en una de estas categorías:\n"
        "\n"
        "1) RESOLUCION_JURIDICA → documentos emitidos por un juzgado.\n"
        "   Subtipos: SENTENCIA, AUTO, DECRETO, PROVIDENCIA.\n"
        "2) ESCRITO_PROCESAL → documentos presentados por las partes.\n"
        "   Subtipos: DEMANDA, RECURSO, ALEGACIONES, OPOSICION.\n"
        "3) OTRO → si no encaja.\n"
        "\n"
        "Instrucciones:\n"
        "- Responde SIEMPRE en JSON estricto.\n"
        "- NO añadas explicaciones.\n"
        "- Usa doc_subtype='DESCONOCIDO' si no estás seguro.\n"
    )


def user_prompt(text_snippet: str, sections: List[str] | None = None) -> str:
    sections_block = "\n".join(f"- {s}" for s in (sections or [])) or "- (sin secciones detectadas)"
    return (
        f"Analiza el siguiente texto y clasifícalo:\n\n"
        f"--- DOCUMENTO ---\n"
        f"{text_snippet}\n"
        f"--- FIN DOCUMENTO ---\n\n"
        f"Secciones detectadas:\n{sections_block}\n\n"
        "Devuelve SOLO un JSON con esta forma:\n"
        "{\n  \"doc_type\": \"...\",\n  \"doc_subtype\": \"...\",\n  \"confidence\": 0.0\n}\n"
    )
