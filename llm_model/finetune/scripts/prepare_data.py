"""Script to prepare training data from annotated stories."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..data_preparation import prepare_all_training_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Prepare training data from annotated stories")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing JSON annotation files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for training data JSONL files"
    )
    parser.add_argument(
        "--steps",
        type=str,
        nargs="+",
        choices=["character", "instrument", "relationship", "action", "stac", "event_type"],
        default=["character", "instrument", "relationship", "action", "stac", "event_type"],
        help="Pipeline steps to prepare data for (default: all steps)"
    )
    
    args = parser.parse_args()
    
    # Prepare data
    print(f"Preparing training data from {args.data_dir}...")
    print(f"Output directory: {args.output_dir}")
    print(f"Steps: {', '.join(args.steps)}")
    
    all_examples = prepare_all_training_data(
        data_dir=args.data_dir,
        steps=args.steps,
        output_dir=args.output_dir,
    )
    
    # Summary
    print("\n" + "="*60)
    print("Data preparation summary:")
    print("="*60)
    for step, examples in all_examples.items():
        print(f"{step}: {len(examples)} examples")
    print("="*60)


if __name__ == "__main__":
    main()
