from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "wrt_entity_node_backoff_trace",
    TOOLS / "wrt_entity_node_backoff_trace.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_support_bucket_is_bounded_and_monotone() -> None:
    values = [MODULE.support_bucket(value) for value in range(1, 1000)]
    assert values == sorted(values)
    assert MODULE.support_bucket(0) == 0
    assert MODULE.support_bucket(1 << 30) == 15


def test_backoff_predicts_before_current_truth_update() -> None:
    model = MODULE.EntityNodeBackoff(
        profile="global",
        max_contexts=100,
        base_buckets=32,
        retrieval_buckets=16,
        prior_strength=8,
    )
    kwargs = {
        "node": 7,
        "relative_bit": 0,
        "base_p1": 32768,
        "retrieval_p1": 60000,
        "support": 12,
    }
    first = model.predict_then_update(**kwargs, bit=1)
    second = model.predict_then_update(**kwargs, bit=1)
    assert first == 32768
    assert second > first


def test_node_profile_adds_exact_node_coordinates() -> None:
    model = MODULE.EntityNodeBackoff(
        profile="node",
        max_contexts=100,
        base_buckets=32,
        retrieval_buckets=16,
        prior_strength=8,
    )
    keys = model.keys(
        node=11,
        relative_bit=9,
        base_p1=40000,
        retrieval_p1=50000,
        support=4,
    )
    assert [key[0] for key in keys] == [
        "map",
        "position",
        "node_coarse",
        "node_exact",
    ]
    assert all(key[1] == 11 for key in keys[2:])


def test_context_cap_blocks_new_keys_without_evicting_history() -> None:
    table = MODULE.BoundedCounts(cap=1)
    table.update([("first",)], 1)
    table.update([("second",)], 0)
    assert table.counts == {("first",): [0, 1]}
    assert table.blocked == 1
