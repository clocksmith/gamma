#!/usr/bin/env python3
"""Record one driver result JSON into a candidate meta.json file."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
RESULTS = ROOT / "results"


def rel(path: pathlib.Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def artifact_metadata(path: pathlib.Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "bytes": stat.st_size,
        "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def latest_result(program_id: str) -> pathlib.Path:
    result_dir = RESULTS / program_id
    matches = sorted(result_dir.glob("*.json"), key=lambda path: path.stat().st_mtime)
    if not matches:
        raise SystemExit(f"no result JSON files found under {rel(result_dir)}")
    return matches[-1]


def deterministic(result: dict[str, Any]) -> bool | None:
    value = result.get("determinism")
    if not isinstance(value, dict):
        return None
    flag = value.get("single_host_byte_equal")
    return flag if isinstance(flag, bool) else None


def guard_record(guard: dict[str, Any], guard_path: pathlib.Path) -> dict[str, Any]:
    meta = artifact_metadata(guard_path)
    return {
        "rss_guard_json": rel(guard_path),
        "rss_guard_json_bytes": meta["bytes"],
        "rss_guard_json_mtime_utc": meta["mtime_utc"],
        "rss_guard_json_sha256": meta["sha256"],
        "rss_guard_kib": guard.get("limit_kib"),
        "rss_guard_limit_mode": guard.get("limit_mode", "max_single"),
        "max_sampled_single_rss_kib": guard.get("max_sampled_single_rss_kib"),
        "max_sampled_tree_rss_kib": guard.get("max_sampled_tree_rss_kib"),
        "rss_guard_exceeded": guard.get("rss_guard_exceeded"),
        "rss_guard_returncode": guard.get("returncode"),
        "rss_guard_status": guard.get("status"),
        "rss_sample_count": guard.get("sample_count"),
        "official_decimal_limit_kib": guard.get("official_decimal_limit_kib"),
        "official_decimal_over_limit_kib": guard.get(
            "official_decimal_over_limit_kib"
        ),
        "guard_failure": guard.get("failure"),
    }


def result_record(
    result: dict[str, Any],
    result_path: pathlib.Path,
    guard: dict[str, Any] | None = None,
    guard_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    meta = artifact_metadata(result_path)
    record = {
        "result_path": rel(result_path),
        "result_json_bytes": meta["bytes"],
        "result_json_mtime_utc": meta["mtime_utc"],
        "result_json_sha256": meta["sha256"],
        "data_size": result.get("data_size"),
        "data_md5": result.get("data_md5"),
        "data_sha256": result.get("data_sha256"),
        "compressed_size": result.get("compressed_size"),
        "program_size": result.get("program_size"),
        "hutter_score": result.get("hutter_score"),
        "bits_per_byte": result.get("bits_per_byte"),
        "roundtrip_ok": result.get("roundtrip_ok"),
        "determinism": deterministic(result),
        "compressed_sha256": result.get("compressed_sha256"),
        "compress_time_s": result.get("compress_time_s"),
        "decompress_time_s": result.get("decompress_time_s"),
    }
    if guard is not None and guard_path is not None:
        record.update(guard_record(guard, guard_path))
    return record


def guard_only_record(
    guard: dict[str, Any],
    guard_path: pathlib.Path,
    scope: int | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "guard_path": rel(guard_path),
        "data_size": scope,
        "roundtrip_ok": False,
        "determinism": False,
    }
    record.update(guard_record(guard, guard_path))
    max_rss = guard.get("max_sampled_single_rss_kib")
    limit = guard.get("limit_kib")
    if isinstance(max_rss, int) and isinstance(limit, int):
        record["single_rss_over_ceiling_kib"] = max_rss - limit
    if isinstance(guard.get("failure"), str):
        record["failure"] = guard["failure"]
    elif guard.get("rss_guard_exceeded") is True:
        record["failure"] = "compression_rss_crossed_local_guard_before_archive_or_roundtrip"
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("program_id")
    parser.add_argument("--result", type=pathlib.Path)
    parser.add_argument("--guard-json", type=pathlib.Path)
    parser.add_argument("--guard-only", action="store_true")
    parser.add_argument("--scope", type=int)
    parser.add_argument("--label", required=True)
    parser.add_argument("--status")
    parser.add_argument("--verdict")
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="append a note string to the recorded result",
    )
    args = parser.parse_args()

    meta_path = PROGRAMS / args.program_id / "meta.json"
    if not meta_path.exists():
        raise SystemExit(f"missing meta.json: {rel(meta_path)}")
    guard = None
    guard_path = args.guard_json
    if guard_path is not None:
        if not guard_path.exists():
            raise SystemExit(f"missing guard JSON: {guard_path}")
        guard = load_json(guard_path)
    if args.guard_only:
        if guard is None or guard_path is None:
            raise SystemExit("--guard-only requires --guard-json")
        result_path = None
        result = None
    else:
        result_path = args.result or latest_result(args.program_id)
        if not result_path.exists():
            raise SystemExit(f"missing result JSON: {result_path}")
        result = load_json(result_path)

    meta = load_json(meta_path)
    if not isinstance(meta, dict):
        raise SystemExit(f"invalid meta shape: {rel(meta_path)}")
    if result is not None and not isinstance(result, dict):
        raise SystemExit(f"invalid result shape: {result_path}")
    if result is not None and result.get("program_id") != args.program_id:
        raise SystemExit(
            f"result program_id {result.get('program_id')!r} does not match {args.program_id!r}"
        )

    measured = meta.setdefault("measured", {})
    if not isinstance(measured, dict):
        measured = {}
        meta["measured"] = measured
    if args.guard_only:
        record = guard_only_record(guard, guard_path, args.scope)
    else:
        record = result_record(result, result_path, guard, guard_path)
    if args.note:
        record["notes"] = args.note
    measured[args.label] = record
    if result_path is not None:
        meta["latest_result"] = rel(result_path)
    if args.status:
        meta["status"] = args.status
    if args.verdict:
        meta["verdict"] = args.verdict

    write_json(meta_path, meta)
    print(
        json.dumps(
            {
                "meta": rel(meta_path),
                "label": args.label,
                "result": rel(result_path) if result_path is not None else None,
                "guard": rel(guard_path) if guard_path is not None else None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
