from pathlib import Path
import sys


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from wrt_exact import WrtEvent  # noqa: E402
from wrt_reference_prefix_cts_shadow import (  # noqa: E402
    ContinuationTable,
    ReferenceScanner,
    Variant,
    candidate_probability,
    count_reference_bodies,
    normalized_event_signature,
)


def event(start: int, encoded: bytes, decoded: bytes) -> WrtEvent:
    return WrtEvent(start, start + len(encoded), encoded, decoded, "literal")


def test_scanner_releases_reference_only_after_close() -> None:
    scanner = ReferenceScanner()
    assert scanner.observe_event(event(0, b"a", b"&lt;ref name='x'&gt;")) is None
    assert scanner.in_body
    body = event(1, b"b", b"citation")
    assert scanner.observe_event(body) is None
    assert scanner.current_events == [body]
    closing = event(2, b"c", b"&lt;/ref&gt;")
    completed = scanner.observe_event(closing)
    assert completed == (body, closing)
    assert not scanner.in_body
    assert scanner.completed_references == 1


def test_scanner_ignores_self_closing_reference() -> None:
    scanner = ReferenceScanner()
    assert scanner.observe_event(event(0, b"a", b"&lt;ref name='x'/&gt;")) is None
    assert not scanner.in_body
    assert scanner.self_closing_references == 1
    assert scanner.completed_references == 0


def test_table_uses_only_inserted_prior_references() -> None:
    table = ContinuationTable()
    first = event(0, b"x", b"Cite")
    second = event(1, b"y", b"2026")
    assert table.candidates([first]) == {}
    table.add_reference((first, second))
    candidates = table.candidates([first])
    assert candidates[1] == {b"y": 1}
    assert table.inserted_references == 1


def test_candidate_filters_only_by_already_observed_bits() -> None:
    variant = Variant(context_length=1, min_support=1, blend_ppm=200_000)
    counter = {b"\xa0": 3, b"\xbf": 1}
    first = candidate_probability(counter, 0, 0, 32768, variant)
    assert first is not None
    # Both candidates begin with one, so observing that bit keeps all support.
    second = candidate_probability(counter, 1, 1, 32768, variant)
    assert second is not None and second[1] == 4
    # A zero first-bit prefix has no compatible prior continuation.
    assert candidate_probability(counter, 1, 0, 32768, variant) is None


def test_normalization_collapses_numeric_runs_without_future_state() -> None:
    one = event(0, b"x", b"2026")
    two = event(0, b"x", b"1999")
    assert normalized_event_signature(one) == normalized_event_signature(two)


def test_raw_census_matches_complete_not_self_closing_refs() -> None:
    raw = (
        b"&lt;ref&gt;a&lt;/ref&gt;"
        b"&lt;ref name='x'/&gt;"
        b"&lt;REF&gt;b&lt;/REF&gt;"
    )
    assert count_reference_bodies(raw) == 2
