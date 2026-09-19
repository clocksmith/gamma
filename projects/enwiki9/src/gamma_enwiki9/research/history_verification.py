"""Coordinate original-closure validation without granting new-run authority."""
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import tempfile

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import inspect, materialize
from gamma_enwiki9.execution.sandbox import python_command


def verify(root: Path, manifest_path: Path, output: Path) -> dict:
    manifest = json.loads(manifest_path.read_bytes())
    state = inspect(root, manifest)
    if state.missing or manifest["declaration"].get("kind") != "verification":
        raise ValueError("complete original verification closure is required")
    output.mkdir()
    with tempfile.TemporaryDirectory(prefix="gamma-original-verification-") as directory:
        snapshot = Path(directory) / "snapshot"
        materialize(root, manifest, snapshot)
        artifact = manifest["declaration"]["artifact"]
        validator = manifest["declaration"]["validator"]
        mounted = "/snapshot/projects/enwiki9"
        command = python_command(readonly={snapshot: mounted}, writable={},
            argv=[mounted + "/" + validator, mounted + "/" + artifact], cwd=mounted)
        result = subprocess.run(command, capture_output=True, timeout=60)
        publish_immutable_artifact(output / "stdout.json", result.stdout)
        publish_immutable_artifact(output / "stderr.txt", result.stderr)
        verified = result.returncode == 0
        if verified:
            value = json.loads(result.stdout)
            verified = value.get("valid") is True and all(r.get("valid") for r in value.get("artifacts", []))
        state = inspect(root, manifest, replay_verified=verified)
        report = {"schema": "gamma.enwiki9.original-closure-verification.v1",
            "closure_sha256": manifest["closure_sha256"], "artifact": artifact,
            "validator": validator, "state": asdict(state), "returncode": result.returncode,
            "isolated": True, "checkout_mounted": False, "snapshot_writable": False,
            "new_execution_authorized": False, "stdout": fingerprint(output / "stdout.json", output),
            "stderr": fingerprint(output / "stderr.txt", output)}
        publish_immutable_artifact(output / "verification.json", canonical_bytes(report) + b"\n")
    return report
