"""Thin client for the local Ollama HTTP API.

Docs (Ollama): https://github.com/ollama/ollama/blob/main/docs/api.md

We use /api/chat because it's better suited for structured prompting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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


class OllamaError(RuntimeError):
    pass


def chat(
    *,
    config: OllamaConfig,
    messages: List[Dict[str, str]],
    response_format_json: bool = True,
    timeout_s: float = 120.0,
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
    if not isinstance(content, str):
        raise OllamaError(f"Unexpected message content type: {type(content)}")

    return content
