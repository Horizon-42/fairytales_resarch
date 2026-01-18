"""Prompt builder utilities that wrap full_detection prompts for training."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Import prompts from full_detection (non-invasive reuse)
from ...full_detection.prompts import (
    SYSTEM_PROMPT_CHARACTER_RECOGNITION,
    SYSTEM_PROMPT_INSTRUMENT,
    SYSTEM_PROMPT_RELATIONSHIP,
    SYSTEM_PROMPT_ACTION,
    SYSTEM_PROMPT_STAC,
    SYSTEM_PROMPT_EVENT_TYPE,
    build_character_recognition_prompt,
    build_instrument_prompt,
    build_relationship_prompt,
    build_action_category_prompt,
    build_stac_prompt,
    build_event_type_prompt,
)


def build_character_prompt_for_training(
    text_span: str,
    summary: str,
    existing_characters: List[Dict[str, Any]],
    story_context: Optional[str] = None
) -> str:
    """Build character recognition prompt for training.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        existing_characters: Existing global character list
        story_context: Optional full story context
    
    Returns:
        Combined system + user prompt string
    """
    system_prompt = SYSTEM_PROMPT_CHARACTER_RECOGNITION
    user_prompt = build_character_recognition_prompt(
        text_span=text_span,
        summary=summary,
        existing_characters=existing_characters,
        story_context=story_context
    )
    
    # Combine system and user prompts
    return f"{system_prompt}\n\n{user_prompt}"


def build_instrument_prompt_for_training(
    text_span: str,
    summary: str,
    doers: List[str]
) -> str:
    """Build instrument recognition prompt for training.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        doers: List of doer names from Step 2
    
    Returns:
        Combined system + user prompt string
    """
    system_prompt = SYSTEM_PROMPT_INSTRUMENT
    user_prompt = build_instrument_prompt(
        text_span=text_span,
        summary=summary,
        doers=doers
    )
    
    # Combine system and user prompts
    return f"{system_prompt}\n\n{user_prompt}"


def build_relationship_prompt_for_training(
    text_span: str,
    summary: str,
    doers: List[str],
    receivers: List[str],
    story_context: Optional[str] = None
) -> str:
    """Build relationship deduction prompt for training.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        doers: List of doer names
        receivers: List of receiver names (characters only)
        story_context: Optional full story context
    
    Returns:
        Combined system + user prompt string
    """
    system_prompt = SYSTEM_PROMPT_RELATIONSHIP
    user_prompt = build_relationship_prompt(
        text_span=text_span,
        summary=summary,
        doers=doers,
        receivers=receivers,
        story_context=story_context
    )
    
    # Combine system and user prompts
    return f"{system_prompt}\n\n{user_prompt}"


def build_action_prompt_for_training(
    text_span: str,
    summary: str,
    doers: List[str],
    receivers: List[str],
    instrument: str = ""
) -> str:
    """Build action category deduction prompt for training.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        doers: List of doer names
        receivers: List of receiver names
        instrument: Instrument name (if any)
    
    Returns:
        Combined system + user prompt string
    """
    system_prompt = SYSTEM_PROMPT_ACTION
    user_prompt = build_action_category_prompt(
        text_span=text_span,
        summary=summary,
        doers=doers,
        receivers=receivers,
        instrument=instrument
    )
    
    # Combine system and user prompts
    return f"{system_prompt}\n\n{user_prompt}"


def build_stac_prompt_for_training(
    text_span: str,
    summary: str,
    story_context: Optional[str] = None
) -> str:
    """Build STAC analysis prompt for training.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        story_context: Optional full story context
    
    Returns:
        Combined system + user prompt string
    """
    system_prompt = SYSTEM_PROMPT_STAC
    user_prompt = build_stac_prompt(
        text_span=text_span,
        summary=summary,
        story_context=story_context
    )
    
    # Combine system and user prompts
    return f"{system_prompt}\n\n{user_prompt}"


def build_event_type_prompt_for_training(
    text_span: str,
    summary: str,
    stac: Dict[str, str]
) -> str:
    """Build event type classification prompt for training.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        stac: STAC analysis from Step 5
    
    Returns:
        Combined system + user prompt string
    """
    system_prompt = SYSTEM_PROMPT_EVENT_TYPE
    user_prompt = build_event_type_prompt(
        text_span=text_span,
        summary=summary,
        stac=stac
    )
    
    # Combine system and user prompts
    return f"{system_prompt}\n\n{user_prompt}"
