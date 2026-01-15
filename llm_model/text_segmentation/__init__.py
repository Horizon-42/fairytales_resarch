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

__all__ = [
    "SimilarityMatrixBuilder",
    "MagneticClustering",
    "GraphSegSM",
    "BoundarySegmentationMetric",
    "TextSegmenter",
]
