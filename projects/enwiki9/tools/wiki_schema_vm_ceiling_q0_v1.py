#!/usr/bin/env python3
"""Build and repeat the sealed zero-credit WIKI-SCHEMA-VM ceiling scanner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
CANDIDATE_ID = "wiki_schema_vm_ceiling_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID
SOURCE = PROJECT / "programs/wiki_schema_vm_ceiling_q0_v1/schema-vm-scan.cpp"
INTERFACE = PROJECT / "programs/wiki_schema_vm_ceiling_q0_v1/interface-contract.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments/wiki_schema_vm_ceiling_q0_v1.json"
PROPOSAL = (
    PROJECT
    / "operations/adaptive/proposals/developed/000_wiki_schema_vm_ceiling_q0_v1.json"
)
CANDIDATE_REVISION = (
    PROJECT
    / "operations/adaptive/candidate-revisions/wiki_schema_vm_ceiling_q0_v1/"
    "20260824T030345533597Z_0e08910e5a25.json"
)
PLAN = PROJECT / "operations/planning/wiki_schema_vm_ceiling_q0_v1.json"
PLAN_SCHEMA = PROJECT / "contracts/research/v1/wiki-schema-vm-ceiling-plan.schema.json"
SCAN_SCHEMA = PROJECT / "contracts/research/v1/wiki-schema-vm-scan.schema.json"
DECISION_SCHEMA = (
    PROJECT / "contracts/research/v1/wiki-schema-vm-ceiling-decision.schema.json"
)
MANIFEST_SCHEMA = (
    PROJECT / "contracts/research/v1/wiki-schema-vm-output-manifest.schema.json"
)
PARENT_QUALIFICATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/cmix-memory-safe-parent-qualification-receipt-v2.schema.json"
)
PARENT_VERIFICATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/cmix-memory-safe-parent-qualification-verification-v2.schema.json"
)
MANAGED_LEASE_IMPLEMENTATION = PROJECT / "tools/managed_exclusive_lease.py"
EXCLUSIVE_LEASE_SCHEMA = PROJECT / "operations/runtime/exclusive_full1g.schema.json"
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
LEASE_LOCK = PROJECT / "operations/runtime/exclusive_full1g.json.lock"
INPUT = Path(
    "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
    "cmix_lex_payload_transfer_v1_retry2/transformed_ready.bin"
)
COMPILER = Path(
    "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin/clang++-17"
)

INPUT_BYTES = 587_138_826
INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
REQUIRED_CORRECT_BYTES = 4_079_243
REQUIRED_OPPORTUNITY_BYTES = 254_953
MAX_OPTIMISTIC_GAIN_BYTES_PER_OPPORTUNITY = 16
CANDIDATE_TREE_SHA256 = (
    "sha256:0e08910e5a25a2dd3f57f94a915bbe9a14b2abc750db1fe4bcc58e9473ba958a"
)
EXPECTED_SHA256 = {
    EXPERIMENT: "457afbd9c70b244ebd7d72b7e155bc3b4caea07de84aff963a90c02b00923ecf",
    PROPOSAL: "b5fd8a87b958d15d14c34dc94da03f7f99e1f0a52dce31e70a7378e91cd2eea7",
    CANDIDATE_REVISION: "41f8bfa04a93fe4cd1e82c8b9d79409d60438a1a3aee8e3fb8bbfcf2114f74c7",
    INTERFACE: "dca250e6df422898fa20b398123e9a9acd5445994331a8aa00e54f3e47612c4b",
    SOURCE: "d54ff0bb169f44ca695f943d6a119c9a780783479b3187ecdbc88322c3732691",
    PLAN_SCHEMA: "eba9d1e74f908d40ff58447845a023f7a2ae7ed6ca26291f6d2102158690fa41",
    SCAN_SCHEMA: "f2519e7c88436e1d95995558dfc36d886bba2dca69d08d4f07db01ce3e1e9ae2",
    DECISION_SCHEMA: "6356dda2a97acc78b561eb3e96dfaf87d7c17417b39b53dbac3eb06818f62eca",
    MANIFEST_SCHEMA: "b054e1e6c06f514681aef13d7890ef1b87c1f314d61e8583389e183cd8f842eb",
    PARENT_QUALIFICATION_SCHEMA: "1863e57073cf937e036b29d69b59467c8dbd167adedb36f61246a0bc02465494",
    PARENT_VERIFICATION_SCHEMA: "3bcf47489de593d541504b06a9735979701d1da08bf8cc70253339f05538a74d",
    MANAGED_LEASE_IMPLEMENTATION: "c3cedd46af3c3cbe8969ae9961e4b16b2d6df5873cd0a761c54b5d53ffd053b1",
    EXCLUSIVE_LEASE_SCHEMA: "96a97198bb004df485ce8f910f9645e87bfa9287bfda09c57d3f59b3cf5ebb96",
    COMPILER: "011362d67c1a55636e9e1fa8fb87705980ebe94037213686897e1dadba007e43",
}
COMPILE_FLAGS = [
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
ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}
CLAIM_BOUNDARY = (
    "Two exact passes over the frozen post-WRT transformed population measure only "
    "causal opportunity volume and association controls. Their 16-byte-per-active-byte "
    "quantized log-loss envelope is optimistic; they prove no arithmetic-code gain, "
    "inverse, package score, parent compatibility, or prize qualification."
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


def artifact(path: Path, known_sha256: str | None = None) -> dict[str, Any]:
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"artifact is not a regular file: {path}")
    return {
        "path": display_path(path),
        "bytes": metadata.st_size,
        "sha256": known_sha256 or sha256(path),
    }


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_bytes_exclusive(path: Path, data: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short output write")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_bytes_exclusive(path, data)


def validate_with_schema(value: Any, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def assert_no_symlink_components(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"symlink component is forbidden: {current}")


def verify_locked_file(path: Path, expected_sha256: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"locked file is missing, non-regular, or a symlink: {path}")
    actual = sha256(path)
    if actual != expected_sha256:
        raise RuntimeError(
            f"locked file SHA-256 mismatch: {path}: expected {expected_sha256}, got {actual}"
        )
    return artifact(path, actual)


def validate_planning_contract(plan: dict[str, Any], runner_sha256: str) -> None:
    validate_with_schema(plan, PLAN_SCHEMA)
    if plan["planning_schema_sha256"] != EXPECTED_SHA256[PLAN_SCHEMA]:
        raise RuntimeError("planning schema digest mismatch")
    expected_bindings = (
        (plan["candidate_revision"], CANDIDATE_REVISION, EXPECTED_SHA256[CANDIDATE_REVISION]),
        (plan["experiment"], EXPERIMENT, EXPECTED_SHA256[EXPERIMENT]),
        (plan["proposal"], PROPOSAL, EXPECTED_SHA256[PROPOSAL]),
    )
    for record, path, digest in expected_bindings:
        if record.get("path") != display_path(path) or record.get("sha256") != digest:
            raise RuntimeError(f"planning artifact binding mismatch: {path}")
    if plan["candidate_revision"]["candidate_tree_sha256"] != CANDIDATE_TREE_SHA256.removeprefix(
        "sha256:"
    ):
        raise RuntimeError("planning candidate-tree binding mismatch")
    expected_implementation = {
        "source": display_path(SOURCE),
        "source_sha256": EXPECTED_SHA256[SOURCE],
        "interface": display_path(INTERFACE),
        "interface_sha256": EXPECTED_SHA256[INTERFACE],
        "runner": display_path(Path(__file__).resolve()),
        "runner_sha256": runner_sha256,
    }
    if plan["implementation"] != expected_implementation:
        raise RuntimeError("planning implementation closure mismatch")
    expected_schemas = {
        "plan": display_path(PLAN_SCHEMA),
        "scan": display_path(SCAN_SCHEMA),
        "scan_sha256": EXPECTED_SHA256[SCAN_SCHEMA],
        "decision": display_path(DECISION_SCHEMA),
        "decision_sha256": EXPECTED_SHA256[DECISION_SCHEMA],
        "output_manifest": display_path(MANIFEST_SCHEMA),
        "output_manifest_sha256": EXPECTED_SHA256[MANIFEST_SCHEMA],
    }
    if plan["schemas"] != expected_schemas:
        raise RuntimeError("planning schema closure mismatch")
    expected_lane = {
        "implementation": display_path(MANAGED_LEASE_IMPLEMENTATION),
        "implementation_sha256": EXPECTED_SHA256[MANAGED_LEASE_IMPLEMENTATION],
        "schema": display_path(EXCLUSIVE_LEASE_SCHEMA),
        "schema_sha256": EXPECTED_SHA256[EXCLUSIVE_LEASE_SCHEMA],
        "policy": plan["exclusive_lane"]["policy"],
    }
    if plan["exclusive_lane"] != expected_lane:
        raise RuntimeError("planning exclusive-lane closure mismatch")
    if plan["population"] != {
        "path": str(INPUT),
        "bytes": INPUT_BYTES,
        "sha256": INPUT_SHA256,
    }:
        raise RuntimeError("planning population binding mismatch")
    if plan["command_template"] != [
        "python3",
        display_path(Path(__file__).resolve()),
        "--parent-qualification-receipt",
        "<schema-valid-q1-qualification-receipt>",
        "--parent-qualification-verification",
        "<schema-valid-independent-q1-verification>",
    ]:
        raise RuntimeError("planning command template mismatch")
    if plan["outputs"] != [
        f"results/{CANDIDATE_ID}/lease-evidence.json",
        f"results/{CANDIDATE_ID}/lease-transitions.json",
        f"results/{CANDIDATE_ID}/scan-a.json",
        f"results/{CANDIDATE_ID}/scan-b.json",
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/output-manifest.json",
    ]:
        raise RuntimeError("planning output-set mismatch")


def proc_start_ticks(pid: int) -> int | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()
        return int(fields[21])
    except (FileNotFoundError, IndexError, ValueError):
        return None


def assert_exclusive_host_released() -> None:
    if LEASE_LOCK.exists():
        raise RuntimeError(f"exclusive full-1G lease lock exists: {LEASE_LOCK}")
    if not LEASE.is_file():
        return
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    pid = lease.get("pid")
    start_ticks = lease.get("proc_start_ticks")
    if isinstance(pid, int) and proc_start_ticks(pid) == start_ticks:
        raise RuntimeError(f"exclusive full-1G lease remains active for PID {pid}")
    codec_pid = lease.get("codec_pid")
    if isinstance(codec_pid, int) and Path(f"/proc/{codec_pid}").exists():
        raise RuntimeError(f"exclusive full-1G codec PID remains active: {codec_pid}")


def run_command(
    step_id: str,
    argv: list[str],
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=PROJECT,
        env=ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        close_fds=True,
    )
    write_bytes_exclusive(stdout_path, completed.stdout)
    write_bytes_exclusive(stderr_path, completed.stderr)
    command_contract = {
        "argv": argv,
        "cwd": str(PROJECT),
        "environment": ENVIRONMENT,
    }
    return {
        "id": step_id,
        **command_contract,
        "command_sha256": canonical_sha256(command_contract),
        "returncode": completed.returncode,
        "stdout": artifact(stdout_path),
        "stderr": artifact(stderr_path),
    }


def semantic_scan_checks(summary: dict[str, Any]) -> None:
    opportunities = summary["opportunity_bytes"]
    for name in (
        "treatment_correct_bytes",
        "random_correct_bytes",
        "shifted_correct_bytes",
    ):
        if summary[name] > opportunities:
            raise RuntimeError(f"{name} exceeds the matched opportunity population")
    if summary["treatment_minus_random_correct_bytes"] != (
        summary["treatment_correct_bytes"] - summary["random_correct_bytes"]
    ):
        raise RuntimeError("treatment-minus-random arithmetic mismatch")
    if summary["treatment_minus_shifted_correct_bytes"] != (
        summary["treatment_correct_bytes"] - summary["shifted_correct_bytes"]
    ):
        raise RuntimeError("treatment-minus-shifted arithmetic mismatch")
    if summary["minimum_third_treatment_correct_bytes"] != min(
        summary["treatment_correct_by_third"]
    ):
        raise RuntimeError("chronological-third minimum mismatch")
    if sum(summary["treatment_correct_by_third"]) != summary["treatment_correct_bytes"]:
        raise RuntimeError("chronological-third treatment total mismatch")
    if summary["templates_completed"] > summary["templates_opened"]:
        raise RuntimeError("completed-template count exceeds opens")
    if summary["table_hits"] > summary["table_lookups"]:
        raise RuntimeError("table hits exceed lookups")
    if summary["table_updates"] != summary["completed_template_updates"]:
        raise RuntimeError("table updates were not exclusively close-committed")


def validate_parent_qualification(
    receipt_path: Path, verification_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    for path in (receipt_path, verification_path):
        assert_no_symlink_components(path)
        resolved = path.resolve(strict=True)
        if PROJECT not in resolved.parents:
            raise RuntimeError(f"parent qualification artifact escapes project: {path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    validate_with_schema(receipt, PARENT_QUALIFICATION_SCHEMA)
    validate_with_schema(verification, PARENT_VERIFICATION_SCHEMA)

    receipt_sha256 = sha256(receipt_path)
    if (
        receipt["schema"] != "gamma.enwiki9.cmix-memory-safe-parent-qualification-receipt.v2"
        or receipt["candidate_id"] != "cmix_obias_memory_safe_parent_filebacked_q1_v1"
    ):
        raise RuntimeError("q1 v2 qualification router identity mismatch")
    if (
        verification["schema"] != "gamma.enwiki9.cmix-memory-safe-parent-qualification-verification.v2"
        or verification["verified"] is not True
        or verification["qualified"] is not True
        or verification["errors"] != []
        or verification["qualification_failures"] != []
        or verification["receipt_sha256"] != receipt_sha256
        or not all(verification["checks"].values())
        or verification["claim_authority"] != "memory_safe_external_parent_only"
        or verification["promotion_authority"] is not True
    ):
        raise RuntimeError("independent q1 qualification verification is not fully positive")
    derived = verification["derived"]
    if (
        derived["maximum_tree_rss_kib"] > 9_000_000
        or derived["maximum_cgroup_memory_bytes"] >= 10_000_000_000
        or derived["geekbench5_single_core_score"] is None
        or derived["runtime_limit_seconds"] is None
    ):
        raise RuntimeError("q1 qualification lacks engineering headroom, runtime, or closure")
    return artifact(receipt_path, receipt_sha256), artifact(verification_path)


def empty_gates() -> dict[str, None]:
    return {
        "full_population_pass": None,
        "target_scale_quantized_log_loss_envelope_pass": None,
        "one_byte_per_correct_volume_screen_pass": None,
        "all_thirds_live_pass": None,
        "beats_random_pass": None,
        "beats_shifted_pass": None,
        "repeat_identity_pass": None,
        "bounded_state_pass": None,
        "all_promotion_predicates_pass": None,
    }


def result_manifest(complete: bool) -> dict[str, Any]:
    roles = [
        ("lease_evidence", "lease-evidence.json"),
        ("lease_transitions", "lease-transitions.json"),
        ("compile_stdout", "compile.stdout"),
        ("compile_stderr", "compile.stderr"),
        ("scanner_binary", "wiki-schema-vm-scan"),
        ("scan_a_receipt", "scan-a.json"),
        ("scan_a_stdout", "scan-a.stdout"),
        ("scan_a_stderr", "scan-a.stderr"),
        ("scan_b_receipt", "scan-b.json"),
        ("scan_b_stdout", "scan-b.stdout"),
        ("scan_b_stderr", "scan-b.stderr"),
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
    expected_roles = {role for role, _ in roles}
    expected_files = {relative for _, relative in roles}
    actual_roles = {record["role"] for record in artifacts}
    observed_entries = sorted(path.name for path in RESULT.iterdir())
    unexpected_entries = sorted(set(observed_entries) - expected_files)
    exact_file_set = (
        set(observed_entries) == expected_files
        and all(
            path.is_file() and not path.is_symlink()
            for path in RESULT.iterdir()
        )
    )
    return {
        "schema": "gamma.enwiki9.wiki-schema-vm-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "result_root": "results/wiki_schema_vm_ceiling_q0_v1",
        "pre_manifest_exact_file_set_pass": exact_file_set,
        "unexpected_pre_manifest_entries": unexpected_entries,
        "complete_result_artifacts_pass": (
            complete and exact_file_set and actual_roles == expected_roles
        ),
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-qualification-receipt", type=Path, required=True)
    parser.add_argument("--parent-qualification-verification", type=Path, required=True)
    args = parser.parse_args()
    assert_exclusive_host_released()

    parent_receipt_path = args.parent_qualification_receipt
    if not parent_receipt_path.is_absolute():
        parent_receipt_path = PROJECT / parent_receipt_path
    parent_verification_path = args.parent_qualification_verification
    if not parent_verification_path.is_absolute():
        parent_verification_path = PROJECT / parent_verification_path
    parent_receipt, parent_verification = validate_parent_qualification(
        parent_receipt_path,
        parent_verification_path,
    )

    bindings = {
        "experiment": verify_locked_file(EXPERIMENT, EXPECTED_SHA256[EXPERIMENT]),
        "proposal": verify_locked_file(PROPOSAL, EXPECTED_SHA256[PROPOSAL]),
        "candidate_revision": verify_locked_file(
            CANDIDATE_REVISION, EXPECTED_SHA256[CANDIDATE_REVISION]
        ),
        "interface_contract": verify_locked_file(INTERFACE, EXPECTED_SHA256[INTERFACE]),
        "scanner_source": verify_locked_file(SOURCE, EXPECTED_SHA256[SOURCE]),
        "planning_contract": artifact(PLAN),
        "planning_schema": verify_locked_file(PLAN_SCHEMA, EXPECTED_SHA256[PLAN_SCHEMA]),
        "scanner_schema": verify_locked_file(SCAN_SCHEMA, EXPECTED_SHA256[SCAN_SCHEMA]),
        "decision_schema": verify_locked_file(
            DECISION_SCHEMA, EXPECTED_SHA256[DECISION_SCHEMA]
        ),
        "output_manifest_schema": verify_locked_file(
            MANIFEST_SCHEMA, EXPECTED_SHA256[MANIFEST_SCHEMA]
        ),
        "parent_qualification_schema": verify_locked_file(
            PARENT_QUALIFICATION_SCHEMA, EXPECTED_SHA256[PARENT_QUALIFICATION_SCHEMA]
        ),
        "parent_verification_schema": verify_locked_file(
            PARENT_VERIFICATION_SCHEMA, EXPECTED_SHA256[PARENT_VERIFICATION_SCHEMA]
        ),
        "managed_lease_implementation": verify_locked_file(
            MANAGED_LEASE_IMPLEMENTATION,
            EXPECTED_SHA256[MANAGED_LEASE_IMPLEMENTATION],
        ),
        "exclusive_lease_schema": verify_locked_file(
            EXCLUSIVE_LEASE_SCHEMA, EXPECTED_SHA256[EXCLUSIVE_LEASE_SCHEMA]
        ),
        "parent_qualification_receipt": parent_receipt,
        "parent_qualification_verification": parent_verification,
        "runner": artifact(Path(__file__).resolve()),
        "compiler": verify_locked_file(COMPILER, EXPECTED_SHA256[COMPILER]),
    }
    planning = json.loads(PLAN.read_text(encoding="utf-8"))
    validate_planning_contract(planning, bindings["runner"]["sha256"])
    revision = json.loads(CANDIDATE_REVISION.read_text(encoding="utf-8"))
    if (
        revision.get("candidateId") != CANDIDATE_ID
        or revision.get("candidateTreeSha256") != CANDIDATE_TREE_SHA256
    ):
        raise RuntimeError("candidate revision identity mismatch")

    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite result root: {RESULT}")
    RESULT.mkdir(mode=0o700, parents=True)

    invocation_contract = {
        "argv": [str(Path(__file__).resolve()), *sys.argv[1:]],
        "cwd": str(PROJECT),
        "environment": ENVIRONMENT,
    }
    # Import only after the implementation bytes have matched the frozen digest.
    # A top-level import would execute an unverified transitive dependency.
    from managed_exclusive_lease import ManagedExclusiveLease

    lease: Any = None
    try:
        lease = ManagedExclusiveLease.acquire(
            lease_path=LEASE,
            transition_path=RESULT / "lease-transitions.json",
            candidate_id=CANDIDATE_ID,
            command_sha256=canonical_sha256(invocation_contract),
            runner_sha256=bindings["runner"]["sha256"],
            guard_path=str(RESULT),
            result_path=str(RESULT),
            scratch_path=str(RESULT),
            claim_boundary=(
                "Managed exclusive lane for two zero-credit full transformed-stream "
                "WIKI-SCHEMA-VM scans; no signaling authority."
            ),
        )
    except Exception:
        RESULT.rmdir()
        raise

    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.wiki-schema-vm-ceiling-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal_infrastructure_failure",
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_authority": "causal_shadow_opportunity_screen_only",
        "population": {
            "path": str(INPUT),
            "bytes": INPUT_BYTES,
            "sha256": INPUT_SHA256,
        },
        "bindings": bindings,
        "exclusive_lease": {
            "lease_id": lease.record["lease_id"],
            "release_pass": False,
            "evidence": None,
            "transitions": None,
        },
        "compile_flags": COMPILE_FLAGS,
        "compile": None,
        "scanner": None,
        "scan_a_command": None,
        "scan_b_command": None,
        "scan_a": None,
        "scan_b": None,
        "measurements": None,
        "repeat_summary_byte_identity_pass": None,
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
        assert_no_symlink_components(INPUT)
        input_metadata = INPUT.stat()
        if (
            not stat.S_ISREG(input_metadata.st_mode)
            or input_metadata.st_nlink != 1
            or input_metadata.st_size != INPUT_BYTES
            or sha256(INPUT) != INPUT_SHA256
        ):
            raise RuntimeError("transformed-ready population identity mismatch")
        lease.heartbeat()

        binary = RESULT / "wiki-schema-vm-scan"
        compile_argv = [str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)]
        decision["compile"] = run_command(
            "compile", compile_argv, RESULT / "compile.stdout", RESULT / "compile.stderr"
        )
        if decision["compile"]["returncode"] != 0:
            raise RuntimeError("scanner compilation failed")
        decision["scanner"] = artifact(binary)
        lease.heartbeat()

        scan_a_path = RESULT / "scan-a.json"
        scan_a_argv = [str(binary), str(INPUT), str(scan_a_path)]
        decision["scan_a_command"] = run_command(
            "scan_a", scan_a_argv, RESULT / "scan-a.stdout", RESULT / "scan-a.stderr"
        )
        if decision["scan_a_command"]["returncode"] != 0:
            raise RuntimeError("scanner Arm A failed")
        summary_a = json.loads(scan_a_path.read_text(encoding="utf-8"))
        validate_with_schema(summary_a, SCAN_SCHEMA)
        semantic_scan_checks(summary_a)
        decision["scan_a"] = artifact(scan_a_path)
        lease.heartbeat()

        scan_b_path = RESULT / "scan-b.json"
        scan_b_argv = [str(binary), str(INPUT), str(scan_b_path)]
        decision["scan_b_command"] = run_command(
            "scan_b", scan_b_argv, RESULT / "scan-b.stdout", RESULT / "scan-b.stderr"
        )
        if decision["scan_b_command"]["returncode"] != 0:
            raise RuntimeError("scanner Arm B failed")
        summary_b = json.loads(scan_b_path.read_text(encoding="utf-8"))
        validate_with_schema(summary_b, SCAN_SCHEMA)
        semantic_scan_checks(summary_b)
        decision["scan_b"] = artifact(scan_b_path)
        lease.heartbeat()

        repeat_identity = scan_a_path.read_bytes() == scan_b_path.read_bytes()
        measurements = {
            "scanned_bytes": summary_a["population_bytes"],
            "opportunity_bytes": summary_a["opportunity_bytes"],
            "quantized_log_loss_upper_bound_bytes": (
                summary_a["opportunity_bytes"]
                * MAX_OPTIMISTIC_GAIN_BYTES_PER_OPPORTUNITY
            ),
            "treatment_correct_bytes": summary_a["treatment_correct_bytes"],
            "random_correct_bytes": summary_a["random_correct_bytes"],
            "shifted_correct_bytes": summary_a["shifted_correct_bytes"],
            "treatment_minus_random_correct_bytes": summary_a[
                "treatment_minus_random_correct_bytes"
            ],
            "treatment_minus_shifted_correct_bytes": summary_a[
                "treatment_minus_shifted_correct_bytes"
            ],
            "treatment_correct_by_third": summary_a["treatment_correct_by_third"],
            "minimum_third_treatment_correct_bytes": summary_a[
                "minimum_third_treatment_correct_bytes"
            ],
            "opportunity_fnv1a64": summary_a["opportunity_fnv1a64"],
            "parser_fnv1a64": summary_a["parser_fnv1a64"],
            "table_fnv1a64": summary_a["table_fnv1a64"],
            "bounded_state_pass": summary_a["bounded_state_pass"],
        }
        gates = {
            "full_population_pass": measurements["scanned_bytes"] == INPUT_BYTES,
            "target_scale_quantized_log_loss_envelope_pass": (
                measurements["opportunity_bytes"] >= REQUIRED_OPPORTUNITY_BYTES
                and measurements["quantized_log_loss_upper_bound_bytes"]
                >= REQUIRED_CORRECT_BYTES
            ),
            "one_byte_per_correct_volume_screen_pass": (
                measurements["treatment_correct_bytes"] >= REQUIRED_CORRECT_BYTES
            ),
            "all_thirds_live_pass": (
                measurements["minimum_third_treatment_correct_bytes"] > 0
            ),
            "beats_random_pass": (
                measurements["treatment_minus_random_correct_bytes"] > 0
            ),
            "beats_shifted_pass": (
                measurements["treatment_minus_shifted_correct_bytes"] > 0
            ),
            "repeat_identity_pass": repeat_identity,
            "bounded_state_pass": measurements["bounded_state_pass"] is True,
            "all_promotion_predicates_pass": False,
        }
        gates["all_promotion_predicates_pass"] = all(
            value
            for key, value in gates.items()
            if key
            not in {
                "all_promotion_predicates_pass",
                "one_byte_per_correct_volume_screen_pass",
            }
        )
        passed = gates["all_promotion_predicates_pass"]
        decision.update(
            {
                "operational_status": "terminal",
                "measurements": measurements,
                "repeat_summary_byte_identity_pass": repeat_identity,
                "gates": gates,
                "scientific_verdict": (
                    "authorize_retained_parent_donor_surprise_trace_zero_credit"
                    if passed
                    else "retire_exact_schema_program_information_source"
                ),
                "next_authority": (
                    "retained_parent_donor_surprise_trace_only"
                    if passed
                    else "one_materially_different_information_source"
                ),
            }
        )
    except Exception as error:  # A terminal failure receipt is mandatory after creation.
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
            lease_message = f"lease release failure: {type(lease_error).__name__}: {lease_error}"
            decision["error"] = (
                lease_message
                if decision["error"] is None
                else f"{decision['error']}; {lease_message}"
            )
            decision.update(
                {
                    "operational_status": "terminal_infrastructure_failure",
                    "scientific_verdict": "none_infrastructure_failure",
                    "next_authority": "one_correction_only_runner_successor",
                }
            )
            evidence_path = RESULT / "lease-evidence.json"
            transition_path = RESULT / "lease-transitions.json"
            decision["exclusive_lease"] = {
                "lease_id": lease.record["lease_id"],
                "release_pass": False,
                "evidence": artifact(evidence_path) if evidence_path.is_file() else None,
                "transitions": (
                    artifact(transition_path) if transition_path.is_file() else None
                ),
            }

    validate_with_schema(decision, DECISION_SCHEMA)
    write_json_exclusive(RESULT / "decision.json", decision)
    complete = decision["operational_status"] == "terminal"
    manifest = result_manifest(complete)
    validate_with_schema(manifest, MANIFEST_SCHEMA)
    write_json_exclusive(RESULT / "output-manifest.json", manifest)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
