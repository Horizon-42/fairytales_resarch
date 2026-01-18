from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-4B"

# load the tokenizer and the model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

# prepare the model input
prompt = "Give me a short introduction to large language model."
messages = [
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# conduct text completion
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

# parsing thinking content
try:
    # rindex finding 151668 (</think>)
    index = len(output_ids) - output_ids[::-1].index(151668)
except ValueError:
    index = 0

thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

print("thinking content:", thinking_content)
print("content:", content)

# ================= 导出为Ollama格式 =================
import os
from pathlib import Path
from unsloth import FastLanguageModel

OUTPUT_DIR = "./models/exported"
OLLAMA_NAME = "qwen3-4b-baseline"

print("\n" + "=" * 60)
print("开始导出为Ollama格式")
print("=" * 60)

# 1. 先保存模型和tokenizer
print(f"💾 正在保存模型到: {OUTPUT_DIR}...")
os.makedirs(OUTPUT_DIR, exist_ok=True)
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✅ 模型已保存")

# 2. 使用unsloth转换为GGUF
print(f"🔄 正在转换为GGUF格式...")
try:
    # 用unsloth加载已保存的模型（从本地路径）
    export_model, export_tokenizer = FastLanguageModel.from_pretrained(
        model_name=OUTPUT_DIR,  # 从本地路径加载
        max_seq_length=2048,
        load_in_4bit=False,  # 已经加载的模型不需要再量化
    )
    
    # 设置为推理模式
    FastLanguageModel.for_inference(export_model)
    
    # 导出为GGUF
    export_model.save_pretrained_gguf(
        OUTPUT_DIR,
        export_tokenizer,
        quantization_method="q4_k_m",
    )
    
    print(f"✅ GGUF模型已导出到: {OUTPUT_DIR}")
    
    # 3. 创建Modelfile并导入Ollama
    output_path = Path(OUTPUT_DIR)
    gguf_files = list(output_path.glob("*.gguf"))
    
    if gguf_files:
        gguf_file = gguf_files[0]
        modelfile_path = output_path / "Modelfile"
        modelfile_content = f"""FROM {gguf_file.absolute()}

# Model exported from Qwen3-4B
PARAMETER temperature 0.7
PARAMETER top_p 0.8
PARAMETER top_k 20
"""
        modelfile_path.write_text(modelfile_content, encoding="utf-8")
        print(f"✅ Modelfile已创建: {modelfile_path}")
        
        # 导入到Ollama
        import subprocess
        print(f"📦 正在导入到Ollama (模型名称: {OLLAMA_NAME})...")
        try:
            subprocess.run(
                ["ollama", "create", OLLAMA_NAME, "-f", str(modelfile_path)],
                check=True,
            )
            print(f"✅ 模型已成功导入到Ollama: {OLLAMA_NAME}")
            print(f"🚀 现在可以使用: ollama run {OLLAMA_NAME}")
        except FileNotFoundError:
            print(f"⚠️  找不到ollama命令，请手动导入:")
            print(f"   ollama create {OLLAMA_NAME} -f {modelfile_path}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  导入失败，请手动导入:")
            print(f"   ollama create {OLLAMA_NAME} -f {modelfile_path}")
    else:
        print(f"⚠️  未找到GGUF文件，请检查导出过程")
        
except Exception as e:
    print(f"❌ 导出失败: {e}")
    import traceback
    traceback.print_exc()
