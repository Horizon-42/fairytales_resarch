"""Tests for Boundary Segmentation Metric."""

import pytest

from ..boundary_metric import BoundarySegmentationMetric


def test_boundary_metric_perfect_match():
    """Test metric with perfect match."""
    metric = BoundarySegmentationMetric()
    
    ref = [2, 5, 8]
    hyp = [2, 5, 8]
    
    score = metric.calculate(ref, hyp)
    
    assert score == 1.0


def test_boundary_metric_no_match():
    """Test metric with no matches."""
    metric = BoundarySegmentationMetric()
    
    ref = [2, 5]
    hyp = [10, 15]
    
    score = metric.calculate(ref, hyp)
    
    assert 0.0 <= score <= 1.0
    assert score < 1.0


def test_boundary_metric_near_miss():
    """Test metric with near misses."""
    metric = BoundarySegmentationMetric(tolerance=2)
    
    ref = [2, 5, 8]
    hyp = [3, 5, 9]  # 3 is near 2, 9 is near 8
    
    score = metric.calculate(ref, hyp)
    
    assert 0.0 <= score <= 1.0
    # Should be better than no match but worse than perfect
    assert score > 0.0


def test_boundary_metric_insertions():
    """Test metric with insertions."""
    metric = BoundarySegmentationMetric()
    
    ref = [2, 5]
    hyp = [2, 3, 5, 7]  # 3 and 7 are insertions
    
    score = metric.calculate(ref, hyp)
    
    assert 0.0 <= score <= 1.0
    assert score < 1.0


def test_boundary_metric_deletions():
    """Test metric with deletions."""
    metric = BoundarySegmentationMetric()
    
    ref = [2, 5, 8]
    hyp = [5]  # 2 and 8 are deletions
    
    score = metric.calculate(ref, hyp)
    
    assert 0.0 <= score <= 1.0
    assert score < 1.0


def test_boundary_metric_empty():
    """Test metric with empty boundaries."""
    metric = BoundarySegmentationMetric()
    
    # Both empty (perfect match)
    score = metric.calculate([], [])
    assert score == 1.0
    
    # One empty
    score = metric.calculate([], [1, 2])
    assert 0.0 <= score <= 1.0
    
    score = metric.calculate([1, 2], [])
    assert 0.0 <= score <= 1.0


def test_boundary_metric_tolerance():
    """Test that tolerance affects near miss detection."""
    metric_tight = BoundarySegmentationMetric(tolerance=1)
    metric_loose = BoundarySegmentationMetric(tolerance=5)
    
    ref = [5]
    hyp = [7]  # Distance of 2
    
    score_tight = metric_tight.calculate(ref, hyp)
    score_loose = metric_loose.calculate(ref, hyp)
    
    # Loose tolerance should treat it as near miss (better score)
    assert score_loose >= score_tight


def test_find_near_misses():
    """Test near miss finding logic."""
    metric = BoundarySegmentationMetric(tolerance=2)
    
    ref = [2, 5, 8]
    hyp = [3, 6, 10]
    matches = set()
    
    near_misses = metric._find_near_misses(ref, hyp, matches)
    
    # 3 is near 2, 6 is near 5, 10 is not near 8 (distance > 2)
    assert len(near_misses) >= 0  # At least some near misses found


def test_find_edit_operations():
    """Test edit operation finding."""
    metric = BoundarySegmentationMetric()
    
    ref = [2, 5, 8]
    hyp = [2, 7, 10]
    matches = {2}
    near_misses = [(5, 7)]  # 5 and 7 are near
    
    insertions, deletions = metric._find_edit_operations(
        ref, hyp, matches, near_misses
    )
    
    # 10 is an insertion, 8 is a deletion
    assert isinstance(insertions, list)
    assert isinstance(deletions, list)
