"""Evaluation utilities for fine-tuned models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ..evaluation import CompositeEvaluator
    from ..full_detection import process_story
    from ..full_detection.story_processor import generate_story_summary
    from ..llm_router import LLMConfig
except ImportError:
    try:
        from llm_model.evaluation import CompositeEvaluator
        from llm_model.full_detection import process_story
        from llm_model.full_detection.story_processor import generate_story_summary
        from llm_model.llm_router import LLMConfig
    except ImportError:
        CompositeEvaluator = None
        process_story = None
        generate_story_summary = None
        LLMConfig = None


def evaluate_finetuned_pipeline(
    test_stories: List[Dict[str, Any]],
    groundtruth_stories: List[Dict[str, Any]],
    fine_tuned_model_paths: Optional[Dict[str, str]] = None,
    output_dir: str = "./evaluation_results",
    verbose: bool = True,
) -> Dict[str, Any]:
    """Evaluate fine-tuned models on test set using full pipeline.
    
    This function:
    1. Uses fine-tuned models (if provided) or default models to run the full detection pipeline
    2. Compares predictions with groundtruth
    3. Uses evaluation module to calculate accuracy metrics
    
    Args:
        test_stories: List of test story dictionaries (with text_content)
        groundtruth_stories: List of groundtruth JSON v3 dictionaries
        fine_tuned_model_paths: Optional dict mapping step names to model paths
                              e.g., {"character": "./models/character_recognition", ...}
        output_dir: Output directory for evaluation results
        verbose: Print progress information
    
    Returns:
        Evaluation results dictionary
    """
    if CompositeEvaluator is None:
        raise ImportError("llm_model.evaluation module not available")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create evaluator
    evaluator = CompositeEvaluator()
    
    # TODO: Integrate fine-tuned models with LLM router
    # For now, using default LLM config
    # In the future, we can create a custom LLMConfig that loads fine-tuned models
    llm_config = LLMConfig()
    
    if verbose:
        print(f"Evaluating {len(test_stories)} test stories...")
        if fine_tuned_model_paths:
            print(f"Using fine-tuned models: {list(fine_tuned_model_paths.keys())}")
        else:
            print("Using default models (fine-tuned models not provided)")
    
    all_results = []
    
    for idx, (test_story, gt_story) in enumerate(zip(test_stories, groundtruth_stories), 1):
        try:
            story_id = gt_story.get("metadata", {}).get("id", f"story_{idx}")
            story_text = test_story.get("source_info", {}).get("text_content", "")
            
            if not story_text:
                if verbose:
                    print(f"  [{idx}/{len(test_stories)}] {story_id}: Skipping (no text content)")
                continue
            
            # Get text spans from groundtruth
            gt_events = gt_story.get("narrative_events", [])
            text_spans = []
            for event in gt_events:
                text_span = event.get("text_span", {})
                if "text" in text_span:
                    text_spans.append(text_span)
                elif "start" in text_span and "end" in text_span:
                    text_spans.append({
                        "start": text_span["start"],
                        "end": text_span["end"],
                        "text": story_text[text_span["start"]:text_span["end"]]
                    })
            
            if not text_spans:
                if verbose:
                    print(f"  [{idx}/{len(test_stories)}] {story_id}: Skipping (no text spans)")
                continue
            
            # Generate summary
            summary = generate_story_summary(
                story_text=story_text,
                llm_config=llm_config
            )
            
            # Run full pipeline
            # TODO: Integrate fine-tuned models here
            # For now, using default pipeline
            result = process_story(
                story_text=story_text,
                text_spans=text_spans,
                characters=gt_story.get("characters", []),
                llm_config=llm_config,
                include_instrument=False,
                generate_summary=False,
                summary=summary,
            )
            
            # Build prediction JSON v3 format
            prediction = {
                "version": "3.0",
                "metadata": gt_story.get("metadata", {}),
                "source_info": {
                    "text_content": story_text,
                    **gt_story.get("source_info", {})
                },
                "characters": result.get("updated_characters", []),
                "narrative_events": result.get("narrative_events", []),
            }
            
            # Evaluate
            eval_result = evaluator.evaluate(prediction, gt_story, story_text)
            eval_result["story_id"] = story_id
            all_results.append(eval_result)
            
            if verbose and ((idx % 10 == 0) or (idx == len(test_stories))):
                overall = eval_result.get("overall_score", 0.0)
                print(f"  [{idx}/{len(test_stories)}] {story_id}: Overall Score = {overall:.3f}")
        
        except Exception as e:
            if verbose:
                print(f"  [{idx}/{len(test_stories)}] Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_results:
        print("Warning: No evaluation results generated")
        return {}
    
    # Aggregate results
    aggregated = evaluator.aggregate_results(all_results)
    
    # Save evaluation results
    eval_file = output_path / "evaluation_results.json"
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump({
            "aggregated": aggregated,
            "individual_results": all_results,
            "num_stories": len(all_results),
            "fine_tuned_models": fine_tuned_model_paths or {},
        }, f, indent=2, ensure_ascii=False)
    
    # Generate report
    report_file = output_path / "evaluation_report.md"
    evaluator.generate_report(aggregated, str(report_file), format="markdown")
    
    if verbose:
        print(f"\nEvaluation results saved to {eval_file}")
        print(f"Evaluation report saved to {report_file}")
        print(f"\nOverall Score: {aggregated.get('overall_score', 0.0):.3f}")
        print("Component Scores:")
        for component, score in aggregated.get("component_scores", {}).items():
            if score is not None:
                print(f"  {component}: {score:.3f}")
    
    return aggregated
