from pathlib import Path
import sys


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from wrt_exact import WrtEvent  # noqa: E402
from wrt_normalized_phrase_copy_shadow import (  # noqa: E402
    PhraseTable,
    actual_path_endpoints,
    continuation_endpoint,
    signature,
    specs,
)
from wrt_normalized_phrase_endpoint_trace import (  # noqa: E402
    HEADER_BYTES,
    PAIR_MAGIC,
    initialize_trace,
)


def event(start: int, encoded: bytes, decoded: bytes) -> WrtEvent:
    return WrtEvent(start, start + len(encoded), encoded, decoded, "literal")


def test_normalized_table_matches_changed_numbers() -> None:
    table = PhraseTable("normalized")
    first = event(0, b"a", b"2026")
    next_event = event(1, b"b", b"title")
    table.observe(first)
    table.observe(next_event)
    table.history = [signature(event(0, b"x", b"1999"), "normalized")]
    assert table.candidates()[1] == {b"b": 1}


def test_exact_control_does_not_merge_changed_codes() -> None:
    table = PhraseTable("exact")
    table.observe(event(0, b"a", b"same"))
    table.observe(event(1, b"b", b"next"))
    table.history = [signature(event(0, b"x", b"same"), "exact")]
    assert table.candidates() == {}


def test_transition_is_unavailable_until_event_observed() -> None:
    table = PhraseTable("normalized")
    first = event(0, b"a", b"cite")
    second = event(1, b"b", b"url")
    table.observe(first)
    assert table.candidates() == {}
    table.observe(second)
    table.history = [signature(first, "normalized")]
    assert table.candidates()[1] == {b"b": 1}


def test_endpoint_count_is_shared_across_blend_variants() -> None:
    counter = {b"\xa0": 3, b"\xbf": 1}
    endpoint = continuation_endpoint(counter, 1, 1)
    assert endpoint is not None
    _, support = endpoint
    assert support == 4
    assert continuation_endpoint(counter, 1, 0) is None


def test_coarse_grid_is_staged_not_a_full_cartesian_sweep() -> None:
    coarse = specs("coarse")
    assert len(coarse) == 30
    assert {item.min_support for item in coarse} == {1}
    assert {item.blend_ppm for item in coarse} == {10_000, 50_000, 200_000}
    routed = specs("coarse", "context_regret", ("normalized",))
    assert len(routed) == 15
    assert all(item.router == "context_regret" for item in routed)
    assert all(item.variant_id.endswith("_context_regret") for item in routed)


def test_path_precomputation_matches_prefix_only_reference() -> None:
    counter = {b"\xa0": 3, b"\xbf": 1, b"\x20": 2}
    actual = b"\xa0"
    path = actual_path_endpoints(counter, actual)
    prefix = 0
    for bit_index, endpoint in enumerate(path):
        assert endpoint == continuation_endpoint(counter, bit_index, prefix)
        bit = (actual[bit_index // 8] >> (7 - (bit_index & 7))) & 1
        prefix = (prefix << 1) | bit


def test_pair_trace_header_and_shape(tmp_path: Path) -> None:
    path = tmp_path / "pair.bin"
    pair = initialize_trace(path, PAIR_MAGIC, 3, 2)
    pair[:, :] = [[1, 2], [3, 4], [5, 6]]
    pair.flush()
    del pair
    assert path.read_bytes()[:8] == PAIR_MAGIC
    assert path.stat().st_size == HEADER_BYTES + 3 * 2 * 2
