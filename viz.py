# viz.py
import torch
from utils import (
    load_model_and_tokenizer,
    apply_temperature,
    get_top_k_tokens_and_probs,
    apply_top_k,
    apply_top_p,
    prepare_inputs,
)


def visualize_step(logits, tokenizer, top_k=None, top_p=None):
    """Visualizes top-k and top-p probabilities for a single step."""

    print("\n--- Visualization ---")

    if top_k is not None:
        top_k_tokens, top_k_probs, _ = get_top_k_tokens_and_probs(
            logits, tokenizer, top_k
        )
        print(f"\nTop-{top_k} Tokens and Probabilities:")
        for token, prob in zip(top_k_tokens, top_k_probs):
            print(f"  {token}: {prob:.4f}")

    if top_p is not None:
        filtered_logits = apply_top_p(logits, top_p)
        probabilities = torch.softmax(filtered_logits, dim=-1)
        sorted_probs, sorted_indices = torch.sort(
            probabilities, descending=True, dim=-1
        )
        cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
        top_p_mask = cumulative_probs <= top_p
        top_p_mask[..., :1] = True
        top_p_indices_filtered = sorted_indices[0][top_p_mask[0]]
        top_p_probs_filtered = sorted_probs[0][top_p_mask[0]]

        print(f"\nTop-p ({top_p}) Tokens and Probabilities:")

        for i in range(len(top_p_indices_filtered)):
            token_id = top_p_indices_filtered[i].item()
            probability = top_p_probs_filtered[i].item()
            word = tokenizer.decode([token_id]).strip()
            print(f"  {word}: {probability:.4f}")


if __name__ == "__main__":
    model_name = "google/gemma-2b-it"  # Or any other model
    print(f"Loading model: {model_name} and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(model_name)

    input_text = "The quick brown fox"  # Example input
    input_ids, attention_mask = prepare_inputs(input_text, tokenizer, model)

    # Get logits for the *next* token (after "fox")
    outputs = model(input_ids, attention_mask=attention_mask)
    next_token_logits = outputs.logits[:, -1, :]

    # Set visualization parameters
    top_k_vis = 10
    top_p_vis = 0.9

    # Apply temperature (optional, but consistent with game.py)
    temperature = 0.7
    next_token_logits = apply_temperature(next_token_logits, temperature)

    # Visualize the step
    visualize_step(next_token_logits, tokenizer, top_k=top_k_vis, top_p=top_p_vis)
    # visualize_step(next_token_logits, tokenizer, top_k=top_k_vis) # Just Top K
    # visualize_step(next_token_logits, tokenizer, top_p=top_p_vis) # Just Top P
