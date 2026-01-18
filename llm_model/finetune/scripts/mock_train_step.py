"""Mock training script to test training pipeline without loading models.

This script tests all steps of the training pipeline except actual model loading
and training. It's useful for debugging data preparation, extraction, and formatting
without requiring GPU or model downloads.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from ..config import FineTuneConfig
from ..data_preparation import (
    extract_action_examples,
    extract_character_examples,
    extract_event_type_examples,
    extract_instrument_examples,
    extract_relationship_examples,
    extract_stac_examples,
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
from .train_step import get_extract_function, get_trainer_class


def mock_train_step(
    step: str,
    data_dir: str,
    model_name: str = "unsloth/Qwen2.5-7B-Instruct",
    output_dir: str = "./models",
    config: Optional[FineTuneConfig] = None,
    train_split: float = 0.9,
):
    """Mock training step that tests fine-tuning pipeline components.
    
    This function tests the fine-tuning pipeline using pre-prepared training data:
    1. Loads training examples from JSONL files
    2. Validates example structure
    3. Tests data formatting (format_example)
    4. Tests dataset preparation (prepare_dataset)
    5. Tests training configuration
    6. Does NOT test data extraction (data is already prepared)
    7. Does NOT load actual models (mock test only)
    
    Args:
        step: Step name ("character", "instrument", "relationship", "action", "stac", "event_type")
        data_dir: Directory containing JSONL training data files
        model_name: Base model name (for compatibility)
        output_dir: Output directory (for saving validation results)
        config: Fine-tuning configuration (default: FineTuneConfig())
        train_split: Train/test split ratio
    
    Returns:
        Dict with validation results
    """
    print(f"=== Mock Training Test for Step: {step} ===\n")
    
    if config is None:
        config = FineTuneConfig(model_name=model_name, output_dir=output_dir)
    else:
        config.model_name = model_name
        config.output_dir = output_dir
    
    validation_results = {
        "step": step,
        "data_loading": {"success": False, "error": None, "num_examples": 0},
        "data_validation": {"success": False, "error": None, "invalid_count": 0},
        "data_formatting": {"success": False, "error": None, "num_formatted": 0, "errors": []},
        "dataset_preparation": {"success": False, "error": None},
        "config_validation": {"success": False, "error": None},
        "data_split": {"success": False, "error": None, "train_count": 0, "eval_count": 0},
        "loss_and_eval": {"success": False, "error": None},
    }
    
    try:
        # Step 1: Load training data from JSONL
        print(f"[1/6] Loading training data from {data_dir}...")
        data_path = Path(data_dir)
        jsonl_file = data_path / f"{step}_train.jsonl"
        
        if not jsonl_file.exists():
            error_msg = f"Training data file not found: {jsonl_file}"
            print(f"      ✗ {error_msg}")
            validation_results["data_loading"]["error"] = error_msg
            return validation_results
        
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
                    print(f"      ⚠ Warning: Failed to parse line {line_num}: {e}")
                    continue
        
        print(f"      ✓ Loaded {len(all_examples)} training examples from {jsonl_file.name}")
        validation_results["data_loading"]["success"] = True
        validation_results["data_loading"]["num_examples"] = len(all_examples)
        
        if len(all_examples) == 0:
            print("      ✗ No valid examples found!")
            return validation_results
        
        # Step 2: Validate example structure
        print(f"[2/6] Validating example structure...")
        required_keys = ["instruction", "input", "output"]
        invalid_examples = []
        
        for idx, example in enumerate(all_examples[:100]):  # Check first 100
            if not isinstance(example, dict):
                invalid_examples.append({"index": idx, "error": "Not a dictionary"})
                continue
            missing_keys = [key for key in required_keys if key not in example]
            if missing_keys:
                invalid_examples.append({"index": idx, "error": f"Missing keys: {missing_keys}"})
        
        if invalid_examples:
            print(f"      ⚠ Found {len(invalid_examples)} invalid examples (first 100 checked)")
            for inv in invalid_examples[:5]:
                print(f"         Example {inv['index']}: {inv['error']}")
        else:
            print(f"      ✓ All examples have required keys (checked first 100)")
        
        validation_results["data_validation"]["success"] = len(invalid_examples) == 0
        validation_results["data_validation"]["invalid_count"] = len(invalid_examples)
        
        # Step 3: Test data formatting
        print(f"[3/6] Testing data formatting (format_example)...")
        trainer_class = get_trainer_class(step)
        trainer = trainer_class(model_name=model_name, step_name=step, config=config)
        
        formatted_count = 0
        formatting_errors = []
        
        for idx, example in enumerate(all_examples[:100]):  # Test first 100
            try:
                formatted = trainer.format_example(example)
                if not isinstance(formatted, str) or len(formatted) == 0:
                    formatting_errors.append({"index": idx, "error": "Empty or invalid formatted string"})
                else:
                    formatted_count += 1
            except Exception as e:
                formatting_errors.append({"index": idx, "error": str(e)})
        
        if formatting_errors:
            print(f"      ⚠ Found {len(formatting_errors)} formatting errors (first 100 checked)")
            for err in formatting_errors[:5]:
                print(f"         Example {err['index']}: {err['error']}")
        else:
            print(f"      ✓ All examples formatted successfully (checked first 100)")
        
        validation_results["data_formatting"]["success"] = len(formatting_errors) == 0
        validation_results["data_formatting"]["num_formatted"] = formatted_count
        validation_results["data_formatting"]["errors"] = formatting_errors[:10]  # Store first 10 errors
        
        # Step 4: Test dataset preparation
        print(f"[4/7] Testing dataset preparation (prepare_dataset)...")
        try:
            test_examples = all_examples[:50]  # Test with 50 examples
            dataset = trainer.prepare_dataset(test_examples)
            
            # Validate dataset structure
            # HuggingFace Dataset uses column names, not attributes
            if hasattr(dataset, "column_names") and "formatted_text" in dataset.column_names:
                print(f"      ✓ Dataset created successfully with {len(dataset)} examples")
                print(f"      ✓ Dataset has 'formatted_text' column")
                
                # Test accessing the data
                if len(dataset) > 0:
                    first_item = dataset[0]
                    if "formatted_text" in first_item:
                        print(f"      ✓ Can access formatted_text data (length: {len(first_item['formatted_text'])})")
                    else:
                        print(f"      ⚠ Cannot access formatted_text from dataset items")
                        validation_results["dataset_preparation"]["error"] = "Cannot access formatted_text data"
                        validation_results["dataset_preparation"]["success"] = False
                        return validation_results
                
                validation_results["dataset_preparation"]["success"] = True
            elif hasattr(dataset, "formatted_text"):
                # Fallback: check if it's an attribute
                print(f"      ✓ Dataset created successfully with {len(dataset)} examples")
                print(f"      ✓ Dataset has 'formatted_text' attribute")
                validation_results["dataset_preparation"]["success"] = True
            else:
                print(f"      ✗ Dataset created but missing 'formatted_text' field")
                print(f"         Available columns: {getattr(dataset, 'column_names', 'unknown')}")
                validation_results["dataset_preparation"]["error"] = "Missing formatted_text field"
                validation_results["dataset_preparation"]["success"] = False
        except ImportError as e:
            # Missing dependency - this should fail in mock test
            print(f"      ✗ Dataset preparation failed: {e}")
            print(f"         Install required dependencies: pip install datasets")
            validation_results["dataset_preparation"]["error"] = str(e)
        except Exception as e:
            print(f"      ✗ Dataset preparation failed: {e}")
            validation_results["dataset_preparation"]["error"] = str(e)
            import traceback
            traceback.print_exc()
        
        # Step 5: Validate training configuration
        print(f"[5/7] Validating training configuration...")
        try:
            output_dir = str(Path(config.output_dir) / step)
            training_args_dict = config.get_training_args(output_dir=output_dir)
            
            required_config_keys = ["output_dir", "num_train_epochs", "per_device_train_batch_size", "learning_rate"]
            missing_keys = [key for key in required_config_keys if key not in training_args_dict]
            
            if missing_keys:
                print(f"      ⚠ Missing config keys: {missing_keys}")
                validation_results["config_validation"]["error"] = f"Missing keys: {missing_keys}"
            else:
                print(f"      ✓ Training configuration valid")
                print(f"         Epochs: {training_args_dict.get('num_train_epochs')}")
                print(f"         Batch size: {training_args_dict.get('per_device_train_batch_size')}")
                print(f"         Learning rate: {training_args_dict.get('learning_rate')}")
                validation_results["config_validation"]["success"] = True
        except Exception as e:
            print(f"      ✗ Config validation failed: {e}")
            validation_results["config_validation"]["error"] = str(e)
        
        # Step 6: Test data splitting
        print(f"[6/7] Testing data splitting (train_split={train_split})...")
        try:
            split_idx = int(len(all_examples) * train_split)
            train_examples = all_examples[:split_idx]
            eval_examples = all_examples[split_idx:] if split_idx < len(all_examples) else []
            
            print(f"      ✓ Train examples: {len(train_examples)}")
            print(f"      ✓ Eval examples: {len(eval_examples)}")
            validation_results["data_split"]["success"] = True
            validation_results["data_split"]["train_count"] = len(train_examples)
            validation_results["data_split"]["eval_count"] = len(eval_examples)
        except Exception as e:
            print(f"      ✗ Data splitting failed: {e}")
            validation_results["data_split"]["error"] = str(e)
        
        # Step 7: Test loss recording and evaluation
        print(f"[7/7] Testing loss recording and evaluation...")
        try:
            # Mock loss history (simulate training steps)
            loss_history = []
            for step_num in range(0, 100, 10):  # Simulate 10 training steps
                loss_history.append({
                    "step": step_num,
                    "epoch": step_num / 100.0,
                    "train_loss": 2.5 - (step_num * 0.01),  # Decreasing loss
                    "learning_rate": 0.0002,
                })
            
            # Save loss history as CSV
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            loss_file = output_path / "loss_history.csv"
            import csv
            with open(loss_file, "w", encoding="utf-8", newline="") as f:
                if loss_history:
                    fieldnames = ["step", "epoch", "train_loss", "eval_loss", "learning_rate"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                    for entry in loss_history:
                        writer.writerow(entry)
            print(f"      ✓ Loss history saved to {loss_file} ({len(loss_history)} entries)")
            
            # Test evaluation with mocked model output (copy from ground truth)
            if eval_examples:
                print(f"      Testing evaluation with {len(eval_examples[:20])} examples...")
                correct = 0
                total = 0
                predictions = []
                
                for idx, example in enumerate(eval_examples[:20], 1):  # Test first 20
                    try:
                        # Mock model output: directly copy from ground truth
                        expected_output = json.loads(example["output"])
                        predicted_output = expected_output  # Simulate perfect model
                        
                        # Test comparison logic
                        is_correct = trainer._compare_outputs(predicted_output, expected_output)
                        
                        predictions.append({
                            "example_idx": idx,
                            "expected": expected_output,
                            "predicted": predicted_output,
                            "correct": is_correct,
                        })
                        
                        if is_correct:
                            correct += 1
                        total += 1
                    except Exception as e:
                        print(f"         ⚠ Error evaluating example {idx}: {e}")
                        continue
                
                accuracy = correct / total if total > 0 else 0.0
                print(f"      ✓ Evaluation completed: {accuracy:.3f} accuracy ({correct}/{total})")
                
                # Save evaluation results
                eval_file = output_path / "step_evaluation.json"
                eval_results = {
                    "step_name": step,
                    "total_examples": total,
                    "correct": correct,
                    "accuracy": accuracy,
                    "predictions": predictions,
                }
                with open(eval_file, "w", encoding="utf-8") as f:
                    json.dump(eval_results, f, indent=2, ensure_ascii=False)
                print(f"      ✓ Evaluation results saved to {eval_file}")
                
                validation_results["loss_and_eval"] = {
                    "success": True,
                    "loss_entries": len(loss_history),
                    "eval_accuracy": accuracy,
                    "eval_examples": total,
                }
            else:
                print(f"      ⊘ Evaluation skipped (no eval examples)")
                validation_results["loss_and_eval"] = {
                    "success": True,
                    "loss_entries": len(loss_history),
                    "eval_accuracy": None,
                    "eval_examples": 0,
                }
                
        except Exception as e:
            print(f"      ✗ Loss/evaluation test failed: {e}")
            validation_results["loss_and_eval"] = {
                "success": False,
                "error": str(e),
            }
            import traceback
            traceback.print_exc()
        
        # Save validation results
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        results_file = output_path / f"mock_train_{step}_results.json"
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== Validation Complete ===")
        print(f"Results saved to: {results_file}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"  Data Loading: {'✓' if validation_results['data_loading']['success'] else '✗'}")
        print(f"  Data Validation: {'✓' if validation_results['data_validation']['success'] else '✗'}")
        print(f"  Data Formatting: {'✓' if validation_results['data_formatting']['success'] else '✗'}")
        print(f"  Dataset Preparation: {'✓' if validation_results['dataset_preparation']['success'] else '✗'}")
        print(f"  Config Validation: {'✓' if validation_results['config_validation']['success'] else '✗'}")
        print(f"  Data Split: {'✓' if validation_results['data_split']['success'] else '✗'}")
        
        loss_eval = validation_results.get('loss_and_eval', {})
        if loss_eval.get('success'):
            acc = loss_eval.get('eval_accuracy')
            if acc is not None:
                print(f"  Loss Recording & Evaluation: ✓ (accuracy: {acc:.3f})")
            else:
                print(f"  Loss Recording & Evaluation: ✓ (loss only, no eval examples)")
        else:
            print(f"  Loss Recording & Evaluation: ✗")
        
        return validation_results
        
    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        validation_results["error"] = str(e)
        return validation_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mock training to test pipeline without loading models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single step
  python -m llm_model.finetune.scripts.mock_train_step \\
      --step character \\
      --data-dir training_data \\
      --output-dir ./mock_test_results

  # Test multiple steps
  python -m llm_model.finetune.scripts.mock_train_step \\
      --step character action relationship \\
      --data-dir training_data \\
      --output-dir ./mock_test_results

  # Test all steps
  python -m llm_model.finetune.scripts.mock_train_step \\
      --step all \\
      --data-dir training_data \\
      --output-dir ./mock_test_results
        """
    )
    
    parser.add_argument(
        "--step",
        type=str,
        nargs="+",  # Allow multiple steps
        default=None,
        choices=["character", "instrument", "relationship", "action", "stac", "event_type", "all"],
        help="Pipeline step(s) to test. Use 'all' to test all steps, or specify multiple steps: --step character action"
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
        help="Base model name (not actually used, for compatibility)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./mock_test_results",
        help="Output directory for validation results (default: ./mock_test_results)"
    )
    parser.add_argument(
        "--train-split",
        type=float,
        default=0.9,
        help="Train/test split ratio (default: 0.9)"
    )
    args = parser.parse_args()
    
    # Determine which steps to test
    all_steps = ["character", "instrument", "relationship", "action", "stac", "event_type"]
    
    if args.step is None:
        print("Error: --step is required. Use --step <step_name> or --step all")
        return 1
    
    if "all" in args.step:
        steps_to_test = all_steps
    else:
        steps_to_test = args.step
    
    # Remove duplicates while preserving order
    seen = set()
    steps_to_test = [s for s in steps_to_test if s not in seen and not seen.add(s)]
    
    print(f"Testing {len(steps_to_test)} step(s): {', '.join(steps_to_test)}\n")
    
    # Run mock training for each step
    all_results = {}
    failed_steps = []
    
    for step in steps_to_test:
        print(f"\n{'='*60}")
        print(f"Testing step: {step}")
        print(f"{'='*60}\n")
        
        try:
            # Create step-specific output directory
            step_output_dir = str(Path(args.output_dir) / step)
            
            results = mock_train_step(
                step=step,
                data_dir=args.data_dir,
                model_name=args.model_name,
                output_dir=step_output_dir,
                train_split=args.train_split,
            )
            
            all_results[step] = results
            
            # Check if step failed
            if not results.get("data_loading", {}).get("success"):
                failed_steps.append(f"{step}: data_loading failed")
            elif not results.get("data_formatting", {}).get("success"):
                failed_steps.append(f"{step}: data_formatting failed")
            elif not results.get("dataset_preparation", {}).get("success"):
                failed_steps.append(f"{step}: dataset_preparation failed")
            elif not results.get("loss_and_eval", {}).get("success"):
                failed_steps.append(f"{step}: loss_and_eval failed")
            
        except Exception as e:
            print(f"\n✗ Error testing step {step}: {e}")
            failed_steps.append(f"{step}: {str(e)}")
            all_results[step] = {"error": str(e)}
            import traceback
            traceback.print_exc()
    
    # Save aggregated results
    if len(steps_to_test) > 1:
        aggregated_file = Path(args.output_dir) / "all_steps_results.json"
        with open(aggregated_file, "w", encoding="utf-8") as f:
            json.dump({
                "steps_tested": steps_to_test,
                "total_steps": len(steps_to_test),
                "failed_steps": failed_steps,
                "results": all_results,
            }, f, indent=2, ensure_ascii=False)
        print(f"\n{'='*60}")
        print(f"Aggregated results saved to: {aggregated_file}")
        print(f"{'='*60}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}")
    for step in steps_to_test:
        results = all_results.get(step, {})
        if "error" in results:
            print(f"  {step}: ✗ Error - {results['error']}")
        else:
            data_loading = results.get("data_loading", {}).get("success", False)
            data_formatting = results.get("data_formatting", {}).get("success", False)
            dataset_prep = results.get("dataset_preparation", {}).get("success", False)
            loss_eval = results.get("loss_and_eval", {}).get("success", False)
            
            if all([data_loading, data_formatting, dataset_prep, loss_eval]):
                print(f"  {step}: ✓ All tests passed")
            else:
                print(f"  {step}: ✗ Some tests failed")
                if not data_loading:
                    print(f"      - Data loading failed")
                if not data_formatting:
                    print(f"      - Data formatting failed")
                if not dataset_prep:
                    print(f"      - Dataset preparation failed")
                if not loss_eval:
                    print(f"      - Loss/evaluation failed")
    
    # Return error code if any step failed
    if failed_steps:
        print(f"\n✗ {len(failed_steps)} step(s) failed: {', '.join(failed_steps)}")
        return 1
    
    print(f"\n✓ All {len(steps_to_test)} step(s) passed!")
    return 0


if __name__ == "__main__":
    exit(main())
