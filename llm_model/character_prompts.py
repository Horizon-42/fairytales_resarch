"""Prompt templates for character-only annotation.

Goal: extract story characters and assign a narrative archetype.

This output is designed to plug directly into the frontend "Characters" tab:
- `motif.character_archetypes`: list of {name, alias, archetype}
- (optional) `motif.helper_type` and `motif.obstacle_thrower`

Archetype guideline source:
- `docs/Character_Resources/character_arctypes.md`

Important:
- Use ONLY the allowed archetype labels below, because the UI uses a fixed list.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Literal, Optional


ALLOWED_ARCHETYPES = [
    "Hero",
    "Shadow",
    "Sidekick/Helper",
    "Villain",
    "Lover",
    "Mentor",
    "Mother",
    "Everyman",
    "Damsel",
    "Trickster",
    "Guardian",
    "Herald",
    "Scapegoat",
    "Outlaw",
    "Rebel",
    "Ruler",
    "Other",
]

ALLOWED_HELPER_TYPES = [
    "ANIMAL",
    "SUPERNATURAL",
    "COMPANION",
    "DEAD",
    "MAIDEN",
    "HUMAN",
    "OBJECT"
]

def build_character_user_prompt(
    *,
    text: str,
    culture: Optional[str] = None,
    existing_characters: Optional[Dict[str, Any]] = None,
    mode: Literal["supplement", "modify", "recreate"] = "recreate",
    additional_prompt: Optional[str] = None,
) -> str:
    """Build the user prompt for character-only extraction.

    Args:
        text: The story text to annotate.
        culture: Optional culture hint.
        existing_characters: Optional existing character annotation to use as base.
        mode: Annotation mode ("supplement", "modify", or "recreate").
        additional_prompt: Optional additional instructions from the user.
    """

    culture_hint = f"Culture hint: {culture}\n" if culture else ""

    # Build mode-specific instructions
    mode_instructions = ""
    if existing_characters is not None and mode != "recreate":
        existing_json_str = json.dumps(existing_characters, ensure_ascii=False, indent=2)
        if mode == "supplement":
            mode_instructions = (
                "\nIMPORTANT: You have been provided with an existing character annotation. "
                "Your task is to SUPPLEMENT it by adding ONLY missing characters. "
                "DO NOT modify or remove existing characters. "
                "Keep all existing character_archetypes, helper_type, and obstacle_thrower exactly as they are. "
                "Only add new characters that are clearly missing from the existing annotation.\n\n"
                "Existing character annotation:\n"
                "---\n"
                f"{existing_json_str}\n"
                "---\n\n"
            )
        elif mode == "modify":
            mode_instructions = (
                "\nIMPORTANT: You have been provided with an existing character annotation. "
                "Your task is to MODIFY and IMPROVE it. "
                "You can update existing character archetypes, fix errors, add missing characters, "
                "and improve the quality of annotations. "
                "You should review the existing annotation and enhance it based on the text.\n\n"
                "Existing character annotation:\n"
                "---\n"
                f"{existing_json_str}\n"
                "---\n\n"
            )

    # Keep definitions compact but explicit. This is derived from the guidelines file.
    definitions = "\n".join(
        [
            "Archetype definitions (choose the best fit):",
            "- Hero: central protagonist pursuing the main objective; tested by trials.",
            "- Shadow: dark mirror of the Hero; embodies what the Hero fears/becomes.",
            "- Sidekick/Helper: supports the Hero; grounding, advice, comic relief.",
            "- Villain: primary antagonist whose goals directly conflict with the Hero.",
            "- Lover: heart-led, harmony-seeking; avoids conflict; cares for relationships.",
            "- Mentor: wiser guide; provides knowledge/tools; nudges the Hero forward.",
            "- Mother: nurturing refuge; provides safety/healing (not necessarily literal mother).",
            "- Everyman: ordinary relatable person; ""normal"" viewpoint in extraordinary events.",
            "- Damsel: innocent/naive/hopeful; may need rescue; symbolizes vulnerability/hope.",
            "- Trickster: clever, self-interested; may help or hinder depending on advantage.",
            "- Guardian: threshold keeper/obstacle that blocks progress; tests growth.",
            "- Herald: announces change/call-to-adventure; triggers plot shift.",
            "- Scapegoat: takes blame; their fall enables others; unites people against them.",
            "- Outlaw: independent, outside society; strong self-direction; may be hunted.",
            "- Rebel: revolutionary; fights injustice; willing to burn bridges for a cause.",
            "- Ruler: authority figure; values order/tradition/status quo; may oppose change.",
            "- Other: use when none fits or evidence is weak.",
        ]
    )

    helper_definition = (
        "Helper types (choose all that clearly apply):\n"
        "- ANIMAL: talking or magical animals that assist the hero.\n"
        "- SUPERNATURAL: gods, spirits, deities, or magical beings aiding the hero.\n"
        "- COMPANION: friends or allies who accompany the hero on their journey.\n"
        "- DEAD: deceased characters who provide guidance or assistance.\n"
        "- MAIDEN: young female characters who help the hero, often with kindness or gifts.\n"
        "- HUMAN: ordinary people who assist the hero through practical help or advice.\n"
        "- OBJECT: magical or special items that aid the hero in their quest."
    )

    allowed = ", ".join(ALLOWED_ARCHETYPES)
    allowed_helpers = ", ".join(ALLOWED_HELPER_TYPES)

    return (
        mode_instructions
        + "Extract the characters and output JSON with this exact schema:\n"
        "{\n"
        "  \"character_archetypes\": [\n"
        "    { \"name\": string, \"alias\": string, \"archetype\": one_of_allowed }\n"
        "  ],\n"
        "  \"helper_type\": [string],\n"
        "  \"obstacle_thrower\": [string]\n"
        "}\n\n"
        "Rules:\n"
        "- Characters maybe human, but also could be animals, mythical beings, or anthropomorphized objects.\n"
        f"- `archetype` must be exactly one of: [{allowed}].\n"
        "- `name` should be the canonical name as it appears in the story (short).\n"
        "- `alias` is optional; one character may have one or more aliases; use ONLY for titles/epithets/roles that are EXPLICITLY mentioned in the story text itself (e.g., \"the king\", \"old woman\"). DO NOT invent aliases based on common sense or general knowledge. The alias must be directly quoted or clearly referenced in the provided text.\n"
        "- Include only salient characters (typically 2-12).\n"
        "- If a group is mentioned (e.g., \"soldiers\"), include it only if it acts as an agent in events.\n"
        f"- `helper_type` is a coarse story-level list of helper categories if clearly present (else empty list). It should chose from {allowed_helpers}\n"
        "- `obstacle_thrower` is a story-level list of character names who create obstacles (often villains/guardians); else empty list.\n"
        "- Output strict JSON only.\n\n"
        f"{culture_hint}"
        f"helper definations: {helper_definition}\n"
        f"{definitions}\n\n"
        "Text:\n---\n"
        f"{text}\n"
        "---\n"
        + ("" if mode == "recreate" else f"\nRemember: Mode is '{mode}'. Follow the instructions above.\n")
        + (f"\n\nAdditional instructions from user:\n{additional_prompt}\n" if additional_prompt and additional_prompt.strip() else "")
    )
