# Vector Database (ATU + Motif) using `qwen3-embedding:4b`

This module builds a **local** vector database to quickly retrieve the most similar:

- **ATU types** from `docs/ATU_Resources/ATU_types_complete.csv`
- **Motifs (TMI v1.2)** from `docs/Motif/tmi_v.1.2.csv`

It uses:

- **Ollama** for embeddings (model: `qwen3-embedding:4b`)
- **hnswlib** for fast approximate nearest-neighbor search
- **sqlite3** (stdlib) to store document text + metadata

## Why this vector DB choice?

For a single-machine research workflow, `hnswlib + sqlite3` is a good fit:

- **Fast** similarity search (HNSW graph index)
- **Simple** deployment: no server to run, files live in `store/`
- **Large motif list friendly** (46k rows) with low query latency

If you later want multi-user / remote access, we can swap to a server-backed DB (e.g. Qdrant).

For implementation details (architecture, build pipeline, scoring), see:

- [llm_model/vector_database/TECHNICAL.md](llm_model/vector_database/TECHNICAL.md)

## Setup

### Option A: Use your conda env `nlp` (recommended)

All commands below can be run via `conda run -n nlp ...`.

1) Ensure Ollama is running:

```bash
ollama serve
```

2) Pull the embedding model:

```bash
ollama pull qwen3-embedding:4b
```

3) Install Python deps:

```bash
conda run -n nlp pip install -r llm_model/vector_database/requirements.txt
```

If you prefer installing as a project extra:

```bash
conda run -n nlp pip install -e ".[vector-db]"
```

## Build the vector database

This will generate these artifacts under `llm_model/vector_database/store/`:

- `docs.sqlite` (text + metadata)
- `atu_hnsw.bin` (ATU vector index)
- `motif_hnsw.bin` (Motif vector index)
- `meta.json` (dimension + settings)

Command:

```bash
conda run -n nlp python -m llm_model.vector_database.cli build \
  --atu-csv docs/ATU_Resources/ATU_types_complete.csv \
  --motif-csv docs/Motif/tmi_v.1.2.csv \
  --embedding-model qwen3-embedding:4b
```

Notes:

- Building the motif index may take a while because it embeds ~46k rows.
- If you have GPU-enabled Ollama, embedding will be much faster.

## Detect ATU types and motifs from a story

```bash
conda run -n nlp python -m llm_model.vector_database.cli detect \
  --text-file datasets/ChineseTales/texts/孟姜女哭长城.md \
  --embedding-model qwen3-embedding:4b \
  --top-k 10 \
  --atu-min-similarity 0.45 \
  --motif-min-similarity 0.35
```

The output is JSON:

- `atu`: sorted best matches, each with `similarity` and `metadata.atu_number`
- `motifs`: sorted best matches, each with `similarity` and `metadata.code`
- `chunks`: how many chunks the story was split into

## Programmatic API

```python
from llm_model.vector_database import FairyVectorDB, VectorDBPaths
from llm_model.vector_database.db import QueryConfig

from pathlib import Path

db = FairyVectorDB(paths=VectorDBPaths(root_dir=Path("llm_model/vector_database/store")))
db.load()

result = db.detect(
    text="Once upon a time ...",
    config=QueryConfig(
        embedding_model="qwen3-embedding:4b",
        ollama_base_url="http://localhost:11434",
    ),
)
```

## Tuning

- `--atu-min-similarity` / `--motif-min-similarity`: controls strictness.
  - If you get too many irrelevant results, increase them.
  - If you miss obvious matches, decrease them.
- `--top-k`: controls how many neighbors are considered per chunk.
- `--max-chars`/`--overlap`: chunking affects recall on long stories.
