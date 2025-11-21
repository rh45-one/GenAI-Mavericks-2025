"""Prompt templates for structured simplification with falloLiteral mapping."""
from __future__ import annotations

from typing import Optional, Dict


def system_prompt() -> str:
    return (
        "Eres un experto en Lenguaje Juridico Claro en Espana. SOLO puedes usar falloLiteral como fuente para el resultado.\n\n"
        "Reglas clave:\n"
        "- No deduzcas ni infieras nada de antecedentes, fundamentos, peticiones ni doctrina.\n"
        "- No inventes contenido; si falta texto, no lo menciones.\n"
        "- Prohibido frases meta como 'el texto continua'.\n\n"
        "Mapeo determinista:\n"
        "whoWins: 'se estima la demanda' -> actora; 'se estima parcialmente' -> parcial; 'se desestima la demanda' -> demandado; nada -> desconocido.\n"
        "costs: 'costas a la actora' -> actora; 'costas a la demandada' -> demandado; 'sin especial pronunciamiento' -> sin_costas; nada -> desconocido.\n\n"
        "Si no hay falloLiteral: whoWins=desconocido, costs=desconocido, plainText='No se ha localizado el fallo en este documento.', falloLiteral=''.\n\n"
        "Devuelve SIEMPRE un JSON con esta estructura exacta:\n"
        "{\n"
        '  \"headerSummary\": {\"court\": \"...\", \"date\": \"...\", \"caseNumber\": \"...\", \"resolutionNumber\": \"...\", \"procedureType\": \"...\", \"judge\": \"...\"},\n'
        '  \"partiesSummary\": {\"plaintiff\": \"...\", \"plaintiffRepresentatives\": \"...\", \"defendant\": \"...\", \"defendantRepresentatives\": \"...\"},\n'
        '  \"proceduralContext\": \"Resumen de hechos procesales sin interpretacion juridica.\",\n'
        '  \"decisionFallo\": {\"whoWins\": \"actora | demandado | parcial | desconocido\", \"costs\": \"actora | demandado | sin_costas | desconocido\", \"plainText\": \"Resumen breve basado unicamente en falloLiteral.\", \"falloLiteral\": \"COPIA EXACTA del falloLiteral\"}\n'
        "}\n"
        "No incluyas texto fuera del JSON ni fences."
    )


def user_prompt(
    text: str,
    doc_type: Optional[str] = None,
    doc_subtype: Optional[str] = None,
    fallo_literal: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    parties: Optional[Dict[str, str]] = None,
) -> str:
    metadata = metadata or {}
    parties = parties or {}
    header = (
        f"Tipo de documento: {doc_type or 'DESCONOCIDO'} / {doc_subtype or 'DESCONOCIDO'}\n"
        f"Juzgado: {metadata.get('courtName','')}\n"
        f"Ciudad: {metadata.get('city','')}\n"
        f"Fecha: {metadata.get('decisionDate','')}\n"
        f"Numero de caso: {metadata.get('caseNumber','')}\n"
        f"Numero de resolucion: {metadata.get('resolutionNumber','')}\n"
        f"Tipo de procedimiento: {metadata.get('procedureType','')}\n"
        f"Juez/Jueza: {metadata.get('judgeName','')}\n\n"
    )
    parties_block = (
        f"Demandante: {parties.get('plaintiffName','')}\n"
        f"Representantes Demandante: {parties.get('plaintiffRepresentatives','')}\n"
        f"Demandado: {parties.get('defendantName','')}\n"
        f"Representantes Demandado: {parties.get('defendantRepresentatives','')}\n\n"
    )

    fallo_block = (
        "--- FALLO_LITERAL ---\n"
        f"{fallo_literal or ''}\n"
        "--- FIN FALLO_LITERAL ---\n\n"
        "Resultado y costas deben salir unicamente de este bloque falloLiteral. Prohibido usar otras secciones.\n\n"
    )

    return (
        header
        + parties_block
        + fallo_block
        + "Devuelve SOLO el JSON con la estructura indicada. No menciones texto truncado ni agregues comentarios.\n"
        "--- TEXTO ORIGINAL ---\n"
        f"{text}\n"
        "--- FIN TEXTO ---\n"
    )
