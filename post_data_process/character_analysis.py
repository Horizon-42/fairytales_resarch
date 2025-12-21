#!/usr/bin/env python3
"""
Character analysis utilities for fairytale visualization.
Handles character sorting, relationship analysis, and hero identification.

Updated logic:
1. Hostility/friendliness determined by voting across all narratives
   - If equal votes, later (more recent) interaction decides
   - Neutral characters treated as friendly
2. Centrality used for character importance ordering
   - Higher centrality = closer to hero
   - Hero identified by highest centrality among Hero archetypes
"""

import networkx as nx
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


# Sentiment classification
FRIENDLY_SENTIMENTS = {'positive', 'romantic', 'respectful', 'grateful'}
HOSTILE_SENTIMENTS = {'negative', 'hostile', 'fearful', 'antagonistic'}
NEUTRAL_SENTIMENTS = {'neutral', ''}


def build_interaction_graph(events: List[Dict], characters: List[Dict]) -> nx.Graph:
    """
    Build a weighted undirected graph from character interactions.
    Edge weights represent interaction frequency.
    
    Args:
        events: List of narrative events with agents and targets
        characters: List of character dicts
    
    Returns:
        NetworkX graph with characters as nodes and interactions as edges
    """
    char_names = {c['name'] for c in characters}
    
    def find_char_name(name: str) -> Optional[str]:
        if name in char_names:
            return name
        for char_name in char_names:
            if name in char_name or char_name in name:
                return char_name
        return None
    
    G = nx.Graph()
    
    # Add all characters as nodes
    for char in characters:
        G.add_node(char['name'], archetype=char.get('archetype', ''))
    
    # Add edges from events
    for event in events:
        agents = [find_char_name(a) for a in event.get('agents', [])]
        targets = [find_char_name(t) for t in event.get('targets', [])]
        agents = [a for a in agents if a]
        targets = [t for t in targets if t]
        
        # Create edges between all participants
        all_participants = set(agents + targets)
        participants = list(all_participants)
        
        for i in range(len(participants)):
            for j in range(i + 1, len(participants)):
                if G.has_edge(participants[i], participants[j]):
                    G[participants[i]][participants[j]]['weight'] += 1
                else:
                    G.add_edge(participants[i], participants[j], weight=1)
    
    return G


def calculate_centrality(G: nx.Graph) -> Dict[str, float]:
    """
    Calculate centrality scores for all characters.
    Uses a combination of degree centrality and eigenvector centrality.
    
    Args:
        G: NetworkX graph of character interactions
    
    Returns:
        Dict mapping character name to centrality score
    """
    if len(G.nodes()) == 0:
        return {}
    
    # Calculate different centrality measures
    try:
        # Weighted degree centrality
        degree_cent = nx.degree_centrality(G)
        
        # Try eigenvector centrality (may fail for disconnected graphs)
        try:
            eigen_cent = nx.eigenvector_centrality_numpy(G, weight='weight')
        except:
            eigen_cent = {n: 0 for n in G.nodes()}
        
        # Combine centralities (weighted average)
        combined = {}
        for node in G.nodes():
            # Weight: 60% degree, 40% eigenvector
            combined[node] = 0.6 * degree_cent.get(node, 0) + 0.4 * eigen_cent.get(node, 0)
        
        return combined
    except Exception as e:
        # Fallback to simple degree
        return {n: G.degree(n) / max(1, len(G.nodes()) - 1) for n in G.nodes()}


def identify_main_hero(characters: List[Dict], centrality: Dict[str, float]) -> Optional[str]:
    """
    Identify the main hero character based on centrality.
    Priority: Hero archetype with highest centrality > highest centrality overall
    
    Args:
        characters: List of character dicts
        centrality: Centrality scores from calculate_centrality
    
    Returns:
        Name of the main hero character
    """
    # First, find characters with Hero archetype
    heroes = [c for c in characters if c.get('archetype', '').lower() == 'hero']
    
    if heroes:
        # Among heroes, pick the one with highest centrality
        main_hero = max(heroes, key=lambda c: centrality.get(c['name'], 0))
        return main_hero['name']
    
    # If no heroes, pick character with highest centrality
    if characters and centrality:
        main_char = max(characters, key=lambda c: centrality.get(c['name'], 0))
        return main_char['name']
    
    return None


def analyze_character_relationships_voting(
    events: List[Dict], 
    characters: List[Dict], 
    hero_name: str
) -> Dict[str, Dict]:
    """
    Analyze each character's relationship to the hero using voting.
    
    Voting rules:
    - Only count sentiment when OTHER CHARACTER is the AGENT (acting towards hero)
    - When hero is agent, hostile sentiment towards X counts as hostile for X
      (hero attacking X means X is likely hostile)
    - When hero is agent with positive sentiment, it does NOT make target friendly
      (hero showing kindness doesn't mean target is friendly)
    - If friendly > hostile: friendly
    - If hostile > friendly: hostile  
    - If equal: use the most recent (later time_order) interaction
    - Neutral characters (no interactions) are treated as friendly
    
    Args:
        events: List of narrative events (should be sorted by time_order)
        characters: List of character dicts
        hero_name: Name of the main hero
    
    Returns:
        Dict mapping character name to relationship analysis
    """
    char_names = {c['name'] for c in characters}
    
    def find_char_name(name: str) -> Optional[str]:
        if name in char_names:
            return name
        for char_name in char_names:
            if name in char_name or char_name in name:
                return char_name
        return None
    
    # Track votes and last interaction for each character
    # Structure: {char_name: {'friendly': count, 'hostile': count, 'last_sentiment': str, 'last_time': int}}
    char_votes = {
        c['name']: {
            'friendly_votes': 0,
            'hostile_votes': 0,
            'last_sentiment': None,
            'last_time': -1
        }
        for c in characters
    }
    
    hero_matched = find_char_name(hero_name)
    if not hero_matched:
        # Return neutral for all if hero not found
        return {
            c['name']: {
                'friendly_count': 0,
                'hostile_count': 0,
                'affinity_score': 0.0,
                'classification': 'friendly'  # Default to friendly
            }
            for c in characters
        }
    
    # Sort events by time_order to ensure correct "last" determination
    sorted_events = sorted(events, key=lambda e: e.get('time_order', 0))
    
    # Analyze events involving the hero
    for event in sorted_events:
        agents = [find_char_name(a) for a in event.get('agents', [])]
        targets = [find_char_name(t) for t in event.get('targets', [])]
        agents = [a for a in agents if a]
        targets = [t for t in targets if t]
        
        sentiment = event.get('sentiment', '').lower()
        time_order = event.get('time_order', 0)
        
        # Classify sentiment
        if sentiment in FRIENDLY_SENTIMENTS:
            sentiment_type = 'friendly'
        elif sentiment in HOSTILE_SENTIMENTS:
            sentiment_type = 'hostile'
        else:
            sentiment_type = 'neutral'
        
        # Case 1: Hero is TARGET - other characters (agents) are acting on hero
        # This directly reflects how they treat the hero
        if hero_matched in targets:
            for agent in agents:
                if agent and agent != hero_matched and agent in char_votes:
                    if sentiment_type == 'friendly':
                        char_votes[agent]['friendly_votes'] += 1
                    elif sentiment_type == 'hostile':
                        char_votes[agent]['hostile_votes'] += 1
                    char_votes[agent]['last_sentiment'] = sentiment_type
                    char_votes[agent]['last_time'] = time_order
        
        # Case 2: Hero is AGENT - hero is acting on other characters (targets)
        # Only hostile actions from hero indicate hostile relationship
        # (If hero attacks X, X is likely an enemy)
        # Friendly actions from hero do NOT make targets friendly
        # (Hero showing kindness to antagonist doesn't make them friendly)
        if hero_matched in agents:
            for target in targets:
                if target and target != hero_matched and target in char_votes:
                    if sentiment_type == 'hostile':
                        # Hero attacking someone = they are hostile
                        char_votes[target]['hostile_votes'] += 1
                        char_votes[target]['last_sentiment'] = 'hostile'
                        char_votes[target]['last_time'] = time_order
                    # Note: friendly sentiment from hero is ignored for classification
    
    # Build final analysis with voting results
    analysis = {}
    for char_name, votes in char_votes.items():
        if char_name == hero_matched:
            analysis[char_name] = {
                'friendly_count': votes['friendly_votes'],
                'hostile_count': votes['hostile_votes'],
                'affinity_score': 0.0,
                'classification': 'hero'
            }
            continue
        
        friendly = votes['friendly_votes']
        hostile = votes['hostile_votes']
        total = friendly + hostile
        
        # Calculate affinity score
        if total > 0:
            affinity_score = (friendly - hostile) / total
        else:
            affinity_score = 0.0
        
        # Determine classification by voting
        if friendly > hostile:
            classification = 'friendly'
        elif hostile > friendly:
            classification = 'hostile'
        else:
            # Tie: use last interaction, or default to friendly
            last_sentiment = votes['last_sentiment']
            if last_sentiment == 'hostile':
                classification = 'hostile'
            else:
                # Neutral or friendly or no interaction -> friendly
                classification = 'friendly'
        
        analysis[char_name] = {
            'friendly_count': friendly,
            'hostile_count': hostile,
            'affinity_score': affinity_score,
            'classification': classification
        }
    
    return analysis


def sort_characters_for_ribbon(
    characters: List[Dict],
    centrality: Dict[str, float],
    hero_analysis: Dict[str, Dict],
    hero_name: str
) -> List[Dict]:
    """
    Sort characters for ribbon visualization using centrality.
    
    - Hero at center
    - Friendly characters above hero, sorted by centrality (highest closest to hero)
    - Hostile characters below hero, sorted by centrality (highest closest to hero)
    
    Args:
        characters: Original character list
        centrality: Centrality scores
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
            'centrality': centrality.get(name, 0),
            'affinity_score': hero_analysis.get(name, {}).get('affinity_score', 0),
            'hero_relationship': hero_analysis.get(name, {}).get('classification', 'friendly'),
            'is_main_hero': name == hero_name,
            'friendly_count': hero_analysis.get(name, {}).get('friendly_count', 0),
            'hostile_count': hero_analysis.get(name, {}).get('hostile_count', 0),
        }
        enriched.append(char_data)
    
    # Separate into groups
    hero_char = None
    friendly_chars = []
    hostile_chars = []
    
    for char in enriched:
        if char['is_main_hero']:
            hero_char = char
        elif char['hero_relationship'] == 'hostile':
            hostile_chars.append(char)
        else:
            # Friendly and neutral both go to friendly side
            friendly_chars.append(char)
    
    # Sort each group by centrality (highest centrality = closest to hero)
    # For friendly: highest centrality at the bottom (closest to hero)
    # For hostile: highest centrality at the top (closest to hero)
    friendly_chars.sort(key=lambda c: c['centrality'])  # Low to high (high at bottom, near hero)
    hostile_chars.sort(key=lambda c: -c['centrality'])  # High to low (high at top, near hero)
    
    # Build final order: friendly (top, low centrality first) -> hero -> hostile (bottom, high centrality first)
    sorted_chars = []
    
    # Add friendly characters (above hero)
    sorted_chars.extend(friendly_chars)
    
    # Add hero at center
    if hero_char:
        sorted_chars.append(hero_char)
    
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
    
    Uses:
    1. Voting-based hostility/friendliness determination
    2. Centrality-based ordering
    
    Args:
        characters: List of character dicts from original data
        events: List of narrative events
    
    Returns:
        Tuple of (sorted_characters, analysis_metadata)
    """
    if not characters:
        return [], {}
    
    # Step 1: Build interaction graph and calculate centrality
    G = build_interaction_graph(events, characters)
    centrality = calculate_centrality(G)
    
    # Step 2: Identify main hero (by centrality)
    hero_name = identify_main_hero(characters, centrality)
    
    # Step 3: Analyze relationships using voting
    hero_analysis = {}
    if hero_name:
        hero_analysis = analyze_character_relationships_voting(events, characters, hero_name)
    
    # Step 4: Sort characters by centrality within groups
    sorted_chars = sort_characters_for_ribbon(characters, centrality, hero_analysis, hero_name)
    
    # Build metadata
    metadata = {
        'main_hero': hero_name,
        'hero_centrality': centrality.get(hero_name, 0) if hero_name else 0,
        'total_characters': len(characters),
        'friendly_count': sum(1 for c in sorted_chars if c.get('hero_relationship') == 'friendly'),
        'hostile_count': sum(1 for c in sorted_chars if c.get('hero_relationship') == 'hostile'),
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
        {"time_order": 1, "agents": ["祝英台"], "targets": ["梁山伯"], "sentiment": "romantic"},
        {"time_order": 2, "agents": ["祝员外"], "targets": ["祝英台"], "sentiment": "negative"},
        {"time_order": 3, "agents": ["丫环银心"], "targets": ["祝英台"], "sentiment": "positive"},
        {"time_order": 4, "agents": ["马文才"], "targets": ["祝英台"], "sentiment": "hostile"},
        {"time_order": 5, "agents": ["祝员外"], "targets": ["祝英台"], "sentiment": "positive"},  # Changes to friendly
    ]
    
    sorted_chars, meta = analyze_and_sort_characters(test_characters, test_events)
    
    print("Sorted characters (by centrality, grouped by relationship):")
    print("=" * 60)
    for c in sorted_chars:
        hero_rel = c['hero_relationship']
        marker = "★" if c['is_main_hero'] else " "
        print(f"  {marker} {c['display_order']}: {c['name']}")
        print(f"      Relationship: {hero_rel}, Centrality: {c['centrality']:.3f}")
        print(f"      Friendly votes: {c['friendly_count']}, Hostile votes: {c['hostile_count']}")
    
    print(f"\nMetadata: {meta}")
