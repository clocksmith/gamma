import random
from typing import List, Tuple, Dict, Any, Optional

from src.core.engine_interface import LLMEngine
from src.core import config as cfg
from src.ui import displays as ui


def _is_code_like_or_url(token_text: str) -> bool:
    stripped_text = token_text.strip()
    if not stripped_text:
        return False
    if "/" in stripped_text or "\\" in stripped_text:
        return True
    if stripped_text.startswith("http:") or stripped_text.startswith("https:") or stripped_text.startswith("www."):
        return True
    if stripped_text.startswith("<") and stripped_text.endswith(">") and len(stripped_text) > 2 and any(c.isalpha() for c in stripped_text[1:-1]):
        return True
    code_symbols = ["{", "}", "[", "]", "(", ")", ";", "_", "#", "=", "+", "-", "*", "%", "&", "|", "^", "~", ":"]
    symbol_count = sum(1 for char in stripped_text if char in code_symbols)
    if symbol_count >= 2 and len(stripped_text) <= 10:
        return True
    if symbol_count > 0 and any(char.isdigit() for char in stripped_text):
        return True
    if "___" in stripped_text or "---" in stripped_text or "===" in stripped_text:
        return True
    if stripped_text.count("_") > 2 and len(stripped_text) > 5 and not any(c.isalpha() for c in stripped_text):
        return True
    return False


def generate_choices(
    engine: LLMEngine,
    processed_logits: Any,
    num_choices: int,
    permutation_length: int,
    focus_words: bool,
) -> Tuple[List[List[Tuple[str, int]]], List[Tuple[str, int]]]:
    k_for_pool = max(num_choices * permutation_length * (4 if focus_words else 2), cfg.MAX_TOKENS_FOR_PROB_DISPLAY * 2, 50)
    top_tokens_texts, _, top_tokens_ids = engine.get_probabilities_at_step(processed_logits, "final_for_choices", k=k_for_pool)

    if not top_tokens_texts:
        unk_token_id = engine.get_unk_token_id()
        if unk_token_id is None:
            unk_token_id = -1
        unk_token_text = engine.get_token_text(unk_token_id)
        unk_token_info = (unk_token_text, unk_token_id)
        return [[unk_token_info] * permutation_length] * num_choices, [unk_token_info] * permutation_length

    # Filter out special tokens from the pool
    filtered_pool = []
    special_token_patterns = ['<unused', '<pad>', '<eos>', '<bos>', '<unk>', '<mask>', '<cls>', '<sep>', '<ID:', '<DecodeErr:']
    
    for text, token_id in zip(top_tokens_texts, top_tokens_ids):
        # Skip special tokens
        is_special = any(text.startswith(pattern) for pattern in special_token_patterns)
        
        # Also skip tokens that look like special tokens with brackets
        if not is_special:
            # Check for [something] pattern which indicates special tokens
            if text.startswith('[') and text.endswith(']'):
                is_special = True
            # Check for tokens that are just punctuation or whitespace
            elif text.strip() in ['', '\n', '\t', '\r'] or text == '▁':
                is_special = True
        
        if not is_special:
            filtered_pool.append((text, token_id))
    
    # If we filtered out too much, try to get some reasonable tokens
    if len(filtered_pool) < num_choices * permutation_length:
        # Add back some tokens, but still skip the worst special tokens
        for text, token_id in zip(top_tokens_texts, top_tokens_ids):
            if text not in ['[multimodal]', '<unused', '<pad>', '<eos>', '<bos>']:
                if (text, token_id) not in filtered_pool:
                    filtered_pool.append((text, token_id))
                if len(filtered_pool) >= num_choices * permutation_length * 2:
                    break
    
    # If we still don't have enough, use what we have
    if not filtered_pool:
        # Last resort: use some simple tokens
        filtered_pool = [(" ", 0), (".", 1), (",", 2)]
    
    # Build the model's actual top sequence from filtered tokens
    model_actual_top_sequence_info: List[Tuple[str, int]] = []
    for i in range(permutation_length):
        if i < len(filtered_pool):
            model_actual_top_sequence_info.append(filtered_pool[i])
        else:
            # Use the first filtered token as padding if we run out
            model_actual_top_sequence_info.append(filtered_pool[0] if filtered_pool else (" ", 0))

    choices_list_info: List[List[Tuple[str, int]]] = [model_actual_top_sequence_info]
    full_token_pool_info: List[Tuple[str, int]] = filtered_pool
    distractor_candidate_pool_info: List[Tuple[str, int]]

    if focus_words:
        word_like_pool = []
        other_pool = []
        for text, token_id in full_token_pool_info:
            if engine.is_word_like_token(token_id, text) and not _is_code_like_or_url(text):
                word_like_pool.append((text, token_id))
            else:
                other_pool.append((text, token_id))
        distractor_candidate_pool_info = word_like_pool
        if len(word_like_pool) < num_choices * permutation_length:
            distractor_candidate_pool_info.extend(other_pool)
        if not distractor_candidate_pool_info:
            unk_id = engine.get_unk_token_id()
            if unk_id is None:
                unk_id = -1
            distractor_candidate_pool_info = [(engine.get_token_text(unk_id), unk_id)]
    else:
        distractor_candidate_pool_info = full_token_pool_info

    if not distractor_candidate_pool_info:
        unk_id = engine.get_unk_token_id()
        if unk_id is None:
            unk_id = -1
        distractor_candidate_pool_info = [(engine.get_token_text(unk_id), unk_id)]

    random.shuffle(distractor_candidate_pool_info)
    attempts = 0
    max_attempts_distractors = num_choices * permutation_length * 5

    while len(choices_list_info) < num_choices and attempts < max_attempts_distractors:
        attempts += 1
        if not distractor_candidate_pool_info: break
        current_distractor_info: List[Tuple[str, int]] = []
        temp_pool_for_this_choice = list(distractor_candidate_pool_info)
        for _ in range(permutation_length):
            if not temp_pool_for_this_choice:
                unk_id = engine.get_unk_token_id()
                if unk_id is None:
                    unk_id = -1
                current_distractor_info.append((engine.get_token_text(unk_id), unk_id))
                continue
            sampled_token_info_tuple = random.choice(temp_pool_for_this_choice)
            current_distractor_info.append(sampled_token_info_tuple)
            if len(temp_pool_for_this_choice) > 1:
                try: temp_pool_for_this_choice.remove(sampled_token_info_tuple)
                except ValueError: pass
        if current_distractor_info not in choices_list_info:
            choices_list_info.append(current_distractor_info)

    while len(choices_list_info) < num_choices:
        variation = list(model_actual_top_sequence_info)
        if permutation_length > 0 and len(distractor_candidate_pool_info) > 1:
            idx_to_change = random.randrange(permutation_length)
            original_token_info = variation[idx_to_change]
            new_token_options = [t_info for t_info in distractor_candidate_pool_info if t_info != original_token_info]
            if new_token_options: variation[idx_to_change] = random.choice(new_token_options)
            else: variation[idx_to_change] = random.choice(distractor_candidate_pool_info)
            choices_list_info.append(variation)
        else:
            choices_list_info.append(list(model_actual_top_sequence_info))

    random.shuffle(choices_list_info)
    return choices_list_info, model_actual_top_sequence_info


def process_player_guess(
    engine: LLMEngine,
    prediction_result: Dict[str, Any],
    game_args: Any,
    current_sentence_text: str,
    previously_explained_tokens: set,
) -> Tuple[int, int, List[Tuple[str, int]], List[Tuple[str, int]]]:
    processed_logits = prediction_result["logits_processed"]
    choices_info, correct_sequence_info = generate_choices(engine, processed_logits, game_args.num_choices, game_args.permutation_length, game_args.focus_words)
    choices_texts_for_display = [[token_info[0] for token_info in choice_seq] for choice_seq in choices_info]

    if game_args.focus_words:
        for choice_seq_info in choices_info:
            for token_text, token_id in choice_seq_info:
                ui.display_token_explanation_if_needed(engine, token_id, token_text, previously_explained_tokens, is_part_of_player_choice=True)

    valid_options_letters = ui.display_player_choices(choices_texts_for_display, current_sentence_text, game_args.permutation_length, game_args.focus_words)
    user_choice_letter = ui.get_user_input("Your choice (A, B, C...)", valid_options_letters, allow_quit=True)

    if user_choice_letter == cfg.SHORTCUT_QUIT:
        return -1, -1, [], []

    chosen_index = ord(user_choice_letter.lower()) - ord("a")
    chosen_sequence_info = choices_info[chosen_index]
    score = 0
    max_possible_score = game_args.permutation_length
    for i in range(max_possible_score):
        if i < len(chosen_sequence_info) and i < len(correct_sequence_info) and chosen_sequence_info[i][1] == correct_sequence_info[i][1]:
            score += 1
    is_perfect_match = score == max_possible_score

    ui.display_guess_result([txt_id[0] for txt_id in chosen_sequence_info], [txt_id[0] for txt_id in correct_sequence_info], score, max_possible_score, is_perfect_match)

    if ui.get_user_input(f"Press Enter to see probability breakdown, or '{cfg.SHORTCUT_QUIT}' to skip to next round", allow_empty=True, allow_quit=True) == cfg.SHORTCUT_QUIT:
        return score, max_possible_score, chosen_sequence_info, correct_sequence_info

    prob_data_map = {
        "Raw (Unfiltered)": prediction_result.get("probabilities_raw"),
        f"After Temperature ({game_args.temperature:.2f})": prediction_result.get("probabilities_temp"),
        f"After Top-K ({game_args.top_k})": prediction_result.get("probabilities_top_k"),
        f"After Top-P ({game_args.top_p:.2f}) [Final]": prediction_result.get("probabilities_processed"),
    }

    # Collect all stages data for grid display
    stages_data = []
    for stage_name, prob_source_data in prob_data_map.items():
        if prob_source_data is not None:
            token_texts_for_stage, prob_values_for_stage, _ = engine.get_probabilities_at_step(prob_source_data, stage_name, cfg.MAX_TOKENS_FOR_PROB_DISPLAY)
            # Check if probabilities are all zero, which indicates a problem.
            if not any(p > 1e-9 for p in prob_values_for_stage): # Check if effectively all zero
                 print(ui.color_text(f"  Warning: Probabilities for stage '{stage_name}' are all (near) zero. Model output may be compromised.", cfg.COLOR_YELLOW))
            stages_data.append((stage_name, token_texts_for_stage, prob_values_for_stage))
        else:
            stages_data.append((stage_name, [], []))
            if game_args.verbose:
                print(ui.color_text(f"  Note: Probability data for stage '{stage_name}' is not available from the engine.", cfg.COLOR_YELLOW))
    
    # Display all 4 stages in a 2x2 grid
    ui.display_probability_stages_grid(stages_data, cfg.MAX_TOKENS_FOR_PROB_DISPLAY, game_args.verbose)


    return score, max_possible_score, chosen_sequence_info, correct_sequence_info