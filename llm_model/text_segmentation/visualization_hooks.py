"""Non-intrusive hooks for collecting visualization data from segmentation algorithms.

This module provides wrapper classes that collect intermediate data during
segmentation without modifying the core algorithm implementations.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .graph_segsm import GraphSegSM
from .magnetic_clustering import MagneticClustering
from .similarity_matrix import SimilarityMatrixBuilder


class VisualizableMagneticClustering(MagneticClustering):
    """Wrapper for MagneticClustering that collects visualization data.
    
    This class extends MagneticClustering to collect intermediate data
    for visualization while maintaining the same interface.
    """

    def __init__(self, *args, **kwargs):
        """Initialize with same parameters as MagneticClustering."""
        super().__init__(*args, **kwargs)
        self._visualization_data: Dict[str, Any] = {}

    def segment(
        self,
        sentences: List[str],
    ) -> List[int]:
        """Segment text and collect visualization data.
        
        Args:
            sentences: List of sentence strings.
            
        Returns:
            List of boundary indices.
        """
        if len(sentences) <= 1:
            return []

        # Build similarity matrix
        similarity_matrix = self.similarity_builder.build_similarity_matrix(sentences)
        n = len(sentences)

        # Store similarity matrix
        self._visualization_data["similarity_matrix"] = similarity_matrix

        # Compute magnetic forces
        magnetic_forces = self._compute_magnetic_forces(similarity_matrix, n)
        self._visualization_data["raw_forces"] = magnetic_forces.copy()

        # Apply smoothing
        smoothed_forces = self._smooth_forces(magnetic_forces)
        self._visualization_data["smoothed_forces"] = smoothed_forces.copy()

        # Find boundaries
        boundaries = self._find_boundaries(smoothed_forces)
        self._visualization_data["boundaries"] = boundaries.copy()

        return boundaries

    def get_visualization_data(self) -> Dict[str, Any]:
        """Get collected visualization data.
        
        Returns:
            Dictionary containing:
            - similarity_matrix: np.ndarray
            - raw_forces: np.ndarray
            - smoothed_forces: np.ndarray
            - boundaries: List[int]
        """
        return self._visualization_data.copy()


class VisualizableGraphSegSM(GraphSegSM):
    """Wrapper for GraphSegSM that collects visualization data.
    
    This class extends GraphSegSM to collect intermediate data
    for visualization while maintaining the same interface.
    """

    def __init__(self, *args, **kwargs):
        """Initialize with same parameters as GraphSegSM."""
        super().__init__(*args, **kwargs)
        self._visualization_data: Dict[str, Any] = {}

    def segment(
        self,
        sentences: List[str],
    ) -> List[int]:
        """Segment text and collect visualization data.
        
        Args:
            sentences: List of sentence strings.
            
        Returns:
            List of boundary indices.
        """
        if len(sentences) <= 1:
            return []

        # Build similarity matrix
        similarity_matrix = self.similarity_builder.build_similarity_matrix(sentences)
        n = len(sentences)

        # Store similarity matrix
        self._visualization_data["similarity_matrix"] = similarity_matrix

        # Build semantic graph
        graph = self._build_graph(similarity_matrix, n)
        self._visualization_data["graph"] = graph
        self._visualization_data["threshold"] = self.threshold

        # Find maximal cliques
        cliques = self._find_maximal_cliques(graph)
        self._visualization_data["cliques"] = cliques

        # Create initial segments
        segments = self._cliques_to_segments(cliques, n)
        self._visualization_data["initial_segments"] = segments.copy()

        # Merge small segments
        segments = self._merge_small_segments(segments, similarity_matrix, n)

        # Convert segments to boundaries
        boundaries = self._segments_to_boundaries(segments, n)
        self._visualization_data["boundaries"] = boundaries.copy()

        return boundaries

    def get_visualization_data(self) -> Dict[str, Any]:
        """Get collected visualization data.
        
        Returns:
            Dictionary containing:
            - similarity_matrix: np.ndarray
            - graph: networkx.Graph
            - threshold: float
            - cliques: List[Set[int]]
            - initial_segments: List[List[int]]
            - boundaries: List[int]
        """
        return self._visualization_data.copy()


class VisualizableTextSegmenter:
    """Wrapper for TextSegmenter that collects visualization data.
    
    This class extends TextSegmenter to collect intermediate data
    for visualization while maintaining the same interface.
    """

    def __init__(
        self,
        embedding_func: Callable,
        algorithm: str = "magnetic",
        **kwargs,
    ):
        """Initialize with same parameters as TextSegmenter.
        
        Args:
            embedding_func: Function that generates embeddings.
            algorithm: Algorithm to use ("magnetic" or "graph").
            **kwargs: Additional parameters passed to the algorithm.
        """
        from .segmenter import TextSegmenter

        self.embedding_func = embedding_func
        self.algorithm = algorithm
        self.embedding_model = kwargs.get("embedding_model", "nomic-embed-text")

        # Build similarity matrix builder
        from .similarity_matrix import SimilarityMatrixBuilder

        context_window = kwargs.get("context_window", 2)
        self.similarity_builder = SimilarityMatrixBuilder(
            embedding_func=embedding_func,
            context_window=context_window,
        )

        # Initialize algorithm with visualization wrapper
        if algorithm == "magnetic":
            self.segmenter = VisualizableMagneticClustering(
                similarity_builder=self.similarity_builder,
                window_size=kwargs.get("window_size", 3),
                weights=kwargs.get("weights"),
                filter_width=kwargs.get("filter_width", 2.0),
            )
        elif algorithm == "graph":
            self.segmenter = VisualizableGraphSegSM(
                similarity_builder=self.similarity_builder,
                threshold=kwargs.get("threshold", 0.7),
                min_seg_size=kwargs.get("min_seg_size", 3),
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Create base segmenter for text processing
        self.base_segmenter = TextSegmenter(
            embedding_func=embedding_func,
            algorithm=algorithm,
            **kwargs,
        )

    def segment(
        self,
        text: str = "",
        document_id: str = "doc_001",
        sentences: Optional[List[str]] = None,
        reference_boundaries: Optional[List[int]] = None,
    ):
        """Segment text and collect visualization data.
        
        Args:
            text: Input text (ignored if sentences provided).
            document_id: Document identifier.
            sentences: Pre-split sentences.
            reference_boundaries: Optional reference boundaries.
            
        Returns:
            SegmentationResult with visualization data stored in segmenter.
        """
        # Use base segmenter for text processing
        result = self.base_segmenter.segment(
            text=text,
            document_id=document_id,
            sentences=sentences,
            reference_boundaries=reference_boundaries,
        )

        # But use visualizable segmenter to get intermediate data
        if sentences is None:
            sentences = self.base_segmenter._split_sentences(text)

        # Re-segment with visualizable segmenter to collect data
        # (This is a small overhead but keeps things non-intrusive)
        _ = self.segmenter.segment(sentences)

        return result

    def get_visualization_data(self) -> Dict[str, Any]:
        """Get collected visualization data.
        
        Returns:
            Dictionary with visualization data depending on algorithm:
            - For Magnetic: similarity_matrix, raw_forces, smoothed_forces, boundaries
            - For Graph: similarity_matrix, graph, threshold, cliques, boundaries
        """
        return self.segmenter.get_visualization_data()
