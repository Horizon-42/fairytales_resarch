"""Tests for similarity matrix builder."""

import numpy as np
import pytest

from ..similarity_matrix import SimilarityMatrixBuilder


def dummy_embedding_func(texts):
    """Dummy embedding function for testing."""
    # Return simple embeddings: each text gets a unique vector
    embeddings = []
    for i, text in enumerate(texts):
        # Create a simple embedding vector
        vec = np.zeros(10)
        vec[i % 10] = 1.0
        embeddings.append(vec.tolist())
    return embeddings


def test_similarity_matrix_builder_basic():
    """Test basic similarity matrix construction."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    
    sentences = ["Sentence one.", "Sentence two.", "Sentence three."]
    matrix = builder.build_similarity_matrix(sentences)
    
    assert matrix.shape == (3, 3)
    assert np.allclose(matrix.diagonal(), 1.0)  # Diagonal should be 1.0 (self-similarity)


def test_similarity_matrix_builder_context_window():
    """Test context window functionality."""
    builder = SimilarityMatrixBuilder(
        embedding_func=dummy_embedding_func,
        context_window=2,
    )
    
    sentences = ["A", "B", "C", "D"]
    embeddings = builder.build_embeddings(sentences)
    
    # Should have 4 embeddings (one for each sentence with context)
    assert len(embeddings) == 4
    
    # Check that context windows are built correctly
    context_sentences = builder._build_context_windows(sentences)
    assert len(context_sentences) == 4
    assert context_sentences[0] == "A B"
    assert context_sentences[1] == "B C"
    assert context_sentences[2] == "C D"
    assert context_sentences[3] == "D"


def test_similarity_matrix_builder_local_neighborhood():
    """Test local neighborhood optimization."""
    builder = SimilarityMatrixBuilder(
        embedding_func=dummy_embedding_func,
        local_neighborhood=1,
    )
    
    sentences = ["A", "B", "C", "D", "E"]
    matrix = builder.build_similarity_matrix(sentences)
    
    # Only diagonal and immediate neighbors should be non-zero
    for i in range(5):
        for j in range(5):
            if abs(i - j) > 1:
                assert matrix[i, j] == 0.0


def test_get_approximate_similarity():
    """Test approximate similarity calculation."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    
    sentences = ["A", "B", "C"]
    matrix = builder.build_similarity_matrix(sentences)
    
    # Test within bounds
    sim = builder.get_approximate_similarity(matrix, 0, 1)
    assert isinstance(sim, float)
    
    # Test out of bounds (should use diagonal average)
    sim = builder.get_approximate_similarity(matrix, 0, 10)
    assert isinstance(sim, float)


def test_empty_sentences():
    """Test with empty sentence list."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    
    matrix = builder.build_similarity_matrix([])
    assert matrix.shape == (0, 0) or len(matrix) == 0


def test_single_sentence():
    """Test with single sentence."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    
    sentences = ["Only one sentence."]
    matrix = builder.build_similarity_matrix(sentences)
    
    assert matrix.shape == (1, 1)
    assert matrix[0, 0] == 1.0
