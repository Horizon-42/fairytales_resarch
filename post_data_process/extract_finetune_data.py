#!/usr/bin/env python3
"""
Extract relationships, action_layer, and action data (agents, targets, target_type, instrument)
from JSON v3 files for finetuning purposes.

Outputs:
1. relationships.csv - All relationships from narrative_events
2. action_layer.csv - All action_layer data from narrative_events
3. actions.csv - Agents, targets, target_type, instrument from narrative_events

All files include story_name and text_span for tracking.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict
import sys


def extract_from_v3(v3_path: Path) -> Dict[str, List[Dict]]:
    """
    Extract relationships, action_layer, and actions from v3 JSON file.
    
    Returns:
        Dict with keys: 'relationships', 'action_layers', 'actions'
    """
    result = {
        'relationships': [],
        'action_layers': [],
        'actions': []
    }
    
    if not v3_path.exists():
        return result
    
    try:
        with open(v3_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Get story metadata
            metadata = data.get("metadata", {})
            story_name = metadata.get("id") or metadata.get("title", "Unknown")
            
            narrative_events = data.get("narrative_events", [])
            
            for event in narrative_events:
                event_id = event.get("id", "")
                text_span = event.get("text_span", {})
                
                # Extract relationships (can be multiple per event)
                relationships = event.get("relationships", [])
                if isinstance(relationships, list) and relationships:
                    for rel in relationships:
                        if isinstance(rel, dict):
                            rel_record = {
                                "story_name": story_name,
                                "event_id": event_id,
                                "text_span_start": text_span.get("start", ""),
                                "text_span_end": text_span.get("end", ""),
                                "text_span_text": text_span.get("text", ""),
                                "agent": rel.get("agent", ""),
                                "target": rel.get("target", ""),
                                "relationship_level1": rel.get("relationship_level1", ""),
                                "relationship_level2": rel.get("relationship_level2", ""),
                                "sentiment": rel.get("sentiment", ""),
                            }
                            result['relationships'].append(rel_record)
                
                # Extract action_layer (one per event)
                action_layer = event.get("action_layer", {})
                if isinstance(action_layer, dict):
                    action_layer_record = {
                        "story_name": story_name,
                        "event_id": event_id,
                        "text_span_start": text_span.get("start", ""),
                        "text_span_end": text_span.get("end", ""),
                        "text_span_text": text_span.get("text", ""),
                        "category": action_layer.get("category", ""),
                        "type": action_layer.get("type", ""),
                        "context": action_layer.get("context", ""),
                        "status": action_layer.get("status", ""),
                        "function": action_layer.get("function", ""),
                    }
                    result['action_layers'].append(action_layer_record)
                
                # Extract action data: agents, targets, target_type, instrument (one per event)
                agents = event.get("agents", [])
                targets = event.get("targets", [])
                target_type = event.get("target_type", "")
                instrument = event.get("instrument", "")
                
                action_record = {
                    "story_name": story_name,
                    "event_id": event_id,
                    "text_span_start": text_span.get("start", ""),
                    "text_span_end": text_span.get("end", ""),
                    "text_span_text": text_span.get("text", ""),
                    "agents": "; ".join(agents) if isinstance(agents, list) else str(agents) if agents else "",
                    "targets": "; ".join(targets) if isinstance(targets, list) else str(targets) if targets else "",
                    "target_type": target_type,
                    "instrument": instrument,
                }
                result['actions'].append(action_record)
    
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"  Warning: Error reading {v3_path}: {e}")
    
    return result


def process_directory(input_dir: Path, output_dir: Path):
    """
    Process all JSON v3 files in the input directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file paths
    relationships_file = output_dir / "relationships.csv"
    action_layer_file = output_dir / "action_layer.csv"
    actions_file = output_dir / "actions.csv"
    
    # Collect all data
    all_relationships = []
    all_action_layers = []
    all_actions = []
    
    # Find all JSON files in input directory
    json_files = list(input_dir.glob("*_v3.json")) + list(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    print(f"Found {len(json_files)} JSON file(s) to process")
    
    for json_file in sorted(json_files):
        print(f"Processing: {json_file.name}")
        
        extracted = extract_from_v3(json_file)
        
        all_relationships.extend(extracted['relationships'])
        all_action_layers.extend(extracted['action_layers'])
        all_actions.extend(extracted['actions'])
        
        print(f"  - {len(extracted['relationships'])} relationships")
        print(f"  - {len(extracted['action_layers'])} action layers")
        print(f"  - {len(extracted['actions'])} actions")
    
    # Write relationships CSV
    relationships_fields = [
        "story_name",
        "event_id",
        "text_span_start",
        "text_span_end",
        "text_span_text",
        "agent",
        "target",
        "relationship_level1",
        "relationship_level2",
        "sentiment",
    ]
    
    with open(relationships_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=relationships_fields)
        writer.writeheader()
        writer.writerows(all_relationships)
    
    print(f"\nSaved {len(all_relationships)} relationships to: {relationships_file}")
    
    # Write action_layer CSV
    action_layer_fields = [
        "story_name",
        "event_id",
        "text_span_start",
        "text_span_end",
        "text_span_text",
        "category",
        "type",
        "context",
        "status",
        "function",
    ]
    
    with open(action_layer_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=action_layer_fields)
        writer.writeheader()
        writer.writerows(all_action_layers)
    
    print(f"Saved {len(all_action_layers)} action layers to: {action_layer_file}")
    
    # Write actions CSV
    actions_fields = [
        "story_name",
        "event_id",
        "text_span_start",
        "text_span_end",
        "text_span_text",
        "agents",
        "targets",
        "target_type",
        "instrument",
    ]
    
    with open(actions_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=actions_fields)
        writer.writeheader()
        writer.writerows(all_actions)
    
    print(f"Saved {len(all_actions)} actions to: {actions_file}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total relationships: {len(all_relationships)}")
    print(f"  Total action layers: {len(all_action_layers)}")
    print(f"  Total actions: {len(all_actions)}")
    print(f"  Output directory: {output_dir}")
    print(f"{'='*60}")


def main():
    """Main function"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Parse command line arguments
    if len(sys.argv) >= 3:
        input_dir = Path(sys.argv[1])
        output_dir = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        input_dir = Path(sys.argv[1])
        output_dir = script_dir / "finetune_data"
    else:
        # Default: use json_v3 directory
        input_dir = project_root / "datasets" / "ChineseTales" / "json_v3"
        output_dir = script_dir / "finetune_data"
    
    # Convert to absolute paths
    if not input_dir.is_absolute():
        input_dir = project_root / input_dir
    
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        print("\nUsage:")
        print(f"  python {Path(__file__).name} [input_dir] [output_dir]")
        print(f"\nDefault: input_dir={input_dir}, output_dir={output_dir}")
        sys.exit(1)
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}\n")
    
    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()
