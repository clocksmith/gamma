#!/usr/bin/env python3
"""Attribute NNCP's midpoint gain to one output-bias-only Adam step."""

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
import torch.nn.functional as F

import nncp_midsegment32_update_qm0 as q0


CANDIDATE_ID = "nncp_midpoint_bias_only_qm0_v1"
GAIN_GATE_BYTES = 1_600
SOURCE_LIMIT_BYTES = 65_536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def install_bias_only_midpoint() -> None:
    call_state = {"index": 0}

    def update_slice(
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        logits: torch.Tensor,
        targets: torch.Tensor,
        config: object,
    ) -> float:
        loss = F.cross_entropy(
            logits.reshape(-1, config.vocabulary), targets.reshape(-1)
        )
        loss.backward()
        is_midpoint = call_state["index"] % 2 == 0
        if is_midpoint:
            for name, parameter in model.named_parameters():
                if name != "output_bias":
                    parameter.grad = None
        q0.core.per_parameter_clip(model, config.gradient_clip)
        optimizer.step()
        call_state["index"] += 1
        return float(loss.detach().cpu())

    original_run_once = q0.run_once

    def run_once(*args, **kwargs):
        call_state["index"] = 0
        result = original_run_once(*args, **kwargs)
        expected_calls = 2 * (q0.STREAM_LENGTH // args[1].segment_length)
        if call_state["index"] != expected_calls:
            raise RuntimeError(
                f"update call count mismatch: {call_state['index']} != {expected_calls}"
            )
        return result

    q0.update_slice = update_slice
    q0.run_once = run_once


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")

    install_bias_only_midpoint()
    q0.CANDIDATE_ID = CANDIDATE_ID
    q0.ACTUAL_GAIN_GATE_BYTES = GAIN_GATE_BYTES
    status = q0.main()

    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    comparison = decision["midsegment_comparison"]
    ideal = comparison["aligned_ideal"]

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_midsegment32_update_qm0.py",
        ROOT / "docs/nncp_midpoint_bias_only_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)
    comparison["incremental_source_package_bytes"] = len(source_package)
    comparison["incremental_source_limit_bytes"] = SOURCE_LIMIT_BYTES
    comparison["required_actual_gain_bytes"] = GAIN_GATE_BYTES

    failed: list[str] = []
    if not all(bool(value) for value in decision["integrity"].values()):
        failed.append("exact_identity_failed")
    if comparison["actual_gain_bytes"] < GAIN_GATE_BYTES:
        failed.append("actual_gain_below_1600")
    if any(value <= 0 for value in ideal["chronological_third_gain_bytes"]):
        failed.append("aligned_ideal_chronological_third_nonpositive")
    resource = decision["resource"]
    if not (
        resource["decimal_10gb_allocated_pass"]
        and resource["decimal_10gb_reserved_pass"]
    ):
        failed.append("decimal_10gb_memory_failed")
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("incremental_source_exceeds_65536")

    promotion = not failed
    decision.update(
        {
            "schema": "enwiki9_nncp_midpoint_bias_only_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "status": "AUTHORIZED_SYMBOL_BIAS_TRANSFER" if promotion else "REJECT",
            "verdict": (
                "authorize_compact_symbol_bias_transfer"
                if promotion
                else "retire_output_bias_only_midpoint_transfer"
            ),
            "score_credit_bytes": 0,
            "epistemic_tier": "exact_65536_symbol_attribution_child_zero_credit",
            "update_schedule": {
                "segment_symbols": 64,
                "midpoint_after_symbols": 32,
                "midpoint_parameter_scope": ["output_bias"],
                "midpoint_parameter_count": 16_392,
                "segment_end_parameter_scope": "all_faithful_parameters",
                "single_shared_adam_optimizer": True,
                "post_midpoint_kv_rebuilt": True,
                "parameter_delta": 0,
                "archive_side_information_bytes": 0,
            },
            "midsegment_comparison": comparison,
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact 65,536-symbol attribution of one output-bias-only "
                "midpoint Adam step followed by the faithful full update. No "
                "parameter-group, split, optimizer, learning-rate, scope, "
                "published-score, or full-corpus inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["bias_only_driver_script_sha256"] = sha256_file(
        Path(__file__)
    )
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
                "ideal_third_gain_bytes": ideal["chronological_third_gain_bytes"],
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
        print(f"nncp-midpoint-bias-only-qm0: {error}", file=sys.stderr)
        raise
