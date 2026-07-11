"""Export attention and hidden-state summaries for selected token patterns."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "google/gemma-3-1b-it"
OUTPUT_FILE = Path("reports/model_analysis/canvas_attention_data.json")

# The "Texture Pack" - permutations of overloading
PROMPTS = [
    # LENGTH 2: PIXELS (Atomic Bias)
    "canvas canvas",
    "canvas context",
    "context canvas",
    "context context",
    # LENGTH 4: TILES (Structure)
    "canvas context canvas context",  # The Grid (ABAB)
    "canvas canvas context context",  # The Split (AABB)
    "canvas context context canvas",  # The Nest (ABBA)
    "canvas canvas canvas canvas",  # The Smear (AAAA)
    # LENGTH 8: TEXTURES (Long-Range)
    "canvas canvas canvas canvas canvas canvas canvas canvas",  # Saturated Smear
    "canvas context canvas context canvas context canvas context",  # Strict Clock
    "canvas canvas context context context context canvas canvas",  # Deep Nest / Arch
    "canvas canvas canvas canvas context context context context",  # Phase Shift
    "canvas context canvas canvas context canvas canvas canvas",  # Entropy / Glitch
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default=MODEL_NAME, help="Hugging Face model identifier"
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_FILE, help="Output JSON path"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Loading {args.model}...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model)
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            attn_implementation="eager",
        )
    except Exception as e:
        print(f"Failed to load model. Is your venv active? {e}")
        return

    export_data = {}

    print("\nGenerating attention texture data...\n")

    for i, prompt in enumerate(PROMPTS):
        print(f"[{i + 1}/{len(PROMPTS)}] Processing: '{prompt}'")

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model(**inputs, output_attentions=True, output_hidden_states=True)

        # 1. Attention Matrix
        last_layer_attn = outputs.attentions[-1]
        avg_attn = last_layer_attn.mean(dim=1).squeeze().cpu().tolist()

        # 2. Hidden States (The "Value" space)
        last_layer_hidden = outputs.hidden_states[-1].squeeze().cpu().numpy()

        # 3. Generate Summaries
        summaries = []
        if len(last_layer_hidden.shape) == 1:
            last_layer_hidden = last_layer_hidden[np.newaxis, :]

        for token_vec in last_layer_hidden:
            # Vector Summary (16 points)
            summary = token_vec.reshape(16, -1).mean(axis=1).tolist()
            summaries.append([round(x, 4) for x in summary])

        # Get token strings
        tokens = [tokenizer.decode([t]) for t in inputs.input_ids[0]]

        export_data[prompt] = {
            "tokens": tokens,
            "matrix": avg_attn,
            "summaries": summaries,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting artifacts to {args.output}...")

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    print("Done. The canvas dataset is ready.")


if __name__ == "__main__":
    main()
