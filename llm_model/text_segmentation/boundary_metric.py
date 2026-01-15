"""Boundary Segmentation Metric for evaluating text segmentation."""

from __future__ import annotations

from typing import List, Set, Tuple


class BoundarySegmentationMetric:
    """Boundary Segmentation Metric (B) for evaluating segmentation quality.
    
    This metric evaluates how well predicted boundaries match reference
    boundaries, using a formula that accounts for exact matches, near misses,
    insertions, and deletions.
    """

    def __init__(self, tolerance: int = 2):
        """Initialize the metric.
        
        Args:
            tolerance: Tolerance (n_t) for near misses. A boundary is considered
                a near miss if it's within tolerance positions of a reference
                boundary. Default is 2 (allows 1 sentence deviation).
        """
        self.tolerance = tolerance

    def calculate(
        self,
        reference_boundaries: List[int],
        hypothesis_boundaries: List[int],
    ) -> float:
        """Calculate boundary similarity score.
        
        Args:
            reference_boundaries: List of reference (ground truth) boundary indices.
            hypothesis_boundaries: List of predicted boundary indices.
            
        Returns:
            Boundary similarity score B in range [0, 1], where 1 is perfect match.
        """
        ref_set = set(reference_boundaries)
        hyp_set = set(hypothesis_boundaries)
        
        # Find exact matches
        matches = ref_set & hyp_set
        n_matches = len(matches)
        
        # Find near misses (within tolerance)
        near_misses = self._find_near_misses(
            reference_boundaries,
            hypothesis_boundaries,
            matches,
        )
        
        # Find insertions and deletions
        insertions, deletions = self._find_edit_operations(
            reference_boundaries,
            hypothesis_boundaries,
            matches,
            near_misses,
        )
        
        # Calculate score using the formula
        score = self._compute_score(
            n_matches,
            near_misses,
            insertions,
            deletions,
            len(reference_boundaries),
        )
        
        return score

    def _find_near_misses(
        self,
        reference_boundaries: List[int],
        hypothesis_boundaries: List[int],
        matches: Set[int],
    ) -> List[Tuple[int, int]]:
        """Find near miss pairs (within tolerance distance).
        
        Args:
            reference_boundaries: Reference boundaries.
            hypothesis_boundaries: Hypothesis boundaries.
            matches: Set of exact matches (to exclude).
            
        Returns:
            List of (ref_idx, hyp_idx) pairs for near misses.
        """
        near_misses = []
        used_ref = set(matches)
        used_hyp = set(matches)
        
        for ref_idx in reference_boundaries:
            if ref_idx in used_ref:
                continue
            
            for hyp_idx in hypothesis_boundaries:
                if hyp_idx in used_hyp:
                    continue
                
                distance = abs(ref_idx - hyp_idx)
                if distance < self.tolerance:
                    near_misses.append((ref_idx, hyp_idx))
                    used_ref.add(ref_idx)
                    used_hyp.add(hyp_idx)
                    break
        
        return near_misses

    def _find_edit_operations(
        self,
        reference_boundaries: List[int],
        hypothesis_boundaries: List[int],
        matches: Set[int],
        near_misses: List[Tuple[int, int]],
    ) -> Tuple[List[int], List[int]]:
        """Find insertions and deletions.
        
        Args:
            reference_boundaries: Reference boundaries.
            hypothesis_boundaries: Hypothesis boundaries.
            matches: Set of exact matches.
            near_misses: List of near miss pairs.
            
        Returns:
            Tuple of (insertions, deletions) where each is a list of indices.
        """
        # Get indices involved in near misses
        near_miss_ref = {pair[0] for pair in near_misses}
        near_miss_hyp = {pair[1] for pair in near_misses}
        
        # Insertions: in hypothesis but not in reference (and not near miss)
        insertions = [
            idx for idx in hypothesis_boundaries
            if idx not in matches and idx not in near_miss_hyp
        ]
        
        # Deletions: in reference but not in hypothesis (and not near miss)
        deletions = [
            idx for idx in reference_boundaries
            if idx not in matches and idx not in near_miss_ref
        ]
        
        return insertions, deletions

    def _compute_score(
        self,
        n_matches: int,
        near_misses: List[Tuple[int, int]],
        insertions: List[int],
        deletions: List[int],
        n_ref: int,
    ) -> float:
        """Compute the boundary similarity score using the formula.
        
        Formula: B = 1 - (|A_ε| + w_span(T_ε, n_t)) / (|A_ε| + |T_ε| + |B_M|)
        
        Where:
        - B_M: Exact matches
        - T_ε: Near misses
        - A_ε: Edit operations (insertions + deletions)
        - w_span: Penalty weight for near misses
        
        Args:
            n_matches: Number of exact matches.
            near_misses: List of near miss pairs.
            insertions: List of insertion indices.
            deletions: List of deletion indices.
            n_ref: Total number of reference boundaries.
            
        Returns:
            Boundary similarity score.
        """
        n_edits = len(insertions) + len(deletions)
        n_near_misses = len(near_misses)
        
        # Calculate penalty for near misses
        # w_span is typically half the penalty of insertions/deletions
        # when tolerance is 2
        w_span = 0.0
        for ref_idx, hyp_idx in near_misses:
            distance = abs(ref_idx - hyp_idx)
            # Normalize distance penalty (half weight for near misses)
            w_span += 0.5 * (distance / self.tolerance)
        
        # Apply formula
        denominator = n_edits + n_near_misses + n_matches
        if denominator == 0:
            # Perfect match (no boundaries or all matched)
            return 1.0
        
        numerator = n_edits + w_span
        score = 1.0 - (numerator / denominator)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
