#!/usr/bin/env python3
"""Recover an interrupted qm8 terminal-dispatch activation transaction."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_full_qm8_terminal_dispatch_activate as dispatcher
import cmix_filebacked_fxcm_qm8_terminal_closure as closure


PROJECT = Path(__file__).resolve().parents[1]
RESULT = PROJECT / "results/cmix_filebacked_fxcm_full_a_qm8_v1"
PLAN_ROOT = PROJECT / "operations/planning"
RECOVERY_CONTRACT = (
    PLAN_ROOT
    / "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_recovery_q0_v1.json"
)
PREPARATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-recovery-preparation.schema.json"
)
COMPLETION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-recovery-completion.schema.json"
)
FINALIZATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-recovery-finalization.schema.json"
)
PYTHON = Path("/usr/bin/python3.14")


@dataclass(frozen=True)
class TransactionPaths:
    transaction_id: str
    preparation: Path
    archived_intent: Path
    aborted_activated_plan: Path
    completion: Path
    finalization: Path

    @classmethod
    def from_id(cls, transaction_id: str) -> "TransactionPaths":
        prefix = RESULT / f"terminal-dispatch-recovery-{transaction_id}"
        return cls(
            transaction_id=transaction_id,
            preparation=prefix.with_name(f"{prefix.name}-preparation.json"),
            archived_intent=prefix.with_name(
                f"{prefix.name}-dispatch-intent.json"
            ),
            aborted_activated_plan=prefix.with_name(
                f"{prefix.name}-aborted-activated-plan.json"
            ),
            completion=prefix.with_name(f"{prefix.name}-completion.json"),
            finalization=prefix.with_name(f"{prefix.name}-finalization.json"),
        )


def load_json(path: Path, label: str) -> dict[str, Any]:
    raw = closure.read_regular_file(path, label)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def validate_json(
    value: dict[str, Any], schema_path: Path, label: str
) -> None:
    schema = load_json(schema_path, f"{label} schema")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def artifact(path: Path) -> dict[str, Any]:
    return closure.artifact(path)


def same_artifact(left: Any, right: Any) -> bool:
    return (
        isinstance(left, dict)
        and isinstance(right, dict)
        and set(left) == {"path", "bytes", "sha256"}
        and set(right) == {"path", "bytes", "sha256"}
        and Path(left["path"]).absolute() == Path(right["path"]).absolute()
        and left["bytes"] == right["bytes"]
        and left["sha256"] == right["sha256"]
    )


def same_content(record: Any, expected: Any) -> bool:
    return (
        isinstance(record, dict)
        and isinstance(expected, dict)
        and set(record) == {"path", "bytes", "sha256"}
        and set(expected) == {"path", "bytes", "sha256"}
        and record["bytes"] == expected["bytes"]
        and record["sha256"] == expected["sha256"]
    )


def read_record_at(record: Any, path: Path, label: str) -> bytes:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} record is malformed")
    raw = closure.read_regular_file(path, label)
    if len(raw) != record["bytes"] or closure.sha256_bytes(raw) != record["sha256"]:
        raise RuntimeError(f"{label} content does not match its record")
    return raw


def optional_artifact(path: Path) -> dict[str, Any] | None:
    if path.exists() or path.is_symlink():
        return artifact(path)
    return None


def static_binding(record: Any, expected: Path, label: str) -> None:
    closure.static_binding(record, expected, label)


def validate_recovery_contract() -> dict[str, Any]:
    value = load_json(RECOVERY_CONTRACT, "qm8 terminal-dispatch recovery contract")
    plan_schema = load_json(dispatcher.PLAN_SCHEMA, "campaign static-contract schema")
    jsonschema.Draft202012Validator.check_schema(plan_schema)
    jsonschema.Draft202012Validator(plan_schema).validate(value)
    contract = value.get("contract", {})
    if (
        value.get("artifact_id")
        != "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_recovery_q0_v1"
        or value.get("revision") != 1
        or value.get("operational_status") != "dormant_dependency"
        or value.get("claim_authority") != "none"
        or contract.get("candidate_id")
        != "cmix_filebacked_fxcm_full_a_qm8_v1"
        or contract.get("execution_authority") is not False
        or contract.get("verifier_execution_authority") is not False
        or contract.get("arm_b_authority") is not False
        or contract.get("memory_safe_parent_qualification_authority") is not False
        or contract.get("gamma_compression_credit_bytes") != 0
        or contract.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("qm8 terminal-dispatch recovery authority drift")
    expected = {
        "recovery_tool": Path(__file__).resolve(strict=True),
        "closure_helper": Path(closure.__file__).resolve(strict=True),
        "dispatcher": Path(dispatcher.__file__).resolve(strict=True),
        "dispatch_contract": dispatcher.ACTIVATION_CONTRACT,
        "plan_schema": dispatcher.PLAN_SCHEMA,
        "roundtrip_schema": closure.ROUNDTRIP_SCHEMA,
        "intent_schema": dispatcher.INTENT_SCHEMA,
        "activation_schema": dispatcher.RECEIPT_SCHEMA,
        "preparation_schema": PREPARATION_SCHEMA,
        "completion_schema": COMPLETION_SCHEMA,
        "finalization_schema": FINALIZATION_SCHEMA,
        "python_runtime": PYTHON,
    }
    for name, path in expected.items():
        static_binding(contract.get(name), path, name)
    dormant = contract.get("dormant_plans", {})
    for branch in dispatcher.BRANCHES.values():
        record = dormant.get(branch["name"])
        frozen_path = str(branch["plan"].relative_to(PROJECT))
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "bytes", "sha256"}
            or record["path"] != frozen_path
            or isinstance(record["bytes"], bool)
            or not isinstance(record["bytes"], int)
            or record["bytes"] < 1
            or record["sha256"] != branch["plan_sha256"]
        ):
            raise RuntimeError(f"{branch['name']} frozen-plan recovery binding drift")
    expected_command = [
        str(PYTHON),
        "tools/cmix_filebacked_fxcm_full_qm8_terminal_dispatch_recover.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
    ]
    if contract.get("command") != expected_command:
        raise RuntimeError("qm8 terminal-dispatch recovery command drift")
    return value


def dispatch_contract(recovery: dict[str, Any]) -> dict[str, Any]:
    record = recovery["contract"]["dispatch_contract"]
    raw = closure.static_binding(
        record,
        dispatcher.ACTIVATION_CONTRACT,
        "frozen terminal-dispatch activation contract",
    )
    value = json.loads(raw)
    plan_schema = load_json(dispatcher.PLAN_SCHEMA, "campaign static-contract schema")
    jsonschema.Draft202012Validator(plan_schema).validate(value)
    return value


def plan_paths(branch: str) -> tuple[dict[str, Any], dict[str, Any]]:
    terminal_pass = branch == "success"
    return dispatcher.BRANCHES[terminal_pass], dispatcher.BRANCHES[not terminal_pass]


def frozen_plan_record(
    dispatch: dict[str, Any], branch: str
) -> dict[str, Any]:
    record = dispatch["contract"]["dormant_plans"].get(branch)
    if not isinstance(record, dict):
        raise RuntimeError(f"missing frozen {branch} plan record")
    return record


def validate_plan_content(
    raw: bytes,
    expected_record: dict[str, Any],
    expected_path: Path,
    label: str,
) -> dict[str, Any]:
    if len(raw) != expected_record["bytes"] or closure.sha256_bytes(raw) != expected_record["sha256"]:
        raise RuntimeError(f"{label} identity mismatch")
    declared = Path(expected_record["path"])
    declared = declared if declared.is_absolute() else PROJECT / declared
    if declared.absolute() != expected_path.absolute():
        raise RuntimeError(f"{label} frozen path mismatch")
    value = json.loads(raw)
    schema = load_json(dispatcher.PLAN_SCHEMA, "campaign static-contract schema")
    jsonschema.Draft202012Validator(schema).validate(value)
    return value


def find_dormant_raw(
    selected: Path,
    frozen: dict[str, Any],
) -> bytes:
    for path in (selected, dispatcher.DISPLACED_DORMANT):
        if path.exists() or path.is_symlink():
            raw = closure.read_regular_file(path, "selected dormant-plan candidate")
            if len(raw) == frozen["bytes"] and closure.sha256_bytes(raw) == frozen["sha256"]:
                return raw
    raise RuntimeError("exact selected dormant-plan bytes are not recoverable")


def validate_intent(
    raw: bytes,
    witness: closure.ReceiptWitness,
    dispatch: dict[str, Any],
) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("terminal-dispatch intent is not an object")
    validate_json(value, dispatcher.INTENT_SCHEMA, "terminal-dispatch intent")
    branch = value["branch"]
    selected, non_selected = plan_paths(branch)
    selected_frozen = frozen_plan_record(dispatch, branch)
    non_selected_frozen = frozen_plan_record(
        dispatch, "failure" if branch == "success" else "success"
    )
    if (
        value["terminal_pass"] is not (branch == "success")
        or value["terminal_pass"] is not witness.value["terminal_pass"]
        or value["terminal_receipt"] != witness.record()
        or not same_artifact(value["dispatch_contract"], artifact(dispatcher.ACTIVATION_CONTRACT))
        or value["displaced_dormant_plan_path"]
        != str(dispatcher.DISPLACED_DORMANT)
        or value["planning_lock"]["path"] != str(dispatcher.PLAN_LOCK)
        or value["full1g_lock"]["path"] != str(closure.LEASE_LOCK)
        or value["verifier_executed"] is not False
        or value["arm_b_authorized"] is not False
        or value["gamma_compression_credit_bytes"] != 0
        or value["gamma_score_credit_bytes"] != 0
    ):
        raise RuntimeError("terminal-dispatch intent semantic mismatch")
    if not closure.runtime_record_matches_static(
        value["non_selected_plan"],
        non_selected_frozen,
        non_selected["plan"],
        "non-selected terminal plan",
    ):
        raise RuntimeError("non-selected plan no longer matches the frozen plan")
    if not same_content(value["dormant_plan"], selected_frozen):
        raise RuntimeError("selected dormant-plan intent binding mismatch")
    if Path(value["dormant_plan"]["path"]).absolute() != selected["plan"].absolute():
        raise RuntimeError("selected dormant-plan path mismatch")
    dormant_raw = find_dormant_raw(selected["plan"], selected_frozen)
    dormant = validate_plan_content(
        dormant_raw, selected_frozen, selected["plan"], "selected dormant plan"
    )
    activated = dispatcher.activated_plan(
        dormant, selected, witness.sha256
    )
    if value["expected_activated_plan"] != dispatcher.expected_plan_record(
        selected, activated
    ):
        raise RuntimeError("expected activated-plan derivation mismatch")
    closure.validate_closure_record(
        value["closure_before_publication"],
        value["terminal_pass"],
        "terminal-dispatch pre-publication closure",
    )
    return value


@dataclass
class LockWitness:
    record: dict[str, Any]
    path: Path
    descriptor: int
    payload: bytes
    released: bool = False

    @classmethod
    def open(cls, record: Any, expected: Path, label: str) -> "LockWitness":
        if not isinstance(record, dict) or set(record) != {
            "path", "device", "inode", "payload_sha256"
        }:
            raise RuntimeError(f"{label} lock record is malformed")
        if Path(record["path"]).absolute() != expected.absolute():
            raise RuntimeError(f"{label} lock path mismatch")
        path = closure.regular(expected, label)
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            payload = closure.read_fd(descriptor)
            current = path.lstat()
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or current.st_dev != metadata.st_dev
                or current.st_ino != metadata.st_ino
                or current.st_nlink != 1
                or metadata.st_dev != record["device"]
                or metadata.st_ino != record["inode"]
                or closure.sha256_bytes(payload) != record["payload_sha256"]
            ):
                raise RuntimeError(f"{label} lock identity mismatch")
        except Exception:
            os.close(descriptor)
            raise
        return cls(record=record, path=path, descriptor=descriptor, payload=payload)

    def verify(self) -> None:
        current = self.path.lstat()
        metadata = os.fstat(self.descriptor)
        if (
            current.st_dev != self.record["device"]
            or current.st_ino != self.record["inode"]
            or current.st_nlink != 1
            or metadata.st_dev != self.record["device"]
            or metadata.st_ino != self.record["inode"]
            or closure.read_fd(self.descriptor) != self.payload
        ):
            raise RuntimeError(f"recovered lock identity changed: {self.path}")

    def release(self) -> dict[str, Any]:
        self.verify()
        self.path.unlink()
        closure.fsync_directory(self.path.parent)
        os.close(self.descriptor)
        self.released = True
        return {
            "path": str(self.path),
            "device": self.record["device"],
            "inode": self.record["inode"],
            "disposition": "released_by_recovery",
        }

    def close(self) -> None:
        if not self.released:
            os.close(self.descriptor)


def lock_payloads(
    planning: LockWitness,
    full1g: LockWitness,
    intent: dict[str, Any],
    witness: closure.ReceiptWitness,
) -> int:
    planning_value = json.loads(planning.payload)
    full_owner = full_lock_owner(full1g, witness)
    owner = planning_value.get("owner_pid")
    if (
        not isinstance(owner, int)
        or isinstance(owner, bool)
        or owner < 1
        or full_owner != owner
        or planning_value.get("branch") != intent["branch"]
        or planning_value.get("receipt_sha256") != witness.sha256
        or set(planning_value) != {"branch", "owner_pid", "receipt_sha256"}
    ):
        raise RuntimeError("preserved terminal-dispatch lock payload mismatch")
    if (Path("/proc") / str(owner)).exists():
        raise RuntimeError("terminal-dispatch lock owner PID is still live or reused")
    return owner


def full_lock_owner(
    full1g: LockWitness, witness: closure.ReceiptWitness
) -> int:
    full_value = json.loads(full1g.payload)
    owner = full_value.get("owner_pid")
    if (
        not isinstance(owner, int)
        or isinstance(owner, bool)
        or owner < 1
        or full_value.get("purpose") != "qm8_terminal_dispatch_activation"
        or full_value.get("terminal_receipt_sha256") != witness.sha256
        or set(full_value)
        != {"owner_pid", "purpose", "terminal_receipt_sha256"}
    ):
        raise RuntimeError("preserved full-1G lock payload mismatch")
    if (Path("/proc") / str(owner)).exists():
        raise RuntimeError("terminal-dispatch lock owner PID is still live or reused")
    return owner


def transaction_paths_for_intent(raw: bytes) -> TransactionPaths:
    transaction_id = closure.sha256_bytes(raw)
    return TransactionPaths.from_id(transaction_id)


def incomplete_preparations() -> list[Path]:
    candidates: list[Path] = []
    pattern = "terminal-dispatch-recovery-*-preparation.json"
    for path in sorted(RESULT.glob(pattern)):
        name = path.name
        transaction_id = name.removeprefix(
            "terminal-dispatch-recovery-"
        ).removesuffix("-preparation.json")
        if len(transaction_id) != 64:
            continue
        paths = TransactionPaths.from_id(transaction_id)
        if not paths.finalization.exists() and not paths.finalization.is_symlink():
            candidates.append(path)
    return candidates


def locate_transaction(
    witness: closure.ReceiptWitness,
) -> tuple[TransactionPaths, bytes | None]:
    if dispatcher.INTENT.exists() or dispatcher.INTENT.is_symlink():
        raw = closure.read_regular_file(
            dispatcher.INTENT, "terminal-dispatch activation intent"
        )
        return transaction_paths_for_intent(raw), raw
    matches: list[TransactionPaths] = []
    for path in incomplete_preparations():
        value = load_json(path, "incomplete recovery preparation")
        try:
            validate_json(value, PREPARATION_SCHEMA, "recovery preparation")
        except (jsonschema.ValidationError, RuntimeError):
            continue
        if value.get("terminal_receipt") == witness.record():
            matches.append(TransactionPaths.from_id(value["transaction_id"]))
    if len(matches) != 1:
        raise RuntimeError(
            "recovery requires one canonical dispatch intent or one unique incomplete preparation"
        )
    return matches[0], None


def load_intent_raw(
    paths: TransactionPaths,
    preparation: dict[str, Any] | None,
    canonical_raw: bytes | None,
) -> bytes:
    if canonical_raw is not None:
        if paths.archived_intent.exists() or paths.archived_intent.is_symlink():
            raise RuntimeError("canonical and archived dispatch intents both exist")
        return canonical_raw
    if preparation is None:
        raise RuntimeError("recovery preparation is required after intent archival")
    return read_record_at(
        preparation["dispatch_intent"],
        paths.archived_intent,
        "archived terminal-dispatch intent",
    )


def plan_kind(
    path: Path,
    dormant: dict[str, Any],
    activated: dict[str, Any],
    label: str,
) -> str | None:
    if not path.exists() and not path.is_symlink():
        return None
    record = artifact(path)
    if same_content(record, dormant):
        return "dormant"
    if same_content(record, activated):
        return "activated"
    raise RuntimeError(f"{label} has an unknown identity")


def initial_action(
    witness: closure.ReceiptWitness,
    intent: dict[str, Any],
    dispatch: dict[str, Any],
) -> str:
    branch = intent["branch"]
    selected, _ = plan_paths(branch)
    dormant = frozen_plan_record(dispatch, branch)
    activated = intent["expected_activated_plan"]
    selected_kind = plan_kind(
        selected["plan"], dormant, activated, "selected terminal plan"
    )
    displaced_kind = plan_kind(
        dispatcher.DISPLACED_DORMANT,
        dormant,
        activated,
        "displaced terminal plan",
    )
    activation_present = (
        dispatcher.ACTIVATION_RECEIPT.exists()
        or dispatcher.ACTIVATION_RECEIPT.is_symlink()
    )
    if activation_present:
        if selected_kind != "activated" or displaced_kind != "dormant":
            raise RuntimeError("committed activation has inconsistent plan state")
        closure.validate_dispatch_activation(
            witness,
            branch,
            selected["plan"],
            plan_paths(branch)[1]["plan"],
        )
        return "finalize_committed_activation"
    allowed = {
        ("dormant", None),
        ("activated", "dormant"),
        ("dormant", "activated"),
    }
    if (selected_kind, displaced_kind) not in allowed:
        raise RuntimeError("uncommitted activation is not in a recoverable plan state")
    return "rollback_uncommitted_activation"


def create_preparation(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    recovery: dict[str, Any],
    intent: dict[str, Any],
    action: str,
    owner_pid: int,
    lock_presence: dict[str, bool],
    closure_record: dict[str, Any],
) -> dict[str, Any]:
    selected, non_selected = plan_paths(intent["branch"])
    value = {
        "schema": "gamma.enwiki9.cmix-filebacked-fxcm-qm8-terminal-dispatch-recovery-preparation.v1",
        "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
        "transaction_id": paths.transaction_id,
        "action": action,
        "branch": intent["branch"],
        "terminal_pass": intent["terminal_pass"],
        "terminal_receipt": witness.record(),
        "recovery_contract": artifact(RECOVERY_CONTRACT),
        "dispatch_contract": artifact(dispatcher.ACTIVATION_CONTRACT),
        "dispatch_intent": artifact(dispatcher.INTENT),
        "activation_receipt": optional_artifact(dispatcher.ACTIVATION_RECEIPT),
        "selected_plan": artifact(selected["plan"]),
        "displaced_dormant_plan": optional_artifact(dispatcher.DISPLACED_DORMANT),
        "non_selected_plan": artifact(non_selected["plan"]),
        "planning_lock": intent["planning_lock"],
        "full1g_lock": intent["full1g_lock"],
        "lock_presence_at_preparation": lock_presence,
        "dispatch_owner_pid": owner_pid,
        "closure_at_preparation": closure_record,
        "state": "prepared_before_recovery_mutation",
        "verifier_executed": False,
        "arm_b_authorized": False,
        "memory_safe_parent_qualified": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    return dispatcher.write_new_json(
        paths.preparation, value, PREPARATION_SCHEMA
    )


def validate_preparation(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    recovery: dict[str, Any],
    intent: dict[str, Any],
    dispatch: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    value = load_json(paths.preparation, "recovery preparation")
    validate_json(value, PREPARATION_SCHEMA, "recovery preparation")
    if (
        value["transaction_id"] != paths.transaction_id
        or value["branch"] != intent["branch"]
        or value["terminal_pass"] is not intent["terminal_pass"]
        or value["terminal_receipt"] != witness.record()
        or not same_artifact(value["recovery_contract"], artifact(RECOVERY_CONTRACT))
        or not same_artifact(value["dispatch_contract"], artifact(dispatcher.ACTIVATION_CONTRACT))
        or value["dispatch_intent"]["sha256"] != paths.transaction_id
        or Path(value["dispatch_intent"]["path"]).absolute()
        != dispatcher.INTENT.absolute()
        or value["planning_lock"] != intent["planning_lock"]
        or value["full1g_lock"] != intent["full1g_lock"]
    ):
        raise RuntimeError("recovery preparation binding mismatch")
    presence = value["lock_presence_at_preparation"]
    if (
        value["action"] == "rollback_uncommitted_activation"
        and presence != {"planning": True, "full1g": True}
    ) or (
        value["action"] == "finalize_committed_activation"
        and presence
        not in (
            {"planning": True, "full1g": True},
            {"planning": False, "full1g": True},
        )
    ):
        raise RuntimeError("recovery preparation lock-presence mismatch")
    closure.validate_closure_record(
        value["closure_at_preparation"],
        value["terminal_pass"],
        "recovery preparation closure",
    )
    observed_action = initial_action(witness, intent, dispatch)
    if value["action"] != observed_action:
        raise RuntimeError("recovery preparation action no longer matches state")
    return value, artifact(paths.preparation)


def move_exact(
    source: Path,
    destination: Path,
    expected: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    source_present = source.exists() or source.is_symlink()
    destination_present = destination.exists() or destination.is_symlink()
    if source_present and destination_present:
        raise RuntimeError(f"both source and archive exist for {label}")
    if source_present:
        read_record_at(expected, source, label)
        closure.rename_noreplace(source, destination)
        closure.fsync_directory(source.parent)
        if destination.parent != source.parent:
            closure.fsync_directory(destination.parent)
    elif not destination_present:
        raise RuntimeError(f"neither source nor archive exists for {label}")
    read_record_at(expected, destination, f"archived {label}")
    return artifact(destination)


def rollback(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    intent: dict[str, Any],
    dispatch: dict[str, Any],
    preparation_record: dict[str, Any],
) -> dict[str, Any]:
    selected, non_selected = plan_paths(intent["branch"])
    dormant = frozen_plan_record(dispatch, intent["branch"])
    activated = intent["expected_activated_plan"]
    selected_record = artifact(selected["plan"])
    displaced_record = optional_artifact(dispatcher.DISPLACED_DORMANT)
    archived_activated = optional_artifact(paths.aborted_activated_plan)
    if same_content(selected_record, activated) and same_content(displaced_record, dormant):
        dispatcher.rename_exchange(dispatcher.DISPLACED_DORMANT, selected["plan"])
        closure.fsync_directory(PLAN_ROOT)
        selected_record = artifact(selected["plan"])
        displaced_record = artifact(dispatcher.DISPLACED_DORMANT)
    if not same_content(selected_record, dormant):
        raise RuntimeError("rollback did not restore the exact dormant selected plan")
    if displaced_record is not None:
        if not same_content(displaced_record, activated) or archived_activated is not None:
            raise RuntimeError("post-rollback displaced plan identity mismatch")
        archived_activated = move_exact(
            dispatcher.DISPLACED_DORMANT,
            paths.aborted_activated_plan,
            activated,
            "aborted activated plan",
        )
    elif archived_activated is not None and not same_content(
        archived_activated, activated
    ):
        raise RuntimeError("aborted activated-plan archive identity mismatch")
    archived_intent = move_exact(
        dispatcher.INTENT,
        paths.archived_intent,
        preparation_record["dispatch_intent"],
        "terminal-dispatch intent",
    )
    if (
        dispatcher.INTENT.exists()
        or dispatcher.INTENT.is_symlink()
        or dispatcher.DISPLACED_DORMANT.exists()
        or dispatcher.DISPLACED_DORMANT.is_symlink()
        or dispatcher.ACTIVATION_RECEIPT.exists()
        or dispatcher.ACTIVATION_RECEIPT.is_symlink()
    ):
        raise RuntimeError("rollback left a canonical activation artifact")
    if not same_content(artifact(selected["plan"]), dormant):
        raise RuntimeError("selected terminal plan changed after rollback")
    non_selected_record = artifact(non_selected["plan"])
    if not same_content(
        non_selected_record,
        frozen_plan_record(
            dispatch,
            "failure" if intent["branch"] == "success" else "success",
        ),
    ):
        raise RuntimeError("non-selected terminal plan changed during rollback")
    return {
        "dispatch_intent": archived_intent,
        "activated_plan_archive": archived_activated,
        "activation_receipt": None,
        "selected_plan": artifact(selected["plan"]),
        "displaced_dormant_plan": None,
        "non_selected_plan": non_selected_record,
        "state": "rollback_complete_locks_owned",
    }


def committed_state(
    witness: closure.ReceiptWitness,
    intent: dict[str, Any],
) -> dict[str, Any]:
    selected, non_selected = plan_paths(intent["branch"])
    closure.validate_dispatch_activation(
        witness, intent["branch"], selected["plan"], non_selected["plan"]
    )
    return {
        "dispatch_intent": artifact(dispatcher.INTENT),
        "activated_plan_archive": None,
        "activation_receipt": artifact(dispatcher.ACTIVATION_RECEIPT),
        "selected_plan": artifact(selected["plan"]),
        "displaced_dormant_plan": artifact(dispatcher.DISPLACED_DORMANT),
        "non_selected_plan": artifact(non_selected["plan"]),
        "state": "committed_activation_validated_locks_owned",
    }


def create_completion(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    recovery: dict[str, Any],
    preparation: dict[str, Any],
    preparation_artifact: dict[str, Any],
    state: dict[str, Any],
    planning: LockWitness | None,
    full1g: LockWitness,
    closure_record: dict[str, Any],
) -> dict[str, Any]:
    presence = preparation["lock_presence_at_preparation"]
    if planning is not None:
        planning.verify()
    elif presence["planning"]:
        raise RuntimeError("recovery completion lost its planning-lock descriptor")
    elif dispatcher.PLAN_LOCK.exists() or dispatcher.PLAN_LOCK.is_symlink():
        raise RuntimeError("unexpected planning lock appeared during recovery")
    full1g.verify()
    value = {
        "schema": "gamma.enwiki9.cmix-filebacked-fxcm-qm8-terminal-dispatch-recovery-completion.v1",
        "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
        "transaction_id": paths.transaction_id,
        "action": preparation["action"],
        "branch": preparation["branch"],
        "terminal_pass": preparation["terminal_pass"],
        "terminal_receipt": witness.record(),
        "recovery_contract": artifact(RECOVERY_CONTRACT),
        "preparation": preparation_artifact,
        **state,
        "planning_lock": preparation["planning_lock"],
        "full1g_lock": preparation["full1g_lock"],
        "lock_presence_at_publication": presence,
        "closure_at_completion": closure_record,
        "verifier_executed": False,
        "arm_b_authorized": False,
        "memory_safe_parent_qualified": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    return dispatcher.write_new_json(
        paths.completion, value, COMPLETION_SCHEMA
    )


def validate_completion(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    preparation: dict[str, Any],
    preparation_artifact: dict[str, Any],
    intent: dict[str, Any],
    dispatch: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    value = load_json(paths.completion, "recovery completion")
    validate_json(value, COMPLETION_SCHEMA, "recovery completion")
    if (
        value["transaction_id"] != paths.transaction_id
        or value["action"] != preparation["action"]
        or value["branch"] != preparation["branch"]
        or value["terminal_pass"] is not preparation["terminal_pass"]
        or value["terminal_receipt"] != witness.record()
        or value["preparation"] != preparation_artifact
        or value["planning_lock"] != preparation["planning_lock"]
        or value["full1g_lock"] != preparation["full1g_lock"]
        or value["lock_presence_at_publication"]
        != preparation["lock_presence_at_preparation"]
    ):
        raise RuntimeError("recovery completion binding mismatch")
    closure.validate_closure_record(
        value["closure_at_completion"],
        value["terminal_pass"],
        "recovery completion closure",
    )
    if value["action"] == "rollback_uncommitted_activation":
        selected, non_selected = plan_paths(value["branch"])
        read_record_at(
            value["dispatch_intent"],
            paths.archived_intent,
            "archived dispatch intent",
        )
        if value["dispatch_intent"]["sha256"] != paths.transaction_id:
            raise RuntimeError("archived dispatch-intent transaction mismatch")
        if value["activated_plan_archive"] is not None:
            read_record_at(
                value["activated_plan_archive"],
                paths.aborted_activated_plan,
                "aborted activated-plan archive",
            )
            if not same_content(
                value["activated_plan_archive"],
                intent["expected_activated_plan"],
            ):
                raise RuntimeError("aborted activated-plan archive mismatch")
        closure.read_bound_artifact(
            value["selected_plan"], selected["plan"], "restored selected plan"
        )
        closure.read_bound_artifact(
            value["non_selected_plan"],
            non_selected["plan"],
            "non-selected plan",
        )
        if not same_content(
            value["selected_plan"],
            frozen_plan_record(dispatch, value["branch"]),
        ) or not same_content(
            value["non_selected_plan"],
            frozen_plan_record(
                dispatch,
                "failure" if value["branch"] == "success" else "success",
            ),
        ):
            raise RuntimeError("completed rollback plan identity mismatch")
        if (
            dispatcher.INTENT.exists()
            or dispatcher.INTENT.is_symlink()
            or dispatcher.DISPLACED_DORMANT.exists()
            or dispatcher.DISPLACED_DORMANT.is_symlink()
            or dispatcher.ACTIVATION_RECEIPT.exists()
            or dispatcher.ACTIVATION_RECEIPT.is_symlink()
        ):
            raise RuntimeError("completed rollback canonical state drift")
    else:
        selected, non_selected = plan_paths(value["branch"])
        closure.validate_dispatch_activation(
            witness, value["branch"], selected["plan"], non_selected["plan"]
        )
    return value, artifact(paths.completion)


def lock_absent_observation(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": record["path"],
        "device": record["device"],
        "inode": record["inode"],
        "disposition": "already_absent_after_completion",
    }


def release_one(record: dict[str, Any], expected: Path, label: str) -> dict[str, Any]:
    if not expected.exists() and not expected.is_symlink():
        return lock_absent_observation(record)
    lock = LockWitness.open(record, expected, label)
    try:
        return lock.release()
    finally:
        lock.close()


def create_finalization(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    preparation: dict[str, Any],
    completion_artifact: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        dispatcher.PLAN_LOCK.exists()
        or dispatcher.PLAN_LOCK.is_symlink()
        or closure.LEASE_LOCK.exists()
        or closure.LEASE_LOCK.is_symlink()
    ):
        raise RuntimeError("recovery lock path remains occupied")
    value = {
        "schema": "gamma.enwiki9.cmix-filebacked-fxcm-qm8-terminal-dispatch-recovery-finalization.v1",
        "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
        "transaction_id": paths.transaction_id,
        "action": preparation["action"],
        "branch": preparation["branch"],
        "terminal_pass": preparation["terminal_pass"],
        "terminal_receipt": witness.record(),
        "recovery_contract": artifact(RECOVERY_CONTRACT),
        "completion": completion_artifact,
        "planning_lock": preparation["planning_lock"],
        "full1g_lock": preparation["full1g_lock"],
        "lock_release_observations": observations,
        "state": "recovery_complete_locks_absent",
        "verifier_executed": False,
        "arm_b_authorized": False,
        "memory_safe_parent_qualified": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    return dispatcher.write_new_json(
        paths.finalization, value, FINALIZATION_SCHEMA
    )


def validate_finalization(
    paths: TransactionPaths,
    witness: closure.ReceiptWitness,
    preparation: dict[str, Any],
    completion_artifact: dict[str, Any],
) -> dict[str, Any]:
    value = load_json(paths.finalization, "recovery finalization")
    validate_json(value, FINALIZATION_SCHEMA, "recovery finalization")
    if (
        value["transaction_id"] != paths.transaction_id
        or value["action"] != preparation["action"]
        or value["branch"] != preparation["branch"]
        or value["terminal_pass"] is not preparation["terminal_pass"]
        or value["terminal_receipt"] != witness.record()
        or value["completion"] != completion_artifact
        or value["planning_lock"] != preparation["planning_lock"]
        or value["full1g_lock"] != preparation["full1g_lock"]
        or dispatcher.PLAN_LOCK.exists()
        or dispatcher.PLAN_LOCK.is_symlink()
        or closure.LEASE_LOCK.exists()
        or closure.LEASE_LOCK.is_symlink()
    ):
        raise RuntimeError("recovery finalization binding mismatch")
    if not same_artifact(value["recovery_contract"], artifact(RECOVERY_CONTRACT)):
        raise RuntimeError("recovery finalization contract binding mismatch")
    for observation, record in zip(
        value["lock_release_observations"],
        (preparation["planning_lock"], preparation["full1g_lock"]),
        strict=True,
    ):
        if (
            observation["path"] != record["path"]
            or observation["device"] != record["device"]
            or observation["inode"] != record["inode"]
        ):
            raise RuntimeError("recovery lock-release observation mismatch")
    return artifact(paths.finalization)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    expected_command = [
        str(PYTHON),
        "tools/cmix_filebacked_fxcm_full_qm8_terminal_dispatch_recover.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
    ]
    actual_command = [str(Path(sys.executable).resolve(strict=True)), *sys.argv]
    if actual_command != expected_command:
        raise SystemExit("terminal-dispatch recovery requires the frozen command and runtime")

    recovery = validate_recovery_contract()
    dispatch = dispatch_contract(recovery)
    with closure.open_terminal_receipt(args.receipt) as witness:
        paths, canonical_raw = locate_transaction(witness)
        preparation: dict[str, Any] | None = None
        if paths.preparation.exists() or paths.preparation.is_symlink():
            preparation = load_json(paths.preparation, "recovery preparation")
            validate_json(preparation, PREPARATION_SCHEMA, "recovery preparation")
        intent_raw = load_intent_raw(paths, preparation, canonical_raw)
        if closure.sha256_bytes(intent_raw) != paths.transaction_id:
            raise RuntimeError("recovery transaction ID does not match dispatch intent")
        intent = validate_intent(intent_raw, witness, dispatch)

        if paths.finalization.exists() or paths.finalization.is_symlink():
            if preparation is None:
                raise RuntimeError("finalized recovery lacks its preparation")
            preparation, preparation_artifact = validate_preparation(
                paths, witness, recovery, intent, dispatch
            )
            _, completion_artifact = validate_completion(
                paths,
                witness,
                preparation,
                preparation_artifact,
                intent,
                dispatch,
            )
            finalization_artifact = validate_finalization(
                paths, witness, preparation, completion_artifact
            )
        else:
            if preparation is None:
                action = initial_action(witness, intent, dispatch)
                planning_present = (
                    dispatcher.PLAN_LOCK.exists()
                    or dispatcher.PLAN_LOCK.is_symlink()
                )
                full1g_present = (
                    closure.LEASE_LOCK.exists()
                    or closure.LEASE_LOCK.is_symlink()
                )
                if action == "rollback_uncommitted_activation" and not (
                    planning_present and full1g_present
                ):
                    raise RuntimeError("rollback requires both exact dispatch locks")
                if action == "finalize_committed_activation" and (
                    not full1g_present
                    or (planning_present and not full1g_present)
                ):
                    raise RuntimeError(
                        "committed recovery requires the surviving full-1G lock"
                    )
                planning: LockWitness | None = None
                if planning_present:
                    planning = LockWitness.open(
                        intent["planning_lock"],
                        dispatcher.PLAN_LOCK,
                        "planning",
                    )
                try:
                    full1g = LockWitness.open(
                        intent["full1g_lock"], closure.LEASE_LOCK, "full-1G"
                    )
                    try:
                        owner_pid = (
                            lock_payloads(planning, full1g, intent, witness)
                            if planning is not None
                            else full_lock_owner(full1g, witness)
                        )
                        recovery_closure = closure.closure_snapshot(
                            witness.value, intent["terminal_pass"], full1g
                        )
                        create_preparation(
                            paths,
                            witness,
                            recovery,
                            intent,
                            action,
                            owner_pid,
                            {
                                "planning": planning is not None,
                                "full1g": True,
                            },
                            recovery_closure,
                        )
                    finally:
                        full1g.close()
                finally:
                    if planning is not None:
                        planning.close()
            preparation, preparation_artifact = validate_preparation(
                paths, witness, recovery, intent, dispatch
            )
            owner_pid = preparation["dispatch_owner_pid"]
            if (Path("/proc") / str(owner_pid)).exists():
                raise RuntimeError("terminal-dispatch owner PID is live or reused")

            if not paths.completion.exists() and not paths.completion.is_symlink():
                presence = preparation["lock_presence_at_preparation"]
                planning = None
                if presence["planning"]:
                    planning = LockWitness.open(
                        preparation["planning_lock"],
                        dispatcher.PLAN_LOCK,
                        "planning",
                    )
                elif dispatcher.PLAN_LOCK.exists() or dispatcher.PLAN_LOCK.is_symlink():
                    raise RuntimeError(
                        "unexpected planning lock appeared after recovery preparation"
                    )
                try:
                    full1g = LockWitness.open(
                        preparation["full1g_lock"],
                        closure.LEASE_LOCK,
                        "full-1G",
                    )
                    try:
                        if planning is not None:
                            lock_payloads(planning, full1g, intent, witness)
                        elif full_lock_owner(full1g, witness) != owner_pid:
                            raise RuntimeError("full-1G recovery owner changed")
                        recovery_closure = closure.closure_snapshot(
                            witness.value, intent["terminal_pass"], full1g
                        )
                        if (
                            preparation["action"]
                            == "rollback_uncommitted_activation"
                        ):
                            state = rollback(
                                paths,
                                witness,
                                intent,
                                dispatch,
                                preparation,
                            )
                        else:
                            state = committed_state(witness, intent)
                        create_completion(
                            paths,
                            witness,
                            recovery,
                            preparation,
                            preparation_artifact,
                            state,
                            planning,
                            full1g,
                            recovery_closure,
                        )
                    finally:
                        full1g.close()
                finally:
                    if planning is not None:
                        planning.close()
            _, completion_artifact = validate_completion(
                paths,
                witness,
                preparation,
                preparation_artifact,
                intent,
                dispatch,
            )
            observations = [
                release_one(
                    preparation["planning_lock"], dispatcher.PLAN_LOCK, "planning"
                ),
                release_one(
                    preparation["full1g_lock"], closure.LEASE_LOCK, "full-1G"
                ),
            ]
            finalization_artifact = create_finalization(
                paths,
                witness,
                preparation,
                completion_artifact,
                observations,
            )

        result = {
            "event": "qm8_terminal_dispatch_recovery_finalized",
            "transaction_id": paths.transaction_id,
            "action": preparation["action"],
            "branch": preparation["branch"],
            "terminal_pass": preparation["terminal_pass"],
            "finalization": finalization_artifact,
            "verifier_executed": False,
            "arm_b_authorized": False,
            "memory_safe_parent_qualified": False,
            "gamma_compression_credit_bytes": 0,
            "gamma_score_credit_bytes": 0,
        }
        sys.stdout.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
