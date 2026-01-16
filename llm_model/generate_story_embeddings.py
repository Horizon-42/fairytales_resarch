"""Generate embeddings for complete stories from JSON v3 files.

This script reads story JSON files, extracts the complete story text, generates embeddings
for each story, and saves the results to TSV files:
1. story_embeddings.tsv: Contains all story embedding vectors (tab-separated)
2. story_metadata.tsv: Contains metadata (story_id, title, culture, etc.)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import List

from llm_model.embedding_generator import generate_embeddings


def load_story_from_json(json_path: Path) -> dict | None:
    """Load story data from a JSON v3 file.

    Args:
        json_path: Path to the JSON file.

    Returns:
        Dictionary containing story data, or None if loading fails.
    """
    return extract_story_metadata_from_json(json_path)


def extract_story_text(story_data: dict) -> str:
    """Extract the complete story text from story data (legacy function for directory scanning mode).

    Args:
        story_data: Dictionary containing story JSON data.

    Returns:
        The complete story text as a string.
    """
    # Try to get text from source_info.text_content
    source_info = story_data.get("source_info", {})
    text = source_info.get("text_content", "")
    
    if not text:
        # Fallback: try to read from text file if reference_uri is provided
        reference_uri = source_info.get("reference_uri", "")
        if reference_uri:
            # Try relative to repo root
            repo_root = Path(__file__).resolve().parents[1]
            text_path = repo_root / reference_uri
            if text_path.exists():
                try:
                    text = text_path.read_text(encoding="utf-8")
                except IOError:
                    pass
    
    return text


def load_story_text_from_file(text_path: Path) -> str:
    """Load story text directly from text file.

    Args:
        text_path: Path to the text file.

    Returns:
        The complete story text as a string.
    """
    try:
        return text_path.read_text(encoding="utf-8")
    except IOError as e:
        print(f"Warning: Failed to read text file {text_path}: {e}", file=__import__("sys").stderr)
        return ""


def extract_story_metadata_from_json(json_path: Path) -> dict | None:
    """Extract metadata from JSON v3 file if available.

    Args:
        json_path: Path to the JSON v3 file.

    Returns:
        Dictionary containing story metadata, or None if loading fails.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load JSON metadata from {json_path}: {e}", file=__import__("sys").stderr)
        return None


def find_story_json_files(directory: Path, pattern: str = "*_v3.json") -> List[Path]:
    """Find all story JSON files in a directory.

    Args:
        directory: Directory to search in.
        pattern: Glob pattern for JSON files.

    Returns:
        List of paths to JSON files.
    """
    if not directory.exists():
        return []
    
    json_files = list(directory.glob(pattern))
    return sorted(json_files)


def load_stories_from_annotation_status(
    csv_path: Path, repo_root: Path
) -> tuple[List[dict], dict[str, dict]]:
    """Load story information from annotation_status.csv.

    This function reads stories directly from CSV, using text_file for text content
    and optionally v3_path for metadata if available.

    Args:
        csv_path: Path to annotation_status.csv file.
        repo_root: Repository root directory for resolving relative paths.

    Returns:
        Tuple of (list of story dicts with text_file and optional v3_path, 
                 mapping of story identifier to CSV metadata).
    """
    stories: List[dict] = []
    csv_metadata: dict[str, dict] = {}
    
    if not csv_path.exists():
        print(f"Warning: annotation_status.csv not found at {csv_path}", file=__import__("sys").stderr)
        return stories, csv_metadata
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text_file_str = row.get("text_file", "").strip()
            if not text_file_str:
                continue
            
            # Resolve text file path
            text_path = repo_root / text_file_str
            if not text_path.exists():
                print(f"Warning: Text file not found: {text_path}", file=__import__("sys").stderr)
                continue
            
            # Get optional v3 JSON path for metadata
            v3_path_str = row.get("v3_path", "").strip()
            json_path = None
            if v3_path_str:
                json_path = repo_root / v3_path_str
                if not json_path.exists():
                    json_path = None  # JSON file doesn't exist, will skip metadata from JSON
            
            story_name = row.get("story_name", "")
            story_id = f"{row.get('dataset', '')}_{story_name}"
            
            # Store story info
            story_info = {
                "text_file": text_path,
                "json_file": json_path,
                "story_id": story_id,
            }
            stories.append(story_info)
            
            # Store CSV metadata
            csv_metadata[story_id] = {
                "dataset": row.get("dataset", ""),
                "story_name": story_name,
                "text_file": text_file_str,
                "v3_path": v3_path_str if json_path else "",
            }
    
    return stories, csv_metadata


def save_embeddings_tsv(embeddings: List[List[float]], output_path: Path) -> None:
    """Save embeddings to TSV file.

    Each row contains one embedding vector, with values separated by tabs.

    Args:
        embeddings: List of embedding vectors.
        output_path: Path to output TSV file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for emb in embeddings:
            # Convert each float to string and join with tabs
            line = "\t".join(str(val) for val in emb)
            f.write(line + "\n")


def save_metadata_tsv(
    stories: List[dict],
    output_path: Path,
    csv_metadata_map: dict[str, dict] | None = None,
) -> None:
    """Save story metadata to TSV file.

    Args:
        stories: List of story dictionaries containing metadata.
        output_path: Path to output TSV file.
        csv_metadata_map: Optional mapping from JSON path to CSV metadata (dataset, story_name).
    """
    if not stories:
        return

    # Define columns to include
    include_columns = [
        "dataset",
        "story_name",
        "story_id",
        "title",
        "culture",
        "language",
        "reference_uri",
        "date_annotated",
        "annotator",
        "confidence",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=include_columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for story in stories:
            # Extract metadata from story data structure (may not exist if no JSON file)
            metadata = story.get("metadata", {})
            source_info = story.get("source_info", {})
            
            # Get CSV metadata if available
            story_id = story.get("_story_id", "")
            json_path = story.get("_json_path", "")
            
            # Try to get metadata from CSV first
            csv_meta = csv_metadata_map.get(story_id, {}) if csv_metadata_map else {}
            if not csv_meta and json_path:
                # Fallback: try to get by JSON path (legacy mode)
                csv_meta = csv_metadata_map.get(json_path, {}) if csv_metadata_map else {}
            
            row = {
                "dataset": csv_meta.get("dataset", "") or metadata.get("culture", "") or "",
                "story_name": csv_meta.get("story_name", "") or metadata.get("id", "") or story_id.split("_", 1)[-1] if story_id else "",
                "story_id": metadata.get("id", "") or story_id or "",
                "title": metadata.get("title", "") or "",
                "culture": metadata.get("culture", "") or csv_meta.get("dataset", "") or "",
                "language": source_info.get("language", "") if source_info else "",
                "reference_uri": source_info.get("reference_uri", "") if source_info else csv_meta.get("text_file", ""),
                "date_annotated": metadata.get("date_annotated", "") if metadata else "",
                "annotator": metadata.get("annotator", "") if metadata else "",
                "confidence": str(metadata.get("confidence", "")) if metadata and "confidence" in metadata else "",
            }
            writer.writerow(row)


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).resolve().parents[1]
    
    parser = argparse.ArgumentParser(
        description="Generate embeddings for complete stories from JSON v3 files"
    )
    parser.add_argument(
        "--annotation-csv",
        type=Path,
        default=repo_root / "post_data_process" / "annotation_status.csv",
        help="Path to annotation_status.csv file (default: post_data_process/annotation_status.csv)",
    )
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=None,
        help="Directory containing story JSON v3 files (if provided, scans directory instead of using CSV)",
    )
    parser.add_argument(
        "--json-pattern",
        type=str,
        default="*_v3.json",
        help="Glob pattern for JSON files when using --json-dir (default: *_v3.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "post_data_process",
        help="Directory to save output TSV files",
    )
    parser.add_argument(
        "--embeddings-file",
        type=str,
        default="story_embeddings.tsv",
        help="Name of the embeddings TSV file",
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        default="story_metadata.tsv",
        help="Name of the metadata TSV file",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("EMBEDDING_PROVIDER", "ollama"),
        help="Embedding provider (default: ollama)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        help="Embedding model name",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Base URL for embedding provider",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of stories to process in each batch (default: 10)",
    )
    parser.add_argument(
        "--min-text-length",
        type=int,
        default=10,
        help="Minimum text length to process a story (default: 10)",
    )
    parser.add_argument(
        "--instruction",
        type=str,
        default=os.getenv("EMBEDDING_INSTRUCTION", None),
        help="Optional instruction to prepend to each text for instruction-based embeddings. "
             "If provided, each input will be formatted as '{instruction} {text}'. "
             "Can also be set via EMBEDDING_INSTRUCTION environment variable.",
    )
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load stories from CSV or directory
    csv_metadata_map: dict[str, dict] | None = None
    if args.json_dir is not None:
        # Use directory scanning mode (legacy)
        if not args.json_dir.exists():
            print(f"Error: Input directory not found: {args.json_dir}", file=__import__("sys").stderr)
            return 1
        print(f"Scanning for story JSON files in {args.json_dir}...")
        json_files = find_story_json_files(args.json_dir, args.json_pattern)
        print(f"Found {len(json_files)} JSON files")
        
        # Load stories and extract texts from JSON files
        stories_data: List[dict] = []
        story_texts: List[str] = []
        
        for json_file in json_files:
            story_data = load_story_from_json(json_file)
            if story_data is None:
                continue
            
            text = extract_story_text(story_data)
            if len(text) < args.min_text_length:
                print(
                    f"Warning: Story {json_file.name} has text shorter than {args.min_text_length} chars, skipping",
                    file=__import__("sys").stderr,
                )
                continue
            
            story_data["_json_path"] = str(json_file)
            stories_data.append(story_data)
            story_texts.append(text)
    else:
        # Use annotation_status.csv mode (default) - read directly from text_file
        print(f"Loading stories from {args.annotation_csv}...")
        stories_info, csv_metadata_map = load_stories_from_annotation_status(args.annotation_csv, repo_root)
        print(f"Found {len(stories_info)} stories in CSV")
        
        # Load stories and extract texts from text files
        stories_data: List[dict] = []
        story_texts: List[str] = []
        
        for story_info in stories_info:
            text_file = story_info["text_file"]
            json_file = story_info.get("json_file")
            story_id = story_info["story_id"]
            
            # Load text directly from text file
            text = load_story_text_from_file(text_file)
            if len(text) < args.min_text_length:
                print(
                    f"Warning: Story {text_file.name} has text shorter than {args.min_text_length} chars, skipping",
                    file=__import__("sys").stderr,
                )
                continue
            
            # Try to load metadata from JSON if available
            story_data: dict = {
                "_story_id": story_id,
                "_text_file": str(text_file),
                "_json_path": str(json_file) if json_file else "",
            }
            
            if json_file:
                json_metadata = extract_story_metadata_from_json(json_file)
                if json_metadata:
                    # Merge JSON metadata into story_data
                    story_data.update(json_metadata)
            
            stories_data.append(story_data)
            story_texts.append(text)

    if not stories_data:
        print("No valid stories found", file=__import__("sys").stderr)
        return 1

    print(f"Loaded {len(stories_data)} valid stories")

    # Generate embeddings in batches
    print(f"Generating embeddings using {args.provider} ({args.model})...")
    all_embeddings: List[List[float]] = []

    for i in range(0, len(story_texts), args.batch_size):
        batch = story_texts[i : i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(story_texts) + args.batch_size - 1) // args.batch_size
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} stories)...")

        try:
            batch_embeddings = generate_embeddings(
                batch,
                provider=args.provider,
                model=args.model,
                base_url=args.base_url,
                instruction=args.instruction,
            )
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Error generating embeddings for batch {batch_num}: {e}", file=__import__("sys").stderr)
            return 1

    print(f"Generated {len(all_embeddings)} embeddings")

    # Verify we have the same number of embeddings as stories
    if len(all_embeddings) != len(stories_data):
        print(
            f"Error: Mismatch between stories ({len(stories_data)}) and embeddings ({len(all_embeddings)})",
            file=__import__("sys").stderr,
        )
        return 1

    # Save embeddings to TSV
    embeddings_path = args.output_dir / args.embeddings_file
    print(f"Saving embeddings to {embeddings_path}...")
    save_embeddings_tsv(all_embeddings, embeddings_path)

    # Save metadata to TSV
    metadata_path = args.output_dir / args.metadata_file
    print(f"Saving metadata to {metadata_path}...")
    save_metadata_tsv(stories_data, metadata_path, csv_metadata_map)

    print("Done!")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Metadata: {metadata_path}")
    print(f"  Total stories processed: {len(stories_data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
