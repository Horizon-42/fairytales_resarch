# Fine-tuning Module for Full Detection Pipeline

This module provides fine-tuning capabilities for each step of the `full_detection` pipeline using unsloth. It allows you to fine-tune models for:

1. **Character Recognition** - Identify characters and items (doers/receivers)
2. **Instrument Recognition** - Identify key instruments or tools (optional)
3. **Relationship Deduction** - Deduce relationships between characters
4. **Action Category Deduction** - Classify narrative actions
5. **STAC Analysis** - Analyze Situation, Task, Action, Consequence
6. **Event Type Classification** - Classify events using Propp functions

## Overview

This module is designed to:
- **Reuse code non-invasively**: Import and use prompts from `full_detection` without modifying it
- **Modular design**: Each pipeline step has an independent trainer
- **Use unsloth**: Efficient LoRA/QLoRA fine-tuning with unsloth library
- **Maintain consistency**: Training prompts match inference prompts exactly

## Installation

### Dependencies

Install required dependencies:

```bash
# Core dependencies
pip install unsloth[colab-new]
pip install trl transformers datasets accelerate

# Or install from requirements (if available)
pip install -r llm_model/finetune/requirements.txt
```

### Note on unsloth

Unsloth can be installed from:
- PyPI: `pip install unsloth` (if available)
- GitHub: `pip install "git+https://github.com/unslothai/unsloth.git"`

See unsloth documentation for more details.

## Quick Start

### 1. Prepare Training Data

Extract training examples from annotated JSON files:

```bash
python -m llm_model.finetune.scripts.prepare_data \
    --data-dir datasets/ChineseTales/json_v3 \
    --output-dir ./training_data \
    --steps character relationship action
```

This will generate JSONL files in `./training_data/`:
- `character_train.jsonl`
- `relationship_train.jsonl`
- `action_train.jsonl`
- etc.

### 2. Train a Single Step

Train a model for a specific pipeline step:

```bash
python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir datasets/ChineseTales/json_v3 \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```

### 3. Train All Steps

Train models for all pipeline steps:

```bash
python -m llm_model.finetune.scripts.train_all \
    --data-dir datasets/ChineseTales/json_v3 \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --steps character relationship action stac event_type
```

## Usage

### Python API

#### Prepare Training Data

```python
from llm_model.finetune.data_preparation import prepare_all_training_data

# Prepare training data for all steps
all_examples = prepare_all_training_data(
    data_dir="datasets/ChineseTales/json_v3",
    steps=["character", "relationship", "action"],
    output_dir="./training_data",  # Optional: save to files
)
```

#### Train a Single Step

```python
from llm_model.finetune.config import FineTuneConfig
from llm_model.finetune.trainers import CharacterTrainer
from llm_model.finetune.data_preparation import extract_character_examples, load_all_annotated_stories

# Load stories
stories = load_all_annotated_stories("datasets/ChineseTales/json_v3")

# Extract examples
all_examples = []
for story in stories:
    examples = extract_character_examples(story)
    all_examples.extend(examples)

# Configure
config = FineTuneConfig(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-4,
)

# Train
trainer = CharacterTrainer(
    model_name=config.model_name,
    step_name="character_recognition",
    config=config,
)
trainer.load_model()
trainer.train(all_examples)
```

#### Train All Steps

```python
from llm_model.finetune.scripts.train_all import train_all_steps
from llm_model.finetune.config import FineTuneConfig

config = FineTuneConfig(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    num_epochs=3,
    batch_size=4,
)

train_all_steps(
    data_dir="datasets/ChineseTales/json_v3",
    steps=["character", "relationship", "action"],
    config=config,
)
```

## Configuration

### FineTuneConfig

The `FineTuneConfig` class provides configuration options:

```python
from llm_model.finetune.config import FineTuneConfig

config = FineTuneConfig(
    # Model configuration
    model_name="unsloth/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    
    # LoRA configuration
    lora_r=16,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=None,  # Auto-detected based on model
    
    # Training configuration
    batch_size=4,
    gradient_accumulation_steps=4,
    num_epochs=3,
    learning_rate=2e-4,
    warmup_steps=50,
    
    # Data type
    bf16=True,  # Use bfloat16
    
    # Output
    output_dir="./models",
)
```

## Data Format

Training examples are dictionaries with:

```python
{
    "instruction": "System + user prompt string (from full_detection)",
    "input": "",  # Empty (instruction contains full input)
    "output": "JSON string of expected output"
}
```

Example for character recognition:

```python
{
    "instruction": "You are an expert folktale annotation assistant...\n\nIdentify all main characters...",
    "input": "",
    "output": '{"doers": ["牛郎"], "receivers": ["织女"], "new_characters": [], "notes": ""}'
}
```

## Architecture

### Module Structure

```
llm_model/finetune/
├── __init__.py
├── config.py                    # FineTuneConfig class
├── data_preparation.py          # Data extraction utilities
├── base_trainer.py              # BaseTrainer class
├── trainers/
│   ├── character_trainer.py     # Character Recognition trainer
│   ├── instrument_trainer.py    # Instrument Recognition trainer
│   ├── relationship_trainer.py  # Relationship Deduction trainer
│   ├── action_trainer.py        # Action Category trainer
│   ├── stac_trainer.py          # STAC Analysis trainer
│   └── event_type_trainer.py    # Event Type Classification trainer
├── utils/
│   └── prompt_builder.py        # Prompt building utilities (wraps full_detection)
└── scripts/
    ├── prepare_data.py          # Data preparation script
    ├── train_step.py            # Single step training script
    └── train_all.py             # All steps training script
```

### Code Reuse Strategy

The module reuses code from `full_detection` **non-invasively**:

1. **Import prompts**: Direct imports from `llm_model.full_detection.prompts`
2. **Wrap prompts**: `utils/prompt_builder.py` wraps prompt functions for training
3. **No modifications**: No changes to `full_detection` code

Example:

```python
# In utils/prompt_builder.py
from ...full_detection.prompts import (
    SYSTEM_PROMPT_CHARACTER_RECOGNITION,
    build_character_recognition_prompt,
)

def build_character_prompt_for_training(...):
    system_prompt = SYSTEM_PROMPT_CHARACTER_RECOGNITION
    user_prompt = build_character_recognition_prompt(...)
    return f"{system_prompt}\n\n{user_prompt}"
```

## Notes

1. **Prompt Consistency**: Training prompts match inference prompts exactly
2. **Model Compatibility**: Supports Qwen, Llama, and generic chat models
3. **Chat Format**: Automatically detects and uses appropriate chat format
4. **Summary Handling**: Summary can be empty during training (optional field)
5. **Memory Efficiency**: Uses 4-bit quantization and LoRA for efficient training

## Troubleshooting

### Import Errors

If you get import errors for `unsloth`, install it:

```bash
pip install "git+https://github.com/unslothai/unsloth.git"
```

### Out of Memory

Reduce batch size or use gradient accumulation:

```python
config = FineTuneConfig(
    batch_size=2,
    gradient_accumulation_steps=8,
)
```

### Model Loading Issues

Ensure model name is correct for unsloth:

```python
# Supported formats:
"unsloth/Qwen2.5-7B-Instruct"
"unsloth/Llama-3.1-8B-Instruct"
# etc.
```

## Development

See `DEVELOPMENT_PLAN.md` for detailed architecture and design decisions.

## License

Same as parent project.
