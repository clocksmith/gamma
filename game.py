import torch
import random
from transformers import AutoTokenizer, AutoModelForCausalLM
import time

# Configuration
model_name = "google/gemma-2b-it"
max_decode_steps = 12
top_k = 8  # Top-k for initial candidate selection
top_p = 0.95  # Top-p for actual sampling
temperature = 0.7  # Temparature for model
num_choices = 3  # Number of choices presented to the user
permutation_length = 3  # How many tokens to show in each choice
show_attention = True  # Enable/disable attention visualization
max_top_k_for_probs = 16  # Limit tokens for probability display

# Colors for terminal prints
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


def load_model_and_tokenizer(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", attn_implementation="eager"
    )
    return model, tokenizer


def apply_temperature(logits, temperature):
    return logits / temperature


def apply_top_k(logits, top_k):
    top_k_values, top_k_indices = torch.topk(logits, top_k, dim=-1)
    filtered_logits = torch.full_like(logits, float("-inf"))
    filtered_logits.scatter_(-1, top_k_indices, top_k_values)
    return filtered_logits


def apply_top_p(logits, top_p):
    sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
    cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
    sorted_indices_to_remove = cumulative_probs > top_p
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = 0
    filtered_logits = sorted_logits.clone()
    filtered_logits[sorted_indices_to_remove] = float("-inf")

    # Convert back to original indices
    unsorted_filtered_logits = torch.full_like(logits, float("-inf"))
    unsorted_filtered_logits.scatter_(-1, sorted_indices, filtered_logits)
    return unsorted_filtered_logits


def get_top_tokens_and_probs(logits, tokenizer, k=None):
    probabilities = torch.softmax(logits, dim=-1)
    if k is not None:
        top_k_values, top_k_indices = torch.topk(probabilities, k, dim=-1)
    else:
        top_k_values, top_k_indices = torch.sort(probabilities, descending=True, dim=-1)

    top_k_tokens = [
        tokenizer.decode([token_id.item()]).strip() for token_id in top_k_indices[0]
    ]
    top_k_probs = top_k_values[0].tolist()
    return top_k_tokens, top_k_probs, top_k_indices


def prepare_inputs(input_text, tokenizer, model):
    encoded_input = tokenizer.encode_plus(input_text, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(model.device)
    attention_mask = encoded_input["attention_mask"].to(model.device)
    return input_ids, attention_mask


def color_print(text, color):
    print(color + text + RESET)


def get_attention_heatmap(outputs, input_ids, tokenizer):
    if not hasattr(outputs, "attentions") or outputs.attentions is None:
        return None

    last_layer_attentions = outputs.attentions[-1]
    attention_weights = last_layer_attentions[0, :, -1, :-1].mean(dim=0)

    if not isinstance(attention_weights, torch.Tensor):
        return None

    averaged_attention = attention_weights
    input_tokens = tokenizer.convert_ids_to_tokens(input_ids[0][:-1])
    attention_scores = averaged_attention.tolist()
    max_attention = max(attention_scores) if attention_scores else 1.0
    # Normalized to 0-1
    normalized_attention = [(score / max_attention) for score in attention_scores]

    return (
        input_tokens,
        normalized_attention,
    )


def color_attention_text(
    tokens,
    normalized_attention,
    reset_color=RESET,
):
    if tokens is None or normalized_attention is None:
        return "Sentence without attention visualization.", ""

    colored_tokens_output = []
    heatmap_scale_output = "Heatmap scale: 0 (low attention) to 1 (high attention)\n"

    for token_text, attention_score in zip(tokens, normalized_attention):
        token_text = token_text.replace(" ", "").replace("_", "")
        normalized_score = attention_score

        # Linear interpolation for magenta: (255, 0, 255) at 1.0, (0, 0, 0) at 0.0
        red = int(255 * normalized_score)
        green = 0
        blue = int(255 * normalized_score)

        color_code_bg = f"\033[48;2;{red};{green};{blue}m"
        colored_token = f"{color_code_bg}{token_text}{reset_color}"
        # Show normalized score
        colored_tokens_output.append(f"{colored_token} ({normalized_score:.2f})")

    return " ".join(colored_tokens_output).replace("  ", " "), heatmap_scale_output


def guess_next_word_sequence(
    tokenizer,
    logits_raw,
    logits_temp,
    logits_top_k,
    logits_top_p,
    num_choices,
    top_n_tokens,
    permutation_length,
    current_ids,
    current_sentence,
    max_tokens_for_probs,
):
    """Generates choices, gets user input, and THEN shows probabilities."""

    # Prepare choices using tokens from after top_p
    top_p_tokens, top_p_probs, _ = get_top_tokens_and_probs(
        logits_top_p, tokenizer, k=max_top_k_for_probs
    )
    top_n_tokens_decoded = top_p_tokens[:top_n_tokens]
    top_n_probs_final = top_p_probs[:top_n_tokens]

    choices = []
    token_prob_tuples = sorted(
        zip(top_n_tokens_decoded, top_n_probs_final), key=lambda x: x[1], reverse=True
    )
    top_tokens_sorted = [token for token, _ in token_prob_tuples]
    top_choice = top_tokens_sorted[:permutation_length]
    choices.append(top_choice)

    while len(choices) < num_choices:
        shuffled_tokens = top_n_tokens_decoded[:permutation_length]
        random.shuffle(shuffled_tokens)
        if shuffled_tokens not in choices:
            choices.append(shuffled_tokens)

    random.shuffle(choices)

    print(f"\nGuess the next {permutation_length} words, completing the sentence:")
    for i, choice_tokens in enumerate(choices):
        formatted_choice = f"[[ {', '.join(choice_tokens)} ]]"
        print(f"  {chr(ord('a') + i)}) {current_sentence} {formatted_choice}")

    while True:
        user_choice = input("Your choice: ").strip().lower()
        if "a" <= user_choice <= chr(ord("a") + len(choices) - 1):
            break
        else:
            print("Invalid input.  Choose a letter from the choices.")
    chosen_index = ord(user_choice) - ord("a")
    chosen_tokens = choices[chosen_index]

    print("\n--- Probabilities (Before any filtering): ---")
    all_tokens, all_probs, _ = get_top_tokens_and_probs(
        logits_raw, tokenizer, k=max_tokens_for_probs
    )
    for token, prob in zip(all_tokens, all_probs):
        print(f"    {token}: {prob:.6f}")

    print("\n--- Probabilities (After Temperature): ---")
    temp_tokens, temp_probs, _ = get_top_tokens_and_probs(
        logits_temp, tokenizer, k=max_tokens_for_probs
    )
    for token, prob in zip(temp_tokens, temp_probs):
        print(f"    {token}: {prob:.6f}")

    print("\n--- Probabilities (After Top-k): ---")
    top_k_tokens, top_k_probs, _ = get_top_tokens_and_probs(
        logits_top_k, tokenizer, k=max_tokens_for_probs
    )
    for token, prob in zip(top_k_tokens, top_k_probs):
        print(f"    {token}: {prob:.6f}")

    print("\n--- Probabilities (After Top-p): ---")
    top_p_tokens, top_p_probs, _ = get_top_tokens_and_probs(
        logits_top_p, tokenizer, k=max_top_k_for_probs
    )
    for token, prob in zip(top_p_tokens, top_p_probs):
        print(f"    {token}: {prob:.6f}")

    correct_sequence = top_choice
    chosen_token_ids = [
        tokenizer.encode(token, add_special_tokens=False) for token in chosen_tokens
    ]
    chosen_token_ids = [item for sublist in chosen_token_ids for item in sublist]
    correct_token_ids = [
        tokenizer.encode(token, add_special_tokens=False) for token in correct_sequence
    ]
    correct_token_ids = [item for sublist in correct_token_ids for item in sublist]

    score = 0
    max_score = len(chosen_tokens)
    for i in range(max_score):
        if chosen_tokens[i] == correct_sequence[i]:
            score += 1

    is_perfect = score == max_score

    color_print(
        f"You chose: {current_sentence} [[ {', '.join(chosen_tokens)} ]]",
        RED if not is_perfect else GREEN,
    )
    color_print(
        f"Correct sequence: {current_sentence} [[ {' '.join(correct_sequence)} ]] ({'Perfect!' if is_perfect else f'Score: {score}/{max_score}'})",
        GREEN if is_perfect else RED,
    )

    return score, max_score, chosen_token_ids, correct_token_ids, is_perfect


if __name__ == "__main__":
    model, tokenizer = load_model_and_tokenizer(model_name)

    print(
        f"Settings: max_steps={max_decode_steps}, top_k={top_k}, top_p={top_p}, temp={temperature}, choices={num_choices}, perm_len={permutation_length}, attention={show_attention}, max_top_k_for_probs={max_top_k_for_probs}"
    )

    input_text = input("Start a sentence: ")
    input_ids, attention_mask = prepare_inputs(input_text, tokenizer, model)

    total_score = 0
    total_max_score = 0
    current_sentence = input_text
    attention_history = []

    for step in range(max_decode_steps):
        print(f"\n--- Decoding Step: {step + 1} ---")

        start_time = time.time()
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=show_attention,
        )
        print(f"  Model forward pass time : {time.time() - start_time:.4f}s")

        logits_raw = outputs.logits[:, -1, :]

        # Apply temperature, top_k, and top_p filtering
        print(f"  Applying temperature : {time.time() - start_time:.4f}s")
        logits_temp = apply_temperature(logits_raw, temperature)
        print(f"  Finished applying temperature : {time.time() - start_time:.4f}s")
        print(f"  Applying top-k : {time.time() - start_time:.4f}s")
        logits_top_k = apply_top_k(logits_temp, top_k)
        print(f"  Finished applying top-k : {time.time() - start_time:.4f}s")
        print(f"  Applying top-p : {time.time() - start_time:.4f}s")
        logits_top_p = apply_top_p(logits_top_k, top_p)
        print(f"  Finished applying top-p : {time.time() - start_time:.4f}s")

        # Attention vizualization
        if show_attention:
            current_tokens, normalized_attention_scores = get_attention_heatmap(
                outputs, input_ids, tokenizer
            )
            colored_sentence_part, heatmap_scale = color_attention_text(
                current_tokens, normalized_attention_scores
            )

            attention_history.append(colored_sentence_part)

            print("\n--- Attention Heatmap (Current Step) ---")
            print(heatmap_scale)
            print(
                f"Current sentence with attention (magenta highlights): {colored_sentence_part}"
            )

            print("\n--- Attention Heatmap History: ---")
            for i, past_attention in enumerate(attention_history):
                print(f"  Step {i + 1}: {past_attention}")

        # Game Logic
        step_score, step_max_score, chosen_token_ids, correct_token_ids, is_perfect = (
            guess_next_word_sequence(
                tokenizer,
                logits_raw,
                logits_temp,
                logits_top_k,
                logits_top_p,
                num_choices,
                top_k,
                permutation_length,
                input_ids,
                current_sentence,
                max_top_k_for_probs,
            )
        )
        total_score += step_score
        total_max_score += step_max_score

        print(f"  Applying softmax : {time.time() - start_time:.4f}s")
        probabilities = torch.softmax(logits_top_p, dim=-1)
        print(f"  Finished applying softmax : {time.time() - start_time:.4f}s")
        _, best_token_indices = torch.topk(probabilities, 1, dim=-1)
        next_token_id = [best_token_indices[0, 0].item()]
        next_word = tokenizer.decode(next_token_id).strip()
        current_sentence += " " + next_word

        input_ids = torch.cat(
            [input_ids, torch.tensor([next_token_id], device=model.device)], dim=-1
        )
        print(f"  Applying attention mask : {time.time() - start_time:.4f}s")
        attention_mask = torch.cat(
            [
                attention_mask,
                torch.ones((attention_mask.shape[0], 1), device=model.device),
            ],
            dim=-1,
        )
        print(f"  Finished applying attention mask : {time.time() - start_time:.4f}s")

        if next_token_id[0] == tokenizer.eos_token_id:
            break

    decoded_output = tokenizer.decode(input_ids[0], skip_special_tokens=True)
    print(f"\n--- Generated Text: ---\n{decoded_output}")
    print(f"\n--- Final Score: {total_score} / {total_max_score} ---")
