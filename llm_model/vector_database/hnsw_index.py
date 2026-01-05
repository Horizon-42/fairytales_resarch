from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class HNSWConfig:
    space: str = "cosine"  # cosine distance; similarity = 1 - distance
    ef_construction: int = 200
    m: int = 32
    ef_search: int = 64


class HNSWIndex:
    def __init__(self, *, dim: int, config: Optional[HNSWConfig] = None):
        self.dim = int(dim)
        self.config = config or HNSWConfig()

        import hnswlib  # local dependency

        self._hnswlib = hnswlib
        self._index = hnswlib.Index(space=self.config.space, dim=self.dim)
        self._initialized = False

    def init(self, *, max_elements: int) -> None:
        self._index.init_index(
            max_elements=int(max_elements),
            ef_construction=int(self.config.ef_construction),
            M=int(self.config.m),
        )
        self._index.set_ef(int(self.config.ef_search))
        self._initialized = True

    def add(self, *, vectors: Sequence[Sequence[float]], ids: Sequence[int]) -> None:
        if not self._initialized:
            raise RuntimeError("Index not initialized")
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids length mismatch")
        if not vectors:
            return

        arr = np.asarray(vectors, dtype=np.float32)
        self._index.add_items(arr, np.asarray(ids, dtype=np.int64))

    def knn(self, *, vector: Sequence[float], k: int) -> Tuple[List[int], List[float]]:
        if not self._initialized:
            raise RuntimeError("Index not initialized")
        vec = np.asarray([vector], dtype=np.float32)
        labels, distances = self._index.knn_query(vec, k=int(k))
        return labels[0].tolist(), distances[0].tolist()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._index.save_index(str(path))

    def load(self, path: Path, *, max_elements: int) -> None:
        # Must be initialized before load in hnswlib.
        self.init(max_elements=max_elements)
        self._index.load_index(str(path))
        self._index.set_ef(int(self.config.ef_search))

    def get_current_count(self) -> int:
        return int(self._index.get_current_count())
