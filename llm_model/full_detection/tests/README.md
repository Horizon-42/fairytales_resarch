# Full Detection Package - Unit Tests

## Running Tests

**IMPORTANT**: Always run tests in the conda nlp environment:

```bash
# Activate conda environment
conda activate nlp

# Run all tests
pytest llm_model/full_detection/tests/

# Run specific test file
pytest llm_model/full_detection/tests/test_utils.py

# Run with verbose output
pytest llm_model/full_detection/tests/ -v

# Run with coverage
pytest llm_model/full_detection/tests/ --cov=llm_model.full_detection
```

Or using conda run:

```bash
conda run -n nlp python -m pytest llm_model/full_detection/tests/
```

## Test Structure

- `test_utils.py`: Tests for utility functions (character matching, alias resolution)
- `test_pipeline_state.py`: Tests for PipelineState dataclass
- `test_pipeline.py`: Tests for pipeline orchestration (with mocked LLM calls)
- `test_story_processor.py`: Tests for story-level processing (with mocked LLM calls)

## Mocking Strategy

Unit tests use `unittest.mock` to mock LLM calls, avoiding dependency on actual Ollama/Gemini services:

- `@patch('llm_model.full_detection.pipeline.chat')` for pipeline tests
- `@patch('llm_model.full_detection.story_processor.chat')` for story processor tests

This ensures:
- Tests run quickly without network calls
- Tests are deterministic and reproducible
- Tests don't require LLM services to be running

## Test Coverage Goals

- ✅ Utility functions (100% coverage)
- ✅ PipelineState (basic operations)
- ✅ Pipeline orchestration (with mocks)
- ✅ Story processor (with mocks)
- 🔄 Integration tests (can be added later for end-to-end testing)
