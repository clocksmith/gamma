import random
from typing import List, Tuple, Dict, Any, Optional

from .engine_interface import LLMEngine
from . import config as cfg
from . import ui

def generate_choices(
    engine: LLMEngine,
    processed_logits: Any, # Engine-specific logits after filtering
    num_choices: int,
    permutation_length: int
    ) -> Tuple[List[List[str]], List[str]]:
    """
    Generates candidate next-token sequences for the player to choose from.

    Args:
        engine: The LLM engine instance.
        processed_logits: The final logits after all sampling filters.
        num_choices: How many options to present to the player.
        permutation_length: How many tokens deep each choice sequence should be.

    Returns:
        A tuple containing:
        - choices: A list of candidate token sequences (each sequence is a list of strings).
        - correct_sequence: The sequence ranked highest by the model.
    """
    # Get a sufficient number of top tokens after final filtering
    # We need enough to build diverse permutations. Request more than strictly needed.
    k_for_choices = max(num_choices * permutation_length, cfg.MAX_TOKENS_FOR_PROB_DISPLAY * 2, 10)
    top_tokens, _, top_ids = engine.get_probabilities_at_step(
        processed_logits, "final_processed", k=k_for_choices
    )

    if not top_tokens:
         # Handle edge case where no tokens are possible after filtering
         # This might happen with very restrictive Top-K/Top-P or unusual model states
         fallback_token = cfg.TOKEN_UNK
         return [[fallback_token] * permutation_length] * num_choices, [fallback_token] * permutation_length


    # The model's top choice is the correct answer
    correct_sequence = top_tokens[:permutation_length]

    # Ensure the correct sequence has the expected length, padding if necessary
    # (e.g., if fewer than `permutation_length` tokens were possible after filtering)
    while len(correct_sequence) < permutation_length:
        correct_sequence.append(cfg.TOKEN_PAD) # Or another suitable placeholder

    choices = [correct_sequence]
    available_tokens_pool = top_tokens[:k_for_choices] # Use the pool we fetched

    # Generate alternative, distinct choices
    attempts = 0
    max_attempts = 100 # Safety break

    while len(choices) < num_choices and attempts < max_attempts:
        attempts += 1
        # Create a new permutation. Sample *with replacement*? No, sample without.
        # Ensure the pool is large enough. If not, we might generate duplicates.
        pool_size = len(available_tokens_pool)
        if pool_size < permutation_length:
            # If pool is too small, pad the choices with placeholders
            sample_indices = random.sample(range(pool_size), pool_size)
            new_choice = [available_tokens_pool[i] for i in sample_indices]
            while len(new_choice) < permutation_length:
                new_choice.append(cfg.TOKEN_UNK) # Pad if pool exhausted
        else:
            # Sample indices from the available pool
            sample_indices = random.sample(range(pool_size), permutation_length)
            new_choice = [available_tokens_pool[i] for i in sample_indices]

        # Add if it's different from existing choices
        is_unique = True
        for existing_choice in choices:
            if new_choice == existing_choice:
                is_unique = False
                break
        if is_unique:
            choices.append(new_choice)

    # If we still don't have enough unique choices (e.g., very peaked distribution),
    # duplicate the correct answer or create simple variations if needed.
    while len(choices) < num_choices:
        # Simple fallback: add a slightly modified correct sequence or just duplicate
        if len(correct_sequence) > 1:
             variation = correct_sequence[:]
             variation[-1] = cfg.TOKEN_UNK # Simple modification
             if variation not in choices:
                   choices.append(variation)
             else: # If even that is taken, just duplicate correct
                   choices.append(correct_sequence[:]) # Append a copy
        else: # Cannot vary if only one token
             choices.append(correct_sequence[:])


    random.shuffle(choices)
    return choices, correct_sequence


def process_player_guess(
    engine: LLMEngine,
    prediction_result: Dict[str, Any],
    num_choices: int,
    permutation_length: int,
    current_sentence: str,
    verbose: bool
    ) -> Tuple[int, int, List[str], List[str]]:
    """
    Handles one round of player guessing: displays choices, gets input, shows results & probabilities.

    Args:
        engine: The LLM engine instance.
        prediction_result: The dictionary returned by engine.predict_next().
        num_choices: Number of choices to present.
        permutation_length: Length of token sequences in choices.
        current_sentence: The sentence context for the guess.
        verbose: Whether to show detailed probability explanations.

    Returns:
        A tuple: (score, max_score, chosen_sequence, correct_sequence).
        Returns (-1, -1, [], []) if the user quits.
    """
    processed_logits = prediction_result['logits_processed']

    # 1. Generate Choices
    choices, correct_sequence = generate_choices(
        engine, processed_logits, num_choices, permutation_length
    )

    # 2. Display Choices and Get Player Input
    valid_options = ui.display_player_choices(choices, current_sentence, permutation_length)
    user_choice_letter = ui.get_user_input("Your choice (A, B, C...)", valid_options, allow_quit=True)

    if user_choice_letter == cfg.SHORTCUT_QUIT:
        return -1, -1, [], [] # Signal quit

    chosen_index = ord(user_choice_letter) - ord('a')
    chosen_sequence = choices[chosen_index]

    # 3. Evaluate Score
    score = 0
    max_score = permutation_length
    for i in range(max_score):
        # Check bounds and compare tokens
        if i < len(chosen_sequence) and i < len(correct_sequence) and chosen_sequence[i] == correct_sequence[i]:
            score += 1
    is_perfect = score == max_score

    # 4. Display Guess Result
    ui.display_guess_result(chosen_sequence, correct_sequence, score, max_score, is_perfect)

    # 5. Display Detailed Probabilities (optional pause before this)
    input("\nPress Enter to see the probability breakdown...")

    # Extract logits/probabilities at different stages
    logits_raw = prediction_result.get('logits_raw')
    probs_raw = prediction_result.get('probabilities_raw')
    probs_temp = prediction_result.get('probabilities_temp')
    probs_top_k = prediction_result.get('probabilities_top_k')
    probs_processed = prediction_result.get('probabilities_processed') # From final logits

    # Show probabilities using the engine's method to ensure correct decoding
    if probs_raw is not None:
        tokens, probs, _ = engine.get_probabilities_at_step(probs_raw, "Raw (Unfiltered)", cfg.MAX_TOKENS_FOR_PROB_DISPLAY)
        ui.display_probability_stage("Raw (Unfiltered)", tokens, probs, cfg.MAX_TOKENS_FOR_PROB_DISPLAY, verbose)

    if probs_temp is not None:
        tokens, probs, _ = engine.get_probabilities_at_step(probs_temp, f"After Temperature ({cfg.DEFAULT_TEMPERATURE:.1f})", cfg.MAX_TOKENS_FOR_PROB_DISPLAY)
        ui.display_probability_stage(f"After Temperature ({cfg.DEFAULT_TEMPERATURE:.1f})", tokens, probs, cfg.MAX_TOKENS_FOR_PROB_DISPLAY, verbose)

    if probs_top_k is not None:
        tokens, probs, _ = engine.get_probabilities_at_step(probs_top_k, f"After Top-K ({cfg.DEFAULT_TOP_K})", cfg.MAX_TOKENS_FOR_PROB_DISPLAY)
        ui.display_probability_stage(f"After Top-K ({cfg.DEFAULT_TOP_K})", tokens, probs, cfg.MAX_TOKENS_FOR_PROB_DISPLAY, verbose)

    if probs_processed is not None:
        tokens, probs, _ = engine.get_probabilities_at_step(probs_processed, f"After Top-P ({cfg.DEFAULT_TOP_P:.2f}) [Final]", cfg.MAX_TOKENS_FOR_PROB_DISPLAY)
        ui.display_probability_stage(f"After Top-P ({cfg.DEFAULT_TOP_P:.2f}) [Final]", tokens, probs, cfg.MAX_TOKENS_FOR_PROB_DISPLAY, verbose)


    return score, max_score, chosen_sequence, correct_sequence