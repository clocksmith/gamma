#!/usr/bin/env python3
"""Probe LibNC's unfused softmax and indexed-log backward contract."""

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
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_softmax_indexed_log_backward_parity_v1"
CLASSES = 256
COLUMNS = 4
TARGETS = np.asarray([60, 109, 101, 100], dtype=np.int64)
THRESHOLD = 2e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fixture() -> np.ndarray:
    logits = np.empty((CLASSES, COLUMNS), dtype=np.float32)
    for column in range(COLUMNS):
        for class_index in range(CLASSES):
            value = (class_index * 37 + column * 53) % 509 - 254
            logits[class_index, column] = (
                np.float32(value) / np.float32(128.0)
            )
    return logits


def fused_contract(logits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    value = torch.tensor(logits.T, dtype=torch.float32, requires_grad=True)
    target = torch.tensor(TARGETS, dtype=torch.int64)
    probabilities = torch.softmax(value, dim=-1)
    F.cross_entropy(value, target, reduction="mean").backward()
    return probabilities.detach().numpy().T, value.grad.detach().numpy().T


def explicit_contract(logits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    value = torch.tensor(logits.T, dtype=torch.float32, requires_grad=True)
    target = torch.tensor(TARGETS, dtype=torch.int64)
    probabilities = torch.softmax(value, dim=-1)
    selected = probabilities[torch.arange(COLUMNS), target]
    (-torch.log(selected).sum() / COLUMNS).backward()
    return probabilities.detach().numpy().T, value.grad.detach().numpy().T


def closed_form_contract(logits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    value = torch.tensor(logits.T, dtype=torch.float32)
    probabilities = torch.softmax(value, dim=-1)
    gradient = probabilities.clone()
    gradient[torch.arange(COLUMNS), torch.tensor(TARGETS)] -= 1.0
    gradient /= COLUMNS
    return probabilities.numpy().T, gradient.numpy().T


def metrics(
    reference: tuple[np.ndarray, np.ndarray],
    candidate: tuple[np.ndarray, np.ndarray],
) -> dict[str, float]:
    probability_error = np.abs(reference[0] - candidate[0])
    gradient_error = np.abs(reference[1] - candidate[1])
    return {
        "maximum_absolute_probability_error": float(probability_error.max()),
        "mean_absolute_probability_error": float(probability_error.mean()),
        "maximum_absolute_gradient_error": float(gradient_error.max()),
        "mean_absolute_gradient_error": float(gradient_error.mean()),
    }


def aggregate_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in ("probabilities.bin", "logit_gradient.bin"):
        digest.update(name.encode("ascii") + b"\0")
        digest.update((directory / name).read_bytes())
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
        default=ROOT / "tools/nncp_libnc_softmax_indexed_log_probe.c",
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

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-loss-") as temp:
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
            np.fromfile(first_dir / "probabilities.bin", dtype="<f4").reshape(
                (CLASSES, COLUMNS), order="F"
            ),
            np.fromfile(first_dir / "logit_gradient.bin", dtype="<f4").reshape(
                (CLASSES, COLUMNS), order="F"
            ),
        )
        logits = fixture()
        comparisons = {
            "pytorch_fused_cross_entropy": metrics(
                reference, fused_contract(logits)
            ),
            "pytorch_explicit_softmax_indexed_log": metrics(
                reference, explicit_contract(logits)
            ),
            "probability_minus_onehot_closed_form": metrics(
                reference, closed_form_contract(logits)
            ),
        }
        matches = [
            name
            for name, item in comparisons.items()
            if item["maximum_absolute_probability_error"] <= THRESHOLD
            and item["maximum_absolute_gradient_error"] <= THRESHOLD
        ]
        novel_match = repeated and len(matches) == 1 and matches != [
            "pytorch_fused_cross_entropy"
        ]
        result = {
            "schema": (
                "gamma.nncp_v33_libnc_softmax_indexed_log_backward_parity.v1"
            ),
            "candidate_id": CANDIDATE_ID,
            "status": "PASS" if novel_match else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "classes": CLASSES,
                "columns": COLUMNS,
                "targets": TARGETS.tolist(),
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
                    "replay the bound miniature with the matched loss backward"
                    if novel_match
                    else "retire the softmax-indexed-log loss graph as the cause"
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
