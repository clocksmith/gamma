#!/usr/bin/env python3
"""Compare direct LibNC RMSNorm values and gradients with frozen contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Callable

import torch


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_rmsnorm_backward_parity_v1"
EPSILON = 1e-5
THRESHOLD = 2e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def compare(
    rows: list[dict[str, float]],
    contract: Callable[[torch.Tensor], torch.Tensor],
) -> dict[str, float]:
    columns = max(int(row["column"]) for row in rows) + 1
    features = max(int(row["feature"]) for row in rows) + 1
    x = torch.empty(columns, features, dtype=torch.float32)
    upstream = torch.empty_like(x)
    reference_y = torch.empty_like(x)
    reference_dx = torch.empty_like(x)
    for row in rows:
        column = int(row["column"])
        feature = int(row["feature"])
        x[column, feature] = row["x"]
        upstream[column, feature] = row["upstream"]
        reference_y[column, feature] = row["y"]
        reference_dx[column, feature] = row["dx"]
    x.requires_grad_(True)
    y = contract(x)
    (y * upstream).sum().backward()
    forward_error = (y.detach() - reference_y).abs()
    gradient_error = (x.grad - reference_dx).abs()
    gradient_scale = reference_dx.abs().clamp_min(1e-12)
    return {
        "maximum_absolute_forward_error": float(forward_error.max()),
        "maximum_absolute_gradient_error": float(gradient_error.max()),
        "maximum_relative_gradient_error": float(
            (gradient_error / gradient_scale).max()
        ),
        "mean_absolute_forward_error": float(forward_error.mean()),
        "mean_absolute_gradient_error": float(gradient_error.mean()),
    }


def mean_eps_inside_sqrt(value: torch.Tensor) -> torch.Tensor:
    return value * torch.rsqrt(
        value.square().mean(dim=-1, keepdim=True) + EPSILON
    )


def mean_eps_outside_sqrt(value: torch.Tensor) -> torch.Tensor:
    return value / (
        torch.sqrt(value.square().mean(dim=-1, keepdim=True)) + EPSILON
    )


def sum_eps_rescaled(value: torch.Tensor) -> torch.Tensor:
    return value * math.sqrt(value.shape[-1]) * torch.rsqrt(
        value.square().sum(dim=-1, keepdim=True) + EPSILON
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

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-rmsnorm-") as temp:
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
        probe = json.loads(first.stdout)
        contracts = {
            "mean_eps_inside_sqrt": mean_eps_inside_sqrt,
            "mean_eps_outside_sqrt": mean_eps_outside_sqrt,
            "sum_eps_rescaled": sum_eps_rescaled,
        }
        comparisons = {
            name: compare(probe["rows"], contract)
            for name, contract in contracts.items()
        }
        matches = [
            name
            for name, metrics in comparisons.items()
            if metrics["maximum_absolute_forward_error"] <= THRESHOLD
            and metrics["maximum_absolute_gradient_error"] <= THRESHOLD
        ]
        current_matches = matches == ["mean_eps_inside_sqrt"]
        corrected_matches = len(matches) == 1 and not current_matches
        status = (
            "REJECT_RMSNORM_CAUSE"
            if current_matches
            else "AUTHORIZED_CORRECTED_UPDATE"
            if corrected_matches
            else "UNRESOLVED_CONTRACT"
        )
        result = {
            "schema": "gamma.nncp_v33_libnc_rmsnorm_backward_parity.v1",
            "candidate_id": CANDIDATE_ID,
            "status": status if repeated else "BROKEN_REPEAT",
            "score_credit_bytes": 0,
            "inputs": {
                "probe_source_sha256": sha256(probe_source),
                "libnc_header_sha256": sha256(header),
                "libnc_library_sha256": sha256(library),
                "script_sha256": sha256(Path(__file__).resolve()),
            },
            "compile": {
                "command": command,
                "stderr": compiled.stderr,
                "executable_sha256": sha256(executable),
            },
            "probe": {
                "rows": len(probe["rows"]),
                "stdout_sha256": hashlib.sha256(first.stdout).hexdigest(),
                "repeat_stdout_sha256": hashlib.sha256(second.stdout).hexdigest(),
                "repeat_byte_identical": repeated,
            },
            "comparisons": comparisons,
            "gate": {
                "maximum_absolute_error": THRESHOLD,
                "matching_contracts": matches,
                "current_contract_matches_uniquely": current_matches,
            },
            "decision": {
                "promotion_authorized": corrected_matches and repeated,
                "authorized_next_action": (
                    "run one corrected bound miniature full-update replay"
                    if corrected_matches
                    else "retire RMSNorm backward as the remaining cause"
                    if current_matches
                    else "localize LibNC RMSNorm operation order"
                ),
                "forecast_bytes": 109389323,
                "verified_full_1g_score_bytes": None,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if repeated else 1


if __name__ == "__main__":
    raise SystemExit(main())
