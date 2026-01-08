"""CLI runner for character-only annotation.

Example:
  python -m llm_model.auto_characters_cli --model qwen3:8b --text-file datasets/ChineseTales/texts/孟姜女哭长城.md

Output is a small JSON object you can merge into app state under `motif`.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from llm_model.character_annotator import CharacterAnnotatorConfig, annotate_characters
from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(description="Character-only auto-annotation via LLM provider (Ollama/Gemini).")
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
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), help="Ollama base URL")
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

    provider = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    ollama_model = args.model if provider != "gemini" else os.getenv("OLLAMA_MODEL", "qwen3:8b")
    gemini_model = args.model if provider == "gemini" else os.getenv("GEMINI_MODEL", "")

    cfg = CharacterAnnotatorConfig(
        llm=LLMConfig(
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
