#!/usr/bin/env python3
"""Run the exact MIXREGRET-CERT closure audit on the native paired trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_suffix(".cpp")
DEFAULT_INPUT_ROOT = Path(
    "/home/clocksmith/enwiki9-nonproof/results/endpoint428_title_1m_v1"
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pair-trace",
        type=Path,
        default=DEFAULT_INPUT_ROOT / "endpoint428_pair_trace.bin",
    )
    parser.add_argument(
        "--baseline-payload",
        type=Path,
        default=DEFAULT_INPUT_ROOT / "baseline.payload",
    )
    parser.add_argument(
        "--final-p1",
        type=Path,
        default=DEFAULT_INPUT_ROOT / "endpoint428.p1",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=DEFAULT_INPUT_ROOT / "input.wrt.store",
    )
    parser.add_argument("--raw-scope", type=int, default=1_000_000)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results/mixregret_pair_closure_v1/receipt.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in (
        args.pair_trace,
        args.baseline_payload,
        args.final_p1,
        args.wrt_store,
        SOURCE,
    ):
        if not path.is_file():
            raise SystemExit(f"missing required input: {path}")
    with tempfile.TemporaryDirectory(prefix="mixregret-pair-") as directory:
        binary = Path(directory) / "mixregret"
        subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-pedantic",
                str(SOURCE),
                "-o",
                str(binary),
            ],
            check=True,
        )
        completed = subprocess.run(
            [
                str(binary),
                str(args.pair_trace),
                str(args.final_p1),
                str(args.wrt_store),
                str(args.baseline_payload.stat().st_size),
                str(args.raw_scope),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
    receipt = json.loads(completed.stdout)
    receipt["proposal_id"] = "mixregret_pair_closure_v1"
    receipt["score_credit_bytes"] = 0
    receipt["claim_boundary"] = (
        "This closes only routing among compact-base, endpoint428, and their "
        "native hybrid on the opening-1M paired trace. The unavailable full "
        "internal component vector remains untested."
    )
    receipt["inputs"] = {
        "pair_trace": artifact(args.pair_trace),
        "baseline_payload": artifact(args.baseline_payload),
        "final_p1": artifact(args.final_p1),
        "wrt_store": artifact(args.wrt_store),
    }
    receipt["implementation"] = {
        "source": artifact(SOURCE),
        "wrapper": artifact(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "authorize_full_component_trace": receipt[
                    "authorize_full_component_trace"
                ],
                "baseline_identity": receipt["baseline_identity"],
                "decision": receipt["decision"],
                "null_adjusted_u0_saved_bytes": receipt[
                    "null_adjusted_u0_saved_bytes"
                ],
                "r1_net_saved_bytes_per_million": receipt["r1"][
                    "net_saved_bytes_per_million"
                ],
                "u0_saved_bytes": receipt["u0_saved_bytes"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
