#!/usr/bin/env python3
"""
Core logic for the R-Eval / Routing Mode.
This module is responsible for getting responses from multiple LLMs
and using a router model to select the best one.
"""

from typing import List, Dict, Any
import argparse

# Use the existing gamma engine infrastructure
from src.engines.engine_factory import get_engine
from src.engines.classification_engine import SequenceClassificationEngine
from src.core.engine_interface import LLMEngine

def get_responses(prompt: str, candidate_models: List[Dict[str, str]], common_args: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Get responses from a list of candidate LLMs.
    """
    responses = []
    for model_info in candidate_models:
        print(f"\nGetting response from: {model_info['model']}")
        try:
            engine_args = argparse.Namespace(**common_args)
            engine_args.engine = model_info['engine']
            engine_args.model = model_info['model']

            engine: LLMEngine = get_engine(engine_args.engine, engine_args.model, vars(engine_args))
            engine.load()

            input_ids, attention_mask = engine.encode(prompt)
            generated_token_ids = []
            
            # Use a simple generation loop
            for _ in range(150):  # Generate up to 150 tokens
                prediction = engine.predict_next(input_ids, attention_mask, 0.7, 40, 0.9)
                next_token_id = prediction['next_token_id']

                if next_token_id == engine.get_eos_token_id():
                    break
                
                generated_token_ids.append(next_token_id)
                
                # Prepare for next iteration (leveraging KV cache)
                input_ids = engine.convert_from_numpy(np.array([[next_token_id]]))
                attention_mask = None # Not needed when using KV cache for single token

            response_text = engine.decode(generated_token_ids, skip_special_tokens=True)
            print(f"  Response: {response_text}")
            responses.append({"model": model_info['model'], "response": response_text})

        except Exception as e:
            print(f"  Failed to get response from {model_info['model']}: {e}")
            responses.append({"model": model_info['model'], "response": "Error generating response."})
    
    return responses


def route_responses(prompt: str, responses: List[Dict[str, str]], router_model_name: str) -> Dict[str, str]:
    """
    Use a router model to select the best response.

    Args:
        prompt: The original user prompt.
        responses: A list of responses from the candidate models.
        router_model_name: The name of the sequence classification model to use as the router.

    Returns:
        The dictionary of the winning model and its response.
    """
    print(f"Using router model: {router_model_name}")
    router_engine = SequenceClassificationEngine(router_model_name)
    router_engine.load()

    # Format the input for the router model
    # This typically involves combining the prompt and each response.
    router_inputs = [f"[INST] {prompt} [/INST] {r['response']}" for r in responses]

    scores = router_engine.predict(router_inputs)

    # The response with the highest score wins
    best_response_index = scores.index(max(scores))
    return responses[best_response_index]
