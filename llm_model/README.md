LLM model finetune and inference

This folder contains **only model-related logic** used for automatic annotation:

- Ollama HTTP client (`ollama_client.py`)
- Gemini HTTP client (`gemini_client.py`)
- Unified router (`llm_router.py`)
- Prompt templates (`prompts.py`)
- JSON extraction utilities (`json_utils.py`)
- High-level annotator (`annotator.py`)
- STAC (Situation, Task, Action, Consequence) analyzer (`stac_analyzer/`)
- Sentence-level event analysis (`sentence_analysis/`)

The FastAPI server that the frontend calls lives in `backend/`.

## Installation

Install core dependencies:

```bash
pip install -r llm_model/requirements.txt
```

Or install the package in editable mode (recommended):

```bash
pip install -e .
```

This makes `llm_model` importable from anywhere in the project.

## Quick CLI test

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.auto_annotate_cli --model llama3.1 --text-file datasets/ChineseTales/texts/孟姜女哭长城.md
```

Gemini (requires repo-root `.env`):

```bash
LLM_PROVIDER=gemini \
python -m llm_model.auto_annotate_cli --provider gemini --model "$GEMINI_MODEL" --thinking \
	--text-file datasets/ChineseTales/texts/孟姜女哭长城.md
```

## Character-only CLI

This produces fields that map to the frontend Characters tab.

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.auto_characters_cli --model qwen3:8b --text-file datasets/ChineseTales/texts/孟姜女哭长城.md
```

## Sentence-level Event Analysis CLI

Analyze sentences to determine:
- Whether it contains an event or is just description (location, background, scene)
- If it's an event: extract doer, receiver, sentiment, and emotion
- Extract location information from the sentence

### Modes:

1. **With Context Mode** (default): Analyze sentences within the context of a complete story
2. **No Context Mode**: Analyze sentences directly without story context

### Analyze a single sentence (with context):

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.sentence_analysis.cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --sentence "The hero defeated the dragon."
```

### Analyze a single sentence (no context):

```bash
python -m llm_model.sentence_analysis.cli \
  --no-context \
  --sentence "The hero defeated the dragon."
```

(Default model is `qwen3:8b`. Use `--model` to specify a different model.)

### Auto-split and analyze all sentences:

The tool can automatically split the text file into sentences and analyze each one, outputting results as JSON with sentence indices:

```bash
# With context (default) - uses story context for each sentence analysis
python -m llm_model.sentence_analysis.cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json

# Without context - analyzes each sentence independently, no story context
python -m llm_model.sentence_analysis.cli \
  --no-context \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json
```

Note: In `--no-context` mode, the `--story-file` is still used for batch processing (sentence splitting), but the file content is NOT used as context when analyzing each sentence. Each sentence is analyzed independently.

The output JSON will have this structure:
```json
{
  "story_file": "path/to/story.txt",
  "use_context": true,
  "total_sentences": 10,
  "analyzed_sentences": 10,
  "sentences": [
    {
      "sentence_index": 1,
      "sentence": "First sentence...",
      "analysis": {
        "is_event": true,
        "content_type": "event",
        "location": "forest",
        "doer": "hero",
        "receiver": "dragon",
        "sentiment": "hostile",
        "emotion": "anger",
        "explanation": "..."
      }
    },
    ...
  ]
}
```

With Gemini:

```bash
# With context
LLM_PROVIDER=gemini \
python -m llm_model.sentence_analysis.cli \
  --provider gemini \
  --model "$GEMINI_MODEL" \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json

# Without context
LLM_PROVIDER=gemini \
python -m llm_model.sentence_analysis.cli \
  --provider gemini \
  --model "$GEMINI_MODEL" \
  --no-context \
  --sentence "The hero defeated the dragon."
```

## STAC (Situation, Task, Action, Consequence) Analysis CLI

Analyze sentences using STAC classification:
- **Situation**: Provides background context or sets the stage (extracts location)
- **Task**: States an explicit requirement (extracts task roles)
- **Action**: Indicates an activity performed (extracts doers and receivers)
- **Consequence**: Describes the outcome of a prior event (extracts changed state)

### Analyze a single sentence (with context):

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.auto_stac_cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --sentence "王子来到了森林"
```

### Analyze a single sentence (no context):

```bash
python -m llm_model.auto_stac_cli \
  --no-context \
  --sentence "王子来到了森林"
```

### Auto-split and analyze all sentences:

```bash
# With context (default) - uses story context for each sentence analysis
python -m llm_model.auto_stac_cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json

# Without context - analyzes each sentence independently
python -m llm_model.auto_stac_cli \
  --no-context \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json

# With neighboring sentences as auxiliary context
python -m llm_model.auto_stac_cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --use-neighboring-sentences \
  --output result.json
```

The output JSON structure:
```json
{
  "story_file": "path/to/story.txt",
  "use_context": true,
  "use_neighboring_sentences": false,
  "total_sentences": 10,
  "analyzed_sentences": 10,
  "sentences": [
    {
      "sentence_index": 1,
      "sentence": "第一句话...",
      "analysis": {
        "stac_category": "situation",
        "location": "森林",
        "task_roles": [],
        "doers": [],
        "receivers": [],
        "changed_state": "",
        "explanation": "..."
      }
    },
    ...
  ]
}
```

With Gemini:

```bash
# With context
LLM_PROVIDER=gemini \
python -m llm_model.auto_stac_cli \
  --provider gemini \
  --model "$GEMINI_MODEL" \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json
```