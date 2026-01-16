"""Generate embeddings for story summaries from story_summaries.csv.

This script reads story summaries from story_summaries.csv, generates embeddings
for each summary, and saves the results to TSV files:
1. summary_embeddings.tsv: Contains all summary embedding vectors (tab-separated)
2. summary_metadata.tsv: Contains metadata (story_name, text_file, summary)
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List

from llm_model.embedding_generator import generate_embeddings


def load_summaries_from_csv(csv_path: Path) -> List[dict]:
    """Load story summaries from CSV file.

    Args:
        csv_path: Path to the story_summaries.csv file.

    Returns:
        List of dictionaries containing story_name, text_file, summary.
    """
    summaries: List[dict] = []
    
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=__import__(
            "sys").stderr)
        return summaries
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            story_name = row.get("story_name", "").strip()
            text_file = row.get("text_file", "").strip()
            summary = row.get("summary", "").strip()
            
            if not story_name or not summary:
                continue
            
            summaries.append({
                "story_name": story_name,
                "text_file": text_file,
                "summary": summary,
            })
    
    return summaries


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


def save_metadata_tsv(summaries: List[dict], output_path: Path) -> None:
    """Save summary metadata to TSV file.

    Args:
        summaries: List of dictionaries with story_name, text_file, summary.
        output_path: Path to output TSV file.
    """
    if not summaries:
        return

    fieldnames = ["story_name", "text_file", "summary"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for summary_data in summaries:
            writer.writerow(summary_data)


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).resolve().parents[1]
    
    parser = argparse.ArgumentParser(
        description="Generate embeddings for story summaries from story_summaries.csv"
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=repo_root / "post_data_process" / "story_summaries.csv",
        help="Path to story_summaries.csv file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "post_data_process",
        help="Directory to save output TSV files",
    )
    parser.add_argument(
        "--embeddings-file",
        type=str,
        default="summary_embeddings.tsv",
        help="Name of the embeddings TSV file",
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        default="summary_metadata.tsv",
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
        "--instruction",
        type=str,
        default=os.getenv("EMBEDDING_INSTRUCTION", None),
        help="Optional instruction to prepend to each summary for instruction-based embeddings",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of summaries to process in each batch (default: 100)",
    )
    args = parser.parse_args()

    # Validate input file
    if not args.input_csv.exists():
        print(f"Error: Input CSV file not found: {args.input_csv}", file=__import__(
            "sys").stderr)
        return 1

    # Create output directory if it doesn't exist
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load summaries from CSV
    print(f"Loading summaries from {args.input_csv}...")
    summaries = load_summaries_from_csv(args.input_csv)
    print(f"Found {len(summaries)} summaries")

    if not summaries:
        print("No summaries found in CSV", file=__import__("sys").stderr)
        return 1

    # Extract summary texts
    summary_texts = [s["summary"] for s in summaries]

    # Generate embeddings in batches
    print(f"Generating embeddings using {args.provider} ({args.model})...")
    all_embeddings: List[List[float]] = []

    for i in range(0, len(summary_texts), args.batch_size):
        batch = summary_texts[i: i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(summary_texts) +
                         args.batch_size - 1) // args.batch_size
        print(
            f"Processing batch {batch_num}/{total_batches} ({len(batch)} summaries)...")

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

    # Verify we have the same number of embeddings as summaries
    if len(all_embeddings) != len(summaries):
        print(
            f"Error: Mismatch between summaries ({len(summaries)}) and embeddings ({len(all_embeddings)})",
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
    save_metadata_tsv(summaries, metadata_path)

    print("Done!")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Metadata: {metadata_path}")
    print(f"  Total summaries processed: {len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
