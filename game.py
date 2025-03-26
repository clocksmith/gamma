import torch
import random
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import os
import argparse

###########################################
# Model Configuration
###########################################
MODEL_NAME = "google/gemma-3-1b-it"  # Default model
TEMPERATURE = 0.7  # Temperature for softening logits distribution
TOP_K = 8  # Number of highest probability tokens to keep for top-k filtering
TOP_P = 0.95  # Cumulative probability threshold for top-p (nucleus) sampling
MAX_TOP_K_FOR_PROBS = (
    16  # Maximum number of tokens to display in probability visualization
)

###########################################
# Game Configuration
###########################################
MAX_DECODE_STEPS = 8  # Maximum number of tokens to predict
NUM_CHOICES = 4  # Number of options presented to the player
PERMUTATION_LENGTH = 4  # Number of tokens shown in each choice
SHOW_ATTENTION = True  # Whether to visualize attention patterns

###########################################
# Terminal Colors Configuration
###########################################
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Check if running in a terminal that supports ANSI color codes
# This helps with compatibility across different terminal environments
USE_COLORS = True
if os.name == "nt":  # Windows
    try:
        import colorama

        colorama.init()
    except ImportError:
        # Fallback for Windows without colorama
        if os.environ.get("TERM") != "xterm":
            USE_COLORS = False


def load_model_and_tokenizer(model_name):
    """
    Loads the language model and tokenizer from Hugging Face.

    Args:
        model_name: Name of the model to load from Hugging Face

    Returns:
        Tuple of (model, tokenizer)
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", attn_implementation="eager"
    )
    return model, tokenizer


def prepare_inputs(input_text, tokenizer, model):
    """
    Tokenizes the input text and prepares it for the model.

    Args:
        input_text: The text to tokenize
        tokenizer: The tokenizer to use
        model: The model to prepare inputs for

    Returns:
        Tuple of (input_ids, attention_mask)
    """
    encoded_input = tokenizer.encode_plus(input_text, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(model.device)
    attention_mask = encoded_input["attention_mask"].to(model.device)
    return input_ids, attention_mask


def apply_temperature(logits, temperature):
    """
    Applies temperature scaling to logits.

    Args:
        logits: Raw logits from the model
        temperature: Temperature value (higher = more random, lower = more deterministic)

    Returns:
        Temperature-scaled logits
    """
    return logits / temperature


def apply_top_k(logits, top_k):
    """
    Applies top-k filtering to logits.

    Args:
        logits: Logits to filter
        top_k: Number of highest probability tokens to keep

    Returns:
        Filtered logits with only top-k values preserved
    """
    top_k_values, top_k_indices = torch.topk(logits, top_k, dim=-1)
    filtered_logits = torch.full_like(logits, float("-inf"))
    filtered_logits.scatter_(-1, top_k_indices, top_k_values)
    return filtered_logits


def apply_top_p(logits, top_p):
    """
    Applies top-p (nucleus) filtering to logits.

    Args:
        logits: Logits to filter
        top_p: Cumulative probability threshold

    Returns:
        Filtered logits with tokens above cumulative probability threshold
    """
    sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
    cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)

    # Remove tokens with cumulative probability above threshold
    sorted_indices_to_remove = cumulative_probs > top_p

    # Shift indices to keep first token above threshold
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = 0

    # Apply filtering
    filtered_logits = sorted_logits.clone()
    filtered_logits[sorted_indices_to_remove] = float("-inf")

    # Convert back to original indices
    unsorted_filtered_logits = torch.full_like(logits, float("-inf"))
    unsorted_filtered_logits.scatter_(-1, sorted_indices, filtered_logits)
    return unsorted_filtered_logits


def get_top_tokens_and_probs(logits, tokenizer, k=None):
    """
    Gets the top tokens and their probabilities from logits.

    Args:
        logits: Logits to extract tokens from
        tokenizer: Tokenizer to decode token IDs
        k: Number of top tokens to return (optional)

    Returns:
        Tuple of (tokens, probabilities, token_indices)
    """
    probabilities = torch.softmax(logits, dim=-1)
    if k is not None:
        top_k_values, top_k_indices = torch.topk(probabilities, k, dim=-1)
    else:
        top_k_values, top_k_indices = torch.sort(probabilities, descending=True, dim=-1)

    top_k_tokens = []
    for token_id in top_k_indices[0]:
        token_text = tokenizer.decode([token_id.item()]).strip()

        # Handle special tokens
        if token_text == "":
            if token_id.item() == tokenizer.pad_token_id:
                token_text = "<pad> (padding token)"
            elif token_id.item() == tokenizer.eos_token_id:
                token_text = "<eos> (end of sequence token)"
            elif token_id.item() == tokenizer.bos_token_id:
                token_text = "<bos> (beginning of sequence token)"
            elif token_id.item() == tokenizer.mask_token_id:
                token_text = "<mask> (masked token placeholder)"
            else:
                token_text = f"<special_{token_id.item()}>"

        top_k_tokens.append(token_text)

    top_k_probs = top_k_values[0].tolist()
    return top_k_tokens, top_k_probs, top_k_indices


def color_print(text, color):
    """
    Prints text with specified color if terminal supports it.

    Args:
        text: Text to print
        color: ANSI color code to use
    """
    if USE_COLORS:
        print(color + text + RESET)
    else:
        print(text)


def wait_for_player():
    """
    Simple utility to pause and wait for player to press Enter.
    """
    input("\nPress Enter to continue...")


def get_attention_heatmap(outputs, input_ids, tokenizer):
    """
    Extracts attention weights from model outputs.

    Args:
        outputs: Model outputs containing attention weights
        input_ids: Input token IDs
        tokenizer: Tokenizer to decode token IDs

    Returns:
        Tuple of (input_tokens, normalized_attention_scores) or None if not available
    """
    # Check if attention weights are available
    if not hasattr(outputs, "attentions") or outputs.attentions is None:
        return None, None

    # Get the last layer attention weights
    last_layer_attentions = outputs.attentions[-1]

    # Average attention from all heads to the last token (next token prediction)
    attention_weights = last_layer_attentions[0, :, -1, :-1].mean(dim=0)

    if not isinstance(attention_weights, torch.Tensor):
        return None, None

    # Convert input IDs to tokens (excluding the last token)
    input_tokens = tokenizer.convert_ids_to_tokens(input_ids[0][:-1])
    attention_scores = attention_weights.tolist()

    # Normalize attention scores to 0-1 range for visualization
    max_attention = max(attention_scores) if attention_scores else 1.0
    normalized_attention = [(score / max_attention) for score in attention_scores]

    return input_tokens, normalized_attention


def color_attention_text(tokens, normalized_attention, reset_color=RESET):
    """
    Creates a colored text representation of attention weights.

    Args:
        tokens: Token texts
        normalized_attention: Normalized attention scores (0-1)
        reset_color: ANSI reset color code

    Returns:
        Tuple of (colored_text_output, heatmap_scale_description)
    """
    if tokens is None or normalized_attention is None:
        return "Sentence without attention visualization.", ""

    colored_tokens_output = []
    heatmap_scale_output = "Heatmap scale: 0 (low attention) to 1 (high attention)\n"

    # Terminal-agnostic approach for attention visualization
    for token_text, attention_score in zip(tokens, normalized_attention):
        token_text = token_text.replace(" ", "").replace("_", "")

        if USE_COLORS:
            # Use different intensities of magenta for visualization
            if attention_score < 0.2:
                color_code = f"\033[38;5;54m"  # Very light magenta
            elif attention_score < 0.4:
                color_code = f"\033[38;5;91m"  # Light magenta
            elif attention_score < 0.6:
                color_code = f"\033[38;5;127m"  # Medium magenta
            elif attention_score < 0.8:
                color_code = f"\033[38;5;164m"  # Bright magenta
            else:
                color_code = f"\033[38;5;201m"  # Intense magenta

            colored_token = f"{color_code}{token_text}{reset_color}"
        else:
            # Fallback for terminals without color support
            stars = "*" * int(attention_score * 5)
            colored_token = f"{token_text}{stars}"

        # Show normalized score
        colored_tokens_output.append(f"{colored_token} ({attention_score:.2f})")

    return " ".join(colored_tokens_output).replace("  ", " "), heatmap_scale_output


def generate_player_choices(tokenizer, logits, num_choices, permutation_length):
    """
    Generates multiple choices for the player to select from.

    Args:
        tokenizer: Tokenizer to decode token IDs
        logits: Filtered logits after all sampling steps
        num_choices: Number of choices to generate
        permutation_length: Number of tokens in each choice

    Returns:
        List of choice options (each containing token sequences)
    """
    # Get top tokens after all filtering steps
    top_tokens, top_probs, _ = get_top_tokens_and_probs(logits, tokenizer, k=TOP_K)

    # Sort tokens by probability
    token_prob_tuples = sorted(
        zip(top_tokens, top_probs), key=lambda x: x[1], reverse=True
    )
    top_tokens_sorted = [token for token, _ in token_prob_tuples]

    # The model's actual top choice (correct answer)
    top_choice = top_tokens_sorted[:permutation_length]
    choices = [top_choice]

    # Generate alternative choices by shuffling top tokens
    available_tokens = top_tokens[
        : permutation_length * 2
    ]  # Use more tokens for variety
    attempt_count = 0
    max_attempts = 100  # Prevent infinite loops

    while len(choices) < num_choices and attempt_count < max_attempts:
        # Create alternative choice by sampling from available tokens
        shuffled_tokens = random.sample(available_tokens, permutation_length)

        # Only add if this is a unique choice
        if shuffled_tokens not in choices:
            choices.append(shuffled_tokens)

        attempt_count += 1

    # Random shuffle choices so correct one isn't always first
    random.shuffle(choices)

    return choices, top_choice


def display_probabilities(
    tokenizer, logits_raw, logits_temp, logits_top_k, logits_top_p
):
    """
    Displays token probabilities at each filtering stage.

    Args:
        tokenizer: Tokenizer to decode token IDs
        logits_raw: Raw logits from model
        logits_temp: Logits after temperature scaling
        logits_top_k: Logits after top-k filtering
        logits_top_p: Logits after top-p filtering
    """
    # Raw logits (before any filtering)
    print("\n--- Probabilities (Before any filtering): ---")
    all_tokens, all_probs, _ = get_top_tokens_and_probs(
        logits_raw, tokenizer, k=MAX_TOP_K_FOR_PROBS
    )
    for token, prob in zip(all_tokens, all_probs):
        print(f"    {token}: {prob:.6f}")

    # After temperature scaling
    print("\n--- Probabilities (After Temperature): ---")
    temp_tokens, temp_probs, _ = get_top_tokens_and_probs(
        logits_temp, tokenizer, k=MAX_TOP_K_FOR_PROBS
    )
    for token, prob in zip(temp_tokens, temp_probs):
        print(f"    {token}: {prob:.6f}")

    # After top-k filtering
    print("\n--- Probabilities (After Top-k): ---")
    top_k_tokens, top_k_probs, _ = get_top_tokens_and_probs(
        logits_top_k, tokenizer, k=MAX_TOP_K_FOR_PROBS
    )
    for token, prob in zip(top_k_tokens, top_k_probs):
        print(f"    {token}: {prob:.6f}")

    # After top-p filtering (final distribution)
    print("\n--- Probabilities (After Top-p): ---")
    top_p_tokens, top_p_probs, _ = get_top_tokens_and_probs(
        logits_top_p, tokenizer, k=MAX_TOP_K_FOR_PROBS
    )
    for token, prob in zip(top_p_tokens, top_p_probs):
        print(f"    {token}: {prob:.6f}")


def process_player_guess(
    tokenizer,
    logits_raw,
    logits_temp,
    logits_top_k,
    logits_top_p,
    num_choices,
    permutation_length,
    current_sentence,
):
    """
    Handles the player's next token guess, including choice presentation and feedback.

    Args:
        tokenizer: Tokenizer to decode token IDs
        logits_raw: Raw logits from model
        logits_temp: Logits after temperature scaling
        logits_top_k: Logits after top-k filtering
        logits_top_p: Logits after top-p filtering
        num_choices: Number of choices to present
        permutation_length: Number of tokens in each choice
        current_sentence: Current generated text

    Returns:
        Tuple of (score, max_score, is_perfect)
    """
    # Generate choices for the player
    choices, correct_sequence = generate_player_choices(
        tokenizer, logits_top_p, num_choices, permutation_length
    )

    # Present choices to the player
    print(f"\n🎮 Predict what Gemma will choose next to complete this sentence:")
    print(f'\n"{current_sentence}..."')
    print(f"\nGuess which sequence Gemma ranked highest after all filtering steps:")

    for i, choice_tokens in enumerate(choices):
        formatted_choice = " ".join(choice_tokens)
        print(f"  {chr(ord('A') + i)}) {formatted_choice}")

    # Get player's choice
    while True:
        valid_choices_str = "".join([chr(ord("A") + i) for i in range(len(choices))])
        user_choice = (
            input(f"\nYour choice (enter {', '.join(valid_choices_str)}): ")
            .strip()
            .upper()
        )
        if user_choice and user_choice in valid_choices_str:
            break
        else:
            print(
                f"Invalid input. Please choose a letter from {', '.join(valid_choices_str)}."
            )

    chosen_index = ord(user_choice) - ord("A")
    chosen_tokens = choices[chosen_index]

    # Evaluate player's answer
    score = 0
    max_score = permutation_length
    for i in range(max_score):
        if (
            i < len(chosen_tokens)
            and i < len(correct_sequence)
            and chosen_tokens[i] == correct_sequence[i]
        ):
            score += 1

    is_perfect = score == max_score

    # Show results with pauses for better player experience
    print("\n🎲 Checking your answer...")
    time.sleep(1)

    color_print(
        f"\nYou chose: {' '.join(chosen_tokens)}", GREEN if is_perfect else BLUE
    )

    time.sleep(0.5)

    color_print(f"Gemma's choice: {' '.join(correct_sequence)}", GREEN)

    time.sleep(0.5)

    if is_perfect:
        color_print("✅ Perfect! You matched Gemma's prediction exactly!", GREEN)
    else:
        color_print(
            f"⚠️ Close! You matched {score} out of {max_score} tokens correctly.", YELLOW
        )

    # Wait for player to acknowledge before showing detailed probabilities
    wait_for_player()

    # Show detailed token probabilities at each stage
    display_probabilities(
        tokenizer, logits_raw, logits_temp, logits_top_k, logits_top_p
    )

    return score, max_score, is_perfect


def explain_transformer_steps():
    """
    Provides a more detailed explanation of Transformer architecture steps.
    """
    print("\n--- Deep Dive into Transformer Steps ---")
    print(
        "Let's break down what happens inside Gemma when it predicts the next token:\n"
    )

    print("1. **Tokenization & Embedding:**")
    print(
        "   - First, your input text is converted into tokens, which are just numbers the model understands."
    )
    print(
        "   - Then, each token is transformed into an 'embedding' - a vector that represents its meaning."
    )
    print("   - Think of embeddings as rich numerical representations of words.\n")

    print("2. **Positional Encoding:**")
    print(
        "   - Since Transformers don't inherently know word order (unlike reading left-to-right),"
    )
    print(
        "   - 'Positional encodings' are added to the embeddings. These are special vectors"
    )
    print("   - that tell the model the position of each word in the sentence.\n")

    print("3. **Attention Mechanism (Multi-Head):**")
    print(
        "   - This is the core of the Transformer!  The model uses 'attention' to focus on"
    )
    print(
        "   - the most relevant parts of the input sentence when predicting the next word."
    )
    print(
        "   - 'Multi-Head' means this attention process happens in parallel multiple times ('heads'),"
    )
    print(
        "   - allowing the model to capture different kinds of relationships between words.\n"
    )
    print("   - In each attention head, the model calculates:")
    print(
        "     - **Query, Key, Value matrices:** These are transformations of the input embeddings."
    )
    print(
        "     - **Attention Scores:** By comparing Queries and Keys, the model figures out"
    )
    print("       how much each word should 'attend' to other words.")
    print(
        "     - **Weighted Values:** These attention scores are used to weight the 'Value' vectors,"
    )
    print("       emphasizing the important words.\n")

    print("4. **Feed-Forward Networks:**")
    print(
        "   - After the attention layers, the processed information goes through 'Feed-Forward Networks'."
    )
    print(
        "   - These are like standard neural network layers that further analyze the information"
    )
    print(
        "   - learned by the attention mechanism, refining the model's understanding.\n"
    )

    print("5. **Residual Connections & Layer Normalization:**")
    print(
        "   - Throughout the Transformer, there are 'residual connections' that add the original input"
    )
    print("   - to the output of each layer. This helps with training deeper networks.")
    print(
        "   - 'Layer Normalization' is used to stabilize the activations within the network,"
    )
    print("   - making training more efficient and effective.\n")

    print("6. **Logits and Probabilities:**")
    print(
        "   - Finally, the Transformer outputs 'logits'. These are raw scores for each word in the vocabulary."
    )
    print(
        "   - A 'softmax' function is applied to these logits to convert them into probabilities,"
    )
    print("   - indicating how likely each word is to be the next token.\n")

    print("7. **Sampling (Temperature, Top-K, Top-P):**")
    print("   - To generate the next token, we use 'sampling techniques'.")
    print("   - 'Temperature' adjusts how random the generation is.")
    print(
        "   - 'Top-K' and 'Top-P' (Nucleus sampling) are methods to focus on the most probable tokens"
    )
    print(
        "     and make the generation more coherent and less likely to go off-topic.\n"
    )

    print(
        "In essence, the Transformer uses attention to understand the context of the input text,"
    )
    print(
        "processes this context through feed-forward networks, and then predicts the next word"
    )
    print("by choosing from a probability distribution over the vocabulary.\n")


def explain_attention_mechanism():
    """
    Provides an explanation of the attention mechanism for the player.
    """
    print("\n--- About Attention in Language Models ---")
    print(
        "Attention is a key mechanism in transformer-based language models like Gemma."
    )
    print(
        "It determines how much focus each input token gets when predicting the next token."
    )
    print("")
    print("In the visualization:")
    print(
        "1. Higher attention (darker magenta) indicates tokens the model focused on more"
    )
    print(
        "2. Lower attention (lighter magenta) indicates tokens the model considered less relevant"
    )
    print(
        "3. The values show normalized attention (0-1 scale), where 1 means maximum focus"
    )
    print("")
    print(
        "Attention works by calculating relationships between all tokens in the sequence."
    )
    print(
        "During the forward pass, the model computes query, key, and value vectors for each token,"
    )
    print("then calculates compatibility scores between them to determine importance.")
    print("")
    print(
        "The normalized attention shown here is averaged across all attention heads in the"
    )
    print(
        "final layer, focused specifically on what influenced the next token prediction."
    )
    print("")
    print(
        "This visualization helps you understand which parts of your input most strongly"
    )
    print("influenced Gemma's token predictions.")
    print(
        "\nFor a more detailed explanation of the Transformer architecture, choose 'Explain Transformer Steps' from the main menu."
    )


def run_game(cli_model_name=None):
    """
    Main game function that coordinates the token prediction game.
    """

    gemma_models = [
        "google/gemma-3-1b-it",
        "google/gemma-3-4b-it",
        "google/gemma-3-12b-it",
        "google/gemma-3-27b-it",
        "google/gemma-3-1b",
        "google/gemma-3-4b",
        "google/gemma-3-12b",
        "google/gemma-3-27b",
        "google/gemma-2-2b-it",
        "google/gemma-2-7b-it",
        "google/gemma-2-9b-it",
        "google/gemma-2-2b",
        "google/gemma-2-7b",
        "google/gemma-2-9b",
    ]

    print("\n" + "=" * 70)
    print("🤖 Welcome to the LLM Next Token Prediction Game! 🎮")
    print("=" * 70)
    print("\nTest your ability to predict what Gemma will generate next!")
    print("You'll see a sentence and need to guess which tokens Gemma would choose.")

    print("\nAvailable Gemma Models:")
    for i, model_name in enumerate(gemma_models):
        print(f"  {i+1}) {model_name}")

    while True:
        model_choice_str = input(
            f"\nChoose a Gemma model (1-{len(gemma_models)}, default is 1): "
        ).strip()
        if not model_choice_str:
            model_index = 0  # Default to the first model in the list
            break
        try:
            model_index = int(model_choice_str) - 1
            if 0 <= model_index < len(gemma_models):
                break
            else:
                print(
                    f"Invalid choice. Please enter a number between 1 and {len(gemma_models)}."
                )
        except ValueError:
            print("Invalid input. Please enter a number.")

    selected_model_name = gemma_models[model_index]

    print("\nConfiguration:")
    print(f"• Model: {selected_model_name}")
    print(
        f"• Temperature: {TEMPERATURE} (higher = more random, lower = more deterministic)"
    )
    print(f"• Top-k: {TOP_K} (restricts to top k most probable tokens)")
    print(
        f"• Top-p: {TOP_P} (restricts to tokens comprising top p% of probability mass)"
    )
    print(f"• Decode Steps: {MAX_DECODE_STEPS} (how many rounds we'll play)")
    print("\nLet's get started!")

    # Load model and tokenizer
    model, tokenizer = load_model_and_tokenizer(selected_model_name)

    # Get starting sentence from player
    input_text = input("\nStart a sentence (or press Enter for default): ").strip()
    if not input_text:
        input_text = "In the distant future, humanity had finally"
        print(f'Using default: "{input_text}"')

    # Prepare model inputs
    input_ids, attention_mask = prepare_inputs(input_text, tokenizer, model)

    # Initialize game state
    total_score = 0
    total_max_score = 0
    current_sentence = input_text
    attention_history = []

    # Explain attention mechanism if enabled
    if SHOW_ATTENTION:
        explain_attention_mechanism()
        wait_for_player()

    # Main game loop
    for step in range(MAX_DECODE_STEPS):
        print(f"\n{'='*30} Round {step + 1} {'='*30}")

        # Forward pass through the model
        start_time = time.time()
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=SHOW_ATTENTION,
        )
        forward_time = time.time() - start_time
        print(f"  ⚙️ Model forward pass: {forward_time:.4f}s")

        # Get logits for next token prediction
        logits_raw = outputs.logits[:, -1, :]

        # Apply temperature, top-k, and top-p filtering
        logits_temp = apply_temperature(logits_raw, TEMPERATURE)
        logits_top_k = apply_top_k(logits_temp, TOP_K)
        logits_top_p = apply_top_p(logits_top_k, TOP_P)

        # Visualize attention if enabled
        if SHOW_ATTENTION:
            current_tokens, normalized_attention_scores = get_attention_heatmap(
                outputs, input_ids, tokenizer
            )
            colored_sentence_part, heatmap_scale = color_attention_text(
                current_tokens, normalized_attention_scores
            )

            if colored_sentence_part:
                attention_history.append(colored_sentence_part)

                print("\n--- Attention Heatmap (Current Step) ---")
                print(heatmap_scale)
                print(f"Current sentence with attention: {colored_sentence_part}")

                if len(attention_history) > 1:
                    print("\n--- Previous Attention Patterns: ---")
                    for i, past_attention in enumerate(attention_history[:-1]):
                        print(f"  Step {i + 1}: {past_attention}")

        # Process player's guess
        step_score, step_max_score, is_perfect = process_player_guess(
            tokenizer,
            logits_raw,
            logits_temp,
            logits_top_k,
            logits_top_p,
            NUM_CHOICES,
            PERMUTATION_LENGTH,
            current_sentence,
        )

        # Update score
        total_score += step_score
        total_max_score += step_max_score

        # Select the next token based on model prediction
        probabilities = torch.softmax(logits_top_p, dim=-1)
        _, best_token_indices = torch.topk(probabilities, 1, dim=-1)
        next_token_id = best_token_indices[0, 0].item()
        next_word = tokenizer.decode([next_token_id]).strip()

        # Check for special tokens
        special_token = ""
        if next_token_id == tokenizer.eos_token_id:
            special_token = " (<eos> End of sequence reached)"
            print(f"\n🏁 The model generated an end-of-sequence token.")
            print("Game completed early as the model thinks the text is complete.")
            break
        elif next_token_id == tokenizer.pad_token_id:
            special_token = " (<pad> Padding token)"
        elif next_word == "":
            special_token = f" (Special token ID: {next_token_id})"

        # Continue the sentence with the generated token
        current_sentence += " " + next_word
        print(f'\n📝 Continuing sentence: "{current_sentence}"{special_token}')

        # Update model inputs for next step
        input_ids = torch.cat(
            [input_ids, torch.tensor([[next_token_id]], device=model.device)], dim=-1
        )
        attention_mask = torch.cat(
            [
                attention_mask,
                torch.ones((attention_mask.shape[0], 1), device=model.device),
            ],
            dim=-1,
        )

        # Optional pause between rounds
        if step < MAX_DECODE_STEPS - 1:
            wait_for_player()

    # Game summary
    print("\n" + "=" * 70)
    print("🎮 Game Complete! 🎮")
    print("=" * 70)
    print(
        f'\n📝 Final generated text:\n"{tokenizer.decode(input_ids[0], skip_special_tokens=True)}"'
    )

    # Calculate and display final score
    score_percentage = (
        (total_score / total_max_score) * 100 if total_max_score > 0 else 0
    )
    print(
        f"\n🏆 Final Score: {total_score} / {total_max_score} ({score_percentage:.1f}%)"
    )

    if score_percentage >= 80:
        print("🌟 Excellent! You think very much like Gemma!")
    elif score_percentage >= 60:
        print(
            "✨ Great job! You have a good understanding of how language models work!"
        )
    elif score_percentage >= 40:
        print("👍 Not bad! You're getting the hang of predicting language models!")
    else:
        print("🎓 Good effort! Language models can be unpredictable - keep practicing!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Next Token Prediction Game")
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,  # Model selection is now interactive, remove default from here
        help="Model name to use (e.g., google/gemma-3-4b-it, google/gemma-2-7b-it)",
    )
    parser.add_argument(
        "-e",
        "--explain",
        action="store_true",
        help="Explain Transformer architecture steps before starting the game",
    )

    args = parser.parse_args()

    if args.explain:
        explain_transformer_steps()
        input("\nPress Enter to start the game...")

    run_game(args.model)
    print(open(__file__).read())
