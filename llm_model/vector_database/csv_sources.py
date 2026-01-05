from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

from .sqlite_store import DocRecord


@dataclass(frozen=True)
class SourcePaths:
    atu_csv: Path
    motif_csv: Path


def iter_atu_records(csv_path: Path) -> Iterator[DocRecord]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            atu_number = (row.get("atu_number") or "").strip()
            title = (row.get("title") or "").strip()
            description = (row.get("description") or "").strip()
            level_1 = (row.get("level_1_category") or "").strip()
            level_2 = (row.get("level_2_category") or "").strip()
            level_3 = (row.get("level_3_category") or "").strip()
            category_range = (row.get("category_range") or "").strip()
            detail_url = (row.get("detail_url") or "").strip()

            if not atu_number:
                continue

            text = (
                f"ATU {atu_number}: {title}\n"
                f"Category: {level_1} > {level_2} > {level_3} ({category_range})\n"
                f"Description: {description}"
            ).strip()

            metadata = {
                "atu_number": atu_number,
                "title": title,
                "level_1_category": level_1,
                "level_2_category": level_2,
                "level_3_category": level_3,
                "category_range": category_range,
                "detail_url": detail_url,
            }

            yield DocRecord(
                collection="atu",
                doc_key=f"atu:{atu_number}",
                text=text,
                metadata=metadata,
            )


def iter_motif_records(csv_path: Path) -> Iterator[DocRecord]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("code") or "").strip().strip('"')
            motif = (row.get("MOTIF") or "").strip().strip('"')
            chapter = (row.get("chapter") or "").strip().strip('"')
            division1 = (row.get("division1") or "").strip().strip('"')
            division2 = (row.get("division2") or "").strip().strip('"')
            division3 = (row.get("division3") or "").strip().strip('"')

            if not code or not motif:
                continue

            # Keep the main searchable text short and semantically focused.
            text = (
                f"Motif {code}: {motif}\n"
                f"Chapter: {chapter}\n"
                f"Divisions: {division1} | {division2} | {division3}"
            ).strip()

            metadata = {
                "code": code,
                "motif": motif,
                "chapter": chapter,
                "division1": division1,
                "division2": division2,
                "division3": division3,
            }

            yield DocRecord(
                collection="motif",
                doc_key=f"motif:{code}",
                text=text,
                metadata=metadata,
            )
