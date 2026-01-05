"""Local vector database utilities for ATU types and motifs.

This package builds and queries a lightweight local vector database backed by:
- hnswlib for ANN vector search
- sqlite3 for document + metadata storage

Embeddings are produced by Ollama using an embedding model (default: qwen3-embedding:4b).
"""

from .db import FairyVectorDB, VectorDBPaths

__all__ = ["FairyVectorDB", "VectorDBPaths"]
