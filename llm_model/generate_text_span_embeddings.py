"""Generate embeddings for text spans from text_spans.csv.

This script reads text spans from post_data_process/text_spans.csv, generates embeddings
for each span, and saves the results to TSV files:
1. embeddings.tsv: Contains all embedding vectors (tab-separated)
2. span_metadata.tsv: Contains metadata (story name, span range, etc.)
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List

from llm_model.embedding_generator import generate_embeddings


def read_text_spans_csv(csv_path: Path) -> List[dict]:
    """Read text spans from CSV file.

    Args:
        csv_path: Path to the text_spans.csv file.

    Returns:
        List of dictionaries containing span data.
    """
    spans = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            spans.append(row)
    return spans


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
    spans: List[dict],
    output_path: Path,
    include_columns: List[str] | None = None,
) -> None:
    """Save span metadata to TSV file.

    Args:
        spans: List of span dictionaries.
        output_path: Path to output TSV file.
        include_columns: List of column names to include. If None, includes:
                         span_name, story_name, start, end, event_id, event_type, time_order
    """
    if include_columns is None:
        include_columns = ["span_name", "story_name", "start", "end", "event_id", "event_type", "time_order"]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=include_columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for span in spans:
            # Create row with span_name as combination of story_name and span range
            row = {col: span.get(col, "") for col in include_columns if col != "span_name"}
            # Add span_name column
            row["span_name"] = create_span_name(
                span.get("story_name", ""),
                span.get("start", ""),
                span.get("end", ""),
            )
            # Reorder to match include_columns
            ordered_row = {col: row.get(col, "") for col in include_columns}
            writer.writerow(ordered_row)


def create_span_name(story_name: str, start: str, end: str) -> str:
    """Create a span identifier from story name and range.

    Args:
        story_name: Name of the story.
        start: Start position of the span.
        end: End position of the span.

    Returns:
        A string identifier like "story_name_start_end".
    """
    return f"{story_name}_{start}_{end}"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for text spans from text_spans.csv"
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "post_data_process" / "text_spans.csv",
        help="Path to input text_spans.csv file",
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
        default="text_span_embeddings.tsv",
        help="Name of the embeddings TSV file",
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        default="text_span_metadata.tsv",
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
        default=100,
        help="Number of texts to process in each batch (default: 100)",
    )
    args = parser.parse_args()

    # Validate input file
    if not args.input_csv.exists():
        print(f"Error: Input file not found: {args.input_csv}", file=__import__("sys").stderr)
        return 1

    # Create output directory if it doesn't exist
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Read spans from CSV
    print(f"Reading text spans from {args.input_csv}...")
    spans = read_text_spans_csv(args.input_csv)
    print(f"Found {len(spans)} text spans")

    if not spans:
        print("No spans found in input file", file=__import__("sys").stderr)
        return 1

    # Extract text column
    texts = [span.get("text", "") for span in spans]
    if not all(texts):
        print("Warning: Some spans have empty text", file=__import__("sys").stderr)

    # Generate embeddings in batches
    print(f"Generating embeddings using {args.provider} ({args.model})...")
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), args.batch_size):
        batch = texts[i : i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(texts) + args.batch_size - 1) // args.batch_size
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")

        try:
            batch_embeddings = generate_embeddings(
                batch,
                provider=args.provider,
                model=args.model,
                base_url=args.base_url,
            )
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Error generating embeddings for batch {batch_num}: {e}", file=__import__("sys").stderr)
            return 1

    print(f"Generated {len(all_embeddings)} embeddings")

    # Verify we have the same number of embeddings as spans
    if len(all_embeddings) != len(spans):
        print(
            f"Error: Mismatch between spans ({len(spans)}) and embeddings ({len(all_embeddings)})",
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
    save_metadata_tsv(spans, metadata_path)

    print("Done!")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
