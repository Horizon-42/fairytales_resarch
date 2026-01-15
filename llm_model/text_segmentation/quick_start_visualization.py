#!/usr/bin/env python3
"""Quick start example for text segmentation visualization.

This example demonstrates the non-intrusive visualization module
for debugging and validating text segmentation algorithms.
"""

from llm_model.text_segmentation import (
    VisualizableTextSegmenter,
    SegmentationVisualizer,
    visualize_segmentation_result,
)
from llm_model.ollama_client import embed


def main():
    """Main example function."""
    
    print("Text Segmentation Visualization - Quick Start")
    print("=" * 60)
    
    # Step 1: Define embedding function
    def embedding_func(texts):
        """Get embeddings from Ollama."""
        return embed(
            base_url="http://localhost:11434",
            model="nomic-embed-text",  # or your preferred model
            inputs=texts,
        )
    
    # Step 2: Create visualizable segmenter
    print("\n1. Creating visualizable segmenter...")
    segmenter = VisualizableTextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",  # or "graph"
        embedding_model="nomic-embed-text",
        window_size=3,
        filter_width=2.0,
    )
    
    # Step 3: Prepare text
    print("2. Preparing text...")
    text = """
    Once upon a time, there was a young prince who lived in a beautiful castle.
    The prince was known throughout the kingdom for his kindness and wisdom.
    One day, he received a mysterious letter from a faraway land.
    The letter spoke of a hidden treasure that could save the kingdom.
    Determined to find it, the prince embarked on a long and dangerous journey.
    After many months of travel, he finally reached the treasure's location.
    The treasure turned out to be not gold, but ancient wisdom.
    He returned home and used this wisdom to rule the kingdom justly.
    The kingdom prospered for many years under his wise leadership.
    """
    
    sentences = [
        "First topic sentence one about machine learning.",
        "First topic sentence two about neural networks.",
        "First topic sentence three about deep learning.",
        "Second topic sentence one about natural language processing.",
        "Second topic sentence two about text analysis.",
        "Second topic sentence three about NLP algorithms.",
        "Third topic sentence one about computer vision.",
        "Third topic sentence two about image recognition.",
    ]
    
    # Step 4: Segment text
    print("3. Segmenting text...")
    result = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="example_001",
    )
    
    print(f"   Found {len(result.segments)} segments")
    print(f"   Boundaries: {result.boundaries}")
    
    # Step 5: Get visualization data
    print("4. Collecting visualization data...")
    viz_data = segmenter.get_visualization_data()
    print(f"   Available data: {list(viz_data.keys())}")
    
    # Step 6: Create visualizer
    print("5. Creating visualizer...")
    visualizer = SegmentationVisualizer(figsize=(12, 8))
    
    # Step 7: Visualize similarity matrix
    print("6. Plotting similarity matrix...")
    if "similarity_matrix" in viz_data:
        visualizer.plot_similarity_matrix(
            viz_data["similarity_matrix"],
            title="Similarity Matrix - Example",
        )
    
    # Step 8: Visualize magnetic signal (if using Magnetic Clustering)
    if result.meta["algorithm"] == "magnetic" and "raw_forces" in viz_data:
        print("7. Plotting magnetic signal...")
        visualizer.plot_magnetic_signal(
            viz_data["raw_forces"],
            smoothed_b_values=viz_data.get("smoothed_forces"),
            predicted_boundaries=result.boundaries,
            title="Magnetic Signal Analysis",
        )
    
    # Step 9: Visualize with reference boundaries (optional)
    print("\n8. Visualization with reference boundaries...")
    ref_boundaries = [2, 5]  # Expected boundaries
    
    # Re-segment with reference
    result_with_ref = segmenter.segment(
        text="",
        sentences=sentences,
        document_id="example_002",
        reference_boundaries=ref_boundaries,
    )
    
    doc_len = len(sentences)
    viz_data = segmenter.get_visualization_data()
    
    if "similarity_matrix" in viz_data:
        visualizer.plot_similarity_matrix(
            viz_data["similarity_matrix"],
            ground_truth_boundaries=ref_boundaries,
            title="Similarity Matrix with Ground Truth",
        )
    
    visualizer.plot_segmentation_comparison(
        doc_len=doc_len,
        true_boundaries=ref_boundaries,
        pred_boundaries=result_with_ref.boundaries,
        metric_score=result_with_ref.meta.get("evaluation_score"),
        title="Segmentation Comparison",
    )
    
    # Alternative: Use convenience function
    print("\n9. Using convenience function...")
    visualize_segmentation_result(
        result=result_with_ref,
        similarity_matrix=viz_data.get("similarity_matrix"),
        reference_boundaries=ref_boundaries,
        magnetic_data={
            "raw_forces": viz_data.get("raw_forces"),
            "smoothed_forces": viz_data.get("smoothed_forces"),
        },
    )
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("\nTips:")
    print("- Adjust window_size and filter_width for Magnetic Clustering")
    print("- Adjust threshold for GraphSegSM")
    print("- Check similarity matrix for block structures")
    print("- Verify boundaries align with zero-crossings (Magnetic)")


if __name__ == "__main__":
    main()
