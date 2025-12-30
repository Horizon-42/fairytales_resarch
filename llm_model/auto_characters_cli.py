"""CLI runner for character-only annotation.

Example:
  python -m llm_model.auto_characters_cli --model qwen3:8b --text-file datasets/ChineseTales/texts/孟姜女哭长城.md

Output is a small JSON object you can merge into app state under `motif`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_model.character_annotator import CharacterAnnotatorConfig, annotate_characters
from llm_model.ollama_client import OllamaConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Character-only auto-annotation via Ollama.")
    parser.add_argument("--model", default="qwen3:8b", help="Ollama model name")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--text-file", type=Path, required=True, help="Path to a UTF-8 text file")
    parser.add_argument("--culture", default=None, help="Optional culture hint")
    parser.add_argument(
        "--existing-characters",
        type=Path,
        default=None,
        help="Path to existing character annotation JSON file (for incremental annotation)",
    )
    parser.add_argument(
        "--mode",
        choices=["supplement", "modify", "recreate"],
        default="recreate",
        help="Annotation mode: supplement (add missing), modify (update existing), recreate (from scratch)",
    )
    parser.add_argument(
        "--additional-prompt",
        default=None,
        help="Additional instructions for the annotation model",
    )
    args = parser.parse_args()

    text = args.text_file.read_text(encoding="utf-8")

    existing_characters = None
    if args.existing_characters:
        if not args.existing_characters.exists():
            print(f"Error: Existing character annotation file not found: {args.existing_characters}", file=__import__("sys").stderr)
            return 1
        try:
            existing_characters = json.loads(args.existing_characters.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse existing character annotation JSON: {e}", file=__import__("sys").stderr)
            return 1

    cfg = CharacterAnnotatorConfig(
        ollama=OllamaConfig(base_url=args.base_url, model=args.model),
    )

    result = annotate_characters(
        text=text,
        culture=args.culture,
        existing_characters=existing_characters,
        mode=args.mode,
        additional_prompt=args.additional_prompt,
        config=cfg,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
