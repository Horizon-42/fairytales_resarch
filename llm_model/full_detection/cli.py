"""CLI interface for the full detection pipeline.

Example:
  # Analyze a single text span
  python -m llm_model.full_detection.cli \
    --story-file /path/to/story.txt \
    --start 0 \
    --end 200 \
    --characters-json characters.json \
    --time-order 1
  
  # Analyze multiple spans from a JSON file
  python -m llm_model.full_detection.cli \
    --story-file /path/to/story.txt \
    --spans-json spans.json \
    --characters-json characters.json \
    --output result.json
  
  # Include instrument recognition
  python -m llm_model.full_detection.cli \
    --story-file /path/to/story.txt \
    --start 0 \
    --end 200 \
    --include-instrument \
    --output result.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_model.env import load_repo_dotenv
from llm_model.full_detection import PipelineError, run_pipeline, run_pipeline_batch
from llm_model.gemini_client import GeminiConfig
from llm_model.huggingface_client import HuggingFaceConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig


def load_characters(file_path: Path) -> List[Dict[str, Any]]:
    """Load characters from JSON file."""
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Try common keys
        return data.get("characters", data.get("character_archetypes", []))
    return []


def load_text_spans(file_path: Path) -> List[Dict[str, Any]]:
    """Load text spans from JSON file."""
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Try to extract spans from narrative_events or similar
        if "narrative_events" in data:
            return [e.get("text_span", {}) for e in data["narrative_events"] if "text_span" in e]
        return []
    return []


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(
        description="Full narrative detection pipeline using LangChain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # LLM configuration
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "ollama"),
        help="LLM provider: ollama, gemini, or huggingface",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Enable thinking mode (for Gemini)",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Model name (varies by provider)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama base URL",
    )
    
    # Input arguments
    parser.add_argument(
        "--story-file",
        type=Path,
        required=True,
        help="Path to the full story text file (UTF-8)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Start index for single text span (0-based)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End index for single text span",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text content for single span (alternative to --start/--end)",
    )
    parser.add_argument(
        "--spans-json",
        type=Path,
        default=None,
        help="Path to JSON file with multiple text spans (for batch processing)",
    )
    parser.add_argument(
        "--characters-json",
        type=Path,
        default=None,
        help="Path to JSON file with character list (optional)",
    )
    parser.add_argument(
        "--time-order",
        type=int,
        default=1,
        help="Time order for single span (default: 1)",
    )
    
    # Options
    parser.add_argument(
        "--include-instrument",
        action="store_true",
        help="Include instrument recognition (Step 2.5)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path (default: stdout)",
    )
    
    args = parser.parse_args()

    # Validate story file
    if not args.story_file.exists():
        print(f"Error: Story file not found: {args.story_file}", file=sys.stderr)
        return 1
    
    story_text = args.story_file.read_text(encoding="utf-8")
    
    # Load characters
    characters = []
    if args.characters_json:
        characters = load_characters(args.characters_json)
    
    # Determine mode: single span or batch
    if args.spans_json:
        # Batch mode
        text_spans = load_text_spans(args.spans_json)
        if not text_spans:
            print("Error: No text spans found in --spans-json", file=sys.stderr)
            return 1
        
        # Ensure spans have 'text' field
        for span in text_spans:
            if "text" not in span and "start" in span and "end" in span:
                span["text"] = story_text[span["start"]:span["end"]]
        
        mode = "batch"
    elif args.start is not None and args.end is not None:
        # Single span mode with indices
        text_span = {
            "start": args.start,
            "end": args.end,
            "text": story_text[args.start:args.end],
        }
        mode = "single"
    elif args.text:
        # Single span mode with text
        # Try to find indices in story
        start_idx = story_text.find(args.text)
        if start_idx == -1:
            print("Warning: Text not found in story, using start=0", file=sys.stderr)
            start_idx = 0
        text_span = {
            "start": start_idx,
            "end": start_idx + len(args.text),
            "text": args.text,
        }
        mode = "single"
    else:
        print("Error: Must provide either --spans-json or (--start/--end or --text)", file=sys.stderr)
        return 1
    
    # Setup LLM config
    provider = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    
    llm_config = LLMConfig(
        provider=provider,
        thinking=bool(args.thinking),
        ollama=OllamaConfig(
            base_url=args.base_url,
            model=args.model if provider == "ollama" else os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        ),
        gemini=GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=args.model if provider == "gemini" else os.getenv("GEMINI_MODEL", ""),
            model_thinking=os.getenv("GEMINI_MODEL_THINKING", ""),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.9")),
            max_output_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")),
        ),
        huggingface=HuggingFaceConfig(
            model=args.model if provider in ("huggingface", "hf", "colab") else os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
            device=os.getenv("HF_DEVICE", "auto"),
            temperature=float(os.getenv("HF_TEMPERATURE", "0.2")),
            top_p=float(os.getenv("HF_TOP_P", "0.9")),
            max_new_tokens=int(os.getenv("HF_MAX_NEW_TOKENS", "2048")),
        ),
    )
    
    # Run pipeline
    try:
        if mode == "single":
            print(f"Running pipeline on text span [{text_span['start']}:{text_span['end']}]...", file=sys.stderr)
            result = run_pipeline(
                story_text=story_text,
                text_span=text_span,
                characters=characters,
                time_order=args.time_order,
                llm_config=llm_config,
                include_instrument=args.include_instrument,
            )
            output_data = {
                "narrative_event": result["narrative_event"],
                "updated_characters": result["updated_characters"],
            }
        else:
            print(f"Running pipeline on {len(text_spans)} text spans...", file=sys.stderr)
            result = run_pipeline_batch(
                story_text=story_text,
                text_spans=text_spans,
                characters=characters,
                llm_config=llm_config,
                include_instrument=args.include_instrument,
            )
            output_data = {
                "narrative_events": result["narrative_events"],
                "updated_characters": result["updated_characters"],
                "results": result["results"],
            }
        
        # Output results
        output_json = json.dumps(output_data, ensure_ascii=False, indent=2)
        
        if args.output:
            args.output.write_text(output_json, encoding="utf-8")
            print(f"Results written to: {args.output}", file=sys.stderr)
        else:
            print(output_json)
        
        return 0
        
    except PipelineError as e:
        print(f"Pipeline Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
