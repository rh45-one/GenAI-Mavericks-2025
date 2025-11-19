"""LLM client wrapper for Justice Made Clear."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests

PLACEHOLDER_API_KEY = "DEEPSEEK_API_KEY_PLACEHOLDER"


class LLMClient:
    """
    Encapsulate all outbound calls to the LLM provider.

    En esta versión:
    - Usamos la API de DeepSeek (compatible con OpenAI) vía HTTPS.
    - Llamamos al endpoint /v1/chat/completions.
    - Modelo por defecto: 'deepseek-chat' (configurable via settings).
    """

    def __init__(self, settings: Dict[str, Any]):
        # Ajustes principales (se permiten claves legacy por compatibilidad)
        self.base_url: str = (
            settings.get("llm_base_url")
            or settings.get("base_url")
            or "https://api.deepseek.com"
        )
        self.model: str = (
            settings.get("llm_model_name")
            or settings.get("model")
            or "deepseek-chat"
        )
        self.api_key: str = (
            settings.get("llm_api_key")
            or settings.get("api_key")
            or PLACEHOLDER_API_KEY
        )
        self.default_temperature: float = float(settings.get("llm_temperature", 0.2))
        max_tokens = settings.get("llm_max_tokens")
        self.max_tokens: Optional[int] = int(max_tokens) if max_tokens else None

    # ------------------------------------------------------------------
    # Helper interno: llamada genérica a DeepSeek Chat
    # ------------------------------------------------------------------
    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """
        Hace una llamada al endpoint /v1/chat/completions de DeepSeek y devuelve
        solo el contenido de la respuesta del asistente.
        """
        if not self.api_key or self.api_key == PLACEHOLDER_API_KEY:
            raise RuntimeError(
                "DeepSeek API key missing. Set DEEPSEEK_API_KEY before calling the LLM."
            )

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else self.default_temperature,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Formato compatible OpenAI: { "choices": [ { "message": { "content": "..." } } ] }
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("DeepSeek response missing 'choices'.")
        message = choices[0].get("message") or {}
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
        """  Simplify the source document based on its classification.
        - Mantener sentido jurídico, plazos, importes y partes.
        - Reescribir en lenguaje claro, siguiendo la Guía de redacción judicial clara.
        """

        system_prompt = (
            "Eres un EXPERTO en Lenguaje Jurídico Claro y Legal Design en España.\n"
            "Tu misión es REESCRIBIR el texto legal original para que un ciudadano sin conocimientos de derecho\n"
            "lo entienda perfectamente, SIN CAMBIAR el efecto jurídico, los plazos, las cantidades, las partes\n"
            "ni el sentido del fallo.\n"
            "\n"
            "APLICA SIEMPRE, DE FORMA OBLIGATORIA, ESTAS REGLAS BASADAS EN LA GUÍA DE REDACCIÓN JUDICIAL CLARA:\n"
            "\n"
            "1) ESTRUCTURA VISUAL Y PÁRRAFOS\n"
            "- Convierte enumeraciones complejas en LISTAS VERTICALES con guiones (-) o números (1., 2., 3.).\n"
            "- Separa las ideas en párrafos cortos con saltos de línea.\n"
            "- Agrupa en el mismo párrafo solo ideas muy relacionadas.\n"
            "\n"
            "2) MAYÚSCULAS Y FORMATO\n"
            "- Evita escribir palabras enteras en MAYÚSCULAS salvo siglas (por ejemplo, mantén LEC, LOPJ, etc.).\n"
            "- Escribe normalmente 'Sentencia', 'Auto', 'Juzgado', salvo cuando sean siglas oficiales.\n"
            "\n"
            "3) FECHAS, CIFRAS Y NÚMEROS\n"
            "- Escribe los plazos y cantidades SIEMPRE con dígitos: '20 días', '3.000 euros'.\n"
            "- Mantén TODAS las fechas y plazos que aparezcan en el texto original.\n"
            "- No inventes fechas ni plazos nuevos.\n"
            "\n"
            "4) REFERENCIAS LEGALES\n"
            "- Mantén los artículos y normas citadas, pero colócalos al final de la frase o entre paréntesis\n"
            "  para no interrumpir la lectura. Ejemplo: '... según el artículo 24 de la Constitución Española'.\n"
            "- No elimines la cita legal, solo hazla más legible.\n"
            "\n"
            "5) TRATO AL CIUDADANO Y TONO\n"
            "- Usa 'usted' como forma de cortesía y fórmulas modernas ('Sr.', 'Sra.').\n"
            "- Evita abreviaturas antiguas como 'D.' y 'Dª.' salvo que sean estrictamente necesarias.\n"
            "- Evita fórmulas arcaicas o excesivamente solemnes en los saludos o encabezados.\n"
            "\n"
            "6) TERMINOLOGÍA TÉCNICA\n"
            "- Mantén los términos jurídicos importantes, pero añádeles una explicación breve entre paréntesis\n"
            "  o un sinónimo fácil. Ejemplo: 'enervación de la acción de desahucio (posibilidad de frenar el\n"
            "  desahucio pagando lo que se debe)'.\n"
            "- No elimines conceptos jurídicos relevantes, solo hazlos comprensibles.\n"
            "\n"
            "7) LONGITUD DE LAS FRASES\n"
            "- Usa frases CORTAS.\n"
            "- Evita, siempre que sea posible, oraciones de más de 40 palabras.\n"
            "- Cuando detectes una frase muy larga con varias subordinadas, divídela en 2 o 3 frases más simples.\n"
            "\n"
            "8) ORDEN GRAMATICAL Y CLARIDAD\n"
            "- Utiliza preferentemente el orden Sujeto + Verbo + Complementos.\n"
            "- Di claramente quién hace qué y a quién: 'El juzgado decide que...', 'La persona demandada debe pagar...'.\n"
            "- Evita estructuras muy enrevesadas o con exceso de subordinadas.\n"
            "\n"
            "9) TIEMPOS VERBALES MODERNOS\n"
            "- Elimina el uso del futuro de subjuntivo ('quien tuviere', 'hubiere') y sustitúyelo por formas actuales\n"
            "  ('quien tenga', 'haya').\n"
            "- Mantén el tiempo verbal coherente con la decisión judicial (normalmente pasado o presente).\n"
            "\n"
            "10) MANTENER EL SENTIDO JURÍDICO\n"
            "- No cambies quién gana o pierde, ni quién debe hacer qué.\n"
            "- No cambies importes, plazos, fechas ni condiciones.\n"
            "- No inventes hechos ni derechos nuevos.\n"
            "- Si algo no se entiende bien, acláralo SIN añadir información que no esté en el texto.\n"
            "\n"
            "INSTRUCCIONES DE RESPUESTA:\n"
            "- Reescribe TODO el texto aplicando estas reglas.\n"
            "- Usa saltos de línea para separar párrafos.\n"
            "- No añadas comentarios meta ni expliques qué estás haciendo.\n"
            "- No incluyas comillas al principio o al final.\n"
        )

        user_prompt = f"""Tipo de documento: {doc_type} / {doc_subtype}

Reescribe el siguiente texto jurídico en lenguaje claro para una persona sin formación jurídica.
No añadas información nueva ni elimines plazos, importes, partes o derechos.

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
