"""High-level annotator that prompts Ollama and returns a Python dict.

This module is intentionally backend-agnostic: it can be used from FastAPI,
CLI scripts, notebooks, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

from .json_utils import loads_strict_json
from .llm_router import LLMConfig, LLMRouterError, chat
from .prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass(frozen=True)
class AnnotatorConfig:
    """Controls model choice and LLM provider."""

    llm: LLMConfig = LLMConfig()


class AnnotationError(RuntimeError):
    pass


def annotate_text_v2(
    *,
    text: str,
    reference_uri: str = "",
    culture: Optional[str] = None,
    language: str = "en",
    source_type: str = "story",
    existing_annotation: Optional[Dict[str, Any]] = None,
    mode: Literal["supplement", "modify", "recreate"] = "recreate",
    config: AnnotatorConfig = AnnotatorConfig(),
) -> Dict[str, Any]:
    """Generate an auto-annotation compatible with the frontend v2 JSON shape.

    The caller provides the raw text; we ask the model to fill a minimal v2
    object that the UI can load as a starting point.

    Args:
        text: The story text to annotate.
        reference_uri: Optional reference URI for the source.
        culture: Optional culture hint for the model.
        language: Language tag (default: "en").
        source_type: Source type tag (default: "story").
        existing_annotation: Optional existing annotation to use as base.
        mode: Annotation mode:
            - "supplement": Add missing fields, keep existing ones unchanged
            - "modify": Update and improve existing fields, may add new ones
            - "recreate": Ignore existing annotation, generate from scratch
        config: Annotator configuration.

    Note: We keep `source_info.text_content` equal to the provided text.

    Raises:
        AnnotationError: if Ollama fails or JSON is invalid.
    """

    if not isinstance(text, str) or not text.strip():
        raise AnnotationError("`text` must be a non-empty string")

    if existing_annotation is not None and mode == "recreate":
        existing_annotation = None  # Ignore existing annotation in recreate mode

    # We embed some fields ourselves to reduce hallucination.
    # The model still returns a full JSON object, but we post-normalize.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(
                text=text, culture=culture, existing_annotation=existing_annotation, mode=mode
            ),
        },
    ]

    try:
        raw = chat(config=config.llm, messages=messages, response_format_json=True)
    except LLMRouterError as exc:
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

    # Merge with existing annotation based on mode
    if existing_annotation is not None and mode in ("supplement", "modify"):
        data = _merge_annotations(data, existing_annotation, mode)

    return data


def _merge_annotations(
    new_data: Dict[str, Any], existing_data: Dict[str, Any], mode: Literal["supplement", "modify"]
) -> Dict[str, Any]:
    """Merge new annotation with existing annotation based on mode.

    Args:
        new_data: The newly generated annotation.
        existing_data: The existing annotation to merge with.
        mode: "supplement" keeps existing, adds missing; "modify" updates existing.

    Returns:
        Merged annotation dictionary.
    """
    result = existing_data.copy() if mode == "supplement" else {}

    # Merge source_info (always use new for text_content, but preserve other fields in supplement mode)
    if mode == "supplement":
        result["source_info"] = existing_data.get("source_info", {}).copy()
        result["source_info"].update(new_data.get("source_info", {}))
    else:  # modify mode
        result["source_info"] = new_data.get("source_info", {})

    # Merge characters
    if mode == "supplement":
        existing_chars = {c.get("name", ""): c for c in existing_data.get("characters", [])}
        new_chars = {c.get("name", ""): c for c in new_data.get("characters", [])}
        # Keep existing, add new ones that don't exist
        result["characters"] = list(existing_chars.values())
        for name, char in new_chars.items():
            if name and name not in existing_chars:
                result["characters"].append(char)
    else:  # modify mode
        result["characters"] = new_data.get("characters", [])

    # Merge narrative_events
    if mode == "supplement":
        existing_events = {e.get("id", ""): e for e in existing_data.get("narrative_events", [])}
        new_events = {e.get("id", ""): e for e in new_data.get("narrative_events", [])}
        # Keep existing, add new ones that don't exist
        result["narrative_events"] = list(existing_events.values())
        for event_id, event in new_events.items():
            if event_id and event_id not in existing_events:
                result["narrative_events"].append(event)
    else:  # modify mode
        result["narrative_events"] = new_data.get("narrative_events", [])

    # Merge themes_and_motifs
    if mode == "supplement":
        existing_motifs = existing_data.get("themes_and_motifs", {})
        new_motifs = new_data.get("themes_and_motifs", {})
        result["themes_and_motifs"] = existing_motifs.copy()
        # For lists, add new items that don't exist
        for key in ["key_values", "motif_type", "atu_categories", "obstacle_thrower", "helper_type"]:
            existing_list = existing_motifs.get(key, [])
            new_list = new_motifs.get(key, [])
            combined = list(existing_list)
            for item in new_list:
                if item not in combined:
                    combined.append(item)
            result["themes_and_motifs"][key] = combined
        # For strings, use new if existing is empty
        for key in ["ending_type", "thinking_process"]:
            if not existing_motifs.get(key):
                result["themes_and_motifs"][key] = new_motifs.get(key, "")
    else:  # modify mode
        result["themes_and_motifs"] = new_data.get("themes_and_motifs", {})

    # Merge analysis
    if mode == "supplement":
        existing_analysis = existing_data.get("analysis", {})
        new_analysis = new_data.get("analysis", {})
        result["analysis"] = existing_analysis.copy()
        # Merge propp_functions (keep existing, add new)
        existing_propp = {f.get("fn", ""): f for f in existing_analysis.get("propp_functions", [])}
        new_propp = {f.get("fn", ""): f for f in new_analysis.get("propp_functions", [])}
        result["analysis"]["propp_functions"] = list(existing_propp.values())
        for fn, func in new_propp.items():
            if fn and fn not in existing_propp:
                result["analysis"]["propp_functions"].append(func)
        # For strings, use new if existing is empty
        for key in ["propp_notes", "qa_notes"]:
            if not existing_analysis.get(key):
                result["analysis"][key] = new_analysis.get(key, "")
        # Merge paragraph_summaries (keep existing, add new)
        existing_para = existing_analysis.get("paragraph_summaries", {})
        new_para = new_analysis.get("paragraph_summaries", {})
        result["analysis"]["paragraph_summaries"] = existing_para.copy()
        if "per_paragraph" in new_para:
            result["analysis"]["paragraph_summaries"]["per_paragraph"] = {
                **existing_para.get("per_paragraph", {}),
                **new_para.get("per_paragraph", {}),
            }
        # Merge bias_reflection
        existing_bias = existing_analysis.get("bias_reflection", {})
        new_bias = new_analysis.get("bias_reflection", {})
        result["analysis"]["bias_reflection"] = existing_bias.copy()
        for key in ["cultural_reading", "gender_norms", "hero_villain_mapping"]:
            if not existing_bias.get(key):
                result["analysis"]["bias_reflection"][key] = new_bias.get(key, "")
        # Merge ambiguous_motifs list
        existing_ambiguous = existing_bias.get("ambiguous_motifs", [])
        new_ambiguous = new_bias.get("ambiguous_motifs", [])
        combined_ambiguous = list(existing_ambiguous)
        for item in new_ambiguous:
            if item not in combined_ambiguous:
                combined_ambiguous.append(item)
        result["analysis"]["bias_reflection"]["ambiguous_motifs"] = combined_ambiguous
    else:  # modify mode
        result["analysis"] = new_data.get("analysis", {})

    # Ensure version is set
    result["version"] = new_data.get("version", "2.0")

    return result
