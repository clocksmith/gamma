"""Contract tests for the SAME-R experiment register."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "samer"
    / "experiments"
    / "validate_experiment_register.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "validate_experiment_register", _VALIDATOR_PATH
)
assert _SPEC is not None and _SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _VALIDATOR
_SPEC.loader.exec_module(_VALIDATOR)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _init_git_repository(path: Path) -> str:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Gamma Test"], cwd=path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "gamma@example.invalid"],
        cwd=path,
        check=True,
    )
    marker = path / "marker.txt"
    marker.write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=path, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


class ExperimentRegisterTests(unittest.TestCase):
    def test_checked_in_register_and_schema_are_valid(self) -> None:
        _VALIDATOR.validate_schema_alignment()
        records = _VALIDATOR.validate_register()
        self.assertGreaterEqual(
            {record["status"] for record in records},
            {
                "harness_ready",
                "capability_proven",
                "rejected",
                "blocked",
            },
        )

    def test_duplicate_experiment_ids_are_rejected(self) -> None:
        records = _VALIDATOR.validate_register(verify_available_artifacts=False)
        duplicate = copy.deepcopy(records[0])
        with tempfile.TemporaryDirectory() as temp_dir:
            register = Path(temp_dir) / "duplicate.jsonl"
            _write_rows(register, [records[0], duplicate])

            with self.assertRaisesRegex(
                _VALIDATOR.RegistryValidationError, "duplicate"
            ):
                _VALIDATOR.validate_register(
                    register, verify_available_artifacts=False
                )

    def test_unknown_method_is_rejected(self) -> None:
        record = copy.deepcopy(
            _VALIDATOR.validate_register(verify_available_artifacts=False)[0]
        )
        record["methodIds"] = ["unrecorded_optimizer"]
        with tempfile.TemporaryDirectory() as temp_dir:
            register = Path(temp_dir) / "unknown-method.jsonl"
            _write_rows(register, [record])

            with self.assertRaisesRegex(
                _VALIDATOR.RegistryValidationError, "methodIds"
            ):
                _VALIDATOR.validate_register(
                    register, verify_available_artifacts=False
                )

    def test_available_related_artifact_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repository = workspace / "gamma"
            artifact = repository / "evidence" / "receipt.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("{}\n", encoding="utf-8")
            related = repository / "evidence" / "training-result.json"
            related.write_text("[]\n", encoding="utf-8")

            record = copy.deepcopy(
                _VALIDATOR.validate_register(verify_available_artifacts=False)[0]
            )
            record["owner"] = {
                "repository": "clocksmith/gamma",
                "path": "evidence",
            }
            record["artifact"] = {
                "repository": "clocksmith/gamma",
                "path": "evidence/receipt.json",
                "revision": "0" * 40,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
            record["relatedArtifacts"] = [
                {
                    "repository": "clocksmith/gamma",
                    "path": "evidence/training-result.json",
                    "revision": "0" * 40,
                    "sha256": "f" * 64,
                }
            ]
            register = workspace / "bad-hash.jsonl"
            _write_rows(register, [record])

            with self.assertRaisesRegex(
                _VALIDATOR.RegistryValidationError, "hash mismatch"
            ):
                _VALIDATOR.validate_register(register, workspace_root=workspace)

    def test_git_artifact_is_verified_at_recorded_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repository = workspace / "gamma"
            artifact = repository / "evidence" / "receipt.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("{\"version\":1}\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repository), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            commit_env = {
                **os.environ,
                "GIT_AUTHOR_NAME": "Gamma Test",
                "GIT_AUTHOR_EMAIL": "gamma-test@example.invalid",
                "GIT_COMMITTER_NAME": "Gamma Test",
                "GIT_COMMITTER_EMAIL": "gamma-test@example.invalid",
            }
            subprocess.run(
                ["git", "-C", str(repository), "commit", "-q", "-m", "fixture"],
                check=True,
                env=commit_env,
            )
            revision = subprocess.check_output(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
            artifact.write_text("{\"version\":2}\n", encoding="utf-8")

            record = copy.deepcopy(
                _VALIDATOR.validate_register(verify_available_artifacts=False)[0]
            )
            record["owner"] = {
                "repository": "clocksmith/gamma",
                "path": "evidence",
            }
            record["artifact"] = {
                "repository": "clocksmith/gamma",
                "path": "evidence/receipt.json",
                "revision": revision,
                "sha256": expected_hash,
            }
            record.pop("relatedArtifacts", None)
            register = workspace / "historical.jsonl"
            _write_rows(register, [record])

            validated = _VALIDATOR.validate_register(
                register,
                workspace_root=workspace,
            )
            self.assertEqual(validated[0]["artifact"]["revision"], revision)

    def test_git_artifact_missing_at_pinned_revision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repository = workspace / "gamma"
            revision = _init_git_repository(repository)
            artifact = repository / "evidence" / "receipt.json"
            artifact.parent.mkdir()
            artifact.write_text("{}\n", encoding="utf-8")

            record = copy.deepcopy(
                _VALIDATOR.validate_register(verify_available_artifacts=False)[0]
            )
            record["owner"] = {
                "repository": "clocksmith/gamma",
                "path": "evidence",
            }
            record["artifact"] = {
                "repository": "clocksmith/gamma",
                "path": "evidence/receipt.json",
                "revision": revision,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
            record.pop("relatedArtifacts", None)
            register = workspace / "missing-at-revision.jsonl"
            _write_rows(register, [record])

            with self.assertRaisesRegex(
                _VALIDATOR.RegistryValidationError,
                "does not exist at recorded revision",
            ):
                _VALIDATOR.validate_register(register, workspace_root=workspace)

if __name__ == "__main__":
    unittest.main()
