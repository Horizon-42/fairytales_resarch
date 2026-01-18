"""Base trainer class for fine-tuning using unsloth."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import FineTuneConfig


class BaseTrainer:
    """Base trainer class for fine-tuning pipeline steps.
    
    This class provides common functionality for all step trainers.
    Subclasses should implement format_training_example() method.
    """
    
    def __init__(
        self,
        model_name: str,
        step_name: str,
        config: FineTuneConfig
    ):
        """Initialize trainer.
        
        Args:
            model_name: Base model name (unsloth compatible)
            step_name: Name of the pipeline step (e.g., "character_recognition")
            config: Fine-tuning configuration
        """
        self.model_name = model_name
        self.step_name = step_name
        self.config = config
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """Load model using unsloth.
        
        This method uses unsloth's FastLanguageModel to load and prepare
        the model for LoRA fine-tuning.
        """
        try:
            from unsloth import FastLanguageModel
        except ImportError:
            raise ImportError(
                "unsloth is not installed. Install it with: "
                "pip install unsloth"
            )
        
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=self.config.max_seq_length,
            dtype=None,  # Auto detection
            load_in_4bit=True,  # 4bit quantization
        )
        
        # Apply LoRA adapters
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=self.config.lora_r,
            target_modules=self.config.target_modules,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            use_gradient_checkpointing=True,
        )
    
    
    def _format_chat_qwen(self, instruction: str, input_text: str, output_text: str) -> str:
        """Format example for Qwen chat models.
        
        Args:
            instruction: System/user prompt
            input_text: Input text (can be empty if instruction contains it)
            output_text: Expected output (JSON)
        
        Returns:
            Formatted chat string
        """
        # Qwen format: <|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>
        
        # Instruction contains both system and user prompts combined
        if input_text:
            user_content = f"{instruction}\n\n{input_text}"
        else:
            user_content = instruction
        
        formatted = (
            f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
            f"<|im_start|>user\n{user_content}<|im_end|>\n"
            f"<|im_start|>assistant\n{output_text}<|im_end|>"
        )
        return formatted
    
    def _format_chat_llama(self, instruction: str, input_text: str, output_text: str) -> str:
        """Format example for Llama chat models.
        
        Args:
            instruction: System/user prompt
            input_text: Input text (can be empty if instruction contains it)
            output_text: Expected output (JSON)
        
        Returns:
            Formatted chat string
        """
        # Llama format: [INST] {instruction} [/INST] {output}
        
        if input_text:
            user_content = f"{instruction}\n\n{input_text}"
        else:
            user_content = instruction
        
        formatted = f"[INST] {user_content} [/INST] {output_text}"
        return formatted
    
    def _detect_chat_format(self) -> str:
        """Detect chat format based on model name.
        
        Returns:
            "qwen" or "llama" or "generic"
        """
        model_lower = self.model_name.lower()
        if "qwen" in model_lower:
            return "qwen"
        elif "llama" in model_lower:
            return "llama"
        else:
            return "generic"
    
    def format_example(self, example: Dict[str, Any]) -> str:
        """Format example using the appropriate chat format.
        
        Args:
            example: Training example dict
        
        Returns:
            Formatted text string
        """
        chat_format = self._detect_chat_format()
        
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        output_text = example.get("output", "")
        
        if chat_format == "qwen":
            return self._format_chat_qwen(instruction, input_text, output_text)
        elif chat_format == "llama":
            return self._format_chat_llama(instruction, input_text, output_text)
        else:
            # Generic format: instruction + output
            if input_text:
                return f"{instruction}\n\n{input_text}\n\n{output_text}"
            else:
                return f"{instruction}\n\n{output_text}"
    
    def prepare_dataset(self, examples: List[Dict[str, Any]]) -> Any:
        """Prepare dataset from examples.
        
        Args:
            examples: List of training examples
        
        Returns:
            HuggingFace Dataset object with "formatted_text" field
        """
        try:
            from datasets import Dataset
        except ImportError:
            raise ImportError(
                "datasets is not installed. Install it with: "
                "pip install datasets"
            )
        
        formatted_texts = [self.format_example(ex) for ex in examples]
        
        dataset_dict = {"formatted_text": formatted_texts}
        dataset = Dataset.from_dict(dataset_dict)
        
        return dataset
    
    def train(
        self,
        train_examples: List[Dict[str, Any]],
        eval_examples: Optional[List[Dict[str, Any]]] = None
    ):
        """Train the model.
        
        Args:
            train_examples: List of training examples
            eval_examples: Optional list of evaluation examples
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        try:
            from trl import SFTTrainer
            from transformers import TrainingArguments
        except ImportError:
            raise ImportError(
                "trl or transformers is not installed. Install them with: "
                "pip install trl transformers"
            )
        
        # Prepare datasets
        train_dataset = self.prepare_dataset(train_examples)
        eval_dataset = None
        if eval_examples:
            eval_dataset = self.prepare_dataset(eval_examples)
        
        # Get training arguments
        output_dir = str(Path(self.config.output_dir) / self.step_name)
        training_args_dict = self.config.get_training_args(output_dir=output_dir)
        
        if eval_dataset:
            training_args_dict["evaluation_strategy"] = "epoch"
            training_args_dict["load_best_model_at_end"] = True
        
        training_args = TrainingArguments(**training_args_dict)
        
        # Create trainer
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            dataset_text_field="formatted_text",
            max_seq_length=self.config.max_seq_length,
            packing=False,
            args=training_args,
        )
        
        # Train
        print(f"Starting training for {self.step_name}...")
        trainer.train()
        
        # Save model
        self.save_model(output_dir)
        
        print(f"Training completed for {self.step_name}")
    
    def save_model(self, output_dir: Optional[str] = None):
        """Save trained model.
        
        Args:
            output_dir: Output directory (default: config.output_dir / step_name)
        """
        if self.model is None:
            raise ValueError("Model not loaded or trained.")
        
        if output_dir is None:
            output_dir = str(Path(self.config.output_dir) / self.step_name)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save using unsloth
        try:
            from unsloth import FastLanguageModel
        except ImportError:
            raise ImportError("unsloth is not installed.")
        
        FastLanguageModel.for_inference(self.model)  # Disable training mode
        self.model.save_pretrained(str(output_path))
        self.tokenizer.save_pretrained(str(output_path))
        
        print(f"Model saved to {output_path}")
