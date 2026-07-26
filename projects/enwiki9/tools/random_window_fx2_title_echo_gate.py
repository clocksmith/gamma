#!/usr/bin/env python3
"""Replay a frozen random-window transform through the native FX2/WRT path.

This is a target-substrate transfer gate, not an official prefix benchmark.
The selected byte range must already exist in a frozen novelty-screen receipt.
Both the raw control and transformed candidate are compressed, decompressed,
and compressed a second time under the same RSS guard contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

import random_window_novelty_screen as novelty


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_CONFIRMATION = ROOT / "results" / "random_window_novelty_v1" / "confirmation.json"
DEFAULT_OUT = ROOT / "results" / "random_window_novelty_v1" / "fx2_native"
DEFAULT_GUARD = ROOT / "tools" / "run_with_rss_guard.py"
DECIMAL_10GB_KIB = 9_765_625
LOCAL_10GIB_KIB = 10_485_760
TARGET_GAIN_PER_MILLION = 700.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def select_window(receipt: dict[str, object], window_id: str) -> dict[str, object]:
    matches = [row for row in receipt["windows"] if row["window_id"] == window_id]
    if len(matches) != 1:
        raise ValueError(f"expected one frozen window named {window_id!r}, found {len(matches)}")
    return matches[0]


def read_guard(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def run_guarded_phase(
    *,
    name: str,
    command: list[str],
    work_dir: Path,
    guard_script: Path,
    guard_dir: Path,
    local_limit_kib: int,
    decimal_limit_kib: int,
) -> dict[str, object]:
    guard_path = guard_dir / f"{name}.guard.json"
    log_path = guard_dir / f"{name}.log"
    guard_path.unlink(missing_ok=True)
    started = time.time()
    guarded_command = [
        sys.executable,
        str(guard_script),
        "--limit-kib",
        str(local_limit_kib),
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        str(decimal_limit_kib),
        "--sample-interval",
        "0.25",
        "--guard-json",
        str(guard_path),
        "--label",
        name,
        "--",
        *command,
    ]
    with log_path.open("wb") as log:
        completed = subprocess.run(
            guarded_command,
            cwd=work_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "elapsed_s": round(time.time() - started, 6),
        "guard_path": str(guard_path),
        "guard": read_guard(guard_path),
        "log_path": str(log_path),
        "log_sha256": sha256_file(log_path),
    }


def render_markdown(receipt: dict[str, object]) -> str:
    result = receipt.get("result") or {}
    lines = [
        "# Random-Window FX2 Title-Echo Gate",
        "",
        f"- Window: `{receipt['window']['window_id']}`",
        f"- Offset: `{receipt['window']['offset']}`",
        f"- Scope bytes: `{receipt['window']['window_size']}`",
        f"- Status: `{receipt['status']}`",
        f"- FX2 source commit: `{receipt['fx2']['source_commit']}`",
        f"- FX2 binary SHA-256: `{receipt['fx2']['binary_sha256']}`",
        "- Backend path: native FX2 `-c`/`-d` with WRT dictionary preprocessing.",
        "- Claim boundary: an arbitrary-window target-substrate result is not an official prefix score or a 10.80% proof.",
        "",
    ]
    if result:
        lines.extend(
            [
                "## Result",
                "",
                f"- Raw archive: `{result['identity_archive_bytes']}` bytes",
                f"- Title-echo archive: `{result['candidate_archive_bytes']}` bytes",
                f"- Candidate delta: `{result['archive_delta_vs_identity']:+d}` bytes",
                f"- Gross gain: `{result['gross_gain_bytes_per_million']:.3f}` B/1M",
                f"- Transform size delta: `{result['transformed_delta_bytes']:+d}` bytes",
                f"- Raw roundtrip: `{str(result['identity_roundtrip_ok']).lower()}`",
                f"- Candidate roundtrip: `{str(result['candidate_roundtrip_ok']).lower()}`",
                f"- Raw deterministic archive: `{str(result['identity_deterministic']).lower()}`",
                f"- Candidate deterministic archive: `{str(result['candidate_deterministic']).lower()}`",
                f"- Verdict: `{result['verdict']}`",
                "",
            ]
        )
    if receipt.get("failure"):
        lines.extend(["## Failure", "", f"`{receipt['failure']}`", ""])
    lines.extend(
        [
            "## Guarded Phases",
            "",
            "| Phase | Return | Peak single RSS KiB | Guard status |",
            "|---|---:|---:|---|",
        ]
    )
    for phase in receipt["phases"]:
        guard = phase.get("guard") or {}
        lines.append(
            f"| `{phase['name']}` | {phase['returncode']} | "
            f"{guard.get('max_sampled_single_rss_kib', 'n/a')} | "
            f"`{guard.get('status', 'missing')}` |"
        )
    lines.append("")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    confirmation = json.loads(args.confirmation.read_text())
    window = select_window(confirmation, args.window_id)
    transform_tool_sha = sha256_file(Path(novelty.__file__))
    if transform_tool_sha != confirmation["tool_sha256"]:
        raise ValueError("frozen confirmation tool hash does not match the current transform source")
    if args.data.stat().st_size != confirmation["corpus_bytes"]:
        raise ValueError("corpus size does not match the frozen confirmation receipt")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = args.out_dir / args.window_id
    work_dir.mkdir(parents=True, exist_ok=True)
    guard_dir = work_dir / "phases"
    guard_dir.mkdir(parents=True, exist_ok=True)

    offset = int(window["offset"])
    window_size = int(window["window_size"])
    with args.data.open("rb") as corpus:
        corpus.seek(offset)
        raw = corpus.read(window_size)
    if len(raw) != window_size:
        raise ValueError("short corpus read")
    raw_sha = hashlib.sha256(raw).hexdigest()
    if raw_sha != window["sha256"]:
        raise ValueError("window bytes do not match the frozen confirmation receipt")

    transformed = novelty.title_echo_encode(raw)
    transform_roundtrip_ok = novelty.title_echo_decode(transformed) == raw
    transform_deterministic = novelty.title_echo_encode(raw) == transformed
    if not transform_roundtrip_ok or not transform_deterministic:
        raise ValueError("title-echo transform failed before native replay")

    raw_path = work_dir / "identity.input"
    transformed_path = work_dir / "title_echo.input"
    raw_path.write_bytes(raw)
    transformed_path.write_bytes(transformed)

    identity_a = work_dir / "identity.a.cmix"
    identity_b = work_dir / "identity.b.cmix"
    candidate_a = work_dir / "title_echo.a.cmix"
    candidate_b = work_dir / "title_echo.b.cmix"
    identity_restored = work_dir / "identity.restored"
    candidate_restored = work_dir / "title_echo.restored"
    for path in (
        identity_a,
        identity_b,
        candidate_a,
        candidate_b,
        identity_restored,
        candidate_restored,
    ):
        path.unlink(missing_ok=True)

    cmix = str(args.cmix.resolve())
    dictionary = str(args.dictionary.resolve())
    phases: list[dict[str, object]] = []
    plan = [
        ("identity_compress_a", [cmix, "-c", dictionary, str(raw_path.resolve()), str(identity_a.resolve())]),
        ("candidate_compress_a", [cmix, "-c", dictionary, str(transformed_path.resolve()), str(candidate_a.resolve())]),
        ("identity_decompress", [cmix, "-d", dictionary, str(identity_a.resolve()), str(identity_restored.resolve())]),
        ("candidate_decompress", [cmix, "-d", dictionary, str(candidate_a.resolve()), str(candidate_restored.resolve())]),
        ("identity_compress_b", [cmix, "-c", dictionary, str(raw_path.resolve()), str(identity_b.resolve())]),
        ("candidate_compress_b", [cmix, "-c", dictionary, str(transformed_path.resolve()), str(candidate_b.resolve())]),
    ]

    receipt: dict[str, object] = {
        "schema_version": 1,
        "mode": "random_window_fx2_wrt_native_transform_gate",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "running",
        "evidence_level": "target_substrate_random_window_roundtrip_and_determinism",
        "claim_boundary": "This arbitrary-window FX2/WRT comparison is not an official prefix score, a counted integration, or a 10.80% proof.",
        "promotion_boundary": "Positive disjoint native windows earn an integrated WRT-aware title endpoint with counted source; they do not earn a full-corpus gate.",
        "confirmation_receipt": {
            "path": str(args.confirmation),
            "sha256": sha256_file(args.confirmation),
            "tool_sha256": confirmation["tool_sha256"],
        },
        "gate_tool": {
            "path": str(Path(__file__)),
            "sha256": sha256_file(Path(__file__)),
        },
        "window": window,
        "corpus": {
            "path": str(args.data),
            "bytes": args.data.stat().st_size,
            "receipt_sha256": confirmation["corpus_sha256"],
            "window_sha256": raw_sha,
        },
        "algorithm": {
            "name": "title_echo",
            "transform_tool": str(Path(novelty.__file__)),
            "transform_tool_sha256": transform_tool_sha,
            "decoder_table_payload_bytes": 0,
            "integrated_source_cost_counted": False,
            "transform_roundtrip_ok": transform_roundtrip_ok,
            "transform_deterministic": transform_deterministic,
        },
        "fx2": {
            "source_commit": args.fx2_source_commit,
            "source_tree_sha256": args.fx2_source_tree_sha256,
            "source_diff_sha256": args.fx2_source_diff_sha256,
            "binary_path": str(args.cmix),
            "binary_bytes": args.cmix.stat().st_size,
            "binary_sha256": sha256_file(args.cmix),
            "dictionary_path": str(args.dictionary),
            "dictionary_bytes": args.dictionary.stat().st_size,
            "dictionary_sha256": sha256_file(args.dictionary),
            "build_contract": args.build_contract,
            "compiler": args.compiler,
            "wrt_preprocessing": True,
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "guard_contract": {
            "local_10gib_limit_kib": args.local_limit_kib,
            "official_decimal_10gb_limit_kib": args.decimal_limit_kib,
            "limit_mode": "max_single",
        },
        "phases": phases,
    }

    exit_code = 0
    for name, command in plan:
        phase = run_guarded_phase(
            name=name,
            command=command,
            work_dir=work_dir,
            guard_script=args.guard_script,
            guard_dir=guard_dir,
            local_limit_kib=args.local_limit_kib,
            decimal_limit_kib=args.decimal_limit_kib,
        )
        phases.append(phase)
        if phase["returncode"] != 0:
            receipt["status"] = "failed"
            receipt["failure"] = f"phase {name} returned {phase['returncode']}"
            exit_code = 1
            break

    if exit_code == 0:
        restored_candidate_bytes = candidate_restored.read_bytes()
        identity_roundtrip_ok = identity_restored.read_bytes() == raw
        candidate_roundtrip_ok = novelty.title_echo_decode(restored_candidate_bytes) == raw
        identity_deterministic = identity_a.read_bytes() == identity_b.read_bytes()
        candidate_deterministic = candidate_a.read_bytes() == candidate_b.read_bytes()
        identity_bytes = identity_a.stat().st_size
        candidate_bytes = candidate_a.stat().st_size
        delta = candidate_bytes - identity_bytes
        gain = -delta * 1_000_000 / window_size
        all_checks = (
            identity_roundtrip_ok
            and candidate_roundtrip_ok
            and identity_deterministic
            and candidate_deterministic
            and all((phase.get("guard") or {}).get("status") == "complete" for phase in phases)
        )
        if all_checks and gain >= TARGET_GAIN_PER_MILLION:
            verdict = "positive_native_transfer_needs_counted_integration"
        elif all_checks and delta < 0:
            verdict = "positive_but_below_economic_screen"
        elif all_checks:
            verdict = "negative_native_transfer"
        else:
            verdict = "invalid_native_replay"
            exit_code = 1
        receipt["status"] = "complete" if all_checks else "failed"
        receipt["result"] = {
            "identity_archive_bytes": identity_bytes,
            "candidate_archive_bytes": candidate_bytes,
            "archive_delta_vs_identity": delta,
            "gross_gain_bytes_per_million": round(gain, 6),
            "raw_input_bytes": len(raw),
            "transformed_input_bytes": len(transformed),
            "transformed_delta_bytes": len(transformed) - len(raw),
            "identity_archive_sha256": sha256_file(identity_a),
            "candidate_archive_sha256": sha256_file(candidate_a),
            "identity_roundtrip_ok": identity_roundtrip_ok,
            "candidate_roundtrip_ok": candidate_roundtrip_ok,
            "identity_deterministic": identity_deterministic,
            "candidate_deterministic": candidate_deterministic,
            "verdict": verdict,
        }

    return receipt, exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--confirmation", type=Path, default=DEFAULT_CONFIRMATION)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--cmix", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--fx2-source-commit", required=True)
    parser.add_argument("--fx2-source-tree-sha256", required=True)
    parser.add_argument("--fx2-source-diff-sha256", required=True)
    parser.add_argument("--build-contract", required=True)
    parser.add_argument("--compiler", required=True)
    parser.add_argument("--guard-script", type=Path, default=DEFAULT_GUARD)
    parser.add_argument("--local-limit-kib", type=int, default=LOCAL_10GIB_KIB)
    parser.add_argument("--decimal-limit-kib", type=int, default=DECIMAL_10GB_KIB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)
    for path, label in (
        (args.data, "corpus"),
        (args.confirmation, "confirmation receipt"),
        (args.cmix, "cmix binary"),
        (args.dictionary, "dictionary"),
        (args.guard_script, "RSS guard"),
    ):
        if not path.is_file():
            raise SystemExit(f"missing {label}: {path}")
    if args.local_limit_kib < args.decimal_limit_kib:
        raise SystemExit("local guard cannot be smaller than the decimal accounting guard")

    json_out = args.json_out or args.out_dir / f"{args.window_id}.json"
    md_out = args.md_out or args.out_dir / f"{args.window_id}.md"
    try:
        receipt, exit_code = run(args)
    except Exception as exc:
        raise SystemExit(f"native gate setup failed: {exc}") from exc
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    md_out.write_text(render_markdown(receipt))
    print(json.dumps(receipt.get("result", {"status": receipt["status"]}), indent=2))
    print(f"wrote {json_out}")
    print(f"wrote {md_out}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
