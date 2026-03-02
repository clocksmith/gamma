"""
GAMMA CLI Game Controller

This module contains the game state machine and flow control logic.
"""

import argparse
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from src.core import config as cfg
from src.core.fallback_telemetry import FallbackTelemetry
from src.core.engine_interface import LLMEngine
from src.game import game_logic
from src.game.difficulty_levels import (
    DifficultyLevel,
    DifficultyManager,
    GameSession,
    RoundStats,
)
from src.game.cli.renderer import (
    display_final_score_and_message,
    display_round_info,
    display_session_summary,
    display_level_transition,
    display_personalized_tip,
    display_debug_token_info,
    display_player_choice_mode_info,
    display_eos_reached,
    # New visual enhancements
    get_attention_tracker,
    get_streak_tracker,
    reset_trackers,
    display_attention_history,
    display_streak_notification,
    display_round_result_enhanced,
    display_game_header_enhanced,
    display_compact_stats,
)
from src.ui import displays as ui

logger = logging.getLogger(__name__)
_FALLBACKS = FallbackTelemetry("game_cli_controller", logger)

# Global for tracking explained tokens in focus mode
PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE: Set[Union[int, str]] = set()


class GameController:
    """Controls the game state machine and flow."""

    def __init__(self, engine: LLMEngine, args: argparse.Namespace):
        self.engine = engine
        self.args = args
        self.session: Optional[GameSession] = None
        self.current_full_text: str = ""
        self.total_score: int = 0
        self.total_max_score: int = 0
        self.round_counter: int = 0

        # Tensor tracking
        self.full_history_input_ids: Any = None
        self.full_history_attention_mask: Any = None
        self.incremental_input_ids: Any = None

        # Visual tracking (using global instances)
        self.attention_tracker = get_attention_tracker()
        self.streak_tracker = get_streak_tracker()
        reset_trackers()  # Start fresh for new game

    def initialize_session(self) -> GameSession:
        """Initialize a new game session."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.session = GameSession(
            session_id=session_id,
            current_level=DifficultyLevel.SIMPLE
        )
        return self.session

    def get_initial_prompt(self) -> Optional[str]:
        """Get the initial prompt from user."""
        initial_text = ui.get_user_input(
            "Enter a starting sentence (or press Enter for default)",
            allow_empty=True,
            default_val_on_empty="Mars attacks"
        )

        if initial_text == cfg.SHORTCUT_QUIT:
            return None

        return initial_text

    def setup_context(self, initial_text: str) -> None:
        """Set up the initial context for generation."""
        self.current_full_text = initial_text
        self.full_history_input_ids, self.full_history_attention_mask = \
            self.engine.encode(self.current_full_text, add_special_tokens=True)
        self.incremental_input_ids = self.full_history_input_ids

    def run_single_round(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Run a single round of the game.

        Returns:
            Tuple of (should_continue, round_result)
        """
        self.round_counter += 1

        # Enhanced header with progress and streak
        display_game_header_enhanced(
            self.round_counter,
            self.args.steps,
            self.total_score,
            self.streak_tracker.current_streak
        )
        ui.display_current_sentence(self.current_full_text)

        # Determine input for prediction
        use_kv_cache = (
            hasattr(self.engine, 'engine_config') and
            self.engine.engine_config.get('use_kv_cache', cfg.PYTORCH_USE_KV_CACHE)
        )

        if self.round_counter == 1 or not use_kv_cache:
            ids_for_prediction = self.full_history_input_ids
        else:
            ids_for_prediction = self.incremental_input_ids

        attention_mask_for_prediction = self.full_history_attention_mask

        # Perform prediction
        pred_result = self.engine.predict_next(
            ids_for_prediction,
            attention_mask_for_prediction,
            self.args.temperature,
            self.args.top_k,
            self.args.top_p,
            self.args.show_attention
        )

        # Track round timing
        round_start_time = time.time()

        # Process player guess
        score, max_s, chosen_sequence_info, correct_sequence_info = game_logic.process_player_guess(
            self.engine,
            pred_result,
            self.args,
            self.current_full_text,
            PREVIOUSLY_EXPLAINED_TOKENS_IN_FOCUS_MODE
        )

        if score == -1:
            return False, None

        self.total_score += score
        self.total_max_score += max_s

        # Determine if correct
        is_correct = (score == max_s)

        # Track streak and display notification
        streak, is_new_best = self.streak_tracker.record_result(is_correct)
        display_streak_notification(streak, is_new_best)

        # Show attention visualization if requested (now with correctness info)
        if self.args.show_attention and pred_result.get("attention"):
            self._show_attention(pred_result, is_correct)

        # Display enhanced result
        chosen_text = chosen_sequence_info[0][0] if chosen_sequence_info else "?"
        correct_text = correct_sequence_info[0][0] if correct_sequence_info else "?"
        display_round_result_enhanced(
            is_correct, score, max_s, streak, chosen_text, correct_text
        )

        # Track round stats
        round_stats = self._create_round_stats(pred_result, score, max_s, round_start_time)
        self.session.add_round(round_stats)

        # Show compact stats periodically
        if self.round_counter % 3 == 0:
            display_compact_stats(
                self.streak_tracker.total_correct,
                self.streak_tracker.total_rounds,
                self.streak_tracker.best_streak,
                self.streak_tracker.current_streak
            )

        # Show attention history periodically (every 5 rounds)
        if self.round_counter % 5 == 0 and self.attention_tracker.history:
            display_attention_history(self.attention_tracker)

        # Show personalized tips periodically
        if self.round_counter % 5 == 0:
            tip = self.session.get_personalized_tip()
            if tip:
                display_personalized_tip(tip)

        # Check for level changes periodically
        if self.round_counter % 10 == 0:
            self._check_level_change()

        # Determine and apply next token
        next_token_id, next_token_text = self._determine_next_token(
            pred_result, score, max_s, chosen_sequence_info
        )

        # Check for EOS
        if self._is_eos_token(next_token_id):
            display_eos_reached()
            return False, pred_result

        # Update context with new token
        self._update_context(next_token_id, next_token_text)

        return True, pred_result

    def _show_attention(self, pred_result: Dict[str, Any], is_correct: bool = False) -> None:
        """Show attention visualization and track history."""
        attn_texts, attn_scores = self.engine.get_attention_for_visualization(
            pred_result["attention"],
            self.full_history_input_ids
        )
        if attn_texts and attn_scores:
            ui.display_attention_heatmap(attn_texts, attn_scores, self.args.verbose)
            # Track in attention history
            self.attention_tracker.add_round(
                round_num=self.round_counter,
                token_texts=attn_texts,
                attention_scores=attn_scores,
                is_correct=is_correct
            )
        elif self.args.verbose:
            print(ui.color_text("(Attention data unavailable/unprocessed this step)", cfg.COLOR_YELLOW))

    def _create_round_stats(
        self,
        pred_result: Dict[str, Any],
        score: int,
        max_s: int,
        round_start_time: float
    ) -> RoundStats:
        """Create round statistics."""
        correct_token_prob = self._extract_probability_for_token(
            pred_result, pred_result["next_token_id"]
        ) or 0.0

        return RoundStats(
            round_number=self.round_counter,
            correct=(score == max_s),
            probability_of_correct=correct_token_prob,
            time_taken_seconds=time.time() - round_start_time,
            difficulty_level=self.session.current_level,
            temperature=self.args.temperature,
            top_k=self.args.top_k
        )

    def _extract_probability_for_token(
        self,
        prediction: Dict[str, Any],
        token_id: int
    ) -> Optional[float]:
        """Extract probability for a specific token from prediction results."""
        probability_keys = [
            "probabilities_processed",
            "probabilities",
            "probabilities_top_k",
            "probabilities_temp",
            "probabilities_raw",
        ]
        for key in probability_keys:
            probs_source = prediction.get(key)
            if probs_source is None:
                continue
            try:
                if isinstance(probs_source, dict):
                    value = probs_source.get(token_id)
                    if value is not None:
                        return float(value)
                    continue
                if hasattr(probs_source, "detach") and callable(getattr(probs_source, "detach")):
                    array = probs_source.detach().cpu().numpy()
                elif hasattr(probs_source, "cpu") and callable(getattr(probs_source, "cpu")) and hasattr(probs_source, "numpy"):
                    array = probs_source.cpu().numpy()
                else:
                    array = np.asarray(probs_source)
                array = np.asarray(array).reshape(-1)
                if 0 <= token_id < array.size:
                    return float(array[token_id])
            except (AttributeError, RuntimeError, TypeError, ValueError, IndexError, KeyError) as exc:
                _FALLBACKS.record("extract_probability_failed", exc)
                continue
        return None

    def _check_level_change(self) -> None:
        """Check if level should change based on performance."""
        recommended_level = DifficultyManager.recommend_level(self.session)
        if recommended_level != self.session.current_level:
            message = DifficultyManager.get_level_transition_message(
                self.session.current_level,
                recommended_level
            )
            display_level_transition(self.session.current_level, recommended_level, message)

            response = ui.get_user_input(
                "Accept level change? (y/n)",
                allow_empty=False
            )
            if response.lower() == 'y':
                self.session.current_level = recommended_level
                print(f"\n{cfg.COLOR_GREEN}Level changed!{cfg.COLOR_RESET}")
                print(f"New features: {', '.join(recommended_level.get_features()[-2:])}\n")

    def _determine_next_token(
        self,
        pred_result: Dict[str, Any],
        score: int,
        max_s: int,
        chosen_sequence_info: Optional[List]
    ) -> Tuple[int, str]:
        """Determine the next token based on game mode."""
        if self.args.player_choice_mode and chosen_sequence_info and score == max_s:
            next_token_id = chosen_sequence_info[0][1]
            next_token_text = chosen_sequence_info[0][0]
            display_player_choice_mode_info(next_token_text)
        else:
            next_token_id = pred_result["next_token_id"]
            next_token_text = self.engine.get_token_text(next_token_id)

        return next_token_id, next_token_text

    def _is_eos_token(self, token_id: int) -> bool:
        """Check if token is end-of-sequence."""
        return (
            hasattr(self.engine.tokenizer, 'eos_token_id') and
            token_id == self.engine.tokenizer.eos_token_id
        )

    def _update_context(self, next_token_id: int, next_token_text: str) -> None:
        """Update the context with the new token."""
        decoded_token = self.engine.decode([next_token_id])
        if not decoded_token:
            decoded_token = next_token_text
        self.current_full_text += decoded_token

        if self.args.verbose:
            display_debug_token_info(
                next_token_text, next_token_id, decoded_token, self.current_full_text
            )

        # Update tensor tracking
        next_token_array = np.array([[next_token_id]])
        next_token_tensor = self.engine.convert_from_numpy(next_token_array)

        self.full_history_input_ids = self._concatenate_tensors(
            self.full_history_input_ids, next_token_tensor, dim=-1
        )

        if self.full_history_attention_mask is not None:
            batch_size = 1
            if hasattr(self.full_history_attention_mask, 'shape'):
                if len(self.full_history_attention_mask.shape) > 1:
                    batch_size = self.full_history_attention_mask.shape[0]

            ones_array = np.ones((batch_size, 1))
            ones_tensor = self.engine.convert_from_numpy(ones_array)

            if ones_tensor is not None:
                self.full_history_attention_mask = self._concatenate_tensors(
                    self.full_history_attention_mask, ones_tensor, dim=-1
                )

        self.incremental_input_ids = next_token_tensor

    def _concatenate_tensors(
        self,
        tensor1: Any,
        tensor2: Any,
        dim: int = -1
    ) -> Optional[Any]:
        """Concatenate tensors using engine abstraction."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1

        try:
            return self.engine.concatenate_tensors(tensor1, tensor2, dim=dim)
        except (AttributeError, RuntimeError, TypeError, ValueError) as e:
            _FALLBACKS.record("concatenate_tensors_failed", e)
            print(f"Warning: Failed to concatenate using engine abstraction: {e}")

        if isinstance(tensor1, list) and isinstance(tensor2, list):
            return tensor1 + tensor2

        print(f"Warning: Could not concatenate tensors of types ({type(tensor1)}, {type(tensor2)})")
        return None

    def finalize_session(self) -> None:
        """Save session and display final results."""
        # Show final attention history if available
        if self.attention_tracker.history:
            display_attention_history(self.attention_tracker)

        display_final_score_and_message(
            self.total_score, self.total_max_score, self.current_full_text
        )

        # Show final streak stats
        if self.streak_tracker.best_streak >= 2:
            print(f"\n{cfg.COLOR_YELLOW}🏆 Best Streak: {self.streak_tracker.best_streak} correct in a row!{cfg.COLOR_RESET}")

        # Save session
        os.makedirs("sessions", exist_ok=True)
        session_file = f"sessions/{self.session.session_id}.json"
        self.session.save_to_file(session_file)

        # Display summary
        stats = self.session.export_stats()
        achievements_with_desc = [
            self.session.get_achievement_description(a)
            for a in self.session.achievements
        ]
        display_session_summary(
            self.session.session_id,
            self.session.current_level,
            stats,
            achievements_with_desc,
            session_file
        )


def run_game_loop(engine: LLMEngine, args: argparse.Namespace) -> None:
    """Main game loop with difficulty levels and session tracking."""
    controller = GameController(engine, args)

    # Initialize session
    controller.initialize_session()

    # Welcome message
    ui.print_separator()
    print(f"\n{cfg.COLOR_CYAN}🎮 Welcome to GAMMA!{cfg.COLOR_RESET}")
    print(f"\nCurrent Level: {controller.session.current_level.get_display_name()}")
    print(f"{controller.session.current_level.get_description()}\n")

    # Get initial prompt
    initial_text = controller.get_initial_prompt()
    if initial_text is None:
        return

    controller.setup_context(initial_text)

    # Main game loop
    while controller.round_counter < args.steps:
        should_continue, pred_result = controller.run_single_round()
        if not should_continue:
            break

    controller.finalize_session()

    # Offer to continue if not at EOS
    if args.allow_eos_continue and controller.round_counter >= args.steps:
        if pred_result and not controller._is_eos_token(pred_result.get("next_token_id", -1)):
            continue_choice = ui.get_user_input(
                "\nMax steps reached but no <EOS>. Continue for more rounds? (y/n)",
                valid_choices=["y", "n"],
                allow_quit=False
            )
            if continue_choice.lower() == "y":
                args.steps += cfg.DEFAULT_MAX_DECODE_STEPS
                run_game_loop(engine, args)
