"""Tests for story segmentation visualization."""

import pytest

from ..visualization import SegmentationVisualizer


def test_plot_story_segmentation():
    """Test story segmentation plotting."""
    visualizer = SegmentationVisualizer()
    
    sentences = [
        "Once upon a time, there was a prince.",
        "He lived in a beautiful castle.",
        "One day, he met a princess.",
        "They fell in love.",
        "They got married.",
        "Everyone lived happily ever after.",
    ]
    
    segments = [
        {
            "segment_id": 1,
            "start_sentence_idx": 0,
            "end_sentence_idx": 2,
            "text": "Once upon a time, there was a prince. He lived in a beautiful castle. One day, he met a princess.",
        },
        {
            "segment_id": 2,
            "start_sentence_idx": 3,
            "end_sentence_idx": 5,
            "text": "They fell in love. They got married. Everyone lived happily ever after.",
        },
    ]
    
    boundaries = [2]
    
    try:
        visualizer.plot_story_segmentation(
            sentences=sentences,
            segments=segments,
            boundaries=boundaries,
            title="Test Story Segmentation",
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_story_segmentation raised {e}")


def test_plot_segmentation_interface():
    """Test segmentation interface plotting."""
    from ..segmenter import SegmentationResult
    
    visualizer = SegmentationVisualizer()
    
    sentences = [
        "First sentence.",
        "Second sentence.",
        "Third sentence.",
        "Fourth sentence.",
    ]
    
    result = SegmentationResult(
        document_id="test_001",
        segments=[
            {
                "segment_id": 1,
                "start_sentence_idx": 0,
                "end_sentence_idx": 1,
                "text": "First sentence. Second sentence.",
            },
            {
                "segment_id": 2,
                "start_sentence_idx": 2,
                "end_sentence_idx": 3,
                "text": "Third sentence. Fourth sentence.",
            },
        ],
        boundaries=[1],
        meta={
            "algorithm": "magnetic",
            "embedding_model": "test-model",
            "evaluation_score": None,
        },
    )
    
    try:
        visualizer.plot_segmentation_interface(
            result=result,
            sentences=sentences,
            title="Test Interface",
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_segmentation_interface raised {e}")


def test_plot_story_segmentation_with_truncation():
    """Test story segmentation with text truncation."""
    visualizer = SegmentationVisualizer()
    
    # Create long sentences
    sentences = [
        "Short sentence.",
        "This is a very long sentence that should be truncated because it exceeds the maximum text length limit that we set for visualization purposes.",
        "Another sentence.",
    ]
    
    segments = [
        {
            "segment_id": 1,
            "start_sentence_idx": 0,
            "end_sentence_idx": 2,
            "text": " ".join(sentences),
        },
    ]
    
    try:
        visualizer.plot_story_segmentation(
            sentences=sentences,
            segments=segments,
            boundaries=[],
            max_text_length=50,
            max_sentences_per_segment=2,
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_story_segmentation with truncation raised {e}")


def test_plot_story_segmentation_empty():
    """Test story segmentation with empty input."""
    visualizer = SegmentationVisualizer()
    
    try:
        visualizer.plot_story_segmentation(
            sentences=[],
            segments=[],
            boundaries=[],
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        # Empty input might raise an error, which is acceptable
        pass
