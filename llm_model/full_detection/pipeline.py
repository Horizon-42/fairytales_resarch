"""Main pipeline orchestration for full narrative detection."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..llm_router import LLMConfig
from .chains import (
    create_action_category_chain,
    create_character_recognition_chain,
    create_event_type_chain,
    create_finalize_chain,
    create_instrument_chain,
    create_relationship_chain,
    create_stac_chain,
    create_summary_chain,
)
from .pipeline_state import PipelineState


class PipelineError(RuntimeError):
    """Raised when pipeline execution fails."""
    pass


def build_pipeline(
    llm_config: LLMConfig,
    include_instrument: bool = False,
    summary: Optional[str] = None,
) -> Any:
    """Build the full detection pipeline.
    
    Args:
        llm_config: LLM configuration for all chains
        include_instrument: Whether to include instrument recognition (Step 2.5)
        summary: Optional pre-generated summary. If provided, skips summary generation step.
        
    Returns:
        Composed LangChain pipeline
    """
    from langchain_core.runnables import RunnableLambda
    
    # Build individual chains
    char_chain = create_character_recognition_chain(llm_config)
    instrument_chain = create_instrument_chain(llm_config) if include_instrument else None
    relationship_chain = create_relationship_chain(llm_config)
    action_chain = create_action_category_chain(llm_config)
    stac_chain = create_stac_chain(llm_config)
    event_type_chain = create_event_type_chain(llm_config)
    finalize_chain = create_finalize_chain()
    
    # Compose pipeline
    # If summary is provided, inject it directly; otherwise generate it
    if summary is not None:
        def inject_summary(state: Dict[str, Any]) -> Dict[str, Any]:
            """Inject pre-generated summary into state."""
            if isinstance(state, PipelineState):
                state_dict = state.to_dict()
            else:
                state_dict = state.copy()
            state_dict["summary"] = summary
            return state_dict
        
        pipeline = RunnableLambda(inject_summary)
    else:
        summary_chain = create_summary_chain(llm_config)
        pipeline = summary_chain
    
    # Character recognition (depends on summary)
    pipeline = pipeline | char_chain
    
    # Instrument recognition (optional, depends on character recognition)
    if instrument_chain:
        pipeline = pipeline | instrument_chain
    
    # Relationship deduction (depends on character recognition)
    pipeline = pipeline | relationship_chain
    
    # Action category (depends on character recognition and instrument)
    pipeline = pipeline | action_chain
    
    # STAC analysis (depends on summary)
    pipeline = pipeline | stac_chain
    
    # Event type (depends on summary and STAC)
    pipeline = pipeline | event_type_chain
    
    # Finalize
    pipeline = pipeline | finalize_chain
    
    return pipeline


def run_pipeline(
    story_text: str,
    text_span: Dict[str, Any],
    characters: List[Dict[str, Any]],
    time_order: int,
    event_id: Optional[str] = None,
    llm_config: Optional[LLMConfig] = None,
    include_instrument: bool = False,
    summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full detection pipeline.
    
    Args:
        story_text: Full story text for context
        text_span: Text span dict with 'start', 'end', 'text' keys
        characters: Existing global character list (may be empty)
        time_order: Temporal order of this event
        event_id: Optional UUID for the event (generated if not provided)
        llm_config: LLM configuration (uses default if not provided)
        include_instrument: Whether to include instrument recognition
        summary: Optional pre-generated summary. If provided, skips summary generation.
        
    Returns:
        Dictionary with 'narrative_event' key containing the final structured event,
        and 'updated_characters' key with the updated character list
        
    Raises:
        PipelineError: If pipeline execution fails
    """
    if llm_config is None:
        llm_config = LLMConfig()
    
    if event_id is None:
        event_id = str(uuid4())
    
    # Validate text_span
    if not isinstance(text_span, dict):
        raise PipelineError("text_span must be a dictionary")
    if "text" not in text_span:
        raise PipelineError("text_span must contain 'text' key")
    if "start" not in text_span or "end" not in text_span:
        # Try to infer from text if possible, or use defaults
        text_span = {
            "start": 0,
            "end": len(text_span.get("text", "")),
            "text": text_span.get("text", ""),
            **{k: v for k, v in text_span.items() if k not in ["start", "end", "text"]}
        }
    
    # Create initial state
    initial_state = PipelineState(
        story_text=story_text,
        text_span=text_span,
        characters=characters or [],
        time_order=time_order,
        event_id=event_id,
        summary=summary,  # Include summary if provided
    )
    
    # Build and run pipeline
    try:
        pipeline = build_pipeline(llm_config, include_instrument=include_instrument, summary=summary)
        
        # Convert state to dict for pipeline
        state_dict = initial_state.to_dict()
        
        # Run pipeline
        result_dict = pipeline.invoke(state_dict)
        
        # Extract results
        narrative_event = result_dict.get("narrative_event")
        updated_characters = result_dict.get("updated_characters") or result_dict.get("characters", [])
        
        if narrative_event is None:
            raise PipelineError("Pipeline did not produce a narrative_event")
        
        return {
            "narrative_event": narrative_event,
            "updated_characters": updated_characters,
            "pipeline_state": result_dict,  # Full state for debugging
        }
        
    except Exception as e:
        raise PipelineError(f"Pipeline execution failed: {e}") from e


def run_pipeline_batch(
    story_text: str,
    text_spans: List[Dict[str, Any]],
    characters: List[Dict[str, Any]],
    llm_config: Optional[LLMConfig] = None,
    include_instrument: bool = False,
    summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Run pipeline for multiple text spans sequentially.
    
    Characters list is updated incrementally as new characters are discovered.
    
    Args:
        story_text: Full story text for context
        text_spans: List of text span dicts, each with 'start', 'end', 'text'
        characters: Initial global character list (may be empty)
        llm_config: LLM configuration (uses default if not provided)
        include_instrument: Whether to include instrument recognition
        summary: Optional pre-generated summary shared across all spans
        
    Returns:
        Dictionary with:
        - 'narrative_events': List of narrative event dicts
        - 'updated_characters': Final updated character list
        - 'results': List of individual results with metadata
    """
    if llm_config is None:
        llm_config = LLMConfig()
    
    current_characters = characters.copy() if characters else []
    narrative_events = []
    results = []
    
    for idx, text_span in enumerate(text_spans, start=1):
        try:
            result = run_pipeline(
                story_text=story_text,
                text_span=text_span,
                characters=current_characters,
                time_order=idx,
                llm_config=llm_config,
                include_instrument=include_instrument,
                summary=summary,  # Pass shared summary
            )
            
            # Update character list for next iteration
            current_characters = result["updated_characters"]
            
            # Collect results
            narrative_events.append(result["narrative_event"])
            results.append({
                "index": idx,
                "success": True,
                "narrative_event": result["narrative_event"],
            })
            
        except Exception as e:
            # Log error but continue with next span
            results.append({
                "index": idx,
                "success": False,
                "error": str(e),
            })
    
    return {
        "narrative_events": narrative_events,
        "updated_characters": current_characters,
        "results": results,
    }
