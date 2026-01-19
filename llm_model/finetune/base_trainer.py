"""Base trainer class for fine-tuning using unsloth."""

from __future__ import annotations

# Import unsloth FIRST before any other imports (required for optimizations)
# This must be at the very top to ensure all optimizations are applied
try:
    import unsloth  # noqa: F401
except ImportError:
    pass  # Will raise error later if actually needed

# Now import other modules
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
        
        print("=" * 60)
        print("MODEL LOADING INFORMATION")
        print("=" * 60)
        print(f"Model name: {self.model_name}")
        print(f"Step name: {self.step_name}")
        print(f"Max sequence length: {self.config.max_seq_length}")
        
        # Check HuggingFace cache location
        from pathlib import Path
        import os
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        model_cache_name = f"models--{self.model_name.replace('/', '--')}"
        model_cache_path = hf_cache / model_cache_name
        print(f"HuggingFace cache: {hf_cache}")
        print(f"Model cache path: {model_cache_path}")
        if model_cache_path.exists():
            # Calculate size
            total_size = sum(f.stat().st_size for f in model_cache_path.rglob('*') if f.is_file())
            size_gb = total_size / (1024**3)
            print(f"✅ Model found in cache: {size_gb:.2f} GB")
        else:
            print(f"⚠️  Model not in cache, will download from HuggingFace")
            print("Note: First-time download may take several minutes depending on network speed...")
        print()
        
        # Check if model is already quantized (contains "bnb-4bit" or "4bit")
        is_pre_quantized = "bnb-4bit" in self.model_name.lower() or "4bit" in self.model_name.lower()
        
        # Prepare loading parameters
        load_kwargs = {
            "model_name": self.model_name,
            "max_seq_length": self.config.max_seq_length,
            "dtype": None,  # Auto detection
        }
        
        # For pre-quantized models, still set load_in_4bit=True (it's safe and ensures correct loading)
        # For non-quantized models, enable 4-bit quantization
        load_kwargs["load_in_4bit"] = True  # Always use 4-bit for memory efficiency
        if is_pre_quantized:
            print("📦 Model type: Pre-quantized 4-bit model (already quantized)")
        else:
            print("📦 Model type: Full precision (will be quantized to 4-bit during loading)")
        
        # Enable CPU offload if configured (for low GPU memory scenarios)
        # For pre-quantized models, CPU offload may still be needed if GPU RAM is limited
        if self.config.enable_cpu_offload:
            load_kwargs["device_map"] = "auto"  # Auto device mapping
            load_kwargs["llm_int8_enable_fp32_cpu_offload"] = True
            print("💾 CPU offload: ENABLED (some modules will be offloaded to CPU)")
        else:
            print("💾 CPU offload: DISABLED (all modules on GPU)")
        
        print()
        print("Loading parameters:")
        for key, value in load_kwargs.items():
            print(f"  - {key}: {value}")
        print()
        print("Starting model loading...")
        print("-" * 60)
        
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(**load_kwargs)
            
            # Log model information after loading
            print("-" * 60)
            print("✅ Model loaded successfully!")
            print()
            print("Loaded model information:")
            print(f"  - Model type: {type(self.model).__name__}")
            print(f"  - Model name: {self.model_name}")
            if hasattr(self.model, 'config'):
                config = self.model.config
                print(f"  - Model architecture: {getattr(config, 'model_type', 'unknown')}")
                print(f"  - Hidden size: {getattr(config, 'hidden_size', 'unknown')}")
                print(f"  - Number of layers: {getattr(config, 'num_hidden_layers', 'unknown')}")
                print(f"  - Vocabulary size: {getattr(config, 'vocab_size', 'unknown')}")
            if hasattr(self.tokenizer, 'vocab_size'):
                print(f"  - Tokenizer vocab size: {self.tokenizer.vocab_size}")
            print(f"  - Max sequence length: {self.config.max_seq_length}")
            
            # Check device
            try:
                import torch
                if hasattr(self.model, 'device'):
                    print(f"  - Device: {self.model.device}")
                elif hasattr(self.model, 'hf_device_map'):
                    print(f"  - Device map: {self.model.hf_device_map}")
            except:
                pass
            
            print()
            print("=" * 60)
        except (RuntimeError, ValueError) as e:
            error_msg = str(e)
            
            # Check for GPU memory issues
            if "GPU RAM" in error_msg or "dispatched on the CPU" in error_msg or "device_map" in error_msg.lower() or "llm_int8_enable_fp32_cpu_offload" in error_msg:
                # Auto-suggest CPU offload if not already enabled
                cpu_offload_suggestion = ""
                if not self.config.enable_cpu_offload:
                    cpu_offload_suggestion = "\n💡 Try adding --enable-cpu-offload to your command"
                
                raise RuntimeError(
                    f"GPU memory insufficient for model '{self.model_name}'. "
                    f"Solutions:\n"
                    f"1. Enable CPU offload: --enable-cpu-offload (slower but uses less GPU RAM){cpu_offload_suggestion}\n"
                    f"2. Use 4-bit quantized model: --model-name unsloth/Qwen3-8B-unsloth-bnb-4bit\n"
                    f"3. Use a smaller model: --model-name unsloth/Qwen2.5-7B-Instruct\n"
                    f"4. Reduce batch size: --batch-size 2 (or smaller)\n\n"
                    f"Error details: {error_msg}"
                ) from e
            
            # Check for model not found
            if "No config file found" in error_msg or "model_name" in error_msg.lower():
                raise RuntimeError(
                    f"Failed to load model '{self.model_name}'. "
                    f"Possible reasons:\n"
                    f"1. Model name is incorrect or doesn't exist on HuggingFace\n"
                    f"2. Network connection issue (cannot download from HuggingFace)\n"
                    f"3. Model path is incorrect (if using local path)\n\n"
                    f"Error details: {error_msg}\n\n"
                    f"Common model names:\n"
                    f"  - unsloth/Qwen3-8B-unsloth-bnb-4bit (4-bit quantized, recommended)\n"
                    f"  - unsloth/Qwen3-8B (full precision)\n"
                    f"  - unsloth/Qwen2.5-7B-Instruct\n"
                    f"  - Qwen/Qwen3-8B (original HuggingFace)"
                ) from e
            
            # Re-raise other errors
            raise
        
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
        """Format example for Qwen chat models (Qwen2.5 and Qwen3).
        
        For Qwen3, thinking mode is disabled (enable_thinking=False).
        
        Args:
            instruction: System/user prompt
            input_text: Input text (can be empty if instruction contains it)
            output_text: Expected output (JSON)
        
        Returns:
            Formatted chat string
        """
        # For Qwen3, try to use tokenizer.apply_chat_template if available
        # This ensures thinking mode is properly disabled
        if self.tokenizer is not None and "qwen3" in self.model_name.lower():
            try:
                # Use tokenizer's chat template with enable_thinking=False
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                ]
                
                if input_text:
                    user_content = f"{instruction}\n\n{input_text}"
                else:
                    user_content = instruction
                
                messages.append({"role": "user", "content": user_content})
                
                if output_text:
                    messages.append({"role": "assistant", "content": output_text})
                
                # Apply chat template with thinking disabled
                formatted = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=(not bool(output_text)),
                    enable_thinking=False  # Disable thinking mode for Qwen3
                )
                return formatted
            except Exception as e:
                # Fallback to manual formatting if tokenizer method fails
                print(f"Warning: Failed to use tokenizer.apply_chat_template: {e}. Using manual formatting.")
        
        # Manual formatting (for Qwen2.5 or fallback)
        # Qwen format: <|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>
        
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
            "qwen" or "qwen3" or "llama" or "generic"
        """
        model_lower = self.model_name.lower()
        if "qwen3" in model_lower:
            return "qwen3"
        elif "qwen" in model_lower:
            return "qwen"
        elif "llama" in model_lower:
            return "llama"
        else:
            return "generic"
    
    def format_example(self, example: Dict[str, Any]) -> str:
        """Format example using the appropriate chat format.
        
        For Qwen3, thinking mode is disabled (enable_thinking=False).
        
        Args:
            example: Training example dict
        
        Returns:
            Formatted text string
        """
        chat_format = self._detect_chat_format()
        
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        output_text = example.get("output", "")
        
        if chat_format in ("qwen", "qwen3"):
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
        eval_examples: Optional[List[Dict[str, Any]]] = None,
        resume_from_checkpoint: Optional[str] = None
    ):
        """Train the model.

        Args:
            train_examples: List of training examples
            eval_examples: Optional list of evaluation examples
            resume_from_checkpoint: Path to checkpoint to resume from (default: None)
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Import transformers after unsloth (already imported at top)
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

        # Enable evaluation if we have eval_examples (for early stopping)
        enable_eval = eval_dataset is not None
        training_args_dict = self.config.get_training_args(output_dir=output_dir, enable_eval=enable_eval)
        
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

        # Early stopping callback
        class EarlyStoppingCallback(TrainerCallback):
            def __init__(self, patience: int = 3, threshold: float = 0.001):
                self.patience = patience
                self.threshold = threshold
                self.best_metric = None
                self.patience_counter = 0

            def on_evaluate(self, args, state, control, metrics=None, **kwargs):
                if metrics is None:
                    return

                current_metric = metrics.get("eval_loss")
                if current_metric is None:
                    return

                # Check if this is the best metric so far
                if self.best_metric is None:
                    self.best_metric = current_metric
                    print(f"\n📊 Early stopping: Initial eval_loss = {current_metric:.4f}")
                elif current_metric < self.best_metric - self.threshold:
                    # Improved
                    improvement = self.best_metric - current_metric
                    print(f"\n✓ Early stopping: eval_loss improved by {improvement:.4f} ({self.best_metric:.4f} → {current_metric:.4f})")
                    self.best_metric = current_metric
                    self.patience_counter = 0
                else:
                    # No improvement
                    self.patience_counter += 1
                    print(f"\n⚠️  Early stopping: No improvement for {self.patience_counter}/{self.patience} evaluations (current: {current_metric:.4f}, best: {self.best_metric:.4f})")

                    if self.patience_counter >= self.patience:
                        print(f"\n🛑 Early stopping triggered! Stopping training.")
                        control.should_training_stop = True

        loss_callback = LossCallback(loss_history)

        # Create callbacks list
        callbacks = [loss_callback]

        # Add early stopping if evaluation is enabled
        if enable_eval and hasattr(self.config, 'early_stopping_patience'):
            early_stopping = EarlyStoppingCallback(
                patience=self.config.early_stopping_patience,
                threshold=self.config.early_stopping_threshold
            )
            callbacks.append(early_stopping)
            print(f"✓ Early stopping enabled (patience={self.config.early_stopping_patience}, threshold={self.config.early_stopping_threshold})")

        # Formatting function for Unsloth (required in newer versions)
        def formatting_func(examples):
            """Format examples for training."""
            texts = []
            for instruction, input_text, output in zip(
                examples.get("instruction", examples.get("formatted_text", [])),
                examples.get("input", [""] * len(examples.get("instruction", examples.get("formatted_text", [])))),
                examples.get("output", examples.get("formatted_text", []))
            ):
                # Handle both old format (formatted_text) and new format (instruction/input/output)
                if isinstance(instruction, str) and "instruction" in examples:
                    # New format with instruction/input/output
                    if input_text:
                        text = f"{instruction}\n\nInput:\n{input_text}\n\nOutput:\n{output}"
                    else:
                        text = f"{instruction}\n\nOutput:\n{output}"
                else:
                    # Old format with formatted_text
                    text = instruction  # formatted_text is already formatted
                texts.append(text)
            return texts

        # Create trainer
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            formatting_func=formatting_func,  # Use formatting_func instead of dataset_text_field
            max_seq_length=self.config.max_seq_length,
            packing=False,
            args=training_args,
            callbacks=callbacks,  # Use the callbacks list (includes loss tracking and early stopping)
        )
        
        # Train
        if resume_from_checkpoint:
            print(f"Resuming training for {self.step_name} from checkpoint: {resume_from_checkpoint}")
        else:
            print(f"Starting training for {self.step_name}...")
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)
        
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
                # Format input - for Qwen3, ensure thinking is disabled
                # Use tokenizer.apply_chat_template if available for Qwen3
                if "qwen3" in self.model_name.lower() and self.tokenizer is not None:
                    try:
                        messages = [
                            {"role": "system", "content": "You are a helpful assistant."},
                        ]
                        
                        input_text = example.get("input", "")
                        if input_text:
                            user_content = f"{example['instruction']}\n\n{input_text}"
                        else:
                            user_content = example["instruction"]
                        
                        messages.append({"role": "user", "content": user_content})
                        
                        # Apply chat template with thinking disabled
                        formatted_input = self.tokenizer.apply_chat_template(
                            messages,
                            tokenize=False,
                            add_generation_prompt=True,
                            enable_thinking=False  # Disable thinking mode for Qwen3
                        )
                    except Exception:
                        # Fallback to format_example if tokenizer method fails
                        formatted_input = self.format_example({
                            "instruction": example["instruction"],
                            "input": example.get("input", ""),
                            "output": "",  # Empty, we want model to generate
                        })
                else:
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
                
                # For Qwen3 non-thinking mode, use recommended parameters:
                # Temperature=0.7, TopP=0.8, TopK=20, MinP=0
                # For other models, use more conservative settings
                is_qwen3 = "qwen3" in self.model_name.lower()
                
                with self.model.inference_mode():
                    if is_qwen3:
                        # Qwen3 non-thinking mode parameters
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=512,
                            temperature=0.7,
                            top_p=0.8,
                            top_k=20,
                            do_sample=True,  # Required for non-thinking mode
                        )
                    else:
                        # Default parameters for other models
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=512,
                            temperature=0.1,
                            do_sample=False,
                        )
                
                # Decode output
                # For Qwen3, skip thinking content if present
                generated_text = self.tokenizer.decode(
                    outputs[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True
                ).strip()
                
                # For Qwen3, remove any thinking content that might have been generated
                # (should not happen with enable_thinking=False, but just in case)
                if is_qwen3 and "<think>" in generated_text and "</think>" in generated_text:
                    # Extract content after </think> tag
                    think_end = generated_text.rfind("</think>")
                    if think_end != -1:
                        generated_text = generated_text[think_end + len("</think>"):].strip()
                
                # Parse expected output
                expected_output = json.loads(example["output"])
                
                # Try to parse generated output
                try:
                    # Try to extract JSON from generated text
                    # Import from parent module (llm_model.json_utils)
                    import sys
                    import pathlib
                    parent_path = pathlib.Path(__file__).parent.parent.parent
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
