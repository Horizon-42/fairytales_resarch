#!/bin/bash
set -e

echo "Unsloth 安装脚本（CUDA 12.8）"
echo "================================"

# 清理可能冲突的包，让unsloth自己安装匹配的版本
echo "清理旧版本..."
pip uninstall -y torch torchvision torchaudio 2>/dev/null || true

# 让unsloth自己处理torch安装，避免版本冲突
echo "安装 unsloth（会自动安装匹配的torch版本）..."
pip install 'unsloth[colab-new]' 'unsloth-zoo' 'datasets==4.3.0'

echo ""
echo "验证安装..."
python -c "from unsloth import FastLanguageModel; import torch; print(f'✅ PyTorch {torch.__version__}, CUDA可用: {torch.cuda.is_available()}')"

echo ""
echo "安装完成！"
