# Full Pipeline of Narrative Detection

A comprehensive LangChain-based pipeline for extracting structured narrative events from story segments.

## Overview

This package implements a multi-step analysis pipeline that processes story segments and generates structured narrative events following the v3 JSON schema. Each step builds upon previous steps, allowing the pipeline to leverage accumulated context throughout the analysis.

## Installation

The package uses existing dependencies from the parent `llm_model` module:
- `langchain` and `langchain-core` (for chain composition)
- `llm_model.llm_router` (for LLM provider abstraction)
- `llm_model.json_utils` (for JSON parsing)

## Pipeline Steps

### Input
- **Whole story text**: Full narrative context
- **Text span**: Specific segment to analyze (with start/end indices and text)
- **Characters list**: Existing global character list (may be empty initially)

### Step 0: Summary (Pre-processing)
Generate a summary of the story (or story segment) once before processing narrative events. This summary is shared across all text spans in the story. The summary preserves key characters and main plot points in 4-7 sentences.

**Note**: Summary generation is now done separately (via `generate_story_summary()` or `process_story()`) and passed as input to the pipeline. The pipeline no longer generates summaries internally.

### Step 1: Character Recognition (Entity Name Recognition)
Recognize all main characters and items in the segment, label them as **doers** (agents) and **receivers** (targets). Add new characters to the global character list, handling alias resolution (e.g., if "孩子" is already in list as "一儿一女"). Uses the summary from Step 0 as context.

### Step 2: Instrument Recognition (Optional)
Recognize key instruments/tools that the doer(s) used in this event/action. Only significant instruments are identified (common tools are ignored).

### Step 3: Relationship Deduction
If receivers are characters (not items), deduce relationships between doers and receivers. Multiple relationships are possible (e.g., multiple doer-receiver pairs).

### Step 4: Action Category Deduction
Classify the action category using the Universal Narrative Action Taxonomy, including:
- **Category**: physical, communicative, transaction, cognitive, existential
- **Type**: specific action (e.g., attack, inform, give)
- **Context**: context tags (e.g., ambush, quest)
- **Status**: outcome (attempt, success, failure, etc.)
- **Function**: narrative role (trigger, climax, resolution)

### Step 5: STAC Analysis
Recognize the **Situation, Task, Action, and Consequence** of this segment, each summarized in one short sentence. Uses the summary from Step 0 as context.

### Step 6: Event Type Classification
Classify the event using Vladimir Propp's Morphology of the Folktale (Propp functions like A, a, B, C, etc., or "OTHER"). Uses both the summary and STAC analysis from previous steps.

### Output
Structure the result as a complete `narrative_event` JSON object compatible with v3 schema.

## Usage

### Python API

#### Story-Level Processing (Recommended)

Process an entire story with summary generated once and shared across all segments:

```python
from llm_model.full_detection import process_story
from llm_model.llm_router import LLMConfig

# Process entire story with multiple text spans
result = process_story(
    story_text="...",
    text_spans=[
        {"start": 0, "end": 200, "text": "..."},
        {"start": 200, "end": 400, "text": "..."},
    ],
    characters=[],  # May be empty initially
    llm_config=LLMConfig(provider="ollama"),
    include_instrument=False,  # Optional
)

# Summary is generated once and shared across all spans
summary = result["summary"]
narrative_events = result["narrative_events"]
updated_characters = result["updated_characters"]
```

#### Single Segment Processing

Process a single text span (summary can be provided or generated):

```python
from llm_model.full_detection import run_pipeline, process_story_segment
from llm_model.llm_router import LLMConfig

# Option 1: With pre-generated summary
result = run_pipeline(
    story_text="...",
    text_span={"start": 0, "end": 200, "text": "..."},
    characters=[],
    time_order=1,
    summary="Pre-generated summary...",  # Use provided summary
    llm_config=LLMConfig(provider="ollama"),
)

# Option 2: Generate summary for single segment
result = process_story_segment(
    story_text="...",
    text_span={"start": 0, "end": 200, "text": "..."},
    characters=[],
    time_order=1,
    llm_config=LLMConfig(provider="ollama"),
)
```

#### Generate Summary Separately

Generate a summary independently:

```python
from llm_model.full_detection import generate_story_summary

# Generate summary for entire story
summary = generate_story_summary(
    story_text="...",
    llm_config=LLMConfig(provider="ollama"),
)

# Generate summary for specific segment
summary = generate_story_summary(
    story_text="...",
    text_span={"start": 0, "end": 200, "text": "..."},
    llm_config=LLMConfig(provider="ollama"),
)
```

### Command Line Interface

```bash
# Single text span
python -m llm_model.full_detection.cli \
    --story-file story.txt \
    --start 0 \
    --end 200 \
    --time-order 1 \
    --output result.json

# Batch processing with multiple spans
python -m llm_model.full_detection.cli \
    --story-file story.txt \
    --spans-json spans.json \
    --characters-json characters.json \
    --include-instrument \
    --output result.json
```

## Architecture

The pipeline is implemented using **LangChain** chains, where:
- Each step is a `Runnable` that processes pipeline state
- State accumulates through sequential steps
- Each step can access outputs from all previous steps
- Error handling and validation at each stage
- **Summary is generated once** (outside the pipeline) and passed as input to all segments

### Story Processing Flow

```
Story → Generate Summary (once) → Process Each Segment → Narrative Events
```

The `story_processor` module provides high-level functions to:
1. Generate story summary once
2. Process all segments with the shared summary
3. Update character list incrementally across segments

See `DEVELOPMENT.md` for detailed architecture and implementation notes.

## Output Schema

The pipeline produces a `narrative_event` JSON object:

```json
{
  "id": "uuid",
  "text_span": {"start": 0, "end": 200, "text": "..."},
  "event_type": "VILLAINY",
  "description": "general;specific",
  "agents": ["doer1", "doer2"],
  "targets": ["receiver1"],
  "target_type": "character",
  "object_type": "",
  "instrument": "sword",
  "time_order": 1,
  "relationships": [
    {
      "agent": "doer1",
      "target": "receiver1",
      "relationship_level1": "Adversarial",
      "relationship_level2": "enemy",
      "sentiment": "hostile"
    }
  ],
  "action_layer": {
    "category": "physical",
    "type": "attack",
    "context": "ambush",
    "status": "success",
    "function": "trigger"
  }
}
```

## Testing

Unit tests are available in `tests/` directory. **Always run tests in conda nlp environment**:

```bash
conda activate nlp
pytest llm_model/full_detection/tests/

# Or using conda run
conda run -n nlp python -m pytest llm_model/full_detection/tests/
```

See `tests/README.md` for detailed testing instructions.

Tests use mocks for LLM calls to ensure fast, deterministic execution without requiring actual LLM services.