#!/usr/bin/env python3
"""Split datasets/ChineseTales/中国民间故事.md into separate story .txt files.

The input file is a book-like Markdown export that contains story boundaries in the form:

    【第一篇】
    牛郎织女
    ... story body ...

This script detects those boundary markers (the bracketed chapter label on its own line),
uses the following non-empty line as the story title, and writes each story into:

    datasets/ChineseTales/traditional_texts/CH_XXX_<title>.txt

By default it writes all 41 stories.

Usage:
  python3 scripts/split_traditional_chinese_tales_md.py
  python3 scripts/split_traditional_chinese_tales_md.py --force

"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = "datasets/ChineseTales/中国民间故事.md"
DEFAULT_OUT_DIR = "datasets/ChineseTales/traditional_texts"
DEFAULT_PREFIX = "CH"


_MARKER_ALONE_RE = re.compile(r"^【第[^】]+篇】\s*$")


@dataclass(frozen=True)
class StorySpan:
    title: str
    start_line: int  # 0-based inclusive (title line)
    end_line: int    # 0-based exclusive


def _is_marker_alone(line: str) -> bool:
    return bool(_MARKER_ALONE_RE.match(line.strip()))


def _next_non_empty(lines: list[str], start: int) -> int | None:
    i = start
    while i < len(lines):
        if lines[i].strip() != "":
            return i
        i += 1
    return None


def _sanitize_filename_component(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", " ", s)
    # Remove some brackets that often appear in titles.
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = s.replace("[", "_").replace("]", "_")
    s = s.replace(" ", "")
    s = s.strip("._")
    return s or "Untitled"


def _drop_known_headers_footers(lines: Iterable[str]) -> list[str]:
    """Remove obvious page headers/footers that appear as standalone lines."""
    junk = {
        "中国",
        "民间故事",
        "中国民间故事",
        "最畅销中外名著",
        "名 家 导 读 本",
        "名家导读",
        "Contents",
        "Table of Contents",
    }

    out: list[str] = []
    for line in lines:
        t = line.strip()
        if t in junk:
            continue
        out.append(line)
    return out


def _normalize_text(lines: list[str]) -> str:
    # Strip leading/trailing empty lines and collapse repeated empty lines.
    trimmed = [l.rstrip() for l in lines]

    # Remove obvious header/footer noise.
    trimmed = _drop_known_headers_footers(trimmed)

    # Collapse 3+ blank lines into 1 blank line.
    normalized: list[str] = []
    blank_run = 0
    for l in trimmed:
        if l.strip() == "":
            blank_run += 1
            if blank_run <= 1:
                normalized.append("")
            continue
        blank_run = 0
        normalized.append(l.strip())

    # Trim again.
    while normalized and normalized[0] == "":
        normalized.pop(0)
    while normalized and normalized[-1] == "":
        normalized.pop()

    return "\n".join(normalized) + "\n"


def find_story_spans(lines: list[str]) -> list[StorySpan]:
    marker_positions = [i for i, l in enumerate(lines) if _is_marker_alone(l)]
    spans: list[StorySpan] = []

    for idx, marker_i in enumerate(marker_positions):
        title_i = _next_non_empty(lines, marker_i + 1)
        if title_i is None:
            continue
        title = lines[title_i].strip()
        if not title:
            continue

        end_i = marker_positions[idx + 1] if idx + 1 < len(marker_positions) else len(lines)
        spans.append(StorySpan(title=title, start_line=title_i, end_line=end_i))

    return spans


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=DEFAULT_INPUT)
    p.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    p.add_argument("--prefix", default=DEFAULT_PREFIX)
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    p.add_argument("--limit", type=int, default=0, help="Only write first N stories (0 = all)")

    args = p.parse_args(argv)

    in_path = Path(args.input)
    out_dir = Path(args.out_dir)

    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    lines = in_path.read_text(encoding="utf-8").splitlines()
    spans = find_story_spans(lines)

    if args.limit and args.limit > 0:
        spans = spans[: args.limit]

    written = 0
    for i, span in enumerate(spans, start=1):
        index = f"{i:03d}"
        safe_title = _sanitize_filename_component(span.title)
        filename = f"{args.prefix}_{index}_{safe_title}.txt"
        out_path = out_dir / filename

        if out_path.exists() and not args.force:
            continue

        story_lines = lines[span.start_line : span.end_line]
        text = _normalize_text(story_lines)

        # Ensure the first line is exactly the title.
        if not text.startswith(span.title):
            text = f"{span.title}\n\n" + text

        out_path.write_text(text, encoding="utf-8")
        written += 1

    print(f"Detected stories: {len(find_story_spans(lines))}")
    print(f"Written: {written}")
    print(f"Output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
