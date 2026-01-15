"""CLI runner for sentence-level event analysis.

Example:
  # Analyze a single sentence
  python -m llm_model.auto_sentence_analysis_cli \
    --story-file /path/to/story.txt \
    --sentence "The hero defeated the dragon."
  
  # Auto-split and analyze all sentences
  python -m llm_model.auto_sentence_analysis_cli \
    --story-file /path/to/story.txt \
    --output result.json

This tool analyzes sentences within the context of a complete story.
If --sentence is provided, it analyzes only that sentence.
Otherwise, it automatically splits the story into sentences and analyzes each one.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import sentence_splitter
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig
from llm_model.sentence_analyzer import SentenceAnalyzerConfig, analyze_sentence
from pre_data_process.sentence_splitter import split_sentences_advanced


def main() -> int:
    load_repo_dotenv()

    parser = argparse.ArgumentParser(
        description="Analyze sentences within the context of a story."
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
        default="qwen3:8b",
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
        default=None,
        help="Path to the text file (UTF-8). Required for context mode or batch processing. In no-context mode, can be used for batch sentence splitting.",
    )
    parser.add_argument(
        "--sentence",
        type=str,
        default=None,
        help="Optional: analyze only this specific sentence. If not provided, auto-split and analyze all sentences from --story-file.",
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Analyze sentences without story context. In this mode, --story-file can still be used for batch processing (sentence splitting), but won't be used as context.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional: output JSON file path. If not provided, output to stdout.",
    )
    args = parser.parse_args()

    use_context = not args.no_context

    # Validate arguments based on mode
    file_content = None
    if use_context:
        # Context mode: story_file is required
        if not args.story_file:
            print("Error: --story-file is required when using context mode", file=sys.stderr)
            return 1
        if not args.story_file.exists():
            print(f"Error: Story file not found: {args.story_file}", file=sys.stderr)
            return 1
        file_content = args.story_file.read_text(encoding="utf-8")
        story_context = file_content  # Use as context
    else:
        # No-context mode: story_file is optional
        # If provided, it will be used for batch processing (sentence splitting) but not as context
        if args.story_file:
            if not args.story_file.exists():
                print(f"Error: Story file not found: {args.story_file}", file=sys.stderr)
                return 1
            file_content = args.story_file.read_text(encoding="utf-8")
        story_context = None  # Never use as context in no-context mode

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
        # If a specific sentence is provided, analyze only that sentence
        if args.sentence:
            sentence = args.sentence.strip()
            if not sentence:
                print("Error: Sentence cannot be empty", file=sys.stderr)
                return 1
            
            result = analyze_sentence(
                sentence=sentence,
                story_context=story_context,
                use_context=use_context,
                config=config,
            )
            output_data = result
        else:
            # Auto-split and analyze all sentences
            # Need file_content for sentence splitting (can be from story_file in both modes)
            if not file_content:
                print("Error: --story-file is required for batch processing", file=sys.stderr)
                return 1
            
            print("Splitting text into sentences...", file=sys.stderr)
            sentences = split_sentences_advanced(file_content)
            print(f"Found {len(sentences)} sentences. Analyzing...", file=sys.stderr)
            
            results = []
            for idx, sentence in enumerate(sentences, start=1):
                print(f"Analyzing sentence {idx}/{len(sentences)}: {sentence[:50]}...", file=sys.stderr)
                try:
                    analysis = analyze_sentence(
                        sentence=sentence,
                        story_context=story_context if use_context else None,
                        use_context=use_context,
                        config=config,
                    )
                    results.append({
                        "sentence_index": idx,
                        "sentence": sentence,
                        "analysis": analysis,
                    })
                except Exception as e:
                    print(f"Warning: Failed to analyze sentence {idx}: {e}", file=sys.stderr)
                    results.append({
                        "sentence_index": idx,
                        "sentence": sentence,
                        "analysis": None,
                        "error": str(e),
                    })
            
            output_data = {
                "story_file": str(args.story_file) if args.story_file else None,
                "use_context": use_context,
                "total_sentences": len(sentences),
                "analyzed_sentences": len(results),
                "sentences": results,
            }
        
        # Output results
        output_json = json.dumps(output_data, ensure_ascii=False, indent=2)
        
        if args.output:
            args.output.write_text(output_json, encoding="utf-8")
            print(f"Results written to: {args.output}", file=sys.stderr)
        else:
            print(output_json)
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
