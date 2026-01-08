"""Narrative event annotation API.

v3-first: the model returns nested structures:
- `relationships`: list of {agent, target, relationship_level1, relationship_level2, sentiment}
- `action_layer`: {category, type, context, status, function}

The frontend UI still edits a flat internal shape, but we keep the LLM output in v3
to match the exported JSON format.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from .json_utils import loads_strict_json
from .narrative_prompts import SYSTEM_PROMPT_NARRATIVE, build_narrative_user_prompt
from .llm_router import LLMConfig, LLMRouterError, chat


@dataclass(frozen=True)
class NarrativeAnnotatorConfig:
    """Controls model choice and LLM provider."""

    llm: LLMConfig = LLMConfig()


class NarrativeAnnotationError(RuntimeError):
    pass


def annotate_narrative_event(
    *,
    narrative_id: str,
    text_span: Dict[str, Any],
    narrative_text: str,
    character_list: List[str],
    culture: Optional[str] = None,
    existing_event: Optional[Dict[str, Any]] = None,
    history_events: Optional[List[Dict[str, Any]]] = None,
    mode: Literal["supplement", "modify", "recreate"] = "recreate",
    additional_prompt: Optional[str] = None,
    config: NarrativeAnnotatorConfig = NarrativeAnnotatorConfig(),
) -> Dict[str, Any]:
    """Annotate a single narrative event within a story.

    Args:
        narrative_id: The ID for this narrative event.
        text_span: The text span information {start, end, text}.
        narrative_text: The full narrative text providing context.
        character_list: List of available character names.
        culture: Optional culture hint.
        existing_event: Optional existing event annotation to use as base.
        history_events: Optional list of previous events for context.
        mode: Annotation mode ("supplement", "modify", or "recreate").
        additional_prompt: Optional additional instructions from the user.
        config: Narrative annotator configuration.

    Returns a dict representing the narrative event.

    Raises:
        NarrativeAnnotationError: on model/JSON failure.
    """

    if not isinstance(narrative_text, str) or not narrative_text.strip():
        raise NarrativeAnnotationError("`narrative_text` must be a non-empty string")

    if existing_event is not None and mode == "recreate":
        existing_event = None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_NARRATIVE},
        {
            "role": "user",
            "content": build_narrative_user_prompt(
                narrative_id=narrative_id,
                text_span=text_span,
                narrative_text=narrative_text,
                character_list=character_list,
                culture=culture,
                existing_event=existing_event,
                history_events=history_events,
                mode=mode,
                additional_prompt=additional_prompt,
            ),
        },
    ]

    try:
        raw = chat(config=config.llm, messages=messages, response_format_json=True)
    except LLMRouterError as exc:
        raise NarrativeAnnotationError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise NarrativeAnnotationError("Model output JSON must be an object")

    # Normalize output to ensure it matches the expected schema
    result = _normalize_event_data(data, narrative_id, text_span)

    # Merge with existing event if needed
    if existing_event is not None and mode in ("supplement", "modify"):
        result = _merge_event_annotations(result, existing_event, mode)

    return result


def _normalize_event_data(data: Dict[str, Any], narrative_id: str, text_span: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the model output matches the v3 narrative event schema."""
    
    # Force ID and text_span to match input if model deviated
    data["id"] = narrative_id
    data["text_span"] = text_span
    
    # Ensure lists are lists
    for key in ["agents", "targets"]:
        if not isinstance(data.get(key), list):
            data[key] = [str(data.get(key))] if data.get(key) else []
        else:
            data[key] = [str(x) for x in data.get(key) if str(x).strip()]

    # Ensure standard string fields exist
    string_fields = [
        "event_type",
        "description",
        "target_type",
        "object_type",
        "instrument",
    ]
    for field in string_fields:
        if field not in data:
            data[field] = ""
        else:
            data[field] = str(data[field])

    # Normalize relationships (v3)
    rels_raw = data.get("relationships")
    if not isinstance(rels_raw, list):
        rels_raw = []
    rels: List[Dict[str, str]] = []
    for r in rels_raw:
        if not isinstance(r, dict):
            continue
        rels.append(
            {
                "agent": str(r.get("agent", "")),
                "target": str(r.get("target", "")),
                "relationship_level1": str(r.get("relationship_level1", r.get("level1", ""))),
                "relationship_level2": str(r.get("relationship_level2", r.get("level2", ""))),
                "sentiment": str(r.get("sentiment", "")),
            }
        )
    data["relationships"] = rels

    # Normalize action_layer (v3)
    al_raw = data.get("action_layer")
    if not isinstance(al_raw, dict):
        al_raw = {}
    data["action_layer"] = {
        "category": str(al_raw.get("category", "")),
        "type": str(al_raw.get("type", "")),
        "context": str(al_raw.get("context", "")),
        "status": str(al_raw.get("status", "")),
        "function": str(al_raw.get("function", al_raw.get("narrative_function", data.get("narrative_function", "")))),
    }

    # Ensure time_order is int
    try:
        data["time_order"] = int(data.get("time_order", 0))
    except (ValueError, TypeError):
        data["time_order"] = 0

    # Return only the expected v3 keys (keeps output stable)
    return {
        "id": data.get("id", narrative_id),
        "text_span": data.get("text_span", text_span),
        "event_type": data.get("event_type", ""),
        "description": data.get("description", ""),
        "agents": data.get("agents", []),
        "targets": data.get("targets", []),
        "target_type": data.get("target_type", ""),
        "object_type": data.get("object_type", ""),
        "instrument": data.get("instrument", ""),
        "relationships": data.get("relationships", []),
        "action_layer": data.get("action_layer", {}),
        "time_order": data.get("time_order", 0),
    }


def _merge_event_annotations(
    new_data: Dict[str, Any], existing_data: Dict[str, Any], mode: Literal["supplement", "modify"]
) -> Dict[str, Any]:
    """Merge new event annotation with existing one."""
    if mode == "modify":
        # In modify mode, we generally trust the new generation but can fallback if needed.
        # For now, we simple return the new data as it was prompted to improve the old one.
        return new_data
    
    # supplement mode: keep existing non-empty values
    result = existing_data.copy()

    for key, value in new_data.items():
        existing_val = result.get(key)

        # If existing is empty/null/falsey, use new value
        if not existing_val:
            result[key] = value
            continue

        # Special case: action_layer deep-merge empty-string fields
        if key == "action_layer" and isinstance(existing_val, dict) and isinstance(value, dict):
            merged = dict(existing_val)
            for kk, vv in value.items():
                if not merged.get(kk):
                    merged[kk] = vv
            result[key] = merged
            continue

        # Special case for lists
        if isinstance(existing_val, list) and isinstance(value, list):
            if len(existing_val) == 0:
                result[key] = value
            # else: keep existing list as-is in supplement mode
            continue

    return result
