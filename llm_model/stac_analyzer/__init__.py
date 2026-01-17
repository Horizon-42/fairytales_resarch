"""STAC (Situation, Task, Action, Consequence) analysis module.

This module provides functionality to classify sentences into STAC categories
and extract relevant information based on the classification.
"""

from __future__ import annotations

from .stac_analyzer import (
    STACAnalysisError,
    STACAnalyzerConfig,
    STACCategory,
    analyze_stac,
    analyze_stac_batch,
)

__all__ = [
    "STACAnalysisError",
    "STACAnalyzerConfig",
    "STACCategory",
    "analyze_stac",
    "analyze_stac_batch",
]
