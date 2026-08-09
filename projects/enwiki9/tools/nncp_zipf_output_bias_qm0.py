#!/usr/bin/env python3
"""Test one fixed decoder-derived Zipf initialization of NNCP output bias."""

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

import nncp_evicted_ema_memory_qm0 as harness


CANDIDATE_ID = "nncp_zipf_output_bias_qm0_v1"
ALPHA = 0.435
SOURCE_LIMIT_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def install_zipf_output_bias() -> None:
    model_type = harness.parent.core.FaithfulModel
    faithful_reset = model_type.reset_parameters

    def zipf_reset(self: object) -> None:
        faithful_reset(self)
        with torch.no_grad():
            symbol_id = torch.arange(
                self.config.vocabulary,
                dtype=torch.float64,
                device=self.output_bias.device,
            )
            prior = -ALPHA * torch.log(symbol_id + 1.0)
            self.output_bias.copy_(prior.to(self.output_bias.dtype))

    model_type.reset_parameters = zipf_reset


def main() -> int:
    harness.CANDIDATE_ID = CANDIDATE_ID
    harness.install_ema_memory = install_zipf_output_bias
    status = harness.main()

    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    comparison = decision.pop("ema_comparison")
    decision.pop("ema_memory")

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_evicted_ema_memory_qm0.py",
        ROOT / "docs/nncp_zipf_output_bias_qm0_plan.md",
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
            "schema": "enwiki9_nncp_zipf_output_bias_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "status": "AUTHORIZED_MATURE_ZIPF_PRIOR" if promotion else "REJECT",
            "verdict": (
                "authorize_mature_zipf_output_prior"
                if promotion
                else "retire_zipf_output_bias"
            ),
            "zipf_output_prior": {
                "alpha": ALPHA,
                "formula": "output_bias[i] = -alpha * ln(i + 1)",
                "parameter_delta": 0,
                "resident_memory_shape_delta": 0,
                "transmitted_table_bytes": 0,
                "online_bias_training_unchanged": True,
            },
            "zipf_comparison": comparison,
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact fixed-alpha zero-table output-bias initialization child "
                "at 65,536 symbols. No exponent, offset, piecewise-law, frequency-"
                "table, published-score, package-forecast, or full-corpus "
                "inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["zipf_driver_script_sha256"] = sha256_file(Path(__file__))
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
        print(f"nncp-zipf-output-bias-qm0: {error}", file=sys.stderr)
        raise
