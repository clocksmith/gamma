"""Print top next-token probabilities for a prompt."""

import argparse
from pathlib import Path
import sys
import warnings

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


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
    parser.add_argument(
        "--top-k", type=positive_int, default=10, help="Number of tokens to print"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import numpy as np

    from src.engines import sampling_utils
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

    print("Predicting next token...")
    # predict_next(input_ids, attention_mask, temperature, top_k, top_p)
    # Using default values suitable for raw logits extraction
    try:
        result = engine.predict_next(
            input_ids, attention_mask, temperature=1.0, top_k=0, top_p=1.0
        )
    except Exception as exc:
        print(f"Prediction failed: {exc}")
        return 1

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

        top_k = args.top_k
        top_indices = np.argsort(probs)[-top_k:][::-1]

        print(f"\nTop {top_k} Probabilities for prompt: '{prompt}'")
        print("-" * 50)
        print(f"{'Token':<20} | {'Probability':<12} | {'Token ID':<8}")
        print("-" * 50)
        for i in top_indices:
            token_text = engine.get_token_text(int(i))
            # Clean up token text for display (remove newlines/controls)
            display_text = token_text.replace("\n", "\\n").replace("\r", "\\r")
            prob = probs[i]
            print(f"{display_text:<20} | {prob:.6f}     | {i:<8}")
        print("-" * 50)

    else:
        print("Could not extract probabilities.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
