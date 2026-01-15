"""Magnetic Clustering algorithm for text segmentation."""

from __future__ import annotations

from typing import List, Optional

import numpy as np
from scipy.ndimage import gaussian_filter1d

from .similarity_matrix import SimilarityMatrixBuilder


class MagneticClustering:
    """Magnetic Clustering algorithm for text segmentation.
    
    This algorithm simulates magnetic attraction, where text blocks are
    "attracted" left or right to form clusters. Boundaries are detected
    where the magnetic force changes direction.
    """

    def __init__(
        self,
        similarity_builder: SimilarityMatrixBuilder,
        window_size: int = 3,
        weights: Optional[List[float]] = None,
        filter_width: float = 2.0,
    ):
        """Initialize Magnetic Clustering.
        
        Args:
            similarity_builder: SimilarityMatrixBuilder instance.
            window_size: Size of the window (d) for computing magnetic force.
            weights: Weight parameters w_k for distances. If None, uses
                exponential decay: w_k = exp(-k/2).
            filter_width: Standard deviation for Gaussian smoothing filter.
        """
        self.similarity_builder = similarity_builder
        self.window_size = window_size
        self.filter_width = filter_width
        
        # Set default weights if not provided
        if weights is None:
            # Exponential decay: closer neighbors have higher weight
            self.weights = [np.exp(-k / 2.0) for k in range(1, window_size + 1)]
        else:
            if len(weights) != window_size:
                raise ValueError(f"weights length ({len(weights)}) must equal window_size ({window_size})")
            self.weights = weights

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
        
        # Compute magnetic forces
        magnetic_forces = self._compute_magnetic_forces(similarity_matrix, n)
        
        # Apply smoothing
        smoothed_forces = self._smooth_forces(magnetic_forces)
        
        # Find boundaries (zero crossings from negative to positive)
        boundaries = self._find_boundaries(smoothed_forces)
        
        return boundaries

    def _compute_magnetic_forces(
        self,
        similarity_matrix: np.ndarray,
        n: int,
    ) -> np.ndarray:
        """Compute magnetic force b_i for each sentence gap.
        
        Args:
            similarity_matrix: The similarity matrix.
            n: Number of sentences.
            
        Returns:
            Array of magnetic forces, shape (n-1,).
        """
        forces = []
        
        for i in range(n - 1):
            # Compute right attraction (forward)
            right_attraction = 0.0
            for k in range(1, self.window_size + 1):
                j = i + k
                if j < n:
                    sim = self.similarity_builder.get_approximate_similarity(
                        similarity_matrix, i, j
                    )
                    right_attraction += self.weights[k - 1] * sim
            
            # Compute left attraction (backward)
            left_attraction = 0.0
            for k in range(1, self.window_size + 1):
                j = i - k
                if j >= 0:
                    sim = self.similarity_builder.get_approximate_similarity(
                        similarity_matrix, i, j
                    )
                    left_attraction += self.weights[k - 1] * sim
            
            # Magnetic force is the difference
            force = right_attraction - left_attraction
            forces.append(force)
        
        return np.array(forces)

    def _smooth_forces(self, forces: np.ndarray) -> np.ndarray:
        """Apply Gaussian smoothing to magnetic forces.
        
        Args:
            forces: Raw magnetic forces.
            
        Returns:
            Smoothed forces.
        """
        if len(forces) == 0:
            return forces
        
        # Use Gaussian filter for smoothing
        smoothed = gaussian_filter1d(forces, sigma=self.filter_width)
        return smoothed

    def _find_boundaries(self, smoothed_forces: np.ndarray) -> List[int]:
        """Find boundaries where force changes from negative to positive.
        
        Args:
            smoothed_forces: Smoothed magnetic forces.
            
        Returns:
            List of boundary indices.
        """
        boundaries = []
        
        for i in range(len(smoothed_forces) - 1):
            # Boundary: b_i < 0 and b_{i+1} > 0
            if smoothed_forces[i] < 0 and smoothed_forces[i + 1] > 0:
                boundaries.append(i)
        
        return boundaries
