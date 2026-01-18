# GPU 问题排查指南

## 模型下载位置

模型已成功下载到：
```
~/.cache/huggingface/hub/models--unsloth--Qwen3-8B-unsloth-bnb-4bit/
```

大小：约 13.93 GB（4-bit 量化版本）

## 当前问题

**Unsloth 无法找到 GPU**，错误信息：
```
Unsloth cannot find any torch accelerator? You need a GPU.
CUDA available: False
```

## 解决方案

### 方案 1：检查 GPU 驱动（推荐）

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 如果 nvidia-smi 失败，需要安装/更新驱动
# Ubuntu/Debian:
sudo apt update
sudo apt install nvidia-driver-xxx  # 替换 xxx 为最新版本号

# 检查 CUDA 是否可用
conda run -n nlp python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

### 方案 2：使用 CPU 训练（不推荐，非常慢）

Unsloth 主要设计用于 GPU。如果必须使用 CPU：

1. **使用 transformers 而不是 unsloth**（需要修改代码）
2. **使用更小的模型**（如 Qwen3-4B）
3. **预期训练时间**：可能需要数天甚至数周

### 方案 3：使用云 GPU（推荐用于训练）

- Google Colab（免费 GPU）
- Kaggle（免费 GPU）
- AWS/GCP/Azure（付费）

### 方案 4：检查 CUDA 环境

```bash
# 检查 CUDA 版本
nvcc --version

# 检查 PyTorch CUDA 版本
conda run -n nlp python -c "import torch; print(torch.version.cuda)"

# 如果版本不匹配，重新安装 PyTorch
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

## 验证 GPU 可用性

运行以下命令验证：

```bash
conda run -n nlp python -c "
import torch
print('PyTorch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA version:', torch.version.cuda)
    print('GPU count:', torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}:', torch.cuda.get_device_name(i))
"
```

## 模型位置说明

HuggingFace 模型缓存位置：
- **Linux**: `~/.cache/huggingface/hub/`
- **Windows**: `C:\Users\<username>\.cache\huggingface\hub\`
- **macOS**: `~/.cache/huggingface/hub/`

可以通过环境变量 `HF_HOME` 自定义：
```bash
export HF_HOME=/path/to/custom/cache
```

## 下一步

1. **如果有 GPU**：修复 CUDA 驱动/环境配置
2. **如果没有 GPU**：考虑使用云 GPU 服务
3. **如果必须本地 CPU**：需要大幅修改代码，使用标准 transformers 而不是 unsloth
