"""Sentence-level event analysis API.

This module provides functionality to analyze a single sentence within the context
of a complete story, determining if it contains an event and extracting relevant
information about the event, including location, participants, and emotions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

from .json_utils import loads_strict_json
from .llm_router import LLMConfig, LLMRouterError, chat
from .sentence_analysis_prompts import (
    SYSTEM_PROMPT_SENTENCE_ANALYSIS,
    build_sentence_analysis_prompt,
)


@dataclass(frozen=True)
class SentenceAnalyzerConfig:
    """Controls model choice and LLM provider."""

    llm: LLMConfig = LLMConfig()


class SentenceAnalysisError(RuntimeError):
    pass


def analyze_sentence(
    *,
    sentence: str,
    story_context: Optional[str] = None,
    use_context: bool = True,
    config: SentenceAnalyzerConfig = SentenceAnalyzerConfig(),
) -> Dict[str, Any]:
    """Analyze a single sentence, optionally within the context of a complete story.

    Args:
        sentence: The specific sentence to analyze.
        story_context: The full story text providing context (required if use_context is True).
        use_context: Whether to use story context in the analysis. If False, only the sentence is analyzed.
        config: Sentence analyzer configuration.

    Returns a dict containing:
        - is_event: bool - Whether the sentence contains an event
        - content_type: str - Type of content ("event", "location", "background", "scene_description", "other")
        - location: str - Location mentioned in the sentence (empty if not applicable)
        - doer: str - The agent/character who performs the action (empty if not applicable)
        - receiver: str - The target/recipient of the action (empty if not applicable)
        - sentiment: str - Emotional attitude of doer toward receiver (empty if not applicable)
        - emotion: str - Emotional state of the doer (empty if not applicable)
        - explanation: str - Brief explanation of the analysis

    Raises:
        SentenceAnalysisError: on model/JSON failure.
    """

    if not isinstance(sentence, str) or not sentence.strip():
        raise SentenceAnalysisError("`sentence` must be a non-empty string")

    if use_context:
        if not isinstance(story_context, str) or not story_context.strip():
            raise SentenceAnalysisError("`story_context` must be a non-empty string when use_context is True")
    else:
        # If not using context, story_context is optional
        story_context = None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_SENTENCE_ANALYSIS},
        {
            "role": "user",
            "content": build_sentence_analysis_prompt(
                sentence=sentence,
                story_context=story_context,
                use_context=use_context,
            ),
        },
    ]

    try:
        raw = chat(config=config.llm, messages=messages, response_format_json=True)
    except LLMRouterError as exc:
        raise SentenceAnalysisError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise SentenceAnalysisError("Model output JSON must be an object")

    # Normalize output to ensure it matches the expected schema
    result = _normalize_analysis_data(data)

    return result


def _normalize_analysis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the model output matches the expected schema."""

    # Ensure is_event is boolean
    is_event = bool(data.get("is_event", False))

    # Normalize content_type
    content_type = str(data.get("content_type", "other")).lower()
    valid_content_types = ["event", "location", "background", "scene_description", "other"]
    if content_type not in valid_content_types:
        content_type = "other"

    # Normalize string fields
    location = str(data.get("location", "")).strip()
    doer = str(data.get("doer", "")).strip()
    receiver = str(data.get("receiver", "")).strip()
    sentiment = str(data.get("sentiment", "")).strip()
    emotion = str(data.get("emotion", "")).strip()
    explanation = str(data.get("explanation", "")).strip()

    # If not an event, clear event-related fields
    if not is_event:
        doer = ""
        receiver = ""
        sentiment = ""
        emotion = ""

    return {
        "is_event": is_event,
        "content_type": content_type,
        "location": location,
        "doer": doer,
        "receiver": receiver,
        "sentiment": sentiment,
        "emotion": emotion,
        "explanation": explanation,
    }
