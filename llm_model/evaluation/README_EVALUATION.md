# Validation Set Evaluation Guide

## Overview

This document describes how to evaluate the full_detection pipeline on the validation set of 10 stories.

## Validation Set Stories

Based on the 80/20 split (using random seed 42), the validation set contains **10 stories**:

1. **CH_003_孟姜女哭长城** (140 examples)
2. **CH_007_嫦娥奔月** (16 examples)
3. **CH_012_后羿射日** (10 examples)
4. **CH_014_武松打虎** (2 examples)
5. **CH_301_神犬盘瓠** (4 examples)
6. **EN_006_The_Magic_Fiddle** (16 examples)
7. **EN_007_The_Cruel_Crane_Outwitted** (18 examples)
8. **EN_009_Harisarman** (18 examples)
9. **jp_006** (18 examples)
10. **jp_013** (18 examples)

**Total validation examples**: 342 (across all 10 stories)

## Evaluation Scripts

Three evaluation scripts have been created:

### 1. `run_baseline_eval.py` - Baseline Evaluation (Base Model)

Evaluates the **base model without fine-tuning** on validation stories.

**Usage:**
```bash
python3 llm_model/evaluation/run_baseline_eval.py \
    --data-dir training_data \
    --json-v3-dir datasets/ChineseTales/json_v3 \
    --base-model unsloth/Qwen3-4B-unsloth-bnb-4bit \
    --output-dir evaluation_results/baseline \
    --limit 10  # Evaluate all 10 validation stories
```

**Requirements:**
- unsloth library
- PyTorch with CUDA support
- transformers library

### 2. `run_finetuned_eval.py` - Fine-tuned Model Evaluation

Evaluates the **fine-tuned models** on validation stories.

**Usage:**
```bash
python3 llm_model/evaluation/run_finetuned_eval.py \
    --data-dir training_data \
    --json-v3-dir datasets/ChineseTales/json_v3 \
    --models-dir models \
    --base-model unsloth/Qwen3-4B-unsloth-bnb-4bit \
    --output-dir evaluation_results/finetuned \
    --step character \
    --limit 10
```

**Requirements:**
- Same as baseline evaluation
- Trained model in `models/character/` directory

### 3. `run_full_detection_eval.py` - Full Pipeline Evaluation

Evaluates the **complete full_detection pipeline** (all steps) using fine-tuned models.

**Note:** This script requires the evaluation package dependencies (sklearn) which are currently not installed.

## Installation Requirements

To run the evaluation scripts, you need to install:

```bash
# Core dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers
pip install unsloth

# For full evaluation (optional)
pip install scikit-learn
```

## Evaluation Metrics

The evaluation scripts calculate:

### Character Detection Metrics:
- **Precision**: Of the characters predicted, how many were correct?
- **Recall**: Of the ground truth characters, how many were detected?
- **F1 Score**: Harmonic mean of precision and recall

### Example Output:
```
Average Metrics:
  Precision: 0.850
  Recall: 0.720
  F1 Score: 0.780
```

## Output Files

Results are saved to the specified `--output-dir`:

- `baseline_evaluation_summary.json` - Aggregated baseline results
- `{step}_evaluation_summary.json` - Aggregated fine-tuned results
- `{story_id}_prediction.json` - Individual story predictions
- `{story_id}_evaluation.json` - Individual story evaluation results

## Example Result Structure

```json
{
  "average_metrics": {
    "precision": 0.850,
    "recall": 0.720,
    "f1": 0.780
  },
  "individual_results": [
    {
      "story_id": "CH_003_孟姜女哭长城",
      "precision": 0.900,
      "recall": 0.750,
      "f1": 0.818,
      "true_positives": 9,
      "false_positives": 1,
      "false_negatives": 3,
      "predicted_count": 10,
      "ground_truth_count": 12,
      "correct_characters": ["孟姜女", "范喜良", ...],
      "missing_characters": ["秦始皇", ...],
      "extra_characters": ["..."
      ]
    },
    ...
  ],
  "config": {
    "model": "baseline",
    "base_model": "unsloth/Qwen3-4B-unsloth-bnb-4bit",
    "num_stories": 10
  }
}
```

## Next Steps

1. **Install dependencies** (see Installation Requirements above)
2. **Run baseline evaluation** to get baseline metrics
3. **Train fine-tuned models** if not already done:
   ```bash
   python -m llm_model.finetune.scripts.train_step \
       --step character \
       --data-dir training_data \
       --output-dir models
   ```
4. **Run fine-tuned evaluation** to compare with baseline
5. **Analyze results** to measure improvement from fine-tuning

## Troubleshooting

### ModuleNotFoundError: No module named 'unsloth'
Install unsloth: `pip install unsloth`

### ModuleNotFoundError: No module named 'sklearn'
Install scikit-learn: `pip install scikit-learn`

### CUDA out of memory
- Reduce the number of stories with `--limit` parameter
- Enable CPU offload (slower but uses less GPU memory)
- Use a smaller base model

### Ground truth file not found
Make sure the JSON v3 files exist in `datasets/ChineseTales/json_v3/`
