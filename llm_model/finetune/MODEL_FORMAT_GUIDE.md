# 模型格式说明：Unsloth vs Ollama

## 当前模型：Qwen3-8B

默认模型为 **Qwen3-8B**，支持 thinking 模式。但在本项目中进行微调和推理时，**thinking 模式默认关闭**（`enable_thinking=False`），以确保：
1. **提高效率**：直接响应，无需额外的 thinking tokens
2. **匹配训练格式**：训练数据不包含 thinking 内容
3. **行为一致**：与 Qwen2.5 风格的直接响应保持一致

代码会自动处理：
- 使用 `tokenizer.apply_chat_template(..., enable_thinking=False)` 格式化 Qwen3 输入
- 使用推荐的 non-thinking 参数：`Temperature=0.7`, `TopP=0.8`, `TopK=20`
- 过滤掉生成输出中可能出现的 thinking 内容

## 关键区别

### Unsloth（训练时）
- **格式**：HuggingFace 格式（PyTorch/Safetensors）
- **加载方式**：`FastLanguageModel.from_pretrained("unsloth/Qwen3-8B")`
- **来源**：从 HuggingFace Hub 自动下载
- **用途**：用于 LoRA 微调训练

### Ollama（推理时）
- **格式**：GGUF 格式
- **加载方式**：Ollama 本地服务
- **来源**：通过 `ollama pull` 下载
- **用途**：用于本地推理

## 答案：需要重新下载

**不能直接使用 Ollama 的模型进行训练**，原因：

1. **格式不兼容**：
   - Ollama 使用 GGUF 格式（用于推理）
   - Unsloth 需要 HuggingFace 格式（用于训练）

2. **模型来源不同**：
   - Ollama 模型：`ollama pull qwen3:8b` → GGUF 格式
   - Unsloth 模型：`unsloth/Qwen3-8B` → HuggingFace 格式

3. **自动下载**：
   - 首次运行时，unsloth 会自动从 HuggingFace 下载模型
   - 下载后会在本地缓存，后续使用不需要重新下载

## 工作流程

### 1. 训练阶段（使用 Unsloth）

```bash
# 训练时，unsloth 会自动从 HuggingFace 下载模型
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir training_data \
    --model-name unsloth/Qwen3-8B \
    --output-dir ./models
```

**首次运行会下载模型**（约 7GB，取决于模型大小），下载后缓存到：
- `~/.cache/huggingface/hub/` (Linux)
- 或 HuggingFace 默认缓存目录

### 2. 推理阶段（可选：导出到 Ollama）

如果需要用 Ollama 进行推理，可以导出为 GGUF 格式：

```python
from unsloth import FastLanguageModel

# 加载微调后的模型
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./models/character",  # 微调后的模型路径
    max_seq_length=2048,
)

# 导出为 GGUF 格式供 Ollama 使用
model.save_pretrained_gguf("models/character_gguf", tokenizer, quantization_method="q4_k_m")
```

然后创建 Ollama Modelfile 并导入。

## 模型选择建议

### 推荐模型（Unsloth 兼容）

1. **Qwen3 系列**（推荐，最新）：
   - `unsloth/Qwen3-8B`（默认，thinking 模式已关闭）
   - `Qwen/Qwen3-8B`（原始 HuggingFace 版本）

2. **Qwen2.5 系列**（上一代）：
   - `unsloth/Qwen2.5-7B-Instruct`
   - `unsloth/Qwen2.5-14B-Instruct`（更大，需要更多显存）

2. **Llama 系列**：
   - `unsloth/Llama-3.1-8B-Instruct`
   - `unsloth/Llama-3.1-70B-Instruct`

3. **其他**：
   - 任何 HuggingFace 上的模型（如果架构兼容）

### 模型大小和显存需求

- **7B 模型**：约 7GB（4-bit 量化后约 4GB）
- **14B 模型**：约 14GB（4-bit 量化后约 7GB）
- **70B 模型**：需要多 GPU 或大量显存

## 常见问题

### Q: 我已经用 Ollama 下载了 qwen3:8b，可以直接用吗？
**A**: 不可以。需要从 HuggingFace 下载 `unsloth/Qwen3-8B`（或类似的 HuggingFace 格式模型）。Ollama 的 GGUF 格式不能直接用于训练。

### Q: 训练后的模型可以在 Ollama 中使用吗？
**A**: 可以，但需要导出为 GGUF 格式。训练后的模型是 HuggingFace 格式（包含 LoRA 权重），需要转换为 GGUF 才能被 Ollama 使用。

### Q: 如何减少下载时间？
**A**: 
- 模型会缓存到本地，第二次使用不需要重新下载
- 可以使用镜像站点（如果在中国）
- 或者手动下载模型文件到缓存目录

### Q: 可以使用本地已有的 HuggingFace 模型吗？
**A**: 可以！如果本地已有 HuggingFace 格式的模型，可以直接使用路径：
```bash
--model-name /path/to/local/model
```

## 总结

- ✅ **训练时**：使用 HuggingFace 格式模型（unsloth 会自动下载）
- ❌ **不能**：直接使用 Ollama 的 GGUF 模型进行训练
- ✅ **可以**：训练后将模型导出为 GGUF 供 Ollama 使用
- 💾 **缓存**：模型下载后会缓存，后续使用不需要重新下载
