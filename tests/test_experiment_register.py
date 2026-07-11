"""Contract tests for the verifier-guided experiment register."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "shared"
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


if __name__ == "__main__":
    unittest.main()
