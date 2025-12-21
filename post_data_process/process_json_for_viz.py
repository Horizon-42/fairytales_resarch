#!/usr/bin/env python3
"""
Post-process fairytale JSON files to generate visualization-ready data.
Generates two outputs:
1. Character relationship data (nodes + edges)
2. Story ribbon data (timeline events with character involvement)
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
import uuid

from character_analysis import analyze_and_sort_characters


def extract_character_relationships(data: dict) -> dict:
    """
    Extract character nodes and relationship edges from narrative events.
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
    edges = []
    edge_counts = defaultdict(lambda: defaultdict(int))
    edge_details = defaultdict(list)
    
    for event in narrative_events:
        agents = event.get("agents", [])
        targets = event.get("targets", [])
        rel_level1 = event.get("relationship_level1", "")
        rel_level2 = event.get("relationship_level2", "")
        sentiment = event.get("sentiment", "")
        event_type = event.get("event_type", "")
        description = event.get("description", "")
        time_order = event.get("time_order", 0)
        
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
        
        events.append({
            "id": event.get("id", str(uuid.uuid4())),
            "time_order": time_order,
            "event_type": event.get("event_type", "OTHER"),
            "description": event.get("description", ""),
            "agents": event.get("agents", []),
            "targets": event.get("targets", []),
            "relationship_level1": event.get("relationship_level1", ""),
            "relationship_level2": event.get("relationship_level2", ""),
            "sentiment": event.get("sentiment", ""),
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


def process_single_file(input_path: str) -> tuple:
    """
    Process a single JSON file and return relationship and ribbon data.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    relationship_data = extract_character_relationships(data)
    ribbon_data = extract_story_ribbons(data)
    
    return relationship_data, ribbon_data


def process_all_files(input_dir: str, output_dir: str):
    """
    Process all JSON files in the input directory.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_stories = []
    
    for json_file in sorted(input_path.glob("*.json")):
        print(f"Processing: {json_file.name}")
        
        try:
            relationship_data, ribbon_data = process_single_file(str(json_file))
            
            story_id = json_file.stem.replace("_v2", "")
            
            # Save individual files
            rel_output = output_path / f"{story_id}_relationships.json"
            ribbon_output = output_path / f"{story_id}_ribbons.json"
            
            with open(rel_output, "w", encoding="utf-8") as f:
                json.dump(relationship_data, f, ensure_ascii=False, indent=2)
            
            with open(ribbon_output, "w", encoding="utf-8") as f:
                json.dump(ribbon_data, f, ensure_ascii=False, indent=2)
            
            all_stories.append({
                "id": story_id,
                "title": ribbon_data["title"],
                "character_count": len(relationship_data["nodes"]),
                "event_count": ribbon_data["total_events"],
                "relationship_file": f"{story_id}_relationships.json",
                "ribbon_file": f"{story_id}_ribbons.json",
            })
            
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
    
    # Save index file
    index_output = output_path / "stories_index.json"
    with open(index_output, "w", encoding="utf-8") as f:
        json.dump({"stories": all_stories}, f, ensure_ascii=False, indent=2)
    
    print(f"\nProcessed {len(all_stories)} stories")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    # Default paths
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "datasets" / "ChineseTales" / "json_v2"
    output_dir = base_dir / "visualization" / "public" / "data"
    
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    
    process_all_files(str(input_dir), str(output_dir))

