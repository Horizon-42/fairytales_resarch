"""Prompt templates for sentence-level event analysis."""

from __future__ import annotations

SYSTEM_PROMPT_SENTENCE_ANALYSIS = """You are an expert narrative analyst specializing in sentence-level event detection and analysis.
Your task is to analyze a single sentence within the context of a complete story.
You must output STRICT JSON only (no markdown, no commentary).
"""

SENTIMENT_AND_EMOTION_GUIDE = """
### Sentiment and Emotion
- **Sentiment**: The emotional attitude of the doer toward the receiver in this specific event.
  Use one of: `romantic`, `positive`, `neutral`, `negative`, `fearful`, `hostile`
  
- **Emotion**: The emotional state or feeling expressed or experienced by the doer.
  Common emotions: `joy`, `sadness`, `anger`, `fear`, `surprise`, `disgust`, `love`, `hate`, 
  `anxiety`, `relief`, `guilt`, `shame`, `pride`, `envy`, `jealousy`, `gratitude`, `hope`, 
  `despair`, `contempt`, `embarrassment`, `excitement`, `calm`, `confusion`, etc.
  Use empty string "" if no clear emotion is present.
"""

def build_sentence_analysis_prompt(
    *,
    sentence: str,
    story_context: str | None = None,
    use_context: bool = True,
) -> str:
    """Build the user prompt for sentence-level event analysis.
    
    Args:
        sentence: The specific sentence to analyze.
        story_context: The full story text providing context (optional if use_context is False).
        use_context: Whether to use story context in the analysis.
    """
    
    if use_context and story_context:
        task_description = (
            "# TASK\n"
            "Analyze a single sentence within the context of a complete story. "
            "Determine if it contains an event, and if so, extract detailed information about it.\n\n"

            "# INPUT\n"
            f"**Story Context (Full Story)**:\n"
            f"---\n"
            f"{story_context}\n"
            f"---\n\n"

            f"**Sentence to Analyze**:\n"
            f"\"{sentence}\"\n\n"
        )
    else:
        task_description = (
            "# TASK\n"
            "Analyze a single sentence. "
            "Determine if it contains an event, and if so, extract detailed information about it.\n\n"

            "# INPUT\n"
            f"**Sentence to Analyze**:\n"
            f"\"{sentence}\"\n\n"
        )

    return (
        task_description +
        
        "# ANALYSIS REQUIREMENTS\n\n"
        
        "## 1. Event Detection\n"
        "First, determine if the sentence contains an **event** (an action or occurrence) "
        "or if it is just:\n"
        "- Location description (place setting)\n"
        "- Background information (contextual details)\n"
        "- Scene/landscape description (environmental description)\n"
        "- Other non-event content\n\n"
        
        "## 2. Location Extraction\n"
        "Extract **important/key location** information mentioned in the sentence:\n"
        "- **location**: The important place or location mentioned in the sentence (e.g., \"forest\", \"palace\", \"village\", etc.)\n"
        "  - Focus on **significant locations** that are relevant to the narrative or event\n"
        "  - Extract explicit location names (e.g., \"the palace\", \"a forest\", \"the village square\")\n"
        "  - Extract descriptive location phrases that are important to the context (e.g., \"by the river\", \"in the mountains\")\n"
        "  - **Do NOT** extract generic or trivial locations (e.g., \"here\", \"there\", \"somewhere\")\n"
        "  - **Do NOT** extract locations that are just part of background description without narrative significance\n"
        "  - If no important location is mentioned, use empty string \"\"\n"
        "  - Prioritize locations that are directly related to events or are setting the scene for important narrative moments\n\n"

        "## 3. Event Information (if event detected)\n"
        "If the sentence contains an event, extract:\n"
        "- **doer**: The agent/character who performs the action (empty string if no clear doer)\n"
        "- **receiver**: The target/recipient of the action (empty string if no clear receiver)\n"
        "- **sentiment**: The emotional attitude of the doer toward the receiver "
        "(one of: `romantic`, `positive`, `neutral`, `negative`, `fearful`, `hostile`, or empty string if not applicable)\n"
        "- **emotion**: The emotional state of the doer (e.g., `joy`, `sadness`, `anger`, `fear`, etc., or empty string if not clear)\n\n"

        f"{SENTIMENT_AND_EMOTION_GUIDE}\n"
        
        "# OUTPUT FORMAT\n"
        "Return a single Valid JSON object. Do not include markdown formatting.\n\n"
        "**JSON Schema**:\n"
        "{\n"
        "  \"is_event\": boolean,\n"
        "  \"content_type\": string (\"event\" | \"location\" | \"background\" | \"scene_description\" | \"other\"),\n"
        "  \"location\": string (location name or description, empty string if no location mentioned),\n"
        "  \"doer\": string (character name or empty string),\n"
        "  \"receiver\": string (character/object name or empty string),\n"
        "  \"sentiment\": string (sentiment code or empty string),\n"
        "  \"emotion\": string (emotion name or empty string),\n"
        "  \"explanation\": string (brief explanation of the analysis)\n"
        "}\n\n"
        
        "**Rules**:\n"
        "- If `is_event` is false, set `doer`, `receiver`, `sentiment`, and `emotion` to empty strings \"\".\n"
        "- If `is_event` is true but no clear doer/receiver, use empty strings.\n"
        "- Extract `location` only if an **important/key location** is mentioned in the sentence, regardless of whether it's an event or not.\n"
        "  - Focus on locations that have narrative significance or are directly relevant to the content\n"
        "  - Ignore generic, trivial, or non-significant location references\n"
        "- If no important location is mentioned, set `location` to empty string \"\".\n"
    )
