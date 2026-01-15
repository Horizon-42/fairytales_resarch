"""Main interface for text segmentation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from .boundary_metric import BoundarySegmentationMetric
from .graph_segsm import GraphSegSM
from .magnetic_clustering import MagneticClustering
from .similarity_matrix import SimilarityMatrixBuilder


@dataclass
class SegmentationResult:
    """Result of text segmentation."""
    
    document_id: str
    segments: List[Dict[str, Any]]
    boundaries: List[int]
    meta: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document_id": self.document_id,
            "segments": self.segments,
            "meta": self.meta,
        }


class TextSegmenter:
    """Main interface for LLM-based text segmentation.
    
    This class provides a unified interface for segmenting text using
    either Magnetic Clustering or GraphSegSM algorithms.
    """

    def __init__(
        self,
        embedding_func: callable,
        algorithm: Literal["magnetic", "graph"] = "magnetic",
        embedding_model: str = "nomic-embed-text",
        context_window: int = 2,
        # Magnetic Clustering parameters
        window_size: int = 3,
        weights: Optional[List[float]] = None,
        filter_width: float = 2.0,
        # GraphSegSM parameters
        threshold: float = 0.7,
        min_seg_size: int = 3,
    ):
        """Initialize TextSegmenter.
        
        Args:
            embedding_func: Function that takes a list of strings and returns
                embeddings. Should have signature:
                embeddings = embedding_func(texts: List[str]) -> List[List[float]]
            algorithm: Algorithm to use ("magnetic" or "graph").
            embedding_model: Name of the embedding model (for metadata).
            context_window: Number of consecutive sentences to use as context.
            window_size: Window size for Magnetic Clustering.
            weights: Weight parameters for Magnetic Clustering.
            filter_width: Gaussian filter width for Magnetic Clustering.
            threshold: Similarity threshold for GraphSegSM.
            min_seg_size: Minimum segment size for GraphSegSM.
        """
        self.embedding_func = embedding_func
        self.algorithm = algorithm
        self.embedding_model = embedding_model
        
        # Build similarity matrix builder
        self.similarity_builder = SimilarityMatrixBuilder(
            embedding_func=embedding_func,
            context_window=context_window,
        )
        
        # Initialize algorithm
        if algorithm == "magnetic":
            self.segmenter = MagneticClustering(
                similarity_builder=self.similarity_builder,
                window_size=window_size,
                weights=weights,
                filter_width=filter_width,
            )
        elif algorithm == "graph":
            self.segmenter = GraphSegSM(
                similarity_builder=self.similarity_builder,
                threshold=threshold,
                min_seg_size=min_seg_size,
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def segment(
        self,
        text: str,
        document_id: str = "doc_001",
        sentences: Optional[List[str]] = None,
        reference_boundaries: Optional[List[int]] = None,
    ) -> SegmentationResult:
        """Segment text into semantic segments.
        
        Args:
            text: Input text to segment. Ignored if sentences is provided.
            document_id: Identifier for the document.
            sentences: Pre-split sentences. If None, text will be split
                using simple sentence splitting.
            reference_boundaries: Optional reference boundaries for evaluation.
            
        Returns:
            SegmentationResult containing segments and metadata.
        """
        # Split into sentences if not provided
        if sentences is None:
            sentences = self._split_sentences(text)
        
        if not sentences:
            return SegmentationResult(
                document_id=document_id,
                segments=[],
                boundaries=[],
                meta={
                    "algorithm": self.algorithm,
                    "embedding_model": self.embedding_model,
                    "evaluation_score": None,
                },
            )
        
        # Perform segmentation
        boundaries = self.segmenter.segment(sentences)
        
        # Build segments
        segments = self._build_segments(sentences, boundaries)
        
        # Evaluate if reference boundaries provided
        evaluation_score = None
        if reference_boundaries is not None:
            metric = BoundarySegmentationMetric()
            evaluation_score = metric.calculate(reference_boundaries, boundaries)
        
        # Build result
        result = SegmentationResult(
            document_id=document_id,
            segments=segments,
            boundaries=boundaries,
            meta={
                "algorithm": self.algorithm,
                "embedding_model": self.embedding_model,
                "evaluation_score": evaluation_score,
            },
        )
        
        return result

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        This is a simple implementation. For better results, use the
        sentence_splitter module from pre_data_process.
        
        Args:
            text: Input text.
            
        Returns:
            List of sentences.
        """
        # Simple sentence splitting
        import re
        
        # Split on sentence-ending punctuation
        sentences = re.split(r'[。！？.!\?]+', text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences

    def _build_segments(
        self,
        sentences: List[str],
        boundaries: List[int],
    ) -> List[Dict[str, Any]]:
        """Build segment dictionaries from sentences and boundaries.
        
        Args:
            sentences: List of sentences.
            boundaries: List of boundary indices.
            
        Returns:
            List of segment dictionaries.
        """
        segments = []
        
        # Add boundaries at start and end for easier processing
        all_boundaries = [-1] + sorted(boundaries) + [len(sentences) - 1]
        
        for seg_id, (start_idx, end_idx) in enumerate(
            zip(all_boundaries[:-1], all_boundaries[1:]), start=1
        ):
            # Adjust indices (boundary is after the sentence)
            start_sent_idx = start_idx + 1
            end_sent_idx = end_idx
            
            # Extract segment text
            segment_sentences = sentences[start_sent_idx : end_sent_idx + 1]
            segment_text = " ".join(segment_sentences)
            
            segments.append({
                "segment_id": seg_id,
                "start_sentence_idx": start_sent_idx,
                "end_sentence_idx": end_sent_idx,
                "text": segment_text,
            })
        
        return segments
