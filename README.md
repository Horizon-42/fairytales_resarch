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