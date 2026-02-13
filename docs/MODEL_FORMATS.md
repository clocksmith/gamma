# Model Formats & Engines

| Engine            | Model Formats                      | Inference Library          | Notes                                  |
|-------------------|------------------------------------|----------------------------|----------------------------------------|
| PyTorch           | HF Transformers (`.bin`, `.safetensors`) | `torch`, `transformers`    | Optional `bitsandbytes`/`accelerate`   |
| PyTorch CUDA      | HF Transformers (`.bin`, `.safetensors`) | `torch`, `transformers`    | GPU accel; same formats as PyTorch     |
| MLX / MLX GPU     | MLX-format HF models               | `mlx`, `mlx-lm`            | Apple Silicon only                     |
| LlamaCpp          | GGUF                                | `llama-cpp-python`         | Metal/CUDA/Vulkan/CPU (build-dependent)|
| vLLM              | HF-style (`.bin`, `.safetensors`, AWQ, GPTQ) | `vllm`                     | CUDA required                          |
| ONNX              | ONNX + HF tokenizer                 | `onnxruntime`              | CPU/CUDA/CoreML/DirectML providers     |
| TensorFlow        | TensorFlow/Keras HF models          | `tensorflow`               | Limited LLM availability               |
| JAX/Flax          | HF Flax checkpoints                  | `jax`, `flax`              | CPU/TPU; some tracing issues           |
| Ollama            | Ollama server models (HTTP)         | `requests` to Ollama API   | Logits limited; not for game/mind-meld |
