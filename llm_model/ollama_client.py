"""Thin client for the local Ollama HTTP API.

Docs (Ollama): https://github.com/ollama/ollama/blob/main/docs/api.md

We use /api/chat because it's better suited for structured prompting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import requests


@dataclass(frozen=True)
class OllamaConfig:
    """Connection + generation settings for Ollama."""

    base_url: str = "http://localhost:11434"
    model: str = "llama3.1"

    # Reasonable defaults; tune per your hardware/model.
    temperature: float = 0.2
    top_p: float = 0.9
    num_ctx: int = 8192
    
    # Performance optimization options
    num_predict: Optional[int] = None  # Max tokens to generate (None = default 128, -1 = unlimited)
    num_thread: Optional[int] = None   # CPU threads (None = auto-detect)
    
    # Control thinking mode for models that support it (e.g., qwen3)
    # Set to False to disable thinking mode, True to enable, None to use model default
    think: Optional[bool] = None


class OllamaError(RuntimeError):
    pass


def list_local_models(
    *,
    base_url: str,
    timeout_s: float = 5.0,
) -> List[str]:
    """List locally available model names from Ollama.

    Uses GET /api/tags.

    Returns:
        A list of model names like ["qwen3:8b", "qwen3-embedding:4b", ...].
    """

    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        resp = requests.get(url, timeout=timeout_s)
    except requests.RequestException as exc:
        raise OllamaError(f"Failed to reach Ollama at {url}: {exc}") from exc

    if resp.status_code != 200:
        raise OllamaError(f"Ollama /api/tags failed: HTTP {resp.status_code}: {resp.text[:500]}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise OllamaError(f"Ollama returned non-JSON response on {url}: {resp.text[:500]}") from exc

    models = data.get("models")
    if not isinstance(models, list):
        raise OllamaError(f"Unexpected /api/tags response shape: {data}")

    names: List[str] = []
    for m in models:
        if not isinstance(m, dict):
            continue
        name = m.get("name")
        if isinstance(name, str) and name:
            names.append(name)

    return names


def embed(
    *,
    base_url: str,
    model: str,
    inputs: Sequence[str],
    instruction: str | None = None,
    timeout_s: float = 600.0,
) -> List[List[float]]:
    """Generate embeddings for one or more input strings.

    This function prefers Ollama's batch endpoint when available.

    Endpoints (varies by Ollama version):
    - POST /api/embed  (batch): {model, input: [..]} -> {embeddings: [[..], ...]}
    - POST /api/embeddings (single): {model, prompt} -> {embedding: [..]}

    Args:
        base_url: Ollama server URL (e.g., http://localhost:11434)
        model: Embedding model name (e.g., qwen3-embedding:4b)
        inputs: Texts to embed.
        instruction: Optional instruction to prepend to each input text for instruction-based
                    embeddings. If provided, each input will be formatted as "{instruction} {text}".
        timeout_s: HTTP timeout.

    Returns:
        List of embedding vectors aligned with inputs.
    """

    if not inputs:
        return []

    # Apply instruction if provided
    processed_inputs = list(inputs)
    if instruction:
        processed_inputs = [f"{instruction} {text}" if text.strip() else text for text in inputs]

    base = base_url.rstrip("/")

    # 1) Prefer batch endpoint
    url_batch = f"{base}/api/embed"
    payload_batch: Dict[str, Any] = {
        "model": model,
        "input": processed_inputs,
    }
    try:
        resp = requests.post(url_batch, json=payload_batch, timeout=timeout_s)
        if resp.status_code == 200:
            data = resp.json()
            embeddings = data.get("embeddings")
            if isinstance(embeddings, list) and all(isinstance(v, list) for v in embeddings):
                return embeddings  # type: ignore[return-value]
        # If not supported, fall through to single-request API.
    except requests.RequestException:
        # Fall back to single endpoint below.
        pass
    except ValueError as exc:
        raise OllamaError(
            f"Ollama returned non-JSON response on {url_batch}: {resp.text[:500]}"  # type: ignore[name-defined]
        ) from exc

    # 2) Fallback: single embedding endpoint
    url_single = f"{base}/api/embeddings"
    out: List[List[float]] = []
    for text in processed_inputs:
        payload_single: Dict[str, Any] = {
            "model": model,
            "prompt": text,
        }
        try:
            resp = requests.post(url_single, json=payload_single, timeout=timeout_s)
        except requests.RequestException as exc:
            raise OllamaError(f"Failed to reach Ollama at {url_single}: {exc}") from exc

        if resp.status_code != 200:
            raise OllamaError(
                f"Ollama /api/embeddings failed: HTTP {resp.status_code}: {resp.text[:500]}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise OllamaError(
                f"Ollama returned non-JSON response on {url_single}: {resp.text[:500]}"
            ) from exc

        emb = data.get("embedding")
        if not isinstance(emb, list):
            raise OllamaError(f"Unexpected embeddings response shape: {data}")
        out.append(emb)

    return out


def chat(
    *,
    config: OllamaConfig,
    messages: List[Dict[str, str]],
    response_format_json: bool = True,
    timeout_s: float = 300.0,
) -> str:
    """Send a chat request and return the assistant content as a string.

    Args:
        config: OllamaConfig with base_url/model and options.
        messages: List of {role: "system"|"user"|"assistant", content: str}.
        response_format_json: If True, requests a JSON response format (if supported).
        timeout_s: HTTP timeout.

    Raises:
        OllamaError: on non-200 response or invalid payload.

    Returns:
        Assistant message content.
    """

    url = f"{config.base_url.rstrip('/')}/api/chat"

    options: Dict[str, Any] = {
        "temperature": config.temperature,
        "top_p": config.top_p,
        "num_ctx": config.num_ctx,
    }
    
    # Add performance optimization options
    if config.num_predict is not None:
        options["num_predict"] = config.num_predict
    
    if config.num_thread is not None:
        options["num_thread"] = config.num_thread
    
    # Add think parameter if explicitly set (for qwen3 and other thinking models)
    # Set to False by default for better performance
    if config.think is not None:
        options["think"] = config.think
    elif config.model.startswith("qwen3"):
        # Disable thinking mode for qwen3 by default for faster inference
        options["think"] = False

    payload: Dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "stream": False,
        "options": options,
    }

    # Ollama recently supports a structured response hint. If not supported,
    # it is ignored by older versions.
    if response_format_json:
        payload["format"] = "json"

    try:
        resp = requests.post(url, json=payload, timeout=timeout_s)
    except requests.RequestException as exc:
        raise OllamaError(f"Failed to reach Ollama at {url}: {exc}") from exc

    if resp.status_code != 200:
        raise OllamaError(
            f"Ollama /api/chat failed: HTTP {resp.status_code}: {resp.text[:500]}"
        )

    try:
        data = resp.json()
    except ValueError as exc:
        raise OllamaError(f"Ollama returned non-JSON response: {resp.text[:500]}") from exc

    # Expected shape: { message: { role: ..., content: ... }, ... }
    message = data.get("message")
    if not isinstance(message, dict) or "content" not in message:
        raise OllamaError(f"Unexpected Ollama response shape: {data}")

    content = message.get("content")
    if content is None:
        raise OllamaError(f"Ollama response has None content. Full response: {data}")
    
    if not isinstance(content, str):
        raise OllamaError(f"Unexpected message content type: {type(content)}, value: {repr(content)}")

    # Content can be empty string in some cases (model refused to answer, etc.)
    # Return as-is - caller should handle empty responses
    return content
