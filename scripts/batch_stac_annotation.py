#!/usr/bin/env python3
"""批量 STAC 标注脚本

对指定文件夹中的所有故事文件进行 STAC (Situation, Task, Action, Consequence) 标注。

使用方法:
    python scripts/batch_stac_annotation.py \
        --input-dir datasets/ChineseTales/texts \
        --output-dir datasets/ChineseTales/stac_annotations \
        --model qwen3:8b

    # 使用邻近句子作为辅助上下文
    python scripts/batch_stac_annotation.py \
        --input-dir datasets/ChineseTales/texts \
        --output-dir datasets/ChineseTales/stac_annotations \
        --use-neighboring-sentences

    # 不使用故事上下文（独立分析每个句子）
    python scripts/batch_stac_annotation.py \
        --input-dir datasets/ChineseTales/texts \
        --output-dir datasets/ChineseTales/stac_annotations \
        --no-context
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_model.env import load_repo_dotenv
from llm_model.gemini_client import GeminiConfig
from llm_model.llm_router import LLMConfig
from llm_model.ollama_client import OllamaConfig
from llm_model.stac_analyzer import STACAnalyzerConfig, analyze_stac
from pre_data_process.sentence_splitter import split_sentences_advanced


# 支持的文本文件扩展名
SUPPORTED_EXTENSIONS = {".txt"}


def find_story_files(input_dir: Path) -> List[Path]:
    """查找输入目录中的所有故事文件。"""
    story_files = set()  # 使用集合避免重复
    for ext in SUPPORTED_EXTENSIONS:
        # 递归查找所有子目录中的文件（包括当前目录）
        story_files.update(input_dir.glob(f"**/*{ext}"))
    # 过滤掉目录（只保留文件）
    story_files = {f for f in story_files if f.is_file()}
    return sorted(story_files)


def process_story_file(
    story_file: Path,
    output_file: Path,
    *,
    config: STACAnalyzerConfig,
    use_context: bool = True,
    use_neighboring_sentences: bool = False,
) -> dict:
    """处理单个故事文件，进行 STAC 标注。
    
    Returns:
        包含处理结果的字典，包括成功/失败状态和统计信息
    """
    try:
        # 读取故事内容
        story_content = story_file.read_text(encoding="utf-8")
        if not story_content.strip():
            return {
                "status": "skipped",
                "reason": "Empty file",
                "file": str(story_file),
            }
        
        # 分割句子
        sentences = split_sentences_advanced(story_content)
        if not sentences:
            return {
                "status": "skipped",
                "reason": "No sentences found",
                "file": str(story_file),
            }
        
        print(f"  Processing {len(sentences)} sentences...", file=sys.stderr)
        
        # 分析每个句子
        results = []
        story_context = story_content if use_context else None
        
        for idx, sentence in enumerate(sentences, start=1):
            try:
                # 获取邻近句子（如果启用）
                previous_sentence = None
                next_sentence = None
                if use_neighboring_sentences:
                    sent_idx = idx - 1
                    if sent_idx > 0:
                        previous_sentence = sentences[sent_idx - 1]
                    if sent_idx < len(sentences) - 1:
                        next_sentence = sentences[sent_idx + 1]
                
                # 执行 STAC 分析
                analysis = analyze_stac(
                    sentence=sentence,
                    story_context=story_context,
                    use_context=use_context,
                    previous_sentence=previous_sentence,
                    next_sentence=next_sentence,
                    use_neighboring_sentences=use_neighboring_sentences,
                    config=config,
                )
                
                results.append({
                    "sentence_index": idx,
                    "sentence": sentence,
                    "analysis": analysis,
                })
                
                # 显示进度（每10个句子显示一次）
                if idx % 10 == 0:
                    print(f"    Analyzed {idx}/{len(sentences)} sentences...", file=sys.stderr)
                    
            except Exception as e:
                print(f"    Warning: Failed to analyze sentence {idx}: {e}", file=sys.stderr)
                results.append({
                    "sentence_index": idx,
                    "sentence": sentence,
                    "analysis": None,
                    "error": str(e),
                })
        
        # 构建输出数据
        output_data = {
            "source_file": str(story_file),
            "use_context": use_context,
            "use_neighboring_sentences": use_neighboring_sentences,
            "total_sentences": len(sentences),
            "analyzed_sentences": len(results),
            "sentences": results,
        }
        
        # 保存结果
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return {
            "status": "success",
            "file": str(story_file),
            "output_file": str(output_file),
            "total_sentences": len(sentences),
            "analyzed_sentences": len(results),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "file": str(story_file),
            "error": str(e),
        }


def main() -> int:
    load_repo_dotenv()
    
    parser = argparse.ArgumentParser(
        description="批量对故事文件进行 STAC 标注",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="输入文件夹路径（包含故事文件的文件夹）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="输出文件夹路径（标注结果将保存到这里）",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "ollama"),
        help="LLM 提供商: ollama (本地) 或 gemini (云端)",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="启用思考模式（Gemini 使用 GEMINI_MODEL_THINKING）",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        help="模型名称（Ollama 模型或 Gemini 模型，取决于 --provider）",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama 基础 URL",
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="不使用故事上下文（独立分析每个句子）",
    )
    parser.add_argument(
        "--use-neighboring-sentences",
        action="store_true",
        help="使用邻近句子作为辅助上下文",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=list(SUPPORTED_EXTENSIONS),
        help=f"支持的文件扩展名（默认: {', '.join(SUPPORTED_EXTENSIONS)}）",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="跳过已存在的输出文件",
    )
    
    args = parser.parse_args()
    
    # 验证输入目录
    input_dir = args.input_dir.resolve()
    if not input_dir.exists():
        print(f"错误: 输入目录不存在: {input_dir}", file=sys.stderr)
        return 1
    if not input_dir.is_dir():
        print(f"错误: 输入路径不是目录: {input_dir}", file=sys.stderr)
        return 1
    
    # 创建输出目录
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找所有故事文件
    story_files = find_story_files(input_dir)
    if not story_files:
        print(f"错误: 在 {input_dir} 中未找到任何故事文件", file=sys.stderr)
        print(f"支持的文件扩展名: {', '.join(SUPPORTED_EXTENSIONS)}", file=sys.stderr)
        return 1
    
    print(f"找到 {len(story_files)} 个故事文件", file=sys.stderr)
    
    # 设置 LLM 配置
    provider = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    ollama_model = args.model if provider != "gemini" else os.getenv("OLLAMA_MODEL", "qwen3:8b")
    gemini_model = args.model if provider == "gemini" else os.getenv("GEMINI_MODEL", "")
    
    llm = LLMConfig(
        provider=provider,
        thinking=bool(args.thinking),
        ollama=OllamaConfig(base_url=args.base_url, model=ollama_model),
        gemini=GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=gemini_model,
            model_thinking=os.getenv("GEMINI_MODEL_THINKING", ""),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.9")),
            max_output_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")),
        ),
    )
    
    config = STACAnalyzerConfig(llm=llm)
    use_context = not args.no_context
    
    # 处理每个文件
    results_summary = {
        "success": [],
        "skipped": [],
        "error": [],
    }
    
    for idx, story_file in enumerate(story_files, start=1):
        print(f"\n[{idx}/{len(story_files)}] 处理: {story_file.name}", file=sys.stderr)
        
        # 确定输出文件路径（保持相对路径结构）
        try:
            relative_path = story_file.relative_to(input_dir)
            output_file = output_dir / f"{relative_path.stem}_stac.json"
        except ValueError:
            # 如果无法计算相对路径，直接使用文件名
            output_file = output_dir / f"{story_file.stem}_stac.json"
        
        # 检查是否跳过已存在的文件
        if args.skip_existing and output_file.exists():
            print(f"  跳过已存在的文件: {output_file.name}", file=sys.stderr)
            results_summary["skipped"].append({
                "file": str(story_file),
                "reason": "Output file already exists",
            })
            continue
        
        # 处理文件
        result = process_story_file(
            story_file=story_file,
            output_file=output_file,
            config=config,
            use_context=use_context,
            use_neighboring_sentences=args.use_neighboring_sentences,
        )
        
        # 记录结果
        status = result.get("status", "unknown")
        if status == "success":
            results_summary["success"].append(result)
            print(f"  ✓ 完成: {output_file.name}", file=sys.stderr)
        elif status == "skipped":
            results_summary["skipped"].append(result)
            print(f"  ⊘ 跳过: {result.get('reason', 'Unknown reason')}", file=sys.stderr)
        else:
            results_summary["error"].append(result)
            print(f"  ✗ 错误: {result.get('error', 'Unknown error')}", file=sys.stderr)
    
    # 打印总结
    print("\n" + "=" * 60, file=sys.stderr)
    print("处理完成！", file=sys.stderr)
    print(f"成功: {len(results_summary['success'])}", file=sys.stderr)
    print(f"跳过: {len(results_summary['skipped'])}", file=sys.stderr)
    print(f"错误: {len(results_summary['error'])}", file=sys.stderr)
    
    if results_summary["error"]:
        print("\n错误文件列表:", file=sys.stderr)
        for err in results_summary["error"]:
            print(f"  - {err.get('file', 'Unknown')}: {err.get('error', 'Unknown error')}", file=sys.stderr)
    
    # 保存处理摘要
    summary_file = output_dir / "_batch_summary.json"
    summary_data = {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "use_context": use_context,
        "use_neighboring_sentences": args.use_neighboring_sentences,
        "provider": provider,
        "model": args.model,
        "total_files": len(story_files),
        "results": results_summary,
    }
    summary_file.write_text(
        json.dumps(summary_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n处理摘要已保存到: {summary_file}", file=sys.stderr)
    
    return 0 if not results_summary["error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
