# 故障排除指南

## 常见错误和解决方案

### 1. Unsloth 导入警告

**错误信息**：
```
WARNING: Unsloth should be imported before transformers to ensure all optimizations are applied.
```

**解决方案**：
✅ 已修复：代码已在文件顶部导入 `unsloth`，警告应该消失。

### 2. 模型找不到错误

**错误信息**：
```
RuntimeError: Unsloth: No config file found - are you sure the `model_name` is correct?
```

**可能原因和解决方案**：

#### A. 模型名称不正确

**解决方案**：使用正确的模型名称

```bash
# 推荐的模型名称（按优先级）
--model-name unsloth/Qwen3-8B                  # 首选（最新 Qwen3，thinking 已关闭）
--model-name Qwen/Qwen3-8B                     # 备选（原始 HuggingFace 模型）
--model-name unsloth/Qwen2.5-7B-Instruct       # 上一代模型
--model-name unsloth/Qwen2.5-14B-Instruct      # 更大模型（需要更多显存）
--model-name unsloth/Llama-3.1-8B-Instruct      # Llama 系列
```

#### B. 网络连接问题

**症状**：无法从 HuggingFace 下载模型

**解决方案**：
1. 检查网络连接
2. 如果在中国，可能需要配置 HuggingFace 镜像或使用 VPN
3. 手动下载模型到本地，然后使用本地路径：
   ```bash
   --model-name /path/to/local/model
   ```

#### C. HuggingFace 认证问题

**症状**：某些模型需要登录才能访问

**解决方案**：
```bash
# 安装 huggingface-hub 并登录
pip install huggingface-hub
huggingface-cli login
```

### 3. 显存不足错误

**错误信息**：
```
CUDA out of memory
```

**解决方案**：
1. 减小批次大小：
   ```bash
   --batch-size 2  # 或更小
   ```
2. 使用更小的模型：
   ```bash
   --model-name unsloth/Qwen2.5-1.5B-Instruct  # 更小的模型
   ```
3. 增加梯度累积步数（保持有效批次大小）：
   ```python
   # 在 config 中设置
   gradient_accumulation_steps=8  # 增加此值
   ```

### 4. 依赖缺失错误

**错误信息**：
```
ModuleNotFoundError: No module named 'unsloth'
```

**解决方案**：
```bash
pip install -r llm_model/finetune/requirements.txt
```

### 5. 数据文件找不到

**错误信息**：
```
FileNotFoundError: Training data file not found: training_data/character_train.jsonl
```

**解决方案**：
1. 确保已提取训练数据：
   ```bash
   python -m llm_model.finetune.scripts.extract_training_data \
       --synthetic \
       --groundtruth-dir synthetic_datasets/groundtruth \
       --generated-stories-dir synthetic_datasets/generated_stories \
       --output-dir training_data
   ```
2. 检查 `training_data/` 目录下是否有对应的 JSONL 文件

## 验证步骤

在开始训练前，建议按以下顺序验证：

### 1. 检查依赖

```bash
conda run -n nlp python -c "import unsloth; print('unsloth OK')"
conda run -n nlp python -c "import transformers; print('transformers OK')"
conda run -n nlp python -c "import datasets; print('datasets OK')"
```

### 2. Mock 测试

```bash
conda run -n nlp python -m llm_model.finetune.scripts.mock_train_step \
    --step character \
    --data-dir training_data
```

### 3. 测试模型加载（单独测试）

```python
from unsloth import FastLanguageModel

# 测试模型是否可以加载
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)
print("Model loaded successfully!")
```

## 模型名称参考

### Unsloth 支持的模型

| 模型名称 | 参数量 | 显存需求（4-bit） | 推荐场景 |
|---------|--------|------------------|---------|
| `unsloth/Qwen3-8B` | 8.2B | ~4GB | **推荐默认**（最新，thinking 已关闭） |
| `Qwen/Qwen3-8B` | 8.2B | ~4GB | 备选（原始 HuggingFace） |
| `unsloth/Qwen2.5-1.5B-Instruct` | 1.5B | ~1GB | 测试、资源受限 |
| `unsloth/Qwen2.5-7B-Instruct` | 7B | ~4GB | 上一代模型 |
| `unsloth/Qwen2.5-14B-Instruct` | 14B | ~7GB | 更高性能需求 |
| `unsloth/Llama-3.1-8B-Instruct` | 8B | ~4GB | Llama 系列 |

### 如果 unsloth 版本不可用

可以使用原始 HuggingFace 模型（但可能性能稍差）：

```bash
--model-name Qwen/Qwen3-8B  # Qwen3 原始版本
# 或
--model-name Qwen/Qwen2.5-7B-Instruct  # Qwen2.5 原始版本
```

### Qwen3 Thinking 模式

**注意**：Qwen3 支持 thinking 模式，但在此项目中**默认关闭**。代码会自动：
- 在格式化时使用 `enable_thinking=False`
- 使用推荐的 non-thinking 参数（Temperature=0.7, TopP=0.8）
- 过滤掉任何可能生成的 thinking 内容

如果遇到模型生成 `<think>...</think>` 标签，这是正常的，代码会自动处理。

## 获取帮助

如果遇到其他问题：

1. 检查错误日志的完整堆栈跟踪
2. 确认所有依赖已正确安装
3. 验证网络连接和 HuggingFace 访问
4. 查看 [MODEL_FORMAT_GUIDE.md](MODEL_FORMAT_GUIDE.md) 了解模型格式要求
