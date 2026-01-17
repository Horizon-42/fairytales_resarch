"""Base evaluator abstract class for evaluation components."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseEvaluator(ABC):
    """基础评估器抽象类"""
    
    @abstractmethod
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行评估
        
        Args:
            prediction: LLM 预测的 JSON v3 格式数据
            ground_truth: 标准答案的 JSON v3 格式数据
            text: 原始文本（可选，某些评估器可能需要）
            
        Returns:
            评估结果字典，包含各种指标
            
        Note:
            如果 ground_truth 中某项数据缺失（如 None、空列表、空字符串），
            应使用 handle_missing_ground_truth() 方法进行合理处理
        """
        pass
    
    @abstractmethod
    def get_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """
        从评估结果中提取关键指标摘要
        
        Args:
            results: evaluate() 返回的结果字典
            
        Returns:
            包含主要指标（如精确率、召回率、F1）的字典
        """
        pass
    
    def handle_missing_ground_truth(
        self,
        prediction_value: Any,
        ground_truth_value: Any,
        field_name: str
    ) -> Dict[str, Any]:
        """
        处理 Ground Truth 缺失数据的情况
        
        策略：
        - 如果 GT 值为 None/空列表/空字符串，且预测值非空：
          * 不将其视为错误（不惩罚）
          * 标记为 "extra"（预测有但 GT 没有）
          * 不计入 false positive，因为 GT 不完整
        - 如果 GT 值和预测值都为空：
          * 视为匹配（true negative）
        - 如果 GT 值非空但预测值为空：
          * 视为缺失（false negative）
        
        Args:
            prediction_value: 预测的值
            ground_truth_value: Ground Truth 的值
            field_name: 字段名称（用于日志和报告）
            
        Returns:
            包含处理结果的字典：
            {
                "status": "matched" | "extra" | "missing" | "mismatch",
                "count_as_error": bool,  # 是否计入错误统计
                "reason": str  # 处理原因说明
            }
        """
        # 判断是否为空值
        def is_empty(val):
            return val is None or val == "" or val == [] or (isinstance(val, dict) and len(val) == 0)
        
        pred_empty = is_empty(prediction_value)
        gt_empty = is_empty(ground_truth_value)
        
        if gt_empty and not pred_empty:
            # GT 缺失但预测有值：不惩罚，标记为 extra
            return {
                "status": "extra",
                "count_as_error": False,  # 不计入错误
                "reason": f"Ground truth missing for {field_name}, prediction has value"
            }
        elif gt_empty and pred_empty:
            # 两者都为空：视为匹配
            return {
                "status": "matched",
                "count_as_error": False,
                "reason": f"Both empty for {field_name}"
            }
        elif not gt_empty and pred_empty:
            # GT 有值但预测为空：缺失（false negative）
            return {
                "status": "missing",
                "count_as_error": True,
                "reason": f"Prediction missing for {field_name}"
            }
        else:
            # 两者都有值：正常比较（由子类处理）
            return {
                "status": "mismatch",  # 占位符，实际比较结果由子类决定
                "count_as_error": None,  # 由实际比较决定
                "reason": f"Both have values, need comparison"
            }