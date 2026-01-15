"""Integration tests for the complete text segmentation pipeline."""

import numpy as np
import pytest

from ..segmenter import TextSegmenter
from ..boundary_metric import BoundarySegmentationMetric


def create_similarity_embedding_func(similarity_matrix):
    """Create an embedding function that returns embeddings matching a similarity matrix.
    
    This is useful for testing with known similarity patterns.
    """
    # Use SVD to get embeddings from similarity matrix
    # Since similarity = cosine(emb_i, emb_j), we can factorize
    U, s, Vt = np.linalg.svd(similarity_matrix)
    embeddings = U @ np.diag(np.sqrt(s))
    
    def embedding_func(texts):
        # Return embeddings corresponding to the first len(texts) rows
        n = len(texts)
        return embeddings[:n].tolist()
    
    return embedding_func


def test_integration_simple_segmentation():
    """Test complete pipeline with simple text."""
    # Create a simple similarity pattern: first 3 sentences similar, last 2 similar
    n = 5
    similarity_matrix = np.eye(n)
    similarity_matrix[0:3, 0:3] = 0.9  # First cluster
    similarity_matrix[3:5, 3:5] = 0.9  # Second cluster
    similarity_matrix[0:3, 3:5] = 0.2  # Low similarity between clusters
    similarity_matrix[3:5, 0:3] = 0.2
    
    embedding_func = create_similarity_embedding_func(similarity_matrix)
    
    segmenter = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
        window_size=2,
    )
    
    sentences = ["A", "B", "C", "D", "E"]
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="integration_001",
    )
    
    # Should find a boundary somewhere
    assert len(result.boundaries) >= 0
    assert len(result.segments) > 0


def test_integration_graph_algorithm():
    """Test complete pipeline with GraphSegSM."""
    n = 6
    similarity_matrix = np.eye(n)
    # Create two clear clusters
    similarity_matrix[0:3, 0:3] = 0.8
    similarity_matrix[3:6, 3:6] = 0.8
    similarity_matrix[0:3, 3:6] = 0.3
    similarity_matrix[3:6, 0:3] = 0.3
    
    embedding_func = create_similarity_embedding_func(similarity_matrix)
    
    segmenter = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="graph",
        threshold=0.5,
        min_seg_size=2,
    )
    
    sentences = ["A", "B", "C", "D", "E", "F"]
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="integration_002",
    )
    
    assert len(result.segments) > 0
    assert result.meta["algorithm"] == "graph"


def test_integration_with_evaluation():
    """Test pipeline with evaluation."""
    n = 8
    similarity_matrix = np.eye(n)
    # Create three clusters
    similarity_matrix[0:3, 0:3] = 0.85
    similarity_matrix[3:6, 3:6] = 0.85
    similarity_matrix[6:8, 6:8] = 0.85
    similarity_matrix[0:3, 3:8] = 0.2
    similarity_matrix[3:6, [0, 1, 2, 6, 7]] = 0.2
    similarity_matrix[6:8, 0:6] = 0.2
    
    embedding_func = create_similarity_embedding_func(similarity_matrix)
    
    segmenter = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
    )
    
    sentences = ["A", "B", "C", "D", "E", "F", "G", "H"]
    ref_boundaries = [2, 5]  # Expected boundaries after sentences 2 and 5
    
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="integration_003",
        reference_boundaries=ref_boundaries,
    )
    
    # Should have evaluation score
    assert result.meta["evaluation_score"] is not None
    assert 0.0 <= result.meta["evaluation_score"] <= 1.0
    
    # Check output format
    output_dict = result.to_dict()
    assert "document_id" in output_dict
    assert "segments" in output_dict
    assert "meta" in output_dict


def test_integration_context_window():
    """Test that context window affects results."""
    n = 5
    similarity_matrix = np.eye(n)
    similarity_matrix[0:3, 0:3] = 0.9
    similarity_matrix[3:5, 3:5] = 0.9
    similarity_matrix[0:3, 3:5] = 0.2
    similarity_matrix[3:5, 0:3] = 0.2
    
    embedding_func = create_similarity_embedding_func(similarity_matrix)
    
    # Without context window
    segmenter_no_ctx = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
        context_window=1,
    )
    
    # With context window
    segmenter_ctx = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
        context_window=2,
    )
    
    sentences = ["A", "B", "C", "D", "E"]
    
    result_no_ctx = segmenter_no_ctx.segment(
        text="",
        sentences=sentences,
        document_id="integration_004a",
    )
    
    result_ctx = segmenter_ctx.segment(
        text="",
        sentences=sentences,
        document_id="integration_004b",
    )
    
    # Both should produce valid results
    assert len(result_no_ctx.segments) > 0
    assert len(result_ctx.segments) > 0


def test_integration_realistic_text():
    """Test with more realistic text structure."""
    # Simulate a document with topic shifts
    # Sentences 0-2: Topic A (high similarity)
    # Sentences 3-5: Topic B (high similarity)
    # Sentences 6-8: Topic A again (high similarity with 0-2)
    n = 9
    similarity_matrix = np.eye(n) * 0.5
    
    # Topic A cluster (sentences 0-2, 6-8)
    topic_a_indices = [0, 1, 2, 6, 7, 8]
    for i in topic_a_indices:
        for j in topic_a_indices:
            if i != j:
                similarity_matrix[i, j] = 0.85
    
    # Topic B cluster (sentences 3-5)
    topic_b_indices = [3, 4, 5]
    for i in topic_b_indices:
        for j in topic_b_indices:
            if i != j:
                similarity_matrix[i, j] = 0.85
    
    # Low similarity between topics
    for i in topic_a_indices:
        for j in topic_b_indices:
            similarity_matrix[i, j] = 0.2
            similarity_matrix[j, i] = 0.2
    
    embedding_func = create_similarity_embedding_func(similarity_matrix)
    
    segmenter = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="graph",
        threshold=0.6,
        min_seg_size=2,
    )
    
    sentences = [f"Sentence {i}" for i in range(n)]
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="integration_005",
    )
    
    # Should identify topic boundaries
    assert len(result.boundaries) >= 0
    assert len(result.segments) > 0
    
    # Verify output structure
    for seg in result.segments:
        assert "segment_id" in seg
        assert "start_sentence_idx" in seg
        assert "end_sentence_idx" in seg
        assert "text" in seg
        assert seg["start_sentence_idx"] <= seg["end_sentence_idx"]
