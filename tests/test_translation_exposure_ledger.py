import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "projects" / "distillation" / "translation" / "pipeline"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ledger_module = load_module("translation_exposure_ledger", PIPELINE / "exposure_ledger.py")


def test_committed_exposure_ledger_is_hash_chained_and_wmt13_is_development_only():
    ledger_path = ROOT / "projects" / "distillation" / "translation" / "promotion" / "exposure-ledger.v1.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger_module.validate_ledger(ledger) == []
    wmt13_events = [event for event in ledger["events"] if event.get("artifact", {}).get("id") == "wmt13-enes-128-legacy"]
    assert wmt13_events
    assert {event.get("role") for event in wmt13_events} == {"development"}
    assert all(event.get("details", {}).get("promotionUseAllowed") is not True for event in wmt13_events)


def test_nonfinite_values_have_canonical_hashes_but_are_rejected_as_evidence():
    assert ledger_module.hash_evidence({"value": math.nan}) != ledger_module.hash_evidence({"value": math.inf})
    ledger = {
        "schema": ledger_module.EXPOSURE_LEDGER_SCHEMA,
        "schemaSha256": ledger_module.EXPOSURE_LEDGER_SCHEMA_SHA256,
        "ledgerId": "invalid",
        "repository": "gamma",
        "events": ledger_module.seal_events([{
            "eventId": "invalid",
            "occurredAt": "2026-07-19T00:00:00.000Z",
            "type": "safeguard_verified",
            "repository": "gamma",
            "experimentId": "invalid",
            "actor": {"type": "repository", "id": "gamma"},
            "details": {"metric": math.nan},
        }]),
    }
    assert any("nonfinite" in reason for reason in ledger_module.validate_ledger(ledger))
