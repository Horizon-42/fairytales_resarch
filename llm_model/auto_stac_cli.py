"""CLI runner for STAC (Situation, Task, Action, Consequence) analysis.

Example:
  # Basic usage with a single sentence
  python -m llm_model.auto_stac_cli --sentence "王子来到了森林"

  # With story context
  python -m llm_model.auto_stac_cli --sentence "王子来到了森林" --story-file story.txt

  # With neighboring sentences
  python -m llm_model.auto_stac_cli --sentence "王子来到了森林" --prev-sentence "从前有一个王子" --next-sentence "他在森林里遇到了仙女"

  # With both story context and neighboring sentences
  python -m llm_model.auto_stac_cli --sentence "王子来到了森林" --story-file story.txt --prev-sentence "从前有一个王子" --next-sentence "他在森林里遇到了仙女"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig
from llm_model.stac_analyzer import STACAnalyzerConfig, analyze_stac


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(
        description="STAC (Situation, Task, Action, Consequence) analysis via LLM provider (Ollama/Gemini)."
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "ollama"),
        help="LLM provider: ollama (local) or gemini (cloud)",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Enable thinking mode (Gemini uses GEMINI_MODEL_THINKING)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        help="Model name (Ollama model or Gemini model, depends on --provider)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama base URL",
    )
    parser.add_argument(
        "--sentence",
        type=str,
        required=True,
        help="The sentence to analyze (required)",
    )
    parser.add_argument(
        "--story-file",
        type=Path,
        default=None,
        help="Path to a UTF-8 text file containing the full story context",
    )
    parser.add_argument(
        "--use-context",
        action="store_true",
        default=False,
        help="Use story context in analysis (requires --story-file)",
    )
    parser.add_argument(
        "--prev-sentence",
        type=str,
        default=None,
        help="Previous sentence (for auxiliary context)",
    )
    parser.add_argument(
        "--next-sentence",
        type=str,
        default=None,
        help="Next sentence (for auxiliary context)",
    )
    parser.add_argument(
        "--use-neighboring",
        action="store_true",
        default=False,
        help="Use neighboring sentences as auxiliary information (requires at least one of --prev-sentence or --next-sentence)",
    )
    args = parser.parse_args()

    # Validate sentence
    if not args.sentence.strip():
        print("Error: --sentence must be a non-empty string", file=sys.stderr)
        return 1

    # Read story context if provided
    story_context = None
    if args.story_file:
        if not args.story_file.exists():
            print(f"Error: Story file not found: {args.story_file}", file=sys.stderr)
            return 1
        try:
            story_context = args.story_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error: Failed to read story file: {e}", file=sys.stderr)
            return 1

    # Validate use_context
    if args.use_context and not story_context:
        print("Error: --use-context requires --story-file", file=sys.stderr)
        return 1

    # Validate use_neighboring
    if args.use_neighboring and not args.prev_sentence and not args.next_sentence:
        print(
            "Error: --use-neighboring requires at least one of --prev-sentence or --next-sentence",
            file=sys.stderr,
        )
        return 1

    # Setup LLM config
    provider = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    ollama_model = args.model if provider != "gemini" else os.getenv("OLLAMA_MODEL", "qwen3:8b")
    gemini_model = args.model if provider == "gemini" else os.getenv("GEMINI_MODEL", "")

    llm = LLMConfig(
        provider=provider,
        thinking=bool(args.thinking),
        ollama=OllamaConfig(base_url=args.base_url, model=ollama_model),
        gemini=GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=gemini_model,
            model_thinking=os.getenv("GEMINI_MODEL_THINKING", ""),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.9")),
            max_output_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")),
        ),
    )

    config = STACAnalyzerConfig(llm=llm)

    try:
        result = analyze_stac(
            sentence=args.sentence,
            story_context=story_context,
            use_context=args.use_context,
            previous_sentence=args.prev_sentence,
            next_sentence=args.next_sentence,
            use_neighboring_sentences=args.use_neighboring,
            config=config,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"Error: STAC analysis failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
