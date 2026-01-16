#!/usr/bin/env python3
"""
从 annotation_status.csv 读取有 v3 标注的故事，
提取所有 narrative_events 中的 text_span，
生成新的 CSV 文件，每一行代表一个 text_span。
"""

import json
import csv
from pathlib import Path
from typing import List, Dict


def extract_text_spans_from_v3(v3_path: Path) -> List[Dict]:
    """
    从 v3 标注文件中提取所有 text_span。
    返回 text_span 列表，每个包含 start, end, text 等信息。
    """
    text_spans = []
    
    if not v3_path.exists():
        return text_spans
    
    try:
        with open(v3_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            narrative_events = data.get("narrative_events", [])
            
            for event in narrative_events:
                text_span = event.get("text_span")
                if text_span is None:
                    continue
                
                # 提取 text_span 信息
                span_info = {
                    "start": text_span.get("start", ""),
                    "end": text_span.get("end", ""),
                    "text": text_span.get("text", ""),
                    "event_id": event.get("id", ""),
                    "event_type": event.get("event_type", ""),
                    "time_order": event.get("time_order", ""),
                }
                text_spans.append(span_info)
    
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"  Warning: Error reading {v3_path}: {e}")
    
    return text_spans


def main():
    """主函数：读取 annotation_status.csv，提取所有 text_span，生成新 CSV"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 读取 annotation_status.csv
    annotation_csv = script_dir / "annotation_status.csv"
    
    if not annotation_csv.exists():
        print(f"Error: {annotation_csv} does not exist!")
        print("Please run check_annotations.py first to generate annotation_status.csv")
        return
    
    all_text_spans = []
    
    print(f"Reading annotation status from: {annotation_csv}")
    
    # 读取 annotation_status.csv
    with open(annotation_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            story_name = row["story_name"]
            text_file = row["text_file"]
            v3_path_str = row["v3_path"]
            has_narrative = row["has_narrative"] == "True"
            
            # 只处理有 v3 标注且有 narrative 的故事
            if not v3_path_str or not has_narrative:
                continue
            
            # 构建 v3 文件的完整路径
            v3_path = project_root / v3_path_str
            
            print(f"Processing: {story_name}")
            
            # 提取 text_span
            text_spans = extract_text_spans_from_v3(v3_path)
            
            # 为每个 text_span 创建一行记录
            for span in text_spans:
                record = {
                    "story_name": story_name,
                    "text_file": text_file,
                    "v3_path": v3_path_str,
                    "event_id": span["event_id"],
                    "event_type": span["event_type"],
                    "time_order": span["time_order"],
                    "start": span["start"],
                    "end": span["end"],
                    "text": span["text"],
                }
                all_text_spans.append(record)
            
            print(f"  Extracted {len(text_spans)} text spans")
    
    # 写入新的 CSV 文件
    output_file = script_dir / "text_spans.csv"
    
    fieldnames = [
        "story_name",
        "text_file",
        "v3_path",
        "event_id",
        "event_type",
        "time_order",
        "start",
        "end",
        "text",
    ]
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_text_spans)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total text spans: {len(all_text_spans)}")
    print(f"  Results saved to: {output_file.relative_to(project_root)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
