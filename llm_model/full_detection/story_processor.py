"""Story-level processing module for full narrative detection.

This module provides functionality to process an entire story by:
1. Generating a summary of the whole story (or story segment) once
2. Processing all narrative segments using the pipeline with the shared summary
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from ..llm_router import LLMConfig, LLMRouterError, chat
from ..json_utils import loads_strict_json
from .pipeline import run_pipeline
from .pipeline_state import PipelineState
from .prompts import SYSTEM_PROMPT_SUMMARY, build_summary_prompt


class StoryProcessingError(RuntimeError):
    """Raised when story processing fails."""
    pass


def generate_story_summary(
    story_text: str,
    text_span: Optional[Dict[str, Any]] = None,
    llm_config: Optional[LLMConfig] = None,
) -> str:
    """Generate a summary for the story or a specific segment.
    
    Args:
        story_text: Full story text
        text_span: Optional text span dict with 'start', 'end', 'text' keys.
                   If provided, summarizes only this segment.
                   If None, summarizes the entire story.
        llm_config: LLM configuration (uses default if not provided)
        
    Returns:
        Summary text (4-7 sentences)
        
    Raises:
        StoryProcessingError: If summary generation fails
    """
    if llm_config is None:
        llm_config = LLMConfig()
    
    # Determine text to summarize
    if text_span and "text" in text_span:
        segment_text = text_span["text"]
    elif text_span and "start" in text_span and "end" in text_span:
        segment_text = story_text[text_span["start"]:text_span["end"]]
    else:
        # Summarize entire story
        segment_text = story_text
    
    prompt = build_summary_prompt(
        text_span=segment_text,
        story_context=None  # Always None to save memory (summary generation doesn't need full context)
    )
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_SUMMARY},
        {"role": "user", "content": prompt},
    ]
    
    try:
        raw = chat(config=llm_config, messages=messages, response_format_json=False)
        
        # The summary might be in JSON format or plain text
        try:
            data = loads_strict_json(raw)
            if isinstance(data, dict) and "summary" in data:
                return data["summary"]
            elif isinstance(data, str):
                return data
        except Exception:
            # Not JSON, use raw text
            pass
        
        # Clean up the raw text (remove markdown code fences if present)
        summary = raw.strip()
        if summary.startswith("```"):
            lines = summary.splitlines()
            if len(lines) >= 2:
                lines = lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]
            summary = "\n".join(lines).strip()
        
        return summary
        
    except LLMRouterError as e:
        raise StoryProcessingError(f"Failed to generate summary: {e}") from e
    except Exception as e:
        raise StoryProcessingError(f"Unexpected error during summary generation: {e}") from e


def process_story(
    story_text: str,
    text_spans: List[Dict[str, Any]],
    characters: Optional[List[Dict[str, Any]]] = None,
    llm_config: Optional[LLMConfig] = None,
    include_instrument: bool = False,
    generate_summary: bool = True,
    summary: Optional[str] = None,
    on_span_complete: Optional[Callable[[int, Dict[str, Any], float], None]] = None,
) -> Dict[str, Any]:
    """Process an entire story through the narrative detection pipeline.
    
    This function:
    1. Generates a summary of the story (if not provided)
    2. Processes each text span using the pipeline with the shared summary
    
    Args:
        story_text: Full story text
        text_spans: List of text span dicts, each with 'start', 'end', 'text' keys
        characters: Initial global character list (may be empty)
        llm_config: LLM configuration (uses default if not provided)
        include_instrument: Whether to include instrument recognition
        generate_summary: Whether to generate summary (if summary not provided)
        summary: Pre-generated summary (if provided, skips summary generation)
        on_span_complete: Optional callback function called after each span completes.
                        Called with (span_idx, result_dict, elapsed_time).
                        Result dict contains 'narrative_event' and 'updated_characters'.
        
    Returns:
        Dictionary with:
        - 'summary': Story/segment summary
        - 'narrative_events': List of narrative event dicts
        - 'updated_characters': Final updated character list
        - 'results': List of individual results with metadata
        
    Raises:
        StoryProcessingError: If processing fails
    """
    if llm_config is None:
        llm_config = LLMConfig()
    
    if characters is None:
        characters = []
    
    # Step 1: Generate or use provided summary
    if summary is None:
        if generate_summary:
            try:
                print("Generating story summary...", flush=True)
                start_time = time.time()
                summary = generate_story_summary(
                    story_text=story_text,
                    text_span=None,  # Summarize entire story
                    llm_config=llm_config,
                )
                elapsed = time.time() - start_time
                print(f"✓ Summary generated in {elapsed:.1f}s", flush=True)
            except StoryProcessingError as e:
                raise StoryProcessingError(f"Failed to generate story summary: {e}") from e
        else:
            # Use empty summary if not generating and not provided
            summary = ""
    
    # Step 2: Process each text span with the shared summary
    current_characters = characters.copy()
    narrative_events = []
    results = []
    total_spans = len(text_spans)
    
    print(f"\nProcessing {total_spans} text spans...", flush=True)
    
    for idx, text_span in enumerate(text_spans, start=1):
        span_start_time = time.time()
        try:
            # Show progress with text preview
            span_text_preview = text_span.get("text", "")[:50] if "text" in text_span else ""
            if span_text_preview:
                span_text_preview = span_text_preview.replace("\n", " ")
                if len(span_text_preview) > 50:
                    span_text_preview = span_text_preview[:47] + "..."
            print(f"[{idx}/{total_spans}] Processing span {idx}... {span_text_preview}", flush=True)
            
            # Ensure text_span has 'text' field
            if "text" not in text_span:
                if "start" in text_span and "end" in text_span:
                    text_span = {
                        **text_span,
                        "text": story_text[text_span["start"]:text_span["end"]],
                    }
                else:
                    raise StoryProcessingError(f"Text span {idx} missing 'text' or 'start'/'end' fields")
            
            # Run pipeline with pre-generated summary
            result = run_pipeline(
                story_text=story_text,
                text_span=text_span,
                characters=current_characters,
                time_order=idx,
                summary=summary,  # Pass summary as input
                llm_config=llm_config,
                include_instrument=include_instrument,
            )
            
            # Update character list for next iteration
            current_characters = result["updated_characters"]
            
            # Collect results
            narrative_events.append(result["narrative_event"])
            
            elapsed = time.time() - span_start_time
            print(f"  ✓ Span {idx} completed in {elapsed:.1f}s", flush=True)
            
            results.append({
                "index": idx,
                "success": True,
                "narrative_event": result["narrative_event"],
                "processing_time": elapsed,
            })
            
            # Call callback if provided
            if on_span_complete:
                try:
                    on_span_complete(
                        span_idx=idx,
                        result={
                            "narrative_event": result["narrative_event"],
                            "updated_characters": current_characters,
                        },
                        elapsed_time=elapsed,
                    )
                except Exception as callback_error:
                    print(f"  ⚠ Callback error for span {idx}: {callback_error}", flush=True)
            
        except Exception as e:
            # Log error but continue with next span
            elapsed = time.time() - span_start_time
            print(f"  ✗ Span {idx} failed after {elapsed:.1f}s: {e}", flush=True)
            
            results.append({
                "index": idx,
                "success": False,
                "error": str(e),
                "processing_time": elapsed,
            })
    
    return {
        "summary": summary,
        "narrative_events": narrative_events,
        "updated_characters": current_characters,
        "results": results,
    }


def process_story_segment(
    story_text: str,
    text_span: Dict[str, Any],
    characters: Optional[List[Dict[str, Any]]] = None,
    time_order: int = 1,
    llm_config: Optional[LLMConfig] = None,
    include_instrument: bool = False,
    generate_summary: bool = True,
    summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Process a single story segment with optional summary generation.
    
    This is a convenience wrapper around process_story for single segments.
    
    Args:
        story_text: Full story text
        text_span: Text span dict with 'start', 'end', 'text' keys
        characters: Initial global character list (may be empty)
        time_order: Temporal order of this event
        llm_config: LLM configuration (uses default if not provided)
        include_instrument: Whether to include instrument recognition
        generate_summary: Whether to generate summary for this segment (if summary not provided)
        summary: Pre-generated summary (if provided, skips summary generation)
        
    Returns:
        Dictionary with:
        - 'summary': Segment summary
        - 'narrative_event': Narrative event dict
        - 'updated_characters': Updated character list
        
    Raises:
        StoryProcessingError: If processing fails
    """
    if summary is None and generate_summary:
        summary = generate_story_summary(
            story_text=story_text,
            text_span=text_span,
            llm_config=llm_config,
        )
    elif summary is None:
        summary = ""
    
    result = run_pipeline(
        story_text=story_text,
        text_span=text_span,
        characters=characters or [],
        time_order=time_order,
        summary=summary,  # Pass summary as input
        llm_config=llm_config,
        include_instrument=include_instrument,
    )
    
    return {
        "summary": summary,
        "narrative_event": result["narrative_event"],
        "updated_characters": result["updated_characters"],
    }
