# Justice Made Clear – Empowering the citizens

Justice Made Clear is a one-week prototype that helps citizens understand legal documents. A user uploads a PDF, image, or text file, and the system orchestrates OCR, normalization, LLM-based classification, simplification, legal guide generation, and safety checks. The result is citizen-friendly text plus actionable guidance and warnings.

## Architecture overview
- **Frontend (presentation layer):** Upload form + panels for original text, simplified summary, and legal guide. It never applies legal logic and simply calls the backend API.
- **Backend API & orchestrator:** FastAPI service exposing `POST /process_document`, sequencing every pipeline step.
- **Internal processing services:** Ingestion, normalization, classification, simplification, legal guide building, and safety checking.
- **External service clients:** Thin wrappers over OCR providers and LLM APIs.
- **Shared models & utilities:** DTOs and helper modules to keep the pipeline consistent and testable.

## Repository layout
- `frontend/` – Placeholder SPA scaffolding, ready for the UI team.
- `backend/` – FastAPI skeleton plus services, clients, schemas, and utilities.
- `docs/` – Architecture and process documentation.
- `.env.example` – Sample environment configuration.
- `requirements.txt` – Python dependencies for the backend.

## Main user flow
1. Citizen uploads a document through the frontend.
2. Frontend sends the payload to `POST /process_document`.
3. Backend ingestion + OCR produce normalized text and sections.
4. LLM classification, simplification, and legal guide generation run in order.
5. Safety checks compare the original and simplified outputs.
6. Frontend displays the original document, simplified explanation, four-block guide, and warnings if any.

## Debugging & development
- **DeepSeek API configuration:** The backend now targets DeepSeek's OpenAI-compatible endpoint. Copy `.env.example` to `.env` and provide placeholders or real credentials:

	```dotenv
	DEEPSEEK_API_KEY=replace-with-deepseek-key
	DEEPSEEK_MODEL=deepseek-chat
	DEEPSEEK_BASE_URL=https://api.deepseek.com
	```

	Leaving the placeholder value will prevent outbound calls and raises a helpful error, which keeps the prototype safe during local demos without credentials.
- **Frontend debug controls:** Launch the SPA with `?debug=true` appended to the URL (for example, `http://localhost:5173/?debug=true`) to surface the quick-state buttons. These controls let you force the Home, Loading, or Output UI states without wiring backend responses, and they remain hidden unless the `debug` query string is explicitly set to `true`.
- **Frontend dev server:** Install npm dependencies (`npm install`) once inside `frontend/`, then from that same folder run:

	```pwsh
	cd frontend
	npm run dev -- --host 127.0.0.1 --port 5173
	```

	The explicit host/port keeps the preview reachable from other devices (or Codespaces) while avoiding port collisions.
