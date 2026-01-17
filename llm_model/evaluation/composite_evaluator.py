"""Composite evaluator that combines all evaluation components."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from llm_model.evaluation.base_evaluator import BaseEvaluator
from llm_model.evaluation.character_evaluator import CharacterEvaluator
from llm_model.evaluation.relationship_evaluator import RelationshipEvaluator
from llm_model.evaluation.sentiment_evaluator import SentimentEvaluator
from llm_model.evaluation.action_layer_evaluator import ActionLayerEvaluator
from llm_model.evaluation.text_span_evaluator import TextSpanEvaluator


class CompositeEvaluator:
    """组合评估器（聚合所有评估结果）"""
    
    def __init__(
        self,
        character_evaluator: Optional[CharacterEvaluator] = None,
        relationship_evaluator: Optional[RelationshipEvaluator] = None,
        sentiment_evaluator: Optional[SentimentEvaluator] = None,
        action_layer_evaluator: Optional[ActionLayerEvaluator] = None,
        text_span_evaluator: Optional[TextSpanEvaluator] = None
    ):
        """
        初始化组合评估器
        
        Args:
            character_evaluator: 角色评估器（可选，默认创建新的）
            relationship_evaluator: 关系评估器（可选，默认创建新的）
            sentiment_evaluator: 情感评估器（可选，默认创建新的）
            action_layer_evaluator: 动作层评估器（可选，默认创建新的）
            text_span_evaluator: 文本跨度评估器（可选，默认创建新的）
        """
        self.character_evaluator = character_evaluator or CharacterEvaluator()
        self.relationship_evaluator = relationship_evaluator or RelationshipEvaluator()
        self.sentiment_evaluator = sentiment_evaluator or SentimentEvaluator()
        self.action_layer_evaluator = action_layer_evaluator or ActionLayerEvaluator()
        self.text_span_evaluator = text_span_evaluator or TextSpanEvaluator()
    
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行完整评估
        
        Args:
            prediction: 预测的 JSON v3 数据
            ground_truth: Ground Truth JSON v3 数据
            text: 原始文本（可选，某些评估器需要）
            
        Returns:
            完整的评估结果字典
        """
        # 如果没有提供文本，尝试从数据中获取
        if text is None:
            text = prediction.get("source_info", {}).get("text_content", "")
            if not text:
                text = ground_truth.get("source_info", {}).get("text_content", "")
        
        # 执行各个评估器的评估
        character_results = self.character_evaluator.evaluate(prediction, ground_truth, text)
        relationship_results = self.relationship_evaluator.evaluate(prediction, ground_truth, text)
        sentiment_results = self.sentiment_evaluator.evaluate(prediction, ground_truth, text)
        action_layer_results = self.action_layer_evaluator.evaluate(prediction, ground_truth, text)
        text_span_results = self.text_span_evaluator.evaluate(prediction, ground_truth, text)
        
        # 计算组件得分（归一化到 0-1）
        component_scores = self._calculate_component_scores(
            character_results,
            relationship_results,
            sentiment_results,
            action_layer_results,
            text_span_results
        )
        
        # 计算总体得分（各组件得分的平均值）
        valid_scores = [s for s in component_scores.values() if s is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        
        # 统计事件信息
        pred_events = prediction.get("narrative_events", [])
        gt_events = ground_truth.get("narrative_events", [])
        
        # 统计匹配的事件数（简单统计，基于数量）
        event_accuracy = 0.0
        if len(gt_events) > 0:
            # 这里可以更精确地匹配事件，但简单起见使用数量比例
            event_accuracy = min(len(pred_events) / len(gt_events), 1.0) if len(gt_events) > 0 else 0.0
        
        return {
            "overall_score": overall_score,
            "component_scores": component_scores,
            "detailed_results": {
                "characters": character_results,
                "relationships": relationship_results,
                "sentiment": sentiment_results,
                "action_layer": action_layer_results,
                "text_span": text_span_results
            },
            "summary": {
                "total_events_predicted": len(pred_events),
                "total_events_ground_truth": len(gt_events),
                "event_accuracy": event_accuracy
            }
        }
    
    def _calculate_component_scores(
        self,
        character_results: Dict[str, Any],
        relationship_results: Dict[str, Any],
        sentiment_results: Dict[str, Any],
        action_layer_results: Dict[str, Any],
        text_span_results: Dict[str, Any]
    ) -> Dict[str, Optional[float]]:
        """计算各组件得分（归一化到 0-1）"""
        scores = {}
        
        # 角色得分：使用 F1 分数
        if character_results.get("gt_incomplete"):
            scores["characters"] = None
        else:
            scores["characters"] = character_results.get("character_f1", 0.0)
        
        # 关系得分：使用 F1 分数
        if relationship_results.get("gt_incomplete"):
            scores["relationships"] = None
        else:
            scores["relationships"] = relationship_results.get("relationship_f1", 0.0)
        
        # 情感得分：使用 F1 分数
        if sentiment_results.get("gt_incomplete"):
            scores["sentiment"] = None
        else:
            scores["sentiment"] = sentiment_results.get("sentiment_f1", 0.0)
        
        # 动作层得分：使用完全匹配比例和字段准确率的平均值
        if action_layer_results.get("gt_incomplete"):
            scores["action_layer"] = None
        else:
            complete_match = action_layer_results.get("action_layer_complete_match", 0.0)
            # 计算字段准确率的平均值
            field_accuracies = [
                action_layer_results.get("action_category_accuracy", 0.0),
                action_layer_results.get("action_type_accuracy", 0.0),
                action_layer_results.get("action_context_accuracy", 0.0),
                action_layer_results.get("action_status_accuracy", 0.0),
                action_layer_results.get("action_function_accuracy", 0.0)
            ]
            # 只计算有值的字段
            valid_accuracies = [a for a in field_accuracies if a > 0.0]
            avg_field_accuracy = sum(valid_accuracies) / len(valid_accuracies) if valid_accuracies else 0.0
            scores["action_layer"] = (complete_match + avg_field_accuracy) / 2.0
        
        # 文本跨度得分：使用 boundary_score
        if text_span_results.get("gt_incomplete") or text_span_results.get("boundary_score") is None:
            scores["text_span"] = None
        else:
            boundary_score = text_span_results.get("boundary_score", 0.0)
            mean_overlap = text_span_results.get("mean_overlap", 0.0)
            # 综合边界得分和重叠比例
            scores["text_span"] = (boundary_score + mean_overlap) / 2.0
        
        return scores
    
    def generate_report(
        self,
        results: Dict[str, Any],
        output_path: Optional[str] = None,
        format: str = "json"
    ) -> str:
        """
        生成评估报告
        
        Args:
            results: evaluate() 返回的结果字典
            output_path: 输出文件路径（可选，如果为 None 则不保存文件）
            format: 报告格式（"json" 或 "markdown"）
            
        Returns:
            报告字符串
        """
        if format == "json":
            report = json.dumps(results, indent=2, ensure_ascii=False)
        elif format == "markdown":
            report = self._generate_markdown_report(results)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """生成 Markdown 格式的报告"""
        lines = ["# Evaluation Report\n"]
        
        # 总体得分
        overall_score = results.get("overall_score", 0.0)
        lines.append(f"## Overall Score: {overall_score:.3f}\n")
        
        # 组件得分
        component_scores = results.get("component_scores", {})
        lines.append("## Component Scores\n")
        for component, score in component_scores.items():
            if score is not None:
                lines.append(f"- **{component}**: {score:.3f}")
            else:
                lines.append(f"- **{component}**: N/A (GT incomplete)")
        lines.append("")
        
        # 详细结果
        detailed_results = results.get("detailed_results", {})
        lines.append("## Detailed Results\n")
        
        for component, component_results in detailed_results.items():
            lines.append(f"### {component.capitalize()}\n")
            
            if component_results.get("gt_incomplete"):
                lines.append(f"⚠️ Ground Truth incomplete: {component_results.get('gt_incomplete_reason', 'N/A')}\n")
            else:
                summary = self._get_component_summary(component, component_results)
                for key, value in summary.items():
                    if isinstance(value, float):
                        lines.append(f"- **{key}**: {value:.3f}")
                    else:
                        lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_component_summary(self, component: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """获取组件结果摘要"""
        if component == "characters":
            return {
                "F1": results.get("character_f1", 0.0),
                "Archetype Accuracy": results.get("character_archetype_accuracy", 0.0),
                "Missing Characters": len(results.get("missing_characters", [])),
                "Extra Characters": len(results.get("extra_characters", []))
            }
        elif component == "relationships":
            return {
                "F1": results.get("relationship_f1", 0.0),
                "Level 1 Accuracy": results.get("level1_accuracy", 0.0),
                "Level 2 Accuracy": results.get("level2_accuracy", 0.0)
            }
        elif component == "sentiment":
            return {
                "F1": results.get("sentiment_f1", 0.0),
                "Polarity Accuracy": results.get("sentiment_polarity_accuracy", 0.0)
            }
        elif component == "action_layer":
            return {
                "Complete Match Ratio": results.get("action_layer_complete_match", 0.0),
                "Category Accuracy": results.get("action_category_accuracy", 0.0),
                "Type Accuracy": results.get("action_type_accuracy", 0.0)
            }
        elif component == "text_span":
            return {
                "Boundary Score": results.get("boundary_score"),
                "Mean Overlap": results.get("mean_overlap", 0.0)
            }
        else:
            return {}
    
    def aggregate_results(self, results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合多个评估结果（计算平均值）
        
        Args:
            results_list: 评估结果列表
            
        Returns:
            聚合后的结果字典
        """
        if not results_list:
            return {}
        
        # 初始化累加器
        component_scores_sum = {}
        component_counts = {}
        overall_scores = []
        
        for results in results_list:
            overall_score = results.get("overall_score", 0.0)
            overall_scores.append(overall_score)
            
            component_scores = results.get("component_scores", {})
            for component, score in component_scores.items():
                if score is not None:
                    if component not in component_scores_sum:
                        component_scores_sum[component] = 0.0
                        component_counts[component] = 0
                    component_scores_sum[component] += score
                    component_counts[component] += 1
        
        # 计算平均值
        avg_component_scores = {
            component: component_scores_sum[component] / component_counts[component]
            if component_counts[component] > 0 else None
            for component in component_scores_sum.keys()
        }
        
        avg_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
        
        return {
            "overall_score": avg_overall_score,
            "component_scores": avg_component_scores,
            "n_evaluations": len(results_list)
        }