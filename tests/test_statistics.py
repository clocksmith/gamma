"""
Test Mind Meld Statistics Tracking

Tests comprehensive statistics collection including:
- ModelStatistics: Individual model performance metrics
- SwapEvent: Model swap event recording
- MeldStatistics: Session-level statistics aggregation
- StatisticsTracker: Convenience tracking interface
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
import json
import time
from unittest.mock import patch, MagicMock
from io import StringIO

from src.mind_meld.core.statistics import (
    ModelStatistics,
    SwapEvent,
    MeldStatistics,
    StatisticsTracker
)


class TestModelStatistics(unittest.TestCase):
    """Test ModelStatistics dataclass."""

    def test_creation(self):
        """Should create ModelStatistics with default values."""
        stats = ModelStatistics(model_name="test_model")

        self.assertEqual(stats.model_name, "test_model")
        self.assertEqual(stats.tokens_generated, 0)
        self.assertEqual(stats.total_time, 0.0)
        self.assertEqual(stats.avg_confidence, 0.0)
        self.assertEqual(stats.avg_perplexity, 0.0)
        self.assertEqual(stats.swap_count, 0)

    def test_avg_time_per_token_with_tokens(self):
        """Should calculate average time per token."""
        stats = ModelStatistics(model_name="test_model")
        stats.tokens_generated = 10
        stats.total_time = 5.0

        self.assertEqual(stats.avg_time_per_token, 0.5)

    def test_avg_time_per_token_without_tokens(self):
        """Should return 0 when no tokens generated."""
        stats = ModelStatistics(model_name="test_model")

        self.assertEqual(stats.avg_time_per_token, 0.0)

    def test_contribution_percentage_default(self):
        """Should return 0.0 for contribution_percentage by default."""
        stats = ModelStatistics(model_name="test_model")

        self.assertEqual(stats.contribution_percentage, 0.0)

    def test_contribution_percentage_with_value(self):
        """Should return contribution percentage when set."""
        stats = ModelStatistics(model_name="test_model")
        stats._contribution_pct = 45.5

        self.assertEqual(stats.contribution_percentage, 45.5)

    def test_update_without_perplexity(self):
        """Should update statistics without perplexity."""
        stats = ModelStatistics(model_name="test_model")

        stats.update("hello", confidence=0.95, time_taken=0.1)

        self.assertEqual(stats.tokens_generated, 1)
        self.assertEqual(stats.total_time, 0.1)
        self.assertEqual(len(stats.token_texts), 1)
        self.assertEqual(stats.token_texts[0], "hello")
        self.assertEqual(len(stats.confidence_history), 1)
        self.assertAlmostEqual(stats.avg_confidence, 0.95)
        self.assertEqual(stats.avg_perplexity, 0.0)

    def test_update_with_perplexity(self):
        """Should update statistics with perplexity."""
        stats = ModelStatistics(model_name="test_model")

        stats.update("hello", confidence=0.9, time_taken=0.1, perplexity=5.0)
        stats.update("world", confidence=0.8, time_taken=0.15, perplexity=7.0)

        self.assertEqual(stats.tokens_generated, 2)
        self.assertAlmostEqual(stats.total_time, 0.25)
        self.assertEqual(len(stats.perplexity_history), 2)
        self.assertAlmostEqual(stats.avg_perplexity, 6.0)
        self.assertAlmostEqual(stats.avg_confidence, 0.85)

    def test_update_multiple_tokens(self):
        """Should correctly accumulate statistics over multiple updates."""
        stats = ModelStatistics(model_name="test_model")

        for i in range(5):
            stats.update(f"token{i}", confidence=0.9 - i*0.1, time_taken=0.1)

        self.assertEqual(stats.tokens_generated, 5)
        self.assertAlmostEqual(stats.total_time, 0.5)
        self.assertEqual(len(stats.token_texts), 5)
        self.assertEqual(len(stats.confidence_history), 5)


class TestSwapEvent(unittest.TestCase):
    """Test SwapEvent dataclass."""

    def test_creation(self):
        """Should create SwapEvent with all fields."""
        event = SwapEvent(
            round_num=42,
            from_model="model_a",
            to_model="model_b",
            reason="low confidence",
            token_before="hello",
            timestamp=1234567890.0
        )

        self.assertEqual(event.round_num, 42)
        self.assertEqual(event.from_model, "model_a")
        self.assertEqual(event.to_model, "model_b")
        self.assertEqual(event.reason, "low confidence")
        self.assertEqual(event.token_before, "hello")
        self.assertEqual(event.timestamp, 1234567890.0)


class TestMeldStatistics(unittest.TestCase):
    """Test MeldStatistics session tracking."""

    def setUp(self):
        """Create a MeldStatistics instance for testing."""
        self.stats = MeldStatistics()

    def test_creation(self):
        """Should create MeldStatistics with default values."""
        self.assertEqual(self.stats.total_tokens, 0)
        self.assertEqual(self.stats.total_swaps, 0)
        self.assertEqual(len(self.stats.model_stats), 0)
        self.assertEqual(len(self.stats.swap_events), 0)
        self.assertIsNone(self.stats.current_model)
        self.assertEqual(self.stats.max_streak, ("", 0))

    def test_duration_without_end_time(self):
        """Should calculate duration using current time when end_time is None."""
        start = time.time()
        stats = MeldStatistics(start_time=start)
        time.sleep(0.01)  # Sleep a tiny bit

        duration = stats.duration
        self.assertGreater(duration, 0)

    def test_duration_with_end_time(self):
        """Should calculate duration using end_time when set."""
        stats = MeldStatistics(start_time=100.0)
        stats.end_time = 150.0

        self.assertEqual(stats.duration, 50.0)

    def test_swaps_per_token_with_tokens(self):
        """Should calculate swaps per token."""
        self.stats.total_tokens = 100
        self.stats.total_swaps = 25

        self.assertEqual(self.stats.swaps_per_token, 0.25)

    def test_swaps_per_token_without_tokens(self):
        """Should return 0 when no tokens."""
        self.assertEqual(self.stats.swaps_per_token, 0.0)

    def test_add_model(self):
        """Should add a model to track."""
        self.stats.add_model("model_a")

        self.assertIn("model_a", self.stats.model_stats)
        self.assertEqual(self.stats.model_stats["model_a"].model_name, "model_a")

    def test_add_model_duplicate(self):
        """Should not duplicate model if already exists."""
        self.stats.add_model("model_a")
        self.stats.add_model("model_a")

        self.assertEqual(len(self.stats.model_stats), 1)

    def test_record_token_creates_model_if_missing(self):
        """Should auto-create model if not exists."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)

        self.assertIn("model_a", self.stats.model_stats)
        self.assertEqual(self.stats.total_tokens, 1)

    def test_record_token_updates_streak_same_model(self):
        """Should increment streak when same model continues."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_a", "world", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_a", "test", confidence=0.9, time_taken=0.1)

        self.assertEqual(self.stats.current_streak, 3)
        self.assertEqual(self.stats.current_model, "model_a")

    def test_record_token_resets_streak_different_model(self):
        """Should reset streak when model changes."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_a", "world", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_b", "test", confidence=0.9, time_taken=0.1)

        self.assertEqual(self.stats.current_streak, 1)
        self.assertEqual(self.stats.current_model, "model_b")
        self.assertEqual(self.stats.max_streak, ("model_a", 2))

    def test_record_token_tracks_max_streak(self):
        """Should track maximum streak across models."""
        # Model A: 3 tokens
        for i in range(3):
            self.stats.record_token("model_a", f"token{i}", confidence=0.9, time_taken=0.1)

        # Model B: 5 tokens
        for i in range(5):
            self.stats.record_token("model_b", f"token{i}", confidence=0.9, time_taken=0.1)

        # Model A: 2 tokens
        for i in range(2):
            self.stats.record_token("model_a", f"token{i}", confidence=0.9, time_taken=0.1)

        self.assertEqual(self.stats.max_streak, ("model_b", 5))

    def test_record_token_with_perplexity(self):
        """Should record token with perplexity."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1, perplexity=5.0)

        self.assertEqual(self.stats.model_stats["model_a"].avg_perplexity, 5.0)

    def test_record_swap(self):
        """Should record a swap event."""
        self.stats.add_model("model_a")
        self.stats.record_swap(10, "model_a", "model_b", "low confidence", "hello")

        self.assertEqual(self.stats.total_swaps, 1)
        self.assertEqual(len(self.stats.swap_events), 1)

        event = self.stats.swap_events[0]
        self.assertEqual(event.round_num, 10)
        self.assertEqual(event.from_model, "model_a")
        self.assertEqual(event.to_model, "model_b")
        self.assertEqual(event.reason, "low confidence")

    def test_record_swap_updates_pattern_counts(self):
        """Should track swap patterns."""
        self.stats.add_model("model_a")
        self.stats.add_model("model_b")

        self.stats.record_swap(1, "model_a", "model_b", "test", "token1")
        self.stats.record_swap(2, "model_a", "model_b", "test", "token2")
        self.stats.record_swap(3, "model_b", "model_a", "test", "token3")

        self.assertEqual(self.stats.swap_patterns["model_a -> model_b"], 2)
        self.assertEqual(self.stats.swap_patterns["model_b -> model_a"], 1)

    def test_record_swap_increments_model_swap_count(self):
        """Should increment swap count for source model."""
        self.stats.add_model("model_a")
        self.stats.record_swap(1, "model_a", "model_b", "test", "token")

        self.assertEqual(self.stats.model_stats["model_a"].swap_count, 1)

    def test_calculate_contributions_empty(self):
        """Should handle empty statistics."""
        self.stats.calculate_contributions()
        # Should not crash

    def test_calculate_contributions(self):
        """Should calculate contribution percentages."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_a", "world", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_b", "test", confidence=0.9, time_taken=0.1)

        self.stats.calculate_contributions()

        # 2 out of 3 tokens = 66.67%
        self.assertAlmostEqual(
            self.stats.model_stats["model_a"].contribution_percentage,
            66.666666,
            places=5
        )
        # 1 out of 3 tokens = 33.33%
        self.assertAlmostEqual(
            self.stats.model_stats["model_b"].contribution_percentage,
            33.333333,
            places=5
        )

    def test_get_summary(self):
        """Should generate complete summary."""
        self.stats.record_token("model_a", "hello", confidence=0.95, time_taken=0.1, perplexity=5.0)
        self.stats.record_token("model_a", "world", confidence=0.85, time_taken=0.15)
        self.stats.record_token("model_b", "test", confidence=0.9, time_taken=0.12)
        self.stats.record_swap(1, "model_a", "model_b", "low confidence", "world")

        summary = self.stats.get_summary()

        self.assertIn("duration_seconds", summary)
        self.assertEqual(summary["total_tokens"], 3)
        self.assertEqual(summary["total_swaps"], 1)
        self.assertIn("models", summary)
        self.assertIn("model_a", summary["models"])
        self.assertIn("model_b", summary["models"])
        self.assertIn("max_streak", summary)

    def test_get_summary_with_swap_patterns(self):
        """Should include top swap patterns in summary."""
        self.stats.add_model("model_a")
        self.stats.add_model("model_b")

        for i in range(3):
            self.stats.record_swap(i, "model_a", "model_b", "test", f"token{i}")

        summary = self.stats.get_summary()

        self.assertIn("top_swap_patterns", summary)
        self.assertEqual(summary["top_swap_patterns"]["model_a -> model_b"], 3)

    def test_print_summary(self):
        """Should print formatted summary without crashing."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1, perplexity=5.0)
        self.stats.record_token("model_b", "world", confidence=0.85, time_taken=0.12)
        self.stats.record_swap(1, "model_a", "model_b", "test", "hello")

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.stats.print_summary()
            output = fake_out.getvalue()

            self.assertIn("Mind Meld Session Statistics", output)
            self.assertIn("Overall Statistics", output)
            self.assertIn("Model Contributions", output)
            self.assertIn("model_a", output)
            self.assertIn("model_b", output)

    def test_print_live_stats(self):
        """Should print live statistics during generation."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_a", "world", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_b", "test", confidence=0.9, time_taken=0.1)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.stats.print_live_stats("model_b", round_num=10)
            output = fake_out.getvalue()

            self.assertIn("Round 10", output)
            self.assertIn("Active: model_b", output)
            self.assertIn("Model Contributions", output)
            self.assertIn("Swaps:", output)

    def test_save_to_file(self):
        """Should save statistics to JSON file."""
        self.stats.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)
        self.stats.record_token("model_b", "world", confidence=0.85, time_taken=0.12)
        self.stats.record_swap(1, "model_a", "model_b", "test", "hello")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            with patch('sys.stdout', new=StringIO()):
                self.stats.save_to_file(filepath)

            # Verify file was created and contains valid JSON
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.assertIn("summary", data)
            self.assertIn("detailed", data)
            self.assertEqual(data["summary"]["total_tokens"], 2)
            self.assertEqual(data["summary"]["total_swaps"], 1)
            self.assertIn("models", data["detailed"])
            self.assertIn("swap_events", data["detailed"])
        finally:
            os.unlink(filepath)

    def test_save_to_file_limits_history_length(self):
        """Should limit token history to first 100 tokens when saving."""
        # Add 150 tokens
        for i in range(150):
            self.stats.record_token("model_a", f"token{i}", confidence=0.9, time_taken=0.1)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            with patch('sys.stdout', new=StringIO()):
                self.stats.save_to_file(filepath)

            with open(filepath, 'r') as f:
                data = json.load(f)

            # Should only save first 100 tokens
            self.assertEqual(len(data["detailed"]["models"]["model_a"]["token_texts"]), 100)
            self.assertEqual(len(data["detailed"]["models"]["model_a"]["confidence_history"]), 100)
        finally:
            os.unlink(filepath)


class TestStatisticsTracker(unittest.TestCase):
    """Test StatisticsTracker convenience class."""

    def test_initialization(self):
        """Should initialize tracker with models."""
        tracker = StatisticsTracker(models=["model_a", "model_b"], show_live=False)

        self.assertIn("model_a", tracker.stats.model_stats)
        self.assertIn("model_b", tracker.stats.model_stats)
        self.assertFalse(tracker.show_live)
        self.assertIsNone(tracker.save_file)
        self.assertEqual(tracker.round_counter, 0)

    def test_initialization_with_options(self):
        """Should initialize tracker with live display and save file."""
        tracker = StatisticsTracker(
            models=["model_a"],
            show_live=True,
            save_file="test.json"
        )

        self.assertTrue(tracker.show_live)
        self.assertEqual(tracker.save_file, "test.json")

    def test_start_round(self):
        """Should increment round counter."""
        tracker = StatisticsTracker(models=["model_a"])

        round1 = tracker.start_round()
        round2 = tracker.start_round()
        round3 = tracker.start_round()

        self.assertEqual(round1, 1)
        self.assertEqual(round2, 2)
        self.assertEqual(round3, 3)
        self.assertEqual(tracker.round_counter, 3)

    def test_record_token(self):
        """Should record token to statistics."""
        tracker = StatisticsTracker(models=["model_a"])

        tracker.record_token("model_a", "hello", confidence=0.9, time_taken=0.1, perplexity=5.0)

        self.assertEqual(tracker.stats.total_tokens, 1)
        self.assertEqual(tracker.stats.model_stats["model_a"].tokens_generated, 1)

    def test_record_token_with_live_display(self):
        """Should show live stats every 5 rounds."""
        tracker = StatisticsTracker(models=["model_a"], show_live=True)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            # Rounds 1-4: no output
            for i in range(4):
                tracker.start_round()
                tracker.record_token("model_a", f"token{i}", confidence=0.9, time_taken=0.1)

            output1 = fake_out.getvalue()
            self.assertEqual(output1, "")  # No output yet

            # Round 5: should display
            tracker.start_round()
            tracker.record_token("model_a", "token5", confidence=0.9, time_taken=0.1)

            output2 = fake_out.getvalue()
            self.assertIn("Round 5", output2)

    def test_record_token_without_live_display(self):
        """Should not show live stats when disabled."""
        tracker = StatisticsTracker(models=["model_a"], show_live=False)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            for i in range(10):
                tracker.start_round()
                tracker.record_token("model_a", f"token{i}", confidence=0.9, time_taken=0.1)

            output = fake_out.getvalue()
            self.assertEqual(output, "")  # No output

    def test_record_swap(self):
        """Should record swap to statistics."""
        tracker = StatisticsTracker(models=["model_a", "model_b"])
        tracker.start_round()

        tracker.record_swap("model_a", "model_b", "low confidence", "hello")

        self.assertEqual(tracker.stats.total_swaps, 1)
        self.assertEqual(len(tracker.stats.swap_events), 1)
        self.assertEqual(tracker.stats.swap_events[0].round_num, 1)

    def test_finish_without_save(self):
        """Should print summary without saving."""
        tracker = StatisticsTracker(models=["model_a"])
        tracker.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.finish()
            output = fake_out.getvalue()

            self.assertIn("Mind Meld Session Statistics", output)
            self.assertIsNotNone(tracker.stats.end_time)

    def test_finish_with_save(self):
        """Should print summary and save to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            tracker = StatisticsTracker(models=["model_a"], save_file=filepath)
            tracker.record_token("model_a", "hello", confidence=0.9, time_taken=0.1)

            with patch('sys.stdout', new=StringIO()):
                tracker.finish()

            # Verify file was created
            self.assertTrue(os.path.exists(filepath))

            with open(filepath, 'r') as f:
                data = json.load(f)

            self.assertIn("summary", data)
            self.assertEqual(data["summary"]["total_tokens"], 1)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


def run_tests():
    """Run all statistics tests."""
    print("=" * 80)
    print("Testing Mind Meld Statistics")
    print("=" * 80)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
