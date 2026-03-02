#!/usr/bin/env python3
"""
GAMMA Prompt Analyzer

This tool analyzes a prompt using a specified model to provide:
1. Probability distribution for the NEXT token.
2. Attention matrix showing how each token in the prompt attends to previous tokens.

Usage:
    python3 tools/analyze_prompt.py --prompt "your prompt" [options]
"""

import sys
import argparse
import numpy as np
import warnings
import torch

try:
    from tools._path_setup import ensure_project_root_on_path
except ModuleNotFoundError:
    from _path_setup import ensure_project_root_on_path

# Suppress warnings
warnings.filterwarnings("ignore")

ensure_project_root_on_path()

from src.engines.engine_factory import get_engine
from src.engines import sampling_utils

def setup_args():
    parser = argparse.ArgumentParser(description="Analyze prompt probabilities and attention.")
    parser.add_argument("--prompt", type=str, required=True, help="The input prompt to analyze.")
    parser.add_argument("--model", type=str, default="google/gemma-2-2b-it", help="Model to use (default: google/gemma-2-2b-it)")
    parser.add_argument("--engine", type=str, default="pytorch", help="Engine to use (default: pytorch)")
    parser.add_argument("--focus", type=str, default=None, help="Optional string to highlight in attention report (e.g., 'canvas')")
    parser.add_argument("--top-k", type=int, default=10, help="Number of top probability tokens to show (default: 10)")
    return parser.parse_args()

def analyze_probabilities(engine, result, top_k=10):
    print("\n" + "="*80)
    print(f" NEXT TOKEN PROBABILITIES (Top {top_k})")
    print("="*80)
    
    # Extract logits/probs
    logits = result.get("logits_raw")
    probs = result.get("probabilities")
    
    # If no probs but logits, calculate them
    if probs is None and logits is not None:
        if isinstance(logits, torch.Tensor):
            logits_np = logits.detach().to(torch.float32).cpu().numpy()
        else:
            logits_np = np.array(logits)
             
        # Flatten if needed
        if logits_np.ndim > 1:
            logits_np = logits_np.flatten()
            
        probs = sampling_utils.softmax(logits_np)

    if probs is not None:
        # Convert to numpy if needed
        if hasattr(engine, "convert_to_numpy"):
            probs = engine.convert_to_numpy(probs)
        elif hasattr(probs, "numpy"):
            probs = probs.numpy()
        elif not isinstance(probs, np.ndarray):
            probs = np.array(probs)
            
        if probs.ndim > 1:
            probs = probs.flatten()
            
        # Get top K
        top_indices = np.argsort(probs)[-top_k:][::-1]
        
        print(f"{'Token':<20} | {'Probability':<12} | {'Token ID':<8}")
        print("-" * 50)
        for i in top_indices:
            token_text = engine.get_token_text(int(i))
            # Clean up token text for display
            display_text = token_text.replace('\n', '\\n').replace('\r', '\\r').replace('▁', ' ')
            prob = probs[i]
            print(f"{display_text:<20} | {prob:.6f}     | {i:<8}")
    else:
        print("Could not extract probabilities.")

def analyze_attention(engine, result, input_ids_list, focus_str=None):
    attentions = result.get("attention")
    if attentions is None:
        print("\nNo attention weights returned by the model/engine.")
        return

    print("\n" + "="*80)
    print(f" ATTENTION ANALYSIS (Last Layer)")
    print("="*80)
    print(f"Total attention layers: {len(attentions)}")
    
    # Use the last layer
    last_layer_attn = attentions[-1]
    
    # Check shape: (batch, heads, seq_len, seq_len)
    if len(last_layer_attn.shape) == 4:
        attn_tensor = last_layer_attn[0] # Remove batch dim
    else:
        attn_tensor = last_layer_attn

    # Average across heads
    if isinstance(attn_tensor, torch.Tensor):
        avg_attn = attn_tensor.mean(dim=0)
    else:
        avg_attn = np.mean(attn_tensor, axis=0)
    
    attn_matrix = avg_attn.tolist()
    
    # Prepare labels
    labels = []
    focus_indices = []
    
    for idx, tid in enumerate(input_ids_list):
        text = engine.get_token_text(tid)
        clean_text = text.replace('\n', '\\n').replace('▁', ' ')
        
        # Check focus
        if focus_str and focus_str.lower() in text.lower():
            focus_indices.append(idx)
            
        # Truncate for label
        label_text = clean_text
        if len(label_text) > 8:
            label_text = label_text[:7] + "…"
        labels.append(f"{idx}:{label_text}")

    # Print Matrix
    print("\nAttention Matrix (Avg across heads):")
    print("Rows = Query (Current Token), Columns = Key (Past Token)")
    
    # Header
    print("\n" + " " * 16 + " | ".join(f"{l:<10}" for l in labels))
    print("-" * (16 + 13 * len(labels)))
    
    for row_idx, row_weights in enumerate(attn_matrix):
        row_label = labels[row_idx]
        # Format row
        row_str = " | ".join(f"{w:.4f}    " if w > 0.001 else "   .      " for w in row_weights)
        print(f"{row_label:<16} {row_str}")

    # Detailed breakdown if focus string provided
    if focus_str and focus_indices:
        print(f"\nDetailed breakdown for tokens containing '{focus_str}':")
        print("-" * 60)
        
        for idx in focus_indices:
            token_text = engine.get_token_text(input_ids_list[idx]).replace('\n', '\\n')
            print(f"Token {idx} ('{token_text}') attention distribution:")
            
            # Get weights for this token
            weights = attn_matrix[idx][:idx+1]
            sorted_indices = np.argsort(weights)[::-1]
            
            # Show top 5 attended tokens
            for k in range(min(5, len(sorted_indices))):
                target_idx = sorted_indices[k]
                w = weights[target_idx]
                target_text = engine.get_token_text(input_ids_list[target_idx]).replace('\n', '\\n')
                print(f"  -> {w:.4f} attention to Token {target_idx} ('{target_text}')")
            print("")
    
    # Always show the last token's attention (what generated the prediction)
    last_idx = len(input_ids_list) - 1
    if not focus_indices or last_idx not in focus_indices:
        print(f"\nLast Token {last_idx} ('{engine.get_token_text(input_ids_list[last_idx]).replace(chr(10), str(r'\\n'))}') attention (driving next prediction):")
        weights = attn_matrix[last_idx]
        sorted_indices = np.argsort(weights)[::-1]
        for k in range(min(5, len(sorted_indices))):
            target_idx = sorted_indices[k]
            w = weights[target_idx]
            target_text = engine.get_token_text(input_ids_list[target_idx]).replace('\n', '\\n')
            print(f"  -> {w:.4f} attention to Token {target_idx} ('{target_text}')")

def main():
    args = setup_args()
    
    identifier = f"{args.engine}:{args.model}"
    print(f"Initializing {identifier}...")
    
    try:
        engine = get_engine(args.engine, args.model)
        engine.load()
    except Exception as e:
        print(f"Error loading engine: {e}")
        return

    print(f"\nAnalyzing Prompt: '{args.prompt}'")
    input_ids, attention_mask = engine.encode(args.prompt)
    
    # Convert input_ids to list
    if hasattr(input_ids, "tolist"):
        input_ids_list = input_ids.tolist()
    else:
        input_ids_list = list(input_ids)
        
    if isinstance(input_ids_list[0], list):
        input_ids_list = input_ids_list[0]

    print(f"Tokenized length: {len(input_ids_list)} tokens")
    
    try:
        result = engine.predict_next(
            input_ids,
            attention_mask,
            temperature=1.0,
            top_k=0,
            top_p=1.0,
            output_attentions=True
        )
    except Exception as e:
        print(f"Prediction failed: {e}")
        return

    analyze_probabilities(engine, result, args.top_k)
    analyze_attention(engine, result, input_ids_list, args.focus)

if __name__ == "__main__":
    main()
