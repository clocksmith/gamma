"""
Tests for Mind Meld event sink system.

Tests the pluggable event sink interface including EventSinkManager,
JSONFileSink, ConsoleSink, StatsSink, and NullSink.
"""

import sys
import os
import json
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mind_meld.core.event_sinks import (
    TokenEvent,
    SwapEvent,
    EventSink,
    EventSinkManager,
    JSONFileSink,
    ConsoleSink,
    StatsSink,
    NullSink,
)


class TestTokenEvent(unittest.TestCase):
    """Tests for TokenEvent dataclass."""

    def test_token_event_creation(self):
        """Test basic TokenEvent creation."""
        event = TokenEvent(
            model_name="model-a",
            token_text="hello",
            probability=0.95,
            time_seconds=0.01,
            position=1
        )
        self.assertEqual(event.model_name, "model-a")
        self.assertEqual(event.token_text, "hello")
        self.assertEqual(event.probability, 0.95)
        self.assertEqual(event.time_seconds, 0.01)
        self.assertEqual(event.position, 1)
        self.assertIsNone(event.perplexity)

    def test_token_event_with_perplexity(self):
        """Test TokenEvent with optional perplexity."""
        event = TokenEvent(
            model_name="model-a",
            token_text="world",
            probability=0.8,
            time_seconds=0.02,
            position=2,
            perplexity=1.5
        )
        self.assertEqual(event.perplexity, 1.5)

    def test_token_event_has_timestamp(self):
        """Test that TokenEvent has auto-generated timestamp."""
        event = TokenEvent(
            model_name="model-a",
            token_text="test",
            probability=0.9,
            time_seconds=0.01,
            position=1
        )
        self.assertIsNotNone(event.timestamp)
        self.assertGreater(event.timestamp, 0)


class TestSwapEvent(unittest.TestCase):
    """Tests for SwapEvent dataclass."""

    def test_swap_event_creation(self):
        """Test basic SwapEvent creation."""
        event = SwapEvent(
            position=5,
            from_model="model-a",
            to_model="model-b",
            reason="punctuation"
        )
        self.assertEqual(event.position, 5)
        self.assertEqual(event.from_model, "model-a")
        self.assertEqual(event.to_model, "model-b")
        self.assertEqual(event.reason, "punctuation")
        self.assertIsNone(event.confidence_before)
        self.assertIsNone(event.coherence_score)

    def test_swap_event_with_optional_fields(self):
        """Test SwapEvent with optional confidence and coherence."""
        event = SwapEvent(
            position=10,
            from_model="model-a",
            to_model="model-b",
            reason="confidence_drop",
            confidence_before=0.6,
            coherence_score=0.85
        )
        self.assertEqual(event.confidence_before, 0.6)
        self.assertEqual(event.coherence_score, 0.85)

    def test_swap_event_has_timestamp(self):
        """Test that SwapEvent has auto-generated timestamp."""
        event = SwapEvent(
            position=1,
            from_model="a",
            to_model="b",
            reason="test"
        )
        self.assertIsNotNone(event.timestamp)


class TestEventSinkManager(unittest.TestCase):
    """Tests for EventSinkManager."""

    def test_manager_creation(self):
        """Test manager starts with no sinks."""
        manager = EventSinkManager()
        self.assertEqual(len(manager._sinks), 0)

    def test_add_sink_chaining(self):
        """Test that add_sink returns self for chaining."""
        manager = EventSinkManager()
        result = manager.add_sink(NullSink())
        self.assertIs(result, manager)

    def test_add_multiple_sinks(self):
        """Test adding multiple sinks."""
        manager = EventSinkManager()
        manager.add_sink(NullSink()).add_sink(NullSink())
        self.assertEqual(len(manager._sinks), 2)

    def test_remove_sink(self):
        """Test removing a sink."""
        manager = EventSinkManager()
        sink = NullSink()
        manager.add_sink(sink)
        self.assertTrue(manager.remove_sink(sink))
        self.assertEqual(len(manager._sinks), 0)

    def test_remove_nonexistent_sink(self):
        """Test removing a sink that doesn't exist."""
        manager = EventSinkManager()
        sink = NullSink()
        self.assertFalse(manager.remove_sink(sink))

    def test_start_resets_position(self):
        """Test that start resets position counter."""
        manager = EventSinkManager()
        manager._position = 100
        manager.start(["model-a"])
        self.assertEqual(manager._position, 0)

    def test_on_token_increments_position(self):
        """Test that on_token_generated increments position."""
        manager = EventSinkManager()
        stats = StatsSink()
        manager.add_sink(stats)
        manager.start(["model-a"])

        manager.on_token_generated("model-a", "hello", 0.9, 0.01)
        self.assertEqual(manager._position, 1)

        manager.on_token_generated("model-a", "world", 0.8, 0.02)
        self.assertEqual(manager._position, 2)

    def test_events_dispatched_to_all_sinks(self):
        """Test that events are dispatched to all registered sinks."""
        manager = EventSinkManager()
        sink1 = StatsSink()
        sink2 = StatsSink()
        manager.add_sink(sink1).add_sink(sink2)
        manager.start(["model-a"])

        manager.on_token_generated("model-a", "test", 0.9, 0.01)

        self.assertEqual(sink1.total_tokens, 1)
        self.assertEqual(sink2.total_tokens, 1)

    def test_swap_event_dispatched(self):
        """Test that swap events are dispatched."""
        manager = EventSinkManager()
        stats = StatsSink()
        manager.add_sink(stats)
        manager.start(["model-a", "model-b"])

        manager.on_swap("model-a", "model-b", "punctuation")

        self.assertEqual(stats.total_swaps, 1)
        self.assertEqual(stats.swaps[0].from_model, "model-a")
        self.assertEqual(stats.swaps[0].to_model, "model-b")

    def test_get_all_summaries(self):
        """Test getting summaries from all sinks."""
        manager = EventSinkManager()
        manager.add_sink(StatsSink()).add_sink(NullSink())
        manager.start(["model-a"])
        manager.on_token_generated("model-a", "test", 0.9, 0.01)

        summaries = manager.get_all_summaries()

        self.assertIn("StatsSink", summaries)
        self.assertIn("NullSink", summaries)
        self.assertEqual(summaries["StatsSink"]["total_tokens"], 1)


class TestJSONFileSink(unittest.TestCase):
    """Tests for JSONFileSink."""

    def test_json_sink_creates_file(self):
        """Test that JSONFileSink creates output file on finish."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            sink = JSONFileSink(filepath)
            sink.on_start(["model-a", "model-b"])
            sink.on_token(TokenEvent(
                model_name="model-a",
                token_text="hello",
                probability=0.9,
                time_seconds=0.01,
                position=1
            ))
            sink.on_finish()

            with open(filepath, 'r') as f:
                data = json.load(f)

            self.assertEqual(data["model_names"], ["model-a", "model-b"])
            self.assertEqual(data["total_tokens"], 1)
            self.assertEqual(data["total_swaps"], 0)
        finally:
            os.unlink(filepath)

    def test_json_sink_records_swaps(self):
        """Test that swaps are recorded in JSON output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            sink = JSONFileSink(filepath)
            sink.on_start(["model-a", "model-b"])
            sink.on_swap(SwapEvent(
                position=5,
                from_model="model-a",
                to_model="model-b",
                reason="confidence_drop"
            ))
            sink.on_finish()

            with open(filepath, 'r') as f:
                data = json.load(f)

            self.assertEqual(len(data["swaps"]), 1)
            self.assertEqual(data["swaps"][0]["from_model"], "model-a")
        finally:
            os.unlink(filepath)

    def test_json_sink_token_limit(self):
        """Test that tokens are limited to last 1000."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            sink = JSONFileSink(filepath)
            sink.on_start(["model-a"])

            # Add 1500 tokens
            for i in range(1500):
                sink.on_token(TokenEvent(
                    model_name="model-a",
                    token_text=f"tok{i}",
                    probability=0.9,
                    time_seconds=0.01,
                    position=i + 1
                ))

            sink.on_finish()

            with open(filepath, 'r') as f:
                data = json.load(f)

            # Total should be 1500, but tokens array limited to 1000
            self.assertEqual(data["total_tokens"], 1500)
            self.assertEqual(len(data["tokens"]), 1000)
            # Should be the LAST 1000 tokens
            self.assertEqual(data["tokens"][0]["token_text"], "tok500")
        finally:
            os.unlink(filepath)

    def test_json_sink_exclude_tokens(self):
        """Test that tokens can be excluded from output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            sink = JSONFileSink(filepath, include_tokens=False)
            sink.on_start(["model-a"])
            sink.on_token(TokenEvent(
                model_name="model-a",
                token_text="test",
                probability=0.9,
                time_seconds=0.01,
                position=1
            ))
            sink.on_finish()

            with open(filepath, 'r') as f:
                data = json.load(f)

            self.assertNotIn("tokens", data)
            self.assertEqual(data["total_tokens"], 0)  # Not tracked when include_tokens=False
        finally:
            os.unlink(filepath)

    def test_json_sink_summary_statistics(self):
        """Test summary statistics calculation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            sink = JSONFileSink(filepath)
            sink.on_start(["model-a", "model-b"])

            # Add tokens from both models
            for i in range(10):
                sink.on_token(TokenEvent(
                    model_name="model-a",
                    token_text=f"a{i}",
                    probability=0.9,
                    time_seconds=0.01,
                    position=i + 1
                ))
            for i in range(5):
                sink.on_token(TokenEvent(
                    model_name="model-b",
                    token_text=f"b{i}",
                    probability=0.8,
                    time_seconds=0.02,
                    position=10 + i + 1
                ))

            sink.on_finish()

            with open(filepath, 'r') as f:
                data = json.load(f)

            summary = data["summary"]
            self.assertEqual(summary["total_tokens"], 15)
            self.assertIn("model-a", summary["models"])
            self.assertIn("model-b", summary["models"])

            # Model-a should have ~67% contribution
            self.assertAlmostEqual(
                summary["models"]["model-a"]["contribution_pct"],
                66.67, places=1
            )
        finally:
            os.unlink(filepath)


class TestConsoleSink(unittest.TestCase):
    """Tests for ConsoleSink."""

    def test_console_sink_start_prints(self):
        """Test that on_start prints model names."""
        sink = ConsoleSink()
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sink.on_start(["model-a", "model-b"])
            output = mock_stdout.getvalue()
        self.assertIn("model-a", output)
        self.assertIn("model-b", output)

    def test_console_sink_finish_prints(self):
        """Test that on_finish prints summary."""
        sink = ConsoleSink()
        sink.on_start(["model-a"])
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sink.on_finish()
            output = mock_stdout.getvalue()
        self.assertIn("Generation complete", output)

    def test_console_sink_progress_interval(self):
        """Test that progress is shown every N tokens."""
        sink = ConsoleSink(show_every_n_tokens=5)
        sink.on_start(["model-a"])

        outputs = []
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            for i in range(10):
                sink.on_token(TokenEvent(
                    model_name="model-a",
                    token_text=f"tok{i}",
                    probability=0.9,
                    time_seconds=0.01,
                    position=i + 1
                ))
            outputs.append(mock_stdout.getvalue())

        # Should print at token 5 and 10
        output = outputs[0]
        self.assertIn("Token 5", output)
        self.assertIn("Token 10", output)
        self.assertNotIn("Token 3", output)

    def test_console_sink_swap_display(self):
        """Test that swaps are displayed when enabled."""
        sink = ConsoleSink(show_swaps=True)
        sink.on_start(["model-a", "model-b"])

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sink.on_swap(SwapEvent(
                position=5,
                from_model="model-a",
                to_model="model-b",
                reason="confidence_drop"
            ))
            output = mock_stdout.getvalue()

        self.assertIn("Swap #1", output)
        self.assertIn("model-a", output)
        self.assertIn("model-b", output)

    def test_console_sink_swap_hidden(self):
        """Test that swaps can be hidden."""
        sink = ConsoleSink(show_swaps=False)
        sink.on_start(["model-a", "model-b"])

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sink.on_swap(SwapEvent(
                position=5,
                from_model="model-a",
                to_model="model-b",
                reason="confidence_drop"
            ))
            output = mock_stdout.getvalue()

        self.assertNotIn("Swap", output)

    def test_console_sink_summary(self):
        """Test get_summary returns correct data."""
        sink = ConsoleSink()
        sink.on_start(["model-a", "model-b"])

        for i in range(5):
            sink.on_token(TokenEvent(
                model_name="model-a",
                token_text=f"tok{i}",
                probability=0.9,
                time_seconds=0.01,
                position=i + 1
            ))

        sink.on_swap(SwapEvent(
            position=5,
            from_model="model-a",
            to_model="model-b",
            reason="test"
        ))

        summary = sink.get_summary()
        self.assertEqual(summary["total_tokens"], 5)
        self.assertEqual(summary["total_swaps"], 1)
        self.assertEqual(summary["model_tokens"]["model-a"], 5)


class TestStatsSink(unittest.TestCase):
    """Tests for StatsSink."""

    def test_stats_sink_counts_tokens(self):
        """Test that StatsSink counts tokens correctly."""
        sink = StatsSink()
        sink.on_start(["model-a"])

        for i in range(5):
            sink.on_token(TokenEvent(
                model_name="model-a",
                token_text=f"tok{i}",
                probability=0.9,
                time_seconds=0.01,
                position=i + 1
            ))

        self.assertEqual(sink.total_tokens, 5)

    def test_stats_sink_counts_swaps(self):
        """Test that StatsSink counts swaps correctly."""
        sink = StatsSink()
        sink.on_start(["model-a", "model-b"])

        sink.on_swap(SwapEvent(position=1, from_model="a", to_model="b", reason="test"))
        sink.on_swap(SwapEvent(position=2, from_model="b", to_model="a", reason="test"))

        self.assertEqual(sink.total_swaps, 2)

    def test_stats_sink_provides_token_list(self):
        """Test that tokens property returns all tokens."""
        sink = StatsSink()
        sink.on_start(["model-a"])

        sink.on_token(TokenEvent(
            model_name="model-a",
            token_text="hello",
            probability=0.9,
            time_seconds=0.01,
            position=1
        ))

        self.assertEqual(len(sink.tokens), 1)
        self.assertEqual(sink.tokens[0].token_text, "hello")

    def test_stats_sink_provides_swap_list(self):
        """Test that swaps property returns all swaps."""
        sink = StatsSink()
        sink.on_start(["model-a", "model-b"])

        sink.on_swap(SwapEvent(
            position=1,
            from_model="model-a",
            to_model="model-b",
            reason="punctuation"
        ))

        self.assertEqual(len(sink.swaps), 1)
        self.assertEqual(sink.swaps[0].reason, "punctuation")

    def test_stats_sink_model_contribution(self):
        """Test get_model_contribution calculation."""
        sink = StatsSink()
        sink.on_start(["model-a", "model-b"])

        # 3 tokens from model-a, 1 from model-b
        for i in range(3):
            sink.on_token(TokenEvent(
                model_name="model-a",
                token_text=f"a{i}",
                probability=0.9,
                time_seconds=0.01,
                position=i + 1
            ))
        sink.on_token(TokenEvent(
            model_name="model-b",
            token_text="b0",
            probability=0.8,
            time_seconds=0.02,
            position=4
        ))

        contrib_a = sink.get_model_contribution("model-a")
        self.assertEqual(contrib_a["tokens_generated"], 3)
        self.assertEqual(contrib_a["contribution_pct"], 75.0)

        contrib_b = sink.get_model_contribution("model-b")
        self.assertEqual(contrib_b["tokens_generated"], 1)
        self.assertEqual(contrib_b["contribution_pct"], 25.0)

    def test_stats_sink_avg_probability(self):
        """Test average probability calculation."""
        sink = StatsSink()
        sink.on_start(["model-a"])

        sink.on_token(TokenEvent(
            model_name="model-a",
            token_text="t1",
            probability=0.8,
            time_seconds=0.01,
            position=1
        ))
        sink.on_token(TokenEvent(
            model_name="model-a",
            token_text="t2",
            probability=1.0,
            time_seconds=0.01,
            position=2
        ))

        contrib = sink.get_model_contribution("model-a")
        self.assertEqual(contrib["avg_probability"], 0.9)

    def test_stats_sink_summary(self):
        """Test get_summary returns complete data."""
        sink = StatsSink()
        sink.on_start(["model-a", "model-b"])

        sink.on_token(TokenEvent(
            model_name="model-a",
            token_text="t1",
            probability=0.9,
            time_seconds=0.01,
            position=1
        ))
        sink.on_swap(SwapEvent(
            position=1,
            from_model="model-a",
            to_model="model-b",
            reason="test"
        ))

        summary = sink.get_summary()
        self.assertEqual(summary["total_tokens"], 1)
        self.assertEqual(summary["total_swaps"], 1)
        self.assertIn("model-a", summary["models"])
        self.assertIn("model-b", summary["models"])


class TestNullSink(unittest.TestCase):
    """Tests for NullSink."""

    def test_null_sink_accepts_tokens(self):
        """Test that NullSink accepts tokens without error."""
        sink = NullSink()
        # Should not raise
        sink.on_token(TokenEvent(
            model_name="model-a",
            token_text="test",
            probability=0.9,
            time_seconds=0.01,
            position=1
        ))

    def test_null_sink_accepts_swaps(self):
        """Test that NullSink accepts swaps without error."""
        sink = NullSink()
        # Should not raise
        sink.on_swap(SwapEvent(
            position=1,
            from_model="a",
            to_model="b",
            reason="test"
        ))

    def test_null_sink_empty_summary(self):
        """Test that NullSink returns empty summary."""
        sink = NullSink()
        self.assertEqual(sink.get_summary(), {})


class TestEventSinkIntegration(unittest.TestCase):
    """Integration tests for event sink system."""

    def test_full_generation_flow(self):
        """Test complete generation flow with multiple sinks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            manager = EventSinkManager()
            stats_sink = StatsSink()
            manager.add_sink(JSONFileSink(filepath))
            manager.add_sink(stats_sink)

            # Simulate generation
            manager.start(["model-a", "model-b"])

            for i in range(10):
                model = "model-a" if i % 3 != 0 else "model-b"
                manager.on_token_generated(
                    model_name=model,
                    token_text=f"token{i}",
                    probability=0.9 - (i * 0.01),
                    time_seconds=0.01 + (i * 0.001)
                )

                if i == 5:
                    manager.on_swap(
                        from_model="model-a",
                        to_model="model-b",
                        reason="punctuation",
                        confidence_before=0.75
                    )

            manager.finish()

            # Verify stats sink
            self.assertEqual(stats_sink.total_tokens, 10)
            self.assertEqual(stats_sink.total_swaps, 1)

            # Verify JSON file
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.assertEqual(data["total_tokens"], 10)
            self.assertEqual(data["total_swaps"], 1)

        finally:
            os.unlink(filepath)


if __name__ == "__main__":
    unittest.main()
