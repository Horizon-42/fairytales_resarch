# 生成合成数据摘要脚本使用说明

## 功能

`generate_synthetic_summaries.py` 脚本用于为 `synthetic_datasets/generated_stories` 中的所有故事生成摘要。

### 主要特性

1. **自动扫描所有故事文件**：递归扫描 `synthetic_datasets/generated_stories` 目录下的所有 `.txt` 文件
2. **语言检测**：自动检测故事语言（中文、英文、日文等）
3. **语言对齐**：生成的摘要使用与故事相同的语言
4. **非 Thinking 模式**：使用 `think=False` 禁用 thinking 模式，加快推理速度
5. **进度保存**：每处理 10 个故事自动保存进度，支持中断后继续

## 使用方法

### 基本用法

```bash
conda run -n nlp python -m llm_model.generate_synthetic_summaries
```

### 完整参数

```bash
conda run -n nlp python -m llm_model.generate_synthetic_summaries \
    --stories-dir synthetic_datasets/generated_stories \
    --output-csv synthetic_datasets/story_summaries.csv \
    --model qwen3:8b \
    --base-url http://localhost:11434 \
    --temperature 0.3 \
    --start-from 0 \
    --max-stories 100
```

### 参数说明

- `--stories-dir`: 故事文件目录（默认：`synthetic_datasets/generated_stories`）
- `--output-csv`: 输出 CSV 文件路径（默认：`synthetic_datasets/story_summaries.csv`）
- `--model`: Ollama 模型名称（默认：`qwen3:8b`）
- `--base-url`: Ollama 服务地址（默认：`http://localhost:11434`）
- `--temperature`: 生成温度（默认：`0.3`）
- `--start-from`: 从第几个故事开始处理（用于中断后继续，默认：`0`）
- `--max-stories`: 最多处理多少个故事（用于测试，默认：处理所有）

## 输出格式

生成的 CSV 文件包含以下列：

- `story_name`: 故事名称
- `relative_path`: 相对于项目根目录的文件路径
- `culture`: 文化类型（从目录结构推断，如 "ChineseTales", "IndianTales"）
- `language`: 检测到的语言代码（'zh', 'en', 'ja' 等）
- `summary`: 生成的摘要文本

## 语言检测逻辑

1. **文件名检测**：
   - 包含 `ch_` 或 `chinese` → 中文 (zh)
   - 包含 `en_` 或 `english` 或 `indian` → 英文 (en)
   - 包含 `ja_` 或 `japanese` → 日文 (ja)

2. **内容检测**：
   - 统计中文字符比例（>10% → 中文）
   - 统计日文字符比例（>10% → 日文）
   - 统计英文单词比例（>30% → 英文）
   - 默认：英文

## 示例

### 处理所有故事

```bash
conda run -n nlp python -m llm_model.generate_synthetic_summaries
```

### 测试模式（只处理前 5 个）

```bash
conda run -n nlp python -m llm_model.generate_synthetic_summaries --max-stories 5
```

### 中断后继续（从第 50 个开始）

```bash
conda run -n nlp python -m llm_model.generate_synthetic_summaries --start-from 50
```

## 注意事项

1. **Thinking 模式**：脚本自动设置 `think=False`，使用非 thinking 模式以加快速度
2. **语言对齐**：摘要语言会自动与故事语言对齐
3. **进度保存**：每 10 个故事自动保存，可以安全中断和恢复
4. **错误处理**：单个故事失败不会中断整个流程，会在最后显示失败统计

## 输出示例

```
Scanning for story files in synthetic_datasets/generated_stories...
Found 150 story files
Using model: qwen3:8b at http://localhost:11434
Thinking mode: DISABLED (think=False)
Processing 150 stories...

[1/150] Processing: CH_002_牛郎织女
  File: synthetic_datasets/generated_stories/ChineseTales/CH_002_牛郎织女_v3/gemini/CH_002_牛郎织女_gen_01.txt
  Culture: ChineseTales
  Detected language: zh
  Generating summary in zh...
  ✓ Summary generated (245 chars)

[2/150] Processing: EN_001_The_Lion_and_the_Crane
  File: synthetic_datasets/generated_stories/IndianTales/EN_001_The_Lion_and_the_Crane_v3/gemini/EN_001_The_Lion_and_the_Crane_gen_01.txt
  Culture: IndianTales
  Detected language: en
  Generating summary in en...
  ✓ Summary generated (189 chars)

...

Done!
  Total stories processed: 150
  Successful summaries: 148
  Failed: 2
  Output file: synthetic_datasets/story_summaries.csv
```
