from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class DocRecord:
    collection: str
    doc_key: str
    text: str
    metadata: Dict[str, Any]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
          id INTEGER PRIMARY KEY,
          collection TEXT NOT NULL,
          doc_key TEXT NOT NULL,
          text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          UNIQUE(collection, doc_key)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_collection
        ON documents(collection);
        """
    )


def upsert_documents(
    conn: sqlite3.Connection, records: Iterable[DocRecord]
) -> None:
    rows = [
        (
            r.collection,
            r.doc_key,
            r.text,
            json.dumps(r.metadata, ensure_ascii=False),
        )
        for r in records
    ]
    conn.executemany(
        """
        INSERT INTO documents(collection, doc_key, text, metadata_json)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(collection, doc_key) DO UPDATE SET
          text=excluded.text,
          metadata_json=excluded.metadata_json;
        """,
        rows,
    )


def fetch_by_ids(
    conn: sqlite3.Connection, ids: Iterable[int]
) -> Dict[int, DocRecord]:
    ids_list = list(ids)
    if not ids_list:
        return {}

    placeholders = ",".join(["?"] * len(ids_list))
    cur = conn.execute(
        f"SELECT id, collection, doc_key, text, metadata_json FROM documents WHERE id IN ({placeholders})",
        ids_list,
    )

    out: Dict[int, DocRecord] = {}
    for row in cur.fetchall():
        doc_id, collection, doc_key, text, metadata_json = row
        out[int(doc_id)] = DocRecord(
            collection=str(collection),
            doc_key=str(doc_key),
            text=str(text),
            metadata=json.loads(metadata_json),
        )
    return out


def iter_collection(
    conn: sqlite3.Connection, collection: str
) -> Iterable[Tuple[int, DocRecord]]:
    cur = conn.execute(
        "SELECT id, collection, doc_key, text, metadata_json FROM documents WHERE collection=? ORDER BY id",
        (collection,),
    )
    for row in cur.fetchall():
        doc_id, collection, doc_key, text, metadata_json = row
        yield int(doc_id), DocRecord(
            collection=str(collection),
            doc_key=str(doc_key),
            text=str(text),
            metadata=json.loads(metadata_json),
        )


def count_collection(conn: sqlite3.Connection, collection: str) -> int:
    cur = conn.execute("SELECT COUNT(1) FROM documents WHERE collection=?", (collection,))
    value = cur.fetchone()
    return int(value[0]) if value else 0


def get_max_id(conn: sqlite3.Connection) -> Optional[int]:
    cur = conn.execute("SELECT MAX(id) FROM documents")
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else None
