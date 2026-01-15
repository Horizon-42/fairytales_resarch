"""Prompt templates for STAC (Situation, Task, Action, Consequence) analysis."""

from __future__ import annotations

SYSTEM_PROMPT_STAC_ANALYSIS = """You are an expert narrative analyst specializing in STAC (Situation, Task, Action, Consequence) classification and annotation.
Your task is to classify a sentence into one of four STAC categories and then extract relevant information based on the classification.
You must output STRICT JSON only (no markdown, no commentary).
"""


def build_stac_analysis_prompt(
    *,
    sentence: str,
    story_context: str | None = None,
    use_context: bool = True,
    previous_sentence: str | None = None,
    next_sentence: str | None = None,
    use_neighboring_sentences: bool = False,
) -> str:
    """Build the user prompt for STAC analysis.
    
    Args:
        sentence: The specific sentence to analyze.
        story_context: The full story text providing context (optional if use_context is False).
        use_context: Whether to use story context in the analysis.
        previous_sentence: The sentence immediately before the target sentence.
        next_sentence: The sentence immediately after the target sentence.
        use_neighboring_sentences: Whether to include neighboring sentences as auxiliary information.
    """
    
    # Build task description with story context (if enabled)
    if use_context and story_context:
        task_description = (
            "# TASK\n"
            "Classify a single sentence into one of four STAC categories and extract relevant information "
            "within the context of a complete story.\n\n"

            "# INPUT\n"
            f"**Story Context (Full Story)**:\n"
            f"---\n"
            f"{story_context}\n"
            f"---\n\n"
        )
    else:
        task_description = (
            "# TASK\n"
            "Classify a single sentence into one of four STAC categories and extract relevant information.\n\n"

            "# INPUT\n"
        )
    
    # Add neighboring sentences as auxiliary information (if enabled)
    # This is independent of story_context mode
    if use_neighboring_sentences:
        neighboring_info = ""
        if previous_sentence:
            neighboring_info += f"**Previous Sentence (Auxiliary Context)**:\n\"{previous_sentence}\"\n\n"
        if next_sentence:
            neighboring_info += f"**Next Sentence (Auxiliary Context)**:\n\"{next_sentence}\"\n\n"
        
        if neighboring_info:
            task_description += neighboring_info
    
    # Add the target sentence to analyze
    task_description += f"**Sentence to Analyze**:\n\"{sentence}\"\n\n"

    return (
        task_description +
        
        "# STAC CLASSIFICATION\n\n"
        
        "Classify the sentence into exactly one of the following four categories:\n\n"
        
        "## 1. Situation\n"
        "Provides background context or sets the stage for future events.\n"
        "- **Classification**: \"situation\"\n"
        "- **Annotation Required**:\n"
        "  - **location**: Identify the location mentioned in the sentence. "
        "Note: Only output ONE location as the narrative focus/target location.\n"
        "    - If multiple locations are mentioned, choose the one that is the narrative focus.\n"
        "    - If no location is mentioned, use empty string \"\".\n\n"
        
        "## 2. Task\n"
        "States an explicit requirement or responsibility that must be fulfilled.\n"
        "- **Classification**: \"task\"\n"
        "- **Annotation Required**:\n"
        "  - **task_roles**: List of characters/roles who need to complete the task. Can be multiple roles.\n"
        "    - Format as a JSON array of strings, e.g., [\"character1\", \"character2\"]\n"
        "    - If no clear task roles are identified, use empty array [].\n\n"
        
        "## 3. Action\n"
        "Indicates an activity actively performed or just completed.\n"
        "- **Classification**: \"action\"\n"
        "- **Annotation Required**:\n"
        "  - **doers**: List of characters/roles who perform the action. Can be multiple roles.\n"
        "    - Format as a JSON array of strings, e.g., [\"character1\", \"character2\"]\n"
        "    - If no clear doer is identified, use empty array [].\n"
        "  - **receivers**: List of characters/objects that receive the action. Can be multiple roles.\n"
        "    - Format as a JSON array of strings, e.g., [\"character1\", \"object1\"]\n"
        "    - If no clear receiver is identified, use empty array [].\n\n"
        
        "## 4. Consequence\n"
        "Describes the outcome of a prior event that changes the state.\n"
        "- **Classification**: \"consequence\"\n"
        "- **Annotation Required**:\n"
        "  - **changed_state**: Description of the state change or outcome (string).\n"
        "    - Describe what changed as a result of the prior event.\n"
        "    - If no clear state change is described, use empty string \"\".\n\n"
        
        "# OUTPUT FORMAT\n"
        "Return a single Valid JSON object. Do not include markdown formatting.\n\n"
        "**JSON Schema**:\n"
        "{\n"
        "  \"stac_category\": string (\"situation\" | \"task\" | \"action\" | \"consequence\"),\n"
        "  \"location\": string (for situation: location name, empty string if not applicable),\n"
        "  \"task_roles\": array of strings (for task: list of roles, empty array if not applicable),\n"
        "  \"doers\": array of strings (for action: list of doers, empty array if not applicable),\n"
        "  \"receivers\": array of strings (for action: list of receivers, empty array if not applicable),\n"
        "  \"changed_state\": string (for consequence: description of state change, empty string if not applicable),\n"
        "  \"explanation\": string (brief explanation of the classification and annotation)\n"
        "}\n\n"
        
        "**Rules**:\n"
        "- The sentence must be classified into exactly one STAC category.\n"
        "- Only populate fields relevant to the classified category:\n"
        "  - If `stac_category` is \"situation\", only populate `location` (others should be empty/empty array).\n"
        "  - If `stac_category` is \"task\", only populate `task_roles` (others should be empty/empty array/empty string).\n"
        "  - If `stac_category` is \"action\", only populate `doers` and `receivers` (others should be empty/empty array/empty string).\n"
        "  - If `stac_category` is \"consequence\", only populate `changed_state` (others should be empty/empty array/empty string).\n"
        "- Always provide an `explanation` field with a brief explanation of your classification and annotation.\n"
    )
