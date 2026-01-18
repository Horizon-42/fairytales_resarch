# Fine-tuning Module

This module provides fine-tuning capabilities for each step of the `full_detection` pipeline using `unsloth`.

## Installation

Install fine-tuning dependencies:

```bash
pip install -r llm_model/finetune/requirements.txt
```

Or install specific packages:

```bash
pip install transformers trl peft datasets accelerate unsloth[colab-new]
```

**Note**: The `datasets` package is required for dataset preparation. If you're only running mock tests, it can be skipped, but actual training requires all dependencies.

## Features

- **Modular Design**: Each pipeline step can be fine-tuned independently
- **Loss Tracking**: Automatic loss history recording during training
- **Evaluation**: Built-in evaluation after training (single-step and full pipeline)
- **Mock Testing**: Test training pipeline without loading models

## Quick Start

### 1. Extract Training Data

```bash
# From regular annotated data
python -m llm_model.finetune.scripts.extract_training_data \
    --input-dir datasets/ChineseTales/json_v3 \
    --output-dir training_data

# From synthetic data
python -m llm_model.finetune.scripts.extract_training_data \
    --synthetic \
    --groundtruth-dir synthetic_datasets/groundtruth \
    --generated-stories-dir synthetic_datasets/generated_stories \
    --output-dir training_data
```

### 2. Test Training Pipeline (Mock)

Before actual training, test the pipeline without loading models:

```bash
python -m llm_model.finetune.scripts.mock_train_step \
    --step character \
    --data-dir training_data \
    --output-dir ./mock_test_results
```

This will:
- Load and validate data
- Extract training examples
- Test data formatting
- Mock model loading/training (no actual model calls)

### 3. Train a Step

```bash
python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir training_data \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```

### 4. Evaluate Full Pipeline

```bash
python -m llm_model.finetune.scripts.evaluate_model \
    --test-dir datasets/ChineseTales/json_v3 \
    --groundtruth-dir datasets/ChineseTales/json_v3 \
    --models-dir ./models \
    --output-dir ./evaluation_results
```

## Pipeline Steps

Available steps for fine-tuning:
- `character`: Character Recognition
- `instrument`: Instrument Recognition
- `relationship`: Relationship Deduction
- `action`: Action Category Deduction
- `stac`: STAC Analysis
- `event_type`: Event Type Classification

## Output Files

### Training Output

```
models/
├── {step_name}/
│   ├── loss_history.csv            # Loss history during training (CSV format)
│   ├── step_evaluation.json       # Single-step evaluation results
│   └── ... (model files)
```

### Mock Test Output

```
mock_test_results/
└── mock_train_{step}_results.json  # Validation results
```

### Evaluation Output

```
evaluation_results/
├── evaluation_results.json        # Full evaluation results
└── evaluation_report.md            # Markdown report
```

## Configuration

Fine-tuning parameters can be configured via `FineTuneConfig`:

```python
from llm_model.finetune import FineTuneConfig

config = FineTuneConfig(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    lora_r=16,
    lora_alpha=32,
    batch_size=4,
    num_epochs=3,
    learning_rate=2e-4,
)
```

## Mock Testing

The `mock_train_step` script is useful for:
- Testing data loading and extraction
- Validating data format
- Debugging without GPU/model requirements
- CI/CD pipeline testing

```bash
# Test data validation only (faster)
python -m llm_model.finetune.scripts.mock_train_step \
    --step character \
    --data-dir training_data \
    --validate-data-only

# Test full pipeline with mocked model
python -m llm_model.finetune.scripts.mock_train_step \
    --step character \
    --data-dir training_data
```

## Documentation

- [Training Guide](TRAINING_GUIDE.md): Detailed guide on loss tracking and evaluation
- [Development Plan](DEVELOPMENT_PLAN.md): Architecture and design decisions
