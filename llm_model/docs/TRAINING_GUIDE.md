# Fine-tuning Training Guide

## Loss 记录

训练过程中会自动记录 loss 历史：

### Loss 文件位置

训练完成后，loss 历史保存在：
```
{output_dir}/{step_name}/loss_history.csv
```

### Loss 文件格式

CSV 格式，包含以下列：
- `step`: 训练步数
- `epoch`: 当前 epoch
- `train_loss`: 训练 loss
- `eval_loss`: 验证 loss（如果有验证集）
- `learning_rate`: 学习率

示例：
```csv
step,epoch,train_loss,eval_loss,learning_rate
10,0.1,2.345,,0.0002
20,0.2,2.123,2.456,0.0002
30,0.3,1.987,2.234,0.0002
...
```

### 查看 Loss

```python
import csv
from pathlib import Path

# 加载 loss 历史
loss_file = Path("./models/character_recognition/loss_history.csv")
with open(loss_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    loss_history = list(reader)

# 查看训练 loss 趋势
train_losses = [float(e["train_loss"]) for e in loss_history if e.get("train_loss")]
print(f"Final train loss: {train_losses[-1]}")
```

或者使用 pandas（如果已安装）：
```python
import pandas as pd

loss_df = pd.read_csv("./models/character_recognition/loss_history.csv")
print(loss_df.tail())  # 查看最后几行
loss_df.plot(x='step', y='train_loss')  # 绘制 loss 曲线
```

## 评估功能

### 1. 训练后自动评估（单步评估）

训练完成后，如果提供了 eval_examples，会自动在测试集上评估：

**输出文件**：
- `{output_dir}/{step_name}/step_evaluation.json` - 详细的评估结果

**评估指标**：
- `accuracy`: 准确率（精确匹配）
- `total_examples`: 测试样本总数
- `correct`: 正确预测数
- `predictions`: 每个样本的预测详情

### 2. 完整 Pipeline 评估

使用 `evaluate_model.py` 脚本评估完整 pipeline：

```bash
python -m llm_model.finetune.scripts.evaluate_model \
    --test-dir datasets/ChineseTales/json_v3 \
    --groundtruth-dir datasets/ChineseTales/json_v3 \
    --models-dir ./models \
    --output-dir ./evaluation_results
```

**输出文件**：
- `evaluation_results/evaluation_results.json` - 完整的评估结果
- `evaluation_results/evaluation_report.md` - Markdown 格式的报告

**评估指标**（来自 evaluation 模块）：
- `overall_score`: 总体得分 (0-1)
- `component_scores`: 各组件得分
  - `characters`: 角色识别 F1
  - `relationships`: 关系推断 F1
  - `sentiment`: 情感分析 F1
  - `action_layer`: 动作层准确率
  - `text_span`: 文本跨度得分

## 训练输出结构

```
models/
├── character_recognition/
│   ├── loss_history.json          # Loss 历史记录
│   ├── step_evaluation.json       # 单步评估结果（如果启用）
│   ├── adapter_config.json        # LoRA 配置
│   ├── adapter_model.bin          # LoRA 权重
│   └── ...
├── relationship_deduction/
│   └── ...
└── ...
```

## 使用示例

### 训练并自动评估

```bash
python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir training_data \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --num-epochs 3 \
    --train-split 0.9
    # 默认会进行评估，使用 --no-evaluate 跳过
```

### 仅训练（跳过评估）

```bash
python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir training_data \
    --output-dir ./models \
    --no-evaluate
```

### 训练后单独评估完整 Pipeline

```bash
python -m llm_model.finetune.scripts.evaluate_model \
    --test-dir datasets/ChineseTales/json_v3 \
    --groundtruth-dir datasets/ChineseTales/json_v3 \
    --models-dir ./models \
    --output-dir ./evaluation_results
```

## 注意事项

1. **Loss 记录**：每个训练步骤都会记录，包括 train_loss 和 eval_loss（如果有验证集）
2. **评估时机**：
   - 单步评估：训练完成后立即进行（如果启用）
   - 完整评估：需要手动运行 `evaluate_model.py`
3. **模型集成**：当前完整 pipeline 评估使用默认模型，微调模型的集成需要后续实现
4. **评估数据**：确保测试集和 groundtruth 数据格式一致
