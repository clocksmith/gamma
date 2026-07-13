#!/usr/bin/env python3
"""Validate Gamma's cross-repository verifier-guided experiment register."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_REGISTER = Path(__file__).with_name("experiment-register.jsonl")
SCHEMA_PATH = Path(__file__).with_name("experiment-register.schema.json")
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
REPOSITORY_PATTERN = re.compile(r"^[a-z0-9_.-]+/[a-z0-9_.-]+$")
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DOMAINS = {
    "coding",
    "finance_documents",
    "legal_documents",
    "simulation_rendering",
    "translation",
    "wgsl",
}
METHOD_IDS = {
    "active_learning",
    "adversarial_self_play",
    "checkpoint_selection",
    "construction_search",
    "data_centric_sft",
    "dpo",
    "execution_verified_sft",
    "gepa",
    "grpo_rlvr",
    "human_adjudicated_sft",
    "logit_distillation",
    "minimum_risk_training",
    "on_policy_distillation",
    "process_supervision",
    "reflective_prompt_mutation",
    "rejection_sampling",
    "routing",
    "rule_based_ai_feedback",
    "sequence_level_distillation",
    "training_backend_parity",
}
STATUSES = {
    "proposed",
    "harness_ready",
    "mechanics_proven",
    "capability_proven",
    "promoted",
    "rejected",
    "blocked",
}
REWARD_TYPES = {
    "deterministic",
    "learned_metric",
    "ai_judge",
    "human_adjudicated",
}
REWARD_ROLES = {"blocking", "supporting", "promotion"}
REQUIRED_FIELDS = {
    "schemaVersion",
    "experimentId",
    "recordedAt",
    "domain",
    "owner",
    "hypothesis",
    "methodIds",
    "status",
    "claimBoundary",
    "artifact",
    "rewardComponents",
    "nextGate",
}
OPTIONAL_FIELDS = {"relatedArtifacts"}


class RegistryValidationError(ValueError):
    """Raised when the experiment register violates its contract."""


def _require_string(value: Any, field: str, line_number: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryValidationError(
            f"line {line_number}: {field} must be a nonempty string"
        )
    return value


def _validate_relative_path(value: Any, field: str, line_number: int) -> str:
    path = _require_string(value, field, line_number)
    pure_path = PurePosixPath(path)
    if pure_path.is_absolute() or ".." in pure_path.parts or "\\" in path:
        raise RegistryValidationError(
            f"line {line_number}: {field} must be a repository-relative POSIX path"
        )
    return path


def _validate_pointer(
    value: Any,
    field: str,
    line_number: int,
    *,
    artifact: bool,
) -> dict[str, Any]:
    expected = {"repository", "path", "revision", "sha256"} if artifact else {
        "repository",
        "path",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise RegistryValidationError(
            f"line {line_number}: {field} fields must be {sorted(expected)}"
        )
    repository = _require_string(value["repository"], f"{field}.repository", line_number)
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise RegistryValidationError(
            f"line {line_number}: {field}.repository must be owner/repository"
        )
    _validate_relative_path(value["path"], f"{field}.path", line_number)
    if artifact:
        revision = _require_string(value["revision"], f"{field}.revision", line_number)
        digest = _require_string(value["sha256"], f"{field}.sha256", line_number)
        if not REVISION_PATTERN.fullmatch(revision):
            raise RegistryValidationError(
                f"line {line_number}: {field}.revision must be a 40-character commit"
            )
        if not SHA256_PATTERN.fullmatch(digest):
            raise RegistryValidationError(
                f"line {line_number}: {field}.sha256 must be a lowercase SHA-256"
            )
    return value


def validate_record(record: Any, line_number: int) -> dict[str, Any]:
    """Validate one parsed JSONL record and return it unchanged."""
    if not isinstance(record, dict):
        raise RegistryValidationError(f"line {line_number}: record must be an object")
    if not REQUIRED_FIELDS <= set(record) or not set(record) <= REQUIRED_FIELDS | OPTIONAL_FIELDS:
        missing = sorted(REQUIRED_FIELDS - set(record))
        extra = sorted(set(record) - REQUIRED_FIELDS - OPTIONAL_FIELDS)
        raise RegistryValidationError(
            f"line {line_number}: field mismatch missing={missing} extra={extra}"
        )
    if record["schemaVersion"] != 1:
        raise RegistryValidationError(f"line {line_number}: schemaVersion must be 1")

    experiment_id = _require_string(record["experimentId"], "experimentId", line_number)
    if not ID_PATTERN.fullmatch(experiment_id):
        raise RegistryValidationError(
            f"line {line_number}: experimentId has invalid characters"
        )
    recorded_at = _require_string(record["recordedAt"], "recordedAt", line_number)
    if not DATE_PATTERN.fullmatch(recorded_at):
        raise RegistryValidationError(
            f"line {line_number}: recordedAt must use YYYY-MM-DD"
        )
    if record["domain"] not in DOMAINS:
        raise RegistryValidationError(f"line {line_number}: unknown domain")

    owner = _validate_pointer(record["owner"], "owner", line_number, artifact=False)
    artifact = _validate_pointer(
        record["artifact"], "artifact", line_number, artifact=True
    )
    if owner["repository"] != artifact["repository"]:
        raise RegistryValidationError(
            f"line {line_number}: artifact repository must match owner repository"
        )
    related_artifacts = record.get("relatedArtifacts", [])
    if "relatedArtifacts" in record and (
        not isinstance(related_artifacts, list) or not related_artifacts
    ):
        raise RegistryValidationError(
            f"line {line_number}: relatedArtifacts must be a nonempty array"
        )
    artifact_paths = {artifact["path"]}
    for index, related in enumerate(related_artifacts):
        related_field = f"relatedArtifacts[{index}]"
        related = _validate_pointer(
            related, related_field, line_number, artifact=True
        )
        if owner["repository"] != related["repository"]:
            raise RegistryValidationError(
                f"line {line_number}: {related_field} repository must match owner repository"
            )
        if related["path"] in artifact_paths:
            raise RegistryValidationError(
                f"line {line_number}: duplicate artifact path {related['path']}"
            )
        artifact_paths.add(related["path"])

    _require_string(record["hypothesis"], "hypothesis", line_number)
    _require_string(record["claimBoundary"], "claimBoundary", line_number)

    method_ids = record["methodIds"]
    if not isinstance(method_ids, list) or not method_ids:
        raise RegistryValidationError(
            f"line {line_number}: methodIds must be a nonempty array"
        )
    if len(method_ids) != len(set(method_ids)) or not set(method_ids) <= METHOD_IDS:
        raise RegistryValidationError(
            f"line {line_number}: methodIds contain duplicates or unknown values"
        )
    if record["status"] not in STATUSES:
        raise RegistryValidationError(f"line {line_number}: unknown status")

    rewards = record["rewardComponents"]
    if not isinstance(rewards, list) or not rewards:
        raise RegistryValidationError(
            f"line {line_number}: rewardComponents must be a nonempty array"
        )
    reward_ids: set[str] = set()
    for index, reward in enumerate(rewards):
        reward_field = f"rewardComponents[{index}]"
        expected_reward_fields = {"id", "type", "role", "description"}
        if not isinstance(reward, dict) or set(reward) != expected_reward_fields:
            raise RegistryValidationError(
                f"line {line_number}: {reward_field} has invalid fields"
            )
        reward_id = _require_string(reward["id"], f"{reward_field}.id", line_number)
        if not ID_PATTERN.fullmatch(reward_id) or reward_id in reward_ids:
            raise RegistryValidationError(
                f"line {line_number}: {reward_field}.id is invalid or duplicated"
            )
        reward_ids.add(reward_id)
        if reward["type"] not in REWARD_TYPES or reward["role"] not in REWARD_ROLES:
            raise RegistryValidationError(
                f"line {line_number}: {reward_field} has unknown type or role"
            )
        _require_string(
            reward["description"], f"{reward_field}.description", line_number
        )

    next_gate = record["nextGate"]
    if not isinstance(next_gate, list) or not next_gate:
        raise RegistryValidationError(
            f"line {line_number}: nextGate must be a nonempty array"
        )
    for index, gate in enumerate(next_gate):
        _require_string(gate, f"nextGate[{index}]", line_number)
    return record


def _verify_artifact(
    record: dict[str, Any], line_number: int, workspace_root: Path
) -> None:
    for artifact in [record["artifact"], *record.get("relatedArtifacts", [])]:
        repository_name = artifact["repository"].rsplit("/", 1)[1]
        repository_root = workspace_root / repository_name
        if not repository_root.is_dir():
            continue
        artifact_path = repository_root / artifact["path"]
        git_repository = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
        if git_repository.returncode == 0 and git_repository.stdout.strip() == "true":
            revision_path = f'{artifact["revision"]}:{artifact["path"]}'
            historical = subprocess.run(
                ["git", "-C", str(repository_root), "show", revision_path],
                check=False,
                capture_output=True,
            )
            if historical.returncode != 0:
                raise RegistryValidationError(
                    f"line {line_number}: artifact does not exist at recorded revision: "
                    f"{artifact['repository']}@{revision_path}"
                )
            artifact_bytes = historical.stdout
            identity = f"{artifact['repository']}@{revision_path}"
        else:
            if not artifact_path.is_file():
                raise RegistryValidationError(
                    f"line {line_number}: available artifact does not exist: {artifact_path}"
                )
            artifact_bytes = artifact_path.read_bytes()
            identity = str(artifact_path)
        digest = hashlib.sha256(artifact_bytes).hexdigest()
        if digest != artifact["sha256"]:
            raise RegistryValidationError(
                f"line {line_number}: artifact hash mismatch for {identity}"
            )


def validate_register(
    path: Path = DEFAULT_REGISTER,
    *,
    workspace_root: Path | None = None,
    verify_available_artifacts: bool = True,
) -> list[dict[str, Any]]:
    """Validate a JSONL register, duplicate IDs, and locally available artifacts."""
    root = workspace_root or REPO_ROOT.parent
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            parsed = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise RegistryValidationError(
                f"line {line_number}: invalid JSON: {error.msg}"
            ) from error
        record = validate_record(parsed, line_number)
        experiment_id = record["experimentId"]
        if experiment_id in seen_ids:
            raise RegistryValidationError(
                f"line {line_number}: duplicate experimentId {experiment_id}"
            )
        seen_ids.add(experiment_id)
        if verify_available_artifacts:
            _verify_artifact(record, line_number, root)
        records.append(record)
    if not records:
        raise RegistryValidationError("register must contain at least one record")
    return records


def _schema_enums() -> dict[str, set[str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    properties = schema["properties"]
    return {
        "domains": set(properties["domain"]["enum"]),
        "methods": set(properties["methodIds"]["items"]["enum"]),
        "statuses": set(properties["status"]["enum"]),
        "reward_types": set(
            properties["rewardComponents"]["items"]["properties"]["type"]["enum"]
        ),
        "reward_roles": set(
            properties["rewardComponents"]["items"]["properties"]["role"]["enum"]
        ),
    }


def validate_schema_alignment() -> None:
    """Keep the dependency-free validator enums aligned with the JSON Schema."""
    enums = _schema_enums()
    expected = {
        "domains": DOMAINS,
        "methods": METHOD_IDS,
        "statuses": STATUSES,
        "reward_types": REWARD_TYPES,
        "reward_roles": REWARD_ROLES,
    }
    if enums != expected:
        raise RegistryValidationError("validator enums do not match JSON Schema")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--workspace-root", type=Path, default=REPO_ROOT.parent)
    parser.add_argument(
        "--skip-artifact-hashes",
        action="store_true",
        help="validate pointers without checking artifacts available in the workspace",
    )
    args = parser.parse_args()
    try:
        validate_schema_alignment()
        records = validate_register(
            args.register,
            workspace_root=args.workspace_root,
            verify_available_artifacts=not args.skip_artifact_hashes,
        )
    except (OSError, RegistryValidationError) as error:
        print(f"[experiment-register] error: {error}")
        return 1
    print(f"[experiment-register] ok: {len(records)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
