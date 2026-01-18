# Ollama Performance Optimization Guide

## Are Ollama Models Quantized?

**Yes!** Ollama models use **GGUF format**, which are pre-quantized. When you run `ollama pull qwen3:8b`, you're downloading a quantized model (typically Q4_K_M or Q8_0).

## Quantization Levels

| Quant Type | Bits | Speed | Quality | Memory | Use Case |
|------------|------|-------|---------|--------|----------|
| **Q4_K_M** | ~4.5 | Fastest | Good | Smallest | Best for 8-16GB VRAM |
| **Q8_0** | 8 | Fast | Excellent | Medium | Close to full precision |
| **FP16** | 16 | Slower | Best | Largest | Maximum quality |

## Speed Optimization Strategies

### 1. Use More Aggressively Quantized Models

Check your current model's quantization:
```bash
ollama show qwen3:8b --modelfile
```

Try faster quantized variants if available:
- `qwen3:8b-q4` (Q4 quantization - faster but lower quality)
- `qwen3:8b-q8` (Q8 quantization - balanced)

### 2. Configure Runtime Optimizations

#### A. Environment Variables (Set Before Running Ollama)

Add to your `~/.bashrc` or set in terminal:
```bash
# KV cache quantization (saves memory, speeds up long contexts)
export OLLAMA_KV_CACHE_TYPE=q8_0  # or q4_0 for more aggressive

# Flash attention (faster attention computation)
export OLLAMA_FLASH_ATTENTION=1

# GPU layers (if you have GPU with limited VRAM)
# Set to number of layers to offload to GPU, rest on CPU
export OLLAMA_GPU_LAYERS=20  # Adjust based on your GPU VRAM

# Num threads (optimize CPU inference)
# Set to number of physical CPU cores
export OLLAMA_NUM_THREAD=8  # Example: 8 cores
```

#### B. Application-Level Options (Already Implemented)

In `scripts/run_full_pipeline_and_evaluate.py`, you can set:

```bash
# CPU threads - match to your physical cores
--num-thread 8

# Disable thinking mode (already disabled for qwen3 by default)
--disable-thinking

# Context size - reduce if you don't need long context
--num-ctx 4096  # Lower = faster, but less context

# Max tokens - set appropriately to avoid truncation
--num-predict 512  # For JSON responses
```

### 3. Model Selection

- **For Speed**: Use smaller models (`qwen3:4b` vs `qwen3:8b`) or more aggressive quantization
- **For Quality**: Use larger models or Q8_0/FP16 quantization

### 4. Hardware Considerations

| Hardware | Recommended Settings |
|----------|---------------------|
| **CPU-only (8+ cores)** | `--num-thread 8`, Q4_K_M models, `OLLAMA_NUM_THREAD=8` |
| **GPU (8-12GB VRAM)** | `OLLAMA_GPU_LAYERS=20-30`, Q4_K_M models |
| **GPU (16+ GB VRAM)** | `OLLAMA_GPU_LAYERS=all`, Q8_0 models |
| **Limited RAM** | Smaller models (4B), Q4_K_S quantization |

### 5. Pipeline-Specific Optimizations

For the `full_detection` pipeline:

1. **Pre-generate summaries** (already implemented) - avoids redundant calls
2. **Batch processing** - process multiple spans sequentially (not parallel) to avoid memory issues
3. **Set `num_predict` appropriately** - don't set too low (<256) to avoid truncation

### Example: Optimized Run Command

```bash
# Set environment variables first
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_NUM_THREAD=8  # Match your CPU cores

# Run pipeline with optimized settings
conda run -n nlp python scripts/run_full_pipeline_and_evaluate.py \
    --story-file story.txt \
    --ground-truth ground_truth.json \
    --model qwen3:8b \
    --num-thread 8 \
    --num-ctx 4096 \
    --num-predict 512
```

## Benchmarking

To measure performance improvements:

1. **Time total pipeline execution**
2. **Monitor token generation rate** (tokens/second)
3. **Check memory usage** during inference

Current implementation already includes timing in `story_processor.py` and `run_full_pipeline_and_evaluate.py`.

## Trade-offs

| Optimization | Speed Gain | Quality Loss | Memory Impact |
|--------------|------------|--------------|---------------|
| Q4 vs Q8 | ~2x faster | ~5-10% | ~50% less |
| KV cache quant | ~10-20% faster | Minimal | ~30% less |
| Flash attention | ~15-25% faster | None | Similar |
| More threads | ~20-40% faster | None | More CPU usage |
| Smaller model | ~2-3x faster | ~10-20% | ~50% less |

## Troubleshooting

- **Still slow?** Check if thinking mode is disabled (`--disable-thinking`)
- **Out of memory?** Use smaller models or more aggressive quantization
- **GPU not used?** Set `OLLAMA_GPU_LAYERS` appropriately
- **Low quality?** Use Q8_0 or larger models

## References

- [Ollama GGUF Documentation](https://ollama.com/docs/hub/gguf)
- [GGUF Quantization Guide](https://github.com/ggerganov/llama.cpp/discussions/406)
