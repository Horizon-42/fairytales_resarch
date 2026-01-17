"""Hugging Face Transformers client for Colab.

This module provides a client interface compatible with Ollama/Gemini
but using Hugging Face Transformers models loaded in Colab.

Supports models like:
- Qwen/Qwen2.5-7B-Instruct
- Qwen/Qwen2.5-3B-Instruct
- Qwen/Qwen2-7B-Instruct
- And other chat models from Hugging Face

Example:
    config = HuggingFaceConfig(
        model="Qwen/Qwen2.5-7B-Instruct",
        device="cuda",  # or "cpu" or "auto"
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
    response = chat(config=config, messages=messages, response_format_json=True)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    torch = None


class HuggingFaceError(RuntimeError):
    pass


@dataclass(frozen=True)
class HuggingFaceConfig:
    """Configuration for Hugging Face model."""

    # Model ID from Hugging Face Hub (e.g., "Qwen/Qwen2.5-7B-Instruct")
    model: str = "Qwen/Qwen2.5-7B-Instruct"

    # Device: "cuda", "cpu", or "auto" (auto-detect)
    device: str = "auto"

    # Generation parameters
    temperature: float = 0.2
    top_p: float = 0.9
    max_new_tokens: int = 2048

    # Model loading options
    torch_dtype: Optional[str] = None  # "float16", "bfloat16", or None (auto)


# Global cache for loaded models (reuse across calls)
_model_cache: Dict[str, Any] = {}
_tokenizer_cache: Dict[str, Any] = {}


def _get_device(device: str) -> str:
    """Get the actual device string."""
    if device == "auto":
        if HF_AVAILABLE and torch is not None and torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return device


def _get_torch_dtype(dtype_str: Optional[str], device: str) -> Any:
    """Get torch dtype object."""
    if not HF_AVAILABLE or torch is None:
        return None
    
    if dtype_str is None:
        # Auto-select based on device
        if device == "cuda":
            # Prefer bfloat16 for modern GPUs, float16 otherwise
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16
        return torch.float32
    
    dtype_map = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    return dtype_map.get(dtype_str, None)


def _load_model_and_tokenizer(
    model_id: str,
    device: str,
    torch_dtype: Optional[str] = None,
) -> tuple[Any, Any]:
    """Load model and tokenizer, with caching."""
    cache_key = f"{model_id}::{device}::{torch_dtype or 'auto'}"
    
    if cache_key in _model_cache and cache_key in _tokenizer_cache:
        return _model_cache[cache_key], _tokenizer_cache[cache_key]
    
    if not HF_AVAILABLE:
        raise HuggingFaceError(
            "transformers and torch not installed. "
            "Install with: pip install transformers torch"
        )
    
    actual_device = _get_device(device)
    dtype = _get_torch_dtype(torch_dtype, actual_device)
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model
        model_kwargs: Dict[str, Any] = {
            "trust_remote_code": True,
        }
        if dtype is not None:
            model_kwargs["torch_dtype"] = dtype
        
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs,
        )
        model = model.to(actual_device)
        model.eval()
        
        # Cache for reuse
        _model_cache[cache_key] = model
        _tokenizer_cache[cache_key] = tokenizer
        
        return model, tokenizer
    
    except Exception as e:
        raise HuggingFaceError(f"Failed to load model {model_id}: {e}") from e


def chat(
    *,
    config: HuggingFaceConfig,
    messages: List[Dict[str, str]],
    response_format_json: bool = True,
    timeout_s: float = 300.0,
) -> str:
    """Send a chat request and return assistant content as a string.
    
    Args:
        config: HuggingFaceConfig with model name and options.
        messages: List of {role: "system"|"user"|"assistant", content: str}.
        response_format_json: If True, instructs model to return JSON (via system prompt).
        timeout_s: Timeout (not strictly enforced, but used for generation limits).
    
    Returns:
        Assistant message content.
    """
    
    if not HF_AVAILABLE:
        raise HuggingFaceError(
            "transformers and torch not installed. "
            "Install with: pip install transformers torch accelerate"
        )
    
    # Load model and tokenizer
    model, tokenizer = _load_model_and_tokenizer(
        model_id=config.model,
        device=config.device,
        torch_dtype=config.torch_dtype,
    )
    
    # Convert messages to prompt format
    # Most chat models use a specific template (Qwen uses chatml format)
    system_prompt = ""
    chat_messages = []
    
    for msg in messages:
        role = (msg.get("role") or "").strip().lower()
        content = msg.get("content") or ""
        
        if role == "system":
            system_prompt = content
            # If JSON response is required, add to system prompt
            if response_format_json and "JSON" not in system_prompt.upper():
                if system_prompt:
                    system_prompt += "\n\nYou must respond with valid JSON only (no markdown, no commentary)."
                else:
                    system_prompt = "You must respond with valid JSON only (no markdown, no commentary)."
        elif role in ("user", "assistant"):
            chat_messages.append({"role": role, "content": content})
    
    # Format prompt for Qwen-style chat models
    # Qwen models use apply_chat_template
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            # Try using the tokenizer's chat template
            prompt = tokenizer.apply_chat_template(
                chat_messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            if system_prompt:
                # Some models handle system prompt differently
                # For Qwen, we prepend it
                prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n{prompt}"
        except Exception:
            # Fallback: manual formatting
            prompt = _format_messages_manual(chat_messages, system_prompt)
    else:
        prompt = _format_messages_manual(chat_messages, system_prompt)
    
    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt")
    if inputs.input_ids.device.type != _get_device(config.device):
        inputs = {k: v.to(_get_device(config.device)) for k, v in inputs.items()}
    
    # Generate
    actual_device = _get_device(config.device)
    generation_kwargs = {
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_new_tokens": config.max_new_tokens,
        "do_sample": config.temperature > 0.0,
    }
    
    try:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                **generation_kwargs,
                return_dict_in_generate=False,  # Ensure we get tensor, not dict
            )
    except Exception as e:
        raise HuggingFaceError(f"Generation failed: {e}") from e
    
    # Decode response
    # model.generate() returns a tensor: [batch_size, seq_len]
    # We need to extract only the newly generated tokens (excluding input tokens)
    input_length = inputs.input_ids.shape[1]
    
    # Handle outputs: should be a tensor with shape [batch_size, seq_len]
    if isinstance(outputs, torch.Tensor):
        if len(outputs.shape) == 2:
            # [batch_size, seq_len] -> take first batch and skip input tokens
            generated_ids = outputs[0][input_length:]
        elif len(outputs.shape) == 1:
            # Already 1D, just skip input tokens
            generated_ids = outputs[input_length:]
        else:
            raise HuggingFaceError(f"Unexpected tensor shape: {outputs.shape}")
    elif isinstance(outputs, (list, tuple)):
        # If it's a list/tuple, take first element
        if len(outputs) > 0:
            generated_ids = torch.tensor(outputs[0][input_length:])
        else:
            raise HuggingFaceError("Empty generation output")
    else:
        raise HuggingFaceError(f"Unexpected output type: {type(outputs)}. Expected torch.Tensor, got {type(outputs)}")
    
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    return response.strip()


def _format_messages_manual(
    messages: List[Dict[str, str]],
    system_prompt: str = "",
) -> str:
    """Manually format messages as prompt (fallback when tokenizer doesn't have chat template)."""
    parts = []
    
    if system_prompt:
        parts.append(f"System: {system_prompt}\n")
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            parts.append(f"User: {content}\n")
        elif role == "assistant":
            parts.append(f"Assistant: {content}\n")
    
    parts.append("Assistant: ")
    return "".join(parts)
