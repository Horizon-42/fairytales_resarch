# Fine-tuning Training Commands

## 快速开始

### 1. 准备训练数据（如果还没有）

```bash
# 从合成数据准备训练数据
conda run -n nlp python -m llm_model.finetune.scripts.extract_training_data \
    --synthetic \
    --groundtruth-dir synthetic_datasets/groundtruth \
    --generated-stories-dir synthetic_datasets/generated_stories \
    --output-dir training_data
```

### 2. 测试训练流程（Mock）

在开始实际训练前，建议先运行 mock 测试验证流程：

```bash
# 测试单个 step
conda run -n nlp python -m llm_model.finetune.scripts.mock_train_step \
    --step character \
    --data-dir training_data \
    --output-dir ./mock_test_results

# 测试多个 step
conda run -n nlp python -m llm_model.finetune.scripts.mock_train_step \
    --step character action relationship \
    --data-dir training_data \
    --output-dir ./mock_test_results

# 测试所有 step
conda run -n nlp python -m llm_model.finetune.scripts.mock_train_step \
    --step all \
    --data-dir training_data \
    --output-dir ./mock_test_results
```

### 3. 开始微调

#### 训练单个 step

```bash
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step character \
    --data-dir training_data \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```

#### 训练多个 step

```bash
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step character action relationship \
    --data-dir training_data \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```

#### 训练所有 step

```bash
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step all \
    --data-dir training_data \
    --model-name unsloth/Qwen2.5-7B-Instruct \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```

## 参数说明

- `--step`: 要训练的 step(s)，可以是单个、多个或 `all`
- `--data-dir`: 训练数据目录（包含 `{step}_train.jsonl` 文件）
- `--model-name`: 基础模型名称（默认: `unsloth/Qwen2.5-7B-Instruct`）
- `--output-dir`: 模型输出目录（默认: `./models`）
- `--num-epochs`: 训练轮数（默认: 3）
- `--batch-size`: 批次大小（默认: 4）
- `--learning-rate`: 学习率（默认: 2e-4）
- `--train-split`: 训练/验证集分割比例（默认: 0.9）
- `--no-evaluate`: 跳过训练后评估
- `--no-use-jsonl`: 从 JSON 故事文件提取数据（而不是从 JSONL 加载）

## 输出文件

训练完成后，每个 step 会在 `{output_dir}/{step_name}/` 目录下生成：

- `loss_history.csv`: 训练 loss 历史（CSV 格式）
- `step_evaluation.json`: 单步评估结果（如果启用评估）
- `adapter_model.bin`: LoRA 权重
- `adapter_config.json`: LoRA 配置
- 其他模型文件

## 注意事项

1. **GPU 内存**: 确保有足够的 GPU 内存。如果内存不足，可以减小 `--batch-size` 或使用更小的模型
2. **训练时间**: 多个 step 会依次训练，总时间 = 单个 step 时间 × step 数量
3. **数据准备**: 确保 `training_data/` 目录下有对应的 `{step}_train.jsonl` 文件
4. **依赖安装**: 确保已安装 fine-tuning 依赖：
   ```bash
   pip install -r llm_model/finetune/requirements.txt
   ```

## 完整示例

```bash
# 1. 准备数据
conda run -n nlp python -m llm_model.finetune.scripts.extract_training_data \
    --synthetic \
    --groundtruth-dir synthetic_datasets/groundtruth \
    --generated-stories-dir synthetic_datasets/generated_stories \
    --output-dir training_data

# 2. Mock 测试
conda run -n nlp python -m llm_model.finetune.scripts.mock_train_step \
    --step all \
    --data-dir training_data

# 3. 开始训练（所有 step）
conda run -n nlp python -m llm_model.finetune.scripts.train_step \
    --step all \
    --data-dir training_data \
    --output-dir ./models \
    --num-epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-4
```
