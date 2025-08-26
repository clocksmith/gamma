"""
Tutorial Mode for GAMMA - Interactive learning experience for understanding LLMs
"""

import time
from typing import Optional, Dict, Any, List, Tuple
from src.core import config as cfg
from src.core import ui
from src.core.engine_interface import LLMEngine


class TutorialMode:
    """Interactive tutorial that explains transformer concepts through guided gameplay."""
    
    def __init__(self, engine: LLMEngine, verbose: bool = True):
        self.engine = engine
        self.verbose = verbose
        self.lessons_completed = set()
        
    def run_tutorial(self) -> None:
        """Main tutorial flow with interactive lessons."""
        ui.print_separator()
        print(ui.color_text("🎓 Welcome to GAMMA Tutorial Mode!", cfg.COLOR_CYAN))
        print("\nThis interactive tutorial will teach you how language models work by letting you")
        print("experience each step of the prediction process.")
        
        lessons = [
            ("tokenization", "Tokenization: How Text Becomes Numbers"),
            ("attention", "Attention Mechanism: How Models Focus"),
            ("sampling", "Sampling Strategies: Temperature, Top-K, and Top-P"),
            ("generation", "Autoregressive Generation: Building Text Token by Token"),
        ]
        
        print("\nAvailable Lessons:")
        for i, (_, title) in enumerate(lessons, 1):
            status = "✓" if f"lesson_{i}" in self.lessons_completed else " "
            print(f"  [{status}] {i}. {title}")
        
        while True:
            choice = ui.get_user_input(
                "\nSelect a lesson (1-4)",
                valid_choices=["1", "2", "3", "4", "q"],
                allow_quit=True
            )
            
            if choice == cfg.SHORTCUT_QUIT or choice == "q":
                break
                
            lesson_idx = int(choice) - 1
            lesson_key, lesson_title = lessons[lesson_idx]
            
            ui.print_separator()
            print(ui.color_text(f"\n📚 Lesson {choice}: {lesson_title}", cfg.COLOR_YELLOW))
            
            if lesson_key == "tokenization":
                self._lesson_tokenization()
            elif lesson_key == "attention":
                self._lesson_attention()
            elif lesson_key == "sampling":
                self._lesson_sampling()
            elif lesson_key == "generation":
                self._lesson_generation()
            
            self.lessons_completed.add(f"lesson_{choice}")
            
            print(ui.color_text(f"\n✓ Lesson {choice} completed!", cfg.COLOR_GREEN))
            
            continue_choice = ui.get_user_input(
                "Continue to next lesson? (y/n)",
                valid_choices=["y", "n"],
                allow_quit=False
            )
            if continue_choice.lower() == "n":
                break
    
    def _lesson_tokenization(self) -> None:
        """Lesson on how tokenization works."""
        print("\n" + "="*60)
        print("TOKENIZATION converts human-readable text into numbers (tokens)")
        print("that the model can process.")
        print("="*60)
        
        # Interactive example
        example_text = ui.get_user_input(
            "\nEnter a short phrase to tokenize (or press Enter for default)",
            allow_empty=True,
            default_val_on_empty="Hello world!"
        )
        
        if example_text == cfg.SHORTCUT_QUIT:
            return
        
        print(f"\nTokenizing: '{example_text}'")
        
        # Tokenize the text
        input_ids, _ = self.engine.encode(example_text, add_special_tokens=False)
        
        # Show the process step by step
        print("\n1️⃣  Original text:")
        print(f"   '{example_text}'")
        
        time.sleep(1)
        
        print("\n2️⃣  Split into tokens:")
        tokens = []
        for token_id in self._get_token_ids_list(input_ids):
            token_text = self.engine.get_token_text(token_id)
            tokens.append(token_text)
        
        print("   [", end="")
        for i, token in enumerate(tokens):
            if i > 0:
                print(", ", end="")
            print(ui.color_text(f"'{token}'", cfg.COLOR_CYAN), end="")
        print("]")
        
        time.sleep(1)
        
        print("\n3️⃣  Convert to token IDs (numbers):")
        print("   [", end="")
        token_ids = self._get_token_ids_list(input_ids)
        for i, (token, token_id) in enumerate(zip(tokens, token_ids)):
            if i > 0:
                print(", ", end="")
            print(f"{token_id}", end="")
        print("]")
        
        print("\n\n💡 Key Insights:")
        print("• Tokens can be whole words, parts of words, or even single characters")
        print("• Common words often get single tokens, rare words are split into pieces")
        print("• The model has a fixed vocabulary of tokens it knows")
        print(f"• This model's vocabulary size: {self.engine.get_vocab_size():,} tokens")
        
        if self.verbose:
            print("\n📊 Token Details:")
            for token, token_id in zip(tokens, token_ids):
                print(f"   Token '{token}' → ID {token_id}")
    
    def _lesson_attention(self) -> None:
        """Lesson on attention mechanism."""
        print("\n" + "="*60)
        print("ATTENTION MECHANISM lets the model decide which previous tokens")
        print("are most important when predicting the next token.")
        print("="*60)
        
        example_text = "The cat sat on the"
        print(f"\nExample sentence: '{example_text}'")
        
        print("\nWhen predicting what comes after 'the', the model uses attention")
        print("to look back at all previous tokens and decide their importance.")
        
        # Encode and get attention
        input_ids, attention_mask = self.engine.encode(example_text, add_special_tokens=True)
        
        print("\n🔍 Running model to see attention patterns...")
        pred_result = self.engine.predict_next(
            input_ids,
            attention_mask,
            temperature=0.7,
            top_k=8,
            top_p=0.95,
            return_attention=True
        )
        
        if pred_result.get("attention"):
            attn_texts, attn_scores = self.engine.get_attention_for_visualization(
                pred_result["attention"],
                input_ids
            )
            
            if attn_texts and attn_scores:
                print("\n📊 Attention Weights (darker = more attention):")
                ui.display_attention_heatmap(attn_texts, attn_scores, verbose=False)
                
                print("\n💡 What this means:")
                print("• Higher attention (darker) = more influence on the prediction")
                print("• The model learned these patterns from training data")
                print("• Different tokens get different attention based on context")
                
                # Find most attended token
                max_idx = attn_scores.index(max(attn_scores))
                print(f"\n🎯 Most attended token: '{attn_texts[max_idx]}' (weight: {attn_scores[max_idx]:.3f})")
        
        print("\n📝 In the game, you'll see these attention patterns to help")
        print("understand why the model makes certain predictions!")
    
    def _lesson_sampling(self) -> None:
        """Lesson on sampling strategies."""
        print("\n" + "="*60)
        print("SAMPLING STRATEGIES control how random or focused the model's")
        print("predictions are. Three main techniques: Temperature, Top-K, Top-P")
        print("="*60)
        
        example_text = "The weather today is"
        print(f"\nExample: '{example_text}'")
        
        input_ids, attention_mask = self.engine.encode(example_text, add_special_tokens=True)
        
        # Show different temperature effects
        print("\n🌡️  TEMPERATURE controls randomness:")
        print("  • Low (0.3) = More focused, predictable")
        print("  • Medium (0.7) = Balanced creativity")
        print("  • High (1.5) = More random, creative")
        
        for temp in [0.3, 0.7, 1.5]:
            pred_result = self.engine.predict_next(
                input_ids,
                attention_mask,
                temperature=temp,
                top_k=50,
                top_p=1.0,
                return_attention=False
            )
            
            tokens, probs, _ = self.engine.get_probabilities_at_step(
                pred_result["logits_after_temperature"],
                "temperature",
                k=5
            )
            
            print(f"\n  Temperature {temp}:")
            for token, prob in zip(tokens[:3], probs[:3]):
                print(f"    '{token}': {prob:.1%}")
        
        time.sleep(1)
        
        # Show Top-K filtering
        print("\n🎯 TOP-K keeps only the K most likely tokens:")
        pred_result = self.engine.predict_next(
            input_ids,
            attention_mask,
            temperature=0.7,
            top_k=5,
            top_p=1.0,
            return_attention=False
        )
        
        tokens_before, _, _ = self.engine.get_probabilities_at_step(
            pred_result["logits_after_temperature"],
            "temperature",
            k=10
        )
        
        tokens_after, _, _ = self.engine.get_probabilities_at_step(
            pred_result["logits_after_top_k"],
            "top_k",
            k=10
        )
        
        print(f"  Before Top-5: {len(tokens_before)} possible tokens")
        print(f"  After Top-5: {len(tokens_after)} tokens remain")
        filtered_str = ', '.join([f"'{t}'" for t in tokens_after[:5]])
        print(f"  Filtered tokens: {filtered_str}")
        
        time.sleep(1)
        
        # Show Top-P filtering
        print("\n📊 TOP-P (Nucleus) keeps tokens until cumulative probability ≥ P:")
        pred_result = self.engine.predict_next(
            input_ids,
            attention_mask,
            temperature=0.7,
            top_k=50,
            top_p=0.9,
            return_attention=False
        )
        
        tokens_p, probs_p, _ = self.engine.get_probabilities_at_step(
            pred_result["logits_after_top_p"],
            "top_p",
            k=20
        )
        
        cumulative = 0
        for i, (token, prob) in enumerate(zip(tokens_p, probs_p)):
            cumulative += prob
            print(f"  '{token}': {prob:.1%} (cumulative: {cumulative:.1%})")
            if cumulative >= 0.9:
                print(f"  ↑ Cutoff at {i+1} tokens (≥90%)")
                break
        
        print("\n💡 In the game, you'll see how each filter changes the probabilities")
        print("and need to predict which tokens survive all the filtering!")
    
    def _lesson_generation(self) -> None:
        """Lesson on autoregressive generation."""
        print("\n" + "="*60)
        print("AUTOREGRESSIVE GENERATION builds text one token at a time,")
        print("using previous predictions as input for the next prediction.")
        print("="*60)
        
        start_text = "Once upon"
        print(f"\nStarting with: '{start_text}'")
        print("\nWatch as the model generates text step by step:")
        
        current_text = start_text
        input_ids, attention_mask = self.engine.encode(current_text, add_special_tokens=True)
        
        for step in range(5):
            print(f"\n🔄 Step {step + 1}:")
            print(f"   Input: '{current_text}'")
            
            # Predict next token
            pred_result = self.engine.predict_next(
                input_ids,
                attention_mask,
                temperature=0.7,
                top_k=8,
                top_p=0.95,
                return_attention=False
            )
            
            next_token_id = pred_result["next_token_id"]
            next_token_text = self.engine.get_token_text(next_token_id)
            
            # Show top predictions
            tokens, probs, _ = self.engine.get_probabilities_at_step(
                pred_result["logits_after_top_p"],
                "final",
                k=3
            )
            
            print("   Top predictions:")
            for token, prob in zip(tokens, probs):
                marker = "→" if token == next_token_text else " "
                print(f"     {marker} '{token}': {prob:.1%}")
            
            # Update text
            decoded_token = self.engine.decode([next_token_id], skip_special_tokens=True)
            if not decoded_token:
                decoded_token = next_token_text
            current_text += decoded_token
            
            print(f"   Output: '{current_text}'")
            
            # Update input_ids for next iteration
            if "torch" in str(type(input_ids)):
                import torch
                device = input_ids.device
                next_token_tensor = torch.tensor([[next_token_id]], device=device)
                input_ids = torch.cat([input_ids, next_token_tensor], dim=-1)
                if attention_mask is not None:
                    attention_mask = torch.cat([attention_mask, torch.ones((1, 1), device=device)], dim=-1)
            else:
                # Handle other tensor types
                input_ids = self._concatenate_ids(input_ids, [[next_token_id]])
            
            time.sleep(1)
        
        print("\n💡 Key Concepts:")
        print("• Each new token becomes part of the input for the next prediction")
        print("• The model has no plan - it just predicts one token at a time")
        print("• Different sampling settings create different 'personalities'")
        print("• In the game, YOU try to predict what the model will choose!")
    
    def _get_token_ids_list(self, input_ids) -> List[int]:
        """Convert tensor to list of token IDs."""
        if hasattr(input_ids, 'tolist'):
            ids = input_ids.tolist()
            if isinstance(ids[0], list):
                return ids[0]
            return ids
        elif isinstance(input_ids, list):
            if isinstance(input_ids[0], list):
                return input_ids[0]
            return input_ids
        return []
    
    def _concatenate_ids(self, ids1, ids2):
        """Concatenate token IDs based on type."""
        if hasattr(ids1, 'cat'):
            import torch
            return torch.cat([ids1, torch.tensor(ids2, device=ids1.device)], dim=-1)
        elif isinstance(ids1, list):
            return ids1 + ids2
        return ids1