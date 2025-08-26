from typing import Any
from src.core import ui
from src.core import config as cfg


def explain_game_concepts(args: Any):
    ui.print_header("Understanding GAMMA Concepts")
    ui.wrap_print("GAMMA helps visualize how LLMs predict the next piece of text (token).")
    ui.wrap_print("You'll interact with these key stages:", indent=" ")
    ui.wrap_print("1. Attention: See which previous words the model focuses on (heatmap, if engine supports).", indent="  ")
    ui.wrap_print("2. Probabilities (Raw): The model's initial guess probabilities for all possible next tokens.", indent="  ")
    ui.wrap_print("3. Sampling Filters: How the model refines its choices using parameters like:", indent="  ")
    ui.wrap_print(f"   - Temperature ({args.temperature:.2f}): Sharpens (low temp) or flattens (high temp) predictions.", indent="    ")
    ui.wrap_print(f"   - Top-K ({args.top_k}): Limits choices to the 'K' most likely tokens.", indent="    ")
    ui.wrap_print(f"   - Top-P ({args.top_p:.2f}): Limits choices to a core set whose probabilities sum to 'P'.", indent="    ")
    ui.wrap_print("4. Your Guess: Predict the token sequence the model ranks highest after all filtering.", indent="  ")

    if args.verbose:
        ui.wrap_print("\nToken Types:", indent=" ")
        ui.wrap_print("LLMs see text as 'tokens' - common words, sub-words, punctuation, or special symbols. "
                      "The 'Focus Words' mode (if active) tries to make choices more about guessing word tokens.", indent="  ")
    ui.wrap_print("\nGoal: Develop intuition for how context and sampling strategies shape LLM output. Have fun!")


def explain_attention(args: Any):
    ui.print_header("Understanding Attention")
    ui.wrap_print("Attention lets the model weigh the importance of different words in the input sequence when predicting the next word.")
    ui.wrap_print("\nIn the heatmap visualization (if available for the current engine):", indent=" ")
    ui.wrap_print("- Each word from the current input is shown.", indent="  ")
    ui.wrap_print("- Color intensity indicates how much 'focus' that word received for predicting the next token.", indent="  ")
    ui.wrap_print("- Scores are normalized (0-1), often averaged across multiple 'attention heads' in one of the model's final layers.", indent="  ")

    if args.verbose:
        ui.wrap_print("\nWhy it matters:", indent=" ")
        ui.wrap_print("It enables understanding of long-range dependencies and context. For example, in 'The cat sat on the mat, it...', attention helps the model infer that 'it' likely refers to 'cat'.", indent="   ")
        ui.wrap_print("\nPatterns change each step as the context grows!", indent="   ")


def explain_sampling_filters(args: Any):
    ui.print_header("Understanding Sampling Filters")
    ui.wrap_print("After calculating raw probabilities, the model uses filters to select the next token, making output more coherent and controllable.")
    ui.wrap_print("\nFilters Used in GAMMA (with current settings):", indent=" ")
    ui.wrap_print(f"1. Temperature ({args.temperature:.2f}):", indent="   ")
    ui.wrap_print("   Adjusts 'randomness'. < 1.0 sharpens peaks (more deterministic); > 1.0 flattens (more creative/random).", indent="     ", initial_indent_add=" ")
    ui.wrap_print(f"\n2. Top-K Filtering ({args.top_k}):", indent="   ")
    ui.wrap_print("   Considers only the K most probable tokens, discarding the rest.", indent="     ", initial_indent_add=" ")
    ui.wrap_print(f"\n3. Top-P (Nucleus) Sampling ({args.top_p:.2f}):", indent="   ")
    ui.wrap_print("   Selects the smallest set of tokens whose cumulative probability exceeds P. Adapts dynamically to distribution shape.", indent="     ", initial_indent_add=" ")

    if args.verbose:
        ui.wrap_print("\nCombined Effect:", indent=" ")
        ui.wrap_print("These filters work together. Temperature scales probabilities, then Top-K might remove some, then Top-P might remove more. The model's final choice (for this game, its top-ranked remaining token) comes from this filtered set.", indent="   ")


def explain_focus_words_mode(args: Any):
    if not args.focus_words:
        return
    ui.print_header("Focus Words Mode Explained")
    ui.wrap_print("You are playing in 'Focus Words' mode!")
    ui.wrap_print("In this mode, the choices presented to you will prioritize sequences composed of common word tokens over punctuation or highly specialized/technical tokens.", indent="  ")
    ui.wrap_print("The model's underlying prediction process remains the same, but your guessing task is geared more towards natural language continuation.", indent="  ")
    ui.wrap_print(f"A token is generally considered a 'word' if it contains letters and meets a minimum length (currently {cfg.MIN_WORD_TOKEN_LENGTH} chars, unless purely alphabetic like 'a' or 'I'). Some code-like tokens might also be filtered out from choices.", indent="  ")
    ui.wrap_print("If the model predicts many special tokens or punctuation, these might still appear if not enough 'wordy' alternatives are highly ranked, or they form part of the model's absolute top choice.", indent="  ")


def explain_player_choice_mode(args: Any):
    if not args.player_choice_mode:
        return
    ui.print_header("Player Choice Mode (Experimental)")
    ui.wrap_print("You are playing in 'Player Choice Mode'!")
    ui.wrap_print("In this mode, if you guess the entire token sequence correctly, your chosen sequence will be used to continue the generation for the next step.", indent="  ")
    ui.wrap_print("If your guess is not a perfect match, the model's own top-ranked sequence will be used, as in the standard game mode.", indent="  ")
    ui.wrap_print("This allows you to steer the generation more directly, provided your intuition aligns perfectly with the model's preferences for that step.", indent="  ")