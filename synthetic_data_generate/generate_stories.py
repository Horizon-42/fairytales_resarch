#!/usr/bin/env python3
"""
根据清洗后的 JSON v3 标注数据生成故事文本。

使用 Gemini 1.5 Flash 和 GPT-3（或其他模型），调高温度，
为每个 JSON 生成 10 篇故事。
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加 repo_root 到路径，以便导入 llm_model
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig, chat as gemini_chat
from llm_model.llm_router import LLMConfig, chat as llm_chat


# 加载环境变量
load_repo_dotenv()


def build_story_generation_prompt(json_data: Dict[str, Any]) -> str:
    """构建用于生成故事的 prompt。"""
    
    metadata = json_data.get("metadata", {})
    title = metadata.get("title", "")
    culture = metadata.get("culture", "")
    
    characters = json_data.get("characters", [])
    character_list = "\n".join([
        f"- {char.get('name', '')} ({char.get('archetype', '')})" + 
        (f" - also known as: {char.get('alias', '')}" if char.get('alias') else "")
        for char in characters
    ])
    
    narrative_events = json_data.get("narrative_events", [])
    # 按 time_order 排序
    sorted_events = sorted(narrative_events, key=lambda x: x.get("time_order", 0))
    
    event_summary = []
    for event in sorted_events:
        event_info = {
            "order": event.get("time_order", 0),
            "type": event.get("event_type", ""),
            "description": event.get("description", ""),
            "agents": ", ".join(event.get("agents", [])) if event.get("agents") else "N/A",
            "targets": ", ".join(event.get("targets", [])) if event.get("targets") else "N/A",
            "instrument": event.get("instrument", "") if event.get("instrument") else "",
        }
        event_line = f"Event {event_info['order']}: [{event_info['type']}] {event_info['description']}"
        event_line += f" | Agents: {event_info['agents']}" if event_info['agents'] != "N/A" else ""
        event_line += f" | Targets: {event_info['targets']}" if event_info['targets'] != "N/A" else ""
        event_line += f" | Instrument: {event_info['instrument']}" if event_info['instrument'] else ""
        event_summary.append(event_line)
    
    events_text = "\n".join(event_summary)
    
    # 确定语言：优先根据 culture，其次根据 source_info.language
    source_info = json_data.get("source_info", {})
    language_from_source = source_info.get("language", "en")

    # 根据 culture 映射到对应语言
    culture_to_language = {
        "Chinese": "zh",
        "Japanese": "ja",
        "Indian": "en",  # 印度故事通常用英文（数据集中的情况）
        "Persian": "fa",
        "English": "en",
    }

    # 优先使用 culture 对应的语言，如果没有则使用 source_info 中的语言
    language_code = culture_to_language.get(culture, language_from_source)

    language_map = {
        "zh": "中文",
        "en": "English",
        "ja": "Japanese",
        "fa": "Persian",
    }
    story_language = language_map.get(language_code, "English")
    
    prompt = f"""You are a master storyteller with deep expertise in {culture} folktales, myths, and traditional narratives. Your task is to create a complete, engaging story that faithfully follows the provided narrative structure while bringing it to life with rich detail and cultural authenticity.

**CRITICAL LANGUAGE REQUIREMENT:**
You MUST write the entire story in {story_language}. This is not optional. Every word, sentence, and paragraph must be in {story_language}, not English or any other language.

**STORY INFORMATION:**
- Title: {title}
- Cultural Origin: {culture}
- Required Language: {story_language}

**CHARACTERS:**
{character_list}

Each character has an archetypal role. Develop them in a way that is consistent with their archetype while also giving them depth and personality. Use character names consistently throughout the story, including any aliases provided.

**NARRATIVE STRUCTURE:**

The story must follow these {len(sorted_events)} events in the exact order specified. Each event must correspond to ONE paragraph in your output, wrapped in curly braces {{}}:

{events_text}

Each event represents a key plot point that must be included in your narrative. The event type (e.g., VILLAINY, DEPARTURE, VICTORY) indicates the narrative function, which should inform how you present and develop that moment in the story. You must generate exactly {len(sorted_events)} paragraphs, each wrapped in {{}}, corresponding to these {len(sorted_events)} events in order.

**STORY GENERATION REQUIREMENTS:**

1. **Narrative Flow**: The story must progress smoothly through all events in chronological order. Create natural transitions between events that feel organic and engaging.

2. **Character Development**: Include all listed characters and develop their roles naturally. Characters should feel authentic to their archetypal roles while also having individual personalities.

3. **Cultural Authenticity**: 
   - Use appropriate cultural details, settings, and traditions for {culture} folktales
   - Incorporate relevant cultural elements, motifs, and storytelling conventions
   - Maintain the traditional narrative style typical of {culture} stories

4. **Writing Style**:
   - Use vivid, descriptive language that brings scenes to life
   - Include sensory details (sights, sounds, emotions) where appropriate
   - Balance dialogue and narration effectively
   - Create tension and emotional resonance where the events suggest it

5. **Completeness**: The story should be self-contained and readable as a standalone narrative. Do not include meta-commentary, explanations, or analysis—only the story itself.

6. **Length**: Generate a substantial, well-developed story that fully explores each event. Aim for a length appropriate to the complexity of the narrative structure provided.

**OUTPUT FORMAT - CRITICAL:**

You must format the story as follows:
- Each narrative event corresponds to ONE story paragraph
- Each paragraph MUST be wrapped in curly braces {{}}
- The paragraphs must appear in the exact order of the events (Event 1, Event 2, ..., Event {len(sorted_events)})
- Each paragraph should be a self-contained narrative segment that develops the corresponding event

Format example:
{{First paragraph corresponding to Event 1}}
{{Second paragraph corresponding to Event 2}}
{{Third paragraph corresponding to Event 3}}
...

Requirements:
- Each {{}} block should contain the story text for ONE narrative event only
- Do NOT include any text outside the curly braces
- Do NOT include the event numbers or labels inside the braces
- Do NOT include any introduction, explanation, meta-commentary, notes, or analysis
- Do NOT include the title
- The story should flow naturally from one {{}} block to the next

**LANGUAGE REMINDER:**
CRITICAL: You must write the entire story in {story_language}, not in English. The story must be completely in {story_language} from the first word to the last word. Do not use English at all.

**BEGIN THE STORY NOW (with proper formatting):**

"""
    
    return prompt


def generate_story_with_gemini(json_data: Dict[str, Any], temperature: float = 1.0) -> Optional[str]:
    """使用 Gemini 1.5 Flash 生成故事。"""
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            print("Warning: GEMINI_API_KEY not set", file=sys.stderr)
            return None
        
        # 使用 gemini-1.5-flash (用户选择，因为没有 gemini-3 flash token)
        config = GeminiConfig(
            api_key=api_key,
            model="gemini-2.5-flash",  # 使用 Gemini 1.5 Flash
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=8192,
        )
        
        prompt = build_story_generation_prompt(json_data)
        
        messages = [{"role": "user", "content": prompt}]
        
        response = gemini_chat(
            config=config,
            messages=messages,
            response_format_json=False,  # 不需要 JSON 格式，直接生成文本
            timeout_s=300.0,
        )
        
        return response.strip()
    except Exception as e:
        print(f"Error generating story with Gemini: {e}", file=sys.stderr)
        return None


def generate_story_with_gpt3(json_data: Dict[str, Any], temperature: float = 1.0) -> Optional[str]:
    """
    使用 GPT-3 或其他支持的模型生成故事。
    
    注意：如果需要使用 OpenAI GPT-3，需要添加 openai 客户端代码。
    或者使用 Ollama 等本地模型。
    """
    # TODO: 实现 GPT-3 或其他模型的调用
    # 这里先返回 None，等待用户确认使用哪个模型
    print("Warning: GPT-3 generation not yet implemented", file=sys.stderr)
    return None


def generate_stories_for_json(
    json_path: Path,
    output_dir: Path,
    num_stories: int = 10,
    model: str = "gemini",
    temperature: float = 1.0,
):
    """为单个 JSON 文件生成多个故事。"""
    
    # 读取 JSON
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    story_name = json_data.get("metadata", {}).get("id", json_path.stem)
    
    print(f"Generating {num_stories} stories for: {story_name} (model: {model}, temp: {temperature})")
    
    # 生成故事
    for i in range(num_stories):
        print(f"  Generating story {i+1}/{num_stories}...", end=" ", flush=True)
        
        if model.lower() in ["gemini", "gemini3", "flash"]:
            story_text = generate_story_with_gemini(json_data, temperature)
        elif model.lower() in ["gpt3", "gpt-3", "openai"]:
            story_text = generate_story_with_gpt3(json_data, temperature)
        else:
            print(f"Unknown model: {model}", file=sys.stderr)
            story_text = None
        
        if story_text:
            # 保存故事
            output_path = output_dir / f"{story_name}_gen_{i+1:02d}.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(story_text)
            
            print("✓")
        else:
            print("✗ Failed")
        
        # 避免 API 速率限制
        time.sleep(1)
    
    print(f"Completed: {story_name}")


def main():
    """主函数：处理 groundtruth 目录中的所有 JSON 文件。"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate stories from cleaned JSON v3 annotations"
    )
    parser.add_argument(
        "--groundtruth-dir",
        type=str,
        default=str(repo_root / "synthetic_datasets" / "groundtruth"),
        help="Directory containing cleaned JSON v3 files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(repo_root / "synthetic_datasets" / "generated_stories"),
        help="Output directory for generated stories",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini",
        choices=["gemini", "gpt3"],
        help="Model to use for generation",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Temperature for generation (higher = more creative)",
    )
    parser.add_argument(
        "--num-stories",
        type=int,
        default=10,
        help="Number of stories to generate per JSON",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Process only a specific JSON file (optional)",
    )
    
    args = parser.parse_args()
    
    groundtruth_dir = Path(args.groundtruth_dir)
    output_dir = Path(args.output_dir)
    
    if not groundtruth_dir.exists():
        print(f"Error: {groundtruth_dir} not found", file=sys.stderr)
        sys.exit(1)
    
    # 收集所有 JSON 文件
    json_files = []
    if args.file:
        json_path = Path(args.file)
        if json_path.exists():
            json_files.append(json_path)
        else:
            print(f"Error: {json_path} not found", file=sys.stderr)
            sys.exit(1)
    else:
        json_files = list(groundtruth_dir.rglob("*.json"))

    # sort jsonfiles
    json_files.sort()
    
    print(f"Found {len(json_files)} JSON files to process")
    print(f"Model: {args.model}, Temperature: {args.temperature}, Stories per file: {args.num_stories}")
    print(f"Output directory: {output_dir}\n")
    
    # 处理每个 JSON 文件
    for json_path in json_files:
        # 计算相对路径以保持目录结构
        rel_path = json_path.relative_to(groundtruth_dir)
        story_output_dir = output_dir / rel_path.parent / json_path.stem
        story_output_dir = story_output_dir / args.model
        
        try:
            generate_stories_for_json(
                json_path=json_path,
                output_dir=story_output_dir,
                num_stories=args.num_stories,
                model=args.model,
                temperature=args.temperature,
            )
        except Exception as e:
            print(f"Error processing {json_path}: {e}", file=sys.stderr)
            continue
    
    print(f"\nAll stories generated in: {output_dir}")


if __name__ == "__main__":
    main()
