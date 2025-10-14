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
    ModelContribution
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
