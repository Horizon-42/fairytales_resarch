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


def is_cjk_char(char: str) -> bool:
    """
    检查字符是否是CJK（中日韩）字符
    
    Args:
        char: 单个字符
        
    Returns:
        如果是CJK字符返回True，否则返回False
    """
    if not char:
        return False
    code = ord(char)
    # CJK统一表意文字：U+4E00-U+9FFF
    # CJK扩展A：U+3400-U+4DBF
    # CJK扩展B：U+20000-U+2A6DF (需要代理对处理，这里简化处理)
    # 日文平假名：U+3040-U+309F
    # 日文片假名：U+30A0-U+30FF
    # 日文汉字：U+4E00-U+9FFF (与中文共享)
    return (
        (0x4E00 <= code <= 0x9FFF) or  # CJK统一表意文字
        (0x3400 <= code <= 0x4DBF) or  # CJK扩展A
        (0x3040 <= code <= 0x309F) or  # 日文平假名
        (0x30A0 <= code <= 0x30FF)     # 日文片假名
    )


def split_sentences_with_quotes(text: str) -> List[str]:
    """
    智能句子切分，正确处理引号内的对话和破折号
    
    引号类型：
    - 中文双引号：「」『』
    - 中文单引号：''
    - 英文双引号：""
    - 英文单引号：''
    
    破折号处理：
    - 中文破折号（——）和英文破折号（—、–、--）与其之前的句子视为一个句子
    - 如果句子结束标点后跟着破折号，不在此处切分，继续收集字符
    """
    if not text:
        return []
    
    # 将所有类型的引号统一分组，视为同一种符号进行配对
    # 双引号组：所有类型的双引号都视为同一种
    # U+0022: 标准双引号 ", U+201C: 左双引号 ", U+201D: 右双引号 "
    double_quotes = {'\u0022', '\u201C', '\u201D'}  # 标准双引号、左弯引号、右弯引号
    # 单引号组：所有类型的单引号都视为同一种
    # U+0027: 标准单引号 ', U+2018: 左单引号 ', U+2019: 右单引号 '
    single_quotes = {'\u0027', '\u2018', '\u2019'}  # 标准单引号、左弯引号、右弯引号
    # 中文引号对（保持独立）
    chinese_quote_pairs = {
        '「': '」',  # 中文双引号
        '『': '』',  # 中文双引号（另一种）
    }
    
    # 定义所有可能的引号字符
    all_quote_chars = double_quotes | single_quotes | set(chinese_quote_pairs.keys()) | set(chinese_quote_pairs.values())

    sentences = []
    i = 0
    current_sentence = []
    # 引号栈：使用字符串标记引号类型（'double', 'single', '「', '『'）
    quote_stack = []
    sentence_end_chars = ['。', '！', '？', '.', '!', '?', '؟']
    closing_chars = ['」', '』', '"', "'", '"', "'", ')', '）']
    # 破折号：中文破折号（——）和英文破折号（—、--）
    dash_chars = ['—', '–']  # em dash 和 en dash
    dash_pattern = '——'  # 中文破折号（两个连续的破折号）
    
    while i < len(text):
        char = text[i]
        
        # 检查是否是中文引号
        if char in chinese_quote_pairs:
            # 中文引号开始
            quote_stack.append(char)
            current_sentence.append(char)
            i += 1
            continue
        
        if char in chinese_quote_pairs.values():
            # 中文引号结束
            if quote_stack and quote_stack[-1] in chinese_quote_pairs:
                expected_close = chinese_quote_pairs[quote_stack[-1]]
                if char == expected_close:
                    quote_stack.pop()
                    current_sentence.append(char)
                    
                    # 引号闭合后的处理（与下面双引号/单引号的处理相同）
                    quote_content_ends_with_sentence = False
                    if len(current_sentence) >= 2:
                        prev_char = current_sentence[-2]
                        if prev_char in sentence_end_chars:
                            quote_content_ends_with_sentence = True
                    
                    if quote_content_ends_with_sentence:
                        j = i + 1
                        while j < len(text) and text[j] in closing_chars:
                            current_sentence.append(text[j])
                            j += 1
                        while j < len(text) and text[j] in ' \t\n':
                            j += 1
                        
                        has_continuation_punct = False
                        punct_length = 0
                        if j < len(text):
                            if j + 1 < len(text) and text[j:j+2] == dash_pattern:
                                has_continuation_punct = True
                                punct_length = 2
                            elif text[j] in dash_chars:
                                has_continuation_punct = True
                                punct_length = 1
                            elif j + 1 < len(text) and text[j:j+2] == '--':
                                has_continuation_punct = True
                                punct_length = 2
                            elif text[j] in ['：', ':']:
                                has_continuation_punct = True
                                punct_length = 1
                            elif text[j] in ['；', ';']:
                                has_continuation_punct = True
                                punct_length = 1
                        
                        if has_continuation_punct:
                            for k in range(punct_length):
                                if j + k < len(text):
                                    current_sentence.append(text[j + k])
                            i = j + punct_length
                            continue
                        
                        # 检查后面是否有小写字母或CJK字符开头的文本（可能是对话后的叙述/说明）
                        has_narration = False
                        if j < len(text):
                            next_char = text[j]
                            if next_char.islower() or is_cjk_char(next_char):
                                has_narration = True
                        
                        if has_narration:
                            i = j
                            continue
                        
                        if j < len(text):
                            sentence = ''.join(current_sentence).strip()
                            if sentence:
                                sentences.append(sentence)
                            current_sentence = []
                            i = j
                            continue
                    
                    i += 1
                    continue
        
        # 检查是否是双引号（所有类型的双引号都视为同一种）
        if char in double_quotes:
            if quote_stack and quote_stack[-1] == 'double':
                # 引号栈不为空且栈顶是双引号，说明是闭引号
                quote_stack.pop()
                current_sentence.append(char)

                # 引号闭合后，检查引号内的最后一个字符是否是句子结束标点
                quote_content_ends_with_sentence = False
                if len(current_sentence) >= 2:
                    prev_char = current_sentence[-2]
                    if prev_char in sentence_end_chars:
                        quote_content_ends_with_sentence = True

                # 如果引号内以句子结束标点结尾，且后面还有更多内容，应该切分
                if quote_content_ends_with_sentence:
                    j = i + 1
                    # 跳过可能的闭合标点
                    while j < len(text) and text[j] in closing_chars:
                        current_sentence.append(text[j])
                        j += 1

                    # 跳过空白字符
                    while j < len(text) and text[j] in ' \t\n':
                        j += 1
                    
                    # 检查后面是否有破折号、冒号、分号等连接标点
                    # 如果后面有这些标点，不应该在这里切分，继续收集字符
                    has_continuation_punct = False
                    punct_length = 0
                    if j < len(text):
                        # 检查是否是中文破折号（——）
                        if j + 1 < len(text) and text[j:j+2] == dash_pattern:
                            has_continuation_punct = True
                            punct_length = 2
                        # 检查是否是英文破折号（—、–）
                        elif text[j] in dash_chars:
                            has_continuation_punct = True
                            punct_length = 1
                        # 检查是否是两个连字符（--）
                        elif j + 1 < len(text) and text[j:j+2] == '--':
                            has_continuation_punct = True
                            punct_length = 2
                        # 检查是否是冒号（：、:）
                        elif text[j] in ['：', ':']:
                            has_continuation_punct = True
                            punct_length = 1
                        # 检查是否是分号（；、;）
                        elif text[j] in ['；', ';']:
                            has_continuation_punct = True
                            punct_length = 1
                    
                    # 如果有连接标点，将标点添加到当前句子，然后继续收集字符，不切分
                    if has_continuation_punct:
                        # 将连接标点添加到当前句子
                        for k in range(punct_length):
                            if j + k < len(text):
                                current_sentence.append(text[j + k])
                        # 跳过连接标点，继续处理后面的内容
                        i = j + punct_length
                        continue

                    # 检查后面是否有小写字母或CJK字符开头的文本（可能是对话后的叙述/说明）
                    # 例如："Who shall be my teacher?" the lad asked.
                    # 例如："爹爹，我们拿这粪瓢来舀干天河的水。"小女儿終于揩干了眼泪
                    # 例如：「ドンブラコッコ、スッコッコ。」と流ながれて来きました
                    # 这种情况下，叙述部分应该和对话部分属于同一个句子
                    has_narration = False
                    if j < len(text):
                        next_char = text[j]
                        # 如果下一个字符是小写字母或CJK字符，可能是叙述文本
                        if next_char.islower() or is_cjk_char(next_char):
                            has_narration = True
                            # 继续收集字符，直到遇到下一个句子结束标点
                            # 不在这里切分，让后续的句子结束标点处理逻辑来切分
                    
                    # 如果有叙述文本，继续收集，不切分
                    if has_narration:
                        i = j
                        continue

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
            else:
                # 引号栈为空或栈顶不是双引号，说明是开引号
                quote_stack.append('double')
                current_sentence.append(char)
                i += 1
                continue
        
        # 检查是否是单引号（所有类型的单引号都视为同一种）
        if char in single_quotes:
            if quote_stack and quote_stack[-1] == 'single':
                # 引号栈不为空且栈顶是单引号，说明是闭引号
                quote_stack.pop()
                current_sentence.append(char)
                
                # 引号闭合后的处理（与双引号相同）
                quote_content_ends_with_sentence = False
                if len(current_sentence) >= 2:
                    prev_char = current_sentence[-2]
                    if prev_char in sentence_end_chars:
                        quote_content_ends_with_sentence = True
                
                if quote_content_ends_with_sentence:
                    j = i + 1
                    while j < len(text) and text[j] in closing_chars:
                        current_sentence.append(text[j])
                        j += 1
                    while j < len(text) and text[j] in ' \t\n':
                        j += 1
                    
                    has_continuation_punct = False
                    punct_length = 0
                    if j < len(text):
                        if j + 1 < len(text) and text[j:j+2] == dash_pattern:
                            has_continuation_punct = True
                            punct_length = 2
                        elif text[j] in dash_chars:
                            has_continuation_punct = True
                            punct_length = 1
                        elif j + 1 < len(text) and text[j:j+2] == '--':
                            has_continuation_punct = True
                            punct_length = 2
                        elif text[j] in ['：', ':']:
                            has_continuation_punct = True
                            punct_length = 1
                        elif text[j] in ['；', ';']:
                            has_continuation_punct = True
                            punct_length = 1
                    
                    if has_continuation_punct:
                        for k in range(punct_length):
                            if j + k < len(text):
                                current_sentence.append(text[j + k])
                        i = j + punct_length
                        continue
                    
                    # 检查后面是否有小写字母或CJK字符开头的文本（可能是对话后的叙述/说明）
                    has_narration = False
                    if j < len(text):
                        next_char = text[j]
                        if next_char.islower() or is_cjk_char(next_char):
                            has_narration = True
                    
                    if has_narration:
                        i = j
                        continue
                    
                    if j < len(text):
                        sentence = ''.join(current_sentence).strip()
                        if sentence:
                            sentences.append(sentence)
                        current_sentence = []
                        i = j
                        continue
                
                i += 1
                continue
            else:
                # 引号栈为空或栈顶不是单引号，说明是开引号
                quote_stack.append('single')
                current_sentence.append(char)
                i += 1
                continue
        
        # 旧的引号处理逻辑已移除，现在统一使用上面的分组处理
            # 这是一个闭引号，但类型不匹配当前栈顶
            # 为了简化，我们假设如果遇到闭引号且栈不为空，就关闭当前引号
            quote_stack.pop()
            current_sentence.append(char)
            
            # 旧的引号处理逻辑已移除
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
                
                # 检查后面是否有破折号、冒号、分号等连接标点
                # 如果后面有这些标点，不应该在这里切分，继续收集字符
                has_continuation_punct = False
                punct_length = 0
                if j < len(text):
                    # 检查是否是中文破折号（——）
                    if j + 1 < len(text) and text[j:j+2] == dash_pattern:
                        has_continuation_punct = True
                        punct_length = 2
                    # 检查是否是英文破折号（—、–）
                    elif text[j] in dash_chars:
                        has_continuation_punct = True
                        punct_length = 1
                    # 检查是否是两个连字符（--）
                    elif j + 1 < len(text) and text[j:j+2] == '--':
                        has_continuation_punct = True
                        punct_length = 2
                    # 检查是否是冒号（：、:）
                    elif text[j] in ['：', ':']:
                        has_continuation_punct = True
                        punct_length = 1
                    # 检查是否是分号（；、;）
                    elif text[j] in ['；', ';']:
                        has_continuation_punct = True
                        punct_length = 1

                # 如果有连接标点，将标点添加到当前句子，然后继续收集字符，不切分
                if has_continuation_punct:
                    # 将连接标点添加到当前句子
                    for k in range(punct_length):
                        if j + k < len(text):
                            current_sentence.append(text[j + k])
                    # 跳过连接标点，继续处理后面的内容
                    i = j + punct_length
                    continue

                # 完成当前句子
                sentence = ''.join(current_sentence).strip()
                if sentence:
                    sentences.append(sentence)
                
                current_sentence = []
                i = j
                continue
            else:
                # 在引号内，继续收集字符，不切分
                # 这是关键：引号内的句子结束标点不应该导致切分
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
