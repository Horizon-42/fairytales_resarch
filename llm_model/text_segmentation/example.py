"""Example usage of the text segmentation package."""

from __future__ import annotations

from llm_model.text_segmentation import TextSegmenter
from llm_model.ollama_client import embed


def main():
    """Example usage of TextSegmenter."""
    
    # Define embedding function using Ollama
    def embedding_func(texts):
        """Get embeddings from Ollama."""
        return embed(
            base_url="http://localhost:11434",
            model="nomic-embed-text",  # or your preferred embedding model
            inputs=texts,
        )
    
    # Example 1: Using Magnetic Clustering
    print("Example 1: Magnetic Clustering")
    print("=" * 50)
    
    segmenter_magnetic = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="magnetic",
        embedding_model="nomic-embed-text",
        window_size=3,
        filter_width=2.0,
    )
    
    text1 = """
    Once upon a time, there was a young prince. He lived in a beautiful castle.
    The prince was known for his kindness. One day, he met a mysterious stranger.
    The stranger told him about a hidden treasure. The prince decided to search for it.
    After many adventures, he found the treasure. He returned home as a hero.
    """
    
    result1 = segmenter_magnetic.segment(text1, document_id="example_001")
    print(f"Found {len(result1.segments)} segments")
    for seg in result1.segments:
        print(f"\nSegment {seg['segment_id']}:")
        print(f"  Sentences {seg['start_sentence_idx']}-{seg['end_sentence_idx']}")
        print(f"  Text: {seg['text'][:100]}...")
    
    # Example 2: Using GraphSegSM
    print("\n\nExample 2: GraphSegSM")
    print("=" * 50)
    
    segmenter_graph = TextSegmenter(
        embedding_func=embedding_func,
        algorithm="graph",
        embedding_model="nomic-embed-text",
        threshold=0.7,
        min_seg_size=3,
    )
    
    text2 = """
    The first topic discusses machine learning. It covers neural networks and deep learning.
    Neural networks are powerful tools. Deep learning has revolutionized AI.
    The second topic is about natural language processing. NLP involves text analysis.
    Text analysis requires sophisticated algorithms. These algorithms process human language.
    """
    
    result2 = segmenter_graph.segment(text2, document_id="example_002")
    print(f"Found {len(result2.segments)} segments")
    for seg in result2.segments:
        print(f"\nSegment {seg['segment_id']}:")
        print(f"  Sentences {seg['start_sentence_idx']}-{seg['end_sentence_idx']}")
        print(f"  Text: {seg['text'][:100]}...")
    
    # Example 3: With evaluation
    print("\n\nExample 3: With Evaluation")
    print("=" * 50)
    
    sentences = [
        "First sentence of topic A.",
        "Second sentence of topic A.",
        "Third sentence of topic A.",
        "First sentence of topic B.",
        "Second sentence of topic B.",
        "Third sentence of topic B.",
    ]
    
    # Reference boundaries (after sentences 2 and 5)
    ref_boundaries = [2, 5]
    
    result3 = segmenter_magnetic.segment(
        text="",
        sentences=sentences,
        document_id="example_003",
        reference_boundaries=ref_boundaries,
    )
    
    print(f"Evaluation score: {result3.meta['evaluation_score']:.3f}")
    print(f"Predicted boundaries: {result3.boundaries}")
    print(f"Reference boundaries: {ref_boundaries}")
    
    # Example 4: Output to JSON
    print("\n\nExample 4: JSON Output")
    print("=" * 50)
    
    import json
    output_dict = result3.to_dict()
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
