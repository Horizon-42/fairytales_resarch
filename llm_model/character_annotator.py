"""Character-only annotation API.

This produces fields that map directly onto the frontend Characters tab:
- `motif.character_archetypes`
- `motif.helper_type`
- `motif.obstacle_thrower`

Use this when you want to (re)generate character info without touching other
annotations (motifs, narrative events, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from .character_prompts import SYSTEM_PROMPT_CHARACTERS, build_character_user_prompt
from .json_utils import loads_strict_json
from .ollama_client import OllamaConfig, OllamaError, chat


@dataclass(frozen=True)
class CharacterAnnotatorConfig:
    """Controls model choice and Ollama connection."""

    ollama: OllamaConfig = OllamaConfig()


class CharacterAnnotationError(RuntimeError):
    pass


def annotate_characters(
    *,
    text: str,
    culture: Optional[str] = None,
    existing_characters: Optional[Dict[str, Any]] = None,
    mode: Literal["supplement", "modify", "recreate"] = "recreate",
    additional_prompt: Optional[str] = None,
    config: CharacterAnnotatorConfig = CharacterAnnotatorConfig(),
) -> Dict[str, Any]:
    """Extract character archetypes (and simple helper/obstacle hints) from text.

    Args:
        text: The story text to annotate.
        culture: Optional culture hint.
        existing_characters: Optional existing character annotation to use as base.
        mode: Annotation mode:
            - "supplement": Add missing characters, keep existing ones unchanged
            - "modify": Update and improve existing characters, may add new ones
            - "recreate": Ignore existing annotation, generate from scratch
        additional_prompt: Optional additional instructions from the user.
        config: Character annotator configuration.

    Returns a dict:
      {
        "character_archetypes": [ {"name": str, "alias": str, "archetype": str}, ... ],
        "helper_type": [str, ...],
        "obstacle_thrower": [str, ...]
      }

    The caller can merge these fields into app state under `motif`.

    Raises:
        CharacterAnnotationError: on model/JSON failure.
    """

    if not isinstance(text, str) or not text.strip():
        raise CharacterAnnotationError("`text` must be a non-empty string")

    if existing_characters is not None and mode == "recreate":
        existing_characters = None  # Ignore existing annotation in recreate mode

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_CHARACTERS},
        {
            "role": "user",
            "content": build_character_user_prompt(
                text=text, culture=culture, existing_characters=existing_characters, mode=mode, additional_prompt=additional_prompt
            ),
        },
    ]

    try:
        raw = chat(config=config.ollama, messages=messages, response_format_json=True)
    except OllamaError as exc:
        raise CharacterAnnotationError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise CharacterAnnotationError("Model output JSON must be an object")

    # Normalize output shape.
    characters = data.get("character_archetypes")
    if not isinstance(characters, list):
        characters = []

    normalized_characters: List[Dict[str, str]] = []
    for item in characters:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or "").strip()
        alias = str(item.get("alias", "") or "").strip()
        archetype = str(item.get("archetype", "") or "").strip()
        if not name:
            continue
        normalized_characters.append({"name": name, "alias": alias, "archetype": archetype})

    helper_type = data.get("helper_type")
    if not isinstance(helper_type, list):
        helper_type = []
    helper_type = [str(x).strip() for x in helper_type if str(x).strip()]

    obstacle_thrower = data.get("obstacle_thrower")
    if not isinstance(obstacle_thrower, list):
        obstacle_thrower = []
    obstacle_thrower = [str(x).strip() for x in obstacle_thrower if str(x).strip()]

    result = {
        "character_archetypes": normalized_characters,
        "helper_type": helper_type,
        "obstacle_thrower": obstacle_thrower,
    }

    # Merge with existing annotation based on mode
    if existing_characters is not None and mode in ("supplement", "modify"):
        result = _merge_character_annotations(result, existing_characters, mode)

    return result


def _merge_character_annotations(
    new_data: Dict[str, Any], existing_data: Dict[str, Any], mode: Literal["supplement", "modify"]
) -> Dict[str, Any]:
    """Merge new character annotation with existing annotation based on mode.

    Args:
        new_data: The newly generated character annotation.
        existing_data: The existing character annotation to merge with.
        mode: "supplement" keeps existing, adds missing; "modify" updates existing.

    Returns:
        Merged character annotation dictionary.
    """
    if mode == "supplement":
        # Keep existing characters, add new ones that don't exist
        existing_chars = {c.get("name", ""): c for c in existing_data.get("character_archetypes", [])}
        new_chars = {c.get("name", ""): c for c in new_data.get("character_archetypes", [])}
        merged_chars = list(existing_chars.values())
        for name, char in new_chars.items():
            if name and name not in existing_chars:
                merged_chars.append(char)

        # Merge helper_type and obstacle_thrower lists
        existing_helpers = existing_data.get("helper_type", [])
        new_helpers = new_data.get("helper_type", [])
        merged_helpers = list(existing_helpers)
        for item in new_helpers:
            if item not in merged_helpers:
                merged_helpers.append(item)

        existing_obstacles = existing_data.get("obstacle_thrower", [])
        new_obstacles = new_data.get("obstacle_thrower", [])
        merged_obstacles = list(existing_obstacles)
        for item in new_obstacles:
            if item not in merged_obstacles:
                merged_obstacles.append(item)

        return {
            "character_archetypes": merged_chars,
            "helper_type": merged_helpers,
            "obstacle_thrower": merged_obstacles,
        }
    else:  # modify mode - use new data
        return new_data
