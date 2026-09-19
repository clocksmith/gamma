#!/usr/bin/env python3
"""Read cmix21 gate receipts and emit the next safe action as JSON."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
RESULTS = ROOT / "results"
LOCAL_RSS_GUARD_KIB = 10_485_760
OFFICIAL_DECIMAL_RSS_GUARD_KIB = 10_000_000_000 // 1024
FULL_SCOPE_BYTES = 1_000_000_000
TARGET_SCORE_BYTES = 108_000_000
OFFICIAL_DECIMAL_MEMORY_FAILURE = "active_compressor_exceeded_official_decimal_10gb_limit"


def rel(path: pathlib.Path | None) -> str | None:
    if path is None:
        return None
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def add_file_metadata(payload: dict[str, Any], key: str, path: pathlib.Path | None) -> None:
    payload[f"{key}_bytes"] = None
    payload[f"{key}_mtime_utc"] = None
    payload[f"{key}_sha256"] = None
    if path is None:
        return
    try:
        stat = path.stat()
        content = path.read_bytes()
    except OSError:
        return
    payload[f"{key}_bytes"] = stat.st_size
    payload[f"{key}_mtime_utc"] = (
        dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
    payload[f"{key}_sha256"] = hashlib.sha256(content).hexdigest()


def determinism_ok(result: dict[str, Any]) -> bool | None:
    value = result.get("determinism")
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        flag = value.get("single_host_byte_equal")
        return flag if isinstance(flag, bool) else None
    return None


def latest_driver_result(candidate: str, scope: int) -> pathlib.Path | None:
    result_dir = RESULTS / candidate
    matches: list[pathlib.Path] = []
    for path in result_dir.glob("*.json"):
        try:
            payload = load_json(path)
        except Exception:
            continue
        if payload.get("program_id") == candidate and payload.get("data_size") == scope:
            matches.append(path)
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


def default_guard_path(candidate: str, scope: int) -> pathlib.Path:
    short = re.search(r"(ppmd\d+k)", candidate)
    tag = short.group(1) if short else "gate"
    return RESULTS / candidate / f"{tag}_{scope}_determinism_rss_guard.json"


def guard_scope_from_path(path: pathlib.Path) -> int | None:
    match = re.search(r"_(?P<scope>[0-9]+).*rss_guard[.]json$", path.name)
    if not match:
        return None
    try:
        return int(match.group("scope"))
    except ValueError:
        return None


def guard_scope_from_command(payload: dict[str, Any]) -> int | None:
    command = payload.get("command")
    if not isinstance(command, list):
        return None
    parts = [str(part) for part in command]
    if "--limit" not in parts:
        return None
    index = parts.index("--limit")
    if index + 1 >= len(parts):
        return None
    try:
        return int(parts[index + 1])
    except ValueError:
        return None


def guard_scope(path: pathlib.Path, payload: dict[str, Any] | None) -> int | None:
    if isinstance(payload, dict):
        scope = guard_scope_from_command(payload)
        if scope is not None:
            return scope
    return guard_scope_from_path(path)


def existing_guard_path(candidate: str, scope: int) -> pathlib.Path | None:
    result_dir = RESULTS / candidate
    matches: list[pathlib.Path] = []
    for path in sorted(result_dir.glob("*rss_guard.json")):
        try:
            payload = load_json(path)
        except Exception:
            payload = {}
        if guard_scope(path, payload) == scope:
            matches.append(path)
    if not matches:
        return None

    def sort_key(path: pathlib.Path) -> tuple[int, float]:
        return (1 if "determinism" in path.name else 0, path.stat().st_mtime)

    return max(matches, key=sort_key)


def next_scope(scope: int) -> int | None:
    if scope == 1_024:
        return 250_000
    if scope == 250_000:
        return 1_000_000
    if scope == 1_000_000:
        return 10_000_000
    if scope == 10_000_000:
        return 100_000_000
    if scope == 100_000_000:
        return 1_000_000_000
    return None


def command_for_gate(
    candidate: str,
    scope: int,
) -> list[str]:
    guard = default_guard_path(candidate, scope)
    tag = re.search(r"ppmd(\d+k)", candidate)
    label_tag = f"ppmd{tag.group(1)}" if tag else "gate"
    command = [
        "python3",
        "projects/enwiki9/tools/run_with_rss_guard.py",
        "--limit-kib",
        str(LOCAL_RSS_GUARD_KIB),
        "--official-decimal-limit-kib",
        str(OFFICIAL_DECIMAL_RSS_GUARD_KIB),
        "--sample-interval",
        "1",
        "--guard-json",
        rel(guard) or str(guard),
        "--label",
        f"cmix21_{label_tag}_fxcmrcm20_{scope}_determinism",
        "--",
        "python3",
        "projects/enwiki9/lib/driver.py",
        candidate,
        "--limit",
        str(scope),
        "--check-determinism",
    ]
    return command


def record_command(
    candidate: str,
    scope: int,
    result_path: pathlib.Path,
    guard_path: pathlib.Path,
    verdict: str,
    note: str,
) -> list[str]:
    label_by_scope = {
        10_000_000: "10m_determinism_replay",
        100_000_000: "100m_determinism_replay",
        1_000_000_000: "1g_determinism_replay",
    }
    return [
        "python3",
        "projects/enwiki9/tools/record_driver_result.py",
        candidate,
        "--result",
        rel(result_path) or str(result_path),
        "--guard-json",
        rel(guard_path) or str(guard_path),
        "--label",
        label_by_scope.get(scope, f"{scope}_determinism_replay"),
        "--status",
        "active",
        "--verdict",
        verdict,
        "--note",
        note,
        "--note",
        f"Guard artifact: {rel(guard_path) or guard_path.as_posix()}",
    ]


def record_rss_failure_command(
    candidate: str,
    scope: int,
    guard_path: pathlib.Path,
    verdict: str,
    note: str,
) -> list[str]:
    return [
        "python3",
        "projects/enwiki9/tools/record_driver_result.py",
        candidate,
        "--guard-json",
        rel(guard_path) or str(guard_path),
        "--guard-only",
        "--scope",
        str(scope),
        "--label",
        f"{scope}_rss_guard_fail",
        "--status",
        "active",
        "--verdict",
        verdict,
        "--note",
        note,
        "--note",
        f"Guard artifact: {rel(guard_path) or guard_path.as_posix()}",
    ]


def record_result_failure_command(
    candidate: str,
    scope: int,
    result_path: pathlib.Path,
    guard_path: pathlib.Path | None,
    verdict: str,
    reason: str,
) -> list[str]:
    command = [
        "python3",
        "projects/enwiki9/tools/record_driver_result.py",
        candidate,
        "--result",
        rel(result_path) or str(result_path),
        "--label",
        f"{scope}_{verdict}",
        "--status",
        "active",
        "--verdict",
        verdict,
        "--note",
        reason,
    ]
    if guard_path is not None and guard_path.exists():
        command.extend(["--guard-json", rel(guard_path) or str(guard_path)])
        command.extend(
            [
                "--note",
                f"Guard artifact: {rel(guard_path) or guard_path.as_posix()}",
            ]
        )
    return command


def record_guard_failure_command(
    candidate: str,
    scope: int,
    guard_path: pathlib.Path,
    verdict: str,
    reason: str,
) -> list[str]:
    return [
        "python3",
        "projects/enwiki9/tools/record_driver_result.py",
        candidate,
        "--guard-json",
        rel(guard_path) or str(guard_path),
        "--guard-only",
        "--scope",
        str(scope),
        "--label",
        f"{scope}_{verdict}",
        "--status",
        "active",
        "--verdict",
        verdict,
        "--note",
        reason,
        "--note",
        f"Guard artifact: {rel(guard_path) or guard_path.as_posix()}",
    ]


def apply_terminal_command(
    candidate: str,
    scope: int,
    *,
    launch_next: bool = False,
    package_lower: bool = False,
) -> list[str]:
    command = [
        "python3",
        "projects/enwiki9/tools/cmix21_gate_decider.py",
        candidate,
        "--scope",
        str(scope),
        "--apply-terminal",
        "--normalize",
    ]
    if launch_next:
        command.append("--launch-next")
    if package_lower:
        command.append("--package-lower")
    return command


def recorded_rss_failure(candidate: str, scope: int) -> dict[str, Any] | None:
    meta_path = PROGRAMS / candidate / "meta.json"
    if not meta_path.exists():
        return None
    try:
        meta = load_json(meta_path)
    except Exception:
        return None
    measured = meta.get("measured", {})
    if not isinstance(measured, dict):
        return None
    for label, row in measured.items():
        if not isinstance(label, str) or not isinstance(row, dict):
            continue
        if row.get("data_size") != scope:
            continue
        memory_failure = row.get("failure") == OFFICIAL_DECIMAL_MEMORY_FAILURE
        memory_failure = memory_failure or row.get("guard_failure") == OFFICIAL_DECIMAL_MEMORY_FAILURE
        if row.get("rss_guard_exceeded") is not True and not memory_failure:
            continue
        return {
            "label": label,
            "guard_path": row.get("guard_path"),
            "max_sampled_single_rss_kib": row.get("max_sampled_single_rss_kib"),
            "memory_ceiling_kib": row.get("memory_ceiling_kib"),
            "single_rss_over_ceiling_kib": row.get("single_rss_over_ceiling_kib"),
            "official_decimal_limit_kib": row.get("official_decimal_limit_kib"),
            "official_decimal_over_limit_kib": row.get("official_decimal_over_limit_kib"),
            "failure": row.get("failure"),
        }
    return None


def lower_ppmd_suggestion(candidate: str, step_kib: int) -> dict[str, Any] | None:
    match = re.search(r"ppmd(\d+)k", candidate)
    if not match:
        return None
    current = int(match.group(1))
    lower = current - step_kib
    if lower <= 0:
        return None
    next_id = candidate.replace(f"ppmd{current}k", f"ppmd{lower}k")
    meta_path = PROGRAMS / candidate / "meta.json"
    defines: list[str] = []
    if meta_path.exists():
        meta = load_json(meta_path)
        source = meta.get("source", {})
        raw_defines = source.get("defines", [])
        if isinstance(raw_defines, list):
            for item in raw_defines:
                if not isinstance(item, str):
                    continue
                if item.startswith("-DCMIX_PPMD_MEMORY_KB="):
                    defines.append(f"-DCMIX_PPMD_MEMORY_KB={lower}")
                else:
                    defines.append(item)
    command = [
        "python3",
        "projects/enwiki9/tools/cmix21_package_candidate.py",
        "--id",
        next_id,
        "--parent",
        candidate,
        "--description",
        f"cmix21 PAQ5 text-mode PPMD{lower}K candidate shaving only the PPMD cap after {current}K failed a promotion gate.",
        "--hypothesis",
        f"PPMD{current}K failed the RSS guard at a larger scope. Reducing only PPMD to {lower} KiB should buy RSS margin while preserving the PAQ5/FXCM archive-critical surface.",
        "--status",
        "candidate",
    ]
    for define in defines:
        command.append(f"--define={define}")
    return {
        "surface": "PPMD cap",
        "current_kib": current,
        "suggested_kib": lower,
        "suggested_candidate": next_id,
        "defines": defines,
        "package_command": command,
        "reason": "RSS failure should cut the smallest measured memory surface first.",
    }


def decide(
    candidate: str,
    scope: int,
    guard_path: pathlib.Path,
    step_kib: int,
) -> dict[str, Any]:
    if not guard_path.exists():
        discovered_guard = existing_guard_path(candidate, scope)
        if discovered_guard is not None:
            guard_path = discovered_guard
    result_path = latest_driver_result(candidate, scope)
    result = load_json(result_path) if result_path else None
    guard = load_json(guard_path) if guard_path.exists() else None

    payload: dict[str, Any] = {
        "candidate": candidate,
        "scope_bytes": scope,
        "driver_result_json": rel(result_path),
        "driver_result_json_present": result_path is not None,
        "rss_guard_json": rel(guard_path) if guard_path.exists() else rel(guard_path),
        "rss_guard_json_present": guard_path.exists(),
        "verdict": "incomplete",
        "next_action": "wait_for_gate_receipts",
    }
    add_file_metadata(payload, "driver_result_json", result_path)
    add_file_metadata(payload, "rss_guard_json", guard_path if guard_path.exists() else None)

    if guard:
        payload["rss_guard_status"] = guard.get("status")
        payload["sample_count"] = guard.get("sample_count")
        payload["rss_guard_exceeded"] = guard.get("rss_guard_exceeded")
        payload["guard_failure"] = guard.get("failure")
        payload["official_decimal_limit_kib"] = guard.get("official_decimal_limit_kib")
        payload["official_decimal_over_limit_kib"] = guard.get("official_decimal_over_limit_kib")
        max_single = guard.get("max_sampled_single_rss_kib")
        max_tree = guard.get("max_sampled_tree_rss_kib")
        limit = guard.get("limit_kib")
        latest_sample = guard.get("latest_sample")
        payload["max_sampled_single_rss_kib"] = max_single
        payload["max_sampled_tree_rss_kib"] = max_tree
        payload["rss_guard_kib"] = limit
        payload["returncode"] = guard.get("returncode")
        if isinstance(latest_sample, dict):
            latest_single = latest_sample.get("max_single_rss_kib")
            latest_tree = latest_sample.get("tree_rss_kib")
            payload["latest_sample_max_single_rss_kib"] = latest_single
            payload["latest_sample_tree_rss_kib"] = latest_tree
            if isinstance(latest_single, int) and isinstance(limit, int):
                payload["latest_sample_single_rss_margin_kib"] = limit - latest_single
            if isinstance(latest_tree, int) and isinstance(limit, int):
                payload["latest_sample_tree_rss_margin_kib"] = limit - latest_tree
        if isinstance(max_single, int) and isinstance(limit, int):
            payload["single_rss_margin_kib"] = limit - max_single
            if max_single > limit:
                payload["single_rss_over_guard_kib"] = max_single - limit
            if 0 <= limit - max_single < 65_536:
                payload["single_rss_boundary_tight"] = True
        if isinstance(max_tree, int) and isinstance(limit, int):
            payload["tree_rss_margin_kib"] = limit - max_tree
            if max_tree > limit:
                payload["tree_rss_over_guard_kib"] = max_tree - limit
                payload["tree_rss_boundary_warning"] = (
                    "process tree RSS crossed the same numeric ceiling; the local kill guard is single-process"
                )
        official_decimal_memory_failed = (
            guard.get("failure") == OFFICIAL_DECIMAL_MEMORY_FAILURE
            or guard.get("status") == "aborted_official_decimal_memory_limit"
        )
        if guard.get("rss_guard_exceeded") is True or official_decimal_memory_failed:
            already_recorded = recorded_rss_failure(candidate, scope)
            if isinstance(max_single, int) and isinstance(limit, int):
                payload["single_rss_over_guard_kib"] = max(0, max_single - limit)
            payload["verdict"] = "rss_fail"
            payload["recorded_rss_failure"] = already_recorded
            lower = lower_ppmd_suggestion(candidate, step_kib)
            payload["lower_memory_suggestion"] = lower
            if official_decimal_memory_failed:
                payload["memory_failure_kind"] = "official_decimal_10gb"
            if already_recorded:
                lower_id = lower.get("suggested_candidate") if isinstance(lower, dict) else None
                lower_meta = PROGRAMS / lower_id / "meta.json" if isinstance(lower_id, str) else None
                if lower_meta is not None and lower_meta.exists():
                    payload["next_action"] = "launch_lower_prefix_gate"
                    payload["lower_candidate_packaged"] = True
                    payload["lower_prefix_scope_bytes"] = 1_024
                    payload["lower_prefix_gate_command"] = command_for_gate(
                        lower_id,
                        1_024,
                    )
                else:
                    payload["next_action"] = "bracket_lower_from_recorded_rss_failure"
                    payload["lower_candidate_packaged"] = False
                    payload["apply_terminal_command"] = apply_terminal_command(
                        candidate,
                        scope,
                        package_lower=True,
                    )
            else:
                payload["next_action"] = "record_rss_failure_and_bracket_lower"
                payload["record_rss_failure_command"] = record_rss_failure_command(
                    candidate,
                    scope,
                    guard_path,
                    "rss_fail",
                    (
                        f"{scope} gate failed official decimal 10GB memory accounting "
                        "before producing a scored archive or roundtrip."
                        if official_decimal_memory_failed
                        else f"{scope} gate failed RSS guard before producing a scored archive or roundtrip."
                    ),
                )
                payload["apply_terminal_command"] = apply_terminal_command(
                    candidate,
                    scope,
                    package_lower=True,
                )
            return payload
        if guard.get("status") == "running":
            payload["verdict"] = "running"
            payload["next_action"] = "wait_for_gate_completion"
            return payload
        if guard.get("status") == "aborted_operator_cancelled":
            payload["verdict"] = "cancelled_no_result"
            payload["next_action"] = "inspect_queue_before_launch"
            payload["terminal_reason"] = guard.get("terminal_reason")
            return payload

        guard_returncode = guard.get("returncode")
        if result is None and guard_returncode not in (0, None):
            payload["verdict"] = "guard_returncode_fail"
            payload["next_action"] = "record_guard_failure"
            payload["record_failure_command"] = record_guard_failure_command(
                candidate,
                scope,
                guard_path,
                "guard_returncode_fail",
                (
                    f"{scope} gate guard returned {guard_returncode} before a "
                    "complete driver result was produced; no roundtrip or "
                    "determinism claim is made."
                ),
            )
            payload["apply_terminal_command"] = apply_terminal_command(candidate, scope)
            return payload

    if result:
        compressed_size = result.get("compressed_size")
        program_size = result.get("program_size")
        payload.update(
            {
                "compressed_size": compressed_size,
                "program_size": program_size,
                "local_score": result.get("hutter_score"),
                "roundtrip_ok": result.get("roundtrip_ok"),
                "determinism_ok": determinism_ok(result),
                "compressed_sha256": result.get("compressed_sha256"),
            }
        )
        if isinstance(compressed_size, int) and scope > 0:
            payload["archive_bpb"] = (8 * compressed_size) / scope
            payload["linear_archive_projection_score"] = int(
                compressed_size * (FULL_SCOPE_BYTES / scope)
                + (program_size if isinstance(program_size, int) else 0)
            )
        if isinstance(program_size, int):
            payload["required_full_archive_bytes_for_10_95"] = TARGET_SCORE_BYTES - program_size
        if result.get("roundtrip_ok") is not True:
            payload["verdict"] = "roundtrip_fail"
            payload["next_action"] = "record_roundtrip_failure"
            payload["record_failure_command"] = record_result_failure_command(
                candidate,
                scope,
                result_path,
                guard_path if guard_path.exists() else None,
                "roundtrip_fail",
                f"{scope} gate produced a result JSON but failed roundtrip.",
            )
            payload["apply_terminal_command"] = apply_terminal_command(candidate, scope)
            return payload
        if determinism_ok(result) is not True:
            payload["verdict"] = "determinism_fail"
            payload["next_action"] = "record_determinism_failure"
            payload["record_failure_command"] = record_result_failure_command(
                candidate,
                scope,
                result_path,
                guard_path if guard_path.exists() else None,
                "determinism_fail",
                f"{scope} gate produced a result JSON but failed determinism replay.",
            )
            payload["apply_terminal_command"] = apply_terminal_command(candidate, scope)
            return payload
        if guard is None:
            payload["verdict"] = "receipt_incomplete"
            payload["next_action"] = "wait_for_rss_guard_receipt"
            return payload
        if guard.get("returncode") not in (0, None):
            payload["verdict"] = "guard_returncode_fail"
            payload["next_action"] = "record_guard_failure"
            payload["record_failure_command"] = record_result_failure_command(
                candidate,
                scope,
                result_path,
                guard_path,
                "guard_returncode_fail",
                f"{scope} gate produced a result JSON but the RSS guard returned nonzero.",
            )
            payload["apply_terminal_command"] = apply_terminal_command(candidate, scope)
            return payload
        payload["verdict"] = "pass"
        payload["record_command"] = record_command(
            candidate,
            scope,
            result_path,
            guard_path,
            "pass",
            f"{scope} gate passed with roundtrip, determinism, and RSS guard.",
        )
        nxt = next_scope(scope)
        if nxt is None:
            payload["next_action"] = "official_accounting_audit"
            payload["apply_terminal_command"] = apply_terminal_command(candidate, scope)
        else:
            payload["next_action"] = "promote_unchanged"
            payload["next_scope_bytes"] = nxt
            payload["next_gate_command"] = command_for_gate(
                candidate,
                nxt,
            )
            payload["apply_terminal_command"] = apply_terminal_command(
                candidate,
                scope,
                launch_next=True,
            )
        return payload

    return payload


def run_action(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def apply_terminal_decision(
    decision: dict[str, Any],
    *,
    normalize: bool,
    launch_next: bool,
    package_lower: bool,
) -> list[list[str]]:
    executed: list[list[str]] = []
    verdict = decision.get("verdict")

    if verdict == "pass":
        command = decision.get("record_command")
        if isinstance(command, list) and all(isinstance(part, str) for part in command):
            run_action(command)
            executed.append(command)
        if normalize:
            command = ["python3", "projects/enwiki9/tools/enwiki9_normalize_receipts.py"]
            run_action(command)
            executed.append(command)
        if launch_next:
            command = decision.get("next_gate_command")
            if isinstance(command, list) and all(isinstance(part, str) for part in command):
                run_action(command)
                executed.append(command)
        return executed

    if verdict == "rss_fail":
        command = decision.get("record_rss_failure_command")
        if isinstance(command, list) and all(isinstance(part, str) for part in command):
            run_action(command)
            executed.append(command)
        if normalize:
            command = ["python3", "projects/enwiki9/tools/enwiki9_normalize_receipts.py"]
            run_action(command)
            executed.append(command)
        if package_lower:
            lower = decision.get("lower_memory_suggestion")
            if isinstance(lower, dict):
                command = lower.get("package_command")
                if isinstance(command, list) and all(isinstance(part, str) for part in command):
                    run_action(command)
                    executed.append(command)
        return executed

    if verdict in {"roundtrip_fail", "determinism_fail", "guard_returncode_fail"}:
        command = decision.get("record_failure_command")
        if isinstance(command, list) and all(isinstance(part, str) for part in command):
            run_action(command)
            executed.append(command)
        if normalize:
            command = ["python3", "projects/enwiki9/tools/enwiki9_normalize_receipts.py"]
            run_action(command)
            executed.append(command)
        return executed

    return executed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--scope", type=int, required=True)
    parser.add_argument("--guard-json", type=pathlib.Path)
    parser.add_argument("--ppmd-step-kib", type=int, default=128)
    parser.add_argument("--apply-terminal", action="store_true")
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--launch-next", action="store_true")
    parser.add_argument("--package-lower", action="store_true")
    args = parser.parse_args()

    guard_path = args.guard_json or default_guard_path(args.candidate, args.scope)
    decision = decide(
        args.candidate,
        args.scope,
        guard_path,
        args.ppmd_step_kib,
    )
    print(json.dumps(decision, indent=2))
    if args.apply_terminal:
        executed = apply_terminal_decision(
            decision,
            normalize=args.normalize,
            launch_next=args.launch_next,
            package_lower=args.package_lower,
        )
        print(json.dumps({"executed_commands": executed}, indent=2))
        if not executed:
            print(
                "no applicable terminal action executed for verdict "
                f"{decision.get('verdict')!r}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
