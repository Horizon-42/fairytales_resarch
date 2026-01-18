"""Script to train all pipeline steps."""

from __future__ import annotations

import argparse
from typing import List, Optional

from ..config import FineTuneConfig
from ..data_preparation import prepare_all_training_data
from ..trainers import (
    ActionTrainer,
    CharacterTrainer,
    EventTypeTrainer,
    InstrumentTrainer,
    RelationshipTrainer,
    StacTrainer,
)


def train_all_steps(
    data_dir: str,
    steps: Optional[List[str]] = None,
    model_name: str = "unsloth/Qwen2.5-7B-Instruct",
    output_dir: str = "./models",
    config: Optional[FineTuneConfig] = None,
):
    """Train all specified pipeline steps.
    
    Args:
        data_dir: Directory containing JSON annotation files
        steps: List of steps to train (default: all steps)
        model_name: Base model name
        output_dir: Output directory for trained models
        config: Fine-tuning configuration (default: FineTuneConfig())
    """
    if steps is None:
        steps = ["character", "instrument", "relationship", "action", "stac", "event_type"]
    
    if config is None:
        config = FineTuneConfig(model_name=model_name, output_dir=output_dir)
    else:
        config.model_name = model_name
        config.output_dir = output_dir
    
    # Prepare all training data
    print(f"Preparing training data from {data_dir}...")
    all_examples = prepare_all_training_data(
        data_dir=data_dir,
        steps=steps,
        output_dir=None,  # Don't save intermediate files
    )
    
    # Trainer class map
    trainer_map = {
        "character": CharacterTrainer,
        "instrument": InstrumentTrainer,
        "relationship": RelationshipTrainer,
        "action": ActionTrainer,
        "stac": StacTrainer,
        "event_type": EventTypeTrainer,
    }
    
    # Train each step
    for step in steps:
        if step not in all_examples:
            print(f"Warning: No examples found for {step}, skipping...")
            continue
        
        examples = all_examples[step]
        if not examples:
            print(f"Warning: No examples found for {step}, skipping...")
            continue
        
        print(f"\n{'='*60}")
        print(f"Training {step} with {len(examples)} examples")
        print(f"{'='*60}")
        
        # Get trainer class
        trainer_class = trainer_map[step]
        
        # Create trainer
        trainer = trainer_class(model_name=model_name, step_name=step, config=config)
        
        # Load model
        print(f"Loading model {model_name}...")
        trainer.load_model()
        
        # Train (no eval split for simplicity in batch training)
        trainer.train(examples, eval_examples=None)
        
        print(f"Completed training for {step}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train all pipeline steps")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing JSON annotation files"
    )
    parser.add_argument(
        "--steps",
        type=str,
        nargs="+",
        choices=["character", "instrument", "relationship", "action", "stac", "event_type"],
        default=["character", "instrument", "relationship", "action", "stac", "event_type"],
        help="Pipeline steps to train (default: all steps)"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="unsloth/Qwen2.5-7B-Instruct",
        help="Base model name (default: unsloth/Qwen2.5-7B-Instruct)"
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
        default=3,
        help="Number of training epochs (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Training batch size (default: 4)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate (default: 2e-4)"
    )
    
    args = parser.parse_args()
    
    # Create config
    config = FineTuneConfig(
        model_name=args.model_name,
        output_dir=args.output_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )
    
    # Train all steps
    train_all_steps(
        data_dir=args.data_dir,
        steps=args.steps,
        model_name=args.model_name,
        output_dir=args.output_dir,
        config=config,
    )


if __name__ == "__main__":
    main()
