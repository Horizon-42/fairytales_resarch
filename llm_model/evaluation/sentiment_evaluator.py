"""Sentiment evaluator for JSON v3 annotations."""

from typing import Dict, Any, List, Optional, Tuple
from llm_model.evaluation.base_evaluator import BaseEvaluator
from llm_model.evaluation.metrics import calculate_precision_recall_f1
from llm_model.evaluation.utils import load_sentiment_taxonomy


class SentimentEvaluator(BaseEvaluator):
    """评估叙事事件中的情感标注"""
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        初始化情感评估器
        
        Args:
            taxonomy_path: 情感标签标准 CSV 文件路径（可选）
        """
        super().__init__()
        self.taxonomy = load_sentiment_taxonomy(taxonomy_path)
    
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估情感标注
        
        Args:
            prediction: 预测的 JSON v3 数据
            ground_truth: Ground Truth JSON v3 数据
            text: 原始文本（此评估器不需要）
            
        Returns:
            评估结果字典
        """
        pred_events = prediction.get("narrative_events", [])
        gt_events = ground_truth.get("narrative_events", [])
        
        # 按事件ID或时间顺序匹配事件（复用 RelationshipEvaluator 的逻辑）
        event_matches = self._match_events(pred_events, gt_events)
        
        # 评估每个匹配事件的情感
        total_sentiment_correct = 0
        total_sentiment_pred = 0
        total_sentiment_gt = 0
        
        polarity_correct = 0
        polarity_total = 0
        
        n_relationships_skipped = 0  # GT 缺失的关系数
        
        for pred_event, gt_event in event_matches:
            if gt_event is None:
                continue
            
            pred_relationships = pred_event.get("relationships", [])
            gt_relationships = gt_event.get("relationships", [])
            
            if not pred_relationships or not gt_relationships:
                # 如果任一为空，跳过该事件
                if not gt_relationships and pred_relationships:
                    # GT 缺失但预测有值：不惩罚
                    n_relationships_skipped += len(pred_relationships)
                continue
            
            # 评估该事件的关系情感
            rel_matches = self._match_relationships(pred_relationships, gt_relationships)
            
            for pred_rel, gt_rel in rel_matches:
                if gt_rel is None:
                    continue
                
                pred_sentiment = pred_rel.get("sentiment", "").strip()
                gt_sentiment = gt_rel.get("sentiment", "").strip()
                
                # 检查 GT 是否缺失情感
                if not gt_sentiment:
                    # GT 缺失：不惩罚
                    missing_result = self.handle_missing_ground_truth(
                        pred_sentiment,
                        gt_sentiment,
                        f"sentiment for relationship {pred_rel.get('agent', '')}-{pred_rel.get('target', '')}"
                    )
                    
                    if missing_result["status"] == "extra":
                        n_relationships_skipped += 1
                        continue
                
                # 正常评估
                if pred_sentiment and gt_sentiment:
                    total_sentiment_gt += 1
                    total_sentiment_pred += 1
                    
                    if pred_sentiment == gt_sentiment:
                        total_sentiment_correct += 1
                    
                    # 评估情感极性（将情感映射到极性）
                    pred_polarity = self._sentiment_to_polarity(pred_sentiment)
                    gt_polarity = self._sentiment_to_polarity(gt_sentiment)
                    
                    if pred_polarity and gt_polarity:
                        polarity_total += 1
                        if pred_polarity == gt_polarity:
                            polarity_correct += 1
        
        # 计算指标
        false_positives = total_sentiment_pred - total_sentiment_correct
        false_negatives = total_sentiment_gt - total_sentiment_correct
        
        precision, recall, f1 = calculate_precision_recall_f1(
            total_sentiment_correct,
            false_positives,
            false_negatives
        )
        
        polarity_accuracy = (
            polarity_correct / polarity_total if polarity_total > 0 else 0.0
        )
        
        gt_incomplete = n_relationships_skipped > 0
        
        return {
            "sentiment_precision": precision,
            "sentiment_recall": recall,
            "sentiment_f1": f1,
            "sentiment_polarity_accuracy": polarity_accuracy,
            "n_relationships_skipped": n_relationships_skipped,
            "gt_incomplete": gt_incomplete,
            "total_sentiment_correct": total_sentiment_correct,
            "total_sentiment_pred": total_sentiment_pred,
            "total_sentiment_gt": total_sentiment_gt,
            "polarity_correct": polarity_correct,
            "polarity_total": polarity_total
        }
    
    def get_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """提取关键指标摘要"""
        summary = {
            "sentiment_f1": results.get("sentiment_f1", 0.0),
            "sentiment_polarity_accuracy": results.get("sentiment_polarity_accuracy", 0.0)
        }
        return summary
    
    def _match_events(
        self,
        pred_events: List[Dict[str, Any]],
        gt_events: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """匹配预测事件和 GT 事件（复用 RelationshipEvaluator 的逻辑）"""
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
    
    def _match_relationships(
        self,
        pred_relationships: List[Dict[str, Any]],
        gt_relationships: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        """匹配预测关系和 GT 关系（按 agent-target 对）"""
        matches = []
        
        gt_rel_key_map = {}
        for rel in gt_relationships:
            agent = rel.get("agent", "").strip()
            target = rel.get("target", "").strip()
            if agent and target:
                key = (agent.lower(), target.lower())
                gt_rel_key_map[key] = rel
        
        used_gt_keys = set()
        
        for pred_rel in pred_relationships:
            agent = pred_rel.get("agent", "").strip()
            target = pred_rel.get("target", "").strip()
            
            if not agent or not target:
                matches.append((pred_rel, None))
                continue
            
            key = (agent.lower(), target.lower())
            
            if key in gt_rel_key_map and key not in used_gt_keys:
                matches.append((pred_rel, gt_rel_key_map[key]))
                used_gt_keys.add(key)
            else:
                matches.append((pred_rel, None))
        
        return matches
    
    def _sentiment_to_polarity(self, sentiment: str) -> Optional[str]:
        """
        将情感标签映射到极性（positive/negative/neutral）
        
        根据 sentiment.csv：
        - romantic, positive -> "positive"
        - neutral -> "neutral"
        - negative, fearful, hostile -> "negative"
        """
        sentiment_lower = sentiment.lower()
        
        if sentiment_lower in ["romantic", "positive"]:
            return "positive"
        elif sentiment_lower == "neutral":
            return "neutral"
        elif sentiment_lower in ["negative", "fearful", "hostile"]:
            return "negative"
        else:
            return None