from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "wikiir_page_list_referentiation_probe",
    TOOLS / "wikiir_page_list_referentiation_probe.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_scan_pages_and_targets_preserves_order() -> None:
    raw = (
        b"<page><title>A</title>[[One]][[Two|label]]</page>"
        b"<page><title>B</title>[[Two]][[One]]</page>"
    )
    pages = MODULE.scan_pages(raw)
    assert [page.title for page in pages] == [b"A", b"B"]
    assert pages[0].targets == (b"One", b"Two")
    assert pages[1].targets == (b"Two", b"One")


def test_delta_cost_rewards_ordered_copy_interval() -> None:
    prior = MODULE.Page(0, b"A", (b"Alpha", b"Beta", b"Gamma"))
    current = MODULE.Page(1, b"B", (b"Alpha", b"Beta", b"Delta"))
    result = MODULE.delta_cost(prior, current)
    assert result["copy_blocks"] == 1
    assert result["copied_target_bytes"] == len(b"AlphaBeta")
    assert result["literal_target_bytes"] == len(b"Delta")


def test_candidate_priors_use_only_previously_indexed_pages() -> None:
    postings = {b"A": [0, 2], b"B": [1]}
    page = MODULE.Page(3, b"P", (b"A", b"B"))
    assert MODULE.candidate_prior_ids(page, postings, 16) == [2, 1, 0]


def test_random_prior_is_strictly_earlier() -> None:
    for ordinal in range(1, 100):
        assert 0 <= MODULE.random_prior_id(ordinal) < ordinal
