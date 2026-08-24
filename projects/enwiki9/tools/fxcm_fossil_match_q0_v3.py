#!/usr/bin/env python3
"""Execute two guarded zero-credit FOSSIL-MATCH v3 causal scans."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fxcm_fossil_match_q0_v3"
RESULT = PROJECT / "results" / CANDIDATE_ID
SOURCE = PROJECT / "programs/fxcm_fossil_match_q0_v3/fossil-match-scan.cpp"
INTERFACE = PROJECT / "programs/fxcm_fossil_match_q0_v3/interface-contract.json"
SCAN_SCHEMA = PROJECT / "programs/fxcm_fossil_match_q0_v3/scan-receipt.schema.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments/fxcm_fossil_match_q0_v3.json"
PROPOSAL = (
    PROJECT
    / "operations/adaptive/proposals/developed/000_fxcm_fossil_match_q0_v3.json"
)
CANDIDATE_REVISION = (
    PROJECT
    / "operations/adaptive/candidate-revisions/fxcm_fossil_match_q0_v3/"
    "20260824T065546247311Z_bff0b35e7ce1.json"
)
PLAN = PROJECT / "operations/planning/fxcm_fossil_match_q0_v3_execution.json"
PLAN_SCHEMA = PROJECT / "operations/planning/fxcm-fossil-match-execution-plan.schema.json"
DECISION_SCHEMA = PROJECT / "operations/planning/fxcm-fossil-match-decision.schema.json"
RESOURCE_SCHEMA = (
    PROJECT / "operations/planning/fxcm-fossil-match-resource-summary.schema.json"
)
MANIFEST_SCHEMA = (
    PROJECT / "operations/planning/fxcm-fossil-match-output-manifest.schema.json"
)
VERIFICATION_SCHEMA = (
    PROJECT / "operations/planning/fxcm-fossil-match-verification.schema.json"
)
PARENT_POLICY = (
    PROJECT
    / "operations/planning/"
    "cmix_obias_memory_safe_parent_filebacked_q1_qualification_policy_v4.json"
)
PARENT_RECEIPT_SCHEMA = (
    PROJECT
    / "contracts/research/v1/cmix-memory-safe-parent-qualification-receipt-v2.schema.json"
)
PARENT_VERIFICATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/"
    "cmix-memory-safe-parent-qualification-verification-v2.schema.json"
)
PARENT_VERIFIER = PROJECT / "tools/cmix_memory_safe_parent_qualification_verify_v2.py"
RESOURCE_GUARD = PROJECT / "tools/run_with_resource_guard_v3.py"
RESOURCE_GUARD_SCHEMA = (
    PROJECT / "contracts/research/v1/resource-guard-receipt.v3.schema.json"
)
LEASE_IMPLEMENTATION = PROJECT / "tools/managed_exclusive_lease.py"
LEASE_VERIFIER = PROJECT / "tools/managed_exclusive_lease_verify.py"
LEASE_SCHEMA = PROJECT / "operations/runtime/exclusive_full1g.schema.json"
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
LEASE_LOCK = PROJECT / "operations/runtime/exclusive_full1g.json.lock"
INPUT = Path(
    "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
    "cmix_lex_payload_transfer_v1_retry2/transformed_ready.bin"
)
COMPILER = Path(
    "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/lib/llvm-17/bin/clang"
)
LOADER_LIBRARY = Path(
    "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/lib/"
    "x86_64-linux-gnu/libLLVM-17.so.1"
)
LD_LIBRARY_PATH = LOADER_LIBRARY.parent
TASKSET = Path("/usr/bin/taskset")
CGROUP_A = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-fossil-match-v3-a"
)
CGROUP_B = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-fossil-match-v3-b"
)

INPUT_BYTES = 587_138_826
INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
REQUIRED_ACTIVE_BYTES = 254_953
TREE_LIMIT_KIB = 196_608
CGROUP_LIMIT_BYTES = 760_000_000
SCRATCH_LIMIT_BYTES = 100_000_000
CANDIDATE_TREE_SHA256 = (
    "bff0b35e7ce18439839bf7291d096f602908d455018bd6643122d7bbc899ed39"
)
COMPILE_FLAGS = [
    "--driver-mode=g++",
    "-std=c++17",
    "-O2",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-pedantic",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-march=x86-64",
    "-mtune=generic",
    "-Wl,--build-id=none",
]
BASE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}
COMPILE_ENVIRONMENT = {
    **BASE_ENVIRONMENT,
    "LD_LIBRARY_PATH": str(LD_LIBRARY_PATH),
}
CLAIM_BOUNDARY = (
    "Two guarded scans measure only causal far-history opportunity volume and "
    "matched-control association. They prove no arithmetic-code gain, inverse, "
    "package score, parent compatibility, or prize qualification."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT).as_posix()
    except ValueError:
        return str(resolved)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def artifact(path: Path, known_sha256: str | None = None) -> dict[str, Any]:
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"artifact is not regular: {path}")
    return {
        "path": display_path(path),
        "bytes": metadata.st_size,
        "sha256": known_sha256 or sha256(path),
    }


def write_bytes_exclusive(path: Path, raw: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    write_bytes_exclusive(
        path,
        (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )


def validate_with_schema(value: Any, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def assert_regular_no_symlink(path: Path, *, one_link: bool = False) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"symlink component is forbidden: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or (one_link and metadata.st_nlink != 1):
        raise RuntimeError(f"regular single-link artifact required: {path}")


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    resolved = path.resolve(strict=True) if path.is_absolute() else (PROJECT / path).resolve(strict=True)
    if not path.is_absolute() and PROJECT not in resolved.parents:
        raise RuntimeError(f"project-relative path escapes project: {value}")
    return resolved


def verify_reference(record: dict[str, Any], expected: Path | None = None) -> dict[str, Any]:
    path = resolve_project_path(record["path"])
    if expected is not None and path != expected.resolve(strict=True):
        raise RuntimeError(f"artifact path mismatch: {path} != {expected}")
    assert_regular_no_symlink(path)
    digest = sha256(path)
    if digest != record["sha256"]:
        raise RuntimeError(f"artifact digest mismatch: {path}")
    return artifact(path, digest)


def verify_policy_v4(policy: dict[str, Any]) -> None:
    contract = policy["contract"]
    if (
        policy["artifact_id"]
        != "cmix_obias_memory_safe_parent_filebacked_q1_qualification_policy_v4"
        or policy["operational_status"] != "dormant_dependency"
        or contract["v1_qualification_authority_revoked"] is not True
        or contract["v2_future_qualification_authority_revoked"] is not True
        or contract["v3_future_qualification_authority_revoked"] is not True
        or contract["engineering_parent_rss_ceiling_kib"] != 9_000_000
        or contract["hard_cgroup_memory_ceiling_bytes"] != 10_000_000_000
    ):
        raise RuntimeError("qualification policy v4 authority boundary mismatch")

    def verify_pairs(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                verify_pairs(item)
            return
        if not isinstance(value, dict):
            return
        if set(value) == {"path", "sha256"}:
            verify_reference(value)
            return
        for key, digest in value.items():
            if key.endswith("_sha256") and isinstance(digest, str):
                base = key.removesuffix("_sha256")
                candidate_path = value.get(base)
                if isinstance(candidate_path, str):
                    resolved = resolve_project_path(candidate_path)
                    if sha256(resolved) != digest:
                        raise RuntimeError(f"policy v4 closure mismatch: {candidate_path}")
        for child in value.values():
            verify_pairs(child)

    verify_pairs(contract)
    superseded = resolve_project_path(contract["supersedes"])
    if sha256(superseded) != contract["superseded_policy_sha256"]:
        raise RuntimeError("policy v4 superseded-policy binding mismatch")
    objective = PROJECT / "contracts/research/v1/objective-contract.json"
    if sha256(objective) != contract["objective_raw_sha256"]:
        raise RuntimeError("policy v4 objective binding mismatch")


def validate_parent(
    receipt_path: Path, verification_path: Path
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    for path in (receipt_path, verification_path):
        assert_regular_no_symlink(path, one_link=True)
        if PROJECT not in path.resolve(strict=True).parents:
            raise RuntimeError(f"parent evidence escapes project: {path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    validate_with_schema(receipt, PARENT_RECEIPT_SCHEMA)
    validate_with_schema(verification, PARENT_VERIFICATION_SCHEMA)
    receipt_digest = sha256(receipt_path)
    if (
        verification["verified"] is not True
        or verification["qualified"] is not True
        or verification["errors"] != []
        or verification["qualification_failures"] != []
        or verification["receipt_sha256"] != receipt_digest
        or not all(verification["checks"].values())
        or verification["claim_authority"] != "memory_safe_external_parent_only"
        or verification["promotion_authority"] is not True
        or verification["derived"]["maximum_tree_rss_kib"] > 9_000_000
        or verification["derived"]["maximum_cgroup_memory_bytes"]
        > 10_000_000_000
    ):
        raise RuntimeError("q1 parent qualification is not fully positive")

    policy = json.loads(PARENT_POLICY.read_text(encoding="utf-8"))
    verify_policy_v4(policy)
    if LEASE.exists() or LEASE_LOCK.exists():
        raise RuntimeError("exclusive full-1G namespace is occupied")
    with tempfile.TemporaryDirectory(prefix="gamma-fossil-parent-reverify-") as temporary:
        output = Path(temporary) / "verification.json"
        completed = subprocess.run(
            [
                "/usr/bin/python3",
                str(PARENT_VERIFIER),
                "--receipt",
                str(receipt_path),
                "--exclusive-lease",
                str(LEASE),
                "--verification",
                str(output),
            ],
            cwd=PROJECT,
            env=BASE_ENVIRONMENT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            close_fds=True,
        )
        if completed.returncode != 0 or not output.is_file():
            raise RuntimeError(
                "source-bound q1 independent reverification failed: "
                + completed.stderr.decode("utf-8", errors="replace")
            )
        reverified = json.loads(output.read_text(encoding="utf-8"))
        if reverified != verification:
            raise RuntimeError("q1 independent reverification differs from supplied evidence")
        reverified_raw = output.read_bytes()
    return artifact(receipt_path, receipt_digest), artifact(verification_path), reverified_raw


def validate_plan(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_with_schema(plan, PLAN_SCHEMA)
    expected_paths = {
        "source": SOURCE,
        "interface": INTERFACE,
        "scan_schema": SCAN_SCHEMA,
        "runner": Path(__file__).resolve(),
        "verifier": PROJECT / "tools/fxcm_fossil_match_q0_v3_verify.py",
    }
    bindings: dict[str, dict[str, Any]] = {}
    for key, path in expected_paths.items():
        record = {
            "path": plan["implementation"][key],
            "sha256": plan["implementation"][f"{key}_sha256"],
        }
        bindings[key] = verify_reference(record, path)
    bindings["candidate_revision"] = verify_reference(
        plan["candidate_revision"], CANDIDATE_REVISION
    )
    revision = json.loads(CANDIDATE_REVISION.read_text(encoding="utf-8"))
    if (
        revision["candidateId"] != CANDIDATE_ID
        or revision["candidateTreeSha256"]
        != f"sha256:{plan['candidate_revision']['candidate_tree_sha256']}"
        or plan["candidate_revision"]["candidate_tree_sha256"]
        != CANDIDATE_TREE_SHA256
    ):
        raise RuntimeError("candidate revision identity mismatch")
    bindings["experiment"] = verify_reference(plan["experiment"], EXPERIMENT)
    bindings["proposal"] = verify_reference(plan["proposal"], PROPOSAL)
    expected_schema_paths = {
        "plan": PLAN_SCHEMA,
        "decision": DECISION_SCHEMA,
        "resource_summary": RESOURCE_SCHEMA,
        "output_manifest": MANIFEST_SCHEMA,
        "verification": VERIFICATION_SCHEMA,
    }
    if set(plan["schemas"]) != set(expected_schema_paths):
        raise RuntimeError("execution schema role set mismatch")
    for key, path in expected_schema_paths.items():
        bindings[f"schema_{key}"] = verify_reference(plan["schemas"][key], path)
    parent_expected = {
        "policy": PARENT_POLICY,
        "receipt_schema": PARENT_RECEIPT_SCHEMA,
        "verification_schema": PARENT_VERIFICATION_SCHEMA,
        "verifier": PARENT_VERIFIER,
    }
    for key, path in parent_expected.items():
        bindings[f"parent_{key}"] = verify_reference(
            plan["parent_qualification"][key], path
        )
    bindings["lease_implementation"] = verify_reference(
        plan["exclusive_lane"]["implementation"], LEASE_IMPLEMENTATION
    )
    bindings["lease_schema"] = verify_reference(
        plan["exclusive_lane"]["schema"], LEASE_SCHEMA
    )
    bindings["lease_verifier"] = verify_reference(
        plan["exclusive_lane"]["verifier"], LEASE_VERIFIER
    )
    bindings["resource_guard"] = verify_reference(
        plan["resource_guard"]["implementation"], RESOURCE_GUARD
    )
    bindings["resource_guard_schema"] = verify_reference(
        plan["resource_guard"]["receipt_schema"], RESOURCE_GUARD_SCHEMA
    )
    toolchain = plan["toolchain"]
    for name, expected in (
        ("compiler", COMPILER),
        ("loader_library", LOADER_LIBRARY),
        ("taskset", TASKSET),
    ):
        path = Path(toolchain[name])
        assert_regular_no_symlink(path)
        digest = sha256(path)
        if path != expected or digest != toolchain[f"{name}_sha256"]:
            raise RuntimeError(f"toolchain binding mismatch: {name}")
        bindings[name] = artifact(path, digest)
    if (
        toolchain["ld_library_path"] != str(LD_LIBRARY_PATH)
        or toolchain["compile_flags"] != COMPILE_FLAGS
        or plan["population"]
        != {"path": str(INPUT), "bytes": INPUT_BYTES, "sha256": INPUT_SHA256}
        or plan["resource_guard"]["cgroup_a"] != str(CGROUP_A)
        or plan["resource_guard"]["cgroup_b"] != str(CGROUP_B)
        or plan["exclusive_lane"]["lease"] != display_path(LEASE)
        or plan["exclusive_lane"]["lock"] != display_path(LEASE_LOCK)
        or plan["command_template"]
        != [
            "python3",
            "tools/fxcm_fossil_match_q0_v3.py",
            "--parent-qualification-receipt",
            "<schema-valid-policy-v4-q1-qualification-receipt>",
            "--parent-qualification-verification",
            "<schema-valid-independent-policy-v4-q1-verification>",
        ]
        or plan["outputs"]
        != [
            "results/fxcm_fossil_match_q0_v3/lease-evidence.json",
            "results/fxcm_fossil_match_q0_v3/lease-transitions.json",
            "results/fxcm_fossil_match_q0_v3/scan-a.json",
            "results/fxcm_fossil_match_q0_v3/scan-b.json",
            "results/fxcm_fossil_match_q0_v3/resource-guard.json",
            "results/fxcm_fossil_match_q0_v3/decision.json",
            "results/fxcm_fossil_match_q0_v3/output-manifest.json",
        ]
    ):
        raise RuntimeError("execution plan constants mismatch")
    bindings["execution_plan"] = artifact(PLAN)
    bindings["execution_plan_schema"] = artifact(PLAN_SCHEMA)
    return bindings


def hash_population() -> str:
    assert_regular_no_symlink(INPUT, one_link=True)
    if INPUT.stat().st_size != INPUT_BYTES:
        raise RuntimeError("transformed population size mismatch")
    descriptor = os.open(INPUT, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    offset = 0
    try:
        while True:
            block = os.read(descriptor, 8 << 20)
            if not block:
                break
            digest.update(block)
            block_start = offset
            offset += len(block)
            if hasattr(os, "posix_fadvise"):
                os.posix_fadvise(
                    descriptor, block_start, len(block), os.POSIX_FADV_DONTNEED
                )
    finally:
        os.close(descriptor)
    if offset != INPUT_BYTES or digest.hexdigest() != INPUT_SHA256:
        raise RuntimeError("transformed population digest mismatch")
    return digest.hexdigest()


def read_cgroup_sample(path: Path) -> tuple[int, int]:
    try:
        current = int((path / "memory.current").read_text(encoding="ascii").strip())
        fields: dict[str, int] = {}
        for line in (path / "memory.stat").read_text(encoding="ascii").splitlines():
            name, value = line.split()
            fields[name] = int(value)
        return current, fields.get("file", 0)
    except (FileNotFoundError, PermissionError, ValueError):
        return 0, 0


def run_command(
    *,
    step_id: str,
    argv: list[str],
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    lease: Any | None = None,
    cgroup_path: Path | None = None,
) -> tuple[dict[str, Any], int, int]:
    process = subprocess.Popen(
        argv,
        cwd=PROJECT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    current_peak = 0
    file_peak = 0
    last_heartbeat = time.monotonic()
    while True:
        try:
            stdout, stderr = process.communicate(timeout=0.5)
            break
        except subprocess.TimeoutExpired:
            now = time.monotonic()
            if lease is not None and now - last_heartbeat >= 10:
                lease.heartbeat()
                last_heartbeat = now
            if cgroup_path is not None:
                current, file_bytes = read_cgroup_sample(cgroup_path)
                current_peak = max(current_peak, current)
                file_peak = max(file_peak, file_bytes)
    if cgroup_path is not None:
        current, file_bytes = read_cgroup_sample(cgroup_path)
        current_peak = max(current_peak, current)
        file_peak = max(file_peak, file_bytes)
    write_bytes_exclusive(stdout_path, stdout)
    write_bytes_exclusive(stderr_path, stderr)
    command = {"argv": argv, "cwd": str(PROJECT), "environment": environment}
    return (
        {
            "id": step_id,
            **command,
            "command_sha256": canonical_sha256(command),
            "returncode": process.returncode,
            "stdout": artifact(stdout_path),
            "stderr": artifact(stderr_path),
        },
        current_peak,
        file_peak,
    )


def scan_command(binary: Path, output: Path, guard: Path, cgroup: Path, arm: str) -> list[str]:
    return [
        "/usr/bin/python3",
        str(RESOURCE_GUARD),
        "--limit-kib",
        str(TREE_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        "9765625",
        "--cgroup-path",
        str(cgroup),
        "--cgroup-memory-max-bytes",
        str(CGROUP_LIMIT_BYTES),
        "--scratch-path",
        str(RESULT),
        "--temporary-disk-limit-bytes",
        str(SCRATCH_LIMIT_BYTES),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard),
        "--label",
        f"fossil-match-v3-{arm}",
        "--phase",
        "diagnostic",
        "--",
        str(TASKSET),
        "--cpu-list",
        "0",
        str(binary),
        str(INPUT),
        str(output),
    ]


def semantic_scan_checks(summary: dict[str, Any]) -> None:
    if (
        summary["positions_scored"] != INPUT_BYTES - 16
        or summary["table_lookups"] != summary["positions_scored"]
        or summary["table_replacements"] != summary["positions_scored"]
        or summary["ring_writes"] != INPUT_BYTES
        or summary["hash_rolls"] != summary["positions_scored"]
        or summary["causal_and_verification_pass"] is not True
        or summary["treatment_k_state_identity_pass"] is not True
        or summary["control_outcomes_feed_state"] is not False
    ):
        raise RuntimeError("scanner transition invariants failed")
    lookup_partition = sum(
        summary[name]
        for name in (
            "table_empty",
            "table_tag_mismatches",
            "invalid_continuations",
            "context_verification_failures",
            "distance_suppressed",
            "active_bytes",
        )
    )
    if lookup_partition != summary["table_lookups"]:
        raise RuntimeError("scanner lookup partition mismatch")
    for rows in (
        summary["correct_by_third"],
        summary["correct_by_distance_bucket"],
    ):
        if sum(row["active"] for row in rows) != summary["active_bytes"]:
            raise RuntimeError("scanner active partition mismatch")
        for key, total in (
            ("D", summary["treatment_correct_bytes"]),
            ("S", summary["alias_correct_bytes"]),
            ("R", summary["random_correct_bytes"]),
            ("N", summary["negated_correct_bytes"]),
        ):
            if sum(row[key] for row in rows) != total:
                raise RuntimeError(f"scanner {key} partition mismatch")


def validate_guard(guard: dict[str, Any]) -> None:
    validate_with_schema(guard, RESOURCE_GUARD_SCHEMA)
    if (
        guard["schema"] != "gamma.enwiki9.resource-guard-receipt.v3"
        or guard["status"] != "complete"
        or guard["returncode"] != 0
        or any(guard["guards"].values())
        or not all(guard["measurements"].values())
        or guard["peaks"]["max_sampled_tree_rss_kib"] > TREE_LIMIT_KIB
        or guard["peaks"]["max_observed_process_vmhwm_kib"] > TREE_LIMIT_KIB
        or guard["peaks"]["cgroup_memory_peak_bytes"] > CGROUP_LIMIT_BYTES
        or guard["peaks"]["max_sampled_scratch_logical_bytes"]
        > SCRATCH_LIMIT_BYTES
        or guard["cgroup_events"]["delta"]["max"] != 0
        or guard["cgroup_events"]["delta"]["oom"] != 0
        or guard["cgroup_events"]["delta"]["oom_kill"] != 0
    ):
        raise RuntimeError("scanner resource guard did not pass")


def resource_summary(
    guards: dict[str, dict[str, Any]], scans: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    values = list(guards.values())
    summary = {
        "schema": "gamma.enwiki9.fxcm-fossil-match-resource-summary.v1",
        "candidate_id": CANDIDATE_ID,
        "arms": {arm: scans[arm]["guard"] for arm in ("a", "b")},
        "maximum_tree_rss_kib": max(
            guard["peaks"]["max_sampled_tree_rss_kib"] for guard in values
        ),
        "maximum_process_vmhwm_kib": max(
            guard["peaks"]["max_observed_process_vmhwm_kib"] for guard in values
        ),
        "maximum_cgroup_memory_bytes": max(
            guard["peaks"]["cgroup_memory_peak_bytes"] for guard in values
        ),
        "maximum_sampled_cgroup_file_bytes": max(
            scans[arm]["sampled_cgroup_file_peak_bytes"] for arm in ("a", "b")
        ),
        "maximum_scratch_logical_bytes": max(
            guard["peaks"]["max_sampled_scratch_logical_bytes"] for guard in values
        ),
        "maximum_scratch_allocated_bytes": max(
            guard["peaks"]["max_sampled_scratch_allocated_bytes"] for guard in values
        ),
        "cgroup_max_events": sum(
            guard["cgroup_events"]["delta"]["max"] for guard in values
        ),
        "cgroup_oom_events": sum(
            guard["cgroup_events"]["delta"]["oom"] for guard in values
        ),
        "cgroup_oom_kill_events": sum(
            guard["cgroup_events"]["delta"]["oom_kill"] for guard in values
        ),
        "all_resource_predicates_pass": True,
    }
    summary["all_resource_predicates_pass"] = (
        summary["maximum_tree_rss_kib"] <= TREE_LIMIT_KIB
        and summary["maximum_process_vmhwm_kib"] <= TREE_LIMIT_KIB
        and summary["maximum_cgroup_memory_bytes"] <= CGROUP_LIMIT_BYTES
        and summary["maximum_scratch_logical_bytes"] <= SCRATCH_LIMIT_BYTES
        and summary["cgroup_max_events"] == 0
        and summary["cgroup_oom_events"] == 0
        and summary["cgroup_oom_kill_events"] == 0
    )
    validate_with_schema(summary, RESOURCE_SCHEMA)
    return summary


def empty_scan() -> dict[str, Any]:
    return {
        "command": None,
        "receipt": None,
        "guard": None,
        "sampled_cgroup_file_peak_bytes": None,
        "sampled_cgroup_current_peak_bytes": None,
    }


def empty_gates() -> dict[str, None]:
    return {
        "full_population_pass": None,
        "target_scale_envelope_pass": None,
        "all_thirds_beat_controls_pass": None,
        "distance_transfer_pass": None,
        "repeat_identity_pass": None,
        "causal_verification_pass": None,
        "resource_pass": None,
        "all_promotion_predicates_pass": None,
    }


def result_manifest(complete: bool) -> dict[str, Any]:
    roles = [
        ("lease_evidence", "lease-evidence.json"),
        ("lease_transitions", "lease-transitions.json"),
        ("parent_reverification", "parent-reverification.json"),
        ("compile_stdout", "compile.stdout"),
        ("compile_stderr", "compile.stderr"),
        ("scanner_binary", "fossil-match-scan"),
        ("scan_a_receipt", "scan-a.json"),
        ("scan_a_guard", "guard-a.json"),
        ("scan_a_stdout", "scan-a.stdout"),
        ("scan_a_stderr", "scan-a.stderr"),
        ("scan_b_receipt", "scan-b.json"),
        ("scan_b_guard", "guard-b.json"),
        ("scan_b_stdout", "scan-b.stdout"),
        ("scan_b_stderr", "scan-b.stderr"),
        ("resource_summary", "resource-guard.json"),
        ("decision", "decision.json"),
    ]
    artifacts = []
    for role, relative in roles:
        path = RESULT / relative
        if path.is_file():
            record = artifact(path)
            record["role"] = role
            record["path"] = relative
            artifacts.append(record)
    observed = sorted(path.name for path in RESULT.iterdir())
    expected = {relative for _, relative in roles}
    exact = set(observed) == expected and all(
        path.is_file() and not path.is_symlink() for path in RESULT.iterdir()
    )
    manifest = {
        "schema": "gamma.enwiki9.fxcm-fossil-match-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "result_root": f"results/{CANDIDATE_ID}",
        "pre_manifest_exact_file_set_pass": exact,
        "unexpected_pre_manifest_entries": sorted(set(observed) - expected),
        "complete_result_artifacts_pass": complete and exact and len(artifacts) == len(roles),
        "artifacts": artifacts,
    }
    validate_with_schema(manifest, MANIFEST_SCHEMA)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-qualification-receipt", required=True, type=Path)
    parser.add_argument("--parent-qualification-verification", required=True, type=Path)
    args = parser.parse_args()
    receipt_path = args.parent_qualification_receipt
    if not receipt_path.is_absolute():
        receipt_path = PROJECT / receipt_path
    verification_path = args.parent_qualification_verification
    if not verification_path.is_absolute():
        verification_path = PROJECT / verification_path

    if RESULT.exists() or RESULT.is_symlink():
        raise FileExistsError(f"refusing to overwrite result root: {RESULT}")
    for path in (CGROUP_A, CGROUP_B, LEASE, LEASE_LOCK):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"exclusive execution namespace occupied: {path}")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    bindings = validate_plan(plan)
    parent_receipt, parent_verification, parent_reverification = validate_parent(
        receipt_path, verification_path
    )
    preflight_hashes = {
        path: sha256(path)
        for path in (
            PLAN,
            SOURCE,
            INTERFACE,
            SCAN_SCHEMA,
            EXPERIMENT,
            PROPOSAL,
            CANDIDATE_REVISION,
            PARENT_POLICY,
            receipt_path,
            verification_path,
        )
    }

    RESULT.mkdir(mode=0o700, parents=True)
    invocation = {
        "argv": [str(Path(__file__).resolve()), *sys.argv[1:]],
        "cwd": str(PROJECT),
        "environment": BASE_ENVIRONMENT,
    }
    from managed_exclusive_lease import ManagedExclusiveLease

    try:
        lease = ManagedExclusiveLease.acquire(
            lease_path=LEASE,
            transition_path=RESULT / "lease-transitions.json",
            candidate_id=CANDIDATE_ID,
            command_sha256=canonical_sha256(invocation),
            runner_sha256=bindings["runner"]["sha256"],
            guard_path=str(RESULT),
            result_path=str(RESULT),
            scratch_path=str(RESULT),
            claim_boundary=(
                "Managed exclusive lane for two zero-credit FOSSIL-MATCH scans; "
                "no signal authority."
            ),
        )
    except Exception:
        RESULT.rmdir()
        raise

    write_bytes_exclusive(RESULT / "parent-reverification.json", parent_reverification)
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.fxcm-fossil-match-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal_infrastructure_failure",
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_authority": "causal_shadow_opportunity_screen_only",
        "bindings": bindings,
        "parent_qualification": {
            "receipt": parent_receipt,
            "verification": parent_verification,
            "independent_reverification": artifact(RESULT / "parent-reverification.json"),
            "policy_v4": artifact(PARENT_POLICY),
            "fully_positive": True,
        },
        "population": {
            "path": str(INPUT),
            "bytes": INPUT_BYTES,
            "sha256": INPUT_SHA256,
            "verified": False,
        },
        "exclusive_lease": {
            "lease_id": lease.record["lease_id"],
            "release_pass": False,
            "evidence": None,
            "transitions": None,
        },
        "compile": None,
        "scans": {"a": empty_scan(), "b": empty_scan()},
        "resource_summary": None,
        "measurements": None,
        "gates": empty_gates(),
        "scientific_verdict": "none_infrastructure_failure",
        "promotion_authorized": False,
        "next_authority": "one_correction_only_runner_successor",
        "archive_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
        "error": None,
    }
    try:
        population_digest = hash_population()
        decision["population"]["verified"] = population_digest == INPUT_SHA256
        lease.heartbeat()
        binary = RESULT / "fossil-match-scan"
        compile_command, _, _ = run_command(
            step_id="compile",
            argv=[str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)],
            environment=COMPILE_ENVIRONMENT,
            stdout_path=RESULT / "compile.stdout",
            stderr_path=RESULT / "compile.stderr",
            lease=lease,
        )
        decision["compile"] = compile_command
        if compile_command["returncode"] != 0:
            raise RuntimeError("scanner compilation failed")

        scans: dict[str, dict[str, Any]] = {}
        guard_values: dict[str, dict[str, Any]] = {}
        for arm, cgroup in (("a", CGROUP_A), ("b", CGROUP_B)):
            receipt = RESULT / f"scan-{arm}.json"
            guard_path = RESULT / f"guard-{arm}.json"
            command, current_peak, file_peak = run_command(
                step_id=f"scan_{arm}",
                argv=scan_command(binary, receipt, guard_path, cgroup, arm),
                environment=BASE_ENVIRONMENT,
                stdout_path=RESULT / f"scan-{arm}.stdout",
                stderr_path=RESULT / f"scan-{arm}.stderr",
                lease=lease,
                cgroup_path=cgroup,
            )
            if command["returncode"] != 0 or not receipt.is_file() or not guard_path.is_file():
                raise RuntimeError(f"scanner arm {arm} failed")
            summary = json.loads(receipt.read_text(encoding="utf-8"))
            guard = json.loads(guard_path.read_text(encoding="utf-8"))
            validate_with_schema(summary, SCAN_SCHEMA)
            semantic_scan_checks(summary)
            validate_guard(guard)
            if cgroup.exists():
                raise RuntimeError(f"scanner cgroup {arm} was not cleaned")
            scans[arm] = {
                "command": command,
                "receipt": artifact(receipt),
                "guard": artifact(guard_path),
                "sampled_cgroup_file_peak_bytes": file_peak,
                "sampled_cgroup_current_peak_bytes": current_peak,
            }
            guard_values[arm] = guard
            decision["scans"][arm] = scans[arm]
            lease.heartbeat()

        summary_a = json.loads((RESULT / "scan-a.json").read_text(encoding="utf-8"))
        summary_b = json.loads((RESULT / "scan-b.json").read_text(encoding="utf-8"))
        repeat_identity = (RESULT / "scan-a.json").read_bytes() == (
            RESULT / "scan-b.json"
        ).read_bytes()
        resources = resource_summary(guard_values, scans)
        write_json_exclusive(RESULT / "resource-guard.json", resources)
        decision["resource_summary"] = artifact(RESULT / "resource-guard.json")
        measurements = {
            "scanned_bytes": summary_a["population_bytes"],
            "active_bytes": summary_a["active_bytes"],
            "treatment_correct_bytes": summary_a["treatment_correct_bytes"],
            "alias_correct_bytes": summary_a["alias_correct_bytes"],
            "random_correct_bytes": summary_a["random_correct_bytes"],
            "negated_correct_bytes": summary_a["negated_correct_bytes"],
            "minimum_third_treatment_minus_max_control_correct_bytes": summary_a[
                "minimum_third_treatment_minus_max_control_correct_bytes"
            ],
            "positive_distance_bucket_count": summary_a[
                "positive_distance_bucket_count"
            ],
            "opportunity_fnv1a64": summary_a["opportunity_fnv1a64"],
            "repeat_identity_pass": repeat_identity,
            "maximum_tree_rss_kib": resources["maximum_tree_rss_kib"],
            "maximum_cgroup_memory_bytes": resources["maximum_cgroup_memory_bytes"],
            "maximum_sampled_cgroup_file_bytes": resources[
                "maximum_sampled_cgroup_file_bytes"
            ],
        }
        gates = {
            "full_population_pass": measurements["scanned_bytes"] == INPUT_BYTES,
            "target_scale_envelope_pass": measurements["active_bytes"]
            >= REQUIRED_ACTIVE_BYTES,
            "all_thirds_beat_controls_pass": measurements[
                "minimum_third_treatment_minus_max_control_correct_bytes"
            ]
            > 0,
            "distance_transfer_pass": measurements["positive_distance_bucket_count"]
            >= 2,
            "repeat_identity_pass": repeat_identity and summary_a == summary_b,
            "causal_verification_pass": summary_a["causal_and_verification_pass"]
            is True,
            "resource_pass": resources["all_resource_predicates_pass"] is True,
            "all_promotion_predicates_pass": False,
        }
        gates["all_promotion_predicates_pass"] = all(
            value
            for key, value in gates.items()
            if key != "all_promotion_predicates_pass"
        )
        for path, digest in preflight_hashes.items():
            if sha256(path) != digest:
                raise RuntimeError(f"source or antecedent drifted during execution: {path}")
        passed = gates["all_promotion_predicates_pass"]
        decision.update(
            {
                "operational_status": "terminal",
                "measurements": measurements,
                "gates": gates,
                "scientific_verdict": (
                    "authorize_retained_parent_surprisal_trace_zero_credit"
                    if passed
                    else "retire_exact_fossil_match_information_source"
                ),
                "promotion_authorized": passed,
                "next_authority": (
                    "retained_parent_surprisal_trace_only"
                    if passed
                    else "one_materially_different_information_source"
                ),
            }
        )
    except Exception as error:
        decision["error"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            lease.heartbeat()
            lease.release(evidence_path=RESULT / "lease-evidence.json")
            decision["exclusive_lease"] = {
                "lease_id": lease.record["lease_id"],
                "release_pass": True,
                "evidence": artifact(RESULT / "lease-evidence.json"),
                "transitions": artifact(RESULT / "lease-transitions.json"),
            }
        except Exception as lease_error:
            message = f"lease release failure: {type(lease_error).__name__}: {lease_error}"
            decision["error"] = (
                message if decision["error"] is None else f"{decision['error']}; {message}"
            )
            decision.update(
                {
                    "operational_status": "terminal_infrastructure_failure",
                    "scientific_verdict": "none_infrastructure_failure",
                    "promotion_authorized": False,
                    "next_authority": "one_correction_only_runner_successor",
                }
            )

    validate_with_schema(decision, DECISION_SCHEMA)
    write_json_exclusive(RESULT / "decision.json", decision)
    manifest = result_manifest(decision["operational_status"] == "terminal")
    write_json_exclusive(RESULT / "output-manifest.json", manifest)
    return 0 if decision["operational_status"] == "terminal" else 1


if __name__ == "__main__":
    raise SystemExit(main())
