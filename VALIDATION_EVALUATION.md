# Validation Set Evaluation - Documentation

## Summary

This document describes the validation set evaluation setup for the full_detection pipeline.

## Validation Set

The validation set consists of **10 stories** (20% of 47 total stories):

1. CH_003_孟姜女哭长城 (140 training examples)
2. CH_007_嫦娥奔月 (16 examples)
3. CH_012_后羿射日 (10 examples)
4. CH_014_武松打虎 (2 examples)
5. CH_301_神犬盘瓠 (4 examples)
6. EN_006_The_Magic_Fiddle (16 examples)
7. EN_007_The_Cruel_Crane_Outwitted (18 examples)
8. EN_009_Harisarman (18 examples)
9. jp_006 (18 examples)
10. jp_013 (18 examples)

**Total validation examples**: 342

The stories were selected using an 80/20 split with random seed 42 (same as `split_by_story.py`).

## Setup

### 1. Added Unsloth Support to LLM Router

Modified the following files to support fine-tuned unsloth models:

- **New file**: [`llm_model/unsloth_client.py`](llm_model/unsloth_client.py)
  - Implements chat interface for unsloth models
  - Caches loaded models to avoid reloading
  - Uses FastLanguageModel.for_inference for efficient inference

- **Updated**: [`llm_model/llm_router.py`](llm_model/llm_router.py)
  - Added `"unsloth"` as a new LLM provider
  - Added `UnslothConfig` to `LLMConfig`
  - Routes to unsloth_client when provider is "unsloth"

### 2. Created Evaluation Script

**Script**: [`scripts/eval_validation_set.py`](scripts/eval_validation_set.py)

This script:
1. Identifies the 10 validation stories using the same split logic as training
2. Loads ground truth JSON v3 files for each story
3. Runs `full_detection` pipeline on each story's text spans
4. Evaluates predictions against ground truth
5. Reports aggregated metrics

## Usage

### Run with Fine-tuned Model (Unsloth)

```bash
conda run -n nlp python3 scripts/eval_validation_set.py \
    --provider unsloth \
    --model-path models/character \
    --base-model unsloth/Qwen3-4B-unsloth-bnb-4bit \
    --limit 10  # All validation stories
```

### Run with Base Model (Baseline)

```bash
conda run -n nlp python3 scripts/eval_validation_set.py \
    --provider ollama \
    --limit 10
```

### Test with One Story

```bash
conda run -n nlp python3 scripts/eval_validation_set.py \
    --provider unsloth \
    --model-path models/character \
    --limit 1
```

## Environment

**Important**: Always use the `conda nlp` environment for running evaluations.

```bash
conda activate nlp
# or
conda run -n nlp <command>
```

The nlp environment contains:
- unsloth
- transformers
- torch with CUDA support
- All other required dependencies

## Metrics

The evaluation computes the following metrics:

### Character Detection
- **Precision**: Of predicted characters, how many are correct
- **Recall**: Of ground truth characters, how many were detected
- **F1 Score**: Harmonic mean of precision and recall

### Event Detection
- **Count Accuracy**: Ratio of predicted event count to ground truth event count (capped at 1.0)

## Output

Results are saved to `evaluation_results/` directory:

- `validation_summary.json` - Aggregated metrics across all stories
- `{story_id}_prediction.json` - Full pipeline prediction for each story
- `{story_id}_evaluation.json` - Per-story evaluation metrics

### Example Summary Structure

```json
{
  "overall_metrics": {
    "character_precision": 1.0,
    "character_recall": 0.364,
    "character_f1": 0.533,
    "event_count_accuracy": 1.0
  },
  "per_story_results": [
    {
      "story_id": "CH_003_孟姜女哭长城",
      "character_metrics": {
        "precision": 1.0,
        "recall": 0.364,
        "f1": 0.533,
        "correct": 4,
        "predicted": 4,
        "ground_truth": 11
      },
      "event_metrics": {
        "accuracy": 1.0,
        "predicted": 20,
        "ground_truth": 20
      }
    }
  ],
  "config": {
    "provider": "unsloth",
    "model_path": "models/character",
    "base_model": "unsloth/Qwen3-4B-unsloth-bnb-4bit",
    "num_stories": 1
  }
}
```

## Initial Test Results

**Test run** (1 story: CH_003_孟姜女哭长城):

```
Character Detection:
  Average Precision: 1.000
  Average Recall:    0.364
  Average F1 Score:  0.533

Event Detection:
  Average Count Accuracy: 1.000
```

**Observations**:
- Model loaded successfully from `models/character`
- Pipeline ran end-to-end
- Some JSON parsing failures (model outputted Chinese summaries instead of JSON for some steps)
- Character detection had high precision but low recall (detected 4 out of 11 characters correctly)

## Next Steps

1. **Run on all 10 validation stories**:
   ```bash
   conda run -n nlp python3 scripts/eval_validation_set.py --provider unsloth --model-path models/character
   ```

2. **Compare with baseline** (base model without fine-tuning)

3. **Evaluate other pipeline steps** (relationship, action, etc.)

4. **Fine-tune other models** (relationship, action) and re-evaluate

## Troubleshooting

### Model Loading Issues

If you see "unsloth is not installed":
```bash
conda activate nlp
pip install unsloth
```

### CUDA Out of Memory

- Reduce `--limit` to process fewer stories at a time
- The unsloth client uses 4-bit quantization to reduce memory usage

### JSON Parsing Failures

This is expected if the model outputs non-JSON responses. The evaluation script handles this gracefully and continues processing.

## Files Modified/Created

### New Files
- `llm_model/unsloth_client.py` - Unsloth chat client
- `scripts/eval_validation_set.py` - Validation evaluation script
- `llm_model/evaluation/README_EVALUATION.md` - Evaluation guide
- `VALIDATION_EVALUATION.md` - This document

### Modified Files
- `llm_model/llm_router.py` - Added unsloth provider support
