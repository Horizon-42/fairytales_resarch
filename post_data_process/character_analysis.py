#!/usr/bin/env python3
"""
Character analysis utilities for fairytale visualization.
Handles character sorting, relationship analysis, and hero identification.
"""

from collections import defaultdict
from typing import List, Dict, Tuple, Optional


# Sentiment classification
FRIENDLY_SENTIMENTS = {'positive', 'romantic'}
HOSTILE_SENTIMENTS = {'negative', 'hostile', 'fearful'}
NEUTRAL_SENTIMENTS = {'neutral', ''}


def calculate_character_degrees(events: List[Dict], characters: List[Dict]) -> Dict[str, Dict]:
    """
    Calculate in-degree (被动) and out-degree (主动) for each character.
    
    Args:
        events: List of narrative events with agents and targets
        characters: List of character dicts with id and name
    
    Returns:
        Dict mapping character name to {in_degree, out_degree, total_degree}
    """
    char_names = {c['name'] for c in characters}
    
    # Helper to match character names (fuzzy)
    def find_char_name(name: str) -> Optional[str]:
        if name in char_names:
            return name
        for char_name in char_names:
            if name in char_name or char_name in name:
                return char_name
        return None
    
    degrees = {c['name']: {'in_degree': 0, 'out_degree': 0, 'total_degree': 0} 
               for c in characters}
    
    for event in events:
        agents = event.get('agents', [])
        targets = event.get('targets', [])
        
        for agent in agents:
            matched = find_char_name(agent)
            if matched:
                degrees[matched]['out_degree'] += 1
                degrees[matched]['total_degree'] += 1
        
        for target in targets:
            matched = find_char_name(target)
            if matched:
                degrees[matched]['in_degree'] += 1
                degrees[matched]['total_degree'] += 1
    
    return degrees


def identify_main_hero(characters: List[Dict], degrees: Dict[str, Dict]) -> Optional[str]:
    """
    Identify the main hero character.
    Priority: Hero archetype with highest total degree > highest total degree
    
    Args:
        characters: List of character dicts
        degrees: Degree information from calculate_character_degrees
    
    Returns:
        Name of the main hero character
    """
    # First, find characters with Hero archetype
    heroes = [c for c in characters if c.get('archetype', '').lower() == 'hero']
    
    if heroes:
        # Among heroes, pick the one with highest total degree
        main_hero = max(heroes, key=lambda c: degrees.get(c['name'], {}).get('total_degree', 0))
        return main_hero['name']
    
    # If no heroes, pick character with highest total degree
    if characters and degrees:
        main_char = max(characters, key=lambda c: degrees.get(c['name'], {}).get('total_degree', 0))
        return main_char['name']
    
    return None


def analyze_character_relationships_to_hero(
    events: List[Dict], 
    characters: List[Dict], 
    hero_name: str
) -> Dict[str, Dict]:
    """
    Analyze each character's relationship sentiment toward the hero.
    
    Args:
        events: List of narrative events
        characters: List of character dicts
        hero_name: Name of the main hero
    
    Returns:
        Dict mapping character name to relationship analysis:
        {
            'friendly_count': int,
            'hostile_count': int,
            'neutral_count': int,
            'affinity_score': float,  # positive = friendly, negative = hostile
            'classification': 'friendly' | 'hostile' | 'neutral'
        }
    """
    char_names = {c['name'] for c in characters}
    
    def find_char_name(name: str) -> Optional[str]:
        if name in char_names:
            return name
        for char_name in char_names:
            if name in char_name or char_name in name:
                return char_name
        return None
    
    # Initialize analysis
    analysis = {
        c['name']: {
            'friendly_count': 0,
            'hostile_count': 0,
            'neutral_count': 0,
            'affinity_score': 0.0,
            'classification': 'neutral'
        }
        for c in characters
    }
    
    hero_matched = find_char_name(hero_name)
    if not hero_matched:
        return analysis
    
    # Analyze events involving the hero
    for event in events:
        agents = [find_char_name(a) for a in event.get('agents', [])]
        targets = [find_char_name(t) for t in event.get('targets', [])]
        sentiment = event.get('sentiment', '').lower()
        
        agents = [a for a in agents if a]
        targets = [t for t in targets if t]
        
        # Check if hero is involved
        hero_is_agent = hero_matched in agents
        hero_is_target = hero_matched in targets
        
        if not (hero_is_agent or hero_is_target):
            continue
        
        # Determine other participants
        other_chars = set()
        if hero_is_agent:
            other_chars.update(targets)
        if hero_is_target:
            other_chars.update(agents)
        other_chars.discard(hero_matched)
        
        # Classify sentiment
        if sentiment in FRIENDLY_SENTIMENTS:
            sentiment_type = 'friendly'
        elif sentiment in HOSTILE_SENTIMENTS:
            sentiment_type = 'hostile'
        else:
            sentiment_type = 'neutral'
        
        # Update analysis for each other character
        for char in other_chars:
            if char in analysis:
                if sentiment_type == 'friendly':
                    analysis[char]['friendly_count'] += 1
                elif sentiment_type == 'hostile':
                    analysis[char]['hostile_count'] += 1
                else:
                    analysis[char]['neutral_count'] += 1
    
    # Calculate affinity scores and classifications
    for char_name, data in analysis.items():
        if char_name == hero_matched:
            data['classification'] = 'hero'
            data['affinity_score'] = 0  # Hero is center
            continue
        
        friendly = data['friendly_count']
        hostile = data['hostile_count']
        total = friendly + hostile + data['neutral_count']
        
        if total > 0:
            # Affinity score: positive = friendly, negative = hostile
            data['affinity_score'] = (friendly - hostile) / total
        
        # Classification based on majority
        if friendly > hostile:
            data['classification'] = 'friendly'
        elif hostile > friendly:
            data['classification'] = 'hostile'
        else:
            data['classification'] = 'neutral'
    
    return analysis


def sort_characters_for_ribbon(
    characters: List[Dict],
    degrees: Dict[str, Dict],
    hero_analysis: Dict[str, Dict],
    hero_name: str
) -> List[Dict]:
    """
    Sort characters for ribbon visualization:
    - Hero at center
    - Friendly characters above hero (sorted by affinity)
    - Hostile characters below hero (sorted by affinity)
    - Neutral characters at the edges
    
    Args:
        characters: Original character list
        degrees: Degree information
        hero_analysis: Relationship analysis toward hero
        hero_name: Name of the main hero
    
    Returns:
        Sorted list of characters with added metadata
    """
    # Add analysis data to characters
    enriched = []
    for char in characters:
        name = char['name']
        char_data = {
            **char,
            'in_degree': degrees.get(name, {}).get('in_degree', 0),
            'out_degree': degrees.get(name, {}).get('out_degree', 0),
            'total_degree': degrees.get(name, {}).get('total_degree', 0),
            'affinity_score': hero_analysis.get(name, {}).get('affinity_score', 0),
            'hero_relationship': hero_analysis.get(name, {}).get('classification', 'neutral'),
            'is_main_hero': name == hero_name,
        }
        enriched.append(char_data)
    
    # Separate into groups
    hero_char = None
    friendly_chars = []
    hostile_chars = []
    neutral_chars = []
    
    for char in enriched:
        if char['is_main_hero']:
            hero_char = char
        elif char['hero_relationship'] == 'friendly':
            friendly_chars.append(char)
        elif char['hero_relationship'] == 'hostile':
            hostile_chars.append(char)
        else:
            neutral_chars.append(char)
    
    # Sort each group by total_degree (descending) then affinity
    friendly_chars.sort(key=lambda c: (-c['affinity_score'], -c['total_degree']))
    hostile_chars.sort(key=lambda c: (c['affinity_score'], -c['total_degree']))  # Most hostile first
    neutral_chars.sort(key=lambda c: -c['total_degree'])
    
    # Build final order: friendly (top) -> hero (center) -> hostile (bottom)
    # Neutral characters go to either side based on their index
    sorted_chars = []
    
    # Add friendly characters (above hero)
    sorted_chars.extend(friendly_chars)
    
    # Add neutral characters (split between friendly and hostile sides)
    half_neutral = len(neutral_chars) // 2
    sorted_chars.extend(neutral_chars[:half_neutral])
    
    # Add hero at center
    if hero_char:
        sorted_chars.append(hero_char)
    
    # Add remaining neutral characters
    sorted_chars.extend(neutral_chars[half_neutral:])
    
    # Add hostile characters (below hero)
    sorted_chars.extend(hostile_chars)
    
    # Add display_order to each character
    for i, char in enumerate(sorted_chars):
        char['display_order'] = i
    
    return sorted_chars


def analyze_and_sort_characters(
    characters: List[Dict],
    events: List[Dict]
) -> Tuple[List[Dict], Dict]:
    """
    Main function to analyze and sort characters for visualization.
    
    Args:
        characters: List of character dicts from original data
        events: List of narrative events
    
    Returns:
        Tuple of (sorted_characters, analysis_metadata)
    """
    if not characters:
        return [], {}
    
    # Step 1: Calculate degrees
    degrees = calculate_character_degrees(events, characters)
    
    # Step 2: Identify main hero
    hero_name = identify_main_hero(characters, degrees)
    
    # Step 3: Analyze relationships to hero
    hero_analysis = {}
    if hero_name:
        hero_analysis = analyze_character_relationships_to_hero(events, characters, hero_name)
    
    # Step 4: Sort characters
    sorted_chars = sort_characters_for_ribbon(characters, degrees, hero_analysis, hero_name)
    
    # Build metadata
    metadata = {
        'main_hero': hero_name,
        'total_characters': len(characters),
        'friendly_count': sum(1 for c in sorted_chars if c.get('hero_relationship') == 'friendly'),
        'hostile_count': sum(1 for c in sorted_chars if c.get('hero_relationship') == 'hostile'),
        'neutral_count': sum(1 for c in sorted_chars if c.get('hero_relationship') == 'neutral'),
    }
    
    return sorted_chars, metadata


if __name__ == "__main__":
    # Test with sample data
    test_characters = [
        {"id": "char_0", "name": "祝英台", "archetype": "Hero"},
        {"id": "char_1", "name": "祝员外", "archetype": "Other"},
        {"id": "char_2", "name": "丫环银心", "archetype": "Sidekick/Helper"},
        {"id": "char_3", "name": "梁山伯", "archetype": "Hero"},
        {"id": "char_4", "name": "马文才", "archetype": "Villain"},
    ]
    
    test_events = [
        {"agents": ["祝英台"], "targets": ["梁山伯"], "sentiment": "romantic"},
        {"agents": ["祝员外"], "targets": ["祝英台"], "sentiment": "negative"},
        {"agents": ["丫环银心"], "targets": ["祝英台"], "sentiment": "positive"},
        {"agents": ["马文才"], "targets": ["祝英台"], "sentiment": "hostile"},
    ]
    
    sorted_chars, meta = analyze_and_sort_characters(test_characters, test_events)
    
    print("Sorted characters:")
    for c in sorted_chars:
        print(f"  {c['display_order']}: {c['name']} ({c['hero_relationship']}, affinity: {c['affinity_score']:.2f})")
    
    print(f"\nMetadata: {meta}")

