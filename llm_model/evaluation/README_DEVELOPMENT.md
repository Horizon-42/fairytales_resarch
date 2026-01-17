# LLM 结果评估模块开发文档 (Evaluation Package Development Guide)

## 1. 概述 (Overview)

本文档描述了在 `llm_model` 中新增的 `evaluation` package 的设计方案。该模块旨在为 LLM 生成的 JSON v3 格式标注结果提供一套解耦的、合理的评估方法。

### 1.1 目标

- 对 LLM 生成的 JSON v3 格式标注进行系统性评估
- 提供解耦的评估方法，分别检测各个组件（角色、关系、情感、动作层等）
- 提供独立的 `text_span` 边界评估模块，使用与文本分割文档相同的算法
- 支持灵活的输入格式（默认支持 `text` 和 `text_span`）
- **处理 Ground Truth 缺失数据**：当 Ground Truth 中某项数据缺失时，采用合理的评估策略（例如：不惩罚预测了 GT 中没有的数据，或使用部分匹配策略）

### 1.2 评估范围

根据 JSON v3 的数据结构，评估模块需要覆盖以下内容：

1. **角色 (Characters)**：角色列表的完整性、准确性
2. **叙事事件 (Narrative Events)** 中的各个字段：
   - **关系 (Relationships)**：`relationship_level1`, `relationship_level2`
   - **情感 (Sentiment)**：情感标签的准确性
   - **动作层 (Action Layer)**：`category`, `type`, `context`, `status`, `function`
   - **文本跨度 (Text Span)**：`start`, `end`, `text` 的边界准确性

## 2. 数据格式 (Data Schema)

### 2.1 JSON v3 输入格式

```json
{
  "version": "3.0",
  "metadata": {...},
  "source_info": {
    "text_content": "完整的故事文本"
  },
  "characters": [
    {
      "name": "角色名",
      "alias": "别名",
      "archetype": "角色类型"
    }
  ],
  "narrative_events": [
    {
      "id": "事件ID",
      "text_span": {
        "start": 0,
        "end": 100,
        "text": "文本片段"
      },
      "agents": ["角色名"],
      "targets": ["角色名或对象"],
      "relationships": [
        {
          "agent": "角色A",
          "target": "角色B",
          "relationship_level1": "Family & Kinship",
          "relationship_level2": "sibling",
          "sentiment": "positive"
        }
      ],
      "action_layer": {
        "category": "Physical & Conflict",
        "type": "attack",
        "context": "duel",
        "status": "success",
        "function": "trigger"
      }
    }
  ]
}
```

### 2.2 评估数据来源

评估模块需要使用以下文档中的数据作为参考标准：

- `docs/Character_Resources/relationship.csv` - 关系分类标准
- `docs/Character_Resources/sentiment.csv` - 情感标签标准
- `docs/Universal Narrative Action Taxonomy/Universal_Narrative_Action_Taxonomy.md` - 动作分类标准
- `datasets/*/json_v3/*.json` - Ground Truth 标注数据

## 3. 模块架构设计 (Module Architecture)

### 3.1 目录结构

```
llm_model/evaluation/
├── __init__.py                 # 包初始化
├── base_evaluator.py          # 基础评估器抽象类
├── character_evaluator.py     # 角色评估器
├── relationship_evaluator.py  # 关系评估器
├── sentiment_evaluator.py     # 情感评估器
├── action_layer_evaluator.py  # 动作层评估器
├── text_span_evaluator.py     # 文本跨度边界评估器
├── composite_evaluator.py     # 组合评估器（聚合所有评估结果）
├── utils.py                   # 工具函数（数据加载、标准化等）
├── metrics.py                 # 评估指标计算（精确率、召回率、F1等）
└── tests/                     # 单元测试
    ├── __init__.py
    ├── test_character_evaluator.py
    ├── test_relationship_evaluator.py
    ├── test_sentiment_evaluator.py
    ├── test_action_layer_evaluator.py
    ├── test_text_span_evaluator.py
    └── test_composite_evaluator.py
```

### 3.2 核心组件设计

#### 3.2.1 基础评估器 (Base Evaluator)

所有评估器都应继承自 `BaseEvaluator` 抽象类：

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

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
```

#### 3.2.2 角色评估器 (Character Evaluator)

评估角色列表的准确性和完整性。

**评估维度**：
- 角色名称匹配（考虑别名）
- 角色类型（archetype）匹配
- 角色完整性（缺失、多余的角色）

**评估方法**：
- 精确匹配：完全相同的角色名称
- 模糊匹配：通过别名匹配
- 集合比较：预测集合 vs 真实集合的差异
- **缺失数据处理**：如果 GT 中 `characters` 为空或 None，则：
  * 预测的角色不视为 `extra_characters`（不计入 false positive）
  * 将这种情况标记为 `gt_incomplete: true`，并在报告中说明

**输出指标**：
- `character_precision`: 预测正确的角色数 / 预测的角色总数
- `character_recall`: 预测正确的角色数 / 真实角色总数
- `character_f1`: F1 分数
- `character_archetype_accuracy`: 角色类型匹配准确率
- `missing_characters`: 缺失的角色列表
- `extra_characters`: 多余的角色列表

#### 3.2.3 关系评估器 (Relationship Evaluator)

评估叙事事件中的关系标注。

**评估维度**：
- `relationship_level1` 分类准确性（使用 `relationship.csv` 作为标准）
- `relationship_level2` 二级分类准确性
- 关系对（agent-target pairs）的完整性

**评估方法**：
- 逐事件评估关系列表
- 支持多对一、一对多的关系匹配
- 考虑关系标签的层次结构（level1 和 level2 的组合）
- **缺失数据处理**：如果某个事件的 GT `relationships` 为空列表或 None：
  * 预测的关系不视为错误（不惩罚）
  * 该事件的关系评估跳过或标记为 `gt_incomplete`
  * 如果整个事件不存在于 GT 中，则整条关系的评估跳过

**输出指标**：
- `relationship_precision`: 关系预测精确率
- `relationship_recall`: 关系预测召回率
- `relationship_f1`: 关系 F1 分数
- `level1_accuracy`: Level 1 分类准确率
- `level2_accuracy`: Level 2 分类准确率
- `relationship_pair_coverage`: 关系对覆盖率

#### 3.2.4 情感评估器 (Sentiment Evaluator)

评估叙事事件中的情感标注。

**评估维度**：
- 情感标签准确性（使用 `sentiment.csv` 作为标准）
- 情感极性（positive/negative/neutral）的一致性

**评估方法**：
- 逐关系对评估情感标签
- 支持情感标签的多值性（一个关系可能有多种情感）
- **缺失数据处理**：如果某个关系的 GT `sentiment` 为空字符串或 None：
  * 预测的情感标签不视为错误（因为 GT 未标注）
  * 该关系的情感评估标记为 `gt_incomplete`，不计入准确率计算的分母
  * 如果整个 `relationships` 列表为空，则跳过情感评估

**输出指标**：
- `sentiment_precision`: 情感预测精确率
- `sentiment_recall`: 情感预测召回率
- `sentiment_f1`: 情感 F1 分数
- `sentiment_polarity_accuracy`: 情感极性准确率（正负中性分类）

#### 3.2.5 动作层评估器 (Action Layer Evaluator)

评估叙事事件中的动作层标注。

**评估维度**：
- `category` 分类准确性（使用 Universal Narrative Action Taxonomy）
- `type` 动作类型准确性
- `context` 上下文标签准确性
- `status` 状态标签准确性
- `function` 叙事功能准确性

**评估方法**：
- 逐事件评估动作层对象
- 考虑动作分类的层次结构
- 支持部分匹配（例如 category 正确但 type 错误）
- **缺失数据处理**：如果某个事件的 GT `action_layer` 为 `{}` 或字段为空字符串：
  * 仅评估 GT 中有值的字段（例如 GT 只有 `category`，则只评估 `category`）
  * GT 中缺失的字段不参与评估，预测值不视为错误
  * 如果整个 `action_layer` 为空对象，则跳过该事件的动作层评估
  * 计算准确率时，分母只包含 GT 中有值的字段数量

**输出指标**：
- `action_category_accuracy`: Category 准确率
- `action_type_accuracy`: Type 准确率
- `action_context_accuracy`: Context 准确率
- `action_status_accuracy`: Status 准确率
- `action_function_accuracy`: Function 准确率
- `action_layer_complete_match`: 完全匹配的动作层比例
- `action_layer_partial_match`: 部分匹配的动作层比例

#### 3.2.6 文本跨度评估器 (Text Span Evaluator)

**独立的边界评估模块**，评估 `text_span` 的边界准确性。

**设计要点**：
- 使用与 `docs/LLM 文本分割开发文档.md` 相同的 **Boundary Segmentation Metric** 算法
- 将 `text_span` 的边界（start, end）转换为句子边界索引
- 支持与现有 `text_segmentation/boundary_metric.py` 的集成

**评估方法**：
1. 将文本按句子分割（参考文本分割模块的方法）
2. 将 `text_span` 的字符位置转换为句子索引
3. 使用 Boundary Segmentation Metric 计算边界相似度
- **缺失数据处理**：如果某个事件的 GT `text_span` 为 `null` 或不存在：
  * 该事件的边界不参与 Boundary Segmentation Metric 计算
  * 预测的边界不视为插入错误（不计入 false positive）
  * 在边界列表中排除该事件，重新计算指标
  * 如果所有事件的 GT `text_span` 都缺失，则返回 `gt_incomplete: true`，边界得分为 `None`

**输入格式**：
- `text`: 完整文本
- `prediction_text_spans`: 预测的 text_span 列表 `[{start, end, text}, ...]`
- `ground_truth_text_spans`: 真实的 text_span 列表

**输出指标**：
- `boundary_score`: Boundary Segmentation Metric 得分（0-1）
- `exact_matches`: 精确匹配的边界数量
- `near_misses`: 近距错配的边界数量（在容忍度范围内）
- `insertions`: 插入的边界数量（预测有但真实没有）
- `deletions`: 删除的边界数量（真实有但预测没有）
- `overlap_ratio`: 文本片段重叠比例（IoU 类似指标）

**实现参考**：
- 复用 `llm_model/text_segmentation/boundary_metric.py` 中的 `BoundarySegmentationMetric` 类
- 需要添加文本到句子索引的转换逻辑

#### 3.2.7 组合评估器 (Composite Evaluator)

聚合所有评估器的结果，提供整体评估报告。

**功能**：
- 协调各个评估器的执行
- 汇总评估结果
- 生成综合评估报告（JSON 或 Markdown 格式）

**输出结构**：
```json
{
  "overall_score": 0.85,
  "component_scores": {
    "characters": 0.90,
    "relationships": 0.88,
    "sentiment": 0.82,
    "action_layer": 0.80,
    "text_span": 0.85
  },
  "detailed_results": {
    "characters": {...},
    "relationships": {...},
    "sentiment": {...},
    "action_layer": {...},
    "text_span": {...}
  },
  "summary": {
    "total_events": 10,
    "correct_events": 8,
    "event_accuracy": 0.80
  }
}
```

## 4. 实现细节 (Implementation Details)

### 4.1 数据加载与标准化

**工具函数 (`utils.py`)**：

```python
def load_ground_truth(json_path: str) -> Dict[str, Any]:
    """从 JSON v3 文件加载 Ground Truth 数据"""
    
def load_prediction(json_path: str) -> Dict[str, Any]:
    """从 JSON v3 文件加载预测数据"""
    
def normalize_character_name(name: str, aliases: List[str]) -> str:
    """标准化角色名称（处理别名）"""
    
def load_relationship_taxonomy(csv_path: str) -> Dict[str, List[str]]:
    """加载关系分类标准"""
    
def load_sentiment_taxonomy(csv_path: str) -> List[str]:
    """加载情感标签标准"""
    
def load_action_taxonomy(md_path: str) -> Dict[str, Any]:
    """加载动作分类标准"""
    
def text_to_sentence_indices(text: str) -> List[Tuple[int, int]]:
    """
    将文本转换为句子索引列表
    
    Returns:
        List of (start_char, end_char) for each sentence
    """
    
def char_position_to_sentence_index(
    char_pos: int,
    sentence_indices: List[Tuple[int, int]]
) -> int:
    """
    将字符位置转换为句子索引
    
    Args:
        char_pos: 字符在文本中的位置
        sentence_indices: 句子索引列表
        
    Returns:
        句子索引（0-based）
    """
```

### 4.2 评估指标计算 (`metrics.py`)

```python
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

def calculate_set_metrics(
    prediction_set: Set[Any],
    ground_truth_set: Set[Any],
    gt_incomplete: bool = False
) -> Dict[str, float]:
    """
    计算集合比较指标（精确率、召回率、F1）
    
    Args:
        prediction_set: 预测的集合
        ground_truth_set: 真实集合
        gt_incomplete: 如果 GT 为空或缺失，设为 True
        
    Returns:
        包含 precision, recall, f1 的字典
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
    """计算两个文本跨度的重叠比例（IoU 类似）"""
```

### 4.3 文本跨度评估器的特殊实现

`text_span_evaluator.py` 需要特殊处理：

```python
from llm_model.text_segmentation.boundary_metric import BoundarySegmentationMetric
from llm_model.evaluation.utils import (
    text_to_sentence_indices,
    char_position_to_sentence_index
)

class TextSpanEvaluator(BaseEvaluator):
    """文本跨度边界评估器"""
    
    def __init__(self, tolerance: int = 2):
        """
        Args:
            tolerance: Boundary Segmentation Metric 的容忍度参数
        """
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
        """
        if text is None:
            text = prediction.get("source_info", {}).get("text_content", "")
            if not text:
                raise ValueError("text is required for text_span evaluation")
        
        # 提取 text_spans
        pred_spans = self._extract_text_spans(prediction)
        gt_spans = self._extract_text_spans(ground_truth)
        
        # 转换为句子边界索引
        sentence_indices = text_to_sentence_indices(text)
        pred_boundaries = self._spans_to_boundaries(pred_spans, sentence_indices)
        gt_boundaries = self._spans_to_boundaries(gt_spans, sentence_indices)
        
        # 使用 Boundary Segmentation Metric
        boundary_score = self.boundary_metric.calculate(
            reference_boundaries=gt_boundaries,
            hypothesis_boundaries=pred_boundaries
        )
        
        # 计算重叠比例
        overlap_scores = self._calculate_overlap_scores(pred_spans, gt_spans)
        
        # 检查 GT 是否完整
        gt_incomplete = len(gt_spans) == 0 or all(
            span.get("start") is None or span.get("end") is None 
            for span in gt_spans
        )
        
        return {
            "boundary_score": boundary_score if not gt_incomplete else None,
            "overlap_scores": overlap_scores,
            "mean_overlap": sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0,
            "predicted_boundaries": pred_boundaries,
            "ground_truth_boundaries": gt_boundaries,
            "n_predicted": len(pred_boundaries),
            "n_ground_truth": len(gt_boundaries),
            "gt_incomplete": gt_incomplete,
            "gt_incomplete_reason": "No valid text_span in ground truth" if gt_incomplete else None
        }
    
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
                boundaries.append(end_sent_idx - 1)
        return sorted(set(boundaries))
    
    def _calculate_overlap_scores(
        self,
        pred_spans: List[Dict[str, Any]],
        gt_spans: List[Dict[str, Any]]
    ) -> List[float]:
        """计算预测和真实文本跨度的重叠比例"""
        # 使用最佳匹配算法（如匈牙利算法）进行配对
        # 简化版本：按顺序匹配或使用最近邻匹配
        scores = []
        # TODO: 实现匹配逻辑
        return scores
```

## 5. 使用示例 (Usage Examples)

### 5.1 单独使用某个评估器

```python
from llm_model.evaluation.character_evaluator import CharacterEvaluator
from llm_model.evaluation.utils import load_ground_truth, load_prediction

# 加载数据
ground_truth = load_ground_truth("datasets/ChineseTales/json_v3/CH_002_牛郎织女2_v3.json")
prediction = load_prediction("llm_output/CH_002_牛郎织女2_v3_pred.json")

# 创建评估器
evaluator = CharacterEvaluator()

# 执行评估
results = evaluator.evaluate(prediction, ground_truth)

# 查看结果
print(f"Character F1: {results['character_f1']:.3f}")
print(f"Missing characters: {results['missing_characters']}")
```

### 5.2 使用组合评估器

```python
from llm_model.evaluation.composite_evaluator import CompositeEvaluator
from llm_model.evaluation.utils import load_ground_truth, load_prediction

# 加载数据
ground_truth = load_ground_truth("datasets/ChineseTales/json_v3/CH_002_牛郎织女2_v3.json")
prediction = load_prediction("llm_output/CH_002_牛郎织女2_v3_pred.json")

# 创建组合评估器
composite = CompositeEvaluator()

# 执行完整评估
results = composite.evaluate(prediction, ground_truth)

# 查看总体得分
print(f"Overall Score: {results['overall_score']:.3f}")
print(f"Component Scores: {results['component_scores']}")

# 生成报告
composite.generate_report(results, output_path="evaluation_report.json")
```

### 5.3 批量评估

```python
from llm_model.evaluation.composite_evaluator import CompositeEvaluator
from pathlib import Path
import json

composite = CompositeEvaluator()
results_list = []

# 遍历所有 json_v3 文件
gt_dir = Path("datasets/ChineseTales/json_v3")
pred_dir = Path("llm_output")

for gt_file in gt_dir.glob("*.json"):
    pred_file = pred_dir / gt_file.name.replace("_v3.json", "_v3_pred.json")
    
    if pred_file.exists():
        gt_data = json.load(gt_file.open())
        pred_data = json.load(pred_file.open())
        
        results = composite.evaluate(pred_data, gt_data)
        results["file"] = gt_file.name
        results_list.append(results)

# 计算平均指标
avg_scores = composite.aggregate_results(results_list)
print(f"Average Overall Score: {avg_scores['overall_score']:.3f}")
```

### 5.4 处理 Ground Truth 缺失数据示例

```python
from llm_model.evaluation.relationship_evaluator import RelationshipEvaluator
from llm_model.evaluation.utils import load_ground_truth, load_prediction

# 示例：GT 中某个事件的 relationships 为空
ground_truth = {
    "narrative_events": [
        {
            "id": "event1",
            "relationships": []  # GT 中缺失关系标注
        }
    ]
}

prediction = {
    "narrative_events": [
        {
            "id": "event1",
            "relationships": [
                {
                    "agent": "角色A",
                    "target": "角色B",
                    "relationship_level1": "Family & Kinship",
                    "relationship_level2": "sibling",
                    "sentiment": "positive"
                }
            ]  # 预测有关系，但 GT 为空
        }
    ]
}

evaluator = RelationshipEvaluator()
results = evaluator.evaluate(prediction, ground_truth)

# 检查 GT 不完整的情况
if results.get("gt_incomplete"):
    print(f"Warning: Ground truth incomplete - {results['gt_incomplete_reason']}")
    print(f"Predicted relationships are not counted as errors: {results['extra_relationships']}")

# 结果示例：
# {
#     "relationship_precision": None,  # 不计算（GT 不完整）
#     "relationship_recall": None,     # 不计算
#     "relationship_f1": None,
#     "gt_incomplete": True,
#     "gt_incomplete_reason": "Event 'event1' has empty relationships in ground truth",
#     "extra_relationships": [...],    # 预测的关系，但不视为错误
#     "n_events_skipped": 1           # 跳过的评估事件数
# }
```

**处理逻辑说明**：

1. **GT 缺失但预测有值**：
   - 不视为 `false_positive`
   - 标记为 `extra_*` 字段（用于报告）
   - 在报告中说明 GT 不完整

2. **GT 和预测都缺失**：
   - 视为 `true_negative`（匹配）
   - 不参与准确率计算

3. **GT 有值但预测缺失**：
   - 视为 `false_negative`（真正的错误）
   - 正常计入召回率计算

4. **部分字段缺失**（如 `action_layer`）：
   - 只评估 GT 中有值的字段
   - 缺失字段的预测值不惩罚
   - 分母只包含有 GT 值的字段数量

## 6. 测试策略 (Testing Strategy)

### 6.1 单元测试

每个评估器都应有对应的单元测试文件，测试：
- 边界情况（空列表、None 值等）
- 精确匹配场景
- 部分匹配场景
- **Ground Truth 缺失数据场景**：
  * GT 字段为空 `[]`、`None` 或空字符串 `""` 的情况
  * GT 部分字段缺失（如 `action_layer` 只有 `category`，缺少 `type`）
  * GT 整条记录缺失（如某个事件在 GT 中不存在）
  * 验证预测值不被错误地标记为 `false_positive`
  * 验证 `gt_incomplete` 标志正确设置
- 错误处理

### 6.2 集成测试

使用真实的 JSON v3 数据进行端到端测试，验证：
- 评估器之间的协作
- 数据加载和格式转换
- 指标计算的正确性

### 6.3 性能测试

对大规模数据集进行性能测试，确保评估速度可接受。

## 7. 扩展性考虑 (Extensibility)

### 7.1 自定义评估器

通过继承 `BaseEvaluator`，可以轻松添加新的评估器（例如评估 `themes_and_motifs`）。

### 7.2 自定义指标

在 `metrics.py` 中添加新的指标计算函数。

### 7.3 评估策略配置

支持通过配置文件或参数选择不同的评估策略（严格匹配 vs 模糊匹配）。

## 8. 依赖项 (Dependencies)

- `numpy`: 数值计算
- `pandas`: 数据加载和处理（CSV 文件）
- `scikit-learn`: 评估指标（可选，也可自己实现）
- 复用 `llm_model/text_segmentation/boundary_metric.py` 中的 `BoundarySegmentationMetric`

## 9. 开发计划 (Development Plan)

### Phase 1: 基础架构
- [ ] 创建目录结构和基础文件
- [ ] 实现 `BaseEvaluator` 抽象类
- [ ] 实现 `utils.py` 中的数据加载函数

### Phase 2: 核心评估器
- [ ] 实现 `CharacterEvaluator`
- [ ] 实现 `RelationshipEvaluator`
- [ ] 实现 `SentimentEvaluator`
- [ ] 实现 `ActionLayerEvaluator`

### Phase 3: 文本跨度评估
- [ ] 实现文本到句子索引的转换
- [ ] 实现 `TextSpanEvaluator`（集成 Boundary Segmentation Metric）
- [ ] 实现重叠比例计算

### Phase 4: 组合和工具
- [ ] 实现 `CompositeEvaluator`
- [ ] 实现报告生成功能
- [ ] 添加批量评估工具

### Phase 5: 测试和文档
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 编写使用文档和示例

## 10. 注意事项 (Notes)

1. **数据标准化**：不同来源的 JSON v3 数据可能有细微差异，需要统一的标准化处理
2. **别名处理**：角色别名可能导致匹配问题，需要模糊匹配策略
3. **Ground Truth 缺失数据处理**：**重要** - 当 GT 中某项数据缺失时，需要合理处理：
   - **基本原则**：GT 不完整不应该惩罚模型的预测能力
   - **处理策略**：GT 缺失的字段，预测值不视为错误，不计入 false positive
   - **评估报告**：需要明确标记哪些字段/事件存在 GT 不完整的情况（`gt_incomplete` 标志）
   - **指标计算**：分母（分母）应排除 GT 缺失的数据点
   - **示例**：
     * GT 中某个事件的 `relationships` 为空 `[]` → 预测的关系不惩罚
     * GT 中某个事件的 `action_layer.category` 为空字符串 → 只评估其他有值的字段
     * GT 中 `text_span` 为 `null` → 该事件不参与边界评估
4. **空值处理**：某些字段可能为空，评估时需要明确区分"GT 缺失"和"预测错误"两种情况
5. **性能优化**：大规模评估时，考虑并行化处理
6. **边界情况**：处理文本分割失败、句子索引转换错误等情况

## 11. 参考资料 (References)

- `docs/LLM 文本分割开发文档.md` - Boundary Segmentation Metric 算法
- `llm_model/text_segmentation/boundary_metric.py` - 现有实现
- `docs/Character_Resources/relationship.csv` - 关系分类标准
- `docs/Character_Resources/sentiment.csv` - 情感标签标准
- `docs/Universal Narrative Action Taxonomy/Universal_Narrative_Action_Taxonomy.md` - 动作分类标准

---

**文档版本**: 1.0  
**创建日期**: 2026-01-XX  
**待审核**: 等待 review 后开始实现