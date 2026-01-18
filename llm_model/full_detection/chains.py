"""LangChain chains for the full detection pipeline."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.exceptions import OutputParserException

from ..json_utils import loads_strict_json, JsonExtractionError
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
            
        Raises:
            ValueError: If JSON parsing fails after all recovery attempts
        """
        user_prompt = input.get("prompt", "")
        if not user_prompt:
            raise ValueError("Input must contain 'prompt' key")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            raw = chat(config=self.llm_config, messages=messages, response_format_json=True)
        except Exception as chat_error:
            print(f"\n{'='*60}", flush=True)
            print(f"ERROR: LLM chat call failed", flush=True)
            print(f"{'='*60}", flush=True)
            print(f"Error type: {type(chat_error).__name__}", flush=True)
            print(f"Error message: {chat_error}", flush=True)
            print(f"{'='*60}\n", flush=True)
            return {}  # Return empty dict if chat fails
        
        # Check if response is empty or None
        if not raw:
            print(f"\n{'='*60}", flush=True)
            print(f"WARNING: Empty or None LLM response", flush=True)
            print(f"{'='*60}", flush=True)
            print(f"Response type: {type(raw)}", flush=True)
            print(f"Response value: {repr(raw)}", flush=True)
            print(f"Response is None: {raw is None}", flush=True)
            print(f"Response is empty string: {raw == ''}", flush=True)
            print(f"{'='*60}\n", flush=True)
            return {}  # Return empty dict if response is empty
        
        # Check if response is a string but empty or whitespace only
        if isinstance(raw, str) and not raw.strip():
            print(f"\n{'='*60}", flush=True)
            print(f"WARNING: Empty or whitespace-only LLM response", flush=True)
            print(f"{'='*60}", flush=True)
            print(f"Response type: {type(raw)}", flush=True)
            print(f"Response repr: {repr(raw)}", flush=True)
            print(f"Response length: {len(raw)}", flush=True)
            print(f"{'='*60}\n", flush=True)
            return {}  # Return empty dict if response is whitespace only
        
        # Parse JSON with multiple fallback strategies
        data = None
        last_error = None
        
        # Strategy 1: Try loads_strict_json (handles code fences, extracts JSON from text)
        try:
            data = loads_strict_json(raw)
            if isinstance(data, dict):
                return data
        except (JsonExtractionError, json.JSONDecodeError) as e1:
            last_error = e1
        except Exception as e1:
            last_error = e1
        
        # Strategy 2: Try to extract JSON from text more aggressively using regex
        try:
            import re
            # Try to find the largest JSON object in the response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    # Try the strict loader which might handle it better
                    data = loads_strict_json(json_str)
                    if isinstance(data, dict):
                        return data
        except Exception as e2:
            last_error = e2
        
        # Strategy 3: Clean and try basic json.loads
        try:
            cleaned = raw.strip()
            # Remove markdown code fences
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 2:
                    lines = lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]
                cleaned = "\n".join(lines).strip()
            
            # Try direct JSON parse
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except Exception as e3:
            last_error = e3
        
        # Strategy 4: Try LangChain's JsonOutputParser as last resort (it's more strict)
        try:
            data = self.parser.parse(raw)
            if isinstance(data, dict):
                return data
        except (OutputParserException, Exception) as e4:
            last_error = e4
        
        # If all strategies fail, provide helpful error message and return empty dict
        # This prevents the pipeline from crashing, though the output will be incomplete
        print(f"\n{'='*60}", flush=True)
        print(f"JSON Parsing Failed", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Last error: {type(last_error).__name__}: {last_error}", flush=True)
        
        # Check if response might be truncated
        if len(raw) > 0 and (not raw.strip().endswith('}') or raw.count('{') != raw.count('}')):
            print(f"\n⚠️  Response may be truncated (unbalanced braces or incomplete JSON)", flush=True)
            print(f"   This often happens when --num-predict is too low.", flush=True)
            print(f"   Try increasing --num-predict to 512 or higher, or remove it.", flush=True)
        
        print(f"\nRaw LLM response (full):", flush=True)
        print(f"{raw}", flush=True)
        print(f"Response length: {len(raw)} characters", flush=True)
        print(f"\n{'='*60}\n", flush=True)
        
        # Return empty dict to allow pipeline to continue
        return {}


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
        try:
            result = llm_runnable.invoke({"prompt": prompt})
        except Exception as e:
            print(f"Warning: Character recognition failed: {e}", flush=True)
            result = {}  # Use empty dict as fallback
        
        # Extract doers and receivers (handle empty result gracefully)
        doers = result.get("doers", []) if isinstance(result, dict) else []
        receivers = result.get("receivers", []) if isinstance(result, dict) else []
        new_characters = result.get("new_characters", []) if isinstance(result, dict) else []
        
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
        try:
            result = llm_runnable.invoke({"prompt": prompt})
        except Exception as e:
            print(f"Warning: Instrument recognition LLM call failed: {e}", flush=True)
            result = {}
        
        instrument = result.get("instrument", "") if isinstance(result, dict) else ""
        if not isinstance(instrument, str):
            instrument = str(instrument).strip() if instrument else ""
        
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
        try:
            result = llm_runnable.invoke({"prompt": prompt})
        except Exception as e:
            print(f"Warning: Relationship deduction LLM call failed: {e}", flush=True)
            result = {}
        
        relationships = result.get("relationships", []) if isinstance(result, dict) else []
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
        try:
            result = llm_runnable.invoke({"prompt": prompt})
        except Exception as e:
            print(f"Warning: Action category LLM call failed: {e}", flush=True)
            result = {}
        
        action_layer = {
            "category": result.get("category", "") if isinstance(result, dict) else "",
            "type": result.get("type", "") if isinstance(result, dict) else "",
            "context": result.get("context", "") if isinstance(result, dict) else "",
            "status": result.get("status", "") if isinstance(result, dict) else "",
            "function": result.get("function", "") if isinstance(result, dict) else "",
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
        try:
            result = llm_runnable.invoke({"prompt": prompt})
        except Exception as e:
            print(f"Warning: STAC analysis LLM call failed: {e}", flush=True)
            result = {}
        
        stac = {
            "situation": result.get("situation", "") if isinstance(result, dict) else "",
            "task": result.get("task", "") if isinstance(result, dict) else "",
            "action": result.get("action", "") if isinstance(result, dict) else "",
            "consequence": result.get("consequence", "") if isinstance(result, dict) else "",
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
        try:
            result = llm_runnable.invoke({"prompt": prompt})
        except Exception as e:
            print(f"Warning: Event type classification LLM call failed: {e}", flush=True)
            result = {}
        
        event_type = result.get("event_type", "OTHER") if isinstance(result, dict) else "OTHER"
        desc_general = result.get("description_general", "") if isinstance(result, dict) else ""
        desc_specific = result.get("description_specific", "") if isinstance(result, dict) else ""
        
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
