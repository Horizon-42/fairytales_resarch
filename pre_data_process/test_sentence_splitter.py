#!/usr/bin/env python3
"""
单元测试 for sentence_splitter.py

测试句子切分器的各种功能，包括：
- 英文、中文、日文的对话+叙述合并
- 引号处理
- 破折号处理
- 边界情况
"""

import unittest
from pathlib import Path
import sys

# 添加父目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent))

from sentence_splitter import (
    split_sentences,
    split_sentences_advanced,
    split_sentences_with_quotes,
    is_cjk_char,
    process_file,
)


class TestCJKCharDetection(unittest.TestCase):
    """测试CJK字符检测功能"""
    
    def test_chinese_char(self):
        """测试中文字符检测"""
        self.assertTrue(is_cjk_char('中'))
        self.assertTrue(is_cjk_char('文'))
        self.assertTrue(is_cjk_char('字'))
        self.assertTrue(is_cjk_char('符'))
    
    def test_japanese_hiragana(self):
        """测试日文平假名检测"""
        self.assertTrue(is_cjk_char('あ'))
        self.assertTrue(is_cjk_char('い'))
        self.assertTrue(is_cjk_char('う'))
        self.assertTrue(is_cjk_char('え'))
        self.assertTrue(is_cjk_char('お'))
    
    def test_japanese_katakana(self):
        """测试日文片假名检测"""
        self.assertTrue(is_cjk_char('ア'))
        self.assertTrue(is_cjk_char('イ'))
        self.assertTrue(is_cjk_char('ウ'))
        self.assertTrue(is_cjk_char('エ'))
        self.assertTrue(is_cjk_char('オ'))
    
    def test_japanese_kanji(self):
        """测试日文汉字检测"""
        self.assertTrue(is_cjk_char('日'))
        self.assertTrue(is_cjk_char('本'))
        self.assertTrue(is_cjk_char('語'))
    
    def test_non_cjk_chars(self):
        """测试非CJK字符"""
        self.assertFalse(is_cjk_char('a'))
        self.assertFalse(is_cjk_char('A'))
        self.assertFalse(is_cjk_char('1'))
        self.assertFalse(is_cjk_char('.'))
        self.assertFalse(is_cjk_char(' '))
        self.assertFalse(is_cjk_char(''))


class TestEnglishDialogueNarration(unittest.TestCase):
    """测试英文对话+叙述合并"""
    
    def test_question_with_narration(self):
        """测试问号后跟叙述的情况（原始bug）"""
        text = '"Who shall be my teacher?" the lad asked.'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"Who shall be my teacher?"', sentences[0])
        self.assertIn('the lad asked', sentences[0])
    
    def test_exclamation_with_narration(self):
        """测试感叹号后跟叙述的情况"""
        text = '"What a beautiful day!" she exclaimed.'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"What a beautiful day!"', sentences[0])
        self.assertIn('she exclaimed', sentences[0])
    
    def test_period_with_narration(self):
        """测试句号后跟叙述的情况"""
        text = '"I will go." he said.'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"I will go."', sentences[0])
        self.assertIn('he said', sentences[0])
    
    def test_single_quotes_with_narration(self):
        """测试单引号后跟叙述的情况"""
        text = "'Who are you?' he asked."
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn("'Who are you?'", sentences[0])
        self.assertIn('he asked', sentences[0])
    
    def test_multiple_dialogues_separate(self):
        """测试多个独立对话应该分开"""
        text = '"Hello!" she said. "How are you?" he replied.'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 2)
        self.assertIn('"Hello!"', sentences[0])
        self.assertIn('"How are you?"', sentences[1])


class TestChineseDialogueNarration(unittest.TestCase):
    """测试中文对话+叙述合并"""
    
    def test_chinese_double_quotes_with_narration(self):
        """测试中文双引号（英文引号）后跟叙述"""
        text = '"爹爹，我们拿这粪瓢来舀干天河的水。"小女儿終于揩干了眼泪，瞪着一对小眼睛, 这么天真而又倔强地提议。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"爹爹，我们拿这粪瓢来舀干天河的水。"', sentences[0])
        self.assertIn('小女儿', sentences[0])
    
    def test_chinese_quote_pairs_with_narration(self):
        """测试中文引号对（「」）后跟叙述"""
        text = '「爹爹，我们拿这粪瓢来舀干天河的水。」小女儿終于揩干了眼泪，瞪着一对小眼睛, 这么天真而又倔强地提议。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('「爹爹，我们拿这粪瓢来舀干天河的水。」', sentences[0])
        self.assertIn('小女儿', sentences[0])
    
    def test_chinese_quote_pairs_alternative(self):
        """测试中文引号对（『』）后跟叙述"""
        text = '『你好吗？』他问道。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('『你好吗？』', sentences[0])
        self.assertIn('他问道', sentences[0])
    
    def test_chinese_exclamation_with_narration(self):
        """测试中文感叹号后跟叙述"""
        text = '"太好了！"她高兴地说。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"太好了！"', sentences[0])
        self.assertIn('她高兴地说', sentences[0])
    
    def test_chinese_period_with_narration(self):
        """测试中文句号后跟叙述"""
        text = '"我会去的。"他说道。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"我会去的。"', sentences[0])
        self.assertIn('他说道', sentences[0])


class TestJapaneseDialogueNarration(unittest.TestCase):
    """测试日文对话+叙述合并"""
    
    def test_japanese_quotes_with_narration(self):
        """测试日文引号后跟叙述"""
        text = '「ドンブラコッコ、スッコッコ。\nドンブラコッコ、スッコッコ。」\nと流ながれて来きました。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('「ドンブラコッコ、スッコッコ。', sentences[0])
        self.assertIn('と流ながれて来きました', sentences[0])
    
    def test_japanese_question_with_narration(self):
        """测试日文问号后跟叙述"""
        text = '「誰ですか？」彼が尋ねました。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('「誰ですか？」', sentences[0])
        self.assertIn('彼が尋ねました', sentences[0])
    
    def test_japanese_exclamation_with_narration(self):
        """测试日文感叹号后跟叙述"""
        text = '「すごい！」彼女は叫びました。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('「すごい！」', sentences[0])
        self.assertIn('彼女は叫びました', sentences[0])


class TestDashContinuation(unittest.TestCase):
    """测试破折号连接处理"""
    
    def test_chinese_dash_continuation(self):
        """测试中文破折号连接"""
        text = '他说："我会去的。"——然后他离开了。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"我会去的。"', sentences[0])
        self.assertIn('——', sentences[0])
        self.assertIn('然后他离开了', sentences[0])
    
    def test_english_dash_continuation(self):
        """测试英文破折号连接"""
        text = 'He said: "I will go."—Then he left.'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"I will go."', sentences[0])
        # 检查是否包含破折号
        self.assertTrue('—' in sentences[0] or '--' in sentences[0])
    
    def test_colon_continuation(self):
        """测试冒号连接"""
        text = '国王说："我的儿子，去完成你的教育。"'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('"我的儿子，去完成你的教育。"', sentences[0])


class TestNormalSentences(unittest.TestCase):
    """测试正常句子切分"""
    
    def test_simple_sentences(self):
        """测试简单句子"""
        text = "First sentence. Second sentence. Third sentence."
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "First sentence.")
        self.assertEqual(sentences[1], "Second sentence.")
        self.assertEqual(sentences[2], "Third sentence.")
    
    def test_chinese_sentences(self):
        """测试中文句子"""
        text = "第一句话。第二句话。第三句话。"
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "第一句话。")
        self.assertEqual(sentences[1], "第二句话。")
        self.assertEqual(sentences[2], "第三句话。")
    
    def test_japanese_sentences(self):
        """测试日文句子"""
        text = "最初の文。二番目の文。三番目の文。"
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 3)
        self.assertIn("最初の文。", sentences[0])
        self.assertIn("二番目の文。", sentences[1])
        self.assertIn("三番目の文。", sentences[2])
    
    def test_mixed_punctuation(self):
        """测试混合标点"""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 3)


class TestQuotesInSentences(unittest.TestCase):
    """测试引号内的句子"""
    
    def test_quote_with_multiple_sentences(self):
        """测试引号内多个句子"""
        text = 'He said: "First. Second. Third." Then he left.'
        sentences = split_sentences_advanced(text)
        # 引号内的句子应该被正确切分
        self.assertGreaterEqual(len(sentences), 2)
        self.assertIn('Then he left', sentences[-1])
    
    def test_nested_quotes(self):
        """测试嵌套引号"""
        text = 'He said: "She told me \'Hello.\'" Then he left.'
        sentences = split_sentences_advanced(text)
        self.assertGreaterEqual(len(sentences), 1)
    
    def test_chinese_nested_quotes(self):
        """测试中文嵌套引号"""
        text = '他说：「她告诉我『你好。』」然后他离开了。'
        sentences = split_sentences_advanced(text)
        self.assertGreaterEqual(len(sentences), 1)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_empty_text(self):
        """测试空文本"""
        sentences = split_sentences_advanced("")
        self.assertEqual(len(sentences), 0)
    
    def test_whitespace_only(self):
        """测试只有空白字符"""
        sentences = split_sentences_advanced("   \n\n\t  ")
        self.assertEqual(len(sentences), 0)
    
    def test_no_sentence_end(self):
        """测试没有句子结束标点"""
        text = "This is a sentence without ending"
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertEqual(sentences[0], text)
    
    def test_only_quotes(self):
        """测试只有引号"""
        text = '""'
        sentences = split_sentences_advanced(text)
        # 应该返回空或包含引号的句子
        self.assertIsInstance(sentences, list)
    
    def test_quote_without_closing(self):
        """测试未闭合的引号"""
        text = '"This is a quote without closing'
        sentences = split_sentences_advanced(text)
        self.assertGreaterEqual(len(sentences), 1)
    
    def test_numbers_with_decimals(self):
        """测试数字中的小数点（不应切分）"""
        text = "The price is 3.14 dollars. That's cheap."
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 2)
        self.assertIn("3.14", sentences[0])
    
    def test_abbreviations(self):
        """测试缩写（不应切分）"""
        text = "Mr. Smith went to the U.S.A. He was happy."
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 2)
        self.assertIn("Mr.", sentences[0])
        self.assertIn("U.S.A.", sentences[0])


class TestRealWorldExamples(unittest.TestCase):
    """测试真实世界的例子"""
    
    def test_english_story_example(self):
        """测试英文故事例子（原始bug案例）"""
        text = '''When he came to years of discretion, and had attained the measure of sixteen years, the King said to him:
"My son, go and complete your education."
"Who shall be my teacher?" the lad asked.
"Go, my son; in the kingdom of Candahar, in the city of Takkasila, is a far-famed teacher from whom I wish you to learn. Take this, and give it him for a fee." With that he gave him a thousand pieces of money, and dismissed him.'''
        sentences = split_sentences_advanced(text)
        # "Who shall be my teacher?" the lad asked. 应该是一个句子
        found_combined = False
        for sent in sentences:
            if '"Who shall be my teacher?"' in sent and 'the lad asked' in sent:
                found_combined = True
                break
        self.assertTrue(found_combined, "Dialogue with narration should be combined")
    
    def test_chinese_story_example(self):
        """测试中文故事例子"""
        text = '"爹爹，我们拿这粪瓢来舀干天河的水。"小女儿終于揩干了眼泪，瞪着一对小眼睛, 这么天真而又倔强地提议。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('小女儿', sentences[0])
    
    def test_japanese_story_example(self):
        """测试日文故事例子"""
        text = '「ドンブラコッコ、スッコッコ。\nドンブラコッコ、スッコッコ。」\nと流ながれて来きました。'
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 1)
        self.assertIn('と流ながれて来きました', sentences[0])


class TestParagraphHandling(unittest.TestCase):
    """测试段落处理"""
    
    def test_multiple_paragraphs(self):
        """测试多个段落"""
        text = "First paragraph. Second sentence.\n\nSecond paragraph. Another sentence."
        sentences = split_sentences_advanced(text)
        self.assertEqual(len(sentences), 4)
    
    def test_paragraph_with_dialogue(self):
        """测试包含对话的段落"""
        text = '''The King said: "Go and learn."
"Who shall be my teacher?" the lad asked.
The King replied.'''
        sentences = split_sentences_advanced(text)
        # 应该正确处理对话+叙述
        self.assertGreaterEqual(len(sentences), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
