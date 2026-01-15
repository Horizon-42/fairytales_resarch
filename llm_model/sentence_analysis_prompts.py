"""Prompt templates for sentence-level event analysis."""

from __future__ import annotations

SYSTEM_PROMPT_SENTENCE_ANALYSIS = """You are an expert narrative analyst specializing in sentence-level event detection and analysis.
Your task is to analyze a single sentence within the context of a complete story.
You must output STRICT JSON only (no markdown, no commentary).
"""

NARRATIVE_FUNCTION_TYPES = """
### Narrative Function Types (for important events)
If the event is important to the story structure, classify it as one of:
- `trigger`: An event that initiates a new plot line or conflict.
- `climax`: The highest point of tension or conflict.
- `resolution`: The action that resolves a conflict.
- `character_arc`: An action defining a shift in personality or belief.
- `setup`: Preparation for future events.
- `exposition`: Action serving primarily to reveal background info.
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
    story_context: str,
    sentence: str,
) -> str:
    """Build the user prompt for sentence-level event analysis.
    
    Args:
        story_context: The full story text providing context.
        sentence: The specific sentence to analyze.
    """
    
    return (
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
        
        "# ANALYSIS REQUIREMENTS\n\n"
        
        "## 1. Event Detection\n"
        "First, determine if the sentence contains an **event** (an action or occurrence) "
        "or if it is just:\n"
        "- Location description (place setting)\n"
        "- Background information (contextual details)\n"
        "- Scene/landscape description (environmental description)\n"
        "- Other non-event content\n\n"
        
        "## 2. Event Information (if event detected)\n"
        "If the sentence contains an event, extract:\n"
        "- **doer**: The agent/character who performs the action (empty string if no clear doer)\n"
        "- **receiver**: The target/recipient of the action (empty string if no clear receiver)\n"
        "- **sentiment**: The emotional attitude of the doer toward the receiver "
        "(one of: `romantic`, `positive`, `neutral`, `negative`, `fearful`, `hostile`, or empty string if not applicable)\n"
        "- **emotion**: The emotional state of the doer (e.g., `joy`, `sadness`, `anger`, `fear`, etc., or empty string if not clear)\n\n"
        
        "## 3. Importance Assessment\n"
        "Evaluate the importance of this event within the entire story:\n"
        "- **importance_score**: A number from 0 to 10, where:\n"
        "  - 0-3: Minor event, not crucial to plot\n"
        "  - 4-6: Moderate importance, contributes to plot development\n"
        "  - 7-10: Highly important, critical to story structure\n"
        "- **narrative_function**: If importance_score >= 6, classify the event's narrative function. "
        "  If importance_score < 6, use empty string \"\".\n\n"
        
        f"{NARRATIVE_FUNCTION_TYPES}\n"
        f"{SENTIMENT_AND_EMOTION_GUIDE}\n"
        
        "# OUTPUT FORMAT\n"
        "Return a single Valid JSON object. Do not include markdown formatting.\n\n"
        "**JSON Schema**:\n"
        "{\n"
        "  \"is_event\": boolean,\n"
        "  \"content_type\": string (\"event\" | \"location\" | \"background\" | \"scene_description\" | \"other\"),\n"
        "  \"doer\": string (character name or empty string),\n"
        "  \"receiver\": string (character/object name or empty string),\n"
        "  \"sentiment\": string (sentiment code or empty string),\n"
        "  \"emotion\": string (emotion name or empty string),\n"
        "  \"importance_score\": integer (0-10),\n"
        "  \"narrative_function\": string (narrative function code or empty string),\n"
        "  \"explanation\": string (brief explanation of the analysis)\n"
        "}\n\n"
        
        "**Rules**:\n"
        "- If `is_event` is false, set `doer`, `receiver`, `sentiment`, `emotion`, and `narrative_function` to empty strings \"\", "
        "and set `importance_score` to 0.\n"
        "- If `is_event` is true but no clear doer/receiver, use empty strings.\n"
        "- Be precise with importance_score: only assign 6+ to events that significantly impact the story structure.\n"
        "- Only set `narrative_function` if `importance_score >= 6`.\n"
    )
