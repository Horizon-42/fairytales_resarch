"""Utility functions for character matching and alias resolution."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any


def normalize_name(name: str) -> str:
    """Normalize character name for comparison."""
    return name.strip().lower().replace(" ", "")


def extract_aliases(character: Dict[str, Any]) -> List[str]:
    """Extract all aliases from a character dict.
    
    Args:
        character: Dict with 'name' and optionally 'alias' fields
        
    Returns:
        List of normalized names (main name + aliases)
    """
    names = [character.get("name", "")]
    alias_str = character.get("alias", "")
    if alias_str:
        # Aliases are separated by semicolons
        aliases = [a.strip() for a in alias_str.split(";") if a.strip()]
        names.extend(aliases)
    return [normalize_name(n) for n in names if n]


def find_character_match(
    name: str,
    characters: List[Dict[str, Any]],
    threshold: float = 0.8
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Find if a name matches an existing character by name or alias.
    
    Args:
        name: Name to search for
        characters: List of character dicts to search in
        threshold: Similarity threshold (for future fuzzy matching)
        
    Returns:
        Tuple of (index, character_dict) if match found, else None
    """
    normalized_search = normalize_name(name)
    
    for idx, char in enumerate(characters):
        aliases = extract_aliases(char)
        if normalized_search in aliases:
            return (idx, char)
    
    # Simple substring matching (could be enhanced with fuzzy matching)
    for idx, char in enumerate(characters):
        aliases = extract_aliases(char)
        for alias in aliases:
            if normalized_search in alias or alias in normalized_search:
                return (idx, char)
    
    return None


def resolve_character_aliases(
    extracted_characters: List[str],
    existing_characters: List[Dict[str, Any]]
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Resolve character aliases and update global character list.
    
    Args:
        extracted_characters: List of character names extracted from text
        existing_characters: Existing global character list
        
    Returns:
        Tuple of (resolved_names, updated_characters_list)
        - resolved_names: List of names that match existing characters (or normalized)
        - updated_characters: Updated character list with new characters added
    """
    updated = existing_characters.copy()
    resolved = []
    seen = set()
    
    for name in extracted_characters:
        if not name or not name.strip():
            continue
            
        # Check if already seen in this batch
        normalized = normalize_name(name)
        if normalized in seen:
            continue
        seen.add(normalized)
        
        # Try to match with existing character
        match = find_character_match(name, updated)
        if match:
            idx, char = match
            # Use the main name from existing character
            resolved.append(char.get("name", name))
        else:
            # New character - add to list
            new_char = {
                "name": name,
                "alias": "",
                "archetype": "Other"  # Default, could be improved
            }
            updated.append(new_char)
            resolved.append(name)
    
    return resolved, updated


def classify_target_type(receivers: List[str], characters: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Determine if receivers are characters or objects.
    
    Args:
        receivers: List of receiver names
        characters: Global character list
        
    Returns:
        Tuple of (target_type, object_type)
        - target_type: "character" or "object"
        - object_type: "normal_object", "magical_agent", or "price" (if target_type is "object")
    """
    if not receivers:
        return "object", "normal_object"
    
    # Check if all receivers are in character list
    character_names = {normalize_name(c.get("name", "")) for c in characters}
    receiver_normalized = {normalize_name(r) for r in receivers}
    
    if receiver_normalized.intersection(character_names):
        # At least one receiver is a character
        return "character", ""
    
    # All receivers are objects
    # This is a simplified classification - could be enhanced with LLM
    return "object", "normal_object"
