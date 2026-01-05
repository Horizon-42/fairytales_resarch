from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VectorDBPaths:
    """Filesystem layout for the local vector database."""

    root_dir: Path

    @property
    def sqlite_path(self) -> Path:
        return self.root_dir / "docs.sqlite"

    @property
    def atu_index_path(self) -> Path:
        return self.root_dir / "atu_hnsw.bin"

    @property
    def motif_index_path(self) -> Path:
        return self.root_dir / "motif_hnsw.bin"

    @property
    def meta_path(self) -> Path:
        return self.root_dir / "meta.json"


def default_paths() -> VectorDBPaths:
    # Store under the package directory by default.
    here = Path(__file__).resolve().parent
    return VectorDBPaths(root_dir=here / "store")
