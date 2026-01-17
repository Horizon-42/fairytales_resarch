"""Quick test script for evaluation package."""

import json
from pathlib import Path
from llm_model.evaluation import (
    CharacterEvaluator,
    RelationshipEvaluator,
    SentimentEvaluator,
    ActionLayerEvaluator,
    TextSpanEvaluator,
    CompositeEvaluator
)
from llm_model.evaluation.utils import load_ground_truth

def test_character_evaluator():
    """测试角色评估器"""
    print("Testing CharacterEvaluator...")
    
    # 创建测试数据
    prediction = {
        "characters": [
            {"name": "牛郎", "alias": "牧牛郎", "archetype": "Hero"},
            {"name": "织女", "alias": "仙女", "archetype": "Lover"}
        ]
    }
    
    ground_truth = {
        "characters": [
            {"name": "牛郎", "alias": "牧牛郎; 爹爹", "archetype": "Hero"},
            {"name": "织女", "alias": "仙女; 姐姐", "archetype": "Lover"},
            {"name": "老牛", "archetype": "Mentor"}
        ]
    }
    
    evaluator = CharacterEvaluator()
    results = evaluator.evaluate(prediction, ground_truth)
    
    print(f"  Character F1: {results.get('character_f1', 'N/A')}")
    print(f"  Missing characters: {results.get('missing_characters', [])}")
    print(f"  Extra characters: {results.get('extra_characters', [])}")
    print("  ✓ CharacterEvaluator test passed!\n")
    return results

def test_relationship_evaluator():
    """测试关系评估器"""
    print("Testing RelationshipEvaluator...")
    
    prediction = {
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "relationships": [
                    {
                        "agent": "哥嫂",
                        "target": "牛郎",
                        "relationship_level1": "Family & Kinship",
                        "relationship_level2": "sibling",
                        "sentiment": "negative"
                    }
                ]
            }
        ]
    }
    
    ground_truth = {
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "relationships": [
                    {
                        "agent": "哥嫂",
                        "target": "牛郎",
                        "relationship_level1": "Family & Kinship",
                        "relationship_level2": "sibling",
                        "sentiment": "negative"
                    }
                ]
            }
        ]
    }
    
    evaluator = RelationshipEvaluator()
    results = evaluator.evaluate(prediction, ground_truth)
    
    print(f"  Relationship F1: {results.get('relationship_f1', 'N/A')}")
    print(f"  Level 1 Accuracy: {results.get('level1_accuracy', 'N/A')}")
    print("  ✓ RelationshipEvaluator test passed!\n")
    return results

def test_sentiment_evaluator():
    """测试情感评估器"""
    print("Testing SentimentEvaluator...")
    
    prediction = {
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "relationships": [
                    {
                        "agent": "哥嫂",
                        "target": "牛郎",
                        "sentiment": "negative"
                    }
                ]
            }
        ]
    }
    
    ground_truth = {
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "relationships": [
                    {
                        "agent": "哥嫂",
                        "target": "牛郎",
                        "sentiment": "negative"
                    }
                ]
            }
        ]
    }
    
    evaluator = SentimentEvaluator()
    results = evaluator.evaluate(prediction, ground_truth)
    
    print(f"  Sentiment F1: {results.get('sentiment_f1', 'N/A')}")
    print(f"  Polarity Accuracy: {results.get('sentiment_polarity_accuracy', 'N/A')}")
    print("  ✓ SentimentEvaluator test passed!\n")
    return results

def test_action_layer_evaluator():
    """测试动作层评估器"""
    print("Testing ActionLayerEvaluator...")
    
    prediction = {
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "action_layer": {
                    "category": "Physical & Conflict",
                    "type": "attack",
                    "status": "success",
                    "function": "trigger"
                }
            }
        ]
    }
    
    ground_truth = {
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "action_layer": {
                    "category": "Physical & Conflict",
                    "type": "attack",
                    "status": "success",
                    "function": "trigger"
                }
            }
        ]
    }
    
    evaluator = ActionLayerEvaluator()
    results = evaluator.evaluate(prediction, ground_truth)
    
    print(f"  Category Accuracy: {results.get('action_category_accuracy', 'N/A')}")
    print(f"  Complete Match Ratio: {results.get('action_layer_complete_match', 'N/A')}")
    print("  ✓ ActionLayerEvaluator test passed!\n")
    return results

def test_missing_gt_handling():
    """测试缺失 GT 处理"""
    print("Testing Missing GT Handling...")
    
    # 测试 GT 中 characters 为空的情况
    prediction = {
        "characters": [
            {"name": "牛郎", "archetype": "Hero"}
        ]
    }
    
    ground_truth = {
        "characters": []  # GT 缺失
    }
    
    evaluator = CharacterEvaluator()
    results = evaluator.evaluate(prediction, ground_truth)
    
    assert results.get("gt_incomplete") == True, "Should mark GT as incomplete"
    assert results.get("character_f1") is None, "F1 should be None when GT incomplete"
    print(f"  GT Incomplete: {results.get('gt_incomplete')}")
    print(f"  F1 Score: {results.get('character_f1')}")
    print("  ✓ Missing GT handling test passed!\n")
    return results

def test_composite_evaluator():
    """测试组合评估器"""
    print("Testing CompositeEvaluator...")
    
    prediction = {
        "source_info": {
            "text_content": "这是一个测试文本。它包含多个句子。用于测试文本分割。"
        },
        "characters": [
            {"name": "牛郎", "archetype": "Hero"}
        ],
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "text_span": {
                    "start": 0,
                    "end": 10,
                    "text": "这是一个测试文本。"
                },
                "relationships": [],
                "action_layer": {
                    "category": "Physical & Conflict",
                    "type": "attack"
                }
            }
        ]
    }
    
    ground_truth = {
        "source_info": {
            "text_content": "这是一个测试文本。它包含多个句子。用于测试文本分割。"
        },
        "characters": [
            {"name": "牛郎", "archetype": "Hero"}
        ],
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "text_span": {
                    "start": 0,
                    "end": 10,
                    "text": "这是一个测试文本。"
                },
                "relationships": [],
                "action_layer": {
                    "category": "Physical & Conflict",
                    "type": "attack"
                }
            }
        ]
    }
    
    evaluator = CompositeEvaluator()
    results = evaluator.evaluate(prediction, ground_truth)
    
    print(f"  Overall Score: {results.get('overall_score', 'N/A')}")
    print(f"  Component Scores: {results.get('component_scores', {})}")
    print("  ✓ CompositeEvaluator test passed!\n")
    return results

if __name__ == "__main__":
    print("=" * 60)
    print("Evaluation Package Quick Test")
    print("=" * 60 + "\n")
    
    try:
        test_character_evaluator()
        test_relationship_evaluator()
        test_sentiment_evaluator()
        test_action_layer_evaluator()
        test_missing_gt_handling()
        test_composite_evaluator()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()