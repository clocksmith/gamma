#!/usr/bin/env python3
"""Lock-aware exact validation queue for GEPA page-order candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import zlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
TRIAGE = ROOT / "tools" / "candidate_triage.py"
DEFAULT_LOCK = pathlib.Path("/tmp/enwiki9-heavy.lock")
DEFAULT_BASELINE = "fx2_geometry_title_sort_dictcmix_xz_zlibpy_min_v1"
FLOCK_BUSY_CODE = 75
ACTIVE_PATTERN = (
    "bench.py|projects/enwiki9/lib/driver.py|lib/driver.py|cmix|qm_context|"
    "enwiki9-heavy.lock|fx2_core_tune_queue.py|fx2_core_tune_package.py"
)
RESPECT_HEAVY_LOCK_DEFAULT = False


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def candidate_score(meta: dict[str, Any]) -> float:
    hit = ((meta.get("screen_evidence") or {}).get("hit") or {})
    for key in ("smooth_objective", "adjacency_score"):
        value = hit.get(key)
        if isinstance(value, int | float):
            return float(value)
    return float("-inf")


def candidate_delta(meta: dict[str, Any]) -> float:
    hit = ((meta.get("screen_evidence") or {}).get("hit") or {})
    value = hit.get("score_delta_vs_original")
    return float(value) if isinstance(value, int | float) else float("-inf")


def candidate_order_sha(meta: dict[str, Any]) -> str | None:
    hit = ((meta.get("screen_evidence") or {}).get("hit") or {})
    value = hit.get("order_sha256")
    return str(value) if value else None


def gate_data(gate_size: int) -> bytes:
    fixture = ROOT / "data" / f"enwik9_{gate_size}.bin"
    if fixture.exists():
        return fixture.read_bytes()
    return (ROOT / "data" / "enwik9").read_bytes()[:gate_size]


def transform_fingerprint(candidate_id: str, gate_size: int) -> dict[str, Any] | None:
    payload = PROGRAMS / candidate_id / "p"
    program = PROGRAMS / candidate_id / "program.py"
    if not payload.exists() or not program.exists():
        return None
    try:
        source = zlib.decompress(payload.read_bytes(), -15).decode()
        namespace: dict[str, Any] = {"__file__": str(program)}
        exec(source, namespace)
        reorder = namespace.get("o")
        if not callable(reorder):
            return None
        data = gate_data(gate_size)
        transformed = reorder(data)
        if transformed is None:
            transformed = data
        if not isinstance(transformed, bytes):
            return None
        return {
            "gate_size": gate_size,
            "sha256": hashlib.sha256(transformed).hexdigest(),
            "changed": transformed != data,
            "pages": transformed.count(b"  <page>\n"),
        }
    except Exception as exc:
        return {"gate_size": gate_size, "error": f"{type(exc).__name__}: {exc}"}


def annotate_transform_fingerprints(
    candidates: list[dict[str, Any]],
    *,
    gate_size: int,
    enabled: bool,
) -> list[dict[str, Any]]:
    if not enabled:
        return candidates
    for candidate in candidates:
        candidate["gate_transform"] = transform_fingerprint(candidate["id"], gate_size)
    return candidates


def dedupe_transform_hashes(
    candidates: list[dict[str, Any]],
    *,
    enabled: bool,
) -> list[dict[str, Any]]:
    if not enabled:
        return candidates
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        transform = candidate.get("gate_transform")
        digest = transform.get("sha256") if isinstance(transform, dict) else None
        if isinstance(digest, str):
            if digest in seen:
                continue
            seen.add(digest)
        out.append(candidate)
    return out


def skip_transform_noops(candidates: list[dict[str, Any]], *, enabled: bool) -> list[dict[str, Any]]:
    if not enabled:
        return candidates
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        transform = candidate.get("gate_transform")
        if isinstance(transform, dict) and transform.get("changed") is False:
            continue
        out.append(candidate)
    return out


def known_transform_hashes(
    *,
    exclude_statuses: set[str],
    gate_size: int,
    enabled: bool,
) -> set[str]:
    if not enabled:
        return set()
    known: set[str] = set()
    for meta_path in PROGRAMS.glob("*/meta.json"):
        meta = load_json(meta_path)
        if not isinstance(meta, dict):
            continue
        if meta.get("family") != "fx2-gepa-order":
            continue
        if str(meta.get("status")) in exclude_statuses:
            continue
        transform = transform_fingerprint(meta_path.parent.name, gate_size)
        digest = transform.get("sha256") if isinstance(transform, dict) else None
        if isinstance(digest, str):
            known.add(digest)
    return known


def skip_known_transform_hashes(
    candidates: list[dict[str, Any]],
    *,
    known_hashes: set[str],
) -> list[dict[str, Any]]:
    if not known_hashes:
        return candidates
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        transform = candidate.get("gate_transform")
        digest = transform.get("sha256") if isinstance(transform, dict) else None
        if isinstance(digest, str) and digest in known_hashes:
            continue
        out.append(candidate)
    return out


def load_candidate(candidate_id: str) -> dict[str, Any]:
    meta_path = PROGRAMS / candidate_id / "meta.json"
    if not meta_path.exists():
        raise SystemExit(f"missing meta.json for {candidate_id}")
    meta = load_json(meta_path)
    if not isinstance(meta, dict):
        raise SystemExit(f"invalid meta.json for {candidate_id}")
    return {
        "id": candidate_id,
        "status": meta.get("status"),
        "family": meta.get("family"),
        "order_fields": meta.get("order_fields", []),
        "screen_score": candidate_score(meta),
        "screen_delta": candidate_delta(meta),
        "screen_order_sha256": candidate_order_sha(meta),
        "screen_source": (meta.get("screen_evidence") or {}).get("source"),
    }


def discover_candidates(statuses: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for meta_path in PROGRAMS.glob("*/meta.json"):
        meta = load_json(meta_path)
        if not isinstance(meta, dict):
            continue
        if meta.get("family") != "fx2-gepa-order":
            continue
        if str(meta.get("status")) not in statuses:
            continue
        rows.append(
            {
                "id": meta_path.parent.name,
                "status": meta.get("status"),
                "family": meta.get("family"),
                "order_fields": meta.get("order_fields", []),
                "screen_score": candidate_score(meta),
                "screen_delta": candidate_delta(meta),
                "screen_order_sha256": candidate_order_sha(meta),
                "screen_source": (meta.get("screen_evidence") or {}).get("source"),
            }
        )
    rows.sort(key=lambda row: (-float(row["screen_score"]), str(row["id"])))
    return rows


def dedupe_order_hashes(candidates: list[dict[str, Any]], enabled: bool) -> list[dict[str, Any]]:
    if not enabled:
        return candidates
    seen: set[tuple[str, ...]] = set()
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        order_hash = candidate.get("screen_order_sha256")
        if order_hash:
            key = ("sha256", str(order_hash))
        else:
            fields = tuple(str(field) for field in candidate.get("order_fields", []))
            key = ("fields",) + fields
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def active_processes() -> list[str]:
    proc = subprocess.run(
        ["pgrep", "-af", ACTIVE_PATTERN],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit(proc.stderr.strip() or "pgrep failed")

    current = os.getpid()
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
        if pid == current:
            continue
        if "pgrep -af" in stripped:
            continue
        if "gepa_validation_queue.py" in stripped:
            continue
        active.append(stripped)
    return active


def lock_is_free(lock_path: pathlib.Path) -> bool:
    proc = subprocess.run(
        ["flock", "-n", "-E", str(FLOCK_BUSY_CODE), str(lock_path), "true"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def wait_for_clear(lock_path: pathlib.Path, *, wait: bool, poll_interval: float) -> dict[str, Any]:
    while True:
        active = active_processes()
        lock_free = lock_is_free(lock_path)
        if not active and lock_free:
            return {"status": "clear", "active_processes": [], "lock_free": True}
        blocked = {
            "status": "blocked",
            "active_processes": active,
            "lock_free": lock_free,
        }
        if not wait:
            return blocked
        time.sleep(poll_interval)


def run_triage_gate(
    candidate_id: str,
    *,
    gate_size: int,
    baseline: str,
    lock_path: pathlib.Path,
    update_meta: bool,
    archive_ceiling: int | None,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(TRIAGE),
        "--run",
        "--reuse-baseline-evidence",
        "--baseline",
        baseline,
        "--gate-size",
        str(gate_size),
        "--candidate",
        candidate_id,
        "--json",
    ]
    if update_meta:
        cmd.insert(3, "--update-meta")
    if archive_ceiling is not None:
        cmd.extend(["--archive-ceiling", f"{gate_size}:{archive_ceiling}"])

    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload: dict[str, Any] | None = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
        "command": cmd,
        "gate_size": gate_size,
    }


def extract_gate(run: dict[str, Any]) -> dict[str, Any] | None:
    payload = run.get("payload")
    if not isinstance(payload, dict):
        return None
    triage = payload.get("triage")
    if not isinstance(triage, list) or not triage:
        return None
    gates = triage[0].get("gates")
    if not isinstance(gates, list) or not gates:
        return None
    gate = gates[-1]
    return gate if isinstance(gate, dict) else None


def archive_delta(gate: dict[str, Any] | None) -> int | None:
    if not isinstance(gate, dict):
        return None
    comparison = gate.get("comparison")
    if not isinstance(comparison, dict):
        return None
    delta = comparison.get("archive_delta_vs_baseline")
    return delta if isinstance(delta, int) else None


def gate_ok(gate: dict[str, Any] | None) -> bool:
    if not isinstance(gate, dict):
        return False
    return (
        gate.get("roundtrip_ok") is True
        and gate.get("determinism_single_host_byte_equal") is True
    )


def run_queue(args: argparse.Namespace, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_result = {"id": candidate["id"], "screen": candidate, "gates": []}
        should_continue = True
        for gate_size in args.gate_size:
            if not should_continue:
                break
            if args.respect_heavy_lock:
                clear = wait_for_clear(
                    args.lock_path,
                    wait=args.wait,
                    poll_interval=args.poll_interval,
                )
                if clear["status"] != "clear":
                    candidate_result["blocked"] = clear
                    results.append(candidate_result)
                    return {"status": "blocked", "results": results}

            run = run_triage_gate(
                candidate["id"],
                gate_size=gate_size,
                baseline=args.baseline,
                lock_path=args.lock_path,
                update_meta=not args.no_update_meta,
                archive_ceiling=args.archive_ceilings.get(gate_size),
            )
            gate = extract_gate(run)
            delta = archive_delta(gate)
            gate_record = {
                "gate_size": gate_size,
                "returncode": run["returncode"],
                "gate": gate,
                "archive_delta_vs_baseline": delta,
            }
            if run["payload"] is None:
                gate_record["stdout"] = run["stdout"]
                gate_record["stderr"] = run["stderr"]
            candidate_result["gates"].append(gate_record)

            if run["returncode"] != 0 or not gate_ok(gate):
                should_continue = False
            elif gate_size >= args.advance_after_gate and not (
                isinstance(delta, int) and delta < 0
            ):
                should_continue = False
        results.append(candidate_result)
    return {"status": "complete", "results": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument(
        "--include-status",
        action="append",
        default=["candidate", "track_source_before_evolution"],
    )
    parser.add_argument("--gate-size", action="append", type=int, default=None)
    parser.add_argument(
        "--archive-ceiling",
        action="append",
        default=[],
        metavar="LIMIT:BYTES",
        help="target-bearing archive ceiling passed to candidate triage; repeatable",
    )
    parser.add_argument("--advance-after-gate", type=int, default=250000)
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--lock-path", type=pathlib.Path, default=DEFAULT_LOCK)
    parser.add_argument("--poll-interval", type=float, default=30.0)
    parser.add_argument(
        "--respect-heavy-lock",
        action="store_true",
        default=RESPECT_HEAVY_LOCK_DEFAULT,
        help=(
            "wait for /tmp/enwiki9-heavy.lock and matching active-process silence "
            "before launching queued gates (off by default)."
        ),
    )
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--no-update-meta", action="store_true")
    parser.add_argument("--dedupe-order-sha", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dedupe-transform-sha", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--skip-transform-noop", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--skip-known-transform-sha", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    args.archive_ceilings = {}
    for value in args.archive_ceiling:
        if ":" not in value:
            raise SystemExit("--archive-ceiling values must be LIMIT:BYTES")
        raw_limit, raw_bytes = value.split(":", 1)
        limit, ceiling = int(raw_limit), int(raw_bytes)
        if limit <= 0 or ceiling <= 0:
            raise SystemExit("--archive-ceiling LIMIT and BYTES must be positive")
        args.archive_ceilings[limit] = ceiling

    if args.top <= 0:
        raise SystemExit("--top must be positive")
    if args.gate_size is None:
        args.gate_size = [1024, 250000, 1000000]
    if any(size <= 0 for size in args.gate_size):
        raise SystemExit("--gate-size values must be positive")

    statuses = set(args.include_status)
    if args.candidate:
        candidates = [load_candidate(candidate_id) for candidate_id in args.candidate]
    else:
        candidates = dedupe_order_hashes(discover_candidates(statuses), args.dedupe_order_sha)
        candidates = annotate_transform_fingerprints(
            candidates,
            gate_size=args.advance_after_gate,
            enabled=args.dedupe_transform_sha,
        )
        candidates = skip_transform_noops(candidates, enabled=args.skip_transform_noop)
        candidates = skip_known_transform_hashes(
            candidates,
            known_hashes=known_transform_hashes(
                exclude_statuses=statuses,
                gate_size=args.advance_after_gate,
                enabled=args.skip_known_transform_sha,
            ),
        )
        candidates = dedupe_transform_hashes(candidates, enabled=args.dedupe_transform_sha)[
            : args.top
        ]
    if args.candidate:
        candidates = annotate_transform_fingerprints(
            candidates,
            gate_size=args.advance_after_gate,
            enabled=args.dedupe_transform_sha,
        )
        candidates = skip_transform_noops(candidates, enabled=args.skip_transform_noop)

    plan = {
        "mode": "run" if args.run else "dry_run",
        "baseline": args.baseline,
        "gate_sizes": args.gate_size,
        "advance_after_gate": args.advance_after_gate,
        "archive_ceilings": args.archive_ceilings,
        "lock_path": str(args.lock_path),
        "respect_heavy_lock": args.respect_heavy_lock,
        "wait": args.wait,
        "selected": candidates,
    }

    if not args.run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    outcome = run_queue(args, candidates)
    plan.update(outcome)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if outcome.get("status") == "complete" else FLOCK_BUSY_CODE


if __name__ == "__main__":
    raise SystemExit(main())
