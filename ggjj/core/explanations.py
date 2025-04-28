from . import ui  # Use ui functions for formatted printing

def explain_game_concepts(verbose: bool):
    ui.print_header("Understanding the Game Concepts")
    ui.wrap_print("This game helps visualize how LLMs predict the next word (token) in a sequence.")

    ui.wrap_print("\nKey Steps Visualized:", indent=" ")
    ui.wrap_print("1. Attention: See which previous words the model focuses on (heatmap).", indent="   ")
    ui.wrap_print("2. Probabilities (Raw): The model's initial guess probabilities for all possible next words.", indent="   ")
    ui.wrap_print("3. Filtering (Temp, Top-K, Top-P): How the model refines its choices.", indent="     ")
    ui.wrap_print("   - Temperature: Makes predictions sharper (low temp) or flatter/random (high temp).", indent="       ")
    ui.wrap_print("   - Top-K: Limits choices to the 'K' most likely words.", indent="       ")
    ui.wrap_print("   - Top-P (Nucleus): Limits choices to a core set whose probabilities sum up to 'P'.", indent="       ")
    ui.wrap_print("4. Your Guess: You predict the sequence the model ranks highest *after* all filtering.", indent="   ")

    if verbose:
        ui.wrap_print("\nPerplexity (Intuition):", indent=" ")
        ui.wrap_print("While not calculated directly here, think of perplexity as how 'surprised' the model is by the actual next token. If the correct token had a very low probability after filtering, the model was more 'perplexed'. High probability = low perplexity/surprise.", indent="   ")

    ui.wrap_print("\nGoal: Develop an intuition for how context (attention) and sampling strategies shape the LLM's output.")
    input("\nPress Enter to continue...")


def explain_attention(verbose: bool):
     ui.print_header("Understanding Attention")
     ui.wrap_print("Attention lets the model weigh the importance of different words in the input sequence when predicting the next word.")
     ui.wrap_print("\nIn the heatmap visualization:", indent=" ")
     ui.wrap_print("- Each word from the current input is shown.", indent="   ")
     ui.wrap_print("- The color intensity (or text markers) indicates how much 'focus' that word received *for predicting the very next token*.", indent="   ")
     ui.wrap_print("- Scores are normalized (0 to 1), averaged across multiple 'attention heads' in the model's final layer.", indent="   ")

     if verbose:
          ui.wrap_print("\nWhy is it important?", indent=" ")
          ui.wrap_print("It allows the model to understand long-range dependencies and context. For example, in 'The cat sat on the mat, it...', attention helps the model focus on 'cat' to predict that 'it' refers to the cat.", indent="   ")
          ui.wrap_print("\nThe patterns change each step as the context grows!", indent="   ")

     input("\nPress Enter to continue...")

def explain_sampling(temp: float, top_k: int, top_p: float, verbose: bool):
    ui.print_header("Understanding Sampling Filters")
    ui.wrap_print("After calculating raw probabilities for the next token, the model uses filters to decide which token to actually choose. This makes the output more coherent and controllable.")

    ui.wrap_print("\nFilters Used in this Game:", indent=" ")
    ui.wrap_print(f"1. Temperature ({temp:.2f}):", indent="   ")
    ui.wrap_print("   - Adjusts the 'peakiness' of the probability distribution.", indent="     ")
    ui.wrap_print("   - < 1.0: Sharpens peaks, favors high-probability tokens (more deterministic).", indent="     ")
    ui.wrap_print("   - > 1.0: Flattens distribution, increases randomness (more creative/surprising).", indent="     ")
    ui.wrap_print(f"   - Current Value: {temp:.2f}", indent="     ")

    ui.wrap_print(f"\n2. Top-K Filtering ({top_k}):", indent="   ")
    ui.wrap_print("   - Discards all tokens except the K most probable ones.", indent="     ")
    ui.wrap_print("   - Reduces the chance of picking very unlikely tokens.", indent="     ")
    ui.wrap_print(f"   - Current Value: {top_k}", indent="     ")

    ui.wrap_print(f"\n3. Top-P (Nucleus) Sampling ({top_p:.2f}):", indent="   ")
    ui.wrap_print("   - Selects the smallest set of tokens whose cumulative probability exceeds P.", indent="     ")
    ui.wrap_print("   - Adapts dynamically: keeps more tokens if probabilities are flat, fewer if peaked.", indent="     ")
    ui.wrap_print(f"   - Current Value: {top_p:.2f}", indent="     ")

    if verbose:
        ui.wrap_print("\nCombined Effect:", indent=" ")
        ui.wrap_print("These filters work together. Temperature scales logits, then Top-K might remove some, then Top-P removes more based on cumulative probability. The final token is chosen (in this game, the *most likely* one remaining) from the filtered set.", indent="   ")

    input("\nPress Enter to continue...")