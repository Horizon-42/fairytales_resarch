"""LLM-based semantic text segmentation package.

This package implements text segmentation algorithms based on LLM embeddings,
including Magnetic Clustering and GraphSegSM algorithms, as well as evaluation
metrics for boundary segmentation.
"""

from .similarity_matrix import SimilarityMatrixBuilder
from .magnetic_clustering import MagneticClustering
from .graph_segsm import GraphSegSM
from .boundary_metric import BoundarySegmentationMetric
from .segmenter import TextSegmenter

# Optional visualization imports (requires matplotlib/seaborn)
try:
    from .visualization import SegmentationVisualizer, visualize_segmentation_result
except ImportError:
    # If matplotlib/seaborn are not installed, visualization is not available
    SegmentationVisualizer = None  # type: ignore
    visualize_segmentation_result = None  # type: ignore

from .visualization_hooks import (
    VisualizableMagneticClustering,
    VisualizableGraphSegSM,
    VisualizableTextSegmenter,
)

__all__ = [
    "SimilarityMatrixBuilder",
    "MagneticClustering",
    "GraphSegSM",
    "BoundarySegmentationMetric",
    "TextSegmenter",
    "SegmentationVisualizer",
    "visualize_segmentation_result",
    "VisualizableMagneticClustering",
    "VisualizableGraphSegSM",
    "VisualizableTextSegmenter",
]
