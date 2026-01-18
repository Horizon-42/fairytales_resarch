# Unsloth 在 CUDA 12.8 上的安装指南

## ⚠️ 重要说明

**CUDA 12.8 支持说明：**
- CUDA 12.8 需要 PyTorch **nightly** 版本（稳定版暂不支持）
- 确保使用匹配的 PyTorch、torchvision 版本
- unsloth 2026.1.3 需要 torch>=2.9.1 和 torchvision>=0.24.0

## 📋 前置要求

1. **GPU 和驱动**
   - NVIDIA GPU（支持 CUDA 12.8，如 RTX 5080/5090 等 Blackwell 架构）
   - 安装最新的 NVIDIA 驱动（支持 CUDA 12.8）
   - 验证驱动：`nvidia-smi` 应显示驱动版本

2. **Python 环境**
   - Python 3.10, 3.11, 3.12, 或 3.13
   - 建议使用 conda 环境

3. **清理旧安装**（可选但推荐）
   ```bash
   # 卸载可能冲突的包
   pip uninstall torch torchvision torchaudio xformers -y
   ```

## 🚀 安装步骤（推荐方法）

### 方法 1: 使用 Nightly PyTorch（CUDA 12.8）

```bash
# 1. 激活 conda 环境
conda activate nlp

# 2. 安装 PyTorch nightly (CUDA 12.8)
pip install --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128 \
    --no-cache-dir

# 3. 验证 PyTorch 安装
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA version: {torch.version.cuda}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"

# 4. 安装 unsloth 和相关依赖（按顺序）
# 先安装核心依赖（确保版本兼容）
pip install --no-cache-dir \
    'transformers>=4.40.0' \
    'trl>=0.8.0' \
    'peft>=0.8.0' \
    'datasets==4.3.0' \
    'accelerate>=0.24.0'

# 5. 安装 unsloth（会自动安装匹配的依赖）
pip install --no-cache-dir 'unsloth[colab-new]>=2024.9'

# 6. 确保 unsloth-zoo 版本匹配
pip install --upgrade --no-cache-dir 'unsloth-zoo>=2026.1.3'

# 7. 验证 unsloth 安装
python -c "
from unsloth import FastLanguageModel
print('✅ Unsloth imported successfully')
print(f'FastLanguageModel available: {FastLanguageModel is not None}')
"
```

### 方法 2: 如果 Nightly 有问题，使用 CUDA 12.1/12.4（降级兼容）

如果 CUDA 12.8 的 nightly 版本有问题，可以使用官方支持的 CUDA 12.1 或 12.4：

```bash
# 1. 激活 conda 环境
conda activate nlp

# 2. 卸载旧版本
pip uninstall torch torchvision torchaudio -y

# 3. 安装 PyTorch CUDA 12.1（更稳定）
pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121 \
    --no-cache-dir

# 4. 验证安装
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"

# 5. 安装 unsloth（同上）
pip install --no-cache-dir \
    'transformers>=4.40.0' \
    'trl>=0.8.0' \
    'peft>=0.8.0' \
    'datasets==4.3.0' \
    'accelerate>=0.24.0' \
    'unsloth[colab-new]>=2024.9' \
    'unsloth-zoo>=2026.1.3'
```

## 🔍 验证安装

运行以下验证脚本：

```bash
python <<EOF
import torch
from unsloth import FastLanguageModel

print("=" * 60)
print("环境验证")
print("=" * 60)

# PyTorch 信息
print(f"\nPyTorch:")
print(f"  版本: {torch.__version__}")
print(f"  CUDA 版本: {torch.version.cuda}")
print(f"  CUDA 可用: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"  GPU 数量: {torch.cuda.device_count()}")
    print(f"  当前 GPU: {torch.cuda.get_device_name(0)}")
    print(f"  GPU 内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

# Unsloth 信息
print(f"\nUnsloth:")
print(f"  FastLanguageModel: {FastLanguageModel}")
print(f"  ✅ 导入成功")

# 检查关键依赖版本
try:
    import transformers
    import trl
    import peft
    import datasets
    print(f"\n关键依赖版本:")
    print(f"  transformers: {transformers.__version__}")
    print(f"  trl: {trl.__version__}")
    print(f"  peft: {peft.__version__}")
    print(f"  datasets: {datasets.__version__}")
except Exception as e:
    print(f"  警告: 无法检查依赖版本 - {e}")

print("\n" + "=" * 60)
print("✅ 验证完成！")
print("=" * 60)
EOF
```

## 🐛 常见问题解决

### 问题 1: torchvision 版本不匹配

**错误信息：**
```
ImportError: Unsloth: torch==2.9.1 requires torchvision>=0.24.0, but found torchvision==0.2.0
```

**解决方案：**
```bash
# 确保 torch 和 torchvision 版本匹配
pip uninstall torchvision -y
pip install torchvision --index-url https://download.pytorch.org/whl/nightly/cu128
```

### 问题 2: datasets 版本冲突

**错误信息：**
```
NotImplementedError: Using `datasets = 4.5.0` will cause recursion errors.
```

**解决方案：**
```bash
pip install --force-reinstall 'datasets==4.3.0'
```

### 问题 3: unsloth-zoo 版本不匹配

**错误信息：**
```
unsloth 2026.1.3 requires unsloth_zoo>=2026.1.3, but you have unsloth-zoo 2025.11.2
```

**解决方案：**
```bash
pip install --upgrade 'unsloth-zoo>=2026.1.3'
```

### 问题 4: CUDA 不可用

**检查步骤：**
```bash
# 1. 检查驱动
nvidia-smi

# 2. 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"

# 3. 如果显示 False，重新安装 CUDA 版本的 PyTorch
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/nightly/cu128
```

## 📝 完整一键安装脚本

创建 `install_unsloth_cuda128.sh`：

```bash
#!/bin/bash
set -e

echo "============================================================"
echo "Unsloth CUDA 12.8 安装脚本"
echo "============================================================"

# 检查 conda 环境
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  未检测到 conda 环境，建议先激活: conda activate nlp"
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 清理旧安装
echo "步骤 1: 清理旧安装..."
pip uninstall -y torch torchvision torchaudio xformers 2>/dev/null || true

# 2. 安装 PyTorch nightly (CUDA 12.8)
echo "步骤 2: 安装 PyTorch nightly (CUDA 12.8)..."
pip install --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128 \
    --no-cache-dir

# 3. 验证 PyTorch
echo "步骤 3: 验证 PyTorch..."
python -c "
import torch
assert torch.cuda.is_available(), 'CUDA 不可用！'
print(f'✅ PyTorch {torch.__version__} with CUDA {torch.version.cuda}')
"

# 4. 安装核心依赖
echo "步骤 4: 安装核心依赖..."
pip install --no-cache-dir \
    'transformers>=4.40.0' \
    'trl>=0.8.0' \
    'peft>=0.8.0' \
    'datasets==4.3.0' \
    'accelerate>=0.24.0'

# 5. 安装 unsloth
echo "步骤 5: 安装 unsloth..."
pip install --no-cache-dir 'unsloth[colab-new]>=2024.9'

# 6. 安装 unsloth-zoo
echo "步骤 6: 安装 unsloth-zoo..."
pip install --upgrade --no-cache-dir 'unsloth-zoo>=2026.1.3'

# 7. 最终验证
echo "步骤 7: 验证安装..."
python -c "
from unsloth import FastLanguageModel
import torch
print('✅ 所有组件安装成功！')
print(f'  - PyTorch: {torch.__version__}')
print(f'  - CUDA: {torch.version.cuda}')
print(f'  - CUDA 可用: {torch.cuda.is_available()}')
print(f'  - Unsloth: 导入成功')
"

echo "============================================================"
echo "✅ 安装完成！"
echo "============================================================"
```

使用脚本：
```bash
chmod +x install_unsloth_cuda128.sh
conda activate nlp
./install_unsloth_cuda128.sh
```

## 🔗 参考资源

- [Unsloth 官方文档](https://unsloth.ai/docs/get-started/install-and-update/pip-install)
- [PyTorch 安装指南](https://pytorch.org/get-started/locally/)
- [CUDA 12.8 支持](https://pytorch.org/get-started/previous-versions/)

## ⚠️ 注意事项

1. **Nightly 版本警告**：使用 nightly 版本可能不稳定，建议在稳定环境中测试
2. **版本锁定**：建议使用 `requirements.txt` 锁定版本，避免自动升级导致冲突
3. **环境隔离**：建议在独立的 conda 环境中安装，避免影响其他项目
4. **定期更新**：检查 unsloth 和 PyTorch 的更新，但更新前先备份环境
