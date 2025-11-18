"""LLM client wrapper for Justice Made Clear."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests


class LLMClient:
    """
    Encapsulate all outbound calls to the LLM provider.

    En esta versión:
    - Usamos Ollama en local, sin API keys ni servicios externos.
    - Llamamos al endpoint HTTP: http://localhost:11434/api/chat
    - Modelo por defecto: 'llama3.1' (configurable via settings).
    """

    def __init__(self, settings: Dict[str, Any]):
        # URL base de Ollama (por defecto localhost)
        self.base_url: str = settings.get("base_url", "http://localhost:11434")
        # Nombre del modelo en Ollama (ej: `llama3.1`, `phi3`, etc.)
        self.model: str = settings.get("model", "llama3.1")

    # ------------------------------------------------------------------
    # Helper interno: llamada genérica a Ollama Chat
    # ------------------------------------------------------------------
    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """
        Hace una llamada al endpoint /api/chat de Ollama y devuelve
        solo el contenido de la respuesta del asistente.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Formato estándar de /api/chat: { "message": { "content": "..." }, ... }
        message = data.get("message") or {}
        content = message.get("content", "")

        return content

    # ------------------------------------------------------------------
    # 1) Clasificación de documento
    # ------------------------------------------------------------------
   

    def callClassifier(
        self,
        text: str,
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Classify the document type/subtype and return confidences.

        Devuelve un dict:
        {
          "doc_type": "RESOLUCION_JURIDICA" | "ESCRITO_PROCESAL" | "OTRO",
          "doc_subtype": "SENTENCIA" | "AUTO" | "DEMANDA" | "RECURSO" | "DESCONOCIDO",
          "confidence": float,
          "raw_response": str
        }

        Estrategia:
        - 1º aplicamos reglas duras muy sencillas sobre el texto.
        - 2º, si hay duda, preguntamos al LLM.
        - 3º, si el LLM devuelve algo raro, nos quedamos con el fallback de reglas.
        """
        snippet = text[:8000]  # suficiente para ver encabezados importantes
        upper = snippet.upper()

        # -----------------------------
        # 1) Heurísticas base por texto
        # -----------------------------
        print("🟦DEBUG snippet:", repr(snippet))
        print("🟥DEBUG upper:", repr(upper))
        is_resolucion = any(
            kw in upper
            for kw in [
                "SENTENCIA",
                "AUTO",
                "FALLO",
                "FUNDAMENTOS DE DERECHO",
                "ANTECEDENTES DE HECHO",
                "JUZGADO DE PRIMERA INSTANCIA",
                "MAGISTRADO",
                "MAGISTRADA",
                "JUZGADO DE 1ª INSTANCIA",
            ]
        )

        is_escrito = any(
            kw in upper
            for kw in [
                "SUPLICO AL JUZGADO",
                "AL JUZGADO",
                "AL JUZGADO DE",
                "DEMANDA",
                "RECURSO",
                "ESCRITO DE ALEGACIONES",
                "ESCRITO DE OPOSICIÓN",
            ]
        )

        rule_doc_type = "OTRO"
        rule_doc_subtype = "DESCONOCIDO"
        rule_conf = 0.0

        if is_resolucion and not is_escrito:
            rule_doc_type = "RESOLUCION_JURIDICA"
            if "SENTENCIA" in upper:
                rule_doc_subtype = "SENTENCIA"
            elif "AUTO" in upper:
                rule_doc_subtype = "AUTO"
            rule_conf = 0.9

        elif is_escrito and not is_resolucion:
            rule_doc_type = "ESCRITO_PROCESAL"
            if "DEMANDA" in upper:
                rule_doc_subtype = "DEMANDA"
            elif "RECURSO" in upper:
                rule_doc_subtype = "RECURSO"
            rule_conf = 0.9

        # Si las reglas ya lo tienen bastante claro, puedes incluso devolver directamente:
        if rule_conf >= 0.9:
            return {
                "doc_type": rule_doc_type,
                "doc_subtype": rule_doc_subtype,
                "confidence": rule_conf,
                "raw_response": "RULE_BASED",
            }

        # ---------------------------------
        # 2) Si no está claro, preguntamos LLM
        # ---------------------------------
        system_prompt = (
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

        user_prompt = f"""Analiza el siguiente texto y clasifícalo:

--- DOCUMENTO ---
{snippet}
--- FIN DOCUMENTO ---

Devuelve SOLO un JSON con esta forma:
{{
  "doc_type": "...",
  "doc_subtype": "...",
  "confidence": 0.0
}}"""

        try:
            raw = self._chat(system_prompt, user_prompt, temperature=0.0)
            data = json.loads(raw)
        except Exception:
            # Si el LLM falla, volvemos a lo que hayan dicho las reglas
            return {
                "doc_type": rule_doc_type,
                "doc_subtype": rule_doc_subtype,
                "confidence": rule_conf,
                "raw_response": "RULE_FALLBACK",
            }

        doc_type = data.get("doc_type", "OTRO")
        doc_subtype = data.get("doc_subtype", "DESCONOCIDO")
        confidence = float(data.get("confidence", 0.0))

        # ---------------------------------
        # 3) Ajuste final con reglas
        # ---------------------------------
        # Si LLM dice algo raro pero las reglas detectan clarísimamente SENTENCIA:
        if rule_conf > confidence:
            doc_type = rule_doc_type
            doc_subtype = rule_doc_subtype
            confidence = rule_conf
            raw_response = f"LLM:{data} | APPLIED_RULE_OVERRIDE"
        else:
            raw_response = raw

        return {
            "doc_type": doc_type,
            "doc_subtype": doc_subtype,
            "confidence": confidence,
            "raw_response": raw_response,
        }
    # ------------------------------------------------------------------
    # 2) Simplificación en lenguaje claro
    # ------------------------------------------------------------------
    def callSimplifier(self, text: str, doc_type: str, doc_subtype: str) -> str:
        """
        Simplify the source document based on its classification.
        - Mantener sentido juridico, plazos, importes y partes.
        - Reescribir en lenguaje claro.
        """
        system_prompt = (
            "Eres un asistente especializado en redaccion judicial clara en España.\n"
            "Tu tarea es reescribir el texto jurídico en lenguaje claro, "
            "SIN CAMBIAR el significado jurídico, las partes, los plazos, "
            "las cantidades ni el sentido del fallo.\n"
            "Usa frases cortas, orden lógico, evita tecnicismos innecesarios, "
            "y si mantienes un tecnicismo importante, explícalo brevemente.\n"
            "MUY IMPORTANTE: responde SOLO con el texto reescrito, "
            "sin explicaciones adicionales, sin comillas, sin saludos.\n"
        )

        user_prompt = f"""Tipo de documento: {doc_type} / {doc_subtype}

Reescribe el siguiente texto jurídico en lenguaje claro para una persona sin formación jurídica.
No añadas información nueva ni elimines plazos o derechos.

--- TEXTO ORIGINAL ---
{text}
--- FIN TEXTO ---"""

        simplified = self._chat(system_prompt, user_prompt, temperature=0.3)
        return simplified

    # ------------------------------------------------------------------
    # 3) Generación de la guía jurídica (4 bloques)
    # ------------------------------------------------------------------
    def callGuideGenerator(
        self,
        simplified_text: str,
        sections: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generate the four guide blocks from simplified text and references.

        Devuelve un dict:
        {
          "meaning_for_you": "...",
          "what_to_do_now": "...",
          "what_happens_next": "...",
          "deadlines_and_risks": "..."
        }
        """
        system_prompt = (
            "Eres un asistente jurídico que explica resoluciones y escritos judiciales "
            "a ciudadanos en España.\n"
            "A partir del texto simplificado, debes generar una guia en 4 bloques.\n"
            "Responde SIEMPRE en JSON estricto con las claves:\n"
            "  meaning_for_you, what_to_do_now, what_happens_next, deadlines_and_risks.\n"
        )

        user_prompt = f"""Usa el siguiente texto simplificado como base:

--- TEXTO SIMPLIFICADO ---
{simplified_text}
--- FIN TEXTO SIMPLIFICADO ---

Devuelve SOLO un JSON con esta forma:
{{
  "meaning_for_you": "...",
  "what_to_do_now": "...",
  "what_happens_next": "...",
  "deadlines_and_risks": "..."
}}"""

        raw = self._chat(system_prompt, user_prompt, temperature=0.2)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "meaning_for_you": "No se ha podido generar la explicación correctamente.",
                "what_to_do_now": "",
                "what_happens_next": "",
                "deadlines_and_risks": "",
            }

        return data

    # ------------------------------------------------------------------
    # 4) Verificación de seguridad jurídica
    # ------------------------------------------------------------------
    def callVerifier(
        self,
        original_text: str,
        simplified_text: str,
        legal_guide: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Ask the LLM to confirm that critical meaning remains intact.

        Devuelve:
        {
          "is_safe": bool,
          "warnings": [str, ...],
          "raw_response": str
        }
        """
        system_prompt = (
            "Eres un revisor jurídico. Debes comparar el texto original, "
            "el texto simplificado y la guía para el ciudadano.\n"
            "Tu objetivo es detectar si se ha perdido información clave: plazos, importes, "
            "obligaciones o el sentido del fallo.\n"
            "Responde SIEMPRE en JSON estricto con:\n"
            "  is_safe: true/false\n"
            "  warnings: lista de strings explicando posibles problemas.\n"
        )

        user_prompt = f"""TEXTO ORIGINAL:
--- ORIGINAL ---
{original_text}
--- FIN ORIGINAL ---

TEXTO SIMPLIFICADO:
--- SIMPLIFICADO ---
{simplified_text}
--- FIN SIMPLIFICADO ---

GUIA PARA EL CIUDADANO:
--- GUIA ---
{json.dumps(legal_guide, ensure_ascii=False)}
--- FIN GUIA ---

Devuelve SOLO un JSON con esta forma:
{{
  "is_safe": true,
  "warnings": ["..."]
}}"""

        raw = self._chat(system_prompt, user_prompt, temperature=0.0)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "is_safe": False,
                "warnings": ["No se ha podido verificar correctamente el significado."],
            }

        data["raw_response"] = raw
        return data
