from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "wrt_event_srstc_trace", TOOLS / "wrt_event_srstc_trace.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_continuations_use_only_prior_event_codes() -> None:
    table = MODULE.EventContinuationTable(max_keys=4, codes_per_key=4)
    key = ("schema", 7)
    assert table.candidate([key], 0, 0, alpha2=1, min_support=1) == (None, 0, 0)
    table.update([key], b"\x80")
    table.update([key], b"\xff")
    probability, support, hits = table.candidate([key], 0, 0, alpha2=1, min_support=1)
    assert probability is not None
    assert support == hits == 2
    assert probability > 32768


def test_continuation_prefix_filters_candidates_causally() -> None:
    table = MODULE.EventContinuationTable(max_keys=4, codes_per_key=4)
    key = ("schema", 7)
    table.update([key], b"\x80\x00")
    table.update([key], b"\x80\xff")
    probability, support, _hits = table.candidate(
        [key], 8, 0x80, alpha2=1, min_support=1
    )
    assert probability is not None
    assert support == 2
    assert 30000 < probability < 36000


def test_table_bounds_keys_and_distinct_codes() -> None:
    table = MODULE.EventContinuationTable(max_keys=1, codes_per_key=1)
    table.update([("a",)], b"a")
    table.update([("a",)], b"b")
    table.update([("b",)], b"c")
    assert list(table.counts) == [("b",)]
    assert table.rejected_codes == 1
    assert table.evicted_keys == 1


def test_semantic_state_changes_only_after_observation() -> None:
    state = MODULE.RawSemanticState(suffix_len=8, sketch_len=8)
    before = state.features()
    assert state.features() == before
    state.observe(b"<title>x")
    assert state.features() != before
