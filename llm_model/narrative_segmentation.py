"""Narrative pre-annotation helper: automatic segmentation.

Goal:
- Split a story into narrative-friendly segments before event annotation.

Modes:
- llm_only: LLM segments using story logic only (no embedding similarity signal).
- embedding_assisted: compute embedding cosine similarity between adjacent chunks and
    provide it as a boundary hint to the LLM.

Pipeline (embedding_assisted):
1) Create initial overlapping chunks based on text length.
2) Compute embedding cosine similarity between adjacent chunks.
3) Ask an LLM (e.g., qwen3:8b) to propose final segment spans using similarity + logic.
4) Return "empty" narrative event objects with populated `text_span`.

This module is intentionally lightweight and backend-friendly.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from .json_utils import loads_strict_json
from .ollama_client import OllamaConfig, OllamaError, chat, embed


class NarrativeSegmentationError(RuntimeError):
    pass


@dataclass(frozen=True)
class NarrativeSegmentationConfig:
    ollama: OllamaConfig = OllamaConfig()

    # Embedding model used for chunk similarity.
    embedding_model: str = "qwen3-embedding:4b"

    # Chunking rule: chunk_size = max(1, int(len(text) * chunk_ratio))
    chunk_ratio: float = 0.1

    # Overlap ratio within [0.10, 0.20]. Default 0.15 (15%).
    overlap_ratio: float = 0.15


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        # Defensive: different embedding dims -> cannot compare
        return 0.0

    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += float(x) * float(y)
        na += float(x) * float(x)
        nb += float(y) * float(y)

    denom = math.sqrt(na) * math.sqrt(nb)
    if denom <= 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / denom))


def _build_overlapping_chunks(
    text: str,
    *,
    chunk_ratio: float,
    overlap_ratio: float,
) -> List[Dict[str, Any]]:
    n = len(text)
    if n == 0:
        return []

    # As requested: chunk size is 0.1 * text length.
    # For very short texts, keep at least 1 char.
    chunk_size = max(1, int(n * float(chunk_ratio)))

    # Overlap must be 10%-20% of chunk_size.
    overlap_ratio = float(overlap_ratio)
    if overlap_ratio < 0.10:
        overlap_ratio = 0.10
    if overlap_ratio > 0.20:
        overlap_ratio = 0.20

    overlap = max(1, int(chunk_size * overlap_ratio))
    step = max(1, chunk_size - overlap)

    chunks: List[Dict[str, Any]] = []
    start = 0
    idx = 0
    while start < n:
        end = min(n, start + chunk_size)
        chunk_text = text[start:end]
        chunks.append(
            {
                "index": idx,
                "start": start,
                "end": end,
                "text": chunk_text,
            }
        )
        if end >= n:
            break
        start = start + step
        idx += 1

    # Ensure we have at least 2 chunks when text is not tiny, otherwise
    # similarity list will be empty. This is fine; the LLM can still segment.
    return chunks


def _normalize_spans(spans: List[Dict[str, Any]], text_len: int) -> List[Tuple[int, int]]:
    # Accepts spans from model; returns a cleaned list of (start,end)
    cleaned: List[Tuple[int, int]] = []
    for s in spans:
        if not isinstance(s, dict):
            continue
        try:
            start = int(s.get("start"))
            end = int(s.get("end"))
        except (TypeError, ValueError):
            continue

        start = max(0, min(text_len, start))
        end = max(0, min(text_len, end))
        if end <= start:
            continue
        cleaned.append((start, end))

    if not cleaned:
        return [(0, text_len)] if text_len > 0 else []

    cleaned.sort(key=lambda x: (x[0], x[1]))

    # Force contiguous coverage (no gaps/overlaps), and cover [0, text_len].
    out: List[Tuple[int, int]] = []
    prev_end = 0
    for i, (start, end) in enumerate(cleaned):
        if i == 0:
            start = 0
        else:
            start = prev_end

        if end <= start:
            continue
        out.append((start, end))
        prev_end = end
        if prev_end >= text_len:
            break

    if out:
        s0, e0 = out[0]
        if s0 != 0:
            out[0] = (0, e0)
        sl, el = out[-1]
        if el != text_len:
            out[-1] = (sl, text_len)

    # If somehow we ended early, append tail.
    if out and out[-1][1] < text_len:
        out.append((out[-1][1], text_len))

    # Remove tiny/empty after forcing
    out2: List[Tuple[int, int]] = []
    for start, end in out:
        if end > start:
            out2.append((start, end))

    return out2


def _build_segmentation_prompt(
    *,
    text: str,
    chunks: List[Dict[str, Any]],
    adjacent_similarities: List[float],
    culture: Optional[str],
    include_similarity: bool,
) -> List[Dict[str, str]]:
    # We keep the prompt very explicit about indices and coverage.
    payload: Dict[str, Any] = {
        "text_length": len(text),
        "chunks": [
            {
                "i": c["index"],
                "start": c["start"],
                "end": c["end"],
                # Provide short preview only to save context
                "preview": (c.get("text") or "")[:200],
            }
            for c in chunks
        ],
    }

    if include_similarity and adjacent_similarities:
        payload["adjacent_similarities"] = [
            {
                "between": [i, i + 1],
                "similarity": float(adjacent_similarities[i]),
                # boundary region center hint near the overlap zone
                "boundary_hint": int(
                    chunks[i]["end"]
                    - max(1, int((chunks[i]["end"] - chunks[i]["start"]) * 0.15))
                ),
            }
            for i in range(len(adjacent_similarities))
        ]

    culture_hint = f"Culture hint: {culture}\n" if culture else ""

    system = (
        "You are a narrative segmentation assistant. "
        "You must output STRICT JSON only (no markdown, no commentary)."
    )

    similarity_instructions = (
        "You are given: (1) the full story text, (2) initial overlapping chunks and (3) embedding cosine similarities between adjacent chunks. "
        "Lower similarity often suggests a boundary; higher similarity suggests continuity, but you must also use story logic.\n\n"
        if include_similarity
        else "You are given: (1) the full story text and (2) initial overlapping chunks. Use story logic to choose boundaries.\n\n"
    )

    low_sim_line = (
        "- Choose boundaries near low-similarity points when it makes narrative sense, but do not over-segment.\n"
        if include_similarity
        else ""
    )

    user = (
        "Task: Segment the full story text into a sequence of coherent narrative segments for later narrative-event annotation.\n\n"
        + similarity_instructions
        + "IMPORTANT constraints:\n"
        + "- Output spans MUST use character indices into the full text (Python-style slicing indices).\n"
        + "- Spans MUST cover the entire text from start=0 to end=text_length with NO gaps and NO overlaps.\n"
        + "- Spans MUST be in increasing order.\n"
        + low_sim_line
        + "- Aim for segments that are usable for narrative annotation (typically multi-sentence, coherent action unit).\n\n"
        + "Return STRICT JSON with EXACTLY this schema (top-level key must be 'spans'):\n"
        + "{\n"
        + '  "spans": [\n'
        + '    {"start": 0, "end": 1234},\n'
        + "    ...\n"
        + "  ]\n"
        + "}\n\n"
        + "Do NOT output keys like 'segments', 'events', 'narrative_events', or 'boundaries'. Only output {\"spans\": [...]}\n\n"
        + f"{culture_hint}"
        + "Input signals (JSON):\n"
        + f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        + "Full story text:\n"
        + f"{text}"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def auto_segment_to_empty_narratives(
    *,
    text: str,
    culture: Optional[str] = None,
    mode: Literal["llm_only", "embedding_assisted"] = "embedding_assisted",
    config: NarrativeSegmentationConfig = NarrativeSegmentationConfig(),
) -> List[Dict[str, Any]]:
    if not isinstance(text, str) or not text.strip():
        raise NarrativeSegmentationError("`text` must be a non-empty string")

    chunks = _build_overlapping_chunks(
        text,
        chunk_ratio=config.chunk_ratio,
        overlap_ratio=config.overlap_ratio,
    )

    # Compute similarities between adjacent chunks via embeddings (optional).
    adjacent_similarities: List[float] = []
    if mode == "embedding_assisted" and len(chunks) >= 2:
        try:
            embs = embed(
                base_url=config.ollama.base_url,
                model=config.embedding_model,
                inputs=[c.get("text") or "" for c in chunks],
                timeout_s=600.0,
            )
        except OllamaError as exc:
            raise NarrativeSegmentationError(str(exc)) from exc

        for i in range(len(embs) - 1):
            adjacent_similarities.append(_cosine_similarity(embs[i], embs[i + 1]))

    # Ask the main LLM to propose final segmentation spans.
    messages = _build_segmentation_prompt(
        text=text,
        chunks=chunks,
        adjacent_similarities=adjacent_similarities,
        culture=culture,
        include_similarity=(mode == "embedding_assisted"),
    )

    try:
        raw = chat(config=config.ollama, messages=messages, response_format_json=True, timeout_s=600.0)
    except OllamaError as exc:
        raise NarrativeSegmentationError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise NarrativeSegmentationError("Model output JSON must be an object")

    spans_raw: Any = data.get("spans")

    # Be tolerant: some models ignore the schema and use different keys.
    if not isinstance(spans_raw, list):
        alt = data.get("segments")
        if isinstance(alt, list):
            spans_raw = alt
        else:
            alt_events = data.get("narrative_events")
            if isinstance(alt_events, list):
                extracted: List[Dict[str, Any]] = []
                for evt in alt_events:
                    if not isinstance(evt, dict):
                        continue
                    ts = evt.get("text_span")
                    if isinstance(ts, dict) and "start" in ts and "end" in ts:
                        extracted.append({"start": ts.get("start"), "end": ts.get("end")})
                    elif "start" in evt and "end" in evt:
                        extracted.append({"start": evt.get("start"), "end": evt.get("end")})
                if extracted:
                    spans_raw = extracted
            else:
                # Boundaries/cuts: list of indices where a new segment begins.
                boundaries = data.get("boundaries") or data.get("cuts") or data.get("split_points")
                if isinstance(boundaries, list) and all(isinstance(x, (int, float, str)) for x in boundaries):
                    pts: List[int] = []
                    for x in boundaries:
                        try:
                            pts.append(int(float(x)))
                        except (TypeError, ValueError):
                            continue
                    pts = [p for p in pts if 0 < p < len(text)]
                    pts = sorted(set(pts))
                    spans_raw = [{"start": a, "end": b} for a, b in zip([0] + pts, pts + [len(text)])]

    if not isinstance(spans_raw, list):
        keys = sorted([str(k) for k in data.keys()])
        preview = raw[:800].replace("\n", " ")
        raise NarrativeSegmentationError(
            "Model output must contain a 'spans' array. "
            f"Got keys={keys}. Raw preview: {preview}"
        )

    spans = _normalize_spans(spans_raw, len(text))

    # Convert spans to empty narrative event objects expected by frontend.
    events: List[Dict[str, Any]] = []
    for idx, (start, end) in enumerate(spans):
        span_text = text[start:end]
        events.append(
            {
                "id": str(uuid.uuid4()),
                "event_type": "",
                "description": "",
                "agents": [],
                "targets": [],
                "text_span": {"start": start, "end": end, "text": span_text},
                "target_type": "character",
                "object_type": "",
                "instrument": "",
                "time_order": idx + 1,
                "relationship_level1": "",
                "relationship_level2": "",
                "sentiment": "",
                "action_category": "",
                "action_type": "",
                "action_context": "",
                "action_status": "",
            }
        )

    return events
