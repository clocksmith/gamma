# game.py
import torch
import random
from transformers import AutoTokenizer  # Import for type hinting
from utils import (
    load_model_and_tokenizer,
    apply_temperature,
    generate_next_token,
    get_top_k_tokens_and_probs,
    prepare_inputs,
    apply_top_k,
    apply_top_p,
)


# ========================= Configuration =========================
num_choices = 3  # Number of multiple-choice options


def guess_next_word(tokenizer: AutoTokenizer, top_k_indices, num_choices):
    """Presents a multiple-choice guessing game for the next word."""

    choices = []
    # Select top 'num_choices' from top_k_indices
    for i in range(min(num_choices, len(top_k_indices[0]))):
        token_id = top_k_indices[0, i].item()
        word = tokenizer.decode([token_id]).strip()
        if word:  # Ensure the word isn't empty
            choices.append((word, token_id))

    random.shuffle(choices)

    print("\nGuess the next word (enter the letter of your choice):")
    for i, (word, _) in enumerate(choices):
        print(f"  {chr(ord('a') + i)}) {word}")

    while True:
        user_choice = input("Your choice: ").strip().lower()
        if "a" <= user_choice <= chr(ord("a") + len(choices) - 1):
            break
        else:
            print(
                "Invalid input.  Please enter a letter corresponding to one of the choices."
            )

    chosen_index = ord(user_choice) - ord("a")
    chosen_word, chosen_token_id = choices[chosen_index]

    correct_token_id = top_k_indices[0, 0].item()
    correct_word = tokenizer.decode([correct_token_id]).strip()

    print(f"You chose: {chosen_word}")
    is_correct = chosen_token_id == correct_token_id
    print(
        f"Correct answer: {correct_word} ({'Correct!' if is_correct else 'Incorrect!'})"
    )

    return correct_token_id, is_correct


def visualize_probabilities(logits, tokenizer, top_k=None, top_p=None):
    """Visualizes the top-k and top-p probabilities (adapted from viz.py)."""

    if top_k is not None:
        top_k_tokens, top_k_probs, _ = get_top_k_tokens_and_probs(
            logits, tokenizer, top_k
        )
        print(f"\nTop-{top_k} Tokens and Probabilities:")
        for token, prob in zip(top_k_tokens, top_k_probs):
            print(f"  {token}: {prob:.4f}")

    if top_p is not None:
        filtered_logits = apply_top_p(logits, top_p)  # Apply top-p filtering
        probabilities = torch.softmax(filtered_logits, dim=-1)
        sorted_probs, sorted_indices = torch.sort(
            probabilities, descending=True, dim=-1
        )
        cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
        top_p_mask = cumulative_probs <= top_p
        top_p_mask[..., :1] = True  # Ensure the first token is always included

        top_p_indices_filtered = sorted_indices[0][top_p_mask[0]]
        top_p_probs_filtered = sorted_probs[0][top_p_mask[0]]

        print(f"\nTop-p ({top_p}) Tokens and Probabilities:")
        for i in range(len(top_p_indices_filtered)):
            token_id = top_p_indices_filtered[i].item()
            probability = top_p_probs_filtered[i].item()
            word = tokenizer.decode([token_id]).strip()
            if word:  # Ensure the word isn't empty
                print(f"  {word}: {probability:.4f}")


# ========================= Main Script =========================

if __name__ == "__main__":
    model_name = "google/gemma-2b-it"  # Change this to test different models
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

    input_text = input("Start a sentence... then press enter... ")
    input_ids, attention_mask = prepare_inputs(input_text, tokenizer, model)

    generated_ids = input_ids
    score = 0
    for step in range(max_decode_steps):
        print(f"\n--- Decoding Step: {step + 1} ---")

        outputs = model(generated_ids, attention_mask=attention_mask)
        next_token_logits = outputs.logits[:, -1, :]
        next_token_logits = apply_temperature(next_token_logits, temperature)

        top_k_values, top_k_indices = torch.topk(
            torch.softmax(next_token_logits, dim=-1), top_k, dim=-1
        )
        # --- Get the correct next token ID *before* the guessing game ---
        correct_token_id = top_k_indices[0, 0].item()
        correct_word = tokenizer.decode([correct_token_id]).strip()

        # --- Skip if the correct word is empty or just whitespace ---
        if not correct_word:
            print(f"Skipping empty/whitespace token: {repr(correct_word)}")
            next_token_id = torch.tensor(
                [[correct_token_id]], dtype=torch.long, device=model.device
            )
        else:
            # --- Proceed with the guessing game ---
            chosen_token_id, is_correct = guess_next_word(
                tokenizer, top_k_indices, num_choices
            )
            next_token_id = torch.tensor(
                [[correct_token_id]], dtype=torch.long, device=model.device
            )

            if is_correct:
                score += 1

            # --- Visualize probabilities *after* the guess ---
            visualize_probabilities(
                next_token_logits, tokenizer, top_k=top_k, top_p=top_p
            )

        generated_ids = torch.cat([generated_ids, next_token_id], dim=-1)
        print(
            f"Current sentence: {tokenizer.decode(generated_ids[0], skip_special_tokens=True)}"
        )

        if attention_mask is not None:
            attention_mask = torch.cat(
                [
                    attention_mask,
                    torch.ones((attention_mask.shape[0], 1), device=model.device),
                ],
                dim=-1,
            )

        if next_token_id[0, 0].item() == tokenizer.eos_token_id:
            break

    decoded_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print(f"\n--- Final Generated Text: ---\n{decoded_output}")
    print(f"\n--- Final Score: {score} / {step + 1} ---")
