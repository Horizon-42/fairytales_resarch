"""Batch generate English summaries for all stories in annotation_status.csv.

This script reads all stories from annotation_status.csv, generates English summaries
using qwen3:8b model, and saves the results to a CSV file with columns:
story_name, text_file, summary
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List

from llm_model.env import load_repo_dotenv
from llm_model.ollama_client import OllamaConfig, chat


# Load environment variables if available
load_repo_dotenv()


def load_stories_from_csv(csv_path: Path, repo_root: Path) -> List[dict]:
    """Load story information from annotation_status.csv.

    Args:
        csv_path: Path to annotation_status.csv file.
        repo_root: Repository root directory for resolving relative paths.

    Returns:
        List of story dictionaries with text_file paths.
    """
    stories: List[dict] = []
    
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=__import__("sys").stderr)
        return stories
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text_file_str = row.get("text_file", "").strip()
            story_name = row.get("story_name", "").strip()
            
            if not text_file_str or not story_name:
                continue
            
            # Resolve text file path
            text_path = repo_root / text_file_str
            if not text_path.exists():
                print(f"Warning: Text file not found: {text_path}", file=__import__("sys").stderr)
                continue
            
            stories.append({
                "story_name": story_name,
                "text_file": text_file_str,
                "text_path": text_path,
            })
    
    return stories


def load_story_text(text_path: Path) -> str:
    """Load story text from file.

    Args:
        text_path: Path to the text file.

    Returns:
        The complete story text as a string.
    """
    try:
        return text_path.read_text(encoding="utf-8")
    except IOError as e:
        print(f"Error: Failed to read text file {text_path}: {e}", file=__import__("sys").stderr)
        return ""


def generate_summary(
    text: str,
    *,
    config: OllamaConfig,
    max_retries: int = 3,
) -> str:
    """Generate English summary for a story text.

    Args:
        text: The story text to summarize.
        config: OllamaConfig with base_url/model settings.
        max_retries: Maximum number of retries on failure.

    Returns:
        The generated summary as a string.
    """
    prompt = f"""Please provide a concise English summary of the following story. 
The summary should be 2-4 sentences long and capture the main plot, characters, and key events.

Story text:
{text}

Summary:"""

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]
    
    for attempt in range(max_retries):
        try:
            response = chat(
                config=config,
                messages=messages,
                response_format_json=False,  # Summary is plain text
                timeout_s=300.0,
            )
            return response.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Warning: Failed to generate summary (attempt {attempt + 1}/{max_retries}): {e}", file=__import__("sys").stderr)
            else:
                print(f"Error: Failed to generate summary after {max_retries} attempts: {e}", file=__import__("sys").stderr)
                return ""
    
    return ""


def save_summaries_csv(summaries: List[dict], output_path: Path) -> None:
    """Save summaries to CSV file.

    Args:
        summaries: List of dictionaries with story_name, text_file, summary.
        output_path: Path to output CSV file.
    """
    if not summaries:
        print("Warning: No summaries to save", file=__import__("sys").stderr)
        return
    
    fieldnames = ["story_name", "text_file", "summary"]
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for summary_data in summaries:
            writer.writerow(summary_data)


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).resolve().parents[1]
    
    parser = argparse.ArgumentParser(
        description="Batch generate English summaries for all stories in annotation_status.csv"
    )
    parser.add_argument(
        "--annotation-csv",
        type=Path,
        default=repo_root / "post_data_process" / "annotation_status.csv",
        help="Path to annotation_status.csv file",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=repo_root / "post_data_process" / "story_summaries.csv",
        help="Path to output CSV file with summaries",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model name (default: qwen3:8b)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama base URL",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Temperature for generation (default: 0.3)",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start processing from story index (for resuming interrupted runs)",
    )
    parser.add_argument(
        "--max-stories",
        type=int,
        default=None,
        help="Maximum number of stories to process (for testing)",
    )
    args = parser.parse_args()

    # Validate input file
    if not args.annotation_csv.exists():
        print(f"Error: Input CSV file not found: {args.annotation_csv}", file=__import__("sys").stderr)
        return 1

    # Load stories from CSV
    print(f"Loading stories from {args.annotation_csv}...")
    stories = load_stories_from_csv(args.annotation_csv, repo_root)
    print(f"Found {len(stories)} stories")

    if not stories:
        print("No stories found in CSV", file=__import__("sys").stderr)
        return 1

    # Limit stories if specified
    if args.max_stories:
        stories = stories[:args.max_stories]
        print(f"Limited to {len(stories)} stories for processing")

    # Skip stories before start_from
    if args.start_from > 0:
        stories = stories[args.start_from:]
        print(f"Starting from index {args.start_from}")

    # Setup Ollama config
    config = OllamaConfig(
        base_url=args.base_url,
        model=args.model,
        temperature=args.temperature,
    )

    print(f"Using model: {args.model} at {args.base_url}")
    print(f"Processing {len(stories)} stories...")

    # Process stories and generate summaries
    summaries: List[dict] = []
    failed_count = 0

    for idx, story in enumerate(stories):
        story_idx = args.start_from + idx
        story_name = story["story_name"]
        text_file = story["text_file"]
        
        print(f"\n[{story_idx + 1}/{len(stories) + args.start_from}] Processing: {story_name}")

        # Load story text
        text = load_story_text(story["text_path"])
        if not text:
            print(f"  Warning: Empty text, skipping", file=__import__("sys").stderr)
            failed_count += 1
            continue

        # Generate summary
        print(f"  Generating summary...")
        summary = generate_summary(text, config=config)

        if not summary:
            print(f"  Error: Failed to generate summary", file=__import__("sys").stderr)
            failed_count += 1
            continue

        # Store summary
        summaries.append({
            "story_name": story_name,
            "text_file": text_file,
            "summary": summary,
        })
        print(f"  ✓ Summary generated ({len(summary)} chars)")

        # Save progress periodically (every 10 stories)
        if (idx + 1) % 10 == 0:
            print(f"  Saving progress...")
            save_summaries_csv(summaries, args.output_csv)

    # Save final results
    print(f"\nSaving all summaries to {args.output_csv}...")
    save_summaries_csv(summaries, args.output_csv)

    print(f"\nDone!")
    print(f"  Total stories processed: {len(stories)}")
    print(f"  Successful summaries: {len(summaries)}")
    print(f"  Failed: {failed_count}")
    print(f"  Output file: {args.output_csv}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
