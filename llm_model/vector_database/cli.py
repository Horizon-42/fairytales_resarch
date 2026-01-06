from __future__ import annotations

import argparse
import json
from pathlib import Path

from .csv_sources import SourcePaths
from .db import BuildConfig, FairyVectorDB, QueryConfig
from .paths import VectorDBPaths
from .text_chunking import ChunkingConfig


def _read_text(text_file: str | None, text: str | None) -> str:
    if text_file:
        return Path(text_file).read_text(encoding="utf-8")
    return text or ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m llm_model.vector_database.cli",
        description="Build and query a local vector database for ATU types and motifs (TMI).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build vector DB from ATU + Motif CSVs")
    p_build.add_argument(
        "--atu-csv",
        default="docs/ATU_Resources/ATU_types_complete.csv",
        help="Path to ATU_types_complete.csv",
    )
    p_build.add_argument(
        "--motif-csv",
        default="docs/Motif/tmi_v.1.2.csv",
        help="Path to tmi_v.1.2.csv",
    )
    p_build.add_argument(
        "--store-dir",
        default=str(Path(__file__).resolve().parent / "store"),
        help="Directory to write the local vector DB artifacts",
    )
    p_build.add_argument(
        "--ollama-base-url",
        default="http://localhost:11434",
        help="Ollama base URL",
    )
    p_build.add_argument(
        "--embedding-model",
        default="qwen3-embedding:4b",
        help="Embedding model name (Ollama)",
    )
    p_build.add_argument(
        "--embed-batch-size",
        type=int,
        default=512,
        help="Embedding batch size sent to Ollama",
    )

    p_detect = sub.add_parser("detect", help="Detect likely ATU types and motifs in a story")
    p_detect.add_argument(
        "--store-dir",
        default=str(Path(__file__).resolve().parent / "store"),
        help="Directory containing the built vector DB artifacts",
    )
    p_detect.add_argument("--text-file", default=None, help="Path to a UTF-8 text/markdown file")
    p_detect.add_argument("--text", default=None, help="Inline story text")
    p_detect.add_argument(
        "--ollama-base-url",
        default="http://localhost:11434",
        help="Ollama base URL",
    )
    p_detect.add_argument(
        "--embedding-model",
        default="qwen3-embedding:4b",
        help="Embedding model name (Ollama)",
    )
    p_detect.add_argument("--top-k", type=int, default=10, help="Top-k neighbors per chunk")
    p_detect.add_argument(
        "--atu-min-similarity",
        type=float,
        default=0.45,
        help="Minimum cosine similarity to keep an ATU match",
    )
    p_detect.add_argument(
        "--motif-min-similarity",
        type=float,
        default=0.35,
        help="Minimum cosine similarity to keep a motif match",
    )
    p_detect.add_argument("--max-chars", type=int, default=1200, help="Chunk size")
    p_detect.add_argument("--overlap", type=int, default=120, help="Chunk overlap")

    args = parser.parse_args(argv)

    if args.cmd == "build":
        db = FairyVectorDB(paths=VectorDBPaths(root_dir=Path(args.store_dir)))
        db.build_from_csvs(
            sources=SourcePaths(atu_csv=Path(args.atu_csv), motif_csv=Path(args.motif_csv)),
            config=BuildConfig(
                ollama_base_url=args.ollama_base_url,
                embedding_model=args.embedding_model,
                embed_batch_size=int(args.embed_batch_size),
            ),
        )
        print(f"Built vector DB at: {args.store_dir}")
        return 0

    if args.cmd == "detect":
        text = _read_text(args.text_file, args.text)
        db = FairyVectorDB(paths=VectorDBPaths(root_dir=Path(args.store_dir)))
        db.load()
        result = db.detect(
            text=text,
            config=QueryConfig(
                ollama_base_url=args.ollama_base_url,
                embedding_model=args.embedding_model,
                top_k=int(args.top_k),
                atu_min_similarity=float(args.atu_min_similarity),
                motif_min_similarity=float(args.motif_min_similarity),
                chunking=ChunkingConfig(
                    max_chars=int(args.max_chars),
                    overlap=int(args.overlap),
                ),
            ),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    raise RuntimeError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
