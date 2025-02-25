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

num_choices = 3
use_top_k_sampling = True
use_top_p_sampling = True

# ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def color_print(text, color):
    print(color + text + RESET)


def guess_next_word(
    tokenizer: AutoTokenizer,
    top_k_indices,
    num_choices,
    current_ids,
    top_k_probs=None,
    top_p_tokens=None,
    top_p_probs=None,
):
    choices = []
    token_counts = []

    for i in range(min(num_choices, len(top_k_indices[0]))):
        token_ids = [top_k_indices[0, i].item()]
        word = tokenizer.decode(token_ids).strip()
        num_tokens = 1

        while True:
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
            start_time = time.time()
            outputs = model(next_ids)
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
                token_ids + [next_token_id[0].item()]
            ).strip()

            if (
                not next_word
                or not combined_word.startswith(word)
                or len(combined_word) <= len(word)
                or tokenizer.decode([next_token_id[0].item()]).startswith(" ")
            ):
                break

            word = combined_word
            token_ids.append(next_token_id[0].item())
            num_tokens += 1

        if word:
            choices.append((word, token_ids))
            token_counts.append(num_tokens)

    random.shuffle(choices)

    print(f"\nGuess the next word (enter the letter of your choice):")
    for i, (word, _) in enumerate(choices):
        print(
            f"  {chr(ord('a') + i)}) {word} ({token_counts[i]} token{'s' if token_counts[i] > 1 else ''})"
        )

    while True:
        user_choice = input("Your choice: ").strip().lower()
        if "a" <= user_choice <= chr(ord("a") + len(choices) - 1):
            break
        else:
            print(
                "Invalid input.  Please enter a letter corresponding to one of the choices."
            )

    chosen_index = ord(user_choice) - ord("a")
    chosen_word, chosen_token_ids = choices[chosen_index]

    correct_token_ids = [top_k_indices[0, 0].item()]
    correct_word = tokenizer.decode(correct_token_ids).strip()
    num_tokens = 1

    while True:
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
        start_time = time.time()
        outputs = model(next_ids)
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
            or tokenizer.decode([next_token_id[0].item()]).startswith(" ")
        ):
            break

        correct_word = combined_word
        correct_token_ids.append(next_token_id[0].item())
        num_tokens += 1

    color_print(
        f"You chose: {chosen_word} ({len(chosen_token_ids)} token{'s' if len(chosen_token_ids) > 1 else ''})",
        RED if chosen_token_ids != correct_token_ids else GREEN,
    )

    is_correct = chosen_token_ids == correct_token_ids
    color_print(
        f"Correct answer: {correct_word} ({len(correct_token_ids)} token{'s' if len(correct_token_ids) > 1 else ''}) ({'Correct!' if is_correct else 'Incorrect!'})",
        GREEN if is_correct else RED,
    )

    return correct_token_ids, is_correct


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
        print(f"\nTop-{top_k} Tokens and Probabilities (before Top-p):")
        for token, prob in zip(top_k_tokens, top_k_probs):
            print(f"  {token}: {prob:.4f}")

    if top_p is not None and top_p_tokens is not None and top_p_probs is not None:
        print(f"\nTop-p ({top_p}) Tokens and Probabilities (before Top-k):")
        for token, prob in zip(top_p_tokens, top_p_probs):
            print(f"  {token}: {prob:.4f}")


if __name__ == "__main__":
    model_name = "google/gemma-2b-it"
    print(f"Loading model: {model_name} and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(model_name)

    max_decode_steps = 16
    top_k = 5
    top_p = 0.95
    temperature = 0.7
    print(
        f"Custom loop set to max_decode_steps: {max_decode_steps}, top_k: {top_k}, top_p: {top_p}, temperature: {temperature}..."
    )
    print(f"Number of choices: {num_choices}")
    print(f"Using top-k sampling: {use_top_k_sampling}")
    print(f"Using top-p sampling: {use_top_p_sampling}")

    if not use_top_k_sampling and not use_top_p_sampling:
        print("Error: At least one of top-k or top-p sampling must be enabled.")
        exit()

    input_text = input("Start a sentence... then press enter... ")
    input_ids, attention_mask = prepare_inputs(input_text, tokenizer, model)

    generated_ids = input_ids
    score = 0
    for step in range(max_decode_steps):
        print(f"\n--- Decoding Step: {step + 1} ---")

        start_time = time.time()
        outputs = model(generated_ids, attention_mask=attention_mask)
        print(f"  Model forward pass took: {time.time() - start_time:.4f} seconds")
        next_token_logits = outputs.logits[:, -1, :]

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

        correct_token_ids, is_correct = guess_next_word(
            tokenizer,
            top_k_indices,
            num_choices,
            generated_ids,
            top_k_probs,
            top_p_tokens,
            top_p_probs,
        )
        next_token_id = torch.tensor(
            correct_token_ids, dtype=torch.long, device=model.device
        ).unsqueeze(0)

        if is_correct:
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

        print(
            f"Current sentence: {tokenizer.decode(generated_ids[0], skip_special_tokens=True)}"
        )

        if attention_mask is not None:
            start_time = time.time()
            attention_mask = torch.cat(
                [
                    attention_mask,
                    torch.ones((attention_mask.shape[0], 1), device=model.device),
                ],
                dim=-1,
            )
            print(
                f"  Attention mask concatenation took: {time.time() - start_time:.4f} seconds"
            )

        if next_token_id[0, -1].item() == tokenizer.eos_token_id:
            break

    decoded_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print(f"\n--- Final Generated Text: ---\n{decoded_output}")
    print(f"\n--- Final Score: {score} / {step + 1} ---")
