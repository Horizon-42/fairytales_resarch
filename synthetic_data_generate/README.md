# Synthetic Data Generation

根据清洗后的 JSON v3 标注数据生成故事文本的脚本。

## 功能

1. **清洗 JSON v3 标注数据** (`clean_v3_annotations.py`)
   - 从 `annotation_status.csv` 中读取包含 narrative 的条目
   - 清理 JSON v3 文件中的所有 `text` 字段（包括 `source_info.text_content` 和 `narrative_events[].text_span.text`）
   - 保存到 `synthetic_datasets/groundtruth/` 目录

2. **生成故事文本** (`generate_stories.py`)
   - 使用清洗后的 JSON v3 标注数据生成故事
   - 支持 Gemini 3 Flash 模型（默认）
   - 可配置温度参数以增加创作性
   - 每个 JSON 文件可生成多个故事（默认 10 个）

## 使用方法

### 步骤 1: 清洗 JSON v3 标注数据

```bash
python3 synthetic_data_generate/clean_v3_annotations.py
```

这将：
- 读取 `post_data_process/annotation_status.csv`
- 找出所有 `has_narrative=True` 的条目
- 清理对应的 v3 JSON 文件中的 text 字段
- 保存到 `synthetic_datasets/groundtruth/` 目录，保持原有的目录结构

### 步骤 2: 生成故事

```bash
# 使用 Gemini 3 Flash，温度 1.0，每个 JSON 生成 10 篇故事
python3 synthetic_data_generate/generate_stories.py \
    --model gemini \
    --temperature 1.0 \
    --num-stories 10
```

参数说明：
- `--groundtruth-dir`: 清洗后的 JSON 文件目录（默认: `synthetic_datasets/groundtruth`）
- `--output-dir`: 生成故事的输出目录（默认: `synthetic_datasets/generated_stories`）
- `--model`: 使用的模型（`gemini` 或 `gpt3`，默认: `gemini`）
- `--temperature`: 生成温度（默认: 1.0，越高越有创意）
- `--num-stories`: 每个 JSON 生成的故事数量（默认: 10）
- `--file`: 只处理指定的 JSON 文件（可选）

### 一键运行

```bash
bash synthetic_data_generate/run_all.sh
```

## 环境变量配置

确保在项目根目录的 `.env` 文件中配置：

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# 如果需要使用 GPT-3
# OPENAI_API_KEY=your_openai_api_key_here
```

## 输出结构

```
synthetic_datasets/
├── groundtruth/              # 清洗后的 JSON v3 文件
│   ├── ChineseTales/
│   │   ├── CH_002_牛郎织女_v3.json
│   │   └── ...
│   ├── IndianTales/
│   └── Japanese/
└── generated_stories/        # 生成的故事文本
    ├── ChineseTales/
    │   └── CH_002_牛郎织女_v3/
    │       ├── gemini/
    │       │   ├── CH_002_牛郎织女_gen_01.txt
    │       │   ├── CH_002_牛郎织女_gen_02.txt
    │       │   └── ...
    │       └── gpt3/  # 如果使用 GPT-3
    └── ...
```

## Prompt 设计

生成故事使用的 prompt 包含：
- 故事标题和文化背景
- 角色列表（名称和原型）
- 按时间顺序排列的叙事事件（事件类型、描述、角色、目标）
- 详细的生成指令，要求保持文化真实性和叙事连贯性

## 注意事项

1. **API 限制**: 脚本会在每个请求之间暂停 1 秒，以避免触发 API 速率限制
2. **GPT-3 支持**: 当前 GPT-3 生成功能尚未完全实现，需要根据实际使用的模型进行配置
3. **温度参数**: 建议使用较高的温度（0.8-1.2）以增加故事的多样性
