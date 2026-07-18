from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TOOLS = Path(__file__).resolve().parents[1] / "projects/enwiki9/tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "wrt_entity_trie_fx2_shadow.py"
SPEC = importlib.util.spec_from_file_location("wrt_entity_trie_fx2_shadow", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def events(text: bytes) -> list[MODULE.WrtEvent]:
    return [
        MODULE.WrtEvent(
            start=index,
            end=index + 1,
            encoded=bytes((value,)),
            decoded=bytes((value,)),
            kind="literal",
        )
        for index, value in enumerate(text)
    ]


def test_observer_builds_title_then_exposes_link_prefix() -> None:
    observer = MODULE.EntityObserver()
    trie = MODULE.EntityTrie(cap_nodes=100)
    completed = []
    for event in events(b"<title>Alpha</title>"):
        row = observer.observe(event)
        if row:
            completed.append(row)
            trie.insert(row[1])

    assert completed == [("title", tuple(bytes((value,)) for value in b"Alpha"))]
    assert observer.completed_titles == 1

    for event in events(b"[["):
        assert observer.observe(event) is None
    assert observer.in_link is True
    node = trie.follow(observer.link_prefix)
    p1, support = trie.predict(node, 0, 0, min_support=1, alpha2=1)
    assert p1 is not None
    assert support == 1
    assert p1 < MODULE.TOTAL // 2  # ASCII 'A' begins with a zero bit.


def test_trie_prediction_filters_completed_bit_prefix() -> None:
    trie = MODULE.EntityTrie(cap_nodes=100)
    trie.insert((b"A",))
    trie.insert((b"C",))

    # Both candidates begin 01; after 010000 the next bit separates A from C.
    p1, support = trie.predict(0, 6, 0b010000, min_support=1, alpha2=1)

    assert p1 is not None
    assert support == 2
    assert p1 == MODULE.TOTAL // 2


def test_link_target_is_inserted_without_delimiter() -> None:
    observer = MODULE.EntityObserver()
    output = []
    for event in events(b"[[Known Target|label]]"):
        row = observer.observe(event)
        if row:
            output.append(row)

    assert output == [
        ("link", tuple(bytes((value,)) for value in b"Known Target"))
    ]
    assert observer.completed_links == 1


def test_p1_trace_accepts_both_sealed_magics(tmp_path: Path) -> None:
    for magic in MODULE.P1_MAGICS:
        path = tmp_path / magic.hex()
        path.write_bytes(magic + (1).to_bytes(8, "little") + (32768).to_bytes(2, "little"))
        trace = MODULE.P1Trace(path)
        try:
            assert trace.rows == 1
            assert trace.p1(0) == 32768
        finally:
            trace.close()
