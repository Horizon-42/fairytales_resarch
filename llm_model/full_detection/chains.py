"""LangChain chains for the full detection pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough

from ..json_utils import loads_strict_json
from ..llm_router import LLMConfig, chat
from .pipeline_state import PipelineState
from .prompts import (
    SYSTEM_PROMPT_ACTION,
    SYSTEM_PROMPT_CHARACTER_RECOGNITION,
    SYSTEM_PROMPT_EVENT_TYPE,
    SYSTEM_PROMPT_INSTRUMENT,
    SYSTEM_PROMPT_RELATIONSHIP,
    SYSTEM_PROMPT_STAC,
    SYSTEM_PROMPT_SUMMARY,
    build_action_category_prompt,
    build_character_recognition_prompt,
    build_event_type_prompt,
    build_instrument_prompt,
    build_relationship_prompt,
    build_stac_prompt,
    build_summary_prompt,
)
from .utils import classify_target_type, resolve_character_aliases


class LLMRouterRunnable(Runnable):
    """LangChain Runnable wrapper around the existing LLM router."""
    
    def __init__(self, system_prompt: str, llm_config: LLMConfig):
        """Initialize the LLM router runnable.
        
        Args:
            system_prompt: System prompt for the LLM
            llm_config: LLM configuration
        """
        self.system_prompt = system_prompt
        self.llm_config = llm_config
        self.parser = JsonOutputParser()
    
    def invoke(self, input: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """Invoke the LLM with the given input.
        
        Args:
            input: Dictionary with 'prompt' key containing user prompt
            config: Optional configuration (not used currently)
            
        Returns:
            Parsed JSON response
        """
        user_prompt = input.get("prompt", "")
        if not user_prompt:
            raise ValueError("Input must contain 'prompt' key")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        raw = chat(config=self.llm_config, messages=messages, response_format_json=True)
        
        # Parse JSON
        try:
            data = loads_strict_json(raw)
        except Exception as e:
            # Fallback to JsonOutputParser
            data = self.parser.parse(raw)
        
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict output, got {type(data)}")
        
        return data


# Step 1: Summary Chain
def create_summary_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for story segment summarization."""
    
    def summary_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary from state."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        prompt = build_summary_prompt(
            text_span=s.text_span.get("text", ""),
            story_context=s.story_text if s.story_text else None
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_SUMMARY, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        # Handle both dict and string outputs
        if isinstance(result, dict) and "summary" in result:
            summary = result["summary"]
        elif isinstance(result, str):
            summary = result
        else:
            # Try to extract from any field
            summary = str(result).strip()
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict["summary"] = summary
        return state_dict
    
    return RunnablePassthrough() | summary_func


# Step 2: Character Recognition Chain
def create_character_recognition_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for character recognition and extraction."""
    
    def char_recognition_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract characters (doers/receivers) and update character list."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        prompt = build_character_recognition_prompt(
            text_span=s.text_span.get("text", ""),
            summary=s.summary or "",
            existing_characters=s.characters or [],
            story_context=s.story_text if s.story_text else None
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_CHARACTER_RECOGNITION, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        # Extract doers and receivers
        doers = result.get("doers", [])
        receivers = result.get("receivers", [])
        new_characters = result.get("new_characters", [])
        
        # Resolve aliases and update character list
        resolved_doers, updated_chars = resolve_character_aliases(doers, s.characters or [])
        resolved_receivers, updated_chars = resolve_character_aliases(receivers, updated_chars)
        
        # Add any new characters from LLM output that weren't matched
        for new_char in new_characters:
            if isinstance(new_char, dict):
                name = new_char.get("name", "")
                # Check if already in list
                from .utils import find_character_match
                if name and not find_character_match(name, updated_chars):
                    updated_chars.append(new_char)
        
        # Classify target type
        target_type, object_type = classify_target_type(resolved_receivers, updated_chars)
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict.update({
            "doers": resolved_doers,
            "receivers": resolved_receivers,
            "updated_characters": updated_chars,
            "characters": updated_chars,  # Update global list
            "target_type": target_type,
            "object_type": object_type,
        })
        return state_dict
    
    return RunnablePassthrough() | char_recognition_func


# Step 2.5: Instrument Recognition Chain (optional)
def create_instrument_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for instrument recognition."""
    
    def instrument_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract instrument from state."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        prompt = build_instrument_prompt(
            text_span=s.text_span.get("text", ""),
            summary=s.summary or "",
            doers=s.doers or []
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_INSTRUMENT, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        instrument = result.get("instrument", "")
        if not isinstance(instrument, str):
            instrument = str(instrument).strip()
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict["instrument"] = instrument
        return state_dict
    
    return RunnablePassthrough() | instrument_func


# Step 3: Relationship Deduction Chain
def create_relationship_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for relationship deduction."""
    
    def relationship_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relationships from state."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        # Only process if receivers are characters
        if s.target_type != "character" or not s.receivers:
            state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
            state_dict["relationships"] = []
            return state_dict
        
        prompt = build_relationship_prompt(
            text_span=s.text_span.get("text", ""),
            summary=s.summary or "",
            doers=s.doers or [],
            receivers=s.receivers or [],
            story_context=s.story_text if s.story_text else None
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_RELATIONSHIP, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        relationships = result.get("relationships", [])
        if not isinstance(relationships, list):
            relationships = []
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict["relationships"] = relationships
        return state_dict
    
    return RunnablePassthrough() | relationship_func


# Step 4: Action Category Chain
def create_action_category_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for action category deduction."""
    
    def action_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract action layer from state."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        prompt = build_action_category_prompt(
            text_span=s.text_span.get("text", ""),
            summary=s.summary or "",
            doers=s.doers or [],
            receivers=s.receivers or [],
            instrument=s.instrument or ""
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_ACTION, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        action_layer = {
            "category": result.get("category", ""),
            "type": result.get("type", ""),
            "context": result.get("context", ""),
            "status": result.get("status", ""),
            "function": result.get("function", ""),
        }
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict["action_layer"] = action_layer
        return state_dict
    
    return RunnablePassthrough() | action_func


# Step 5: STAC Analysis Chain
def create_stac_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for STAC analysis.
    
    Note: This uses a direct LLM call. In the future, we could integrate
    with the existing stac_analyzer module for consistency.
    """
    
    def stac_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract STAC analysis from state."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        prompt = build_stac_prompt(
            text_span=s.text_span.get("text", ""),
            summary=s.summary or "",
            story_context=s.story_text if s.story_text else None
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_STAC, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        stac = {
            "situation": result.get("situation", ""),
            "task": result.get("task", ""),
            "action": result.get("action", ""),
            "consequence": result.get("consequence", ""),
        }
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict["stac"] = stac
        return state_dict
    
    return RunnablePassthrough() | stac_func


# Step 6: Event Type Classification Chain
def create_event_type_chain(llm_config: LLMConfig) -> Runnable:
    """Create chain for event type classification (Propp functions)."""
    
    def event_type_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract event type and description from state."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        prompt = build_event_type_prompt(
            text_span=s.text_span.get("text", ""),
            summary=s.summary or "",
            stac=s.stac or {}
        )
        
        llm_runnable = LLMRouterRunnable(SYSTEM_PROMPT_EVENT_TYPE, llm_config)
        result = llm_runnable.invoke({"prompt": prompt})
        
        event_type = result.get("event_type", "OTHER")
        desc_general = result.get("description_general", "")
        desc_specific = result.get("description_specific", "")
        
        # Combine descriptions with semicolon
        if desc_general and desc_specific:
            description = f"{desc_general};{desc_specific}"
        elif desc_general:
            description = desc_general
        elif desc_specific:
            description = desc_specific
        else:
            # Fallback to summary
            description = s.summary or ""
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict.update({
            "event_type": event_type,
            "description": description,
        })
        return state_dict
    
    return RunnablePassthrough() | event_type_func


# Final Step: Finalize Narrative Event
def create_finalize_chain() -> Runnable:
    """Create chain to finalize the narrative event JSON structure."""
    
    def finalize_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Build final narrative_event JSON structure."""
        # Convert dict to PipelineState for access
        if isinstance(state, PipelineState):
            s = state
        else:
            s = PipelineState(**state)
        
        narrative_event = {
            "id": s.event_id,
            "text_span": s.text_span,
            "event_type": s.event_type or "OTHER",
            "description": s.description or (s.summary or ""),
            "agents": s.doers or [],
            "targets": s.receivers or [],
            "target_type": s.target_type or "object",
            "object_type": s.object_type or "",
            "instrument": s.instrument or "",
            "time_order": s.time_order,
            "relationships": s.relationships or [],
            "action_layer": s.action_layer or {
                "category": "",
                "type": "",
                "context": "",
                "status": "",
                "function": "",
            },
        }
        
        # Return updated state dict
        state_dict = s.to_dict() if isinstance(state, PipelineState) else state.copy()
        state_dict["narrative_event"] = narrative_event
        return state_dict
    
    return RunnablePassthrough() | finalize_func
