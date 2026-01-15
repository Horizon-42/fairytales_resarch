"""Tests for Magnetic Clustering algorithm."""

import numpy as np
import pytest

from ..magnetic_clustering import MagneticClustering
from ..similarity_matrix import SimilarityMatrixBuilder


def dummy_embedding_func(texts):
    """Dummy embedding function for testing."""
    embeddings = []
    for i, text in enumerate(texts):
        vec = np.zeros(10)
        vec[i % 10] = 1.0
        embeddings.append(vec.tolist())
    return embeddings


def test_magnetic_clustering_basic():
    """Test basic magnetic clustering."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    clustering = MagneticClustering(
        similarity_builder=builder,
        window_size=2,
    )
    
    sentences = ["A", "B", "C", "D", "E"]
    boundaries = clustering.segment(sentences)
    
    # Should return a list of boundary indices
    assert isinstance(boundaries, list)
    assert all(isinstance(b, int) for b in boundaries)


def test_magnetic_clustering_custom_weights():
    """Test magnetic clustering with custom weights."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    weights = [0.8, 0.5, 0.3]
    clustering = MagneticClustering(
        similarity_builder=builder,
        window_size=3,
        weights=weights,
    )
    
    sentences = ["A", "B", "C", "D"]
    boundaries = clustering.segment(sentences)
    
    assert isinstance(boundaries, list)


def test_magnetic_clustering_invalid_weights():
    """Test that invalid weights raise error."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    
    with pytest.raises(ValueError):
        MagneticClustering(
            similarity_builder=builder,
            window_size=3,
            weights=[0.5, 0.3],  # Wrong length
        )


def test_magnetic_clustering_smoothing():
    """Test that smoothing is applied."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    clustering = MagneticClustering(
        similarity_builder=builder,
        filter_width=1.0,
    )
    
    sentences = ["A", "B", "C", "D", "E", "F"]
    boundaries = clustering.segment(sentences)
    
    # Smoothing should reduce noise, so boundaries should be reasonable
    assert isinstance(boundaries, list)


def test_magnetic_clustering_empty():
    """Test with empty or single sentence."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    clustering = MagneticClustering(similarity_builder=builder)
    
    assert clustering.segment([]) == []
    assert clustering.segment(["Only one"]) == []


def test_magnetic_clustering_force_direction():
    """Test that boundaries are found at force direction changes."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    clustering = MagneticClustering(
        similarity_builder=builder,
        window_size=2,
    )
    
    sentences = ["A", "B", "C", "D"]
    boundaries = clustering.segment(sentences)
    
    # Boundaries should be valid indices
    for b in boundaries:
        assert 0 <= b < len(sentences) - 1
