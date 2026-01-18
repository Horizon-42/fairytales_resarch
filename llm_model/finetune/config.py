"""Configuration for fine-tuning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FineTuneConfig:
    """Configuration for fine-tuning pipeline steps.
    
    Attributes:
        model_name: Base model name (unsloth compatible)
        max_seq_length: Maximum sequence length
        lora_r: LoRA rank
        lora_alpha: LoRA alpha
        lora_dropout: LoRA dropout
        target_modules: Target modules for LoRA (auto-detected if None)
        batch_size: Training batch size per device
        gradient_accumulation_steps: Gradient accumulation steps
        num_epochs: Number of training epochs
        learning_rate: Learning rate
        warmup_steps: Warmup steps
        bf16: Use bfloat16 (True) or float16 (False)
        output_dir: Output directory for trained models
    """
    
    # Model configuration
    # Qwen3-4B: Smaller model for lower GPU memory usage (7.71 GB GPU recommended)
    # Use 4-bit quantized version for lower GPU memory usage
    # Note: If unsloth/Qwen3-4B-unsloth-bnb-4bit is unavailable, try:
    # - unsloth/Qwen3-8B-unsloth-bnb-4bit (larger model, requires more GPU RAM)
    # - unsloth/Qwen3-8B (full precision, requires more GPU RAM)
    # - unsloth/Qwen2.5-7B-Instruct (previous generation)
    model_name: str = "unsloth/Qwen3-4B-unsloth-bnb-4bit"
    max_seq_length: int = 2048
    
    # LoRA configuration
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: Optional[List[str]] = None
    
    # Training configuration
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    learning_rate: float = 2e-4
    warmup_steps: int = 50
    
    # Data type
    bf16: bool = True  # Use bfloat16
    
    # Memory optimization
    enable_cpu_offload: bool = False  # Enable CPU offload for low GPU memory (slower but uses less GPU RAM)
    
    # Output
    output_dir: str = "./models"
    
    def __post_init__(self):
        """Auto-detect target modules if not specified."""
        if self.target_modules is None:
            # Default target modules based on model architecture
            model_lower = self.model_name.lower()
            if "qwen" in model_lower or "qwen2.5" in model_lower or "qwen3" in model_lower:
                self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
            elif "llama" in model_lower:
                self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
            else:
                # Generic default
                self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
    
    def get_training_args(self, output_dir: Optional[str] = None) -> dict:
        """Get training arguments dictionary for transformers."""
        if output_dir is None:
            output_dir = self.output_dir
        
        return {
            "per_device_train_batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "warmup_steps": self.warmup_steps,
            "num_train_epochs": self.num_epochs,
            "learning_rate": self.learning_rate,
            "fp16": not self.bf16,
            "bf16": self.bf16,
            "logging_steps": 10,
            "output_dir": output_dir,
            "save_strategy": "epoch",
            "evaluation_strategy": "no",  # Can be overridden
            "save_total_limit": 3,
            "load_best_model_at_end": False,
        }
