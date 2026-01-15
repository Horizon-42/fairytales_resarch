LLM model finetune and inference

This folder contains **only model-related logic** used for automatic annotation:

- Ollama HTTP client (`ollama_client.py`)
- Gemini HTTP client (`gemini_client.py`)
- Unified router (`llm_router.py`)
- Prompt templates (`prompts.py`)
- JSON extraction utilities (`json_utils.py`)
- High-level annotator (`annotator.py`)

The FastAPI server that the frontend calls lives in `backend/`.

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

Analyze sentences within the context of a complete story to determine:
- Whether it contains an event or is just description (location, background, scene)
- If it's an event: extract doer, receiver, sentiment, and emotion
- Assess the event's importance and classify its narrative function (if important)

### Analyze a single sentence:

```bash
cd /home/supercomputing/studys/fairytales_resarch
python -m llm_model.auto_sentence_analysis_cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --sentence "The hero defeated the dragon." \
  --model llama3.1
```

### Auto-split and analyze all sentences:

The tool can automatically split the story into sentences and analyze each one, outputting results as JSON with sentence indices:

```bash
python -m llm_model.auto_sentence_analysis_cli \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json \
  --model llama3.1
```

The output JSON will have this structure:
```json
{
  "story_file": "path/to/story.txt",
  "total_sentences": 10,
  "analyzed_sentences": 10,
  "sentences": [
    {
      "sentence_index": 1,
      "sentence": "First sentence...",
      "analysis": {
        "is_event": true,
        "content_type": "event",
        "doer": "...",
        "receiver": "...",
        "sentiment": "...",
        "emotion": "...",
        "importance_score": 7,
        "narrative_function": "trigger",
        "explanation": "..."
      }
    },
    ...
  ]
}
```

With Gemini:

```bash
LLM_PROVIDER=gemini \
python -m llm_model.auto_sentence_analysis_cli \
  --provider gemini \
  --model "$GEMINI_MODEL" \
  --story-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --output result.json
```