# Funnel

FastAPI backend for prompt narrowing with a two-round facet discovery flow.

## Features

- Two-round facet discovery: LLM-generated topic facets + optional refine
- Static defaults for Audience / Format / Length (single-select)
- Multi-select topic facets with “all options” support
- Trace ledger with compiled prompt + model response metadata
- GitHub Pages UI for simple static hosting

## Railway Deployment (API + UI)

The UI is served from `public/index.html` by the FastAPI app at `/` (and `/ui`).

1. Create a new Railway service from this repo (branch `main`).
2. Set environment variables:
   - `OPENAI_API_KEY=...`
   - `CORS_ORIGINS=https://<your-railway-domain>`
3. Start command:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Open your Railway URL:
   - UI: `https://<your-railway-domain>/`
   - API: `https://<your-railway-domain>/api/discover`

## Quickstart (uv)

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

cp .env.example .env
# edit OPENAI_API_KEY

uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## API

- `POST /api/discover` → Round 1 facets + defaults
- `POST /api/refine` → Round 2 facets (conditional)
- `POST /api/answer` → compiled prompt + answer + trace
