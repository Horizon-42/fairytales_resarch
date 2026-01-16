#!/usr/bin/env python3
"""
遍历 datasets/ 目录中的所有子文件夹，检查标注文件的存在情况。
从 texts/ 目录获取故事列表，检查是否有对应的 v2、v3 标注文件。
如果有 v3 标注，进一步检查是否有 narrative 标注。
将结果写入 CSV 文件。
"""

import json
import os
import csv
from pathlib import Path
from typing import List, Dict, Tuple


def get_story_basename(text_file: Path) -> str:
    """
    从文本文件名提取故事的基础名称（去除扩展名）。
    例如: CH_002_牛郎织女.txt -> CH_002_牛郎织女
    """
    return text_file.stem


def check_v2_annotation(dataset_dir: Path, story_basename: str, datasets_base: Path) -> Tuple[bool, str]:
    """
    检查是否存在 v2 标注文件
    返回: (是否存在, 相对路径)
    """
    json_v2_dir = dataset_dir / "json_v2"
    if not json_v2_dir.exists():
        return False, ""
    
    # 尝试多种可能的文件名格式
    possible_names = [
        f"{story_basename}_v2.json",
        f"{story_basename}.json",  # 有些可能没有 _v2 后缀
    ]
    
    for name in possible_names:
        json_file = json_v2_dir / name
        if json_file.exists():
            # 返回相对路径
            relative_path = json_file.relative_to(datasets_base.parent)
            return True, str(relative_path)
    
    return False, ""


def check_v3_annotation(dataset_dir: Path, story_basename: str, datasets_base: Path) -> Tuple[bool, str]:
    """
    检查是否存在 v3 标注文件
    返回: (是否存在, 相对路径)
    """
    json_v3_dir = dataset_dir / "json_v3"
    if not json_v3_dir.exists():
        return False, ""
    
    # 尝试多种可能的文件名格式
    possible_names = [
        f"{story_basename}_v3.json",
        f"{story_basename}.json",  # 有些可能没有 _v3 后缀
    ]
    
    for name in possible_names:
        json_file = json_v3_dir / name
        if json_file.exists():
            # 返回相对路径
            relative_path = json_file.relative_to(datasets_base.parent)
            return True, str(relative_path)
    
    return False, ""


def check_narrative_annotation(dataset_dir: Path, story_basename: str) -> bool:
    """
    检查 v3 标注文件中是否有 narrative 标注。
    返回 True 如果存在有效的 narrative_events。
    
    特殊情况：
    - 如果数组长度为1，且第一个事件的 text_span 是 null，视为无 narrative。
    """
    json_v3_dir = dataset_dir / "json_v3"
    if not json_v3_dir.exists():
        return False
    
    # 尝试多种可能的文件名格式
    possible_names = [
        f"{story_basename}_v3.json",
        f"{story_basename}.json",
    ]
    
    for name in possible_names:
        json_file = json_v3_dir / name
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 检查是否有 narrative_events 字段且非空
                    narrative_events = data.get("narrative_events", [])
                    if not narrative_events or len(narrative_events) == 0:
                        return False
                    
                    # 特殊情况：如果数组长度为1，且第一个事件的 text_span 是 null，视为无 narrative
                    if len(narrative_events) == 1:
                        first_event = narrative_events[0]
                        text_span = first_event.get("text_span")
                        if text_span is None:
                            return False
                    
                    return True
            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f"  Warning: Error reading {json_file}: {e}")
                return False
    
    return False


def process_dataset(datasets_base: Path, dataset_name: str) -> List[Dict]:
    """
    处理单个数据集目录，返回该数据集的所有故事检查结果。
    """
    dataset_dir = datasets_base / dataset_name
    texts_dir = dataset_dir / "texts"
    
    results = []
    
    if not texts_dir.exists():
        print(f"  Warning: {texts_dir} does not exist, skipping...")
        return results
    
    # 获取所有文本文件
    text_files = sorted(text_files for text_files in texts_dir.glob("*.txt"))
    
    if not text_files:
        print(f"  No text files found in {texts_dir}")
        return results
    
    print(f"\nProcessing dataset: {dataset_name} ({len(text_files)} text files)")
    
    for text_file in text_files:
        story_basename = get_story_basename(text_file)
        
        # 检查 v2 标注
        has_v2, v2_path = check_v2_annotation(dataset_dir, story_basename, datasets_base)
        
        # 检查 v3 标注
        has_v3, v3_path = check_v3_annotation(dataset_dir, story_basename, datasets_base)
        
        # 如果有 v3，检查 narrative 标注
        has_narrative = False
        if has_v3:
            has_narrative = check_narrative_annotation(dataset_dir, story_basename)
        
        # 使用相对路径
        text_relative_path = text_file.relative_to(datasets_base.parent)
        
        result = {
            "dataset": dataset_name,
            "story_name": story_basename,
            "text_file": str(text_relative_path),
            "has_v2": has_v2,
            "v2_path": v2_path,
            "has_v3": has_v3,
            "v3_path": v3_path,
            "has_narrative": has_narrative,
        }
        
        results.append(result)
        
        status = []
        if has_v2:
            status.append("v2")
        if has_v3:
            status.append("v3")
        if has_narrative:
            status.append("narrative")
        
        status_str = ", ".join(status) if status else "none"
        print(f"  {story_basename}: {status_str}")
    
    return results


def main():
    """主函数：遍历所有数据集并生成 CSV 报告"""
    # 获取脚本所在目录的父目录（项目根目录）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    datasets_dir = project_root / "datasets"
    
    if not datasets_dir.exists():
        print(f"Error: {datasets_dir} does not exist!")
        return
    
    print(f"Scanning datasets in: {datasets_dir}")
    
    # 获取所有数据集子目录
    dataset_dirs = [d for d in datasets_dir.iterdir() 
                   if d.is_dir() and not d.name.startswith('.')]
    
    if not dataset_dirs:
        print("No dataset directories found!")
        return
    
    all_results = []
    
    # 处理每个数据集
    for dataset_dir in sorted(dataset_dirs):
        dataset_name = dataset_dir.name
        results = process_dataset(datasets_dir, dataset_name)
        all_results.extend(results)
    
    # 写入 CSV 文件
    output_file = script_dir / "annotation_status.csv"
    
    fieldnames = [
        "dataset",
        "story_name",
        "text_file",
        "has_v2",
        "v2_path",
        "has_v3",
        "v3_path",
        "has_narrative",
    ]
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total stories: {len(all_results)}")
    print(f"  Stories with v2: {sum(1 for r in all_results if r['has_v2'])}")
    print(f"  Stories with v3: {sum(1 for r in all_results if r['has_v3'])}")
    print(f"  Stories with narrative: {sum(1 for r in all_results if r['has_narrative'])}")
    print(f"\nResults saved to: {output_file.relative_to(project_root)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
