"""Utilities for safely extracting JSON from model output."""

from __future__ import annotations

import json
from typing import Any


class JsonExtractionError(ValueError):
    pass


def _strip_code_fences(s: str) -> str:
    """Remove common markdown fences if the model ignored instructions."""
    s = s.strip()
    if s.startswith("```"):
        # Remove first line fence and trailing fence.
        lines = s.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return s


def loads_strict_json(text: str) -> Any:
    """Parse JSON, trying a couple of safe normalizations.

    We do NOT attempt aggressive repair; the goal is to keep failures obvious.
    """
    candidate = _strip_code_fences(text)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        # Common failure mode: extra text before/after JSON.
        # Try to extract the first top-level JSON object.
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise JsonExtractionError(f"Failed to parse model JSON: {exc}") from exc
