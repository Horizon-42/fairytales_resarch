"""FastAPI server that exposes auto-annotation endpoints.

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
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_model.env import load_repo_dotenv

from llm_model.annotator import AnnotatorConfig, AnnotationError, annotate_text_v2
from llm_model.character_annotator import (
    CharacterAnnotationError,
    CharacterAnnotatorConfig,
    annotate_characters,
)
from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.narrative_annotator import (
    NarrativeAnnotationError,
    NarrativeAnnotatorConfig,
    annotate_narrative_event,
)
from llm_model.narrative_segmentation import (
    NarrativeSegmentationConfig,
    NarrativeSegmentationError,
    auto_segment_to_empty_narratives,
)
from llm_model.summaries_annotator import (
    SummariesAnnotationError,
    SummariesAnnotatorConfig,
    annotate_summaries,
    annotate_single_paragraph_summary,
    annotate_whole_summary_from_per_paragraph,
)
from llm_model.text_segmentation import TextSegmenter, VisualizableTextSegmenter
from llm_model.ollama_client import embed as ollama_embed
from llm_model.ollama_client import OllamaConfig, OllamaError, list_local_models
from llm_model.vector_database import FairyVectorDB, VectorDBPaths
from llm_model.vector_database.db import QueryConfig, VectorDBNotBuiltError

# Import visualization processing functions
import sys
from pathlib import Path
# Add post_data_process to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
from post_data_process.process_json_for_viz import (
    process_story_data,
    process_directory,
    load_story_from_file,
)


# Load repo-root .env early (so running uvicorn directly still works).
load_repo_dotenv()


logger = logging.getLogger("fairytales.backend")

# Load repo-root .env if present (for GEMINI_API_KEY etc.)
load_repo_dotenv()


_VECTOR_DB: Optional[FairyVectorDB] = None

# Cached set of local Ollama model names (from GET /api/tags).
_OLLAMA_MODELS: Optional[set[str]] = None


def _refresh_ollama_models() -> Optional[set[str]]:
    """Best-effort refresh of the local Ollama model list.

    Returns None if Ollama is unreachable or returns an unexpected response.
    """

    global _OLLAMA_MODELS
    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        names = list_local_models(base_url=base_url, timeout_s=3.0)
    except OllamaError as exc:
        logger.warning("Ollama model check failed (%s): %s", base_url, exc)
        _OLLAMA_MODELS = None
        return None

    _OLLAMA_MODELS = set(names)
    return _OLLAMA_MODELS


def _ensure_ollama_model_available(*, model_name: str, purpose: str) -> None:
    """Fail fast if we know a required Ollama model is not pulled."""

    if not model_name:
        return

    # If we haven't checked yet, try once (best-effort).
    if _OLLAMA_MODELS is None:
        _refresh_ollama_models()

    if _OLLAMA_MODELS is not None and model_name not in _OLLAMA_MODELS:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Required Ollama model for {purpose} is not available locally: '{model_name}'. "
                f"Run: ollama pull {model_name}"
            ),
        )


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


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name, "1" if default else "0").strip().lower()
    return raw in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    raw = _env(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return int(default)


def _env_float(name: str, default: float) -> float:
    raw = _env(name, str(default)).strip()
    try:
        return float(raw)
    except ValueError:
        return float(default)


def _build_llm_config(*, provider: Optional[str], model: Optional[str], thinking: Optional[bool]) -> LLMConfig:
    provider_final = (provider or _env("LLM_PROVIDER", "ollama")).strip().lower()
    thinking_final = bool(thinking) if thinking is not None else _env_bool("LLM_THINKING", False)

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")

    # Per-request `model` is interpreted as the active provider's model.
    ollama_model = model if provider_final != "gemini" and model else _env("OLLAMA_MODEL", "qwen3:8b")
    gemini_model = model if provider_final == "gemini" and model else _env("GEMINI_MODEL", "")

    return LLMConfig(
        provider=provider_final,  # normalized inside llm_router
        thinking=thinking_final,
        ollama=OllamaConfig(base_url=base_url, model=ollama_model),
        gemini=GeminiConfig(
            api_key=_env("GEMINI_API_KEY", ""),
            model=gemini_model,
            model_thinking=_env("GEMINI_MODEL_THINKING", ""),
            temperature=_env_float("GEMINI_TEMPERATURE", 0.2),
            top_p=_env_float("GEMINI_TOP_P", 0.9),
            max_output_tokens=_env_int("GEMINI_MAX_OUTPUT_TOKENS", 8192),
        ),
    )


class AnnotateRequest(BaseModel):
    """Request payload from the frontend."""

    text: str = Field(..., description="Raw story/summary text")
    reference_uri: str = Field("", description="datasets/... path or other identifier")
    culture: Optional[str] = Field(None, description="Optional culture hint (e.g., Persian)")
    language: str = Field("en", description="en/zh/fa/ja/other")
    source_type: str = Field("story", description="story/summary/other")

    # Generation controls (optional)
    provider: Optional[str] = Field(None, description="LLM provider override: ollama or gemini")
    thinking: Optional[bool] = Field(None, description="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)")
    model: Optional[str] = Field(None, description="Override model name (provider-specific)")
    
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
    provider: Optional[str] = Field(None, description="LLM provider override: ollama or gemini")
    thinking: Optional[bool] = Field(None, description="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)")
    model: Optional[str] = Field(None, description="Override model name (provider-specific)")
    
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
    provider: Optional[str] = None
    thinking: Optional[bool] = None
    model: Optional[str] = None


class NarrativeAnnotateResponse(BaseModel):
    ok: bool
    event: Dict[str, Any]


class NarrativeAutoSegmentRequest(BaseModel):
    """Pre-annotation: auto-segment story text into narrative spans."""

    text: str = Field(..., description="Raw story text")
    culture: Optional[str] = Field(None, description="Optional culture hint")
    mode: Literal["llm_only", "embedding_assisted"] = Field(
        "embedding_assisted",
        description="Segmentation mode: llm_only (no embeddings) or embedding_assisted (use adjacent similarity hints)",
    )
    provider: Optional[str] = Field(None, description="LLM provider override: ollama or gemini")
    thinking: Optional[bool] = Field(None, description="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)")
    model: Optional[str] = Field(None, description="Override LLM model for segmentation (provider-specific)")
    embedding_model: Optional[str] = Field(None, description="Override embedding model (Ollama)")


class NarrativeAutoSegmentResponse(BaseModel):
    ok: bool
    narrative_events: List[Dict[str, Any]]


class SummariesAnnotateRequest(BaseModel):
    """Summaries request payload."""

    text: str = Field(..., description="Raw story text")
    language: str = Field("en", description="en/zh/fa/ja/other")
    # Generation controls
    provider: Optional[str] = Field(None, description="LLM provider override: ollama or gemini")
    thinking: Optional[bool] = Field(None, description="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)")
    model: Optional[str] = Field(None, description="Override model name (provider-specific)")


class SummariesAnnotateResponse(BaseModel):
    ok: bool
    per_paragraph: Dict[str, str]
    whole: str


class SummaryParagraphRequest(BaseModel):
    index: int = Field(..., ge=0, description="Paragraph index")
    paragraph: str = Field(..., description="Paragraph text")
    language: str = Field("en", description="en/zh/fa/ja/other")
    provider: Optional[str] = Field(None, description="LLM provider override: ollama or gemini")
    thinking: Optional[bool] = Field(None, description="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)")
    model: Optional[str] = Field(None, description="Override model name (provider-specific)")


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
    provider: Optional[str] = Field(None, description="LLM provider override: ollama or gemini")
    thinking: Optional[bool] = Field(None, description="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)")
    model: Optional[str] = Field(None, description="Override model name (provider-specific)")


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


class TextSegmentationRequest(BaseModel):
    """Request for text segmentation."""
    
    text: str = Field(..., description="Text to segment")
    sentences: Optional[List[str]] = Field(None, description="Pre-split sentences (optional)")
    algorithm: Literal["magnetic", "graph"] = Field("magnetic", description="Segmentation algorithm")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    context_window: int = Field(2, ge=1, le=5, description="Context window size")
    # Magnetic Clustering parameters
    window_size: int = Field(3, ge=1, le=10, description="Window size for Magnetic Clustering")
    filter_width: float = Field(2.0, ge=0.1, le=10.0, description="Filter width for smoothing")
    # GraphSegSM parameters
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold for GraphSegSM")
    min_seg_size: int = Field(3, ge=1, le=20, description="Minimum segment size for GraphSegSM")
    # Optional reference boundaries for evaluation
    reference_boundaries: Optional[List[int]] = Field(None, description="Ground truth boundaries for evaluation")


class TextSegmentationResponse(BaseModel):
    """Response from text segmentation."""
    
    ok: bool
    document_id: str
    segments: List[Dict[str, Any]]
    boundaries: List[int]
    meta: Dict[str, Any]
    visualization: Optional[Dict[str, Any]] = None  # Visualization data


app = FastAPI(title="Fairytales Auto-Annotation API", version="0.1.0")


class GeminiModelItem(BaseModel):
    id: str
    name: str
    display_name: str = ""
    description: str = ""
    supported_generation_methods: List[str] = []


class GeminiModelsResponse(BaseModel):
    ok: bool
    models: List[GeminiModelItem]


@app.get("/api/gemini/models", response_model=GeminiModelsResponse)
def gemini_models() -> GeminiModelsResponse:
    """List Gemini models available to the configured API key.

    This is proxied via backend to avoid exposing GEMINI_API_KEY in the browser.
    """

    api_key = _env("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is not configured")

    from llm_model.gemini_client import GeminiError, list_models

    try:
        raw_models = list_models(api_key=api_key, timeout_s=10.0)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    out: List[GeminiModelItem] = []
    for m in raw_models:
        name = str(m.get("name", "") or "").strip()
        if not name:
            continue
        model_id = name
        if model_id.startswith("models/"):
            model_id = model_id[len("models/") :]

        methods = m.get("supportedGenerationMethods")
        if not isinstance(methods, list):
            methods = []
        methods = [str(x) for x in methods if str(x)]

        # Only show models that can generate content.
        if "generateContent" not in methods:
            continue

        out.append(
            GeminiModelItem(
                id=model_id,
                name=name,
                display_name=str(m.get("displayName", "") or ""),
                description=str(m.get("description", "") or ""),
                supported_generation_methods=methods,
            )
        )

    out.sort(key=lambda x: x.id)
    return GeminiModelsResponse(ok=True, models=out)


@app.on_event("startup")
def _on_startup() -> None:
    # Uvicorn configures logging; this will show up in the server output.
    provider = _env("LLM_PROVIDER", "ollama")
    thinking = _env_bool("LLM_THINKING", False)

    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    model = _env("OLLAMA_MODEL", "qwen3:8b")
    embedding_model = _env("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:4b")
    gemini_model = _env("GEMINI_MODEL", "")
    gemini_model_thinking = _env("GEMINI_MODEL_THINKING", "")

    logger.info("Backend starting")
    logger.info("LLM: provider=%s thinking=%s", provider, thinking)
    logger.info(
        "Ollama: base_url=%s model=%s embedding_model=%s", base_url, model, embedding_model
    )
    if gemini_model or gemini_model_thinking:
        logger.info(
            "Gemini: model=%s model_thinking=%s (api_key=%s)",
            gemini_model,
            gemini_model_thinking,
            "set" if bool(_env("GEMINI_API_KEY", "")) else "missing",
        )

    models = _refresh_ollama_models()
    if models is not None:
        if model not in models:
            logger.warning("Ollama chat model not found locally: %s (run: ollama pull %s)", model, model)
        if embedding_model not in models:
            logger.warning(
                "Ollama embedding model not found locally: %s (run: ollama pull %s)",
                embedding_model,
                embedding_model,
            )


@app.on_event("shutdown")
def _on_shutdown() -> None:
    logger.info("Backend shutting down")

# CORS: allow your Vite dev servers (5177/5173/5174) and the Node save/load server.
# For dev convenience, we also allow any localhost port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5177",
        "http://localhost:5174",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_origin_regex=r"^http://localhost:\d+$",
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

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

    try:
        annotation = annotate_text_v2(
            text=req.text,
            reference_uri=req.reference_uri,
            culture=req.culture,
            language=req.language,
            source_type=req.source_type,
            existing_annotation=req.existing_annotation,
            mode=req.mode,  # type: ignore
            config=AnnotatorConfig(llm=llm_cfg),
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

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

    try:
        result = annotate_characters(
            text=req.text,
            culture=req.culture,
            existing_characters=req.existing_characters,
            mode=req.mode,  # type: ignore
            additional_prompt=req.additional_prompt,
            config=CharacterAnnotatorConfig(llm=llm_cfg),
        )
    except CharacterAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Frontend merges this into state under `motif`.
    return CharacterAnnotateResponse(ok=True, motif=result)


@app.post("/api/annotate/narrative", response_model=NarrativeAnnotateResponse)
def annotate_narrative_endpoint(req: NarrativeAnnotateRequest) -> NarrativeAnnotateResponse:
    """Extract or refine a single narrative event."""

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

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
            config=NarrativeAnnotatorConfig(llm=llm_cfg),
        )
    except NarrativeAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return NarrativeAnnotateResponse(ok=True, event=result)


@app.post("/api/narrative/auto_segment", response_model=NarrativeAutoSegmentResponse)
def auto_segment_narrative_endpoint(req: NarrativeAutoSegmentRequest) -> NarrativeAutoSegmentResponse:
    """Auto-segment a story into coherent narrative spans for later event annotation."""

    if not isinstance(req.text, str) or not req.text.strip():
        raise HTTPException(status_code=400, detail="`text` must be a non-empty string")

    default_embedding_model = _env("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:4b")

    # Fail fast when embeddings are required.
    if req.mode == "embedding_assisted":
        _ensure_ollama_model_available(
            model_name=req.embedding_model or default_embedding_model,
            purpose="embedding-assisted narrative segmentation",
        )

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

    seg_cfg = NarrativeSegmentationConfig(
        llm=llm_cfg,
        embedding_model=req.embedding_model or default_embedding_model,
    )

    try:
        events = auto_segment_to_empty_narratives(
            text=req.text,
            culture=req.culture,
            mode=req.mode,
            config=seg_cfg,
        )
    except NarrativeSegmentationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return NarrativeAutoSegmentResponse(ok=True, narrative_events=events)


@app.post("/api/annotate/summaries", response_model=SummariesAnnotateResponse)
def annotate_summaries_endpoint(req: SummariesAnnotateRequest) -> SummariesAnnotateResponse:
    """Generate per-paragraph summaries + whole-story summary for the Summaries tab."""

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

    try:
        result = annotate_summaries(
            text=req.text,
            language=req.language,
            config=SummariesAnnotatorConfig(llm=llm_cfg),
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

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

    try:
        text = annotate_single_paragraph_summary(
            index=req.index,
            paragraph=req.paragraph,
            language=req.language,
            config=SummariesAnnotatorConfig(llm=llm_cfg),
        )
    except SummariesAnnotationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SummaryParagraphResponse(ok=True, index=req.index, text=text)


@app.post("/api/annotate/summaries/whole", response_model=SummaryWholeResponse)
def annotate_summary_whole_endpoint(req: SummaryWholeRequest) -> SummaryWholeResponse:
    """Generate a whole-story summary from per-paragraph summaries."""

    llm_cfg = _build_llm_config(provider=req.provider, model=req.model, thinking=req.thinking)

    try:
        per = req.per_section or req.per_paragraph or {}
        whole = annotate_whole_summary_from_per_paragraph(
            per_paragraph=per,
            language=req.language,
            config=SummariesAnnotatorConfig(llm=llm_cfg),
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

    _ensure_ollama_model_available(
        model_name=embedding_model,
        purpose="motif/ATU retrieval embeddings",
    )

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


@app.post("/api/text/segment", response_model=TextSegmentationResponse)
def segment_text(req: TextSegmentationRequest) -> TextSegmentationResponse:
    """Segment text into semantic segments using LLM embeddings."""
    
    if not isinstance(req.text, str) or not req.text.strip():
        raise HTTPException(status_code=400, detail="`text` must be a non-empty string")
    
    base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    embedding_model = req.embedding_model or _env("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    
    _ensure_ollama_model_available(
        model_name=embedding_model,
        purpose="text segmentation embeddings",
    )
    
    # Define embedding function
    def embedding_func(texts):
        return ollama_embed(
            base_url=base_url,
            model=embedding_model,
            inputs=texts,
        )
    
    try:
        # Create visualizable segmenter to collect visualization data
        segmenter = VisualizableTextSegmenter(
            embedding_func=embedding_func,
            algorithm=req.algorithm,
            embedding_model=embedding_model,
            context_window=req.context_window,
            window_size=req.window_size,
            filter_width=req.filter_width,
            threshold=req.threshold,
            min_seg_size=req.min_seg_size,
        )
        
        # Perform segmentation
        result = segmenter.segment(
            text=req.text if not req.sentences else "",
            document_id="api_segment",
            sentences=req.sentences,
            reference_boundaries=req.reference_boundaries,
        )
        
        # Get visualization data
        viz_data = segmenter.get_visualization_data()
        
        # Convert numpy arrays and networkx graphs to JSON-serializable format
        import numpy as np
        
        visualization = {}
        if "similarity_matrix" in viz_data:
            sim_matrix = viz_data["similarity_matrix"]
            if isinstance(sim_matrix, np.ndarray):
                visualization["similarity_matrix"] = sim_matrix.tolist()
            else:
                visualization["similarity_matrix"] = sim_matrix
        
        if req.algorithm == "magnetic":
            if "raw_forces" in viz_data:
                raw_forces = viz_data["raw_forces"]
                if isinstance(raw_forces, np.ndarray):
                    visualization["raw_forces"] = raw_forces.tolist()
                else:
                    visualization["raw_forces"] = raw_forces
            if "smoothed_forces" in viz_data:
                smoothed_forces = viz_data["smoothed_forces"]
                if isinstance(smoothed_forces, np.ndarray):
                    visualization["smoothed_forces"] = smoothed_forces.tolist()
                else:
                    visualization["smoothed_forces"] = smoothed_forces
        elif req.algorithm == "graph":
            visualization["threshold"] = viz_data.get("threshold", req.threshold)
            # Graph structure is too complex to serialize, skip for now
            # Can add simplified version later if needed
        
        return TextSegmentationResponse(
            ok=True,
            document_id=result.document_id,
            segments=result.segments,
            boundaries=result.boundaries,
            meta=result.meta,
            visualization=visualization if visualization else None,
        )
    except Exception as exc:
        logger.exception("Text segmentation failed")
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(exc)}") from exc


class VisualizationProcessRequest(BaseModel):
    """Request to process visualization data from story JSON."""
    
    story_data: Dict[str, Any] = Field(..., description="Story data in json_v3 format")


class VisualizationProcessResponse(BaseModel):
    """Response with processed visualization data."""
    
    ok: bool
    relationship_data: Dict[str, Any]
    ribbon_data: Dict[str, Any]


class VisualizationProcessDirectoryRequest(BaseModel):
    """Request to process all stories in a directory."""
    
    input_dir: str = Field(..., description="Path to directory containing json_v3 files (relative to repo root)")
    output_dir: Optional[str] = Field(None, description="Optional output directory to write files")


class VisualizationProcessDirectoryResponse(BaseModel):
    """Response with all processed stories."""
    
    ok: bool
    stories: List[Dict[str, Any]]
    index: Dict[str, Any]


@app.post("/api/visualization/process", response_model=VisualizationProcessResponse)
def process_visualization(req: VisualizationProcessRequest) -> VisualizationProcessResponse:
    """Process a single story's JSON data to generate visualization data.
    
    This endpoint processes json_v3 format story data and returns:
    - relationship_data: Character graph data (nodes + edges)
    - ribbon_data: Story ribbon timeline data
    
    The frontend can use this to process stories on-the-fly without pre-generating files.
    """
    
    import time
    start_time = time.time()
    story_id = req.story_data.get("metadata", {}).get("id", "unknown")
    story_title = req.story_data.get("metadata", {}).get("title", "unknown")
    
    logger.info(
        "[VISUALIZATION] Processing story: id=%s, title=%s",
        story_id,
        story_title
    )
    
    try:
        relationship_data, ribbon_data = process_story_data(req.story_data)
        
        elapsed = time.time() - start_time
        num_characters = len(relationship_data.get("nodes", []))
        num_edges = len(relationship_data.get("edges", []))
        num_events = ribbon_data.get("total_events", 0)
        
        logger.info(
            "[VISUALIZATION] Successfully processed story: id=%s, "
            "characters=%d, edges=%d, events=%d, elapsed=%.2fs",
            story_id,
            num_characters,
            num_edges,
            num_events,
            elapsed
        )
        
        return VisualizationProcessResponse(
            ok=True,
            relationship_data=relationship_data,
            ribbon_data=ribbon_data,
        )
    except ValueError as exc:
        elapsed = time.time() - start_time
        logger.warning(
            "[VISUALIZATION] Invalid story data: id=%s, error=%s, elapsed=%.2fs",
            story_id,
            str(exc),
            elapsed
        )
        raise HTTPException(status_code=400, detail=f"Invalid story data: {str(exc)}") from exc
    except Exception as exc:
        elapsed = time.time() - start_time
        logger.exception(
            "[VISUALIZATION] Processing failed: id=%s, elapsed=%.2fs",
            story_id,
            elapsed
        )
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}") from exc


@app.post("/api/visualization/process-directory", response_model=VisualizationProcessDirectoryResponse)
def process_visualization_directory(req: VisualizationProcessDirectoryRequest) -> VisualizationProcessDirectoryResponse:
    """Process all JSON files in a directory and return visualization data.
    
    This endpoint processes all json_v3 files in a directory and returns:
    - stories: List of all processed stories with relationship and ribbon data
    - index: Metadata index for all stories
    
    Useful for batch processing or when frontend needs all stories at once.
    """
    
    # Resolve input directory (relative to repo root)
    input_path = repo_root / req.input_dir
    if not input_path.exists():
        raise HTTPException(status_code=404, detail=f"Input directory not found: {req.input_dir}")
    
    if not input_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Input path is not a directory: {req.input_dir}")
    
    # Resolve output directory if provided
    output_path = None
    if req.output_dir:
        output_path = repo_root / req.output_dir
    
    try:
        result = process_directory(str(input_path), str(output_path) if output_path else None)
        return VisualizationProcessDirectoryResponse(
            ok=True,
            stories=result["stories"],
            index=result["index"],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Directory processing failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}") from exc
