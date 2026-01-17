"""Example usage of the evaluation package with real data."""

import json
from pathlib import Path
from llm_model.evaluation import CompositeEvaluator
from llm_model.evaluation.utils import load_ground_truth, load_prediction

def example_evaluate_single_file():
    """示例：评估单个文件的预测结果"""
    print("=" * 60)
    print("Example 1: Evaluating a single file")
    print("=" * 60)
    
    # 假设这是你的预测结果（可以作为参数传入）
    # 这里我们使用 GT 数据作为示例（实际使用时应该传入 LLM 的预测结果）
    
    gt_path = "datasets/ChineseTales/json_v3/CH_002_牛郎织女_v3.json"
    
    if not Path(gt_path).exists():
        print(f"File not found: {gt_path}")
        print("Please provide valid paths to ground truth and prediction files.")
        return
    
    # 加载 Ground Truth
    ground_truth = load_ground_truth(gt_path)
    
    # 假设这是预测结果（实际使用时替换为真实的预测结果）
    # 这里为了演示，我们使用 GT 数据作为"完美预测"
    prediction = ground_truth.copy()
    
    # 创建组合评估器
    composite = CompositeEvaluator()
    
    # 执行评估
    results = composite.evaluate(prediction, ground_truth)
    
    # 打印结果
    print(f"\nOverall Score: {results['overall_score']:.3f}")
    print("\nComponent Scores:")
    for component, score in results['component_scores'].items():
        if score is not None:
            print(f"  - {component}: {score:.3f}")
        else:
            print(f"  - {component}: N/A (GT incomplete)")
    
    # 生成报告（可选）
    # composite.generate_report(results, output_path="evaluation_report.json", format="json")
    # composite.generate_report(results, output_path="evaluation_report.md", format="markdown")
    
    print("\n✓ Evaluation completed!")


def example_evaluate_multiple_files():
    """示例：批量评估多个文件"""
    print("\n" + "=" * 60)
    print("Example 2: Batch evaluating multiple files")
    print("=" * 60)
    
    # 设置目录路径
    gt_dir = Path("datasets/ChineseTales/json_v3")
    
    if not gt_dir.exists():
        print(f"Directory not found: {gt_dir}")
        return
    
    # 创建组合评估器
    composite = CompositeEvaluator()
    results_list = []
    
    # 遍历前几个文件（示例）
    json_files = list(gt_dir.glob("*_v3.json"))[:3]  # 只处理前3个文件作为示例
    
    print(f"\nEvaluating {len(json_files)} files...")
    
    for gt_file in json_files:
        try:
            # 加载 GT
            gt_data = load_ground_truth(str(gt_file))
            
            # 假设预测结果（实际使用时替换为真实的预测结果）
            pred_data = gt_data.copy()  # 这里使用 GT 作为完美预测
            
            # 执行评估
            results = composite.evaluate(pred_data, gt_data)
            results["file"] = gt_file.name
            results_list.append(results)
            
            print(f"  - {gt_file.name}: Overall Score = {results['overall_score']:.3f}")
            
        except Exception as e:
            print(f"  - {gt_file.name}: Error - {e}")
    
    # 聚合结果
    if results_list:
        avg_results = composite.aggregate_results(results_list)
        print(f"\nAverage Overall Score: {avg_results['overall_score']:.3f}")
        print("\nAverage Component Scores:")
        for component, score in avg_results['component_scores'].items():
            if score is not None:
                print(f"  - {component}: {score:.3f}")
        print(f"\nTotal Evaluations: {avg_results['n_evaluations']}")


def example_evaluate_individual_components():
    """示例：单独使用各个评估器"""
    print("\n" + "=" * 60)
    print("Example 3: Using individual evaluators")
    print("=" * 60)
    
    from llm_model.evaluation import (
        CharacterEvaluator,
        RelationshipEvaluator,
        SentimentEvaluator,
        ActionLayerEvaluator,
        TextSpanEvaluator
    )
    
    # 示例数据
    prediction = {
        "characters": [
            {"name": "牛郎", "alias": "牧牛郎", "archetype": "Hero"},
            {"name": "织女", "alias": "仙女", "archetype": "Lover"}
        ],
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "text_span": {"start": 0, "end": 100, "text": "测试文本。"},
                "relationships": [
                    {
                        "agent": "牛郎",
                        "target": "织女",
                        "relationship_level1": "Romance",
                        "relationship_level2": "lover",
                        "sentiment": "romantic"
                    }
                ],
                "action_layer": {
                    "category": "Social & Communicative",
                    "type": "inform",
                    "status": "success"
                }
            }
        ],
        "source_info": {"text_content": "测试文本。"}
    }
    
    ground_truth = {
        "characters": [
            {"name": "牛郎", "alias": "牧牛郎", "archetype": "Hero"},
            {"name": "织女", "alias": "仙女", "archetype": "Lover"}
        ],
        "narrative_events": [
            {
                "id": "event1",
                "time_order": 1,
                "text_span": {"start": 0, "end": 100, "text": "测试文本。"},
                "relationships": [
                    {
                        "agent": "牛郎",
                        "target": "织女",
                        "relationship_level1": "Romance",
                        "relationship_level2": "lover",
                        "sentiment": "romantic"
                    }
                ],
                "action_layer": {
                    "category": "Social & Communicative",
                    "type": "inform",
                    "status": "success"
                }
            }
        ],
        "source_info": {"text_content": "测试文本。"}
    }
    
    # 单独评估各个组件
    evaluators = {
        "Character": CharacterEvaluator(),
        "Relationship": RelationshipEvaluator(),
        "Sentiment": SentimentEvaluator(),
        "Action Layer": ActionLayerEvaluator(),
        "Text Span": TextSpanEvaluator()
    }
    
    for name, evaluator in evaluators.items():
        results = evaluator.evaluate(prediction, ground_truth)
        summary = evaluator.get_metrics_summary(results)
        print(f"\n{name} Evaluator:")
        for key, value in summary.items():
            if value is not None:
                if isinstance(value, float):
                    print(f"  - {key}: {value:.3f}")
                else:
                    print(f"  - {key}: {value}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Evaluation Package - Usage Examples")
    print("=" * 60)
    
    # 运行示例
    try:
        example_evaluate_individual_components()
        example_evaluate_single_file()
        example_evaluate_multiple_files()
        
        print("\n" + "=" * 60)
        print("All examples completed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()