"""Character evaluator for JSON v3 annotations."""

from typing import Dict, Any, List, Set, Optional, Tuple
from llm_model.evaluation.base_evaluator import BaseEvaluator
from llm_model.evaluation.metrics import calculate_precision_recall_f1, calculate_set_metrics
from llm_model.evaluation.utils import normalize_character_name


class CharacterEvaluator(BaseEvaluator):
    """评估角色列表的准确性和完整性"""
    
    def evaluate(
        self,
        prediction: Dict[str, Any],
        ground_truth: Dict[str, Any],
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        评估角色列表
        
        Args:
            prediction: 预测的 JSON v3 数据
            ground_truth: Ground Truth JSON v3 数据
            text: 原始文本（此评估器不需要）
            
        Returns:
            评估结果字典
        """
        pred_characters = prediction.get("characters", [])
        gt_characters = ground_truth.get("characters", [])
        
        # 检查 GT 是否缺失
        gt_incomplete = not gt_characters or len(gt_characters) == 0
        
        # 处理 GT 缺失的情况
        if gt_incomplete:
            missing_result = self.handle_missing_ground_truth(
                pred_characters,
                gt_characters,
                "characters"
            )
            
            return {
                "character_precision": None,
                "character_recall": None,
                "character_f1": None,
                "character_archetype_accuracy": None,
                "missing_characters": [],
                "extra_characters": [c.get("name", "") for c in pred_characters] if pred_characters else [],
                "gt_incomplete": True,
                "gt_incomplete_reason": missing_result["reason"],
                "n_predicted": len(pred_characters),
                "n_ground_truth": 0
            }
        
        # 提取角色名称和类型
        pred_names = self._extract_character_names(pred_characters)
        gt_names = self._extract_character_names(gt_characters)
        
        pred_archetypes = self._extract_character_archetypes(pred_characters, pred_names)
        gt_archetypes = self._extract_character_archetypes(gt_characters, gt_names)
        
        # 角色名称匹配（考虑别名）
        matched_names, missing_names, extra_names = self._match_characters(
            pred_characters, gt_characters, pred_names, gt_names
        )
        
        # 计算角色名称匹配指标
        true_positives = len(matched_names)
        false_positives = len(extra_names)
        false_negatives = len(missing_names)
        
        precision, recall, f1 = calculate_precision_recall_f1(
            true_positives, false_positives, false_negatives
        )
        
        # 计算角色类型准确率（仅针对匹配的角色）
        archetype_correct = 0
        archetype_total = 0
        for name in matched_names:
            if name in pred_archetypes and name in gt_archetypes:
                archetype_total += 1
                if pred_archetypes[name] == gt_archetypes[name]:
                    archetype_correct += 1
        
        archetype_accuracy = (
            archetype_correct / archetype_total if archetype_total > 0 else 0.0
        )
        
        return {
            "character_precision": precision,
            "character_recall": recall,
            "character_f1": f1,
            "character_archetype_accuracy": archetype_accuracy,
            "missing_characters": missing_names,
            "extra_characters": extra_names,
            "matched_characters": list(matched_names),
            "gt_incomplete": False,
            "n_predicted": len(pred_characters),
            "n_ground_truth": len(gt_characters),
            "n_matched": len(matched_names),
            "n_missing": len(missing_names),
            "n_extra": len(extra_names),
            "archetype_correct": archetype_correct,
            "archetype_total": archetype_total
        }
    
    def get_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """提取关键指标摘要"""
        summary = {}
        
        if results.get("gt_incomplete"):
            summary["character_f1"] = None
            summary["character_archetype_accuracy"] = None
        else:
            summary["character_f1"] = results.get("character_f1", 0.0)
            summary["character_archetype_accuracy"] = results.get("character_archetype_accuracy", 0.0)
        
        return summary
    
    def _extract_character_names(self, characters: List[Dict[str, Any]]) -> List[str]:
        """提取角色名称列表"""
        names = []
        for char in characters:
            name = char.get("name", "")
            if name:
                names.append(name.strip())
        return names
    
    def _extract_character_archetypes(
        self,
        characters: List[Dict[str, Any]],
        names: List[str]
    ) -> Dict[str, str]:
        """提取角色名称到类型的映射"""
        archetypes = {}
        for char, name in zip(characters, names):
            archetype = char.get("archetype", "")
            if archetype:
                archetypes[name] = archetype.strip()
        return archetypes
    
    def _match_characters(
        self,
        pred_characters: List[Dict[str, Any]],
        gt_characters: List[Dict[str, Any]],
        pred_names: List[str],
        gt_names: List[str]
    ) -> Tuple[Set[str], List[str], List[str]]:
        """
        匹配角色（考虑别名）
        
        Returns:
            (matched_names, missing_names, extra_names)
        """
        matched_names = set()
        missing_names = []
        extra_names = []
        
        # 构建 GT 角色名称和别名的映射
        gt_name_aliases = {}
        for char in gt_characters:
            name = char.get("name", "").strip()
            if not name:
                continue
            
            # 收集该角色的所有名称（主名 + 别名）
            aliases_str = char.get("alias", "")
            aliases = []
            if aliases_str:
                if isinstance(aliases_str, str):
                    aliases = [a.strip() for a in aliases_str.split(';') if a.strip()]
                elif isinstance(aliases_str, list):
                    aliases = [str(a).strip() for a in aliases_str if str(a).strip()]
            
            all_names = [name] + aliases
            for n in all_names:
                gt_name_aliases[n.lower()] = name  # 使用小写作为键
        
        # 匹配预测的角色
        used_gt_names = set()
        
        for char in pred_characters:
            pred_name = char.get("name", "").strip()
            if not pred_name:
                continue
            
            # 收集预测角色的所有名称
            aliases_str = char.get("alias", "")
            aliases = []
            if aliases_str:
                if isinstance(aliases_str, str):
                    aliases = [a.strip() for a in aliases_str.split(';') if a.strip()]
                elif isinstance(aliases_str, list):
                    aliases = [str(a).strip() for a in aliases_str if str(a).strip()]
            
            all_pred_names = [pred_name] + aliases
            
            # 尝试匹配
            matched = False
            for pred_n in all_pred_names:
                pred_n_lower = pred_n.lower()
                if pred_n_lower in gt_name_aliases:
                    matched_gt_name = gt_name_aliases[pred_n_lower]
                    if matched_gt_name not in used_gt_names:
                        matched_names.add(matched_gt_name)
                        used_gt_names.add(matched_gt_name)
                        matched = True
                        break
            
            if not matched:
                extra_names.append(pred_name)
        
        # 找出缺失的角色
        missing_names = [name for name in gt_names if name not in used_gt_names]
        
        return matched_names, missing_names, extra_names