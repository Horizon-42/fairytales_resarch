"""CLI runner for sentence-level event analysis.

Example:
  python -m llm_model.auto_sentence_analysis_cli \
    --story-file /path/to/story.txt \
    --sentence "The hero defeated the dragon."

This tool analyzes a single sentence within the context of a complete story.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig
from llm_model.sentence_analyzer import SentenceAnalyzerConfig, analyze_sentence


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(
        description="Analyze a single sentence within the context of a story."
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
        default="llama3.1",
        help="Model name (Ollama model or Gemini model, depends on --provider)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama base URL",
    )
    parser.add_argument(
        "--story-file",
        type=Path,
        required=True,
        help="Path to the story text file (UTF-8)",
    )
    parser.add_argument(
        "--sentence",
        type=str,
        required=True,
        help="The sentence to analyze",
    )
    args = parser.parse_args()

    if not args.story_file.exists():
        print(f"Error: Story file not found: {args.story_file}", file=__import__("sys").stderr)
        return 1

    story_context = args.story_file.read_text(encoding="utf-8")
    sentence = args.sentence.strip()

    if not sentence:
        print("Error: Sentence cannot be empty", file=__import__("sys").stderr)
        return 1

    provider = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()

    ollama_model = args.model if provider != "gemini" else os.getenv("OLLAMA_MODEL", "qwen3:8b")
    gemini_model = args.model if provider == "gemini" else os.getenv("GEMINI_MODEL", "")

    llm = LLMConfig(
        provider=provider,  # normalized inside router
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

    config = SentenceAnalyzerConfig(llm=llm)

    try:
        result = analyze_sentence(
            story_context=story_context,
            sentence=sentence,
            config=config,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
