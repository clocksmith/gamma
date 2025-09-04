# Engine Framework

GAMMA uses a modular engine architecture that allows the core game logic to interact with models running on different machine learning frameworks. This makes the tool highly extensible and allows users to select the backend that best suits their hardware and the models they wish to explore.

Each engine is an implementation of the `LLMEngine` interface defined in `src/core/engine_interface.py`.

## Supported Frameworks

The following engines are supported:

- **PyTorch** (`pytorch_engine.py`): The default and most feature-rich engine, recommended for Gemma and other Hugging Face models.
- **TensorFlow** (`tensorflow_engine.py`): For models available in the TensorFlow/Keras ecosystem.
- **JAX** (`jax_engine.py`): For models implemented in JAX, often used for research and high-performance computing.
- **ONNX Runtime** (`onnx_engine.py`): For models that have been converted to the Open Neural Network Exchange (ONNX) format, which can offer performance benefits.
- **llama.cpp** (`llama_cpp_engine.py`): A highly optimized engine for running GGUF-formatted models (like Llama) efficiently on a CPU.
- **MLX** (`mlx_engine.py`): An engine for running models on Apple Silicon, leveraging Apple's MLX framework for unified memory and optimized performance.