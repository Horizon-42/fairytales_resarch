#!/usr/bin/env python3
"""
清洗 JSON v3 标注数据中的 text 字段。

从 annotation_status.csv 中读取包含 narrative 的条目，
清理对应 v3 JSON 文件中的所有 text 字段，
保存到 synthetic_datasets/groundtruth 文件夹。
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List


def remove_text_from_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """递归移除 JSON 数据中的所有 text 字段。"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # 跳过所有名为 "text" 的字段
            if key == "text":
                continue
            # 递归清理嵌套结构
            cleaned[key] = remove_text_from_json(value)
        return cleaned
    elif isinstance(data, list):
        return [remove_text_from_json(item) for item in data]
    else:
        return data


def clean_text_spans(narrative_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """清理 narrative_events 中的 text_span.text 字段。"""
    cleaned_events = []
    for event in narrative_events:
        cleaned_event = event.copy()
        if "text_span" in cleaned_event and isinstance(cleaned_event["text_span"], dict):
            text_span = cleaned_event["text_span"].copy()
            # 移除 text 字段，但保留 start 和 end
            if "text" in text_span:
                del text_span["text"]
            cleaned_event["text_span"] = text_span
        cleaned_events.append(cleaned_event)
    return cleaned_events


def clean_v3_file(input_path: Path, output_path: Path) -> bool:
    """清理单个 v3 JSON 文件。"""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 移除 source_info.text_content
        if "source_info" in data and isinstance(data["source_info"], dict):
            if "text_content" in data["source_info"]:
                del data["source_info"]["text_content"]
        
        # 移除 narrative_events 中每个 text_span.text
        if "narrative_events" in data and isinstance(data["narrative_events"], list):
            data["narrative_events"] = clean_text_spans(data["narrative_events"])
        
        # 保存清理后的文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False


def main():
    """主函数：从 CSV 读取，清理所有包含 narrative 的 v3 文件。"""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "post_data_process" / "annotation_status.csv"
    groundtruth_dir = repo_root / "synthetic_datasets" / "groundtruth"
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found", file=sys.stderr)
        sys.exit(1)
    
    # 读取 CSV，找出 has_narrative=True 的条目
    stories_to_process = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            has_narrative = row.get("has_narrative", "").strip().lower()
            v3_path = row.get("v3_path", "").strip()
            
            if has_narrative == "true" and v3_path:
                stories_to_process.append({
                    "story_name": row.get("story_name", ""),
                    "dataset": row.get("dataset", ""),
                    "v3_path": v3_path,
                })
    
    print(f"Found {len(stories_to_process)} stories with narrative annotations")
    
    # 处理每个故事
    success_count = 0
    for story in stories_to_process:
        input_path = repo_root / story["v3_path"]
        if not input_path.exists():
            print(f"Warning: {input_path} not found, skipping", file=sys.stderr)
            continue
        
        # 保持目录结构：synthetic_datasets/groundtruth/dataset/story_name_v3.json
        dataset_dir = groundtruth_dir / story["dataset"]
        output_filename = f"{story['story_name']}_v3.json"
        output_path = dataset_dir / output_filename
        
        if clean_v3_file(input_path, output_path):
            success_count += 1
            print(f"✓ Cleaned: {story['dataset']}/{story['story_name']}")
        else:
            print(f"✗ Failed: {story['dataset']}/{story['story_name']}", file=sys.stderr)
    
    print(f"\nCompleted: {success_count}/{len(stories_to_process)} files cleaned")
    print(f"Output directory: {groundtruth_dir}")


if __name__ == "__main__":
    main()
