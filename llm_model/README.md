LLM model finetune and inference

This folder contains **only model-related logic** used for automatic annotation:

- Ollama HTTP client (`ollama_client.py`)
- Prompt templates (`prompts.py`)
- JSON extraction utilities (`json_utils.py`)
- High-level annotator (`annotator.py`)

The FastAPI server that the frontend calls lives in `backend/`.

## Quick CLI test

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.auto_annotate_cli --model llama3.1 --text-file datasets/ChineseTales/texts/孟姜女哭长城.md
```

## Character-only CLI

This produces fields that map to the frontend Characters tab.

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.auto_characters_cli --model qwen3:8b --text-file datasets/ChineseTales/texts/孟姜女哭长城.md
```