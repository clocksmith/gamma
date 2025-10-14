"""Unit tests for core Mind Meld orchestration utilities."""

import sys
import os
import types
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Provide a minimal numpy stub if the real package is unavailable. The
# production Mind Meld pipeline expects numpy, but these tests only exercise
# control-flow/bridging logic and do not require numerical ops.
if 'numpy' not in sys.modules:  # pragma: no cover - exercised when numpy missing
    class _MinimalNumpy(types.SimpleNamespace):
        ndarray = object

        def nan_to_num(self, arr, **kwargs):
            return arr

    sys.modules['numpy'] = _MinimalNumpy()


from src.mind_meld.core.meld_engine import MeldEngine


class MindMeldEngineTests(unittest.TestCase):
    """Validate swap heuristics and KV-cache bridging behaviour."""

    def setUp(self) -> None:
        self.args = SimpleNamespace(
            temperature=0.7,
            top_k=8,
            top_p=0.95,
            steps=3,
            verbose=False,
            show_attention=False,
            swap_strategy='fixed',
            fixed_interval=1,
            use_blending=False,
            use_weighted_average=False,
            use_abe=False,
            use_stats_tracker=False,
            stats_file=None,
            initial_prompt="Hello world"
        )

        self.source_engine = MagicMock()
        self.source_engine.model_name = "engine-a"
        self.source_engine.get_num_layers.return_value = 1
        self.source_engine.tokenizer = SimpleNamespace(name_or_path="engine-a")
        self.source_engine.bridge_kv_cache_to.return_value = False

        source_config = SimpleNamespace(
            num_hidden_layers=1,
            num_attention_heads=1,
            hidden_size=1024,
            to_dict=lambda: {"hidden_size": 1024},
        )
        self.source_engine.model = SimpleNamespace(config=source_config)

        self.target_engine = MagicMock()
        self.target_engine.model_name = "engine-b"
        self.target_engine.get_num_layers.return_value = 1
        self.target_engine.tokenizer = SimpleNamespace(name_or_path="engine-b")
        target_config = SimpleNamespace(
            num_hidden_layers=1,
            num_attention_heads=1,
            hidden_size=1024,
            to_dict=lambda: {"hidden_size": 1024},
        )
        self.target_engine.model = SimpleNamespace(config=target_config)

        self.engines = [self.source_engine, self.target_engine]

    def test_fixed_interval_swap_bridges_kv_cache(self) -> None:
        """A fixed-interval swap should transfer the bridged KV cache."""
        meld = MeldEngine(self.engines, self.args)
        meld._transfer_kv_cache = MagicMock(return_value=True)

        meld._perform_swap()

        meld._transfer_kv_cache.assert_called_once_with(self.source_engine, self.target_engine)
        self.target_engine.reset_kv_cache.assert_not_called()
        self.assertEqual(meld.active_model_idx, 1)

    def test_swap_resets_target_cache_when_bridge_fails(self) -> None:
        """If bridging fails, the next engine should reset its cache."""
        meld = MeldEngine(self.engines, self.args)
        meld._transfer_kv_cache = MagicMock(return_value=False)

        meld._perform_swap()

        self.target_engine.reset_kv_cache.assert_called_once()
        self.assertEqual(meld.active_model_idx, 1)

    def test_transfer_prefers_export_import_when_available(self) -> None:
        """The transfer helper should use standard export/import hooks when possible."""
        meld = MeldEngine(self.engines, self.args)

        source_cache = {'layers': []}
        export_state = {'cache_data': [('k', 'v')]}

        self.source_engine.get_kv_cache.return_value = source_cache
        self.source_engine.bridge_kv_cache_to.return_value = False
        self.source_engine.export_kv_cache_state.return_value = export_state
        self.target_engine.import_kv_cache_state.return_value = True

        result = meld._transfer_kv_cache(self.source_engine, self.target_engine)

        self.assertTrue(result)
        self.source_engine.export_kv_cache_state.assert_called_once()
        self.target_engine.import_kv_cache_state.assert_called_once_with(export_state)

    def test_should_swap_respects_strategy(self) -> None:
        """Verify pattern and fixed strategies trigger swaps appropriately."""
        meld = MeldEngine(self.engines, self.args)

        # Fixed interval increments an internal counter
        meld.fixed_interval = 2
        meld.token_counter = 0
        self.assertFalse(meld._should_swap('token'))
        self.assertTrue(meld._should_swap('token'))  # second call hits interval

        meld.swap_strategy = 'pattern'
        self.assertTrue(meld._should_swap('!'))
        self.assertFalse(meld._should_swap('word'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
