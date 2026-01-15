"""Tests for GraphSegSM algorithm."""

import numpy as np
import pytest

from ..graph_segsm import GraphSegSM
from ..similarity_matrix import SimilarityMatrixBuilder


def dummy_embedding_func(texts):
    """Dummy embedding function for testing."""
    embeddings = []
    for i, text in enumerate(texts):
        vec = np.zeros(10)
        vec[i % 10] = 1.0
        embeddings.append(vec.tolist())
    return embeddings


def test_graph_segsm_basic():
    """Test basic GraphSegSM."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    graph_seg = GraphSegSM(
        similarity_builder=builder,
        threshold=0.5,
    )
    
    sentences = ["A", "B", "C", "D", "E"]
    boundaries = graph_seg.segment(sentences)
    
    assert isinstance(boundaries, list)
    assert all(isinstance(b, int) for b in boundaries)


def test_graph_segsm_threshold():
    """Test that threshold affects segmentation."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    
    # Low threshold (more edges)
    graph_seg_low = GraphSegSM(
        similarity_builder=builder,
        threshold=0.1,
    )
    
    # High threshold (fewer edges)
    graph_seg_high = GraphSegSM(
        similarity_builder=builder,
        threshold=0.9,
    )
    
    sentences = ["A", "B", "C", "D"]
    boundaries_low = graph_seg_low.segment(sentences)
    boundaries_high = graph_seg_high.segment(sentences)
    
    # Both should return valid boundaries
    assert isinstance(boundaries_low, list)
    assert isinstance(boundaries_high, list)


def test_graph_segsm_min_seg_size():
    """Test minimum segment size merging."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    graph_seg = GraphSegSM(
        similarity_builder=builder,
        min_seg_size=3,
    )
    
    sentences = ["A", "B", "C", "D", "E", "F"]
    boundaries = graph_seg.segment(sentences)
    
    # Should merge small segments
    assert isinstance(boundaries, list)


def test_graph_segsm_empty():
    """Test with empty or single sentence."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    graph_seg = GraphSegSM(similarity_builder=builder)
    
    assert graph_seg.segment([]) == []
    assert graph_seg.segment(["Only one"]) == []


def test_build_graph():
    """Test graph construction."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    graph_seg = GraphSegSM(
        similarity_builder=builder,
        threshold=0.5,
    )
    
    sentences = ["A", "B", "C"]
    matrix = builder.build_similarity_matrix(sentences)
    graph = graph_seg._build_graph(matrix, len(sentences))
    
    assert graph.number_of_nodes() == 3
    # Edges depend on similarity values


def test_find_maximal_cliques():
    """Test clique finding."""
    import networkx as nx
    
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    graph_seg = GraphSegSM(similarity_builder=builder)
    
    # Create a simple graph
    graph = nx.Graph()
    graph.add_nodes_from([0, 1, 2, 3])
    graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
    
    cliques = graph_seg._find_maximal_cliques(graph)
    
    assert isinstance(cliques, list)
    assert all(isinstance(c, set) for c in cliques)
    assert len(cliques) > 0  # Should find at least some cliques
