#!/usr/bin/env python3
"""Quick script to check model download and GPU availability."""

import os
from pathlib import Path

# Check HuggingFace cache
hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
print(f"HuggingFace cache location: {hf_cache}")
print(f"Cache exists: {hf_cache.exists()}\n")

if hf_cache.exists():
    # List Qwen3 models
    qwen_models = list(hf_cache.glob("models--unsloth--*Qwen3*"))
    print(f"Found {len(qwen_models)} Qwen3 model(s):")
    for model_dir in qwen_models:
        size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
        size_gb = size / (1024**3)
        print(f"  - {model_dir.name}: {size_gb:.2f} GB")
    print()

# Check GPU
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            total_memory = props.total_memory / (1024**3)
            print(f"  GPU {i}: {props.name}, {total_memory:.2f} GB total")
    else:
        print("⚠️  No GPU available - training will be very slow or may fail")
except ImportError:
    print("⚠️  PyTorch not installed")

# Check unsloth (only if GPU is available, otherwise it will fail)
if torch.cuda.is_available():
    try:
        import unsloth
        print(f"\n✅ Unsloth installed: {unsloth.__version__ if hasattr(unsloth, '__version__') else 'unknown version'}")
    except ImportError:
        print("\n❌ Unsloth not installed")
    except Exception as e:
        print(f"\n⚠️  Unsloth import failed: {e}")
else:
    print("\n⚠️  Skipping Unsloth check (no GPU available - Unsloth requires GPU)")

# Check model name
print(f"\nDefault model name: unsloth/Qwen3-8B-unsloth-bnb-4bit")
print(f"Model cache path: {hf_cache / 'models--unsloth--Qwen3-8B-unsloth-bnb-4bit'}")
