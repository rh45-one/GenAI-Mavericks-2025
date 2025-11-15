# Justice Made Clear – Frontend

Vite + React single-page app that talks to the FastAPI backend. The MVP focuses on:
- Uploading text or a file to `POST /process_document`.
- Rendering the simplified explanation, four-block legal guide, and original text preview.
- Highlighting safety warnings returned by the backend.

## Quick start

```pwsh
cd frontend
npm install
npm run dev
```

The dev server prints a localhost URL (defaults to `http://localhost:5173`).

## Configuration

- `VITE_API_BASE_URL` (optional): target backend base URL (defaults to `http://localhost:8000`). Create a `.env` file in this folder if you need to override it.

## Available scripts

- `npm run dev` – start Vite dev server with hot reload.
- `npm run build` – create the production bundle in `dist/`.
- `npm run preview` – serve the build locally for smoke testing.

## Next steps

- Swap placeholders with production components (document rendering, drag-and-drop uploader, etc.).
- Add routing/state management if the workflow grows beyond a single screen.
- Connect auth + analytics once backend endpoints exist.
