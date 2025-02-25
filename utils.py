import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


def load_model_and_tokenizer(model_name):
    """Loads the model and tokenizer, handling quantization for 7b."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if model_name == "google/gemma-7b":
        model = AutoModelForCausalLM.from_pretrained(
            model_name, device_map="auto", load_in_4bit=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    return model, tokenizer


def apply_temperature(logits, temperature):
    """Applies temperature scaling to logits."""
    return logits / temperature


def apply_top_k(logits, top_k):
    """Applies top-k filtering to logits."""
    if top_k is not None:
        top_k_values, top_k_indices = torch.topk(logits, top_k, dim=-1)
        filtered_logits = torch.full_like(logits, float("-inf"))
        filtered_logits.scatter_(-1, top_k_indices, top_k_values)
        return filtered_logits
    return logits


def apply_top_p(logits, top_p):
    """Applies top-p (nucleus) filtering to logits."""
    if top_p is not None:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
        sorted_indices_to_remove = cumulative_probs > top_p
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0
        indices_to_remove = sorted_indices_to_remove.scatter(
            1, sorted_indices, sorted_indices_to_remove
        )
        filtered_logits = sorted_logits.clone()  # Create a copy before modifying
        filtered_logits[indices_to_remove] = float("-inf")
        # Scatter back to original indices
        output_logits = torch.full_like(logits, float("-inf"))
        output_logits.scatter_(-1, sorted_indices, filtered_logits)
        return output_logits
    return logits


def generate_next_token_with_top_k_top_p(logits, top_k=None, top_p=None):
    """Filters logits using top-k and/or top-p, then samples."""
    if top_k is not None:
        logits = apply_top_k(logits, top_k)
    if top_p is not None:
        logits = apply_top_p(logits, top_p)
    next_token_probs = torch.softmax(logits, dim=-1)
    next_token_id = torch.multinomial(next_token_probs, num_samples=1)
    return next_token_id


def get_top_k_tokens_and_probs(logits, tokenizer, top_k):
    """Gets the top-k tokens and their probabilities."""
    probabilities = torch.softmax(logits, dim=-1)
    top_k_values, top_k_indices = torch.topk(probabilities, top_k, dim=-1)
    top_k_tokens = [
        tokenizer.decode([token_id.item()]).strip() for token_id in top_k_indices[0]
    ]
    top_k_probs = top_k_values[0].tolist()  # Convert to list for easier handling
    return top_k_tokens, top_k_probs, top_k_indices


def prepare_inputs(input_text, tokenizer, model):
    """Encodes input text and moves tensors to the correct device."""
    encoded_input = tokenizer.encode_plus(input_text, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(model.device)
    attention_mask = encoded_input["attention_mask"].to(model.device)
    return input_ids, attention_mask
