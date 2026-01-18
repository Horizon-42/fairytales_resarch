"""Data preparation utilities for fine-tuning."""

from __future__ import annotations

import csv
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
        
        # Build prompt (no story_context to save memory)
        instruction = build_character_prompt_for_training(
            text_span=text,
            summary=summary or "",  # Empty if not provided
            existing_characters=current_characters,
            story_context=None  # Always None to save memory
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
            story_context=None  # Always None to save memory
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
            story_context=None  # Always None to save memory
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


def load_generated_story(file_path: str) -> List[str]:
    """Load generated story from text file.
    
    Each line in the file is a paragraph wrapped in {}.
    
    Args:
        file_path: Path to generated story text file
    
    Returns:
        List of paragraph strings (with {} removed)
    """
    paragraphs = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Remove {} wrapper if present
            if line.startswith("{") and line.endswith("}"):
                line = line[1:-1]
            paragraphs.append(line)
    return paragraphs


def find_generated_stories(groundtruth_path: Path, generated_stories_dir: str) -> List[Path]:
    """Find all generated story files for a given groundtruth JSON.
    
    Args:
        groundtruth_path: Path to groundtruth JSON file
        generated_stories_dir: Root directory of generated stories
    
    Returns:
        List of paths to generated story files
    """
    # Extract story ID from groundtruth filename
    # e.g., "CH_002_牛郎织女_v3.json" -> "CH_002_牛郎织女_v3"
    story_id = groundtruth_path.stem  # Removes .json
    
    # Find matching directory in generated_stories
    generated_dir = Path(generated_stories_dir)
    
    # Search for matching story directory
    # Structure: generated_stories/{Culture}/{story_id}/gemini/*.txt
    story_files = []
    
    # Search in all culture directories
    for culture_dir in generated_dir.iterdir():
        if not culture_dir.is_dir():
            continue
        
        story_dir = culture_dir / story_id
        if not story_dir.exists():
            continue
        
        # Look for gemini subdirectory
        gemini_dir = story_dir / "gemini"
        if gemini_dir.exists():
            for txt_file in gemini_dir.glob("*.txt"):
                story_files.append(txt_file)
    
    return sorted(story_files)


def validate_story_paragraphs(
    generated_paragraphs: List[str],
    narrative_events: List[Dict[str, Any]]
) -> bool:
    """Validate that generated story has same number of paragraphs as narrative events.
    
    Args:
        generated_paragraphs: List of generated story paragraphs
        narrative_events: List of narrative events from groundtruth
    
    Returns:
        True if counts match, False otherwise
    """
    return len(generated_paragraphs) == len(narrative_events)


def load_summaries_from_csv(csv_path: Path) -> Dict[str, str]:
    """Load summaries from CSV file.
    
    Args:
        csv_path: Path to story_summaries.csv file
    
    Returns:
        Dictionary mapping relative_path to summary text
    """
    summaries = {}
    
    if not csv_path.exists():
        return summaries
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                relative_path = row.get("relative_path", "").strip()
                summary = row.get("summary", "").strip()
                if relative_path and summary:
                    summaries[relative_path] = summary
    except Exception as e:
        print(f"Warning: Failed to load summaries from {csv_path}: {e}", file=__import__("sys").stderr)
    
    return summaries


def prepare_synthetic_training_data(
    groundtruth_dir: str,
    generated_stories_dir: str,
    output_dir: str,
    steps: Optional[List[str]] = None,
    summaries_csv: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, int]:
    """Prepare training data from synthetic datasets.
    
    Args:
        groundtruth_dir: Directory containing groundtruth JSON v3 files
        generated_stories_dir: Root directory of generated stories
        output_dir: Output directory for training data files
        steps: List of steps to prepare data for (default: all steps)
        summaries_csv: Optional path to story_summaries.csv file (default: auto-detect)
        verbose: Print progress information
    
    Returns:
        Dictionary mapping step names to total number of examples
    """
    if steps is None:
        steps = ["character", "instrument", "relationship", "action", "stac", "event_type"]
    
    groundtruth_path = Path(groundtruth_dir)
    generated_stories_path = Path(generated_stories_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load summaries from CSV if available
    summaries_dict = {}
    if summaries_csv:
        summaries_csv_path = Path(summaries_csv)
    else:
        # Auto-detect: look for story_summaries.csv in synthetic_datasets directory
        synthetic_datasets_dir = generated_stories_path.parent
        summaries_csv_path = synthetic_datasets_dir / "story_summaries.csv"
    
    if summaries_csv_path.exists():
        summaries_dict = load_summaries_from_csv(summaries_csv_path)
        if verbose:
            print(f"Loaded {len(summaries_dict)} summaries from {summaries_csv_path}")
    elif verbose:
        print(f"Warning: Summary CSV not found at {summaries_csv_path}, using empty summaries")
    
    # Find all groundtruth JSON files
    groundtruth_files = list(groundtruth_path.rglob("*.json"))
    
    if verbose:
        print(f"Found {len(groundtruth_files)} groundtruth JSON files")
    
    # Track all examples per step
    all_examples_per_step = {step: [] for step in steps}
    
    # Process each groundtruth file
    for gt_file in groundtruth_files:
        try:
            # Load groundtruth
            groundtruth = load_annotated_story(str(gt_file))
            story_id = groundtruth.get("metadata", {}).get("id", gt_file.stem)
            narrative_events = groundtruth.get("narrative_events", [])
            
            if verbose:
                print(f"\nProcessing: {story_id}")
                print(f"  Groundtruth: {gt_file}")
                print(f"  Narrative events: {len(narrative_events)}")
            
            # Find generated stories
            generated_files = find_generated_stories(gt_file, generated_stories_dir)
            
            if not generated_files:
                if verbose:
                    print(f"  Warning: No generated stories found, skipping...")
                continue
            
            if verbose:
                print(f"  Found {len(generated_files)} generated story files")
            
            # Process each generated story
            for gen_file in generated_files:
                try:
                    # Load generated story
                    generated_paragraphs = load_generated_story(str(gen_file))
                    
                    # Validate paragraph count
                    if not validate_story_paragraphs(generated_paragraphs, narrative_events):
                        if verbose:
                            print(f"  Warning: {gen_file.name} has {len(generated_paragraphs)} paragraphs, "
                                  f"expected {len(narrative_events)}, skipping...")
                        continue
                    
                    # Combine paragraphs into full story text
                    full_story_text = "\n".join(generated_paragraphs)
                    
                    # Create a modified groundtruth with text_span.text filled from generated paragraphs
                    modified_groundtruth = groundtruth.copy()
                    modified_events = []
                    
                    for idx, event in enumerate(narrative_events):
                        # Skip if event is None or empty
                        if not event or not isinstance(event, dict):
                            continue
                        
                        modified_event = event.copy()
                        text_span = modified_event.get("text_span")
                        
                        # Ensure text_span is a dict (handle None case)
                        if text_span is None:
                            text_span = {}
                        elif not isinstance(text_span, dict):
                            # If text_span is not a dict, create a new dict
                            text_span = {}
                        
                        # Fill text from generated paragraph
                        if idx < len(generated_paragraphs):
                            text_span = text_span.copy()  # Now safe to copy
                            text_span["text"] = generated_paragraphs[idx]
                            modified_event["text_span"] = text_span
                        
                        modified_events.append(modified_event)
                    
                    modified_groundtruth["narrative_events"] = modified_events
                    modified_groundtruth["source_info"] = modified_groundtruth.get("source_info", {})
                    modified_groundtruth["source_info"]["text_content"] = full_story_text
                    
                    # Get summary from CSV if available
                    # Generate relative path for lookup: synthetic_datasets/generated_stories/...
                    # CSV stores paths relative to project root, so we need to compute from project root
                    try:
                        # Try to get relative path from project root
                        project_root = generated_stories_path.parent.parent
                        relative_path = gen_file.relative_to(project_root)
                        story_summary = summaries_dict.get(str(relative_path), "")
                    except ValueError:
                        # Fallback: try direct filename match or use empty
                        story_summary = ""
                    
                    # Also try matching by filename as fallback
                    if not story_summary:
                        for csv_path, csv_summary in summaries_dict.items():
                            if gen_file.name in csv_path or gen_file.stem in csv_path:
                                story_summary = csv_summary
                                break
                    
                    if verbose and story_summary:
                        print(f"  Using summary from CSV ({len(story_summary)} chars)")
                    elif verbose and not story_summary:
                        print(f"  No summary found in CSV, using empty summary")
                    
                    # Generate a unique identifier for this story+generation combination
                    gen_id = gen_file.stem  # e.g., "CH_002_牛郎织女_gen_01"
                    
                    # Extract examples for each step
                    step_examples = {}
                    
                    if "character" in steps:
                        examples = extract_character_examples(
                            modified_groundtruth, full_story_text, story_summary
                        )
                        step_examples["character"] = examples
                    
                    if "instrument" in steps:
                        examples = extract_instrument_examples(
                            modified_groundtruth, story_summary
                        )
                        step_examples["instrument"] = examples
                    
                    if "relationship" in steps:
                        examples = extract_relationship_examples(
                            modified_groundtruth, full_story_text, story_summary
                        )
                        step_examples["relationship"] = examples
                    
                    if "action" in steps:
                        examples = extract_action_examples(
                            modified_groundtruth, story_summary
                        )
                        step_examples["action"] = examples
                    
                    if "stac" in steps:
                        examples = extract_stac_examples(
                            modified_groundtruth, full_story_text, story_summary
                        )
                        step_examples["stac"] = examples
                    
                    if "event_type" in steps:
                        examples = extract_event_type_examples(
                            modified_groundtruth, story_summary
                        )
                        step_examples["event_type"] = examples
                    
                    # Save individual story file for each step
                    for step, examples in step_examples.items():
                        if not examples:
                            continue
                        
                        # Create per-story file
                        story_output_dir = output_path / step / "per_story"
                        story_output_dir.mkdir(parents=True, exist_ok=True)
                        
                        story_file = story_output_dir / f"{gen_id}_{step}.jsonl"
                        with open(story_file, "w", encoding="utf-8") as f:
                            for example in examples:
                                f.write(json.dumps(example, ensure_ascii=False) + "\n")
                        
                        # Also collect for final merge
                        all_examples_per_step[step].extend(examples)
                        
                        if verbose:
                            print(f"    {step}: {len(examples)} examples -> {story_file.name}")
                    
                except Exception as e:
                    if verbose:
                        print(f"  Error processing {gen_file.name}: {e}")
                    continue
        
        except Exception as e:
            if verbose:
                print(f"Error processing {gt_file}: {e}")
            continue
    
    # Merge all examples and save final files
    if verbose:
        print(f"\nMerging all examples...")
    
    for step, examples in all_examples_per_step.items():
        if not examples:
            if verbose:
                print(f"  {step}: No examples, skipping...")
            continue
        
        # Save merged file
        merged_file = output_path / f"{step}_train.jsonl"
        with open(merged_file, "w", encoding="utf-8") as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")
        
        if verbose:
            print(f"  {step}: {len(examples)} total examples -> {merged_file}")
    
    # Return counts
    return {step: len(examples) for step, examples in all_examples_per_step.items()}


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
