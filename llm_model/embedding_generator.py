"""Reusable embedding generation utilities.

This module provides functions for generating embeddings from text using various providers.
"""

from __future__ import annotations

import os
from typing import List, Sequence

from llm_model.env import load_repo_dotenv
from llm_model.ollama_client import embed as ollama_embed


# Load environment variables if available
load_repo_dotenv()


def generate_embeddings(
    texts: Sequence[str],
    *,
    provider: str = "ollama",
    model: str | None = None,
    base_url: str | None = None,
    timeout_s: float = 600.0,
) -> List[List[float]]:
    """Generate embeddings for a list of texts.

    This function provides a unified interface for generating embeddings from different providers.
    Currently supports Ollama.

    Args:
        texts: List of text strings to generate embeddings for.
        provider: Embedding provider. Currently supports "ollama".
        model: Model name. If None, uses default from environment or "nomic-embed-text".
        base_url: Base URL for the provider. If None, uses default from environment or
                  "http://localhost:11434" for Ollama.
        timeout_s: Timeout in seconds for API requests.

    Returns:
        List of embedding vectors, one per input text. Each vector is a list of floats.

    Raises:
        ValueError: If provider is not supported.
        RuntimeError: If embedding generation fails.
    """
    if not texts:
        return []

    provider = provider.lower()

    if provider == "ollama":
        if model is None:
            model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        return ollama_embed(
            base_url=base_url,
            model=model,
            inputs=texts,
            timeout_s=timeout_s,
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}. Supported: 'ollama'")
