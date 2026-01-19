"""Unified LLM routing layer.

The rest of the repo was originally Ollama-only.
This module makes it possible to switch between:
- local Ollama (e.g., Qwen3 via `ollama`)
- Google Gemini (cloud)
- Hugging Face Transformers (e.g., Qwen models in Colab)

without changing prompt-building logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal

from .gemini_client import GeminiConfig, GeminiError
from .huggingface_client import HuggingFaceConfig, HuggingFaceError
from .ollama_client import OllamaConfig, OllamaError
from .unsloth_client import UnslothConfig, UnslothError


LLMProvider = Literal["ollama", "gemini", "huggingface", "unsloth"]


class LLMRouterError(RuntimeError):
    pass


def _normalize_provider(provider: str) -> LLMProvider:
    p = (provider or "").strip().lower()
    # Allow a few aliases to make switching ergonomic.
    if p in ("ollama", "qwen", "qwen3", "local"):
        return "ollama"
    if p in ("gemini", "gemini3", "google"):
        return "gemini"
    if p in ("huggingface", "hf", "transformers", "colab"):
        return "huggingface"
    if p in ("unsloth", "finetuned", "ft"):
        return "unsloth"
    raise LLMRouterError(
        f"Unknown provider: {provider!r} (use 'ollama', 'gemini', 'huggingface', or 'unsloth')"
    )


@dataclass(frozen=True)
class LLMConfig:
    provider: LLMProvider = "ollama"
    thinking: bool = False

    ollama: OllamaConfig = OllamaConfig()
    gemini: GeminiConfig = GeminiConfig()
    huggingface: HuggingFaceConfig = HuggingFaceConfig()
    unsloth: UnslothConfig = UnslothConfig()


def chat(
    *,
    config: LLMConfig,
    messages: List[Dict[str, str]],
    response_format_json: bool = True,
    timeout_s: float = 300.0,
) -> str:
    """Chat with the configured provider and return assistant text."""

    provider = _normalize_provider(config.provider)

    if provider == "ollama":
        from .ollama_client import chat as ollama_chat

        try:
            return ollama_chat(
                config=config.ollama,
                messages=messages,
                response_format_json=response_format_json,
                timeout_s=timeout_s,
            )
        except OllamaError as exc:
            raise LLMRouterError(str(exc)) from exc

    if provider == "gemini":
        from .gemini_client import chat as gemini_chat

        try:
            return gemini_chat(
                config=config.gemini,
                messages=messages,
                response_format_json=response_format_json,
                timeout_s=timeout_s,
                thinking=bool(config.thinking),
            )
        except GeminiError as exc:
            raise LLMRouterError(str(exc)) from exc

    if provider == "huggingface":
        from .huggingface_client import chat as huggingface_chat

        try:
            return huggingface_chat(
                config=config.huggingface,
                messages=messages,
                response_format_json=response_format_json,
                timeout_s=timeout_s,
            )
        except HuggingFaceError as exc:
            raise LLMRouterError(str(exc)) from exc

    # provider == "unsloth"
    from .unsloth_client import chat as unsloth_chat

    try:
        return unsloth_chat(
            config=config.unsloth,
            messages=messages,
            response_format_json=response_format_json,
            timeout_s=timeout_s,
        )
    except UnslothError as exc:
        raise LLMRouterError(str(exc)) from exc
