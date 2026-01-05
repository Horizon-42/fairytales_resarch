from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ChunkingConfig:
    max_chars: int = 1200
    overlap: int = 120


def chunk_text(text: str, *, config: ChunkingConfig | None = None) -> List[str]:
    cfg = config or ChunkingConfig()

    normalized = (text or "").strip()
    if not normalized:
        return []

    # Normalize whitespace a bit but keep sentence boundaries.
    normalized = normalized.replace("\r\n", "\n")

    chunks: List[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + cfg.max_chars)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(0, end - cfg.overlap)

    # Deduplicate identical chunks (can happen with tiny texts).
    out: List[str] = []
    seen = set()
    for c in chunks:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out
