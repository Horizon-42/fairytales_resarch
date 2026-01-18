"""Data preparation utilities for fine-tuning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils.prompt_builder import (
    build_character_prompt_for_training,
    build_instrument_prompt_for_training,
    build_relationship_prompt_for_training,
    build_action_prompt_for_training,
    build_stac_prompt_for_training,
    build_event_type_prompt_for_training,
)


def load_annotated_story(file_path: str) -> Dict[str, Any]:
    """Load annotated story from JSON file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Story dictionary with metadata, characters, narrative_events, etc.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_character_examples(
    annotated_story: Dict[str, Any],
    story_text: Optional[str] = None,
    summary: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract character recognition training examples from annotated story.
    
    Args:
        annotated_story: Annotated story dictionary
        story_text: Full story text (if not in annotated_story)
        summary: Story summary (optional, can be empty for training)
    
    Returns:
        List of training examples: {
            "instruction": prompt string,
            "input": input text,
            "output": JSON string of expected output
        }
    """
    story_text = story_text or annotated_story.get("source_info", {}).get("text_content", "")
    narrative_events = annotated_story.get("narrative_events", [])
    characters = annotated_story.get("characters", [])
    
    examples = []
    current_characters = []
    
    for event in narrative_events:
        # Skip if event is None or empty
        if not event or not isinstance(event, dict):
            continue
        
        text_span = event.get("text_span")
        if text_span is None:
            continue
        
        # Handle both dict and direct text cases
        if isinstance(text_span, dict):
            text = text_span.get("text", "")
        elif isinstance(text_span, str):
            text = text_span
        else:
            continue
        
        if not text or not text.strip():
            continue
        
        # Build prompt
        instruction = build_character_prompt_for_training(
            text_span=text,
            summary=summary or "",  # Empty if not provided
            existing_characters=current_characters,
            story_context=story_text if story_text != text else None
        )
        
        # Extract expected output
        agents = event.get("agents", [])
        targets = event.get("targets", [])
        
        # Try to find new characters from this event
        new_characters = []
        all_mentioned = set(agents + targets)
        for char_name in all_mentioned:
            # Check if already in current_characters
            found = False
            for char in current_characters:
                char_names = [char.get("name", "")]
                if char.get("alias"):
                    char_names.extend(char.get("alias", "").split(";"))
                if char_name in char_names:
                    found = True
                    break
            if not found:
                # Try to find in global characters list
                for char in characters:
                    if char.get("name") == char_name:
                        new_characters.append(char)
                        break
        
        output_dict = {
            "doers": agents,
            "receivers": targets,
            "new_characters": new_characters,
            "notes": ""
        }
        
        examples.append({
            "instruction": instruction,
            "input": "",  # Instruction already contains full input
            "output": json.dumps(output_dict, ensure_ascii=False)
        })
        
        # Update current_characters for next event
        for new_char in new_characters:
            if new_char not in current_characters:
                current_characters.append(new_char)
    
    return examples


def extract_instrument_examples(
    annotated_story: Dict[str, Any],
    summary: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract instrument recognition training examples.
    
    Args:
        annotated_story: Annotated story dictionary
        summary: Story summary (optional)
    
    Returns:
        List of training examples
    """
    narrative_events = annotated_story.get("narrative_events", [])
    examples = []
    
    for event in narrative_events:
        # Skip if event is None or empty
        if not event or not isinstance(event, dict):
            continue
        
        text_span = event.get("text_span")
        if text_span is None:
            continue
        
        # Handle both dict and direct text cases
        if isinstance(text_span, dict):
            text = text_span.get("text", "")
        elif isinstance(text_span, str):
            text = text_span
        else:
            continue
        
        if not text or not text.strip():
            continue
        
        agents = event.get("agents", [])
        instrument = event.get("instrument", "")
        
        instruction = build_instrument_prompt_for_training(
            text_span=text,
            summary=summary or "",
            doers=agents
        )
        
        output_dict = {
            "instrument": instrument,
            "explanation": ""
        }
        
        examples.append({
            "instruction": instruction,
            "input": "",
            "output": json.dumps(output_dict, ensure_ascii=False)
        })
    
    return examples


def extract_relationship_examples(
    annotated_story: Dict[str, Any],
    story_text: Optional[str] = None,
    summary: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract relationship deduction training examples.
    
    Args:
        annotated_story: Annotated story dictionary
        story_text: Full story text
        summary: Story summary (optional)
    
    Returns:
        List of training examples
    """
    story_text = story_text or annotated_story.get("source_info", {}).get("text_content", "")
    narrative_events = annotated_story.get("narrative_events", [])
    examples = []
    
    for event in narrative_events:
        # Skip if event is None or empty
        if not event or not isinstance(event, dict):
            continue
        
        text_span = event.get("text_span")
        if text_span is None:
            continue
        
        # Handle both dict and direct text cases
        if isinstance(text_span, dict):
            text = text_span.get("text", "")
        elif isinstance(text_span, str):
            text = text_span
        else:
            continue
        
        if not text or not text.strip():
            continue
        
        agents = event.get("agents", [])
        targets = event.get("targets", [])
        target_type = event.get("target_type", "object")
        relationships = event.get("relationships", [])
        
        if target_type != "character":
            # Skip if no relationships expected
            continue
        
        instruction = build_relationship_prompt_for_training(
            text_span=text,
            summary=summary or "",
            doers=agents,
            receivers=targets,
            story_context=story_text if story_text != text else None
        )
        
        output_dict = {"relationships": relationships}
        
        examples.append({
            "instruction": instruction,
            "input": "",
            "output": json.dumps(output_dict, ensure_ascii=False)
        })
    
    return examples


def extract_action_examples(
    annotated_story: Dict[str, Any],
    summary: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract action category deduction training examples.
    
    Args:
        annotated_story: Annotated story dictionary
        summary: Story summary (optional)
    
    Returns:
        List of training examples
    """
    narrative_events = annotated_story.get("narrative_events", [])
    examples = []
    
    for event in narrative_events:
        # Skip if event is None or empty
        if not event or not isinstance(event, dict):
            continue
        
        text_span = event.get("text_span")
        if text_span is None:
            continue
        
        # Handle both dict and direct text cases
        if isinstance(text_span, dict):
            text = text_span.get("text", "")
        elif isinstance(text_span, str):
            text = text_span
        else:
            continue
        
        if not text or not text.strip():
            continue
        
        agents = event.get("agents", [])
        targets = event.get("targets", [])
        instrument = event.get("instrument", "")
        action_layer = event.get("action_layer", {})
        
        instruction = build_action_prompt_for_training(
            text_span=text,
            summary=summary or "",
            doers=agents,
            receivers=targets,
            instrument=instrument
        )
        
        output_dict = {
            "category": action_layer.get("category", ""),
            "type": action_layer.get("type", ""),
            "context": action_layer.get("context", ""),
            "status": action_layer.get("status", ""),
            "function": action_layer.get("function", "")
        }
        
        examples.append({
            "instruction": instruction,
            "input": "",
            "output": json.dumps(output_dict, ensure_ascii=False)
        })
    
    return examples


def extract_stac_examples(
    annotated_story: Dict[str, Any],
    story_text: Optional[str] = None,
    summary: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract STAC analysis training examples.
    
    Args:
        annotated_story: Annotated story dictionary
        story_text: Full story text
        summary: Story summary (optional)
    
    Returns:
        List of training examples
    """
    story_text = story_text or annotated_story.get("source_info", {}).get("text_content", "")
    narrative_events = annotated_story.get("narrative_events", [])
    examples = []
    
    for event in narrative_events:
        # Skip if event is None or empty
        if not event or not isinstance(event, dict):
            continue
        
        text_span = event.get("text_span")
        if text_span is None:
            continue
        
        # Handle both dict and direct text cases
        if isinstance(text_span, dict):
            text = text_span.get("text", "")
        elif isinstance(text_span, str):
            text = text_span
        else:
            continue
        
        if not text or not text.strip():
            continue
        
        stac = event.get("stac", {})
        
        instruction = build_stac_prompt_for_training(
            text_span=text,
            summary=summary or "",
            story_context=story_text if story_text != text else None
        )
        
        output_dict = {
            "situation": stac.get("situation", ""),
            "task": stac.get("task", ""),
            "action": stac.get("action", ""),
            "consequence": stac.get("consequence", "")
        }
        
        examples.append({
            "instruction": instruction,
            "input": "",
            "output": json.dumps(output_dict, ensure_ascii=False)
        })
    
    return examples


def extract_event_type_examples(
    annotated_story: Dict[str, Any],
    summary: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract event type classification training examples.
    
    Args:
        annotated_story: Annotated story dictionary
        summary: Story summary (optional)
    
    Returns:
        List of training examples
    """
    narrative_events = annotated_story.get("narrative_events", [])
    examples = []
    
    for event in narrative_events:
        # Skip if event is None or empty
        if not event or not isinstance(event, dict):
            continue
        
        text_span = event.get("text_span")
        if text_span is None:
            continue
        
        # Handle both dict and direct text cases
        if isinstance(text_span, dict):
            text = text_span.get("text", "")
        elif isinstance(text_span, str):
            text = text_span
        else:
            continue
        
        if not text or not text.strip():
            continue
        
        stac = event.get("stac", {})
        event_type = event.get("event_type", "OTHER")
        description = event.get("description", "")
        
        instruction = build_event_type_prompt_for_training(
            text_span=text,
            summary=summary or "",
            stac=stac
        )
        
        # Parse description (format: "general;specific")
        desc_parts = description.split(";", 1)
        desc_general = desc_parts[0].strip() if desc_parts else ""
        desc_specific = desc_parts[1].strip() if len(desc_parts) > 1 else ""
        
        output_dict = {
            "event_type": event_type,
            "description_general": desc_general,
            "description_specific": desc_specific
        }
        
        examples.append({
            "instruction": instruction,
            "input": "",
            "output": json.dumps(output_dict, ensure_ascii=False)
        })
    
    return examples


def load_all_annotated_stories(data_dir: str) -> List[Dict[str, Any]]:
    """Load all annotated stories from a directory.
    
    Args:
        data_dir: Directory containing JSON annotation files
    
    Returns:
        List of annotated story dictionaries
    """
    data_path = Path(data_dir)
    stories = []
    
    for json_file in data_path.glob("*.json"):
        try:
            story = load_annotated_story(str(json_file))
            stories.append(story)
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")
    
    return stories


def prepare_all_training_data(
    data_dir: str,
    steps: List[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Prepare training data for all specified steps.
    
    Args:
        data_dir: Directory containing JSON annotation files
        steps: List of steps to prepare data for (default: all steps)
        output_dir: Optional directory to save training data JSON files
    
    Returns:
        Dictionary mapping step names to lists of training examples
    """
    if steps is None:
        steps = ["character", "instrument", "relationship", "action", "stac", "event_type"]
    
    stories = load_all_annotated_stories(data_dir)
    
    all_examples = {}
    
    for story in stories:
        story_text = story.get("source_info", {}).get("text_content", "")
        summary = None  # Can be extracted from story metadata if available
        
        if "character" in steps:
            examples = extract_character_examples(story, story_text, summary)
            all_examples.setdefault("character", []).extend(examples)
        
        if "instrument" in steps:
            examples = extract_instrument_examples(story, summary)
            all_examples.setdefault("instrument", []).extend(examples)
        
        if "relationship" in steps:
            examples = extract_relationship_examples(story, story_text, summary)
            all_examples.setdefault("relationship", []).extend(examples)
        
        if "action" in steps:
            examples = extract_action_examples(story, summary)
            all_examples.setdefault("action", []).extend(examples)
        
        if "stac" in steps:
            examples = extract_stac_examples(story, story_text, summary)
            all_examples.setdefault("stac", []).extend(examples)
        
        if "event_type" in steps:
            examples = extract_event_type_examples(story, summary)
            all_examples.setdefault("event_type", []).extend(examples)
    
    # Save to files if output_dir specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for step, examples in all_examples.items():
            output_file = output_path / f"{step}_train.jsonl"
            with open(output_file, "w", encoding="utf-8") as f:
                for example in examples:
                    f.write(json.dumps(example, ensure_ascii=False) + "\n")
            print(f"Saved {len(examples)} examples for {step} to {output_file}")
    
    return all_examples
