"""Text span evaluator for JSON v3 annotations using Boundary Segmentation Metric."""

from typing import Dict, Any, List, Optional, Tuple
from llm_model.evaluation.base_evaluator import BaseEvaluator
from llm_model.evaluation.utils import text_to_sentence_indices, char_position_to_sentence_index
from llm_model.text_segmentation.boundary_metric import BoundarySegmentationMetric
from llm_model.evaluation.metrics import calculate_overlap_ratio


class TextSpanEvaluator(BaseEvaluator):
    """文本跨度边界评估器"""
    
    def __init__(self, tolerance: int = 2):
        """
        初始化文本跨度评估器
        
        Args:
            tolerance: Boundary Segmentation Metric 的容忍度参数（默认 2）
        """
        super().__init__()
        self.boundary_metric = BoundarySegmentationMetric(tolerance=tolerance)
    
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估 text_span 的边界准确性
        
        算法流程：
        1. 从 prediction 和 ground_truth 中提取 narrative_events
        2. 提取每个事件的 text_span（start, end）
        3. 将文本转换为句子索引列表
        4. 将 text_span 的字符位置转换为句子边界索引
        5. 使用 BoundarySegmentationMetric 计算边界相似度
        6. 计算文本片段重叠比例
        
        Args:
            prediction: 预测的 JSON v3 数据
            ground_truth: Ground Truth JSON v3 数据
            text: 原始文本（必需）
            
        Returns:
            评估结果字典
        """
        if text is None:
            text = prediction.get("source_info", {}).get("text_content", "")
            if not text:
                # 尝试从 GT 获取
                text = ground_truth.get("source_info", {}).get("text_content", "")
                if not text:
                    raise ValueError("text is required for text_span evaluation")
        
        # 提取 text_spans
        pred_spans = self._extract_text_spans(prediction)
        gt_spans = self._extract_text_spans(ground_truth)
        
        # 检查 GT 是否完整
        gt_incomplete = len(gt_spans) == 0 or all(
            span.get("start") is None or span.get("end") is None 
            for span in gt_spans
        )
        
        if gt_incomplete:
            missing_result = self.handle_missing_ground_truth(
                pred_spans,
                gt_spans,
                "text_spans"
            )
            
            return {
                "boundary_score": None,
                "overlap_scores": [],
                "mean_overlap": 0.0,
                "predicted_boundaries": [],
                "ground_truth_boundaries": [],
                "n_predicted": len(pred_spans),
                "n_ground_truth": 0,
                "gt_incomplete": True,
                "gt_incomplete_reason": missing_result["reason"]
            }
        
        # 转换为句子边界索引
        sentence_indices = text_to_sentence_indices(text)
        
        if not sentence_indices:
            # 无法分割句子，返回默认值
            return {
                "boundary_score": None,
                "overlap_scores": [],
                "mean_overlap": 0.0,
                "predicted_boundaries": [],
                "ground_truth_boundaries": [],
                "n_predicted": len(pred_spans),
                "n_ground_truth": len(gt_spans),
                "gt_incomplete": False,
                "error": "Failed to split text into sentences"
            }
        
        pred_boundaries = self._spans_to_boundaries(pred_spans, sentence_indices)
        gt_boundaries = self._spans_to_boundaries(gt_spans, sentence_indices)
        
        # 使用 Boundary Segmentation Metric
        boundary_score = self.boundary_metric.calculate(
            reference_boundaries=gt_boundaries,
            hypothesis_boundaries=pred_boundaries
        )
        
        # 计算重叠比例
        overlap_scores = self._calculate_overlap_scores(pred_spans, gt_spans)
        
        return {
            "boundary_score": boundary_score,
            "overlap_scores": overlap_scores,
            "mean_overlap": sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0,
            "predicted_boundaries": pred_boundaries,
            "ground_truth_boundaries": gt_boundaries,
            "n_predicted": len(pred_boundaries),
            "n_ground_truth": len(gt_boundaries),
            "n_predicted_spans": len(pred_spans),
            "n_ground_truth_spans": len(gt_spans),
            "gt_incomplete": False
        }
    
    def get_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """提取关键指标摘要"""
        summary = {
            "boundary_score": results.get("boundary_score"),
            "mean_overlap": results.get("mean_overlap", 0.0)
        }
        return summary
    
    def _extract_text_spans(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 JSON v3 数据中提取 text_span 列表
        
        注意：只提取有效的 text_span（start 和 end 都不为 None）
        如果 text_span 为 null 或字段缺失，则跳过该事件
        """
        events = data.get("narrative_events", [])
        spans = []
        for event in events:
            text_span = event.get("text_span")
            # 检查 text_span 是否为有效值（不是 null，且 start 和 end 都存在）
            if text_span is not None and isinstance(text_span, dict):
                start = text_span.get("start")
                end = text_span.get("end")
                if start is not None and end is not None:
                    spans.append(text_span)
        return spans
    
    def _spans_to_boundaries(
        self,
        spans: List[Dict[str, Any]],
        sentence_indices: List[Tuple[int, int]]
    ) -> List[int]:
        """
        将 text_span 列表转换为句子边界索引列表
        
        边界索引定义为句子结束位置的索引（即该句子在句子列表中的索引）
        """
        boundaries = []
        for span in spans:
            start = span.get("start", 0)
            end = span.get("end", 0)
            
            # 将字符位置转换为句子索引
            start_sent_idx = char_position_to_sentence_index(start, sentence_indices)
            end_sent_idx = char_position_to_sentence_index(end, sentence_indices)
            
            # 边界为结束句子的索引（不包括最后一个句子本身）
            if end_sent_idx > start_sent_idx:
                # 边界在句子之间，取结束句子的前一个索引
                boundaries.append(end_sent_idx - 1)
            elif end_sent_idx == start_sent_idx and end_sent_idx > 0:
                # 如果 start 和 end 在同一个句子，边界为该句子的前一个索引
                boundaries.append(end_sent_idx - 1)
        
        # 去重并排序
        return sorted(set(boundaries))
    
    def _calculate_overlap_scores(
        self,
        pred_spans: List[Dict[str, Any]],
        gt_spans: List[Dict[str, Any]]
    ) -> List[float]:
        """
        计算预测和真实文本跨度的重叠比例
        
        使用简单的最近邻匹配策略：
        对每个 GT span，找到与其重叠比例最大的预测 span
        """
        if not pred_spans or not gt_spans:
            return []
        
        scores = []
        used_pred_indices = set()
        
        for gt_span in gt_spans:
            gt_start = gt_span.get("start", 0)
            gt_end = gt_span.get("end", 0)
            gt_tuple = (gt_start, gt_end)
            
            best_overlap = 0.0
            best_pred_idx = -1
            
            # 找到与当前 GT span 重叠最大的预测 span
            for idx, pred_span in enumerate(pred_spans):
                if idx in used_pred_indices:
                    continue
                
                pred_start = pred_span.get("start", 0)
                pred_end = pred_span.get("end", 0)
                pred_tuple = (pred_start, pred_end)
                
                overlap = calculate_overlap_ratio(gt_tuple, pred_tuple)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_pred_idx = idx
            
            if best_pred_idx >= 0:
                used_pred_indices.add(best_pred_idx)
                scores.append(best_overlap)
            else:
                # 没有找到匹配的预测 span，重叠为 0
                scores.append(0.0)
        
        return scores