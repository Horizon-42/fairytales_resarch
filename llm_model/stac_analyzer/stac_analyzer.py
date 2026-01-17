"""STAC (Situation, Task, Action, Consequence) analysis API.

This module provides functionality to classify sentences into STAC categories
and extract relevant information based on the classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from ..json_utils import loads_strict_json
from ..llm_router import LLMConfig, LLMRouterError, chat
from .stac_prompts import (
    SYSTEM_PROMPT_STAC_ANALYSIS,
    build_stac_analysis_prompt,
)


@dataclass(frozen=True)
class STACAnalyzerConfig:
    """Controls model choice and LLM provider."""

    llm: LLMConfig = LLMConfig()


class STACAnalysisError(RuntimeError):
    pass


STACCategory = Literal["situation", "task", "action", "consequence"]


def analyze_stac(
    *,
    sentence: str,
    story_context: Optional[str] = None,
    use_context: bool = True,
    previous_sentence: Optional[str] = None,
    next_sentence: Optional[str] = None,
    use_neighboring_sentences: bool = False,
    config: STACAnalyzerConfig = STACAnalyzerConfig(),
) -> Dict[str, Any]:
    """Analyze a single sentence using STAC classification.

    Args:
        sentence: The specific sentence to analyze.
        story_context: The full story text providing context (required if use_context is True).
        use_context: Whether to use story context in the analysis. If False, only the sentence is analyzed.
        previous_sentence: The sentence immediately before the target sentence (used if use_neighboring_sentences is True).
        next_sentence: The sentence immediately after the target sentence (used if use_neighboring_sentences is True).
        use_neighboring_sentences: Whether to use neighboring sentences as auxiliary information. 
            This mode is orthogonal to use_context and can be used independently or together.
        config: STAC analyzer configuration.

    Returns a dict containing:
        - stac_category: str - One of "situation", "task", "action", "consequence"
        - location: str - For situation: location name (empty if not applicable)
        - task_roles: List[str] - For task: list of roles who need to complete the task (empty if not applicable)
        - doers: List[str] - For action: list of doers (empty if not applicable)
        - receivers: List[str] - For action: list of receivers (empty if not applicable)
        - changed_state: str - For consequence: description of state change (empty if not applicable)
        - explanation: str - Brief explanation of the classification and annotation

    Raises:
        STACAnalysisError: on model/JSON failure.
    """

    if not isinstance(sentence, str) or not sentence.strip():
        raise STACAnalysisError("`sentence` must be a non-empty string")

    if use_context:
        if not isinstance(story_context, str) or not story_context.strip():
            raise STACAnalysisError("`story_context` must be a non-empty string when use_context is True")
    else:
        # If not using context, story_context is optional
        story_context = None

    # Validate neighboring sentences if the mode is enabled
    if use_neighboring_sentences:
        # At least one neighboring sentence should be provided
        if previous_sentence is None and next_sentence is None:
            raise STACAnalysisError(
                "At least one of `previous_sentence` or `next_sentence` must be provided "
                "when `use_neighboring_sentences` is True"
            )
        # If provided, they should be non-empty strings
        if previous_sentence is not None and (not isinstance(previous_sentence, str) or not previous_sentence.strip()):
            raise STACAnalysisError("`previous_sentence` must be a non-empty string if provided")
        if next_sentence is not None and (not isinstance(next_sentence, str) or not next_sentence.strip()):
            raise STACAnalysisError("`next_sentence` must be a non-empty string if provided")
    else:
        # If not using neighboring sentences, ignore them
        previous_sentence = None
        next_sentence = None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_STAC_ANALYSIS},
        {
            "role": "user",
            "content": build_stac_analysis_prompt(
                sentence=sentence,
                story_context=story_context,
                use_context=use_context,
                previous_sentence=previous_sentence,
                next_sentence=next_sentence,
                use_neighboring_sentences=use_neighboring_sentences,
            ),
        },
    ]

    try:
        raw = chat(config=config.llm, messages=messages, response_format_json=True)
    except LLMRouterError as exc:
        raise STACAnalysisError(str(exc)) from exc

    data = loads_strict_json(raw)
    if not isinstance(data, dict):
        raise STACAnalysisError("Model output JSON must be an object")

    # Normalize output to ensure it matches the expected schema
    result = _normalize_stac_data(data)

    return result


def _normalize_stac_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the model output matches the expected schema."""

    # Normalize stac_category
    stac_category = str(data.get("stac_category", "")).lower()
    valid_categories: List[STACCategory] = ["situation", "task", "action", "consequence"]
    if stac_category not in valid_categories:
        # Default to "situation" if invalid
        stac_category = "situation"

    # Normalize string fields
    location = str(data.get("location", "")).strip()
    changed_state = str(data.get("changed_state", "")).strip()
    explanation = str(data.get("explanation", "")).strip()

    # Normalize array fields
    task_roles = data.get("task_roles", [])
    if not isinstance(task_roles, list):
        task_roles = []
    task_roles = [str(role).strip() for role in task_roles if str(role).strip()]

    doers = data.get("doers", [])
    if not isinstance(doers, list):
        doers = []
    doers = [str(doer).strip() for doer in doers if str(doer).strip()]

    receivers = data.get("receivers", [])
    if not isinstance(receivers, list):
        receivers = []
    receivers = [str(receiver).strip() for receiver in receivers if str(receiver).strip()]

    # Clear fields that are not relevant to the current category
    if stac_category == "situation":
        task_roles = []
        doers = []
        receivers = []
        changed_state = ""
    elif stac_category == "task":
        location = ""
        doers = []
        receivers = []
        changed_state = ""
    elif stac_category == "action":
        location = ""
        task_roles = []
        changed_state = ""
    elif stac_category == "consequence":
        location = ""
        task_roles = []
        doers = []
        receivers = []

    return {
        "stac_category": stac_category,
        "location": location,
        "task_roles": task_roles,
        "doers": doers,
        "receivers": receivers,
        "changed_state": changed_state,
        "explanation": explanation,
    }


def analyze_stac_batch(
    *,
    sentences: List[str],
    story_context: Optional[str] = None,
    use_context: bool = True,
    use_neighboring_sentences: bool = False,
    config: STACAnalyzerConfig = STACAnalyzerConfig(),
) -> List[Dict[str, Any]]:
    """Analyze multiple sentences in batch using STAC classification.
    
    This function is optimized for batch processing and can leverage
    vLLM's batch inference capabilities for faster processing.
    
    Args:
        sentences: List of sentences to analyze (should be consecutive sentences from a story).
        story_context: The full story text providing context (required if use_context is True).
        use_context: Whether to use story context in the analysis.
        use_neighboring_sentences: Whether to use neighboring sentences as auxiliary information.
        config: STAC analyzer configuration.
    
    Returns:
        List of analysis results, one for each sentence in the same order.
    """

    if not isinstance(sentences, list) or not sentences:
        raise STACAnalysisError("`sentences` must be a non-empty list")

    if use_context:
        if not isinstance(story_context, str) or not story_context.strip():
            raise STACAnalysisError(
                "`story_context` must be a non-empty string when use_context is True")
    else:
        story_context = None

    # Check if using vLLM (better for batch processing)
    use_vllm = False
    if hasattr(config.llm, 'huggingface') and hasattr(config.llm.huggingface, 'use_vllm'):
        use_vllm = config.llm.huggingface.use_vllm

    # For vLLM, we can do true batch inference
    if use_vllm:
        return _analyze_stac_batch_vllm(
            sentences=sentences,
            story_context=story_context,
            use_context=use_context,
            use_neighboring_sentences=use_neighboring_sentences,
            config=config,
        )

    # For transformers, process in parallel (concurrent requests)
    # Note: This is not true batching but can still be faster than sequential
    return _analyze_stac_batch_transformers(
        sentences=sentences,
        story_context=story_context,
        use_context=use_context,
        use_neighboring_sentences=use_neighboring_sentences,
        config=config,
    )


def _analyze_stac_batch_vllm(
    *,
    sentences: List[str],
    story_context: Optional[str],
    use_context: bool,
    use_neighboring_sentences: bool,
    config: STACAnalyzerConfig,
) -> List[Dict[str, Any]]:
    """Batch processing using vLLM (true batch inference)."""
    try:
        from vllm import LLM, SamplingParams
        from transformers import AutoTokenizer
    except ImportError:
        # Fallback to transformers batch processing
        return _analyze_stac_batch_transformers(
            sentences=sentences,
            story_context=story_context,
            use_context=use_context,
            use_neighboring_sentences=use_neighboring_sentences,
            config=config,
        )

    # Get vLLM model from cache (reuse existing model)
    from ..huggingface_client import _chat_with_vllm

    if not hasattr(_chat_with_vllm, "_vllm_cache"):
        # Fallback if vLLM not initialized
        return _analyze_stac_batch_transformers(
            sentences=sentences,
            story_context=story_context,
            use_context=use_context,
            use_neighboring_sentences=use_neighboring_sentences,
            config=config,
        )

    cache_key = f"vllm::{config.llm.huggingface.model}"
    if cache_key not in _chat_with_vllm._vllm_cache:
        # Fallback if model not loaded
        return _analyze_stac_batch_transformers(
            sentences=sentences,
            story_context=story_context,
            use_context=use_context,
            use_neighboring_sentences=use_neighboring_sentences,
            config=config,
        )

    llm = _chat_with_vllm._vllm_cache[cache_key]

    # Prepare tokenizer for prompt formatting
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            config.llm.huggingface.model, trust_remote_code=True)
    except Exception:
        tokenizer = None

    # Prepare all prompts in batch
    prompts = []
    for idx, sentence in enumerate(sentences):
        previous_sentence = None
        next_sentence = None

        if use_neighboring_sentences:
            if idx > 0:
                previous_sentence = sentences[idx - 1]
            if idx < len(sentences) - 1:
                next_sentence = sentences[idx + 1]

        # Format prompt
        system_prompt = SYSTEM_PROMPT_STAC_ANALYSIS
        if True:  # response_format_json
            if "JSON" not in system_prompt.upper():
                system_prompt += "\n\nYou must respond with valid JSON only (no markdown, no commentary)."

        chat_messages = [
            {"role": "user", "content": build_stac_analysis_prompt(
                sentence=sentence,
                story_context=story_context,
                use_context=use_context,
                previous_sentence=previous_sentence,
                next_sentence=next_sentence,
                use_neighboring_sentences=use_neighboring_sentences,
            )}
        ]

        # Format using tokenizer if available
        if tokenizer and hasattr(tokenizer, "apply_chat_template"):
            try:
                prompt = tokenizer.apply_chat_template(
                    chat_messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
                if system_prompt:
                    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n{prompt}"
            except Exception:
                prompt = f"System: {system_prompt}\n\nUser: {chat_messages[0]['content']}\nAssistant: "
        else:
            prompt = f"System: {system_prompt}\n\nUser: {chat_messages[0]['content']}\nAssistant: "

        prompts.append(prompt)

    # Generate with vLLM in batch (true batch processing)
    sampling_params = SamplingParams(
        temperature=config.llm.huggingface.temperature,
        top_p=config.llm.huggingface.top_p,
        max_tokens=config.llm.huggingface.max_new_tokens,
    )

    try:
        # True batch inference: process all prompts at once
        outputs = llm.generate(prompts, sampling_params)

        # Parse results
        results = []
        for output in outputs:
            try:
                raw = output.outputs[0].text.strip()
                data = loads_strict_json(raw)
                if not isinstance(data, dict):
                    raise STACAnalysisError(
                        "Model output JSON must be an object")
                result = _normalize_stac_data(data)
                results.append(result)
            except Exception as e:
                results.append({
                    "stac_category": "situation",
                    "location": "",
                    "task_roles": [],
                    "doers": [],
                    "receivers": [],
                    "changed_state": "",
                    "explanation": f"Error: {str(e)}",
                })

        return results
    except Exception as e:
        # Fallback to transformers batch processing
        return _analyze_stac_batch_transformers(
            sentences=sentences,
            story_context=story_context,
            use_context=use_context,
            use_neighboring_sentences=use_neighboring_sentences,
            config=config,
        )


def _analyze_stac_batch_transformers(
    *,
    sentences: List[str],
    story_context: Optional[str],
    use_context: bool,
    use_neighboring_sentences: bool,
    config: STACAnalyzerConfig,
) -> List[Dict[str, Any]]:
    """Batch processing using transformers (sequential but optimized)."""
    # For transformers, just call analyze_stac for each sentence
    # The model will be cached, so this is still efficient
    results = []
    for idx, sentence in enumerate(sentences):
        previous_sentence = None
        next_sentence = None

        if use_neighboring_sentences:
            if idx > 0:
                previous_sentence = sentences[idx - 1]
            if idx < len(sentences) - 1:
                next_sentence = sentences[idx + 1]

        try:
            result = analyze_stac(
                sentence=sentence,
                story_context=story_context,
                use_context=use_context,
                previous_sentence=previous_sentence,
                next_sentence=next_sentence,
                use_neighboring_sentences=use_neighboring_sentences,
                config=config,
            )
            results.append(result)
        except Exception as e:
            results.append({
                "stac_category": "situation",
                "location": "",
                "task_roles": [],
                "doers": [],
                "receivers": [],
                "changed_state": "",
                "explanation": f"Error: {str(e)}",
            })

    return results
