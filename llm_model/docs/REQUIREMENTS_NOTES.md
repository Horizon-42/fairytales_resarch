# Fine-tuning Requirements 说明

## 重要依赖版本要求

### datasets==4.3.0

**为什么固定版本？**

- Unsloth 与 `datasets==4.5.0` 和 `datasets==4.4.0` 不兼容
- 这些版本会导致递归错误（recursion errors）
- `datasets==4.3.0` 是经过测试的稳定版本

**错误示例：**
```
NotImplementedError: #### Unsloth: Using `datasets = 4.5.0` will cause recursion errors.
Please downgrade datasets to `datasets==4.3.0`
```

**解决方案：**
```bash
pip install 'datasets==4.3.0'
```

### unsloth-zoo>=2026.1.3

**为什么需要这个版本？**

- `unsloth 2026.1.3` 要求 `unsloth_zoo>=2026.1.3`
- 旧版本（如 `2025.11.2`）会导致依赖冲突

**错误示例：**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
unsloth 2026.1.3 requires unsloth_zoo>=2026.1.3, but you have unsloth-zoo 2025.11.2 which is incompatible.
```

**解决方案：**
```bash
pip install --upgrade 'unsloth-zoo>=2026.1.3'
```

## 安装步骤

### 完整安装

```bash
# 1. 安装核心依赖
pip install -r llm_model/finetune/requirements.txt

# 2. 如果遇到版本冲突，强制重新安装
pip install --force-reinstall 'datasets==4.3.0'
pip install --upgrade 'unsloth-zoo>=2026.1.3'
```

### 在 Conda 环境中安装

```bash
conda run -n nlp pip install -r llm_model/finetune/requirements.txt

# 如果遇到冲突
conda run -n nlp pip install --force-reinstall 'datasets==4.3.0'
conda run -n nlp pip install --upgrade 'unsloth-zoo>=2026.1.3'
```

## 验证安装

```bash
# 检查 datasets 版本
python -c "import datasets; print(datasets.__version__)"
# 应该输出: 4.3.0

# 检查 unsloth 和 unsloth-zoo 版本
pip show unsloth unsloth-zoo

# 验证导入
python -c "from unsloth import FastLanguageModel; print('✅ Unsloth imported successfully')"
```

## 常见问题

### Q: 为什么不能使用 datasets 的最新版本？

A: Unsloth 在导入时会 patch `datasets` 库，但 `datasets==4.5.0` 的内部变化导致 patch 失败并引发递归错误。`datasets==4.3.0` 是经过测试的兼容版本。

### Q: 如何更新 unsloth？

A: 
```bash
pip install --upgrade --no-deps --no-cache-dir unsloth
pip install --upgrade 'unsloth-zoo>=2026.1.3'
```

### Q: 如果其他包需要更新的 datasets 版本怎么办？

A: 这是一个已知的兼容性问题。可以考虑：
1. 使用虚拟环境隔离 fine-tuning 依赖
2. 等待 Unsloth 更新以支持新版本的 datasets
3. 检查是否有 Unsloth 的更新版本支持新 datasets

## 相关链接

- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [Unsloth Issues](https://github.com/unslothai/unsloth/issues)
- [datasets 文档](https://huggingface.co/docs/datasets/)
