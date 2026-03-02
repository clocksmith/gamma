#!/usr/bin/env python3
"""
CLI for the R-Eval / Routing Mode.
This tool takes a prompt and a list of models, gets responses from each, 
and uses a router model to determine the best response.
"""

import argparse

# Add project root to the path to allow importing from src
try:
    from tools._path_setup import ensure_project_root_on_path
except ImportError:
    from _path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from src.core.menu.routing_logic import get_responses, route_responses

def main():
    parser = argparse.ArgumentParser(description="Rapid LLM Evaluation and Routing Framework CLI")
    parser.add_argument("--prompt", type=str, required=True, help="The user prompt to send to the models.")
    parser.add_argument("--models", nargs='+', required=True, help="List of candidate models (e.g., pytorch:google/gemma-2b)")
    parser.add_argument("--router", type=str, default="deberta-v3-large-zeroshot-nli-medqa", help="The router model to use.")
    
    # Add common engine args that might be needed by the routing_logic
    parser.add_argument("--hf-token", type=str, default=None, help="Hugging Face Hub token for gated models")
    parser.add_argument("--pytorch-device-map", type=str, default="auto", help="PyTorch: Device map")

    args = parser.parse_args()

    # Prepare model list for the routing logic
    candidate_models = []
    for model_spec in args.models:
        if ":" in model_spec:
            engine, model = model_spec.split(":", 1)
        else:
            engine = "pytorch" # Default to pytorch
            model = model_spec
        candidate_models.append({"engine": engine, "model": model})

    print("--- Getting responses from candidate models ---")
    responses = get_responses(args.prompt, candidate_models, vars(args))
    print("\n--- Candidate Responses ---")
    for i, resp in enumerate(responses):
        print(f"  Model {i+1}: {resp['model']}")
        print(f"  Response: {resp['response']}\n")

    print("--- Routing responses to find the best one ---")
    best_response = route_responses(args.prompt, responses, args.router)

    print("\n--- 🏆 Best Response ---")
    print(f"  Winning Model: {best_response['model']}")
    print(f"  Response: {best_response['response']}")

if __name__ == "__main__":
    main()
