# Text Segmentation Visualization Guide

This guide explains how to use the non-intrusive visualization module for debugging and validating text segmentation algorithms.

## Overview

The visualization module provides tools to visualize:
1. **Similarity Matrix**: Heatmap showing semantic relationships between sentences
2. **Magnetic Signal**: Force curve for Magnetic Clustering algorithm
3. **Graph Structure**: Network visualization for GraphSegSM algorithm
4. **Segmentation Comparison**: Barcode comparison of predicted vs ground truth boundaries

## Quick Start

### Basic Usage

```python
from llm_model.text_segmentation import (
    VisualizableTextSegmenter,
    SegmentationVisualizer,
)
from llm_model.ollama_client import embed

# Define embedding function
def embedding_func(texts):
    return embed(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
        inputs=texts,
    )

# Create visualizable segmenter
segmenter = VisualizableTextSegmenter(
    embedding_func=embedding_func,
    algorithm="magnetic",
)

# Segment text
text = "Your text here..."
result = segmenter.segment(text, document_id="doc_001")

# Get visualization data
viz_data = segmenter.get_visualization_data()

# Create visualizer
visualizer = SegmentationVisualizer()

# Visualize similarity matrix
if "similarity_matrix" in viz_data:
    visualizer.plot_similarity_matrix(
        viz_data["similarity_matrix"],
        title="Similarity Matrix",
    )

# Visualize magnetic signal (for Magnetic Clustering)
if "raw_forces" in viz_data:
    visualizer.plot_magnetic_signal(
        viz_data["raw_forces"],
        smoothed_b_values=viz_data.get("smoothed_forces"),
        predicted_boundaries=result.boundaries,
    )
```

## Visualization Methods

### 1. Similarity Matrix Heatmap

Visualizes the cosine similarity matrix with optional ground truth boundary overlays.

```python
visualizer.plot_similarity_matrix(
    similarity_matrix=sim_matrix,
    ground_truth_boundaries=[2, 5, 8],  # Optional
    title="Similarity Matrix",
    save_path="similarity.png",  # Optional
)
```

**What to look for:**
- Dark/bright square blocks along the diagonal indicate semantic clusters
- If the matrix looks like "snow" with no block structure, the embedding model or window size may need adjustment

### 2. Magnetic Signal Plot

Visualizes the magnetic force signal for debugging Magnetic Clustering.

```python
visualizer.plot_magnetic_signal(
    b_values=raw_forces,
    smoothed_b_values=smoothed_forces,  # Optional
    predicted_boundaries=[2, 5],  # Optional
    title="Magnetic Signal Analysis",
)
```

**What to look for:**
- The curve should show alternating positive/negative regions
- Smoothing should reduce high-frequency noise
- Red vertical lines (boundaries) should align with zero-crossings from negative to positive

### 3. Graph Structure Visualization

Visualizes the semantic graph structure for GraphSegSM.

```python
visualizer.plot_graph_structure(
    similarity_matrix=sim_matrix,
    threshold=0.7,
    segment_window=(0, 50),  # Which sentences to visualize
    title="Graph Structure",
)
```

**What to look for:**
- Adjacency matrix should show block-like connections along diagonal
- If too many connections (all black) or too few (all white), adjust threshold
- Network graph should show semantic clusters as tight cliques

### 4. Segmentation Comparison Barcode

Compares predicted boundaries with ground truth.

```python
visualizer.plot_segmentation_comparison(
    doc_len=20,
    true_boundaries=[5, 10, 15],
    pred_boundaries=[5, 11, 15],
    metric_score=0.92,  # Optional
    tolerance=2,
    title="Segmentation Comparison",
)
```

**Color coding:**
- **Green**: Exact matches
- **Orange**: Near misses (within tolerance)
- **Red**: False positives

## Convenience Function

For quick visualization of complete results:

```python
from llm_model.text_segmentation import visualize_segmentation_result

visualize_segmentation_result(
    result=segmentation_result,
    similarity_matrix=viz_data.get("similarity_matrix"),
    reference_boundaries=[2, 5],
    magnetic_data={
        "raw_forces": viz_data.get("raw_forces"),
        "smoothed_forces": viz_data.get("smoothed_forces"),
    },
    save_dir="output/",  # Optional: save all figures
)
```

## Using Visualization Hooks

The `VisualizableTextSegmenter` is a wrapper that collects intermediate data without modifying core algorithms:

```python
# Instead of TextSegmenter
from llm_model.text_segmentation import VisualizableTextSegmenter

segmenter = VisualizableTextSegmenter(
    embedding_func=embedding_func,
    algorithm="magnetic",
)

result = segmenter.segment(text)
viz_data = segmenter.get_visualization_data()  # Get collected data
```

## Development Workflow

### 1. Initial Development: Similarity Matrix

Start by visualizing the similarity matrix to verify embedding quality:

```python
segmenter = VisualizableTextSegmenter(...)
result = segmenter.segment(text)
viz_data = segmenter.get_visualization_data()

visualizer.plot_similarity_matrix(
    viz_data["similarity_matrix"],
)
```

**Action:** Adjust `context_window` until you see clear block structures.

### 2. Debugging Magnetic Clustering

Visualize the magnetic signal to tune parameters:

```python
visualizer.plot_magnetic_signal(
    viz_data["raw_forces"],
    viz_data["smoothed_forces"],
    result.boundaries,
)
```

**Action:** Adjust `window_size`, `weights`, and `filter_width` until boundaries align with zero-crossings.

### 3. Debugging GraphSegSM

Visualize the graph structure to tune threshold:

```python
visualizer.plot_graph_structure(
    viz_data["similarity_matrix"],
    threshold=viz_data["threshold"],
)
```

**Action:** Adjust `threshold` until the graph is neither fully connected nor fully disconnected.

### 4. Final Evaluation

Compare predictions with ground truth:

```python
visualizer.plot_segmentation_comparison(
    doc_len=len(sentences),
    true_boundaries=ref_boundaries,
    pred_boundaries=result.boundaries,
    metric_score=result.meta.get("evaluation_score"),
)
```

## Saving Figures

All visualization methods support saving to file:

```python
visualizer.plot_similarity_matrix(
    matrix,
    save_path="output/similarity.png",
)
```

Or use the convenience function to save all figures:

```python
visualize_segmentation_result(
    result,
    similarity_matrix=matrix,
    save_dir="output/",
)
```

## Non-Intrusive Design

The visualization module is designed to be **non-intrusive**:

1. **No core algorithm modifications**: Core algorithms (`MagneticClustering`, `GraphSegSM`) remain unchanged
2. **Optional usage**: Visualization is completely optional - use `TextSegmenter` for production
3. **Wrapper classes**: `Visualizable*` classes extend base classes to collect data
4. **Independent module**: Visualization can be imported separately

## Dependencies

```bash
pip install matplotlib seaborn networkx numpy
```

These are already included in `requirements.txt` for the visualization module.

## Examples

See `examples_visualization.py` for complete working examples.
