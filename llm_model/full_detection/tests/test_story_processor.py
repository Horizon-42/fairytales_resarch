"""Unit tests for story processor module."""

from unittest.mock import patch

import pytest

from llm_model.full_detection.story_processor import (
    StoryProcessingError,
    generate_story_summary,
    process_story,
    process_story_segment,
)
from llm_model.llm_router import LLMConfig


class TestGenerateStorySummary:
    """Tests for generate_story_summary function."""
    
    @patch('llm_model.full_detection.story_processor.chat')
    def test_generate_summary_full_story(self, mock_chat):
        """Test generating summary for full story."""
        mock_chat.return_value = "A hero's journey begins. The hero faces challenges."
        
        summary = generate_story_summary(
            story_text="Once upon a time, a hero went on a journey...",
            llm_config=LLMConfig(),
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        mock_chat.assert_called_once()
    
    @patch('llm_model.full_detection.story_processor.chat')
    def test_generate_summary_segment(self, mock_chat):
        """Test generating summary for a specific segment."""
        mock_chat.return_value = "The hero meets a mentor."
        
        text_span = {
            "start": 0,
            "end": 50,
            "text": "The hero traveled to a distant land and met a wise old mentor.",
        }
        
        summary = generate_story_summary(
            story_text="Full story text...",
            text_span=text_span,
            llm_config=LLMConfig(),
        )
        
        assert isinstance(summary, str)
        assert "mentor" in summary.lower() or len(summary) > 0
    
    @patch('llm_model.full_detection.story_processor.chat')
    def test_generate_summary_json_response(self, mock_chat):
        """Test handling JSON response from LLM."""
        mock_chat.return_value = '{"summary": "A hero\'s journey begins."}'
        
        summary = generate_story_summary(
            story_text="Story text",
            llm_config=LLMConfig(),
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    @patch('llm_model.full_detection.story_processor.chat')
    def test_generate_summary_with_code_fences(self, mock_chat):
        """Test handling markdown code fences in response."""
        mock_chat.return_value = '```\nA hero\'s journey begins.\n```'
        
        summary = generate_story_summary(
            story_text="Story text",
            llm_config=LLMConfig(),
        )
        
        assert isinstance(summary, str)
        assert "```" not in summary  # Should be stripped
    
    @patch('llm_model.full_detection.story_processor.chat')
    def test_generate_summary_error_handling(self, mock_chat):
        """Test error handling when LLM call fails."""
        from llm_model.llm_router import LLMRouterError
        
        mock_chat.side_effect = LLMRouterError("Connection failed")
        
        with pytest.raises(StoryProcessingError, match="Failed to generate summary"):
            generate_story_summary(
                story_text="Story text",
                llm_config=LLMConfig(),
            )


class TestProcessStory:
    """Tests for process_story function."""
    
    @patch('llm_model.full_detection.story_processor.chat')
    @patch('llm_model.full_detection.story_processor.run_pipeline')
    def test_process_story_with_generated_summary(self, mock_run_pipeline, mock_chat):
        """Test processing story with auto-generated summary."""
        # Mock summary generation
        mock_chat.return_value = "A hero's journey begins."
        
        # Mock pipeline results
        mock_run_pipeline.return_value = {
            "narrative_event": {
                "id": "event-1",
                "time_order": 1,
                "agents": ["Hero"],
            },
            "updated_characters": [{"name": "Hero", "archetype": "Hero"}],
        }
        
        text_spans = [
            {"start": 0, "end": 50, "text": "First segment text..."},
            {"start": 50, "end": 100, "text": "Second segment text..."},
        ]
        
        result = process_story(
            story_text="Full story text...",
            text_spans=text_spans,
            characters=[],
            llm_config=LLMConfig(),
        )
        
        assert "summary" in result
        assert "narrative_events" in result
        assert "updated_characters" in result
        assert len(result["narrative_events"]) == 2
    
    @patch('llm_model.full_detection.story_processor.run_pipeline')
    def test_process_story_with_provided_summary(self, mock_run_pipeline):
        """Test processing story with pre-provided summary."""
        mock_run_pipeline.return_value = {
            "narrative_event": {"id": "event-1", "time_order": 1},
            "updated_characters": [],
        }
        
        text_spans = [
            {"start": 0, "end": 50, "text": "First segment..."},
        ]
        
        result = process_story(
            story_text="Full story",
            text_spans=text_spans,
            characters=[],
            summary="Pre-generated summary",
            generate_summary=False,
            llm_config=LLMConfig(),
        )
        
        assert result["summary"] == "Pre-generated summary"
        # Summary generation should not be called
        assert len(result["narrative_events"]) == 1
    
    @patch('llm_model.full_detection.story_processor.run_pipeline')
    def test_process_story_character_list_updates(self, mock_run_pipeline):
        """Test that character list updates incrementally."""
        # First call returns character
        # Second call should use updated character list
        call_results = [
            {
                "narrative_event": {"id": "event-1", "time_order": 1},
                "updated_characters": [{"name": "Hero"}],
            },
            {
                "narrative_event": {"id": "event-2", "time_order": 2},
                "updated_characters": [
                    {"name": "Hero"},
                    {"name": "Villain"},
                ],
            },
        ]
        mock_run_pipeline.side_effect = call_results
        
        text_spans = [
            {"start": 0, "end": 50, "text": "First..."},
            {"start": 50, "end": 100, "text": "Second..."},
        ]
        
        result = process_story(
            story_text="Story",
            text_spans=text_spans,
            characters=[],
            summary="Summary",
            llm_config=LLMConfig(),
        )
        
        # Final character list should have both characters
        assert len(result["updated_characters"]) == 2
        assert any(c.get("name") == "Hero" for c in result["updated_characters"])
        assert any(c.get("name") == "Villain" for c in result["updated_characters"])
    
    @patch('llm_model.full_detection.story_processor.run_pipeline')
    def test_process_story_error_handling(self, mock_run_pipeline):
        """Test error handling when pipeline fails for a segment."""
        # First call succeeds, second fails
        mock_run_pipeline.side_effect = [
            {
                "narrative_event": {"id": "event-1"},
                "updated_characters": [],
            },
            Exception("Pipeline failed"),
        ]
        
        text_spans = [
            {"start": 0, "end": 50, "text": "First..."},
            {"start": 50, "end": 100, "text": "Second..."},
        ]
        
        result = process_story(
            story_text="Story",
            text_spans=text_spans,
            characters=[],
            summary="Summary",
            llm_config=LLMConfig(),
        )
        
        # Should have one successful event
        assert len(result["narrative_events"]) == 1
        # Should have error info in results
        assert any(r.get("success") is False for r in result["results"])


class TestProcessStorySegment:
    """Tests for process_story_segment function."""
    
    @patch('llm_model.full_detection.story_processor.generate_story_summary')
    @patch('llm_model.full_detection.story_processor.run_pipeline')
    def test_process_segment_with_generated_summary(
        self, mock_run_pipeline, mock_generate_summary
    ):
        """Test processing segment with auto-generated summary."""
        mock_generate_summary.return_value = "Segment summary"
        mock_run_pipeline.return_value = {
            "narrative_event": {"id": "event-1"},
            "updated_characters": [],
        }
        
        result = process_story_segment(
            story_text="Story",
            text_span={"start": 0, "end": 50, "text": "Segment..."},
            characters=[],
            time_order=1,
            llm_config=LLMConfig(),
        )
        
        assert result["summary"] == "Segment summary"
        assert "narrative_event" in result
        mock_generate_summary.assert_called_once()
    
    @patch('llm_model.full_detection.story_processor.run_pipeline')
    def test_process_segment_with_provided_summary(self, mock_run_pipeline):
        """Test processing segment with provided summary."""
        mock_run_pipeline.return_value = {
            "narrative_event": {"id": "event-1"},
            "updated_characters": [],
        }
        
        result = process_story_segment(
            story_text="Story",
            text_span={"start": 0, "end": 50, "text": "Segment..."},
            characters=[],
            time_order=1,
            summary="Provided summary",
            generate_summary=False,
            llm_config=LLMConfig(),
        )
        
        assert result["summary"] == "Provided summary"
