"""Sentence-level event analysis package.

This package provides functionality to analyze sentences within the context
of a complete story, determining if they contain events and extracting
relevant information about events, including location, participants, and emotions.
"""

from __future__ import annotations

from .analyzer import (
    SentenceAnalysisError,
    SentenceAnalyzerConfig,
    analyze_sentence,
)

__all__ = [
    "SentenceAnalysisError",
    "SentenceAnalyzerConfig",
    "analyze_sentence",
]
