"""Evaluate full_detection pipeline on validation set stories.

This script runs full_detection on all 10 validation stories and computes accuracy.

Usage:
    # Evaluate fine-tuned model (default)
    conda run -n nlp python3 scripts/eval_validation_set.py

    # Evaluate baseline model (no fine-tuning)
    conda run -n nlp python3 scripts/eval_validation_set.py --use-baseline

    # Limit to N stories for testing
    conda run -n nlp python3 scripts/eval_validation_set.py --limit 2
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_model.full_detection import run_pipeline_batch
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig
from llm_model.unsloth_client import UnslothConfig
from llm_model.env import load_repo_dotenv


def identify_val_stories() -> Set[str]:
    """Identify the 10 validation stories using same split logic as training."""
    data_dir = project_root / "training_data" / "character" / "per_story"
    story_examples = defaultdict(list)

    for file in sorted(data_dir.glob('*.jsonl')):
        parts = file.stem.split('_gen_')
        story_id = parts[0] if parts else file.stem

        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    story_examples[story_id].append(example)

    # Same split logic as split_by_story.py
    import random
    story_ids = list(story_examples.keys())
    random.seed(42)
    random.shuffle(story_ids)

    split_idx = int(len(story_ids) * 0.8)
    val_story_ids = set(story_ids[split_idx:])

    return val_story_ids


def load_ground_truth(story_id: str) -> Dict[str, Any]:
    """Load ground truth JSON v3 file for a story."""
    json_v3_dir = project_root / "datasets" / "ChineseTales" / "json_v3"

    # Try different patterns
    for pattern in [f"{story_id}_v3.json", f"{story_id.replace('_', '-')}_v3.json"]:
        file_path = json_v3_dir / pattern
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    # Search for files containing story ID
    for file in json_v3_dir.glob('*_v3.json'):
        if story_id in file.stem:
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)

    return None


def evaluate_characters(pred: Dict, gt: Dict) -> Dict[str, float]:
    """Evaluate character detection."""
    pred_chars = {c.get("name", "") for c in pred.get("characters", []) if c.get("name")}
    gt_chars = {c.get("name", "") for c in gt.get("characters", []) if c.get("name")}

    tp = len(pred_chars & gt_chars)
    fp = len(pred_chars - gt_chars)
    fn = len(gt_chars - pred_chars)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "correct": tp,
        "predicted": len(pred_chars),
        "ground_truth": len(gt_chars)
    }


def evaluate_events(pred: Dict, gt: Dict) -> Dict[str, float]:
    """Evaluate narrative events count."""
    pred_count = len(pred.get("narrative_events", []))
    gt_count = len(gt.get("narrative_events", []))

    accuracy = min(pred_count / gt_count, 1.0) if gt_count > 0 else 0.0

    return {
        "accuracy": accuracy,
        "predicted": pred_count,
        "ground_truth": gt_count
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate full_detection on validation set")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of stories")
    parser.add_argument("--provider", default="unsloth", help="LLM provider (ollama/unsloth)")
    parser.add_argument("--model-path", default="models/character", help="Path to fine-tuned model (for unsloth)")
    parser.add_argument("--base-model", default="unsloth/Qwen3-4B-unsloth-bnb-4bit", help="Base model name (for unsloth)")
    parser.add_argument("--use-baseline", action="store_true", help="Use baseline model (set model-path to base-model)")
    parser.add_argument("--output-dir", default="evaluation_results", help="Output directory")

    args = parser.parse_args()

    # If use-baseline is enabled, override model-path with base-model
    if args.use_baseline:
        args.model_path = args.base_model

    # Load environment
    load_repo_dotenv()

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("="*70)
    print("Full Detection Pipeline - Validation Set Evaluation")
    print("="*70)

    # Identify validation stories
    print("\n[1/4] Identifying validation stories...")
    val_stories = identify_val_stories()
    print(f"Found {len(val_stories)} validation stories")

    if args.limit:
        val_stories = set(sorted(val_stories)[:args.limit])
        print(f"Limited to {args.limit} stories")

    for sid in sorted(val_stories):
        print(f"  - {sid}")

    # Setup LLM
    print(f"\n[2/4] Setting up LLM (provider={args.provider})...")

    if args.provider == "unsloth":
        mode = "BASELINE" if args.use_baseline else "FINE-TUNED"
        print(f"   Mode: {mode}")
        print(f"   Model path: {args.model_path}")
        print(f"   Base model: {args.base_model}")
        llm_config = LLMConfig(
            provider="unsloth",
            unsloth=UnslothConfig(
                model_path=args.model_path,
                base_model=args.base_model
            )
        )
    else:
        llm_config = LLMConfig(
            provider=args.provider,
            ollama=OllamaConfig(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "qwen3:8b")
            )
        )

    # Process each story
    print(f"\n[3/4] Running full_detection on {len(val_stories)} stories...")

    results = []

    for i, story_id in enumerate(sorted(val_stories), 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(val_stories)}] {story_id}")
        print(f"{'='*70}")

        try:
            # Load ground truth
            gt_data = load_ground_truth(story_id)
            if gt_data is None:
                print(f"  ❌ Ground truth not found, skipping")
                continue

            story_text = gt_data.get("source_info", {}).get("text_content", "")
            gt_events = gt_data.get("narrative_events", [])

            print(f"  Ground truth: {len(gt_data.get('characters', []))} chars, {len(gt_events)} events")

            # Extract text spans
            text_spans = []
            for event in gt_events:
                ts = event.get("text_span", {})
                if "start" in ts and "end" in ts:
                    text_spans.append({
                        "start": ts["start"],
                        "end": ts["end"],
                        "text": ts.get("text", story_text[ts["start"]:ts["end"]]),
                        "time_order": event.get("time_order", len(text_spans) + 1)
                    })

            if not text_spans:
                print(f"  ⚠️  No text spans found, using full text")
                text_spans = [{
                    "start": 0,
                    "end": len(story_text),
                    "text": story_text,
                    "time_order": 1
                }]

            print(f"  Running full_detection on {len(text_spans)} text spans...")

            # Run pipeline
            result = run_pipeline_batch(
                story_text=story_text,
                text_spans=text_spans,
                characters=[],
                llm_config=llm_config,
                include_instrument=False
            )

            # Build prediction
            prediction = {
                "characters": result["updated_characters"],
                "narrative_events": result["narrative_events"],
                "source_info": gt_data.get("source_info", {})
            }

            # Save prediction
            pred_file = output_dir / f"{story_id}_prediction.json"
            with open(pred_file, 'w', encoding='utf-8') as f:
                json.dump(prediction, f, ensure_ascii=False, indent=2)
            print(f"  💾 Saved prediction to {pred_file.name}")

            # Evaluate
            char_metrics = evaluate_characters(prediction, gt_data)
            event_metrics = evaluate_events(prediction, gt_data)

            result_data = {
                "story_id": story_id,
                "character_metrics": char_metrics,
                "event_metrics": event_metrics
            }
            results.append(result_data)

            # Print metrics
            print(f"\n  📊 Character Detection:")
            print(f"     Precision: {char_metrics['precision']:.3f}")
            print(f"     Recall:    {char_metrics['recall']:.3f}")
            print(f"     F1 Score:  {char_metrics['f1']:.3f}")
            print(f"     Correct:   {char_metrics['correct']}/{char_metrics['ground_truth']}")

            print(f"\n  📊 Event Detection:")
            print(f"     Count Accuracy: {event_metrics['accuracy']:.3f}")
            print(f"     Predicted:      {event_metrics['predicted']}")
            print(f"     Ground Truth:   {event_metrics['ground_truth']}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Aggregate results
    print(f"\n{'='*70}")
    print("[4/4] Aggregated Results")
    print(f"{'='*70}")

    if not results:
        print("❌ No successful evaluations!")
        return 1

    # Calculate averages
    avg_char_precision = sum(r["character_metrics"]["precision"] for r in results) / len(results)
    avg_char_recall = sum(r["character_metrics"]["recall"] for r in results) / len(results)
    avg_char_f1 = sum(r["character_metrics"]["f1"] for r in results) / len(results)
    avg_event_accuracy = sum(r["event_metrics"]["accuracy"] for r in results) / len(results)

    print(f"\n📊 Overall Metrics ({len(results)} stories):")
    print(f"\n   Character Detection:")
    print(f"     Average Precision: {avg_char_precision:.3f}")
    print(f"     Average Recall:    {avg_char_recall:.3f}")
    print(f"     Average F1 Score:  {avg_char_f1:.3f}")

    print(f"\n   Event Detection:")
    print(f"     Average Count Accuracy: {avg_event_accuracy:.3f}")

    # Save summary
    config_info = {
        "provider": args.provider,
        "num_stories": len(results)
    }
    if args.provider == "unsloth":
        config_info["use_baseline"] = args.use_baseline
        config_info["model_path"] = args.model_path
        config_info["base_model"] = args.base_model
    else:
        config_info["model"] = os.getenv("OLLAMA_MODEL", "qwen3:8b")

    summary = {
        "overall_metrics": {
            "character_precision": avg_char_precision,
            "character_recall": avg_char_recall,
            "character_f1": avg_char_f1,
            "event_count_accuracy": avg_event_accuracy
        },
        "per_story_results": results,
        "config": config_info
    }

    summary_file = output_dir / "validation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Evaluation complete!")
    print(f"   Summary saved to: {summary_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
