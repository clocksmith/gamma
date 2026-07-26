"""Run a single program against enwik9 and emit a result JSON.

Usage: python3 lib/driver.py <program_id> [--data PATH] [--limit BYTES]
                              [--run-purpose PURPOSE] [--run-scope-label LABEL]
                              [--run-context CONTEXT] [--run-source SOURCE]
                              [--run-tag TAG]
                              [--check-determinism]
                              [--archive-ceiling BYTES]
                              [--determinism-archive-ceiling BYTES] [--no-save]

The driver:
  1. loads programs/<program_id>/program.py
  2. reads the dataset (or a prefix when --limit is set)
  3. compresses, decompresses, verifies the roundtrip
  4. measures sizes, times, and bits/byte
  5. (optional) compresses a second time and verifies byte-equal output
  6. writes results/<program_id>/<timestamp>.json
  7. appends one row to results/run_ledger.jsonl (unless --no-ledger)
  8. prints the result
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import pathlib
import platform
import sys
import time

from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DEFAULT = ROOT / "data" / "enwik9"
RESULT_LEDGER_PATH = ROOT / "results" / "run_ledger.jsonl"
LEDGER_SCHEMA = "enwiki9_driver_run_ledger_v1"
SCOPE_LABELS = {
    1024: "1k",
    250_000: "250k",
    1_000_000: "1m",
    10_000_000: "10m",
}


def _load(program_id: str):
    path = ROOT / "programs" / program_id / "program.py"
    if not path.exists():
        raise SystemExit(f"program not found: {path}")
    spec = importlib.util.spec_from_file_location(f"prog_{program_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("compress", "decompress"):
        if not callable(getattr(mod, name, None)):
            raise SystemExit(f"{program_id}: missing callable {name}()")
    return mod, path


def _sample_rss_kib() -> int | None:
    try:
        status = pathlib.Path("/proc/self/status")
        with status.open() as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
        return None
    except OSError:
        pass

    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(usage) if platform.system() != "Darwin" else int(usage // 1024)
    except Exception:
        return None


def _load_program_name(program_id: str) -> str | None:
    meta = ROOT / "programs" / program_id / "meta.json"
    if not meta.exists():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return None
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    desc = data.get("description")
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    return None


def _normalize_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _infer_scope_label(limit: int | None) -> str:
    if limit is None:
        return "full"
    return SCOPE_LABELS.get(limit, f"{limit}B")


def _infer_run_purpose(
    run_purpose: str | None,
    limit: int | None,
    check_determinism: bool,
) -> str:
    if run_purpose is not None:
        return run_purpose
    if check_determinism:
        return "verification"
    if limit in SCOPE_LABELS:
        return "smoke"
    if limit is None:
        return "replay"
    return "candidate"


def _parse_run_tags(raw: list[str]) -> list[str]:
    values: list[str] = []
    for item in raw:
        for part in item.split(","):
            token = part.strip()
            if token:
                values.append(token)
    deduped: list[str] = []
    seen: set[str] = set()
    for token in values:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return deduped


def _append_run_ledger(row: dict[str, Any]) -> None:
    RESULT_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_LEDGER_PATH.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, sort_keys=True) + "\n")


def _build_run_ledger_row(
    result: dict[str, Any],
    result_path: pathlib.Path | None,
    program_name: str | None,
    no_save: bool,
) -> dict[str, Any]:
    memory = result.get("memory_kib") or {}
    return {
        "schema": LEDGER_SCHEMA,
        "run_id": f"{result['program_id']}__{result['timestamp'].replace(':', '')}__{result['compressed_md5'][:8]}",
        "program_id": result["program_id"],
        "algorithm_name": program_name or result["program_id"],
        "data_size": result.get("data_size"),
        "data_md5": result.get("data_md5"),
        "data_sha256": result.get("data_sha256"),
        "compressed_size": result.get("compressed_size"),
        "program_size": result.get("program_size"),
        "hutter_score": result.get("hutter_score"),
        "bits_per_byte": result.get("bits_per_byte"),
        "compress_time_s": result.get("compress_time_s"),
        "decompress_time_s": result.get("decompress_time_s"),
        "run_time_s": result.get("run_time_s"),
        "run_purpose": result.get("run_purpose"),
        "run_scope_label": result.get("run_scope_label"),
        "run_context": result.get("run_context"),
        "run_source": result.get("run_source"),
        "run_tags": result.get("run_tags"),
        "determinism_ok": result.get("determinism", {}).get("single_host_byte_equal")
        if isinstance(result.get("determinism"), dict)
        else None,
        "roundtrip_ok": result.get("roundtrip_ok"),
        "result_path": str(result_path) if result_path is not None else None,
        "archival_scope": "full" if not no_save else "ephemeral",
        "timestamp": result.get("timestamp"),
        "recorded_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "host": result.get("host"),
        "memory_kib_before": memory.get("before"),
        "memory_kib_after": memory.get("after"),
        "memory_kib_peak": memory.get("peak"),
        "rss_sample_count": memory.get("sample_count"),
    }

def run(
    program_id: str,
    data_path: pathlib.Path,
    limit: int | None,
    check_determinism: bool = False,
    archive_ceiling: int | None = None,
    determinism_archive_ceiling: int | None = None,
    run_purpose: str | None = None,
    run_scope_label: str | None = None,
    run_context: str | None = None,
    run_source: str | None = None,
    run_tags: list[str] | None = None,
) -> dict:
    inferred_purpose = _infer_run_purpose(
        run_purpose=_normalize_text(run_purpose),
        limit=limit,
        check_determinism=check_determinism,
    )
    inferred_scope_label = _normalize_text(run_scope_label) or _infer_scope_label(limit)
    normalized_context = _normalize_text(run_context)
    normalized_source = _normalize_text(run_source)
    normalized_tags = run_tags or []
    mod, src_path = _load(program_id)
    program_name = _load_program_name(program_id)
    raw = data_path.read_bytes()
    if limit is not None:
        raw = raw[:limit]
    rss_before = _sample_rss_kib()

    t0 = time.perf_counter()
    compressed = mod.compress(raw)
    t_compress = time.perf_counter() - t0
    stats_fn = getattr(mod, "stats", None)
    program_stats = stats_fn() if callable(stats_fn) else None
    compressed_size = len(compressed)

    archive_ceiling_missed = archive_ceiling is not None and compressed_size > archive_ceiling
    if archive_ceiling_missed:
        t_decompress = 0.0
        ok = None
    else:
        t0 = time.perf_counter()
        decompressed = mod.decompress(compressed)
        t_decompress = time.perf_counter() - t0
        ok = decompressed == raw
    program_dir = src_path.parent
    program_files: list[tuple[str, int]] = []
    for child in sorted(program_dir.iterdir()):
        if child.name in ("meta.json", "__pycache__") or child.name.startswith("."):
            continue
        if child.is_file():
            program_files.append((child.name, child.stat().st_size))
    program_size = sum(sz for _, sz in program_files)
    archive_md5 = hashlib.md5(compressed).hexdigest()
    archive_sha256 = hashlib.sha256(compressed).hexdigest()
    rss_after_compress = _sample_rss_kib()

    determinism: dict | None = None
    should_check_determinism = (
        check_determinism
        and not archive_ceiling_missed
        and (
            determinism_archive_ceiling is None
            or compressed_size <= determinism_archive_ceiling
        )
    )
    if should_check_determinism:
        compressed2 = mod.compress(raw)
        det_ok = compressed == compressed2
        det_md5 = hashlib.md5(compressed2).hexdigest()
        det_sha256 = hashlib.sha256(compressed2).hexdigest()
        determinism = {
            "single_host_byte_equal": det_ok,
            "first_run_md5": archive_md5,
            "second_run_md5": det_md5,
            "first_run_sha256": archive_sha256,
            "second_run_sha256": det_sha256,
            "first_divergence_byte": None
            if det_ok
            else next(
                (i for i, (a, b) in enumerate(zip(compressed, compressed2)) if a != b),
                min(len(compressed), len(compressed2)),
            ),
        }
    elif check_determinism:
        determinism = {
            "single_host_byte_equal": None,
            "skipped": True,
            "reason": "archive_ceiling_missed"
            if archive_ceiling_missed
            else "determinism_archive_ceiling_missed",
            "archive_ceiling": archive_ceiling,
            "determinism_archive_ceiling": determinism_archive_ceiling,
        }

    bits_per_byte = (compressed_size * 8 / len(raw)) if raw else 0.0
    t_finished = time.perf_counter()
    t_total = t_finished - t0
    rss_after = _sample_rss_kib()
    rss_samples = [v for v in (rss_before, rss_after_compress, rss_after) if isinstance(v, int)]
    rss_peak = max(rss_samples) if rss_samples else None

    result = {
        "program_id": program_id,
        "data_path": str(data_path),
        "data_size": len(raw),
        "data_md5": hashlib.md5(raw).hexdigest(),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_size": compressed_size,
        "compressed_md5": archive_md5,
        "compressed_sha256": archive_sha256,
        "program_size": program_size,
        "program_files": program_files,
        "hutter_score": compressed_size + program_size,
        "bits_per_byte": round(bits_per_byte, 6),
        "compress_time_s": round(t_compress, 4),
        "decompress_time_s": round(t_decompress, 4),
        "roundtrip_ok": ok,
        "roundtrip_skipped": {
            "reason": "archive_ceiling_missed",
            "archive_ceiling": archive_ceiling,
        }
        if archive_ceiling_missed
        else None,
        "run_purpose": inferred_purpose,
        "run_scope_label": inferred_scope_label,
        "run_context": normalized_context,
        "run_source": normalized_source,
        "run_tags": normalized_tags,
        "determinism": determinism,
        "host": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
            "node": platform.node(),
        },
        "program_name": program_name,
        "memory_kib": {
            "before": rss_before,
            "during_compress": rss_after_compress,
            "after": rss_after,
            "peak": rss_peak,
            "sample_count": len(rss_samples),
        },
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    result["run_time_s"] = round(t_total, 4)
    if program_stats is not None:
        result["program_stats"] = program_stats
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("program_id")
    ap.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only use the first N bytes (smoke testing)",
    )
    ap.add_argument(
        "--check-determinism",
        action="store_true",
        help="compress twice and verify byte-equal output (single-host determinism)",
    )
    ap.add_argument(
        "--archive-ceiling",
        type=int,
        default=None,
        help="skip roundtrip and determinism when the first archive misses this byte ceiling",
    )
    ap.add_argument(
        "--determinism-archive-ceiling",
        type=int,
        default=None,
        help="skip the second compression when the first archive misses this byte ceiling",
    )
    ap.add_argument(
        "--run-purpose",
        default=None,
        help=(
            "provenance label for this run (for example: smoke|gate|control|"
            "verification|rebaseline|replay)"
        ),
    )
    ap.add_argument(
        "--run-scope-label",
        default=None,
        help="override inferred scope label (for example: full|1k|250k|1m|10m)",
    )
    ap.add_argument(
        "--run-context",
        default=None,
        help="short workflow/lane context label (for example: cmix21_1m_queue)",
    )
    ap.add_argument(
        "--run-source",
        default=None,
        help="how this run was launched (manual|queue|script|gate|normalized)",
    )
    ap.add_argument(
        "--run-tag",
        action="append",
        default=[],
        help="repeatable provenance tag (or comma-separated list)",
    )
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"dataset missing at {args.data} — run bench.py --setup first")

    result = run(
        args.program_id,
        args.data,
        args.limit,
        args.check_determinism,
        args.archive_ceiling,
        args.determinism_archive_ceiling,
        run_purpose=args.run_purpose,
        run_scope_label=args.run_scope_label,
        run_context=args.run_context,
        run_source=args.run_source,
        run_tags=_parse_run_tags(args.run_tag),
    )

    if not args.no_save:
        out_dir = ROOT / "results" / args.program_id
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = result["timestamp"].replace(":", "")
        result_path = out_dir / f"{stamp}.json"
        result_path.write_text(json.dumps(result, indent=2) + "\n")
        if not args.no_ledger:
            ledger_row = _build_run_ledger_row(
                result,
                result_path=result_path,
                program_name=result.get("program_name"),
                no_save=args.no_save,
            )
            _append_run_ledger(ledger_row)

    print(json.dumps(result, indent=2))
    return 0 if result["roundtrip_ok"] is not False else 1


if __name__ == "__main__":
    sys.exit(main())
