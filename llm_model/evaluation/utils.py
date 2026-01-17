"""Utility functions for data loading and normalization."""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


def load_ground_truth(json_path: str) -> Dict[str, Any]:
    """
    从 JSON v3 文件加载 Ground Truth 数据
    
    Args:
        json_path: JSON 文件路径
        
    Returns:
        JSON v3 格式的数据字典
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_prediction(json_path: str) -> Dict[str, Any]:
    """
    从 JSON v3 文件加载预测数据
    
    Args:
        json_path: JSON 文件路径
        
    Returns:
        JSON v3 格式的数据字典
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_character_name(name: str, aliases: List[str]) -> str:
    """
    标准化角色名称（处理别名）
    
    Args:
        name: 角色名称
        aliases: 别名列表（字符串，可能包含分号分隔的多个别名）
        
    Returns:
        标准化后的名称（去除空白，转为小写等）
    """
    if not name:
        return ""
    
    # 去除首尾空白
    normalized = name.strip()
    
    # 处理别名：将分号分隔的别名合并
    alias_list = []
    if aliases:
        if isinstance(aliases, str):
            alias_list = [a.strip() for a in aliases.split(';') if a.strip()]
        elif isinstance(aliases, list):
            alias_list = [str(a).strip() for a in aliases if str(a).strip()]
    
    # 返回主名称和别名的集合（用于后续匹配）
    # 注意：这里返回的是标准化的主名称，实际匹配时需要考虑别名
    return normalized


def load_relationship_taxonomy(csv_path: Optional[str] = None) -> Dict[str, List[str]]:
    """
    加载关系分类标准
    
    Args:
        csv_path: CSV 文件路径，如果为 None 则使用默认路径
        
    Returns:
        字典：{level1: [level2, ...], ...}
    """
    if csv_path is None:
        # 使用相对于项目根目录的路径
        project_root = Path(__file__).parent.parent.parent.parent
        csv_path = project_root / "docs" / "Character_Resources" / "relationship.csv"
    
    taxonomy = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 跳过表头（第一行）
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # CSV 格式：level1,level2,definition,context
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                level1 = parts[0]
                level2 = parts[1] if parts[1] else None
                
                # 跳过空行或只有逗号的行
                if not level1 or not level2:
                    continue
                
                if level1 not in taxonomy:
                    taxonomy[level1] = []
                taxonomy[level1].append(level2)
    except FileNotFoundError:
        # 如果文件不存在，返回空字典（测试时可能用到）
        pass
    
    return taxonomy


def load_sentiment_taxonomy(csv_path: Optional[str] = None) -> List[str]:
    """
    加载情感标签标准
    
    Args:
        csv_path: CSV 文件路径，如果为 None 则使用默认路径
        
    Returns:
        情感标签列表
    """
    if csv_path is None:
        project_root = Path(__file__).parent.parent.parent.parent
        csv_path = project_root / "docs" / "Character_Resources" / "sentiment.csv"
    
    sentiments = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 跳过表头（第一行）
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # CSV 格式：tag,中文名称,极性,行为,level
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 1 and parts[0]:
                sentiments.append(parts[0])
    except FileNotFoundError:
        pass
    
    return sentiments


def load_action_taxonomy(md_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载动作分类标准（从 Markdown 文件）
    
    Args:
        md_path: Markdown 文件路径，如果为 None 则使用默认路径
        
    Returns:
        包含动作分类的字典结构
    """
    if md_path is None:
        project_root = Path(__file__).parent.parent.parent.parent
        md_path = project_root / "docs" / "Universal Narrative Action Taxonomy" / "Universal_Narrative_Action_Taxonomy.md"
    
    # 简化实现：只加载类别和类型
    # 实际使用时可以根据需要扩展
    taxonomy = {
        "categories": [],
        "types": {},
        "statuses": ["attempt", "success", "failure", "interrupted", "backfire", "partial"],
        "functions": ["trigger", "climax", "resolution", "character_arc", "setup", "exposition"]
    }
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的解析：提取 category 和 type
        # 这里可以根据实际 Markdown 格式进行更精确的解析
        # 暂时返回基本结构
        categories = [
            "Physical & Conflict",
            "Social & Communicative",
            "Transaction & Exchange",
            "Mental & Cognitive",
            "Existential & Supernatural"
        ]
        taxonomy["categories"] = categories
        
    except FileNotFoundError:
        pass
    
    return taxonomy


def text_to_sentence_indices(text: str) -> List[Tuple[int, int]]:
    """
    将文本转换为句子索引列表
    
    Args:
        text: 输入文本
        
    Returns:
        List of (start_char, end_char) for each sentence
        每个元组表示一个句子在文本中的字符位置范围（包括句子末尾的标点）
    """
    if not text:
        return []
    
    # 使用正则表达式找到所有句子分隔符的位置
    # 匹配中文句号、感叹号、问号和英文句号、感叹号、问号
    sentence_delimiters = r'[。！？.!\?]+'
    
    # 找到所有分隔符的位置
    matches = list(re.finditer(sentence_delimiters, text))
    
    if not matches:
        # 没有分隔符，整个文本作为一个句子
        return [(0, len(text))]
    
    indices = []
    current_pos = 0
    
    for match in matches:
        # 句子的结束位置（包括标点符号）
        end_pos = match.end()
        
        # 只有非空的句子才添加
        if end_pos > current_pos:
            indices.append((current_pos, end_pos))
            current_pos = end_pos
    
    # 添加最后一个句子（如果文本在最后一个分隔符之后还有内容）
    if current_pos < len(text):
        indices.append((current_pos, len(text)))
    
    # 如果没有找到任何句子，整个文本作为一个句子
    if not indices:
        indices.append((0, len(text)))
    
    return indices


def char_position_to_sentence_index(
    char_pos: int,
    sentence_indices: List[Tuple[int, int]]
) -> int:
    """
    将字符位置转换为句子索引
    
    Args:
        char_pos: 字符在文本中的位置（0-based）
        sentence_indices: 句子索引列表，每个元素为 (start_char, end_char)
        
    Returns:
        句子索引（0-based），如果找不到则返回 -1
    """
    for idx, (start, end) in enumerate(sentence_indices):
        if start <= char_pos < end:
            return idx
    
    # 如果位置在所有句子之后，返回最后一个句子索引
    if sentence_indices and char_pos >= sentence_indices[-1][1]:
        return len(sentence_indices) - 1
    
    # 如果位置在所有句子之前，返回 0
    return 0 if sentence_indices else -1