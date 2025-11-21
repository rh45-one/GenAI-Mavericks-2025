"""Prompt templates for legal guide generation with decisionFallo context."""
from __future__ import annotations
from typing import Dict


def system_prompt() -> str:
    return (
        "Eres un asistente juridico que genera una guia en cuatro bloques: meaning_for_you, what_to_do_now, "
        "what_happens_next, deadlines_and_risks.\n\n"
        "Reglas:\n"
        "- Si whoWins != desconocido, usa frases condicionales: 'Si en el fallo se estima...', 'Si se imponen costas...'.\n"
        "- Si whoWins == desconocido, di que el fallo no permite identificar quien gana y mantente totalmente neutro.\n"
        "- Prohibido inventar efectos juridicos (devoluciones, intereses, ejecucion, firmeza, jurisprudencia, abusividad, etc.) que no esten en falloLiteral.\n"
        "- Plazos de recurso solo si aparecen literalmente en falloLiteral; si no, no los menciones.\n"
    )


def user_prompt(
    simplified_text: str,
    context: Dict[str, str],
    decision_fallo: Dict[str, str],
    metadata: Dict[str, str],
) -> str:
    ctx_lines = "\n".join(f"{k}: {v}" for k, v in context.items())
    dec_lines = "\n".join(f"{k}: {v}" for k, v in decision_fallo.items())
    meta_lines = "\n".join(f"{k}: {v}" for k, v in metadata.items())
    return (
        "Genera la guia legal a partir de la simplificacion y el fallo.\n\n"
        "--- CONTEXTO DOCUMENTO ---\n"
        f"{ctx_lines}\n"
        "--- METADATOS ---\n"
        f"{meta_lines}\n"
        "--- DECISION FALLO ---\n"
        f"{dec_lines}\n"
        "--- TEXTO SIMPLIFICADO ---\n"
        f"{simplified_text}\n"
        "--- FIN ---\n\n"
        "Recuerda: usa condicionales si whoWins no es desconocido. Si whoWins es desconocido, indica que no se puede saber quien gano y mantente neutro.\n"
        "Prohibido inventar efectos o plazos no presentes en falloLiteral. Devuelve solo JSON:\n"
        "{\n"
        '  "meaning_for_you": "...",\n'
        '  "what_to_do_now": "...",\n'
        '  "what_happens_next": "...",\n'
        '  "deadlines_and_risks": "..."\n'
        "}\n"
    )
