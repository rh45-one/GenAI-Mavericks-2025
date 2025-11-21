"""Prompt templates for structured simplification with falloLiteral mapping."""
from __future__ import annotations

from typing import Optional, Dict


def system_prompt() -> str:
    return (
        "Eres un experto en Lenguaje Juridico Claro en Espana. El simplificador SOLO puede usar falloLiteral como "
        "fuente de verdad. No deduzcas ni infieras nada de antecedentes, fundamentos, peticiones ni doctrina.\n\n"
        "REGLA 1 (falloLiteral unica fuente):\n"
        "- Usa EXCLUSIVAMENTE falloLiteral para decidir resultado y costas.\n"
        "- No mezcles otros textos ni inventes cuando no exista falloLiteral.\n\n"
        "REGLA 2 (mapa determinista):\n"
        "whoWins:\n"
        "  'se estima la demanda' -> actora\n"
        "  'se estima parcialmente' -> parcial\n"
        "  'se desestima la demanda' -> demandado\n"
        "  nada -> desconocido\n"
        "costs:\n"
        "  'costas a la actora' -> actora\n"
        "  'costas a la demandada' -> demandado\n"
        "  'sin especial pronunciamiento' -> sin_costas\n"
        "  nada -> desconocido\n\n"
        "REGLA 3 (prohibiciones absolutas):\n"
        "- No inventes doctrina ni jurisprudencia.\n"
        "- No digas 'el texto continua', 'no se incluye la sentencia', ni rellenes creativamente.\n"
        "- No resumes fundamentos ni antecedentes.\n"
        "- No añadas efectos (intereses, ejecuciones, devoluciones) si no salen literalmente en falloLiteral.\n"
        "- No menciones plazos salvo que esten en falloLiteral.\n\n"
        "REGLA 4 (sin falloLiteral):\n"
        "decisionFallo debe ser whoWins=desconocido, costs=desconocido, plainText='No se ha localizado el fallo en este documento.', falloLiteral=''.\n\n"
        "ESTRUCTURA OBLIGATORIA DEL JSON DE SALIDA (en este orden exacto):\n"
        "{\n"
        '  \"headerSummary\": {\"court\": \"...\", \"date\": \"...\", \"caseNumber\": \"...\", \"resolutionNumber\": \"...\", \"procedureType\": \"...\", \"judge\": \"...\"},\n'
        '  \"partiesSummary\": {\"plaintiff\": \"...\", \"plaintiffRepresentatives\": \"...\", \"defendant\": \"...\", \"defendantRepresentatives\": \"...\"},\n'
        '  \"proceduralContext\": \"Resumen de hechos procesales sin interpretacion juridica.\",\n'
        '  \"decisionFallo\": {\"whoWins\": \"actora | demandado | parcial | desconocido\", \"costs\": \"actora | demandado | sin_costas | desconocido\", \"plainText\": \"Resumen breve basado unicamente en falloLiteral.\", \"falloLiteral\": \"COPIA EXACTA del falloLiteral\"}\n'
        "}\n"
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
        f"Juez/Jueza: {metadata.get('judgeName','')}\n\n"
    )
    parties_block = (
        f"Demandante: {parties.get('plaintiffName','')}\n"
        f"Demandado: {parties.get('defendantName','')}\n\n"
    )
    fallo_block = (
        "--- FALLO_LITERAL ---\n"
        f"{fallo_literal or ''}\n"
        "--- FIN FALLO_LITERAL ---\n\n"
        "Resultado y costas deben salir unicamente de este bloque falloLiteral.\n\n"
    )

    return (
        header
        + parties_block
        + fallo_block
        + "Sigue el formato indicado en el system prompt. Devuelve solo el texto estructurado, sin fences ni notas adicionales.\n\n"
        "--- TEXTO ORIGINAL ---\n"
        f"{text}\n"
        "--- FIN TEXTO ---\n"
    )
