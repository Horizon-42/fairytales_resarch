#!/usr/bin/env python3
"""
Post-process fairytale JSON files to generate visualization-ready data.
Generates two outputs:
1. Character relationship data (nodes + edges)
2. Story ribbon data (timeline events with character involvement)

Refactored for backend use: accepts data directly, returns structured data.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
import uuid

# Support both relative import (when used as module) and absolute import (when run directly)
try:
    from .character_analysis import analyze_and_sort_characters
except ImportError:
    from character_analysis import analyze_and_sort_characters


def extract_character_relationships(data: dict) -> dict:
    """
    Extract character nodes and relationship edges from narrative events.
    
    Args:
        data: Dictionary containing 'characters' and 'narrative_events' keys
        
    Returns:
        Dictionary with 'nodes' and 'edges' keys
    """
    characters = data.get("characters", [])
    narrative_events = data.get("narrative_events", [])
    
    # Build character nodes
    nodes = []
    char_name_to_id = {}
    
    for i, char in enumerate(characters):
        char_id = f"char_{i}"
        char_name_to_id[char.get("name", f"Unknown_{i}")] = char_id
        # Also map aliases
        aliases = char.get("alias", "").split(";")
        for alias in aliases:
            alias = alias.strip()
            if alias:
                char_name_to_id[alias] = char_id
        
        nodes.append({
            "id": char_id,
            "name": char.get("name", f"Unknown_{i}"),
            "alias": char.get("alias", ""),
            "archetype": char.get("archetype", "Other"),
        })
    
    # Build relationship edges from narrative events
    # V3 format: events can have multiple relationships, each with its own agent/target
    # V2 fallback: event-level agents/targets with relationship_level1/level2
    edges = []
    edge_counts = defaultdict(lambda: defaultdict(int))
    edge_details = defaultdict(list)
    
    for event in narrative_events:
        event_type = event.get("event_type", "")
        description = event.get("description", "")
        time_order = event.get("time_order", 0)

        # V3 format: Extract relationships from relationships array
        relationships = event.get("relationships", [])

        if relationships and isinstance(relationships, list):
            # V3 format: Process each relationship in the array
            for rel in relationships:
                if not isinstance(rel, dict):
                    continue

                agent = rel.get("agent", "")
                target = rel.get("target", "")
                rel_level1 = rel.get("relationship_level1", "")
                rel_level2 = rel.get("relationship_level2", "")
                sentiment = rel.get("sentiment", "")

                # Skip if missing agent or target
                if not agent or not target:
                    continue

                # Find character IDs
                agent_id = char_name_to_id.get(agent)
                if not agent_id:
                    # Try to find by partial match
                    for name, cid in char_name_to_id.items():
                        if agent in name or name in agent:
                            agent_id = cid
                            break

                target_id = char_name_to_id.get(target)
                if not target_id:
                    for name, cid in char_name_to_id.items():
                        if target in name or name in target:
                            target_id = cid
                            break

                if agent_id and target_id and agent_id != target_id:
                    edge_key = tuple(sorted([agent_id, target_id]))
                    edge_counts[edge_key]["count"] += 1
                    edge_details[edge_key].append({
                        "source": agent_id,
                        "target": target_id,
                        "relationship_level1": rel_level1,
                        "relationship_level2": rel_level2,
                        "sentiment": sentiment,
                        "event_type": event_type,
                        "description": description,
                        "time_order": time_order,
                    })
        else:
            # V2 fallback: Use event-level agents/targets and relationship fields
            agents = event.get("agents", [])
            targets = event.get("targets", [])
            rel_level1 = event.get("relationship_level1", "")
            rel_level2 = event.get("relationship_level2", "")
            sentiment = event.get("sentiment", "")

            # Create edges between agents and targets
            for agent in agents:
                agent_id = char_name_to_id.get(agent)
                if not agent_id:
                    # Try to find by partial match
                    for name, cid in char_name_to_id.items():
                        if agent in name or name in agent:
                            agent_id = cid
                            break

                for target in targets:
                    target_id = char_name_to_id.get(target)
                    if not target_id:
                        for name, cid in char_name_to_id.items():
                            if target in name or name in target:
                                target_id = cid
                                break

                    if agent_id and target_id and agent_id != target_id:
                        edge_key = tuple(sorted([agent_id, target_id]))
                        edge_counts[edge_key]["count"] += 1
                        edge_details[edge_key].append({
                            "source": agent_id,
                            "target": target_id,
                            "relationship_level1": rel_level1,
                            "relationship_level2": rel_level2,
                            "sentiment": sentiment,
                            "event_type": event_type,
                            "description": description,
                            "time_order": time_order,
                        })
    
    # Aggregate edges
    for edge_key, details in edge_details.items():
        # Determine primary relationship type
        rel_types = [d["relationship_level1"] for d in details if d["relationship_level1"]]
        sentiments = [d["sentiment"] for d in details if d["sentiment"]]
        
        primary_rel = max(set(rel_types), key=rel_types.count) if rel_types else "Unknown"
        primary_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else "neutral"
        
        edges.append({
            "source": edge_key[0],
            "target": edge_key[1],
            "weight": len(details),
            "relationship_type": primary_rel,
            "sentiment": primary_sentiment,
            "interactions": details,
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
    }


def extract_story_ribbons(data: dict) -> dict:
    """
    Extract story ribbon data - timeline of events with character involvement.
    Characters are sorted by their relationship to the main hero:
    - Hero at center
    - Friendly characters above
    - Hostile characters below
    
    Args:
        data: Dictionary containing 'characters', 'narrative_events', and 'metadata' keys
        
    Returns:
        Dictionary with story ribbon data including sorted characters and events
    """
    characters = data.get("characters", [])
    narrative_events = data.get("narrative_events", [])
    metadata = data.get("metadata", {})
    
    # Build initial character list
    char_list = []
    for i, char in enumerate(characters):
        char_list.append({
            "id": f"char_{i}",
            "name": char.get("name", f"Unknown_{i}"),
            "archetype": char.get("archetype", "Other"),
        })
    
    # Build timeline events
    events = []
    for event in narrative_events:
        time_order = event.get("time_order", 0)
        if time_order == 0:
            continue  # Skip events without time order
            
        text_span = event.get("text_span", {})
        
        # Extract sentiment from relationships if not at event level
        sentiment = event.get("sentiment", "")
        if not sentiment:
            relationships = event.get("relationships", [])
            if relationships:
                # Use sentiment from first relationship
                sentiment = relationships[0].get("sentiment", "")
        
        events.append({
            "id": event.get("id", str(uuid.uuid4())),
            "time_order": time_order,
            "event_type": event.get("event_type", "OTHER"),
            "description": event.get("description", ""),
            "agents": event.get("agents", []),
            "targets": event.get("targets", []),
            "relationship_level1": event.get("relationship_level1", ""),
            "relationship_level2": event.get("relationship_level2", ""),
            "sentiment": sentiment,
            "relationships": event.get("relationships", []),  # Keep relationships for detailed analysis
            "text_start": text_span.get("start", 0),
            "text_end": text_span.get("end", 0),
            "text_excerpt": text_span.get("text", "")[:200] + "..." if len(text_span.get("text", "")) > 200 else text_span.get("text", ""),
            "action_layer": event.get("action_layer", {}),
        })
    
    # Sort events by time order
    events.sort(key=lambda x: x["time_order"])
    
    # Analyze and sort characters based on hero relationships
    sorted_characters, analysis_meta = analyze_and_sort_characters(char_list, events)
    
    return {
        "title": metadata.get("title", "Unknown Story"),
        "id": metadata.get("id", ""),
        "characters": sorted_characters,
        "events": events,
        "total_events": len(events),
        "analysis": analysis_meta,
    }


def process_story_data(data: dict) -> Tuple[dict, dict]:
    """
    Process a single story's JSON data and return relationship and ribbon data.
    
    This is the main function for backend use - it accepts data directly.
    
    Args:
        data: Dictionary containing story data with 'characters', 'narrative_events', 
              and 'metadata' keys (standard json_v3 format)
        
    Returns:
        Tuple of (relationship_data, ribbon_data) dictionaries
        
    Raises:
        ValueError: If data is missing required keys or is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    relationship_data = extract_character_relationships(data)
    ribbon_data = extract_story_ribbons(data)
    
    return relationship_data, ribbon_data


def load_story_from_file(file_path: Path | str) -> dict:
    """
    Load story data from a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary containing story data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_story_from_file(file_path: Path | str) -> Tuple[dict, dict]:
    """
    Process a single story from a JSON file.
    
    Convenience function that loads and processes in one step.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Tuple of (relationship_data, ribbon_data) dictionaries
    """
    data = load_story_from_file(file_path)
    return process_story_data(data)


def process_directory(input_dir: Path | str, output_dir: Optional[Path | str] = None) -> Dict[str, Any]:
    """
    Process all JSON files in a directory and return structured data.
    
    This is the main function for backend use - it processes all files and returns
    all data in memory without writing to files (unless output_dir is provided).
    
    Args:
        input_dir: Directory containing JSON files (e.g., json_v3 directory)
        output_dir: Optional directory to write output files. If None, files are not written.
        
    Returns:
        Dictionary containing:
        - 'stories': List of processed story data
        - 'index': Index metadata for all stories
        
    Each story in 'stories' contains:
        - 'story_id': Story identifier
        - 'title': Story title
        - 'relationship_data': Character relationship data
        - 'ribbon_data': Story ribbon data
        - 'metadata': Additional metadata (character count, event count, source text)
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_path}")
    
    if not input_path.is_dir():
        raise ValueError(f"Input path is not a directory: {input_path}")
    
    output_path = Path(output_dir) if output_dir else None
    if output_path and output_path.exists() and not output_path.is_dir():
        raise ValueError(f"Output path exists but is not a directory: {output_path}")
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)
    
    all_stories = []
    processed_stories = []
    
    for json_file in sorted(input_path.glob("*.json")):
        story_id = json_file.stem.replace("_v2", "").replace("_v3", "")
        
        try:
            # Load and process story data
            data = load_story_from_file(json_file)
            relationship_data, ribbon_data = process_story_data(data)
            
            # Extract source text from original data if available
            source_text = ""
            if data.get("source_info") and data["source_info"].get("text_content"):
                source_text = data["source_info"]["text_content"]
            
            # Build story metadata
            story_info = {
                "id": story_id,
                "title": ribbon_data["title"],
                "character_count": len(relationship_data["nodes"]),
                "event_count": ribbon_data["total_events"],
                "relationship_file": f"{story_id}_relationships.json",
                "ribbon_file": f"{story_id}_ribbons.json",
                "text_content": source_text,
            }
            all_stories.append(story_info)
            
            # Build full story data for return
            processed_stories.append({
                "story_id": story_id,
                "title": ribbon_data["title"],
                "relationship_data": relationship_data,
                "ribbon_data": ribbon_data,
                "metadata": story_info,
            })
            
            # Optionally write files
            if output_path:
                rel_output = output_path / f"{story_id}_relationships.json"
                ribbon_output = output_path / f"{story_id}_ribbons.json"
                
                with open(rel_output, "w", encoding="utf-8") as f:
                    json.dump(relationship_data, f, ensure_ascii=False, indent=2)
                
                with open(ribbon_output, "w", encoding="utf-8") as f:
                    json.dump(ribbon_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"Error processing {json_file.name}: {e}"
            print(error_msg, file=sys.stderr)
            # Continue processing other files
    
    # Optionally save index file
    index_data = {"stories": all_stories}
    if output_path:
        index_output = output_path / "stories_index.json"
        with open(index_output, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    return {
        "stories": processed_stories,
        "index": index_data,
    }


# Legacy function names for backward compatibility
def process_single_file(input_path: str) -> tuple:
    """
    Legacy function: Process a single JSON file and return relationship and ribbon data.
    
    Deprecated: Use process_story_from_file() or process_story_data() instead.
    """
    return process_story_from_file(input_path)


def process_all_files(input_dir: str, output_dir: str) -> None:
    """
    Legacy function: Process all JSON files in the input directory and write to output.
    
    Deprecated: Use process_directory() instead.
    """
    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    # CLI usage: maintains backward compatibility
    base_dir = Path(__file__).parent.parent
    
    # Default to json_v3 if it exists, otherwise json_v2
    json_v3_dir = base_dir / "datasets" / "ChineseTales" / "json_v3"
    json_v2_dir = base_dir / "datasets" / "ChineseTales" / "json_v2"
    default_input = json_v3_dir if json_v3_dir.exists() else json_v2_dir
    
    default_output = base_dir / "story_visualization" / "public" / "data"
    
    input_dir = default_input
    output_dir = default_output
    
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    
    result = process_directory(str(input_dir), str(output_dir))
    print(f"\nProcessed {len(result['stories'])} stories")
    print(f"Output saved to: {output_dir}")
