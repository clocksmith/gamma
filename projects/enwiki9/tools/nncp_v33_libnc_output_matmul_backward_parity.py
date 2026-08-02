#!/usr/bin/env python3
"""Compare direct LibNC output-projection matmul gradients to frozen orders."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_output_matmul_backward_parity_v1"
OUTPUTS = 256
INPUTS = 32
COLUMNS = 4
THRESHOLD = 2e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    left = np.empty((OUTPUTS, INPUTS), dtype=np.float32)
    right = np.empty((INPUTS, COLUMNS), dtype=np.float32)
    upstream = np.empty((OUTPUTS, COLUMNS), dtype=np.float32)
    for column in range(INPUTS):
        for row in range(OUTPUTS):
            value = (row * 37 + column * 13) % 257 - 128
            left[row, column] = np.float32(value) / np.float32(257.0)
    for column in range(COLUMNS):
        for row in range(INPUTS):
            value = (row * 19 + column * 23) % 67 - 33
            right[row, column] = np.float32(value) / np.float32(41.0)
    for column in range(COLUMNS):
        total = np.float32(0.0)
        for row in range(OUTPUTS - 1):
            value = (row * 29 + column * 17) % 251 - 125
            item = np.float32(value) / np.float32(8192.0)
            upstream[row, column] = item
            total = np.float32(total + item)
        upstream[-1, column] = np.float32(-total)
    return left, right, upstream


def scalar_matmul(
    left: np.ndarray, right: np.ndarray, reverse: bool = False
) -> np.ndarray:
    rows, shared = left.shape
    columns = right.shape[1]
    result = np.empty((rows, columns), dtype=np.float32)
    order = range(shared - 1, -1, -1) if reverse else range(shared)
    for column in range(columns):
        for row in range(rows):
            total = np.float32(0.0)
            for index in order:
                total = np.float32(
                    total + np.float32(left[row, index] * right[index, column])
                )
            result[row, column] = total
    return result


def scalar_contract(
    left: np.ndarray,
    right: np.ndarray,
    upstream: np.ndarray,
    reverse: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    output = scalar_matmul(left, right, reverse)
    left_gradient = scalar_matmul(upstream, right.T, reverse)
    right_gradient = scalar_matmul(left.T, upstream, reverse)
    return output, left_gradient, right_gradient


def torch_contract(
    left: np.ndarray, right: np.ndarray, upstream: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    left_tensor = torch.tensor(left, dtype=torch.float32, requires_grad=True)
    right_tensor = torch.tensor(right, dtype=torch.float32, requires_grad=True)
    upstream_tensor = torch.tensor(upstream, dtype=torch.float32)
    output = left_tensor @ right_tensor
    (output * upstream_tensor).sum().backward()
    return (
        output.detach().numpy(),
        left_tensor.grad.detach().numpy(),
        right_tensor.grad.detach().numpy(),
    )


def metrics(
    reference: tuple[np.ndarray, np.ndarray, np.ndarray],
    candidate: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> dict[str, float]:
    labels = ("forward", "left_gradient", "right_gradient")
    result: dict[str, float] = {}
    for label, expected, actual in zip(labels, reference, candidate):
        difference = np.abs(expected - actual)
        result[f"maximum_absolute_{label}_error"] = float(difference.max())
        result[f"mean_absolute_{label}_error"] = float(difference.mean())
    return result


def aggregate_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in ("output.bin", "left_gradient.bin", "right_gradient.bin"):
        path = directory / name
        digest.update(name.encode("ascii") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


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
        default=ROOT / "tools/nncp_libnc_output_matmul_probe.c",
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
        raise SystemExit("missing probe source, LibNC header, or library")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-matmul-") as temp:
        temporary = Path(temp)
        executable = temporary / "probe"
        first_dir = temporary / "first"
        second_dir = temporary / "second"
        first_dir.mkdir()
        second_dir.mkdir()
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
        subprocess.run([str(executable), str(first_dir)], check=True)
        subprocess.run([str(executable), str(second_dir)], check=True)
        first_hash = aggregate_sha256(first_dir)
        second_hash = aggregate_sha256(second_dir)
        repeated = first_hash == second_hash
        reference = (
            np.fromfile(first_dir / "output.bin", dtype="<f4").reshape(
                (OUTPUTS, COLUMNS), order="F"
            ),
            np.fromfile(
                first_dir / "left_gradient.bin", dtype="<f4"
            ).reshape((OUTPUTS, INPUTS), order="F"),
            np.fromfile(
                first_dir / "right_gradient.bin", dtype="<f4"
            ).reshape((INPUTS, COLUMNS), order="F"),
        )
        left, right, upstream = fixture()
        comparisons = {
            "pytorch_native_matmul": metrics(
                reference, torch_contract(left, right, upstream)
            ),
            "scalar_shared_dimension_ascending": metrics(
                reference, scalar_contract(left, right, upstream)
            ),
            "scalar_shared_dimension_descending": metrics(
                reference,
                scalar_contract(left, right, upstream, reverse=True),
            ),
        }
        matches = [
            name
            for name, item in comparisons.items()
            if max(
                item["maximum_absolute_forward_error"],
                item["maximum_absolute_left_gradient_error"],
                item["maximum_absolute_right_gradient_error"],
            )
            <= THRESHOLD
        ]
        novel_match = repeated and len(matches) == 1 and matches != [
            "pytorch_native_matmul"
        ]
        result = {
            "schema": "gamma.nncp_v33_libnc_output_matmul_backward_parity.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "PASS" if novel_match else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "left_shape": [OUTPUTS, INPUTS],
                "right_shape": [INPUTS, COLUMNS],
                "threshold": THRESHOLD,
                "frozen_contracts": list(comparisons),
            },
            "inputs": {
                "probe_source_sha256": sha256(probe_source),
                "script_sha256": sha256(Path(__file__).resolve()),
                "libnc_header_sha256": sha256(header),
                "libnc_library_sha256": sha256(library),
            },
            "compile": {
                "command": command,
                "stderr": compiled.stderr,
                "executable_sha256": sha256(executable),
            },
            "probe": {
                "first_aggregate_sha256": first_hash,
                "second_aggregate_sha256": second_hash,
                "repeat_byte_identical": repeated,
            },
            "comparisons": comparisons,
            "gate": {
                "matching_contracts": matches,
                "novel_unique_match": novel_match,
            },
            "decision": {
                "promotion_authorized": novel_match,
                "authorized_next_action": (
                    "replay the bound miniature with the matched matmul backward"
                    if novel_match
                    else "retire output-projection matmul reduction as the cause"
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
