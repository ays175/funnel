# Funnel

FastAPI backend for prompt narrowing with a two-round facet discovery flow.

## Features

- Two-round facet discovery: LLM-generated topic facets + optional refine
- Static defaults for Audience / Format / Length (single-select)
- Multi-select topic facets with “all options” support
- Trace ledger with compiled prompt + model response metadata
- GitHub Pages UI for simple static hosting

## Vercel UI

1. Switch to branch `UI`.
2. Deploy the repo on Vercel as a static site.
3. Set the project root to the repo root; the UI is in `public/`.
4. Pass your API base via `?api=https://your-api-host` or use the API settings panel.

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
