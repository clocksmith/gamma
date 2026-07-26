#!/usr/bin/env python3
"""Emit SRSTC-on-fx2 residual-trace shadow commands.

This tool does not run a compressor. It turns an existing `FX2_RESIDUAL_ROW`
stderr log, or an `fx2_residual_probe.py` manifest that points at one, into a
small command queue for `streaming_retrieval_shadow.py`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT_DIR = ROOT / "results" / "streaming_retrieval_shadow"


@dataclass(frozen=True)
class QueueProfile:
    name: str
    feature_source: str
    typed_key_profile: str
    expert_mode: str
    blend_ppm: int
    min_support: int = 8
    partial_byte_family: str = "sketch"
    table_cap_entries: int = 200_000
    byte_table_cap_entries: int = 100_000


PROFILES = (
    QueueProfile(
        name="row_base_aggregate_b20000",
        feature_source="row",
        typed_key_profile="base",
        expert_mode="aggregate",
        blend_ppm=20_000,
    ),
    QueueProfile(
        name="row_rich_aggregate_b20000",
        feature_source="row",
        typed_key_profile="rich",
        expert_mode="aggregate",
        blend_ppm=20_000,
    ),
    QueueProfile(
        name="row_rich_best_abstain_b20000",
        feature_source="row",
        typed_key_profile="rich",
        expert_mode="best_band_abstain",
        blend_ppm=20_000,
    ),
    QueueProfile(
        name="row_richpos_aggregate_b20000",
        feature_source="row",
        typed_key_profile="richpos",
        expert_mode="aggregate",
        blend_ppm=20_000,
    ),
)


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"manifest is not a JSON object: {path}")
    return data


def log_from_manifest(path: pathlib.Path) -> pathlib.Path:
    manifest = load_manifest(path)
    logs = manifest.get("logs")
    if not isinstance(logs, dict):
        raise SystemExit(f"manifest has no logs object: {path}")
    stderr = logs.get("stderr")
    if not isinstance(stderr, str) or not stderr:
        raise SystemExit(f"manifest has no logs.stderr path: {path}")
    log_path = pathlib.Path(stderr)
    if not log_path.is_absolute():
        log_path = (path.parent / log_path).resolve()
    return log_path


def output_path(out_dir: pathlib.Path, label: str, profile: QueueProfile) -> pathlib.Path:
    safe_label = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in label)
    return out_dir / f"{safe_label}_{profile.name}.json"


def command_for(
    *,
    log_path: pathlib.Path,
    data_path: pathlib.Path,
    out_path: pathlib.Path,
    profile: QueueProfile,
    data_limit: int,
    max_rows: int,
    train_bytes: int,
    code_bytes: int,
    scope_bytes: int,
    baseline_score: int,
    target_score: int,
) -> list[str]:
    cmd = [
        "python3",
        "projects/enwiki9/tools/streaming_retrieval_shadow.py",
        str(log_path),
        "--data",
        str(data_path),
        "--output",
        str(out_path),
        "--feature-source",
        profile.feature_source,
        "--typed-key-profile",
        profile.typed_key_profile,
        "--expert-mode",
        profile.expert_mode,
        "--blend-ppm",
        str(profile.blend_ppm),
        "--min-support",
        str(profile.min_support),
        "--partial-byte-family",
        profile.partial_byte_family,
        "--table-cap-entries",
        str(profile.table_cap_entries),
        "--byte-table-cap-entries",
        str(profile.byte_table_cap_entries),
        "--train-bytes",
        str(train_bytes),
        "--added-code-bytes-estimate",
        str(code_bytes),
        "--added-static-table-bytes",
        "0",
        "--scope-bytes",
        str(scope_bytes),
        "--baseline-score",
        str(baseline_score),
        "--target-score",
        str(target_score),
        "--alignment-max-positions",
        "0",
        "--print-summary",
    ]
    if data_limit > 0:
        cmd.extend(["--data-limit", str(data_limit)])
    if max_rows > 0:
        cmd.extend(["--max-rows", str(max_rows)])
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print lock-safe SRSTC shadow commands for an fx2 residual log."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--log", type=pathlib.Path)
    source.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--data-limit", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--train-bytes", type=int, default=30_000)
    parser.add_argument("--code-bytes", type=int, default=12_288)
    parser.add_argument("--scope-bytes", type=int, default=1_000_000_000)
    parser.add_argument("--baseline-score", type=int, default=110_181_114)
    parser.add_argument("--target-score", type=int, default=108_000_000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.log is not None:
        log_path = args.log
    else:
        log_path = log_from_manifest(args.manifest)
    if not log_path.exists():
        raise SystemExit(f"missing fx2 residual log: {log_path}")
    if not args.data.exists():
        raise SystemExit(f"missing data file: {args.data}")
    if args.data_limit < 0 or args.max_rows < 0:
        raise SystemExit("--data-limit and --max-rows must be nonnegative")
    if args.train_bytes < 0:
        raise SystemExit("--train-bytes must be nonnegative")

    queue = []
    for profile in PROFILES:
        out_path = output_path(args.out_dir, args.label, profile)
        cmd = command_for(
            log_path=log_path,
            data_path=args.data,
            out_path=out_path,
            profile=profile,
            data_limit=args.data_limit,
            max_rows=args.max_rows,
            train_bytes=args.train_bytes,
            code_bytes=args.code_bytes,
            scope_bytes=args.scope_bytes,
            baseline_score=args.baseline_score,
            target_score=args.target_score,
        )
        queue.append(
            {
                "profile": profile.name,
                "output": str(out_path),
                "command": cmd,
                "shell": shell_join(cmd),
            }
        )

    payload = {
        "queue_type": "srstc_fx2_trace_shadow_queue",
        "lock_safety": "does_not_launch_compressor_reads_existing_fx2_residual_log",
        "label": args.label,
        "log": str(log_path),
        "data": str(args.data),
        "profiles": queue,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in queue:
            print(f"# {item['profile']}")
            print(item["shell"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
