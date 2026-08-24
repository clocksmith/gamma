#!/usr/bin/env python3
"""Activate exactly one qm8 terminal-verification branch without executing it."""

from __future__ import annotations

import argparse
import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_qm8_terminal_closure as closure


PROJECT = Path(__file__).resolve().parents[1]
RESULT = PROJECT / "results/cmix_filebacked_fxcm_full_a_qm8_v1"
PLAN_ROOT = PROJECT / "operations/planning"
PLAN_SCHEMA = PLAN_ROOT / "campaign-static-contract.schema.json"
ACTIVATION_CONTRACT = (
    PLAN_ROOT
    / "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_activation_q0_v1.json"
)
INTENT_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-intent.schema.json"
)
RECEIPT_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-activation.schema.json"
)
PLAN_LOCK = (
    PLAN_ROOT / "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch.activation.lock"
)
INTENT = RESULT / "terminal-dispatch-activation-intent.json"
ACTIVATION_RECEIPT = RESULT / "terminal-dispatch-activation-receipt.json"
DISPLACED_DORMANT = (
    PLAN_ROOT
    / ".cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch.displaced-dormant.json"
)
PYTHON = Path("/usr/bin/python3.14")
RESEARCH_CONTRACTS = PROJECT / "tools/research_contracts.py"
ALLOWED_CHANGES = {
    "revision",
    "contract.activation.status",
    "contract.activation.execution_authorized",
    "contract.activation.terminal_receipt_sha256",
}

BRANCHES = {
    True: {
        "name": "success",
        "plan": PLAN_ROOT
        / "cmix_filebacked_fxcm_full_a_qm8_soft_high_verification_v1.json",
        "plan_sha256": "dfd11217037b8f5df421a6ef776dee90b39ddb5f2e543c279418846da45ba5f8",
        "artifact_id": "cmix_filebacked_fxcm_full_a_qm8_soft_high_verification_v1",
        "waiting_status": "waiting_for_terminal_passing_qm8",
        "activated_status": "activated_after_terminal_passing_qm8",
        "output": RESULT / "full-soft-high-verification.json",
    },
    False: {
        "name": "failure",
        "plan": PLAN_ROOT
        / "cmix_filebacked_fxcm_full_a_qm8_failure_verification_v1.json",
        "plan_sha256": "2a4cb99a02962b73e215b762ca3d3cea109911c08cd569888b8382431808d5d8",
        "artifact_id": "cmix_filebacked_fxcm_full_a_qm8_failure_verification_v1",
        "waiting_status": "waiting_for_terminal_failed_qm8",
        "activated_status": "activated_after_terminal_failed_qm8",
        "output": RESULT / "full-terminal-failure-verification.json",
    },
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def regular(path: Path, label: str) -> Path:
    return closure.regular(path, label)


def artifact(path: Path) -> dict[str, Any]:
    path = regular(path, "artifact")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def load_json(path: Path, label: str) -> dict[str, Any]:
    path = regular(path, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def binding(record: Any, expected: Path, label: str) -> None:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} binding is malformed")
    declared = Path(record["path"])
    path = declared if declared.is_absolute() else PROJECT / declared
    path = regular(path, label)
    if path != expected.resolve(strict=True):
        raise RuntimeError(f"{label} path mismatch")
    if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
        raise RuntimeError(f"{label} identity mismatch")


def validate_dispatch_contract(plan_schema: dict[str, Any]) -> dict[str, Any]:
    value = load_json(ACTIVATION_CONTRACT, "terminal-dispatch activation contract")
    jsonschema.Draft202012Validator(plan_schema).validate(value)
    contract = value.get("contract", {})
    if (
        value.get("artifact_id")
        != "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_activation_q0_v1"
        or value.get("revision") != 1
        or value.get("operational_status") != "dormant_dependency"
        or value.get("claim_authority") != "none"
        or contract.get("candidate_id") != "cmix_filebacked_fxcm_full_a_qm8_v1"
        or contract.get("execution_authority") is not False
        or contract.get("verifier_execution_authority") is not False
        or contract.get("arm_b_authority") is not False
        or contract.get("memory_safe_parent_qualification_authority") is not False
        or contract.get("gamma_compression_credit_bytes") != 0
        or contract.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("terminal-dispatch activation contract authority drift")
    expected = {
        "dispatcher": Path(__file__).resolve(strict=True),
        "closure_helper": PROJECT
        / "tools/cmix_filebacked_fxcm_qm8_terminal_closure.py",
        "plan_schema": PLAN_SCHEMA,
        "intent_schema": INTENT_SCHEMA,
        "activation_schema": RECEIPT_SCHEMA,
        "roundtrip_schema": PROJECT
        / "contracts/research/v1/cmix-filebacked-fxcm-full-roundtrip.schema.json",
        "research_contracts": RESEARCH_CONTRACTS,
        "python_runtime": PYTHON,
    }
    for name, path in expected.items():
        binding(contract.get(name), path, name)
    dormant = contract.get("dormant_plans", {})
    for branch in BRANCHES.values():
        record = dormant.get(branch["name"])
        binding(record, branch["plan"], f"{branch['name']} dormant plan")
        if record["sha256"] != branch["plan_sha256"]:
            raise RuntimeError(f"{branch['name']} dormant plan digest mismatch")
    expected_command = [
        str(PYTHON),
        "tools/cmix_filebacked_fxcm_full_qm8_terminal_dispatch_activate.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
    ]
    if contract.get("command") != expected_command:
        raise RuntimeError("terminal-dispatch activation command mismatch")
    return value


def validate_dormant_plan(branch: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    path = regular(branch["plan"], f"{branch['name']} dormant plan")
    if sha256(path) != branch["plan_sha256"]:
        raise RuntimeError(f"{branch['name']} dormant plan identity drift")
    plan = load_json(path, f"{branch['name']} dormant plan")
    jsonschema.Draft202012Validator(schema).validate(plan)
    contract = plan.get("contract", {})
    activation = contract.get("activation", {})
    if (
        plan.get("artifact_id") != branch["artifact_id"]
        or plan.get("revision") != 1
        or plan.get("operational_status") != "dormant_dependency"
        or plan.get("claim_authority") != "none"
        or contract.get("candidate_id") != "cmix_filebacked_fxcm_full_a_qm8_v1"
        or contract.get("source_receipt") != str(closure.RECEIPT)
        or contract.get("output") != str(branch["output"])
        or activation
        != {
            "status": branch["waiting_status"],
            "execution_authorized": False,
            "minimum_activation_revision": 2,
            "terminal_receipt_sha256": None,
        }
        or contract.get("promotion_authority") is not False
        or contract.get("memory_safe_parent_qualification_authority") is not False
        or contract.get("gamma_compression_credit_bytes") != 0
        or contract.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError(f"{branch['name']} plan is not the frozen dormant template")
    if branch["name"] == "failure" and contract.get("archive_authority") is not False:
        raise RuntimeError("failure plan archive authority drift")
    return plan


def changed_paths(before: Any, after: Any, prefix: str = "") -> set[str]:
    if isinstance(before, dict) and isinstance(after, dict):
        if set(before) != set(after):
            return {prefix or "$"}
        changes: set[str] = set()
        for key in before:
            child = f"{prefix}.{key}" if prefix else key
            changes.update(changed_paths(before[key], after[key], child))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            return {prefix or "$"}
        changes: set[str] = set()
        for index, (left, right) in enumerate(zip(before, after, strict=True)):
            changes.update(changed_paths(left, right, f"{prefix}[{index}]"))
        return changes
    return set() if before == after else {prefix or "$"}


def activated_plan(
    dormant: dict[str, Any], branch: dict[str, Any], receipt_sha256: str
) -> dict[str, Any]:
    activated = copy.deepcopy(dormant)
    activated["revision"] = 2
    state = activated["contract"]["activation"]
    state["status"] = branch["activated_status"]
    state["execution_authorized"] = True
    state["terminal_receipt_sha256"] = receipt_sha256
    observed = changed_paths(dormant, activated)
    if observed != ALLOWED_CHANGES:
        raise RuntimeError(f"activation semantic diff mismatch: {sorted(observed)}")
    return activated


def json_payload(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def write_all(descriptor: int, payload: bytes) -> None:
    cursor = 0
    while cursor < len(payload):
        written = os.write(descriptor, payload[cursor:])
        if written <= 0:
            raise OSError("short write")
        cursor += written


def write_new_json(path: Path, value: dict[str, Any], schema_path: Path) -> dict[str, Any]:
    schema = load_json(schema_path, f"{path.name} schema")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"new JSON output path is occupied: {path}")
    payload = json_payload(value)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    metadata = os.fstat(descriptor)
    try:
        write_all(descriptor, payload)
        os.fsync(descriptor)
        closure.fsync_directory(path.parent)
    except Exception:
        os.close(descriptor)
        try:
            current = path.lstat()
            if current.st_dev == metadata.st_dev and current.st_ino == metadata.st_ino:
                path.unlink()
                closure.fsync_directory(path.parent)
        except OSError:
            pass
        raise
    os.close(descriptor)
    return artifact(path)


def rename_exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RuntimeError("renameat2(RENAME_EXCHANGE) is unavailable")
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    result = renameat2(-100, os.fsencode(left), -100, os.fsencode(right), 2)
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{left} <-> {right}")


def publish_plan(
    branch: dict[str, Any], dormant: dict[str, Any], activated: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = branch["plan"]
    original = path.stat()
    payload = json.dumps(activated, indent=2).encode("ascii") + b"\n"
    expected_digest = sha256_bytes(payload)
    temporary = DISPLACED_DORMANT
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError("activation temporary path is occupied")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        stat.S_IMODE(original.st_mode),
    )
    temporary_state = os.fstat(descriptor)
    try:
        write_all(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    exchanged = False
    try:
        reparsed = json.loads(temporary.read_text(encoding="ascii"))
        if reparsed != activated or changed_paths(dormant, reparsed) != ALLOWED_CHANGES:
            raise RuntimeError("serialized activation plan changed undeclared semantics")
        current = path.stat()
        if (
            current.st_dev != original.st_dev
            or current.st_ino != original.st_ino
            or current.st_nlink != 1
            or sha256(path) != branch["plan_sha256"]
        ):
            raise RuntimeError("dormant plan changed during activation")
        rename_exchange(temporary, path)
        exchanged = True
        published = path.stat()
        displaced = temporary.stat()
        valid_exchange = (
            published.st_dev == temporary_state.st_dev
            and published.st_ino == temporary_state.st_ino
            and published.st_nlink == 1
            and sha256(path) == expected_digest
            and displaced.st_dev == original.st_dev
            and displaced.st_ino == original.st_ino
            and displaced.st_nlink == 1
            and sha256(temporary) == branch["plan_sha256"]
        )
        if not valid_exchange:
            path_now = path.stat()
            temp_now = temporary.stat()
            if (
                path_now.st_dev == temporary_state.st_dev
                and path_now.st_ino == temporary_state.st_ino
                and temp_now.st_dev == original.st_dev
                and temp_now.st_ino == original.st_ino
            ):
                rename_exchange(temporary, path)
                exchanged = False
                closure.fsync_directory(PLAN_ROOT)
            raise RuntimeError("atomic activation exchange witness mismatch")
        closure.fsync_directory(PLAN_ROOT)
    finally:
        if not exchanged and (temporary.exists() or temporary.is_symlink()):
            current = temporary.lstat()
            if (
                stat.S_ISREG(current.st_mode)
                and current.st_nlink == 1
                and current.st_dev == temporary_state.st_dev
                and current.st_ino == temporary_state.st_ino
            ):
                temporary.unlink()
                closure.fsync_directory(PLAN_ROOT)
            else:
                raise RuntimeError("activation temporary identity changed; preserved")
    return artifact(path), artifact(temporary)


def expected_plan_record(branch: dict[str, Any], activated: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(activated, indent=2).encode("ascii") + b"\n"
    return {
        "path": str(branch["plan"]),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def safe_release(lock: closure.OwnedLock | None) -> None:
    if lock is None or lock.released:
        return
    lock.release()


def require_verifier_outputs_absent() -> None:
    for branch in BRANCHES.values():
        path = branch["output"]
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"terminal-verification output is occupied: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    expected_command = [
        str(PYTHON),
        "tools/cmix_filebacked_fxcm_full_qm8_terminal_dispatch_activate.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
    ]
    actual_command = [str(Path(sys.executable).resolve(strict=True)), *sys.argv]
    if actual_command != expected_command:
        raise SystemExit("terminal dispatcher requires the frozen command and runtime")

    schema = load_json(PLAN_SCHEMA, "campaign static-contract schema")
    jsonschema.Draft202012Validator.check_schema(schema)
    validate_dispatch_contract(schema)
    dormant = {
        verdict: validate_dormant_plan(branch, schema)
        for verdict, branch in BRANCHES.items()
    }
    for path in [
        INTENT,
        ACTIVATION_RECEIPT,
        DISPLACED_DORMANT,
        *(branch["output"] for branch in BRANCHES.values()),
    ]:
        if path.exists() or path.is_symlink():
            raise SystemExit(f"terminal-dispatch output already exists: {path}")

    planning_lock: closure.OwnedLock | None = None
    full1g_lock: closure.OwnedLock | None = None
    intent_written = False
    completed = False
    with closure.open_terminal_receipt(args.receipt) as receipt:
        terminal_pass = receipt.value["terminal_pass"]
        branch = BRANCHES[terminal_pass]
        activated = activated_plan(dormant[terminal_pass], branch, receipt.sha256)
        jsonschema.Draft202012Validator(schema).validate(activated)
        planning_payload = json.dumps(
            {
                "branch": branch["name"],
                "owner_pid": os.getpid(),
                "receipt_sha256": receipt.sha256,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii") + b"\n"
        planning_lock = closure.OwnedLock.acquire(PLAN_LOCK, planning_payload)
        try:
            full1g_lock, first_closure = closure.reserve_full1g(
                receipt, terminal_pass, "qm8_terminal_dispatch_activation"
            )
            receipt.revalidate()
            require_verifier_outputs_absent()
            validate_dispatch_contract(schema)
            for verdict, candidate_branch in BRANCHES.items():
                validate_dormant_plan(candidate_branch, schema)
                if dormant[verdict] != load_json(
                    candidate_branch["plan"], f"{candidate_branch['name']} dormant plan"
                ):
                    raise RuntimeError("dormant plan changed after lock acquisition")
            expected_activated = expected_plan_record(branch, activated)
            intent = {
                "schema": "gamma.enwiki9.cmix-filebacked-fxcm-qm8-terminal-dispatch-intent.v1",
                "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
                "branch": branch["name"],
                "terminal_pass": terminal_pass,
                "terminal_receipt": receipt.record(),
                "dispatch_contract": artifact(ACTIVATION_CONTRACT),
                "dormant_plan": artifact(branch["plan"]),
                "expected_activated_plan": expected_activated,
                "displaced_dormant_plan_path": str(DISPLACED_DORMANT),
                "non_selected_plan": artifact(BRANCHES[not terminal_pass]["plan"]),
                "planning_lock": planning_lock.record(),
                "full1g_lock": full1g_lock.record(),
                "closure_before_publication": first_closure,
                "state": "prepared_before_plan_publication",
                "verifier_executed": False,
                "arm_b_authorized": False,
                "gamma_compression_credit_bytes": 0,
                "gamma_score_credit_bytes": 0,
            }
            intent_record = write_new_json(INTENT, intent, INTENT_SCHEMA)
            intent_written = True
            receipt.revalidate()
            second_closure = closure.closure_snapshot(
                receipt.value, terminal_pass, full1g_lock
            )
            plan_record, displaced_record = publish_plan(
                branch, dormant[terminal_pass], activated
            )
            if plan_record != expected_activated:
                raise RuntimeError("published activation plan identity mismatch")
            receipt.revalidate()
            final_closure = closure.closure_snapshot(
                receipt.value, terminal_pass, full1g_lock
            )
            jsonschema.Draft202012Validator(schema).validate(
                load_json(branch["plan"], "published activation plan")
            )
            non_selected = artifact(BRANCHES[not terminal_pass]["plan"])
            if non_selected["sha256"] != BRANCHES[not terminal_pass]["plan_sha256"]:
                raise RuntimeError("non-selected terminal plan changed")
            require_verifier_outputs_absent()
            output = {
                "schema": "gamma.enwiki9.cmix-filebacked-fxcm-qm8-terminal-dispatch-activation.v1",
                "candidate_id": "cmix_filebacked_fxcm_full_a_qm8_v1",
                "branch": branch["name"],
                "terminal_pass": terminal_pass,
                "terminal_receipt": receipt.record(),
                "dispatch_contract": artifact(ACTIVATION_CONTRACT),
                "activation_intent": intent_record,
                "activated_plan": plan_record,
                "displaced_dormant_plan": displaced_record,
                "non_selected_plan": non_selected,
                "closure_after_intent": second_closure,
                "closure_after_publication": final_closure,
                "verifier_executed": False,
                "arm_b_authorized": False,
                "memory_safe_parent_qualified": False,
                "gamma_compression_credit_bytes": 0,
                "gamma_score_credit_bytes": 0,
            }
            activation_record = write_new_json(
                ACTIVATION_RECEIPT, output, RECEIPT_SCHEMA
            )
            planning_lock.release()
            full1g_lock.release()
            completed = True
        finally:
            if not completed:
                if intent_written:
                    if planning_lock is not None:
                        planning_lock.preserve()
                    if full1g_lock is not None:
                        full1g_lock.preserve()
                else:
                    safe_release(full1g_lock)
                    safe_release(planning_lock)

    result = {
        "event": "qm8_terminal_verification_branch_activated",
        "branch": branch["name"],
        "terminal_pass": terminal_pass,
        "activation_receipt": activation_record,
        "verifier_executed": False,
        "arm_b_authorized": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    sys.stdout.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
