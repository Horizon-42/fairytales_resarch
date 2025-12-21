"""Prompt templates for automatic annotation.

Keep prompts centralized so you can iterate without touching the API server.
"""

from __future__ import annotations

from typing import Optional


SYSTEM_PROMPT = """You are an expert narrative-annotation assistant for folktales.

You must output STRICT JSON only.
Do not wrap JSON in markdown fences.
Do not include any extra keys beyond the requested schema.
If unsure, return empty lists/strings rather than hallucinating.
"""


def build_user_prompt(*, text: str, culture: Optional[str] = None) -> str:
    """Build the user prompt that instructs the model to produce a v2 annotation."""

    culture_hint = f"\nCulture hint: {culture}\n" if culture else "\n"

    # Minimal schema aligned to `annotation_tools` jsonV2 shape.
    # We generate only the parts that can be inferred from text and are useful
    # to pre-fill the UI.
    return (
        "Create an annotation JSON object with this exact schema:\n"
        "{\n"
        "  \"version\": \"2.0\",\n"
        "  \"source_info\": {\n"
        "    \"language\": \"en\" | \"zh\" | \"fa\" | \"ja\" | \"other\",\n"
        "    \"type\": \"story\" | \"summary\" | \"other\",\n"
        "    \"reference_uri\": string,\n"
        "    \"text_content\": string\n"
        "  },\n"
        "  \"characters\": [\n"
        "    { \"name\": string, \"alias\": string, \"archetype\": string }\n"
        "  ],\n"
        "  \"narrative_events\": [\n"
        "    {\n"
        "      \"id\": string,\n"
        "      \"event_type\": string,\n"
        "      \"description\": string,\n"
        "      \"agents\": [string],\n"
        "      \"targets\": [string],\n"
        "      \"text_span\": {\"start\": int, \"end\": int} | null,\n"
        "      \"time_order\": int,\n"
        "      \"relationship_level1\": string,\n"
        "      \"relationship_level2\": string,\n"
        "      \"sentiment\": string,\n"
        "      \"action_layer\": {\"category\": string, \"type\": string, \"context\": string, \"status\": string} | null\n"
        "    }\n"
        "  ],\n"
        "  \"themes_and_motifs\": {\n"
        "    \"ending_type\": string,\n"
        "    \"key_values\": [string],\n"
        "    \"motif_type\": [string],\n"
        "    \"atu_categories\": [string],\n"
        "    \"obstacle_thrower\": [string],\n"
        "    \"helper_type\": [string],\n"
        "    \"thinking_process\": string\n"
        "  },\n"
        "  \"analysis\": {\n"
        "    \"propp_functions\": [ {\"fn\": string, \"evidence\": string} ],\n"
        "    \"propp_notes\": string,\n"
        "    \"paragraph_summaries\": {\n"
        "      \"per_paragraph\": { \"0\": string, \"1\": string },\n"
        "      \"combined\": [ {\"start_para\": int, \"end_para\": int, \"text\": string} ],\n"
        "      \"whole\": string\n"
        "    },\n"
        "    \"bias_reflection\": {\n"
        "      \"cultural_reading\": string,\n"
        "      \"gender_norms\": string,\n"
        "      \"hero_villain_mapping\": string,\n"
        "      \"ambiguous_motifs\": [string]\n"
        "    },\n"
        "    \"qa_notes\": string\n"
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- Use only information supported by the text.\n"
        "- Keep lists short (<= 10) unless necessary.\n"
        "- If you can't find a value, use empty string/empty list/null.\n"
        "- `id` fields must be unique strings; you can use simple UUID-like strings.\n"
        "- text_span indices are character offsets into text_content; if hard, set null.\n\n"
        f"{culture_hint}"
        "Text to annotate:\n"
        "---\n"
        f"{text}\n"
        "---\n"
    )
