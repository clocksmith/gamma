import torch
import json
import os
import itertools
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM

# --- CONFIGURATION ---
MODEL_NAME = "google/gemma-3-1b-it"
OUTPUT_FILE = "tree_attention_data.json"

TOKENS = ["canvas", "context"]

def generate_prompts():
    """Generates all permutations for lengths 2, 4, 6, 8 based on 2-token blocks."""
    prompts = []
    
    # We build by blocks of 2 to match the UI logic
    pairs = list(itertools.product(TOKENS, repeat=2))
    
    def to_str(p_tuple):
        return " ".join(p_tuple)

    # Level 1
    l1 = [to_str(p) for p in pairs]
    prompts.extend(l1)
    
    # Level 2
    l2 = []
    for base in l1:
        for p in pairs:
            l2.append(base + " " + to_str(p))
    prompts.extend(l2)
    
    # Level 3
    l3 = []
    for base in l2:
        for p in pairs:
            l3.append(base + " " + to_str(p))
    prompts.extend(l3)

    # Level 4
    l4 = []
    for base in l3:
        for p in pairs:
            l4.append(base + " " + to_str(p))
    prompts.extend(l4)
    
    return prompts

def main():
    print(f"💀 Loading {MODEL_NAME}...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME, 
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            attn_implementation="eager"
        )
    except Exception as e:
        print(f"❌ Failed to load model. Is your venv active? {e}")
        return

    hidden_size = model.config.hidden_size
    print(f"Model hidden size: {hidden_size}")
    
    # Fixed random projection for consistent fingerprinting
    np.random.seed(42)
    projection_rgb = np.random.randn(hidden_size, 3)

    prompts = generate_prompts()
    print(f"🌊 Generated {len(prompts)} prompts to process.")
    
    export_data = {}

    for i, prompt in enumerate(prompts):
        if i % 10 == 0:
            print(f"[{i+1}/{len(prompts)}] Processing...")
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model(**inputs, output_attentions=True, output_hidden_states=True)
        
        # 1. Attention Matrix
        last_layer_attn = outputs.attentions[-1]
        avg_attn = last_layer_attn.mean(dim=1).squeeze().cpu().tolist()
        
        # 2. Hidden States
        last_layer_hidden = outputs.hidden_states[-1].squeeze().cpu().numpy()
        
        # 3. Generate Fingerprints
        fingerprints = []
        summaries = []
        
        if len(last_layer_hidden.shape) == 1:
            last_layer_hidden = last_layer_hidden[np.newaxis, :]

        for token_vec in last_layer_hidden:
            # RGB Fingerprint
            rgb = np.dot(token_vec, projection_rgb)
            rgb = ((rgb - rgb.min()) / (rgb.max() - rgb.min() + 1e-6) * 255).astype(int).tolist()
            fingerprints.append(rgb)
            
            # Vector Summary (16 points)
            summary = token_vec.reshape(16, -1).mean(axis=1).tolist()
            summaries.append([round(x, 4) for x in summary])

        # Optimize precision
        optimized_matrix = []
        for row in avg_attn:
            optimized_matrix.append([round(x, 4) for x in row])

        tokens = [tokenizer.decode([t]) for t in inputs.input_ids[0]]

        export_data[prompt] = {
            "tokens": tokens,
            "matrix": optimized_matrix,
            "fingerprints": fingerprints,
            "summaries": summaries
        }

    print(f"\n💾 Dumping {len(export_data)} artifacts to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(export_data, f)

    print("✅ Tree Generation Complete.")

if __name__ == "__main__":
    main()
