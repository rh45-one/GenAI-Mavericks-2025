# Justice Made Clear

Citizen-friendly explanations for dense legal documents. Upload a PDF, image, or text file and Justice Made Clear handles OCR, normalization, classification, simplification, legal guidance, and safety checks to return plain-language insights plus actionable next steps.

## Why it matters

- **Accessibility:** Translates formal language into concise Spanish summaries.
- **Trust:** Uses deterministic fallos to avoid hallucinated outcomes.
- **Speed:** Orchestrates OCR + LLM stages so citizens get guidance within seconds.

## Architecture at a glance

- **Frontend (Vite + React):** Handles uploads and renders the original document, simplified summary, legal guide, and safety alerts. All legal reasoning lives on the backend.
- **Backend (FastAPI):** Exposes `POST /process_document`, chains ingestion → OCR → normalization → classification → simplification → legal guide → safety checks.
- **Services & clients:** Dedicated modules for each pipeline step plus thin wrappers around OCR and LLM vendors.
- **Shared schemas & utilities:** Pydantic DTOs, logging helpers, and text cleaning utilities keep the pipeline consistent and testable.

## Repository layout

- `frontend/` – Vite SPA with localized UI, debug-only controls, and API helpers.
- `backend/` – FastAPI app, service layer, LLM/OCR clients, prompts, scripts, and pytest suite.
- `docs/` – Architecture notes and process docs.
- `dev_env.template.txt` – Template for environment variables consumed by scripts.
- `requirements.txt` – Backend Python dependencies.

## Getting started

### Prerequisites

- Python 3.11+ and PowerShell (Windows profile already uses pwsh).
- Node.js 18+.
- (Optional) DeepSeek API credentials for live LLM calls.

### Backend setup

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `dev_env.template.txt` to `dev_env.local.txt`, then set `LLM_API_KEY` (or leave placeholder for offline mode).
3. Start the API:

   ```powershell
   python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend setup

1. Install dependencies once:

   ```powershell
   cd frontend
   npm install
   ```

2. Launch the dev server:

   ```powershell
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

3. Visit `http://localhost:5173/` (or add `?debug=true` to show the debug panels).

## Running tests

```powershell
\.venv\Scripts\python.exe -m pytest backend/tests
```

Fake LLM and OCR clients cover the pipeline end-to-end so you can run the suite without external services.

## Main user flow

1. Citizen uploads a document from the frontend.
2. Backend ingestion and OCR normalize the text and sections.
3. Classification routes the document to the proper simplification strategy.
4. LLM-based simplification and legal guide generation run sequentially.
5. Safety checks compare original vs simplified content for risky mismatches.
6. Frontend displays the simplified explanation, legal guide, and any alerts.

## Debugging & development

- **DeepSeek API configuration:** The backend targets DeepSeek's OpenAI-compatible endpoint. Copy `.env.example` to `.env` and provide placeholders or real credentials:

  ```dotenv
  DEEPSEEK_API_KEY=replace-with-deepseek-key
  DEEPSEEK_MODEL=deepseek-chat
  DEEPSEEK_BASE_URL=https://api.deepseek.com
  ```

  Leaving the placeholder will prevent outbound calls and raise a helpful error, which keeps the prototype safe during local demos without credentials.
- **Frontend debug controls:** Launch the SPA with `?debug=true` appended to the URL (for example, `http://localhost:5173/?debug=true`) to surface the quick-state buttons. These controls let you force the Home, Loading, or Output UI states without wiring backend responses, and they remain hidden unless the `debug` query string is explicitly set to `true`.
- **Frontend dev server:** Install npm dependencies (`npm install`) once inside `frontend/`, then from that same folder run:

  ```pwsh
  cd frontend
  npm run dev -- --host 127.0.0.1 --port 5173
  ```

  The explicit host/port keeps the preview reachable from other devices while avoiding port collisions.

## One-command local run (backend + frontend, with DeepSeek key)

Use the PowerShell helper to load a local env file and launch both servers in separate terminals.

### One-time per machine

```powershell
Copy-Item backend\dev_env.template.txt dev_env.local.txt
# Edit dev_env.local.txt and set LLM_API_KEY or DEEPSEEK_API_KEY.
# Optionally adjust BACKEND_PORT and VITE_API_BASE_URL.
```

### Start everything (from repo root)

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\start_stack.ps1
```

What happens:

- Reads `dev_env.local.txt` (if present) and exports the variables.
- Opens a new PowerShell window running the backend: `python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload` (uses BACKEND_PORT if set).
- Opens another window in `frontend/` running `npm install` (first run) and `npm run dev -- --host 127.0.0.1 --port 5173` (uses VITE_API_BASE_URL if set).

If the DeepSeek key is missing, the backend will exit with an error. Ensure `LLM_API_KEY` is set in `dev_env.local.txt` before launching.
