"""FastAPI server that exposes Ollama-powered auto-annotation endpoints.

This server is intentionally small:
- `llm_model/` contains all model/prompt/parsing logic.
- `backend/` just handles HTTP, validation, and CORS for the React frontend.

Run:
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_model.annotator import AnnotatorConfig, AnnotationError, annotate_text_v2
from llm_model.ollama_client import OllamaConfig


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None and value != "" else default


class AnnotateRequest(BaseModel):
    """Request payload from the frontend."""

    text: str = Field(..., description="Raw story/summary text")
    reference_uri: str = Field("", description="datasets/... path or other identifier")
    culture: Optional[str] = Field(None, description="Optional culture hint (e.g., Persian)")
    language: str = Field("en", description="en/zh/fa/ja/other")
    source_type: str = Field("story", description="story/summary/other")

    # Generation controls (optional)
    model: Optional[str] = Field(None, description="Override Ollama model name")


class AnnotateResponse(BaseModel):
    """Response to the frontend."""

    ok: bool
    annotation: Dict[str, Any]


app = FastAPI(title="Fairytales Auto-Annotation API", version="0.1.0")

# CORS: allow your Vite dev servers (5177/5173) and the Node save/load server.
# For dev convenience, we also allow any localhost port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5177",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_origin_regex=r"^http://localhost:\\d+$",
    allow_credentials=False,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/annotate/v2", response_model=AnnotateResponse)
def annotate_v2(req: AnnotateRequest) -> AnnotateResponse:
    """Generate a v2 JSON annotation from raw text."""

    # Build model config from environment with optional per-request override.
    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = _env("OLLAMA_MODEL", "qwen3:8b")

    ollama_cfg = OllamaConfig(
        base_url=base_url,
        model=req.model or default_model,
    )

    try:
        annotation = annotate_text_v2(
            text=req.text,
            reference_uri=req.reference_uri,
            culture=req.culture,
            language=req.language,
            source_type=req.source_type,
            config=AnnotatorConfig(ollama=ollama_cfg),
        )
    except AnnotationError as exc:
        # Return a clean 502 for "model upstream" errors.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AnnotateResponse(ok=True, annotation=annotation)
