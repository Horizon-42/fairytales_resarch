"""Unsloth client for local fine-tuned models.

This module provides chat interface for unsloth fine-tuned models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


class UnslothError(RuntimeError):
    """Raised when unsloth client encounters an error."""
    pass


@dataclass(frozen=True)
class UnslothConfig:
    """Configuration for unsloth client."""

    model_path: str = "models/character"  # Path to fine-tuned model
    base_model: str = "unsloth/Qwen3-4B-unsloth-bnb-4bit"  # Base model name
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20
    max_new_tokens: int = 512
    enable_cpu_offload: bool = False


# Global model cache to avoid reloading
_model_cache = {}


def load_model(config: UnslothConfig):
    """Load unsloth model (cached).

    Args:
        config: Unsloth configuration

    Returns:
        Tuple of (model, tokenizer)
    """
    cache_key = config.model_path

    if cache_key in _model_cache:
        return _model_cache[cache_key]

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        raise UnslothError(
            "unsloth is not installed. Install it with: pip install unsloth"
        )

    try:
        # Load model
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=config.model_path,
            max_seq_length=1024,
            dtype=None,
            load_in_4bit=True,
        )

        # Enable inference mode
        FastLanguageModel.for_inference(model)

        # Cache the model
        _model_cache[cache_key] = (model, tokenizer)

        print(f"✓ Loaded unsloth model from {config.model_path}")

        return model, tokenizer

    except Exception as e:
        raise UnslothError(f"Failed to load unsloth model: {e}") from e


def chat(
    *,
    config: UnslothConfig,
    messages: List[Dict[str, str]],
    response_format_json: bool = True,
    timeout_s: float = 300.0,
) -> str:
    """Chat with unsloth model.

    Args:
        config: Unsloth configuration
        messages: List of message dicts with 'role' and 'content' keys
        response_format_json: If True, expect JSON output (not enforced by model)
        timeout_s: Timeout in seconds (not used for local inference)

    Returns:
        Generated text response

    Raises:
        UnslothError: If chat fails
    """
    try:
        # Load model (cached)
        model, tokenizer = load_model(config)

        # Format messages using chat template
        formatted_input = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # Disable thinking mode for Qwen3
        )

        # Tokenize
        inputs = tokenizer(
            formatted_input,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(model.device)

        # Generate (model is already in inference mode from FastLanguageModel.for_inference)
        outputs = model.generate(
            **inputs,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            do_sample=True,
        )

        # Decode output
        generated_text = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()

        # Remove thinking tags if present
        if "<think>" in generated_text and "</think>" in generated_text:
            think_end = generated_text.rfind("</think>")
            if think_end != -1:
                generated_text = generated_text[think_end + len("</think>"):].strip()

        return generated_text

    except UnslothError:
        raise
    except Exception as e:
        raise UnslothError(f"Unsloth chat failed: {e}") from e
