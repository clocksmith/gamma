#!/usr/bin/env python3
"""Record one driver result JSON into a candidate meta.json file."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
RESULTS = ROOT / "results"


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


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


def result_record(result: dict[str, Any], result_path: pathlib.Path) -> dict[str, Any]:
    return {
        "result_path": rel(result_path),
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("program_id")
    parser.add_argument("--result", type=pathlib.Path)
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
    result_path = args.result or latest_result(args.program_id)
    if not result_path.exists():
        raise SystemExit(f"missing result JSON: {result_path}")

    meta = load_json(meta_path)
    result = load_json(result_path)
    if not isinstance(meta, dict):
        raise SystemExit(f"invalid meta shape: {rel(meta_path)}")
    if not isinstance(result, dict):
        raise SystemExit(f"invalid result shape: {result_path}")
    if result.get("program_id") != args.program_id:
        raise SystemExit(
            f"result program_id {result.get('program_id')!r} does not match {args.program_id!r}"
        )

    measured = meta.setdefault("measured", {})
    if not isinstance(measured, dict):
        measured = {}
        meta["measured"] = measured
    record = result_record(result, result_path)
    if args.note:
        record["notes"] = args.note
    measured[args.label] = record
    meta["latest_result"] = rel(result_path)
    if args.status:
        meta["status"] = args.status
    if args.verdict:
        meta["verdict"] = args.verdict

    write_json(meta_path, meta)
    print(json.dumps({"meta": rel(meta_path), "label": args.label, "result": rel(result_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
