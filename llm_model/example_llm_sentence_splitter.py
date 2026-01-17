#!/usr/bin/env python3
"""
Example usage of LLM-based sentence splitter.

This script demonstrates how to use the LLMSentenceSplitter class
programmatically.
"""

from llm_model.llm_sentence_splitter import (
    LLMSentenceSplitter,
    LLMSentenceSplitterConfig,
)


def example_basic_usage():
    """Basic usage example."""
    print("=== Example 1: Basic Usage ===")

    # Create splitter with default config (qwen3:8b)
    splitter = LLMSentenceSplitter()

    # Test text with dialogue
    text = '''When he came to years of discretion, and had attained the measure of sixteen years, the King said to him:
"My son, go and complete your education."
"Who shall be my teacher?" the lad asked.'''

    # Split sentences
    result = splitter.split(text, language="en")

    print(f"Split {result.total_count} sentences:")
    for i, sentence in enumerate(result.sentences, 1):
        print(f"{i}. {sentence}")

    print(f"\nMetadata: {result.metadata}")


def example_custom_config():
    """Example with custom configuration."""
    print("\n=== Example 2: Custom Configuration ===")

    # Create custom config
    config = LLMSentenceSplitterConfig(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.0,  # Deterministic
        num_ctx=8192,
    )

    # Create splitter with custom config
    splitter = LLMSentenceSplitter(config=config)

    # Test text
    text = '"爹爹，我们拿这粪瓢来舀干天河的水。"小女儿終于揩干了眼泪，瞪着一对小眼睛, 这么天真而又倔强地提议。'

    # Split sentences
    result = splitter.split(text, language="zh")

    print(f"Split {result.total_count} sentences:")
    for i, sentence in enumerate(result.sentences, 1):
        print(f"{i}. {sentence}")


def example_chinese_text():
    """Example with Chinese text."""
    print("\n=== Example 3: Chinese Text ===")

    splitter = LLMSentenceSplitter()

    text = """相传织女是天帝的孙女，或说是王母娘娘的外孙女，这都用不着去管它了。
总之，是有这么一个仙女，住在银河的东边，用了一种神奇的丝，在织布机上织出了层层叠叠的美丽云彩。
随着时间和季节的不同而变幻它们的颜色，叫做"天衣"，意思就是给天做的衣裳。"""

    result = splitter.split(text, language="zh")

    print(f"Split {result.total_count} sentences:")
    for i, sentence in enumerate(result.sentences, 1):
        print(f"{i}. {sentence}")


def example_japanese_text():
    """Example with Japanese text."""
    print("\n=== Example 4: Japanese Text ===")

    splitter = LLMSentenceSplitter()

    text = """むかし、むかし、あるところに、おじいさんとおばあさんがありました。
まいにち、おじいさんは山へしば刈かりに、おばあさんは川へ洗濯せんたくに行きました。
ある日、おばあさんが、川のそばで、せっせと洗濯せんたくをしていますと、川上かわかみから、大きな桃ももが一つ流ながれて来きました。"""

    result = splitter.split(text, language="ja")

    print(f"Split {result.total_count} sentences:")
    for i, sentence in enumerate(result.sentences, 1):
        print(f"{i}. {sentence}")


def example_file_processing():
    """Example of processing a file."""
    print("\n=== Example 5: File Processing ===")

    splitter = LLMSentenceSplitter()

    # Note: Update this path to an actual file in your project
    input_file = "datasets/IndianTales/texts/EN_020_The_Demon_with_the_Matted_Hair.txt"
    output_file = "example_output_sentences.txt"

    try:
        result = splitter.split_file(
            input_path=input_file,
            output_path=output_file,
            language="en",
        )

        print(f"✓ Successfully processed {input_file}")
        print(f"  Split {result.total_count} sentences")
        print(f"  Output saved to: {output_file}")

    except FileNotFoundError:
        print(f"✗ File not found: {input_file}")
        print("  Please update the path to an actual file in your project")


if __name__ == "__main__":
    print("LLM Sentence Splitter Examples\n")

    try:
        # Run examples
        example_basic_usage()
        example_custom_config()
        example_chinese_text()
        example_japanese_text()
        example_file_processing()

        print("\n✓ All examples completed!")

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("\nMake sure:")
        print("1. Ollama is running (ollama serve)")
        print("2. qwen3:8b model is installed (ollama pull qwen3:8b)")
        print("3. Dependencies are installed (pip install -r requirements.txt)")
