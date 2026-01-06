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
from pathlib import Path
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
from llm_model.vector_database import FairyVectorDB, VectorDBPaths
from llm_model.vector_database.db import QueryConfig, VectorDBNotBuiltError


logger = logging.getLogger("fairytales.backend")


_VECTOR_DB: Optional[FairyVectorDB] = None


def _get_vector_db() -> FairyVectorDB:
    global _VECTOR_DB
    if _VECTOR_DB is not None:
        return _VECTOR_DB

    # Allow overriding the store directory (defaults to llm_model/vector_database/store)
    store_dir = _env("VECTOR_DB_DIR", "")
    paths = VectorDBPaths(root_dir=Path(store_dir)) if store_dir else None

    db = FairyVectorDB(paths=paths)
    db.load()
    _VECTOR_DB = db
    return db


def _format_atu_label(meta: Dict[str, Any]) -> str:
    num = (meta.get("atu_number") or "").strip()
    title = (meta.get("title") or "").strip()
    l1 = (meta.get("level_1_category") or "").strip()
    l2 = (meta.get("level_2_category") or "").strip()
    l3 = (meta.get("level_3_category") or "").strip()
    rng = (meta.get("category_range") or "").strip()

    parts = [p for p in [l1, l2, l3] if p]
    path = " > ".join(parts)
    if rng:
        path = f"{path} ({rng})" if path else f"({rng})"

    core = f"ATU {num}: {title}" if title else f"ATU {num}"
    return f"{core} ({path})" if path else core


def _format_motif_label(meta: Dict[str, Any]) -> str:
    code = (meta.get("code") or "").strip()
    motif = (meta.get("motif") or "").strip()
    chapter = (meta.get("chapter") or "").strip()
    d1 = (meta.get("division1") or "").strip()
    d2 = (meta.get("division2") or "").strip()
    d3 = (meta.get("division3") or "").strip()

    path_parts = [p for p in [chapter, d1, d2, d3] if p]
    path = " > ".join(path_parts)

    core = f"Motif {code}: {motif}" if motif else f"Motif {code}"
    return f"{core} ({path})" if path else core


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
    per_paragraph: Optional[Dict[str, str]] = Field(
        None, description="Map of paragraph index to summary (legacy)"
    )
    per_section: Optional[Dict[str, str]] = Field(
        None, description="Map of text_section to summary (preferred)"
    )
    language: str = Field("en", description="en/zh/fa/ja/other")
    model: Optional[str] = Field(None, description="Override Ollama model name")


class SummaryWholeResponse(BaseModel):
    ok: bool
    whole: str


class MotifAtuDetectRequest(BaseModel):
    text: str = Field(..., description="Story text or summaries to use for retrieval")
    top_k: int = Field(10, ge=1, le=50, description="Top-k neighbors per chunk")
    embedding_model: Optional[str] = Field(None, description="Override embedding model (Ollama)")


class MotifAtuDetectItem(BaseModel):
    label: str
    similarity: float
    doc_key: str


class MotifAtuDetectResponse(BaseModel):
    ok: bool
    atu: List[MotifAtuDetectItem]
    motifs: List[MotifAtuDetectItem]
    chunks: int


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
        per = req.per_section or req.per_paragraph or {}
        whole = annotate_whole_summary_from_per_paragraph(
            per_paragraph=per,
            language=req.language,
            config=SummariesAnnotatorConfig(ollama=ollama_cfg),
        )
    except SummariesAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SummaryWholeResponse(ok=True, whole=whole)


@app.post("/api/detect/motif_atu", response_model=MotifAtuDetectResponse)
def detect_motif_atu(req: MotifAtuDetectRequest) -> MotifAtuDetectResponse:
    """Detect likely ATU types and motifs using the local vector database."""

    if not isinstance(req.text, str) or not req.text.strip():
        raise HTTPException(status_code=400, detail="`text` must be a non-empty string")

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    embedding_model = req.embedding_model or _env("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:4b")

    try:
        db = _get_vector_db()
        result = db.detect(
            text=req.text,
            config=QueryConfig(
                ollama_base_url=base_url,
                embedding_model=embedding_model,
                top_k=int(req.top_k),
            ),
        )
    except VectorDBNotBuiltError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    atu_items: List[MotifAtuDetectItem] = []
    for item in (result.get("atu") or [])[:10]:
        meta = item.get("metadata") or {}
        label = _format_atu_label(meta)
        atu_items.append(
            MotifAtuDetectItem(
                label=label,
                similarity=float(item.get("similarity") or 0.0),
                doc_key=str(item.get("doc_key") or ""),
            )
        )

    motif_items: List[MotifAtuDetectItem] = []
    for item in (result.get("motifs") or [])[:10]:
        meta = item.get("metadata") or {}
        label = _format_motif_label(meta)
        motif_items.append(
            MotifAtuDetectItem(
                label=label,
                similarity=float(item.get("similarity") or 0.0),
                doc_key=str(item.get("doc_key") or ""),
            )
        )

    return MotifAtuDetectResponse(
        ok=True,
        atu=atu_items,
        motifs=motif_items,
        chunks=int(result.get("chunks") or 0),
    )
