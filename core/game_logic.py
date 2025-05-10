import random
from typing import List, Tuple, Dict, Any, Optional

from .engine_interface import LLMEngine
from . import config as cfg
from . import ui


def _is_code_like_or_url(token_text: str) -> bool:
    """Heuristic to identify tokens that look like code, paths, or URLs."""
    stripped_text = token_text.strip()
    if not stripped_text:
        return False

    if "/" in stripped_text or "\\" in stripped_text:
        return True
    if (
        stripped_text.startswith("http:")
        or stripped_text.startswith("https:")
        or stripped_text.startswith("www.")
    ):
        return True
    if (
        stripped_text.startswith("<")
        and stripped_text.endswith(">")
        and len(stripped_text) > 2
        and any(c.isalpha() for c in stripped_text[1:-1])
    ):
        return True  # Basic HTML/XML tag

    code_symbols = [
        "{",
        "}",
        "[",
        "]",
        "(",
        ")",
        ";",
        "_",
        "#",
        "=",
        "+",
        "-",
        "*",
        "%",
        "&",
        "|",
        "^",
        "~",
        ":",
    ]
    symbol_count = sum(1 for char in stripped_text if char in code_symbols)

    if symbol_count >= 2 and len(stripped_text) <= 10:
        return True
    if symbol_count > 0 and any(char.isdigit() for char in stripped_text):
        return True
    if "___" in stripped_text or "---" in stripped_text or "===" in stripped_text:
        return True
    if (
        stripped_text.count("_") > 2
        and len(stripped_text) > 5
        and not any(c.isalpha() for c in stripped_text)
    ):
        return True
    return False


def generate_choices(
    engine: LLMEngine,
    processed_logits: Any,
    num_choices: int,
    permutation_length: int,
    focus_words: bool,
) -> Tuple[
    List[List[Tuple[str, int]]], List[Tuple[str, int]]
]:  # Returns choices with (text, id) tuples
    """
    Generates candidate next-token sequences (text and ID) for the player.
    The model's actual top choice is always preserved.
    """
    k_for_pool = max(
        num_choices * permutation_length * (4 if focus_words else 2),
        cfg.MAX_TOKENS_FOR_PROB_DISPLAY * 2,
        25,
    )

    top_tokens_texts, _, top_tokens_ids = engine.get_probabilities_at_step(
        processed_logits, "final_for_choices", k=k_for_pool
    )

    if not top_tokens_texts:
        unk_token_text = engine.get_token_text(
            getattr(engine.tokenizer, "unk_token_id", -1)
        )  # Get UNK from engine
        unk_token_info = (unk_token_text, getattr(engine.tokenizer, "unk_token_id", -1))
        return [[unk_token_info] * permutation_length] * num_choices, [
            unk_token_info
        ] * permutation_length

    # The model's actual top sequence (text, id)
    model_actual_top_sequence_info: List[Tuple[str, int]] = []
    for i in range(permutation_length):
        if i < len(top_tokens_texts):
            model_actual_top_sequence_info.append(
                (top_tokens_texts[i], top_tokens_ids[i])
            )
        else:
            pad_token_text = engine.get_token_text(
                getattr(engine.tokenizer, "pad_token_id", -2)
            )
            pad_token_id = getattr(engine.tokenizer, "pad_token_id", -2)
            model_actual_top_sequence_info.append((pad_token_text, pad_token_id))

    choices_list_info: List[List[Tuple[str, int]]] = [model_actual_top_sequence_info]

    full_token_pool_info: List[Tuple[str, int]] = list(
        zip(top_tokens_texts, top_tokens_ids)
    )
    distractor_candidate_pool_info: List[Tuple[str, int]]

    if focus_words:
        word_like_pool = []
        other_pool = []
        for text, token_id in full_token_pool_info:
            if engine.is_word_like_token(token_id, text) and not _is_code_like_or_url(
                text
            ):
                word_like_pool.append((text, token_id))
            else:
                other_pool.append((text, token_id))

        distractor_candidate_pool_info = word_like_pool
        if len(word_like_pool) < num_choices * permutation_length:
            distractor_candidate_pool_info.extend(other_pool)
        if not distractor_candidate_pool_info:
            unk_id = getattr(engine.tokenizer, "unk_token_id", -1)
            distractor_candidate_pool_info = [(engine.get_token_text(unk_id), unk_id)]
    else:
        distractor_candidate_pool_info = full_token_pool_info

    if not distractor_candidate_pool_info:  # Absolute fallback
        unk_id = getattr(engine.tokenizer, "unk_token_id", -1)
        distractor_candidate_pool_info = [(engine.get_token_text(unk_id), unk_id)]

    random.shuffle(distractor_candidate_pool_info)

    attempts = 0
    max_attempts_distractors = num_choices * permutation_length * 5

    while len(choices_list_info) < num_choices and attempts < max_attempts_distractors:
        attempts += 1
        if not distractor_candidate_pool_info:
            break

        current_distractor_info: List[Tuple[str, int]] = []
        temp_pool_for_this_choice = list(distractor_candidate_pool_info)

        for _ in range(permutation_length):
            if not temp_pool_for_this_choice:
                unk_id = getattr(engine.tokenizer, "unk_token_id", -1)
                current_distractor_info.append((engine.get_token_text(unk_id), unk_id))
                continue

            sampled_token_info_tuple = random.choice(temp_pool_for_this_choice)
            current_distractor_info.append(sampled_token_info_tuple)
            # To ensure tokens within ONE distractor are unique if possible (and pool allows)
            if len(temp_pool_for_this_choice) > 1:  # Only remove if other options exist
                try:
                    temp_pool_for_this_choice.remove(sampled_token_info_tuple)
                except ValueError:
                    pass  # Item might have been duplicated in original pool

        if current_distractor_info not in choices_list_info:
            choices_list_info.append(current_distractor_info)

    while len(choices_list_info) < num_choices:  # Fallback fill
        variation = list(model_actual_top_sequence_info)
        if permutation_length > 0 and len(distractor_candidate_pool_info) > 1:
            idx_to_change = random.randrange(permutation_length)
            original_token_info = variation[idx_to_change]

            new_token_options = [
                t_info
                for t_info in distractor_candidate_pool_info
                if t_info != original_token_info
            ]
            if new_token_options:
                variation[idx_to_change] = random.choice(new_token_options)
            else:
                variation[idx_to_change] = random.choice(
                    distractor_candidate_pool_info
                )  # Fallback to any

            choices_list_info.append(
                variation
            )  # Allow duplicates if all unique variations exhausted
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
) -> Tuple[
    int, int, List[Tuple[str, int]], List[Tuple[str, int]]
]:  # Returns score, max, chosen (txt,id), correct (txt,id)

    processed_logits = prediction_result["logits_processed"]

    choices_info, correct_sequence_info = generate_choices(
        engine,
        processed_logits,
        game_args.num_choices,
        game_args.permutation_length,
        game_args.focus_words,
    )

    # Extract just texts for display_player_choices
    choices_texts_for_display = [
        [token_info[0] for token_info in choice_seq] for choice_seq in choices_info
    ]

    if (
        game_args.focus_words
    ):  # Explain special tokens within choices before player guesses
        for choice_seq_info in choices_info:
            for token_text, token_id in choice_seq_info:
                ui.display_token_explanation_if_needed(
                    engine,
                    token_id,
                    token_text,
                    previously_explained_tokens,
                    is_part_of_player_choice=True,
                )

    valid_options_letters = ui.display_player_choices(
        choices_texts_for_display,
        current_sentence_text,
        game_args.permutation_length,
        game_args.focus_words,
    )
    user_choice_letter = ui.get_user_input(
        "Your choice (A, B, C...)", valid_options_letters, allow_quit=True
    )

    if user_choice_letter == cfg.SHORTCUT_QUIT:
        return -1, -1, [], []

    chosen_index = ord(user_choice_letter.lower()) - ord("a")
    chosen_sequence_info = choices_info[chosen_index]  # This is List[Tuple[str, int]]

    score = 0
    max_possible_score = game_args.permutation_length
    for i in range(max_possible_score):
        if (
            i < len(chosen_sequence_info)
            and i < len(correct_sequence_info)
            and chosen_sequence_info[i][1] == correct_sequence_info[i][1]
        ):  # Compare by token ID for accuracy
            score += 1
    is_perfect_match = score == max_possible_score

    ui.display_guess_result(
        [txt_id[0] for txt_id in chosen_sequence_info],
        [txt_id[0] for txt_id in correct_sequence_info],
        score,
        max_possible_score,
        is_perfect_match,
    )

    if (
        ui.get_user_input(
            f"Press Enter to see probability breakdown, or '{cfg.SHORTCUT_QUIT}' to skip to next round",
            allow_empty=True,
            allow_quit=True,
        )
        == cfg.SHORTCUT_QUIT
    ):
        return score, max_possible_score, chosen_sequence_info, correct_sequence_info

    prob_data_map = {
        "Raw (Unfiltered)": prediction_result.get("probabilities_raw"),
        f"After Temperature ({game_args.temperature:.2f})": prediction_result.get(
            "probabilities_temp"
        ),
        f"After Top-K ({game_args.top_k})": prediction_result.get(
            "probabilities_top_k"
        ),
        f"After Top-P ({game_args.top_p:.2f}) [Final Distribution]": prediction_result.get(
            "probabilities_processed"
        ),
    }

    for stage_name, prob_source_data in prob_data_map.items():
        if prob_source_data is not None:
            token_texts_for_stage, prob_values_for_stage, _ = (
                engine.get_probabilities_at_step(
                    prob_source_data, stage_name, cfg.MAX_TOKENS_FOR_PROB_DISPLAY
                )
            )
            ui.display_probability_stage(
                stage_name,
                token_texts_for_stage,
                prob_values_for_stage,
                cfg.MAX_TOKENS_FOR_PROB_DISPLAY,
                game_args.verbose,
            )

    return score, max_possible_score, chosen_sequence_info, correct_sequence_info
