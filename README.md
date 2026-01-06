# Fairytales/Folktales across cultures

## Work Plan
30-Day Distributed Research Plan_ The Digital Silk Road

## Researchs
Resources.md

## Annotation tools
### Setup
Run scripts/setup_npm.sh to setup npm env.
### Install 
cd in to annotation_tools, run annotation_tools/install_deps.sh to download necessary node_modules
### Run
npm run start

## LLM-assisted features (Ollama)
This project can use a local Ollama server to help with annotation.

Required Ollama models (recommended defaults):
- LLM (chat/JSON): `qwen3:8b`
- Embeddings (vector + segmentation hints): `qwen3-embedding:4b`

Download models:
- `ollama pull qwen3:8b`
- `ollama pull qwen3-embedding:4b`

Notes:
- Embeddings are used by:
	- Narrative auto-segmentation mode `Embedding assisted`
	- Motif/ATU retrieval (vector database)
- Narrative auto-segmentation also supports `LLM only` mode (no embeddings needed).

## Annotation Guidance
### Propp_Resoruces
Propp_Resoruces/propp_functions_guide_en.md
### ATU types
ATU_Resources/ATU_types.md
### Motifs
Motif/Motifs_extracted_hierarchy.csv
### Universal Narrative Action Taxonomy
Universal Narrative Action Taxonomy/Universal_Narrative_Action_Taxonomy.md


## Visulization
### Story Ribbons
papers/story_ribbons.pdf

## Backend Service
This backend enable you use qwen3 8b to help you annotate.
### Setup
./backend/start.sh setup
### Run
OLLAMA_MODEL=qwen3:8b OLLAMA_EMBEDDING_MODEL=qwen3-embedding:4b ./backend/start.sh

Environment variables:
- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default: `qwen3:8b`)
- `OLLAMA_EMBEDDING_MODEL` (default: `qwen3-embedding:4b`)

**Make sure Ollama is running locally before starting the backend.**

### Narrative auto-segmentation
In the Narrative tab there is an “Automatic sectioning” helper with two modes:
- `LLM only`: uses the LLM to segment the story (no embeddings).
- `Embedding assisted`: computes adjacent chunk similarity (embeddings) as hints to improve boundaries.

If `Embedding assisted` is selected but the embedding model is not available, the backend will warn on startup and the request will fail with a clear error until you run `ollama pull qwen3-embedding:4b`.

### Vector database (optional, skip build)
Motif/ATU retrieval uses a local vector database stored under:
- Default location: `llm_model/vector_database/store/`

If you already have a prebuilt vector database archive, you can install it to skip the build step.

Prebuilt archive (Google Drive):
- https://drive.google.com/file/d/11Lj0yi6yCTjHfIFPjd28EeeAeGKjQxt-/view?usp=sharing

Expected files in the store directory:
- `docs.sqlite`
- `atu_hnsw.bin`
- `motif_hnsw.bin`
- `meta.json`

Install option A (recommended): extract into the default store folder
1) Download the archive from the link above.
2) Extract it so that the files above end up in `llm_model/vector_database/store/`.
	- If the archive contains a top-level folder (e.g. `store/`), move its contents into `llm_model/vector_database/store/`.

Install option B: extract anywhere and point the backend to it
1) Extract the archive to some directory, for example: `/path/to/vector_db_store/`
2) Start backend with:
	- `VECTOR_DB_DIR=/path/to/vector_db_store ./backend/start.sh`

Quick check
- Once installed, the backend Motif/ATU endpoint should work without rebuilding:
  - `POST /api/detect/motif_atu`