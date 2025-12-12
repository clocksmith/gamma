"""
Pluggable event sink interface for Mind Meld telemetry.

Provides a unified interface for receiving generation events (tokens, swaps)
that can be routed to multiple consumers: file loggers, visualizers, stats
collectors, or real-time dashboards.

Usage:
    from src.mind_meld.core.event_sinks import EventSinkManager, JSONFileSink, ConsoleSink

    manager = EventSinkManager()
    manager.add_sink(JSONFileSink("output.json"))
    manager.add_sink(ConsoleSink())

    # In generation loop:
    manager.on_token_generated(model_name, token_text, probability, ...)
    manager.on_swap(from_model, to_model, reason, ...)

    # After generation:
    manager.finish()
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any

# =============================================================================
# Constants
# =============================================================================

# Maximum tokens to store in JSON file output (prevents huge files)
JSON_SINK_TOKEN_LIMIT = 1000

# Default interval for console progress updates
CONSOLE_SINK_DEFAULT_INTERVAL = 10

# Width of contribution bar in console output
CONTRIBUTION_BAR_WIDTH = 50


@dataclass
class TokenEvent:
    """Event emitted when a token is generated."""
    model_name: str
    token_text: str
    probability: float
    time_seconds: float
    position: int
    perplexity: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class SwapEvent:
    """Event emitted when models swap."""
    position: int
    from_model: str
    to_model: str
    reason: str
    confidence_before: Optional[float] = None
    coherence_score: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


class EventSink(ABC):
    """
    Base class for event sinks.

    Implement this to create custom consumers for Mind Meld events.
    """

    @abstractmethod
    def on_token(self, event: TokenEvent) -> None:
        """Called when a token is generated."""
        pass

    @abstractmethod
    def on_swap(self, event: SwapEvent) -> None:
        """Called when a model swap occurs."""
        pass

    def on_start(self, model_names: List[str]) -> None:
        """Called when generation starts. Override if needed."""
        pass

    def on_finish(self) -> None:
        """Called when generation ends. Override if needed."""
        pass

    def get_summary(self) -> Dict[str, Any]:
        """Return summary data. Override if needed."""
        return {}


class EventSinkManager:
    """
    Manages multiple event sinks and routes events to all of them.

    This allows a single generation loop to emit events that are
    consumed by multiple sinks (file logging, console output, stats, etc).
    """

    def __init__(self):
        self._sinks: List[EventSink] = []
        self._position = 0

    def add_sink(self, sink: EventSink) -> 'EventSinkManager':
        """Add a sink. Returns self for chaining."""
        self._sinks.append(sink)
        return self

    def remove_sink(self, sink: EventSink) -> bool:
        """Remove a sink. Returns True if found and removed."""
        try:
            self._sinks.remove(sink)
            return True
        except ValueError:
            return False

    def start(self, model_names: List[str]) -> None:
        """Signal generation start to all sinks."""
        self._position = 0
        for sink in self._sinks:
            sink.on_start(model_names)

    def on_token_generated(
        self,
        model_name: str,
        token_text: str,
        probability: float,
        time_seconds: float,
        perplexity: Optional[float] = None
    ) -> None:
        """Emit token event to all sinks."""
        self._position += 1
        event = TokenEvent(
            model_name=model_name,
            token_text=token_text,
            probability=probability,
            time_seconds=time_seconds,
            position=self._position,
            perplexity=perplexity
        )
        for sink in self._sinks:
            sink.on_token(event)

    def on_swap(
        self,
        from_model: str,
        to_model: str,
        reason: str,
        confidence_before: Optional[float] = None,
        coherence_score: Optional[float] = None
    ) -> None:
        """Emit swap event to all sinks."""
        event = SwapEvent(
            position=self._position,
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            confidence_before=confidence_before,
            coherence_score=coherence_score
        )
        for sink in self._sinks:
            sink.on_swap(event)

    def finish(self) -> None:
        """Signal generation end to all sinks."""
        for sink in self._sinks:
            sink.on_finish()

    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries from all sinks."""
        return {
            sink.__class__.__name__: sink.get_summary()
            for sink in self._sinks
        }


class JSONFileSink(EventSink):
    """Writes all events to a JSON file."""

    def __init__(self, filepath: str, include_tokens: bool = True):
        self.filepath = filepath
        self.include_tokens = include_tokens
        self._model_names: List[str] = []
        self._tokens: List[TokenEvent] = []
        self._swaps: List[SwapEvent] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def on_start(self, model_names: List[str]) -> None:
        self._model_names = model_names
        self._start_time = time.time()

    def on_token(self, event: TokenEvent) -> None:
        if self.include_tokens:
            self._tokens.append(event)

    def on_swap(self, event: SwapEvent) -> None:
        self._swaps.append(event)

    def on_finish(self) -> None:
        self._end_time = time.time()
        self._write_file()

    def _write_file(self) -> None:
        data = {
            "model_names": self._model_names,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "duration_seconds": (self._end_time - self._start_time) if self._end_time and self._start_time else 0,
            "total_tokens": len(self._tokens),
            "total_swaps": len(self._swaps),
            "swaps": [asdict(s) for s in self._swaps],
        }
        if self.include_tokens:
            data["tokens"] = [asdict(t) for t in self._tokens[-JSON_SINK_TOKEN_LIMIT:]]

        data["summary"] = self.get_summary()

        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total_tokens = len(self._tokens)
        total_swaps = len(self._swaps)

        # Aggregate by model
        model_stats = {}
        for token in self._tokens:
            if token.model_name not in model_stats:
                model_stats[token.model_name] = {
                    "tokens_generated": 0,
                    "total_probability": 0.0,
                    "total_time": 0.0
                }
            stats = model_stats[token.model_name]
            stats["tokens_generated"] += 1
            stats["total_probability"] += token.probability
            stats["total_time"] += token.time_seconds

        # Calculate averages
        for model, stats in model_stats.items():
            n = stats["tokens_generated"]
            stats["avg_probability"] = stats["total_probability"] / n if n > 0 else 0
            stats["avg_time_per_token"] = stats["total_time"] / n if n > 0 else 0
            stats["contribution_pct"] = (n / total_tokens * 100) if total_tokens > 0 else 0

        return {
            "total_tokens": total_tokens,
            "total_swaps": total_swaps,
            "swaps_per_token": total_swaps / total_tokens if total_tokens > 0 else 0,
            "models": model_stats
        }


class ConsoleSink(EventSink):
    """Prints live stats to console during generation."""

    def __init__(self, show_every_n_tokens: int = CONSOLE_SINK_DEFAULT_INTERVAL, show_swaps: bool = True):
        self.show_every_n = show_every_n_tokens
        self.show_swaps = show_swaps
        self._token_count = 0
        self._swap_count = 0
        self._model_tokens: Dict[str, int] = {}
        self._model_names: List[str] = []

    def on_start(self, model_names: List[str]) -> None:
        self._model_names = model_names
        self._model_tokens = {name: 0 for name in model_names}
        print(f"\n[Mind Meld] Starting generation with models: {', '.join(model_names)}")

    def on_token(self, event: TokenEvent) -> None:
        self._token_count += 1
        self._model_tokens[event.model_name] = self._model_tokens.get(event.model_name, 0) + 1

        if self._token_count % self.show_every_n == 0:
            self._print_progress(event.model_name)

    def on_swap(self, event: SwapEvent) -> None:
        self._swap_count += 1
        if self.show_swaps:
            print(f"  [Swap #{self._swap_count}] {event.from_model} -> {event.to_model}: {event.reason}")

    def on_finish(self) -> None:
        print(f"\n[Mind Meld] Generation complete: {self._token_count} tokens, {self._swap_count} swaps")
        self._print_final_stats()

    def _print_progress(self, current_model: str) -> None:
        contrib_str = " | ".join(
            f"{name}: {count}" for name, count in self._model_tokens.items()
        )
        print(f"  [Token {self._token_count}] Active: {current_model} | {contrib_str}")

    def _print_final_stats(self) -> None:
        total = self._token_count
        if total == 0:
            return

        print("\nModel Contributions:")
        for name, count in self._model_tokens.items():
            pct = count / total * 100
            bar_len = int(pct * CONTRIBUTION_BAR_WIDTH / 100)
            bar = "#" * bar_len + "." * (CONTRIBUTION_BAR_WIDTH - bar_len)
            print(f"  {name:20} [{bar}] {pct:5.1f}% ({count} tokens)")

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_tokens": self._token_count,
            "total_swaps": self._swap_count,
            "model_tokens": self._model_tokens.copy()
        }


class StatsSink(EventSink):
    """
    Collects statistics for programmatic access.

    Use this when you need to access stats in code rather than
    writing to files or console.
    """

    def __init__(self):
        self._model_names: List[str] = []
        self._tokens: List[TokenEvent] = []
        self._swaps: List[SwapEvent] = []
        self._start_time: Optional[float] = None

    @property
    def tokens(self) -> List[TokenEvent]:
        """All recorded token events."""
        return self._tokens

    @property
    def swaps(self) -> List[SwapEvent]:
        """All recorded swap events."""
        return self._swaps

    @property
    def total_tokens(self) -> int:
        return len(self._tokens)

    @property
    def total_swaps(self) -> int:
        return len(self._swaps)

    def on_start(self, model_names: List[str]) -> None:
        self._model_names = model_names
        self._start_time = time.time()

    def on_token(self, event: TokenEvent) -> None:
        self._tokens.append(event)

    def on_swap(self, event: SwapEvent) -> None:
        self._swaps.append(event)

    def get_model_contribution(self, model_name: str) -> Dict[str, Any]:
        """Get statistics for a specific model."""
        model_tokens = [t for t in self._tokens if t.model_name == model_name]
        n = len(model_tokens)
        total = len(self._tokens)

        return {
            "tokens_generated": n,
            "contribution_pct": (n / total * 100) if total > 0 else 0,
            "avg_probability": sum(t.probability for t in model_tokens) / n if n > 0 else 0,
            "avg_time_per_token": sum(t.time_seconds for t in model_tokens) / n if n > 0 else 0
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "total_swaps": self.total_swaps,
            "models": {
                name: self.get_model_contribution(name)
                for name in self._model_names
            }
        }


class NullSink(EventSink):
    """A sink that discards all events. Useful for testing or disabled telemetry."""

    def on_token(self, event: TokenEvent) -> None:
        pass

    def on_swap(self, event: SwapEvent) -> None:
        pass
