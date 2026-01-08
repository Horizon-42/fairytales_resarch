"""Paragraph + whole-story summarization via Ollama.

This module powers the Summaries tab "Auto Summary" button.

Contract (frontend-facing intent):
- Split the source text into non-empty paragraphs by line (same as frontend).
- Generate per-paragraph summaries.
- Then generate a whole-story summary *based on the per-paragraph summaries*.
- If the source language is English, produce English-only summaries.
- Otherwise, produce bilingual summaries: source language + English.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .json_utils import loads_strict_json
from .llm_router import LLMConfig, LLMRouterError, chat


@dataclass(frozen=True)
class SummariesAnnotatorConfig:
    llm: LLMConfig = LLMConfig()

    # Keep requests small-ish to reduce context overflows.
    max_paragraphs_per_batch: int = 20


class SummariesAnnotationError(RuntimeError):
    pass


def split_non_empty_paragraphs_by_line(text: str) -> List[str]:
    """Split text by '\n' and keep only non-empty (trimmed) lines.

    Must match the frontend SummariesSection paragraph computation.
    """

    if not isinstance(text, str) or not text:
        return []

    paragraphs: List[str] = []
    for line in text.split("\n"):
        if line.strip():
            paragraphs.append(line)
    return paragraphs


def _system_prompt() -> str:
    return (
        "You are a careful summarization assistant. "
        "Return ONLY valid JSON with no extra text. "
        "Do not invent facts. Keep names/entities consistent with the input."
    )


def _user_prompt_paragraph_batch(*, paragraphs: Sequence[Tuple[int, str]], language: str) -> str:
    lang = (language or "en").strip().lower()
    bilingual = lang != "en"

    instructions = (
        "Task: Summarize each paragraph concisely (1-2 sentences).\n"
        "Constraints:\n"
        "- Do not add information not in the paragraph.\n"
        "- Preserve proper nouns if present.\n"
    )

    if bilingual:
        instructions += (
            "- Output two summaries per paragraph: (1) in the source language "
            f"({lang}), and (2) in English.\n"
        )
    else:
        instructions += "- Output English-only summaries.\n"

    instructions += (
        "Output JSON schema:\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "index": 0,\n'
        '      "summary": "...",\n'
        '      "summary_en": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- `index` must match the provided paragraph index.\n"
        "- If English-only, you may omit `summary_en` or set it to an empty string.\n"
        "\nParagraphs:\n"
    )

    for idx, p in paragraphs:
        instructions += f"[{idx}] {p}\n"

    return instructions


def _user_prompt_single_paragraph(*, index: int, paragraph: str, language: str) -> str:
    return _user_prompt_paragraph_batch(paragraphs=[(index, paragraph)], language=language)


def _user_prompt_whole(*, per_paragraph_summaries: Sequence[Tuple[int, str]], language: str) -> str:
    lang = (language or "en").strip().lower()
    bilingual = lang != "en"

    instructions = (
        "Task: Write a concise whole-story summary based ONLY on the per-paragraph summaries below.\n"
        "- Do not re-introduce details not present in those summaries.\n"
        "- Prefer 4-7 sentences, coherent storyline.\n"
    )

    if bilingual:
        instructions += (
            "- Output two versions: (1) in the source language "
            f"({lang}), and (2) in English.\n"
            "Output JSON schema:\n"
            "{\n"
            '  "whole": "...",\n'
            '  "whole_en": "..."\n'
            "}\n"
        )
    else:
        instructions += (
            "- Output English-only.\n"
            "Output JSON schema:\n"
            "{\n"
            '  "whole": "..."\n'
            "}\n"
        )

    instructions += "\nPer-paragraph summaries:\n"
    for idx, s in per_paragraph_summaries:
        instructions += f"[{idx}] {s}\n"

    return instructions


def _format_bilingual(*, source_language: str, native: str, english: Optional[str]) -> str:
    lang = (source_language or "en").strip().lower()
    if lang == "en":
        return (native or "").strip()

    native_clean = (native or "").strip()
    english_clean = (english or "").strip()

    if native_clean and english_clean:
        return f"{native_clean}\nEnglish: {english_clean}"
    if native_clean:
        return native_clean
    if english_clean:
        return f"English: {english_clean}"
    return ""


def annotate_summaries(
    *,
    text: str,
    language: str = "en",
    config: SummariesAnnotatorConfig = SummariesAnnotatorConfig(),
) -> Dict[str, Any]:
    """Generate per-paragraph + whole-story summaries.

    Returns:
      {
        "per_paragraph": {"0": "...", "1": "..."},
        "whole": "..."
      }

    Note: JSON keys are strings to match typical frontend state serialization.
    """

    paragraphs = split_non_empty_paragraphs_by_line(text)
    if not paragraphs:
        return {"per_paragraph": {}, "whole": ""}

    lang = (language or "en").strip().lower()

    # 1) Per-paragraph summaries (batch)
    per_paragraph_out: Dict[str, str] = {}

    max_batch = max(1, int(config.max_paragraphs_per_batch or 20))
    for start in range(0, len(paragraphs), max_batch):
        batch = [(i, paragraphs[i]) for i in range(start, min(len(paragraphs), start + max_batch))]

        messages = [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt_paragraph_batch(paragraphs=batch, language=lang)},
        ]

        try:
            raw = chat(config=config.llm, messages=messages, response_format_json=True, timeout_s=600.0)
        except LLMRouterError as exc:
            raise SummariesAnnotationError(str(exc)) from exc

        data = loads_strict_json(raw)
        if not isinstance(data, dict):
            raise SummariesAnnotationError("Model output JSON must be an object")

        items = data.get("items")
        if not isinstance(items, list):
            raise SummariesAnnotationError("Model output JSON must contain `items` array")

        for item in items:
            if not isinstance(item, dict):
                continue
            idx = item.get("index")
            try:
                idx_int = int(idx)
            except (TypeError, ValueError):
                continue

            if idx_int < 0 or idx_int >= len(paragraphs):
                continue

            summary_native = item.get("summary")
            summary_en = item.get("summary_en")

            # Normalize to strings
            summary_native_s = str(summary_native) if summary_native is not None else ""
            summary_en_s = str(summary_en) if summary_en is not None else ""

            formatted = _format_bilingual(
                source_language=lang,
                native=summary_native_s,
                english=(None if lang == "en" else summary_en_s),
            )
            per_paragraph_out[str(idx_int)] = formatted

    # Ensure all paragraphs exist (even if model missed some)
    for i in range(len(paragraphs)):
        per_paragraph_out.setdefault(str(i), "")

    # 2) Whole-story summary (based on per-paragraph summaries)
    per_paragraph_for_whole = [(i, per_paragraph_out.get(str(i), "")) for i in range(len(paragraphs))]

    messages_whole = [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": _user_prompt_whole(per_paragraph_summaries=per_paragraph_for_whole, language=lang),
        },
    ]

    try:
        raw_whole = chat(config=config.llm, messages=messages_whole, response_format_json=True, timeout_s=600.0)
    except LLMRouterError as exc:
        raise SummariesAnnotationError(str(exc)) from exc

    data_whole = loads_strict_json(raw_whole)
    if not isinstance(data_whole, dict):
        raise SummariesAnnotationError("Model output JSON for whole summary must be an object")

    whole_native = data_whole.get("whole")
    whole_en = data_whole.get("whole_en")

    whole_text = _format_bilingual(
        source_language=lang,
        native=str(whole_native) if whole_native is not None else "",
        english=(None if lang == "en" else (str(whole_en) if whole_en is not None else "")),
    )

    return {"per_paragraph": per_paragraph_out, "whole": whole_text}


def annotate_single_paragraph_summary(
    *,
    index: int,
    paragraph: str,
    language: str = "en",
    config: SummariesAnnotatorConfig = SummariesAnnotatorConfig(),
) -> str:
    """Summarize a single paragraph and return the formatted summary string."""

    if not isinstance(paragraph, str) or not paragraph.strip():
        return ""

    lang = (language or "en").strip().lower()

    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": _user_prompt_single_paragraph(index=index, paragraph=paragraph, language=lang)},
    ]

    try:
        raw = chat(config=config.llm, messages=messages, response_format_json=True, timeout_s=600.0)
    except LLMRouterError as exc:
        raise SummariesAnnotationError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise SummariesAnnotationError("Model output JSON must be an object")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise SummariesAnnotationError("Model output JSON must contain non-empty `items` array")

    item0 = items[0]
    if not isinstance(item0, dict):
        raise SummariesAnnotationError("Model output `items[0]` must be an object")

    summary_native = item0.get("summary")
    summary_en = item0.get("summary_en")

    summary_native_s = str(summary_native) if summary_native is not None else ""
    summary_en_s = str(summary_en) if summary_en is not None else ""

    return _format_bilingual(
        source_language=lang,
        native=summary_native_s,
        english=(None if lang == "en" else summary_en_s),
    )


def annotate_whole_summary_from_per_paragraph(
    *,
    per_paragraph: Dict[str, str],
    language: str = "en",
    config: SummariesAnnotatorConfig = SummariesAnnotatorConfig(),
) -> str:
    """Generate a whole-story summary based ONLY on per-paragraph summaries."""

    lang = (language or "en").strip().lower()

    # Sort numeric keys if possible
    def _key_num(k: str) -> int:
        try:
            return int(k)
        except Exception:
            return 10**9

    ordered = sorted(per_paragraph.items(), key=lambda kv: _key_num(kv[0]))
    per_paragraph_for_whole = [(int(k) if k.isdigit() else i, v) for i, (k, v) in enumerate(ordered)]

    messages_whole = [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": _user_prompt_whole(per_paragraph_summaries=per_paragraph_for_whole, language=lang),
        },
    ]

    try:
        raw_whole = chat(config=config.llm, messages=messages_whole, response_format_json=True, timeout_s=600.0)
    except LLMRouterError as exc:
        raise SummariesAnnotationError(str(exc)) from exc

    data_whole = loads_strict_json(raw_whole)
    if not isinstance(data_whole, dict):
        raise SummariesAnnotationError("Model output JSON for whole summary must be an object")

    whole_native = data_whole.get("whole")
    whole_en = data_whole.get("whole_en")

    return _format_bilingual(
        source_language=lang,
        native=str(whole_native) if whole_native is not None else "",
        english=(None if lang == "en" else (str(whole_en) if whole_en is not None else "")),
    )
