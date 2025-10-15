"""
Test ModelState and StateSnapshot

Tests the model state management features:
- StateSnapshot creation and cloning
- ModelState initialization and metadata extraction
- Snapshot save/restore functionality
- State reset and summary generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock
import time

from src.mind_meld.core.model_state import ModelState, StateSnapshot


class TestStateSnapshot(unittest.TestCase):
    """Test StateSnapshot data structure."""

    def test_snapshot_creation(self):
        """Should create snapshot with all fields."""
        snapshot = StateSnapshot(
            timestamp=1234567890.0,
            token_position=10,
            kv_cache={'key': 'cache'},
            hidden_states=[1, 2, 3],
            attention_weights=[0.5, 0.5],
            logits=[0.1, 0.9],
            confidence=0.85,
            metadata={'test': 'value'}
        )

        self.assertEqual(snapshot.timestamp, 1234567890.0)
        self.assertEqual(snapshot.token_position, 10)
        self.assertEqual(snapshot.kv_cache, {'key': 'cache'})
        self.assertEqual(snapshot.hidden_states, [1, 2, 3])
        self.assertEqual(snapshot.confidence, 0.85)
        self.assertEqual(snapshot.metadata, {'test': 'value'})

    def test_snapshot_clone(self):
        """Should create deep copy of snapshot."""
        original = StateSnapshot(
            timestamp=1234567890.0,
            token_position=5,
            kv_cache={'key': [1, 2, 3]},
            hidden_states=[4, 5, 6],
            metadata={'data': [7, 8, 9]}
        )

        cloned = original.clone()

        # Should have same values
        self.assertEqual(cloned.timestamp, original.timestamp)
        self.assertEqual(cloned.token_position, original.token_position)
        self.assertEqual(cloned.kv_cache, original.kv_cache)
        self.assertEqual(cloned.hidden_states, original.hidden_states)
        self.assertEqual(cloned.metadata, original.metadata)

        # But be different objects (deep copy)
        self.assertIsNot(cloned.kv_cache, original.kv_cache)
        self.assertIsNot(cloned.hidden_states, original.hidden_states)
        self.assertIsNot(cloned.metadata, original.metadata)

        # Modifying clone shouldn't affect original
        cloned.kv_cache['key'].append(4)
        self.assertEqual(len(original.kv_cache['key']), 3)
        self.assertEqual(len(cloned.kv_cache['key']), 4)

    def test_snapshot_clone_with_none_values(self):
        """Should handle None values in clone."""
        original = StateSnapshot(
            timestamp=1234567890.0,
            token_position=5,
            kv_cache=None,
            hidden_states=None,
            attention_weights=None,
            logits=None
        )

        cloned = original.clone()

        self.assertIsNone(cloned.kv_cache)
        self.assertIsNone(cloned.hidden_states)
        self.assertIsNone(cloned.attention_weights)
        self.assertIsNone(cloned.logits)


class TestModelStateBasics(unittest.TestCase):
    """Test basic ModelState functionality."""

    def test_model_state_creation_without_engine(self):
        """Should create ModelState without engine."""
        state = ModelState(
            engine=None,
            name='test_model',
            model_id='test/model-1b'
        )

        self.assertEqual(state.name, 'test_model')
        self.assertEqual(state.model_id, 'test/model-1b')
        self.assertEqual(state.token_count, 0)
        self.assertIsNone(state.input_ids)
        self.assertIsNone(state.kv_cache)
        self.assertEqual(len(state.snapshots), 0)

    def test_model_state_creation_with_mock_engine(self):
        """Should create ModelState with mock engine."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        self.assertEqual(state.vocab_size, 50000)
        mock_engine.get_vocabulary_size.assert_called_once()

    def test_metadata_extraction_with_config(self):
        """Should extract metadata from engine model config."""
        mock_config = Mock()
        mock_config.hidden_size = 768
        mock_config.num_layers = 12
        mock_config.num_attention_heads = 12
        mock_config.max_position_embeddings = 2048

        mock_model = Mock()
        mock_model.config = mock_config

        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000
        mock_engine.model = mock_model

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        self.assertEqual(state.hidden_size, 768)
        self.assertEqual(state.num_layers, 12)
        self.assertEqual(state.num_heads, 12)
        self.assertEqual(state.head_dim, 64)  # 768 / 12
        self.assertEqual(state.context_length, 2048)

    def test_metadata_extraction_with_alternative_names(self):
        """Should handle alternative config attribute names."""
        # Create a simple object with only alternative names
        class ConfigWithAltNames:
            hidden_size = 1024
            n_layers = 24  # Alternative name
            n_heads = 16   # Alternative name
            n_positions = 4096  # Alternative name

        class ModelWithConfig:
            config = ConfigWithAltNames()

        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000
        mock_engine.model = ModelWithConfig()

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # The code uses getattr with fallback, so it should get the alt names
        self.assertEqual(state.num_layers, 24)
        self.assertEqual(state.num_heads, 16)
        self.assertEqual(state.context_length, 4096)

    def test_metadata_extraction_graceful_failure(self):
        """Should handle metadata extraction failures gracefully."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000
        mock_engine.model = None  # No model

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # Should not crash, metadata should be None
        self.assertIsNone(state.hidden_size)
        self.assertIsNone(state.num_layers)


class TestModelStateSnapshots(unittest.TestCase):
    """Test snapshot save/restore functionality."""

    def test_save_snapshot_basic(self):
        """Should save basic snapshot."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        state.token_count = 5
        state.confidence_history = [0.8, 0.9, 0.85]
        state.perplexity_history = [2.5, 2.3, 2.4]

        state.save_snapshot()

        self.assertEqual(len(state.snapshots), 1)
        snapshot = state.snapshots[0]
        self.assertEqual(snapshot.token_position, 5)
        self.assertEqual(snapshot.confidence, 0.85)

    def test_save_snapshot_with_cache(self):
        """Should save snapshot with KV cache."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        state.kv_cache = {'keys': [1, 2, 3], 'values': [4, 5, 6]}
        state.last_hidden_states = [7, 8, 9]
        state.last_attention = [0.3, 0.7]
        state.last_logits = [0.1, 0.9]

        state.save_snapshot(include_cache=True, include_hidden=True)

        snapshot = state.snapshots[0]
        self.assertIsNotNone(snapshot.kv_cache)
        self.assertIsNotNone(snapshot.hidden_states)
        self.assertEqual(snapshot.kv_cache, state.kv_cache)

    def test_save_snapshot_without_cache(self):
        """Should save snapshot without cache when disabled."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        state.kv_cache = {'keys': [1, 2, 3]}
        state.save_snapshot(include_cache=False, include_hidden=False)

        snapshot = state.snapshots[0]
        self.assertIsNone(snapshot.kv_cache)
        self.assertIsNone(snapshot.hidden_states)

    def test_snapshot_max_limit(self):
        """Should limit number of snapshots kept."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )
        state.max_snapshots = 3

        # Save 5 snapshots
        for i in range(5):
            state.token_count = i
            state.save_snapshot()

        # Should only keep last 3
        self.assertEqual(len(state.snapshots), 3)
        self.assertEqual(state.snapshots[0].token_position, 2)
        self.assertEqual(state.snapshots[-1].token_position, 4)

    def test_restore_snapshot_success(self):
        """Should restore state from snapshot."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # Save a snapshot
        state.kv_cache = {'key': 'original'}
        state.last_hidden_states = [1, 2, 3]
        state.save_snapshot()

        # Modify state
        state.kv_cache = {'key': 'modified'}
        state.last_hidden_states = [4, 5, 6]

        # Restore
        success = state.restore_snapshot()

        self.assertTrue(success)
        self.assertEqual(state.kv_cache['key'], 'original')
        self.assertEqual(state.last_hidden_states, [1, 2, 3])

    def test_restore_snapshot_no_snapshots(self):
        """Should return False when no snapshots exist."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        success = state.restore_snapshot()
        self.assertFalse(success)

    def test_restore_snapshot_by_index(self):
        """Should restore specific snapshot by index."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # Save multiple snapshots
        state.kv_cache = {'step': 1}
        state.save_snapshot()
        state.kv_cache = {'step': 2}
        state.save_snapshot()
        state.kv_cache = {'step': 3}
        state.save_snapshot()

        # Restore first snapshot
        state.restore_snapshot(snapshot_idx=0)
        self.assertEqual(state.kv_cache['step'], 1)

        # Restore last snapshot
        state.restore_snapshot(snapshot_idx=-1)
        self.assertEqual(state.kv_cache['step'], 3)

    def test_restore_snapshot_with_attention_and_logits(self):
        """Should restore attention weights and logits."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # Save snapshot with all components
        state.kv_cache = {'key': 'value'}
        state.last_hidden_states = [1, 2, 3]
        state.last_attention = [0.3, 0.7]
        state.last_logits = [0.1, 0.9]
        state.save_snapshot()

        # Modify everything
        state.kv_cache = {'key': 'modified'}
        state.last_hidden_states = [4, 5, 6]
        state.last_attention = [0.5, 0.5]
        state.last_logits = [0.2, 0.8]

        # Restore
        success = state.restore_snapshot()

        self.assertTrue(success)
        self.assertEqual(state.last_attention, [0.3, 0.7])
        self.assertEqual(state.last_logits, [0.1, 0.9])

    def test_restore_snapshot_exception_handling(self):
        """Should handle exceptions during restore."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # Save a snapshot
        state.kv_cache = {'key': 'value'}
        state.save_snapshot()

        # Make engine._kv_cache assignment raise an exception
        type(mock_engine)._kv_cache = property(
            lambda self: None,
            lambda self, value: (_ for _ in ()).throw(RuntimeError("Cache assignment failed"))
        )

        # Restore should return False on exception
        success = state.restore_snapshot()
        self.assertFalse(success)


class TestModelStateReset(unittest.TestCase):
    """Test state reset functionality."""

    def test_reset_clears_all_state(self):
        """Should reset all state variables."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000
        mock_engine.reset_kv_cache = Mock()

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        # Set up some state
        state.input_ids = [1, 2, 3]
        state.attention_mask = [1, 1, 1]
        state.kv_cache = {'keys': [1, 2]}
        state.token_count = 5
        state.confidence_history = [0.8, 0.9]
        state.perplexity_history = [2.5, 2.3]
        state.save_snapshot()

        # Reset
        state.reset()

        # Everything should be cleared
        self.assertIsNone(state.input_ids)
        self.assertIsNone(state.attention_mask)
        self.assertIsNone(state.kv_cache)
        self.assertEqual(state.token_count, 0)
        self.assertEqual(len(state.confidence_history), 0)
        self.assertEqual(len(state.perplexity_history), 0)
        self.assertEqual(len(state.snapshots), 0)

        # Engine reset should be called
        mock_engine.reset_kv_cache.assert_called_once()


class TestModelStateSummary(unittest.TestCase):
    """Test state summary generation."""

    def test_get_state_summary(self):
        """Should generate comprehensive state summary."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        state.token_count = 10
        state.input_ids = [1, 2, 3, 4, 5]
        state.kv_cache = {'key': 'value'}
        state.last_hidden_states = [1, 2, 3]
        state.confidence_history = [0.8, 0.9, 0.85]
        state.perplexity_history = [2.5, 2.3, 2.4]
        state.save_snapshot()
        state.save_snapshot()

        summary = state.get_state_summary()

        self.assertEqual(summary['name'], 'test_model')
        self.assertEqual(summary['model_id'], 'test/model-1b')
        self.assertEqual(summary['token_count'], 10)
        self.assertEqual(summary['vocab_size'], 50000)
        self.assertTrue(summary['has_kv_cache'])
        self.assertTrue(summary['has_hidden_states'])
        self.assertAlmostEqual(summary['avg_confidence'], 0.85)
        self.assertAlmostEqual(summary['avg_perplexity'], 2.4)
        self.assertEqual(summary['num_snapshots'], 2)
        self.assertEqual(summary['context_used'], 5)
        self.assertIn('metadata', summary)

    def test_get_state_summary_empty_history(self):
        """Should handle empty history gracefully."""
        mock_engine = Mock()
        mock_engine.get_vocabulary_size.return_value = 50000

        state = ModelState(
            engine=mock_engine,
            name='test_model',
            model_id='test/model-1b'
        )

        summary = state.get_state_summary()

        self.assertEqual(summary['avg_confidence'], 0.0)
        self.assertEqual(summary['avg_perplexity'], 0.0)
        self.assertEqual(summary['num_snapshots'], 0)


def run_tests():
    """Run all model state tests."""
    print("=" * 80)
    print("Testing ModelState and StateSnapshot")
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
