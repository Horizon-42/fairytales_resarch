#!/usr/bin/env python3
"""
将包含多个故事的 Markdown 文件分割成符合 generated_stories 格式的多个故事文件。

用法:
    python3 scripts/split_md_stories.py \
        --input synthetic_data_generate/prompts/ChineseTales/CH_002_牛郎织女/CH_002_牛郎织女.md \
        --output-dir synthetic_datasets/generated_stories/ChineseTales/CH_002_牛郎织女_v3/gemini \
        --story-name CH_002_牛郎织女
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_next_story_number(output_dir: Path, story_name: str) -> int:
    """查找下一个可用的故事编号。
    
    Args:
        output_dir: 输出目录
        story_name: 故事名称（如 CH_002_牛郎织女）
    
    Returns:
        下一个可用的编号（从1开始）
    """
    if not output_dir.exists():
        return 1
    
    pattern = re.compile(rf"^{re.escape(story_name)}_gen_(\d+)\.txt$")
    max_num = 0
    
    for file in output_dir.iterdir():
        if file.is_file():
            match = pattern.match(file.name)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)
    
    return max_num + 1


def extract_stories_from_md(content: str) -> List[str]:
    """从 Markdown 内容中提取各个故事。
    
    每个故事以 "**故事X：" 开头，以 "---" 或文件结尾结束。
    跳过标题行，只保留用 {} 包裹的段落内容。
    
    Args:
        content: Markdown 文件内容
    
    Returns:
        故事列表，每个故事是纯文本（每行一个 {} 段落）
    """
    lines = content.splitlines()
    stories = []
    current_story = []
    in_story = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测故事开始：**故事X：或 **故事X：
        if re.match(r'^\*\*故事[一二三四五六七八九十\d]+[：:]', line):
            # 如果之前有故事，保存它
            if current_story:
                stories.append('\n'.join(current_story))
                current_story = []
            in_story = True
            # 跳过标题行
            i += 1
            continue
        
        # 检测分隔符 "---"
        if line.strip() == '---':
            # 如果之前有故事，保存它
            if current_story:
                stories.append('\n'.join(current_story))
                current_story = []
            in_story = False
            i += 1
            continue
        
        # 如果在故事中，收集用 {} 包裹的行
        if in_story:
            # 检查是否是 {} 包裹的段落
            if line.strip().startswith('{') and line.strip().endswith('}'):
                current_story.append(line.strip())
            elif line.strip() and not line.strip().startswith('#'):
                # 如果不是空行也不是标题，可能是格式问题，尝试提取 {} 内容
                # 使用正则表达式提取所有 {} 包裹的内容
                matches = re.findall(r'\{[^}]+\}', line)
                for match in matches:
                    current_story.append(match)
        
        i += 1
    
    # 保存最后一个故事
    if current_story:
        stories.append('\n'.join(current_story))
    
    return stories


def extract_stories_from_md_v2(content: str) -> List[str]:
    """从 Markdown 内容中提取各个故事（改进版）。
    
    更准确地识别故事边界和内容。
    """
    lines = content.splitlines()
    stories = []
    current_story = []
    in_story = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测故事开始：**故事X：或 # **故事X：或 **故事X：
        story_start_pattern = re.compile(r'^(#\s*)?\*\*故事[一二三四五六七八九十\d]+[：:].*\*\*$')
        if story_start_pattern.match(line):
            # 如果之前有故事，保存它
            if current_story:
                stories.append('\n'.join(current_story))
                current_story = []
            in_story = True
            # 跳过标题行
            i += 1
            continue
        
        # 检测分隔符 "---"（可能前后有空格）
        if line == '---' or line.startswith('---'):
            # 如果之前有故事，保存它
            if current_story:
                stories.append('\n'.join(current_story))
                current_story = []
            in_story = False
            i += 1
            continue
        
        # 如果在故事中，收集用 {} 包裹的行
        if in_story:
            # 检查是否是 {} 包裹的段落（可能前后有空格）
            stripped = line.strip()
            if stripped.startswith('{') and stripped.endswith('}'):
                current_story.append(stripped)
            elif stripped:
                # 如果不是空行，尝试提取 {} 内容
                # 使用正则表达式提取所有 {} 包裹的内容（包括嵌套的 {}）
                # 但要注意，我们的格式应该是简单的 {内容}
                matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', line)
                if matches:
                    for match in matches:
                        current_story.append(match)
        
        i += 1
    
    # 保存最后一个故事
    if current_story:
        stories.append('\n'.join(current_story))
    
    return stories


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Split a Markdown file containing multiple stories into separate story files"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input Markdown file path",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for story files",
    )
    parser.add_argument(
        "--story-name",
        type=str,
        required=True,
        help="Story name prefix (e.g., CH_002_牛郎织女)",
    )
    parser.add_argument(
        "--start-number",
        type=int,
        help="Starting story number (auto-detected if not specified)",
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    story_name = args.story_name
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # 读取输入文件
    print(f"Reading input file: {input_path}")
    content = input_path.read_text(encoding='utf-8')
    
    # 提取故事
    print("Extracting stories from Markdown...")
    stories = extract_stories_from_md_v2(content)
    
    if not stories:
        print("Error: No stories found in the Markdown file", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(stories)} stories")
    
    # 确定起始编号
    if args.start_number:
        start_num = args.start_number
    else:
        start_num = find_next_story_number(output_dir, story_name)
    
    print(f"Starting from story number: {start_num}")
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存每个故事
    saved_count = 0
    for i, story_content in enumerate(stories):
        story_num = start_num + i
        filename = f"{story_name}_gen_{story_num:02d}.txt"
        output_path = output_dir / filename
        
        # 确保每行都是 {} 包裹的段落
        lines = story_content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                # 确保是 {} 格式
                if not (line.startswith('{') and line.endswith('}')):
                    # 尝试修复：如果内容在 {} 中但格式不对
                    if '{' in line and '}' in line:
                        # 提取 {} 中的内容
                        match = re.search(r'\{([^}]+)\}', line)
                        if match:
                            line = '{' + match.group(1) + '}'
                        else:
                            # 如果无法修复，跳过
                            continue
                    else:
                        continue
                cleaned_lines.append(line)
        
        if not cleaned_lines:
            print(f"  Warning: Story {i+1} has no valid content, skipping", file=sys.stderr)
            continue
        
        # 写入文件
        output_path.write_text('\n'.join(cleaned_lines) + '\n', encoding='utf-8')
        print(f"  Saved: {filename} ({len(cleaned_lines)} paragraphs)")
        saved_count += 1
    
    print(f"\nCompleted: {saved_count} stories saved to {output_dir}")


if __name__ == "__main__":
    main()
