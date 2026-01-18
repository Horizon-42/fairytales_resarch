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
            from transformers import TrainingArguments, TrainerCallback
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
        
        # Add logging directory for loss tracking
        training_args_dict["logging_dir"] = str(Path(output_dir) / "logs")
        
        training_args = TrainingArguments(**training_args_dict)
        
        # Loss tracking callback
        loss_history = []
        
        class LossCallback(TrainerCallback):
            def __init__(self, history_list):
                self.history_list = history_list
            
            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs is not None:
                    log_entry = {
                        "step": state.global_step,
                        "epoch": state.epoch if hasattr(state, "epoch") else None,
                    }
                    if "loss" in logs:
                        log_entry["train_loss"] = logs["loss"]
                    if "eval_loss" in logs:
                        log_entry["eval_loss"] = logs["eval_loss"]
                    if "learning_rate" in logs:
                        log_entry["learning_rate"] = logs["learning_rate"]
                    if log_entry.get("train_loss") is not None or log_entry.get("eval_loss") is not None:
                        self.history_list.append(log_entry)
        
        loss_callback = LossCallback(loss_history)
        
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
            callbacks=[loss_callback],
        )
        
        # Train
        print(f"Starting training for {self.step_name}...")
        trainer.train()
        
        # Save loss history as CSV
        loss_file = Path(output_dir) / "loss_history.csv"
        import csv
        with open(loss_file, "w", encoding="utf-8", newline="") as f:
            if loss_history:
                fieldnames = ["step", "epoch", "train_loss", "eval_loss", "learning_rate"]
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for entry in loss_history:
                    writer.writerow(entry)
        print(f"Loss history saved to {loss_file}")
        
        # Save model
        self.save_model(output_dir)
        
        print(f"Training completed for {self.step_name}")
        
        # Store loss history and trainer for later use
        self.loss_history = loss_history
        self.trainer = trainer  # Store trainer for evaluation
        self.output_dir = output_dir  # Store output directory
    
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
    
    def evaluate_step_output(
        self,
        test_examples: List[Dict[str, Any]],
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate fine-tuned model on test examples for this specific step.
        
        This method:
        1. Uses the fine-tuned model to generate predictions for test examples
        2. Compares predictions with expected outputs
        3. Calculates accuracy metrics for this step
        
        Args:
            test_examples: List of test examples (same format as training examples)
            output_dir: Output directory for evaluation results
        
        Returns:
            Evaluation results dictionary with accuracy metrics
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded or trained.")
        
        if output_dir is None:
            output_dir = str(Path(self.config.output_dir) / self.step_name)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            from unsloth import FastLanguageModel
        except ImportError:
            raise ImportError("unsloth is not installed.")
        
        # Enable inference mode
        FastLanguageModel.for_inference(self.model)
        
        print(f"Evaluating {len(test_examples)} test examples for {self.step_name}...")
        
        correct = 0
        total = 0
        predictions = []
        
        for idx, example in enumerate(test_examples, 1):
            try:
                # Format input
                formatted_input = self.format_example({
                    "instruction": example["instruction"],
                    "input": example.get("input", ""),
                    "output": "",  # Empty, we want model to generate
                })
                
                # Generate prediction
                inputs = self.tokenizer(
                    formatted_input,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.config.max_seq_length,
                ).to(self.model.device)
                
                with self.model.inference_mode():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=512,
                        temperature=0.1,
                        do_sample=False,
                    )
                
                # Decode output
                generated_text = self.tokenizer.decode(
                    outputs[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True
                ).strip()
                
                # Parse expected output
                expected_output = json.loads(example["output"])
                
                # Try to parse generated output
                try:
                    # Try to extract JSON from generated text
                    # Import from parent module (llm_model.json_utils)
                    import sys
                    from pathlib import Path
                    parent_path = Path(__file__).parent.parent.parent
                    if str(parent_path) not in sys.path:
                        sys.path.insert(0, str(parent_path))
                    from llm_model.json_utils import loads_strict_json
                    predicted_output = loads_strict_json(generated_text)
                except Exception:
                    # If parsing fails, try basic json.loads
                    try:
                        predicted_output = json.loads(generated_text)
                    except Exception:
                        predicted_output = {}
                
                # Simple accuracy check (exact match for now)
                # This can be enhanced with step-specific evaluation
                is_correct = self._compare_outputs(predicted_output, expected_output)
                
                predictions.append({
                    "example_idx": idx,
                    "expected": expected_output,
                    "predicted": predicted_output,
                    "correct": is_correct,
                    "raw_output": generated_text,
                })
                
                if is_correct:
                    correct += 1
                total += 1
                
                if (idx % 50 == 0) or (idx == len(test_examples)):
                    print(f"  [{idx}/{len(test_examples)}] Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")
                
            except Exception as e:
                print(f"  [{idx}/{len(test_examples)}] Error: {e}")
                continue
        
        # Calculate metrics
        accuracy = correct / total if total > 0 else 0.0
        
        results = {
            "step_name": self.step_name,
            "total_examples": total,
            "correct": correct,
            "accuracy": accuracy,
            "predictions": predictions,
        }
        
        # Save results
        eval_file = output_path / "step_evaluation.json"
        with open(eval_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Step evaluation results saved to {eval_file}")
        print(f"Final Accuracy: {accuracy:.3f} ({correct}/{total})")
        
        return results
    
    def _compare_outputs(self, predicted: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """Compare predicted and expected outputs.
        
        This is a simple comparison - can be enhanced with step-specific logic.
        
        Args:
            predicted: Predicted output dictionary
            expected: Expected output dictionary
        
        Returns:
            True if outputs match (approximately)
        """
        # Simple exact match for now
        # Can be enhanced with fuzzy matching, field-specific comparison, etc.
        return predicted == expected
