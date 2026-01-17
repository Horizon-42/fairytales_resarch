"""Relationship evaluator for JSON v3 annotations."""

from typing import Dict, Any, List, Optional, Set, Tuple
from llm_model.evaluation.base_evaluator import BaseEvaluator
from llm_model.evaluation.metrics import calculate_precision_recall_f1
from llm_model.evaluation.utils import load_relationship_taxonomy


class RelationshipEvaluator(BaseEvaluator):
    """评估叙事事件中的关系标注"""
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        初始化关系评估器
        
        Args:
            taxonomy_path: 关系分类标准 CSV 文件路径（可选）
        """
        super().__init__()
        self.taxonomy = load_relationship_taxonomy(taxonomy_path)
    
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估关系标注
        
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
        
        # 评估每个匹配事件的关系
        all_level1_correct = 0
        all_level1_total = 0
        all_level2_correct = 0
        all_level2_total = 0
        
        total_relationships_correct = 0
        total_relationships_pred = 0
        total_relationships_gt = 0
        
        n_events_skipped = 0  # GT 缺失的事件数
        
        for pred_event, gt_event in event_matches:
            if gt_event is None:
                # GT 中没有对应事件，跳过
                continue
            
            pred_relationships = pred_event.get("relationships", [])
            gt_relationships = gt_event.get("relationships", [])
            
            # 检查 GT 是否缺失关系
            gt_relationships_empty = not gt_relationships or len(gt_relationships) == 0
            
            if gt_relationships_empty:
                # GT 缺失：不惩罚预测的关系
                missing_result = self.handle_missing_ground_truth(
                    pred_relationships,
                    gt_relationships,
                    f"relationships for event {pred_event.get('id', 'unknown')}"
                )
                
                if missing_result["status"] == "extra":
                    # GT 缺失但预测有值：不计数
                    n_events_skipped += 1
                    continue
            
            # 正常评估
            level1_correct, level1_total, level2_correct, level2_total, rel_matches = \
                self._evaluate_event_relationships(pred_relationships, gt_relationships)
            
            all_level1_correct += level1_correct
            all_level1_total += level1_total
            all_level2_correct += level2_correct
            all_level2_total += level2_total
            
            total_relationships_correct += rel_matches
            total_relationships_pred += len(pred_relationships)
            total_relationships_gt += len(gt_relationships)
        
        # 计算指标
        level1_accuracy = (
            all_level1_correct / all_level1_total if all_level1_total > 0 else 0.0
        )
        level2_accuracy = (
            all_level2_correct / all_level2_total if all_level2_total > 0 else 0.0
        )
        
        # 关系对级别的精确率、召回率、F1
        false_positives = total_relationships_pred - total_relationships_correct
        false_negatives = total_relationships_gt - total_relationships_correct
        
        precision, recall, f1 = calculate_precision_recall_f1(
            total_relationships_correct,
            false_positives,
            false_negatives
        )
        
        gt_incomplete = n_events_skipped > 0
        
        return {
            "relationship_precision": precision,
            "relationship_recall": recall,
            "relationship_f1": f1,
            "level1_accuracy": level1_accuracy,
            "level2_accuracy": level2_accuracy,
            "relationship_pair_coverage": (
                total_relationships_correct / total_relationships_gt 
                if total_relationships_gt > 0 else 0.0
            ),
            "n_events_evaluated": len([m for m in event_matches if m[1] is not None]),
            "n_events_skipped": n_events_skipped,
            "gt_incomplete": gt_incomplete,
            "total_relationships_pred": total_relationships_pred,
            "total_relationships_gt": total_relationships_gt,
            "total_relationships_correct": total_relationships_correct,
            "level1_correct": all_level1_correct,
            "level1_total": all_level1_total,
            "level2_correct": all_level2_correct,
            "level2_total": all_level2_total
        }
    
    def get_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """提取关键指标摘要"""
        summary = {
            "relationship_f1": results.get("relationship_f1", 0.0),
            "level1_accuracy": results.get("level1_accuracy", 0.0),
            "level2_accuracy": results.get("level2_accuracy", 0.0)
        }
        return summary
    
    def _match_events(
        self,
        pred_events: List[Dict[str, Any]],
        gt_events: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """
        匹配预测事件和 GT 事件
        
        策略：
        1. 优先使用事件ID匹配
        2. 如果ID不匹配，使用 time_order 匹配
        
        Returns:
            列表：(pred_event, gt_event)，如果 GT 中没有对应事件则为 None
        """
        matches = []
        
        # 构建 GT 事件索引（按ID和time_order）
        gt_by_id = {e.get("id"): e for e in gt_events if e.get("id")}
        gt_by_time = {e.get("time_order"): e for e in gt_events if e.get("time_order") is not None}
        
        used_gt_ids = set()
        used_gt_times = set()
        
        for pred_event in pred_events:
            pred_id = pred_event.get("id")
            pred_time = pred_event.get("time_order")
            
            matched_gt = None
            
            # 先尝试ID匹配
            if pred_id and pred_id in gt_by_id and pred_id not in used_gt_ids:
                matched_gt = gt_by_id[pred_id]
                used_gt_ids.add(pred_id)
            # 再尝试 time_order 匹配
            elif pred_time is not None and pred_time in gt_by_time and pred_time not in used_gt_times:
                matched_gt = gt_by_time[pred_time]
                used_gt_times.add(pred_time)
            
            matches.append((pred_event, matched_gt))
        
        return matches
    
    def _evaluate_event_relationships(
        self,
        pred_relationships: List[Dict[str, Any]],
        gt_relationships: List[Dict[str, Any]]
    ) -> Tuple[int, int, int, int, int]:
        """
        评估单个事件的关系列表
        
        Returns:
            (level1_correct, level1_total, level2_correct, level2_total, relationship_matches)
        """
        if not pred_relationships or not gt_relationships:
            # 如果任一为空，都返回 0
            return 0, 0, 0, 0, 0
        
        # 构建 GT 关系索引（按 agent-target 对）
        gt_rel_key_map = {}
        for rel in gt_relationships:
            agent = rel.get("agent", "").strip()
            target = rel.get("target", "").strip()
            if agent and target:
                key = (agent.lower(), target.lower())
                gt_rel_key_map[key] = rel
        
        level1_correct = 0
        level1_total = 0
        level2_correct = 0
        level2_total = 0
        relationship_matches = 0
        
        used_gt_keys = set()
        
        # 匹配预测的关系
        for pred_rel in pred_relationships:
            agent = pred_rel.get("agent", "").strip()
            target = pred_rel.get("target", "").strip()
            
            if not agent or not target:
                continue
            
            key = (agent.lower(), target.lower())
            
            if key in gt_rel_key_map and key not in used_gt_keys:
                # 找到匹配的关系
                gt_rel = gt_rel_key_map[key]
                relationship_matches += 1
                used_gt_keys.add(key)
                
                # 评估 level1
                pred_level1 = pred_rel.get("relationship_level1", "").strip()
                gt_level1 = gt_rel.get("relationship_level1", "").strip()
                
                if pred_level1 and gt_level1:
                    level1_total += 1
                    if pred_level1 == gt_level1:
                        level1_correct += 1
                
                # 评估 level2
                pred_level2 = pred_rel.get("relationship_level2", "").strip()
                gt_level2 = gt_rel.get("relationship_level2", "").strip()
                
                if pred_level2 and gt_level2:
                    level2_total += 1
                    if pred_level2 == gt_level2:
                        level2_correct += 1
        
        return level1_correct, level1_total, level2_correct, level2_total, relationship_matches