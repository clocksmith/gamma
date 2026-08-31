#!/usr/bin/env python3
"""Guarded complete Endpoint428 semantic-route tape A/B builder."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_semantic_route_tape_q0_v2"
CANDIDATE = PROJECT / "programs" / CANDIDATE_ID
RESULT = PROJECT / "results" / CANDIDATE_ID
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
ORDERING = PROJECT / "operations/planning/endpoint428_semantic_route_tape_q0_v2_ordering_addendum.json"
STORE = Path("/home/x/enwiki9-nonproof/results/helical_far_history_wrt_event_map_qm2_v1/enwik9.store")
RAW = PROJECT / "data/enwik9"
DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/results/"
    "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
    "clean-build-b/build/english.dic"
)
SCANNER_SOURCE = CANDIDATE / "semantic-route-tape.cpp"
VERIFIER = CANDIDATE / "verify.py"
INTERFACE = CANDIDATE / "interface-contract.json"
GUARD = PROJECT / "tools/run_with_rss_guard.py"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")
ACTIVE_BLOCKER = "endpoint428_horizon_retained_parent_trace_q0_v1"
MAXIMUM_TREE_RSS_KIB = 1_048_576
MAXIMUM_TEMPORARY_DISK_BYTES = 100_000_000_000

EXPECTED = {
    "store": (647_798_597, "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"),
    "raw": (1_000_000_000, "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"),
    "dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}


def require_regular(path: Path, label: str) -> None:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError(f"{label} must be a regular non-symlink file: {path}")


def verify_input(path: Path, expected: tuple[int, str], label: str) -> dict[str, Any]:
    require_regular(path, label)
    row = artifact(path)
    if (row["bytes"], row["sha256"]) != expected:
        raise RuntimeError(f"{label} identity mismatch: {row}")
    return row


def blocker_is_active() -> bool:
    running = PROJECT / "operations/adaptive/running"
    for path in running.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("candidate_id") == ACTIVE_BLOCKER:
            return True
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            command = (process / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if ACTIVE_BLOCKER in command:
            return True
    return False


def run_logged(command: list[str], log: Path) -> None:
    with log.open("xb") as output:
        completed = subprocess.run(command, cwd=PROJECT, stdout=output,
                                   stderr=subprocess.STDOUT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed returncode={completed.returncode}: {command}")


def run_guarded(label: str, command: list[str]) -> dict[str, Any]:
    guard_path = RESULT / f"{label}-guard.json"
    log_path = RESULT / f"{label}.log"
    invocation = [
        sys.executable, str(GUARD),
        "--limit-kib", str(MAXIMUM_TREE_RSS_KIB),
        "--limit-mode", "tree",
        "--official-decimal-limit-kib", "9765625",
        "--sample-interval", "1",
        "--scratch-path", str(RESULT),
        "--temporary-disk-limit-bytes", str(MAXIMUM_TEMPORARY_DISK_BYTES),
        "--guard-json", str(guard_path),
        "--label", f"{CANDIDATE_ID}_{label}",
        "--phase", "diagnostic",
        "--", *command,
    ]
    run_logged(invocation, log_path)
    receipt = json.loads(guard_path.read_text(encoding="utf-8"))
    if (receipt.get("returncode") != 0 or receipt.get("status") != "complete" or
            receipt.get("rss_guard_exceeded") is not False or
            receipt.get("temporary_disk_guard_exceeded") is not False):
        raise RuntimeError(f"guard failed for {label}: {receipt}")
    return {"guard": artifact(guard_path), "log": artifact(log_path), "receipt": receipt}


def write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    required = (SCANNER_SOURCE, VERIFIER, INTERFACE, EXPERIMENT, ORDERING, GUARD, COMPILER,
                STORE, RAW, DICTIONARY)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing required inputs: {missing}")
    if blocker_is_active():
        raise RuntimeError(f"full route-tape build forbidden while {ACTIVE_BLOCKER} is active")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError(f"result directory must be precreated and empty: {RESULT}")

    inputs = {
        "store": verify_input(STORE, EXPECTED["store"], "store"),
        "raw": verify_input(RAW, EXPECTED["raw"], "raw"),
        "dictionary": verify_input(DICTIONARY, EXPECTED["dictionary"], "dictionary"),
        "scanner_source": artifact(SCANNER_SOURCE),
        "verifier": artifact(VERIFIER),
        "interface": artifact(INTERFACE),
        "experiment": artifact(EXPERIMENT),
        "ordering_addendum": artifact(ORDERING),
        "guard": artifact(GUARD),
        "compiler": artifact(COMPILER),
    }
    flags = [
        "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
        "-fno-fast-math", "-ffp-contract=off", "-march=x86-64", "-mtune=generic",
        "-Wl,--build-id=none",
    ]
    with tempfile.TemporaryDirectory(prefix="gamma-semantic-route-build-") as temporary:
        binary = Path(temporary) / "semantic-route-tape"
        run_logged([str(COMPILER), *flags, str(SCANNER_SOURCE), "-o", str(binary)],
                   RESULT / "compile.log")
        build = {"schema": "gamma.enwiki9.endpoint428-semantic-route-tape-build.v2",
                 "inputs": inputs, "flags": flags, "binary": artifact(binary),
                 "archive_authority": False, "score_credit_bytes": 0}
        write_json_exclusive(RESULT / "build.json", build)

        phases: dict[str, Any] = {}
        for arm in ("a", "b"):
            phases[f"build_{arm}"] = run_guarded(
                f"build-{arm}",
                [str(binary), str(STORE), str(RAW), str(DICTIONARY),
                 str(RESULT / f"tape-{arm}.bin"),
                 str(RESULT / f"descriptors-{arm}.bin"),
                 str(RESULT / f"summary-{arm}.json")],
            )
        phases["verification"] = run_guarded(
            "verification",
            [sys.executable, str(VERIFIER), "--store", str(STORE), "--raw", str(RAW),
             "--dictionary", str(DICTIONARY), "--tape-a", str(RESULT / "tape-a.bin"),
             "--tape-b", str(RESULT / "tape-b.bin"),
             "--sidecar-a", str(RESULT / "descriptors-a.bin"),
             "--sidecar-b", str(RESULT / "descriptors-b.bin"),
             "--summary-a", str(RESULT / "summary-a.json"),
             "--summary-b", str(RESULT / "summary-b.json"),
             "--receipt", str(RESULT / "verification.json")],
        )

    verification = json.loads((RESULT / "verification.json").read_text(encoding="utf-8"))
    max_tree_rss = max(
        int(phase["receipt"].get("max_sampled_tree_rss_kib", 0)) for phase in phases.values()
    )
    max_disk = max(
        int(phase["receipt"].get("max_sampled_temporary_disk_bytes", 0)) for phase in phases.values()
    )
    passed = (
        verification.get("verification_pass") is True
        and verification.get("fixture") is False
        and verification.get("scanned_wrt_bytes") == 647_798_592
        and verification.get("reconstructed_raw_bytes") == 1_000_000_000
        and verification.get("repeat_identity_pass") is True
        and verification.get("causal_abi_pass") is True
        and max_tree_rss <= MAXIMUM_TREE_RSS_KIB
        and max_disk <= MAXIMUM_TEMPORARY_DISK_BYTES
    )
    decision = {
        "schema": "gamma.enwiki9.endpoint428-semantic-route-tape-decision.v2",
        "candidate_id": CANDIDATE_ID,
        "status": "passed" if passed else "failed",
        "verification": artifact(RESULT / "verification.json"),
        "phases": phases,
        "maximum_tree_rss_kib": max_tree_rss,
        "maximum_temporary_disk_bytes": max_disk,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "claim": "zero-credit-population-infrastructure",
        "next_action": (
            "authorize one Endpoint428 Fiber-CTS causal probability shadow against a frozen parent ABI"
            if passed else "reject this exact semantic-route tape identity"
        ),
    }
    write_json_exclusive(RESULT / "decision.json", decision)
    if not passed:
        raise RuntimeError(f"semantic route tape failed: {decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
