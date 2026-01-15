"""GraphSegSM algorithm for text segmentation."""

from __future__ import annotations

from typing import List, Set

import networkx as nx
import numpy as np

from .similarity_matrix import SimilarityMatrixBuilder


class GraphSegSM:
    """GraphSegSM algorithm for text segmentation.
    
    This algorithm builds a semantic graph where nodes are sentences and
    edges connect similar sentences. Segmentation is performed by finding
    maximal cliques in the graph.
    """

    def __init__(
        self,
        similarity_builder: SimilarityMatrixBuilder,
        threshold: float = 0.7,
        min_seg_size: int = 3,
    ):
        """Initialize GraphSegSM.
        
        Args:
            similarity_builder: SimilarityMatrixBuilder instance.
            threshold: Similarity threshold (tau) for edge creation.
                Sentences with similarity > threshold are connected.
            min_seg_size: Minimum segment size. Segments smaller than this
                will be merged with their most similar neighbor.
        """
        self.similarity_builder = similarity_builder
        self.threshold = threshold
        self.min_seg_size = min_seg_size

    def segment(
        self,
        sentences: List[str],
    ) -> List[int]:
        """Segment text into semantic segments.
        
        Args:
            sentences: List of sentence strings.
            
        Returns:
            List of boundary indices. A boundary at index i means there's
            a break between sentence i and sentence i+1.
        """
        if len(sentences) <= 1:
            return []
        
        # Build similarity matrix
        similarity_matrix = self.similarity_builder.build_similarity_matrix(sentences)
        n = len(sentences)
        
        # Build semantic graph
        graph = self._build_graph(similarity_matrix, n)
        
        # Find maximal cliques
        cliques = self._find_maximal_cliques(graph)
        
        # Create initial segments from cliques
        segments = self._cliques_to_segments(cliques, n)
        
        # Merge small segments
        segments = self._merge_small_segments(segments, similarity_matrix, n)
        
        # Convert segments to boundaries
        boundaries = self._segments_to_boundaries(segments, n)
        
        return boundaries

    def _build_graph(
        self,
        similarity_matrix: np.ndarray,
        n: int,
    ) -> nx.Graph:
        """Build semantic graph from similarity matrix.
        
        Args:
            similarity_matrix: The similarity matrix.
            n: Number of sentences.
            
        Returns:
            NetworkX graph where nodes are sentence indices and edges
            connect sentences with similarity > threshold.
        """
        graph = nx.Graph()
        graph.add_nodes_from(range(n))
        
        # Add edges for similar sentences
        for i in range(n):
            for j in range(i + 1, n):
                if similarity_matrix[i, j] > self.threshold:
                    graph.add_edge(i, j)
        
        return graph

    def _find_maximal_cliques(self, graph: nx.Graph) -> List[Set[int]]:
        """Find all maximal cliques in the graph.
        
        Args:
            graph: The semantic graph.
            
        Returns:
            List of sets, where each set contains sentence indices in a clique.
        """
        cliques = [set(clique) for clique in nx.find_cliques(graph)]
        return cliques

    def _cliques_to_segments(
        self,
        cliques: List[Set[int]],
        n: int,
    ) -> List[List[int]]:
        """Convert cliques to initial segments.
        
        Args:
            cliques: List of cliques (sets of sentence indices).
            n: Number of sentences.
            
        Returns:
            List of segments, where each segment is a sorted list of
            consecutive sentence indices.
        """
        # Map each sentence to its cliques
        sentence_to_cliques = {i: [] for i in range(n)}
        for clique in cliques:
            for sent_idx in clique:
                sentence_to_cliques[sent_idx].append(clique)
        
        # Assign each sentence to the largest clique it belongs to
        segment_map = {}
        for sent_idx in range(n):
            if sentence_to_cliques[sent_idx]:
                # Find the largest clique containing this sentence
                largest_clique = max(
                    sentence_to_cliques[sent_idx],
                    key=len
                )
                segment_map[sent_idx] = largest_clique
        
        # Group consecutive sentences in the same clique into segments
        segments = []
        current_segment = []
        current_clique = None
        
        for sent_idx in range(n):
            clique = segment_map.get(sent_idx)
            
            if clique == current_clique:
                current_segment.append(sent_idx)
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = [sent_idx] if clique else []
                current_clique = clique
        
        if current_segment:
            segments.append(current_segment)
        
        return segments

    def _merge_small_segments(
        self,
        segments: List[List[int]],
        similarity_matrix: np.ndarray,
        n: int,
    ) -> List[List[int]]:
        """Merge segments smaller than min_seg_size with their neighbors.
        
        Args:
            segments: List of segments.
            similarity_matrix: The similarity matrix.
            n: Number of sentences.
            
        Returns:
            List of merged segments.
        """
        if not segments:
            return segments
        
        merged = []
        i = 0
        
        while i < len(segments):
            seg = segments[i]
            
            # If segment is too small, merge with neighbor
            if len(seg) < self.min_seg_size:
                # Find best neighbor (left or right)
                best_neighbor = None
                best_similarity = -1.0
                merge_direction = None
                
                # Check left neighbor
                if i > 0:
                    left_seg = segments[i - 1]
                    # Compute similarity between last sentence of left segment
                    # and first sentence of current segment
                    sim = similarity_matrix[left_seg[-1], seg[0]]
                    if sim > best_similarity:
                        best_similarity = sim
                        best_neighbor = i - 1
                        merge_direction = "left"
                
                # Check right neighbor
                if i < len(segments) - 1:
                    right_seg = segments[i + 1]
                    # Compute similarity between last sentence of current segment
                    # and first sentence of right segment
                    sim = similarity_matrix[seg[-1], right_seg[0]]
                    if sim > best_similarity:
                        best_similarity = sim
                        best_neighbor = i + 1
                        merge_direction = "right"
                
                # Merge with best neighbor
                if best_neighbor is not None:
                    if merge_direction == "left":
                        # Merge into left segment
                        segments[best_neighbor].extend(seg)
                        # Skip current segment (already merged)
                        i += 1
                        continue
                    else:
                        # Merge into current segment (will merge with right later)
                        seg.extend(segments[best_neighbor])
                        segments.pop(best_neighbor)
                        # Don't increment i, check again
                        continue
            
            merged.append(seg)
            i += 1
        
        return merged

    def _segments_to_boundaries(
        self,
        segments: List[List[int]],
        n: int,
    ) -> List[int]:
        """Convert segments to boundary indices.
        
        Args:
            segments: List of segments.
            n: Number of sentences.
            
        Returns:
            List of boundary indices.
        """
        boundaries = []
        
        for seg in segments:
            # Boundary is after the last sentence of each segment (except the last)
            if seg and seg[-1] < n - 1:
                boundaries.append(seg[-1])
        
        # Remove duplicates and sort
        boundaries = sorted(set(boundaries))
        
        return boundaries
