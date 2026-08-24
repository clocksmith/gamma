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
    "20260824T004226768889Z_3d110ac42c80.json"
)
SCAN_SCHEMA = PROJECT / "contracts/research/v1/wiki-schema-vm-scan.schema.json"
DECISION_SCHEMA = (
    PROJECT / "contracts/research/v1/wiki-schema-vm-ceiling-decision.schema.json"
)
MANIFEST_SCHEMA = (
    PROJECT / "contracts/research/v1/wiki-schema-vm-output-manifest.schema.json"
)
PARENT_QUALIFICATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/cmix-memory-safe-parent-qualification-receipt.schema.json"
)
PARENT_VERIFICATION_SCHEMA = (
    PROJECT
    / "contracts/research/v1/cmix-memory-safe-parent-qualification-verification.schema.json"
)
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
CANDIDATE_TREE_SHA256 = (
    "sha256:3d110ac42c80f454802c09cf706f44ce507097b7d977b4539972ab711f3680c5"
)
EXPECTED_SHA256 = {
    EXPERIMENT: "c298d1525e528984271af602bb9bd84fdc6a2363362a6876e456b66bd8280b3c",
    PROPOSAL: "732d6db8e42ff07c10695c02ece7964fdfe7f516d3bbb15058c425c0a38a6c88",
    CANDIDATE_REVISION: "b704edd93d67329fafa1141d881993304552ef759c1a98a4d489e18c4e8e1a52",
    INTERFACE: "9864e17ab54b73fc5159af1df76b4ca5042e93f3bdc03a02c40507fe0ccaacbb",
    SOURCE: "d54ff0bb169f44ca695f943d6a119c9a780783479b3187ecdbc88322c3732691",
    SCAN_SCHEMA: "016e33bb94bf9c1fd8bd1dbce7f365fbb680eb5a18e96e6002d8c504c5ce621c",
    DECISION_SCHEMA: "050e9dc179cf789f14292ac629de950bb55cea3682ad25613da3fb159bf55460",
    MANIFEST_SCHEMA: "2754749bf9f546b7745456234f9f69bb9db1369f0c5129c05bd8d79caa4e962b",
    PARENT_QUALIFICATION_SCHEMA: "31eb692bf80eaa9472b8feb74bb0cdfe498446a052c4165c345bed847ab48177",
    PARENT_VERIFICATION_SCHEMA: "afec74a401e1351ace4b03b22c96c9699de32c95fa273d7b61bad4c7e4798ca1",
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
    "a causal correct-byte opportunity ceiling. They prove no arithmetic-code gain, "
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
    required_decisions = (
        "build_identity_pass",
        "probability_identity_pass",
        "payload_identity_pass",
        "archive_identity_pass",
        "two_run_determinism_pass",
        "exact_inverse_pass",
        "memory_pass",
        "temporary_disk_pass",
        "package_accounting_complete",
        "memory_safe_parent_qualified",
    )
    receipt_decisions = receipt["decisions"]
    resources = receipt["resources"]
    package = receipt["package"]
    verification_decisions = verification["derived_decisions"]
    if not all(receipt_decisions[name] is True for name in required_decisions):
        raise RuntimeError("q1 qualification receipt lacks a required positive decision")
    if (
        resources["process_tree_peak_rss_kib"] > 9_000_000
        or resources["cgroup_memory_peak_bytes"] > 10_000_000_000
        or resources["memory_events_oom"] != 0
        or resources["memory_events_oom_kill"] != 0
        or resources["runtime_measured"] is not True
        or resources["runtime_eligible"] is not True
        or package["dependency_closure_pass"] is not True
        or package["license_closure_pass"] is not True
    ):
        raise RuntimeError("q1 qualification lacks engineering headroom, runtime, or closure")
    if (
        verification["verified"] is not True
        or verification["qualified"] is not True
        or verification["errors"] != []
        or verification["qualification_failures"] != []
        or verification["receipt_sha256"] != receipt_sha256
        or not all(verification["checks"].values())
        or not all(verification_decisions.values())
    ):
        raise RuntimeError("independent q1 qualification verification is not fully positive")
    return artifact(receipt_path, receipt_sha256), artifact(verification_path)


def empty_gates() -> dict[str, None]:
    return {
        "full_population_pass": None,
        "target_scale_ceiling_pass": None,
        "all_thirds_live_pass": None,
        "beats_random_pass": None,
        "beats_shifted_pass": None,
        "repeat_identity_pass": None,
        "bounded_state_pass": None,
        "all_promotion_predicates_pass": None,
    }


def result_manifest(complete: bool) -> dict[str, Any]:
    roles = [
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
    actual_roles = {record["role"] for record in artifacts}
    return {
        "schema": "gamma.enwiki9.wiki-schema-vm-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "result_root": "results/wiki_schema_vm_ceiling_q0_v1",
        "complete_result_artifacts_pass": complete and actual_roles == expected_roles,
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-qualification-receipt", type=Path, required=True)
    parser.add_argument("--parent-qualification-verification", type=Path, required=True)
    args = parser.parse_args()
    assert_exclusive_host_released()
    assert_no_symlink_components(INPUT)
    input_metadata = INPUT.stat()
    if (
        not stat.S_ISREG(input_metadata.st_mode)
        or input_metadata.st_nlink != 1
        or input_metadata.st_size != INPUT_BYTES
        or sha256(INPUT) != INPUT_SHA256
    ):
        raise RuntimeError("transformed-ready population identity mismatch")

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
        "parent_qualification_receipt": parent_receipt,
        "parent_qualification_verification": parent_verification,
        "runner": artifact(Path(__file__).resolve()),
        "compiler": verify_locked_file(COMPILER, EXPECTED_SHA256[COMPILER]),
    }
    revision = json.loads(CANDIDATE_REVISION.read_text(encoding="utf-8"))
    if (
        revision.get("candidateId") != CANDIDATE_ID
        or revision.get("candidateTreeSha256") != CANDIDATE_TREE_SHA256
    ):
        raise RuntimeError("candidate revision identity mismatch")

    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite result root: {RESULT}")
    RESULT.mkdir(mode=0o700, parents=True)

    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.wiki-schema-vm-ceiling-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal_infrastructure_failure",
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_authority": "causal_shadow_ceiling_only",
        "population": {
            "path": str(INPUT),
            "bytes": INPUT_BYTES,
            "sha256": INPUT_SHA256,
        },
        "bindings": bindings,
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
        binary = RESULT / "wiki-schema-vm-scan"
        compile_argv = [str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)]
        decision["compile"] = run_command(
            "compile", compile_argv, RESULT / "compile.stdout", RESULT / "compile.stderr"
        )
        if decision["compile"]["returncode"] != 0:
            raise RuntimeError("scanner compilation failed")
        decision["scanner"] = artifact(binary)

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

        repeat_identity = scan_a_path.read_bytes() == scan_b_path.read_bytes()
        measurements = {
            "scanned_bytes": summary_a["population_bytes"],
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
            "target_scale_ceiling_pass": (
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
            value for key, value in gates.items() if key != "all_promotion_predicates_pass"
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

    validate_with_schema(decision, DECISION_SCHEMA)
    write_json_exclusive(RESULT / "decision.json", decision)
    complete = decision["operational_status"] == "terminal"
    manifest = result_manifest(complete)
    validate_with_schema(manifest, MANIFEST_SCHEMA)
    write_json_exclusive(RESULT / "output-manifest.json", manifest)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
