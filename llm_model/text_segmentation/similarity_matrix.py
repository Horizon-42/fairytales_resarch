"""Similarity matrix construction for text segmentation."""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityMatrixBuilder:
    """Builds cosine similarity matrix from sentence embeddings.
    
    This class handles:
    - Converting sentences to embeddings using LLM
    - Computing cosine similarity matrix
    - Optimizing storage for linear segmentation (local neighborhood only)
    """

    def __init__(
        self,
        embedding_func: callable,
        context_window: int = 2,
        local_neighborhood: Optional[int] = None,
    ):
        """Initialize the similarity matrix builder.
        
        Args:
            embedding_func: Function that takes a list of strings and returns
                a list of embedding vectors. Should have signature:
                embeddings = embedding_func(texts: List[str]) -> List[List[float]]
            context_window: Number of consecutive sentences to use as context
                when generating embeddings. Default is 2.
            local_neighborhood: If set, only compute similarity for pairs within
                this distance from diagonal. If None, compute full matrix.
        """
        self.embedding_func = embedding_func
        self.context_window = context_window
        self.local_neighborhood = local_neighborhood

    def build_embeddings(
        self,
        sentences: List[str],
    ) -> np.ndarray:
        """Convert sentences to embeddings with optional context window.
        
        Args:
            sentences: List of sentence strings.
            
        Returns:
            Array of shape (n_sentences, embedding_dim) containing embeddings.
        """
        if not sentences:
            return np.array([])
        
        # Build context windows if specified
        if self.context_window > 1:
            context_sentences = self._build_context_windows(sentences)
        else:
            context_sentences = sentences
        
        # Get embeddings
        embeddings = self.embedding_func(context_sentences)
        
        # Convert to numpy array
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)
        
        return embeddings

    def _build_context_windows(self, sentences: List[str]) -> List[str]:
        """Build context windows by concatenating consecutive sentences.
        
        Args:
            sentences: List of sentence strings.
            
        Returns:
            List of context-windowed sentences.
        """
        if len(sentences) <= 1:
            return sentences
        
        context_sentences = []
        for i in range(len(sentences)):
            # Take up to context_window sentences starting from i
            window_sentences = sentences[i : i + self.context_window]
            context_sentences.append(" ".join(window_sentences))
        
        return context_sentences

    def build_similarity_matrix(
        self,
        sentences: List[str],
    ) -> np.ndarray:
        """Build cosine similarity matrix from sentences.
        
        Args:
            sentences: List of sentence strings.
            
        Returns:
            Similarity matrix of shape (n_sentences, n_sentences) where
            S[i, j] is the cosine similarity between sentence i and j.
        """
        if not sentences:
            return np.array([])
        
        # Get embeddings
        embeddings = self.build_embeddings(sentences)
        n = len(embeddings)
        
        if n == 0:
            return np.array([])
        
        # Compute full similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # If local neighborhood is specified, mask out distant pairs
        if self.local_neighborhood is not None:
            mask = np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]) > self.local_neighborhood
            similarity_matrix[mask] = 0.0
        
        return similarity_matrix

    def get_approximate_similarity(
        self,
        similarity_matrix: np.ndarray,
        i: int,
        j: int,
    ) -> float:
        """Get approximate similarity value for matrix position (i, j).
        
        If the value is outside the matrix or masked, use the average
        of values at the same diagonal offset.
        
        Args:
            similarity_matrix: The similarity matrix.
            i: Row index.
            j: Column index.
            
        Returns:
            Approximate similarity value.
        """
        n = similarity_matrix.shape[0]
        
        # If within bounds and not masked, return actual value
        if 0 <= i < n and 0 <= j < n:
            val = similarity_matrix[i, j]
            # If not masked (non-zero or within local neighborhood), return it
            if val != 0.0 or self.local_neighborhood is None:
                return val
        
        # Otherwise, compute average for same diagonal offset
        offset = i - j
        diagonal_values = []
        for k in range(n):
            diag_i = k + offset
            if 0 <= diag_i < n:
                val = similarity_matrix[diag_i, k]
                if val != 0.0 or self.local_neighborhood is None:
                    diagonal_values.append(val)
        
        if diagonal_values:
            return np.mean(diagonal_values)
        else:
            # Fallback: return 0.0 if no values found
            return 0.0
