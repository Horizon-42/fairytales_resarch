#!/usr/bin/env python3
"""
句子切分脚本 - 支持多语言标点符号
支持中文、日语、英文、波斯文的句子切分

使用方法:
    python sentence_splitter.py input.txt output.txt
    python sentence_splitter.py input.txt  # 输出到 input_sentences.txt
"""

import re
import sys
from pathlib import Path
from typing import List


# 定义多语言句子结束标点符号
# 中文、日语、英文、波斯文
SENTENCE_END_MARKS = r'[。！？.!\?؟]'

# 可能出现在句子结束标点后的闭合标点（引号、括号等）
# 包括：右引号、右单引号、英文引号、右括号等
# 使用字符列表避免引号转义问题
closing_chars_list = ['」', '』', '"', "'", '"', "'", ')', '）']
CLOSING_PUNCTUATION = '[' + re.escape(''.join(closing_chars_list)) + ']'

# 构建句子结束模式：句子内容 + 结束标点 + 可能的闭合标点 + 空白
SENTENCE_PATTERN = re.compile(
    rf'([^{SENTENCE_END_MARKS[1:-1]}]+{SENTENCE_END_MARKS}{CLOSING_PUNCTUATION}*)\s*',
    re.UNICODE
)


def split_sentences(text: str) -> List[str]:
    """
    将文本按句子切分，正确处理引号内的对话
    
    Args:
        text: 输入文本
        
    Returns:
        句子列表
    """
    if not text or not text.strip():
        return []
    
    # 标准化空白字符：多个空格/制表符合并为一个空格
    text = re.sub(r'[ \t]+', ' ', text)
    # 保留段落分隔（两个或更多换行）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    sentences = []
    
    # 按段落处理（空行分隔段落）
    paragraphs = re.split(r'\n\s*\n', text)
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 将段落中的单个换行替换为空格，保持文本连续性
        para = re.sub(r'\n+', ' ', para)
        para = para.strip()
        
        if not para:
            continue
        
        # 使用智能切分，考虑引号状态
        para_sentences = split_sentences_with_quotes(para)
        sentences.extend(para_sentences)
    
    # 清理句子：移除空句子和多余的空白
    cleaned_sentences = []
    for sent in sentences:
        sent = sent.strip()
        # 移除全角空格和多余的空白
        sent = re.sub(r'^[\s\u3000]+|[\s\u3000]+$', '', sent)
        if sent and len(sent) > 0:
            cleaned_sentences.append(sent)
    
    return cleaned_sentences


def split_sentences_with_quotes(text: str) -> List[str]:
    """
    智能句子切分，正确处理引号内的对话
    
    引号类型：
    - 中文双引号：「」『』
    - 中文单引号：''
    - 英文双引号：""
    - 英文单引号：''
    """
    if not text:
        return []
    
    # 定义引号对（开引号 -> 闭引号）
    quote_pairs = {
        '「': '」',  # 中文双引号
        '『': '』',  # 中文双引号（另一种）
        '"': '"',   # 英文双引号（弯引号）
        "'": "'",   # 英文单引号（弯引号）
        '"': '"',   # 直双引号
        "'": "'",   # 直单引号
    }
    
    sentences = []
    i = 0
    current_sentence = []
    quote_stack = []  # 跟踪当前打开的引号类型（闭引号列表）
    sentence_end_chars = ['。', '！', '？', '.', '!', '?', '؟']
    closing_chars = ['」', '』', '"', "'", '"', "'", ')', '）']
    
    while i < len(text):
        char = text[i]
        
        # 检查是否是引号开始
        if char in quote_pairs:
            quote_stack.append(quote_pairs[char])
            current_sentence.append(char)
            i += 1
            continue
        
        # 检查是否是引号结束
        if quote_stack and char == quote_stack[-1]:
            quote_stack.pop()
            current_sentence.append(char)
            
            # 引号闭合后，检查引号内的最后一个字符是否是句子结束标点
            # 如果是，则应该切分（引号内的内容是一个完整句子）
            # 查找引号内的最后一个句子结束标点
            quote_content_ends_with_sentence = False
            # 从当前位置向前查找，找到对应的开引号
            # 简化：检查当前句子中，在闭引号之前的最后一个字符是否是句子结束标点
            if len(current_sentence) >= 2:
                # 闭引号前一个字符
                prev_char = current_sentence[-2] if len(current_sentence) >= 2 else ''
                if prev_char in sentence_end_chars:
                    quote_content_ends_with_sentence = True
            
            # 如果引号内以句子结束标点结尾，检查后面是否有更多内容
            if quote_content_ends_with_sentence:
                j = i + 1
                # 跳过可能的闭合标点
                while j < len(text) and text[j] in closing_chars:
                    current_sentence.append(text[j])
                    j += 1
                
                # 跳过空白字符
                while j < len(text) and text[j] in ' \t\n':
                    j += 1
                
                # 如果后面还有非空白字符，说明还有更多内容，应该切分当前句子
                if j < len(text):
                    # 完成当前句子
                    sentence = ''.join(current_sentence).strip()
                    if sentence:
                        sentences.append(sentence)
                    
                    current_sentence = []
                    i = j
                    continue
            
            i += 1
            continue
        
        # 检查是否是句子结束标点
        if char in sentence_end_chars:
            current_sentence.append(char)
            
            # 关键：只有在引号外时，才考虑切分句子
            if not quote_stack:
                # 检查后面是否有闭合标点（引号、括号等）
                j = i + 1
                while j < len(text) and text[j] in closing_chars:
                    current_sentence.append(text[j])
                    j += 1
                
                # 跳过空白字符
                while j < len(text) and text[j] in ' \t\n':
                    j += 1
                
                # 完成当前句子
                sentence = ''.join(current_sentence).strip()
                if sentence:
                    sentences.append(sentence)
                
                current_sentence = []
                i = j
                continue
            else:
                # 在引号内，继续收集字符，不切分
                i += 1
                continue
        
        # 普通字符
        current_sentence.append(char)
        i += 1
    
    # 处理剩余的文本
    if current_sentence:
        sentence = ''.join(current_sentence).strip()
        if sentence:
            sentences.append(sentence)
    
    return sentences


def split_sentences_advanced(text: str) -> List[str]:
    """
    高级句子切分方法，处理更复杂的情况
    
    包括：
    - 处理引号内的句子
    - 处理括号内的内容
    - 处理数字中的小数点（不切分）
    - 处理缩写（如 Mr. Dr. 等）
    - 处理网址和邮箱（不切分）
    """
    if not text or not text.strip():
        return []
    
    # 创建保护映射
    protected_map = {}
    protected_counter = 0
    
    def protect(match):
        nonlocal protected_counter
        placeholder = f"<PROTECTED_{protected_counter}>"
        protected_map[placeholder] = match.group(0)
        protected_counter += 1
        return placeholder
    
    # 1. 保护数字中的小数点（如 3.14, 2023.12.25）
    text = re.sub(r'\d+\.\d+', protect, text)
    
    # 2. 保护网址（http://, https://, www.）
    text = re.sub(r'https?://[^\s]+', protect, text)
    text = re.sub(r'www\.[^\s]+', protect, text)
    
    # 3. 保护邮箱地址
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', protect, text)
    
    # 4. 保护常见英文缩写（Mr., Dr., etc.）
    abbreviations = [
        r'\bMr\.', r'\bMrs\.', r'\bMs\.', r'\bDr\.', r'\bProf\.',
        r'\bSr\.', r'\bJr\.', r'\bInc\.', r'\bLtd\.', r'\bCo\.',
        r'\betc\.', r'\bi\.e\.', r'\be\.g\.', r'\bvs\.', r'\bU\.S\.',
        r'\bA\.D\.', r'\bB\.C\.', r'\ba\.m\.', r'\bp\.m\.',
        r'\bNo\.', r'\bVol\.', r'\bpp\.', r'\bcf\.', r'\bibid\.',
    ]
    for abbr in abbreviations:
        text = re.sub(abbr, protect, text, flags=re.IGNORECASE)
    
    # 进行句子切分
    sentences = split_sentences(text)
    
    # 恢复被保护的片段
    restored_sentences = []
    for sent in sentences:
        for placeholder, original in protected_map.items():
            sent = sent.replace(placeholder, original)
        restored_sentences.append(sent)
    
    return restored_sentences


def process_file(input_path: str, output_path: str = None, use_advanced: bool = True):
    """
    处理文本文件，进行句子切分
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（如果为None，则自动生成）
        use_advanced: 是否使用高级切分方法
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"错误：输入文件不存在: {input_path}")
        sys.exit(1)
    
    # 读取输入文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"错误：无法读取文件 {input_path}: {e}")
        sys.exit(1)
    
    # 进行句子切分
    if use_advanced:
        sentences = split_sentences_advanced(text)
    else:
        sentences = split_sentences(text)
    
    # 确定输出路径
    if output_path is None:
        output_file = input_file.parent / f"{input_file.stem}_sentences.txt"
    else:
        output_file = Path(output_path)
    
    # 写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, sentence in enumerate(sentences, 1):
                f.write(f"{i}. {sentence}\n")
        
        print(f"成功处理文件: {input_path}")
        print(f"输出文件: {output_file}")
        print(f"切分得到 {len(sentences)} 个句子")
    except Exception as e:
        print(f"错误：无法写入文件 {output_file}: {e}")
        sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n使用方法:")
        print("  python sentence_splitter.py <输入文件> [输出文件]")
        print("\n示例:")
        print("  python sentence_splitter.py story.txt")
        print("  python sentence_splitter.py story.txt output.txt")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_file(input_path, output_path, use_advanced=True)


if __name__ == "__main__":
    main()
