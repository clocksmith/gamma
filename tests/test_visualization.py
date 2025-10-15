"""
Test SwapVisualizer

Tests the visualization export/import features:
- SwapVisualizer.export_to_json()
- SwapVisualizer.load_from_json()
- SwapEvent and ModelContribution data structures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
import json

from src.mind_meld.visualization import (
    SwapVisualizer,
    SwapEvent,
    ModelContribution,
    Colors
)


class TestSwapVisualizerBasics(unittest.TestCase):
    """Test basic SwapVisualizer functionality."""

    def test_instantiation(self):
        """SwapVisualizer should be instantiatable with model names."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        self.assertIsNotNone(viz)
        self.assertEqual(viz.model_names, ['model_a', 'model_b'])

    def test_add_swap(self):
        """Should be able to add swap events."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        swap = SwapEvent(
            position=10,
            from_model='model_a',
            to_model='model_b',
            reason='confidence drop',
            timestamp=1234567890.0,
            confidence_before=0.6
        )

        viz.add_swap(swap)
        self.assertEqual(len(viz.swaps), 1)
        self.assertEqual(viz.swaps[0].from_model, 'model_a')
        self.assertEqual(viz.swaps[0].to_model, 'model_b')

    def test_record_token(self):
        """Should be able to record token generation."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        viz.record_token('model_a', probability=0.85, time_seconds=0.05)

        self.assertIn('model_a', viz.contributions)
        self.assertEqual(viz.contributions['model_a'].tokens_generated, 1)

    def test_multiple_tokens(self):
        """Should track multiple tokens per model."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        for i in range(5):
            viz.record_token('model_a', probability=0.8, time_seconds=0.05)

        for i in range(3):
            viz.record_token('model_b', probability=0.9, time_seconds=0.03)

        self.assertEqual(viz.contributions['model_a'].tokens_generated, 5)
        self.assertEqual(viz.contributions['model_b'].tokens_generated, 3)


class TestSwapVisualizerExport(unittest.TestCase):
    """Test export functionality."""

    def test_export_to_json(self):
        """Should export visualization data to JSON."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        # Add some data
        viz.record_token('model_a', probability=0.8, time_seconds=0.05)
        viz.add_swap(SwapEvent(
            position=1,
            from_model='model_a',
            to_model='model_b',
            reason='test swap',
            timestamp=1234567890.0
        ))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            viz.export_to_json(json_path)

            # Verify file exists and is valid JSON
            self.assertTrue(os.path.exists(json_path))

            with open(json_path, 'r') as f:
                data = json.load(f)

            self.assertIsInstance(data, dict)
            self.assertIn('model_names', data)
            self.assertIn('swaps', data)
            self.assertIn('contributions', data)
            self.assertEqual(data['model_names'], ['model_a', 'model_b'])
            self.assertEqual(len(data['swaps']), 1)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_export_preserves_swap_data(self):
        """Exported JSON should preserve swap event details."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        swap = SwapEvent(
            position=5,
            from_model='model_a',
            to_model='model_b',
            reason='high perplexity',
            timestamp=1234567890.5,
            confidence_before=0.65,
            coherence_score=0.92
        )
        viz.add_swap(swap)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            viz.export_to_json(json_path)

            with open(json_path, 'r') as f:
                data = json.load(f)

            swap_data = data['swaps'][0]
            self.assertEqual(swap_data['position'], 5)
            self.assertEqual(swap_data['from_model'], 'model_a')
            self.assertEqual(swap_data['to_model'], 'model_b')
            self.assertEqual(swap_data['reason'], 'high perplexity')
            self.assertEqual(swap_data['confidence_before'], 0.65)
            self.assertEqual(swap_data['coherence_score'], 0.92)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_export_preserves_contribution_data(self):
        """Exported JSON should preserve contribution stats."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        for i in range(10):
            viz.record_token('model_a', probability=0.85, time_seconds=0.05)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            viz.export_to_json(json_path)

            with open(json_path, 'r') as f:
                data = json.load(f)

            contrib = data['contributions']['model_a']
            self.assertEqual(contrib['tokens_generated'], 10)
            self.assertGreater(contrib['avg_confidence'], 0)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)


class TestSwapVisualizerImport(unittest.TestCase):
    """Test import functionality."""

    def test_load_from_json(self):
        """Should be able to load visualization from JSON."""
        # Create and export
        original = SwapVisualizer(['model_a', 'model_b'])
        original.record_token('model_a', probability=0.8, time_seconds=0.05)
        original.add_swap(SwapEvent(
            position=1,
            from_model='model_a',
            to_model='model_b',
            reason='test',
            timestamp=1234567890.0
        ))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            original.export_to_json(json_path)

            # Load it back
            loaded = SwapVisualizer.load_from_json(json_path)

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.model_names, ['model_a', 'model_b'])
            self.assertEqual(len(loaded.swaps), 1)
            self.assertIn('model_a', loaded.contributions)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_roundtrip_preserves_swaps(self):
        """JSON roundtrip should preserve all swap events."""
        original = SwapVisualizer(['model_a', 'model_b', 'model_c'])

        swaps = [
            SwapEvent(i, f'model_{chr(97 + i%3)}', f'model_{chr(97 + (i+1)%3)}',
                     f'reason_{i}', 1234567890.0 + i, 0.7 - i*0.05)
            for i in range(5)
        ]

        for swap in swaps:
            original.add_swap(swap)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            original.export_to_json(json_path)
            loaded = SwapVisualizer.load_from_json(json_path)

            self.assertEqual(len(loaded.swaps), 5)
            for i, swap in enumerate(loaded.swaps):
                self.assertEqual(swap.position, i)
                self.assertIn('reason', swap.reason)

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)

    def test_roundtrip_preserves_contributions(self):
        """JSON roundtrip should preserve contribution stats."""
        original = SwapVisualizer(['model_a', 'model_b'])

        for i in range(10):
            original.record_token('model_a', probability=0.8 + i*0.01, time_seconds=0.05)

        for i in range(5):
            original.record_token('model_b', probability=0.9, time_seconds=0.03)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            original.export_to_json(json_path)
            loaded = SwapVisualizer.load_from_json(json_path)

            self.assertEqual(
                loaded.contributions['model_a'].tokens_generated,
                10
            )
            self.assertEqual(
                loaded.contributions['model_b'].tokens_generated,
                5
            )

        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)


class TestVisualizationDataStructures(unittest.TestCase):
    """Test SwapEvent and ModelContribution data structures."""

    def test_swap_event_creation(self):
        """SwapEvent should be creatable with all fields."""
        event = SwapEvent(
            position=10,
            from_model='a',
            to_model='b',
            reason='test',
            timestamp=123.456,
            confidence_before=0.7,
            coherence_score=0.9
        )

        self.assertEqual(event.position, 10)
        self.assertEqual(event.from_model, 'a')
        self.assertEqual(event.to_model, 'b')
        self.assertEqual(event.reason, 'test')
        self.assertEqual(event.timestamp, 123.456)
        self.assertEqual(event.confidence_before, 0.7)
        self.assertEqual(event.coherence_score, 0.9)

    def test_swap_event_optional_fields(self):
        """SwapEvent should work with optional fields as None."""
        event = SwapEvent(
            position=5,
            from_model='a',
            to_model='b',
            reason='test',
            timestamp=123.0
        )

        self.assertIsNone(event.confidence_before)
        self.assertIsNone(event.coherence_score)

    def test_model_contribution_creation(self):
        """ModelContribution should track model stats."""
        contrib = ModelContribution(
            model_name='test_model',
            tokens_generated=100,
            total_probability=85.0,
            avg_confidence=0.85,
            time_active_seconds=5.0
        )

        self.assertEqual(contrib.model_name, 'test_model')
        self.assertEqual(contrib.tokens_generated, 100)
        self.assertEqual(contrib.avg_confidence, 0.85)
        self.assertEqual(contrib.time_active_seconds, 5.0)


class TestVisualizationRendering(unittest.TestCase):
    """Test visualization rendering methods."""

    def test_colors_get_model_color(self):
        """Colors.get_model_color should return color codes."""
        color0 = Colors.get_model_color(0)
        color1 = Colors.get_model_color(1)
        color4 = Colors.get_model_color(4)  # Should wrap around

        self.assertIsNotNone(color0)
        self.assertIsNotNone(color1)
        self.assertIsNotNone(color4)
        # Index 4 should wrap to index 0
        self.assertEqual(color0, color4)

    def test_highlight_text_by_model_no_color(self):
        """Should highlight text without color."""
        viz = SwapVisualizer(['model_a', 'model_b'], enable_color=False)
        text = "Hello world from models"
        positions = [
            (0, 6, 'model_a'),   # "Hello "
            (6, 12, 'model_b'),  # "world "
            (12, 23, 'model_a')  # "from models"
        ]

        result = viz.highlight_text_by_model(text, positions)

        self.assertIn('[model_a:', result)
        self.assertIn('[model_b:', result)
        self.assertIn('Hello', result)
        self.assertIn('world', result)

    def test_highlight_text_by_model_with_color(self):
        """Should highlight text with color."""
        viz = SwapVisualizer(['model_a', 'model_b'], enable_color=True)
        text = "Hello world"
        positions = [
            (0, 6, 'model_a'),
            (6, 11, 'model_b')
        ]

        result = viz.highlight_text_by_model(text, positions)

        self.assertIn('Hello', result)
        self.assertIn('world', result)
        # Should contain ANSI color codes
        self.assertIn('\033[', result)

    def test_render_contribution_timeline_no_tokens(self):
        """Should handle empty contributions gracefully."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        result = viz.render_contribution_timeline()

        self.assertIn('No tokens', result)

    def test_render_contribution_timeline_with_tokens(self):
        """Should render contribution timeline."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        # Record some tokens
        for i in range(10):
            viz.record_token('model_a', probability=0.8, time_seconds=0.05)
        for i in range(5):
            viz.record_token('model_b', probability=0.9, time_seconds=0.03)

        result = viz.render_contribution_timeline(width=40, show_percentages=True)

        self.assertIn('model_a', result)
        self.assertIn('model_b', result)
        self.assertIn('█', result)  # Should have progress bars
        self.assertIn('%', result)  # Should show percentages
        self.assertIn('tokens', result)

    def test_render_contribution_timeline_no_percentages(self):
        """Should render timeline without percentages."""
        viz = SwapVisualizer(['model_a'])
        viz.record_token('model_a', probability=0.8, time_seconds=0.05)

        result = viz.render_contribution_timeline(show_percentages=False)

        self.assertIn('model_a', result)
        self.assertIn('tokens', result)

    def test_get_summary_stats(self):
        """Should generate summary statistics."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        viz.add_swap(SwapEvent(
            position=1,
            from_model='model_a',
            to_model='model_b',
            reason='confidence drop',
            timestamp=1234567890.0,
            confidence_before=0.6
        ))

        viz.add_swap(SwapEvent(
            position=5,
            from_model='model_b',
            to_model='model_a',
            reason='perplexity threshold',
            timestamp=1234567895.0,
            confidence_before=0.7
        ))

        viz.record_token('model_a', probability=0.85, time_seconds=0.05)
        viz.record_token('model_b', probability=0.90, time_seconds=0.03)

        stats = viz.get_summary_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('total_tokens', stats)
        self.assertIn('total_swaps', stats)
        self.assertEqual(stats['total_swaps'], 2)

    def test_render_swap_log(self):
        """Should render swap log."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        viz.add_swap(SwapEvent(
            position=1,
            from_model='model_a',
            to_model='model_b',
            reason='test',
            timestamp=1234567890.0,
            confidence_before=0.7
        ))

        # Should not raise any exceptions
        log = viz.render_swap_log(max_events=10, show_reasons=True)
        self.assertIsNotNone(log)
        self.assertIsInstance(log, str)
        self.assertIn('model_a', log)
        self.assertIn('model_b', log)

    def test_show_coherence_analysis(self):
        """Should show coherence analysis."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        viz.add_swap(SwapEvent(
            position=5,
            from_model='model_a',
            to_model='model_b',
            reason='test',
            timestamp=1234567890.0,
            coherence_score=0.85
        ))

        # Should not raise any exceptions
        text = "Hello world from models"
        analysis = viz.show_coherence_analysis(text, show_problematic_only=False)
        self.assertIsNotNone(analysis)
        self.assertIsInstance(analysis, str)

    def test_render_live_update(self):
        """Should render live update without errors."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        viz.record_token('model_a', probability=0.85, time_seconds=0.05)

        # Should not raise any exceptions (returns None, prints to console)
        try:
            viz.render_live_update(current_text='Hello', current_model='model_a', last_probability=0.85)
        except Exception as e:
            self.fail(f"render_live_update raised exception: {e}")

    def test_render_swap_log_empty(self):
        """Should handle empty swap log."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        log = viz.render_swap_log()
        self.assertIn('No swaps', log)

    def test_show_coherence_analysis_empty(self):
        """Should handle empty coherence analysis."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        analysis = viz.show_coherence_analysis('test text')
        self.assertIn('No swaps', analysis)

    def test_show_coherence_analysis_jarring(self):
        """Should detect jarring transitions."""
        viz = SwapVisualizer(['model_a', 'model_b'])
        viz.add_swap(SwapEvent(
            position=5,
            from_model='model_a',
            to_model='model_b',
            reason='low confidence',
            timestamp=1234567890.0,
            coherence_score=0.5  # Below threshold
        ))

        text = "Hello world from models"
        analysis = viz.show_coherence_analysis(text, show_problematic_only=False, threshold=0.7)
        self.assertIn('Jarring', analysis)

    def test_show_coherence_analysis_problematic_only(self):
        """Should filter to show only problematic transitions."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        # Add smooth transition
        viz.add_swap(SwapEvent(
            position=2,
            from_model='model_a',
            to_model='model_b',
            reason='test',
            timestamp=1234567890.0,
            coherence_score=0.9  # Above threshold
        ))

        # Add jarring transition
        viz.add_swap(SwapEvent(
            position=5,
            from_model='model_b',
            to_model='model_a',
            reason='test',
            timestamp=1234567891.0,
            coherence_score=0.5  # Below threshold
        ))

        text = "Hello world"
        analysis = viz.show_coherence_analysis(text, show_problematic_only=True, threshold=0.7)
        self.assertIsNotNone(analysis)

    def test_show_coherence_analysis_all_smooth(self):
        """Should show message when all transitions are smooth."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        viz.add_swap(SwapEvent(
            position=2,
            from_model='model_a',
            to_model='model_b',
            reason='test',
            timestamp=1234567890.0,
            coherence_score=0.9
        ))

        text = "Hello world"
        analysis = viz.show_coherence_analysis(text, show_problematic_only=True, threshold=0.7)
        # When all are smooth and we're filtering, should get the "all smooth" message
        self.assertIsNotNone(analysis)

    def test_show_coherence_analysis_no_coherence_score(self):
        """Should handle swaps without coherence scores."""
        viz = SwapVisualizer(['model_a', 'model_b'])

        viz.add_swap(SwapEvent(
            position=2,
            from_model='model_a',
            to_model='model_b',
            reason='test',
            timestamp=1234567890.0,
            coherence_score=None  # No score
        ))

        text = "Hello world"
        analysis = viz.show_coherence_analysis(text, show_problematic_only=False)
        # Should get "all smooth" message since no swaps with scores passed the filter
        self.assertIn('smooth', analysis.lower())


def run_tests():
    """Run all visualization tests."""
    print("=" * 80)
    print("Testing SwapVisualizer Export/Import")
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
