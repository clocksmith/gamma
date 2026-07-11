"""Print an averaged attention matrix for a prompt."""

import argparse
from pathlib import Path
import sys
import warnings

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="pytorch", help="Gamma engine name")
    parser.add_argument(
        "--model", default="google/gemma-2-2b-it", help="Model identifier"
    )
    parser.add_argument(
        "--prompt",
        default="canvas canvas canvas canvas canvas canvas canvas canvas canvas ",
        help="Prompt to inspect",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import numpy as np
    import torch

    from src.engines.engine_factory import get_engine

    model_name = args.model
    engine_type = args.engine
    identifier = f"{engine_type}:{model_name}"
    prompt = args.prompt

    print(f"Loading engine: {identifier}")
    # Initialize engine with minimal config
    engine = get_engine(engine_type, model_name)
    try:
        engine.load()
    except Exception as exc:
        print(f"Failed to load engine: {exc}")
        return 1

    print(f"Encoding prompt: '{prompt}'")
    input_ids, attention_mask = engine.encode(prompt)

    # Identify token IDs for 'canvas'
    # We can do this by tokenizing 'canvas' alone or looking at the ids
    canvas_tokens = engine.encode("canvas", add_special_tokens=False)[0]
    # Handle tensor output from encode
    if hasattr(canvas_tokens, "tolist"):
        canvas_tokens = canvas_tokens.tolist()
    elif hasattr(canvas_tokens, "numpy"):
        canvas_tokens = canvas_tokens.numpy().tolist()

    print(f"Token IDs for 'canvas': {canvas_tokens}")

    # Convert input_ids to list for easy checking
    input_ids_list = (
        input_ids.tolist() if hasattr(input_ids, "tolist") else list(input_ids)
    )
    if not input_ids_list:
        print("The prompt produced no input tokens.")
        return 1
    if isinstance(input_ids_list[0], list):  # Flatten batch dim if present
        input_ids_list = input_ids_list[0]

    print(f"Full input token IDs: {input_ids_list}")

    # Find indices of 'canvas' tokens in the prompt
    canvas_indices = []

    # Let's inspect the tokens to find which ones are "canvas"
    print("\nToken analysis:")
    for idx, token_id in enumerate(input_ids_list):
        text = engine.get_token_text(token_id)
        print(f"Index {idx}: ID {token_id} -> '{text}'")
        if "canvas" in text.lower():
            canvas_indices.append(idx)

    print(f"\nFound 'canvas' tokens at indices: {canvas_indices}")

    print("Predicting next token with attention output...")
    try:
        result = engine.predict_next(
            input_ids,
            attention_mask,
            temperature=1.0,
            top_k=0,
            top_p=1.0,
            output_attentions=True,
        )
    except Exception as exc:
        print(f"Prediction failed: {exc}")
        return 1

    attentions = result.get("attention")
    if attentions is None:
        print("No attention weights returned.")
        return 1

    print(f"\nExtracted {len(attentions)} attention layers.")

    # Use the last layer for visualization as it's usually most relevant for next-token prediction
    last_layer_attn = attentions[-1]

    # Shape check
    # (batch, heads, seq_len, seq_len)
    print(f"Last layer attention shape: {last_layer_attn.shape}")

    # Remove batch dim
    # shape: (heads, seq_len, seq_len)
    attn_tensor = last_layer_attn[0]

    # Average across heads
    if isinstance(attn_tensor, torch.Tensor):
        avg_attn = attn_tensor.mean(dim=0)  # Average over heads -> (seq_len, seq_len)
    else:
        avg_attn = np.mean(attn_tensor, axis=0)

    # Convert to list of lists
    attn_matrix = avg_attn.tolist()

    print(
        "\nAttention Matrix (Avg across heads): Each row is a token attending to previous tokens"
    )
    print("Row = Query (Current Token), Column = Key (Past Token)")

    # Print header
    # Create short labels
    labels = []
    for idx, tid in enumerate(input_ids_list):
        text = engine.get_token_text(tid).replace("\n", "\\n").replace("▁", " ")
        if len(text) > 6:
            text = text[:5] + "."
        labels.append(f"{idx}:{text}")

    print("\n" + " " * 15 + " | ".join(f"{label:<8}" for label in labels))
    print("-" * (15 + 11 * len(labels)))

    for row_idx, row_weights in enumerate(attn_matrix):
        row_label = labels[row_idx]
        row_str = " | ".join(
            f"{w:.4f}  " if w > 0.0001 else "   .    " for w in row_weights
        )
        print(f"{row_label:<15} {row_str}")

    print("\nDetailed breakdown for 'canvas' tokens:")
    print("-" * 60)
    for idx in canvas_indices:
        token_text = engine.get_token_text(input_ids_list[idx])
        print(f"Token {idx} ({token_text}) attention distribution:")

        # Get attention weights for this token (it only attends to 0..idx)
        weights = attn_matrix[idx][: idx + 1]

        # Sort by weight to see top attended tokens
        sorted_indices = np.argsort(weights)[::-1]

        for k in range(min(5, len(sorted_indices))):
            target_idx = sorted_indices[k]
            w = weights[target_idx]
            target_text = engine.get_token_text(input_ids_list[target_idx])
            print(f"  -> {target_idx}:{target_text:<10} : {w:.4f}")
        print("")

    # Also show the last token (space)
    last_idx = len(input_ids_list) - 1
    if last_idx not in canvas_indices:
        print(
            f"Last Token {last_idx} ({engine.get_token_text(input_ids_list[last_idx])}) attention distribution:"
        )
        weights = attn_matrix[last_idx]
        sorted_indices = np.argsort(weights)[::-1]
        for k in range(min(5, len(sorted_indices))):
            target_idx = sorted_indices[k]
            w = weights[target_idx]
            target_text = engine.get_token_text(input_ids_list[target_idx])
            print(f"  -> {target_idx}:{target_text:<10} : {w:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
