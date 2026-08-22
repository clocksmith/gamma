#!/usr/bin/env python3
"""Run the scalar-reference layer-19 BF16 softmax-backward gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "tools/nncp_open_top_attention_softmax_backward_q0.c"
ELEMENTS = 64 * 32 * 8 * 320
BYTES = ELEMENTS * 2
FLAGS = (
    "-std=c11",
    "-O2",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-frounding-math",
    "-fno-vectorize",
    "-fno-slp-vectorize",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str | int]:
    return {
        "id": identifier,
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": f"sha256:{sha256(path)}",
    }


def command_line(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return []
    return [part.decode(errors="replace") for part in raw.split(b"\0") if part]


def refuse_concurrent_heavy() -> None:
    own = os.getpid()
    parent = os.getppid()
    offenders: list[dict[str, Any]] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in {own, parent}:
            continue
        argv = command_line(pid)
        if not argv:
            continue
        executable = Path(argv[0]).name
        joined = " ".join(argv)
        if (
            executable in {"cmix", "cmix_orig", "archive9"}
            or "nncp_open_top_attention" in joined
            or "nncp_libnc_top_attention" in joined
        ):
            offenders.append({"pid": pid, "argv": argv})
    if offenders:
        raise RuntimeError(f"refusing concurrent heavy execution: {offenders}")


def require_input(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_file() or resolved.stat().st_size != BYTES:
        raise ValueError(f"{label} must contain exactly {ELEMENTS} BF16 words")
    return resolved


def run_checked(command: list[str], log: Path) -> dict[str, Any]:
    result = subprocess.run(command, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    log.write_bytes(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with return code {result.returncode}: {command}"
        )
    return {
        "command": command,
        "returncode": result.returncode,
        "log": reference(log, "command-log"),
    }


def byte_equal(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            x = a.read(8 * 1024 * 1024)
            y = b.read(8 * 1024 * 1024)
            if x != y:
                return False
            if not x:
                return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probability", type=Path, required=True)
    parser.add_argument("--probability-adjoint", type=Path, required=True)
    parser.add_argument("--score-adjoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compiler", default="clang-17")
    args = parser.parse_args()

    if sys.byteorder != "little":
        raise RuntimeError("the BF16 reference requires a little-endian host")
    refuse_concurrent_heavy()
    probability = require_input(args.probability, "probability")
    probability_adjoint = require_input(
        args.probability_adjoint, "probability-adjoint"
    )
    score_adjoint = require_input(args.score_adjoint, "score-adjoint")
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"output directory already exists: {output}")
    output.mkdir(parents=True)
    work = output / "work"
    work.mkdir()

    compiler = shutil.which(args.compiler)
    if compiler is None:
        raise FileNotFoundError(f"compiler not found: {args.compiler}")
    compiler_version = subprocess.run(
        [compiler, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    ).stdout
    executable = work / "softmax-backward"
    compile_command = [compiler, *FLAGS, str(KERNEL), "-lm", "-o", str(executable)]
    compile_receipt = run_checked(compile_command, output / "compile.log")

    products = {
        "treatment-a": (output / "open-score-adjoint-a.bf16", "normal"),
        "treatment-b": (output / "open-score-adjoint-b.bf16", "normal"),
        "reverse-keys": (output / "reverse-keys-control.bf16", "reverse-keys"),
        "negate-adjoint": (
            output / "negated-adjoint-control.bf16",
            "negate-adjoint",
        ),
    }
    run_receipts: dict[str, dict[str, Any]] = {}
    for label, (destination, mode) in products.items():
        run_receipts[label] = run_checked(
            [
                str(executable),
                str(probability),
                str(probability_adjoint),
                str(destination),
                mode,
            ],
            output / f"{label}.log",
        )
        if destination.stat().st_size != BYTES:
            raise ValueError(f"{label} output size differs")

    treatment_a = products["treatment-a"][0]
    treatment_b = products["treatment-b"][0]
    reverse = products["reverse-keys"][0]
    negated = products["negate-adjoint"][0]
    measurements = {
        "elementCount": ELEMENTS,
        "treatmentExact": byte_equal(treatment_a, score_adjoint),
        "repeatByteIdentical": byte_equal(treatment_a, treatment_b),
        "reverseKeysMismatches": not byte_equal(reverse, score_adjoint),
        "negatedAdjointMismatches": not byte_equal(negated, score_adjoint),
        "allOutputSizesExact": all(
            path.stat().st_size == BYTES for path, _mode in products.values()
        ),
    }
    passed = all(
        measurements[key]
        for key in (
            "treatmentExact",
            "repeatByteIdentical",
            "reverseKeysMismatches",
            "negatedAdjointMismatches",
            "allOutputSizesExact",
        )
    )
    decision = {
        "candidateId": "nncp_open_top_attention_softmax_backward_64_q0_v1",
        "evidenceClass": "diagnostic",
        "objectiveCreditBytes": 0,
        "formula": "dS_i = P_i * (dP_i - sequential_sum_j(P_j*dP_j))",
        "geometry": {
            "states": 64,
            "streams": 32,
            "heads": 8,
            "keys": 320,
            "serialization": "state,stream,head,key",
            "elements": ELEMENTS,
        },
        "arithmetic": {
            "input": "little-endian BF16",
            "accumulator": "scalar IEEE-754 FP32 sequential key order",
            "rounding": "FE_TONEAREST and BF16 round-to-nearest-even",
            "fmaContraction": False,
            "fastMath": False,
            "ftzDaz": False,
            "compiler": reference(Path(compiler), "compiler"),
            "compilerVersion": compiler_version,
            "flags": list(FLAGS),
        },
        "execution": {
            "compile": compile_receipt,
            "runs": run_receipts,
        },
        "inputs": [
            reference(probability, "probability"),
            reference(probability_adjoint, "probability-adjoint"),
            reference(score_adjoint, "score-adjoint"),
            reference(KERNEL, "kernel-source"),
            reference(Path(__file__).resolve(), "runner"),
        ],
        "measurements": measurements,
        "decision": "authorize-successor" if passed else "retire",
        "promotionPass": passed,
        "objectiveStatus": "zero-credit arithmetic boundary",
        "artifacts": [
            reference(path, label) for label, (path, _mode) in products.items()
        ],
    }
    decision_path = output / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(work)
    print(json.dumps(decision, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
