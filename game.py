# --- game.py ---
import torch
import random
from transformers import AutoTokenizer
from utils import (
    load_model_and_tokenizer,
    apply_temperature,
    get_top_k_tokens_and_probs,
    prepare_inputs,
    apply_top_k,
    apply_top_p,
    generate_next_token_with_top_k_top_p,
)
import time
import numpy as np

# Game config.
num_choices = 3
use_top_k_sampling = True
use_top_p_sampling = True
max_lookahead_steps = 5
show_attention = True

# Model config.
model_name = "google/gemma-2b-it"
max_decode_steps = 12
top_k = 7
top_p = 0.95
temperature = 0.7

# ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"


def color_print(text, color):
    print(color + text + RESET)


def get_attention_heatmap(outputs, input_ids, tokenizer):
    """
    Extracts and processes attention weights to create a heatmap.
    Returns a list of tuples: (token_text, attention_score).
    """
    if not hasattr(outputs, "attentions") or outputs.attentions is None:
        return None

    # Assuming attentions is a tuple of layers, each layer is (batch_size, num_heads, seq_len, seq_len)
    # We are interested in the attention weights from the last layer, last head, for the last token
    # Shape: (batch_size, num_heads, seq_len, seq_len)
    last_layer_attentions = outputs.attentions[-1]

    # Take attention of last generated token to previous tokens.
    # Remove the last token's self-attention.
    # Shape: (num_heads, seq_len-1).
    attention_weights = last_layer_attentions[0, :, -1, :-1]

    # Average attention weights across all heads
    # Shape: (seq_len-1)
    averaged_attention = attention_weights.mean(dim=0)

    # Exclude last token which is the one being predicted, and convert ids to tokens
    input_tokens = tokenizer.convert_ids_to_tokens(input_ids[0][:-1])
    attention_scores = averaged_attention.tolist()

    # Normalize attention scores to 0-1 for heatmap intensity
    max_attention = max(attention_scores) if attention_scores else 1.0
    # Avoid division by zero if sequence is just starting...
    normalized_attention = [(score / max_attention) for score in attention_scores]

    # list of tuples (token, attention_score)
    heatmap = list(zip(input_tokens, normalized_attention))
    return heatmap


def color_attention_text(sentence, heatmap, base_color=BLUE, max_intensity=97):
    """
    Applies color highlighting to tokens based on attention scores.
    Uses a base color and varies intensity based on attention.
    """
    colored_sentence = []
    # re-tokenize to align with heatmap if needed. simpler to assume tokenization is aligned for now.
    tokens = tokenizer.tokenize(sentence)
    # if no attention, just return blue sentence
    if heatmap is None:
        return base_color + sentence + RESET

    heatmap_dict = (
        dict(heatmap) if heatmap else {}
    )  # Ensure heatmap is a dict for lookup

    token_index = 0
    for token_text in tokens:
        # Check if heatmap is available for this token
        attention_score = heatmap_dict.get(token_text)  # Use .get() to avoid KeyError
        if token_index < len(heatmap) and attention_score is not None:
            intensity = int(max_intensity * attention_score)
            color_code = f"\033[{intensity}m"  # Intensity from 90-97 are bright colors
            # Apply intensity color, then base color for hue
            colored_token = color_code + token_text + base_color
        else:
            # Default base color if no attention score
            colored_token = base_color + token_text

        colored_sentence.append(colored_token)
        token_index += 1

    # Join tokens and reset/clear color at the for next print().
    return "".join(colored_sentence) + RESET


def visualize_probabilities(
    logits,
    tokenizer,
    top_k=None,
    top_p=None,
    top_k_tokens=None,
    top_k_probs=None,
    top_p_tokens=None,
    top_p_probs=None,
):
    if top_k is not None and top_k_tokens is not None and top_k_probs is not None:
        print(f"\n    --- Top-{top_k} Tokens and Probabilities (before Top-p): ---")
        for token, prob in zip(top_k_tokens, top_k_probs):
            print(f"      {token}: {prob:.4f}")

    if top_p is not None and top_p_tokens is not None and top_p_probs is not None:
        print(f"\n    --- Top-p ({top_p}) Tokens and Probabilities (before Top-k): ---")
        for token, prob in zip(top_p_tokens, top_p_probs):
            print(f"      {token}: {prob:.4f}")


def guess_next_word(
    tokenizer: AutoTokenizer,
    model,
    top_k_indices,
    num_choices,
    current_ids,
    attention_mask,  # Pass attention mask
    top_k_probs=None,
    top_p_tokens=None,
    top_p_probs=None,
):
    unique_choices = []
    seen_words = set()
    token_counts = []
    eos_choice_index = -1

    for i in range(min(num_choices * 5, len(top_k_indices[0]))):
        token_ids = [top_k_indices[0, i].item()]
        word = tokenizer.decode(token_ids).strip()
        num_tokens = 1
        lookahead_steps = 0

        if token_ids[0] == tokenizer.eos_token_id:
            if tokenizer.eos_token not in seen_words:
                eos_choice_index = len(unique_choices)
                unique_choices.append((tokenizer.eos_token, token_ids))
                seen_words.add(tokenizer.eos_token)
                token_counts.append(num_tokens)
            continue

        current_word_choices = []  # list to hold word choices for current top_k index
        current_word_token_counts = []

        while lookahead_steps < max_lookahead_steps:
            next_ids = current_ids.clone().detach()
            next_ids = torch.cat(
                [
                    next_ids,
                    torch.tensor(
                        [[token_ids[-1]]], dtype=torch.long, device=current_ids.device
                    ),
                ],
                dim=-1,
            )
            # Extend attention mask for lookahead
            next_attention_mask = torch.cat(
                [
                    attention_mask,
                    torch.ones(
                        (
                            attention_mask.shape[0],
                            next_ids.shape[1] - attention_mask.shape[1],
                        ),  # Correctly extend based on diff in seq lengths
                        device=current_ids.device,
                        dtype=attention_mask.dtype,
                    ),
                ],
                dim=-1,
            )
            start_time = time.time()
            outputs = model(
                next_ids,
                attention_mask=next_attention_mask,  # Use extended attention mask
                output_attentions=show_attention,
            )  # Pass attention_mask and request attentions
            # print(
            #     f"    Model forward pass (for lookahead) took: {time.time() - start_time:.4f} seconds"
            # )
            next_token_logits = outputs.logits[:, -1, :]
            start_time = time.time()
            next_token_id = torch.argmax(next_token_logits, dim=-1)
            # print(
            #     f"    Argmax (for lookahead) took: {time.time() - start_time:.4f} seconds"
            # )

            next_word = tokenizer.decode([next_token_id[0].item()]).strip()
            combined_word = tokenizer.decode(
                token_ids + [next_token_id[0].item()]
            ).strip()

            current_word_choices.append(
                (combined_word, token_ids + [next_token_id[0].item()])
            )  # Store current word and tokens
            current_word_token_counts.append(num_tokens + 1)

            if (
                not next_word
                or not combined_word.startswith(word)
                or len(combined_word) <= len(word)
                or next_word == ","  # Stop lookahead at commas
                or next_word == "."  # Stop lookahead at periods
                or next_word == "!"  # Stop lookahead at exclamation points
                or next_word == "?"  # Stop lookahead at question marks
                or next_word.startswith(" ")  # Stop lookahead at spaces (new words)
            ):
                break

            word = combined_word
            token_ids.append(next_token_id[0].item())
            num_tokens += 1
            lookahead_steps += 1

        if current_word_choices:  # If lookahead generated any words
            best_word, best_tokens = current_word_choices[
                -1
            ]  # Take the longest word from lookahead
            if best_word and best_word not in seen_words:
                unique_choices.append((best_word, best_tokens))
                seen_words.add(best_word)
                token_counts.append(len(best_tokens))
                if len(unique_choices) >= num_choices:
                    break
        elif (
            word and word not in seen_words
        ):  # Fallback to initial word if lookahead failed to extend
            unique_choices.append((word, token_ids))
            seen_words.add(word)
            token_counts.append(num_tokens)
            if len(unique_choices) >= num_choices:
                break

    random.shuffle(unique_choices)
    if eos_choice_index != -1 and len(unique_choices) > 1:
        unique_choices.insert(0, unique_choices.pop(eos_choice_index))
    choices_to_display = unique_choices[:num_choices]

    print(f"\nGuess the next word (enter the letter of your choice):")
    for i, (word, token_ids) in enumerate(choices_to_display):
        display_word = word if word != tokenizer.eos_token else "<eos>"
        token_display = tokenizer.decode(token_ids)
        print(
            f"  {chr(ord('a') + i)}) {display_word} ({token_counts[i]} token{'s' if token_counts[i] > 1 else ''}) Tokens: [{token_display}]"
        )

    while True:
        user_choice = input("Your choice: ").strip().lower()
        if "a" <= user_choice <= chr(ord("a") + len(choices_to_display) - 1):
            break
        else:
            print(
                "Invalid input.  Please enter a letter corresponding to one of the choices."
            )

    chosen_index = ord(user_choice) - ord("a")
    chosen_word, chosen_token_ids = choices_to_display[chosen_index]

    correct_token_ids = [top_k_indices[0, 0].item()]
    correct_word = tokenizer.decode(correct_token_ids).strip()
    num_tokens = 1
    lookahead_steps = 0

    while lookahead_steps < max_lookahead_steps:
        next_ids = current_ids.clone().detach()
        next_ids = torch.cat(
            [
                next_ids,
                torch.tensor(
                    [[correct_token_ids[-1]]],
                    dtype=torch.long,
                    device=current_ids.device,
                ),
            ],
            dim=-1,
        )
        # Extend attention mask for lookahead for correct word
        next_attention_mask = torch.cat(
            [
                attention_mask,
                torch.ones(
                    (
                        attention_mask.shape[0],
                        next_ids.shape[1] - attention_mask.shape[1],
                    ),  # Correctly extend
                    device=current_ids.device,
                    dtype=attention_mask.dtype,
                ),
            ],
            dim=-1,
        )
        start_time = time.time()
        outputs = model(
            next_ids,
            attention_mask=next_attention_mask,  # Use extended attention mask
            output_attentions=show_attention,
        )  # Request attentions
        print(
            f"    Model forward pass (for lookahead) took: {time.time() - start_time:.4f} seconds"
        )

        next_token_logits = outputs.logits[:, -1, :]
        start_time = time.time()
        next_token_id = torch.argmax(next_token_logits, dim=-1)
        print(
            f"    Argmax (for lookahead) took: {time.time() - start_time:.4f} seconds"
        )
        next_word = tokenizer.decode([next_token_id[0].item()]).strip()
        combined_word = tokenizer.decode(
            correct_token_ids + [next_token_id[0].item()]
        ).strip()

        if (
            not next_word
            or not combined_word.startswith(correct_word)
            or len(combined_word) <= len(correct_word)
        ):
            break

        correct_word = combined_word
        correct_token_ids.append(next_token_id[0].item())
        num_tokens += 1
        lookahead_steps += 1

    is_correct_eos = correct_token_ids[0] == tokenizer.eos_token_id
    is_chosen_eos = chosen_token_ids[0] == tokenizer.eos_token_id
    is_correct = chosen_token_ids == chosen_token_ids

    chosen_display_word = chosen_word if not is_chosen_eos else "<eos>"
    correct_display_word = correct_word if not is_correct_eos else "<eos>"

    color_print(
        f"You chose: {chosen_display_word} ({len(chosen_token_ids)} token{'s' if len(chosen_token_ids) > 1 else ''})",
        RED if not is_correct else GREEN,
    )
    color_print(
        f"Correct answer: {correct_display_word} ({len(correct_token_ids)} token{'s' if len(correct_token_ids) > 1 else ''}) ({'Correct!' if is_correct else 'Incorrect!'})",
        GREEN if is_correct else RED,
    )

    return (
        correct_token_ids,
        is_correct or is_chosen_eos and is_correct_eos,
        is_chosen_eos,
    )


if __name__ == "__main__":
    print(f"Loading model: {model_name} and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(model_name)

    max_decode_steps = 256
    top_k = 5
    top_p = 0.95
    temperature = 0.7
    print(
        f"Custom loop set to max_decode_steps: {max_decode_steps}, top_k: {top_k}, top_p: {top_p}, temperature: {temperature}..."
    )
    print(f"Number of choices: {num_choices}")
    print(f"Using top-k sampling: {use_top_k_sampling}")
    print(f"Using top-p sampling: {use_top_p_sampling}")
    print(f"Showing attention heatmap: {show_attention}")

    if not use_top_k_sampling and not use_top_p_sampling:
        print("Error: At least one of top-k or top-p sampling must be enabled.")
        exit()

    input_text = input("Start a sentence... then press enter... ")
    input_ids, attention_mask = prepare_inputs(input_text, tokenizer, model)

    generated_ids = input_ids
    score = 0
    previous_sentences_attention = []  # list to store attention-highlighted sentences
    for step in range(max_decode_steps):
        print(f"\n--- Decoding Step: {step + 1} ---")

        start_time = time.time()
        # Main model forward pass (LLM step)
        outputs = model(
            generated_ids,
            attention_mask=attention_mask,  # Use current attention mask
            output_attentions=show_attention,
        )  # Request attentions
        print(
            f"  LLM Forward Pass took: {time.time() - start_time:.4f} seconds"
        )  # Clearer print statement
        next_token_logits = outputs.logits[:, -1, :]

        if show_attention:
            current_heatmap = get_attention_heatmap(outputs, generated_ids, tokenizer)
        else:
            current_heatmap = None

        start_time = time.time()
        next_token_logits = apply_temperature(next_token_logits, temperature)
        print(f"  Temperature scaling took: {time.time() - start_time:.4f} seconds")

        start_time = time.time()
        top_k_tokens, top_k_probs, top_k_indices = get_top_k_tokens_and_probs(
            next_token_logits, tokenizer, top_k
        )
        print(f"  Top-k calculation took: {time.time() - start_time:.4f} seconds")

        top_p_tokens, top_p_probs = None, None
        if use_top_p_sampling:
            start_time = time.time()
            top_p_filtered_logits = apply_top_p(next_token_logits, top_p)
            print(f"  Top-p filtering took: {time.time() - start_time:.4f} seconds")

            start_time = time.time()
            probabilities = torch.softmax(top_p_filtered_logits, dim=-1)
            print(f"  Softmax took: {time.time() - start_time:.4f} seconds")

            sorted_probs, sorted_indices = torch.sort(
                probabilities, descending=True, dim=-1
            )
            cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
            top_p_mask = cumulative_probs <= top_p
            top_p_mask[..., :1] = True
            top_p_indices_filtered = sorted_indices[0][top_p_mask[0]]
            top_p_probs_filtered = sorted_probs[0][top_p_mask[0]]
            top_p_tokens = [
                tokenizer.decode([token_id.item()]).strip()
                for token_id in top_p_indices_filtered
            ]
            top_p_probs = top_p_probs_filtered.tolist()

        correct_token_ids, is_correct, is_chosen_eos = guess_next_word(
            tokenizer,
            model,
            top_k_indices,
            num_choices,
            generated_ids,
            attention_mask,  # Pass attention_mask
            top_k_probs,
            top_p_tokens,
            top_p_probs,
        )
        next_token_id = torch.tensor(
            correct_token_ids, dtype=torch.long, device=model.device
        ).unsqueeze(0)

        if is_correct and not is_chosen_eos:
            score += 1

        visualize_probabilities(
            next_token_logits,
            tokenizer,
            top_k,
            top_p,
            top_k_tokens,
            top_k_probs,
            top_p_tokens,
            top_p_probs,
        )

        start_time = time.time()
        generated_ids = torch.cat([generated_ids, next_token_id], dim=-1)
        print(f"  Tensor concatenation took: {time.time() - start_time:.4f} seconds")

        current_sentence = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        if show_attention:
            heatmap_dict = {
                token: score for token, score in current_heatmap
            }  # Ensure heatmap is a dict for lookup
            colored_sentence = color_attention_text(current_sentence, heatmap_dict)
            previous_sentences_attention.append(
                colored_sentence
            )  # Store colored sentence
        else:
            colored_sentence = BLUE + current_sentence + RESET
            previous_sentences_attention.append(colored_sentence)  # Store blue sentence

        # Print previous attention steps
        print("\n--- Previous Attention Steps ---")
        for prev_sentence in previous_sentences_attention[
            :-1
        ]:  # Exclude current sentence from previous
            print(prev_sentence)

        print(
            f"\nCurrent sentence: {colored_sentence}"
        )  # Print current sentence with attention

        if attention_mask is not None:
            start_time = time.time()
            # Extend attention mask for main decoding loop - Corrected extension logic
            attention_mask = torch.cat(
                [
                    attention_mask,
                    torch.ones(
                        (attention_mask.shape[0], 1),
                        device=model.device,
                        dtype=attention_mask.dtype,
                    ),
                ],
                dim=-1,
            )
            print(
                f"  Attention mask concatenation took: {time.time() - start_time:.4f} seconds"
            )

        if next_token_id[0, -1].item() == tokenizer.eos_token_id or is_chosen_eos:
            break

    decoded_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print(f"\n--- Final Generated Text: ---\n{decoded_output}")
    print(f"\n--- Final Score: {score} / {step + 1} ---")
