"""Prompt templates for legal guide generation (four blocks)."""
from __future__ import annotations

from typing import Dict


def system_prompt() -> str:
    return (
        "Eres un asistente jurídico que explica resoluciones y escritos judiciales "
        "a ciudadanos en España.\n"
        "A partir del texto simplificado, debes generar una guia en 4 bloques.\n"
        "Responde SIEMPRE en JSON estricto con las claves:\n"
        "  meaning_for_you, what_to_do_now, what_happens_next, deadlines_and_risks.\n"
    )


def user_prompt(simplified_text: str, context: Dict[str, str]) -> str:
    context_dump = "\n".join(f"{k}: {v}" for k, v in context.items())
    return (
        f"Usa el siguiente texto simplificado como base:\n\n"
        f"--- TEXTO SIMPLIFICADO ---\n{simplified_text}\n--- FIN TEXTO SIMPLIFICADO ---\n\n"
        f"Contexto:\n{context_dump}\n\n"
        "Devuelve SOLO un JSON con esta forma:\n{\n  \"meaning_for_you\": \"...\",\n  \"what_to_do_now\": \"...\",\n  \"what_happens_next\": \"...\",\n  \"deadlines_and_risks\": \"...\"\n}\n"
    )
