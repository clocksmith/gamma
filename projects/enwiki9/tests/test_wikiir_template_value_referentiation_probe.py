from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "wikiir_template_value_referentiation_probe",
    TOOLS / "wikiir_template_value_referentiation_probe.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_value_copy_charges_reference_and_literal_fields() -> None:
    signature = (b"{{cite|url=", b"|title=", b"}}")
    prior = MODULE.Occurrence(0, 0, b"A", signature, (b"url", b"title"))
    current = MODULE.Occurrence(1, 1, b"B", signature, (b"url", b"other"))
    cost = MODULE._cost(current, prior)
    assert cost["copied_fields"] == 1
    assert cost["copied_value_bytes"] == 3
    assert cost["literal_value_bytes"] == 5


def test_history_is_causal_and_random_control_stays_within_history() -> None:
    raw = (
        b"<page><title>A</title>{{cite|url=same|title=first}}"
        b"{{cite|url=same|title=also-first}}</page>"
        b"<page><title>B</title>{{cite|url=same|title=second}}</page>"
    )
    result = MODULE.run(raw)
    assert result["pages"] == 2
    assert result["template_occurrences"] == 3
    assert result["occurrences_with_same_skeleton_history"] == 1
    assert result["top_occurrences"][0]["prior_page_ordinal"] == 0
