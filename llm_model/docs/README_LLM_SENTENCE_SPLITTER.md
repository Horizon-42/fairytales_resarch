# LLM-based Sentence Splitter

基于大语言模型的句子切分工具，使用 LangChain 和 Ollama。

## 功能特点

- ✅ 使用大语言模型（默认：qwen3:8b）进行智能句子切分
- ✅ 支持多语言文本（英文、中文、日文等）
- ✅ 正确处理对话和引号（例如："Who?" he asked.）
- ✅ 使用 LangChain 框架，代码优雅且可扩展
- ✅ 支持命令行和编程接口两种使用方式

## 安装依赖

```bash
# 安装 LangChain 相关依赖
pip install -r llm_model/requirements.txt

# 或者单独安装
pip install langchain langchain-ollama langchain-core
```

## 前提条件

1. **Ollama 已安装并运行**
   ```bash
   # 确保 Ollama 服务正在运行
   curl http://localhost:11434/api/tags
   ```

2. **qwen3:8b 模型已下载**
   ```bash
   # 下载模型（如果尚未下载）
   ollama pull qwen3:8b
   ```

## 使用方法

### 命令行使用

```bash
# 基本使用
python llm_model/llm_sentence_splitter.py input.txt

# 指定输出文件
python llm_model/llm_sentence_splitter.py input.txt -o output.txt

# 使用不同的模型
python llm_model/llm_sentence_splitter.py input.txt --model qwen2.5:7b

# 指定语言提示（用于更好的切分效果）
python llm_model/llm_sentence_splitter.py input.txt --language zh

# 自定义 Ollama 服务地址
python llm_model/llm_sentence_splitter.py input.txt --base-url http://localhost:11434

# 调整温度参数（默认 0.0 用于确定性输出）
python llm_model/llm_sentence_splitter.py input.txt --temperature 0.1
```

### 编程接口使用

```python
from llm_model.llm_sentence_splitter import LLMSentenceSplitter, LLMSentenceSplitterConfig
from pathlib import Path

# 使用默认配置
splitter = LLMSentenceSplitter()

# 或者自定义配置
config = LLMSentenceSplitterConfig(
    model="qwen3:8b",
    base_url="http://localhost:11434",
    temperature=0.0,
)
splitter = LLMSentenceSplitter(config=config)

# 从字符串切分
text = '"Who shall be my teacher?" the lad asked. The King replied.'
result = splitter.split(text, language="en")
print(f"Split {result.total_count} sentences:")
for i, sentence in enumerate(result.sentences, 1):
    print(f"{i}. {sentence}")

# 从文件切分
result = splitter.split_file(
    input_path="story.txt",
    output_path="story_sentences.txt",
    language="en"
)
```

## 示例

### 处理英文文本

```bash
python llm_model/llm_sentence_splitter.py \
  datasets/IndianTales/texts/EN_020_The_Demon_with_the_Matted_Hair.txt \
  -o output_sentences.txt \
  --language en
```

### 处理中文文本

```bash
python llm_model/llm_sentence_splitter.py \
  datasets/ChineseTales/texts/CH_002_牛郎织女.txt \
  -o output_sentences.txt \
  --language zh
```

### 处理日文文本

```bash
python llm_model/llm_sentence_splitter.py \
  datasets/Japanese/texts/jp_001.txt \
  -o output_sentences.txt \
  --language ja
```

## 输出格式

输出文件格式（每行一个句子，带序号）：

```
1. First sentence.
2. Second sentence.
3. Third sentence.
...
```

## 配置说明

### LLMSentenceSplitterConfig

- `model`: Ollama 模型名称（默认：`qwen3:8b`）
- `base_url`: Ollama 服务地址（默认：`http://localhost:11434`）
- `temperature`: 生成温度（默认：`0.0`，用于确定性输出）
- `num_ctx`: 上下文窗口大小（默认：`8192`）
- `timeout_s`: 请求超时时间（默认：`300.0` 秒）

## 工作原理

1. **输入文本**：接收文本文件或字符串
2. **LLM 处理**：使用 LangChain 的 ChatOllama 调用大语言模型
3. **提示工程**：使用精心设计的 system prompt 和 user prompt
4. **JSON 解析**：解析 LLM 返回的 JSON 数组
5. **结果输出**：返回结构化的 SentenceSplitResult 对象

## 与正则表达式方法的对比

| 特性 | LLM 方法 | 正则表达式方法 |
|------|---------|--------------|
| 准确性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 多语言支持 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 对话处理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 性能 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 依赖 | 需要 Ollama | 无额外依赖 |

## 常见问题

### 1. 连接错误

```
Error: Failed to reach Ollama at http://localhost:11434
```

**解决方案**：
- 确保 Ollama 服务正在运行：`ollama serve`
- 检查端口是否正确
- 如果使用远程服务，更新 `--base-url` 参数

### 2. 模型未找到

```
Error: Model 'qwen3:8b' not found
```

**解决方案**：
```bash
# 下载模型
ollama pull qwen3:8b

# 或使用其他已安装的模型
python llm_sentence_splitter.py input.txt --model llama3.1
```

### 3. JSON 解析错误

如果遇到 JSON 解析错误，脚本会自动尝试提取 JSON 数组。如果仍然失败，请检查：
- 模型输出是否格式正确
- 尝试降低 `temperature` 参数（默认 0.0）

## 技术细节

- 使用 LangChain 的 `ChatOllama` 进行模型调用
- 支持流式和批量处理（可扩展）
- 错误处理和异常管理完善
- 代码结构清晰，易于维护和扩展

## 贡献

欢迎提交 Issue 和 Pull Request！
