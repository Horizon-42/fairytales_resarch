"""Tests for TextSegmenter main interface."""

import numpy as np
import pytest

from ..segmenter import TextSegmenter


def dummy_embedding_func(texts):
    """Dummy embedding function for testing."""
    embeddings = []
    for i, text in enumerate(texts):
        vec = np.zeros(10)
        vec[i % 10] = 1.0
        embeddings.append(vec.tolist())
    return embeddings


def test_text_segmenter_magnetic():
    """Test TextSegmenter with Magnetic Clustering."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
    )
    
    text = "First sentence. Second sentence. Third sentence."
    result = segmenter.segment(text, document_id="test_001")
    
    assert result.document_id == "test_001"
    assert isinstance(result.segments, list)
    assert isinstance(result.boundaries, list)
    assert result.meta["algorithm"] == "magnetic"


def test_text_segmenter_graph():
    """Test TextSegmenter with GraphSegSM."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="graph",
    )
    
    text = "First sentence. Second sentence. Third sentence."
    result = segmenter.segment(text, document_id="test_002")
    
    assert result.document_id == "test_002"
    assert isinstance(result.segments, list)
    assert result.meta["algorithm"] == "graph"


def test_text_segmenter_with_sentences():
    """Test TextSegmenter with pre-split sentences."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
    )
    
    sentences = ["A", "B", "C", "D"]
    result = segmenter.segment(
        text="",  # Ignored
        sentences=sentences,
        document_id="test_003",
    )
    
    assert len(result.segments) > 0
    assert all("segment_id" in seg for seg in result.segments)
    assert all("text" in seg for seg in result.segments)


def test_text_segmenter_evaluation():
    """Test TextSegmenter with reference boundaries."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
    )
    
    sentences = ["A", "B", "C", "D", "E", "F"]
    ref_boundaries = [2, 4]
    
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="test_004",
        reference_boundaries=ref_boundaries,
    )
    
    assert result.meta["evaluation_score"] is not None
    assert 0.0 <= result.meta["evaluation_score"] <= 1.0


def test_text_segmenter_output_format():
    """Test that output format matches specification."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
    )
    
    sentences = ["A", "B", "C"]
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="test_005",
    )
    
    # Check output dictionary format
    output_dict = result.to_dict()
    
    assert "document_id" in output_dict
    assert "segments" in output_dict
    assert "meta" in output_dict
    
    # Check segment format
    for seg in output_dict["segments"]:
        assert "segment_id" in seg
        assert "start_sentence_idx" in seg
        assert "end_sentence_idx" in seg
        assert "text" in seg
    
    # Check meta format
    assert "algorithm" in output_dict["meta"]
    assert "embedding_model" in output_dict["meta"]


def test_text_segmenter_empty_text():
    """Test with empty text."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
    )
    
    result = segmenter.segment("", document_id="test_006")
    
    assert result.segments == []
    assert result.boundaries == []


def test_text_segmenter_invalid_algorithm():
    """Test that invalid algorithm raises error."""
    with pytest.raises(ValueError):
        TextSegmenter(
            embedding_func=dummy_embedding_func,
            algorithm="invalid",
        )


def test_text_segmenter_custom_parameters():
    """Test TextSegmenter with custom parameters."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
        window_size=5,
        filter_width=3.0,
    )
    
    sentences = ["A", "B", "C", "D"]
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="test_007",
    )
    
    assert result.meta["algorithm"] == "magnetic"


def test_build_segments():
    """Test segment building logic."""
    segmenter = TextSegmenter(
        embedding_func=dummy_embedding_func,
        algorithm="magnetic",
    )
    
    sentences = ["A", "B", "C", "D", "E"]
    boundaries = [1, 3]  # Boundaries after sentences 1 and 3
    
    segments = segmenter._build_segments(sentences, boundaries)
    
    assert len(segments) > 0
    # Check that segments cover all sentences
    all_indices = set()
    for seg in segments:
        start = seg["start_sentence_idx"]
        end = seg["end_sentence_idx"]
        all_indices.update(range(start, end + 1))
    
    assert all_indices == set(range(len(sentences)))
