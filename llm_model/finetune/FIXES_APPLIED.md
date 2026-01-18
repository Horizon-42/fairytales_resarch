# Fine-tuning Pipeline Fixes

## Summary

Fixed compatibility issues with newer versions of Unsloth and Transformers libraries.

## Fixes Applied

### 1. Parameter Rename: `evaluation_strategy` → `eval_strategy`

**Issue:** `TypeError: TrainingArguments.__init__() got an unexpected keyword argument 'evaluation_strategy'`

**Cause:** The parameter name was changed in newer versions of transformers.

**Fixed in:**
- [base_trainer.py:386](base_trainer.py#L386)
- [config.py:90](config.py#L90)

**Change:**
```python
# Old
training_args_dict["evaluation_strategy"] = "epoch"

# New
training_args_dict["eval_strategy"] = "epoch"
```

### 2. Added `formatting_func` for SFTTrainer

**Issue:** `RuntimeError: Unsloth: You must specify a formatting_func`

**Cause:** Newer versions of Unsloth require a `formatting_func` parameter instead of `dataset_text_field`.

**Fixed in:**
- [base_trainer.py:418-451](base_trainer.py#L418-L451)

**Change:**
```python
# Added formatting function
def formatting_func(examples):
    """Format examples for training."""
    texts = []
    for instruction, input_text, output in zip(
        examples.get("instruction", examples.get("formatted_text", [])),
        examples.get("input", [""] * len(examples.get("instruction", examples.get("formatted_text", [])))),
        examples.get("output", examples.get("formatted_text", []))
    ):
        if isinstance(instruction, str) and "instruction" in examples:
            if input_text:
                text = f"{instruction}\n\nInput:\n{input_text}\n\nOutput:\n{output}"
            else:
                text = f"{instruction}\n\nOutput:\n{output}"
        else:
            text = instruction
        texts.append(text)
    return texts

# Use formatting_func in SFTTrainer
trainer = SFTTrainer(
    model=self.model,
    tokenizer=self.tokenizer,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    formatting_func=formatting_func,  # Instead of dataset_text_field
    max_seq_length=self.config.max_seq_length,
    packing=False,
    args=training_args,
    callbacks=[loss_callback],
)
```

## Training Configuration

The pipeline uses **4-bit quantized fine-tuning** by default:

- **Model:** `unsloth/Qwen3-4B-unsloth-bnb-4bit`
- **Quantization:** 4-bit (bitsandbytes)
- **GPU Memory:** ~6.65 GB for model
- **LoRA Configuration:**
  - rank (r): 16
  - alpha: 32
  - dropout: 0.1
  - target modules: q_proj, k_proj, v_proj, o_proj

## Usage

Train a single step:
```bash
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir training_data \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4
```

Train all steps:
```bash
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step all \
    --data-dir training_data \
    --output-dir ./models
```

## Output

Models are saved in HuggingFace format at:
```
./models/{step_name}/
```

You can load and use the fine-tuned model directly:
```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./models/character",
    max_seq_length=2048,
    load_in_4bit=True,
)
```

## Notes

- No Ollama/GGUF export needed - use HuggingFace format directly
- All training data is prepared in `training_data/` directory
- Training uses 4-bit quantization for memory efficiency
- The pipeline is now compatible with:
  - Unsloth 2026.1.3
  - Transformers 4.57.2
  - Python 3.13
