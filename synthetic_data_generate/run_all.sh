#!/bin/bash
# 一键运行脚本：清洗 JSON v3 数据并生成故事

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Step 1: Cleaning JSON v3 annotations ==="
python3 synthetic_data_generate/clean_v3_annotations.py

echo ""
echo "=== Step 2: Generating stories with Gemini 3 Flash (temperature=1.0) ==="
python3 synthetic_data_generate/generate_stories.py \
    --model gemini \
    --temperature 1.0 \
    --num-stories 10

echo ""
echo "=== Step 3: Generating stories with GPT-3 (if configured) ==="
# 如果需要使用 GPT-3，取消下面的注释并配置相关环境变量
# python3 synthetic_data_generate/generate_stories.py \
#     --model gpt3 \
#     --temperature 1.0 \
#     --num-stories 10

echo ""
echo "=== All done! ==="
echo "Groundtruth files: synthetic_datasets/groundtruth/"
echo "Generated stories: synthetic_datasets/generated_stories/"
