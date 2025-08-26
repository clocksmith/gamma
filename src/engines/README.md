# Engine Implementations

This directory contains the concrete implementations of the `LLMEngine` interface defined in `core/engine_interface.py`.

Each file in this directory is a self-contained engine for a specific machine learning framework (e.g., PyTorch, TensorFlow, JAX). The purpose of each engine is to act as an **adapter** between its specific framework and the common interface expected by the main application.

## Responsibilities of an Engine:

- **Model Loading**: Loading the model and tokenizer for its specific framework.
- **Prediction**: Implementing the `predict_next` method, which runs the model's forward pass to get logits and other outputs.
- **Data Type Conversion**: Converting data types between the framework's native tensors (e.g., `torch.Tensor`, `tf.Tensor`) and standard Python/NumPy types where necessary.
- **State Management**: Managing the Key-Value (KV) cache for its model.

## Engine Factory:

- **`engine_factory.py`**: This module is responsible for instantiating the correct engine based on the user's command-line arguments (e.g., `--engine pytorch`).
