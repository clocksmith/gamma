#!/usr/bin/env python3
"""Shared fail-closed qm8 receipt, process, cgroup, and lease closure proof."""

from __future__ import annotations

import copy
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Iterator

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
RESULT = PROJECT / "results/cmix_filebacked_fxcm_full_a_qm8_v1"
SCRATCH = PROJECT / "scratch/cmix_filebacked_fxcm_full_a_qm8_v1"
CGROUP = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/"
    "app.slice/gamma-q1-full-a-qm8-v1"
)
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
LEASE_LOCK = LEASE.with_name(f"{LEASE.name}.lock")
RECEIPT = RESULT / "full-roundtrip-receipt.json"
ACTIVATION_RECEIPT = RESULT / "terminal-dispatch-activation-receipt.json"
ACTIVATION_INTENT = RESULT / "terminal-dispatch-activation-intent.json"
ACTIVATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-activation.schema.json"
)
INTENT_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-filebacked-fxcm-qm8-terminal-dispatch-intent.schema.json"
)
DISPATCH_CONTRACT = (
    PROJECT
    / "operations/planning/"
    "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_activation_q0_v1.json"
)
PLAN_SCHEMA = PROJECT / "operations/planning/campaign-static-contract.schema.json"
DISPATCHER = PROJECT / "tools/cmix_filebacked_fxcm_full_qm8_terminal_dispatch_activate.py"
ROUNDTRIP_SCHEMA = (
    PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-full-roundtrip.schema.json"
)
RESEARCH_CONTRACTS = PROJECT / "tools/research_contracts.py"
PYTHON_RUNTIME = Path("/usr/bin/python3.14")
PLAN_LOCK = (
    PROJECT
    / "operations/planning/"
    "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch.activation.lock"
)
DISPLACED_DORMANT = (
    PROJECT
    / "operations/planning/"
    ".cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch.displaced-dormant.json"
)
SOURCE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
SOURCE_CANDIDATE = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
QM8_ID = "cmix_filebacked_fxcm_full_a_qm8_v1"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_fd(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    blocks: list[bytes] = []
    while True:
        block = os.read(descriptor, 1 << 20)
        if not block:
            return b"".join(blocks)
        blocks.append(block)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def regular(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has a symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} is not a single-link regular file: {path}")
    return path.resolve(strict=True)


def artifact(path: Path) -> dict[str, Any]:
    path = regular(path, "artifact")
    payload = path.read_bytes()
    return {"path": str(path), "bytes": len(payload), "sha256": sha256_bytes(payload)}


def read_bound_artifact(record: Any, expected: Path, label: str) -> bytes:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} artifact record is malformed")
    path = regular(Path(record["path"]), label)
    if path != expected.resolve(strict=True):
        raise RuntimeError(f"{label} path mismatch")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        payload = read_fd(descriptor)
        current = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or current.st_dev != metadata.st_dev
            or current.st_ino != metadata.st_ino
            or current.st_nlink != 1
            or len(payload) != record["bytes"]
            or sha256_bytes(payload) != record["sha256"]
        ):
            raise RuntimeError(f"{label} artifact identity mismatch")
        return payload
    finally:
        os.close(descriptor)


def static_binding(record: Any, expected: Path, label: str) -> bytes:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise RuntimeError(f"{label} static binding is malformed")
    declared = Path(record["path"])
    path = declared if declared.is_absolute() else PROJECT / declared
    absolute_record = {**record, "path": str(path)}
    return read_bound_artifact(absolute_record, expected, label)


def runtime_record_matches_static(
    runtime: Any, frozen: Any, expected: Path, label: str
) -> bool:
    if (
        not isinstance(runtime, dict)
        or set(runtime) != {"path", "bytes", "sha256"}
        or not isinstance(frozen, dict)
        or set(frozen) != {"path", "bytes", "sha256"}
    ):
        return False
    runtime_path = Path(runtime["path"])
    frozen_path = Path(frozen["path"])
    if not frozen_path.is_absolute():
        frozen_path = PROJECT / frozen_path
    try:
        expected_path = expected.resolve(strict=True)
        return bool(
            runtime_path.resolve(strict=True) == expected_path
            and frozen_path.resolve(strict=True) == expected_path
            and runtime["bytes"] == frozen["bytes"]
            and runtime["sha256"] == frozen["sha256"]
        )
    except OSError:
        return False


def read_regular_file(path: Path, label: str) -> bytes:
    path = regular(path, label)
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        payload = read_fd(descriptor)
        current = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or current.st_dev != metadata.st_dev
            or current.st_ino != metadata.st_ino
            or current.st_nlink != 1
        ):
            raise RuntimeError(f"{label} identity changed while reading")
        return payload
    finally:
        os.close(descriptor)


@dataclass
class ReceiptWitness:
    path: Path
    descriptor: int
    device: int
    inode: int
    payload: bytes
    sha256: str
    value: dict[str, Any]

    def revalidate(self) -> None:
        descriptor_state = os.fstat(self.descriptor)
        path_state = self.path.lstat()
        payload = read_fd(self.descriptor)
        if (
            not stat.S_ISREG(descriptor_state.st_mode)
            or descriptor_state.st_nlink != 1
            or not stat.S_ISREG(path_state.st_mode)
            or path_state.st_nlink != 1
            or descriptor_state.st_dev != self.device
            or descriptor_state.st_ino != self.inode
            or path_state.st_dev != self.device
            or path_state.st_ino != self.inode
            or payload != self.payload
            or sha256_bytes(payload) != self.sha256
        ):
            raise RuntimeError("qm8 terminal receipt identity changed")
        schema = json.loads(
            read_regular_file(ROUNDTRIP_SCHEMA, "qm8 terminal receipt schema")
        )
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(self.value)
        descriptor_state = os.fstat(self.descriptor)
        path_state = self.path.lstat()
        if (
            descriptor_state.st_dev != self.device
            or descriptor_state.st_ino != self.inode
            or path_state.st_dev != self.device
            or path_state.st_ino != self.inode
            or read_fd(self.descriptor) != self.payload
        ):
            raise RuntimeError("qm8 terminal receipt changed during schema validation")

    def record(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "bytes": len(self.payload),
            "sha256": self.sha256,
        }

@contextmanager
def open_terminal_receipt(path: Path) -> Iterator[ReceiptWitness]:
    path = regular(path, "qm8 terminal receipt")
    if path != RECEIPT.resolve(strict=True):
        raise RuntimeError("qm8 terminal receipt path is not canonical")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise RuntimeError("qm8 terminal receipt descriptor is not single-link regular")
        payload = read_fd(descriptor)
        value = json.loads(payload)
        if not isinstance(value, dict):
            raise RuntimeError("qm8 terminal receipt is not a JSON object")
        witness = ReceiptWitness(
            path=path,
            descriptor=descriptor,
            device=metadata.st_dev,
            inode=metadata.st_ino,
            payload=payload,
            sha256=sha256_bytes(payload),
            value=value,
        )
        witness.revalidate()
        terminal_pass = value.get("terminal_pass")
        if (
            value.get("schema") != SOURCE_SCHEMA
            or value.get("candidate_id") != SOURCE_CANDIDATE
            or value.get("arm") != "a"
            or type(terminal_pass) is not bool
            or value.get("memory_safe_parent_qualified") is not False
            or value.get("promotion_authorized") is not False
            or value.get("execution_authority") is not False
            or value.get("claim_authority")
            != "guarded_full_corpus_roundtrip_arm_a_only"
            or value.get("gamma_compression_credit_bytes") != 0
            or value.get("gamma_score_credit_bytes") != 0
        ):
            raise RuntimeError("receipt is not a terminal zero-credit q1 Arm-A result")
        yield witness
    finally:
        os.close(descriptor)


def proc_identity(pid: int) -> tuple[int, int]:
    raw = (Path("/proc") / str(pid) / "stat").read_text(encoding="ascii")
    close = raw.rfind(")")
    if close < 0:
        raise RuntimeError(f"malformed /proc/{pid}/stat")
    fields = raw[close + 2 :].split()
    if len(fields) <= 19:
        raise RuntimeError(f"short /proc/{pid}/stat")
    return int(fields[1]), int(fields[19])


def identity_is_live(pid: Any, start_ticks: Any) -> bool:
    if (
        isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid < 1
        or isinstance(start_ticks, bool)
        or not isinstance(start_ticks, int)
        or start_ticks < 1
    ):
        return False
    try:
        return proc_identity(pid)[1] == start_ticks
    except (OSError, RuntimeError, ValueError):
        return False


def process_record(pid: int, reasons: list[str]) -> dict[str, Any]:
    try:
        _, start_ticks = proc_identity(pid)
    except (OSError, RuntimeError, ValueError):
        start_ticks = None
    try:
        command = (Path("/proc") / str(pid) / "cmdline").read_bytes()
    except OSError:
        command = b""
    return {
        "pid": pid,
        "start_ticks": start_ticks,
        "reasons": sorted(set(reasons)),
        "command_sha256": sha256_bytes(command),
    }


def launcher_ancestors() -> set[int]:
    ancestors: set[int] = set()
    cursor = os.getppid()
    while cursor > 1 and cursor not in ancestors:
        ancestors.add(cursor)
        try:
            cursor = proc_identity(cursor)[0]
        except (OSError, RuntimeError, ValueError):
            break
    return ancestors


def qm8_processes() -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    ancestors = launcher_ancestors()
    shell_launchers = {"bash", "dash", "sh", "timeout", "zsh"}
    command_tokens = tuple(
        os.fsencode(value)
        for value in (QM8_ID, str(RESULT), str(SCRATCH), str(CGROUP), CGROUP.name)
    )
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        pid = int(process.name)
        if pid == os.getpid():
            continue
        reasons: list[str] = []
        try:
            command = (process / "cmdline").read_bytes()
        except OSError:
            continue
        if any(token in command for token in command_tokens):
            reasons.append("qm8_command_binding")
        try:
            cwd = os.readlink(process / "cwd")
        except OSError:
            cwd = ""
        if str(SCRATCH) in cwd:
            reasons.append("qm8_scratch_cwd")
        try:
            cgroups = (process / "cgroup").read_text(encoding="utf-8")
        except OSError:
            cgroups = ""
        if CGROUP.name in cgroups:
            reasons.append("qm8_cgroup_membership")
        try:
            command_name = (process / "comm").read_text(encoding="utf-8").strip()
        except OSError:
            command_name = ""
        if (
            pid in ancestors
            and reasons == ["qm8_command_binding"]
            and command_name in shell_launchers
        ):
            continue
        if reasons:
            matches.append(process_record(pid, reasons))
    return sorted(matches, key=lambda item: item["pid"])


def load_lease_evidence(source: dict[str, Any]) -> dict[str, Any] | None:
    record = source.get("lease", {}).get("evidence")
    if record is None:
        if source.get("terminal_pass") is True:
            raise RuntimeError("passing qm8 receipt lacks terminal lease evidence")
        return None
    expected = RESULT / "lease-evidence.json"
    value = json.loads(read_bound_artifact(record, expected, "qm8 terminal lease evidence"))
    if (
        not isinstance(value, dict)
        or value.get("schema") != "gamma.enwiki9.exclusive-full1g-lease.v1"
        or value.get("candidate_id")
        != "cmix_obias_memory_safe_parent_filebacked_q1_v1-full-a"
        or value.get("result_path") != str(RESULT)
        or value.get("scratch_path") != str(SCRATCH)
        or isinstance(value.get("pid"), bool)
        or not isinstance(value.get("pid"), int)
        or value["pid"] < 1
        or isinstance(value.get("proc_start_ticks"), bool)
        or not isinstance(value.get("proc_start_ticks"), int)
        or value["proc_start_ticks"] < 1
    ):
        raise RuntimeError("qm8 terminal lease evidence semantic mismatch")
    codec_fields = (value.get("codec_pid"), value.get("codec_proc_start_ticks"))
    if any(field is not None for field in codec_fields) and (
        isinstance(codec_fields[0], bool)
        or not isinstance(codec_fields[0], int)
        or codec_fields[0] < 1
        or isinstance(codec_fields[1], bool)
        or not isinstance(codec_fields[1], int)
        or codec_fields[1] < 1
    ):
        raise RuntimeError("qm8 terminal codec identity is malformed")
    return value


def validate_closure_record(
    value: Any, terminal_pass: bool, label: str
) -> None:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not an object")
    checks = value.get("checks")
    expected_lease = value.get("lease_present")
    lease_candidate = value.get("lease_candidate_id")
    if (
        value.get("terminal_pass") is not terminal_pass
        or not isinstance(checks, dict)
        or not checks
        or any(item is not True for item in checks.values())
        or value.get("errors") != []
        or value.get("live_recorded_identities") != []
        or value.get("matching_processes") != []
        or value.get("cgroup_path") != str(CGROUP)
        or value.get("cgroup_occupants") != []
        or value.get("lease_path") != str(LEASE)
        or value.get("lease_owner_live") is not False
        or type(expected_lease) is not bool
        or (
            expected_lease
            and lease_candidate
            != "cmix_obias_memory_safe_parent_filebacked_q1_v1-full-a"
        )
        or (not expected_lease and lease_candidate is not None)
        or (
            terminal_pass
            and (
                value.get("cgroup_present") is not False
                or expected_lease is not False
            )
        )
    ):
        raise RuntimeError(f"{label} semantic mismatch")


def validate_activated_plan_derivation(
    witness: ReceiptWitness,
    branch: str,
    activated_record: Any,
    selected_plan: Path,
    frozen_record: Any,
    plan_schema: dict[str, Any],
) -> None:
    activated_raw = read_bound_artifact(
        activated_record, selected_plan, "selected activated plan"
    )
    activated = json.loads(activated_raw)
    jsonschema.Draft202012Validator(plan_schema).validate(activated)
    expected_status = (
        "activated_after_terminal_passing_qm8"
        if branch == "success"
        else "activated_after_terminal_failed_qm8"
    )
    activation = activated.get("contract", {}).get("activation", {})
    if (
        activated.get("revision") != 2
        or activation.get("status") != expected_status
        or activation.get("execution_authorized") is not True
        or activation.get("terminal_receipt_sha256") != witness.sha256
    ):
        raise RuntimeError("selected activated plan activation fields mismatch")
    reconstructed = copy.deepcopy(activated)
    reconstructed["revision"] = 1
    reconstructed_activation = reconstructed["contract"]["activation"]
    reconstructed_activation["status"] = (
        "waiting_for_terminal_passing_qm8"
        if branch == "success"
        else "waiting_for_terminal_failed_qm8"
    )
    reconstructed_activation["execution_authorized"] = False
    reconstructed_activation["terminal_receipt_sha256"] = None
    reconstructed_raw = json.dumps(reconstructed, indent=2).encode("ascii") + b"\n"
    if (
        not isinstance(frozen_record, dict)
        or set(frozen_record) != {"path", "bytes", "sha256"}
        or len(reconstructed_raw) != frozen_record["bytes"]
        or sha256_bytes(reconstructed_raw) != frozen_record["sha256"]
    ):
        raise RuntimeError(
            "selected activated plan contains changes beyond the four-field activation"
        )


def validate_dispatch_activation(
    witness: ReceiptWitness,
    branch: str,
    selected_plan: Path,
    non_selected_plan: Path,
) -> dict[str, Any]:
    expected_terminal = branch == "success"
    if branch not in {"success", "failure"} or witness.value["terminal_pass"] is not expected_terminal:
        raise RuntimeError("terminal-dispatch branch does not match receipt")
    activation_raw = read_regular_file(
        ACTIVATION_RECEIPT, "terminal-dispatch activation receipt"
    )
    activation = json.loads(activation_raw)
    activation_schema = json.loads(
        read_regular_file(ACTIVATION_SCHEMA, "terminal-dispatch activation schema")
    )
    jsonschema.Draft202012Validator.check_schema(activation_schema)
    jsonschema.Draft202012Validator(activation_schema).validate(activation)
    dispatch_raw = read_bound_artifact(
        activation.get("dispatch_contract"),
        DISPATCH_CONTRACT,
        "terminal-dispatch activation contract",
    )
    dispatch = json.loads(dispatch_raw)
    dispatch_contract = dispatch.get("contract", {}) if isinstance(dispatch, dict) else {}
    plan_schema = json.loads(
        static_binding(
            dispatch_contract.get("plan_schema"),
            PLAN_SCHEMA,
            "terminal-dispatch plan schema",
        )
    )
    jsonschema.Draft202012Validator.check_schema(plan_schema)
    jsonschema.Draft202012Validator(plan_schema).validate(dispatch)
    expected_command = [
        str(PYTHON_RUNTIME),
        "tools/cmix_filebacked_fxcm_full_qm8_terminal_dispatch_activate.py",
        "--receipt",
        "results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json",
    ]
    if (
        dispatch.get("artifact_id")
        != "cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_activation_q0_v1"
        or dispatch.get("revision") != 1
        or dispatch.get("operational_status") != "dormant_dependency"
        or dispatch.get("claim_authority") != "none"
        or dispatch_contract.get("candidate_id") != QM8_ID
        or dispatch_contract.get("command") != expected_command
        or dispatch_contract.get("execution_authority") is not False
        or dispatch_contract.get("verifier_execution_authority") is not False
        or dispatch_contract.get("arm_b_authority") is not False
        or dispatch_contract.get("memory_safe_parent_qualification_authority")
        is not False
        or dispatch_contract.get("gamma_compression_credit_bytes") != 0
        or dispatch_contract.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("terminal-dispatch activation contract authority drift")
    static_binding(
        dispatch_contract.get("dispatcher"),
        DISPATCHER,
        "terminal-dispatch dispatcher",
    )
    static_binding(
        dispatch_contract.get("closure_helper"),
        Path(__file__).resolve(strict=True),
        "terminal-dispatch closure helper",
    )
    static_binding(
        dispatch_contract.get("intent_schema"),
        INTENT_SCHEMA,
        "terminal-dispatch intent schema",
    )
    static_binding(
        dispatch_contract.get("activation_schema"),
        ACTIVATION_SCHEMA,
        "terminal-dispatch activation schema",
    )
    static_binding(
        dispatch_contract.get("roundtrip_schema"),
        ROUNDTRIP_SCHEMA,
        "terminal-dispatch roundtrip schema",
    )
    static_binding(
        dispatch_contract.get("research_contracts"),
        RESEARCH_CONTRACTS,
        "terminal-dispatch contract validator",
    )
    static_binding(
        dispatch_contract.get("python_runtime"),
        PYTHON_RUNTIME,
        "terminal-dispatch Python runtime",
    )
    activation_record = {
        "path": str(ACTIVATION_RECEIPT.resolve(strict=True)),
        "bytes": len(activation_raw),
        "sha256": sha256_bytes(activation_raw),
    }
    if (
        activation.get("branch") != branch
        or activation.get("terminal_pass") is not expected_terminal
        or activation.get("terminal_receipt") != witness.record()
        or not artifact_matches_path(activation.get("dispatch_contract"), DISPATCH_CONTRACT)
        or not artifact_matches_path(activation.get("activated_plan"), selected_plan)
        or not artifact_matches_path(activation.get("non_selected_plan"), non_selected_plan)
        or activation.get("verifier_executed") is not False
        or activation.get("arm_b_authorized") is not False
        or activation.get("memory_safe_parent_qualified") is not False
        or activation.get("gamma_compression_credit_bytes") != 0
        or activation.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("terminal-dispatch activation receipt binding mismatch")
    validate_closure_record(
        activation.get("closure_after_intent"),
        expected_terminal,
        "terminal-dispatch closure after intent",
    )
    validate_closure_record(
        activation.get("closure_after_publication"),
        expected_terminal,
        "terminal-dispatch closure after publication",
    )
    intent_record = activation.get("activation_intent")
    intent_raw = read_bound_artifact(
        intent_record, ACTIVATION_INTENT, "terminal-dispatch activation intent"
    )
    intent = json.loads(intent_raw)
    intent_schema = json.loads(
        read_regular_file(INTENT_SCHEMA, "terminal-dispatch intent schema")
    )
    jsonschema.Draft202012Validator.check_schema(intent_schema)
    jsonschema.Draft202012Validator(intent_schema).validate(intent)
    dormant_plans = dispatch_contract.get("dormant_plans", {})
    selected_frozen = dormant_plans.get(branch)
    non_selected_frozen = dormant_plans.get(
        "failure" if branch == "success" else "success"
    )
    displaced_raw = read_bound_artifact(
        activation.get("displaced_dormant_plan"),
        DISPLACED_DORMANT,
        "displaced dormant plan",
    )
    if (
        intent.get("branch") != branch
        or intent.get("terminal_pass") is not expected_terminal
        or intent.get("terminal_receipt") != witness.record()
        or intent.get("dispatch_contract") != activation.get("dispatch_contract")
        or intent.get("displaced_dormant_plan_path") != str(DISPLACED_DORMANT)
        or not runtime_record_matches_static(
            intent.get("dormant_plan"),
            selected_frozen,
            selected_plan,
            "selected dormant plan",
        )
        or intent.get("expected_activated_plan") != activation.get("activated_plan")
        or intent.get("non_selected_plan") != activation.get("non_selected_plan")
        or not runtime_record_matches_static(
            activation.get("non_selected_plan"),
            non_selected_frozen,
            non_selected_plan,
            "non-selected dormant plan",
        )
        or intent.get("planning_lock", {}).get("path") != str(PLAN_LOCK)
        or intent.get("full1g_lock", {}).get("path") != str(LEASE_LOCK)
        or intent.get("verifier_executed") is not False
        or intent.get("arm_b_authorized") is not False
        or intent.get("gamma_compression_credit_bytes") != 0
        or intent.get("gamma_score_credit_bytes") != 0
        or not isinstance(selected_frozen, dict)
        or len(displaced_raw) != selected_frozen.get("bytes")
        or sha256_bytes(displaced_raw) != selected_frozen.get("sha256")
    ):
        raise RuntimeError("terminal-dispatch activation intent binding mismatch")
    validate_activated_plan_derivation(
        witness,
        branch,
        activation.get("activated_plan"),
        selected_plan,
        selected_frozen,
        plan_schema,
    )
    static_binding(
        non_selected_frozen,
        non_selected_plan,
        "non-selected dormant plan",
    )
    validate_closure_record(
        intent.get("closure_before_publication"),
        expected_terminal,
        "terminal-dispatch closure before publication",
    )
    witness.revalidate()
    return {"record": activation_record, "value": activation}


def artifact_matches_path(record: Any, expected: Path) -> bool:
    try:
        read_bound_artifact(record, expected, f"artifact {expected.name}")
    except (OSError, RuntimeError, TypeError, json.JSONDecodeError):
        return False
    return True


def cgroup_occupants() -> list[int]:
    try:
        values = (CGROUP / "cgroup.procs").read_text(encoding="ascii").split()
    except FileNotFoundError:
        return []
    return sorted(int(value) for value in values)


def closure_snapshot(
    source: dict[str, Any], terminal_pass: bool, held_full_lock: "OwnedLock"
) -> dict[str, Any]:
    held_full_lock.verify()
    evidence = load_lease_evidence(source)
    identities: list[dict[str, Any]] = []
    if evidence is not None:
        identities.append(
            {
                "role": "coordinator",
                "pid": evidence.get("pid"),
                "start_ticks": evidence.get("proc_start_ticks"),
            }
        )
        if "codec_pid" in evidence or "codec_proc_start_ticks" in evidence:
            identities.append(
                {
                    "role": "native_codec",
                    "pid": evidence.get("codec_pid"),
                    "start_ticks": evidence.get("codec_proc_start_ticks"),
                }
            )
    live_identities = [
        identity for identity in identities if identity_is_live(identity["pid"], identity["start_ticks"])
    ]
    processes = qm8_processes()
    occupants = cgroup_occupants()
    lease_present = LEASE.exists() or LEASE.is_symlink()
    lease_owner_live = False
    lease_candidate: str | None = None
    if lease_present:
        current = json.loads(read_regular_file(LEASE, "current full-1G lease"))
        if (
            not isinstance(current, dict)
            or current.get("schema") != "gamma.enwiki9.exclusive-full1g-lease.v1"
            or current.get("candidate_id")
            != "cmix_obias_memory_safe_parent_filebacked_q1_v1-full-a"
            or isinstance(current.get("pid"), bool)
            or not isinstance(current.get("pid"), int)
            or current["pid"] < 1
            or isinstance(current.get("proc_start_ticks"), bool)
            or not isinstance(current.get("proc_start_ticks"), int)
            or current["proc_start_ticks"] < 1
        ):
            raise RuntimeError("current full-1G lease is malformed or belongs to another lane")
        current_codec = (
            current.get("codec_pid"),
            current.get("codec_proc_start_ticks"),
        )
        if any(field is not None for field in current_codec) and (
            isinstance(current_codec[0], bool)
            or not isinstance(current_codec[0], int)
            or current_codec[0] < 1
            or isinstance(current_codec[1], bool)
            or not isinstance(current_codec[1], int)
            or current_codec[1] < 1
        ):
            raise RuntimeError("current full-1G lease codec identity is malformed")
        lease_candidate = current.get("candidate_id")
        lease_owner_live = identity_is_live(
            current.get("pid"), current.get("proc_start_ticks")
        ) or identity_is_live(
            current.get("codec_pid"), current.get("codec_proc_start_ticks")
        )
    checks = {
        "full1g_lock_owned": True,
        "recorded_identities_dead": not live_identities,
        "qm8_process_scan_empty": not processes,
        "qm8_cgroup_unoccupied": not occupants,
        "current_lease_has_no_live_owner": not lease_owner_live,
        "success_lease_absent": (not terminal_pass) or not lease_present,
        "success_cgroup_absent": (not terminal_pass) or not CGROUP.exists(),
    }
    errors = [name for name, passed in checks.items() if not passed]
    snapshot = {
        "checks": checks,
        "errors": errors,
        "recorded_identities": identities,
        "live_recorded_identities": live_identities,
        "matching_processes": processes,
        "cgroup_path": str(CGROUP),
        "cgroup_present": CGROUP.exists(),
        "cgroup_occupants": occupants,
        "lease_path": str(LEASE),
        "lease_present": lease_present,
        "lease_candidate_id": lease_candidate,
        "lease_owner_live": lease_owner_live,
        "terminal_pass": terminal_pass,
    }
    if errors:
        raise RuntimeError(f"qm8 terminal closure failed: {errors}")
    return snapshot


@dataclass
class OwnedLock:
    path: Path
    descriptor: int
    device: int
    inode: int
    payload: bytes
    released: bool = False

    @classmethod
    def acquire(cls, path: Path, payload: bytes) -> "OwnedLock":
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"lock path is occupied: {path}")
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
        )
        metadata = os.fstat(descriptor)
        try:
            cursor = 0
            while cursor < len(payload):
                written = os.write(descriptor, payload[cursor:])
                if written <= 0:
                    raise OSError("short lock write")
                cursor += written
            os.fsync(descriptor)
            fsync_directory(path.parent)
        except Exception:
            os.close(descriptor)
            try:
                current = path.lstat()
                if current.st_dev == metadata.st_dev and current.st_ino == metadata.st_ino:
                    path.unlink()
                    fsync_directory(path.parent)
            except OSError:
                pass
            raise
        return cls(path, descriptor, metadata.st_dev, metadata.st_ino, payload)

    def verify(self) -> None:
        descriptor_state = os.fstat(self.descriptor)
        path_state = self.path.lstat()
        if (
            not stat.S_ISREG(path_state.st_mode)
            or path_state.st_nlink != 1
            or descriptor_state.st_dev != self.device
            or descriptor_state.st_ino != self.inode
            or path_state.st_dev != self.device
            or path_state.st_ino != self.inode
            or self.path.read_bytes() != self.payload
        ):
            raise RuntimeError(f"owned lock identity changed: {self.path}")

    def record(self) -> dict[str, Any]:
        self.verify()
        return {
            "path": str(self.path),
            "device": self.device,
            "inode": self.inode,
            "payload_sha256": sha256_bytes(self.payload),
        }

    def release(self) -> None:
        self.verify()
        self.path.unlink()
        fsync_directory(self.path.parent)
        os.close(self.descriptor)
        self.released = True

    def preserve(self) -> None:
        if not self.released:
            os.close(self.descriptor)


def rename_noreplace(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RuntimeError("renameat2(RENAME_NOREPLACE) is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{source} -> {destination}")


@dataclass
class PreparedOutput:
    path: Path
    temporary: Path
    device: int
    inode: int
    payload: bytes
    published: bool = False

    @classmethod
    def prepare(cls, path: Path, value: dict[str, Any]) -> "PreparedOutput":
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"canonical output is occupied: {path}")
        temporary = path.with_name(f".{path.name}.prepared-{os.getpid()}")
        if temporary.exists() or temporary.is_symlink():
            raise RuntimeError(f"prepared output path is occupied: {temporary}")
        payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
        )
        metadata = os.fstat(descriptor)
        try:
            cursor = 0
            while cursor < len(payload):
                written = os.write(descriptor, payload[cursor:])
                if written <= 0:
                    raise OSError("short prepared-output write")
                cursor += written
            os.fsync(descriptor)
        except Exception:
            os.close(descriptor)
            try:
                current = temporary.lstat()
                if current.st_dev == metadata.st_dev and current.st_ino == metadata.st_ino:
                    temporary.unlink()
                    fsync_directory(path.parent)
            except OSError:
                pass
            raise
        os.close(descriptor)
        prepared = cls(path, temporary, metadata.st_dev, metadata.st_ino, payload)
        try:
            fsync_directory(path.parent)
        except Exception:
            prepared.discard()
            raise
        return prepared

    def publish(self) -> None:
        current = self.temporary.lstat()
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_nlink != 1
            or current.st_dev != self.device
            or current.st_ino != self.inode
            or self.temporary.read_bytes() != self.payload
        ):
            raise RuntimeError("prepared output identity changed")
        rename_noreplace(self.temporary, self.path)
        self.published = True
        fsync_directory(self.path.parent)
        published = self.path.lstat()
        if (
            not stat.S_ISREG(published.st_mode)
            or published.st_nlink != 1
            or published.st_dev != self.device
            or published.st_ino != self.inode
            or self.path.read_bytes() != self.payload
        ):
            raise RuntimeError("published output identity mismatch")

    def discard(self) -> None:
        if self.published or not (self.temporary.exists() or self.temporary.is_symlink()):
            return
        current = self.temporary.lstat()
        if (
            stat.S_ISREG(current.st_mode)
            and current.st_nlink == 1
            and current.st_dev == self.device
            and current.st_ino == self.inode
        ):
            self.temporary.unlink()
            fsync_directory(self.temporary.parent)
        else:
            raise RuntimeError("prepared output identity changed; preserved")


def reserve_full1g(
    witness: ReceiptWitness, terminal_pass: bool, purpose: str
) -> tuple[OwnedLock, dict[str, Any]]:
    payload = (
        json.dumps(
            {
                "owner_pid": os.getpid(),
                "purpose": purpose,
                "terminal_receipt_sha256": witness.sha256,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("ascii")
    lock = OwnedLock.acquire(LEASE_LOCK, payload)
    try:
        witness.revalidate()
        snapshot = closure_snapshot(witness.value, terminal_pass, lock)
    except Exception:
        lock.release()
        raise
    return lock, snapshot
