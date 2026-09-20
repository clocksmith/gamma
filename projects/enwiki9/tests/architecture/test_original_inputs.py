"""Terminal source interpretation does not relax live admission identities."""
import hashlib
import json
from pathlib import Path

import pytest

from gamma_enwiki9.evidence import contracts
from gamma_enwiki9.evidence.history import blob_path, freeze, original_input_sources


@pytest.fixture
def historical_inputs(tmp_path, monkeypatch):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/driver.py").write_text("import helper\n")
    (tmp_path / "tools/helper.py").write_text("raise RuntimeError('never execute source during resolution')\n")
    (tmp_path / "asset.bin").write_bytes(b"original asset")
    names = ["tools/driver.py", "tools/helper.py", "asset.bin"]
    freeze(tmp_path, {name: "input" for name in names}, declaration={}, destination=tmp_path / "closure.json")
    refs = [{"id": str(i), "path": name, "sha256": "sha256:" + hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()}
            for i, name in enumerate(names)]
    project = Path(__file__).resolve().parents[2]
    value = json.loads((project / "operations/adaptive/experiments/xml_history250k_q0_v2.json").read_bytes())
    value["parent"] = None
    value["inputs"] = refs
    value["pythonSourceClosureEntries"] = ["0"]
    path = tmp_path / "experiment.json"
    path.write_text(json.dumps(value))
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    return tmp_path, refs, path


def test_original_source_geometry_survives_current_framework_change(historical_inputs):
    root, refs, experiment = historical_inputs
    (root / "tools/driver.py").write_text("import added_later\n")
    (root / "tools/added_later.py").write_text("pass\n")
    (root / "asset.bin").unlink()
    with original_input_sources(root, refs) as restored:
        assert (restored / "tools/driver.py").read_text() == "import helper\n"
        assert not (restored / "tools/added_later.py").exists()
    assert contracts.validate_artifact(experiment, original_experiment_inputs=True)["valid"]
    # Successful original interpretation never changes default launch checks.
    with pytest.raises(ValueError, match="digest differs"):
        contracts.validate_artifact(experiment)


def test_corrupt_original_blob_fails_closed(historical_inputs):
    root, refs, _ = historical_inputs
    (root / "tools/driver.py").write_text("different")
    blob = blob_path(root, refs[0]["sha256"])
    blob.chmod(0o644)
    blob.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="original input"):
        with original_input_sources(root, refs):
            pass
