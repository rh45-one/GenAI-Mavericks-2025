# División de trabajo – Justice Made Clear – Empowering the citizens

Este documento resume cómo nos organizamos para desarrollar el prototipo en una semana.

---

## Equipo

- **Sebas**
  - Database management
  - Model training
  - Python, Java
  - Presentaciones (PowerPoint)
  - Azure, DevOps

- **Samu**
  - Modelado
  - Model training
  - Python, MatLab, C
  - PowerBI

- **Alex**
  - Database management (nivel medio)
  - Extracción y análisis de datos
  - Presentaciones (PowerPoint – nivel medio)
  - Python

- **Lucía**
  - Bases de datos (evitar CSV)
  - Python
  - LLMs

- **Hugo**
  - Front-end (web design & dev)
  - HTML, CSS, JavaScript (nivel medio)
  - Python y Java (básico)
  - Docker, virtualización
  - Presentaciones (PowerPoint)

---

## Bloques de trabajo

### Bloque A – Backend API y orquestador  
**Líder: Sebas**

Responsable de la “capa BackendAPI” del diagrama de clases:

- Ficheros principales:
  - `backend/app.py`
  - `backend/config.py`
  - `backend/dependencies.py`
- Tareas:
  - Definir la app FastAPI y el endpoint `POST /process_document`.
  - Implementar la clase/estructura tipo **BackendAPI** con métodos conceptuales:
    - `processDocument`
    - `ingestAndOcr`
    - `normalizeAndSegment`
    - `classifyDocument`
    - `simplifyDocument`
    - `generateLegalGuide`
    - `safetyCheck`
  - Orquestar la llamada secuencial a los servicios:
    1. `IngestService`
    2. `NormalizationService`
    3. `ClassificationService`
    4. `SimplificationService`
    5. `LegalGuideService`
    6. `SafetyCheckService`
  - Asegurar que las I/O usan los modelos definidos en `schemas.py`.
  - (Opcional) Base para Docker / despliegue sencillo (p. ej. en Azure).

Colaboración clave con:
- Alex: modelos de datos (`schemas.py`).
- Lucía: clientes LLM/OCR y servicios internos.

---

### Bloque B – Modelos de datos y utilidades  
**Líder: Alex**

Responsable de la parte de **DocumentInput**, **ProcessedDocument**, **LegalGuide** del diagrama de clases:

- Ficheros principales:
  - `backend/schemas.py`
  - `backend/utils/text_cleaning.py`
  - `backend/utils/date_amount_parsing.py`
  - `backend/utils/logging_utils.py`
- Tareas:
  - Definir modelos (Pydantic/DTO) para:
    - `DocumentInput` (`sourceType`, `fileContent`, `plainText`).
    - `ProcessedDocument` (`rawText`, `sections`, `docType`, `docSubtype`, `simplifiedText`).
    - `LegalGuide` (`meaningForYou`, `whatToDoNow`, `whatHappensNext`, `deadlinesAndRisks`).
    - Resultados intermedios: `IngestResult`, `SegmentedDocument`, `ClassificationResult`, `SimplificationResult`, `SafetyCheckResult`, `ProcessDocumentResponse`, etc.
  - Documentar campos y tipos esperados para que el resto del equipo sepa qué usar.
  - Crear utilidades de soporte:
    - Limpieza de texto genérica.
    - Parsing básico de fechas e importes (soporte al `SafetyCheckService`).
    - Utilidades de logging comunes a todo el backend.

Colaboración clave con:
- Sebas: para encajar modelos en el endpoint.
- Lucía: para tipos de entrada/salida de los servicios y del `LLMClient`.

---

### Bloque C – LLM, OCR y servicios internos de procesamiento  
**Líder: Lucía**  
**Apoyo: Samu**

Responsable de **LLMClient**, **OCRService** y de los servicios del pipeline interno del diagrama de clases:

- Ficheros principales:
  - `backend/clients/llm_client.py`
  - `backend/clients/ocr_client.py`
  - `backend/services/ingest_service.py`
  - `backend/services/normalization_service.py`
  - `backend/services/classification_service.py`
  - `backend/services/simplification_service.py`
  - `backend/services/legal_guide_service.py`
  - `backend/services/safety_check_service.py`
- Tareas Lucía:
  - Definir la clase `LLMClient` con métodos stub:
    - `callClassifier`
    - `callSimplifier`
    - `callGuideGenerator`
    - `callVerifier`
  - Definir la clase `OCRService` con:
    - `extractTextFromImage`
    - `extractTextFromPdf`
  - Implementar la estructura de los servicios:
    - `IngestService` (`fromText`, `fromPdf`, `fromImage`).
    - `NormalizationService` (`normalizeText`, `segmentSections`).
    - `ClassificationService` (`classifyWithLLM`).
    - `SimplificationService` (`simplifyResolution`, `simplifyProceduralWriting`).
    - `LegalGuideService` (`buildGuide`).
    - `SafetyCheckService` (`ruleBasedCheck`, `llmVerification`).
  - Añadir **docstrings y TODOs** para explicar:
    - Qué prompt irá en cada llamada al LLM (sin implementarlo aún).
    - Qué entra y qué sale de cada método (usando los modelos de `schemas.py`).

- Tareas Samu:
  - Apoyar en el diseño conceptual de los prompts y el flujo de:
    - Clasificación (qué secciones se pasan al LLM).
    - Simplificación (qué información es crítica y no se puede perder).
    - Verificación (criterios de “riesgo de cambio de significado”).
  - Pensar y documentar brevemente cómo se podría evaluar la calidad del modelo en una versión futura (métricas, ideas de test).

Colaboración clave con:
- Sebas: conexión de servicios con el endpoint.
- Alex: tipos de datos y estructuras.

---

### Bloque D – Frontend y experiencia de usuario  
**Líder: Hugo**

Responsable de la clase **Frontend** del diagrama de clases:

- Ficheros principales:
  - `frontend/README.md`
  - `frontend/src/main_placeholder.js` (o TSX equivalente)
  - `frontend/src/components/UploadFormPlaceholder.jsx`
  - `frontend/src/components/DocumentViewerPlaceholder.jsx`
  - `frontend/src/components/SimplifiedTextPanelPlaceholder.jsx`
  - `frontend/src/components/LegalGuidePanelPlaceholder.jsx`
- Tareas:
  - Definir estructura y comentarios de los componentes para:
    - `uploadDocument`
    - `showOriginal`
    - `showSimplified`
    - `showLegalGuide`
  - Diseñar la distribución de pantalla:
    - Panel “Documento original”.
    - Panel “Texto simplificado”.
    - Panel “Guía jurídica” con 4 bloques fijos.
  - Dejar preparado el pseudo-código/calls para consumir `POST /process_document`.
  - Asegurar que el diseño es **responsive (mobile-first)**.
  - Apoyar en la parte visual de la presentación (capturas, mockups).

Colaboración clave con:
- Sebas: formato exacto de la respuesta JSON.
- Todo el equipo: feedback sobre UX y claridad para el ciudadano.

---

### Bloque E – Documentación, arquitectura y presentación  
**Liderazgo compartido: Sebas + Hugo**  
**Apoyo: todo el equipo**

- Ficheros principales:
  - `README.md`
  - `docs/architecture.md`
  - Presentación (fuera del repo, p. ej. `docs/slides/` si se quiere versionar).
- Tareas:
  - **Sebas**:
    - Documentar la arquitectura en `docs/architecture.md`:
      - Incluir el `flowchart` Mermaid del pipeline.
      - Incluir el `classDiagram` Mermaid con las clases definidas.
      - Describir brevemente cada etapa del flujo.
  - **Hugo**:
    - Preparar las diapositivas de la demo:
      - Problema → solución.
      - Arquitectura a alto nivel.
      - Flujo demo (subir documento → resultado).
      - Rol de cada miembro del equipo.
  - **Samu & Alex**:
    - Aportar contenido para explicar:
      - Cómo se han modelado los datos.
      - Cómo se podría medir y mejorar el sistema.
  - **Lucía**:
    - Preparar un pequeño texto/slide que explique:
      - Por qué usamos LLMs + safety check.
      - Cómo reducimos el riesgo de errores/omisiones.

---

## Plan de trabajo para la semana (resumen)

- **Día 1**
  - Generar skeleton del proyecto con Codex usando el prompt.
  - Ajustar estructura mínima (carpetas, ficheros) entre todos.

- **Día 2–3**
  - Sebas: endpoint y orquestación básica.
  - Alex: modelos en `schemas.py` + utils base.
  - Lucía + Samu: estructura de `LLMClient`, `OCRService` y servicios del pipeline.
  - Hugo: maqueta del frontend (componentes placeholder y layout).

- **Día 4–5**
  - Encadenar un “happy path” mínimo (aunque sea con mocks):
    - Subir texto sencillo → flujo completo → respuesta simulada.
  - Empezar documentación técnica y presentación.

- **Día 6–7**
  - Pulir demo y UX.
  - Preparar discurso de la presentación y ensayar.
  - Añadir, si se puede, 1–2 ejemplos reales de documentos cortos.

---
