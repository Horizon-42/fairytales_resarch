"""CLI runner for narrative event annotation.

Example:
  python -m llm_model.auto_narratives_cli --model qwen3:8b --text-file datasets/ChineseTales/texts/孟姜女哭长城.md --characters "孟姜女,范喜良,始皇帝"
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from llm_model.narrative_annotator import NarrativeAnnotatorConfig, annotate_narrative_event
from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(description="Narrative event auto-annotation via LLM provider (Ollama/Gemini).")
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
    parser.add_argument("--text-file", type=Path, required=True, help="Path to a UTF-8 text file containing the story segment")
    parser.add_argument("--characters", required=True, help="Comma-separated list of characters (e.g., 'Hero,Villain')")
    parser.add_argument("--culture", default=None, help="Optional culture hint")
    parser.add_argument("--narrative-id", help="UUID for the event (generates one if missing)")
    parser.add_argument("--text-span", help="JSON string for text_span: '{\"start\": 0, \"end\": 10, \"text\": \"...\"}'")
    
    parser.add_argument(
        "--existing-event",
        type=Path,
        default=None,
        help="Path to existing event JSON file",
    )
    parser.add_argument(
        "--history-events",
        type=Path,
        default=None,
        help="Path to JSON file containing list of previous events",
    )
    parser.add_argument(
        "--mode",
        choices=["supplement", "modify", "recreate"],
        default="recreate",
        help="Annotation mode",
    )
    parser.add_argument(
        "--additional-prompt",
        default=None,
        help="Additional instructions",
    )
    
    args = parser.parse_args()

    # Load text
    narrative_text = args.text_file.read_text(encoding="utf-8")

    # Parse characters
    character_list = [c.strip() for c in args.characters.split(",") if c.strip()]

    # Parse text_span
    if args.text_span:
        text_span = json.loads(args.text_span)
    else:
        # Default to whole text if not provided
        text_span = {"start": 0, "end": len(narrative_text), "text": narrative_text[:100] + "..."}

    # Load existing event
    existing_event = None
    if args.existing_event:
        existing_event = json.loads(args.existing_event.read_text(encoding="utf-8"))

    # Load history
    history_events = None
    if args.history_events:
        history_events = json.loads(args.history_events.read_text(encoding="utf-8"))

    provider = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    ollama_model = args.model if provider != "gemini" else os.getenv("OLLAMA_MODEL", "qwen3:8b")
    gemini_model = args.model if provider == "gemini" else os.getenv("GEMINI_MODEL", "")

    cfg = NarrativeAnnotatorConfig(
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

    narrative_id = args.narrative_id or str(uuid.uuid4())

    try:
        result = annotate_narrative_event(
            narrative_id=narrative_id,
            text_span=text_span,
            narrative_text=narrative_text,
            character_list=character_list,
            culture=args.culture,
            existing_event=existing_event,
            history_events=history_events,
            mode=args.mode,
            additional_prompt=args.additional_prompt,
            config=cfg,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"Error during annotation: {e}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
