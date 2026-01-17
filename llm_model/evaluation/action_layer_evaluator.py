"""Action layer evaluator for JSON v3 annotations."""

from typing import Dict, Any, List, Optional, Tuple
from llm_model.evaluation.base_evaluator import BaseEvaluator
from llm_model.evaluation.utils import load_action_taxonomy


class ActionLayerEvaluator(BaseEvaluator):
    """评估叙事事件中的动作层标注"""
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        初始化动作层评估器
        
        Args:
            taxonomy_path: 动作分类标准 Markdown 文件路径（可选）
        """
        super().__init__()
        self.taxonomy = load_action_taxonomy(taxonomy_path)
    
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估动作层标注
        
        Args:
            prediction: 预测的 JSON v3 数据
            ground_truth: Ground Truth JSON v3 数据
            text: 原始文本（此评估器不需要）
            
        Returns:
            评估结果字典
        """
        pred_events = prediction.get("narrative_events", [])
        gt_events = ground_truth.get("narrative_events", [])
        
        # 按事件ID或时间顺序匹配事件
        event_matches = self._match_events(pred_events, gt_events)
        
        # 评估每个匹配事件的动作层
        field_counts = {
            "category": {"correct": 0, "total": 0},
            "type": {"correct": 0, "total": 0},
            "context": {"correct": 0, "total": 0},
            "status": {"correct": 0, "total": 0},
            "function": {"correct": 0, "total": 0}
        }
        
        complete_matches = 0
        partial_matches = 0
        total_evaluated = 0
        
        n_events_skipped = 0  # GT 缺失的事件数
        
        for pred_event, gt_event in event_matches:
            if gt_event is None:
                continue
            
            pred_action_layer = pred_event.get("action_layer", {})
            gt_action_layer = gt_event.get("action_layer", {})
            
            # 检查 GT 是否为空对象
            if not gt_action_layer or not isinstance(gt_action_layer, dict):
                # GT 缺失：不惩罚
                missing_result = self.handle_missing_ground_truth(
                    pred_action_layer,
                    gt_action_layer,
                    f"action_layer for event {pred_event.get('id', 'unknown')}"
                )
                
                if missing_result["status"] == "extra":
                    n_events_skipped += 1
                    continue
            
            # 评估动作层的各个字段（只评估 GT 中有值的字段）
            field_results = self._evaluate_action_layer_fields(
                pred_action_layer,
                gt_action_layer
            )
            
            # 统计各字段的正确数和总数
            for field, is_correct in field_results.items():
                if field in field_counts:
                    field_counts[field]["total"] += 1
                    if is_correct:
                        field_counts[field]["correct"] += 1
            
            # 判断完全匹配和部分匹配
            evaluated_fields = [f for f, is_correct in field_results.items() if field_counts[f]["total"] > 0]
            correct_fields = [f for f, is_correct in field_results.items() if is_correct]
            
            if len(evaluated_fields) > 0:
                total_evaluated += 1
                if len(correct_fields) == len(evaluated_fields):
                    complete_matches += 1
                elif len(correct_fields) > 0:
                    partial_matches += 1
        
        # 计算各字段的准确率
        field_accuracies = {}
        for field, counts in field_counts.items():
            accuracy = (
                counts["correct"] / counts["total"] 
                if counts["total"] > 0 else 0.0
            )
            field_accuracies[f"action_{field}_accuracy"] = accuracy
        
        # 计算完全匹配和部分匹配的比例
        complete_match_ratio = (
            complete_matches / total_evaluated 
            if total_evaluated > 0 else 0.0
        )
        partial_match_ratio = (
            partial_matches / total_evaluated 
            if total_evaluated > 0 else 0.0
        )
        
        gt_incomplete = n_events_skipped > 0
        
        result = {
            **field_accuracies,
            "action_layer_complete_match": complete_match_ratio,
            "action_layer_partial_match": partial_match_ratio,
            "n_events_evaluated": total_evaluated,
            "n_events_skipped": n_events_skipped,
            "complete_matches": complete_matches,
            "partial_matches": partial_matches,
            "gt_incomplete": gt_incomplete
        }
        
        return result
    
    def get_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """提取关键指标摘要"""
        summary = {
            "action_category_accuracy": results.get("action_category_accuracy", 0.0),
            "action_type_accuracy": results.get("action_type_accuracy", 0.0),
            "action_context_accuracy": results.get("action_context_accuracy", 0.0),
            "action_status_accuracy": results.get("action_status_accuracy", 0.0),
            "action_function_accuracy": results.get("action_function_accuracy", 0.0),
            "action_layer_complete_match": results.get("action_layer_complete_match", 0.0)
        }
        return summary
    
    def _match_events(
        self,
        pred_events: List[Dict[str, Any]],
        gt_events: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """匹配预测事件和 GT 事件"""
        matches = []
        
        gt_by_id = {e.get("id"): e for e in gt_events if e.get("id")}
        gt_by_time = {e.get("time_order"): e for e in gt_events if e.get("time_order") is not None}
        
        used_gt_ids = set()
        used_gt_times = set()
        
        for pred_event in pred_events:
            pred_id = pred_event.get("id")
            pred_time = pred_event.get("time_order")
            
            matched_gt = None
            
            if pred_id and pred_id in gt_by_id and pred_id not in used_gt_ids:
                matched_gt = gt_by_id[pred_id]
                used_gt_ids.add(pred_id)
            elif pred_time is not None and pred_time in gt_by_time and pred_time not in used_gt_times:
                matched_gt = gt_by_time[pred_time]
                used_gt_times.add(pred_time)
            
            matches.append((pred_event, matched_gt))
        
        return matches
    
    def _evaluate_action_layer_fields(
        self,
        pred_action_layer: Dict[str, Any],
        gt_action_layer: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        评估动作层的各个字段
        
        只评估 GT 中有值的字段，GT 中缺失的字段不参与评估
        
        Returns:
            字典：{field_name: is_correct}
        """
        fields = ["category", "type", "context", "status", "function"]
        results = {}
        
        for field in fields:
            pred_value = pred_action_layer.get(field, "").strip() if isinstance(pred_action_layer.get(field), str) else None
            gt_value = gt_action_layer.get(field, "").strip() if isinstance(gt_action_layer.get(field), str) else None
            
            # 只评估 GT 中有值的字段
            if gt_value and gt_value != "":
                # GT 有值：正常比较
                if pred_value and pred_value != "":
                    results[field] = (pred_value == gt_value)
                else:
                    # 预测值为空：错误
                    results[field] = False
            else:
                # GT 缺失：不参与评估（设为 None 表示跳过）
                results[field] = None
        
        return results