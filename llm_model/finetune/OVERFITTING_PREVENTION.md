# 防止过拟合指南

## 问题

使用 50 个故事生成多个版本进行微调存在过拟合风险，因为：

1. 样本多样性不足（只有 50 个不同故事）
2. 即使生成多个版本，核心情节和模式仍然相似
3. 模型可能"记住"特定故事而不是学习通用规律

## 解决方案

我们实施了三个关键改进：

### 1. 按故事ID划分训练/验证集

**问题**：原来的划分方式可能把同一故事的不同版本分到训练集和验证集，导致数据泄漏。

**解决**：确保同一故事的所有版本都在同一集合（训练或验证）中。

```bash
# 按故事ID重新划分数据
python -m llm_model.finetune.scripts.split_by_story \
  --data-dir training_data \
  --step character \
  --train-ratio 0.8 \
  --seed 42

# 对所有步骤执行
for step in character instrument relationship action stac event_type; do
  python -m llm_model.finetune.scripts.split_by_story \
    --data-dir training_data \
    --step $step \
    --train-ratio 0.8 \
    --seed 42
done
```

这会生成：
- `character_train.jsonl` - 来自 80% 故事的训练数据
- `character_val.jsonl` - 来自 20% 故事的验证数据

### 2. 调整训练配置

在 [config.py](config.py) 中已经做了以下调整：

**减少过拟合的配置：**
```python
# LoRA 配置
lora_dropout: float = 0.1  # 从 0 增加到 0.1（正则化）

# 训练配置
num_epochs: int = 2  # 从 3 减少到 2（减少训练轮数）

# Early stopping
early_stopping_patience: int = 3  # 连续3次评估无改善则停止
early_stopping_threshold: float = 0.001  # 最小改善阈值
```

**为什么这些有效：**
- **LoRA dropout**: 在训练时随机丢弃一些 LoRA 权重，防止模型过度依赖特定模式
- **减少 epochs**: 限制模型在同一数据上重复训练的次数
- **Early stopping**: 自动检测过拟合并提前停止

### 3. Early Stopping

现在训练会自动监控验证损失：

```bash
# 使用验证集训练（自动启用 early stopping）
python -m llm_model.finetune.scripts.train_step \
  --step character \
  --data-dir training_data \
  --output-dir ./models
```

**Early stopping 工作流程：**
1. 每 50 步在验证集上评估
2. 跟踪最佳验证损失
3. 如果连续 3 次评估无改善（< 0.001），自动停止训练
4. 加载最佳检查点

**示例输出：**
```
📊 Early stopping: Initial eval_loss = 0.4523
✓ Early stopping: eval_loss improved by 0.0234 (0.4523 → 0.4289)
⚠️  Early stopping: No improvement for 1/3 evaluations (current: 0.4301, best: 0.4289)
⚠️  Early stopping: No improvement for 2/3 evaluations (current: 0.4315, best: 0.4289)
🛑 Early stopping triggered! Stopping training.
```

## 完整工作流程

### 步骤 1: 重新划分数据

```bash
# 为所有步骤按故事ID重新划分
cd /home/supercomputing/studys/fairytales_resarch

for step in character instrument relationship action stac event_type; do
  echo "Splitting $step..."
  python -m llm_model.finetune.scripts.split_by_story \
    --data-dir training_data \
    --step $step \
    --train-ratio 0.8 \
    --seed 42
done
```

### 步骤 2: 训练（带 Early Stopping）

```bash
# 单步训练
python -m llm_model.finetune.scripts.train_step \
  --step character \
  --data-dir training_data \
  --output-dir ./models

# 顺序训练多步
python -m llm_model.finetune.scripts.train_step \
  --step character relationship action \
  --data-dir training_data \
  --output-dir ./models
```

### 步骤 3: 监控过拟合

**检查训练历史：**
```bash
# 查看损失历史
cat ./models/character/loss_history.csv
```

**检查过拟合迹象：**
- ❌ **训练损失持续下降，验证损失上升** → 过拟合
- ✅ **训练和验证损失都下降** → 良好
- ✅ **Early stopping 在合理时机触发** → 良好

## 其他建议

### 短期（当前数据）

1. ✅ **已实施**：按故事划分训练/验证集
2. ✅ **已实施**：添加 dropout (0.1)
3. ✅ **已实施**：减少 epochs (3→2)
4. ✅ **已实施**：Early stopping

### 中期（提升质量）

5. **增加数据多样性**：
   - 收集更多不同的故事（目标：200+）
   - 使用跨文化数据（日本、中国、欧洲童话）

6. **使用数据增强**：
   - 生成版本时增加变化强度
   - 改变情节顺序
   - 使用不同的叙述视角

### 长期（最佳实践）

7. **三集划分**：
   - 训练集：60% 故事
   - 验证集：20% 故事（用于 early stopping）
   - 测试集：20% 故事（用于最终评估）

8. **K-fold 交叉验证**：
   - 在不同的故事子集上训练多个模型
   - 评估模型在完全未见故事上的表现

## 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `lora_dropout` | 0.1 | LoRA dropout率（0=无dropout，0.1=10%dropout）|
| `num_epochs` | 2 | 训练轮数 |
| `early_stopping_patience` | 3 | 连续无改善的评估次数 |
| `early_stopping_threshold` | 0.001 | 最小改善阈值 |
| `eval_steps` | 50 | 每多少步评估一次 |
| `save_steps` | 50 | 每多少步保存checkpoint |

## 常见问题

**Q: 如何禁用 early stopping？**

A: 训练时不提供验证数据：
```bash
python -m llm_model.finetune.scripts.train_step \
  --step character \
  --data-dir training_data \
  --output-dir ./models \
  --train-split 1.0  # 使用 100% 数据训练，无验证集
```

**Q: 如何调整 early stopping 灵敏度？**

A: 修改 [config.py](config.py)：
```python
# 更宽容（允许更多次无改善）
early_stopping_patience: int = 5

# 更严格（要求更大的改善）
early_stopping_threshold: float = 0.01
```

**Q: 训练损失很低（< 0.01）是否正常？**

A: **不正常**，这通常表示过拟合。应该：
1. 检查验证损失是否也很低
2. 在新故事上测试模型性能
3. 考虑增加正则化（更高的 dropout，更少的 epochs）

**Q: 如何确认没有数据泄漏？**

A: 检查训练和验证文件：
```bash
# 查看训练集的故事
python3 << EOF
import json
stories = set()
with open('training_data/character_train.jsonl', 'r') as f:
    for line in f:
        # 需要根据实际数据格式提取故事ID
        pass
EOF
```

## 性能监控

推荐监控指标：

1. **训练损失 vs 验证损失**
   - 如果训练损失 ≪ 验证损失 → 过拟合

2. **准确率差异**
   - 训练准确率 vs 验证准确率
   - 如果差异 > 10% → 可能过拟合

3. **Early stopping 行为**
   - 如果在第 1 个 epoch 就触发 → 可能需要更多训练
   - 如果从不触发 → 可能需要更严格的阈值

## 总结

✅ **已实施的改进：**
1. 按故事ID划分数据（防止数据泄漏）
2. 添加 LoRA dropout（正则化）
3. 减少训练轮数（防止过度训练）
4. 实现 Early Stopping（自动检测过拟合）

🎯 **预期效果：**
- 减少过拟合风险
- 提高模型在新故事上的泛化能力
- 自动在最佳时机停止训练

📊 **下一步：**
- 在新故事上测试模型性能
- 监控训练/验证损失曲线
- 考虑收集更多多样化的故事数据
