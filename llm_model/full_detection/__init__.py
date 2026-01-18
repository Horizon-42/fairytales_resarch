"""Full detection pipeline for narrative event extraction.

This package implements a comprehensive pipeline using LangChain to process
story segments and generate structured narrative events following the v3 JSON schema.
"""

from __future__ import annotations

from .pipeline import PipelineError, build_pipeline, run_pipeline, run_pipeline_batch
from .pipeline_state import PipelineState
from .story_processor import (
    StoryProcessingError,
    generate_story_summary,
    process_story,
    process_story_segment,
)

__all__ = [
    "PipelineError",
    "PipelineState",
    "build_pipeline",
    "run_pipeline",
    "run_pipeline_batch",
    "StoryProcessingError",
    "generate_story_summary",
    "process_story",
    "process_story_segment",
]
