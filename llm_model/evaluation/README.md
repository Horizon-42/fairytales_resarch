# LLM 结果评估模块 (Evaluation Package)

用于评估 LLM 生成的 JSON v3 格式标注结果的评估模块。

## 功能特性

- ✅ **解耦设计**：各组件（角色、关系、情感、动作层、文本跨度）独立评估
- ✅ **缺失数据处理**：合理处理 Ground Truth 缺失数据的情况
- ✅ **文本跨度评估**：使用 Boundary Segmentation Metric 算法评估文本边界
- ✅ **综合报告**：支持 JSON 和 Markdown 格式的评估报告生成
- ✅ **批量评估**：支持批量处理多个文件并聚合结果

## 快速开始

### 基本使用

```python
from llm_model.evaluation import CompositeEvaluator
from llm_model.evaluation.utils import load_ground_truth, load_prediction

# 加载数据
ground_truth = load_ground_truth("datasets/ChineseTales/json_v3/CH_002_牛郎织女_v3.json")
prediction = load_prediction("llm_output/CH_002_牛郎织女_v3_pred.json")

# 创建组合评估器
composite = CompositeEvaluator()

# 执行评估
results = composite.evaluate(prediction, ground_truth)

# 查看结果
print(f"Overall Score: {results['overall_score']:.3f}")
print(f"Component Scores: {results['component_scores']}")
```

### 单独使用某个评估器

```python
from llm_model.evaluation import CharacterEvaluator

# 创建评估器
evaluator = CharacterEvaluator()

# 执行评估
results = evaluator.evaluate(prediction, ground_truth)

# 查看结果
print(f"Character F1: {results['character_f1']:.3f}")
print(f"Missing characters: {results['missing_characters']}")
```

### 生成评估报告

```python
# 生成 JSON 报告
composite.generate_report(results, output_path="report.json", format="json")

# 生成 Markdown 报告
composite.generate_report(results, output_path="report.md", format="markdown")
```

## 评估组件

### 1. CharacterEvaluator（角色评估器）

评估角色列表的准确性和完整性。

**输出指标**：
- `character_f1`: F1 分数
- `character_archetype_accuracy`: 角色类型匹配准确率
- `missing_characters`: 缺失的角色列表
- `extra_characters`: 多余的角色列表

### 2. RelationshipEvaluator（关系评估器）

评估叙事事件中的关系标注。

**输出指标**：
- `relationship_f1`: 关系 F1 分数
- `level1_accuracy`: Level 1 分类准确率
- `level2_accuracy`: Level 2 分类准确率

### 3. SentimentEvaluator（情感评估器）

评估叙事事件中的情感标注。

**输出指标**：
- `sentiment_f1`: 情感 F1 分数
- `sentiment_polarity_accuracy`: 情感极性准确率（正负中性分类）

### 4. ActionLayerEvaluator（动作层评估器）

评估叙事事件中的动作层标注。

**输出指标**：
- `action_category_accuracy`: Category 准确率
- `action_type_accuracy`: Type 准确率
- `action_context_accuracy`: Context 准确率
- `action_status_accuracy`: Status 准确率
- `action_function_accuracy`: Function 准确率
- `action_layer_complete_match`: 完全匹配的动作层比例

### 5. TextSpanEvaluator（文本跨度评估器）

评估 `text_span` 的边界准确性。

**输出指标**：
- `boundary_score`: Boundary Segmentation Metric 得分（0-1）
- `mean_overlap`: 文本片段平均重叠比例

## 缺失数据处理

当 Ground Truth 中某项数据缺失时，评估模块会采用合理的处理策略：

- **GT 缺失但预测有值**：不视为错误，不计入 false positive
- **GT 和预测都缺失**：视为匹配（true negative）
- **GT 有值但预测缺失**：视为缺失（false negative）

在评估结果中，缺失数据的情况会被标记为 `gt_incomplete: true`。

## 文件结构

```
llm_model/evaluation/
├── __init__.py                 # 包初始化
├── base_evaluator.py          # 基础评估器抽象类
├── character_evaluator.py     # 角色评估器
├── relationship_evaluator.py  # 关系评估器
├── sentiment_evaluator.py     # 情感评估器
├── action_layer_evaluator.py  # 动作层评估器
├── text_span_evaluator.py     # 文本跨度评估器
├── composite_evaluator.py     # 组合评估器
├── utils.py                   # 工具函数
├── metrics.py                 # 评估指标计算
├── README.md                  # 本文档
├── README_DEVELOPMENT.md      # 开发文档
├── quick_test.py              # 快速测试脚本
├── example_usage.py           # 使用示例
└── tests/                     # 测试目录
    └── __init__.py
```

## 运行测试

```bash
# 使用 conda 环境 nlp
conda run -n nlp python3 llm_model/evaluation/quick_test.py

# 运行使用示例
conda run -n nlp python3 llm_model/evaluation/example_usage.py
```

## 依赖项

- Python 3.9+
- numpy
- pandas（可选，用于 CSV 文件加载）
- `llm_model.text_segmentation.boundary_metric`（用于文本跨度评估）

## 参考文档

详细的开发文档请参阅 `README_DEVELOPMENT.md`。

## 许可证

与项目主许可证保持一致。