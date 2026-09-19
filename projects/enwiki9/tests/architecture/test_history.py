import json
from pathlib import Path
import shutil

import pytest

from gamma_enwiki9.evidence.history import blob_path, freeze, inspect, materialize
from gamma_enwiki9.research.history_verification import verify

PROJECT = Path(__file__).resolve().parents[2]


def test_restoration_ignores_checkout_edits_and_refuses_corrupt_blobs(tmp_path):
    (tmp_path / "validator.py").write_text("original")
    manifest = freeze(tmp_path, {"validator.py": "validator"}, declaration={"complete": True},
                      destination=tmp_path / "manifest.json")
    (tmp_path / "validator.py").write_text("replacement")
    materialize(tmp_path, manifest, tmp_path / "restored")
    assert (tmp_path / "restored/validator.py").read_text() == "original"
    assert not (tmp_path / "restored/validator.py").stat().st_mode & 0o222
    assert not inspect(tmp_path, manifest).authorized_for_new_execution
    blob = blob_path(tmp_path, manifest["files"][0]["sha256"])
    blob.chmod(0o644)
    blob.write_text("corrupt")
    assert inspect(tmp_path, manifest).evidence_state == "missing or corrupt evidence"
    with pytest.raises(ValueError, match="corrupt"):
        materialize(tmp_path, manifest, tmp_path / "bad")


@pytest.mark.historical
@pytest.mark.skipif(shutil.which("bwrap") is None, reason="historical isolation lane requires bubblewrap")
def test_real_historical_negative_validates_under_original_closure(tmp_path):
    manifest = PROJECT / "operations/adaptive/framework-closures/causal-wordcode-original-verification.json"
    result = verify(PROJECT, manifest, tmp_path / "verification")
    assert result["state"]["evidence_state"] == "verified under original closure"
    assert not result["state"]["compatible_with_current_launcher"]
    assert not result["new_execution_authorized"]
    original = json.loads((tmp_path / "verification/stdout.json").read_bytes())
    assert original["artifacts"][0]["decision"] == "retire"
    assert original["objectiveId"] == "gamma-enwiki9-hutter-99m-v2"
