from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "projects" / "enwiki9" / "tools"
BUNDLE = (
    ROOT
    / "projects"
    / "enwiki9"
    / "operations"
    / "clockwork"
    / "residual_expert_search_v1"
    / "imports"
    / "m3t4-e6d0ed9d"
)
TRANSFER = (
    ROOT
    / "projects"
    / "enwiki9"
    / "operations"
    / "clockwork"
    / "residual_expert_search_v1"
    / "transfer-trace.json"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


contracts = _load_module("clockwork_contracts", TOOLS / "clockwork_contracts.py")
gate = _load_module("clockwork_candidate_gate", TOOLS / "clockwork_candidate_gate.py")


def _rewrite_bundle_file(bundle: Path, filename: str, value: dict) -> None:
    path = bundle / filename
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = bundle / "import-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][filename] = contracts.sha256_digest(path.read_bytes())
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_gamma_independently_accepts_the_imported_frontier_candidate() -> None:
    receipt = gate.evaluate_bundle(
        BUNDLE,
        transfer_trace_path=TRANSFER,
        created_at="2026-07-26T00:00:00Z",
    )
    assert receipt["authority"] == "gamma"
    assert receipt["result"] == "accepted"
    assert receipt["firstFailedGate"] is None
    assert all(result["status"] == "passed" for result in receipt["gates"].values())
    assert receipt["ledgers"]["bytes"]["compressionBytesClaimed"] is False
    assert receipt["ledgers"]["bytes"]["development"]["developmentSavingsUnits"] > 0
    assert receipt["ledgers"]["bytes"]["transfer"]["developmentSavingsUnits"] > 0


def test_gamma_rejects_m3t4_evidence_that_disagrees_with_independent_replay(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    receipt_path = bundle / "search-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    candidate_digest = json.loads(
        (bundle / "candidate.json").read_text(encoding="utf-8")
    )["candidateDigest"]
    row = next(
        item for item in receipt["evaluations"]
        if item["candidateDigest"] == candidate_digest
    )
    row["rawLedger"]["candidateLossUnits"] += 1
    receipt["receiptDigest"] = contracts.artifact_digest(receipt, "receiptDigest")
    _rewrite_bundle_file(bundle, "search-receipt.json", receipt)
    result = gate.evaluate_bundle(
        bundle,
        transfer_trace_path=TRANSFER,
        created_at="2026-07-26T00:00:00Z",
    )
    assert result["result"] == "rejected"
    assert result["firstFailedGate"] == "sourceAccounting"
    assert result["gates"]["sourceAccounting"]["status"] == "failed"


def test_gamma_fails_closed_on_import_manifest_tampering(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    candidate = json.loads((bundle / "candidate.json").read_text(encoding="utf-8"))
    candidate["resourceDeclaration"]["peakStateBytes"] = 7
    (bundle / "candidate.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        gate.evaluate_bundle(
            bundle,
            transfer_trace_path=TRANSFER,
            created_at="2026-07-26T00:00:00Z",
        )
    except ValueError as error:
        assert "import manifest digest mismatch for candidate.json" in str(error)
    else:
        raise AssertionError("tampered bundle unexpectedly passed import verification")
