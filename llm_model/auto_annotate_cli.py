"""CLI runner for quick local testing of the model layer.

Example:
  python -m llm_model.auto_annotate_cli --model llama3.1 --text-file /path/to/story.txt

This is optional for your workflow, but useful for debugging prompts.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from llm_model.annotator import AnnotatorConfig, annotate_text_v2
from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(description="Auto-annotate a text using Ollama.")
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
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), help="Ollama base URL")
    parser.add_argument("--text-file", type=Path, required=True, help="Path to a UTF-8 text file")
    parser.add_argument("--culture", default=None, help="Optional culture hint")
    parser.add_argument("--reference-uri", default="", help="Optional dataset uri")
    parser.add_argument("--language", default="en", help="Language tag")
    parser.add_argument("--source-type", default="story", help="Source type tag")
    parser.add_argument(
        "--existing-annotation",
        type=Path,
        default=None,
        help="Path to existing annotation JSON file (for incremental annotation)",
    )
    parser.add_argument(
        "--mode",
        choices=["supplement", "modify", "recreate"],
        default="recreate",
        help="Annotation mode: supplement (add missing), modify (update existing), recreate (from scratch)",
    )
    args = parser.parse_args()

    text = args.text_file.read_text(encoding="utf-8")

    existing_annotation = None
    if args.existing_annotation:
        if not args.existing_annotation.exists():
            print(f"Error: Existing annotation file not found: {args.existing_annotation}", file=__import__("sys").stderr)
            return 1
        try:
            existing_annotation = json.loads(args.existing_annotation.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse existing annotation JSON: {e}", file=__import__("sys").stderr)
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

    config = AnnotatorConfig(llm=llm)

    result = annotate_text_v2(
        text=text,
        reference_uri=args.reference_uri,
        culture=args.culture,
        language=args.language,
        source_type=args.source_type,
        existing_annotation=existing_annotation,
        mode=args.mode,
        config=config,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
