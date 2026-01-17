# Funnel

FastAPI backend for prompt narrowing with a two-round facet discovery flow.

## Quickstart (uv)

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

cp .env.example .env
# edit OPENAI_API_KEY

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API

- `POST /api/discover` → Round 1 facets + defaults
- `POST /api/refine` → Round 2 facets (conditional)
- `POST /api/answer` → compiled prompt + answer + trace
