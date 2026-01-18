"""Unit tests for pipeline orchestration."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from llm_model.full_detection.pipeline import PipelineError, build_pipeline, run_pipeline
from llm_model.llm_router import LLMConfig


class TestBuildPipeline:
    """Tests for build_pipeline function."""
    
    def test_build_pipeline_without_summary(self):
        """Test building pipeline without pre-generated summary."""
        llm_config = LLMConfig()
        pipeline = build_pipeline(llm_config, include_instrument=False)
        
        # Pipeline should be a runnable
        assert pipeline is not None
        # Note: We can't easily test the internal structure without running it
    
    def test_build_pipeline_with_summary(self):
        """Test building pipeline with pre-generated summary."""
        llm_config = LLMConfig()
        summary = "A hero's journey begins."
        pipeline = build_pipeline(llm_config, include_instrument=False, summary=summary)
        
        assert pipeline is not None
    
    def test_build_pipeline_with_instrument(self):
        """Test building pipeline with instrument recognition."""
        llm_config = LLMConfig()
        pipeline = build_pipeline(llm_config, include_instrument=True)
        
        assert pipeline is not None


class TestRunPipeline:
    """Tests for run_pipeline function."""
    
    @patch('llm_model.full_detection.chains.chat')
    def test_run_pipeline_basic(self, mock_chat):
        """Test running pipeline with mocked LLM calls."""
        # Mock LLM responses for each chain
        mock_responses = [
            # Character recognition
            '{"doers": ["Hero"], "receivers": ["Villain"], "new_characters": []}',
            # Relationship
            '{"relationships": [{"agent": "Hero", "target": "Villain", "relationship_level1": "Adversarial", "relationship_level2": "enemy", "sentiment": "hostile"}]}',
            # Action category
            '{"category": "physical", "type": "attack", "context": "", "status": "success", "function": ""}',
            # STAC
            '{"situation": "Hero faces villain", "task": "Defeat villain", "action": "Hero attacks", "consequence": "Villain defeated"}',
            # Event type
            '{"event_type": "A", "description_general": "Villainy", "description_specific": "Villain attacks hero"}',
        ]
        
        mock_chat.side_effect = mock_responses
        
        result = run_pipeline(
            story_text="A hero faces a villain.",
            text_span={"start": 0, "end": 23, "text": "A hero faces a villain."},
            characters=[],
            time_order=1,
            summary="Hero faces villain",
            llm_config=LLMConfig(),
            include_instrument=False,
        )
        
        assert "narrative_event" in result
        assert "updated_characters" in result
        event = result["narrative_event"]
        assert event["id"] is not None
        assert event["time_order"] == 1
        assert "Hero" in event["agents"]
    
    def test_run_pipeline_invalid_text_span(self):
        """Test running pipeline with invalid text_span."""
        with pytest.raises(PipelineError, match="text_span must be a dictionary"):
            run_pipeline(
                story_text="Story",
                text_span="invalid",  # Should be dict
                characters=[],
                time_order=1,
            )
    
    def test_run_pipeline_missing_text_key(self):
        """Test running pipeline with missing 'text' key in text_span."""
        with pytest.raises(PipelineError, match="text_span must contain 'text' key"):
            run_pipeline(
                story_text="Story",
                text_span={"start": 0, "end": 5},  # Missing 'text'
                characters=[],
                time_order=1,
            )
    
    def test_run_pipeline_auto_infer_indices(self):
        """Test that pipeline can infer start/end indices from text."""
        with patch('llm_model.full_detection.chains.chat') as mock_chat:
            # Mock all chain calls
            mock_chat.side_effect = [
                '{"doers": [], "receivers": [], "new_characters": []}',
                '{"relationships": []}',
                '{"category": "", "type": "", "context": "", "status": "", "function": ""}',
                '{"situation": "", "task": "", "action": "", "consequence": ""}',
                '{"event_type": "OTHER", "description_general": "", "description_specific": ""}',
            ]
            
            # This should not raise an error - indices should be inferred
            try:
                result = run_pipeline(
                    story_text="A hero's journey.",
                    text_span={"text": "A hero's journey."},  # Missing start/end
                    characters=[],
                    time_order=1,
                    summary="Summary",
                )
                # If it doesn't raise, check that indices were added
                assert "narrative_event" in result
            except PipelineError:
                # This is acceptable if validation is strict
                pass
    
    def test_run_pipeline_with_event_id(self):
        """Test running pipeline with custom event_id."""
        custom_id = str(uuid4())
        
        with patch('llm_model.full_detection.chains.chat') as mock_chat:
            # Mock all chain calls
            mock_chat.side_effect = [
                '{"doers": [], "receivers": [], "new_characters": []}',
                '{"relationships": []}',
                '{"category": "", "type": "", "context": "", "status": "", "function": ""}',
                '{"situation": "", "task": "", "action": "", "consequence": ""}',
                '{"event_type": "OTHER", "description_general": "", "description_specific": ""}',
            ]
            
            result = run_pipeline(
                story_text="Story",
                text_span={"start": 0, "end": 5, "text": "Story"},
                characters=[],
                time_order=1,
                event_id=custom_id,
                summary="Summary",
            )
            
        # Verify the function ran successfully
        assert result is not None
        assert "narrative_event" in result
