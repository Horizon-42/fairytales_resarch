# 安装指南 (Installation Guide)

本指南说明如何在新机器上安装和配置项目，确保所有依赖正确安装。

This guide helps you set up the project on a new machine with all dependencies.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Ollama (for local LLM inference) - [Install Ollama](https://ollama.ai/)
- (Optional) Conda (if you prefer conda environments)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd fairytales_resarch
```

## Step 2: Install Python Dependencies

### Option A: Install using pip (Recommended)

```bash
# Install core dependencies for llm_model (includes STAC analyzer)
pip install -r llm_model/requirements.txt

# Or install the package in editable mode (recommended)
pip install -e .
```

### Option B: Install using pyproject.toml

```bash
# This will install core dependencies (requests, python-dotenv)
pip install -e .

# For optional vector database features
pip install -e ".[vector-db]"
```

### Option C: Using Conda

```bash
# Create a new conda environment
conda create -n nlp python=3.9
conda activate nlp

# Install dependencies
pip install -r llm_model/requirements.txt
# Or
pip install -e .
```

## Step 3: Install Backend Dependencies (if using backend)

```bash
pip install -r backend/requirements.txt
```

## Step 4: Install Optional Dependencies

### Text Segmentation Module (optional)

If you need text segmentation features:

```bash
pip install -r llm_model/text_segmentation/requirements.txt
```

### Vector Database (optional)

If you need vector database features:

```bash
pip install -r llm_model/vector_database/requirements.txt
# Or use the optional dependency
pip install -e ".[vector-db]"
```

## Step 5: Set Up Ollama (for local LLM)

1. Install Ollama: https://ollama.ai/
2. Start Ollama service
3. Download required models:

```bash
# LLM model for chat/JSON generation
ollama pull qwen3:8b

# Embedding model (optional, for embeddings and segmentation)
ollama pull qwen3-embedding:4b
```

## Step 6: Environment Variables (Optional)

Create a `.env` file in the repository root for Gemini API (if using):

```bash
# Copy example if available
cp .env.example .env

# Edit .env and add:
# LLM_PROVIDER=gemini  # or "ollama" for local
# GEMINI_API_KEY=your_api_key_here
# GEMINI_MODEL=your_model_name
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen3:8b
```

## Step 7: Verify Installation

### Test STAC Analyzer

```bash
python -m llm_model.auto_stac_cli --help
```

### Test Sentence Analysis

```bash
python -m llm_model.sentence_analysis.cli --help
```

### Test Backend (if installed)

```bash
python backend/smoke_test.py
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError: No module named 'llm_model'`:

```bash
# Make sure you're in the repository root
cd /path/to/fairytales_resarch

# Install in editable mode
pip install -e .
```

### Missing Dependencies

If you get import errors for specific modules:

1. Check which module is missing
2. Install the corresponding requirements file:
   - Core: `llm_model/requirements.txt`
   - Backend: `backend/requirements.txt`
   - Text segmentation: `llm_model/text_segmentation/requirements.txt`
   - Vector DB: `llm_model/vector_database/requirements.txt`

### Ollama Connection Issues

If Ollama is not responding:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Python Version

Ensure you're using Python 3.9 or higher:

```bash
python --version  # Should be 3.9+
```

## Quick Start

After installation, you can immediately use the STAC analyzer:

```bash
# Analyze a single sentence
python -m llm_model.auto_stac_cli \
  --sentence "王子来到了森林" \
  --no-context

# Analyze a whole story
python -m llm_model.auto_stac_cli \
  --story-file path/to/story.txt \
  --output result.json
```

## Project Structure

```
fairytales_resarch/
├── llm_model/              # Core LLM modules
│   ├── requirements.txt    # Core dependencies (requests, python-dotenv)
│   ├── stac_analyzer/      # STAC analysis module
│   ├── sentence_analysis/  # Sentence analysis module
│   └── ...
├── backend/                # FastAPI backend
│   └── requirements.txt    # Backend dependencies
├── pre_data_process/        # Preprocessing utilities (sentence_splitter)
├── pyproject.toml          # Project configuration
└── README.md               # Main project README
```

## Dependencies Summary

### Core Dependencies (Required)
- `requests>=2.32.0` - HTTP client for Ollama/Gemini API
- `python-dotenv>=1.0.0` - Environment variable loading

### Backend Dependencies (if using backend)
- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.30.0`
- `pydantic>=2.8.0`
- `numpy>=1.24.0`
- `hnswlib>=0.8.0`

### Optional Dependencies
- Text segmentation: `numpy`, `scipy`, `networkx`, `scikit-learn`, `matplotlib`, `seaborn`
- Vector database: `numpy`, `hnswlib`, `tqdm`

All dependencies are specified in their respective `requirements.txt` files.
