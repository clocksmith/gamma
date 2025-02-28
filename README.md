# Interactive Language Models: Explore, Play, Visualize

## TODO
    - make "qqq" auto <eos>
    - Figure out slow down at 50ish encode steps
    - Features:
        - Add highlighting for current setence of attention
        - toggle print statements
        - give more info in look ahead
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

## File Structure (For Developers)

*   **`game.py`:**  Contains the main script for the interactive word-guessing game, including user input, model interaction, and output display. It orchestrates the overall flow of the application.
*   **`utils.py`:**  Provides utility functions for model loading, applying sampling techniques (temperature, top-k, top-p), and preparing input data. This promotes code reusability and separation of concerns.
*   **`viz.py`:** This file is no longer used in the current implementation. The visualization has been integrated into `game.py`.