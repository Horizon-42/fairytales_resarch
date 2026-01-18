#!/usr/bin/env python3
"""Extract training data from json_v3 annotation files.

This script extracts training examples from JSON v3 annotation files
and saves them in JSONL format for fine-tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

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


def extract_data_from_directory(
    input_dir: str,
    output_dir: str,
    steps: Optional[List[str]] = None,
    summary: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, int]:
    """Extract training data from all JSON files in a directory.
    
    Args:
        input_dir: Directory containing JSON v3 annotation files
        output_dir: Output directory for JSONL training files
        steps: List of steps to extract (default: all steps)
        summary: Optional summary to use for all stories (default: None/empty)
        verbose: Print progress information
    
    Returns:
        Dictionary mapping step names to number of examples extracted
    """
    if steps is None:
        steps = ["character", "instrument", "relationship", "action", "stac", "event_type"]
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load all stories
    if verbose:
        print(f"Loading JSON files from: {input_dir}")
    
    stories = load_all_annotated_stories(input_dir)
    
    if verbose:
        print(f"Loaded {len(stories)} story files")
    
    # Extract examples for each step
    all_examples = {step: [] for step in steps}
    
    for idx, story in enumerate(stories, 1):
        if verbose:
            story_id = story.get("metadata", {}).get("id", f"story_{idx}")
            print(f"Processing [{idx}/{len(stories)}]: {story_id}")
        
        story_text = story.get("source_info", {}).get("text_content", "")
        
        # Use provided summary or None (empty summary for training)
        story_summary = summary
        
        # Extract examples for each step
        if "character" in steps:
            examples = extract_character_examples(story, story_text, story_summary)
            all_examples["character"].extend(examples)
            if verbose and examples:
                print(f"  - Character: {len(examples)} examples")
        
        if "instrument" in steps:
            examples = extract_instrument_examples(story, story_summary)
            all_examples["instrument"].extend(examples)
            if verbose and examples:
                print(f"  - Instrument: {len(examples)} examples")
        
        if "relationship" in steps:
            examples = extract_relationship_examples(story, story_text, story_summary)
            all_examples["relationship"].extend(examples)
            if verbose and examples:
                print(f"  - Relationship: {len(examples)} examples")
        
        if "action" in steps:
            examples = extract_action_examples(story, story_summary)
            all_examples["action"].extend(examples)
            if verbose and examples:
                print(f"  - Action: {len(examples)} examples")
        
        if "stac" in steps:
            examples = extract_stac_examples(story, story_text, story_summary)
            all_examples["stac"].extend(examples)
            if verbose and examples:
                print(f"  - STAC: {len(examples)} examples")
        
        if "event_type" in steps:
            examples = extract_event_type_examples(story, story_summary)
            all_examples["event_type"].extend(examples)
            if verbose and examples:
                print(f"  - Event Type: {len(examples)} examples")
    
    # Save examples to JSONL files
    if verbose:
        print(f"\nSaving training data to: {output_dir}")
    
    counts = {}
    for step, examples in all_examples.items():
        if not examples:
            if verbose:
                print(f"Warning: No examples extracted for '{step}', skipping...")
            continue
        
        # Save as JSONL
        output_file = output_path / f"{step}_train.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")
        
        counts[step] = len(examples)
        if verbose:
            print(f"  - {step}: {len(examples)} examples -> {output_file}")
    
    return counts


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract training data from JSON v3 annotation files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all steps from a directory
  python -m llm_model.finetune.scripts.extract_training_data \\
      --input-dir datasets/ChineseTales/json_v3 \\
      --output-dir ./training_data

  # Extract specific steps only
  python -m llm_model.finetune.scripts.extract_training_data \\
      --input-dir datasets/ChineseTales/json_v3 \\
      --output-dir ./training_data \\
      --steps character relationship action

  # Extract without verbose output
  python -m llm_model.finetune.scripts.extract_training_data \\
      --input-dir datasets/ChineseTales/json_v3 \\
      --output-dir ./training_data \\
      --quiet
        """
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Input directory containing JSON v3 annotation files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for JSONL training files"
    )
    parser.add_argument(
        "--steps",
        type=str,
        nargs="+",
        choices=["character", "instrument", "relationship", "action", "stac", "event_type"],
        default=["character", "instrument", "relationship", "action", "stac", "event_type"],
        help="Pipeline steps to extract (default: all steps)"
    )
    parser.add_argument(
        "--summary",
        type=str,
        default=None,
        help="Optional summary text to use for all stories (default: empty)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        return 1
    
    if not input_path.is_dir():
        print(f"Error: Input path is not a directory: {args.input_dir}")
        return 1
    
    # Extract data
    try:
        counts = extract_data_from_directory(
            input_dir=str(input_path),
            output_dir=args.output_dir,
            steps=args.steps,
            summary=args.summary,
            verbose=not args.quiet,
        )
        
        # Summary
        if not args.quiet:
            print("\n" + "="*60)
            print("Extraction Summary:")
            print("="*60)
            total = sum(counts.values())
            for step, count in counts.items():
                print(f"  {step:20s}: {count:5d} examples")
            print(f"  {'Total':20s}: {total:5d} examples")
            print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
