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
    model_name: str = "unsloth/Qwen2.5-7B-Instruct",
    output_dir: str = "./models",
    config: Optional[FineTuneConfig] = None,
    train_split: float = 0.9,
):
    """Train a single pipeline step.
    
    Args:
        step: Step name ("character", "instrument", "relationship", "action", "stac", "event_type")
        data_dir: Directory containing JSON annotation files
        model_name: Base model name
        output_dir: Output directory for trained models
        config: Fine-tuning configuration (default: FineTuneConfig())
        train_split: Train/test split ratio
    """
    if config is None:
        config = FineTuneConfig(model_name=model_name, output_dir=output_dir)
    else:
        config.model_name = model_name
        config.output_dir = output_dir
    
    # Get trainer class
    trainer_class = get_trainer_class(step)
    
    # Get extraction function
    extract_func = get_extract_function(step)
    
    # Load stories
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
    trainer.train(train_examples, eval_examples)
    
    print(f"Training completed for {step}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train a single pipeline step")
    parser.add_argument(
        "--step",
        type=str,
        required=True,
        choices=["character", "instrument", "relationship", "action", "stac", "event_type"],
        help="Pipeline step to train"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing JSON annotation files"
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
    parser.add_argument(
        "--train-split",
        type=float,
        default=0.9,
        help="Train/test split ratio (default: 0.9)"
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
    
    # Train
    train_step(
        step=args.step,
        data_dir=args.data_dir,
        model_name=args.model_name,
        output_dir=args.output_dir,
        config=config,
        train_split=args.train_split,
    )


if __name__ == "__main__":
    main()
