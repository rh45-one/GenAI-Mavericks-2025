"""Prompt templates for safety verifier."""
from __future__ import annotations

from typing import Dict


def system_prompt() -> str:
    return (
        "Eres un revisor jurídico. Debes comparar el texto original, "
        "el texto simplificado y la guía para el ciudadano.\n"
        "Tu objetivo es detectar si se ha perdido información clave: plazos, importes, "
        "obligaciones o el sentido del fallo.\n"
        "Responde SIEMPRE en JSON estricto con:\n"
        "  is_safe: true/false\n"
        "  warnings: lista de strings explicando posibles problemas.\n"
    )


def user_prompt(original: str, simplified: str, guide: Dict[str, str]) -> str:
    return (
        f"TEXTO ORIGINAL:\n--- ORIGINAL ---\n{original}\n--- FIN ORIGINAL ---\n\n"
        f"TEXTO SIMPLIFICADO:\n--- SIMPLIFICADO ---\n{simplified}\n--- FIN SIMPLIFICADO ---\n\n"
        f"GUIA PARA EL CIUDADANO:\n--- GUIA ---\n{guide}\n--- FIN GUIA ---\n\n"
        "Devuelve SOLO un JSON con esta forma:\n{\n  \"is_safe\": true,\n  \"warnings\": [\"...\"]\n}\n"
    )
