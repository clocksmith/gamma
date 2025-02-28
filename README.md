# Interactive Language Models: Explore, Play, Visualize

## TODO
    - make "qqq" auto <eos>
    - Figure out slow down at 50ish encode steps
    - Features:
        - Add highlighting for current setence of attention
        - toggle print statements
        - give more info in look ahead (tree of probabilities, etc)
        - give more context into what part of forward feed attention step it is on within the transformer
        - Add visuals for encoding steps happening in parallel
        - Use commutative property of  multiplication as exxamples as oppose to RNN


This project provides an interactive environment for exploring the behavior of large language models (LLMs). It allows you to experiment with different generation parameters, play a word-guessing game, and visualize the inner workings of top-k and top-p sampling. While currently focused on Google's Gemma models, the core concepts apply broadly to many other LLMs.

## Features

*   **Interactive Guessing Game:** Test your intuition against the language model! The script presents you with multiple-choice options for the next word, drawn from the model's top-k predictions.  Your score is tracked, providing a fun and engaging way to understand how LLMs predict text.

*   **Model Selection:** Easily switch between different Gemma models (`google/gemma-2b`, `google/gemma-2b-it`, `google/gemma-7b`, `google/gemma-9b`, and `google/gemma-9b-it`).

*   **Automatic Quantization (for 7b+):**  The script can use 4-bit quantization when loading models larger than `gemma-2b` models, such as `google/gemma-7b`, which need at least 32gb of ram, to prevent out-of-memory errors and performance degredation from memory/disk swapping, making it accessible on a wider range of hardware. This requires the `bitsandbytes` library.

## Prerequisites

*   Python 3.8+
*   `transformers` library
*   `torch` library
*   `bitsandbytes` library (required for `google/gemma-7b`)
*   `accelerate` library
*   `optimum` and `auto-gptq` (optional, for improved 4-bit quantization. Highly recommended for `google/gemma-7b`!)

## Installation
1.  **Install Dependencies based on Model Choice:**

    *   **For `google/gemma-2b` and `google/gemma-2b-it`:**

        ```bash
        pip install transformers torch accelerate
        ```

    *   **For `google/gemma-7b` (Recommended Installation):**

        ```bash
        pip install transformers torch accelerate bitsandbytes optimum auto-gptq
        ```
    *   **For `google/gemma-7b` (Minimum Installation):**
        ```bash
        pip install transformers torch accelerate bitsandbytes
        ```

2.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
3.  **Create and Activate a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

## Usage

1.  **Configure the Script (`game.py`):**

    *   **Model Parameters:**
        *   `model_name`: Select the Gemma model (e.g., `"google/gemma-2b"`, `"google/gemma-2b-it"`, `"google/gemma-7b"`).
        *   `max_decode_steps`:  Maximum number of tokens to generate.
        *   `top_k`:  The number of highest probability tokens to consider for sampling.
        *   `top_p`:  The cumulative probability threshold for nucleus sampling.
        *   `temperature`:  Controls the randomness of the generation (lower values = more deterministic, higher values = more creative).

    *   **Game Parameters:**
        *   `num_choices`:  Set the number of multiple-choice options for the guessing game.

2.  **Run the Script:**

    ```bash
    python game.py
    ```

    You'll be prompted to enter a starting sentence.  The script will then guide you through the guessing game.

## Examples

*   **Run with the 2b-it model, 4 choices, top_k=10, top_p=0.9, temperature=0.3, and 20 decode steps:**

    Modify `game.py` to set:

    ```python
    model_name = "google/gemma-2b-it"
    num_choices = 4
    max_decode_steps = 20
    top_k = 10
    top_p = 0.9
    temperature = 0.3
    ```

    Then run `python game.py`.

*   **Run with the 7b model, top_k=5, top_p=0.95, temperature=0.6, and 10 decode steps:**
      Modify `game.py` to set:

    ```python
    model_name = "google/gemma-7b"
    max_decode_steps = 10
    top_k = 5
    top_p = 0.95
    temperature = 0.6
    ```
     Then run `python game.py`.

* **Run gemma-2b with top-k = 50, top-p=0.9, temperature = 1.0**
    ```python
        model_name = "google/gemma-2b"
        max_decode_steps = 25
        top_k = 50
        top_p = 0.9
        temperature = 1.0
    ```
## Notes (transformer steps)

Tokenization (Software): Input text -> tokens (integer IDs). CPU, string manipulation, lookup tables. Numerical representation of text.

Embedding Lookup (Software & Hardware): Token IDs -> embedding vectors (from HBM on TPU). CPU initiates, TPU HBM provides access. Dense vector representation of tokens.

Positional Encoding Generation (Software/Hardware): Create/retrieve positional encoding vectors (CPU or TPU). Provides word order information.

Positional Encoding Addition (Hardware): Add encodings to embeddings (element-wise on TPU). Combines semantic and positional information.

Encoder Query Weight Matrix Multiplication (Hardware): Input × Wᵠ (TPU MXUs). (sequence_length, embedding_dim) × (embedding_dim, dₖ). Projects input to "query" space.

Encoder Key Weight Matrix Multiplication (Hardware): Input × Wᵏ (TPU MXUs). (sequence_length, embedding_dim) × (embedding_dim, dₖ). Projects input to "key" space.

Encoder Value Weight Matrix Multiplication (Hardware): Input × Wᵛ (TPU MXUs). (sequence_length, embedding_dim) × (embedding_dim, dᵥ). Creates "value" representation.

Query-Key Matrix Multiplication (Hardware): QKᵀ (TPU MXUs). (sequence_length, dₖ) × (dₖ, sequence_length). Computes raw attention scores.

Scaling (Hardware): QKᵀ / √dₖ (element-wise on TPU). Prevents large dot products.

Padding Mask Creation (Encoder) (Software): Create padding mask (CPU). Identifies padding tokens.

Padding Mask Application (Encoder) (Hardware): Add mask to scaled QKᵀ (element-wise on TPU). Disables attention to padding.

Softmax (Encoder Self-Attention) (Hardware): Softmax(masked, scaled QKᵀ) (row-wise on TPU). Attention weights (probabilities).

Attention-Value Matrix Multiplication (Hardware): Softmax output × V (TPU MXUs). (sequence_length, sequence_length) × (sequence_length, dᵥ). Weighted sum of value vectors.

Multi-Head Concatenation (Hardware): Concatenate attention head outputs (TPU). Combines multiple attention perspectives.

Multi-Head Output Projection (Hardware): Concatenated output × Wᴼ (TPU MXUs). (sequence_length, h*dᵥ) × (h*dᵥ, embedding_dim). Projects back to embedding dimension.

Residual Addition (Encoder) (Hardware): Original input + attention output (element-wise on TPU). Aids gradient flow.

Layer Normalization (Encoder) (Hardware): Normalize the result (TPU). Stabilizes training.

Feed-Forward Layer 1 (Encoder) (Hardware): Normalized output × weight matrix (TPU MXUs). Non-linear transformation.

Add Bias 1 (Encoder FFN)(Hardware): Adds the first bias vector. Affine transformation

Activation (Encoder) (Hardware): Apply activation (e.g., GeLU) (element-wise on TPU). Introduces non-linearity.

Feed-Forward Layer 2 (Encoder) (Hardware): Activated output × weight matrix (TPU MXUs). Further processing.

Add Bias 2 (Encoder FFN)(Hardware): Adds the second bias term. Increases flexibility

Residual Addition (Encoder) (Hardware): Feed-forward input + output (element-wise on TPU). Aids gradient flow.

Layer Normalization (Encoder) (Hardware): Normalize (TPU). Final encoder layer normalization.

Decoder Input Embedding (Software & Hardware): Start token or previous tokens -> embeddings (CPU, TPU HBM). Initializes decoder input.

Decoder Query Weight Matrix Multiplication (Hardware): Similar to Step 5, but for decoder (TPU MXUs). Decoder "query" space.

Decoder Key Weight Matrix Multiplication (Hardware): Similar to Step 6, but for decoder (TPU MXUs). Decoder "key" space.

Decoder Value Weight Matrix Multiplication (Hardware): Similar to Step 7, but for decoder (TPU MXUs). Decoder "value" representation.

Query-Key Matrix Multiplication (Decoder) (Hardware): Similar to Step 8, but for decoder (TPU MXUs). Decoder raw attention scores.

Scaling (Decoder) (Hardware): Similar to Step 9, but for decoder (TPU). Prevents large dot products (decoder).

Attention Mask Creation (Decoder) (Software): Create attention mask (CPU) for autoregressive masking. Blocks future tokens.

Padding Mask Creation (Decoder) (Software): Create padding mask (CPU) if needed. Handles padding in decoder.

Mask Application (Decoder) (Hardware): Add attention + padding masks to scaled QKᵀ (element-wise on TPU). Applies masks.

Softmax (Decoder Self-Attention) (Hardware): Softmax(masked, scaled QKᵀ) (row-wise on TPU). Decoder self-attention probabilities.

Attention-Value Matrix Multiplication (Decoder) (Hardware): Softmax output × Value matrix (decoder) (TPU MXUs). Weighted sum (decoder values).

Multi-Head Concatenation (Decoder) (Hardware): Similar to Step 14, but for decoder (TPU). Combines decoder attention heads.

Multi-Head Output Projection (Decoder) (Hardware): Similar to Step 15, but for decoder (TPU MXUs). Projects decoder output.

Residual Addition (Decoder Self-Attention) (Hardware): Decoder input + attention output (element-wise on TPU). Decoder residual connection.

Layer Normalization (Decoder Self-Attention) (Hardware): Normalize (TPU). Decoder self-attention normalization.

Encoder Output Key Multiplication (Hardware): Final encoder output × Key weight matrix (Encoder-Decoder attention) (TPU MXUs). Encoder "key" for cross-attention.

Encoder Output Value Multiplication (Hardware): Final encoder output × Value weight matrix (Encoder-Decoder attention) (TPU MXUs). Encoder "value" for cross-attention.

Decoder Query - Encoder Key Multiplication (Hardware): Q (decoder) × K (encoder) (TPU MXUs). Cross-attention scores.

Scaling (Encoder-Decoder Attention)(Hardware): Divide by √dₖ (TPU). Prevents large dot products (cross-attention).

Padding Mask Application (Encoder-Decoder Attention) (Hardware): Add encoder padding mask (element-wise on TPU). Handles encoder padding in cross-attention.

Softmax (Encoder-Decoder Attention) (Hardware): Apply softmax (TPU). Cross-attention probabilities.

Attention-Value Multiplication (Encoder-Decoder Attention) (Hardware): Softmax output × Value matrix (encoder) (TPU MXUs). Weighted sum (encoder values).

Multi-Head Concatenation (Encoder-Decoder Attention) (Hardware): Concatenate heads (TPU). Combines cross-attention heads.

Multi-Head Output Projection (Encoder-Decoder Attention) (Hardware): Project output (TPU MXUs). Projects cross-attention output.

Residual Addition (Encoder-Decoder Attention) (Hardware): Input + cross-attention output (element-wise on TPU). Cross-attention residual connection.

Layer Normalization (Encoder-Decoder Attention) (Hardware): Normalize (TPU). Cross-attention normalization.

Feed-Forward Layer 1 (Decoder) (Hardware): Similar to Step 18, but for decoder (TPU MXUs). Decoder feed-forward (1).

Add Bias 1 (Decoder FFN)(Hardware): Adds first bias. Decoder bias 1

Activation (Decoder) (Hardware): Similar to Step 20, but for decoder (TPU). Decoder non-linearity.

Feed-Forward Layer 2 (Decoder) (Hardware): Similar to Step 21, but for decoder (TPU MXUs). Decoder feed-forward (2).

Add Bias 2 (Decoder FFN)(Hardware): Add second bias. Decoder bias 2

Residual Addition (Decoder) (Hardware): Similar to Step 23, but for decoder (TPU). Decoder feed-forward residual.

Layer Normalization (Decoder) (Hardware): Similar to Step 24, but for decoder (TPU). Final decoder normalization.

Final Linear Transformation (Hardware): Decoder output × final weight matrix (TPU MXUs). Projects to vocabulary size (logits).

Add final Bias(Hardware). Adds the final bias.

Repetition Penalty (Software/Hardware): Before softmax, we modify the logits based on previous tokens, by multiplying by a penalty factor < 1 if it was generated or > 1.

Temperature Scaling (Software/Hardware): Divide logits by temperature (TPU or CPU). Controls output randomness.

Softmax (Final Output) (Hardware): Apply softmax to logits (TPU). Creates probability distribution.

Top-k Filtering (Software): Select top k probabilities, set others to 0. (CPU, sorting, masking). Limits to k most likely.

Probability Masking for Top-k (Software): Sets to zero the probability of the non-top-k tokens.

Top-p Filtering (Software): Sum probabilities until threshold p is reached, set others to 0. (CPU, sorting, accumulation, masking). Dynamically selects tokens.

Probability Masking for Top-p (Software): Sets to zero the probability of the non-top-p tokens.

Renormalization (Software/Hardware): Renormalize the probabilities after Top-k/Top-p filtering to ensure they sum to 1 (CPU or TPU). Ensures a valid probability distribution.

Sampling (Software/Hardware): Sample a token ID based on the (modified) probabilities (CPU and/or TPU). Selects the next token.

Token-to-Text Conversion (Software): Token ID -> text (CPU, vocabulary lookup). Converts to human-readable text.