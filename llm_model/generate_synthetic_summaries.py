"""Batch generate summaries for all stories in synthetic_datasets/generated_stories.

This script:
1. Scans synthetic_datasets/generated_stories for all .txt story files
2. Detects story language (Chinese, English, Japanese, etc.)
3. Generates summaries in the same language as the story
4. Uses non-thinking mode for faster inference
5. Saves results to CSV file
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from llm_model.env import load_repo_dotenv
from llm_model.ollama_client import OllamaConfig, chat


# Load environment variables if available
load_repo_dotenv()


def detect_language(text: str, filename: str = "", culture: str = "") -> str:
    """Detect story language from text content, filename, and culture.
    
    Args:
        text: Story text content
        filename: Story filename (may contain language hints)
        culture: Culture/directory name (e.g., "Japanese", "ChineseTales")
    
    Returns:
        Language code: 'zh' (Chinese), 'en' (English), 'ja' (Japanese), etc.
    """
    # Check culture/directory name first (most reliable)
    culture_lower = culture.lower()
    if 'japanese' in culture_lower:
        return 'ja'
    if 'chinese' in culture_lower:
        return 'zh'
    if 'indian' in culture_lower:
        return 'en'
    
    # Check filename for language hints
    filename_lower = filename.lower()
    if 'ch_' in filename_lower or 'chinese' in filename_lower:
        return 'zh'
    if 'en_' in filename_lower or 'english' in filename_lower or 'indian' in filename_lower:
        return 'en'
    # Check for both ja_ and jp_ (Japanese stories use jp_ prefix)
    if 'ja_' in filename_lower or 'jp_' in filename_lower or 'japanese' in filename_lower:
        return 'ja'
    
    # Detect from text content (simple heuristic)
    # Count Chinese characters (CJK Unified Ideographs)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Count Japanese characters (Hiragana, Katakana, and some CJK)
    # Hiragana: \u3040-\u309f, Katakana: \u30a0-\u30ff
    # Also include common Japanese punctuation and symbols
    japanese_hiragana = len(re.findall(r'[\u3040-\u309f]', text))
    japanese_katakana = len(re.findall(r'[\u30a0-\u30ff]', text))
    japanese_chars = japanese_hiragana + japanese_katakana
    # Count English words
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    
    total_chars = len(text)
    
    if total_chars == 0:
        return 'en'  # Default to English
    
    # Calculate ratios
    chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
    japanese_ratio = japanese_chars / total_chars if total_chars > 0 else 0
    english_ratio = english_words / (total_chars / 5) if total_chars > 0 else 0  # Rough estimate
    
    # Determine language (prioritize Japanese if hiragana/katakana found)
    if japanese_ratio > 0.05 or japanese_hiragana > 10 or japanese_katakana > 10:  # More than 5% Japanese characters or significant hiragana/katakana
        return 'ja'
    elif chinese_ratio > 0.1:  # More than 10% Chinese characters
        return 'zh'
    elif english_ratio > 0.3:  # More than 30% English words
        return 'en'
    else:
        # Default to English if unclear
        return 'en'


def get_language_prompt(language: str) -> Tuple[str, str]:
    """Get prompt template for summary generation in specific language.
    
    Args:
        language: Language code ('zh', 'en', 'ja', etc.)
    
    Returns:
        Tuple of (instruction_template, language_name)
    """
    language_map = {
        'zh': ('请用中文为以下故事提供一个简洁的摘要。摘要应该包含2-4句话，概括主要情节、人物和关键事件。', '中文'),
        'en': ('Please provide a concise summary of the following story. The summary should be 2-4 sentences long and capture the main plot, characters, and key events.', 'English'),
        'ja': ('以下の物語の簡潔な要約を日本語で提供してください。要約は2-4文で、主なプロット、登場人物、重要な出来事を捉える必要があります。', 'Japanese'),
    }
    
    return language_map.get(language, language_map['en'])


def find_story_files(stories_dir: Path) -> List[dict]:
    """Find all story text files in synthetic_datasets/generated_stories.
    
    Args:
        stories_dir: Path to synthetic_datasets/generated_stories directory
    
    Returns:
        List of dictionaries with story information:
        {
            "story_name": str,
            "file_path": Path,
            "relative_path": str,
            "culture": str (inferred from directory structure)
        }
    """
    story_files = []
    
    if not stories_dir.exists():
        print(f"Error: Stories directory not found: {stories_dir}", file=__import__("sys").stderr)
        return story_files
    
    # Walk through all subdirectories
    for txt_file in stories_dir.rglob("*.txt"):
        # Skip if in hidden directories
        if any(part.startswith('.') for part in txt_file.parts):
            continue
        
        # Extract story name from path
        # Format: stories_dir/Culture/StoryName_v3/gemini/StoryName_gen_XX.txt
        parts = txt_file.relative_to(stories_dir).parts
        
        if len(parts) >= 2:
            culture = parts[0]  # e.g., "ChineseTales", "IndianTales", "Japanese"
            story_folder = parts[1]  # e.g., "CH_002_牛郎织女_v3"
            
            # Extract base story name
            story_name = story_folder.replace('_v3', '').replace('_gen_', '_')
            
            # Get relative path for reference
            relative_path = txt_file.relative_to(stories_dir.parent.parent)
            
            story_files.append({
                "story_name": story_name,
                "file_path": txt_file,
                "relative_path": str(relative_path),
                "culture": culture,
            })
        else:
            # Fallback: use filename
            story_name = txt_file.stem
            story_files.append({
                "story_name": story_name,
                "file_path": txt_file,
                "relative_path": str(txt_file.relative_to(stories_dir.parent.parent)),
                "culture": "Unknown",
            })
    
    return sorted(story_files, key=lambda x: (x["culture"], x["story_name"], x["file_path"].name))


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
    language: str,
    *,
    config: OllamaConfig,
    max_retries: int = 3,
) -> str:
    """Generate summary for a story text in the specified language.
    
    Args:
        text: The story text to summarize.
        language: Language code ('zh', 'en', 'ja', etc.)
        config: OllamaConfig with base_url/model settings (think=False for non-thinking mode).
        max_retries: Maximum number of retries on failure.
    
    Returns:
        The generated summary as a string in the specified language.
    """
    instruction_template, language_name = get_language_prompt(language)
    
    prompt = f"""{instruction_template}

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
        summaries: List of dictionaries with story_name, relative_path, culture, language, summary.
        output_path: Path to output CSV file.
    """
    if not summaries:
        print("Warning: No summaries to save", file=__import__("sys").stderr)
        return
    
    fieldnames = ["story_name", "relative_path", "culture", "language", "summary"]
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for summary_data in summaries:
            writer.writerow(summary_data)


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).resolve().parents[1]
    
    parser = argparse.ArgumentParser(
        description="Batch generate summaries for all stories in synthetic_datasets/generated_stories"
    )
    parser.add_argument(
        "--stories-dir",
        type=Path,
        default=repo_root / "synthetic_datasets" / "generated_stories",
        help="Path to synthetic_datasets/generated_stories directory",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=repo_root / "synthetic_datasets" / "story_summaries.csv",
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

    # Validate input directory
    if not args.stories_dir.exists():
        print(f"Error: Stories directory not found: {args.stories_dir}", file=__import__("sys").stderr)
        return 1

    # Find all story files
    print(f"Scanning for story files in {args.stories_dir}...")
    story_files = find_story_files(args.stories_dir)
    print(f"Found {len(story_files)} story files")

    if not story_files:
        print("No story files found", file=__import__("sys").stderr)
        return 1

    # Limit stories if specified
    if args.max_stories:
        story_files = story_files[:args.max_stories]
        print(f"Limited to {len(story_files)} stories for processing")

    # Skip stories before start_from
    if args.start_from > 0:
        story_files = story_files[args.start_from:]
        print(f"Starting from index {args.start_from}")

    # Setup Ollama config with non-thinking mode
    config = OllamaConfig(
        base_url=args.base_url,
        model=args.model,
        temperature=args.temperature,
        think=False,  # Disable thinking mode for faster inference
    )

    print(f"Using model: {args.model} at {args.base_url}")
    print(f"Thinking mode: DISABLED (think=False)")
    print(f"Processing {len(story_files)} stories...")

    # Process stories and generate summaries
    summaries: List[dict] = []
    failed_count = 0

    for idx, story_info in enumerate(story_files):
        story_idx = args.start_from + idx
        story_name = story_info["story_name"]
        file_path = story_info["file_path"]
        relative_path = story_info["relative_path"]
        culture = story_info["culture"]
        
        print(f"\n[{story_idx + 1}/{len(story_files) + args.start_from}] Processing: {story_name}")
        print(f"  File: {relative_path}")
        print(f"  Culture: {culture}")

        # Load story text
        text = load_story_text(file_path)
        if not text:
            print(f"  Warning: Empty text, skipping", file=__import__("sys").stderr)
            failed_count += 1
            continue

        # Detect language (pass culture for better detection)
        language = detect_language(text, file_path.name, culture)
        print(f"  Detected language: {language}")

        # Generate summary
        print(f"  Generating summary in {language}...")
        summary = generate_summary(text, language, config=config)

        if not summary:
            print(f"  Error: Failed to generate summary", file=__import__("sys").stderr)
            failed_count += 1
            continue

        # Store summary
        summaries.append({
            "story_name": story_name,
            "relative_path": relative_path,
            "culture": culture,
            "language": language,
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
    print(f"  Total stories processed: {len(story_files)}")
    print(f"  Successful summaries: {len(summaries)}")
    print(f"  Failed: {failed_count}")
    print(f"  Output file: {args.output_csv}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
