# 数据预处理工具

## 句子切分脚本 (sentence_splitter.py)

### 功能说明

`sentence_splitter.py` 是一个多语言句子切分工具，支持对以下语言的文本进行逐句切分：

- **中文**：支持中文标点符号（。！？等）
- **日语**：支持日文标点符号（。！？等）
- **英文**：支持英文标点符号（. ! ? 等）
- **波斯文**：支持波斯语标点符号（. ؟ 等）

### 使用方法

#### 基本用法

```bash
# 处理单个文件，自动生成输出文件名
python sentence_splitter.py input.txt

# 指定输出文件名
python sentence_splitter.py input.txt output.txt
```

#### 示例

```bash
# 处理中文故事文本
python sentence_splitter.py ../datasets/ChineseTales/texts/CH_004_梁山伯与祝英台.txt

# 处理日文故事文本
python sentence_splitter.py ../datasets/Japanese/texts/jp_001.txt jp_001_sentences.txt

# 处理英文故事文本
python sentence_splitter.py ../datasets/IndianTales/texts/EN_001_The_Lion_and_the_Crane.txt

# 处理波斯文故事文本
python sentence_splitter.py ../datasets/PersianTales/texts/FA_001_en.txt
```

### 输出格式

输出文件为文本文件，每行一个句子，格式如下：

```
1. 第一句话。
2. 第二句话。
3. 第三句话。
...
```

### 特性

1. **多语言支持**：自动识别并处理中文、日语、英文、波斯文的句子结束标点
2. **智能处理**：
   - 保护数字中的小数点（如 3.14）
   - 保护常见英文缩写（如 Mr., Dr., etc.）
   - 保护网址和邮箱地址
3. **段落感知**：保留段落结构，按段落进行切分
4. **引号处理**：正确处理引号内的句子结束标点

### 注意事项

- 输入文件必须是 UTF-8 编码
- 输出文件也是 UTF-8 编码
- 对于引号内包含多个句子的情况，可能会被切分成多个句子
- 脚本会自动处理常见的缩写和数字格式

### 技术细节

脚本使用正则表达式进行句子切分，主要识别以下句子结束标点：

- 中文/日语：`。` `！` `？`
- 英文：`.` `!` `?`
- 波斯文：`.` `؟`

脚本会智能处理：
- 数字中的小数点（不切分）
- 常见英文缩写（不切分）
- 网址和邮箱（不切分）
- 引号和括号的闭合

### 依赖

- Python 3.6+
- 标准库：`re`, `sys`, `pathlib`, `typing`

无需安装额外依赖。

### 运行测试

项目包含完整的单元测试，使用 Python 标准库的 `unittest` 框架：

```bash
# 运行所有测试
python3 test_sentence_splitter.py

# 或者使用 unittest 模块
python3 -m unittest test_sentence_splitter.py -v
```

测试覆盖以下场景：
- ✅ CJK字符检测（中文、日文平假名、片假名、汉字）
- ✅ 英文对话+叙述合并（原始bug修复）
- ✅ 中文对话+叙述合并（英文引号和中文引号）
- ✅ 日文对话+叙述合并
- ✅ 破折号连接处理
- ✅ 正常句子切分
- ✅ 引号内句子处理
- ✅ 边界情况（空文本、未闭合引号、数字、缩写等）
- ✅ 真实世界例子

当前测试套件包含 **40 个测试用例**，全部通过。
