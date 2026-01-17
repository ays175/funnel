# Funnel

FastAPI backend for prompt narrowing with a two-round facet discovery flow.

## Features

- Two-round facet discovery: LLM-generated topic facets + optional refine
- Static defaults for Audience / Format / Length (single-select)
- Multi-select topic facets with “all options” support
- Trace ledger with compiled prompt + model response metadata
- GitHub Pages UI for simple static hosting

## GitHub Pages UI

1. Switch to branch `UI`.
2. In GitHub repo settings → Pages:
   - Source: branch `UI`
   - Folder: `/docs`
3. Open the Pages URL and pass your API base if needed:
   - `https://<username>.github.io/funnel/?api=https://your-api-host`

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
