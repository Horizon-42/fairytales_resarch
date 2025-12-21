"""High-level annotator that prompts Ollama and returns a Python dict.

This module is intentionally backend-agnostic: it can be used from FastAPI,
CLI scripts, notebooks, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .json_utils import loads_strict_json
from .ollama_client import OllamaConfig, OllamaError, chat
from .prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass(frozen=True)
class AnnotatorConfig:
    """Controls model choice and Ollama connection."""

    ollama: OllamaConfig = OllamaConfig()


class AnnotationError(RuntimeError):
    pass


def annotate_text_v2(
    *,
    text: str,
    reference_uri: str = "",
    culture: Optional[str] = None,
    language: str = "en",
    source_type: str = "story",
    config: AnnotatorConfig = AnnotatorConfig(),
) -> Dict[str, Any]:
    """Generate an auto-annotation compatible with the frontend v2 JSON shape.

    The caller provides the raw text; we ask the model to fill a minimal v2
    object that the UI can load as a starting point.

    Note: We keep `source_info.text_content` equal to the provided text.

    Raises:
        AnnotationError: if Ollama fails or JSON is invalid.
    """

    if not isinstance(text, str) or not text.strip():
        raise AnnotationError("`text` must be a non-empty string")

    # We embed some fields ourselves to reduce hallucination.
    # The model still returns a full JSON object, but we post-normalize.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(text=text, culture=culture)},
    ]

    try:
        raw = chat(config=config.ollama, messages=messages, response_format_json=True)
    except OllamaError as exc:
        raise AnnotationError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise AnnotationError("Model output JSON must be an object")

    # Post-normalize key fields (source_info is authoritative from caller).
    src = data.get("source_info")
    if not isinstance(src, dict):
        src = {}

    src["language"] = language or src.get("language") or "en"
    src["type"] = source_type or src.get("type") or "story"
    src["reference_uri"] = reference_uri or src.get("reference_uri") or ""
    src["text_content"] = text

    data["version"] = "2.0"
    data["source_info"] = src

    # Ensure required top-level keys exist.
    data.setdefault("characters", [])
    data.setdefault("narrative_events", [])
    data.setdefault(
        "themes_and_motifs",
        {
            "ending_type": "",
            "key_values": [],
            "motif_type": [],
            "atu_categories": [],
            "obstacle_thrower": [],
            "helper_type": [],
            "thinking_process": "",
        },
    )
    data.setdefault(
        "analysis",
        {
            "propp_functions": [],
            "propp_notes": "",
            "paragraph_summaries": {"per_paragraph": {}, "combined": [], "whole": ""},
            "bias_reflection": {
                "cultural_reading": "",
                "gender_norms": "",
                "hero_villain_mapping": "",
                "ambiguous_motifs": [],
            },
            "qa_notes": "",
        },
    )

    return data
