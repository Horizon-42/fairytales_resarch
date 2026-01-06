"""FastAPI server that exposes Ollama-powered auto-annotation endpoints.

This server is intentionally small:
- `llm_model/` contains all model/prompt/parsing logic.
- `backend/` just handles HTTP, validation, and CORS for the React frontend.

Run:
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_model.annotator import AnnotatorConfig, AnnotationError, annotate_text_v2
from llm_model.character_annotator import (
    CharacterAnnotationError,
    CharacterAnnotatorConfig,
    annotate_characters,
)
from llm_model.narrative_annotator import (
    NarrativeAnnotationError,
    NarrativeAnnotatorConfig,
    annotate_narrative_event,
)
from llm_model.summaries_annotator import (
    SummariesAnnotationError,
    SummariesAnnotatorConfig,
    annotate_summaries,
    annotate_single_paragraph_summary,
    annotate_whole_summary_from_per_paragraph,
)
from llm_model.ollama_client import OllamaConfig


logger = logging.getLogger("fairytales.backend")


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
    
    # Incremental annotation (optional)
    existing_annotation: Optional[Dict[str, Any]] = Field(
        None, description="Existing annotation for incremental annotation"
    )
    mode: str = Field(
        "recreate", description="Annotation mode: supplement, modify, or recreate"
    )


class AnnotateResponse(BaseModel):
    """Response to the frontend."""

    ok: bool
    annotation: Dict[str, Any]


class CharacterAnnotateRequest(BaseModel):
    """Character-only request payload.

    This is meant to (re)fill the Characters tab without touching other fields.
    """

    text: str = Field(..., description="Raw story/summary text")
    culture: Optional[str] = Field(None, description="Optional culture hint (e.g., Persian)")
    # Generation controls (optional)
    model: Optional[str] = Field(None, description="Override Ollama model name")
    
    # Incremental annotation (optional)
    existing_characters: Optional[Dict[str, Any]] = Field(
        None, description="Existing character annotation for incremental annotation"
    )
    mode: str = Field(
        "recreate", description="Annotation mode: supplement, modify, or recreate"
    )
    additional_prompt: Optional[str] = Field(
        None, description="Additional instructions for the annotation model"
    )


class CharacterAnnotateResponse(BaseModel):
    ok: bool
    motif: Dict[str, Any]


class NarrativeAnnotateRequest(BaseModel):
    """Narrative-only request payload for a single event."""

    narrative_id: str
    text_span: Dict[str, Any]
    narrative_text: str
    character_list: List[str]
    culture: Optional[str] = None
    existing_event: Optional[Dict[str, Any]] = None
    history_events: Optional[List[Dict[str, Any]]] = None
    mode: str = "recreate"
    additional_prompt: Optional[str] = None
    # Generation controls
    model: Optional[str] = None


class NarrativeAnnotateResponse(BaseModel):
    ok: bool
    event: Dict[str, Any]


class SummariesAnnotateRequest(BaseModel):
    """Summaries request payload."""

    text: str = Field(..., description="Raw story text")
    language: str = Field("en", description="en/zh/fa/ja/other")
    # Generation controls
    model: Optional[str] = Field(None, description="Override Ollama model name")


class SummariesAnnotateResponse(BaseModel):
    ok: bool
    per_paragraph: Dict[str, str]
    whole: str


class SummaryParagraphRequest(BaseModel):
    index: int = Field(..., ge=0, description="Paragraph index")
    paragraph: str = Field(..., description="Paragraph text")
    language: str = Field("en", description="en/zh/fa/ja/other")
    model: Optional[str] = Field(None, description="Override Ollama model name")


class SummaryParagraphResponse(BaseModel):
    ok: bool
    index: int
    text: str


class SummaryWholeRequest(BaseModel):
    per_paragraph: Dict[str, str] = Field(..., description="Map of paragraph index to summary")
    language: str = Field("en", description="en/zh/fa/ja/other")
    model: Optional[str] = Field(None, description="Override Ollama model name")


class SummaryWholeResponse(BaseModel):
    ok: bool
    whole: str


app = FastAPI(title="Fairytales Auto-Annotation API", version="0.1.0")


@app.on_event("startup")
def _on_startup() -> None:
    # Uvicorn configures logging; this will show up in the server output.
    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    model = _env("OLLAMA_MODEL", "qwen3:8b")
    logger.info("Backend starting")
    logger.info("Ollama: base_url=%s model=%s", base_url, model)


@app.on_event("shutdown")
def _on_shutdown() -> None:
    logger.info("Backend shutting down")

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
            existing_annotation=req.existing_annotation,
            mode=req.mode,  # type: ignore
            config=AnnotatorConfig(ollama=ollama_cfg),
        )
    except AnnotationError as exc:
        # Return a clean 502 for "model upstream" errors.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AnnotateResponse(ok=True, annotation=annotation)


@app.post("/api/annotate/characters", response_model=CharacterAnnotateResponse)
def annotate_characters_endpoint(req: CharacterAnnotateRequest) -> CharacterAnnotateResponse:
    """Extract character archetypes for the Characters tab.

    Returns a `motif` object with keys:
    - character_archetypes: [{name, alias, archetype}]
    - helper_type: [string]
    - obstacle_thrower: [string]
    """

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = _env("OLLAMA_MODEL", "qwen3:8b")

    ollama_cfg = OllamaConfig(
        base_url=base_url,
        model=req.model or default_model,
    )

    try:
        result = annotate_characters(
            text=req.text,
            culture=req.culture,
            existing_characters=req.existing_characters,
            mode=req.mode,  # type: ignore
            additional_prompt=req.additional_prompt,
            config=CharacterAnnotatorConfig(ollama=ollama_cfg),
        )
    except CharacterAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Frontend merges this into state under `motif`.
    return CharacterAnnotateResponse(ok=True, motif=result)


@app.post("/api/annotate/narrative", response_model=NarrativeAnnotateResponse)
def annotate_narrative_endpoint(req: NarrativeAnnotateRequest) -> NarrativeAnnotateResponse:
    """Extract or refine a single narrative event."""

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = _env("OLLAMA_MODEL", "qwen3:8b")

    ollama_cfg = OllamaConfig(
        base_url=base_url,
        model=req.model or default_model,
    )

    try:
        result = annotate_narrative_event(
            narrative_id=req.narrative_id,
            text_span=req.text_span,
            narrative_text=req.narrative_text,
            character_list=req.character_list,
            culture=req.culture,
            existing_event=req.existing_event,
            history_events=req.history_events,
            mode=req.mode,  # type: ignore
            additional_prompt=req.additional_prompt,
            config=NarrativeAnnotatorConfig(ollama=ollama_cfg),
        )
    except NarrativeAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return NarrativeAnnotateResponse(ok=True, event=result)


@app.post("/api/annotate/summaries", response_model=SummariesAnnotateResponse)
def annotate_summaries_endpoint(req: SummariesAnnotateRequest) -> SummariesAnnotateResponse:
    """Generate per-paragraph summaries + whole-story summary for the Summaries tab."""

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = _env("OLLAMA_MODEL", "qwen3:8b")

    ollama_cfg = OllamaConfig(
        base_url=base_url,
        model=req.model or default_model,
    )

    try:
        result = annotate_summaries(
            text=req.text,
            language=req.language,
            config=SummariesAnnotatorConfig(ollama=ollama_cfg),
        )
    except SummariesAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SummariesAnnotateResponse(
        ok=True,
        per_paragraph=result.get("per_paragraph", {}) or {},
        whole=result.get("whole", "") or "",
    )


@app.post("/api/annotate/summaries/paragraph", response_model=SummaryParagraphResponse)
def annotate_summary_paragraph_endpoint(req: SummaryParagraphRequest) -> SummaryParagraphResponse:
    """Generate a summary for one paragraph (used for incremental UI updates)."""

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = _env("OLLAMA_MODEL", "qwen3:8b")

    ollama_cfg = OllamaConfig(
        base_url=base_url,
        model=req.model or default_model,
    )

    try:
        text = annotate_single_paragraph_summary(
            index=req.index,
            paragraph=req.paragraph,
            language=req.language,
            config=SummariesAnnotatorConfig(ollama=ollama_cfg),
        )
    except SummariesAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SummaryParagraphResponse(ok=True, index=req.index, text=text)


@app.post("/api/annotate/summaries/whole", response_model=SummaryWholeResponse)
def annotate_summary_whole_endpoint(req: SummaryWholeRequest) -> SummaryWholeResponse:
    """Generate a whole-story summary from per-paragraph summaries."""

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = _env("OLLAMA_MODEL", "qwen3:8b")

    ollama_cfg = OllamaConfig(
        base_url=base_url,
        model=req.model or default_model,
    )

    try:
        whole = annotate_whole_summary_from_per_paragraph(
            per_paragraph=req.per_paragraph,
            language=req.language,
            config=SummariesAnnotatorConfig(ollama=ollama_cfg),
        )
    except SummariesAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SummaryWholeResponse(ok=True, whole=whole)
