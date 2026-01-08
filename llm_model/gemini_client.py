"""Thin client for Google Gemini (Generative Language API).

We intentionally use plain HTTP (requests) to avoid SDK lock-in.
The rest of the codebase talks in an Ollama-like message format:
  [{role: system|user|assistant, content: str}, ...]

Gemini API shape (v1beta, may evolve):
- POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=...

This module converts messages and returns the first candidate text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


class GeminiError(RuntimeError):
    pass


def _normalize_model_id(model: str) -> str:
    m = (model or "").strip()
    if m.startswith("models/"):
        m = m[len("models/") :]
    return m


@dataclass(frozen=True)
class GeminiConfig:
    """Connection + generation settings for Gemini."""

    api_key: str = ""

    # Example values (you should set these in .env):
    # - gemini-2.0-flash
    # - gemini-2.0-pro
    # - (if available in your account) a *thinking* model variant
    model: str = ""
    model_thinking: str = ""

    temperature: float = 0.2
    top_p: float = 0.9
    max_output_tokens: int = 8192


def _extract_text(data: Dict[str, Any]) -> str:
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GeminiError(f"Gemini returned no candidates: {data}")

    c0 = candidates[0]
    if not isinstance(c0, dict):
        raise GeminiError(f"Gemini candidate has unexpected shape: {data}")

    content = c0.get("content")
    if not isinstance(content, dict):
        raise GeminiError(f"Gemini content missing: {data}")

    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        raise GeminiError(f"Gemini content.parts missing: {data}")

    # Join all text parts.
    out: List[str] = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        t = p.get("text")
        if isinstance(t, str) and t:
            out.append(t)

    text = "".join(out).strip()
    if not text:
        raise GeminiError(f"Gemini returned empty text: {data}")

    return text


def chat(
    *,
    config: GeminiConfig,
    messages: List[Dict[str, str]],
    response_format_json: bool = True,
    timeout_s: float = 300.0,
    thinking: bool = False,
) -> str:
    """Send a chat request and return assistant content as a string."""

    if not config.api_key:
        raise GeminiError("Missing Gemini API key (set GEMINI_API_KEY in .env)")

    model = _normalize_model_id(
        config.model_thinking if thinking and config.model_thinking else config.model
    )
    if not model:
        raise GeminiError(
            "Missing Gemini model name (set GEMINI_MODEL, and optionally GEMINI_MODEL_THINKING in .env)"
        )

    # Separate system prompt(s) from the rest.
    system_chunks: List[str] = []
    contents: List[Dict[str, Any]] = []
    for m in messages:
        role = (m.get("role") or "").strip().lower()
        content = m.get("content")
        if not isinstance(content, str):
            continue

        if role == "system":
            if content.strip():
                system_chunks.append(content.strip())
            continue

        # Gemini uses role: user|model
        g_role = "model" if role == "assistant" else "user"
        contents.append({"role": g_role, "parts": [{"text": content}]})

    if not contents:
        raise GeminiError("No user/assistant messages provided")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    params = {"key": config.api_key}

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": float(config.temperature),
            "topP": float(config.top_p),
            "maxOutputTokens": int(config.max_output_tokens),
        },
    }

    # Prefer a hard JSON response when the upstream supports it.
    if response_format_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    system_text = "\n\n".join(system_chunks).strip()
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    try:
        resp = requests.post(url, params=params, json=payload, timeout=timeout_s)
    except requests.RequestException as exc:
        raise GeminiError(f"Failed to reach Gemini at {url}: {exc}") from exc

    if resp.status_code != 200:
        # Error bodies are usually JSON, but not guaranteed.
        body = resp.text[:2000]
        raise GeminiError(f"Gemini generateContent failed: HTTP {resp.status_code}: {body}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise GeminiError(f"Gemini returned non-JSON response: {resp.text[:2000]}") from exc

    return _extract_text(data)


def list_models(*, api_key: str, timeout_s: float = 10.0) -> List[Dict[str, Any]]:
    """List available Gemini models.

    Uses:
      GET https://generativelanguage.googleapis.com/v1beta/models?key=...

    Returns:
      Raw model dicts from the API.
    """

    if not api_key:
        raise GeminiError("Missing Gemini API key (set GEMINI_API_KEY in .env)")

    url = "https://generativelanguage.googleapis.com/v1beta/models"
    params = {"key": api_key}

    try:
        resp = requests.get(url, params=params, timeout=timeout_s)
    except requests.RequestException as exc:
        raise GeminiError(f"Failed to reach Gemini at {url}: {exc}") from exc

    if resp.status_code != 200:
        raise GeminiError(f"Gemini list models failed: HTTP {resp.status_code}: {resp.text[:2000]}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise GeminiError(f"Gemini returned non-JSON response: {resp.text[:2000]}") from exc

    models = data.get("models")
    if not isinstance(models, list):
        raise GeminiError(f"Unexpected list models response shape: {data}")

    return [m for m in models if isinstance(m, dict)]
