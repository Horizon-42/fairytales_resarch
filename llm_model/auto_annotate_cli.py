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

    config = AnnotatorConfig(
        ollama=OllamaConfig(base_url=args.base_url, model=args.model),
    )

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
