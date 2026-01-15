# LLM-Based Text Segmentation Package

This package implements semantic text segmentation algorithms based on LLM embeddings, as described in the development document. It includes:

- **Magnetic Clustering**: A lightweight algorithm based on "magnetic" attraction
- **GraphSegSM**: A graph-based algorithm using maximal cliques
- **Boundary Segmentation Metric**: Evaluation metric for segmentation quality

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from llm_model.text_segmentation import TextSegmenter
from llm_model.ollama_client import embed

# Define embedding function
def embedding_func(texts):
    return embed(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
        inputs=texts,
    )

# Create segmenter
segmenter = TextSegmenter(
    embedding_func=embedding_func,
    algorithm="magnetic",  # or "graph"
    embedding_model="nomic-embed-text",
)

# Segment text
text = "First paragraph. Second paragraph. Third paragraph."
result = segmenter.segment(text, document_id="doc_001")

# Access results
print(f"Found {len(result.segments)} segments")
for seg in result.segments:
    print(f"Segment {seg['segment_id']}: {seg['text'][:50]}...")
```

## Usage Examples

### Using Magnetic Clustering

```python
from llm_model.text_segmentation import TextSegmenter, SimilarityMatrixBuilder, MagneticClustering

# Custom embedding function
def my_embedding_func(texts):
    # Your embedding logic here
    return embeddings

# Build similarity matrix
builder = SimilarityMatrixBuilder(
    embedding_func=my_embedding_func,
    context_window=2,
)

# Create clustering algorithm
clustering = MagneticClustering(
    similarity_builder=builder,
    window_size=3,
    filter_width=2.0,
)

# Segment sentences
sentences = ["Sentence 1", "Sentence 2", "Sentence 3"]
boundaries = clustering.segment(sentences)
```

### Using GraphSegSM

```python
from llm_model.text_segmentation import GraphSegSM, SimilarityMatrixBuilder

builder = SimilarityMatrixBuilder(embedding_func=my_embedding_func)
graph_seg = GraphSegSM(
    similarity_builder=builder,
    threshold=0.7,
    min_seg_size=3,
)

boundaries = graph_seg.segment(sentences)
```

### Evaluating Segmentation

```python
from llm_model.text_segmentation import BoundarySegmentationMetric

metric = BoundarySegmentationMetric(tolerance=2)
score = metric.calculate(
    reference_boundaries=[2, 5, 8],
    hypothesis_boundaries=[2, 6, 8],
)
print(f"Boundary similarity score: {score}")
```

## Output Format

The segmenter returns a `SegmentationResult` object with the following structure:

```python
{
    "document_id": "doc_001",
    "segments": [
        {
            "segment_id": 1,
            "start_sentence_idx": 0,
            "end_sentence_idx": 5,
            "text": "..."
        },
        ...
    ],
    "meta": {
        "algorithm": "MagneticClustering",
        "embedding_model": "nomic-embed-text",
        "evaluation_score": 0.72
    }
}
```

## Parameters

### Magnetic Clustering
- `window_size`: Size of the window for computing magnetic force (default: 3)
- `weights`: Weight parameters for distances (default: exponential decay)
- `filter_width`: Gaussian filter width for smoothing (default: 2.0)

### GraphSegSM
- `threshold`: Similarity threshold for edge creation (default: 0.7)
- `min_seg_size`: Minimum segment size (default: 3)

### Similarity Matrix Builder
- `context_window`: Number of consecutive sentences for context (default: 2)
- `local_neighborhood`: Only compute similarity within this distance (optional)

## Testing

Run the test suite:

```bash
pytest llm_model/text_segmentation/tests/
```

## References

This implementation is based on the paper "LLM-Enhanced Semantic Text Segmentation" and follows the development document specifications.
