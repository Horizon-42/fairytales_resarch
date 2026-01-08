"""Quick smoke test for the FastAPI endpoints.

Run (after server is up):
    python backend/smoke_test.py

Tips:
- If you don't have `llama3.1` pulled, pass `--model qwen3:8b` (or set OLLAMA_MODEL).
- If the request hangs, Ollama may be downloading the model on first use.

This script currently tests `/api/annotate/v2`.
For Summaries auto-generation, the backend exposes:
- POST `/api/annotate/summaries`
"""

from __future__ import annotations

import argparse
import json
import os

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for the auto-annotation backend.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "ollama"),
        help="LLM provider: ollama or gemini",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        help="Model name (Ollama model or Gemini model, depends on --provider)",
    )
    args = parser.parse_args()

    # 1) Health check
    try:
        h = requests.get(f"{args.api_base}/health", timeout=5)
        print("/health:", h.status_code, h.text.strip())
    except requests.RequestException as exc:
        print("Failed to reach backend /health:", exc)
        print("Is the server running? Try:")
        print("  conda run -n nlp python -m uvicorn backend.main:app --app-dir /home/supercomputing/studys/fairytales_resarch --host 127.0.0.1 --port 8000")
        return 2

    # 2) Annotate request
    payload = {
        "text": "Once upon a time, a poor woodcutter met a talking fish.",
        "reference_uri": "datasets/demo/story.txt",
        "culture": "Persian",
        "language": "en",
        "source_type": "story",
        "provider": args.provider,
        "thinking": bool(args.thinking),
        "model": args.model,
    }

    try:
        resp = requests.post(f"{args.api_base}/api/annotate/v2", json=payload, timeout=180)
    except requests.RequestException as exc:
        print("Request failed:", exc)
        return 3

    print("/api/annotate/v2:", "HTTP", resp.status_code)
    if resp.status_code != 200:
        print(resp.text)
        print("If this is a model-not-found error, list models with:")
        print("  curl http://127.0.0.1:11434/api/tags")
        return 1

    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
