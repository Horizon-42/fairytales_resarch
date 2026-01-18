"""Script to evaluate fine-tuned models on test set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

from ..data_preparation import load_annotated_story, load_all_annotated_stories
from ..evaluator import evaluate_finetuned_pipeline


def load_test_stories(test_dir: str) -> List[Dict[str, Any]]:
    """Load test stories from directory.
    
    Args:
        test_dir: Directory containing test JSON v3 files
    
    Returns:
        List of story dictionaries
    """
    return load_all_annotated_stories(test_dir)


def find_finetuned_models(models_dir: str) -> Dict[str, str]:
    """Find all fine-tuned models in models directory.
    
    Args:
        models_dir: Directory containing fine-tuned models
    
    Returns:
        Dictionary mapping step names to model paths
    """
    models_path = Path(models_dir)
    if not models_path.exists():
        return {}
    
    step_map = {
        "character_recognition": "character",
        "instrument_recognition": "instrument",
        "relationship_deduction": "relationship",
        "action_category": "action",
        "stac_analysis": "stac",
        "event_type_classification": "event_type",
    }
    
    fine_tuned_models = {}
    
    for step_dir in models_path.iterdir():
        if not step_dir.is_dir():
            continue
        
        step_name = step_dir.name
        # Check if this is a valid model directory (has config.json)
        if (step_dir / "config.json").exists() or (step_dir / "adapter_config.json").exists():
            # Map to step name
            for key, value in step_map.items():
                if step_name == key or step_name.startswith(value):
                    fine_tuned_models[value] = str(step_dir)
                    break
    
    return fine_tuned_models


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate fine-tuned models on test set",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate with fine-tuned models
  python -m llm_model.finetune.scripts.evaluate_model \\
      --test-dir datasets/ChineseTales/json_v3 \\
      --groundtruth-dir datasets/ChineseTales/json_v3 \\
      --models-dir ./models \\
      --output-dir ./evaluation_results

  # Evaluate without fine-tuned models (baseline)
  python -m llm_model.finetune.scripts.evaluate_model \\
      --test-dir datasets/ChineseTales/json_v3 \\
      --groundtruth-dir datasets/ChineseTales/json_v3 \\
      --output-dir ./evaluation_results
        """
    )
    
    parser.add_argument(
        "--test-dir",
        type=str,
        required=True,
        help="Directory containing test story JSON v3 files"
    )
    parser.add_argument(
        "--groundtruth-dir",
        type=str,
        required=True,
        help="Directory containing groundtruth JSON v3 files"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=None,
        help="Directory containing fine-tuned models (optional)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./evaluation_results",
        help="Output directory for evaluation results"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    # Load test and groundtruth stories
    print("Loading test stories...")
    test_stories = load_test_stories(args.test_dir)
    print(f"Loaded {len(test_stories)} test stories")
    
    print("Loading groundtruth stories...")
    groundtruth_stories = load_all_annotated_stories(args.groundtruth_dir)
    print(f"Loaded {len(groundtruth_stories)} groundtruth stories")
    
    if len(test_stories) != len(groundtruth_stories):
        print(f"Warning: Test stories ({len(test_stories)}) and groundtruth ({len(groundtruth_stories)}) count mismatch")
        # Match by story ID
        test_dict = {s.get("metadata", {}).get("id"): s for s in test_stories}
        gt_dict = {s.get("metadata", {}).get("id"): s for s in groundtruth_stories}
        
        matched_test = []
        matched_gt = []
        
        for story_id in test_dict.keys():
            if story_id in gt_dict:
                matched_test.append(test_dict[story_id])
                matched_gt.append(gt_dict[story_id])
        
        test_stories = matched_test
        groundtruth_stories = matched_gt
        print(f"Matched {len(test_stories)} stories by ID")
    
    # Find fine-tuned models
    fine_tuned_models = {}
    if args.models_dir:
        fine_tuned_models = find_finetuned_models(args.models_dir)
        if fine_tuned_models:
            print(f"Found fine-tuned models: {list(fine_tuned_models.keys())}")
        else:
            print("No fine-tuned models found in models directory")
    
    # Evaluate
    try:
        results = evaluate_finetuned_pipeline(
            test_stories=test_stories,
            groundtruth_stories=groundtruth_stories,
            fine_tuned_model_paths=fine_tuned_models if fine_tuned_models else None,
            output_dir=args.output_dir,
            verbose=not args.quiet,
        )
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
