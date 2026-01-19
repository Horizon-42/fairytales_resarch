"""Script to train a single pipeline step."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from ..config import FineTuneConfig
from ..data_preparation import (
    extract_action_examples,
    extract_character_examples,
    extract_event_type_examples,
    extract_instrument_examples,
    extract_relationship_examples,
    extract_stac_examples,
    load_annotated_story,
    load_all_annotated_stories,
)
from ..trainers import (
    ActionTrainer,
    CharacterTrainer,
    EventTypeTrainer,
    InstrumentTrainer,
    RelationshipTrainer,
    StacTrainer,
)


def get_trainer_class(step: str):
    """Get trainer class for a step."""
    step_map = {
        "character": CharacterTrainer,
        "instrument": InstrumentTrainer,
        "relationship": RelationshipTrainer,
        "action": ActionTrainer,
        "stac": StacTrainer,
        "event_type": EventTypeTrainer,
    }
    
    if step not in step_map:
        raise ValueError(
            f"Unknown step: {step}. "
            f"Available steps: {', '.join(step_map.keys())}"
        )
    
    return step_map[step]


def get_extract_function(step: str):
    """Get data extraction function for a step."""
    step_map = {
        "character": extract_character_examples,
        "instrument": extract_instrument_examples,
        "relationship": extract_relationship_examples,
        "action": extract_action_examples,
        "stac": extract_stac_examples,
        "event_type": extract_event_type_examples,
    }
    
    if step not in step_map:
        raise ValueError(f"Unknown step: {step}")
    
    return step_map[step]


def train_step(
    step: str,
    data_dir: str,
    model_name: str = "unsloth/Qwen3-4B-unsloth-bnb-4bit",
    output_dir: str = "./models",
    config: Optional[FineTuneConfig] = None,
    train_split: float = 0.9,
    evaluate_after_training: bool = True,
    use_jsonl: bool = True,
    enable_cpu_offload: bool = False,
    resume_from_checkpoint: Optional[str] = None,
):
    """Train a single pipeline step.

    Args:
        step: Step name ("character", "instrument", "relationship", "action", "stac", "event_type")
        data_dir: Directory containing training data (JSONL files if use_jsonl=True, or JSON annotation files)
        model_name: Base model name
        output_dir: Output directory for trained models
        config: Fine-tuning configuration (default: FineTuneConfig())
        train_split: Train/test split ratio
        evaluate_after_training: Whether to evaluate on test set after training
        use_jsonl: If True, load from JSONL training files; if False, extract from JSON stories
        resume_from_checkpoint: Path to checkpoint to resume from (default: None for fresh training)
    """
    if config is None:
        config = FineTuneConfig(model_name=model_name, output_dir=output_dir, enable_cpu_offload=enable_cpu_offload)
    else:
        config.model_name = model_name
        config.output_dir = output_dir
        config.enable_cpu_offload = enable_cpu_offload
    
    # Get trainer class
    trainer_class = get_trainer_class(step)
    
    # Load training examples
    if use_jsonl:
        # Load from JSONL file
        data_path = Path(data_dir)
        jsonl_file = data_path / f"{step}_train.jsonl"
        
        if not jsonl_file.exists():
            raise FileNotFoundError(
                f"Training data file not found: {jsonl_file}\n"
                f"Make sure you have extracted training data first using:\n"
                f"  python -m llm_model.finetune.scripts.extract_training_data ..."
            )
        
        print(f"Loading training examples from {jsonl_file}...")
        all_examples = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    example = json.loads(line)
                    all_examples.append(example)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                    continue
        
        print(f"Loaded {len(all_examples)} training examples")
    else:
        # Extract from JSON stories (legacy mode)
        extract_func = get_extract_function(step)
        
        print(f"Loading annotated stories from {data_dir}...")
        stories = load_all_annotated_stories(data_dir)
        print(f"Loaded {len(stories)} stories")
        
        # Extract examples
        print(f"Extracting {step} examples...")
        all_examples = []
        for story in stories:
            story_text = story.get("source_info", {}).get("text_content", "")
            summary = None  # Can be extracted from metadata if available
            
            if step == "character":
                examples = extract_func(story, story_text, summary)
            elif step in ["relationship", "stac"]:
                examples = extract_func(story, story_text, summary)
            else:
                examples = extract_func(story, summary)
            
            all_examples.extend(examples)
        
        print(f"Extracted {len(all_examples)} examples")
    
    if len(all_examples) == 0:
        raise ValueError(f"No training examples found for step: {step}")
    
    # Split train/eval
    split_idx = int(len(all_examples) * train_split)
    train_examples = all_examples[:split_idx]
    eval_examples = all_examples[split_idx:] if split_idx < len(all_examples) else None
    
    print(f"Train examples: {len(train_examples)}")
    if eval_examples:
        print(f"Eval examples: {len(eval_examples)}")
    
    # Create trainer
    trainer = trainer_class(model_name=model_name, step_name=step, config=config)
    
    # Load model
    print(f"Loading model {model_name}...")
    trainer.load_model()
    
    # Train
    trainer.train(train_examples, eval_examples, resume_from_checkpoint=resume_from_checkpoint)

    print(f"Training completed for {step}")

    # Evaluate on test set if requested
    if evaluate_after_training and eval_examples:
        print(f"\nEvaluating {step} model on test set...")
        try:
            eval_results = trainer.evaluate_step_output(
                test_examples=eval_examples,
                output_dir=trainer.output_dir,
            )
            print(f"Evaluation completed. Accuracy: {eval_results.get('accuracy', 0.0):.3f}")
        except Exception as e:
            print(f"Warning: Evaluation failed: {e}")
            import traceback
            traceback.print_exc()

    # Free GPU memory after training this step
    # This is crucial for sequential training to avoid OOM
    import torch
    import gc
    del trainer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    print(f"✓ GPU memory freed after {step} training")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Train pipeline step(s)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train single step
  python -m llm_model.finetune.scripts.train_step \\
      --step character \\
      --data-dir training_data \\
      --output-dir ./models

  # Train multiple steps sequentially (each step uses previous step's model)
  python -m llm_model.finetune.scripts.train_step \\
      --step character relationship action \\
      --data-dir training_data \\
      --output-dir ./models

  # Train all steps
  python -m llm_model.finetune.scripts.train_step \\
      --step all \\
      --data-dir training_data \\
      --output-dir ./models

  # Start fresh training (disable auto-resume)
  python -m llm_model.finetune.scripts.train_step \\
      --step character \\
      --data-dir training_data \\
      --output-dir ./models \\
      --no-auto-resume

Notes:
  - By default, training will automatically resume from the latest checkpoint if available
  - When training multiple steps, if one step fails, the pipeline stops (no subsequent steps)
  - Sequential training: step 2 uses step 1's model, step 3 uses step 2's model, etc.
        """
    )
    parser.add_argument(
        "--step",
        type=str,
        nargs="+",  # Allow multiple steps
        required=True,
        choices=["character", "instrument", "relationship", "action", "stac", "event_type", "all"],
        help="Pipeline step(s) to train. Use 'all' to train all steps, or specify multiple: --step character action"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing training data (JSONL files by default, or JSON annotation files if --no-use-jsonl)"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="unsloth/Qwen3-4B-unsloth-bnb-4bit",
        help="Base model name (default: unsloth/Qwen3-4B-unsloth-bnb-4bit, 4-bit quantized for lower GPU memory)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models",
        help="Output directory for trained models (default: ./models)"
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        default=1,
        help="Number of training epochs (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Training batch size (default: 4)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate (default: 2e-4)"
    )
    parser.add_argument(
        "--train-split",
        type=float,
        default=0.9,
        help="Train/test split ratio (default: 0.9)"
    )
    parser.add_argument(
        "--no-evaluate",
        action="store_true",
        help="Skip evaluation after training"
    )
    parser.add_argument(
        "--no-use-jsonl",
        dest="use_jsonl",
        action="store_false",
        default=True,
        help="Extract training data from JSON annotation files instead of JSONL (default: use JSONL)"
    )
    parser.add_argument(
        "--enable-cpu-offload",
        action="store_true",
        help="Enable CPU offload for low GPU memory scenarios (slower but uses less GPU RAM)"
    )
    parser.add_argument(
        "--resume-from-checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint directory to resume training from (e.g., ./models/character/checkpoint-100). By default, automatically resumes from latest checkpoint if available."
    )
    parser.add_argument(
        "--no-auto-resume",
        action="store_true",
        help="Disable automatic checkpoint resuming (start fresh even if checkpoints exist)"
    )

    args = parser.parse_args()
    
    # Determine which steps to train
    all_steps = ["character", "instrument", "relationship", "action", "stac", "event_type"]
    
    if "all" in args.step:
        steps_to_train = all_steps
    else:
        steps_to_train = args.step
    
    # Remove duplicates while preserving order
    seen = set()
    steps_to_train = [s for s in steps_to_train if s not in seen and not seen.add(s)]
    
    print(f"Training {len(steps_to_train)} step(s): {', '.join(steps_to_train)}\n")
    
    # Create config
    config = FineTuneConfig(
        model_name=args.model_name,
        output_dir=args.output_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        enable_cpu_offload=args.enable_cpu_offload,
    )

    # Train each step
    failed_steps = []
    current_model_name = args.model_name  # Track the model to use for each step

    for idx, step in enumerate(steps_to_train):
        print(f"\n{'='*60}")
        print(f"Training step {idx+1}/{len(steps_to_train)}: {step}")
        if idx > 0:
            print(f"Using model from previous step: {current_model_name}")
        print(f"{'='*60}\n")

        # Auto-detect checkpoint for this step if resume_from_checkpoint not explicitly provided
        checkpoint_to_use = args.resume_from_checkpoint
        if checkpoint_to_use is None and not args.no_auto_resume:
            # Look for latest checkpoint in the step's output directory
            step_output_dir = Path(args.output_dir) / step
            if step_output_dir.exists():
                # Find all checkpoint directories
                checkpoints = list(step_output_dir.glob("checkpoint-*"))
                if checkpoints:
                    # Sort by checkpoint number and get the latest
                    checkpoints.sort(key=lambda x: int(x.name.split("-")[1]))
                    checkpoint_to_use = str(checkpoints[-1])
                    print(f"🔄 Found existing checkpoint, will resume from: {checkpoint_to_use}")
        elif args.no_auto_resume and checkpoint_to_use is None:
            print(f"⚠️  Auto-resume disabled, starting training from scratch")

        try:
            train_step(
                step=step,
                data_dir=args.data_dir,
                model_name=current_model_name,  # Use the current model (base or from previous step)
                output_dir=args.output_dir,
                config=config,
                train_split=args.train_split,
                evaluate_after_training=not args.no_evaluate,
                use_jsonl=args.use_jsonl,
                enable_cpu_offload=args.enable_cpu_offload,
                resume_from_checkpoint=checkpoint_to_use,
            )
            print(f"\n✓ Successfully completed training for {step}\n")

            # Update current_model_name to use the fine-tuned model for the next step
            current_model_name = str(Path(args.output_dir) / step)
            print(f"📦 Next step will use fine-tuned model: {current_model_name}\n")
        except Exception as e:
            print(f"\n✗ Error training step {step}: {e}")
            failed_steps.append(step)
            import traceback
            traceback.print_exc()

            # Stop training if a step fails (don't continue to next steps)
            print(f"\n⚠️  Stopping training pipeline due to failure in step: {step}")
            print(f"⚠️  Remaining steps will not be trained: {', '.join(steps_to_train[idx+1:])}")
            break  # Stop the loop instead of continue
    
    # Print summary
    print(f"\n{'='*60}")
    print("Training Summary:")
    print(f"{'='*60}")
    successful_steps = [s for s in steps_to_train if s not in failed_steps]
    
    if successful_steps:
        print(f"✓ Successfully trained: {', '.join(successful_steps)}")
    
    if failed_steps:
        print(f"✗ Failed: {', '.join(failed_steps)}")
        return 1
    
    print(f"\n✓ All {len(steps_to_train)} step(s) trained successfully!")
    return 0


if __name__ == "__main__":
    main()
