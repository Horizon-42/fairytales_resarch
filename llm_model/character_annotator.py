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
from typing import Any, Dict, List, Optional

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
    config: CharacterAnnotatorConfig = CharacterAnnotatorConfig(),
) -> Dict[str, Any]:
    """Extract character archetypes (and simple helper/obstacle hints) from text.

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

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_CHARACTERS},
        {"role": "user", "content": build_character_user_prompt(text=text, culture=culture)},
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

    return {
        "character_archetypes": normalized_characters,
        "helper_type": helper_type,
        "obstacle_thrower": obstacle_thrower,
    }
