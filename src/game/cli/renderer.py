"""
GAMMA CLI Renderer

This module handles all terminal output, formatting, and display functions.
"""

import logging
import shutil
from typing import List, Optional, Tuple

from src.core import config as cfg
from src.core.fallback_telemetry import FallbackTelemetry
from src.ui import displays as ui

logger = logging.getLogger(__name__)
_FALLBACKS = FallbackTelemetry("game_cli_renderer", logger)

# ============================================================================
# Attention History Tracking
# ============================================================================

class AttentionHistoryTracker:
    """Tracks attention patterns across rounds for visualization."""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[dict] = []

    def add_round(
        self,
        round_num: int,
        token_texts: List[str],
        attention_scores: List[float],
        is_correct: bool = False
    ) -> None:
        """Add a round's attention data to history."""
        self.history.append({
            'round': round_num,
            'tokens': token_texts[-15:],  # Keep last 15 tokens per round
            'scores': attention_scores[-15:],
            'correct': is_correct
        })
        # Trim to max history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def clear(self) -> None:
        """Clear history."""
        self.history = []

    def get_display_width(self) -> int:
        """Get maximum display width based on terminal."""
        try:
            return shutil.get_terminal_size().columns
        except (AttributeError, OSError, ValueError) as exc:
            _FALLBACKS.record("terminal_width_unavailable", exc)
            return 80


def display_attention_history(tracker: AttentionHistoryTracker) -> None:
    """Display accumulated attention history as a compact heatmap grid."""
    if not tracker.history:
        return

    print(f"\n{cfg.COLOR_CYAN}{'─'*40}{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_BOLD}📊 Attention History (Last {len(tracker.history)} Rounds){cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_CYAN}{'─'*40}{cfg.COLOR_RESET}")

    # Build the heatmap grid
    for entry in tracker.history:
        round_num = entry['round']
        scores = entry['scores']
        is_correct = entry['correct']

        # Round indicator
        correct_marker = cfg.COLOR_GREEN + "✓" + cfg.COLOR_RESET if is_correct else cfg.COLOR_RED + "✗" + cfg.COLOR_RESET
        round_label = f"R{round_num:2d}{correct_marker} "

        # Build attention bar using block characters
        cells = []
        for score in scores:
            # Map score to block intensity
            if score >= 0.8:
                block = cfg.COLOR_MAGENTA_INTENSE + "█" + cfg.COLOR_RESET
            elif score >= 0.6:
                block = cfg.COLOR_MAGENTA_BRIGHT + "▓" + cfg.COLOR_RESET
            elif score >= 0.4:
                block = cfg.COLOR_MAGENTA_MEDIUM + "▒" + cfg.COLOR_RESET
            elif score >= 0.2:
                block = cfg.COLOR_MAGENTA_LIGHT + "░" + cfg.COLOR_RESET
            else:
                block = cfg.COLOR_MAGENTA_DIM + "·" + cfg.COLOR_RESET
            cells.append(block)

        # Print the row
        print(f"  {round_label}{''.join(cells)}")

    # Legend
    print(f"\n  {cfg.COLOR_MAGENTA_DIM}·{cfg.COLOR_RESET} Low  "
          f"{cfg.COLOR_MAGENTA_LIGHT}░{cfg.COLOR_RESET}  "
          f"{cfg.COLOR_MAGENTA_MEDIUM}▒{cfg.COLOR_RESET}  "
          f"{cfg.COLOR_MAGENTA_BRIGHT}▓{cfg.COLOR_RESET}  "
          f"{cfg.COLOR_MAGENTA_INTENSE}█{cfg.COLOR_RESET} High\n")


# ============================================================================
# Streak and Visual Polish
# ============================================================================

class StreakTracker:
    """Tracks consecutive correct answers for streak display."""

    def __init__(self):
        self.current_streak: int = 0
        self.best_streak: int = 0
        self.total_correct: int = 0
        self.total_rounds: int = 0

    def record_result(self, is_correct: bool) -> Tuple[int, bool]:
        """
        Record a round result.

        Returns:
            Tuple of (current_streak, is_new_best)
        """
        self.total_rounds += 1
        if is_correct:
            self.current_streak += 1
            self.total_correct += 1
            is_new_best = self.current_streak > self.best_streak
            if is_new_best:
                self.best_streak = self.current_streak
            return self.current_streak, is_new_best
        else:
            self.current_streak = 0
            return 0, False

    def get_streak_display(self) -> str:
        """Get a formatted streak display string."""
        if self.current_streak >= 5:
            return f"{cfg.COLOR_YELLOW}🔥🔥🔥 {self.current_streak} STREAK! 🔥🔥🔥{cfg.COLOR_RESET}"
        elif self.current_streak >= 3:
            return f"{cfg.COLOR_YELLOW}🔥 {self.current_streak} streak!{cfg.COLOR_RESET}"
        elif self.current_streak >= 2:
            return f"{cfg.COLOR_GREEN}✨ {self.current_streak} in a row!{cfg.COLOR_RESET}"
        return ""


def display_streak_notification(streak: int, is_new_best: bool) -> None:
    """Display streak notification with visual flair."""
    if streak < 2:
        return

    if is_new_best and streak >= 3:
        print(f"\n  {cfg.COLOR_YELLOW}{'★'*streak} NEW BEST STREAK: {streak}! {'★'*streak}{cfg.COLOR_RESET}")
    elif streak >= 5:
        print(f"\n  {cfg.COLOR_YELLOW}🔥🔥🔥 ON FIRE! {streak} CORRECT IN A ROW! 🔥🔥🔥{cfg.COLOR_RESET}")
    elif streak >= 3:
        print(f"\n  {cfg.COLOR_GREEN}🔥 Nice streak! {streak} in a row!{cfg.COLOR_RESET}")
    else:
        print(f"\n  {cfg.COLOR_GREEN}✨ {streak} in a row!{cfg.COLOR_RESET}")


def display_round_result_enhanced(
    is_correct: bool,
    score: int,
    max_score: int,
    streak: int,
    chosen_text: str,
    correct_text: str
) -> None:
    """Display enhanced round result with visual polish."""
    print()
    if is_correct:
        print(f"  {cfg.COLOR_GREEN}{'━'*50}{cfg.COLOR_RESET}")
        print(f"  {cfg.COLOR_GREEN}✓ CORRECT!{cfg.COLOR_RESET} Score: {score}/{max_score}")
        if streak >= 2:
            streak_bar = "🔥" * min(streak, 10)
            print(f"  {streak_bar} Streak: {streak}")
        print(f"  {cfg.COLOR_GREEN}{'━'*50}{cfg.COLOR_RESET}")
    else:
        print(f"  {cfg.COLOR_RED}{'━'*50}{cfg.COLOR_RESET}")
        print(f"  {cfg.COLOR_RED}✗ Incorrect{cfg.COLOR_RESET} Score: {score}/{max_score}")
        print(f"  Your guess:    {cfg.COLOR_BLUE}{chosen_text}{cfg.COLOR_RESET}")
        print(f"  Model's choice: {cfg.COLOR_GREEN}{correct_text}{cfg.COLOR_RESET}")
        print(f"  {cfg.COLOR_RED}{'━'*50}{cfg.COLOR_RESET}")


def display_progress_bar(current: int, total: int, width: int = 30) -> str:
    """Generate a progress bar string."""
    filled = int((current / total) * width) if total > 0 else 0
    empty = width - filled
    bar = f"[{cfg.COLOR_GREEN}{'█' * filled}{cfg.COLOR_RESET}{'░' * empty}]"
    percentage = (current / total * 100) if total > 0 else 0
    return f"{bar} {current}/{total} ({percentage:.0f}%)"


def display_game_header_enhanced(
    round_num: int,
    max_rounds: int,
    score: int,
    streak: int = 0
) -> None:
    """Display enhanced game header with progress and streak."""
    try:
        term_width = shutil.get_terminal_size().columns
    except (AttributeError, OSError, ValueError) as exc:
        _FALLBACKS.record("header_terminal_width_unavailable", exc)
        term_width = 80

    # Build header components
    title = f"{cfg.COLOR_CYAN}{cfg.COLOR_BOLD}GAMMA{cfg.COLOR_RESET}"
    round_info = f"Round {round_num}/{max_rounds}"
    score_info = f"Score: {score}"
    streak_info = f"🔥{streak}" if streak >= 2 else ""

    # Progress bar
    progress = display_progress_bar(round_num, max_rounds, width=20)

    print(f"\n{cfg.COLOR_CYAN}{'═'*term_width}{cfg.COLOR_RESET}")
    print(f"  {title}  │  {round_info}  │  {score_info}  {streak_info}")
    print(f"  {progress}")
    print(f"{cfg.COLOR_CYAN}{'═'*term_width}{cfg.COLOR_RESET}")


def display_compact_stats(
    total_correct: int,
    total_rounds: int,
    best_streak: int,
    current_streak: int
) -> None:
    """Display compact statistics line."""
    accuracy = (total_correct / total_rounds * 100) if total_rounds > 0 else 0
    accuracy_color = cfg.COLOR_GREEN if accuracy >= 60 else cfg.COLOR_YELLOW if accuracy >= 40 else cfg.COLOR_RED

    print(f"\n  📈 Stats: {accuracy_color}{accuracy:.0f}%{cfg.COLOR_RESET} accuracy "
          f"│ Best streak: {best_streak} │ Current: {current_streak}")


# Global instances for use across the game
_attention_tracker = AttentionHistoryTracker()
_streak_tracker = StreakTracker()


def get_attention_tracker() -> AttentionHistoryTracker:
    """Get the global attention tracker instance."""
    return _attention_tracker


def get_streak_tracker() -> StreakTracker:
    """Get the global streak tracker instance."""
    return _streak_tracker


def reset_trackers() -> None:
    """Reset all trackers for a new game."""
    _attention_tracker.clear()
    _streak_tracker.__init__()


def display_final_score_and_message(
    total_score: int,
    total_max_score: int,
    current_full_text: str
) -> None:
    """Displays the final score and a message to the user."""
    ui.print_separator()
    print(f"\n🎮 {ui.color_text('GAME OVER!', cfg.COLOR_CYAN)}")
    print(f"Final Score: {total_score}/{total_max_score}")

    if total_max_score > 0:
        percentage = (total_score / total_max_score) * 100
        if percentage >= 80:
            print(ui.color_text("🏆 Excellent! You really understand this model!", cfg.COLOR_GREEN))
        elif percentage >= 60:
            print(ui.color_text("👍 Good job! You have a solid grasp of the model's behavior.", cfg.COLOR_YELLOW))
        elif percentage >= 40:
            print(ui.color_text("📚 Not bad! Keep practicing to improve your intuition.", cfg.COLOR_BLUE))
        else:
            print(ui.color_text("💡 Keep learning! LLMs can be unpredictable.", cfg.COLOR_MAGENTA_LIGHT))

    print(f"\nFinal text: \"{current_full_text}\"\n")


def display_round_info(
    round_counter: int,
    max_rounds: int,
    current_full_text: str
) -> None:
    """Display round header and current context."""
    ui.display_round_header(round_counter, max_rounds)
    ui.display_current_sentence(current_full_text)


def display_session_summary(
    session_id: str,
    current_level: 'DifficultyLevel',
    stats: dict,
    achievements: list,
    session_file: str
) -> None:
    """Display end-of-session summary with stats and achievements."""
    print(f"\n{cfg.COLOR_CYAN}{'='*60}{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_BOLD}📊 Session Summary{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_CYAN}{'='*60}{cfg.COLOR_RESET}\n")

    print(f"  Session ID: {session_id}")
    print(f"  Final Level: {current_level.get_display_name()}")
    print(f"  Total Rounds: {stats['total_rounds']}")
    print(f"  Overall Accuracy: {stats['overall_accuracy']:.1%}")
    print(f"  Playtime: {stats['total_playtime_seconds']:.1f} seconds\n")

    if achievements:
        print(f"{cfg.COLOR_GREEN}🏆 Achievements Unlocked:{cfg.COLOR_RESET}")
        for achievement in achievements:
            print(f"  • {achievement}")
        print()

    print(f"{cfg.COLOR_CYAN}Session saved to: {session_file}{cfg.COLOR_RESET}\n")


def display_level_transition(
    old_level: 'DifficultyLevel',
    new_level: 'DifficultyLevel',
    message: str
) -> None:
    """Display level transition message."""
    print(f"\n{cfg.COLOR_YELLOW}{message}{cfg.COLOR_RESET}\n")


def display_personalized_tip(tip: str) -> None:
    """Display a personalized tip for the player."""
    print(f"\n{cfg.COLOR_CYAN}{tip}{cfg.COLOR_RESET}\n")


def display_debug_token_info(
    token_text: str,
    token_id: int,
    decoded_token: str,
    full_text: str
) -> None:
    """Display debug information about token generation."""
    print(f"\n[Debug] Added token: '{token_text}' (ID: {token_id}) -> Decoded: '{decoded_token}'")
    print(f"[Debug] Full text now: '{full_text}'")


def display_player_choice_mode_info(token_text: str) -> None:
    """Display info when using player choice mode."""
    print(ui.color_text(
        f"\n[Player Choice Mode] Using YOUR correct guess: '{token_text}'",
        cfg.COLOR_CYAN
    ))


def display_eos_reached() -> None:
    """Display end-of-sequence token message."""
    print(ui.color_text("\n<End of Sequence> token generated. Ending game.", cfg.COLOR_YELLOW))
