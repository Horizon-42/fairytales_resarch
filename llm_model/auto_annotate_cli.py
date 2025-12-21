"""CLI runner for quick local testing of the model layer.

Example:
  python -m llm_model.auto_annotate_cli --model llama3.1 --text-file /path/to/story.txt

This is optional for your workflow, but useful for debugging prompts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_model.annotator import AnnotatorConfig, annotate_text_v2
from llm_model.ollama_client import OllamaConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-annotate a text using Ollama.")
    parser.add_argument("--model", default="llama3.1", help="Ollama model name")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--text-file", type=Path, required=True, help="Path to a UTF-8 text file")
    parser.add_argument("--culture", default=None, help="Optional culture hint")
    parser.add_argument("--reference-uri", default="", help="Optional dataset uri")
    parser.add_argument("--language", default="en", help="Language tag")
    parser.add_argument("--source-type", default="story", help="Source type tag")
    args = parser.parse_args()

    text = args.text_file.read_text(encoding="utf-8")

    config = AnnotatorConfig(
        ollama=OllamaConfig(base_url=args.base_url, model=args.model),
    )

    result = annotate_text_v2(
        text=text,
        reference_uri=args.reference_uri,
        culture=args.culture,
        language=args.language,
        source_type=args.source_type,
        config=config,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
