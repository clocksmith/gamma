"""Regression tests for substrate-aware SRSTC objective selection."""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "projects/enwiki9/tools/streaming_retrieval_receipt_audit.py"
MODULE = runpy.run_path(str(TOOL))
OBJECTIVE_SELECTION = MODULE["objective_selection"]
AUDIT_CONFIG = MODULE["AuditConfig"]
AUDIT_RECEIPT = MODULE["audit_receipt"]


def row(
    path: str,
    *,
    net: float,
    heldout: float,
    substrate: str,
    raw_ready: bool = False,
    target_ready: bool = False,
    encoded_rows: int = 1_000_000,
) -> dict[str, Any]:
    return {
        "path": path,
        "net_saved_bytes": net,
        "heldout_shadow_saved_bytes": heldout,
        "max_online_state_bytes": 22_400_032,
        "largest_block_regression_bytes": 0.0,
        "promotion_ready_shadow": raw_ready,
        "promotion_blockers": [] if raw_ready else ["raw_data_source"],
        "substrate_class": substrate,
        "target_substrate_ready": target_ready,
        "target_substrate_blockers": [] if target_ready else ["positive_net"],
        "encoded_rows": encoded_rows,
    }


def test_raw_target_closing_win_requires_target_substrate_transfer() -> None:
    selection = OBJECTIVE_SELECTION(
        [
            row(
                "raw.json",
                net=900_464,
                heldout=916_540,
                substrate="raw_order2_shadow",
                raw_ready=True,
            ),
            row(
                "fx2.json",
                net=-16_080,
                heldout=-4,
                substrate="target_probability_trace",
                encoded_rows=4_805_936,
            ),
        ]
    )

    assert selection["recommended_action"] == (
        "construct_residual_conditioned_target_substrate_transfer"
    )
    assert selection["target_substrate_positive_net_receipts"] == 0
    assert selection["target_substrate_ready_receipts"] == 0
    assert selection["broadest_target_substrate_receipt"]["path"] == "fx2.json"


def test_paying_target_substrate_transfer_can_enter_packaging_queue() -> None:
    selection = OBJECTIVE_SELECTION(
        [
            row(
                "raw.json",
                net=900_464,
                heldout=916_540,
                substrate="raw_order2_shadow",
                raw_ready=True,
            ),
            row(
                "fx2-paying.json",
                net=700_000,
                heldout=720_000,
                substrate="target_probability_trace",
                target_ready=True,
                encoded_rows=8_000_000,
            ),
        ]
    )

    assert selection["recommended_action"] == "package_target_substrate_transfer_piece"
    assert selection["target_substrate_positive_net_receipts"] == 1
    assert selection["target_substrate_ready_receipts"] == 1
    assert selection["best_target_substrate_ready_receipt"]["path"] == (
        "fx2-paying.json"
    )


def test_target_trace_can_be_ready_without_raw_data_source() -> None:
    receipt = AUDIT_RECEIPT(
        TOOL.parent.parent
        / "results/streaming_retrieval_shadow/synthetic_target_trace.json",
        {
            "receipt_type": "streaming_retrieval_shadow",
            "method": "streaming_retrieval_shadow_v2",
            "base_trace": "fx2.bin",
            "feature_source": "cache_rows",
            "heldout_shadow_saved_bytes": 10,
            "net_saved_bytes": 5,
            "max_online_state_bytes": 1024,
            "block_rows": [{"gain_bytes": 1.0}],
            "trace_data_alignment": {"warning": None},
        },
        AUDIT_CONFIG(0.0, 64_000_000),
    )

    assert receipt["substrate_class"] == "target_probability_trace"
    assert receipt["promotion_ready_shadow"] is False
    assert receipt["promotion_blockers"] == ["raw_data_source"]
    assert receipt["target_substrate_ready"] is True
    assert receipt["target_substrate_blockers"] == []
