# Backend (FastAPI)

This directory runs the auto-annotation API that the React tool can call.

## Prereqs

- Ollama installed + running (default: `http://localhost:11434`)
- A model pulled, e.g. `ollama pull llama3.1`

## Install

```bash
cd /home/supercomputing/studys/fairytales_resarch/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd /home/supercomputing/studys/fairytales_resarch
source backend/.venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run using conda env `nlp`

If you prefer your existing conda env:

```bash
cd /home/supercomputing/studys/fairytales_resarch
conda run -n nlp python -m pip install -r backend/requirements.txt

# IMPORTANT: ensure the model name exists in `ollama list`.
# Example uses a model seen on many setups; replace with yours.
conda run -n nlp env OLLAMA_MODEL='qwen3:8b' \
  python -m uvicorn backend.main:app \
  --app-dir /home/supercomputing/studys/fairytales_resarch \
  --host 127.0.0.1 --port 8000
```

## Environment variables

- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `llama3.1`)

## API

- `GET /health`
- `POST /api/annotate/v2`

Example:

```bash
curl -s http://localhost:8000/api/annotate/v2 \
  -H 'Content-Type: application/json' \
  -d '{"text":"Once upon a time...","reference_uri":"datasets/...","culture":"Persian"}' | jq
```
