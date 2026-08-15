from __future__ import annotations

import hashlib
import json
from pathlib import Path

from projects.enwiki9.lib import driver
from projects.enwiki9.tools import candidate_triage
from projects.enwiki9.tools import enwiki9_candidate_revisions as revisions


def cached_row() -> dict:
    return {
        "data_size": 1024,
        "compressed_size": 100,
        "program_size": 20,
        "hutter_score": 120,
    }


def test_cached_result_does_not_infer_missing_truth_from_label() -> None:
    normalized = candidate_triage.normalize_cached_result(
        program_id="candidate",
        row=cached_row(),
        source="meta.json",
        label="inherited_identity_1k",
    )

    assert normalized is not None
    assert normalized["roundtrip_ok"] is None
    assert normalized["determinism"]["single_host_byte_equal"] is None


def test_cached_result_preserves_only_explicit_truth() -> None:
    row = cached_row()
    row["roundtrip_ok"] = True
    row["determinism_ok"] = True

    normalized = candidate_triage.normalize_cached_result(
        program_id="candidate",
        row=row,
        source="receipt.json",
    )

    assert normalized is not None
    assert normalized["roundtrip_ok"] is True
    assert normalized["determinism"]["single_host_byte_equal"] is True


def test_program_package_inventory_is_recursive_and_hashes_members(
    tmp_path: Path,
) -> None:
    (tmp_path / "program.py").write_bytes(b"root")
    nested = tmp_path / "model"
    nested.mkdir()
    (nested / "weights.bin").write_bytes(b"weights")
    (tmp_path / "meta.json").write_text('{"deps": []}')

    files, accounting = driver._program_package_inventory(tmp_path, {"deps": []})

    assert files == [("model/weights.bin", 7), ("program.py", 4)]
    receipts = {row["path"]: row for row in accounting["counted_files"]}
    assert receipts["program.py"]["sha256"] == hashlib.sha256(b"root").hexdigest()
    assert receipts["model/weights.bin"]["sha256"] == hashlib.sha256(
        b"weights"
    ).hexdigest()
    assert accounting["dependency_closure_complete"] is False


def test_candidate_revision_binds_immutable_source_and_ignores_derived_meta(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "enwiki9"
    adaptive = project / "operations" / "adaptive"
    monkeypatch.setattr(revisions, "ROOT", project)
    monkeypatch.setattr(revisions, "PROGRAMS", project / "programs")
    monkeypatch.setattr(revisions, "ADAPTIVE", adaptive)
    monkeypatch.setattr(revisions, "REVISIONS", adaptive / "candidate-revisions")
    monkeypatch.setattr(
        revisions,
        "BLOBS",
        adaptive / "candidate-blobs" / "sha256",
    )
    monkeypatch.setattr(revisions, "LOCK", adaptive / "candidate-revisions.lock")
    monkeypatch.setattr(revisions.research_contracts, "PROJECT_ROOT", project)

    candidate = revisions.PROGRAMS / "probe"
    candidate.mkdir(parents=True)
    (candidate / "program.py").write_text(
        "def compress(value): return value\n"
        "def decompress(value): return value\n"
    )
    metadata = {
        "candidate_revision_protocol": "gamma.enwiki9.candidate-revision.v1",
        "deps": [],
        "hypothesis": "identity",
        "id": "probe",
        "status": "candidate",
    }
    (candidate / "meta.json").write_text(json.dumps(metadata))

    first_path, first = revisions.record_revision(
        candidate_id="probe",
        kind="create",
        hypothesis="identity",
        summary=["Create identity candidate."],
    )
    metadata["status"] = "active"
    metadata["measured"] = {"1k": {"roundtrip_ok": True}}
    (candidate / "meta.json").write_text(json.dumps(metadata))
    assert revisions.ensure_current_revision("probe")[0] == first_path

    (candidate / "program.py").write_text(
        "def compress(value): return b'x' + value\n"
        "def decompress(value): return value[1:]\n"
    )
    try:
        revisions.ensure_current_revision("probe")
    except ValueError as exc:
        assert "differs from its latest revision" in str(exc)
    else:
        raise AssertionError("semantic source drift was accepted")

    second_path, second = revisions.seal_candidate(
        "probe",
        hypothesis="reversible marker",
        summary=["Add a reversible marker."],
        evidence=[],
    )
    assert first["candidateTreeSha256"] != second["candidateTreeSha256"]
    snapshot = project / "snapshot" / "probe"
    revisions.materialize_revision(second, snapshot)
    assert (snapshot / "program.py").read_bytes() == (candidate / "program.py").read_bytes()

    pending = adaptive / "pending"
    pending.mkdir(parents=True)
    (pending / "job.json").write_text(json.dumps({"candidate_id": "probe"}))
    (candidate / "program.py").write_text("raise RuntimeError('drift')\n")
    try:
        revisions.seal_candidate(
            "probe",
            hypothesis="forbidden edit",
            summary=["Edit a measured identity."],
            evidence=[],
        )
    except ValueError as exc:
        assert "already has queued or measured evidence" in str(exc)
    else:
        raise AssertionError("measured candidate mutation was accepted")
    assert revisions.receipt_reference(second_path)["sha256"].startswith("sha256:")
