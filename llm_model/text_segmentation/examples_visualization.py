"""Example usage of the visualization module."""

from __future__ import annotations

import numpy as np

from llm_model.text_segmentation import (
    VisualizableTextSegmenter,
    SegmentationVisualizer,
    visualize_segmentation_result,
)
from llm_model.ollama_client import embed


def example_basic_visualization():
    """Example 1: Basic visualization workflow."""
    print("Example 1: Basic Visualization Workflow")
    print("=" * 60)

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
        embedding_model="nomic-embed-text",
        window_size=3,
        filter_width=2.0,
    )

    # Segment text
    text = """
    Once upon a time, there was a young prince. He lived in a beautiful castle.
    The prince was known for his kindness. One day, he met a mysterious stranger.
    The stranger told him about a hidden treasure. The prince decided to search for it.
    After many adventures, he found the treasure. He returned home as a hero.
    The kingdom celebrated his return. Everyone lived happily ever after.
    """

    result = segmenter.segment(text, document_id="example_vis_001")

    # Get visualization data
    viz_data = segmenter.get_visualization_data()

    # Create visualizer
    visualizer = SegmentationVisualizer()

    # Visualize similarity matrix
    if "similarity_matrix" in viz_data:
        visualizer.plot_similarity_matrix(
            viz_data["similarity_matrix"],
            title="Similarity Matrix - Example 1",
        )

    # Visualize magnetic signal
    if "raw_forces" in viz_data:
        visualizer.plot_magnetic_signal(
            viz_data["raw_forces"],
            smoothed_b_values=viz_data.get("smoothed_forces"),
            predicted_boundaries=result.boundaries,
            title="Magnetic Signal - Example 1",
        )


def example_with_reference_boundaries():
    """Example 2: Visualization with reference boundaries for evaluation."""
    print("\nExample 2: Visualization with Reference Boundaries")
    print("=" * 60)

    def embedding_func(texts):
        return embed(
            base_url="http://localhost:11434",
            model="nomic-embed-text",
            inputs=texts,
        )

    segmenter = VisualizableTextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
    )

    sentences = [
        "First topic sentence one.",
        "First topic sentence two.",
        "First topic sentence three.",
        "Second topic sentence one.",
        "Second topic sentence two.",
        "Second topic sentence three.",
        "Third topic sentence one.",
        "Third topic sentence two.",
    ]

    # Reference boundaries (after sentences 2 and 5)
    ref_boundaries = [2, 5]

    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="example_vis_002",
        reference_boundaries=ref_boundaries,
    )

    viz_data = segmenter.get_visualization_data()
    visualizer = SegmentationVisualizer()

    # Plot similarity matrix with reference boundaries
    if "similarity_matrix" in viz_data:
        visualizer.plot_similarity_matrix(
            viz_data["similarity_matrix"],
            ground_truth_boundaries=ref_boundaries,
            title="Similarity Matrix with Ground Truth Boundaries",
        )

    # Plot segmentation comparison
    doc_len = len(sentences)
    visualizer.plot_segmentation_comparison(
        doc_len=doc_len,
        true_boundaries=ref_boundaries,
        pred_boundaries=result.boundaries,
        metric_score=result.meta.get("evaluation_score"),
        title="Segmentation Comparison - Example 2",
    )


def example_graph_visualization():
    """Example 3: GraphSegSM visualization."""
    print("\nExample 3: GraphSegSM Visualization")
    print("=" * 60)

    def embedding_func(texts):
        return embed(
            base_url="http://localhost:11434",
            model="nomic-embed-text",
            inputs=texts,
        )

    segmenter = VisualizableTextSegmenter(
        embedding_func=embedding_func,
        algorithm="graph",
        threshold=0.7,
        min_seg_size=3,
    )

    sentences = [
        "Machine learning is a subset of artificial intelligence.",
        "Neural networks are powerful machine learning models.",
        "Deep learning uses multiple layers of neural networks.",
        "Natural language processing handles human language.",
        "Text analysis requires sophisticated NLP algorithms.",
        "These algorithms process and understand text.",
    ]

    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="example_vis_003",
    )

    viz_data = segmenter.get_visualization_data()
    visualizer = SegmentationVisualizer()

    # Plot graph structure
    if "similarity_matrix" in viz_data and "threshold" in viz_data:
        visualizer.plot_graph_structure(
            viz_data["similarity_matrix"],
            threshold=viz_data["threshold"],
            segment_window=(0, min(50, len(sentences))),
            title="GraphSegSM Structure - Example 3",
        )


def example_convenience_function():
    """Example 4: Using the convenience visualization function."""
    print("\nExample 4: Convenience Visualization Function")
    print("=" * 60)

    def embedding_func(texts):
        return embed(
            base_url="http://localhost:11434",
            model="nomic-embed-text",
            inputs=texts,
        )

    segmenter = VisualizableTextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
    )

    sentences = [
        "Topic A sentence 1.",
        "Topic A sentence 2.",
        "Topic A sentence 3.",
        "Topic B sentence 1.",
        "Topic B sentence 2.",
        "Topic B sentence 3.",
    ]

    ref_boundaries = [2, 5]
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="example_vis_004",
        reference_boundaries=ref_boundaries,
    )

    viz_data = segmenter.get_visualization_data()

    # Use convenience function
    visualize_segmentation_result(
        result=result,
        similarity_matrix=viz_data.get("similarity_matrix"),
        reference_boundaries=ref_boundaries,
        magnetic_data={
            "raw_forces": viz_data.get("raw_forces"),
            "smoothed_forces": viz_data.get("smoothed_forces"),
        },
    )


def example_save_figures():
    """Example 5: Save figures to disk."""
    print("\nExample 5: Save Figures to Disk")
    print("=" * 60)

    def embedding_func(texts):
        return embed(
            base_url="http://localhost:11434",
            model="nomic-embed-text",
            inputs=texts,
        )

    segmenter = VisualizableTextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
    )

    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    result = segmenter.segment(text, document_id="example_vis_005")

    viz_data = segmenter.get_visualization_data()
    visualizer = SegmentationVisualizer()

    # Save figures
    import os
    save_dir = "viz_output"
    os.makedirs(save_dir, exist_ok=True)

    if "similarity_matrix" in viz_data:
        visualizer.plot_similarity_matrix(
            viz_data["similarity_matrix"],
            title="Saved Similarity Matrix",
            save_path=os.path.join(save_dir, "similarity_matrix.png"),
        )

    if "raw_forces" in viz_data:
        visualizer.plot_magnetic_signal(
            viz_data["raw_forces"],
            smoothed_b_values=viz_data.get("smoothed_forces"),
            predicted_boundaries=result.boundaries,
            title="Saved Magnetic Signal",
            save_path=os.path.join(save_dir, "magnetic_signal.png"),
        )

    print(f"Figures saved to {save_dir}/")


if __name__ == "__main__":
    # Run examples (comment out ones that require Ollama)
    print("Visualization Examples")
    print("=" * 60)
    print("\nNote: These examples require Ollama to be running.")
    print("Uncomment the examples you want to run.\n")

    # example_basic_visualization()
    # example_with_reference_boundaries()
    # example_graph_visualization()
    # example_convenience_function()
    # example_save_figures()

    print("\nTo run examples, uncomment them in the main section.")
