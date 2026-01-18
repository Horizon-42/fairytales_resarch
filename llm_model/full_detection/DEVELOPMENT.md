# Full Detection Pipeline - Development Document

## Overview

This package implements a comprehensive narrative detection pipeline that processes story segments and generates structured narrative events. The pipeline uses **LangChain** to orchestrate multiple LLM analysis steps, where each step can utilize information from previous steps.

## Architecture

### Pipeline Flow

```
Input → Summary → Character Recognition → Instrument Recognition (optional) 
     → Relationship Deduction → Action Category Deduction → STAC Analysis → Output
```

### Step-by-Step Description

#### Input
- **Whole story text**: Full narrative context
- **Text span**: Specific segment to analyze (with start/end indices and text)
- **Characters list**: Existing global character list (may be empty initially)

#### Step 1: Summary
**Goal**: Generate a concise 4-7 sentence summary of the story segment, preserving key characters and main plot points.

**Input**: 
- Story segment text (from text_span)
- Optional: Full story context

**Output**:
- Summary text (4-7 sentences)

**LangChain Implementation**: LLM chain with summarization prompt

---

#### Step 2: Character Recognition (Entity Name Recognition)
**Goal**: Identify all main characters and items in the segment, label them as doers and receivers, and update the global character list.

**Input**:
- Story segment text
- Summary from Step 1
- Existing global characters list
- Full story context

**Output**:
- `doers`: List of character/item names who perform actions
- `receivers`: List of character/item names who receive actions
- `updated_characters`: Global character list with new characters added (handling alias resolution)

**Key Logic**:
- Match characters to existing list (by name or alias)
- Add new characters to global list
- Resolve aliases (e.g., if "孩子" is already in list as "一儿一女", don't add duplicate)
- Classify items vs characters (to determine if receivers are characters or objects)

**LangChain Implementation**: LLM chain with extraction prompt, structured output parser

---

#### Step 2.5: Instrument Recognition (Optional)
**Goal**: Identify key instruments/tools that the doer(s) used in this event/action.

**Input**:
- Story segment text
- Summary from Step 1
- Doers from Step 2

**Output**:
- `instrument`: String describing the instrument used (empty if none or too common)

**LangChain Implementation**: LLM chain with extraction prompt (only runs if flag is set)

---

#### Step 3: Relationship Deduction
**Goal**: If receivers are characters (not items), deduce their relationships with doers.

**Input**:
- Story segment text
- Summary from Step 1
- Doers from Step 2
- Receivers from Step 2 (filtered to characters only)
- Full story context (for relationship history)

**Output**:
- `relationships`: List of relationship objects:
  ```python
  {
    "agent": str,           # Doer name
    "target": str,          # Receiver name (character)
    "relationship_level1": str,  # e.g., "Family & Kinship", "Romance"
    "relationship_level2": str,  # e.g., "parent_child", "lover"
    "sentiment": str        # e.g., "positive", "hostile", "romantic"
  }
  ```

**Note**: Multiple relationships possible (e.g., if multiple doers/receivers)

**LangChain Implementation**: LLM chain with structured output parser, using relationship taxonomy from `docs/Character_Resources/`

---

#### Step 4: Action Category Deduction
**Goal**: Classify the action category, including status and function.

**Input**:
- Story segment text
- Summary from Step 1
- Doers and receivers from Step 2
- Instrument from Step 2.5 (if available)

**Output**:
- `action_layer`: Dictionary:
  ```python
  {
    "category": str,    # e.g., "physical", "communicative"
    "type": str,        # e.g., "attack", "inform"
    "context": str,     # e.g., "ambush", "report"
    "status": str,      # e.g., "success", "failure", "attempt"
    "function": str     # e.g., "trigger", "climax", "resolution"
  }
  ```

**LangChain Implementation**: LLM chain with structured output parser, using taxonomy from `docs/Universal Narrative Action Taxonomy/`

---

#### Step 5: STAC Analysis
**Goal**: Recognize the Situation, Task, Action, and Consequence of this segment, summarized in one short sentence each.

**Input**:
- Story segment text
- Summary from Step 1
- Full story context

**Output**:
- `stac`: Dictionary:
  ```python
  {
    "situation": str,      # Background/context
    "task": str,           # Requirement/responsibility
    "action": str,         # Activity performed
    "consequence": str     # Outcome/state change
  }
  ```

**LangChain Implementation**: Reuse existing `stac_analyzer` module, or create LangChain chain wrapper

---

#### Step 6: Event Type Classification (Propp Functions)
**Goal**: Classify the event using Vladimir Propp's Morphology of the Folktale.

**Input**:
- Story segment text
- Summary from Step 1
- STAC analysis from Step 5

**Output**:
- `event_type`: String (Propp function code, e.g., "VILLAINY", "a", "B", or "OTHER")

**LangChain Implementation**: LLM chain with classification prompt, using guide from `docs/Propp_Resources/propp_functions_guide_en.md`

---

#### Output: Structured Narrative Event
Combine all outputs into a v3 narrative_event JSON structure:

```python
{
  "id": str,                      # UUID generated or provided
  "text_span": {
    "start": int,
    "end": int,
    "text": str
  },
  "event_type": str,              # From Step 6
  "description": str,             # General + specific (from Step 1 summary or derived)
  "agents": List[str],            # From Step 2 (doers)
  "targets": List[str],           # From Step 2 (receivers)
  "target_type": str,             # "character" or "object" (from Step 2)
  "object_type": str,             # "normal_object", "magical_agent", or "price" (if target_type is object)
  "instrument": str,              # From Step 2.5 (or empty)
  "time_order": int,              # Provided in input
  "relationships": List[Dict],    # From Step 3 (empty if target_type is "object")
  "action_layer": {               # From Step 4
    "category": str,
    "type": str,
    "context": str,
    "status": str,
    "function": str
  }
}
```

---

## LangChain Design Pattern

### Sequential Pipeline with State Passing

We'll use LangChain's `SequentialChain` or a custom chain composition where:
1. Each step is a `Runnable` that takes previous state
2. State accumulates through the pipeline
3. Each step can access:
   - Original inputs (story, text_span, initial characters)
   - Outputs from all previous steps

### State Object Structure

```python
@dataclass
class PipelineState:
    # Inputs
    story_text: str
    text_span: Dict[str, Any]  # {start, end, text}
    characters: List[Dict[str, Any]]
    time_order: int
    event_id: str
    
    # Intermediate outputs
    summary: Optional[str] = None
    doers: List[str] = None
    receivers: List[str] = None
    updated_characters: List[Dict[str, Any]] = None
    instrument: str = ""
    relationships: List[Dict[str, Any]] = None
    action_layer: Dict[str, str] = None
    stac: Dict[str, str] = None
    event_type: str = "OTHER"
    
    # Final output
    narrative_event: Optional[Dict[str, Any]] = None
```

### Chain Composition

```python
pipeline = (
    RunnablePassthrough.assign(summary=summary_chain)
    .assign(
        doers=character_recognition_chain,
        receivers=character_recognition_chain,
        updated_characters=character_recognition_chain
    )
    .assign(instrument=instrument_chain)  # Optional
    .assign(relationships=relationship_chain)
    .assign(action_layer=action_category_chain)
    .assign(stac=stac_chain)
    .assign(event_type=event_type_chain)
    .assign(narrative_event=finalize_chain)
)
```

---

## Integration with Existing Codebase

### Reuse Existing Modules
- **STAC Analyzer**: `llm_model.stac_analyzer` - wrap in LangChain Runnable
- **LLM Router**: `llm_model.llm_router` - create LangChain LCEL adapters
- **Prompts**: Reference `llm_model.narrative_prompts` for prompt templates
- **JSON Utils**: `llm_model.json_utils` for parsing/validation

### LangChain LLM Integration
- Use LangChain's `ChatOllama`, `ChatGemini`, etc. if available
- Or create custom LangChain `Runnable` wrapper around existing `llm_router.chat()`
- Prefer LangChain's structured output parsers for JSON extraction

---

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create `pipeline_state.py` - State dataclass
2. Create `chains.py` - Individual LangChain chains for each step
3. Create `prompts.py` - Prompt templates for each step
4. Create `main.py` - Pipeline orchestration

### Phase 2: Individual Chain Implementation
1. Summary chain
2. Character recognition chain (with alias resolution logic)
3. Instrument recognition chain (optional)
4. Relationship deduction chain
5. Action category chain
6. STAC analysis chain (wrapper or integration)
7. Event type classification chain

### Phase 3: Integration & Finalization
1. Finalize chain - combine all outputs into narrative_event JSON
2. Error handling and validation
3. CLI interface (similar to `auto_stac_cli.py`)
4. Unit tests

### Phase 4: Documentation & Examples
1. API documentation
2. Usage examples
3. Integration guide

---

## File Structure

```
llm_model/full_detection/
├── __init__.py
├── README.md
├── DEVELOPMENT.md (this file)
├── pipeline_state.py      # State dataclass
├── prompts.py             # Prompt templates
├── chains.py              # Individual LangChain chains
├── pipeline.py            # Main pipeline orchestration
├── cli.py                 # CLI interface
└── utils.py               # Helper functions (alias resolution, etc.)
```

---

## Dependencies

- `langchain` (already in requirements.txt)
- `langchain-core` (already in requirements.txt)
- `langchain-ollama` (already in requirements.txt)
- Existing: `llm_model.llm_router`, `llm_model.json_utils`, `llm_model.stac_analyzer`

---

## Key Design Decisions

1. **State-based pipeline**: Each step receives and modifies a shared state object, allowing easy access to previous outputs.

2. **LangChain over custom**: Use LangChain for chain composition and structured outputs, but integrate with existing LLM router for provider abstraction.

3. **Reuse existing code**: Don't rewrite STAC analyzer or LLM router; wrap them in LangChain interfaces.

4. **Flexible character handling**: Character recognition must handle alias resolution and global list updates intelligently.

5. **Optional steps**: Instrument recognition is optional (flag-controlled).

6. **Error handling**: Each chain should handle LLM errors gracefully and provide fallback values where appropriate.

---

## Next Steps

1. Start with `pipeline_state.py` and basic chain structure
2. Implement summary and character recognition chains first (core functionality)
3. Add remaining chains incrementally
4. Test with example story segments
5. Integrate with existing test data
