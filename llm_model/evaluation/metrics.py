"""Evaluation metrics calculation utilities."""

from typing import Set, Tuple, Dict, Any, Optional


def calculate_precision_recall_f1(
    true_positives: int,
    false_positives: int,
    false_negatives: int,
    gt_incomplete_count: int = 0  # GT 缺失的数据点数量
) -> Tuple[float, float, float]:
    """
    计算精确率、召回率、F1 分数
    
    Args:
        true_positives: 真正例数
        false_positives: 假正例数（已排除 GT 缺失的情况）
        false_negatives: 假负例数
        gt_incomplete_count: GT 缺失的数据点数量（用于报告）
        
    Returns:
        (precision, recall, f1) 元组
        
    Note:
        Precision = TP / (TP + FP)，分母不包括 GT 缺失的情况
        Recall = TP / (TP + FN)，分母不包括 GT 缺失的数据点
    """
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return precision, recall, f1


def calculate_set_metrics(
    prediction_set: Set[Any],
    ground_truth_set: Set[Any],
    gt_incomplete: bool = False
) -> Dict[str, Any]:
    """
    计算集合比较指标（精确率、召回率、F1）
    
    Args:
        prediction_set: 预测的集合
        ground_truth_set: 真实集合
        gt_incomplete: 如果 GT 为空或缺失，设为 True
        
    Returns:
        包含 precision, recall, f1, gt_incomplete 的字典
        如果 gt_incomplete=True，则 precision 不计入预测的额外项
    """
    if gt_incomplete:
        # GT 缺失：只计算召回率（基于预测集合中有多少在 GT 中）
        # 精确率设为 None 或 1.0（表示不惩罚额外项）
        matched = prediction_set & ground_truth_set
        recall = len(matched) / len(ground_truth_set) if ground_truth_set else None
        return {
            "precision": None,  # 或 1.0（表示不惩罚）
            "recall": recall,
            "f1": None,
            "gt_incomplete": True
        }
    else:
        # 正常计算
        matched = prediction_set & ground_truth_set
        precision = len(matched) / len(prediction_set) if prediction_set else 0.0
        recall = len(matched) / len(ground_truth_set) if ground_truth_set else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "gt_incomplete": False
        }


def calculate_overlap_ratio(
    span1: Tuple[int, int],
    span2: Tuple[int, int]
) -> float:
    """
    计算两个文本跨度的重叠比例（IoU 类似）
    
    Args:
        span1: 第一个跨度 (start, end)
        span2: 第二个跨度 (start, end)
        
    Returns:
        重叠比例（0-1之间的值）
    """
    start1, end1 = span1
    start2, end2 = span2
    
    # 计算交集
    intersection_start = max(start1, start2)
    intersection_end = min(end1, end2)
    intersection = max(0, intersection_end - intersection_start)
    
    # 计算并集
    union_start = min(start1, start2)
    union_end = max(end1, end2)
    union = union_end - union_start
    
    # 计算重叠比例
    if union == 0:
        return 0.0
    
    return intersection / union