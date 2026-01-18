# 故事生成 Prompts

本目录包含为所有有 narrative 标注的故事生成的 prompts，可直接在网页聊天中使用。

## 目录结构

```
prompts/
├── ChineseTales/          # 中国故事 (9个)
│   ├── CH_002_牛郎织女/
│   │   └── prompt.txt
│   └── ...
├── IndianTales/            # 印度故事 (20个)
│   ├── EN_001_The_Lion_and_the_Crane/
│   │   └── prompt.txt
│   └── ...
└── Japanese/              # 日本故事 (20个)
    ├── jp_001/
    │   └── prompt.txt
    └── ...
```

## 使用方法

1. **在网页聊天中使用**：
   - 打开任意故事的 `prompt.txt` 文件
   - 复制完整的 prompt 内容
   - 粘贴到网页聊天界面（如 ChatGPT、Claude、Gemini 等）
   - 模型会根据 prompt 生成对应的故事

2. **批量生成**：
   - 使用 `generate_prompts.py` 脚本可以重新生成所有 prompts
   - 支持按数据集筛选：`--dataset ChineseTales`
   - 支持不同的输出格式：`--format flat` 或 `--format nested`

## 生成脚本

使用 `generate_prompts.py` 脚本生成 prompts：

```bash
# 生成所有故事的 prompts（嵌套格式）
python3 synthetic_data_generate/generate_prompts.py --format nested

# 生成所有故事的 prompts（扁平格式）
python3 synthetic_data_generate/generate_prompts.py --format flat

# 只生成特定数据集的 prompts
python3 synthetic_data_generate/generate_prompts.py --dataset ChineseTales

# 指定输出目录
python3 synthetic_data_generate/generate_prompts.py --output-dir /path/to/output
```

## Prompt 说明

每个 prompt 包含：
- **故事信息**：标题、文化背景、语言要求
- **角色列表**：所有角色及其原型类型
- **叙事结构**：按时间顺序排列的事件列表
- **生成要求**：叙事流程、角色发展、文化真实性等
- **输出格式**：要求使用 `{}` 包裹每个段落

## 统计信息

- **总计**：49 个故事
- **中国故事**：9 个
- **印度故事**：20 个
- **日本故事**：20 个

## 注意事项

1. 每个 prompt 都是针对特定故事定制的，包含该故事的完整叙事结构
2. Prompt 中明确指定了故事语言（中文、English、Japanese 等）
3. 输出格式要求每个事件对应一个用 `{}` 包裹的段落
4. 所有 prompts 都复用了 `generate_stories.py` 中的 `build_story_generation_prompt` 函数
