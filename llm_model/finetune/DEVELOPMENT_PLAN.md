# Fine-tuning Module Development Plan

## 概述

本文档描述在 `llm_model/finetune` 中创建基于 unsloth 的微调模块的设计方案。该模块将对 `full_detection` pipeline 中除去 summary 之外的每个步骤进行独立微调。

## 目标

1. **模块化设计**：每个 pipeline 步骤都有独立的微调模块
2. **代码复用**：尽可能复用 `full_detection` 的 prompts 和逻辑，但不侵入修改 `full_detection`
3. **使用 unsloth**：利用 unsloth 进行高效的 LoRA/QLoRA 微调
4. **独立性**：微调模块不依赖修改 `full_detection` 的代码

## Pipeline 步骤（除去 Summary）

根据 `full_detection/pipeline.py` 和 `full_detection/chains.py`，需要微调的步骤包括：

1. **Character Recognition** (Step 1)
   - 输入：text_span, summary, existing_characters, story_context
   - 输出：JSON {doers, receivers, new_characters, notes}
   - Prompt: `build_character_recognition_prompt()` + `SYSTEM_PROMPT_CHARACTER_RECOGNITION`

2. **Instrument Recognition** (Step 2.5, 可选)
   - 输入：text_span, summary, doers
   - 输出：JSON {instrument, explanation}
   - Prompt: `build_instrument_prompt()` + `SYSTEM_PROMPT_INSTRUMENT`

3. **Relationship Deduction** (Step 3)
   - 输入：text_span, summary, doers, receivers, story_context
   - 输出：JSON {relationships: [{agent, target, relationship_level1, relationship_level2, sentiment}]}
   - Prompt: `build_relationship_prompt()` + `SYSTEM_PROMPT_RELATIONSHIP`

4. **Action Category Deduction** (Step 4)
   - 输入：text_span, summary, doers, receivers, instrument
   - 输出：JSON {category, type, context, status, function}
   - Prompt: `build_action_category_prompt()` + `SYSTEM_PROMPT_ACTION`

5. **STAC Analysis** (Step 5)
   - 输入：text_span, summary, story_context
   - 输出：JSON {situation, task, action, consequence}
   - Prompt: `build_stac_prompt()` + `SYSTEM_PROMPT_STAC`

6. **Event Type Classification** (Step 6)
   - 输入：text_span, summary, stac
   - 输出：JSON {event_type, description_general, description_specific}
   - Prompt: `build_event_type_prompt()` + `SYSTEM_PROMPT_EVENT_TYPE`

## 目录结构

```
llm_model/finetune/
├── __init__.py
├── README.md
├── config.py                    # 统一的训练配置
├── data_preparation.py          # 数据准备和格式化
├── base_trainer.py              # 基础训练器类
├── trainers/
│   ├── __init__.py
│   ├── character_trainer.py     # Character Recognition 微调
│   ├── instrument_trainer.py    # Instrument Recognition 微调
│   ├── relationship_trainer.py  # Relationship Deduction 微调
│   ├── action_trainer.py        # Action Category 微调
│   ├── stac_trainer.py          # STAC Analysis 微调
│   └── event_type_trainer.py    # Event Type 微调
├── utils/
│   ├── __init__.py
│   └── prompt_builder.py        # 复用 full_detection 的 prompt 构建逻辑
└── scripts/
    ├── prepare_data.py          # 数据准备脚本
    ├── train_all.py             # 批量训练所有步骤
    └── train_step.py            # 训练单个步骤的脚本
```

## 设计原则

### 1. 代码复用策略

**复用方式**：
- **导入复用**：直接 `from llm_model.full_detection.prompts import ...` 导入 prompt 函数和常量
- **逻辑复用**：在 `utils/prompt_builder.py` 中封装调用 `full_detection` prompt 函数的逻辑
- **数据结构复用**：使用与 `full_detection` 相同的数据结构（PipelineState, 输入输出格式）

**不侵入修改**：
- 不修改 `full_detection` 的任何文件
- 所有微调相关逻辑都在 `finetune/` 目录下
- 通过导入和封装实现复用，而非修改源文件

### 2. 模块化设计

**BaseTrainer 抽象类**：
```python
class BaseTrainer:
    """所有步骤训练器的基类"""
    - model_name: str
    - step_name: str
    - config: FineTuneConfig
    
    def build_prompt(self, input_data): ...  # 由子类实现
    def format_training_example(self, example): ...  # 转换为 instruction format
    def train(self): ...  # 使用 unsloth 进行训练
    def save_model(self, output_dir): ...
```

**各步骤训练器**：
- 继承 `BaseTrainer`
- 实现 `build_prompt()` 方法，调用 `full_detection` 的对应 prompt 函数
- 实现 `format_training_example()` 方法，将数据转换为训练格式

### 3. 数据格式

**训练数据格式**（每个步骤）：
```json
{
  "instruction": "系统提示 + 任务描述",
  "input": "格式化的输入文本（基于 full_detection 的 prompt）",
  "output": "期望的 JSON 输出"
}
```

**数据来源**：
- 从已标注的 JSON 文件中提取每个步骤的输入输出对
- 使用 `full_detection` 的逻辑重建输入格式（text_span, summary, 等）
- 从 JSON 标注中提取期望的输出（doers, relationships, action_layer, 等）

## 实现细节

### 1. Prompt 复用 (`utils/prompt_builder.py`)

```python
"""封装 full_detection 的 prompt 构建逻辑"""

from llm_model.full_detection.prompts import (
    SYSTEM_PROMPT_CHARACTER_RECOGNITION,
    build_character_recognition_prompt,
    # ... 其他 prompts
)

def build_character_prompt_for_training(
    text_span: str,
    summary: str,
    existing_characters: List[Dict],
    story_context: Optional[str] = None
) -> str:
    """为训练构建 character recognition prompt"""
    system_prompt = SYSTEM_PROMPT_CHARACTER_RECOGNITION
    user_prompt = build_character_recognition_prompt(
        text_span=text_span,
        summary=summary,
        existing_characters=existing_characters,
        story_context=story_context
    )
    # 组合为训练格式的 instruction
    return f"{system_prompt}\n\n{user_prompt}"

# 类似的函数为其他步骤
```

### 2. 数据准备 (`data_preparation.py`)

```python
"""从标注数据中提取训练样本"""

def extract_character_examples(annotated_stories: List[Dict]) -> List[Dict]:
    """
    从标注的故事中提取 character recognition 训练样本
    
    Args:
        annotated_stories: 包含 narrative_events 的标注故事列表
    
    Returns:
        List of training examples: {
            "instruction": ...,
            "input": ...,
            "output": ...  # JSON string
        }
    """
    # 1. 遍历每个 story 的每个 narrative_event
    # 2. 从 event 中提取 text_span, summary, characters
    # 3. 使用 build_character_prompt_for_training 构建 input
    # 4. 从 event 中提取期望输出（agents, targets）
    # 5. 格式化为 training example
    ...

# 类似的函数为其他步骤
```

### 3. 基础训练器 (`base_trainer.py`)

```python
"""使用 unsloth 的基础训练器"""

from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

class BaseTrainer:
    def __init__(self, model_name: str, step_name: str, config: FineTuneConfig):
        self.model_name = model_name
        self.step_name = step_name
        self.config = config
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """使用 unsloth 加载模型"""
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=self.config.max_seq_length,
            dtype=None,  # Auto detection
            load_in_4bit=True,  # 4bit quantization
        )
        
        # 应用 LoRA
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=self.config.lora_r,
            target_modules=self.config.target_modules,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            use_gradient_checkpointing=True,
        )
    
    def format_training_example(self, example: Dict) -> str:
        """
        将训练样本格式化为模型输入格式
        
        格式: <|im_start|>system
        {instruction}<|im_end|>
        <|im_start|>user
        {input}<|im_end|>
        <|im_start|>assistant
        {output}<|im_end|>
        """
        # 由子类实现具体格式
        raise NotImplementedError
    
    def train(self, train_dataset, eval_dataset=None):
        """执行训练"""
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            dataset_text_field="formatted_text",
            max_seq_length=self.config.max_seq_length,
            packing=False,
            args=TrainingArguments(
                per_device_train_batch_size=self.config.batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                warmup_steps=self.config.warmup_steps,
                num_train_epochs=self.config.num_epochs,
                learning_rate=self.config.learning_rate,
                fp16=not self.config.bf16,
                bf16=self.config.bf16,
                logging_steps=10,
                output_dir=f"./outputs/{self.step_name}",
                save_strategy="epoch",
                evaluation_strategy="epoch" if eval_dataset else "no",
            ),
        )
        
        trainer.train()
        
        # 保存模型
        self.model.save_pretrained(f"./models/{self.step_name}")
```

### 4. 步骤训练器示例 (`trainers/character_trainer.py`)

```python
"""Character Recognition 训练器"""

from llm_model.finetune.base_trainer import BaseTrainer
from llm_model.finetune.utils.prompt_builder import build_character_prompt_for_training

class CharacterTrainer(BaseTrainer):
    def build_prompt(self, text_span: str, summary: str, 
                     existing_characters: List[Dict], 
                     story_context: Optional[str] = None) -> str:
        """构建训练 prompt"""
        return build_character_prompt_for_training(
            text_span=text_span,
            summary=summary,
            existing_characters=existing_characters,
            story_context=story_context
        )
    
    def format_training_example(self, example: Dict) -> str:
        """格式化训练样本"""
        instruction = self.build_prompt(
            text_span=example["text_span"],
            summary=example["summary"],
            existing_characters=example.get("existing_characters", []),
            story_context=example.get("story_context")
        )
        
        input_text = ""  # instruction 已包含完整输入
        output_text = json.dumps(example["output"], ensure_ascii=False)
        
        # 格式化为基础模型的对话格式
        return self._format_chat(
            instruction=instruction,
            input_text=input_text,
            output_text=output_text
        )
    
    def _format_chat(self, instruction: str, input_text: str, output_text: str) -> str:
        """格式化为模型对话格式"""
        # 根据具体模型调整格式（Qwen, Llama, 等）
        ...
```

### 5. 配置管理 (`config.py`)

```python
"""统一的训练配置"""

from dataclasses import dataclass
from typing import List

@dataclass
class FineTuneConfig:
    """微调配置"""
    # 模型配置
    model_name: str = "unsloth/Qwen2.5-7B-Instruct"
    max_seq_length: int = 2048
    
    # LoRA 配置
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = None  # 默认: ["q_proj", "k_proj", "v_proj", "o_proj"]
    
    # 训练配置
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    learning_rate: float = 2e-4
    warmup_steps: int = 50
    
    # 其他
    bf16: bool = True  # 使用 bfloat16
    
    def __post_init__(self):
        if self.target_modules is None:
            # 根据模型自动选择
            if "qwen" in self.model_name.lower():
                self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
            else:
                self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
```

## 数据流程

### 1. 数据准备阶段

```
标注的 JSON 文件
  ↓
extract_character_examples()
  ↓
训练样本列表 [{instruction, input, output}, ...]
  ↓
format_training_example() (每个样本)
  ↓
格式化的文本（模型输入格式）
  ↓
保存为 JSONL 或 Dataset
```

### 2. 训练阶段

```
加载配置
  ↓
初始化 Trainer (CharacterTrainer, 等)
  ↓
load_model() (unsloth)
  ↓
加载训练数据
  ↓
train() (SFTTrainer)
  ↓
保存模型
```

## 使用示例

### 训练单个步骤

```python
from llm_model.finetune.config import FineTuneConfig
from llm_model.finetune.trainers.character_trainer import CharacterTrainer
from llm_model.finetune.data_preparation import extract_character_examples

# 准备数据
annotated_stories = load_annotated_stories()  # 从文件加载
train_examples = extract_character_examples(annotated_stories)

# 配置
config = FineTuneConfig(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    num_epochs=3,
    batch_size=4,
)

# 训练
trainer = CharacterTrainer(
    model_name=config.model_name,
    step_name="character_recognition",
    config=config
)
trainer.load_model()
trainer.train(train_examples)
```

### 批量训练所有步骤

```python
from llm_model.finetune.scripts.train_all import train_all_steps

config = FineTuneConfig(...)
train_all_steps(
    annotated_stories=annotated_stories,
    config=config,
    steps=["character", "relationship", "action", "stac", "event_type"]
)
```

## 依赖项

需要在 `llm_model/requirements.txt` 或单独的 `llm_model/finetune/requirements.txt` 中添加：

```
# Unsloth for efficient fine-tuning
unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
# 或者从 PyPI（如果有）
# unsloth

# Training dependencies
transformers>=4.40.0
trl>=0.8.0
peft>=0.8.0
datasets>=2.14.0
accelerate>=0.24.0

# Optional: for evaluation
scikit-learn
```

## 注意事项

1. **Prompt 一致性**：确保训练时使用的 prompt 格式与 `full_detection` 推理时完全一致
2. **数据质量**：确保从标注数据中提取的样本质量高，输出格式正确
3. **模型选择**：根据硬件资源选择合适的基础模型和 LoRA 配置
4. **验证集**：建议为每个步骤保留验证集以监控训练效果
5. **推理集成**：训练完成后，需要将微调模型集成到 `full_detection` 的推理流程中（可选，不影响现有代码）

## 后续工作

1. 实现各步骤的训练器
2. 实现数据准备和格式化逻辑
3. 添加训练脚本和 CLI
4. 添加评估脚本（可选）
5. 文档和示例

## 问题与待定

1. **模型格式**：确定使用的基础模型（Qwen, Llama, 等）和对话格式
2. **数据来源**：确定从哪些标注文件中提取训练数据
3. **评估指标**：如何评估每个步骤的微调效果（准确率、F1、等）
4. **推理集成**：是否需要在 `full_detection` 中添加使用微调模型的选项（需要在 `full_detection` 中添加代码，但可以通过配置开关控制）
