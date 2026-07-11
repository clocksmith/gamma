"""Lane 0 triage for enwiki9 candidate measurement cleanup.

The default mode is a dry-run inventory filter. Scoring runs require --run and
are executed through a non-blocking flock around lib/driver.py, with a process
preflight before every gate.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import signal
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS_DIR = ROOT / "programs"
INVENTORY_JSON = ROOT / "candidate_inventory.json"
DRIVER = ROOT / "lib" / "driver.py"
DEFAULT_LOCK_PATH = pathlib.Path("/tmp/enwiki9-heavy.lock")
DEFAULT_BASELINE = "baseline_lzma"
DEFAULT_GATE_SIZES = (1024, 250000)
HEAVY_PROCESS_PATTERN = "bench.py|lib/driver.py|cmix|qm_context"
FLOCK_BUSY_CODE = 75
DRIVER_TIMEOUT_CODE = 124
RESULTS_DIR = ROOT / "results"


@dataclass
class DriverRun:
    program_id: str
    limit: int
    returncode: int
    stdout: str
    stderr: str
    result: dict[str, Any] | None
    blocked_reason: str | None = None


def rel(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_inventory() -> dict[str, Any]:
    if not INVENTORY_JSON.exists():
        raise SystemExit(
            f"missing {rel(INVENTORY_JSON)}; run candidate_audit.py --write first"
        )
    inventory = load_json(INVENTORY_JSON)
    if not isinstance(inventory, dict) or "candidates" not in inventory:
        raise SystemExit(f"invalid inventory shape: {rel(INVENTORY_JSON)}")
    return inventory


def parse_gate_sizes(values: list[int] | None) -> list[int]:
    sizes = list(DEFAULT_GATE_SIZES if values is None else values)
    if not sizes:
        raise SystemExit("at least one --gate-size is required")
    if any(size <= 0 for size in sizes):
        raise SystemExit("--gate-size values must be positive")
    return sizes


def selected_candidates(
    inventory: dict[str, Any],
    *,
    statuses: set[str],
    explicit_ids: list[str],
    skip: int,
    limit: int | None,
) -> list[dict[str, Any]]:
    candidates = inventory.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit("inventory candidates field is not a list")

    if explicit_ids:
        by_id = {candidate.get("id"): candidate for candidate in candidates}
        missing = [candidate_id for candidate_id in explicit_ids if candidate_id not in by_id]
        if missing:
            raise SystemExit(f"unknown candidate id(s): {', '.join(missing)}")
        selected = [by_id[candidate_id] for candidate_id in explicit_ids]
    else:
        selected = [
            candidate
            for candidate in candidates
            if str(candidate.get("status")) in statuses
        ]

    selected = sorted(selected, key=lambda candidate: str(candidate.get("id")))
    if skip:
        selected = selected[skip:]
    if limit is not None:
        selected = selected[:limit]
    return selected


def active_heavy_processes() -> list[str]:
    proc = subprocess.run(
        ["pgrep", "-af", HEAVY_PROCESS_PATTERN],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit(proc.stderr.strip() or "pgrep failed")

    current_pid = os.getpid()
    active: list[str] = []
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        try:
            pid = int(parts[0])
        except ValueError:
            pid = None
        if pid == current_pid:
            continue
        if "pgrep -af" in stripped:
            continue
        if "candidate_triage.py" in stripped:
            continue
        active.append(stripped)
    return active


def parse_driver_stdout(stdout: str) -> dict[str, Any] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return None
    return result if isinstance(result, dict) else None


def run_driver_locked(
    program_id: str,
    *,
    limit: int,
    lock_path: pathlib.Path,
    driver_timeout: int | None = None,
    archive_ceiling: int | None = None,
) -> DriverRun:
    active = active_heavy_processes()
    if active:
        return DriverRun(
            program_id=program_id,
            limit=limit,
            returncode=FLOCK_BUSY_CODE,
            stdout="",
            stderr="\n".join(active),
            result=None,
            blocked_reason="preflight_busy",
        )

    cmd = [
        "flock",
        "-n",
        "-E",
        str(FLOCK_BUSY_CODE),
        str(lock_path),
        sys.executable,
        str(DRIVER),
        program_id,
        "--limit",
        str(limit),
        "--check-determinism",
    ]
    if archive_ceiling is not None:
        cmd.extend(
            [
                "--archive-ceiling",
                str(archive_ceiling),
                "--determinism-archive-ceiling",
                str(archive_ceiling),
            ]
        )
    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(
            timeout=None if driver_timeout is None else driver_timeout
        )
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except Exception:
            stdout, stderr = exc.stdout or "", exc.stderr or ""
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return DriverRun(
            program_id=program_id,
            limit=limit,
            returncode=DRIVER_TIMEOUT_CODE,
            stdout=stdout or "",
            stderr="driver timed out",
            result=None,
            blocked_reason=None,
        )

    blocked_reason = "lock_busy" if proc.returncode == FLOCK_BUSY_CODE else None
    proc_stdout = stdout if stdout is not None else ""
    proc_stderr = stderr if stderr is not None else ""
    return DriverRun(
        program_id=program_id,
        limit=limit,
        returncode=proc.returncode,
        stdout=proc_stdout,
        stderr=proc_stderr,
        result=parse_driver_stdout(proc_stdout),
        blocked_reason=blocked_reason,
    )


def result_is_deterministic(result: dict[str, Any]) -> bool:
    determinism = result.get("determinism")
    if not isinstance(determinism, dict):
        return False
    return determinism.get("single_host_byte_equal") is True


def scope_from_label(label: str) -> int | None:
    parts = label.lower().replace("-", "_").split("_")
    scopes = {
        "1k": 1024,
        "64k": 65536,
        "250k": 250000,
        "1m": 1000000,
        "10m": 10000000,
        "100m": 100000000,
        "1g": 1000000000,
    }
    for part in parts:
        if part in scopes:
            return scopes[part]
    return None


def normalize_cached_result(
    *,
    program_id: str,
    row: dict[str, Any],
    source: str,
    label: str = "",
) -> dict[str, Any] | None:
    data_size = row.get("data_size")
    if not isinstance(data_size, int):
        data_size = row.get("input_bytes")
    if not isinstance(data_size, int):
        data_size = scope_from_label(label)
    compressed_size = row.get("compressed_size")
    if not isinstance(compressed_size, int):
        compressed_size = row.get("archive") or row.get("archive_size")
    program_size = row.get("program_size")
    hutter_score = row.get("hutter_score")
    if (
        not isinstance(hutter_score, int)
        and isinstance(compressed_size, int)
        and isinstance(program_size, int)
    ):
        hutter_score = compressed_size + program_size
    if (
        not isinstance(data_size, int)
        or not isinstance(compressed_size, int)
        or not isinstance(program_size, int)
        or not isinstance(hutter_score, int)
    ):
        return None

    determinism = row.get("determinism")
    if isinstance(determinism, bool):
        determinism = {"single_host_byte_equal": determinism}
    elif not isinstance(determinism, dict):
        deterministic = row.get("deterministic")
        inherited_identity = (
            isinstance(row.get("roundtrip_basis"), str)
            or "inherited" in label
            or "identity" in label
        )
        determinism = {"single_host_byte_equal": deterministic is True or inherited_identity}

    return {
        "program_id": program_id,
        "data_size": data_size,
        "data_md5": row.get("data_md5"),
        "compressed_size": compressed_size,
        "program_size": program_size,
        "hutter_score": hutter_score,
        "bits_per_byte": row.get("bits_per_byte"),
        "roundtrip_ok": row.get("roundtrip_ok") is not False,
        "determinism": determinism,
        "program_stats": row.get("program_stats"),
        "cached_source": source,
    }


def cached_result_for(program_id: str, gate_size: int) -> dict[str, Any] | None:
    result_dir = RESULTS_DIR / program_id
    if result_dir.exists():
        matches: list[dict[str, Any]] = []
        for path in sorted(result_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
            try:
                row = load_json(path)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict) or row.get("data_size") != gate_size:
                continue
            normalized = normalize_cached_result(
                program_id=program_id,
                row=row,
                source=rel(path),
                label=path.stem,
            )
            if (
                normalized is not None
                and normalized.get("roundtrip_ok") is True
                and result_is_deterministic(normalized)
            ):
                matches.append(normalized)
        if matches:
            return matches[-1]

    meta_path = PROGRAMS_DIR / program_id / "meta.json"
    if not meta_path.exists():
        return None
    try:
        meta = load_json(meta_path)
    except json.JSONDecodeError:
        return None
    if not isinstance(meta, dict):
        return None
    for section_name in ("measured", "verified_gates"):
        section = meta.get(section_name)
        if not isinstance(section, dict):
            continue
        for label, row in section.items():
            if not isinstance(row, dict):
                continue
            normalized = normalize_cached_result(
                program_id=program_id,
                row=row,
                source=f"{rel(meta_path)}:{section_name}:{label}",
                label=str(label),
            )
            if (
                normalized is not None
                and normalized.get("data_size") == gate_size
                and normalized.get("roundtrip_ok") is True
                and result_is_deterministic(normalized)
            ):
                return normalized
    return None


def dependency_error(text: str) -> bool:
    needles = (
        "ModuleNotFoundError",
        "ImportError",
        "FileNotFoundError",
        "No such file or directory",
        "cannot open shared object file",
        "not found",
    )
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def timeout_error(text: str) -> bool:
    lowered = text.lower()
    return (
        "timed out" in lowered
        or "timed out while trying to run" in lowered
        or "command timed out" in lowered
    )


def classify_driver_failure(run: DriverRun) -> tuple[str, str]:
    text = "\n".join(part for part in (run.stdout, run.stderr) if part)
    if run.blocked_reason in ("preflight_busy", "lock_busy"):
        return "blocked_by_lock", run.blocked_reason
    if run.returncode == DRIVER_TIMEOUT_CODE:
        return "blocked_dependency", "driver_timeout"
    if "missing callable" in text or "program not found" in text:
        return "retired", "contract_failure"
    if dependency_error(text) or timeout_error(text):
        return "blocked_dependency", "dependency_error"
    return "retired", "driver_failure"


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    determinism = result.get("determinism")
    return {
        "program_id": result.get("program_id"),
        "data_size": result.get("data_size"),
        "data_md5": result.get("data_md5"),
        "compressed_size": result.get("compressed_size"),
        "program_size": result.get("program_size"),
        "hutter_score": result.get("hutter_score"),
        "bits_per_byte": result.get("bits_per_byte"),
        "roundtrip_ok": result.get("roundtrip_ok"),
        "determinism_single_host_byte_equal": (
            determinism.get("single_host_byte_equal")
            if isinstance(determinism, dict)
            else None
        ),
        "program_stats": result.get("program_stats"),
    }


def compare_against_baseline(
    *,
    candidate_result: dict[str, Any],
    baseline_result: dict[str, Any],
) -> dict[str, Any]:
    comparison = {
        "baseline": summarize_result(baseline_result),
        "archive_delta_vs_baseline": None,
        "score_delta_vs_baseline": None,
        "same_scope": (
            candidate_result.get("data_size") == baseline_result.get("data_size")
            and candidate_result.get("data_md5") == baseline_result.get("data_md5")
        ),
    }
    if isinstance(candidate_result.get("compressed_size"), int) and isinstance(
        baseline_result.get("compressed_size"), int
    ):
        comparison["archive_delta_vs_baseline"] = (
            candidate_result["compressed_size"] - baseline_result["compressed_size"]
        )
    if isinstance(candidate_result.get("hutter_score"), int) and isinstance(
        baseline_result.get("hutter_score"), int
    ):
        comparison["score_delta_vs_baseline"] = (
            candidate_result["hutter_score"] - baseline_result["hutter_score"]
        )
    return comparison


def classify_success(gate_rows: list[dict[str, Any]]) -> tuple[str, str]:
    final_gate = gate_rows[-1]
    comparison = final_gate.get("comparison")
    if not isinstance(comparison, dict):
        return "blocked_dependency", "Missing same-scope baseline comparison."
    if comparison.get("same_scope") is not True:
        return "blocked_dependency", "Baseline and candidate data scope did not match."

    score_delta = comparison.get("score_delta_vs_baseline")
    archive_delta = comparison.get("archive_delta_vs_baseline")
    if isinstance(score_delta, int) and score_delta < 0:
        return "active", "Promote: same-scope Hutter score beats baseline."
    if isinstance(archive_delta, int) and archive_delta < 0:
        return (
            "measured_negative",
            "Keep as negative evidence: archive improves but counted program size loses.",
        )
    return "measured_negative", "Keep as negative evidence: valid deterministic loser."


def inspect_contract(candidate_id: str) -> dict[str, Any]:
    program_path = PROGRAMS_DIR / candidate_id / "program.py"
    if not program_path.exists():
        return {
            "id": candidate_id,
            "contract_status": "missing_program",
            "proposed_status": "retired",
            "verdict": "Retire: missing program.py contract.",
            "reasons": ["missing_program_py"],
        }

    probe = """
import importlib.util,json,pathlib,sys,traceback
root=pathlib.Path(sys.argv[1])
candidate_id=sys.argv[2]
path=root/"programs"/candidate_id/"program.py"
try:
 spec=importlib.util.spec_from_file_location("probe_"+candidate_id,path)
 mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod)
 missing=[name for name in ("compress","decompress") if not callable(getattr(mod,name,None))]
 print(json.dumps({"status":"missing_callable" if missing else "ok","missing":missing}))
except Exception as exc:
 print(json.dumps({"status":"import_error","error_type":type(exc).__name__,"error":str(exc)}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", probe, str(ROOT), candidate_id],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload: dict[str, Any] | None = None
    for line in reversed(proc.stdout.splitlines()):
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            payload = parsed
            break
    if payload is None:
        return {
            "id": candidate_id,
            "contract_status": "import_error",
            "proposed_status": "blocked_dependency" if dependency_error(proc.stderr) else "retired",
            "verdict": "Blocked: program.py import probe did not return a contract result."
            if dependency_error(proc.stderr)
            else "Retire: program.py import probe did not return a contract result.",
            "reasons": ["import_probe_failed"],
        }

    status = str(payload.get("status"))
    if status == "import_error":
        text = "\n".join(
            part
            for part in (str(payload.get("error") or ""), str(payload.get("error_type") or ""), proc.stderr)
            if part
        )
        proposed_status = "blocked_dependency" if dependency_error(text) else "retired"
        return {
            "id": candidate_id,
            "contract_status": "import_error",
            "proposed_status": proposed_status,
            "verdict": "Blocked: program.py import failed due to a dependency."
            if proposed_status == "blocked_dependency"
            else "Retire: program.py import failed.",
            "reasons": ["program_py_import_error", str(payload.get("error_type") or "unknown")],
        }

    missing = sorted(str(name) for name in payload.get("missing", []) if isinstance(name, str))
    if missing:
        return {
            "id": candidate_id,
            "contract_status": "missing_callable",
            "proposed_status": "retired",
            "verdict": f"Retire: missing callable(s): {', '.join(missing)}.",
            "reasons": [f"missing_{name}" for name in missing],
        }
    return {
        "id": candidate_id,
        "contract_status": "ok",
        "proposed_status": None,
        "verdict": "program.py imports and exposes compress/decompress.",
        "reasons": [],
    }


def update_contract_meta(candidate_id: str, row: dict[str, Any], *, restore_ok_status: str | None = None) -> bool:
    proposed_status = row.get("proposed_status")
    if proposed_status not in {"retired", "blocked_dependency"} and not (
        restore_ok_status and row.get("contract_status") == "ok"
    ):
        return False
    meta_path = PROGRAMS_DIR / candidate_id / "meta.json"
    if not meta_path.exists():
        return False
    meta = load_json(meta_path)
    if not isinstance(meta, dict):
        raise SystemExit(f"invalid meta shape: {rel(meta_path)}")

    measured = meta.setdefault("measured", {})
    if not isinstance(measured, dict):
        measured = {}
        meta["measured"] = measured
    check_record = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "contract_status": row.get("contract_status"),
        "proposed_status": proposed_status or restore_ok_status,
        "verdict": row.get("verdict"),
        "reasons": row.get("reasons", []),
    }
    checks = measured.setdefault("lane0_contract_checks", [])
    if not isinstance(checks, list):
        checks = []
        measured["lane0_contract_checks"] = checks
    checks.append(check_record)
    measured["lane0_contract"] = check_record
    meta["status"] = proposed_status or restore_ok_status
    meta["verdict"] = row.get("verdict", meta.get("verdict"))
    write_json(meta_path, meta)
    return True


def triage_one(
    candidate_id: str,
    *,
    gate_sizes: list[int],
    baseline_id: str,
    lock_path: pathlib.Path,
    baseline_cache: dict[int, DriverRun],
    driver_timeout: int | None,
    reuse_baseline_evidence: bool,
    archive_ceilings: dict[int, int],
) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []
    for gate_size in gate_sizes:
        baseline_run = baseline_cache.get(gate_size)
        if baseline_run is None:
            cached_baseline = (
                cached_result_for(baseline_id, gate_size)
                if reuse_baseline_evidence
                else None
            )
            if cached_baseline is not None:
                baseline_run = DriverRun(
                    program_id=baseline_id,
                    limit=gate_size,
                    returncode=0,
                    stdout="",
                    stderr="",
                    result=cached_baseline,
                )
            else:
                baseline_run = run_driver_locked(
                    baseline_id,
                    limit=gate_size,
                    lock_path=lock_path,
                    driver_timeout=driver_timeout,
                )
            baseline_cache[gate_size] = baseline_run
        if baseline_run.result is None or baseline_run.returncode != 0:
            status, reason = classify_driver_failure(baseline_run)
            return {
                "id": candidate_id,
                "proposed_status": status,
                "verdict": f"Blocked: baseline {baseline_id} failed at {gate_size}: {reason}.",
                "gates": gates,
                "blocked_reason": baseline_run.blocked_reason,
            }
        if (
            baseline_run.result.get("roundtrip_ok") is not True
            or not result_is_deterministic(baseline_run.result)
        ):
            return {
                "id": candidate_id,
                "proposed_status": "blocked_dependency",
                "verdict": f"Blocked: baseline {baseline_id} is not deterministic at {gate_size}.",
                "gates": gates,
            }

        candidate_run = run_driver_locked(
            candidate_id,
            limit=gate_size,
            lock_path=lock_path,
            driver_timeout=driver_timeout,
            archive_ceiling=archive_ceilings.get(gate_size),
        )
        if candidate_run.result is None:
            status, reason = classify_driver_failure(candidate_run)
            return {
                "id": candidate_id,
                "proposed_status": status,
                "verdict": f"{status}: {reason} at {gate_size}.",
                "gates": gates,
                "blocked_reason": candidate_run.blocked_reason,
            }

        gate = summarize_result(candidate_run.result)
        gate["comparison"] = compare_against_baseline(
            candidate_result=candidate_run.result,
            baseline_result=baseline_run.result,
        )
        ceiling = archive_ceilings.get(gate_size)
        ceiling_missed = (
            ceiling is not None
            and isinstance(candidate_run.result.get("compressed_size"), int)
            and candidate_run.result["compressed_size"] > ceiling
        )
        gate["archive_ceiling"] = ceiling
        gate["archive_ceiling_missed"] = ceiling_missed
        gates.append(gate)

        if ceiling_missed:
            return {
                "id": candidate_id,
                "proposed_status": "measured_negative",
                "verdict": (
                    f"Retire: exact archive exceeded the target-bearing ceiling at "
                    f"{gate_size}: {candidate_run.result['compressed_size']} > {ceiling}."
                ),
                "gates": gates,
            }

        if candidate_run.result.get("roundtrip_ok") is not True:
            return {
                "id": candidate_id,
                "proposed_status": "retired",
                "verdict": f"Retire: roundtrip failed at {gate_size}.",
                "gates": gates,
            }
        if not result_is_deterministic(candidate_run.result):
            return {
                "id": candidate_id,
                "proposed_status": "retired",
                "verdict": f"Retire: deterministic compression failed at {gate_size}.",
                "gates": gates,
            }

    status, verdict = classify_success(gates)
    return {
        "id": candidate_id,
        "proposed_status": status,
        "verdict": verdict,
        "gates": gates,
    }


def update_candidate_meta(candidate_id: str, triage: dict[str, Any]) -> None:
    meta_path = PROGRAMS_DIR / candidate_id / "meta.json"
    if not meta_path.exists():
        return
    meta = load_json(meta_path)
    if not isinstance(meta, dict):
        raise SystemExit(f"invalid meta shape: {rel(meta_path)}")

    measured = meta.setdefault("measured", {})
    if not isinstance(measured, dict):
        measured = {}
        meta["measured"] = measured
    run_record = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gates": triage.get("gates", []),
        "proposed_status": triage.get("proposed_status"),
        "verdict": triage.get("verdict"),
    }
    runs = measured.setdefault("lane0_triage_runs", [])
    if not isinstance(runs, list):
        runs = []
        measured["lane0_triage_runs"] = runs
    runs.append(run_record)
    measured["lane0_triage"] = run_record

    proposed_status = triage.get("proposed_status")
    if proposed_status in {
        "active",
        "measured_negative",
        "retired",
        "blocked_dependency",
        "track_source_before_evolution",
    }:
        meta["status"] = proposed_status
    meta["verdict"] = triage.get("verdict", meta.get("verdict"))
    write_json(meta_path, meta)


def is_transient_lock_block(triage: dict[str, Any]) -> bool:
    return triage.get("blocked_reason") in {"preflight_busy", "lock_busy"}


def render_dry_run(
    *,
    selected: list[dict[str, Any]],
    statuses: set[str],
    selection_mode: str,
    gate_sizes: list[int],
    baseline_id: str,
    lock_path: pathlib.Path,
    archive_ceilings: dict[int, int],
) -> dict[str, Any]:
    return {
        "mode": "dry_run",
        "selection_mode": selection_mode,
        "selected_count": len(selected),
        "selected_statuses": sorted(statuses),
        "planned_gates": gate_sizes,
        "baseline": baseline_id,
        "lock_path": str(lock_path),
        "archive_ceilings": archive_ceilings,
        "selected": [
            {
                "id": candidate.get("id"),
                "status": candidate.get("status"),
                "reasons": candidate.get("reasons", []),
            }
            for candidate in selected
        ],
        "run_command": (
            "python3 projects/enwiki9/tools/candidate_triage.py "
            "--run --limit-candidates N"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--status",
        action="append",
        default=None,
        help="inventory status to select; repeatable; default benchmark_or_retire",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        help="explicit candidate id to triage; repeatable",
    )
    parser.add_argument("--limit-candidates", type=int, default=None)
    parser.add_argument("--skip-candidates", type=int, default=0)
    parser.add_argument("--gate-size", action="append", type=int, default=None)
    parser.add_argument(
        "--archive-ceiling",
        action="append",
        default=[],
        metavar="LIMIT:BYTES",
        help=(
            "skip roundtrip and determinism when a candidate archive exceeds the "
            "target-bearing ceiling for a gate; repeatable"
        ),
    )
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--lock-path", type=pathlib.Path, default=DEFAULT_LOCK_PATH)
    parser.add_argument("--run", action="store_true", help="execute locked gates")
    parser.add_argument(
        "--contract-check",
        action="store_true",
        help="validate program.py contract shape without scoring",
    )
    parser.add_argument(
        "--restore-ok-status",
        help="with --contract-check --update-meta, assign this status to contracts that import cleanly",
    )
    parser.add_argument("--update-meta", action="store_true", help="write triage status to meta.json")
    parser.add_argument(
        "--reuse-baseline-evidence",
        action="store_true",
        help="use deterministic baseline result metadata when available",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON only")
    parser.add_argument(
        "--driver-timeout",
        type=int,
        default=None,
        help=(
            "maximum wall time in seconds per driver invocation; if exceeded, mark"
            " as blocked_dependency."
        ),
    )
    args = parser.parse_args(argv)

    archive_ceilings: dict[int, int] = {}
    for value in args.archive_ceiling:
        if ":" not in value:
            raise SystemExit("--archive-ceiling values must be LIMIT:BYTES")
        raw_limit, raw_bytes = value.split(":", 1)
        limit, ceiling = int(raw_limit), int(raw_bytes)
        if limit <= 0 or ceiling <= 0:
            raise SystemExit("--archive-ceiling LIMIT and BYTES must be positive")
        archive_ceilings[limit] = ceiling

    if args.limit_candidates is not None and args.limit_candidates <= 0:
        raise SystemExit("--limit-candidates must be positive")
    if args.skip_candidates < 0:
        raise SystemExit("--skip-candidates must be non-negative")
    if args.run and args.contract_check:
        raise SystemExit("--run and --contract-check are mutually exclusive")
    if args.run and not args.candidate and args.limit_candidates is None:
        raise SystemExit("--run requires --candidate or --limit-candidates")
    if args.restore_ok_status and not (args.contract_check and args.update_meta):
        raise SystemExit("--restore-ok-status requires --contract-check --update-meta")
    if args.update_meta and not args.run and not args.contract_check:
        raise SystemExit("--update-meta requires --run or --contract-check")

    inventory = load_inventory()
    statuses = set(args.status or ["benchmark_or_retire"])
    gate_sizes = parse_gate_sizes(args.gate_size)
    selected = selected_candidates(
        inventory,
        statuses=statuses,
        explicit_ids=args.candidate,
        skip=0 if args.candidate else args.skip_candidates,
        limit=args.limit_candidates,
    )

    if not args.run:
        if args.contract_check:
            rows = [inspect_contract(str(candidate.get("id"))) for candidate in selected]
            updated_meta_ids: list[str] = []
            if args.update_meta:
                for row in rows:
                    if update_contract_meta(
                        str(row.get("id")),
                        row,
                        restore_ok_status=args.restore_ok_status,
                    ):
                        updated_meta_ids.append(str(row.get("id")))
            payload = {
                "mode": "contract_check",
                "selection_mode": "explicit" if args.candidate else "status",
                "selected_count": len(selected),
                "processed_count": len(rows),
                "update_meta_requested": args.update_meta,
                "updated_meta_count": len(updated_meta_ids),
                "updated_meta_ids": updated_meta_ids,
                "contract": rows,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        payload = render_dry_run(
            selected=selected,
            statuses=statuses,
            selection_mode="explicit" if args.candidate else "status",
            gate_sizes=gate_sizes,
            baseline_id=args.baseline,
            lock_path=args.lock_path,
            archive_ceilings=archive_ceilings,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    active = active_heavy_processes()
    if active:
        payload = {
            "mode": "run",
            "status": "blocked",
            "blocked_reason": "preflight_busy",
            "active_processes": active,
            "selected_count": len(selected),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 75

    baseline_cache: dict[int, DriverRun] = {}
    triage_rows: list[dict[str, Any]] = []
    updated_meta_ids: list[str] = []
    for candidate in selected:
        candidate_id = str(candidate.get("id"))
        row = triage_one(
            candidate_id,
            gate_sizes=gate_sizes,
            baseline_id=args.baseline,
            lock_path=args.lock_path,
            baseline_cache=baseline_cache,
            driver_timeout=args.driver_timeout,
            reuse_baseline_evidence=args.reuse_baseline_evidence,
            archive_ceilings=archive_ceilings,
        )
        triage_rows.append(row)
        if args.update_meta and not is_transient_lock_block(row):
            update_candidate_meta(candidate_id, row)
            updated_meta_ids.append(candidate_id)
        if row.get("blocked_reason") in ("preflight_busy", "lock_busy"):
            break

    payload = {
        "mode": "run",
        "selected_count": len(selected),
        "processed_count": len(triage_rows),
        "update_meta_requested": args.update_meta,
        "updated_meta_count": len(updated_meta_ids),
        "updated_meta_ids": updated_meta_ids,
        "baseline": args.baseline,
        "reuse_baseline_evidence": args.reuse_baseline_evidence,
        "gate_sizes": gate_sizes,
        "archive_ceilings": archive_ceilings,
        "lock_path": str(args.lock_path),
        "triage": triage_rows,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
