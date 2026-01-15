"""Tests for visualization module."""

import numpy as np
import pytest

from ..visualization import SegmentationVisualizer
from ..visualization_hooks import (
    VisualizableMagneticClustering,
    VisualizableGraphSegSM,
)
from ..similarity_matrix import SimilarityMatrixBuilder


def dummy_embedding_func(texts):
    """Dummy embedding function for testing."""
    embeddings = []
    for i, text in enumerate(texts):
        vec = np.zeros(10)
        vec[i % 10] = 1.0
        embeddings.append(vec.tolist())
    return embeddings


def test_segmentation_visualizer_init():
    """Test visualizer initialization."""
    visualizer = SegmentationVisualizer(figsize=(10, 8))
    assert visualizer.figsize == (10, 8)


def test_plot_similarity_matrix():
    """Test similarity matrix plotting."""
    visualizer = SegmentationVisualizer()
    
    # Create a simple similarity matrix
    matrix = np.eye(5) * 0.5
    matrix[0:3, 0:3] = 0.9
    matrix[3:5, 3:5] = 0.9
    
    # Should not raise an error (we can't easily test plot display)
    try:
        visualizer.plot_similarity_matrix(matrix, save_path=None)
        # Close the figure to avoid display
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_similarity_matrix raised {e}")


def test_plot_magnetic_signal():
    """Test magnetic signal plotting."""
    visualizer = SegmentationVisualizer()
    
    # Create sample data
    raw_forces = np.array([-0.5, 0.3, -0.2, 0.8, -0.1])
    smoothed_forces = np.array([-0.3, 0.2, 0.0, 0.5, 0.1])
    boundaries = [2, 3]
    
    try:
        visualizer.plot_magnetic_signal(
            raw_forces,
            smoothed_forces,
            boundaries,
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_magnetic_signal raised {e}")


def test_plot_graph_structure():
    """Test graph structure plotting."""
    visualizer = SegmentationVisualizer()
    
    # Create a simple similarity matrix
    matrix = np.eye(10) * 0.5
    matrix[0:5, 0:5] = 0.8
    matrix[5:10, 5:10] = 0.8
    matrix[0:5, 5:10] = 0.2
    matrix[5:10, 0:5] = 0.2
    
    try:
        visualizer.plot_graph_structure(
            matrix,
            threshold=0.7,
            segment_window=(0, 10),
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_graph_structure raised {e}")


def test_plot_segmentation_comparison():
    """Test segmentation comparison plotting."""
    visualizer = SegmentationVisualizer()
    
    doc_len = 10
    true_boundaries = [3, 7]
    pred_boundaries = [3, 8]
    
    try:
        visualizer.plot_segmentation_comparison(
            doc_len=doc_len,
            true_boundaries=true_boundaries,
            pred_boundaries=pred_boundaries,
            metric_score=0.85,
        )
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        pytest.fail(f"plot_segmentation_comparison raised {e}")


def test_visualizable_magnetic_clustering():
    """Test VisualizableMagneticClustering collects data."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    clustering = VisualizableMagneticClustering(
        similarity_builder=builder,
        window_size=2,
    )
    
    sentences = ["A", "B", "C", "D"]
    boundaries = clustering.segment(sentences)
    
    # Check that data was collected
    viz_data = clustering.get_visualization_data()
    
    assert "similarity_matrix" in viz_data
    assert "raw_forces" in viz_data
    assert "smoothed_forces" in viz_data
    assert "boundaries" in viz_data
    
    # Check data shapes
    assert viz_data["similarity_matrix"].shape == (4, 4)
    assert len(viz_data["raw_forces"]) == 3  # n-1
    assert len(viz_data["smoothed_forces"]) == 3
    assert isinstance(viz_data["boundaries"], list)


def test_visualizable_graph_segsm():
    """Test VisualizableGraphSegSM collects data."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    graph_seg = VisualizableGraphSegSM(
        similarity_builder=builder,
        threshold=0.5,
    )
    
    sentences = ["A", "B", "C", "D"]
    boundaries = graph_seg.segment(sentences)
    
    # Check that data was collected
    viz_data = graph_seg.get_visualization_data()
    
    assert "similarity_matrix" in viz_data
    assert "graph" in viz_data
    assert "threshold" in viz_data
    assert "cliques" in viz_data
    assert "boundaries" in viz_data
    
    # Check data types
    assert isinstance(viz_data["similarity_matrix"], np.ndarray)
    assert viz_data["threshold"] == 0.5


def test_visualization_data_isolation():
    """Test that visualization data is properly isolated."""
    builder = SimilarityMatrixBuilder(embedding_func=dummy_embedding_func)
    clustering = VisualizableMagneticClustering(
        similarity_builder=builder,
    )
    
    sentences = ["A", "B", "C"]
    clustering.segment(sentences)
    
    # Get data twice - should return copies
    data1 = clustering.get_visualization_data()
    data2 = clustering.get_visualization_data()
    
    # Modify data1
    data1["test"] = "modified"
    
    # data2 should not be affected
    assert "test" not in data2


def test_save_path():
    """Test that save_path parameter works."""
    import tempfile
    import os
    
    visualizer = SegmentationVisualizer()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        save_path = tmp.name
    
    try:
        matrix = np.eye(5) * 0.8
        visualizer.plot_similarity_matrix(
            matrix,
            save_path=save_path,
        )
        
        # Check that file was created
        assert os.path.exists(save_path)
        
        # Clean up
        os.unlink(save_path)
        import matplotlib.pyplot as plt
        plt.close('all')
    except Exception as e:
        # Clean up on error
        if os.path.exists(save_path):
            os.unlink(save_path)
        pytest.fail(f"Save path test failed: {e}")
