#!/usr/bin/env python3
"""
Character analysis utilities for fairytale visualization.
Handles character sorting, relationship analysis, and hero identification.

Updated logic:
1. Uses Friendly Level values for voting:
   - romantic: +2, positive: +1, neutral: +1
   - negative: -1, fearful: -2, hostile: -2
2. Camp classification based on total friendly level (active behaviors only)
3. Per-event friendliness tracking for ribbon gradient coloring
4. Initial color tone based on first interaction's friendly level
"""

import networkx as nx
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


# Friendly Level mapping from sentiment.csv
FRIENDLY_LEVELS = {
    'romantic': 2,
    'positive': 1,
    'neutral': 1,
    'negative': -1,
    'fearful': -2,
    'hostile': -2,
}

# Default level for unknown sentiments
DEFAULT_FRIENDLY_LEVEL = 0


def get_friendly_level(sentiment: str) -> int:
    """Get the friendly level for a sentiment."""
    return FRIENDLY_LEVELS.get(sentiment.lower().strip(), DEFAULT_FRIENDLY_LEVEL)


def build_interaction_graph(events: List[Dict], characters: List[Dict]) -> nx.Graph:
    """
    Build a weighted undirected graph from character interactions.
    Edge weights represent interaction frequency.
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
    """
    if len(G.nodes()) == 0:
        return {}
    
    try:
        degree_cent = nx.degree_centrality(G)
        
        try:
            eigen_cent = nx.eigenvector_centrality_numpy(G, weight='weight')
        except:
            eigen_cent = {n: 0 for n in G.nodes()}
        
        combined = {}
        for node in G.nodes():
            combined[node] = 0.6 * degree_cent.get(node, 0) + 0.4 * eigen_cent.get(node, 0)
        
        return combined
    except Exception as e:
        return {n: G.degree(n) / max(1, len(G.nodes()) - 1) for n in G.nodes()}


def identify_main_hero(characters: List[Dict], centrality: Dict[str, float]) -> Optional[str]:
    """
    Identify the main hero character based on centrality.
    Priority: Hero archetype with highest centrality > highest centrality overall
    """
    heroes = [c for c in characters if c.get('archetype', '').lower() == 'hero']
    
    if heroes:
        main_hero = max(heroes, key=lambda c: centrality.get(c['name'], 0))
        return main_hero['name']
    
    if characters and centrality:
        main_char = max(characters, key=lambda c: centrality.get(c['name'], 0))
        return main_char['name']
    
    return None


def analyze_character_relationships_with_levels(
    events: List[Dict], 
    characters: List[Dict], 
    hero_name: str
) -> Tuple[Dict[str, Dict], Dict[str, List[Dict]]]:
    """
    Analyze each character's relationship to the hero using Friendly Levels.
    
    Voting rules (for camp classification):
    - Only count when OTHER CHARACTER is AGENT (acting towards hero)
    - Sum up friendly levels from all interactions
    - Total > 0: friendly camp, Total < 0: hostile camp, Total == 0: use last interaction
    
    Also tracks per-event friendliness for gradient coloring.
    
    Args:
        events: List of narrative events (should be sorted by time_order)
        characters: List of character dicts
        hero_name: Name of the main hero
    
    Returns:
        Tuple of:
        - Dict mapping character name to relationship analysis
        - Dict mapping character name to per-event friendliness history
    """
    char_names = {c['name'] for c in characters}
    
    def find_char_name(name: str) -> Optional[str]:
        if name in char_names:
            return name
        for char_name in char_names:
            if name in char_name or char_name in name:
                return char_name
        return None
    
    # Track votes using friendly levels
    char_votes = {
        c['name']: {
            'total_level': 0,           # Sum of friendly levels (for camp)
            'last_level': None,         # Last interaction's level (for tiebreaker)
            'last_time': -1,            # Time of last interaction
            'first_level': None,        # First interaction's level (for initial color)
            'interaction_count': 0,     # Number of interactions
        }
        for c in characters
    }
    
    # Track per-event friendliness for each character
    # {char_name: [{time_order: int, friendly_level: int, cumulative_level: int}]}
    char_event_history = {c['name']: [] for c in characters}
    
    hero_matched = find_char_name(hero_name)
    if not hero_matched:
        return {
            c['name']: {
                'total_level': 0,
                'classification': 'friendly',
                'first_level': 0,
                'interaction_count': 0,
            }
            for c in characters
        }, char_event_history
    
    # Sort events by time_order
    sorted_events = sorted(events, key=lambda e: e.get('time_order', 0))
    
    # Process each event
    for event in sorted_events:
        agents = [find_char_name(a) for a in event.get('agents', [])]
        targets = [find_char_name(t) for t in event.get('targets', [])]
        agents = [a for a in agents if a]
        targets = [t for t in targets if t]
        
        sentiment = event.get('sentiment', '').lower()
        time_order = event.get('time_order', 0)
        friendly_level = get_friendly_level(sentiment)
        
        # Track all participants in this event for per-event friendliness
        all_participants = set(agents + targets)
        
        # Case 1: Hero is TARGET - other characters (agents) are acting on hero
        # This determines their CAMP classification
        if hero_matched in targets:
            for agent in agents:
                if agent and agent != hero_matched and agent in char_votes:
                    # Add to total level for camp classification
                    char_votes[agent]['total_level'] += friendly_level
                    char_votes[agent]['last_level'] = friendly_level
                    char_votes[agent]['last_time'] = time_order
                    char_votes[agent]['interaction_count'] += 1
                    
                    # Track first interaction level
                    if char_votes[agent]['first_level'] is None:
                        char_votes[agent]['first_level'] = friendly_level
        
        # Case 2: Hero is AGENT - hero is acting on other characters (targets)
        # Only hostile actions count for camp (hero attacking = enemy)
        if hero_matched in agents:
            for target in targets:
                if target and target != hero_matched and target in char_votes:
                    if friendly_level < 0:
                        # Hero attacking someone = they are hostile
                        char_votes[target]['total_level'] += friendly_level
                        char_votes[target]['last_level'] = friendly_level
                        char_votes[target]['last_time'] = time_order
                        char_votes[target]['interaction_count'] += 1
                        
                        if char_votes[target]['first_level'] is None:
                            char_votes[target]['first_level'] = friendly_level
        
        # Track per-event friendliness ONLY for direct interactions with hero
        # This determines the gradient coloring of ribbons
        for char_name in all_participants:
            if char_name and char_name != hero_matched and char_name in char_event_history:
                # Determine this character's friendly level in this event
                char_is_agent = char_name in agents
                char_is_target = char_name in targets
                hero_is_agent = hero_matched in agents
                hero_is_target = hero_matched in targets
                
                event_level = None  # Default: no direct interaction with hero
                
                # Case 1: Character is AGENT acting on HERO (direct interaction)
                # e.g., 老牛 helps 牛郎, 王母娘娘 attacks 牛郎
                if char_is_agent and hero_is_target:
                    event_level = friendly_level
                
                # Case 2: HERO is AGENT acting on CHARACTER (direct interaction)
                # e.g., 牛郎 attacks enemy, 牛郎 helps friend
                elif hero_is_agent and char_is_target:
                    # Hero's action towards character affects their relationship
                    # Negative: hero attacking them = they're hostile
                    # Positive: hero helping them = doesn't make them friendly (they didn't act)
                    if friendly_level < 0:
                        event_level = friendly_level
                    # else: don't record positive actions from hero
                
                # Case 3: Co-participants (both agents or both targets) - NO DIRECT INTERACTION
                # e.g., 天帝 attacks both 牛郎 and 织女 - 织女 is victim, not hostile
                # DO NOT inherit event sentiment - this was the bug!
                # else: event_level stays None
                
                if event_level is not None:
                    # Calculate cumulative level
                    history = char_event_history[char_name]
                    prev_cumulative = history[-1]['cumulative_level'] if history else 0
                    
                    char_event_history[char_name].append({
                        'time_order': time_order,
                        'friendly_level': event_level,
                        'cumulative_level': prev_cumulative + event_level,
                        'sentiment': sentiment,
                    })
    
    # Build final analysis
    analysis = {}
    for char_name, votes in char_votes.items():
        if char_name == hero_matched:
            analysis[char_name] = {
                'total_level': 0,
                'classification': 'hero',
                'first_level': 0,
                'interaction_count': 0,
            }
            continue
        
        total = votes['total_level']
        first_level = votes['first_level'] if votes['first_level'] is not None else 0
        
        # Determine classification by total friendly level
        if total > 0:
            classification = 'friendly'
        elif total < 0:
            classification = 'hostile'
        else:
            # Tie (total == 0): use last interaction, or default to friendly
            last_level = votes['last_level']
            if last_level is not None and last_level < 0:
                classification = 'hostile'
            else:
                classification = 'friendly'
        
        analysis[char_name] = {
            'total_level': total,
            'classification': classification,
            'first_level': first_level,
            'interaction_count': votes['interaction_count'],
        }
    
    return analysis, char_event_history


def sort_characters_for_ribbon(
    characters: List[Dict],
    centrality: Dict[str, float],
    hero_analysis: Dict[str, Dict],
    hero_name: str,
    event_history: Dict[str, List[Dict]]
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
        event_history: Per-event friendliness history for gradient coloring
    
    Returns:
        Sorted list of characters with added metadata
    """
    # Add analysis data to characters
    enriched = []
    for char in characters:
        name = char['name']
        char_analysis = hero_analysis.get(name, {})
        
        char_data = {
            **char,
            'centrality': centrality.get(name, 0),
            'hero_relationship': char_analysis.get('classification', 'friendly'),
            'is_main_hero': name == hero_name,
            'total_level': char_analysis.get('total_level', 0),
            'first_level': char_analysis.get('first_level', 0),
            'interaction_count': char_analysis.get('interaction_count', 0),
            'event_friendliness': event_history.get(name, []),  # Per-event data for gradients
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
            friendly_chars.append(char)
    
    # Sort each group by centrality (highest centrality = closest to hero)
    friendly_chars.sort(key=lambda c: c['centrality'])  # Low to high (high at bottom, near hero)
    hostile_chars.sort(key=lambda c: -c['centrality'])  # High to low (high at top, near hero)
    
    # Build final order
    sorted_chars = []
    sorted_chars.extend(friendly_chars)
    if hero_char:
        sorted_chars.append(hero_char)
    sorted_chars.extend(hostile_chars)
    
    # Add display_order
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
    1. Friendly Level-based voting for camp classification
    2. Centrality-based ordering
    3. Per-event friendliness tracking for gradient coloring
    
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
    
    # Step 3: Analyze relationships using friendly levels
    hero_analysis = {}
    event_history = {}
    if hero_name:
        hero_analysis, event_history = analyze_character_relationships_with_levels(
            events, characters, hero_name
        )
    
    # Step 4: Sort characters
    sorted_chars = sort_characters_for_ribbon(
        characters, centrality, hero_analysis, hero_name, event_history
    )
    
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
        {"time_order": 5, "agents": ["祝员外"], "targets": ["祝英台"], "sentiment": "positive"},
    ]
    
    sorted_chars, meta = analyze_and_sort_characters(test_characters, test_events)
    
    print("Sorted characters (by centrality, grouped by relationship):")
    print("=" * 60)
    for c in sorted_chars:
        hero_rel = c['hero_relationship']
        marker = "★" if c['is_main_hero'] else " "
        print(f"  {marker} {c['display_order']}: {c['name']}")
        print(f"      Relationship: {hero_rel}, Centrality: {c['centrality']:.3f}")
        print(f"      Total Level: {c['total_level']}, First Level: {c['first_level']}")
        if c['event_friendliness']:
            print(f"      Event History: {c['event_friendliness']}")
    
    print(f"\nMetadata: {meta}")
