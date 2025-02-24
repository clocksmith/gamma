from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


def visualize_top_k_top_p(logits, tokenizer, top_k=None, top_p=None):
    """Visualizes top-k and/or top-p sampling for a single step."""

    probabilities = torch.softmax(logits, dim=-1)

    if top_k is not None:
        top_k_values, top_k_indices = torch.topk(probabilities, top_k, dim=-1)

        print(f"\nTop-{top_k} Words and Probabilities:")
        for i in range(top_k):
            token_id = top_k_indices[0, i].item()
            probability = top_k_values[0, i].item()
            word = tokenizer.decode([token_id])
            print(f"  {word}: {probability:.4f}")

    if top_p is not None:
        sorted_probs, sorted_indices = torch.sort(
            probabilities, descending=True, dim=-1
        )
        cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
        top_p_mask = cumulative_probs <= top_p
        top_p_mask[..., :1] = True

        top_p_indices_filtered = sorted_indices[0][top_p_mask[0]]
        top_p_probs_filtered = sorted_probs[0][top_p_mask[0]]

        print(f"\nTop-p ({top_p}) Words and Probabilities:")
        for i in range(len(top_p_indices_filtered)):
            token_id = top_p_indices_filtered[i].item()
            probability = top_p_probs_filtered[i].item()
            word = tokenizer.decode([token_id])
            print(f"  {word}: {probability:.4f}")


# ========================= Main Script =========================

if __name__ == "__main__":
    model_name = "google/gemma-2b-it"
    print(f"Loading model: ${model_name} and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

    max_decode_steps = 16
    top_k = 3
    top_p = 0.95
    temperature = 0.7
    print(
        f"Custom loop set to max_decode_steps: ${max_decode_steps}, top_k: {top_k}, top_p: {top_p}, temperature: {temperature}..."
    )

    input_text = input("Start a sentence... then press enter... ")
    encoded_input = tokenizer.encode_plus(input_text, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(model.device)
    attention_mask = encoded_input["attention_mask"].to(model.device)

    generated_ids = input_ids
    for step in range(max_decode_steps):
        print(f"\n--- Decoding Step: {step + 1} ---")

        outputs = model(generated_ids, attention_mask=attention_mask)
        next_token_logits = outputs.logits[:, -1, :]

        # Apply temperature scaling
        next_token_logits = next_token_logits / temperature

        visualize_top_k_top_p(next_token_logits, tokenizer, top_k=top_k)
        # visualize_top_k_top_p(next_token_logits, tokenizer, top_k=top_k, top_p=top_p)

        if top_k is not None or top_p is not None:
            if top_k is not None:
                top_k_values, top_k_indices = torch.topk(
                    next_token_logits, top_k, dim=-1
                )
                next_token_logits = torch.full_like(next_token_logits, float("-inf"))
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
    print(f"\n--- Generated Text: ---\n{decoded_output}")
