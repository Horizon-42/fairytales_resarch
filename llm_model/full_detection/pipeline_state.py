"""State management for the full detection pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineState:
    """State object that accumulates data through the pipeline.
    
    This state is passed between LangChain chains, allowing each step
    to access outputs from previous steps.
    """
    
    # Input fields (required)
    story_text: str
    text_span: Dict[str, Any]  # {start: int, end: int, text: str}
    characters: List[Dict[str, Any]]  # Existing global character list
    time_order: int
    event_id: str
    
    # Step 1: Summary
    summary: Optional[str] = None
    
    # Step 2: Character Recognition
    doers: List[str] = field(default_factory=list)
    receivers: List[str] = field(default_factory=list)
    updated_characters: List[Dict[str, Any]] = field(default_factory=list)
    target_type: str = ""  # "character" or "object"
    object_type: str = ""  # "normal_object", "magical_agent", or "price" (if target_type is "object")
    
    # Step 2.5: Instrument Recognition (optional)
    instrument: str = ""
    
    # Step 3: Relationship Deduction
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    # Step 4: Action Category Deduction
    action_layer: Dict[str, str] = field(default_factory=dict)  # {category, type, context, status, function}
    
    # Step 5: STAC Analysis
    stac: Dict[str, str] = field(default_factory=dict)  # {situation, task, action, consequence}
    
    # Step 6: Event Type Classification
    event_type: str = "OTHER"
    description: str = ""  # General + specific description
    
    # Final output
    narrative_event: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for easy serialization."""
        return {
            "story_text": self.story_text,
            "text_span": self.text_span,
            "characters": self.characters,
            "time_order": self.time_order,
            "event_id": self.event_id,
            "summary": self.summary,
            "doers": self.doers,
            "receivers": self.receivers,
            "updated_characters": self.updated_characters,
            "target_type": self.target_type,
            "object_type": self.object_type,
            "instrument": self.instrument,
            "relationships": self.relationships,
            "action_layer": self.action_layer,
            "stac": self.stac,
            "event_type": self.event_type,
            "description": self.description,
            "narrative_event": self.narrative_event,
        }
