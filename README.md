# Interactive Language Model Playground: Explore, Guess, and Visualize

This project provides an interactive environment for exploring the behavior of large language models (LLMs).  It allows you to experiment with different generation parameters, play a word-guessing game, and visualize the inner workings of top-k and top-p sampling. While currently focused on Google's Gemma models, the core concepts apply broadly to many other LLMs.

## Features

*   **Interactive Guessing Game:** Test your intuition against the language model! The script presents you with multiple-choice options for the next word, drawn from the model's top-k predictions.  Your score is tracked, providing a fun and engaging way to understand how LLMs predict text.

*   **Top-k, Top-p, and Temperature Visualization:** Gain a deeper understanding of how LLMs generate text by visualizing the probabilities assigned to different words at each step. See how the `top_k`, `top_p`, and `temperature` parameters influence these probabilities.

*   **Model Selection:** Easily switch between different Gemma models (`google/gemma-2b`, `google/gemma-2b-it`, and `google/gemma-7b`).

*   **Automatic Quantization (for 7b):**  The script automatically uses 4-bit quantization when loading the `google/gemma-7b` model to prevent out-of-memory errors, making it accessible on a wider range of hardware. This requires the `bitsandbytes` library.

*   **Adjustable Model Parameters:** Control the generation process with these parameters:
    *   `max_decode_steps`:  Maximum number of tokens to generate.
    *   `top_k`:  The number of highest probability tokens to consider for sampling.
    *   `top_p`:  The cumulative probability threshold for nucleus sampling.
    *   `temperature`:  Controls the randomness of the generation (lower values = more deterministic, higher values = more creative).

*   **Adjustable Game Parameters:**
    *   `nun_choices`: (Guessing Game) The number of multiple-choice options presented to the user.

*   **Clear Output:**  The script displays the evolving generated sentence, your guesses, the correct answers, and your score (in guessing game mode). When the guessing game is disabled, it shows the top-k/top-p visualization.

## Prerequisites

*   Python 3.8+
*   `transformers` library
*   `torch` library
*   `bitsandbytes` library (required for `google/gemma-7b`)
*   `accelerate` library
*   `optimum` and `auto-gptq` (optional, for improved 4-bit quantization. Highly recommended for `google/gemma-7b`!)

## Installation

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install Required Libraries:**

    ```bash
    pip install transformers torch accelerate bitsandbytes
    ```

4.  **Optional (Highly Recommended):** Install `optimum` and `auto-gptq` for enhanced 4-bit quantization, which is particularly beneficial for larger models like `google/gemma-7b`.

    ```bash
    pip install optimum auto-gptq
    ```

## Usage

1.  **Configure the Script (`game.py`):**

    *   **`model_name`:**  Select the Gemma model (e.g., `"google/gemma-2b"`, `"google/gemma-2b-it"`, `"google/gemma-7b"`).
    *   **`GUESS_NEXT_WORD`:**  Enable (`True`) or disable (`False`) the guessing game.  If disabled, you'll see the top-k/top-p visualization.
    *   **`NUM_CHOICES`:**  Set the number of multiple-choice options for the guessing game.
    *   **`max_decode_steps`**, **`top_k`**, **`top_p`**, **`temperature`:**  Adjust these parameters to experiment with different generation styles.

2.  **Run the Script:**

    ```bash
    python game.py
    ```

    You'll be prompted to enter a starting sentence.  The script will then either guide you through the guessing game or display the top-k/top-p visualization, depending on your configuration.

## Examples

TODO