import torch
import random
import time
import os
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Literal, List, Tuple, Dict, Optional

###########################################
# Model Configuration
###########################################
# Parameters to GB (approx @ bfloat16/fp16): 1B params ~ 2GB
# Recommended RAM is a rough estimate for inference, including KV cache, activations, OS, etc.
# It can be VRAM on discrete GPUs or Unified RAM on systems like Apple Silicon.
MODEL_INFO = {
    "google/gemma-3-1b-it": {
        "desc": "1B, Instruct, versatile.",
        "params_b": 1.0,
        "raw_model_gb": 2.0,
        "rec_ram_gb": "4-6GB",
    },
    "google/gemma-3-4b-it": {
        "desc": "4B, Instruct, good balance.",
        "params_b": 4.0,
        "raw_model_gb": 8.0,
        "rec_ram_gb": "12-16GB",
    },
    "google/gemma-3-12b-it": {
        "desc": "12B, Instruct, powerful.",
        "params_b": 12.0,
        "raw_model_gb": 24.0,
        "rec_ram_gb": "32-48GB",
    },
    "google/gemma-3-27b-it": {
        "desc": "27B, Instruct, very strong.",
        "params_b": 27.0,
        "raw_model_gb": 54.0,
        "rec_ram_gb": "64-96GB",
    },
    "google/gemma-3-1b": {
        "desc": "1B, Base, for fine-tuning.",
        "params_b": 1.0,
        "raw_model_gb": 2.0,
        "rec_ram_gb": "4-6GB",
    },
    "google/gemma-3-4b": {
        "desc": "4B, Base.",
        "params_b": 4.0,
        "raw_model_gb": 8.0,
        "rec_ram_gb": "12-16GB",
    },
    "google/gemma-3-12b": {
        "desc": "12B, Base.",
        "params_b": 12.0,
        "raw_model_gb": 24.0,
        "rec_ram_gb": "32-48GB",
    },
    "google/gemma-3-27b": {
        "desc": "27B, Base.",
        "params_b": 27.0,
        "raw_model_gb": 54.0,
        "rec_ram_gb": "64-96GB",
    },
    "google/gemma-2-2b-it": {
        "desc": "Legacy 2B, Instruct.",
        "params_b": 2.0,
        "raw_model_gb": 4.0,
        "rec_ram_gb": "6-8GB",
    },
    "google/gemma-2-7b-it": {
        "desc": "Legacy 7B, Instruct.",
        "params_b": 7.0,
        "raw_model_gb": 14.0,
        "rec_ram_gb": "20-28GB",
    },
    "google/gemma-2-9b-it": {
        "desc": "Legacy 9B, Instruct.",
        "params_b": 9.0,
        "raw_model_gb": 18.0,
        "rec_ram_gb": "24-36GB",
    },
    "google/gemma-2-2b": {
        "desc": "Legacy 2B, Base.",
        "params_b": 2.0,
        "raw_model_gb": 4.0,
        "rec_ram_gb": "6-8GB",
    },
    "google/gemma-2-7b": {
        "desc": "Legacy 7B, Base.",
        "params_b": 7.0,
        "raw_model_gb": 14.0,
        "rec_ram_gb": "20-28GB",
    },
    "google/gemma-2-9b": {
        "desc": "Legacy 9B, Base.",
        "params_b": 9.0,
        "raw_model_gb": 18.0,
        "rec_ram_gb": "24-36GB",
    },
    "google/gemma-3n-e4b-it": {
        "desc": "New 4B, Instruct, efficient.",
        "params_b": 4.0,
        "raw_model_gb": 8.0,
        "rec_ram_gb": "12-16GB",
    },
}
RAM_EXPLANATION_SHOWN = False  # Flag to show RAM explanation only once

GEMMA_MODELS = list(MODEL_INFO.keys())
MODEL_NAME_DEFAULT = GEMMA_MODELS[0]

TEMPERATURE = 0.7
TOP_K = 8
TOP_P = 0.95
MAX_PROB_DISPLAY = 16

###########################################
# Game Configuration
###########################################
MAX_ROUNDS = 5
NUM_CHOICES = 4
PERMUTATION_LENGTH = 3  # For Hard/Expert Mode: Length of sequence to predict
SHOW_ATTENTION = True

TUTORIAL_PROB_DISPLAY_MODE: Literal["before", "after"] = "before"
TUTORIAL_PROB_STAGES_TO_SHOW: List[Literal["raw", "temp", "top_k", "top_p"]] = [
    "raw",
    "temp",
    "top_k",
    "top_p",
]

###########################################
# Terminal Colors Configuration
###########################################
RED, GREEN, BLUE, YELLOW = "\033[91m", "\033[92m", "\033[94m", "\033[93m"
MAGENTA_LIGHT, MAGENTA_MEDIUM, MAGENTA_BRIGHT, MAGENTA_INTENSE = (
    "\033[38;5;54m",
    "\033[38;5;91m",
    "\033[38;5;127m",
    "\033[38;5;164m",
)
RESET = "\033[0m"

USE_COLORS = True
if os.name == "nt":
    try:
        import colorama

        colorama.init()
    except ImportError:
        if os.environ.get("TERM") != "xterm":
            USE_COLORS = False

# --- Core LLM Utility Functions ---


def load_model_and_tokenizer(
    model_name: str,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Loads a Hugging Face model and tokenizer, displaying info and RAM estimates."""
    global RAM_EXPLANATION_SHOWN
    info = MODEL_INFO.get(
        model_name,
        {"desc": "N/A", "params_b": "N/A", "raw_model_gb": "N/A", "rec_ram_gb": "N/A"},
    )
    print(f"Loading model '{model_name}' ({info['desc']})...")
    print(
        f"  Parameters: ~{info['params_b']}B | Raw Model Size: ~{info['raw_model_gb']}GB | Recommended System RAM: {info['rec_ram_gb']}"
    )
    if not RAM_EXPLANATION_SHOWN:
        print(
            f"  {YELLOW}Note: 'RAM' can be dedicated VRAM (GPUs) or Unified RAM (e.g., Apple Silicon).{RESET}"
        )
        RAM_EXPLANATION_SHOWN = True
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Using bfloat16 for supported models, good balance of speed/memory
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            attn_implementation="eager",
            torch_dtype=torch.bfloat16,
        )
        print("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        print(f"{RED}Error loading model '{model_name}': {e}{RESET}")
        print(
            "Ensure you have accepted model terms on Hugging Face and are logged in (`huggingface-cli login`)."
        )
        print(
            f"Also ensure your system meets the RAM requirements (approx. {info['rec_ram_gb']})."
        )
        raise


def prepare_inputs(
    input_text: str, tokenizer: AutoTokenizer, device: torch.device
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Tokenizes input text and prepares tensors for the model."""
    encoded_input = tokenizer.encode_plus(input_text, return_tensors="pt")
    input_ids = encoded_input["input_ids"].to(device)
    attention_mask = encoded_input["attention_mask"].to(device)
    return input_ids, attention_mask


def _apply_temperature(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    """Applies temperature scaling to logits."""
    return logits / (temperature + 1e-7)


def _apply_top_k_filtering(logits: torch.Tensor, top_k: int) -> torch.Tensor:
    """Applies top-k filtering to logits."""
    effective_top_k = min(top_k, logits.size(-1))  # Ensure top_k is not > vocab size
    top_k_values, top_k_indices = torch.topk(logits, effective_top_k, dim=-1)
    logits_after_top_k = torch.full_like(logits, float("-inf"))
    logits_after_top_k.scatter_(-1, top_k_indices, top_k_values)
    return logits_after_top_k


def _apply_top_p_filtering(logits: torch.Tensor, top_p: float) -> torch.Tensor:
    """Applies top-p (nucleus) filtering to logits."""
    sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
    # Ensure logits are float for softmax, especially after potential -inf from top_k
    cumulative_probs = torch.cumsum(
        torch.softmax(sorted_logits.float(), dim=-1), dim=-1
    )

    sorted_indices_to_remove = cumulative_probs > top_p
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = (
        0  # Never remove the most probable if it's the only one considered
    )

    final_logits_sorted = sorted_logits.clone()
    final_logits_sorted[sorted_indices_to_remove] = float("-inf")

    unsorted_final_logits = torch.full_like(logits, float("-inf"))
    unsorted_final_logits.scatter_(-1, sorted_indices, final_logits_sorted)
    return unsorted_final_logits


def get_logits_at_sampling_stages(
    raw_logits: torch.Tensor, temperature: float, top_k: int, top_p: float
) -> Dict[str, torch.Tensor]:
    """Returns logits at each stage of the sampling pipeline for display."""
    logits_after_temp = _apply_temperature(raw_logits, temperature)
    logits_after_top_k = _apply_top_k_filtering(logits_after_temp, top_k)
    logits_after_top_p = _apply_top_p_filtering(
        logits_after_top_k, top_p
    )  # Top-P is applied to Top-K's result
    return {
        "raw": raw_logits,
        "temp": logits_after_temp,
        "top_k": logits_after_top_k,
        "top_p": logits_after_top_p,  # This is the final distribution after all steps
    }


def _decode_and_clean_token_ids(
    token_ids: List[int],
    tokenizer: AutoTokenizer,
    for_sentence_continuation: bool = False,
) -> List[str]:
    """Decodes raw token IDs into human-readable strings, with cleaning options."""
    # ... (implementation from previous version, assumed correct)
    decoded_tokens: List[str] = []
    for token_id in token_ids:
        raw_text = tokenizer.decode([token_id], skip_special_tokens=False)
        if for_sentence_continuation:
            decoded_tokens.append(raw_text)
            continue
        display_text = raw_text.strip().replace(" ", "").replace("_", "")
        if not display_text:
            if raw_text == "\n":
                display_text = "[NEWLINE]"
            elif raw_text == "\t":
                display_text = "[TAB]"
            elif raw_text == "\r":
                display_text = "[CR]"
            elif raw_text.strip() == "":
                display_text = f"[SPACE_{token_id}]"
            elif token_id in tokenizer.all_special_ids:
                special_map = {
                    tokenizer.eos_token_id: "<EOS>",
                    tokenizer.pad_token_id: "<PAD>",
                    tokenizer.bos_token_id: "<BOS>",
                    tokenizer.unk_token_id: "<UNK>",
                    tokenizer.mask_token_id: "<MASK>",
                }
                display_text = special_map.get(token_id, f"<SPECIAL_{token_id}>")
            else:
                display_text = f"<UNDEC_{token_id}>"
        decoded_tokens.append(display_text)
    return decoded_tokens


def get_top_tokens_and_probs(
    logits: torch.Tensor, tokenizer: AutoTokenizer, k: Optional[int] = None
) -> Tuple[List[str], List[float], List[int]]:
    """Retrieves top-k tokens, their probabilities, and IDs from logits."""
    # ... (implementation from previous version, assumed correct)
    probabilities = torch.softmax(logits.float(), dim=-1)
    effective_k = (
        min(k, probabilities.size(-1)) if k is not None else probabilities.size(-1)
    )
    top_k_values, top_k_indices = torch.topk(probabilities, effective_k, dim=-1)
    token_ids_list = top_k_indices[0].tolist()
    decoded_tokens_display = _decode_and_clean_token_ids(token_ids_list, tokenizer)
    top_k_probs = top_k_values[0].tolist()
    return decoded_tokens_display, top_k_probs, token_ids_list


@torch.no_grad()
def get_model_outputs(
    model: AutoModelForCausalLM, input_ids: torch.Tensor, attention_mask: torch.Tensor
) -> object:
    """Performs a forward pass and returns model outputs."""
    return model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        output_attentions=SHOW_ATTENTION,
    )


# --- Display & UI Functions ---
def color_print(text: str, color: str) -> None:
    """Prints text with ANSI color."""
    print(color + text + RESET if USE_COLORS else text)


def wait_for_player(prompt_text: str = "\nPress Enter to continue...") -> None:
    """Pauses for player."""
    input(prompt_text)


def get_attention_heatmap(
    outputs: object, input_ids: torch.Tensor, tokenizer: AutoTokenizer
) -> Optional[Tuple[List[str], List[float], str]]:
    """Extracts and normalizes attention weights for visualization."""
    # ... (implementation from previous version, assumed correct)
    if not (SHOW_ATTENTION and hasattr(outputs, "attentions") and outputs.attentions):
        return None
    last_layer_attentions = outputs.attentions[-1]
    if input_ids.shape[1] <= 1:
        return (
            None,
            None,
            _decode_and_clean_token_ids([input_ids[0, -1].item()], tokenizer)[0],
        )
    attention_weights = last_layer_attentions[0, :, -1, :-1].mean(dim=0)
    if attention_weights.numel() == 0:
        return (
            None,
            None,
            _decode_and_clean_token_ids([input_ids[0, -1].item()], tokenizer)[0],
        )
    context_ids = input_ids[0, :-1].tolist()
    context_display = _decode_and_clean_token_ids(context_ids, tokenizer)
    attending_token_display = _decode_and_clean_token_ids(
        [input_ids[0, -1].item()], tokenizer
    )[0]
    norm_attn = (attention_weights / (attention_weights.max() + 1e-7)).tolist()
    return context_display, norm_attn, attending_token_display


def color_attention_text(
    tokens: List[str], normalized_attention: List[float]
) -> Tuple[str, str]:
    """Creates a color-coded text representation of attention weights."""
    # ... (implementation from previous version, assumed correct)
    if not tokens or not normalized_attention:
        return "No attention data.", ""
    output = []
    for token, score in zip(tokens, normalized_attention):
        if USE_COLORS:
            if score < 0.2:
                c = MAGENTA_LIGHT
            elif score < 0.4:
                c = MAGENTA_MEDIUM
            elif score < 0.6:
                c = MAGENTA_BRIGHT
            else:
                c = MAGENTA_INTENSE
            output.append(f"{c}{token}{RESET} ({score:.2f})")
        else:
            output.append(f"{token}{'*'*int(score*5)} ({score:.2f})")
    return " ".join(output), "Heatmap: 0 (low) to 1 (high)\n"


def display_probabilities(
    logits_stages_dict: Dict[str, torch.Tensor],
    tokenizer: AutoTokenizer,
    stages_to_display: List[str],
    title_prefix: str,
) -> None:
    """Displays token probabilities at specified filtering stages."""
    print(f"\n--- {title_prefix} (Top {MAX_PROB_DISPLAY}) ---")
    stage_descriptions = {
        "raw": "Raw Logits (Model Output)",
        "temp": f"After Temperature ({TEMPERATURE:.1f})",
        "top_k": f"After Top-K ({TOP_K})",
        "top_p": f"After Top-P ({TOP_P:.2f}) (Final Distribution)",
    }
    for i, stage_key in enumerate(stages_to_display):
        if (
            stage_key in logits_stages_dict
            and logits_stages_dict[stage_key] is not None
        ):
            print(
                f"\n{BLUE}{i+1}. {stage_descriptions.get(stage_key, stage_key.capitalize())}:{RESET}"
            )
            tokens_disp, probs_disp, _ = get_top_tokens_and_probs(
                logits_stages_dict[stage_key], tokenizer, k=MAX_PROB_DISPLAY
            )
            for token_str_val, prob_val_num in zip(tokens_disp, probs_disp):
                print(f"    '{token_str_val}': {prob_val_num:.6f}")


# --- Game Mode Specific Logic ---


def get_true_model_sequence(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    current_input_ids: torch.Tensor,
    current_attention_mask: torch.Tensor,
    length: int,
) -> Tuple[List[str], List[int]]:
    """Generates the model's true N-step sequence by always picking the top token after full sampling."""
    # ... (implementation from previous version, assumed correct)
    seq_display, seq_ids = [], []
    temp_input_ids, temp_attn_mask = (
        current_input_ids.clone(),
        current_attention_mask.clone(),
    )
    for _ in range(length):
        outputs = get_model_outputs(model, temp_input_ids, temp_attn_mask)
        logits_next = outputs.logits[:, -1, :]
        final_logits = get_logits_at_sampling_stages(
            logits_next, TEMPERATURE, TOP_K, TOP_P
        )[
            "top_p"
        ]  # Use final 'top_p' stage
        next_token_id = torch.argmax(final_logits, dim=-1).item()
        seq_ids.append(next_token_id)
        seq_display.append(_decode_and_clean_token_ids([next_token_id], tokenizer)[0])
        if next_token_id == tokenizer.eos_token_id:
            break
        temp_input_ids = torch.cat(
            [temp_input_ids, torch.tensor([[next_token_id]], device=model.device)],
            dim=-1,
        )
        temp_attn_mask = torch.cat(
            [temp_attn_mask, torch.ones_like(temp_input_ids[:, :1])], dim=-1
        )
    return seq_display, seq_ids


def _get_player_sequence_choice(prompt: str, choices: List[List[str]]) -> int:
    """Helper to get validated player choice for sequence-based games."""
    print(prompt)
    for i, choice_tokens in enumerate(choices):
        print(f"  {chr(ord('A') + i)}) '{' '.join(choice_tokens)}'")

    chosen_idx = -1
    while True:
        user_char_input = (
            input(f"\nYour choice (A-{chr(ord('A') + len(choices) - 1)}): ")
            .strip()
            .upper()
        )
        if user_char_input and "A" <= user_char_input[0] <= chr(
            ord("A") + len(choices) - 1
        ):
            chosen_idx = ord(user_char_input[0]) - ord("A")
            break
        else:
            print("Invalid input. Please enter a letter corresponding to a choice.")
    return chosen_idx


def _run_sequence_prediction_game_round(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    current_input_ids: torch.Tensor,
    current_attention_mask: torch.Tensor,
    current_sentence_str: str,
    round_num: int,
    game_mode: Literal["hard", "expert"],
) -> Tuple[int, int, torch.Tensor, torch.Tensor, str, bool]:
    """Handles a single round for Hard or Expert mode."""
    print(f"\n{'-'*20} Round {round_num + 1} of {MAX_ROUNDS} {'-'*20}")
    color_print(
        f'Current Sentence: "{current_sentence_str.replace("_", " ").strip()}"', BLUE
    )

    outputs_for_first_token = get_model_outputs(
        model, current_input_ids, current_attention_mask
    )
    logits_for_first_token = outputs_for_first_token.logits[:, -1, :]

    # Attention is always shown before any guess in sequence modes
    attention_data = get_attention_heatmap(
        outputs_for_first_token, current_input_ids, tokenizer
    )
    if attention_data:
        ctx_tokens, norm_attn, attend_token = attention_data
        if ctx_tokens and norm_attn:
            attn_text, scale = color_attention_text(ctx_tokens, norm_attn)
            print(f"\n--- Attention (for predicting 1st token of sequence) ---")
            print(
                f"{scale}Attention of '{attend_token}' on previous tokens: {attn_text}"
            )

    if game_mode == "hard":
        # In Hard mode, show probabilities for the first token before guess
        prob_stages = {
            "raw": logits_for_first_token,
            "temp": _apply_temperature(logits_for_first_token, TEMPERATURE),
            "final_sampling": get_logits_at_sampling_stages(
                logits_for_first_token, TEMPERATURE, TOP_K, TOP_P
            )["top_p"],
        }
        display_probabilities(
            prob_stages,
            tokenizer,
            ["raw", "temp", "final_sampling"],
            "Probabilities for the *First Token* of the Sequence",
        )
        wait_for_player("Press Enter to make your sequence prediction...")

    # elif game_mode == "expert":
    # No probabilities shown before guess in Expert mode.

    # Generate player choices based on the first token's possibilities
    final_dist_first_token = get_logits_at_sampling_stages(
        logits_for_first_token, TEMPERATURE, TOP_K, TOP_P
    )["top_p"]
    top_single_tokens_pool, _, _ = get_top_tokens_and_probs(
        final_dist_first_token, tokenizer, k=MAX_PROB_DISPLAY
    )
    meaningful_choices_pool = [
        t
        for t in top_single_tokens_pool
        if not (t.startswith("<") or t.startswith("["))
    ]

    player_choices: List[List[str]] = []
    if len(meaningful_choices_pool) >= PERMUTATION_LENGTH:
        for _ in range(NUM_CHOICES - 1):  # Distractors
            choice_candidate = random.sample(
                meaningful_choices_pool, PERMUTATION_LENGTH
            )
            if choice_candidate not in player_choices:
                player_choices.append(choice_candidate)

    correct_sequence_display, correct_sequence_ids = get_true_model_sequence(
        model, tokenizer, current_input_ids, current_attention_mask, PERMUTATION_LENGTH
    )

    if correct_sequence_display not in player_choices:
        if len(player_choices) < NUM_CHOICES:
            player_choices.append(correct_sequence_display)
        elif player_choices:
            player_choices[random.randint(0, len(player_choices) - 1)] = (
                correct_sequence_display
            )
    random.shuffle(player_choices)
    while len(player_choices) < NUM_CHOICES:
        player_choices.append(["[N/A]"] * PERMUTATION_LENGTH)

    prompt_str = f"\n🎮 Predict the {PERMUTATION_LENGTH}-token sequence Gemma generates (always top choice after sampling):"
    chosen_idx = _get_player_sequence_choice(prompt_str, player_choices)
    chosen_player_sequence = player_choices[chosen_idx]

    if game_mode == "expert":
        # In Expert mode, show probabilities for the first token *after* the guess
        color_print("\n--- Revealing Probabilities for First Token ---", YELLOW)
        prob_stages = {
            "raw": logits_for_first_token,
            "temp": _apply_temperature(logits_for_first_token, TEMPERATURE),
            "final_sampling": final_dist_first_token,  # Already computed
        }
        display_probabilities(
            prob_stages,
            tokenizer,
            ["raw", "temp", "final_sampling"],
            "Probabilities for the *First Token* of the Sequence",
        )

    # Score and display results
    current_round_score = 0
    len_to_compare = min(len(chosen_player_sequence), len(correct_sequence_display))
    for i in range(len_to_compare):
        if chosen_player_sequence[i] == correct_sequence_display[i]:
            current_round_score += 1

    is_perfect_match = current_round_score == len(correct_sequence_display) and len(
        chosen_player_sequence
    ) == len(correct_sequence_display)
    color_print(
        f"\nYou chose: '{' '.join(chosen_player_sequence)}'",
        GREEN if is_perfect_match else BLUE,
    )
    color_print(f"Gemma's true sequence: '{' '.join(correct_sequence_display)}'", GREEN)
    if is_perfect_match:
        color_print(
            f"✅ Perfect Sequence! ({current_round_score}/{len(correct_sequence_display)})",
            GREEN,
        )
    else:
        color_print(
            f"⚠️ Matched {current_round_score}/{len(correct_sequence_display)} tokens.",
            YELLOW,
        )

    # Update game state
    new_sentence_part = ""
    updated_input_ids = current_input_ids
    updated_attention_mask = current_attention_mask
    eos_reached_in_sequence = False

    if correct_sequence_ids:
        raw_tokens_for_sentence = _decode_and_clean_token_ids(
            correct_sequence_ids, tokenizer, for_sentence_continuation=True
        )
        new_sentence_part = "".join(raw_tokens_for_sentence)

        new_ids_tensor = torch.tensor([correct_sequence_ids], device=model.device)
        updated_input_ids = torch.cat([current_input_ids, new_ids_tensor], dim=-1)
        updated_attention_mask = torch.cat(
            [current_attention_mask, torch.ones_like(new_ids_tensor)], dim=-1
        )
        if correct_sequence_ids[-1] == tokenizer.eos_token_id:
            eos_reached_in_sequence = True
            print("\n🏁 Model generated an EOS token within the sequence.")

    return (
        current_round_score,
        len(correct_sequence_display),
        updated_input_ids,
        updated_attention_mask,
        new_sentence_part,
        eos_reached_in_sequence,
    )


def run_game_sequence_mode(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    initial_input_text: str,
    mode: Literal["hard", "expert"],
):
    """Runs Hard or Expert mode game."""
    mode_name = "Hard" if mode == "hard" else "Expert"
    color_print(f"\n--- Playing Game ({mode_name} Mode) ---", YELLOW)

    input_ids, attention_mask = prepare_inputs(
        initial_input_text, tokenizer, model.device
    )
    current_sentence = initial_input_text
    total_player_score, total_max_score = 0, 0

    for round_num in range(MAX_ROUNDS):
        score, max_s, new_ids, new_mask, sentence_add, eos_in_seq = (
            _run_sequence_prediction_game_round(
                model,
                tokenizer,
                input_ids,
                attention_mask,
                current_sentence,
                round_num,
                mode,
            )
        )
        total_player_score += score
        total_max_score += max_s
        input_ids, attention_mask = new_ids, new_mask
        current_sentence += sentence_add

        if eos_in_seq:
            break
        if round_num < MAX_ROUNDS - 1:
            wait_for_player()

    # Game Summary
    print(f"\n{'='*30} {mode_name} Mode Game Complete! {'='*30}")
    final_sentence_display = (
        tokenizer.decode(input_ids[0], skip_special_tokens=True)
        .replace("_", " ")
        .strip()
    )
    print(f'\n📝 Final generated text:\n"{final_sentence_display}"')
    score_percentage = (
        (total_player_score / total_max_score) * 100 if total_max_score > 0 else 0
    )
    print(
        f"\n🏆 Final Score: {total_player_score} / {total_max_score} ({score_percentage:.1f}%)"
    )
    if score_percentage >= 80:
        print("🌟 Excellent sequence prediction!")
    elif score_percentage >= 50:
        print("✨ Good job! You're getting the hang of it.")
    else:
        print("🎓 Nice try! Predicting sequences is challenging.")


def run_game_tutorial_mode(
    model: AutoModelForCausalLM, tokenizer: AutoTokenizer, initial_input_text: str
) -> None:
    """Runs the 'Tutorial Mode' for single token prediction with detailed probability insights."""
    # ... (implementation from previous version, but ensure display_probabilities uses all 4 stages if configured)
    color_print("\n--- Playing Tutorialized Game ---", YELLOW)
    print(
        "Predict one token at a time. Probabilities (raw, temp, top_k, top_p) shown based on config."
    )

    input_ids, attention_mask = prepare_inputs(
        initial_input_text, tokenizer, model.device
    )
    current_sentence = initial_input_text
    total_player_score, total_max_score = 0, 0

    for round_num in range(MAX_ROUNDS):
        print(f"\n{'-'*20} Round {round_num + 1} of {MAX_ROUNDS} {'-'*20}")
        color_print(
            f'Current Sentence: "{current_sentence.replace("_", " ").strip()}"', BLUE
        )

        outputs = get_model_outputs(model, input_ids, attention_mask)
        logits_next_token = outputs.logits[:, -1, :]

        # Get logits at all 4 stages
        all_logits_stages = get_logits_at_sampling_stages(
            logits_next_token, TEMPERATURE, TOP_K, TOP_P
        )
        # Filter to only those requested for display
        logits_to_display = {
            stage: all_logits_stages[stage]
            for stage in TUTORIAL_PROB_STAGES_TO_SHOW
            if stage in all_logits_stages
        }

        attention_data = get_attention_heatmap(outputs, input_ids, tokenizer)
        if attention_data:
            ctx_tokens, norm_attn, attend_token = attention_data
            if ctx_tokens and norm_attn:
                attn_text, scale = color_attention_text(ctx_tokens, norm_attn)
                print(f"\n--- Attention (for next token prediction) ---")
                print(f"{scale}Attention of '{attend_token}' on previous: {attn_text}")

        if TUTORIAL_PROB_DISPLAY_MODE == "before":
            display_probabilities(
                logits_to_display,
                tokenizer,
                TUTORIAL_PROB_STAGES_TO_SHOW,
                "Probabilities for Next Single Token",
            )
            wait_for_player("Press Enter to make your single token prediction...")

        # Determine correct token and generate choices using the final distribution ('top_p' stage)
        final_sampling_dist = all_logits_stages["top_p"]
        correct_token_display_list, _, correct_token_id_list_full = (
            get_top_tokens_and_probs(final_sampling_dist, tokenizer, k=1)
        )
        correct_token_str = correct_token_display_list[0]
        correct_token_id = correct_token_id_list_full[0]

        all_top_tokens_for_choices, _, _ = get_top_tokens_and_probs(
            final_sampling_dist, tokenizer, k=NUM_CHOICES * 2
        )
        distractor_pool = [
            t
            for t in all_top_tokens_for_choices
            if t != correct_token_str and not (t.startswith("<") or t.startswith("["))
        ]

        player_choices_list = [correct_token_str]
        player_choices_list.extend(
            random.sample(distractor_pool, min(len(distractor_pool), NUM_CHOICES - 1))
        )
        while len(player_choices_list) < NUM_CHOICES:
            player_choices_list.append("[N/A]")
        random.shuffle(player_choices_list)

        print(f"\n🎮 Predict Gemma's next SINGLE token:")
        for i, choice_token_str_option in enumerate(player_choices_list):
            print(f"  {chr(ord('A') + i)}) '{choice_token_str_option}'")

        chosen_idx = -1
        while True:
            user_char_input = (
                input(
                    f"\nYour choice (A-{chr(ord('A') + len(player_choices_list) - 1)}): "
                )
                .strip()
                .upper()
            )
            if user_char_input and "A" <= user_char_input[0] <= chr(
                ord("A") + len(player_choices_list) - 1
            ):
                chosen_idx = ord(user_char_input[0]) - ord("A")
                break
            else:
                print("Invalid input.")

        chosen_token_by_player = player_choices_list[chosen_idx]
        is_player_correct = chosen_token_by_player == correct_token_str

        color_print(
            f"\nYou chose: '{chosen_token_by_player}'",
            GREEN if is_player_correct else BLUE,
        )
        color_print(f"Gemma's choice: '{correct_token_str}'", GREEN)
        if is_player_correct:
            color_print("✅ Correct!", GREEN)
        else:
            color_print(f"⚠️ Not quite.", YELLOW)

        total_player_score += 1 if is_player_correct else 0
        total_max_score += 1

        if TUTORIAL_PROB_DISPLAY_MODE == "after":
            wait_for_player("Press Enter to view probability details...")
            display_probabilities(
                logits_to_display,
                tokenizer,
                TUTORIAL_PROB_STAGES_TO_SHOW,
                "Probabilities for Next Single Token",
            )

        raw_token_for_sentence = _decode_and_clean_token_ids(
            [correct_token_id], tokenizer, for_sentence_continuation=True
        )[0]
        current_sentence += raw_token_for_sentence

        new_id_tensor = torch.tensor([[correct_token_id]], device=model.device)
        input_ids = torch.cat([input_ids, new_id_tensor], dim=-1)
        attention_mask = torch.cat(
            [attention_mask, torch.ones_like(new_id_tensor)], dim=-1
        )

        if correct_token_id == tokenizer.eos_token_id:
            print("\n🏁 Model generated an EOS token. Game round ends.")
            break
        if round_num < MAX_ROUNDS - 1:
            wait_for_player()

    print("\n" + "=" * 30 + " Tutorial Mode Game Complete! " + "=" * 30)
    # ... (Game summary as before) ...
    final_sentence_display = (
        tokenizer.decode(input_ids[0], skip_special_tokens=True)
        .replace("_", " ")
        .strip()
    )
    print(f'\n📝 Final generated text:\n"{final_sentence_display}"')
    score_percentage = (
        (total_player_score / total_max_score) * 100 if total_max_score > 0 else 0
    )
    print(
        f"\n🏆 Final Score: {total_player_score} / {total_max_score} ({score_percentage:.1f}%)"
    )
    if score_percentage >= 80:
        print("🌟 Excellent!")
    elif score_percentage >= 50:
        print("✨ Great job!")
    else:
        print("🎓 Good effort!")


# --- Learning Modules ---
def run_learning_module_tokens(tokenizer: AutoTokenizer) -> None:
    """Interactive module to explore tokens, vocabulary, and tokenization."""
    # ... (implementation from previous version, assumed correct)
    color_print("\n--- Learning: Explore Tokens & Vocabulary ---", YELLOW)
    vocab_size = tokenizer.vocab_size
    print(f"This model's tokenizer has a vocabulary of {vocab_size:,} unique tokens.")
    while True:
        print(
            "\n1) Random tokens | 2) Tokenize text | 3) Detokenize IDs | 4) Stitch concept | 0) Back"
        )
        choice = input("Choice: ").strip()
        if choice == "1":
            print("\nSampling 5 random token IDs:")
            for _ in range(5):
                rand_id = random.randint(0, vocab_size - 1)
                token_str = _decode_and_clean_token_ids([rand_id], tokenizer)[0]
                print(f"  ID: {rand_id:<6}  =>  '{token_str}'")
        elif choice == "2":
            text = input("Enter text: ").strip()
            if text:
                ids = tokenizer.encode(text)
                strs_disp = _decode_and_clean_token_ids(ids, tokenizer)
                raw_pieces = tokenizer.convert_ids_to_tokens(ids)
                print(
                    f"IDs: {ids}\nDisplay Tokens: {strs_disp}\nRaw Pieces: {raw_pieces}\nStitched: '{' | '.join(strs_disp)}'"
                )
        elif choice == "3":
            ids_str = input("Enter token IDs (comma-sep): ").strip()
            try:
                ids = [int(x.strip()) for x in ids_str.split(",")]
                strs_disp = _decode_and_clean_token_ids(ids, tokenizer)
                raw_comb = "".join(
                    _decode_and_clean_token_ids(
                        ids, tokenizer, for_sentence_continuation=True
                    )
                )
                print(f"Display: {strs_disp}\nCombined Raw: '{raw_comb}'")
            except ValueError:
                print("Invalid IDs.")
        elif choice == "4":
            print("\nConcept: 'transformer' -> 'transform' + 'er' (subwords)")
        elif choice == "0":
            break
        else:
            print("Invalid choice.")
        wait_for_player()


def run_learning_module_attention(tokenizer: AutoTokenizer) -> None:
    """Conceptual interactive module for understanding attention."""
    # ... (implementation from previous version, assumed correct)
    color_print("\n--- Learning: Explore Attention (Conceptual) ---", YELLOW)
    example_sentence = "The quick brown fox jumps over the lazy dog"
    tokens_display = _decode_and_clean_token_ids(
        tokenizer.encode(example_sentence), tokenizer
    )
    print(f"Sentence Tokens: {' '.join(tokens_display)}")
    while True:
        try:
            idx_str = input(f"Pick query token (1-{len(tokens_display)}, 0 to exit): ")
            if idx_str == "0":
                break
            query_idx = int(idx_str) - 1
            if not (0 <= query_idx < len(tokens_display)):
                print("Invalid.")
                continue
            query_token = tokens_display[query_idx]
            print(
                f"Query: '{query_token}'. Simulated Attention (higher = more attended):"
            )
            output = []
            for i, key_token in enumerate(tokens_display):
                score = 0.0
                if i == query_idx:
                    score = 0.1
                elif i < query_idx:
                    if (
                        key_token.lower() in query_token.lower()
                        or query_token.lower() in key_token.lower()
                    ):
                        score = 0.8
                    elif (query_token == "fox" and key_token == "dog") or (
                        query_token == "jumps" and key_token == "fox"
                    ):
                        score = 0.6
                    else:
                        score = random.uniform(0.05, 0.3)

                if i < query_idx:
                    c = (
                        MAGENTA_INTENSE
                        if score > 0.7
                        else (
                            MAGENTA_BRIGHT
                            if score > 0.5
                            else MAGENTA_MEDIUM if score > 0.2 else MAGENTA_LIGHT
                        )
                    )
                    output.append(
                        f"{c if USE_COLORS else ''}{key_token}{RESET if USE_COLORS else ''} ({score:.2f})"
                    )
                elif i == query_idx:
                    output.append(
                        f"{BLUE if USE_COLORS else ''}{key_token}{RESET if USE_COLORS else ''} (Query)"
                    )
                else:
                    output.append(f"{key_token} (Future)")
            print(" ".join(output))
        except ValueError:
            print("Invalid input.")
        wait_for_player()


def run_learning_module_cot_simulation() -> None:
    """Simulates Chain-of-Thought prompting conceptually."""
    # ... (implementation from previous version, assumed correct)
    color_print("\n--- Learning: Simulate Chain-of-Thought (CoT) ---", YELLOW)
    prompts = [
        {
            "prompt": "Capital of France?",
            "thoughts": ["France is in Europe.", "Paris is capital."],
            "answer": "Paris.",
        },
        {
            "prompt": "Train (2PM, 60mph), City B 180 miles. Arrival?",
            "thoughts": ["Time=Dist/Speed.", "180/60=3hrs.", "2PM+3hrs."],
            "answer": "5 PM.",
        },
    ]
    for item in prompts:
        print(f"\n{BLUE}Prompt:{RESET} {item['prompt']}")
        wait_for_player("Simulated thoughts...")
        color_print("Conceptual 'Thoughts':", MAGENTA_BRIGHT)
        for i, t in enumerate(item["thoughts"]):
            time.sleep(0.3)
            print(f"  {i+1}: {t}")
        wait_for_player("Final answer...")
        color_print("Answer:", GREEN)
        print(f"  {item['answer']}")
        if item != prompts[-1]:
            wait_for_player("Next...")
    wait_for_player()


def run_learning_module_ram_quantization() -> None:
    """Explains model size, RAM usage, and quantization concepts."""
    color_print("\n--- Learning: Model Size, Quantization & RAM ---", YELLOW)
    print("Understanding how Large Language Models use memory is key.")

    print(f"\n{BLUE}1. Parameters & Model Size:{RESET}")
    print(
        "  - LLMs have billions of 'parameters' (weights and biases). These are the learned numbers."
    )
    print(
        "  - Each parameter typically uses 2 bytes in `bfloat16` or `fp16` (float16) format."
    )
    print(
        "    So, a 1 Billion param model is roughly 1B * 2 bytes = 2 GB on disk/in memory."
    )
    print("    Example: A 7B param model is ~14 GB (raw model weights).")

    print(f"\n{BLUE}2. Why is Recommended RAM Higher than Raw Size?{RESET}")
    print(
        "  - {GREEN}KV Cache:{RESET} During generation, the model stores 'Key' and 'Value' states for previously processed tokens. This 'KV cache' can grow very large, especially with long input sequences or long generated outputs. It can easily take several GBs."
    )
    print(
        "  - {GREEN}Activations:{RESET} Intermediate calculations (activations) during the forward pass also consume memory."
    )
    print(
        "  - {GREEN}Inference Engine & OS Overhead:{RESET} The software running the model (e.g., PyTorch, Transformers library) and the operating system need their own memory."
    )
    print(
        "  - {GREEN}Batch Size:{RESET} If processing multiple inputs at once (batching), memory needs multiply."
    )
    print(
        "  Therefore, you generally need 1.5x to 2x (or more for very long contexts) the raw model size in available RAM (VRAM or Unified RAM) for smooth inference."
    )

    print(f"\n{BLUE}3. Quantization: Making Models Smaller & Faster{RESET}")
    print(
        "  - Quantization reduces the precision of model weights (and sometimes activations) from floats (e.g., 16-bit) to lower-bit integers (e.g., 8-bit, 4-bit)."
    )
    print("  - {GREEN}Benefits:{RESET}")
    print(
        "    - {YELLOW}Smaller Model Size:{RESET} An 8-bit quantized 7B model might be ~7 GB instead of ~14 GB."
    )
    print(
        "    - {YELLOW}Reduced RAM Usage:{RESET} Less memory needed during inference."
    )
    print(
        "    - {YELLOW}Faster Inference (Potentially):{RESET} Integer math can be faster on some hardware."
    )
    print(
        "  - {GREEN}Trade-off:{RESET} Usually a small loss in model performance/accuracy, but often acceptable."
    )
    print("  - {GREEN}Common Techniques (Conceptual):{RESET}")
    print(
        "    - {CYAN}Post-Training Quantization (PTQ):{RESET} Quantize an already trained model. Simpler."
    )
    print(
        "      - {MAGENTA}int8:{RESET} Weights converted to 8-bit integers. Common and effective."
    )
    print(
        "      - {MAGENTA}int4 (e.g., NF4, GPTQ):{RESET} Weights to 4-bit. More aggressive, can achieve ~4x size reduction. Uses clever techniques to maintain quality."
    )
    print(
        "    - {CYAN}Quantization-Aware Training (QAT):{RESET} Simulate quantization effects *during* training. Can yield better accuracy for quantized models but is more complex."
    )
    print("\nQuantized models are crucial for running large LLMs on consumer hardware!")
    wait_for_player()


def explain_transformer_steps() -> None:
    """Provides a detailed explanation of Transformer architecture steps."""
    # ... (full implementation from previous version, assumed correct)
    print("\n--- Deep Dive into Transformer Steps (Decoder-Focused for Gemma) ---")
    steps = [
        (
            "Tokenization & Embedding",
            "Input text -> numerical tokens. Each token -> high-dimensional 'embedding' vector.",
        ),
        ("Positional Encoding", "Word order info added to embeddings."),
        (
            "Decoder Layers (Repeated)",
            "Core: Multi-Head Self-Attention and Feed-Forward Network per layer.",
        ),
        (
            "  Multi-Head Self-Attention",
            "Weighs token importance. Q, K, V vectors -> context-aware representation.",
        ),
        (
            "  Feed-Forward Network (FFN)",
            "Further processes each token's representation.",
        ),
        (
            "Residual Connections & Layer Normalization",
            "Aids training deep networks and stabilizes activations.",
        ),
        (
            "Final Linear Layer & Softmax",
            "Projects to vocab size (logits) -> probabilities over vocabulary.",
        ),
        (
            "Token Selection (Sampling)",
            "Chooses next token using Temperature, Top-K, Top-P.",
        ),
    ]
    for title, desc in steps:
        color_print(f"\n{BLUE}{title}:{RESET}", BLUE)
        print(f"   {desc}")
    print("\nProcess is auto-regressive: generated token becomes input for next step.")


def explain_attention_mechanism() -> None:
    """Provides an explanation of the attention mechanism."""
    # ... (full implementation from previous version, assumed correct)
    print("\n--- Understanding Attention in Language Models ---")
    print("Attention allows dynamic focus on input parts for predictions.")
    print(
        f"\n1. {BLUE}Weighted Importance:{RESET} Assigns scores/weights to previous tokens; higher means more relevant for current prediction."
    )
    print(
        f"2. {BLUE}Contextual Understanding:{RESET} Builds rich context by attending to relevant past tokens."
    )
    print(
        f"3. {BLUE}Queries, Keys, Values (QKV):{RESET} Conceptually: Query (what's sought), Keys (info offered by context), Values (content to pass). Scores from Q-K comparison."
    )
    print(
        f"4. {BLUE}Softmax & Weighted Sum:{RESET} Scores -> weights via softmax. Weights -> weighted sum of Value vectors -> attention output."
    )
    print(
        f"5. {BLUE}Multi-Head Attention:{RESET} Parallel heads learn different relationship types."
    )
    print(
        "\nIn Gamma's Viz: Shows averaged, normalized attention from final layer for *next token prediction*."
    )


# --- Main Application Flow ---
def main_menu(model: AutoModelForCausalLM, tokenizer: AutoTokenizer) -> None:
    """Displays the main menu and routes to different functionalities."""
    while True:
        print(
            f"\n{YELLOW}--- GAMMA Main Menu (Model: {model.config.name_or_path}) ---{RESET}"
        )
        menu_options = {
            "1": "Play Game (Expert Mode - Guess Sequence BEFORE Probs)",
            "2": "Play Game (Hard Mode - Guess Sequence AFTER Probs for 1st Token)",
            "3": "Play Tutorialized Game (Easy Mode - Guess Single Token)",
            "4": "Explore: Tokens & Vocabulary (Interactive)",
            "5": "Explore: Attention Mechanism (Conceptual & Interactive)",
            "6": "Explore: Chain-of-Thought (CoT) Simulation",
            "7": "Explore: Model Size, Quantization & RAM",
            "8": "Explain: Transformer Architecture In-Depth",
            "9": "Explain: Attention Mechanism In-Depth",
            "0": "Change Model / Exit",
        }
        for key, value in menu_options.items():
            print(f"{key}. {value}")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            text = (
                input(
                    "\nStart sentence for Expert Mode (Enter for default 'The journey began'): "
                ).strip()
                or "The journey began"
            )
            run_game_sequence_mode(model, tokenizer, text, "expert")
        elif choice == "2":
            text = (
                input(
                    "\nStart sentence for Hard Mode (Enter for default 'The ancient dragon slept'): "
                ).strip()
                or "The ancient dragon slept"
            )
            run_game_sequence_mode(model, tokenizer, text, "hard")
        elif choice == "3":
            text = (
                input(
                    "\nStart sentence for Tutorial Mode (Enter for default 'Artificial intelligence is'): "
                ).strip()
                or "Artificial intelligence is"
            )
            run_game_tutorial_mode(model, tokenizer, text)
        elif choice == "4":
            run_learning_module_tokens(tokenizer)
        elif choice == "5":
            run_learning_module_attention(tokenizer)
        elif choice == "6":
            run_learning_module_cot_simulation()
        elif choice == "7":
            run_learning_module_ram_quantization()
        elif choice == "8":
            explain_transformer_steps()
            wait_for_player()
        elif choice == "9":
            explain_attention_mechanism()
            wait_for_player()
        elif choice == "0":
            print("Returning to model selection...")
            return
        else:
            print("Invalid choice, please try again.")


def run_game_manager() -> None:
    """Manages the overall game flow, including model selection and main menu navigation."""
    # ... (implementation from previous version, assumed correct)
    parser = argparse.ArgumentParser(description="GAMMA: LLM Interactive Explorer")
    args = parser.parse_args()
    color_print("\n" + "=" * 70, GREEN)
    color_print("🤖 Welcome to GAMMA: LLM Interactive Explorer! 🎮", GREEN)
    color_print("=" * 70, GREEN)
    current_model_instance, current_tokenizer_instance = None, None
    while True:
        if not current_model_instance:
            print("\nAvailable Gemma Models:")
            for i, name in enumerate(GEMMA_MODELS):
                info = MODEL_INFO.get(
                    name,
                    {
                        "desc": "N/A",
                        "params_b": "N/A",
                        "raw_model_gb": "N/A",
                        "rec_ram_gb": "N/A",
                    },
                )
                print(
                    f"  {i+1}) {name:<30} ({info['desc']:<25} Params: ~{info['params_b']}B, Raw: ~{info['raw_model_gb']}GB, Rec.RAM: {info['rec_ram_gb']})"
                )
            idx = -1
            while True:
                try:
                    s = input(
                        f"Choose model (1-{len(GEMMA_MODELS)}, default 1): "
                    ).strip()
                    idx = 0 if not s else int(s) - 1
                    if 0 <= idx < len(GEMMA_MODELS):
                        break
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Please enter a number.")
            try:
                current_model_instance, current_tokenizer_instance = (
                    load_model_and_tokenizer(GEMMA_MODELS[idx])
                )
            except Exception:
                color_print("Model load failed. Check setup/RAM.", RED)
                current_model_instance, current_tokenizer_instance = None, None
                wait_for_player("Enter to retry model selection or Ctrl+C to exit.")
                continue
        if current_model_instance and current_tokenizer_instance:
            main_menu(current_model_instance, current_tokenizer_instance)
            current_model_instance, current_tokenizer_instance = None, None
        else:
            color_print("Exiting GAMMA.", BLUE)
            break


if __name__ == "__main__":
    run_game_manager()
