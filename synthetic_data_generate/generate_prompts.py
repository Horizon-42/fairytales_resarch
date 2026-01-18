#!/usr/bin/env python3
"""
根据 annotation_status.csv 遍历数据集中有 narrative 的故事，
为每个故事生成 prompt 并保存为文件，方便在网页聊天中使用。
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 添加 repo_root 到路径，以便导入 generate_stories 中的函数
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from synthetic_data_generate.generate_stories import build_story_generation_prompt


def load_annotation_status(csv_path: Path) -> list[Dict[str, str]]:
    """加载 annotation_status.csv 文件。
    
    Returns:
        包含所有行的字典列表
    """
    stories = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stories.append(row)
    return stories


def filter_stories_with_narrative(stories: list[Dict[str, str]]) -> list[Dict[str, str]]:
    """筛选出有 narrative 的故事。
    
    Args:
        stories: 故事列表
        
    Returns:
        有 narrative 的故事列表
    """
    return [
        story for story in stories 
        if story.get('has_narrative', '').lower() == 'true'
    ]


def generate_prompt_for_story(
    json_path: Path,
    output_path: Path,
    repo_root: Path
) -> bool:
    """为单个故事生成 prompt 并保存。
    
    Args:
        json_path: JSON v3 文件路径（可能是相对路径）
        output_path: 输出 prompt 文件路径
        repo_root: 项目根目录
        
    Returns:
        是否成功生成
    """
    try:
        # 处理相对路径
        if not json_path.is_absolute():
            json_path = repo_root / json_path
        
        if not json_path.exists():
            print(f"  Warning: JSON file not found: {json_path}", file=sys.stderr)
            return False
        
        # 读取 JSON 数据
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 生成 prompt
        prompt = build_story_generation_prompt(json_data)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存 prompt
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return True
    except Exception as e:
        print(f"  Error processing {json_path}: {e}", file=sys.stderr)
        return False


def main():
    """主函数：遍历所有有 narrative 的故事并生成 prompt。"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate prompts for stories with narrative annotations"
    )
    parser.add_argument(
        "--status-csv",
        type=str,
        default=str(repo_root / "post_data_process" / "annotation_status.csv"),
        help="Path to annotation_status.csv file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(repo_root / "synthetic_data_generate" / "prompts"),
        help="Output directory for prompt files",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["flat", "nested"],
        default="nested",
        help="Output format: 'flat' (all in one dir) or 'nested' (organized by dataset/story)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        help="Filter by specific dataset (optional)",
    )
    
    args = parser.parse_args()
    
    status_csv_path = Path(args.status_csv)
    output_dir = Path(args.output_dir)
    
    if not status_csv_path.exists():
        print(f"Error: {status_csv_path} not found", file=sys.stderr)
        sys.exit(1)
    
    # 加载 CSV
    print(f"Loading annotation status from: {status_csv_path}")
    all_stories = load_annotation_status(status_csv_path)
    
    # 筛选有 narrative 的故事
    stories_with_narrative = filter_stories_with_narrative(all_stories)
    
    # 如果指定了数据集，进一步筛选
    if args.dataset:
        stories_with_narrative = [
            s for s in stories_with_narrative 
            if s.get('dataset', '') == args.dataset
        ]
    
    print(f"Found {len(stories_with_narrative)} stories with narrative annotations")
    
    if len(stories_with_narrative) == 0:
        print("No stories to process.")
        return
    
    # 处理每个故事
    success_count = 0
    fail_count = 0
    
    for story in stories_with_narrative:
        dataset = story.get('dataset', '')
        story_name = story.get('story_name', '')
        v3_path = story.get('v3_path', '')
        
        if not v3_path:
            print(f"  Skipping {story_name}: no v3_path", file=sys.stderr)
            fail_count += 1
            continue
        
        print(f"Processing: {dataset}/{story_name}...", end=" ", flush=True)
        
        # 确定输出路径
        if args.format == "nested":
            # 嵌套格式：output_dir/dataset/story_name/prompt.txt
            output_path = output_dir / dataset / story_name / "prompt.txt"
        else:
            # 扁平格式：output_dir/dataset_story_name_prompt.txt
            safe_story_name = story_name.replace('/', '_').replace('\\', '_')
            output_path = output_dir / f"{dataset}_{safe_story_name}_prompt.txt"
        
        # 生成 prompt
        json_path = Path(v3_path)
        if generate_prompt_for_story(json_path, output_path, repo_root):
            print("✓")
            success_count += 1
        else:
            print("✗")
            fail_count += 1
    
    print(f"\nCompleted: {success_count} succeeded, {fail_count} failed")
    print(f"Prompts saved to: {output_dir}")


if __name__ == "__main__":
    main()
