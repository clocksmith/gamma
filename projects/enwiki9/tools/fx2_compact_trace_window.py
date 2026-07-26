#!/usr/bin/env python3
"""Run a frozen random window through compact FX2 probability tracing."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

import wrt_title_token_automaton as automaton


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_WINDOWS = ROOT / "results" / "random_window_novelty_v1" / "selection.json"
DEFAULT_OUT = (
    ROOT
    / "results"
    / "random_window_novelty_v1"
    / "wrt_title_token_automaton_v1"
)
DEFAULT_DICTIONARY = ROOT / "external" / "fx2-cmix" / "dictionary" / "english.dic"
DEFAULT_SOURCE_PATCH = ROOT / "external" / "fx2-cmix.local.patch"
DEFAULT_GUARD = ROOT / "tools" / "run_with_rss_guard.py"
HEAVY_LOCK = Path("/tmp/enwiki9-heavy.lock")
LOCAL_10GIB_KIB = 10_485_760
DECIMAL_10GB_KIB = 9_765_625


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def select_window(receipt: dict[str, object], window_id: str) -> dict[str, object]:
    matches = [window for window in receipt["windows"] if window["window_id"] == window_id]
    if len(matches) != 1:
        raise ValueError(f"expected one frozen window named {window_id!r}, found {len(matches)}")
    return matches[0]


def run_logged(
    command: list[str],
    *,
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    started = time.time()
    with log_path.open("wb") as log:
        completed = subprocess.run(
            command,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            check=False,
        )
    completed.elapsed_s = round(time.time() - started, 6)  # type: ignore[attr-defined]
    return completed


def read_guard(path: Path) -> dict[str, object] | None:
    return json.loads(path.read_text()) if path.exists() else None


def render_markdown(receipt: dict[str, object]) -> str:
    shadow = receipt.get("shadow") or {}
    best = shadow.get("best") or {}
    control = shadow.get("best_control") or {}
    validation = shadow.get("validations") or {}
    archive_validation = validation.get("archive") or {}
    store_validation = validation.get("wrt_store") or {}
    return "\n".join(
        [
            "# FX2 Compact Title-Token Trace",
            "",
            f"- Window: `{receipt['window']['window_id']}`",
            f"- Phase: `{receipt['phase']}`",
            f"- Substrate: `{receipt['shadow']['substrate']['id']}`",
            f"- State contract: `{receipt['shadow']['substrate']['state_contract']}`",
            f"- Raw scope: `{receipt['window']['window_size']}` bytes",
            f"- WRT bytes: `{receipt['trace']['wrt_bytes']}`",
            f"- Archive bytes: `{receipt['archive']['bytes']}`",
            f"- Guard status: `{receipt['guard']['status']}`",
            f"- Peak single RSS: `{receipt['guard']['max_sampled_single_rss_kib']}` KiB",
            f"- Trace/store identity: `{str(store_validation.get('trace_matches_store')).lower()}`",
            f"- Baseline range identity: `{str(archive_validation.get('baseline_range_match')).lower()}`",
            f"- Best current-title variant: `{best.get('variant_id', 'n/a')}`",
            f"- Current-title qbit gain: `{best.get('qbit_gain_bytes_per_million', 'n/a')}` B/1M",
            f"- Current-title exact saved bytes: `{(best.get('exact') or {}).get('saved_bytes', 'n/a')}`",
            f"- Best future-label byte oracle: `{(receipt['shadow'].get('best_positive_byte_oracle') or {}).get('positive_byte_oracle_bytes_per_million', 'n/a')}` B/1M",
            f"- Best previous-title control: `{control.get('variant_id', 'n/a')}`",
            f"- Previous-title control qbit gain: `{control.get('qbit_gain_bytes_per_million', 'n/a')}` B/1M",
            f"- Verdict: `{receipt['verdict']}`",
            "",
            "This arbitrary-window compact trace is causal shadow evidence. It is not",
            "integrated source, a native candidate archive, an official prefix result,",
            "or a `10.80%` proof.",
            "",
        ]
    )


def run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    frozen = json.loads(args.windows_receipt.read_text())
    window = select_window(frozen, args.window_id)
    if args.data.stat().st_size != int(frozen["corpus_bytes"]):
        raise ValueError("corpus size does not match the frozen window receipt")
    offset = int(window["offset"])
    scope = int(window["window_size"])
    with args.data.open("rb") as corpus:
        corpus.seek(offset)
        raw = corpus.read(scope)
    if len(raw) != scope or hashlib.sha256(raw).hexdigest() != window["sha256"]:
        raise ValueError("frozen window bytes do not match their receipt")

    run_dir = args.out_dir / args.window_id
    run_dir.mkdir(parents=True, exist_ok=True)
    input_path = run_dir / "input.raw"
    store_path = run_dir / "input.wrt.store"
    archive_path = run_dir / "baseline.cmix"
    trace_path = run_dir / "probability.trace"
    guard_path = run_dir / "compression.guard.json"
    preprocess_log = run_dir / "preprocess.log"
    compression_log = run_dir / "compression.log"
    shadow_path = run_dir / "shadow.json"
    input_path.write_bytes(raw)
    for path in (store_path, archive_path, trace_path, guard_path, shadow_path):
        path.unlink(missing_ok=True)

    preprocess_command = [
        str(args.cmix),
        "-s",
        str(args.dictionary),
        str(input_path),
        str(store_path),
    ]
    preprocess = run_logged(
        preprocess_command,
        cwd=args.cmix.parent,
        log_path=preprocess_log,
    )
    if preprocess.returncode != 0:
        raise RuntimeError(f"FX2 preprocessing returned {preprocess.returncode}")

    guarded_command = [
        sys.executable,
        str(args.guard_script),
        "--limit-kib",
        str(args.local_limit_kib),
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        str(args.decimal_limit_kib),
        "--sample-interval",
        "0.25",
        "--guard-json",
        str(guard_path),
        "--label",
        f"fx2_title_trace_{args.window_id}",
        "--",
        str(args.cmix),
        "-c",
        str(args.dictionary),
        str(input_path),
        str(archive_path),
    ]
    trace_env = dict(os.environ)
    trace_env["FX2_COMPACT_PROB_TRACE_PATH"] = str(trace_path)
    lock_handle = HEAVY_LOCK.open("a+")
    try:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("enwiki9 heavy lock is held") from exc
        compression = run_logged(
            guarded_command,
            cwd=args.cmix.parent,
            log_path=compression_log,
            env=trace_env,
        )
    finally:
        lock_handle.close()
    guard = read_guard(guard_path)
    if compression.returncode != 0 or not guard or guard.get("status") != "complete":
        raise RuntimeError(
            f"guarded FX2 compression failed: return={compression.returncode} guard={guard}"
        )
    if not trace_path.is_file() or trace_path.read_bytes()[:8] != automaton.TRACE_MAGIC:
        raise RuntimeError("compact probability trace is missing or malformed")

    score_command = [
        sys.executable,
        str(Path(automaton.__file__).resolve()),
        "--trace",
        str(trace_path),
        "--dictionary",
        str(args.dictionary),
        "--scope-bytes",
        str(scope),
        "--archive",
        str(archive_path),
        "--wrt-store",
        str(store_path),
        "--raw-input",
        str(input_path),
        "--window-id",
        args.window_id,
        "--phase",
        args.phase,
        "--substrate-id",
        "raw_fx2",
        "--state-contract",
        "cold_reset_frozen_random_window",
        "--gross-floor-bpm",
        str(args.gross_floor_bpm),
        "--exact-top",
        str(args.exact_top),
        "--output",
        str(shadow_path),
    ]
    if args.variant_id:
        score_command.extend(("--variant-id", args.variant_id))
    score_log = run_dir / "score.log"
    score = run_logged(score_command, cwd=ROOT, log_path=score_log)
    if score.returncode != 0:
        raise RuntimeError(f"title-token scorer returned {score.returncode}")
    shadow = json.loads(shadow_path.read_text())
    archive_validation = shadow["validations"]["archive"]
    store_validation = shadow["validations"]["wrt_store"]
    if not (
        archive_validation["trace_wrt_bytes_match"]
        and archive_validation["baseline_range_match"]
        and store_validation["trace_matches_store"]
    ):
        raise RuntimeError("compact trace failed archive/store identity checks")

    best = shadow.get("best") or {}
    control = shadow.get("best_control") or {}
    exact = best.get("exact") or {}
    economic = (
        float(best.get("qbit_gain_bytes_per_million", 0)) > args.gross_floor_bpm
    )
    exact_positive = int(exact.get("saved_bytes", 0)) > 0
    control_lower = float(control.get("qbit_gain_bytes_per_million", 0)) < float(
        best.get("qbit_gain_bytes_per_million", 0)
    )
    if args.phase == "selection" and economic and exact_positive and control_lower:
        verdict = "additional_selection_windows_required"
    elif args.phase == "confirmation" and economic and exact_positive and control_lower:
        verdict = "positive_confirmation_needs_counted_native_integration"
    else:
        verdict = "insufficient_realizable_margin_at_this_window"

    trace_rows = (trace_path.stat().st_size - len(automaton.TRACE_MAGIC)) // automaton.TRACE_RECORD.size
    receipt: dict[str, object] = {
        "schema_version": 1,
        "receipt_type": "fx2_compact_random_window_trace",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evidence_level": "guarded_exact_fx2_probability_trace_shadow",
        "claim_boundary": (
            "This arbitrary-window trace is not integrated source, a native candidate "
            "archive, an official prefix result, or a 10.80% proof."
        ),
        "phase": args.phase,
        "window": window,
        "frozen_windows": {
            "path": str(args.windows_receipt),
            "sha256": sha256_file(args.windows_receipt),
        },
        "corpus": {
            "path": str(args.data),
            "bytes": args.data.stat().st_size,
            "sha256": frozen["corpus_sha256"],
            "window_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "source": {
            "base_commit": args.source_commit,
            "patch_path": str(args.source_patch),
            "patch_sha256": sha256_file(args.source_patch),
            "binary_path": str(args.cmix),
            "binary_bytes": args.cmix.stat().st_size,
            "binary_sha256": sha256_file(args.cmix),
            "dictionary_sha256": sha256_file(args.dictionary),
            "build_contract": args.build_contract,
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "trace": {
            "path": str(trace_path),
            "bytes": trace_path.stat().st_size,
            "sha256": sha256_file(trace_path),
            "rows": trace_rows,
            "wrt_bytes": trace_rows // 8,
        },
        "archive": {
            "path": str(archive_path),
            "bytes": archive_path.stat().st_size,
            "sha256": sha256_file(archive_path),
        },
        "wrt_store": {
            "path": str(store_path),
            "bytes": store_path.stat().st_size,
            "sha256": sha256_file(store_path),
        },
        "guard": guard,
        "shadow_path": str(shadow_path),
        "shadow_sha256": sha256_file(shadow_path),
        "shadow": {
            "best": best,
            "best_control": control,
            "best_positive_byte_oracle": shadow.get("best_positive_byte_oracle"),
            "substrate": shadow["substrate"],
            "economics": shadow["economics"],
            "diagnostics": shadow["diagnostics"],
            "validations": shadow["validations"],
        },
        "verdict": verdict,
        "next_action": (
            "Run additional frozen selection windows without changing the candidate grid."
            if verdict == "additional_selection_windows_required"
            else "Do not promote this window; inspect endpoint coverage and regressions."
        ),
    }
    return receipt, 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--windows-receipt", type=Path, default=DEFAULT_WINDOWS)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--phase", choices=("selection", "confirmation"), required=True)
    parser.add_argument("--variant-id")
    parser.add_argument("--cmix", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-patch", type=Path, default=DEFAULT_SOURCE_PATCH)
    parser.add_argument("--build-contract", required=True)
    parser.add_argument("--guard-script", type=Path, default=DEFAULT_GUARD)
    parser.add_argument("--local-limit-kib", type=int, default=LOCAL_10GIB_KIB)
    parser.add_argument("--decimal-limit-kib", type=int, default=DECIMAL_10GB_KIB)
    parser.add_argument("--exact-top", type=int, default=8)
    parser.add_argument("--gross-floor-bpm", type=float, default=700.0)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)
    for path in (
        args.data,
        args.windows_receipt,
        args.cmix,
        args.dictionary,
        args.source_patch,
        args.guard_script,
    ):
        if not path.is_file():
            raise SystemExit(f"missing required file: {path}")
    if args.local_limit_kib < args.decimal_limit_kib:
        raise SystemExit("binary guard cannot be smaller than decimal guard")
    if args.gross_floor_bpm < 0:
        raise SystemExit("gross floor cannot be negative")
    if args.phase == "confirmation" and not args.variant_id:
        raise SystemExit("confirmation requires a frozen --variant-id")

    try:
        receipt, exit_code = run(args)
    except Exception as exc:
        raise SystemExit(f"compact trace gate failed: {exc}") from exc
    json_out = args.json_out or args.out_dir / f"{args.window_id}.json"
    md_out = args.md_out or args.out_dir / f"{args.window_id}.md"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    md_out.write_text(render_markdown(receipt))
    print(json.dumps(receipt["shadow"]["best"], indent=2, sort_keys=True))
    print(f"wrote {json_out}")
    print(f"wrote {md_out}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
