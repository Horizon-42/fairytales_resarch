"""STAC (Situation, Task, Action, Consequence) analysis API.

This module provides functionality to classify sentences into STAC categories
and extract relevant information based on the classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from ..json_utils import loads_strict_json
from ..llm_router import LLMConfig, LLMRouterError, chat
from .stac_prompts import (
    SYSTEM_PROMPT_STAC_ANALYSIS,
    build_stac_analysis_prompt,
)


@dataclass(frozen=True)
class STACAnalyzerConfig:
    """Controls model choice and LLM provider."""

    llm: LLMConfig = LLMConfig()


class STACAnalysisError(RuntimeError):
    pass


STACCategory = Literal["situation", "task", "action", "consequence"]


def analyze_stac(
    *,
    sentence: str,
    story_context: Optional[str] = None,
    use_context: bool = True,
    previous_sentence: Optional[str] = None,
    next_sentence: Optional[str] = None,
    use_neighboring_sentences: bool = False,
    config: STACAnalyzerConfig = STACAnalyzerConfig(),
) -> Dict[str, Any]:
    """Analyze a single sentence using STAC classification.

    Args:
        sentence: The specific sentence to analyze.
        story_context: The full story text providing context (required if use_context is True).
        use_context: Whether to use story context in the analysis. If False, only the sentence is analyzed.
        previous_sentence: The sentence immediately before the target sentence (used if use_neighboring_sentences is True).
        next_sentence: The sentence immediately after the target sentence (used if use_neighboring_sentences is True).
        use_neighboring_sentences: Whether to use neighboring sentences as auxiliary information. 
            This mode is orthogonal to use_context and can be used independently or together.
        config: STAC analyzer configuration.

    Returns a dict containing:
        - stac_category: str - One of "situation", "task", "action", "consequence"
        - location: str - For situation: location name (empty if not applicable)
        - task_roles: List[str] - For task: list of roles who need to complete the task (empty if not applicable)
        - doers: List[str] - For action: list of doers (empty if not applicable)
        - receivers: List[str] - For action: list of receivers (empty if not applicable)
        - changed_state: str - For consequence: description of state change (empty if not applicable)
        - explanation: str - Brief explanation of the classification and annotation

    Raises:
        STACAnalysisError: on model/JSON failure.
    """

    if not isinstance(sentence, str) or not sentence.strip():
        raise STACAnalysisError("`sentence` must be a non-empty string")

    if use_context:
        if not isinstance(story_context, str) or not story_context.strip():
            raise STACAnalysisError("`story_context` must be a non-empty string when use_context is True")
    else:
        # If not using context, story_context is optional
        story_context = None

    # Validate neighboring sentences if the mode is enabled
    if use_neighboring_sentences:
        # At least one neighboring sentence should be provided
        if previous_sentence is None and next_sentence is None:
            raise STACAnalysisError(
                "At least one of `previous_sentence` or `next_sentence` must be provided "
                "when `use_neighboring_sentences` is True"
            )
        # If provided, they should be non-empty strings
        if previous_sentence is not None and (not isinstance(previous_sentence, str) or not previous_sentence.strip()):
            raise STACAnalysisError("`previous_sentence` must be a non-empty string if provided")
        if next_sentence is not None and (not isinstance(next_sentence, str) or not next_sentence.strip()):
            raise STACAnalysisError("`next_sentence` must be a non-empty string if provided")
    else:
        # If not using neighboring sentences, ignore them
        previous_sentence = None
        next_sentence = None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_STAC_ANALYSIS},
        {
            "role": "user",
            "content": build_stac_analysis_prompt(
                sentence=sentence,
                story_context=story_context,
                use_context=use_context,
                previous_sentence=previous_sentence,
                next_sentence=next_sentence,
                use_neighboring_sentences=use_neighboring_sentences,
            ),
        },
    ]

    try:
        raw = chat(config=config.llm, messages=messages, response_format_json=True)
    except LLMRouterError as exc:
        raise STACAnalysisError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise STACAnalysisError("Model output JSON must be an object")

    # Normalize output to ensure it matches the expected schema
    result = _normalize_stac_data(data)

    return result


def _normalize_stac_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the model output matches the expected schema."""

    # Normalize stac_category
    stac_category = str(data.get("stac_category", "")).lower()
    valid_categories: List[STACCategory] = ["situation", "task", "action", "consequence"]
    if stac_category not in valid_categories:
        # Default to "situation" if invalid
        stac_category = "situation"

    # Normalize string fields
    location = str(data.get("location", "")).strip()
    changed_state = str(data.get("changed_state", "")).strip()
    explanation = str(data.get("explanation", "")).strip()

    # Normalize array fields
    task_roles = data.get("task_roles", [])
    if not isinstance(task_roles, list):
        task_roles = []
    task_roles = [str(role).strip() for role in task_roles if str(role).strip()]

    doers = data.get("doers", [])
    if not isinstance(doers, list):
        doers = []
    doers = [str(doer).strip() for doer in doers if str(doer).strip()]

    receivers = data.get("receivers", [])
    if not isinstance(receivers, list):
        receivers = []
    receivers = [str(receiver).strip() for receiver in receivers if str(receiver).strip()]

    # Clear fields that are not relevant to the current category
    if stac_category == "situation":
        task_roles = []
        doers = []
        receivers = []
        changed_state = ""
    elif stac_category == "task":
        location = ""
        doers = []
        receivers = []
        changed_state = ""
    elif stac_category == "action":
        location = ""
        task_roles = []
        changed_state = ""
    elif stac_category == "consequence":
        location = ""
        task_roles = []
        doers = []
        receivers = []

    return {
        "stac_category": stac_category,
        "location": location,
        "task_roles": task_roles,
        "doers": doers,
        "receivers": receivers,
        "changed_state": changed_state,
        "explanation": explanation,
    }
