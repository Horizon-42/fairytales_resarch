#!/usr/bin/env python3
"""Run full detection pipeline and evaluate against ground truth.

This script:
1. Runs the full detection pipeline on an input story
2. Evaluates the results against a json_v3 ground truth file
3. Outputs evaluation metrics and optionally saves reports

Usage:
    conda run -n nlp python scripts/run_full_pipeline_and_evaluate.py \
        --story-file datasets/texts/CH_002_牛郎织女.txt \
        --ground-truth datasets/ChineseTales/json_v3/CH_002_牛郎织女_v3.json \
        --output-dir results/

    # With custom LLM settings
    conda run -n nlp python scripts/run_full_pipeline_and_evaluate.py \
        --story-file story.txt \
        --ground-truth ground_truth.json \
        --provider ollama \
        --model qwen3:8b \
        --include-instrument
    
    # With performance optimizations (faster)
    conda run -n nlp python scripts/run_full_pipeline_and_evaluate.py \
        --story-file story.txt \
        --ground-truth ground_truth.json \
        --num-predict 512 \
        --num-ctx 4096 \
        --disable-thinking
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_model.evaluation import CompositeEvaluator
from llm_model.evaluation.utils import load_ground_truth
from llm_model.full_detection import process_story
from llm_model.gemini_client import GeminiConfig
from llm_model.huggingface_client import HuggingFaceConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig

import time


def extract_text_spans_from_ground_truth(gt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract text spans from ground truth json_v3 file.
    
    Args:
        gt_data: Ground truth data loaded from json_v3 file
        
    Returns:
        List of text span dicts with 'start', 'end', 'text' keys
    """
    narrative_events = gt_data.get("narrative_events", [])
    text_spans = []
    
    for event in narrative_events:
        text_span = event.get("text_span", {})
        if "text" in text_span and "start" in text_span and "end" in text_span:
            text_spans.append(text_span)
    
    return text_spans


def extract_story_text(gt_data: Dict[str, Any], story_file: Path = None) -> str:
    """Extract story text from ground truth or story file.
    
    Args:
        gt_data: Ground truth data
        story_file: Optional path to story text file
        
    Returns:
        Full story text
    """
    # Try story file first
    if story_file and story_file.exists():
        return story_file.read_text(encoding="utf-8")
    
    # Fall back to text_content in ground truth
    source_info = gt_data.get("source_info", {})
    text_content = source_info.get("text_content", "")
    
    if text_content:
        return text_content
    
    # If no text found, raise error
    raise ValueError(
        "Could not find story text. Provide --story-file or ensure "
        "ground truth has source_info.text_content"
    )


def run_pipeline_and_evaluate(
    story_file: Path,
    ground_truth_file: Path,
    output_dir: Path = None,
    llm_config: LLMConfig = None,
    include_instrument: bool = False,
    save_prediction: bool = True,
    save_reports: bool = True,
) -> Dict[str, Any]:
    """Run full pipeline and evaluate results.
    
    Args:
        story_file: Path to story text file
        ground_truth_file: Path to json_v3 ground truth file
        output_dir: Optional output directory for results
        llm_config: LLM configuration
        include_instrument: Whether to include instrument recognition
        save_prediction: Whether to save prediction JSON
        save_reports: Whether to save evaluation reports
        
    Returns:
        Dictionary with evaluation results
    """
    print(f"Loading ground truth from: {ground_truth_file}")
    gt_data = load_ground_truth(str(ground_truth_file))
    
    print(f"Extracting story text from: {story_file}")
    story_text = extract_story_text(gt_data, story_file)
    
    print("Extracting text spans from ground truth...")
    text_spans = extract_text_spans_from_ground_truth(gt_data)
    print(f"Found {len(text_spans)} text spans to process")
    
    # Get initial characters from ground truth
    initial_characters = gt_data.get("characters", [])
    
    print("\n" + "=" * 60)
    print("Running full detection pipeline...")
    print("=" * 60)
    
    # Run pipeline with timing
    pipeline_start = time.time()
    
    result = process_story(
        story_text=story_text,
        text_spans=text_spans,
        characters=initial_characters.copy() if initial_characters else [],
        llm_config=llm_config or LLMConfig(),
        include_instrument=include_instrument,
    )
    
    pipeline_elapsed = time.time() - pipeline_start
    print(f"\n{'='*60}")
    print(f"Pipeline completed in {pipeline_elapsed:.1f}s ({pipeline_elapsed/60:.1f} minutes)")
    print(f"Generated {len(result['narrative_events'])} events")
    
    # Show timing summary
    if result.get("results"):
        successful_results = [r for r in result["results"] if r.get("success")]
        if successful_results:
            times = [r.get("processing_time", 0) for r in successful_results]
            avg_time = sum(times) / len(times) if times else 0
            total_time = sum(times)
            print(f"Average time per span: {avg_time:.1f}s")
            print(f"Total processing time: {total_time:.1f}s")
    
    # Build prediction JSON in v3 format
    prediction = {
        "version": "3.0",
        "metadata": gt_data.get("metadata", {}).copy(),
        "source_info": gt_data.get("source_info", {}).copy(),
        "characters": result["updated_characters"],
        "narrative_events": result["narrative_events"],
    }
    
    # Save prediction if requested
    if save_prediction and output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        pred_file = output_dir / f"{ground_truth_file.stem}_prediction.json"
        with open(pred_file, "w", encoding="utf-8") as f:
            json.dump(prediction, f, ensure_ascii=False, indent=2)
        print(f"Saved prediction to: {pred_file}")
    
    print("\n" + "=" * 60)
    print("Evaluating results...")
    print("=" * 60)
    
    # Evaluate
    composite = CompositeEvaluator()
    eval_results = composite.evaluate(prediction, gt_data)
    
    # Print summary
    print(f"\n{'='*60}")
    print("Evaluation Results")
    print(f"{'='*60}")
    print(f"Overall Score: {eval_results['overall_score']:.3f}")
    print("\nComponent Scores:")
    for component, score in eval_results["component_scores"].items():
        if score is not None:
            print(f"  - {component}: {score:.3f}")
        else:
            print(f"  - {component}: N/A (GT incomplete)")
    
    # Save reports if requested
    if save_reports and output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        report_json = output_dir / f"{ground_truth_file.stem}_evaluation.json"
        with open(report_json, "w", encoding="utf-8") as f:
            json.dump(eval_results, f, ensure_ascii=False, indent=2)
        print(f"\nSaved JSON report to: {report_json}")
        
        # Save Markdown report
        report_md = output_dir / f"{ground_truth_file.stem}_evaluation.md"
        composite.generate_report(eval_results, output_path=str(report_md), format="markdown")
        print(f"Saved Markdown report to: {report_md}")
    
    print(f"\n{'='*60}")
    print("✓ Evaluation completed!")
    print(f"{'='*60}\n")
    
    return eval_results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run full detection pipeline and evaluate against ground truth.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Required arguments
    parser.add_argument(
        "--story-file",
        type=Path,
        required=True,
        help="Path to story text file",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        required=True,
        help="Path to json_v3 ground truth file",
    )
    
    # Optional output
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for prediction and reports (default: current directory)",
    )
    
    # LLM configuration
    parser.add_argument(
        "--provider",
        default="ollama",
        help="LLM provider: ollama, gemini, or huggingface (default: ollama)",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Model name (default: qwen3:8b)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434)",
    )
    
    # Performance options
    parser.add_argument(
        "--num-predict",
        type=int,
        default=None,
        help="Max tokens to generate (None = default 128). Lower = faster (default: None)",
    )
    parser.add_argument(
        "--num-thread",
        type=int,
        default=None,
        help="CPU threads for inference (None = auto-detect). Set to physical cores count (default: None)",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=4096,
        help="Context window size (default: 4096). Lower = faster but less context",
    )
    parser.add_argument(
        "--disable-thinking",
        action="store_true",
        help="Explicitly disable thinking mode (faster for qwen3)",
    )
    
    # Pipeline options
    parser.add_argument(
        "--include-instrument",
        action="store_true",
        help="Include instrument recognition",
    )
    
    # Output options
    parser.add_argument(
        "--no-save-prediction",
        action="store_true",
        help="Don't save prediction JSON",
    )
    parser.add_argument(
        "--no-save-reports",
        action="store_true",
        help="Don't save evaluation reports",
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.story_file.exists():
        print(f"Error: Story file not found: {args.story_file}", file=sys.stderr)
        return 1
    
    if not args.ground_truth.exists():
        print(f"Error: Ground truth file not found: {args.ground_truth}", file=sys.stderr)
        return 1
    
    # Setup output directory
    output_dir = args.output_dir or Path.cwd()
    
    # Setup LLM config
    import os
    llm_config = LLMConfig(
        provider=args.provider,
        ollama=OllamaConfig(
            base_url=args.base_url,
            model=args.model if args.provider == "ollama" else os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            num_ctx=args.num_ctx,
            num_predict=args.num_predict,
            num_thread=args.num_thread,
            think=False if args.disable_thinking else None,  # Disable thinking by default for speed
        ),
        gemini=GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=args.model if args.provider == "gemini" else os.getenv("GEMINI_MODEL", ""),
            model_thinking=os.getenv("GEMINI_MODEL_THINKING", ""),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.9")),
            max_output_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")),
        ),
        huggingface=HuggingFaceConfig(
            model=args.model if args.provider in ("huggingface", "hf") else os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
            device=os.getenv("HF_DEVICE", "auto"),
            temperature=float(os.getenv("HF_TEMPERATURE", "0.2")),
            top_p=float(os.getenv("HF_TOP_P", "0.9")),
            max_new_tokens=int(os.getenv("HF_MAX_NEW_TOKENS", "2048")),
        ),
    )
    
    try:
        run_pipeline_and_evaluate(
            story_file=args.story_file,
            ground_truth_file=args.ground_truth,
            output_dir=output_dir,
            llm_config=llm_config,
            include_instrument=args.include_instrument,
            save_prediction=not args.no_save_prediction,
            save_reports=not args.no_save_reports,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
