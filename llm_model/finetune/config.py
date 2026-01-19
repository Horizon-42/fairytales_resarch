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
    max_seq_length: int = 1024  # Reduced from 2048 to avoid OOM on 8GB GPU
    
    # LoRA configuration (reduced for 8GB GPU memory efficiency)
    lora_r: int = 8  # Reduced from 16 to save memory
    lora_alpha: int = 16  # Reduced proportionally
    lora_dropout: float = 0.1  # Increased from 0 to 0.1 to reduce overfitting
    target_modules: Optional[List[str]] = None

    # Training configuration (optimized for 8GB GPU and reduced overfitting)
    batch_size: int = 1  # Reduced from 4 to avoid OOM on 8GB GPU
    gradient_accumulation_steps: int = 8  # Increased to maintain effective batch size of 8
    num_epochs: int = 2  # Reduced from 3 to 2 to prevent overfitting on limited data
    learning_rate: float = 2e-4
    warmup_steps: int = 50

    # Early stopping configuration
    early_stopping_patience: int = 3  # Stop if no improvement for 3 evaluation steps
    early_stopping_threshold: float = 0.001  # Minimum improvement threshold
    
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
    
    def get_training_args(self, output_dir: Optional[str] = None, enable_eval: bool = True) -> dict:
        """Get training arguments dictionary for transformers.

        Args:
            output_dir: Output directory for checkpoints
            enable_eval: Whether to enable evaluation (requires eval dataset)
        """
        if output_dir is None:
            output_dir = self.output_dir

        args = {
            "per_device_train_batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "warmup_steps": self.warmup_steps,
            "num_train_epochs": self.num_epochs,
            "learning_rate": self.learning_rate,
            "fp16": not self.bf16,
            "bf16": self.bf16,
            "logging_steps": 10,
            "output_dir": output_dir,
            "save_strategy": "steps",
            "save_steps": 50,
            "save_total_limit": 2,
            "gradient_checkpointing": True,
            "optim": "adamw_8bit",
        }

        # Add evaluation and early stopping if enabled
        if enable_eval:
            args.update({
                "eval_strategy": "steps",
                "eval_steps": 50,  # Evaluate every 50 steps
                "metric_for_best_model": "eval_loss",
                "greater_is_better": False,
                "load_best_model_at_end": True,
                # Early stopping via callback (not built-in parameter)
            })
        else:
            args.update({
                "eval_strategy": "no",
                "load_best_model_at_end": False,
            })

        return args
