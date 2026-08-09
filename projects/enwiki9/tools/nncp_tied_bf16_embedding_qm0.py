#!/usr/bin/env python3
"""Test one shared BF16 input/output symbol embedding in exact NNCP."""

from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ROCM_PYTHON = Path("/home/x/deco/gamma/.venv_rocm/bin/python")
os.environ.setdefault("AMD_SERIALIZE_KERNEL", "3")
os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", "11.0.0")
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        os.environ.copy(),
    )

import torch

import nncp_zipf_output_bias_qm0 as child_harness


CANDIDATE_ID = "nncp_tied_bf16_embedding_qm0_v1"
SOURCE_LIMIT_BYTES = 65_536
VOCABULARY = 16_392
WIDTH = 1_024
FAITHFUL_EMBEDDING_BYTES = VOCABULARY * WIDTH * (4 + 2)
TIED_EMBEDDING_BYTES = VOCABULARY * WIDTH * 2
PARAMETER_BYTES_REMOVED = FAITHFUL_EMBEDDING_BYTES - TIED_EMBEDDING_BYTES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def install_tied_embedding() -> None:
    core = child_harness.harness.parent.core

    def tied_make_model(
        config: object, device: torch.device
    ) -> torch.nn.Module:
        torch.manual_seed(config.seed)
        torch.cuda.manual_seed_all(config.seed)
        model = core.FaithfulModel(config)
        tied = torch.nn.Parameter(model.embedding.detach().to(torch.bfloat16))
        model.embedding = tied
        model.output_embedding = tied
        if model.embedding is not model.output_embedding:
            raise ValueError("input and output embeddings are not aliased")
        named = dict(model.named_parameters())
        if "embedding" not in named or "output_embedding" in named:
            raise ValueError("shared embedding parameter enumeration is invalid")
        return model.to(device)

    core.make_model = tied_make_model


def main() -> int:
    child_harness.CANDIDATE_ID = CANDIDATE_ID
    child_harness.install_zipf_output_bias = install_tied_embedding
    status = child_harness.main()

    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    comparison = decision.pop("zipf_comparison")
    decision.pop("zipf_output_prior")

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_zipf_output_bias_qm0.py",
        ROOT / "tools/nncp_evicted_ema_memory_qm0.py",
        ROOT / "docs/nncp_tied_bf16_embedding_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)
    comparison["incremental_source_package_bytes"] = len(source_package)

    failed = [
        condition
        for condition in decision["failed_conditions"]
        if condition != "incremental_source_exceeds_65536"
    ]
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("incremental_source_exceeds_65536")
    promotion = not failed
    decision.update(
        {
            "schema": "enwiki9_nncp_tied_bf16_embedding_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "status": "AUTHORIZED_MATURE_TIED_EMBEDDING" if promotion else "REJECT",
            "verdict": (
                "authorize_mature_tied_bf16_embedding"
                if promotion
                else "retire_tied_bf16_embedding"
            ),
            "tied_embedding": {
                "input_dtype": "torch.bfloat16",
                "output_dtype": "torch.bfloat16",
                "single_parameter_alias": True,
                "faithful_embedding_parameter_bytes": FAITHFUL_EMBEDDING_BYTES,
                "tied_embedding_parameter_bytes": TIED_EMBEDDING_BYTES,
                "parameter_bytes_removed": PARAMETER_BYTES_REMOVED,
                "transmitted_table_bytes": 0,
            },
            "tied_comparison": comparison,
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact shared BF16 input/output embedding child at 65,536 "
                "symbols. No dtype, partial-tying, scale, projection, published-"
                "score, package-forecast, or full-corpus inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["tied_driver_script_sha256"] = sha256_file(Path(__file__))
    decision["artifacts"] = {
        "incremental_source_package": {
            "path": str(source_path.relative_to(ROOT)),
            "bytes": len(source_package),
            "sha256": sha256_file(source_path),
        }
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "actual_gain_bytes": comparison["actual_gain_bytes"],
                "candidate_archive_bytes": comparison["candidate_archive_bytes"],
                "failed_conditions": failed,
                "ideal_third_gain_bytes": comparison["aligned_ideal"][
                    "chronological_third_gain_bytes"
                ],
                "parameter_bytes_removed": PARAMETER_BYTES_REMOVED,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return status


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-tied-bf16-embedding-qm0: {error}", file=sys.stderr)
        raise
