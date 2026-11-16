"""
Mind Meld Visualization Tools

Real-time visualization of multi-model collaboration.
Shows which model generated which tokens, swap patterns, and quality metrics.

Based on Penteract principles: transparency and structured insight.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys


# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal visualization."""
    MODEL_A = '\033[94m'  # Blue
    MODEL_B = '\033[92m'  # Green
    MODEL_C = '\033[93m'  # Yellow
    MODEL_D = '\033[95m'  # Magenta
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    @classmethod
    def get_model_color(cls, model_index: int) -> str:
        """Get color for model by index."""
        colors = [cls.MODEL_A, cls.MODEL_B, cls.MODEL_C, cls.MODEL_D]
        return colors[model_index % len(colors)]


@dataclass
class SwapEvent:
    """Records a single model swap during generation."""
    position: int  # Token position in sequence
    from_model: str  # Model that was active
    to_model: str  # Model that becomes active
    reason: str  # Why the swap occurred
    timestamp: float  # When it happened
    confidence_before: Optional[float] = None  # Confidence of previous token
    coherence_score: Optional[float] = None  # Smoothness of transition


@dataclass
class ModelContribution:
    """Tracks how much each model contributed."""
    model_name: str
    tokens_generated: int
    total_probability: float  # Sum of probabilities for generated tokens
    avg_confidence: float
    time_active_seconds: float


class SwapVisualizer:
    """
    Real-time visualization of Mind Meld model swaps.

    Shows:
    1. Color-coded text showing which model generated what
    2. Timeline of model contributions
    3. Swap event log with reasons
    4. Coherence scores at transition points
    """

    def __init__(self, model_names: List[str], enable_color: bool = True):
        """
        Initialize visualizer.

        Args:
            model_names: Names of models participating
            enable_color: Whether to use ANSI colors (disable for logging)
        """
        self.model_names = model_names
        self.enable_color = enable_color
        self.swaps: List[SwapEvent] = []
        self.contributions: Dict[str, ModelContribution] = {}

        # Initialize contribution tracking
        for name in model_names:
            self.contributions[name] = ModelContribution(
                model_name=name,
                tokens_generated=0,
                total_probability=0.0,
                avg_confidence=0.0,
                time_active_seconds=0.0
            )

    def add_swap(self, event: SwapEvent) -> None:
        """Record a swap event."""
        self.swaps.append(event)

    def record_token(
        self,
        model_name: str,
        probability: float,
        time_seconds: float
    ) -> None:
        """Record a token generation."""
        contrib = self.contributions[model_name]
        contrib.tokens_generated += 1
        contrib.total_probability += probability
        contrib.time_active_seconds += time_seconds
        contrib.avg_confidence = (
            contrib.total_probability / contrib.tokens_generated
        )

    def highlight_text_by_model(
        self,
        text: str,
        token_positions: List[Tuple[int, int, str]]
    ) -> str:
        """
        Color-code text by which model generated it.

        Args:
            text: The full generated text
            token_positions: List of (start_idx, end_idx, model_name) tuples

        Returns:
            Color-coded string (if enable_color), else annotated string
        """
        if not self.enable_color:
            # Non-color version with brackets
            result = ""
            prev_model = None
            for start, end, model in token_positions:
                if model != prev_model:
                    if prev_model is not None:
                        result += "]"
                    result += f"[{model}: "
                result += text[start:end]
                prev_model = model
            if prev_model is not None:
                result += "]"
            return result

        # Color version
        result = ""
        model_index_map = {name: i for i, name in enumerate(self.model_names)}

        for start, end, model in token_positions:
            color = Colors.get_model_color(model_index_map[model])
            result += f"{color}{text[start:end]}{Colors.RESET}"

        return result

    def render_contribution_timeline(
        self,
        width: int = 80,
        show_percentages: bool = True
    ) -> str:
        """
        Render a horizontal bar chart of model contributions.

        Example output:
        Model A: ████████░░░░████░░ (45.2%, 234 tokens)
        Model B: ░░░░░░░░████░░░░██ (32.8%, 170 tokens)
        Model C: ░░██░░░░░░░░░░░░░░ (22.0%, 114 tokens)

        Args:
            width: Width of the timeline bars
            show_percentages: Whether to show percentage contributions
        """
        total_tokens = sum(
            c.tokens_generated for c in self.contributions.values()
        )
        if total_tokens == 0:
            return "No tokens generated yet."

        lines = []

        if show_percentages:
            lines.append(f"\n{'=' * width}")
            lines.append(f"{'Model Contributions':^{width}}")
            lines.append(f"{'=' * width}\n")

        for model_name, contrib in self.contributions.items():
            percentage = (contrib.tokens_generated / total_tokens) * 100
            filled_width = int((contrib.tokens_generated / total_tokens) * width)

            # Build the bar
            bar = '█' * filled_width + '░' * (width - filled_width)

            # Add percentage and token count
            if show_percentages:
                stats = (
                    f"({percentage:5.1f}%, "
                    f"{contrib.tokens_generated} tokens, "
                    f"avg conf: {contrib.avg_confidence:.2f})"
                )
            else:
                stats = f"({contrib.tokens_generated} tokens)"

            model_display = f"{model_name:15}"
            lines.append(f"{model_display} {bar} {stats}")

        return '\n'.join(lines)

    def render_swap_log(
        self,
        max_events: int = 10,
        show_reasons: bool = True
    ) -> str:
        """
        Render recent swap events as a log.

        Example output:
        Swap Log (last 10 events):
        [12] Model A → Model B (Reason: Low confidence, coherence: 0.85)
        [23] Model B → Model A (Reason: Pattern match, coherence: 0.92)
        """
        if not self.swaps:
            return "No swaps yet."

        lines = [f"\n{'=' * 80}"]
        lines.append(f"{'Swap Event Log':^80}")
        lines.append(f"{'=' * 80}\n")

        recent_swaps = self.swaps[-max_events:]

        for swap in recent_swaps:
            reason_str = f" (Reason: {swap.reason})" if show_reasons else ""
            coherence_str = (
                f", coherence: {swap.coherence_score:.2f}"
                if swap.coherence_score is not None
                else ""
            )
            confidence_str = (
                f", prev conf: {swap.confidence_before:.2f}"
                if swap.confidence_before is not None
                else ""
            )

            lines.append(
                f"[Pos {swap.position:3d}] "
                f"{swap.from_model:15} → {swap.to_model:15}"
                f"{reason_str}{confidence_str}{coherence_str}"
            )

        return '\n'.join(lines)

    def show_coherence_analysis(
        self,
        text: str,
        show_problematic_only: bool = False,
        threshold: float = 0.7
    ) -> str:
        """
        Analyze transition smoothness at each swap point.

        Args:
            text: The generated text
            show_problematic_only: Only show jarring transitions
            threshold: Coherence threshold for "smooth" transitions
        """
        if not self.swaps:
            return "No swaps to analyze."

        lines = [f"\n{'=' * 80}"]
        lines.append(f"{'Coherence Analysis':^80}")
        lines.append(f"{'=' * 80}\n")

        for swap in self.swaps:
            if swap.coherence_score is None:
                continue

            is_smooth = swap.coherence_score >= threshold

            if show_problematic_only and is_smooth:
                continue

            # Visual indicator
            if is_smooth:
                indicator = "✓ Smooth"
                color = Colors.MODEL_B if self.enable_color else ""
            else:
                indicator = "⚠ Jarring"
                color = Colors.MODEL_A if self.enable_color else ""

            reset = Colors.RESET if self.enable_color else ""

            lines.append(
                f"Position {swap.position:3d}: "
                f"{color}{indicator}{reset} "
                f"(coherence: {swap.coherence_score:.2f}) - "
                f"{swap.reason}"
            )

        if not lines[3:]:  # No entries added beyond headers
            return "All transitions are smooth! 🎉"

        return '\n'.join(lines)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics for analysis."""
        total_tokens = sum(
            c.tokens_generated for c in self.contributions.values()
        )

        coherence_scores = [
            s.coherence_score for s in self.swaps
            if s.coherence_score is not None
        ]
        avg_coherence = (
            sum(coherence_scores) / len(coherence_scores)
            if coherence_scores else 0.0
        )

        return {
            "total_tokens": total_tokens,
            "total_swaps": len(self.swaps),
            "swaps_per_token": len(self.swaps) / total_tokens if total_tokens > 0 else 0,
            "avg_coherence": avg_coherence,
            "contributions": {
                name: {
                    "tokens": contrib.tokens_generated,
                    "percentage": (
                        contrib.tokens_generated / total_tokens * 100
                        if total_tokens > 0 else 0
                    ),
                    "avg_confidence": contrib.avg_confidence
                }
                for name, contrib in self.contributions.items()
            }
        }

    def export_to_json(self, filepath: str) -> None:
        """Export visualization data for analysis."""
        import json

        data = {
            "model_names": self.model_names,
            "swaps": [
                {
                    "position": s.position,
                    "from_model": s.from_model,
                    "to_model": s.to_model,
                    "reason": s.reason,
                    "timestamp": s.timestamp,
                    "confidence_before": s.confidence_before,
                    "coherence_score": s.coherence_score
                }
                for s in self.swaps
            ],
            "contributions": {
                name: {
                    "tokens_generated": c.tokens_generated,
                    "avg_confidence": c.avg_confidence,
                    "time_active_seconds": c.time_active_seconds
                }
                for name, c in self.contributions.items()
            },
            "summary": self.get_summary_stats()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> 'SwapVisualizer':
        """
        Load visualization data from a JSON file.

        Args:
            filepath: Path to JSON file created by export_to_json()

        Returns:
            SwapVisualizer instance with loaded data
        """
        import json

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Create visualizer with model names
        viz = cls(model_names=data['model_names'], enable_color=True)

        # Restore swaps
        viz.swaps = [
            SwapEvent(
                position=s['position'],
                from_model=s['from_model'],
                to_model=s['to_model'],
                reason=s['reason'],
                timestamp=s['timestamp'],
                confidence_before=s.get('confidence_before'),
                coherence_score=s.get('coherence_score')
            )
            for s in data['swaps']
        ]

        # Restore contributions
        for name, c_data in data['contributions'].items():
            viz.contributions[name] = ModelContribution(
                model_name=name,
                tokens_generated=c_data['tokens_generated'],
                total_probability=c_data['avg_confidence'] * c_data['tokens_generated'],
                avg_confidence=c_data['avg_confidence'],
                time_active_seconds=c_data['time_active_seconds']
            )

        return viz

    def render_live_update(
        self,
        current_text: str,
        current_model: str,
        last_probability: float
    ) -> None:
        """
        Show a live, updating view during generation.

        Useful for real-time monitoring of Mind Meld in action.
        """
        # Clear screen (optional, can be distracting)
        # print('\033[2J\033[H')

        print(f"\n{'─' * 80}")
        print(f"Mind Meld Live View - Current Model: {Colors.BOLD}{current_model}{Colors.RESET}")
        print(f"{'─' * 80}\n")

        print(f"Generated so far ({len(current_text)} chars):")
        print(f"{current_text}\n")

        print(f"Last token probability: {last_probability:.3f}\n")

        print(self.render_contribution_timeline(width=60))

        sys.stdout.flush()
