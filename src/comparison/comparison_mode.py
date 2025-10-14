"""
Model Comparison Mode for GAMMA - Compare predictions across different models
"""

import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from src.core import config as cfg
from src.core import ui
from src.core import game_logic
from src.core.engine_interface import LLMEngine
from src.engines.engine_factory import get_engine


@dataclass
class ModelPrediction:
    """Store prediction data for a model."""
    model_name: str
    tokens: List[str]
    probabilities: List[float]
    token_ids: List[int]
    next_token: str
    next_token_prob: float
    attention_weights: Optional[List[float]] = None
    prediction_time: float = 0.0


class ComparisonMode:
    """Compare multiple models' predictions side by side."""
    
    def __init__(self, models: List[Tuple[str, str]], args: Any):
        """
        Initialize comparison mode with multiple models.
        
        Args:
            models: List of (engine_type, model_name) tuples
            args: Command line arguments
        """
        self.models = models
        self.args = args
        self.engines: List[LLMEngine] = []
        self.model_names: List[str] = []
        self.total_scores: Dict[str, int] = {}
        self.prediction_history: List[Dict[str, ModelPrediction]] = []
        
    def load_models(self) -> bool:
        """Load all models for comparison."""
        print(ui.color_text("\n📊 Loading models for comparison...", cfg.COLOR_CYAN))
        
        for engine_type, model_name in self.models:
            try:
                print(f"\nLoading {model_name} with {engine_type} engine...")
                
                # Create config for this model
                model_config = vars(self.args).copy()
                model_config['engine'] = engine_type
                model_config['model'] = model_name
                
                engine = get_engine(engine_type, model_name, model_config)
                engine.load()
                
                self.engines.append(engine)
                self.model_names.append(f"{model_name.split('/')[-1]}")
                self.total_scores[model_name] = 0
                
                print(ui.color_text(f"✓ {model_name} loaded", cfg.COLOR_GREEN))
                
            except Exception as e:
                print(ui.color_text(f"✗ Failed to load {model_name}: {e}", cfg.COLOR_RED))
                return False
        
        if len(self.engines) < 2:
            print(ui.color_text("\n⚠️  Need at least 2 models for comparison mode", cfg.COLOR_YELLOW))
            return False
            
        return True
    
    def run_comparison(self) -> None:
        """Run the comparison game loop."""
        ui.print_separator()
        print(ui.color_text("🔬 Model Comparison Mode", cfg.COLOR_CYAN))
        print(f"\nComparing {len(self.engines)} models:")
        for i, name in enumerate(self.model_names, 1):
            print(f"  {i}. {name}")
        
        # Get initial text
        ui.print_separator()
        initial_text = ui.get_user_input(
            "Enter a starting sentence (or press Enter for default)",
            allow_empty=True,
            default_val_on_empty="The future of AI"
        )
        
        if initial_text == cfg.SHORTCUT_QUIT:
            return
        
        current_text = initial_text
        round_counter = 0
        max_rounds = self.args.steps
        
        # Initialize each model's context
        model_contexts = {}
        for engine, model_name in zip(self.engines, self.model_names):
            input_ids, attention_mask = engine.encode(current_text, add_special_tokens=True)
            model_contexts[model_name] = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'engine': engine
            }
        
        # Main comparison loop
        while round_counter < max_rounds:
            round_counter += 1
            ui.display_round_header(round_counter, max_rounds)
            ui.display_current_sentence(current_text)
            
            # Get predictions from all models
            predictions = self._get_all_predictions(model_contexts, current_text)
            
            # Display comparison
            self._display_comparison(predictions)
            
            # Let player guess which model will be most confident
            if self.args.player_choice_mode:
                winner_model = self._player_voting(predictions)
            else:
                # Find model with highest confidence
                winner_model = max(predictions.items(), 
                                 key=lambda x: x[1].next_token_prob)[0]
            
            print(f"\n🏆 Most confident: {ui.color_text(winner_model, cfg.COLOR_GREEN)}")
            
            # Show agreement analysis
            self._analyze_agreement(predictions)
            
            # Use consensus or winner's prediction for next token
            next_token_text, next_token_id = self._get_consensus_token(predictions, winner_model)
            
            # Check for EOS
            if any(engine.tokenizer.eos_token_id == next_token_id 
                   for engine in self.engines 
                   if hasattr(engine.tokenizer, 'eos_token_id')):
                print(ui.color_text("\n<End of Sequence> token generated. Ending comparison.", cfg.COLOR_YELLOW))
                break
            
            # Update all contexts
            current_text += next_token_text
            print(f"\n➡️  Adding token: '{next_token_text}'")
            
            for model_name, context in model_contexts.items():
                engine = context['engine']
                # Update the context with the new token
                new_ids, new_mask = engine.encode(current_text, add_special_tokens=True)
                context['input_ids'] = new_ids
                context['attention_mask'] = new_mask
            
            # Store history
            self.prediction_history.append(predictions)
            
            # Pause for readability
            if not self.args.verbose:
                time.sleep(0.5)
        
        # Show final statistics
        self._show_final_statistics()
    
    def _get_all_predictions(self, model_contexts: Dict, current_text: str) -> Dict[str, ModelPrediction]:
        """Get predictions from all models."""
        predictions = {}
        
        print("\n" + "="*60)
        print(ui.color_text("Getting predictions from all models...", cfg.COLOR_CYAN))
        
        for model_name, context in model_contexts.items():
            engine = context['engine']
            input_ids = context['input_ids']
            attention_mask = context['attention_mask']
            
            start_time = time.time()
            
            # Get prediction
            pred_result = engine.predict_next(
                input_ids,
                attention_mask,
                self.args.temperature,
                self.args.top_k,
                self.args.top_p,
                output_attentions=self.args.show_attention
            )
            
            prediction_time = time.time() - start_time
            
            # Get top tokens and probabilities
            # Try different key names for compatibility
            logits_key = None
            for key in ["logits_processed", "logits_after_top_p", "logits_raw"]:
                if key in pred_result:
                    logits_key = key
                    break

            if logits_key is None:
                raise KeyError(f"Could not find logits in prediction result. Available keys: {pred_result.keys()}")

            tokens, probs, token_ids = engine.get_probabilities_at_step(
                pred_result[logits_key],
                "final",
                k=5
            )
            
            # Get the selected next token
            next_token_id = pred_result["next_token_id"]
            next_token_text = engine.get_token_text(next_token_id)
            
            # Find probability of selected token
            next_token_prob = 0.0
            if next_token_id in token_ids:
                idx = token_ids.index(next_token_id)
                next_token_prob = probs[idx]
            
            # Get attention weights if available
            attention_weights = None
            if self.args.show_attention and pred_result.get("attention"):
                _, attn_scores = engine.get_attention_for_visualization(
                    pred_result["attention"],
                    input_ids
                )
                attention_weights = attn_scores
            
            predictions[model_name] = ModelPrediction(
                model_name=model_name,
                tokens=tokens,
                probabilities=probs,
                token_ids=token_ids,
                next_token=next_token_text,
                next_token_prob=next_token_prob,
                attention_weights=attention_weights,
                prediction_time=prediction_time
            )
        
        return predictions
    
    def _display_comparison(self, predictions: Dict[str, ModelPrediction]) -> None:
        """Display side-by-side comparison of predictions."""
        print("\n" + "="*60)
        print(ui.color_text("📊 Model Predictions Comparison", cfg.COLOR_YELLOW))
        print("="*60)
        
        # Create columns for each model
        num_models = len(predictions)
        col_width = max(20, 60 // num_models)
        
        # Header row
        print("\n", end="")
        for model_name in predictions.keys():
            print(f"{model_name[:col_width-1]:<{col_width}}", end="")
        print()
        
        print("-" * (col_width * num_models))
        
        # Top 5 predictions for each model
        for i in range(5):
            for model_name, pred in predictions.items():
                if i < len(pred.tokens):
                    token = pred.tokens[i][:8]  # Truncate long tokens
                    prob = pred.probabilities[i]
                    # Highlight if this is the chosen token
                    if token == pred.next_token:
                        text = ui.color_text(f"→{token}: {prob:.1%}", cfg.COLOR_GREEN)
                    else:
                        text = f" {token}: {prob:.1%}"
                    print(f"{text:<{col_width}}", end="")
                else:
                    print(f"{'':<{col_width}}", end="")
            print()
        
        # Show timing
        print("\n" + "-" * (col_width * num_models))
        for model_name, pred in predictions.items():
            time_str = f"⏱ {pred.prediction_time:.3f}s"
            print(f"{time_str:<{col_width}}", end="")
        print()
        
        # Show attention focus if available
        if any(p.attention_weights for p in predictions.values()):
            print("\n" + ui.color_text("🎯 Attention Focus:", cfg.COLOR_CYAN))
            for model_name, pred in predictions.items():
                if pred.attention_weights:
                    max_attn_idx = pred.attention_weights.index(max(pred.attention_weights))
                    print(f"  {model_name}: Position {max_attn_idx} (weight: {pred.attention_weights[max_attn_idx]:.3f})")
    
    def _player_voting(self, predictions: Dict[str, ModelPrediction]) -> str:
        """Let player vote on which model's prediction to use."""
        print("\n" + ui.color_text("🗳️  Player Choice Mode", cfg.COLOR_MAGENTA_LIGHT))
        print("Which model's prediction seems most appropriate?")
        
        choices = []
        for i, (model_name, pred) in enumerate(predictions.items(), 1):
            print(f"  {i}. {model_name}: '{pred.next_token}' ({pred.next_token_prob:.1%} confidence)")
            choices.append(str(i))
        
        choice = ui.get_user_input(
            f"Select model (1-{len(predictions)})",
            valid_choices=choices,
            allow_quit=False
        )
        
        selected_idx = int(choice) - 1
        selected_model = list(predictions.keys())[selected_idx]
        
        # Update score
        self.total_scores[selected_model] += 1
        
        return selected_model
    
    def _analyze_agreement(self, predictions: Dict[str, ModelPrediction]) -> None:
        """Analyze how much models agree with each other."""
        print("\n" + ui.color_text("🤝 Model Agreement Analysis:", cfg.COLOR_BLUE))
        
        # Check if all models predict the same token
        all_tokens = [p.next_token for p in predictions.values()]
        unique_tokens = set(all_tokens)
        
        if len(unique_tokens) == 1:
            print(ui.color_text("  ✓ Perfect agreement!", cfg.COLOR_GREEN))
            print(f"  All models chose: '{all_tokens[0]}'")
        else:
            print(f"  ⚡ Models disagree! {len(unique_tokens)} different predictions:")
            
            # Count votes for each token
            token_votes = {}
            for token in all_tokens:
                token_votes[token] = token_votes.get(token, 0) + 1
            
            for token, count in sorted(token_votes.items(), key=lambda x: -x[1]):
                models = [name for name, p in predictions.items() if p.next_token == token]
                print(f"    '{token}': {count} vote(s) - {', '.join(models)}")
        
        # Calculate average confidence
        avg_confidence = sum(p.next_token_prob for p in predictions.values()) / len(predictions)
        print(f"\n  📊 Average confidence: {avg_confidence:.1%}")
        
        # Find outliers
        if avg_confidence > 0:
            for model_name, pred in predictions.items():
                diff = abs(pred.next_token_prob - avg_confidence)
                if diff > 0.2:  # 20% difference
                    if pred.next_token_prob > avg_confidence:
                        print(f"  ↑ {model_name} is very confident ({pred.next_token_prob:.1%})")
                    else:
                        print(f"  ↓ {model_name} is uncertain ({pred.next_token_prob:.1%})")
    
    def _get_consensus_token(self, predictions: Dict[str, ModelPrediction], 
                           winner_model: str) -> Tuple[str, int]:
        """Get consensus token or use winner's choice."""
        # Check for consensus
        all_tokens = [(p.next_token, p.next_token_prob) for p in predictions.values()]
        token_votes = {}
        
        for token, prob in all_tokens:
            if token not in token_votes:
                token_votes[token] = []
            token_votes[token].append(prob)
        
        # Find token with most votes
        most_voted = max(token_votes.items(), key=lambda x: len(x[1]))
        
        if len(most_voted[1]) > len(predictions) / 2:
            # Majority agrees
            consensus_token = most_voted[0]
            print(f"\n📍 Using majority choice: '{consensus_token}'")
        else:
            # No clear majority, use winner
            consensus_token = predictions[winner_model].next_token
            print(f"\n📍 No consensus, using {winner_model}'s choice: '{consensus_token}'")
        
        # Get token ID from first model that has this token
        token_id = 0
        for pred in predictions.values():
            if pred.next_token == consensus_token:
                idx = pred.tokens.index(consensus_token) if consensus_token in pred.tokens else 0
                if idx < len(pred.token_ids):
                    token_id = pred.token_ids[idx]
                    break
        
        return consensus_token, token_id
    
    def _show_final_statistics(self) -> None:
        """Show final comparison statistics."""
        ui.print_separator()
        print(ui.color_text("\n📈 Final Comparison Statistics", cfg.COLOR_CYAN))
        print("="*60)
        
        if self.prediction_history:
            # Agreement rate
            total_rounds = len(self.prediction_history)
            agreement_rounds = sum(
                1 for preds in self.prediction_history
                if len(set(p.next_token for p in preds.values())) == 1
            )
            agreement_rate = (agreement_rounds / total_rounds) * 100
            
            print(f"\n🤝 Agreement Rate: {agreement_rate:.1f}%")
            print(f"   Models agreed on {agreement_rounds}/{total_rounds} predictions")
            
            # Average confidence per model
            print("\n📊 Average Confidence by Model:")
            for model_name in self.model_names:
                confidences = [
                    preds[model_name].next_token_prob 
                    for preds in self.prediction_history
                    if model_name in preds
                ]
                if confidences:
                    avg_conf = sum(confidences) / len(confidences)
                    print(f"   {model_name}: {avg_conf:.1%}")
            
            # Speed comparison
            print("\n⚡ Average Prediction Speed:")
            for model_name in self.model_names:
                times = [
                    preds[model_name].prediction_time 
                    for preds in self.prediction_history
                    if model_name in preds
                ]
                if times:
                    avg_time = sum(times) / len(times)
                    print(f"   {model_name}: {avg_time:.3f}s")
            
            # Player scores (if in player choice mode)
            if self.args.player_choice_mode and any(self.total_scores.values()):
                print("\n🏆 Player Selection Scores:")
                for model, score in sorted(self.total_scores.items(), 
                                          key=lambda x: -x[1]):
                    print(f"   {model}: {score} selections")
        
        print("\n" + "="*60)
        print(ui.color_text("Comparison complete! 🎉", cfg.COLOR_GREEN))