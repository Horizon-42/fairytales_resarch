"""Unit tests for utility functions."""

import pytest

from llm_model.full_detection.utils import (
    classify_target_type,
    extract_aliases,
    find_character_match,
    normalize_name,
    resolve_character_aliases,
)


class TestNormalizeName:
    """Tests for normalize_name function."""
    
    def test_basic_normalization(self):
        """Test basic name normalization."""
        assert normalize_name("牛郎") == "牛郎"
        assert normalize_name(" 牛郎 ") == "牛郎"
        assert normalize_name("牛 郎") == "牛郎"
        assert normalize_name("") == ""
    
    def test_case_insensitive(self):
        """Test case insensitive normalization (if applicable)."""
        # Note: This depends on implementation, but typically lowercase
        assert normalize_name("HERO") == "hero"
        assert normalize_name("Hero") == "hero"


class TestExtractAliases:
    """Tests for extract_aliases function."""
    
    def test_single_name(self):
        """Test character with single name."""
        char = {"name": "牛郎", "alias": ""}
        aliases = extract_aliases(char)
        assert "牛郎" in aliases
        assert len(aliases) == 1
    
    def test_with_aliases(self):
        """Test character with multiple aliases."""
        char = {"name": "一儿一女", "alias": "孩子;一对儿女;儿女们"}
        aliases = extract_aliases(char)
        assert normalize_name("一儿一女") in aliases
        assert normalize_name("孩子") in aliases
        assert normalize_name("一对儿女") in aliases
        assert normalize_name("儿女们") in aliases
        assert len(aliases) == 4
    
    def test_no_alias_field(self):
        """Test character without alias field."""
        char = {"name": "牛郎"}
        aliases = extract_aliases(char)
        assert normalize_name("牛郎") in aliases
        assert len(aliases) == 1


class TestFindCharacterMatch:
    """Tests for find_character_match function."""
    
    def test_exact_match(self):
        """Test exact name match."""
        characters = [
            {"name": "牛郎", "alias": ""},
            {"name": "织女", "alias": ""},
        ]
        match = find_character_match("牛郎", characters)
        assert match is not None
        idx, char = match
        assert char["name"] == "牛郎"
        assert idx == 0
    
    def test_alias_match(self):
        """Test alias matching."""
        characters = [
            {"name": "一儿一女", "alias": "孩子;一对儿女"},
        ]
        match = find_character_match("孩子", characters)
        assert match is not None
        idx, char = match
        assert char["name"] == "一儿一女"
    
    def test_no_match(self):
        """Test when no match is found."""
        characters = [
            {"name": "牛郎", "alias": ""},
        ]
        match = find_character_match("织女", characters)
        assert match is None
    
    def test_empty_characters_list(self):
        """Test with empty character list."""
        match = find_character_match("牛郎", [])
        assert match is None


class TestResolveCharacterAliases:
    """Tests for resolve_character_aliases function."""
    
    def test_new_characters(self):
        """Test adding new characters."""
        existing = [
            {"name": "牛郎", "alias": "", "archetype": "Hero"},
        ]
        extracted = ["织女", "天帝"]
        
        resolved, updated = resolve_character_aliases(extracted, existing)
        
        assert "织女" in resolved
        assert "天帝" in resolved
        assert len(updated) == 3  # original + 2 new
    
    def test_alias_resolution(self):
        """Test resolving aliases to existing characters."""
        existing = [
            {"name": "一儿一女", "alias": "孩子;一对儿女", "archetype": "Everyman"},
        ]
        extracted = ["孩子", "牛郎"]
        
        resolved, updated = resolve_character_aliases(extracted, existing)
        
        # "孩子" should resolve to "一儿一女"
        assert "一儿一女" in resolved or "孩子" in resolved
        assert "牛郎" in resolved
        # Should not add duplicate
        assert len(updated) <= 3
    
    def test_duplicate_removal(self):
        """Test removing duplicate names in extracted list."""
        existing = []
        extracted = ["牛郎", "牛郎", "织女"]
        
        resolved, updated = resolve_character_aliases(extracted, existing)
        
        # Should only have unique names
        assert len(resolved) == 2
        assert "牛郎" in resolved
        assert "织女" in resolved
    
    def test_empty_inputs(self):
        """Test with empty inputs."""
        resolved, updated = resolve_character_aliases([], [])
        assert resolved == []
        assert updated == []


class TestClassifyTargetType:
    """Tests for classify_target_type function."""
    
    def test_character_targets(self):
        """Test when receivers are characters."""
        characters = [
            {"name": "牛郎", "alias": ""},
            {"name": "织女", "alias": ""},
        ]
        receivers = ["牛郎", "织女"]
        
        target_type, object_type = classify_target_type(receivers, characters)
        assert target_type == "character"
        assert object_type == ""
    
    def test_object_targets(self):
        """Test when receivers are objects."""
        characters = [
            {"name": "牛郎", "alias": ""},
        ]
        receivers = ["天衣", "银河"]
        
        target_type, object_type = classify_target_type(receivers, characters)
        assert target_type == "object"
        assert object_type == "normal_object"
    
    def test_mixed_targets(self):
        """Test when some receivers are characters."""
        characters = [
            {"name": "牛郎", "alias": ""},
        ]
        receivers = ["牛郎", "天衣"]
        
        target_type, object_type = classify_target_type(receivers, characters)
        assert target_type == "character"  # At least one is character
    
    def test_empty_receivers(self):
        """Test with empty receivers."""
        characters = []
        receivers = []
        
        target_type, object_type = classify_target_type(receivers, characters)
        assert target_type == "object"
        assert object_type == "normal_object"
