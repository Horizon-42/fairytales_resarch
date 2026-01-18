"""Unit tests for PipelineState."""

import pytest

from llm_model.full_detection.pipeline_state import PipelineState


class TestPipelineState:
    """Tests for PipelineState dataclass."""
    
    def test_initialization(self):
        """Test basic state initialization."""
        state = PipelineState(
            story_text="Once upon a time...",
            text_span={"start": 0, "end": 10, "text": "Once upon"},
            characters=[],
            time_order=1,
            event_id="test-123",
        )
        
        assert state.story_text == "Once upon a time..."
        assert state.text_span["start"] == 0
        assert state.time_order == 1
        assert state.event_id == "test-123"
        assert state.summary is None
        assert state.doers == []
    
    def test_default_values(self):
        """Test default values for optional fields."""
        state = PipelineState(
            story_text="",
            text_span={"start": 0, "end": 0, "text": ""},
            characters=[],
            time_order=1,
            event_id="test",
        )
        
        assert state.summary is None
        assert state.doers == []
        assert state.receivers == []
        assert state.relationships == []
        assert state.action_layer == {}
        assert state.instrument == ""
    
    def test_to_dict(self):
        """Test converting state to dictionary."""
        state = PipelineState(
            story_text="Story",
            text_span={"start": 0, "end": 5, "text": "Story"},
            characters=[{"name": "Hero"}],
            time_order=1,
            event_id="test-123",
            summary="A hero's journey",
            doers=["Hero"],
            receivers=["Villain"],
        )
        
        state_dict = state.to_dict()
        
        assert isinstance(state_dict, dict)
        assert state_dict["story_text"] == "Story"
        assert state_dict["summary"] == "A hero's journey"
        assert state_dict["doers"] == ["Hero"]
        assert state_dict["receivers"] == ["Villain"]
        assert state_dict["time_order"] == 1
        assert state_dict["event_id"] == "test-123"
    
    def test_state_updates(self):
        """Test updating state fields."""
        state = PipelineState(
            story_text="Story",
            text_span={"start": 0, "end": 5, "text": "Story"},
            characters=[],
            time_order=1,
            event_id="test",
        )
        
        # Update fields
        state.summary = "Summary"
        state.doers = ["Hero"]
        state.event_type = "VILLAINY"
        
        assert state.summary == "Summary"
        assert state.doers == ["Hero"]
        assert state.event_type == "VILLAINY"
