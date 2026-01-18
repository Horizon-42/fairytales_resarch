# 显存优化指南

## max_seq_length 说明

**是的，`max_seq_length` 包括输入 prompt 和输出。**

在训练时，`max_seq_length` 限制的是**整个序列的长度**，包括：
- System prompt
- User prompt (instruction + input)
- Assistant response (output)

例如，如果 `max_seq_length=2048`：
- 输入 prompt: 1500 tokens
- 输出 response: 500 tokens
- 总计: 2000 tokens ✅ (在限制内)

如果超过限制，序列会被截断。

## 当前代码中的显存使用

### 1. story_context 的使用

在以下步骤中，代码会传入**完整故事文本**作为 `story_context`：

- **Character Recognition** (Step 2): `story_context=story_text`
- **Relationship** (Step 4): `story_context=story_text`  
- **STAC** (Step 6): `story_context=story_text`

这些步骤的 prompt 格式：
```
System Prompt
User Prompt
  - Summary (已包含)
  - Text Span (当前段落)
  - Full Story Context (完整故事文本) ← 这里占用大量 tokens
```

### 2. 显存占用分析

假设：
- Summary: ~200 tokens
- Text Span: ~100 tokens
- Full Story: ~5000 tokens (完整故事)
- Output: ~200 tokens

**当前方式**：总计 ~5500 tokens（需要 `max_seq_length >= 5500`）

**如果只用 Summary**：总计 ~500 tokens（只需要 `max_seq_length >= 500`）

**节省**：约 90% 的 tokens！

## 优化方案：使用 Summary 替代 Full Story

### 方案 1：完全移除 story_context（推荐）

修改 `data_preparation.py`，不再传入完整故事文本：

```python
# 修改前
story_context=story_text if story_text != text else None

# 修改后
story_context=None  # 只使用 summary，不使用完整故事
```

**优点**：
- 大幅减少 tokens（90%+）
- 可以使用更小的 `max_seq_length`（如 512 或 1024）
- 训练速度更快
- 显存占用更少

**缺点**：
- 模型可能失去一些长距离上下文信息
- 但对于大多数任务，summary 已经足够

### 方案 2：条件使用 story_context

只在必要时（如长文本段落）使用完整故事：

```python
# 如果 text_span 很短，使用完整故事；否则只用 summary
if len(text.split()) < 50:  # 短段落
    story_context = story_text
else:  # 长段落，只用 summary
    story_context = None
```

### 方案 3：截断 story_context

如果必须使用完整故事，可以截断：

```python
# 只使用故事的前 N 个字符
max_context_length = 1000  # 字符数
if story_text and len(story_text) > max_context_length:
    story_context = story_text[:max_context_length] + "..."
else:
    story_context = story_text
```

## 推荐配置

### 使用 Summary 的配置（推荐）

```python
# config.py
max_seq_length: int = 1024  # 从 2048 降低到 1024

# data_preparation.py
story_context = None  # 不使用完整故事
```

**预期效果**：
- 显存占用：减少 70-90%
- 训练速度：提升 2-3 倍
- 批次大小：可以增加（如从 4 到 8）

### 保留 Full Story 的配置（如果需要完整上下文）

```python
# config.py
max_seq_length: int = 4096  # 增加到 4096 或更高

# data_preparation.py
story_context = story_text  # 保留完整故事
```

**预期效果**：
- 显存占用：较高
- 训练速度：较慢
- 可能需要启用 CPU offload

## 实施建议

1. **先测试 Summary 方案**：
   - 修改 `data_preparation.py` 移除 `story_context`
   - 降低 `max_seq_length` 到 1024
   - 运行训练，观察效果

2. **如果效果不好，再考虑**：
   - 使用方案 2（条件使用）
   - 或方案 3（截断）

3. **监控指标**：
   - 训练 loss
   - 验证准确率
   - 显存使用率
   - 训练速度

## 代码修改示例

### 修改 data_preparation.py

```python
# Character Recognition
instruction = build_character_prompt_for_training(
    text_span=text,
    summary=summary or "",
    existing_characters=current_characters,
    story_context=None  # 改为 None，不使用完整故事
)

# Relationship
instruction = build_relationship_prompt_for_training(
    text_span=text,
    summary=summary or "",
    doers=agents,
    receivers=targets,
    story_context=None  # 改为 None
)

# STAC
instruction = build_stac_prompt_for_training(
    text_span=text,
    summary=summary or "",
    story_context=None  # 改为 None
)
```

### 修改 config.py

```python
max_seq_length: int = 1024  # 从 2048 降低
```

## 总结

- ✅ `max_seq_length` 包括输入和输出
- ✅ 使用 summary 替代完整故事可以节省 90%+ tokens
- ✅ 推荐先尝试完全移除 `story_context`
- ✅ 如果效果不好，再考虑条件使用或截断方案
