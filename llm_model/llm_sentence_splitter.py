#!/usr/bin/env python3
"""
LLM-based sentence splitter using LangChain and Ollama.

This module provides a sentence splitting service that uses a large language
model (default: qwen3:8b) to intelligently split text into sentences, handling
complex cases like dialogue, nested quotes, and multilingual text.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


@dataclass(frozen=True)
class LLMSentenceSplitterConfig:
    """Configuration for LLM-based sentence splitter."""

    model: str = "qwen3:8b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0  # Deterministic for sentence splitting
    num_ctx: int = 8192  # Context window
    timeout_s: float = 300.0


@dataclass
class SentenceSplitResult:
    """Result of sentence splitting operation."""

    sentences: List[str]
    total_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMSentenceSplitterError(RuntimeError):
    """Raised when sentence splitting fails."""

    pass


class LLMSentenceSplitter:
    """LLM-based sentence splitter using LangChain and Ollama."""

    # System prompt for sentence splitting task
    SYSTEM_PROMPT = """You are an expert in text analysis and semantic sentence segmentation.
Your task is to split text into semantic sentence units based on meaning and grammatical completeness, NOT just punctuation marks.

CRITICAL PRINCIPLE: Split based on semantic completeness (complete thoughts/ideas), not just punctuation. A sentence should be a complete semantic unit that conveys a full meaning.

Guidelines:
1. Semantic Units First: Split at semantic boundaries where a complete thought ends, regardless of punctuation
2. Dialogue Attribution: ALWAYS keep dialogue attribution with its dialogue as ONE sentence
   - CORRECT: "Who shall be my teacher?" the lad asked.
   - CORRECT: "I will go." he said.
   - WRONG: "Who shall be my teacher?" (split incorrectly)
            the lad asked. (split incorrectly)
3. Narrative Flow: Keep narrative continuation together as single units when semantically connected
4. Nested Quotes: Preserve nested quotes and dialogue markers as part of their semantic units
5. Multilingual Support: Handle English, Chinese, Japanese, and other languages using semantic principles
6. Abbreviations & Decimals: Don't split at abbreviations (Mr., Dr., etc.) or decimals (3.14) - they are part of their semantic units
7. Compound Thoughts: Split compound sentences only when they contain distinct semantic ideas

Example Splits:

Example 1 (Dialogue with attribution):
Input: "My son, go and complete your education." "Who shall be my teacher?" the lad asked. "Go to Takkasila."
Output: ["My son, go and complete your education.", "Who shall be my teacher?" the lad asked., "Go to Takkasila."]
Note: "the lad asked" stays with the dialogue it attributes.

Example 2 (Chinese dialogue):
Input: "爹爹，我们拿这粪瓢来舀干天河的水。"小女儿終于揩干了眼泪，瞪着一对小眼睛, 这么天真而又倔强地提议。
Output: ["爹爹，我们拿这粪瓢来舀干天河的水。"小女儿終于揩干了眼泪，瞪着一对小眼睛, 这么天真而又倔强地提议。]
Note: The narrative after dialogue is part of the same semantic unit.

Example 3 (Multiple semantic units):
Input: Once upon a time, there was a king. He had three sons. The eldest was brave.
Output: ["Once upon a time, there was a king.", "He had three sons.", "The eldest was brave."]
Note: Each sentence is a distinct semantic unit.

Example 4 (Complex dialogue):
Input: The King said: "Go and learn." "Who shall be my teacher?" the lad asked. The King replied: "Takkasila."
Output: ["The King said: "Go and learn."", "Who shall be my teacher?" the lad asked., "The King replied: "Takkasila.""]

Example 5 (Japanese dialogue):
Input: 「ドンブラコッコ、スッコッコ。\nドンブラコッコ、スッコッコ。」\nと流ながれて来きました。
Output: ["「ドンブラコッコ、スッコッコ。\nドンブラコッコ、スッコッコ。」\nと流ながれて来きました。"]
Note: The narrative "と流ながれて来きました" (flowed along) is semantically connected to the dialogue.

Example 6 (Dialogue with multiple speakers):
Input: "Hello!" she said. "How are you?" he replied. "I'm fine, thank you." she answered.
Output: ["Hello!" she said., "How are you?" he replied., "I'm fine, thank you." she answered.]
Note: Each dialogue-attribution pair is a complete semantic unit.

Example 7 (Dialogue within narrative):
Input: He walked into the room. "Where is everyone?" he asked. The room was empty.
Output: ["He walked into the room.", "Where is everyone?" he asked., "The room was empty."]
Note: Narrative sentences are separate from dialogue, but dialogue attribution stays with dialogue.

Return only a valid JSON array of strings, no additional text or explanation."""

    USER_PROMPT_TEMPLATE = """Split the following text into semantic sentence units.
Split based on complete semantic meaning, not just punctuation.

Text to split:
{text}

Return format (JSON array):
["sentence 1", "sentence 2", "sentence 3", ...]"""

    def __init__(self, config: Optional[LLMSentenceSplitterConfig] = None):
        """Initialize the sentence splitter.

        Args:
            config: Configuration for the splitter. Uses defaults if None.
        """
        self.config = config or LLMSentenceSplitterConfig()
        self._llm: Optional[ChatOllama] = None

    @property
    def llm(self) -> ChatOllama:
        """Lazy initialization of the LLM client."""
        if self._llm is None:
            self._llm = ChatOllama(
                model=self.config.model,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                num_ctx=self.config.num_ctx,
                timeout=self.config.timeout_s,
            )
        return self._llm

    def split(self, text: str, language: Optional[str] = None) -> SentenceSplitResult:
        """Split text into sentences using LLM.

        Args:
            text: Input text to split.
            language: Optional language hint (e.g., "en", "zh", "ja").

        Returns:
            SentenceSplitResult with split sentences and metadata.

        Raises:
            LLMSentenceSplitterError: If splitting fails.
        """
        if not isinstance(text, str) or not text.strip():
            return SentenceSplitResult(sentences=[], total_count=0)

        try:
            # Prepare messages
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=self.USER_PROMPT_TEMPLATE.format(text=text)),
            ]

            # Get response from LLM
            response = self.llm.invoke(messages)

            # Parse JSON response
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

            # Parse JSON
            try:
                sentences_data = json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from response
                sentences_data = self._extract_json_from_response(content)

            if not isinstance(sentences_data, list):
                raise LLMSentenceSplitterError(
                    f"Expected JSON array, got {type(sentences_data)}: {content[:200]}"
                )

            # Extract sentences
            sentences = [str(s) for s in sentences_data if s]
            sentences = [s.strip() for s in sentences if s.strip()]

            metadata = {
                "model": self.config.model,
                "language": language,
                "original_length": len(text),
                "sentence_count": len(sentences),
            }

            return SentenceSplitResult(
                sentences=sentences, total_count=len(sentences), metadata=metadata
            )

        except Exception as e:
            raise LLMSentenceSplitterError(f"Failed to split sentences: {e}") from e

    def _extract_json_from_response(self, content: str) -> List[str]:
        """Extract JSON array from potentially malformed response.

        Args:
            content: Raw response content.

        Returns:
            List of sentences.

        Raises:
            LLMSentenceSplitterError: If JSON cannot be extracted.
        """
        # Try to find JSON array in response
        import re

        # Look for JSON array pattern
        json_pattern = r"\[(.*?)\]"
        matches = re.findall(json_pattern, content, re.DOTALL)

        if matches:
            try:
                # Try to parse the first match as JSON
                json_str = "[" + matches[0] + "]"
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Fallback: try to extract quoted strings
        string_pattern = r'["\']([^"\']+)["\']'
        matches = re.findall(string_pattern, content)
        if matches:
            return matches

        raise LLMSentenceSplitterError(f"Could not extract JSON from response: {content[:500]}")

    def split_file(
        self,
        input_path: Path | str,
        output_path: Optional[Path | str] = None,
        language: Optional[str] = None,
    ) -> SentenceSplitResult:
        """Split sentences from a file.

        Args:
            input_path: Path to input text file.
            output_path: Optional path to output file. If None, generates from input_path.
            language: Optional language hint.

        Returns:
            SentenceSplitResult with split sentences.

        Raises:
            LLMSentenceSplitterError: If file operations fail.
        """
        input_file = Path(input_path)

        if not input_file.exists():
            raise LLMSentenceSplitterError(f"Input file not found: {input_path}")

        try:
            # Read input file
            text = input_file.read_text(encoding="utf-8")

            # Split sentences
            result = self.split(text, language=language)

            # Write output if requested
            if output_path is not None:
                output_file = Path(output_path)
                self._write_output(result, output_file)

            return result

        except Exception as e:
            raise LLMSentenceSplitterError(f"Failed to process file {input_path}: {e}") from e

    def _write_output(self, result: SentenceSplitResult, output_path: Path) -> None:
        """Write split sentences to output file.

        Args:
            result: SentenceSplitResult to write.
            output_path: Path to output file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            for i, sentence in enumerate(result.sentences, 1):
                f.write(f"{i}. {sentence}\n")

        print(f"✓ Successfully split {result.total_count} sentences")
        print(f"  Output: {output_path}")


def main() -> int:
    """CLI entry point for LLM sentence splitter."""
    import argparse

    parser = argparse.ArgumentParser(
        description="LLM-based sentence splitter using LangChain and Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split a text file
  python llm_sentence_splitter.py input.txt

  # Specify output file
  python llm_sentence_splitter.py input.txt -o output.txt

  # Use different model
  python llm_sentence_splitter.py input.txt --model qwen2.5:7b

  # Specify language hint
  python llm_sentence_splitter.py input.txt --language zh
        """,
    )

    parser.add_argument("input", type=str, help="Input text file path")
    parser.add_argument("-o", "--output", type=str, help="Output file path (optional)")
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3:8b",
        help="Ollama model to use (default: qwen3:8b)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--language",
        type=str,
        help="Language hint (e.g., en, zh, ja) for better splitting",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for generation (default: 0.0 for deterministic)",
    )

    args = parser.parse_args()

    try:
        # Create config
        config = LLMSentenceSplitterConfig(
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
        )

        # Create splitter
        splitter = LLMSentenceSplitter(config=config)

        # Process file
        result = splitter.split_file(
            input_path=args.input,
            output_path=args.output,
            language=args.language,
        )

        print(f"\n✓ Successfully split {result.total_count} sentences")
        print(f"  Model: {result.metadata['model']}")
        if result.metadata.get("language"):
            print(f"  Language: {result.metadata['language']}")

        return 0

    except LLMSentenceSplitterError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
