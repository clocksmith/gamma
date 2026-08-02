#!/usr/bin/env python3
"""Probe LibNC GELU values/gradients and compare frozen PyTorch contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def comparison_metrics(
    rows: list[dict[str, float]], x: torch.Tensor, y: torch.Tensor
) -> dict[str, float]:
    y.sum().backward()
    reference_y = torch.tensor([row["y"] for row in rows], dtype=torch.float32)
    reference_dy = torch.tensor([row["dy"] for row in rows], dtype=torch.float32)
    value_error = (y.detach() - reference_y).abs()
    gradient_error = (x.grad - reference_dy).abs()
    gradient_scale = reference_dy.abs().clamp_min(1e-12)
    return {
        "maximum_absolute_forward_error": float(value_error.max()),
        "maximum_absolute_gradient_error": float(gradient_error.max()),
        "maximum_relative_gradient_error": float(
            (gradient_error / gradient_scale).max()
        ),
        "mean_absolute_forward_error": float(value_error.mean()),
        "mean_absolute_gradient_error": float(gradient_error.mean()),
    }


def compare(rows: list[dict[str, float]], approximation: str) -> dict[str, float]:
    x = torch.tensor([row["x"] for row in rows], dtype=torch.float32)
    x.requires_grad_(True)
    y = F.gelu(x, approximate=approximation)
    return comparison_metrics(rows, x, y)


def compare_libnc_tanh_formula(rows: list[dict[str, float]]) -> dict[str, float]:
    """Use LibNC's unfused F32 operation order and positive-tail saturation."""
    x = torch.tensor([row["x"] for row in rows], dtype=torch.float32)
    x.requires_grad_(True)
    half = torch.tensor(0.5, dtype=torch.float32)
    one = torch.tensor(1.0, dtype=torch.float32)
    cubic = torch.tensor(0.044715, dtype=torch.float32)
    scale = torch.sqrt(torch.tensor(2.0 / math.pi, dtype=torch.float32))
    argument = scale * (x + cubic * x * x * x)
    tanh_value = torch.tanh(argument)
    tanh_value = torch.where(
        argument >= torch.tensor(8.0, dtype=torch.float32), one, tanh_value
    )
    y = half * x * (one + tanh_value)
    return comparison_metrics(rows, x, y)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--libnc-root",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05"),
    )
    parser.add_argument(
        "--probe-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_activation_probe.c",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_activation_backward_parity_v1/decision.json",
    )
    args = parser.parse_args()
    libnc_root = args.libnc_root.resolve()
    probe_source = args.probe_source.resolve()
    header = libnc_root / "libnc.h"
    library = libnc_root / "libnc.so"
    if not all(path.is_file() for path in (probe_source, header, library)):
        raise SystemExit("missing probe source, LibNC header, or LibNC library")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-activation-") as temp:
        executable = Path(temp) / "probe"
        compile_command = [
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
        compile_result = subprocess.run(
            compile_command, check=True, capture_output=True, text=True
        )
        first = subprocess.run(
            [str(executable)], check=True, capture_output=True
        )
        second = subprocess.run(
            [str(executable)], check=True, capture_output=True
        )
        repeated = first.stdout == second.stdout
        probe = json.loads(first.stdout)
        result = {
            "schema": "gamma.nncp_v33_libnc_activation_backward_parity.v1",
            "candidate_id": "nncp_v33_libnc_activation_backward_parity_v1",
            "status": "PASS" if repeated else "BROKEN_REPEAT",
            "score_credit_bytes": 0,
            "inputs": {
                "probe_source": {
                    "path": str(probe_source),
                    "sha256": sha256(probe_source),
                },
                "libnc_header": {
                    "path": str(header),
                    "sha256": sha256(header),
                },
                "libnc_library": {
                    "path": str(library),
                    "sha256": sha256(library),
                },
            },
            "compile": {
                "command": compile_command,
                "stderr": compile_result.stderr,
                "executable_sha256": sha256(executable),
            },
            "probe": {
                "rows": len(probe["rows"]),
                "stdout_sha256": hashlib.sha256(first.stdout).hexdigest(),
                "repeat_stdout_sha256": hashlib.sha256(second.stdout).hexdigest(),
                "repeat_byte_identical": repeated,
            },
            "comparisons": {
                "pytorch_exact_erf": compare(probe["rows"], "none"),
                "pytorch_tanh_approximation": compare(probe["rows"], "tanh"),
                "libnc_unfused_f32_tanh_formula": compare_libnc_tanh_formula(
                    probe["rows"]
                ),
            },
            "gate": {
                "maximum_absolute_gradient_error": 2e-6,
                "matching_contract": None,
            },
            "decision": {
                "promotion_authorized": False,
                "authorized_next_action": "retire GELU backward as the cause",
                "verified_full_1g_score_bytes": None,
                "forecast_bytes": 109389323,
            },
        }
        matches = [
            name
            for name, metrics in result["comparisons"].items()
            if metrics["maximum_absolute_gradient_error"] <= 2e-6
        ]
        if repeated and len(matches) == 1:
            result["gate"]["matching_contract"] = matches[0]
            result["decision"]["promotion_authorized"] = True
            result["decision"]["authorized_next_action"] = (
                "run one corrected bound miniature full-gradient replay"
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if repeated else 1


if __name__ == "__main__":
    raise SystemExit(main())
