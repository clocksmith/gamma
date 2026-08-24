#!/usr/bin/env python3
"""Emit a compact enwiki9 status receipt from current artifacts.

This is a read-only operator view. It does not launch compression. It combines
the conservative upper-bound certificate, cmix21 gate receipts, and current
process/resource state into one JSON/Markdown receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
from typing import Any

import cmix21_gate_decider
try:
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import research_contracts


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
CERT_PATH = ROOT / "upper_bound_certificate.json"
OUT_JSON = ROOT / "docs" / "status_receipt.json"
OUT_MD = ROOT / "docs" / "status_receipt.md"
RELEASE_RECEIPT_INDEX = ROOT / "docs" / "release_receipt_index.json"
LATEST_DELAYED_STATUS_LOG = ROOT / "run_logs" / "enwiki9_delayed_status_latest.log"
LOCAL_RSS_GUARD_KIB = 10_485_760
DECIMAL_10GB_GUARD_KIB = 10_000_000_000 // 1024


def scope_from_gate_label(label: str) -> int | None:
    """Recover an explicitly named raw scope such as ``10m`` from a label."""

    match = re.search(r"(?:^|_)([1-9][0-9]*)([kmg])(?:_|$)", label.lower())
    if match is None:
        return None
    scale = {"k": 1_000, "m": 1_000_000, "g": 1_000_000_000}[match.group(2)]
    return int(match.group(1)) * scale


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def logical_rel(path: pathlib.Path) -> str:
    return path.absolute().relative_to(REPO_ROOT).as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def release_receipt_state(objective: dict[str, Any]) -> dict[str, Any]:
    if not RELEASE_RECEIPT_INDEX.is_file():
        raise ValueError("release receipt index is missing; regenerate normalization views")
    result = research_contracts.validate_artifact(
        RELEASE_RECEIPT_INDEX,
        verify_files=False,
    )
    value = load_json(RELEASE_RECEIPT_INDEX)
    if value.get("objective") != objective:
        raise ValueError("release receipt index objective binding is stale")
    return {
        "path": logical_rel(RELEASE_RECEIPT_INDEX),
        "sha256": sha256(RELEASE_RECEIPT_INDEX),
        "validation_mode": value.get("validationMode"),
        "summary": result["summary"],
    }


def mtime_utc(path: pathlib.Path) -> str | None:
    try:
        return (
            dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
        )
    except OSError:
        return None


def sha256(path: pathlib.Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(1 << 20):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def top_status_by_label(cert: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = cert.get("top_status", [])
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("label"), str):
            out[row["label"]] = row
    return out


def operator_logs_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "latest_delayed_status_log": logical_rel(LATEST_DELAYED_STATUS_LOG),
        "latest_delayed_status_log_present": LATEST_DELAYED_STATUS_LOG.exists(),
    }
    if LATEST_DELAYED_STATUS_LOG.exists():
        try:
            state["latest_delayed_status_log_resolved"] = rel(LATEST_DELAYED_STATUS_LOG.resolve())
        except OSError:
            pass
    return state


def candidate_audit_summary_state() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "projects/enwiki9/tools/candidate_audit.py", "--json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    state: dict[str, Any] = {"returncode": proc.returncode}
    if proc.returncode != 0:
        state["error"] = proc.stderr.strip() or proc.stdout.strip() or "candidate audit failed"
        return state
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        state["error"] = f"candidate audit emitted invalid JSON: {exc}"
        return state
    summary = payload.get("summary")
    if isinstance(summary, dict):
        state["summary"] = summary
    return state


def active_candidate_recent_artifacts(candidate: str | None, limit: int = 12) -> list[dict[str, Any]]:
    if not candidate:
        return []
    result_dir = ROOT / "results" / candidate
    try:
        paths = [path for path in result_dir.rglob("*") if path.is_file()]
    except OSError:
        return []
    rows_with_stat: list[tuple[pathlib.Path, Any]] = []
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        rows_with_stat.append((path, stat))
    rows: list[dict[str, Any]] = []
    for path, stat in sorted(rows_with_stat, key=lambda item: item[1].st_mtime_ns, reverse=True)[:limit]:
        rows.append(
            {
                "path": rel(path),
                "bytes": stat.st_size,
                "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
            }
        )
    return rows


def pgrep(pattern: str) -> list[str]:
    proc = subprocess.run(
        ["pgrep", "-af", pattern],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return [line for line in lines if "enwiki9_status_receipt.py" not in line]


def ps_rss_for_pattern(pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in pgrep(pattern):
        pid_text = line.split(maxsplit=1)[0]
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        proc = subprocess.run(
            ["ps", "-o", "pid=,ppid=,pgid=,stat=,rss=,args=", "-p", str(pid)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        for ps_line in proc.stdout.splitlines():
            parts = ps_line.strip().split(maxsplit=5)
            if len(parts) < 6:
                continue
            try:
                rows.append(
                    {
                        "pid": int(parts[0]),
                        "ppid": int(parts[1]),
                        "pgid": int(parts[2]),
                        "stat": parts[3],
                        "rss_kib": int(parts[4]),
                        "args": parts[5],
                    }
                )
            except ValueError:
                continue
    return rows


def ps_all() -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["ps", "-eo", "pid=,ppid=,pgid=,stat=,rss=,args="],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split(maxsplit=5)
        if len(parts) < 6:
            continue
        try:
            rows.append(
                {
                    "pid": int(parts[0]),
                    "ppid": int(parts[1]),
                    "pgid": int(parts[2]),
                    "stat": parts[3],
                    "rss_kib": int(parts[4]),
                    "args": parts[5],
                }
            )
        except ValueError:
            continue
    return rows


def expand_process_groups(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pgids = {
        row.get("pgid")
        for row in seed_rows
        if isinstance(row.get("pgid"), int) and row.get("pgid", 0) > 0
    }
    if not pgids:
        return seed_rows
    all_rows = ps_all()
    expanded = [row for row in all_rows if row.get("pgid") in pgids]
    selected_pids = {
        row.get("pid") for row in expanded if isinstance(row.get("pid"), int)
    }
    changed = True
    while changed:
        changed = False
        for row in all_rows:
            pid = row.get("pid")
            if pid in selected_pids or row.get("ppid") not in selected_pids:
                continue
            expanded.append(row)
            if isinstance(pid, int):
                selected_pids.add(pid)
            changed = True
    return expanded or seed_rows


def is_cmix_codec_row(row: dict[str, Any]) -> bool:
    try:
        parts = shlex.split(str(row.get("args", "")))
    except ValueError:
        return False
    if not parts:
        return False
    executable = pathlib.Path(parts[0]).name
    codec_name = (
        executable.startswith("cmix21-mmap-bin")
        or executable in {"cmix", "cmix.bin", "cmix_orig"}
    )
    return codec_name and cmix_native_mode(parts) != "unknown"


def cmix_native_mode(parts: list[str]) -> str:
    if "-d" in parts:
        return "decode"
    if "-e" in parts:
        return "encode"
    if "-t" in parts:
        return "text_compress"
    if "-c" in parts:
        return "compress"
    if "-n" in parts:
        return "no_preprocess_compress"
    if "-s" in parts:
        return "preprocess_only"
    return "unknown"


def active_process_state() -> dict[str, Any]:
    guard_seed_rows = ps_rss_for_pattern(
        "run_with_rss_guard|run_with_resource_guard_v3|"
        "cmix_filebacked_fxcm_full_(roundtrip|stage).py|"
        "projects/enwiki9/lib/driver.py|cmix21-mmap-bin|"
        "fx2_public_repro_queue.py|fx2-public-package-.*/cmix_orig"
    )
    guard_rows = expand_process_groups(guard_seed_rows)
    research_rows = ps_rss_for_pattern(
        "projects/enwiki9/tools/(streaming_retrieval_.*shadow|page_order_gepa|"
        "article_order_teacher_distill).py"
    )
    controller_rows = ps_rss_for_pattern("projects/enwiki9/tools/cmix21_gate_decider.py")
    cmix_rows = [row for row in guard_rows if is_cmix_codec_row(row)]
    max_cmix = max(cmix_rows, key=lambda row: row["rss_kib"], default=None)
    state: dict[str, Any] = {
        "active_rows": guard_rows + research_rows,
        "research_rows": research_rows,
        "controller_rows": controller_rows,
        "cmix_rows": cmix_rows,
        "rss_guard_kib": LOCAL_RSS_GUARD_KIB,
        "decimal_10gb_guard_kib": DECIMAL_10GB_GUARD_KIB,
        "max_cmix_process": max_cmix,
        "active_scorer_observed": bool(guard_rows),
    }
    if guard_rows:
        active_tree_rss_kib = sum(int(row["rss_kib"]) for row in guard_rows)
        state["active_tree_rss_kib"] = active_tree_rss_kib
        state["active_tree_margin_kib"] = LOCAL_RSS_GUARD_KIB - active_tree_rss_kib
        state["active_tree_decimal_10gb_margin_kib"] = DECIMAL_10GB_GUARD_KIB - active_tree_rss_kib
        if active_tree_rss_kib > LOCAL_RSS_GUARD_KIB:
            state["active_tree_rss_over_guard_kib"] = active_tree_rss_kib - LOCAL_RSS_GUARD_KIB
            state["active_tree_rss_warning"] = (
                "active process tree RSS crossed the local numeric guard; the running kill guard is single-process"
            )
        if active_tree_rss_kib > DECIMAL_10GB_GUARD_KIB:
            state["active_tree_decimal_10gb_over_kib"] = active_tree_rss_kib - DECIMAL_10GB_GUARD_KIB
    if max_cmix is not None:
        state["single_process_margin_kib"] = LOCAL_RSS_GUARD_KIB - int(max_cmix["rss_kib"])
        state["single_process_decimal_10gb_margin_kib"] = DECIMAL_10GB_GUARD_KIB - int(max_cmix["rss_kib"])
        if int(max_cmix["rss_kib"]) > DECIMAL_10GB_GUARD_KIB:
            state["single_process_decimal_10gb_over_kib"] = int(max_cmix["rss_kib"]) - DECIMAL_10GB_GUARD_KIB
            state["single_process_decimal_10gb_warning"] = (
                "active cmix RSS exceeds decimal 10GB even if it remains under the local binary 10GiB guard"
            )
        io_path = pathlib.Path("/proc") / str(max_cmix["pid"]) / "io"
        proc_io: dict[str, int] = {}
        try:
            for line in io_path.read_text().splitlines():
                if ":" not in line:
                    continue
                key, raw_value = line.split(":", 1)
                try:
                    proc_io[key.strip()] = int(raw_value.strip())
                except ValueError:
                    continue
        except OSError:
            proc_io = {}
        if proc_io:
            state["active_proc_io"] = proc_io
        try:
            parts = shlex.split(str(max_cmix["args"]))
        except ValueError:
            parts = []
        process_cwd: pathlib.Path | None = None
        try:
            process_cwd = pathlib.Path(f"/proc/{max_cmix['pid']}/cwd").resolve()
        except OSError:
            process_cwd = None
        if parts:
            state["active_cmix_mode"] = cmix_native_mode(parts)
        if len(parts) >= 2:
            input_path = pathlib.Path(parts[-2])
            output_path = pathlib.Path(parts[-1])
            if process_cwd is not None:
                if not input_path.is_absolute():
                    input_path = process_cwd / input_path
                if not output_path.is_absolute():
                    output_path = process_cwd / output_path
            output_temp_path = pathlib.Path(str(output_path) + ".cmix.temp")
            temp: dict[str, Any] = {
                "input_path": str(input_path),
                "output_path": str(output_path),
                "output_temp_path": str(output_temp_path),
            }
            for label, path in (
                ("input_bytes", input_path),
                ("output_bytes", output_path),
                ("output_temp_bytes", output_temp_path),
            ):
                try:
                    temp[label] = path.stat().st_size
                except OSError:
                    temp[label] = None
            temp["input_mtime_utc"] = mtime_utc(input_path)
            temp["output_mtime_utc"] = mtime_utc(output_path)
            temp["output_temp_mtime_utc"] = mtime_utc(output_temp_path)
            state["active_temp_io"] = temp
    return state


def argv_option(parts: list[str], option: str) -> str | None:
    try:
        index = parts.index(option)
    except ValueError:
        return None
    if index + 1 >= len(parts):
        return None
    return parts[index + 1]


def has_script(parts: list[str], name: str) -> bool:
    return any(pathlib.Path(part).name == name for part in parts)


def process_cwd(row: dict[str, Any]) -> pathlib.Path | None:
    pid = row.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool):
        return None
    try:
        return pathlib.Path(f"/proc/{pid}/cwd").resolve()
    except OSError:
        return None


def resolved_process_path(row: dict[str, Any], text: str) -> pathlib.Path:
    path = pathlib.Path(text)
    if path.is_absolute():
        return path
    return (process_cwd(row) or REPO_ROOT) / path


def descendant_of(
    row: dict[str, Any], ancestor_pid: int, parent_by_pid: dict[int, int]
) -> bool:
    current = row.get("pid")
    visited: set[int] = set()
    while isinstance(current, int) and current > 0 and current not in visited:
        if current == ancestor_pid:
            return True
        visited.add(current)
        current = parent_by_pid.get(current)
    return False


def resource_guard_metrics(guard: dict[str, Any]) -> dict[str, Any]:
    peaks = guard.get("peaks") if isinstance(guard.get("peaks"), dict) else {}
    latest = (
        guard.get("latest_sample")
        if isinstance(guard.get("latest_sample"), dict)
        else {}
    )
    max_single = peaks.get(
        "max_sampled_single_rss_kib", guard.get("max_sampled_single_rss_kib")
    )
    max_tree = peaks.get(
        "max_sampled_tree_rss_kib", guard.get("max_sampled_tree_rss_kib")
    )
    latest_single = latest.get("max_single_rss_kib")
    latest_tree = latest.get("tree_rss_kib")
    out: dict[str, Any] = {
        "rss_guard_status": guard.get("status"),
        "sample_count": guard.get("sample_count"),
        "returncode": guard.get("returncode"),
        "max_sampled_single_rss_kib": max_single,
        "max_sampled_tree_rss_kib": max_tree,
        "latest_sample_max_single_rss_kib": latest_single,
        "latest_sample_tree_rss_kib": latest_tree,
        "cgroup_memory_peak_bytes": peaks.get("cgroup_memory_peak_bytes"),
        "latest_cgroup_current_bytes": latest.get("cgroup_current_bytes"),
        "cgroup_events_delta": (
            guard.get("cgroup_events", {}).get("delta")
            if isinstance(guard.get("cgroup_events"), dict)
            else None
        ),
    }
    if isinstance(max_single, int):
        out["single_rss_margin_kib"] = LOCAL_RSS_GUARD_KIB - max_single
    if isinstance(max_tree, int):
        out["tree_rss_margin_kib"] = LOCAL_RSS_GUARD_KIB - max_tree
    if isinstance(latest_single, int):
        out["latest_sample_single_rss_margin_kib"] = (
            LOCAL_RSS_GUARD_KIB - latest_single
        )
    if isinstance(latest_tree, int):
        out["latest_sample_tree_rss_margin_kib"] = (
            LOCAL_RSS_GUARD_KIB - latest_tree
        )
    return out


def progress_log_state(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for line in reversed(lines):
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            percent = float(fields[0])
            payload_bytes = int(fields[1])
        except ValueError:
            continue
        if not 0.0 <= percent <= 100.0 or payload_bytes < 0:
            continue
        try:
            stat = path.stat()
        except OSError:
            return None
        return {
            "path": logical_rel(path),
            "bytes": stat.st_size,
            "mtime_utc": mtime_utc(path),
            "reported_scope_percent": percent,
            "reported_payload_bytes": payload_bytes,
        }
    return None


def live_q1_full_gate_from_process(
    process_state: dict[str, Any], adaptive_state: dict[str, Any]
) -> dict[str, Any] | None:
    """Bind a live q1 full-roundtrip coordinator to its current guarded stage."""

    rows = process_state.get("active_rows")
    if not isinstance(rows, list):
        return None
    process_rows = [row for row in rows if isinstance(row, dict)]
    parent_by_pid = {
        row["pid"]: row["ppid"]
        for row in process_rows
        if isinstance(row.get("pid"), int) and isinstance(row.get("ppid"), int)
    }
    for coordinator in process_rows:
        try:
            parts = shlex.split(str(coordinator.get("args", "")))
        except ValueError:
            continue
        if not has_script(parts, "cmix_filebacked_fxcm_full_roundtrip.py"):
            continue
        result_root_text = argv_option(parts, "--result-root")
        corpus_text = argv_option(parts, "--corpus")
        arm = argv_option(parts, "--arm")
        if result_root_text is None or corpus_text is None or arm not in {"a", "b"}:
            continue
        result_root = resolved_process_path(coordinator, result_root_text).resolve()
        corpus = resolved_process_path(coordinator, corpus_text).resolve()
        try:
            scope = corpus.stat().st_size
        except OSError:
            scope = None
        coordinator_pid = coordinator.get("pid")
        if not isinstance(coordinator_pid, int):
            continue

        guard_row: dict[str, Any] | None = None
        guard_parts: list[str] = []
        guard_path: pathlib.Path | None = None
        for row in process_rows:
            if not descendant_of(row, coordinator_pid, parent_by_pid):
                continue
            try:
                candidate_parts = shlex.split(str(row.get("args", "")))
            except ValueError:
                continue
            if not has_script(candidate_parts, "run_with_resource_guard_v3.py"):
                continue
            guard_text = argv_option(candidate_parts, "--guard-json")
            if guard_text is None:
                continue
            candidate_path = resolved_process_path(row, guard_text).resolve()
            if candidate_path.parent.parent != result_root:
                continue
            guard_row = row
            guard_parts = candidate_parts
            guard_path = candidate_path
            break
        if guard_row is None or guard_path is None:
            continue

        phase = guard_path.parent.name
        stage_command = (
            guard_parts[guard_parts.index("--") + 1 :]
            if "--" in guard_parts
            else []
        )
        work_root_text = argv_option(stage_command, "--work-root")
        progress: dict[str, Any] | None = None
        if work_root_text is not None:
            work_root = resolved_process_path(guard_row, work_root_text).resolve()
            progress = progress_log_state(work_root / "progress.log")

        guard = load_json(guard_path)
        receipt_path = result_root / "full-roundtrip-receipt.json"
        status = guard.get("status")
        full_receipt = load_json(receipt_path)
        if (
            receipt_path.is_file()
            and full_receipt.get("schema")
            == "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
            and isinstance(full_receipt.get("terminal_pass"), bool)
        ):
            verdict = (
                "pass" if full_receipt["terminal_pass"] is True else "roundtrip_fail"
            )
            next_action = "record_q1_full_roundtrip_terminal"
        elif status == "running":
            verdict = "running"
            next_action = "wait_for_gate_completion"
        else:
            verdict = "receipt_incomplete"
            next_action = "wait_for_gate_receipts"
        gate: dict[str, Any] = {
            "candidate": result_root.name,
            "guard_pid": guard_row.get("pid"),
            "coordinator_pid": coordinator_pid,
            "scope_bytes": scope,
            "verdict": verdict,
            "next_action": next_action,
            "source": "live_q1_full_roundtrip_guard",
            "active_stage": phase,
            "roundtrip_arm": arm,
            "driver_result_json": logical_rel(receipt_path),
            "driver_result_json_present": receipt_path.is_file(),
            "rss_guard_json": logical_rel(guard_path),
            "rss_guard_json_present": guard_path.is_file(),
            "command": parts,
            "promotion_authorized": False,
            "claim_rule": (
                "The live q1 guard proves only current resource-bounded execution; "
                "full-roundtrip, parent identity, determinism, and score credit remain "
                "false until their terminal receipts exist."
            ),
        }
        gate.update(resource_guard_metrics(guard))
        if progress is not None:
            gate["codec_progress"] = progress
        try:
            guard_stat = guard_path.stat()
        except OSError:
            pass
        else:
            gate["rss_guard_json_bytes"] = guard_stat.st_size
            gate["rss_guard_json_mtime_utc"] = mtime_utc(guard_path)
            gate["rss_guard_json_sha256"] = sha256(guard_path)

        owner = adaptive_job_owning_guard(gate, process_state, adaptive_state)
        if owner is not None:
            gate = bind_guard_to_adaptive_job(gate, owner)
            gate["source"] = "live_q1_full_roundtrip_guard"
            gate["driver_result_json"] = logical_rel(receipt_path)
            gate["driver_result_json_present"] = receipt_path.is_file()
            gate["claim_rule"] = (
                "The q1 coordinator, nested guard, and adaptive owner agree on "
                "candidate identity; this is live monitor evidence only."
            )
        return gate
    return None


def observed_gate_command_state(
    candidate: str | None,
    scope: int | None,
    process_state: dict[str, Any],
) -> dict[str, Any]:
    rows = process_state.get("active_rows")
    if not isinstance(rows, list):
        rows = []
    driver_rows = [
        row
        for row in rows
        if isinstance(row, dict)
        and process_role(row.get("args")) in {"driver", "q1_full_roundtrip"}
    ]
    observed: list[dict[str, Any]] = []
    for row in driver_rows:
        args = str(row.get("args", ""))
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.split()
        role = process_role(args)
        observed_candidate: str | None = None
        observed_scope: int | None = None
        check_determinism = False
        proof_schedule = "unknown"
        command_contract_matches = False
        if role == "driver":
            driver_marker = "projects/enwiki9/lib/driver.py"
            if driver_marker in parts:
                driver_index = parts.index(driver_marker)
                if driver_index + 1 < len(parts):
                    observed_candidate = parts[driver_index + 1]
            limit = argv_option(parts, "--limit")
            if limit is not None:
                try:
                    observed_scope = int(limit)
                except ValueError:
                    observed_scope = None
            check_determinism = "--check-determinism" in parts
            proof_schedule = "generic_driver_with_determinism"
            command_contract_matches = check_determinism
        else:
            result_root_text = argv_option(parts, "--result-root")
            corpus_text = argv_option(parts, "--corpus")
            arm = argv_option(parts, "--arm")
            if result_root_text is not None:
                result_root = resolved_process_path(row, result_root_text).resolve()
                observed_candidate = result_root.name
            if corpus_text is not None:
                corpus = resolved_process_path(row, corpus_text).resolve()
                try:
                    observed_scope = corpus.stat().st_size
                except OSError:
                    observed_scope = None
            required = {
                "--build-receipt",
                "--build-verification",
                "--raw-binary",
                "--scope-build-receipt",
                "--program-lock-verification",
                "--transfer-receipt",
                "--transfer-verification",
                "--authoritative-parent-payload",
                "--resource-guard",
                "--stage-runner",
                "--scratch-root",
                "--cgroup-path",
                "--lease-path",
            }
            command_contract_matches = arm in {"a", "b"} and required.issubset(
                parts
            )
            proof_schedule = (
                f"q1_arm_{arm}_full_roundtrip"
                if arm in {"a", "b"}
                else "q1_invalid_arm"
            )
        observed.append(
            {
                "pid": row.get("pid"),
                "role": role,
                "candidate": observed_candidate,
                "candidate_matches": bool(candidate and observed_candidate == candidate),
                "scope_bytes": observed_scope,
                "scope_matches": observed_scope == scope,
                "check_determinism": check_determinism,
                "proof_schedule": proof_schedule,
                "command_contract_matches": command_contract_matches,
            }
        )
    active_gate_observed = any(
        row.get("candidate_matches") is True
        and row.get("scope_matches") is True
        and row.get("command_contract_matches") is True
        for row in observed
    )
    mismatch_count = sum(
        1
        for row in observed
        if not (
            row.get("candidate_matches") is True
            and row.get("scope_matches") is True
            and row.get("command_contract_matches") is True
        )
    )
    return {
        "expected_candidate": candidate,
        "expected_scope_bytes": scope,
        "driver_process_count": len(observed),
        "active_gate_command_observed": active_gate_observed,
        "mismatch_count": mismatch_count,
        "driver_processes": observed,
    }


def observed_controller_command_state(
    candidate: str | None,
    scope: int | None,
    process_state: dict[str, Any],
) -> dict[str, Any]:
    rows = process_state.get("controller_rows")
    if not isinstance(rows, list):
        rows = []
    observed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        args = str(row.get("args", ""))
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.split()
        controller_candidate: str | None = None
        if "projects/enwiki9/tools/cmix21_gate_decider.py" in parts:
            index = parts.index("projects/enwiki9/tools/cmix21_gate_decider.py")
            if index + 1 < len(parts):
                controller_candidate = parts[index + 1]
        controller_scope: int | None = None
        if "--scope" in parts:
            index = parts.index("--scope")
            if index + 1 < len(parts):
                try:
                    controller_scope = int(parts[index + 1])
                except ValueError:
                    controller_scope = None
        observed.append(
            {
                "pid": row.get("pid"),
                "candidate": controller_candidate,
                "candidate_matches_active": bool(candidate and controller_candidate == candidate),
                "scope_bytes": controller_scope,
                "scope_matches_active_gate": controller_scope == scope,
                "apply_terminal": "--apply-terminal" in parts,
                "normalize": "--normalize" in parts,
                "launch_next": "--launch-next" in parts,
                "package_lower": "--package-lower" in parts,
            }
        )
    return {
        "expected_active_candidate": candidate,
        "expected_active_scope_bytes": scope,
        "controller_process_count": len(observed),
        "controller_processes": observed,
        "scope_note": (
            "Controller scope may be the completed parent gate that launched the active child; "
            "the observed driver command is authoritative for the active gate scope."
        ),
    }


def active_candidate_from_cert(cert: dict[str, Any]) -> tuple[str | None, int | None]:
    labels = top_status_by_label(cert)
    active_gate = labels.get("active gate", {})
    next_gate = labels.get("next gate", {})
    active = labels.get("active candidate", {})
    candidate = active_gate.get("program_id") or next_gate.get("program_id") or active.get("program_id")
    scope = active_gate.get("scope_bytes") or next_gate.get("scope_bytes")
    if isinstance(candidate, str) and isinstance(scope, int):
        return candidate, scope
    if isinstance(candidate, str):
        return candidate, None
    return None, None


def active_candidate_from_process(process_state: dict[str, Any]) -> tuple[str | None, int | None]:
    rows = process_state.get("active_rows")
    if not isinstance(rows, list):
        return None, None
    for row in rows:
        if not isinstance(row, dict):
            continue
        args = str(row.get("args", ""))
        if "projects/enwiki9/lib/driver.py" not in args:
            continue
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.split()
        try:
            driver_index = parts.index("projects/enwiki9/lib/driver.py")
        except ValueError:
            continue
        candidate = parts[driver_index + 1] if driver_index + 1 < len(parts) else None
        scope: int | None = None
        if "--limit" in parts:
            index = parts.index("--limit")
            if index + 1 < len(parts):
                try:
                    scope = int(parts[index + 1])
                except ValueError:
                    scope = None
        if isinstance(candidate, str) and candidate:
            return candidate, scope
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            parts = shlex.split(str(row.get("args", "")))
        except ValueError:
            continue
        if not has_script(parts, "cmix_filebacked_fxcm_full_roundtrip.py"):
            continue
        result_root_text = argv_option(parts, "--result-root")
        corpus_text = argv_option(parts, "--corpus")
        if result_root_text is None:
            continue
        candidate = resolved_process_path(row, result_root_text).resolve().name
        scope: int | None = None
        if corpus_text is not None:
            try:
                scope = resolved_process_path(row, corpus_text).resolve().stat().st_size
            except OSError:
                scope = None
        return candidate, scope
    return None, None


def live_speedlab_gate_from_process(
    process_state: dict[str, Any],
) -> dict[str, Any] | None:
    """Recover a live guarded gate directly from its RSS-guard process."""

    rows = process_state.get("active_rows")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        args = str(row.get("args", ""))
        if "run_with_rss_guard.py" not in args or "--label" not in args:
            continue
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.split()
        if "--guard-json" not in parts or "--label" not in parts or "--" not in parts:
            continue
        guard_index = parts.index("--guard-json")
        label_index = parts.index("--label")
        command_index = parts.index("--")
        if (
            guard_index + 1 >= len(parts)
            or label_index + 1 >= len(parts)
            or command_index + 1 >= len(parts)
        ):
            continue
        guard_path_text = parts[guard_index + 1]
        # A shell launcher can expose the unevaluated command (for example,
        # ``--guard-json $out/guard.json``) alongside the actual guard child.
        # Do not let that wrapper shadow the child's concrete live receipt.
        if "$" in guard_path_text:
            continue
        process_cwd: pathlib.Path | None = None
        pid = row.get("pid")
        if isinstance(pid, int) and not isinstance(pid, bool):
            try:
                process_cwd = pathlib.Path(f"/proc/{pid}/cwd").resolve()
            except OSError:
                process_cwd = None
        guard_path = pathlib.Path(guard_path_text)
        if not guard_path.is_absolute():
            guard_path = (process_cwd or REPO_ROOT) / guard_path
        label = parts[label_index + 1]
        command = parts[command_index + 1 :]
        if not command:
            continue
        candidate = label
        driver_marker = "projects/enwiki9/lib/driver.py"
        if driver_marker in command:
            driver_index = command.index(driver_marker)
            if driver_index + 1 < len(command):
                candidate = command[driver_index + 1]
        input_path: pathlib.Path | None = None
        output_path: pathlib.Path | None = None
        if "--input" in command:
            input_index = command.index("--input")
            if input_index + 1 < len(command):
                input_path = pathlib.Path(command[input_index + 1])
        if "--output" in command:
            output_index = command.index("--output")
            if output_index + 1 < len(command):
                output_path = pathlib.Path(command[output_index + 1])
        if output_path is None and len(command) >= 3:
            input_path = pathlib.Path(command[-2])
            output_path = pathlib.Path(command[-1])
        if input_path is not None or output_path is not None:
            if process_cwd is not None:
                if input_path is not None and not input_path.is_absolute():
                    input_path = process_cwd / input_path
                if output_path is not None and not output_path.is_absolute():
                    output_path = process_cwd / output_path
        scope: int | None = None
        if "--limit" in command:
            limit_index = command.index("--limit")
            if limit_index + 1 < len(command):
                try:
                    scope = int(command[limit_index + 1])
                except ValueError:
                    scope = None
        if scope is None:
            scope = scope_from_gate_label(label)
        if scope is None and input_path is not None:
            try:
                scope = input_path.stat().st_size
            except OSError:
                scope = None
        guard = load_json(guard_path)
        guard_status = guard.get("status")
        receipt_path = guard_path.parent / "receipt.json"
        if guard_status == "running":
            verdict = "running"
            next_action = "wait_for_gate_completion"
        elif receipt_path.is_file():
            verdict = "pass" if guard.get("returncode") == 0 else "guard_returncode_fail"
            next_action = "inspect_speedlab_receipt"
        else:
            verdict = "receipt_incomplete"
            next_action = "wait_for_gate_receipts"
        gate: dict[str, Any] = {
            "candidate": candidate,
            "guard_pid": row.get("pid"),
            "scope_bytes": scope,
            "verdict": verdict,
            "next_action": next_action,
            "source": "live_speedlab_rss_guard",
            "driver_result_json": str(receipt_path),
            "driver_result_json_present": receipt_path.is_file(),
            "rss_guard_json": str(guard_path),
            "rss_guard_json_present": guard_path.is_file(),
            "rss_guard_status": guard_status,
            "sample_count": guard.get("sample_count"),
            "returncode": guard.get("returncode"),
            "max_sampled_single_rss_kib": guard.get(
                "max_sampled_single_rss_kib"
            ),
            "max_sampled_tree_rss_kib": guard.get("max_sampled_tree_rss_kib"),
            "latest_sample_max_single_rss_kib": (
                guard.get("latest_sample", {}).get("max_single_rss_kib")
                if isinstance(guard.get("latest_sample"), dict)
                else None
            ),
            "latest_sample_tree_rss_kib": (
                guard.get("latest_sample", {}).get("tree_rss_kib")
                if isinstance(guard.get("latest_sample"), dict)
                else None
            ),
            "command": command,
            "promotion_authorized": False,
            "claim_rule": "A speedlab prefix is not a constructive 1G score.",
        }
        gate.update(resource_guard_metrics(guard))
        if input_path is not None:
            gate["input_path"] = str(input_path)
        if output_path is not None:
            gate["output_path"] = str(output_path)
        try:
            guard_stat = guard_path.stat()
        except OSError:
            pass
        else:
            gate["rss_guard_json_bytes"] = guard_stat.st_size
            gate["rss_guard_json_mtime_utc"] = mtime_utc(guard_path)
            gate["rss_guard_json_sha256"] = sha256(guard_path)
        max_single = gate.get("max_sampled_single_rss_kib")
        max_tree = gate.get("max_sampled_tree_rss_kib")
        latest_single = gate.get("latest_sample_max_single_rss_kib")
        latest_tree = gate.get("latest_sample_tree_rss_kib")
        if isinstance(max_single, int):
            gate["single_rss_margin_kib"] = LOCAL_RSS_GUARD_KIB - max_single
        if isinstance(max_tree, int):
            gate["tree_rss_margin_kib"] = LOCAL_RSS_GUARD_KIB - max_tree
        if isinstance(latest_single, int):
            gate["latest_sample_single_rss_margin_kib"] = (
                LOCAL_RSS_GUARD_KIB - latest_single
            )
        if isinstance(latest_tree, int):
            gate["latest_sample_tree_rss_margin_kib"] = (
                LOCAL_RSS_GUARD_KIB - latest_tree
            )
        return gate
    return None


def adaptive_job_owning_guard(
    gate: dict[str, Any] | None,
    process_state: dict[str, Any],
    adaptive_state: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the live adaptive job whose worker owns a nested RSS guard."""

    if not isinstance(gate, dict):
        return None
    guard_pid = gate.get("guard_pid")
    if not isinstance(guard_pid, int) or isinstance(guard_pid, bool):
        return None
    rows = process_state.get("active_rows")
    if not isinstance(rows, list):
        return None
    parent_by_pid = {
        row.get("pid"): row.get("ppid")
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("pid"), int)
        and isinstance(row.get("ppid"), int)
    }

    ancestors: set[int] = set()
    current = guard_pid
    while current not in ancestors:
        ancestors.add(current)
        parent = parent_by_pid.get(current)
        if not isinstance(parent, int) or parent <= 0:
            break
        current = parent

    running_jobs = adaptive_state.get("running_jobs")
    if not isinstance(running_jobs, list):
        return None
    owners = [
        row
        for row in running_jobs
        if isinstance(row, dict)
        and row.get("worker_pid_live") is True
        and isinstance(row.get("worker_pid"), int)
        and row.get("worker_pid") in ancestors
    ]
    if len(owners) != 1:
        return None
    return owners[0]


def bind_guard_to_adaptive_job(
    gate: dict[str, Any], job: dict[str, Any]
) -> dict[str, Any]:
    """Keep guard metrics while restoring the owning job's durable identity."""

    bound = dict(gate)
    bound["guard_label_candidate"] = gate.get("candidate")
    bound["guard_inferred_scope_bytes"] = gate.get("scope_bytes")
    candidate = job.get("candidate_id")
    bound["candidate"] = candidate
    bound["gate_size"] = job.get("gate_size")
    bound.pop("scope_bytes", None)
    experiment_reference = job.get("experiment")
    if isinstance(experiment_reference, dict):
        experiment_path = experiment_reference.get("path")
        if isinstance(experiment_path, str):
            resolved_experiment = (ROOT / experiment_path).resolve()
            expected_digest = experiment_reference.get("sha256")
            observed_digest = sha256(resolved_experiment)
            if ROOT.resolve() not in resolved_experiment.parents:
                bound["scope_status"] = "experiment-reference-escapes-project"
            elif expected_digest == f"sha256:{observed_digest}":
                research_contracts.validate_artifact(resolved_experiment)
                experiment = load_json(resolved_experiment)
                population = experiment.get("population")
                if isinstance(population, dict):
                    bound["scope_unit"] = population.get("unit")
                    if isinstance(population.get("scopeBytes"), int):
                        bound["scope_bytes"] = population["scopeBytes"]
                    if isinstance(population.get("scopeSymbols"), int):
                        bound["scope_symbols"] = population["scopeSymbols"]
            else:
                bound["scope_status"] = "experiment-reference-mismatch"
    if "scope_bytes" not in bound and "scope_symbols" not in bound:
        bound.setdefault("scope_status", "missing-experiment-population")
    bound["adaptive_job_id"] = job.get("job_id")
    bound["adaptive_job_path"] = job.get("path")
    bound["adaptive_worker_pid"] = job.get("worker_pid")
    bound["source"] = "live_adaptive_tool_rss_guard"
    if isinstance(candidate, str) and candidate:
        decision_path = ROOT / "results" / candidate / "decision.json"
        bound["driver_result_json"] = logical_rel(decision_path)
        bound["driver_result_json_present"] = decision_path.is_file()
    bound["claim_rule"] = (
        "A nested RSS guard inherits candidate and scope from its verified live "
        "adaptive worker; the guard supplies resource and terminal metrics only."
    )
    return bound


def gate_state(candidate: str | None, scope: int | None) -> dict[str, Any] | None:
    if candidate is None or scope is None:
        return None
    guard = cmix21_gate_decider.default_guard_path(candidate, scope)
    return cmix21_gate_decider.decide(candidate, scope, guard, step_kib=128)


def adaptive_running_jobs_state() -> dict[str, Any]:
    running_dir = ROOT / "operations" / "adaptive" / "running"
    pending_dir = ROOT / "operations" / "adaptive" / "pending"
    jobs: list[dict[str, Any]] = []
    try:
        paths = sorted(running_dir.glob("*.json"))
    except OSError:
        paths = []
    for path in paths:
        job = load_json(path)
        if not job:
            continue
        worker_pid = job.get("worker_pid")
        worker_pid_live = False
        if isinstance(worker_pid, int) and not isinstance(worker_pid, bool) and worker_pid > 0:
            try:
                os.kill(worker_pid, 0)
                command = [
                    token.decode("utf-8", errors="replace")
                    for token in pathlib.Path(f"/proc/{worker_pid}/cmdline")
                    .read_bytes()
                    .split(b"\0")
                    if token
                ]
            except OSError:
                worker_pid_live = False
            else:
                tool = job.get("tool")
                if isinstance(tool, str):
                    expected_command = str((ROOT / tool).resolve())
                    worker_pid_live = expected_command in command
                else:
                    expected_command = str(
                        (ROOT / "tools" / "candidate_triage.py").resolve()
                    )
                    candidate_id = job.get("candidate_id")
                    worker_pid_live = (
                        expected_command in command
                        and isinstance(candidate_id, str)
                        and candidate_id in command
                    )
        jobs.append(
            {
                "job_id": job.get("job_id") or path.stem,
                "candidate_id": job.get("candidate_id"),
                "gate_size": job.get("gate_size"),
                "state": job.get("state"),
                "started_at": job.get("started_at"),
                "worker_pid": worker_pid,
                "worker_pid_live": worker_pid_live,
                "experiment": job.get("experiment"),
                "path": logical_rel(path),
            }
        )
    pending_count = 0
    held_pending_count = 0
    try:
        pending_paths = sorted(pending_dir.glob("*.json"))
    except OSError:
        pending_paths = []
    for path in pending_paths:
        job = load_json(path)
        if not job:
            continue
        pending_count += 1
        if job.get("held") is True:
            held_pending_count += 1
    return {
        "running_job_count": len(jobs),
        "running_jobs": jobs,
        "pending_job_count": pending_count,
        "held_pending_job_count": held_pending_count,
        "claimable_pending_job_count": pending_count - held_pending_count,
    }


def gate_liveness_state(
    candidate: str | None,
    scope: int | None,
    gate: dict[str, Any] | None,
    process_state: dict[str, Any],
    adaptive_state: dict[str, Any],
) -> dict[str, Any]:
    gate = gate if isinstance(gate, dict) else {}
    verdict = gate.get("verdict")
    receipt_running = verdict == "running" or gate.get("rss_guard_status") == "running"
    byte_scope = gate.get("scope_bytes")
    observed_gate = observed_gate_command_state(candidate, byte_scope, process_state)
    observed_controller = observed_controller_command_state(
        candidate, byte_scope, process_state
    )
    controller_processes = observed_controller.get("controller_processes")
    if not isinstance(controller_processes, list):
        controller_processes = []
    matching_controllers = [
        row
        for row in controller_processes
        if isinstance(row, dict) and row.get("candidate_matches_active") is True
    ]
    running_jobs = adaptive_state.get("running_jobs")
    if not isinstance(running_jobs, list):
        running_jobs = []
    matching_jobs = [
        row
        for row in running_jobs
        if isinstance(row, dict)
        and row.get("candidate_id") == candidate
        and row.get("gate_size") == scope
    ]
    driver_observed = observed_gate.get("active_gate_command_observed") is True
    live_worker_job = any(
        row.get("worker_pid_live") is True for row in matching_jobs
    )
    persisted_running = receipt_running or live_worker_job
    live = persisted_running and (
        driver_observed
        or bool(matching_controllers)
        or live_worker_job
    )
    if live:
        classification = "live_observed_owner"
    elif not persisted_running:
        classification = "not_persisted_running"
    elif matching_jobs:
        classification = "registered_running_job_without_live_owner"
    else:
        classification = "orphaned_running_receipt"
    return {
        "candidate": candidate,
        "gate_size": scope,
        "scope_bytes": gate.get("scope_bytes"),
        "scope_symbols": gate.get("scope_symbols"),
        "scope_unit": gate.get("scope_unit"),
        "receipt_running": receipt_running,
        "persisted_running": persisted_running,
        "classification": classification,
        "is_live": live,
        "matching_driver_observed": driver_observed,
        "matching_controller_count": len(matching_controllers),
        "matching_adaptive_job_count": len(matching_jobs),
        "matching_adaptive_worker_live": live_worker_job,
        "claim_rule": (
            "A running receipt or registered adaptive job is live only with an "
            "exact driver, owning controller, or matching live worker PID and command."
        ),
    }


def reconcile_gate_liveness(
    gate: dict[str, Any] | None,
    liveness: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(gate, dict):
        return None
    if (
        liveness.get("is_live") is True
        and gate.get("verdict") in {None, "incomplete", "receipt_incomplete"}
    ):
        reconciled = dict(gate)
        reconciled["persisted_verdict"] = gate.get("verdict")
        reconciled["persisted_next_action"] = gate.get("next_action")
        reconciled["verdict"] = "running"
        reconciled["next_action"] = "wait_for_gate_completion"
        reconciled["live_gate"] = True
        reconciled["liveness_classification"] = liveness.get("classification")
        return reconciled
    if liveness.get("persisted_running") is not True or liveness.get("is_live") is True:
        return gate
    reconciled = dict(gate)
    reconciled["persisted_verdict"] = gate.get("verdict")
    reconciled["persisted_next_action"] = gate.get("next_action")
    reconciled["verdict"] = "orphaned_running_receipt"
    reconciled["next_action"] = "reconcile_orphaned_gate_receipt"
    reconciled["live_gate"] = False
    reconciled["liveness_classification"] = liveness.get("classification")
    return reconciled


def gate_evidence_status(
    gate: dict[str, Any] | None,
    liveness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate = gate if isinstance(gate, dict) else {}
    liveness = liveness if isinstance(liveness, dict) else {}
    verdict = gate.get("verdict")
    driver_present = gate.get("driver_result_json_present") is True
    guard_present = gate.get("rss_guard_json_present") is True
    guard_terminal = (
        guard_present
        and gate.get("rss_guard_status") != "running"
        and (
            gate.get("returncode") is not None
            or verdict == "cancelled_no_result"
        )
    )
    scored = driver_present and verdict in {
        "pass",
        "roundtrip_fail",
        "determinism_fail",
        "guard_returncode_fail",
    }
    live_guard_only = guard_present and not driver_present and gate.get("rss_guard_status") == "running"
    if verdict == "orphaned_running_receipt":
        claim_status = "orphaned_running_receipt"
    elif verdict == "cancelled_no_result":
        claim_status = "cancelled_no_score"
    elif scored:
        claim_status = "scored_gate_result_present"
    elif live_guard_only:
        claim_status = "live_guard_monitor_only"
    elif guard_present and not driver_present:
        claim_status = "guard_without_driver_result"
    else:
        claim_status = "awaiting_gate_receipts"
    return {
        "driver_result_terminal": driver_present,
        "rss_guard_terminal": guard_terminal,
        "scored_gate_result_present": scored,
        "live_guard_only": live_guard_only,
        "live_gate": liveness.get("is_live"),
        "liveness_classification": liveness.get("classification"),
        "claim_status": claim_status,
        "claim_rule": "Only a terminal driver result with roundtrip evidence can become a benchmark row.",
    }


def active_gate_status_state(
    cert_row: dict[str, Any] | None,
    gate: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Expose the live gate decision through the compatibility active_gate row."""

    if not isinstance(cert_row, dict) and not isinstance(gate, dict):
        return None
    row = dict(cert_row) if isinstance(cert_row, dict) else {}
    row["label"] = "active gate"
    if not isinstance(gate, dict):
        return row

    candidate = gate.get("candidate")
    scope = gate.get("scope_bytes")
    verdict = gate.get("verdict")
    row["source"] = gate.get("source", "gate_decision")
    if isinstance(candidate, str):
        row["program_id"] = candidate
    if isinstance(scope, int):
        row["scope_bytes"] = scope
    elif isinstance(gate.get("scope_symbols"), int):
        row.pop("scope_bytes", None)
        row["scope_symbols"] = gate["scope_symbols"]
        row["scope_unit"] = gate.get("scope_unit")
    if isinstance(verdict, str):
        row["status"] = verdict
    for key in (
        "next_action",
        "driver_result_json",
        "driver_result_json_present",
        "rss_guard_json",
        "rss_guard_json_present",
        "rss_guard_status",
        "sample_count",
        "returncode",
        "max_sampled_single_rss_kib",
        "max_sampled_tree_rss_kib",
        "single_rss_margin_kib",
        "tree_rss_margin_kib",
        "latest_sample_max_single_rss_kib",
        "latest_sample_tree_rss_kib",
        "latest_sample_single_rss_margin_kib",
        "latest_sample_tree_rss_margin_kib",
        "rss_guard_json_bytes",
        "rss_guard_json_mtime_utc",
        "rss_guard_json_sha256",
        "gate_size",
        "scope_status",
        "active_stage",
        "roundtrip_arm",
        "coordinator_pid",
        "codec_progress",
        "cgroup_memory_peak_bytes",
        "latest_cgroup_current_bytes",
        "cgroup_events_delta",
    ):
        if key in gate:
            row[key] = gate.get(key)
    if verdict == "rss_fail":
        row["evidence"] = (
            "terminal RSS guard failure; no scored driver result was produced for this gate"
        )
    elif verdict == "pass":
        row["evidence"] = "terminal gate pass with driver result and RSS guard evidence"
    elif verdict in {"roundtrip_fail", "determinism_fail", "guard_returncode_fail"}:
        row["evidence"] = f"terminal gate failure: {verdict}"
    elif verdict == "orphaned_running_receipt":
        row["evidence"] = (
            "persisted running receipt has no live owning job/process evidence; "
            "it is preserved as orphaned state, not an active gate"
        )
    elif verdict == "cancelled_no_result":
        row["evidence"] = (
            "operator-cancelled guard produced no driver result and receives no "
            "roundtrip, determinism, score, or runtime credit"
        )
    elif isinstance(verdict, str):
        row["evidence"] = f"gate decision is {verdict}; wait for terminal receipts"
    return row


def active_candidate_status_state(
    cert_row: dict[str, Any] | None,
    candidate: str | None,
    gate: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if candidate is None:
        return None
    row = dict(cert_row) if isinstance(cert_row, dict) else {}
    row.update(
        {
            "label": "active candidate",
            "program_id": candidate,
            "status": gate.get("verdict") if isinstance(gate, dict) else "active",
            "active_source": (
                gate.get("source", "current status receipt")
                if isinstance(gate, dict)
                else "current status receipt"
            ),
            "evidence": (
                "current process, guard, and adaptive-job evidence identify this candidate"
            ),
        }
    )
    if isinstance(gate, dict):
        if isinstance(gate.get("scope_bytes"), int):
            row["scope_bytes"] = gate["scope_bytes"]
            row.pop("scope_symbols", None)
            row.pop("scope_unit", None)
        elif isinstance(gate.get("scope_symbols"), int):
            row.pop("scope_bytes", None)
            row["scope_symbols"] = gate["scope_symbols"]
            row["scope_unit"] = gate.get("scope_unit")
    return row


def blocker_status_state(
    cert_row: dict[str, Any] | None,
    gate: dict[str, Any] | None,
    action: dict[str, Any],
) -> dict[str, Any] | None:
    """Keep the blocker row aligned with terminal gate decisions."""

    if not isinstance(cert_row, dict) and not isinstance(gate, dict):
        return None
    row = dict(cert_row) if isinstance(cert_row, dict) else {}
    row["label"] = "blocker"
    if not isinstance(gate, dict):
        return row

    verdict = gate.get("verdict")
    if verdict == "rss_fail":
        row.update(
            {
                "status": "rss_guard_exceeded_pending_record",
                "evidence": (
                    "the active gate exceeded the RSS guard before producing a scored driver result"
                ),
                "next_action": action.get("action"),
                "candidate": gate.get("candidate"),
                "scope_bytes": gate.get("scope_bytes"),
            }
        )
    elif verdict == "pass":
        row.update(
            {
                "status": "gate_pass_pending_record",
                "evidence": "the active gate passed; record it before promoting the next scope",
                "next_action": action.get("action"),
                "candidate": gate.get("candidate"),
                "scope_bytes": gate.get("scope_bytes"),
            }
        )
    elif verdict in {"roundtrip_fail", "determinism_fail", "guard_returncode_fail"}:
        row.update(
            {
                "status": f"{verdict}_pending_record",
                "evidence": "the active gate has a terminal failure that must be recorded",
                "next_action": action.get("action"),
                "candidate": gate.get("candidate"),
                "scope_bytes": gate.get("scope_bytes"),
            }
        )
    elif verdict == "orphaned_running_receipt":
        row.update(
            {
                "status": "orphaned_running_receipt",
                "evidence": (
                    "the certificate names a running gate, but no matching adaptive "
                    "job, owning process, or attributable lock evidence exists"
                ),
                "next_action": action.get("action"),
                "candidate": gate.get("candidate"),
                "scope_bytes": gate.get("scope_bytes"),
            }
        )
    elif verdict == "cancelled_no_result":
        row.update(
            {
                "status": "cancelled_no_result",
                "evidence": (
                    "the operator cancelled the gate before a driver result; "
                    "the guard is terminal and non-scoring"
                ),
                "next_action": action.get("action"),
                "candidate": gate.get("candidate"),
                "scope_bytes": gate.get("scope_bytes"),
            }
        )
    return row


def is_ppmd_cmix_candidate(candidate: str | None) -> bool:
    return isinstance(candidate, str) and candidate.startswith("cmix21_text_mmap_") and "ppmd" in candidate


def is_diagnostic_trace_candidate(candidate: str | None) -> bool:
    """Return whether a guarded codec run exists to emit a shadow trace.

    These runs are prerequisites for a separate matched replay.  A clean
    guard proves that the trace producer completed within its resource
    contract; it is not a scored compressor gate and must never inherit the
    generic next-scope promotion ladder.
    """

    return isinstance(candidate, str) and candidate.endswith("_trace")


def contingencies(candidate: str | None, scope: int | None) -> dict[str, Any] | None:
    if candidate is None or scope is None:
        return None
    next_scope = cmix21_gate_decider.next_scope(scope)
    pass_action: dict[str, Any]
    if next_scope is None:
        pass_action = {
            "action": "run official accounting audit",
            "reason": "the current gate is already full-corpus scope",
        }
    else:
        pass_action = {
            "action": "promote unchanged",
            "next_scope_bytes": next_scope,
            "command": cmix21_gate_decider.command_for_gate(candidate, next_scope),
        }
    if is_diagnostic_trace_candidate(candidate):
        pass_action = {
            "action": "run pinned matched replay and seal the trace receipt",
            "next_scope_bytes": None,
            "reason": (
                "a diagnostic trace is not a scored archive and cannot be "
                "promoted through the compression-gate scope ladder"
            ),
        }
    elif not is_ppmd_cmix_candidate(candidate):
        pass_action = {
            "action": "record pass and apply candidate target-gate promotion rule",
            "next_scope_bytes": next_scope,
            "reason": "non-cmix candidates may need archive ceilings, target-gate metadata, or candidate-specific guard labels",
        }
    return {
        "if_passes": pass_action,
        "if_rss_fails": {
            "action": (
                "record RSS failure and package lower PPMD cap"
                if is_ppmd_cmix_candidate(candidate)
                else "record RSS failure and retire or repackage this integration shape"
            ),
            "lower_memory_suggestion": (
                cmix21_gate_decider.lower_ppmd_suggestion(candidate, 128)
                if is_ppmd_cmix_candidate(candidate)
                else None
            ),
        },
        "if_roundtrip_or_determinism_fails": {
            "action": "record failure and do not promote",
            "reason": "compression evidence is not a deterministic constructive upper-bound row",
        },
    }


def operator_action(
    process_state: dict[str, Any],
    gate: dict[str, Any] | None,
) -> dict[str, Any]:
    gate = gate if isinstance(gate, dict) else {}
    verdict = gate.get("verdict")
    next_action = gate.get("next_action")

    if verdict == "orphaned_running_receipt":
        return {
            "safe_to_launch_gate": False,
            "action": "reconcile_orphaned_gate_receipt",
            "reason": (
                "persisted running state has no live owner and must be cleared or "
                "terminalized before this candidate is advanced"
            ),
            "allowed_work": [
                "inspect and repair the orphaned receipt",
                "run independent oracle and shadow experiments",
                "claim and publish independent work",
            ],
            "forbidden_work": ["report the orphaned receipt as active", "advance this candidate"],
        }
    if verdict == "pass":
        if not is_ppmd_cmix_candidate(gate.get("candidate")):
            return {
                "safe_to_launch_gate": False,
                "action": "record_pass_then_apply_candidate_promotion_rule",
                "reason": "non-cmix candidate passed; apply the candidate metadata promotion rule before launching another gate",
                "record_command": gate.get("record_command"),
            }
        return {
            "safe_to_launch_gate": False,
            "action": "record_pass_then_promote",
            "reason": "the gate passed; metadata and ledgers must be updated before the next scope launch",
            "record_command": gate.get("record_command"),
            "next_gate_command": gate.get("next_gate_command"),
        }
    if verdict == "rss_fail":
        if not is_ppmd_cmix_candidate(gate.get("candidate")):
            return {
                "safe_to_launch_gate": False,
                "action": "record_rss_failure_then_retire_or_repackage_candidate",
                "reason": "non-cmix RSS failure has no PPMD lower-memory bracket",
                "record_command": gate.get("record_rss_failure_command"),
            }
        if next_action == "launch_lower_prefix_gate":
            return {
                "safe_to_launch_gate": True,
                "action": "launch_lower_prefix_gate",
                "reason": "RSS failure is recorded and the lower memory-valve candidate is packaged",
                "next_gate_command": gate.get("lower_prefix_gate_command"),
            }
        return {
            "safe_to_launch_gate": False,
            "action": "record_rss_failure_then_package_lower_candidate",
            "reason": "RSS failure must be recorded before the next memory-valve candidate is built",
            "lower_memory_suggestion": gate.get("lower_memory_suggestion"),
        }
    if verdict in {"roundtrip_fail", "determinism_fail", "guard_returncode_fail"}:
        return {
            "safe_to_launch_gate": False,
            "action": "record_failure_and_stop_promotion",
            "reason": "a failed constructive gate cannot be promoted",
        }
    if verdict == "cancelled_no_result":
        return {
            "safe_to_launch_gate": True,
            "action": "inspect_queue_before_launch",
            "reason": (
                "the previous guard was explicitly cancelled without a scored "
                "driver result and no longer owns an active candidate run"
            ),
        }
    if (
        verdict == "incomplete"
        and gate.get("rss_guard_json_present") is False
        and gate.get("driver_result_json_present") is False
        and isinstance(gate.get("candidate"), str)
        and isinstance(gate.get("scope_bytes"), int)
    ):
        return {
            "safe_to_launch_gate": True,
            "action": "launch_active_gate",
            "reason": "the active candidate and scope have no guard or driver receipt yet",
            "next_gate_command": cmix21_gate_decider.command_for_gate(
                gate["candidate"],
                gate["scope_bytes"],
            ),
        }
    if verdict in {"incomplete", "receipt_incomplete", "running"} or next_action in {
        "wait_for_gate_receipts",
        "wait_for_rss_guard_receipt",
        "wait_for_gate_completion",
    }:
        return {
            "safe_to_launch_gate": False,
            "action": "wait_for_gate_receipts",
            "reason": "the gate state is incomplete and cannot drive a mutation yet",
        }
    return {
        "safe_to_launch_gate": True,
        "action": "inspect_queue_before_launch",
        "reason": "no terminal receipt blocks the next candidate queue decision",
    }


def add_active_decode_progress(process_state: dict[str, Any], gate: dict[str, Any] | None) -> None:
    if process_state.get("active_cmix_mode") != "decode":
        return
    gate = gate if isinstance(gate, dict) else {}
    scope = gate.get("scope_bytes")
    temp = process_state.get("active_temp_io")
    if not isinstance(scope, int) or scope <= 0 or not isinstance(temp, dict):
        return
    output_temp_bytes = temp.get("output_temp_bytes")
    if not isinstance(output_temp_bytes, int):
        output_temp_bytes = temp.get("output_bytes")
    if not isinstance(output_temp_bytes, int):
        # cmix may not materialize either decode output path until its first
        # completed write. The absence of a file means zero observed progress,
        # not an unknown decode scope.
        output_temp_bytes = 0
    capped = min(output_temp_bytes, scope)
    process_state["active_decode_progress"] = {
        "scope_bytes": scope,
        "staging_output_bytes": output_temp_bytes,
        "capped_output_bytes": capped,
        "remaining_scope_bytes": max(scope - capped, 0),
        "scope_fraction": capped / scope,
        "scope_percent": (100.0 * capped) / scope,
    }


def handoff_state(
    *,
    candidate: str | None,
    scope: int | None,
    process_state: dict[str, Any],
    gate: dict[str, Any] | None,
    action: dict[str, Any],
    proof: dict[str, Any],
) -> dict[str, Any]:
    gate = gate if isinstance(gate, dict) else {}
    terminal_verdicts = {
        "pass",
        "rss_fail",
        "roundtrip_fail",
        "determinism_fail",
        "guard_returncode_fail",
        "cancelled_no_result",
    }
    verdict = gate.get("verdict")
    terminal = verdict in terminal_verdicts
    apply_command = gate.get("apply_terminal_command")
    out: dict[str, Any] = {
        "candidate": candidate,
        "scope_bytes": scope,
        "scope_symbols": gate.get("scope_symbols"),
        "scope_unit": gate.get("scope_unit"),
        "gate_size": gate.get("gate_size"),
        "gate_verdict": verdict,
        "gate_next_action": gate.get("next_action"),
        "terminal_verdict_present": terminal,
        "active_scorer_observed": process_state.get("active_scorer_observed"),
        "gate_mutation_allowed": False,
        "recommended_action": action.get("action"),
        "has_full_corpus_constructive_result": proof.get("has_full_corpus_constructive_result", False),
        "has_10_95_constructive_upper_bound": proof.get("has_10_95_constructive_upper_bound", False),
        "claim_rule": "No prefix row proves the 10.5000000% full-corpus target.",
    }
    if isinstance(apply_command, list):
        out["apply_terminal_command"] = apply_command
        out["command_source"] = "cmix21_gate_decider.apply_terminal_command"
        out["gate_mutation_allowed"] = True
    elif isinstance(action.get("next_gate_command"), list):
        out["next_gate_command"] = action.get("next_gate_command")
        out["command_source"] = "operator_action.next_gate_command"
        out["gate_mutation_allowed"] = True
    elif isinstance(gate.get("lower_prefix_gate_command"), list):
        out["next_gate_command"] = gate.get("lower_prefix_gate_command")
        out["command_source"] = "cmix21_gate_decider.lower_prefix_gate_command"
        out["gate_mutation_allowed"] = True
    elif verdict == "cancelled_no_result":
        out["command_source"] = (
            "terminal operator cancellation; inspect queue before selecting "
            "new work"
        )
        out["gate_mutation_allowed"] = action.get("safe_to_launch_gate") is True
    elif terminal:
        out["command_source"] = "terminal verdict lacks apply command; inspect cmix21_gate_decider before acting"
    else:
        out["command_source"] = "none while gate is non-terminal"
    return out


def operator_summary_state(
    *,
    candidate: str | None,
    scope: int | None,
    proof: dict[str, Any],
    process_state: dict[str, Any],
    gate: dict[str, Any] | None,
    action: dict[str, Any],
    handoff: dict[str, Any],
) -> dict[str, Any]:
    """Flatten the nested receipt into the handoff fields operators poll first."""

    gate = gate if isinstance(gate, dict) else {}
    max_cmix = process_state.get("max_cmix_process")
    max_sampled_single_rss_kib = gate.get("max_sampled_single_rss_kib")
    max_sampled_tree_rss_kib = gate.get("max_sampled_tree_rss_kib")
    latest_sample_single_rss_kib = gate.get("latest_sample_max_single_rss_kib")
    latest_sample_tree_rss_kib = gate.get("latest_sample_tree_rss_kib")
    summary: dict[str, Any] = {
        "candidate": candidate,
        "scope_bytes": scope,
        "scope_symbols": gate.get("scope_symbols"),
        "scope_unit": gate.get("scope_unit"),
        "gate_size": gate.get("gate_size"),
        "gate_verdict": gate.get("verdict"),
        "gate_next_action": gate.get("next_action"),
        "active_stage": gate.get("active_stage"),
        "roundtrip_arm": gate.get("roundtrip_arm"),
        "codec_progress": gate.get("codec_progress"),
        "active_scorer_observed": process_state.get("active_scorer_observed"),
        "active_cmix_mode": process_state.get("active_cmix_mode"),
        "driver_result_present": gate.get("driver_result_json_present"),
        "driver_result_json": gate.get("driver_result_json"),
        "rss_guard_present": gate.get("rss_guard_json_present"),
        "rss_guard_status": gate.get("rss_guard_status"),
        "rss_guard_json": gate.get("rss_guard_json"),
        "rss_guard_json_sha256": gate.get("rss_guard_json_sha256"),
        "rss_samples": gate.get("sample_count"),
        "binary_10gib_guard_kib": LOCAL_RSS_GUARD_KIB,
        "decimal_10gb_guard_kib": DECIMAL_10GB_GUARD_KIB,
        "max_sampled_single_rss_kib": max_sampled_single_rss_kib,
        "latest_sample_single_rss_kib": latest_sample_single_rss_kib,
        "max_sampled_single_decimal_10gb_margin_kib": None,
        "max_sampled_single_decimal_10gb_safe": None,
        "max_sampled_tree_decimal_10gb_margin_kib": None,
        "max_sampled_tree_decimal_10gb_safe": None,
        "latest_sample_single_decimal_10gb_margin_kib": None,
        "latest_sample_single_decimal_10gb_safe": None,
        "latest_sample_tree_decimal_10gb_margin_kib": None,
        "latest_sample_tree_decimal_10gb_safe": None,
        "single_rss_margin_kib": gate.get("single_rss_margin_kib"),
        "latest_sample_single_rss_margin_kib": gate.get("latest_sample_single_rss_margin_kib"),
        "active_process_tree_rss_kib": process_state.get("active_tree_rss_kib"),
        "active_process_tree_margin_kib": process_state.get("active_tree_margin_kib"),
        "active_process_tree_decimal_10gb_margin_kib": process_state.get("active_tree_decimal_10gb_margin_kib"),
        "operator_action": action.get("action"),
        "safe_to_launch_gate": action.get("safe_to_launch_gate"),
        "terminal_verdict_present": handoff.get("terminal_verdict_present"),
        "gate_mutation_allowed": handoff.get("gate_mutation_allowed"),
        "command_source": handoff.get("command_source"),
        "has_full_corpus_constructive_result": proof.get("has_full_corpus_constructive_result", False),
        "has_10_95_constructive_upper_bound": proof.get("has_10_95_constructive_upper_bound", False),
        "claim_rule": "No prefix row proves the 10.5000000% full-corpus target.",
    }
    if isinstance(max_sampled_single_rss_kib, int):
        summary["max_sampled_single_decimal_10gb_margin_kib"] = DECIMAL_10GB_GUARD_KIB - max_sampled_single_rss_kib
        summary["max_sampled_single_decimal_10gb_safe"] = max_sampled_single_rss_kib <= DECIMAL_10GB_GUARD_KIB
    if isinstance(max_sampled_tree_rss_kib, int):
        summary["max_sampled_tree_decimal_10gb_margin_kib"] = DECIMAL_10GB_GUARD_KIB - max_sampled_tree_rss_kib
        summary["max_sampled_tree_decimal_10gb_safe"] = max_sampled_tree_rss_kib <= DECIMAL_10GB_GUARD_KIB
    if isinstance(latest_sample_single_rss_kib, int):
        summary["latest_sample_single_decimal_10gb_margin_kib"] = DECIMAL_10GB_GUARD_KIB - latest_sample_single_rss_kib
        summary["latest_sample_single_decimal_10gb_safe"] = latest_sample_single_rss_kib <= DECIMAL_10GB_GUARD_KIB
    if isinstance(latest_sample_tree_rss_kib, int):
        summary["latest_sample_tree_decimal_10gb_margin_kib"] = DECIMAL_10GB_GUARD_KIB - latest_sample_tree_rss_kib
        summary["latest_sample_tree_decimal_10gb_safe"] = latest_sample_tree_rss_kib <= DECIMAL_10GB_GUARD_KIB
    if isinstance(max_cmix, dict):
        summary["active_cmix_pid"] = max_cmix.get("pid")
        summary["active_cmix_rss_kib"] = max_cmix.get("rss_kib")
        summary["active_cmix_single_process_margin_kib"] = process_state.get("single_process_margin_kib")
        summary["active_cmix_decimal_10gb_margin_kib"] = process_state.get("single_process_decimal_10gb_margin_kib")
    if isinstance(handoff.get("apply_terminal_command"), list):
        summary["apply_terminal_command"] = handoff.get("apply_terminal_command")
    if isinstance(handoff.get("next_gate_command"), list):
        summary["next_gate_command"] = handoff.get("next_gate_command")
    return summary


def receipt() -> dict[str, Any]:
    objective = research_contracts.objective_binding()
    release_receipts = release_receipt_state(objective)
    cert = load_json(CERT_PATH)
    labels = top_status_by_label(cert)
    proof = cert.get("proof_status", {}) if isinstance(cert.get("proof_status"), dict) else {}
    target = cert.get("target", {}) if isinstance(cert.get("target"), dict) else {}
    if target.get("target_score_10_95") != objective["targetScoreBytes"]:
        raise ValueError("upper-bound certificate target differs from objective contract")
    if target.get("input_size") != objective["corpusBytes"]:
        raise ValueError("upper-bound certificate corpus scope differs from objective contract")
    if cert.get("objective") != objective:
        raise ValueError("upper-bound certificate objective binding is missing or stale")
    process_state = active_process_state()
    adaptive_state = adaptive_running_jobs_state()
    candidate, scope = active_candidate_from_cert(cert)
    live_q1_gate = live_q1_full_gate_from_process(process_state, adaptive_state)
    live_speedlab_gate = (
        None if live_q1_gate is not None else live_speedlab_gate_from_process(process_state)
    )
    if live_q1_gate is not None:
        candidate = live_q1_gate.get("candidate")
        scope = live_q1_gate.get("gate_size")
        if not isinstance(scope, int):
            scope = live_q1_gate.get("scope_bytes")
        gate = live_q1_gate
    elif live_speedlab_gate is not None:
        owning_job = adaptive_job_owning_guard(
            live_speedlab_gate,
            process_state,
            adaptive_state,
        )
        if owning_job is not None:
            live_speedlab_gate = bind_guard_to_adaptive_job(
                live_speedlab_gate,
                owning_job,
            )
        candidate = live_speedlab_gate.get("candidate")
        scope = live_speedlab_gate.get("gate_size")
        if not isinstance(scope, int):
            scope = live_speedlab_gate.get("scope_bytes")
        gate = live_speedlab_gate
    else:
        gate = None
        process_candidate, process_scope = active_candidate_from_process(process_state)
        if process_candidate is not None:
            candidate = process_candidate
            if process_scope is not None:
                scope = process_scope
        else:
            running_jobs = adaptive_state.get("running_jobs")
            live_jobs = (
                [
                    row
                    for row in running_jobs
                    if isinstance(row, dict) and row.get("worker_pid_live") is True
                ]
                if isinstance(running_jobs, list)
                else []
            )
            if live_jobs:
                live_job = live_jobs[0]
                candidate = live_job.get("candidate_id")
                scope = live_job.get("gate_size")
                gate = bind_guard_to_adaptive_job(
                    {
                        "candidate": candidate,
                        "verdict": "running",
                        "next_action": "wait_for_gate_completion",
                        "source": "live_adaptive_job",
                        "driver_result_json_present": False,
                    },
                    live_job,
                )
            else:
                candidate = None
                scope = None
        if gate is None:
            gate = gate_state(candidate, scope)
    liveness = gate_liveness_state(
        candidate,
        scope,
        gate,
        process_state,
        adaptive_state,
    )
    gate = reconcile_gate_liveness(gate, liveness)
    orphaned = gate is not None and gate.get("verdict") == "orphaned_running_receipt"
    live_candidate = None if orphaned else candidate
    live_scope = (
        gate.get("scope_bytes")
        if not orphaned and isinstance(gate, dict)
        else None
    )
    add_active_decode_progress(process_state, gate)
    action = operator_action(process_state, gate)
    handoff = handoff_state(
        candidate=live_candidate,
        scope=live_scope,
        process_state=process_state,
        gate=gate,
        action=action,
        proof=proof,
    )
    operator_summary = operator_summary_state(
        candidate=live_candidate,
        scope=live_scope,
        proof=proof,
        process_state=process_state,
        gate=gate,
        action=action,
        handoff=handoff,
    )
    operator_summary["pending_adaptive_jobs"] = adaptive_state.get(
        "pending_job_count", 0
    )
    operator_summary["held_pending_adaptive_jobs"] = adaptive_state.get(
        "held_pending_job_count", 0
    )
    operator_summary["claimable_pending_adaptive_jobs"] = adaptive_state.get(
        "claimable_pending_job_count", 0
    )
    release_summary = release_receipts["summary"]
    operator_summary["release_bundles"] = release_summary["bundles"]
    operator_summary["release_run_receipts"] = release_summary["runReceipts"]
    operator_summary["release_failed_attempts"] = release_summary["failedAttempts"]
    operator_summary["objective_achieved_receipts"] = release_summary[
        "objectiveAchievedReceipts"
    ]
    certificate_active_gate = labels.get("active gate")
    certificate_blocker = labels.get("blocker")
    return {
        "receipt_type": "operator_status",
        "project": "enwiki9",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "objective": objective,
        "operator_summary": operator_summary,
        "release_receipts": release_receipts,
        "target_score_10_95": objective["targetScoreBytes"],
        "has_full_corpus_constructive_result": proof.get("has_full_corpus_constructive_result", False),
        "has_10_95_constructive_upper_bound": proof.get("has_10_95_constructive_upper_bound", False),
        "best_exact_10m": labels.get("best exact 10M"),
        "best_exact_10m_archive": labels.get("best exact 10M archive"),
        "best_exact_100m": labels.get("best exact 100M"),
        "best_full_1g": labels.get("best full 1G"),
        "best_forecast": labels.get("best forecast"),
        "active_candidate": active_candidate_status_state(
            labels.get("active candidate"), live_candidate, gate
        ),
        "certificate_active_candidate": labels.get("active candidate"),
        "active_gate": (
            active_gate_status_state(certificate_active_gate, gate)
            if not orphaned and live_candidate is not None
            else None
        ),
        "orphaned_gate": (
            active_gate_status_state(certificate_active_gate, gate) if orphaned else None
        ),
        "certificate_active_gate": certificate_active_gate,
        "next_gate": (
            (labels.get("next gate") or certificate_active_gate)
            if not orphaned and live_candidate is not None
            else None
        ),
        "blocker": blocker_status_state(certificate_blocker, gate, action),
        "certificate_blocker": certificate_blocker,
        "operator_logs": operator_logs_state(),
        "candidate_audit": candidate_audit_summary_state(),
        "active_candidate_recent_artifacts": active_candidate_recent_artifacts(live_candidate),
        "adaptive_jobs": adaptive_state,
        "active_processes": process_state,
        "observed_gate_command": observed_gate_command_state(
            candidate,
            gate.get("scope_bytes") if isinstance(gate, dict) else scope,
            process_state,
        ),
        "observed_controller_command": observed_controller_command_state(
            candidate,
            gate.get("scope_bytes") if isinstance(gate, dict) else scope,
            process_state,
        ),
        "gate_decision": gate,
        "gate_liveness": liveness,
        "gate_evidence_status": gate_evidence_status(gate, liveness),
        "operator_action": action,
        "handoff": handoff,
        "contingencies": contingencies(live_candidate, live_scope),
    }


def fmt_bool(value: Any) -> str:
    return "true" if value is True else "false" if value is False else "unknown"


def fmt_int(value: Any) -> str:
    return f"{value:,}" if isinstance(value, int) else "n/a"


def fmt_float(value: Any, digits: int = 6) -> str:
    return f"{value:.{digits}f}" if isinstance(value, float) else "n/a"


def fmt_list(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "n/a"
    return "; ".join(str(item) for item in value)


def fmt_command(value: Any, limit: int = 150) -> str:
    text = str(value) if value is not None else ""
    return text if len(text) <= limit else text[: max(limit - 3, 0)] + "..."


def process_role(args: Any) -> str:
    text = str(args)
    if "cmix21_gate_decider.py" in text:
        return "gate_decider"
    if "cmix_filebacked_fxcm_full_roundtrip.py" in text:
        return "q1_full_roundtrip"
    if "run_with_resource_guard_v3_soft_high.py" in text:
        return "resource_guard_soft_high"
    if "run_with_resource_guard_v3.py" in text:
        return "resource_guard"
    if "cmix_filebacked_fxcm_full_stage.py" in text:
        return "q1_full_stage"
    if "run_with_rss_guard.py" in text:
        return "rss_guard"
    if "projects/enwiki9/lib/driver.py" in text:
        return "driver"
    if "cmix21-mmap-bin" in text:
        return "native_cmix"
    if "fx2_public_repro_queue.py" in text:
        return "fx2_package"
    if "fx2-public-package-" in text and "cmix_orig" in text:
        return "native_fx2"
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = []
    if parts:
        executable = pathlib.Path(parts[0]).name
        if executable in {"cmix", "cmix.bin", "cmix_orig"}:
            return "native_cmix"
    if "streaming_retrieval_shadow.py" in text:
        return "target_trace_shadow"
    if "streaming_retrieval_raw_shadow.py" in text:
        return "raw_shadow"
    if "article_order_teacher_distill.py" in text:
        return "order_teacher"
    if "page_order_gepa.py" in text:
        return "order_proxy"
    return "process"


def render_md(data: dict[str, Any]) -> str:
    proc_state = data.get("active_processes", {})
    max_cmix = proc_state.get("max_cmix_process") if isinstance(proc_state, dict) else None
    active_rows = proc_state.get("active_rows") if isinstance(proc_state, dict) else None
    gate = data.get("gate_decision") if isinstance(data.get("gate_decision"), dict) else {}
    summary = data.get("operator_summary") if isinstance(data.get("operator_summary"), dict) else {}
    lines = [
        "# enwiki9 Status Receipt",
        "",
        "Generated from the current certificate, gate receipts, resource guards, and process table.",
        "",
        f"- Generated at UTC: `{data.get('generated_at_utc', 'unknown')}`",
        "",
        "## Target State",
        "",
        f"- Objective ID: `{data.get('objective', {}).get('objectiveId', 'unknown')}`",
        f"- Objective digest: `{data.get('objective', {}).get('objectiveDigest', 'unknown')}`",
        f"- Objective path: `{data.get('objective', {}).get('objectivePath', 'unknown')}`",
        f"- `10.5000000%` target score: `{fmt_int(data.get('target_score_10_95'))}`",
        f"- Full-corpus constructive result present: `{fmt_bool(data.get('has_full_corpus_constructive_result'))}`",
        f"- `10.5000000%` constructive upper bound present: `{fmt_bool(data.get('has_10_95_constructive_upper_bound'))}`",
        "",
        "## Operator Summary",
        "",
        f"- Candidate: `{summary.get('candidate', 'unknown')}`",
        f"- Scope bytes: `{fmt_int(summary.get('scope_bytes'))}`",
        f"- Scope symbols: `{fmt_int(summary.get('scope_symbols'))}`",
        f"- Scope unit: `{summary.get('scope_unit') or 'n/a'}`",
        f"- Gate verdict: `{summary.get('gate_verdict', 'unknown')}`",
        f"- Gate next action: `{summary.get('gate_next_action', 'unknown')}`",
        f"- Active stage: `{summary.get('active_stage') or 'n/a'}`",
        f"- Roundtrip arm: `{summary.get('roundtrip_arm') or 'n/a'}`",
        f"- Active scorer observed: `{fmt_bool(summary.get('active_scorer_observed'))}`",
        f"- Active cmix mode: `{summary.get('active_cmix_mode') or 'n/a'}`",
        f"- Driver result present: `{fmt_bool(summary.get('driver_result_present'))}`",
        f"- RSS guard status: `{summary.get('rss_guard_status') or 'n/a'}`",
        f"- RSS samples: `{fmt_int(summary.get('rss_samples'))}`",
        f"- Binary `10GiB` guard KiB: `{fmt_int(summary.get('binary_10gib_guard_kib'))}`",
        f"- Decimal `10GB` guard KiB: `{fmt_int(summary.get('decimal_10gb_guard_kib'))}`",
        f"- Max sampled single RSS KiB: `{fmt_int(summary.get('max_sampled_single_rss_kib'))}`",
        f"- Latest sampled single RSS KiB: `{fmt_int(summary.get('latest_sample_single_rss_kib'))}`",
        f"- Tightest binary single-process margin KiB: `{fmt_int(summary.get('single_rss_margin_kib'))}`",
        f"- Tightest decimal single-process margin KiB: `{fmt_int(summary.get('max_sampled_single_decimal_10gb_margin_kib'))}`",
        f"- Latest binary single-process margin KiB: `{fmt_int(summary.get('latest_sample_single_rss_margin_kib'))}`",
        f"- Latest decimal single-process margin KiB: `{fmt_int(summary.get('latest_sample_single_decimal_10gb_margin_kib'))}`",
        f"- Safe to launch candidate gate: `{fmt_bool(summary.get('safe_to_launch_gate'))}`",
        f"- Terminal verdict present: `{fmt_bool(summary.get('terminal_verdict_present'))}`",
        f"- Pending adaptive jobs: `{fmt_int(summary.get('pending_adaptive_jobs'))}`",
        f"- Held pending adaptive jobs: `{fmt_int(summary.get('held_pending_adaptive_jobs'))}`",
        f"- Claimable pending adaptive jobs: `{fmt_int(summary.get('claimable_pending_adaptive_jobs'))}`",
        f"- Canonical release bundles: `{fmt_int(summary.get('release_bundles'))}`",
        f"- Validated release run receipts: `{fmt_int(summary.get('release_run_receipts'))}`",
        f"- Validated failed release attempts: `{fmt_int(summary.get('release_failed_attempts'))}`",
        f"- Objective-achieved receipts: `{fmt_int(summary.get('objective_achieved_receipts'))}`",
        f"- Release index mode: `{data.get('release_receipts', {}).get('validation_mode', 'unknown')}`",
        f"- Command source: `{summary.get('command_source', 'unknown')}`",
        f"- Claim rule: `{summary.get('claim_rule', 'unknown')}`",
        "",
        (
            "## Orphaned Gate Reconciliation"
            if gate.get("verdict") == "orphaned_running_receipt"
            else "## Active Gate"
        ),
        "",
        f"- Gate verdict: `{gate.get('verdict', 'unknown')}`",
        f"- Next action: `{gate.get('next_action', 'unknown')}`",
        f"- Candidate: `{gate.get('candidate', 'unknown')}`",
        f"- Scope bytes: `{fmt_int(gate.get('scope_bytes'))}`",
        f"- Scope symbols: `{fmt_int(gate.get('scope_symbols'))}`",
        f"- Scope unit: `{gate.get('scope_unit') or 'n/a'}`",
        f"- Active stage: `{gate.get('active_stage') or 'n/a'}`",
        f"- Roundtrip arm: `{gate.get('roundtrip_arm') or 'n/a'}`",
        f"- Coordinator PID: `{fmt_int(gate.get('coordinator_pid'))}`",
        f"- Driver result JSON: `{gate.get('driver_result_json') or 'not present'}`",
        f"- Driver result present: `{fmt_bool(gate.get('driver_result_json_present'))}`",
        f"- RSS guard JSON: `{gate.get('rss_guard_json') or 'not present'}`",
        f"- RSS guard present: `{fmt_bool(gate.get('rss_guard_json_present'))}`",
        f"- Active scorer observed: `{fmt_bool(proc_state.get('active_scorer_observed'))}`",
    ]
    codec_progress = (
        gate.get("codec_progress")
        if isinstance(gate.get("codec_progress"), dict)
        else {}
    )
    if codec_progress:
        lines.extend(
            [
                f"- Codec progress: `{fmt_float(codec_progress.get('reported_scope_percent'), 2)}%`",
                f"- Reported payload bytes: `{fmt_int(codec_progress.get('reported_payload_bytes'))}`",
                f"- Progress log: `{codec_progress.get('path') or 'n/a'}`",
                f"- Progress log modified UTC: `{codec_progress.get('mtime_utc') or 'n/a'}`",
            ]
        )
    liveness = data.get("gate_liveness") if isinstance(data.get("gate_liveness"), dict) else {}
    if liveness:
        lines.extend(
            [
                f"- Live gate: `{fmt_bool(liveness.get('is_live'))}`",
                f"- Liveness classification: `{liveness.get('classification', 'unknown')}`",
                f"- Matching adaptive jobs: `{fmt_int(liveness.get('matching_adaptive_job_count'))}`",
                f"- Matching controllers: `{fmt_int(liveness.get('matching_controller_count'))}`",
                f"- Matching driver observed: `{fmt_bool(liveness.get('matching_driver_observed'))}`",
                f"- Liveness claim rule: `{liveness.get('claim_rule', 'unknown')}`",
            ]
        )
    if gate.get("rss_guard_json_present") is True:
        lines.extend(
            [
                f"- RSS guard status: `{gate.get('rss_guard_status', 'unknown')}`",
                f"- RSS guard JSON bytes: `{fmt_int(gate.get('rss_guard_json_bytes'))}`",
                f"- RSS guard JSON modified UTC: `{gate.get('rss_guard_json_mtime_utc') or 'n/a'}`",
                f"- RSS guard JSON SHA-256: `{gate.get('rss_guard_json_sha256') or 'n/a'}`",
                f"- RSS samples: `{fmt_int(gate.get('sample_count'))}`",
                f"- Max sampled single RSS KiB: `{fmt_int(gate.get('max_sampled_single_rss_kib'))}`",
                f"- Max sampled tree RSS KiB: `{fmt_int(gate.get('max_sampled_tree_rss_kib'))}`",
                f"- Single-process RSS margin KiB: `{fmt_int(gate.get('single_rss_margin_kib'))}`",
                f"- Single-process decimal `10GB` margin KiB: `{fmt_int(summary.get('max_sampled_single_decimal_10gb_margin_kib'))}`",
                f"- Tree RSS margin KiB: `{fmt_int(gate.get('tree_rss_margin_kib'))}`",
                f"- Tree decimal `10GB` margin KiB: `{fmt_int(summary.get('max_sampled_tree_decimal_10gb_margin_kib'))}`",
                f"- Latest sampled single RSS KiB: `{fmt_int(gate.get('latest_sample_max_single_rss_kib'))}`",
                f"- Latest sampled tree RSS KiB: `{fmt_int(gate.get('latest_sample_tree_rss_kib'))}`",
                f"- Latest sampled single-process margin KiB: `{fmt_int(gate.get('latest_sample_single_rss_margin_kib'))}`",
                f"- Latest sampled single-process decimal `10GB` margin KiB: `{fmt_int(summary.get('latest_sample_single_decimal_10gb_margin_kib'))}`",
                f"- Latest sampled tree margin KiB: `{fmt_int(gate.get('latest_sample_tree_rss_margin_kib'))}`",
                f"- Latest sampled tree decimal `10GB` margin KiB: `{fmt_int(summary.get('latest_sample_tree_decimal_10gb_margin_kib'))}`",
                f"- Cgroup memory peak bytes: `{fmt_int(gate.get('cgroup_memory_peak_bytes'))}`",
                f"- Latest cgroup current bytes: `{fmt_int(gate.get('latest_cgroup_current_bytes'))}`",
                f"- Cgroup event deltas: `{gate.get('cgroup_events_delta') or 'n/a'}`",
            ]
        )
    if (
        gate.get("rss_guard_json_present") is False
        and proc_state.get("active_scorer_observed") is True
    ):
        lines.append(
            "- Live guard note: `guard JSON is absent while the scorer is observed; "
            "keep waiting for final receipts and use process-table RSS meanwhile`"
        )
    if isinstance(gate.get("compressed_size"), int):
        lines.extend(
            [
                "",
                "## Gate Result Diagnostics",
                "",
                f"- Archive bytes: `{fmt_int(gate.get('compressed_size'))}`",
                f"- Program bytes: `{fmt_int(gate.get('program_size'))}`",
                f"- Local score: `{fmt_int(gate.get('local_score'))}`",
                f"- Archive b/B: `{fmt_float(gate.get('archive_bpb'), 7)}`",
                f"- Required full archive bytes for the `10.5000000%` target: `{fmt_int(gate.get('required_full_archive_bytes_for_10_95'))}`",
                f"- Linear archive projection score: `{fmt_int(gate.get('linear_archive_projection_score'))}`",
                "- Diagnostic note: `linear projection is not a proof; use it only to compare slope pressure`",
            ]
        )
    if isinstance(gate.get("apply_terminal_command"), list):
        lines.extend(
            [
                "",
                "## Terminal Gate Command",
                "",
                "```bash",
                " ".join(str(part) for part in gate["apply_terminal_command"]),
                "```",
            ]
        )
    evidence_status = data.get("gate_evidence_status") if isinstance(data.get("gate_evidence_status"), dict) else {}
    if evidence_status:
        lines.extend(
            [
                "",
                "## Gate Evidence Status",
                "",
                f"- Claim status: `{evidence_status.get('claim_status', 'unknown')}`",
                f"- Driver result terminal: `{fmt_bool(evidence_status.get('driver_result_terminal'))}`",
                f"- RSS guard terminal: `{fmt_bool(evidence_status.get('rss_guard_terminal'))}`",
                f"- Scored gate result present: `{fmt_bool(evidence_status.get('scored_gate_result_present'))}`",
                f"- Live guard only: `{fmt_bool(evidence_status.get('live_guard_only'))}`",
                f"- Claim rule: `{evidence_status.get('claim_rule', 'unknown')}`",
            ]
        )
    observed_gate = data.get("observed_gate_command") if isinstance(data.get("observed_gate_command"), dict) else {}
    if observed_gate:
        lines.extend(
            [
                "",
                "## Observed Gate Command",
                "",
                f"- Expected candidate: `{observed_gate.get('expected_candidate', 'unknown')}`",
                f"- Expected scope bytes: `{fmt_int(observed_gate.get('expected_scope_bytes'))}`",
                f"- Driver process count: `{fmt_int(observed_gate.get('driver_process_count'))}`",
                f"- Active gate command observed: `{fmt_bool(observed_gate.get('active_gate_command_observed'))}`",
                f"- Driver command mismatch count: `{fmt_int(observed_gate.get('mismatch_count'))}`",
                "",
                "| Role | PID | Candidate Match | Scope Bytes | Scope Match | Command Contract | Determinism Flag | Proof Schedule |",
                "|---|---:|---|---:|---|---|---|---|",
            ]
        )
        driver_processes = observed_gate.get("driver_processes")
        if isinstance(driver_processes, list) and driver_processes:
            for row in driver_processes:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    f"| `{row.get('role') or 'unknown'}` | "
                    f"{fmt_int(row.get('pid'))} | "
                    f"`{fmt_bool(row.get('candidate_matches'))}` | "
                    f"{fmt_int(row.get('scope_bytes'))} | "
                    f"`{fmt_bool(row.get('scope_matches'))}` | "
                    f"`{fmt_bool(row.get('command_contract_matches'))}` | "
                    f"`{fmt_bool(row.get('check_determinism'))}` | "
                    f"`{row.get('proof_schedule') or 'unknown'}` |"
                )
        else:
            lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    observed_controller = (
        data.get("observed_controller_command")
        if isinstance(data.get("observed_controller_command"), dict)
        else {}
    )
    if observed_controller:
        lines.extend(
            [
                "",
                "## Observed Controller Command",
                "",
                f"- Expected active candidate: `{observed_controller.get('expected_active_candidate', 'unknown')}`",
                f"- Expected active scope bytes: `{fmt_int(observed_controller.get('expected_active_scope_bytes'))}`",
                f"- Controller process count: `{fmt_int(observed_controller.get('controller_process_count'))}`",
                f"- Scope note: `{observed_controller.get('scope_note', 'unknown')}`",
                "",
                "| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |",
                "|---:|---|---:|---|---|---|---|",
            ]
        )
        controller_processes = observed_controller.get("controller_processes")
        if isinstance(controller_processes, list) and controller_processes:
            for row in controller_processes:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    f"| {fmt_int(row.get('pid'))} | "
                    f"`{fmt_bool(row.get('candidate_matches_active'))}` | "
                    f"{fmt_int(row.get('scope_bytes'))} | "
                    f"`{fmt_bool(row.get('scope_matches_active_gate'))}` | "
                    f"`{fmt_bool(row.get('apply_terminal'))}` | "
                    f"`{fmt_bool(row.get('launch_next'))}` | "
                    f"`{fmt_bool(row.get('package_lower'))}` |"
                )
        else:
            lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    action = data.get("operator_action") if isinstance(data.get("operator_action"), dict) else {}
    if action:
        lines.extend(
            [
                "",
                "## Operator Action",
                "",
                f"- Safe to launch candidate gate: `{fmt_bool(action.get('safe_to_launch_gate'))}`",
                f"- Action: `{action.get('action', 'unknown')}`",
                f"- Reason: `{action.get('reason', 'unknown')}`",
                f"- Allowed work: `{fmt_list(action.get('allowed_work'))}`",
                f"- Forbidden work: `{fmt_list(action.get('forbidden_work'))}`",
            ]
        )
    handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
    if handoff:
        lines.extend(
            [
                "",
                "## Handoff",
                "",
                f"- Terminal verdict present: `{fmt_bool(handoff.get('terminal_verdict_present'))}`",
                f"- Gate mutation allowed: `{fmt_bool(handoff.get('gate_mutation_allowed'))}`",
                f"- Recommended action: `{handoff.get('recommended_action', 'unknown')}`",
                f"- Command source: `{handoff.get('command_source', 'unknown')}`",
                f"- Claim rule: `{handoff.get('claim_rule', 'unknown')}`",
            ]
        )
        if isinstance(handoff.get("apply_terminal_command"), list):
            lines.extend(
                [
                    "- Apply terminal command:",
                    "```bash",
                    " ".join(str(part) for part in handoff["apply_terminal_command"]),
                    "```",
                ]
            )
        if isinstance(handoff.get("next_gate_command"), list):
            lines.extend(
                [
                    "- Next gate command:",
                    "```bash",
                    " ".join(str(part) for part in handoff["next_gate_command"]),
                    "```",
                ]
            )
    operator_logs = data.get("operator_logs") if isinstance(data.get("operator_logs"), dict) else {}
    if operator_logs:
        lines.extend(
            [
                "",
                "## Operator Logs",
                "",
                f"- Latest delayed status log: `{operator_logs.get('latest_delayed_status_log', 'n/a')}`",
                f"- Latest delayed status log present: `{fmt_bool(operator_logs.get('latest_delayed_status_log_present'))}`",
            ]
        )
        if operator_logs.get("latest_delayed_status_log_resolved"):
            lines.append(
                f"- Latest delayed status resolved log: `{operator_logs.get('latest_delayed_status_log_resolved')}`"
            )
    candidate_audit = data.get("candidate_audit") if isinstance(data.get("candidate_audit"), dict) else {}
    summary = candidate_audit.get("summary") if isinstance(candidate_audit.get("summary"), dict) else {}
    if candidate_audit:
        lines.extend(
            [
                "",
                "## Candidate Audit",
                "",
                f"- Audit return code: `{fmt_int(candidate_audit.get('returncode'))}`",
            ]
        )
        if summary:
            status_counts = summary.get("candidate_status_counts")
            lines.extend(
                [
                    f"- Program directories: `{fmt_int(summary.get('program_directories'))}`",
                    f"- Registered programs: `{fmt_int(summary.get('registered_programs'))}`",
                    f"- Untracked nonignored entries: `{fmt_int(summary.get('untracked_nonignored_entries'))}`",
                    f"- Modified tracked entries: `{fmt_int(summary.get('modified_tracked_entries'))}`",
                ]
            )
            if isinstance(status_counts, dict):
                status_summary = ", ".join(
                    f"{key}={value}" for key, value in sorted(status_counts.items())
                )
                lines.append(f"- Candidate statuses: `{status_summary}`")
        elif candidate_audit.get("error"):
            lines.append(f"- Audit error: `{candidate_audit.get('error')}`")
    active_rows = proc_state.get("active_rows") if isinstance(proc_state, dict) else None
    if isinstance(active_rows, list):
        lines.extend(
            [
                "",
                "## Active Runner Process Table",
                "",
                "| Role | PID | PPID | RSS KiB | Command |",
                "|---|---:|---:|---:|---|",
            ]
        )
        if active_rows:
            for row in active_rows:
                if not isinstance(row, dict):
                    continue
                args = row.get("args")
                lines.append(
                    f"| `{process_role(args)}` | "
                    f"{fmt_int(row.get('pid'))} | "
                    f"{fmt_int(row.get('ppid'))} | "
                    f"{fmt_int(row.get('rss_kib'))} | "
                    f"`{fmt_command(args)}` |"
                )
        else:
            lines.append("| n/a | n/a | n/a | n/a | n/a |")
    controller_rows = proc_state.get("controller_rows") if isinstance(proc_state, dict) else None
    if isinstance(controller_rows, list) and controller_rows:
        lines.extend(
            [
                "",
                "## Active Controller Process Table",
                "",
                "| Role | PID | PPID | RSS KiB | Command |",
                "|---|---:|---:|---:|---|",
            ]
        )
        for row in controller_rows:
            if not isinstance(row, dict):
                continue
            args = row.get("args")
            lines.append(
                f"| `{process_role(args)}` | "
                f"{fmt_int(row.get('pid'))} | "
                f"{fmt_int(row.get('ppid'))} | "
                f"{fmt_int(row.get('rss_kib'))} | "
                f"`{fmt_command(args)}` |"
            )
    artifacts = data.get("active_candidate_recent_artifacts")
    if isinstance(artifacts, list):
        lines.extend(
            [
                "",
                "## Active Candidate Recent Artifacts",
                "",
                "| Path | Bytes | Modified UTC |",
                "|---|---:|---|",
            ]
        )
        if artifacts:
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    continue
                lines.append(
                    f"| `{artifact.get('path', 'unknown')}` | "
                    f"{fmt_int(artifact.get('bytes'))} | "
                    f"`{artifact.get('mtime_utc', 'unknown')}` |"
                )
        else:
            lines.append("| n/a | n/a | n/a |")
    if max_cmix:
        temp = proc_state.get("active_temp_io", {}) if isinstance(proc_state.get("active_temp_io"), dict) else {}
        proc_io = proc_state.get("active_proc_io", {}) if isinstance(proc_state.get("active_proc_io"), dict) else {}
        progress = (
            proc_state.get("active_decode_progress")
            if isinstance(proc_state.get("active_decode_progress"), dict)
            else {}
        )
        lines.extend(
            [
                "",
                "## Active RSS",
                "",
                f"- Max cmix PID: `{max_cmix.get('pid')}`",
                f"- Active cmix mode: `{proc_state.get('active_cmix_mode', 'unknown')}`",
                f"- Max cmix RSS KiB: `{fmt_int(max_cmix.get('rss_kib'))}`",
                f"- Active process tree RSS KiB: `{fmt_int(proc_state.get('active_tree_rss_kib'))}`",
                f"- Local binary `10GiB` guard KiB: `{fmt_int(proc_state.get('rss_guard_kib'))}`",
                f"- Decimal `10GB` guard KiB: `{fmt_int(proc_state.get('decimal_10gb_guard_kib'))}`",
                f"- Single-process binary margin KiB: `{fmt_int(proc_state.get('single_process_margin_kib'))}`",
                f"- Single-process decimal margin KiB: `{fmt_int(proc_state.get('single_process_decimal_10gb_margin_kib'))}`",
                f"- Active process tree margin KiB (binary): `{fmt_int(proc_state.get('active_tree_margin_kib'))}`",
                f"- Active process tree decimal margin KiB: `{fmt_int(proc_state.get('active_tree_decimal_10gb_margin_kib'))}`",
                f"- Temp input path: `{temp.get('input_path', 'unknown')}`",
                f"- Temp output path: `{temp.get('output_path', 'unknown')}`",
                f"- Temp output staging path: `{temp.get('output_temp_path', 'unknown')}`",
                f"- Temp input bytes: `{fmt_int(temp.get('input_bytes'))}`",
                f"- Temp output bytes: `{fmt_int(temp.get('output_bytes'))}`",
                f"- Temp output staging bytes: `{fmt_int(temp.get('output_temp_bytes'))}`",
                f"- Temp input modified UTC: `{temp.get('input_mtime_utc') or 'n/a'}`",
                f"- Temp output modified UTC: `{temp.get('output_mtime_utc') or 'n/a'}`",
                f"- Temp output staging modified UTC: `{temp.get('output_temp_mtime_utc') or 'n/a'}`",
                f"- Process read bytes: `{fmt_int(proc_io.get('read_bytes'))}`",
                f"- Process write bytes: `{fmt_int(proc_io.get('write_bytes'))}`",
            ]
        )
        if progress:
            lines.extend(
                [
                    f"- Decode scope progress: `{fmt_int(progress.get('capped_output_bytes'))}` / `{fmt_int(progress.get('scope_bytes'))}` bytes (`{fmt_float(progress.get('scope_percent'), 3)}%`)",
                    f"- Decode remaining scope bytes: `{fmt_int(progress.get('remaining_scope_bytes'))}`",
                ]
            )
        if proc_state.get("active_tree_rss_warning"):
            lines.append(f"- Active process tree warning: `{proc_state.get('active_tree_rss_warning')}`")
    elif isinstance(active_rows, list) and active_rows:
        lines.extend(
            [
                "",
                "## Active RSS",
                "",
                "- Max cmix PID: `n/a`",
                "- Active cmix mode: `n/a`",
                "- Max cmix RSS KiB: `n/a`",
                f"- Active process tree RSS KiB: `{fmt_int(proc_state.get('active_tree_rss_kib'))}`",
                f"- Local binary `10GiB` guard KiB: `{fmt_int(proc_state.get('rss_guard_kib'))}`",
                f"- Decimal `10GB` guard KiB: `{fmt_int(proc_state.get('decimal_10gb_guard_kib'))}`",
                "- Single-process binary margin KiB: `n/a`",
                "- Single-process decimal margin KiB: `n/a`",
                f"- Active process tree margin KiB (binary): `{fmt_int(proc_state.get('active_tree_margin_kib'))}`",
                f"- Active process tree decimal margin KiB: `{fmt_int(proc_state.get('active_tree_decimal_10gb_margin_kib'))}`",
            ]
        )
        if proc_state.get("active_tree_rss_warning"):
            lines.append(f"- Active process tree warning: `{proc_state.get('active_tree_rss_warning')}`")
    conting = data.get("contingencies") if isinstance(data.get("contingencies"), dict) else {}
    if conting:
        if_passes = conting.get("if_passes", {}) if isinstance(conting.get("if_passes"), dict) else {}
        if_rss = conting.get("if_rss_fails", {}) if isinstance(conting.get("if_rss_fails"), dict) else {}
        lower = if_rss.get("lower_memory_suggestion", {}) if isinstance(if_rss.get("lower_memory_suggestion"), dict) else {}
        lines.extend(
            [
                "",
                "## Contingencies",
                "",
                f"- If current gate passes: `{if_passes.get('action', 'unknown')}`",
                f"- Pass next scope: `{fmt_int(if_passes.get('next_scope_bytes'))}`",
                f"- If RSS fails: `{if_rss.get('action', 'unknown')}`",
                f"- Lower candidate: `{lower.get('suggested_candidate', 'unknown')}`",
                f"- Lower PPMD KiB: `{fmt_int(lower.get('suggested_kib'))}`",
                "- If roundtrip or determinism fails: `record failure and do not promote`",
            ]
        )
    lines.extend(["", "## Proof Boundary", ""])
    for key in ("best_exact_10m", "best_exact_10m_archive", "best_exact_100m", "best_full_1g", "best_forecast"):
        row = data.get(key)
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- {key}: `{row.get('program_id', row.get('status', 'none'))}`; "
            f"status `{row.get('status', 'artifact-backed')}`; "
            f"score `{fmt_int(row.get('hutter_score', row.get('projected_score')) )}`"
        )
    lines.extend(
        ["", "## Claim Rule", "", "No prefix row proves the `10.5000000%` full-corpus target."]
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=pathlib.Path, default=OUT_JSON)
    parser.add_argument("--md-out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--check", action="store_true", help="validate current receipt can be rendered")
    args = parser.parse_args()

    data = receipt()
    rendered_json = json.dumps(data, indent=2, sort_keys=True) + "\n"
    rendered_md = render_md(data)
    if args.check:
        required = (
            "project",
            "objective",
            "target_score_10_95",
            "has_10_95_constructive_upper_bound",
            "active_processes",
            "operator_logs",
            "release_receipts",
            "candidate_audit",
            "active_candidate_recent_artifacts",
            "handoff",
            "gate_decision",
            "gate_evidence_status",
            "observed_gate_command",
            "operator_action",
            "contingencies",
        )
        missing = [key for key in required if key not in data]
        if missing:
            print("missing required receipt keys: " + ", ".join(missing))
            return 1
        try:
            json.loads(rendered_json)
        except json.JSONDecodeError as exc:
            print(f"invalid JSON render: {exc}")
            return 1
        if not rendered_md.startswith("# enwiki9 Status Receipt\n"):
            print("invalid Markdown render")
            return 1
        print("status_receipt_render_ok")
        return 0

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(rendered_json)
    args.md_out.write_text(rendered_md)
    print(f"wrote {rel(args.json_out)}")
    print(f"wrote {rel(args.md_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
