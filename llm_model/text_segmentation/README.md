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

**Important: Boundary Index Definition**

The `reference_boundaries` and `hypothesis_boundaries` parameters use **sentence gap indices**:
- A boundary index `i` indicates a segmentation boundary **between sentence `i` and sentence `i+1`**
- Sentence indices are 0-based (first sentence is index 0, second is index 1, etc.)

**Example:**
For a document with 10 sentences (indices 0-9):
- `reference_boundaries=[2, 5]` means boundaries:
  - Between sentence 2 and sentence 3 (after the 2ed sentence)
  - Between sentence 5 and sentence 6 (after the 5th sentence)
- This results in 3 segments:
  - Segment 1: sentences 0-2 (indices 0, 1, 2)
  - Segment 2: sentences 3-5 (indices 3, 4, 5)
  - Segment 3: sentences 6-9 (indices 6, 7, 8, 9)

```python
sentences = [
    "Sentence 0",  # Index 0
    "Sentence 1",  # Index 1
    "Sentence 2",  # Index 2
    "Sentence 3",  # Index 3  <- boundary here (index 2)
    "Sentence 4",  # Index 4
    "Sentence 5",  # Index 5
    "Sentence 6",  # Index 6  <- boundary here (index 5)
    "Sentence 7",  # Index 7
    "Sentence 8",  # Index 8
    "Sentence 9",  # Index 9
]

# reference_boundaries=[2, 5] means:
# - Boundary between sentence 2 and 3 (gap index 2)
# - Boundary between sentence 5 and 6 (gap index 5)
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

## Visualization

The package includes a non-intrusive visualization module for debugging and validation:

```python
from llm_model.text_segmentation import VisualizableTextSegmenter, SegmentationVisualizer

# Use VisualizableTextSegmenter instead of TextSegmenter
segmenter = VisualizableTextSegmenter(
    embedding_func=embedding_func,
    algorithm="magnetic",
)

result = segmenter.segment(text)
viz_data = segmenter.get_visualization_data()

# Visualize
visualizer = SegmentationVisualizer()
visualizer.plot_similarity_matrix(viz_data["similarity_matrix"])
visualizer.plot_magnetic_signal(
    viz_data["raw_forces"],
    smoothed_b_values=viz_data["smoothed_forces"],
    predicted_boundaries=result.boundaries,
)

# Visualize story segmentation result
visualizer.plot_segmentation_interface(
    result=result,
    sentences=sentences,
    title="Story Segmentation Result",
)
```

See `README_VISUALIZATION.md` for detailed visualization guide and `quick_start_visualization.py` for examples.

## References

This implementation is based on the paper "LLM-Enhanced Semantic Text Segmentation" and follows the development document specifications.
