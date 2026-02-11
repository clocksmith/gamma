import sys
import os
import argparse
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
# Also add current dir
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.engines.engine_factory import get_engine
from src.engines import sampling_utils

def main():
    model_name = "google/gemma-2-2b-it"
    engine_type = "pytorch"
    identifier = f"{engine_type}:{model_name}"
    
    prompt = "canvas canvas canvas canvas canvas canvas canvas canvas canvas "
    
    print(f"Loading engine: {identifier}")
    # Initialize engine with minimal config
    engine = get_engine(engine_type, model_name)
    try:
        engine.load()
    except Exception as e:
        print(f"Failed to load engine: {e}")
        # Try finding another available model if this one fails?
        # For now, let's just fail loudly.
        return
    
    print(f"Encoding prompt: '{prompt}'")
    input_ids, attention_mask = engine.encode(prompt)
    
    print("Predicting next token...")
    # predict_next(input_ids, attention_mask, temperature, top_k, top_p)
    # Using default values suitable for raw logits extraction
    try:
        result = engine.predict_next(
            input_ids, 
            attention_mask, 
            temperature=1.0, 
            top_k=0, 
            top_p=1.0
        )
    except Exception as e:
        print(f"Prediction failed: {e}")
        return
    
    # Extract logits/probs
    logits = result.get("logits_raw")
    probs = result.get("probabilities")
    
    if probs is None and logits is not None:
        print("Calculating probabilities from logits...")
        # Convert logits to probs
        if hasattr(engine, "convert_to_numpy"):
             logits_np = engine.convert_to_numpy(logits)
        elif hasattr(logits, "numpy"):
             logits_np = logits.numpy()
        else:
             logits_np = np.array(logits)
             
        # Flatten if needed
        if logits_np.ndim > 1:
            logits_np = logits_np.flatten()
            
        probs = sampling_utils.softmax(logits_np)

    if probs is not None:
        if hasattr(engine, "convert_to_numpy"):
            probs = engine.convert_to_numpy(probs)
        elif hasattr(probs, "numpy"):
            probs = probs.numpy()
        elif not isinstance(probs, np.ndarray):
            probs = np.array(probs)
            
        if probs.ndim > 1:
            probs = probs.flatten()
            
        # Get top 10
        top_k = 10
        top_indices = np.argsort(probs)[-top_k:][::-1]
        
        print(f"\nTop {top_k} Probabilities for prompt: '{prompt}'")
        print("-" * 50)
        print(f"{'Token':<20} | {'Probability':<12} | {'Token ID':<8}")
        print("-" * 50)
        for i in top_indices:
            token_text = engine.get_token_text(int(i))
            # Clean up token text for display (remove newlines/controls)
            display_text = token_text.replace('\n', '\\n').replace('\r', '\\r')
            prob = probs[i]
            print(f"{display_text:<20} | {prob:.6f}     | {i:<8}")
        print("-" * 50)
            
    else:
        print("Could not extract probabilities.")

if __name__ == "__main__":
    main()
