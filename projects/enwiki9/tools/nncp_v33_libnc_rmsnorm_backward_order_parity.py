#!/usr/bin/env python3
"""Identify LibNC RMSNorm backward operation order from direct gradients."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import torch

import nncp_v33_libnc_rmsnorm_backward_parity as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_rmsnorm_backward_order_parity_v1"
THRESHOLD = 1e-7


class OutputOrderRMSNorm(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value: torch.Tensor) -> torch.Tensor:
        inverse = torch.rsqrt(
            value.square().mean(dim=-1, keepdim=True) + parent.EPSILON
        )
        output = value * inverse
        ctx.save_for_backward(inverse, output)
        return output

    @staticmethod
    def backward(ctx, gradient: torch.Tensor) -> torch.Tensor:
        inverse, output = ctx.saved_tensors
        return inverse * (
            gradient
            - output
            * (gradient * output).mean(dim=-1, keepdim=True)
        )


class DividedOrderRMSNorm(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value: torch.Tensor) -> torch.Tensor:
        mean_square = value.square().mean(dim=-1, keepdim=True)
        inverse = torch.rsqrt(mean_square + parent.EPSILON)
        ctx.save_for_backward(value, inverse, mean_square)
        return value * inverse

    @staticmethod
    def backward(ctx, gradient: torch.Tensor) -> torch.Tensor:
        value, inverse, mean_square = ctx.saved_tensors
        return inverse * (
            gradient
            - value
            * (gradient * value).mean(dim=-1, keepdim=True)
            / (mean_square + parent.EPSILON)
        )


def current_autograd(value: torch.Tensor) -> torch.Tensor:
    return value * torch.rsqrt(
        value.square().mean(dim=-1, keepdim=True) + parent.EPSILON
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--libnc-root",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05"),
    )
    parser.add_argument(
        "--probe-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_rmsnorm_probe.c",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()
    libnc_root = args.libnc_root.resolve()
    probe_source = args.probe_source.resolve()
    header = libnc_root / "libnc.h"
    library = libnc_root / "libnc.so"
    if not all(path.is_file() for path in (probe_source, header, library)):
        raise SystemExit("missing probe source, LibNC header, or LibNC library")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-rms-order-") as temp:
        executable = Path(temp) / "probe"
        command = [
            os.environ.get("CC", "cc"),
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            f"-I{libnc_root}",
            str(probe_source),
            f"-L{libnc_root}",
            f"-Wl,-rpath,{libnc_root}",
            "-lnc",
            "-lm",
            "-ldl",
            "-lpthread",
            "-o",
            str(executable),
        ]
        compiled = subprocess.run(
            command, check=True, capture_output=True, text=True
        )
        first = subprocess.run([str(executable)], check=True, capture_output=True)
        second = subprocess.run([str(executable)], check=True, capture_output=True)
        repeated = first.stdout == second.stdout
        rows = json.loads(first.stdout)["rows"]
        comparisons = {
            "current_pytorch_autograd": parent.compare(rows, current_autograd),
            "libnc_output_order_backward": parent.compare(
                rows, OutputOrderRMSNorm.apply
            ),
            "divided_closed_form_backward": parent.compare(
                rows, DividedOrderRMSNorm.apply
            ),
        }
        matches = [
            name
            for name, metrics in comparisons.items()
            if metrics["maximum_absolute_forward_error"] <= THRESHOLD
            and metrics["maximum_absolute_gradient_error"] <= THRESHOLD
        ]
        passed = repeated and matches == ["libnc_output_order_backward"]
        result = {
            "schema": "gamma.nncp_v33_libnc_rmsnorm_backward_order_parity.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "PASS" if passed else "REJECT",
            "score_credit_bytes": 0,
            "inputs": {
                "probe_source_sha256": parent.sha256(probe_source),
                "libnc_header_sha256": parent.sha256(header),
                "libnc_library_sha256": parent.sha256(library),
                "script_sha256": parent.sha256(Path(__file__).resolve()),
            },
            "compile": {
                "command": command,
                "stderr": compiled.stderr,
                "executable_sha256": parent.sha256(executable),
            },
            "probe": {
                "rows": len(rows),
                "repeat_byte_identical": repeated,
                "stdout_sha256": hashlib.sha256(first.stdout).hexdigest(),
            },
            "comparisons": comparisons,
            "gate": {
                "maximum_absolute_error": THRESHOLD,
                "matching_contracts": matches,
            },
            "decision": {
                "promotion_authorized": passed,
                "authorized_next_action": (
                    "run one tanh-GELU plus LibNC-order RMSNorm bound update"
                    if passed
                    else "retire the RMSNorm operation-order hypothesis"
                ),
                "forecast_bytes": 109389323,
                "verified_full_1g_score_bytes": None,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
