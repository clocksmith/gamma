from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import random

# ========================= Configuration =========================
GUESS_NEXT_WORD = False  # Set to False to disable the guessing game
NUM_CHOICES = 3  # Number of multiple-choice options


def guess_next_word(tokenizer, top_k_indices, num_choices):
    """Presents a multiple-choice guessing game for the next word."""

    choices = []
    # Select top 'num_choices' from top_k_indices
    for i in range(min(num_choices, len(top_k_indices[0]))):  # Prevent index error
        token_id = top_k_indices[0, i].item()
        word = tokenizer.decode([token_id]).strip()
        if word:
            choices.append((word, token_id))

    random.shuffle(choices)

    # print("\nGuess the next word (enter the letter of your choice):")
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

    # print(f"You chose: {chosen_word}")
    is_correct = chosen_token_id == correct_token_id
    print(
        f"Correct answer: {correct_word} --- ({'Correct!' if is_correct else 'Wrong!'})"
    )

    return correct_token_id, is_correct


# ========================= Main Script =========================

if __name__ == "__main__":
    model_name = "google/gemma-2b"  # Change this to test different models
    print(f"Loading model: {model_name} and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # --- Conditional Quantization ---
    if model_name == "google/gemma-7b":
        model = AutoModelForCausalLM.from_pretrained(
            model_name, device_map="auto", load_in_4bit=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    # --- End Conditional Quantization ---

    max_decode_steps = 10
    top_k = 10
    top_p = 0.9
    temperature = 0
    print(
        f"Custom loop set to max_decode_steps: {max_decode_steps}, top_k: {top_k}, top_p: {top_p}, temperature: {temperature}..."
    )
    print(
        f"Guessing game: {'Enabled' if GUESS_NEXT_WORD else 'Disabled'}, Number of choices: {NUM_CHOICES}"
    )

    input_text = input("Start a sentence... then press enter... ")
    encoded_input = tokenizer.encode_plus(input_text, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(model.device)
    attention_mask = encoded_input["attention_mask"].to(model.device)

    generated_ids = input_ids
    score = 0
    for step in range(max_decode_steps):
        # print(f"\n--- Decoding Step: {step + 1} ---")

        outputs = model(generated_ids, attention_mask=attention_mask)
        next_token_logits = outputs.logits[:, -1, :]
        next_token_logits = next_token_logits / temperature

        if GUESS_NEXT_WORD:
            top_k_values, top_k_indices = torch.topk(
                torch.softmax(next_token_logits, dim=-1), top_k, dim=-1
            )
            correct_token_id, is_correct = guess_next_word(
                tokenizer, top_k_indices, NUM_CHOICES
            )
            next_token_id = torch.tensor(
                [[correct_token_id]], dtype=torch.long, device=model.device
            )

            if is_correct:
                score += 1

        else:
            if top_k is not None or top_p is not None:
                if top_k is not None:
                    top_k_values, top_k_indices = torch.topk(
                        next_token_logits, top_k, dim=-1
                    )
                    next_token_logits = torch.full_like(
                        next_token_logits, float("-inf")
                    )
                    next_token_logits.scatter_(-1, top_k_indices, top_k_values)

                if top_p is not None:
                    sorted_logits, sorted_indices = torch.sort(
                        next_token_logits, descending=True, dim=-1
                    )
                    cumulative_probs = torch.cumsum(
                        torch.softmax(sorted_logits, dim=-1), dim=-1
                    )
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[
                        ..., :-1
                    ].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    indices_to_remove = sorted_indices_to_remove.scatter(
                        1, sorted_indices, sorted_indices_to_remove
                    )
                    next_token_logits[indices_to_remove] = float("-inf")

            next_token_probs = torch.softmax(next_token_logits, dim=-1)
            next_token_id = torch.multinomial(next_token_probs, num_samples=1)

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
    if GUESS_NEXT_WORD:
        print(f"\n--- Final Score: {score} / {step + 1} ---")
