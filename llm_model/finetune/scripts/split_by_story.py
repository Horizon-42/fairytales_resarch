"""Split training data by story ID to prevent data leakage."""

import argparse
import json
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple


def extract_story_id(filename: str) -> str:
    """Extract base story ID from filename.

    Examples:
        CH_002_牛郎织女_gen_01_character.jsonl -> CH_002_牛郎织女
        CH_003_孟姜女哭长城_gen_05_character.jsonl -> CH_003_孟姜女哭长城
    """
    # Remove file extension
    name = filename.replace('.jsonl', '')

    # Split by underscore and take first parts before _gen_
    parts = name.split('_gen_')
    if len(parts) >= 1:
        return parts[0]

    # Fallback: return the whole filename
    return name


def load_examples_by_story(per_story_dir: Path) -> Dict[str, List[Dict]]:
    """Load examples grouped by story ID.

    Args:
        per_story_dir: Directory containing per-story JSONL files

    Returns:
        Dictionary mapping story_id -> list of examples
    """
    examples_by_story = defaultdict(list)

    for jsonl_file in per_story_dir.glob('*.jsonl'):
        story_id = extract_story_id(jsonl_file.name)

        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    example = json.loads(line)
                    examples_by_story[story_id].append(example)

    return examples_by_story


def split_by_story(
    examples_by_story: Dict[str, List[Dict]],
    train_ratio: float = 0.8,
    seed: int = 42
) -> Tuple[List[Dict], List[Dict]]:
    """Split examples by story ID.

    Args:
        examples_by_story: Dictionary mapping story_id -> list of examples
        train_ratio: Ratio of stories to use for training
        seed: Random seed for reproducibility

    Returns:
        (train_examples, val_examples)
    """
    random.seed(seed)

    # Get all story IDs
    story_ids = list(examples_by_story.keys())
    random.shuffle(story_ids)

    # Split story IDs
    split_idx = int(len(story_ids) * train_ratio)
    train_story_ids = set(story_ids[:split_idx])
    val_story_ids = set(story_ids[split_idx:])

    # Collect examples
    train_examples = []
    val_examples = []

    for story_id, examples in examples_by_story.items():
        if story_id in train_story_ids:
            train_examples.extend(examples)
        else:
            val_examples.extend(examples)

    return train_examples, val_examples


def main():
    parser = argparse.ArgumentParser(description='Split training data by story ID')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Training data directory (e.g., training_data)')
    parser.add_argument('--step', type=str, required=True,
                       choices=['character', 'instrument', 'relationship', 'action', 'stac', 'event_type'],
                       help='Step to split')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                       help='Ratio of stories for training (default: 0.8)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    per_story_dir = data_dir / args.step / 'per_story'

    if not per_story_dir.exists():
        print(f"Error: {per_story_dir} does not exist")
        return 1

    print(f"Loading examples from {per_story_dir}...")
    examples_by_story = load_examples_by_story(per_story_dir)

    print(f"\nFound {len(examples_by_story)} unique stories")
    total_examples = sum(len(exs) for exs in examples_by_story.values())
    print(f"Total examples: {total_examples}")

    # Show story distribution
    print(f"\nExamples per story:")
    for story_id in sorted(examples_by_story.keys())[:10]:
        print(f"  {story_id}: {len(examples_by_story[story_id])} examples")
    if len(examples_by_story) > 10:
        print(f"  ... and {len(examples_by_story) - 10} more stories")

    # Split by story
    print(f"\nSplitting stories (train_ratio={args.train_ratio}, seed={args.seed})...")
    train_examples, val_examples = split_by_story(
        examples_by_story,
        train_ratio=args.train_ratio,
        seed=args.seed
    )

    print(f"\nSplit results:")
    print(f"  Training examples: {len(train_examples)} ({len(train_examples)/total_examples*100:.1f}%)")
    print(f"  Validation examples: {len(val_examples)} ({len(val_examples)/total_examples*100:.1f}%)")

    # Save split files
    train_file = data_dir / f'{args.step}_train.jsonl'
    val_file = data_dir / f'{args.step}_val.jsonl'

    print(f"\nSaving split files...")
    with open(train_file, 'w', encoding='utf-8') as f:
        for example in train_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    print(f"  Saved {train_file}")

    with open(val_file, 'w', encoding='utf-8') as f:
        for example in val_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    print(f"  Saved {val_file}")

    print(f"\n✓ Split complete!")
    return 0


if __name__ == '__main__':
    exit(main())
