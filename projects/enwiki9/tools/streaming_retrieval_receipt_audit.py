#!/usr/bin/env python3
"""Audit SRSTC streaming-retrieval shadow receipts.

The audit separates raw-shadow readiness from target-substrate transfer. A raw
receipt is not marked promotion-ready unless it has held-out savings, alignment
safety, bounded online state, and complete block-regression evidence; even then,
packaging requires a separately paying target-probability-trace receipt.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import shlex
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKTREE_ROOT = ROOT.parent.parent
RESULTS_DIR = ROOT / "results" / "streaming_retrieval_shadow"
OUT_JSON = ROOT / "docs" / "streaming_retrieval_receipt_audit.json"
OUT_MD = ROOT / "docs" / "streaming_retrieval_receipt_audit.md"

CURRENT_WINNER = 110_793_128
TARGET_SCORE = 109_500_000
BEST_FORECAST = 110_181_114
BLOCK_POSTERIOR_CODE_BYTES_ESTIMATE = 3_788
RAW_SHADOW_METHOD = "streaming_retrieval_raw_shadow_v1"


@dataclass(frozen=True)
class AuditConfig:
    max_block_regression_bytes: float
    max_online_state_bytes: int


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def worktree_rel_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    path = pathlib.Path(value)
    try:
        return path.resolve().relative_to(WORKTREE_ROOT).as_posix()
    except (OSError, ValueError):
        return value


def shell_join(parts: list[Any]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_receipt(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("receipt_type") != "streaming_retrieval_shadow":
        return None
    return payload


def block_audit(receipt: dict[str, Any]) -> dict[str, Any]:
    rows = receipt.get("block_rows")
    source = "complete" if isinstance(rows, list) and rows else None
    if source is None:
        rows = receipt.get("worst_blocks_by_qbit_loss")
        source = "worst_blocks_only" if isinstance(rows, list) and rows else "missing"
    if not isinstance(rows, list):
        rows = []

    regression_count = 0
    positive_count = 0
    visible_gain = 0.0
    visible_regression = 0.0
    worst_regression = as_float(receipt.get("largest_block_regression_bytes")) or 0.0
    for row in rows:
        if not isinstance(row, dict):
            continue
        gain = as_float(row.get("gain_bytes"))
        if gain is None:
            continue
        visible_gain += gain
        if gain < 0:
            regression_count += 1
            visible_regression += -gain
            worst_regression = max(worst_regression, -gain)
        elif gain > 0:
            positive_count += 1
    return {
        "block_audit_source": source,
        "complete_block_audit": source == "complete",
        "visible_block_rows": len(rows),
        "visible_block_regression_count": regression_count,
        "visible_positive_block_count": positive_count,
        "visible_block_gain_bytes": visible_gain,
        "visible_block_regression_bytes": visible_regression,
        "largest_block_regression_bytes": worst_regression,
    }


def complete_block_rerun_command(
    path: pathlib.Path,
    receipt: dict[str, Any],
    block: dict[str, Any],
) -> str | None:
    if block["complete_block_audit"]:
        return None
    if receipt.get("method") != "streaming_retrieval_raw_shadow_v1":
        return None
    schema = as_dict(receipt.get("sketch_schema"))
    data_path = worktree_rel_path(receipt.get("data"))
    data_bytes = as_int(receipt.get("data_bytes_loaded"))
    train_bytes = as_int(receipt.get("train_bytes"))
    if data_path is None or data_bytes is None or train_bytes is None:
        return None

    output = (
        ROOT
        / "results"
        / "streaming_retrieval_shadow"
        / f"{path.stem}_complete_blocks.json"
    )
    if output.exists():
        return None
    parts: list[Any] = [
        "python3",
        "projects/enwiki9/tools/streaming_retrieval_raw_shadow.py",
        "--data",
        data_path,
        "--limit-bytes",
        data_bytes,
        "--train-bytes",
        train_bytes,
        "--suffix-len",
        as_int(schema.get("suffix_len")) or 32,
        "--sketch-len",
        as_int(schema.get("sketch_len")) or 96,
        "--base-order",
        as_int(schema.get("base_order")) or 2,
        "--p-buckets",
        as_int(schema.get("p_buckets")) or 32,
        "--min-support",
        as_int(schema.get("min_support")) or 8,
        "--blend-ppm",
        as_int(schema.get("blend_ppm")) or 640000,
        "--base-table-cap-entries",
        as_int(schema.get("base_table_cap_entries")) or 200000,
        "--retrieval-table-cap-entries",
        as_int(schema.get("retrieval_table_cap_entries")) or 200000,
        "--partial-byte-family",
        str(schema.get("partial_byte_family") or "sketch"),
        "--expert-mode",
        str(schema.get("expert_mode") or "aggregate"),
        "--router-decay-shift",
        as_int(schema.get("router_decay_shift")) or 6,
        "--router-abstain-margin-qbits",
        as_int(schema.get("router_abstain_margin_qbits")) or 128,
        "--added-code-bytes-estimate",
        as_int(receipt.get("added_code_bytes_estimate")) or 0,
        "--added-static-table-bytes",
        as_int(receipt.get("added_static_table_bytes")) or 0,
        "--scope-bytes",
        as_int(receipt.get("scope_bytes")) or 1000000000,
        "--output",
        output.resolve().relative_to(WORKTREE_ROOT).as_posix(),
        "--print-summary",
    ]
    target = as_dict(receipt.get("target"))
    baseline_score = as_int(target.get("baseline_score"))
    target_score = as_int(target.get("target_score"))
    if baseline_score is not None:
        parts.extend(["--baseline-score", baseline_score])
    if target_score is not None:
        parts.extend(["--target-score", target_score])
    return shell_join(parts)


def block_posterior_rerun_command(
    path: pathlib.Path,
    receipt: dict[str, Any],
    block: dict[str, Any],
) -> str | None:
    if receipt.get("method") != "streaming_retrieval_raw_shadow_v1":
        return None
    if not block["complete_block_audit"] or block["largest_block_regression_bytes"] <= 0:
        return None
    schema = as_dict(receipt.get("sketch_schema"))
    if str(schema.get("block_router_mode") or "none") != "none":
        return None
    if bool(as_dict(schema.get("copy_channel")).get("enabled")):
        return None
    data_path = worktree_rel_path(receipt.get("data"))
    data_bytes = as_int(receipt.get("data_bytes_loaded"))
    train_bytes = as_int(receipt.get("train_bytes"))
    if data_path is None or data_bytes is None or train_bytes is None:
        return None

    output = RESULTS_DIR / f"{path.stem}_blockposterior_v1.json"
    if output.exists():
        return None
    parts: list[Any] = [
        "python3",
        "projects/enwiki9/tools/streaming_retrieval_raw_shadow.py",
        "--data",
        data_path,
        "--limit-bytes",
        data_bytes,
        "--train-bytes",
        train_bytes,
        "--suffix-len",
        as_int(schema.get("suffix_len")) or 32,
        "--sketch-len",
        as_int(schema.get("sketch_len")) or 96,
        "--base-order",
        as_int(schema.get("base_order")) or 2,
        "--p-buckets",
        as_int(schema.get("p_buckets")) or 32,
        "--min-support",
        as_int(schema.get("min_support")) or 8,
        "--blend-ppm",
        as_int(schema.get("blend_ppm")) or 640000,
        "--base-table-cap-entries",
        as_int(schema.get("base_table_cap_entries")) or 200000,
        "--retrieval-table-cap-entries",
        as_int(schema.get("retrieval_table_cap_entries")) or 200000,
        "--byte-table-cap-entries",
        as_int(schema.get("byte_table_cap_entries")) or 100000,
        "--partial-byte-family",
        str(schema.get("partial_byte_family") or "sketch"),
        "--typed-key-profile",
        str(schema.get("typed_key_profile") or "base"),
        "--expert-mode",
        str(schema.get("expert_mode") or "aggregate"),
        "--byte-prior-blend-ppm",
        as_int(schema.get("byte_prior_blend_ppm")) or 0,
        "--byte-min-support",
        as_int(schema.get("byte_min_support")) or 4,
        "--router-decay-shift",
        as_int(schema.get("router_decay_shift")) or 6,
        "--router-abstain-margin-qbits",
        as_int(schema.get("router_abstain_margin_qbits")) or 128,
        "--block-bytes",
        as_int(schema.get("block_bytes")) or 16384,
        "--block-router-mode",
        "posterior",
        "--block-posterior-srstc-prior-ppm",
        500000,
        "--block-posterior-weight-bits",
        24,
        "--added-code-bytes-estimate",
        (as_int(receipt.get("added_code_bytes_estimate")) or 0)
        + BLOCK_POSTERIOR_CODE_BYTES_ESTIMATE,
        "--added-static-table-bytes",
        as_int(receipt.get("added_static_table_bytes")) or 0,
        "--scope-bytes",
        as_int(receipt.get("scope_bytes")) or 1000000000,
        "--progress-interval-bytes",
        1048576,
        "--output",
        output.resolve().relative_to(WORKTREE_ROOT).as_posix(),
        "--print-summary",
    ]
    if bool(schema.get("log_odds_mix")):
        parts.append("--log-odds-mix")
    target = as_dict(receipt.get("target"))
    baseline_score = as_int(target.get("baseline_score"))
    target_score = as_int(target.get("target_score"))
    if baseline_score is not None:
        parts.extend(["--baseline-score", baseline_score])
    if target_score is not None:
        parts.extend(["--target-score", target_score])
    return shell_join(parts)


def audit_receipt(path: pathlib.Path, receipt: dict[str, Any], config: AuditConfig) -> dict[str, Any]:
    heldout_saved = as_float(receipt.get("heldout_shadow_saved_bytes"))
    net_saved = as_float(receipt.get("net_saved_bytes"))
    state_bytes = as_int(receipt.get("max_online_state_bytes"))
    alignment = receipt.get("trace_data_alignment")
    alignment_warning = (
        isinstance(alignment, dict)
        and alignment.get("warning") not in {None, "", False}
    )
    feature_source = str(receipt.get("feature_source") or "unknown")
    block = block_audit(receipt)
    rerun_command = complete_block_rerun_command(path, receipt, block)
    posterior_rerun_command = block_posterior_rerun_command(path, receipt, block)

    method = str(receipt.get("method") or "unknown")
    base_trace = str(receipt.get("base_trace") or "unknown")
    substrate_class = (
        "raw_order2_shadow"
        if method == RAW_SHADOW_METHOD
        else "target_probability_trace"
    )
    checks = {
        "has_heldout": heldout_saved is not None,
        "positive_heldout": heldout_saved is not None and heldout_saved > 0,
        "positive_net": net_saved is not None and net_saved > 0,
        "alignment_ok": not alignment_warning,
        "raw_data_source": feature_source == "raw_data",
        "state_within_cap": state_bytes is not None and state_bytes <= config.max_online_state_bytes,
        "block_regression_within_cap": block["largest_block_regression_bytes"] <= config.max_block_regression_bytes,
        "complete_block_audit": block["complete_block_audit"],
    }
    blockers = [name for name, ok in checks.items() if not ok]
    promotion_ready = not blockers
    target_substrate_checks = {
        "target_probability_trace": substrate_class == "target_probability_trace",
        "has_heldout": checks["has_heldout"],
        "positive_heldout": checks["positive_heldout"],
        "positive_net": checks["positive_net"],
        "alignment_ok": checks["alignment_ok"],
        "state_within_cap": checks["state_within_cap"],
        "block_regression_within_cap": checks["block_regression_within_cap"],
        "complete_block_audit": checks["complete_block_audit"],
    }
    target_substrate_blockers = [
        name for name, ok in target_substrate_checks.items() if not ok
    ]
    return {
        "path": rel(path),
        "verdict": str(receipt.get("verdict") or "incomplete"),
        "method": method,
        "base_trace": base_trace,
        "substrate_class": substrate_class,
        "feature_source": feature_source,
        "encoded_rows": as_int(receipt.get("encoded_rows")),
        "data_bytes_loaded": as_int(receipt.get("data_bytes_loaded")),
        "train_bytes": as_int(receipt.get("train_bytes")),
        "heldout_shadow_saved_bytes": heldout_saved,
        "net_saved_bytes": net_saved,
        "shadow_saved_bytes": as_float(receipt.get("shadow_saved_bytes")),
        "added_code_bytes_estimate": as_int(receipt.get("added_code_bytes_estimate")),
        "added_static_table_bytes": as_int(receipt.get("added_static_table_bytes")),
        "max_online_state_bytes": state_bytes,
        "alignment_warning": alignment_warning,
        "checks": checks,
        "promotion_blockers": blockers,
        "promotion_ready_shadow": promotion_ready,
        "target_substrate_checks": target_substrate_checks,
        "target_substrate_blockers": target_substrate_blockers,
        "target_substrate_ready": not target_substrate_blockers,
        "complete_block_rerun_command": rerun_command,
        "block_posterior_rerun_command": posterior_rerun_command,
        **block,
    }


def load_rows(results_dir: pathlib.Path, config: AuditConfig) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(results_dir.glob("*.json")):
        receipt = load_receipt(path)
        if receipt is None:
            continue
        rows.append(audit_receipt(path, receipt, config))
    rows.sort(
        key=lambda row: (
            row["promotion_ready_shadow"] is not True,
            -(row["net_saved_bytes"] or float("-inf")),
            row["path"],
        )
    )
    return rows


def objective_row(row: dict[str, Any], *, forecast_gap: int, public_gap: int) -> dict[str, Any]:
    net = row.get("net_saved_bytes")
    forecast_gap_remaining = None
    public_gap_remaining = None
    closes_forecast_gap = False
    closes_public_gap = False
    if isinstance(net, (int, float)):
        forecast_gap_remaining = forecast_gap - net
        public_gap_remaining = public_gap - net
        closes_forecast_gap = forecast_gap_remaining <= 0
        closes_public_gap = public_gap_remaining <= 0
    return {
        "path": row.get("path"),
        "net_saved_bytes": net,
        "heldout_shadow_saved_bytes": row.get("heldout_shadow_saved_bytes"),
        "max_online_state_bytes": row.get("max_online_state_bytes"),
        "largest_block_regression_bytes": row.get("largest_block_regression_bytes"),
        "promotion_ready_shadow": row.get("promotion_ready_shadow"),
        "promotion_blockers": row.get("promotion_blockers") or [],
        "substrate_class": row.get("substrate_class"),
        "target_substrate_ready": row.get("target_substrate_ready"),
        "target_substrate_blockers": row.get("target_substrate_blockers") or [],
        "encoded_rows": row.get("encoded_rows"),
        "forecast_gap_remaining_bytes": forecast_gap_remaining,
        "public_gap_remaining_bytes": public_gap_remaining,
        "closes_forecast_gap": closes_forecast_gap,
        "closes_public_gap": closes_public_gap,
    }


def objective_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forecast_gap = BEST_FORECAST - TARGET_SCORE
    public_gap = CURRENT_WINNER - TARGET_SCORE
    positive_net = [
        row for row in rows
        if isinstance(row.get("net_saved_bytes"), (int, float))
        and row["net_saved_bytes"] > 0
    ]
    promotion_ready = [row for row in positive_net if row.get("promotion_ready_shadow") is True]
    target_closing = [
        row for row in positive_net
        if row["net_saved_bytes"] >= forecast_gap
    ]
    regression_blocked = [
        row for row in positive_net
        if row.get("promotion_blockers") == ["block_regression_within_cap"]
    ]
    target_substrate_rows = [
        row
        for row in rows
        if row.get("substrate_class") == "target_probability_trace"
        and isinstance(row.get("net_saved_bytes"), (int, float))
    ]
    target_substrate_positive = [
        row for row in target_substrate_rows if row["net_saved_bytes"] > 0
    ]
    target_substrate_ready = [
        row for row in target_substrate_positive if row.get("target_substrate_ready") is True
    ]

    best_ready = max(
        promotion_ready,
        key=lambda row: row["net_saved_bytes"],
        default=None,
    )
    best_target_closing = max(
        target_closing,
        key=lambda row: row["net_saved_bytes"],
        default=None,
    )
    best_regression_blocked = max(
        regression_blocked,
        key=lambda row: row["net_saved_bytes"],
        default=None,
    )
    broadest_target_substrate = max(
        target_substrate_rows,
        key=lambda row: (
            row.get("encoded_rows") or 0,
            (
                row["net_saved_bytes"]
                if isinstance(row.get("net_saved_bytes"), (int, float))
                else float("-inf")
            ),
        ),
        default=None,
    )
    best_target_substrate_ready = max(
        target_substrate_ready,
        key=lambda row: row["net_saved_bytes"],
        default=None,
    )
    top_objective_rows = sorted(
        positive_net,
        key=lambda row: (
            not (row["net_saved_bytes"] >= forecast_gap),
            row.get("promotion_ready_shadow") is not True,
            -(row["net_saved_bytes"]),
            row["path"],
        ),
    )[:12]

    if (
        best_target_substrate_ready is not None
        and best_target_substrate_ready["net_saved_bytes"] >= forecast_gap
    ):
        recommended_action = "package_target_substrate_transfer_piece"
        action_reason = (
            "a counted held-out target-substrate transfer receipt closes the "
            "forecast-to-target byte gap"
        )
    elif best_ready is not None and best_ready["net_saved_bytes"] >= forecast_gap:
        recommended_action = "construct_residual_conditioned_target_substrate_transfer"
        action_reason = (
            "the raw-shadow receipt closes the forecast gap, but no counted "
            "target-substrate receipt proves sufficient realizable transfer"
        )
    elif (
        best_regression_blocked is not None
        and best_regression_blocked["net_saved_bytes"] >= forecast_gap
    ):
        recommended_action = "remove_or_route_block_regressions_before_packaging"
        action_reason = (
            "the best target-closing receipt is blocked only by small block regressions"
        )
    elif best_target_substrate_ready is not None:
        recommended_action = "expand_target_substrate_transfer_before_packaging"
        action_reason = (
            "target-substrate transfer is positive and replay-ready but does not "
            "close the forecast-to-target gap"
        )
    elif best_ready is not None:
        recommended_action = "construct_target_substrate_transfer_from_ready_raw_piece"
        action_reason = (
            "raw promotion-ready receipts are positive but have no paying "
            "target-substrate transfer receipt"
        )
    else:
        recommended_action = "generate_more_shadow_receipts_before_packaging"
        action_reason = "no positive promotion-ready receipt is available"

    return {
        "current_winner_score": CURRENT_WINNER,
        "best_forecast_score": BEST_FORECAST,
        "target_score": TARGET_SCORE,
        "public_gap_bytes": public_gap,
        "forecast_gap_bytes": forecast_gap,
        "best_target_closing_receipt": (
            objective_row(best_target_closing, forecast_gap=forecast_gap, public_gap=public_gap)
            if best_target_closing is not None
            else None
        ),
        "best_regression_blocked_receipt": (
            objective_row(best_regression_blocked, forecast_gap=forecast_gap, public_gap=public_gap)
            if best_regression_blocked is not None
            else None
        ),
        "best_promotion_ready_receipt": (
            objective_row(best_ready, forecast_gap=forecast_gap, public_gap=public_gap)
            if best_ready is not None
            else None
        ),
        "target_substrate_receipts": len(target_substrate_rows),
        "target_substrate_positive_net_receipts": len(target_substrate_positive),
        "target_substrate_ready_receipts": len(target_substrate_ready),
        "broadest_target_substrate_receipt": (
            objective_row(
                broadest_target_substrate,
                forecast_gap=forecast_gap,
                public_gap=public_gap,
            )
            if broadest_target_substrate is not None
            else None
        ),
        "best_target_substrate_ready_receipt": (
            objective_row(
                best_target_substrate_ready,
                forecast_gap=forecast_gap,
                public_gap=public_gap,
            )
            if best_target_substrate_ready is not None
            else None
        ),
        "recommended_action": recommended_action,
        "action_reason": action_reason,
        "top_objective_rows": [
            objective_row(row, forecast_gap=forecast_gap, public_gap=public_gap)
            for row in top_objective_rows
        ],
    }


def summarize(rows: list[dict[str, Any]], config: AuditConfig) -> dict[str, Any]:
    positive_net = [row for row in rows if (row.get("net_saved_bytes") or 0) > 0]
    promotion_ready = [row for row in rows if row.get("promotion_ready_shadow") is True]
    blocker_counts: dict[str, int] = {}
    for row in rows:
        for blocker in row.get("promotion_blockers", []):
            blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1
    best_net = max(
        (row for row in rows if row.get("net_saved_bytes") is not None),
        key=lambda row: row["net_saved_bytes"],
        default=None,
    )
    complete_block_rerun_queue = [
        row
        for row in rows
        if row.get("complete_block_rerun_command")
        and "complete_block_audit" in row.get("promotion_blockers", [])
        and (row.get("net_saved_bytes") or 0) > 0
    ][:8]
    block_posterior_rerun_queue = [
        row
        for row in rows
        if row.get("block_posterior_rerun_command")
        and row.get("promotion_blockers") == ["block_regression_within_cap"]
        and (row.get("net_saved_bytes") or 0) >= BEST_FORECAST - TARGET_SCORE
    ][:4]
    substrate_groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = f"{row.get('method') or 'unknown'} / {row.get('base_trace') or 'unknown'}"
        group = substrate_groups.setdefault(
            key,
            {
                "substrate": key,
                "receipts": 0,
                "positive_net_receipts": 0,
                "promotion_ready_shadow_receipts": 0,
                "best_net_saved_bytes": None,
                "best_heldout_shadow_saved_bytes": None,
                "best_receipt": None,
            },
        )
        group["receipts"] += 1
        net = row.get("net_saved_bytes")
        heldout = row.get("heldout_shadow_saved_bytes")
        if isinstance(net, (int, float)) and net > 0:
            group["positive_net_receipts"] += 1
        if row.get("promotion_ready_shadow") is True:
            group["promotion_ready_shadow_receipts"] += 1
        current_best = group["best_net_saved_bytes"]
        if isinstance(net, (int, float)) and (
            current_best is None or net > current_best
        ):
            group["best_net_saved_bytes"] = net
            group["best_heldout_shadow_saved_bytes"] = heldout
            group["best_receipt"] = row.get("path")
    substrate_summary = sorted(
        substrate_groups.values(),
        key=lambda group: (
            -(group["best_net_saved_bytes"] if group["best_net_saved_bytes"] is not None else float("-inf")),
            str(group["substrate"]),
        ),
    )
    return {
        "receipt_type": "streaming_retrieval_receipt_audit",
        "source_results_dir": rel(RESULTS_DIR),
        "max_block_regression_bytes": config.max_block_regression_bytes,
        "max_online_state_bytes": config.max_online_state_bytes,
        "receipts_scanned": len(rows),
        "positive_net_receipts": len(positive_net),
        "promotion_ready_shadow_receipts": len(promotion_ready),
        "best_net_receipt": best_net,
        "promotion_blocker_counts": dict(sorted(blocker_counts.items())),
        "complete_block_rerun_queue": complete_block_rerun_queue,
        "block_posterior_rerun_queue": block_posterior_rerun_queue,
        "substrate_summary": substrate_summary,
        "objective_selection": objective_selection(rows),
        "top_rows": rows[:20],
    }


def fmt_number(value: Any) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.3f}"
    return "n/a"


def render_md(summary: dict[str, Any]) -> str:
    best = summary.get("best_net_receipt") if isinstance(summary.get("best_net_receipt"), dict) else None
    lines = [
        "# Streaming Retrieval Receipt Audit",
        "",
        "This report audits cached SRSTC shadow receipts. It is not a compressor",
        "benchmark and does not mutate the active cmix21 runner.",
        "",
        "Promotion rule:",
        "",
        "```text",
        "positive_net_shadow is evidence, not promotion.",
        "promotion requires held-out gain, no alignment warning, bounded state,",
        "and complete block-regression evidence.",
        "```",
        "",
        "## Summary",
        "",
        f"- Receipts scanned: `{fmt_number(summary.get('receipts_scanned'))}`",
        f"- Positive net receipts: `{fmt_number(summary.get('positive_net_receipts'))}`",
        f"- Promotion-ready shadow receipts: `{fmt_number(summary.get('promotion_ready_shadow_receipts'))}`",
        f"- Max block regression cap: `{fmt_number(summary.get('max_block_regression_bytes'))}` bytes",
        f"- Max online state cap: `{fmt_number(summary.get('max_online_state_bytes'))}` bytes",
    ]
    if best:
        lines.extend(
            [
                f"- Best net receipt: `{best['path']}`",
                f"- Best net saved bytes: `{fmt_number(best.get('net_saved_bytes'))}`",
                f"- Best held-out saved bytes: `{fmt_number(best.get('heldout_shadow_saved_bytes'))}`",
                f"- Best receipt blockers: `{', '.join(best.get('promotion_blockers') or ['none'])}`",
            ]
        )
    selection = (
        summary.get("objective_selection")
        if isinstance(summary.get("objective_selection"), dict)
        else {}
    )
    if selection:
        best_target = (
            selection.get("best_target_closing_receipt")
            if isinstance(selection.get("best_target_closing_receipt"), dict)
            else None
        )
        best_ready = (
            selection.get("best_promotion_ready_receipt")
            if isinstance(selection.get("best_promotion_ready_receipt"), dict)
            else None
        )
        broadest_transfer = (
            selection.get("broadest_target_substrate_receipt")
            if isinstance(selection.get("broadest_target_substrate_receipt"), dict)
            else None
        )
        lines.extend(
            [
                "",
                "## Objective Selection",
                "",
                "This is the SRSTC generator-verifier-selector loop in receipt form:",
                "candidate receipts are generated separately, verified by held-out",
                "same-coder bytes, then selected by net bytes after counted costs",
                "and promotion blockers.",
                "",
                f"- Current winner score: `{fmt_number(selection.get('current_winner_score'))}`",
                f"- Best forecast score: `{fmt_number(selection.get('best_forecast_score'))}`",
                f"- Target score: `{fmt_number(selection.get('target_score'))}`",
                f"- Public-record gap to target: `{fmt_number(selection.get('public_gap_bytes'))}` bytes",
                f"- Forecast gap to target: `{fmt_number(selection.get('forecast_gap_bytes'))}` bytes",
                f"- Recommended action: `{selection.get('recommended_action', 'unknown')}`",
                f"- Reason: `{selection.get('action_reason', 'unknown')}`",
                f"- Target-substrate receipts: `{fmt_number(selection.get('target_substrate_receipts'))}`",
                f"- Positive-net target-substrate receipts: `{fmt_number(selection.get('target_substrate_positive_net_receipts'))}`",
                f"- Replay-ready target-substrate receipts: `{fmt_number(selection.get('target_substrate_ready_receipts'))}`",
            ]
        )
        if broadest_transfer:
            lines.extend(
                [
                    f"- Broadest target-substrate receipt: `{broadest_transfer.get('path')}`",
                    f"- Broadest target-substrate encoded rows: `{fmt_number(broadest_transfer.get('encoded_rows'))}`",
                    f"- Broadest target-substrate net bytes: `{fmt_number(broadest_transfer.get('net_saved_bytes'))}`",
                    f"- Broadest target-substrate held-out bytes: `{fmt_number(broadest_transfer.get('heldout_shadow_saved_bytes'))}`",
                    f"- Broadest target-substrate blockers: `{', '.join(broadest_transfer.get('target_substrate_blockers') or ['none'])}`",
                ]
            )
        if best_target:
            lines.extend(
                [
                    f"- Best target-closing receipt: `{best_target.get('path')}`",
                    f"- Target-closing net saved bytes: `{fmt_number(best_target.get('net_saved_bytes'))}`",
                    f"- Forecast gap remaining after best target-closing receipt: `{fmt_number(best_target.get('forecast_gap_remaining_bytes'))}`",
                    f"- Target-closing blockers: `{', '.join(best_target.get('promotion_blockers') or ['none'])}`",
                ]
            )
        if best_ready:
            lines.extend(
                [
                    f"- Best promotion-ready fallback: `{best_ready.get('path')}`",
                    f"- Ready fallback net saved bytes: `{fmt_number(best_ready.get('net_saved_bytes'))}`",
                    f"- Forecast gap remaining after ready fallback: `{fmt_number(best_ready.get('forecast_gap_remaining_bytes'))}`",
                ]
            )
        rows = selection.get("top_objective_rows")
        if isinstance(rows, list) and rows:
            lines.extend(
                [
                    "",
                    "| Receipt | Substrate | Net Saved | Forecast Gap Remaining | Raw-shadow Ready | Largest Regression | Blockers |",
                    "|---|---|---:|---:|---|---:|---|",
                ]
            )
            for row in rows:
                if not isinstance(row, dict):
                    continue
                blockers_text = ", ".join(row.get("promotion_blockers") or ["none"])
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            f"`{row.get('path')}`",
                            f"`{row.get('substrate_class') or 'unknown'}`",
                            fmt_number(row.get("net_saved_bytes")),
                            fmt_number(row.get("forecast_gap_remaining_bytes")),
                            f"`{str(row.get('promotion_ready_shadow')).lower()}`",
                            fmt_number(row.get("largest_block_regression_bytes")),
                            f"`{blockers_text}`",
                        ]
                    )
                    + " |"
                )
    blockers = summary.get("promotion_blocker_counts")
    if isinstance(blockers, dict) and blockers:
        lines.extend(["", "## Blocker Counts", "", "| Blocker | Receipts |", "|---|---:|"])
        for name, count in blockers.items():
            lines.append(f"| `{name}` | {fmt_number(count)} |")

    substrate_summary = summary.get("substrate_summary")
    if isinstance(substrate_summary, list) and substrate_summary:
        lines.extend(
            [
                "",
                "## Substrate Summary",
                "",
                "This separates SRSTC as a standalone raw-byte model from SRSTC as",
                "a correction layer on an existing probability trace.",
                "",
                "| Substrate | Receipts | Positive Net | Ready | Best Net | Best Held-out | Best Receipt |",
                "|---|---:|---:|---:|---:|---:|---|",
            ]
        )
        for group in substrate_summary:
            if not isinstance(group, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{group.get('substrate')}`",
                        fmt_number(group.get("receipts")),
                        fmt_number(group.get("positive_net_receipts")),
                        fmt_number(group.get("promotion_ready_shadow_receipts")),
                        fmt_number(group.get("best_net_saved_bytes")),
                        fmt_number(group.get("best_heldout_shadow_saved_bytes")),
                        f"`{group.get('best_receipt') or 'n/a'}`",
                    ]
                )
                + " |"
            )

    posterior_queue = summary.get("block_posterior_rerun_queue")
    if isinstance(posterior_queue, list) and posterior_queue:
        first_posterior = posterior_queue[0]
        first_posterior = first_posterior if isinstance(first_posterior, dict) else {}
        forecast_debt = BEST_FORECAST - TARGET_SCORE
        queued_code_budget = (
            as_int(first_posterior.get("added_code_bytes_estimate")) or 0
        ) + BLOCK_POSTERIOR_CODE_BYTES_ESTIMATE
        required_gross_after_router = forecast_debt + queued_code_budget
        existing_gross = as_float(first_posterior.get("heldout_shadow_saved_bytes"))
        available_degradation = (
            existing_gross - required_gross_after_router
            if existing_gross is not None
            else None
        )
        required_retention_pct = (
            required_gross_after_router * 100.0 / existing_gross
            if existing_gross
            else None
        )
        allowed_surrender_pct = (
            100.0 - required_retention_pct
            if required_retention_pct is not None
            else None
        )
        visible_regression_bytes = as_float(
            first_posterior.get("visible_block_regression_bytes")
        )
        visible_regression_share_pct = (
            visible_regression_bytes * 100.0 / existing_gross
            if visible_regression_bytes is not None and existing_gross
            else None
        )
        lines.extend(
            [
                "",
                "## Block-Posterior Replay Queue",
                "",
                "These complete-block receipts close the forecast gap but regress on",
                "isolated blocks. The queued causal experiment mixes the base and raw",
                "SRSTC experts with decoder-rebuilt fixed-point posterior weights.",
                "It is not searching for a fresh forecast-gap improvement; it is testing",
                "whether a replayable posterior can preserve enough of an already",
                "target-closing SRSTC shadow gain while insuring exceptional blocks.",
                "",
                "Economics:",
                "",
                "```text",
                f"required gross after router = {fmt_number(forecast_debt)} debt + {fmt_number(queued_code_budget)} code = {fmt_number(required_gross_after_router)}",
                f"existing gross             = {fmt_number(existing_gross)}",
                f"available degradation      = {fmt_number(available_degradation)}",
                f"required retention         = {fmt_number(required_retention_pct)}%",
                f"allowed surrender          = {fmt_number(allowed_surrender_pct)}%",
                f"observed regression bytes  = {fmt_number(visible_regression_bytes)} across {fmt_number(first_posterior.get('visible_block_regression_count'))} of {fmt_number(first_posterior.get('visible_block_rows'))} blocks",
                f"regression share of gross  = {fmt_number(visible_regression_share_pct)}%",
                "```",
                "",
                "The small-scope block-posterior probe is a fixed-cost amortization check,",
                "not counter-evidence to the mechanism: its role is to prove deterministic",
                "causal improvement before the queued same-scope replay tests retention.",
                "",
                "| Receipt | Net Saved | Largest Regression | Counted Router Delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in posterior_queue:
            if not isinstance(row, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row.get('path')}`",
                        fmt_number(row.get("net_saved_bytes")),
                        fmt_number(row.get("largest_block_regression_bytes")),
                        fmt_number(BLOCK_POSTERIOR_CODE_BYTES_ESTIMATE),
                    ]
                )
                + " |"
            )
        lines.extend(["", "Commands:", ""])
        for row in posterior_queue:
            command = (
                row.get("block_posterior_rerun_command")
                if isinstance(row, dict)
                else None
            )
            if isinstance(command, str) and command:
                lines.extend(["```bash", command, "```", ""])
        lines.extend(
            [
                "The lock-aware continuation helper selects this queue first:",
                "",
                "```bash",
                "python3 projects/enwiki9/tools/streaming_retrieval_continue_shadow.py --refresh-audit",
                "```",
                "",
                "Add `--run` only after it reports that the cmix heavy lock is clear.",
                "",
            ]
        )

    queue = summary.get("complete_block_rerun_queue")
    if isinstance(queue, list) and queue:
        lines.extend(
            [
                "",
                "## Complete-Block Rerun Queue",
                "",
                "These are cached positive-net raw SRSTC receipts whose next proof step is",
                "regenerating the same shadow run with complete block rows.",
                "",
                "| Receipt | Net Saved | Held-out Saved | Rerun Output |",
                "|---|---:|---:|---|",
            ]
        )
        for row in queue:
            if not isinstance(row, dict):
                continue
            command = row.get("complete_block_rerun_command")
            output = "n/a"
            if isinstance(command, str) and " --output " in command:
                output = command.split(" --output ", 1)[1].split(" ", 1)[0]
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row.get('path')}`",
                        fmt_number(row.get("net_saved_bytes")),
                        fmt_number(row.get("heldout_shadow_saved_bytes")),
                        f"`{output}`",
                    ]
                )
                + " |"
            )
        lines.extend(["", "Commands:", ""])
        for row in queue:
            command = row.get("complete_block_rerun_command") if isinstance(row, dict) else None
            if isinstance(command, str) and command:
                lines.extend(["```bash", command, "```", ""])
        lines.extend(
            [
                "Safe continuation helper:",
                "",
                "```bash",
                "python3 projects/enwiki9/tools/streaming_retrieval_continue_shadow.py --refresh-audit",
                "```",
                "",
                "Add `--run` only when the helper reports that the cmix heavy lock is clear.",
                "",
            ]
        )

    lines.extend(
        [
            "",
            "## Top Rows",
            "",
            "| Receipt | Net Saved | Held-out Saved | State Bytes | Block Audit | Largest Regression | Ready | Blockers |",
            "|---|---:|---:|---:|---|---:|---|---|",
        ]
    )
    for row in summary.get("top_rows", []):
        if not isinstance(row, dict):
            continue
        blockers_text = ", ".join(row.get("promotion_blockers") or ["none"])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('path')}`",
                    fmt_number(row.get("net_saved_bytes")),
                    fmt_number(row.get("heldout_shadow_saved_bytes")),
                    fmt_number(row.get("max_online_state_bytes")),
                    f"`{row.get('block_audit_source')}`",
                    fmt_number(row.get("largest_block_regression_bytes")),
                    f"`{str(row.get('promotion_ready_shadow')).lower()}`",
                    f"`{blockers_text}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Readout",
            "",
            "- A positive net receipt can justify more shadow work.",
            "- Raw-shadow promotion readiness does not prove additive transfer onto fx2 or cmix21.",
            "- Packaging requires a positive counted target-substrate replay, not only a raw-shadow win.",
            "- Existing receipts without full block rows should be regenerated with complete block diagnostics before packaging.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=pathlib.Path, default=RESULTS_DIR)
    parser.add_argument("--json-out", type=pathlib.Path, default=OUT_JSON)
    parser.add_argument("--md-out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--max-block-regression-bytes", type=float, default=0.0)
    parser.add_argument("--max-online-state-bytes", type=int, default=64_000_000)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config = AuditConfig(
        max_block_regression_bytes=args.max_block_regression_bytes,
        max_online_state_bytes=args.max_online_state_bytes,
    )
    summary = summarize(load_rows(args.results_dir, config), config)
    json_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    md_text = render_md(summary)
    if args.check:
        try:
            current_json = args.json_out.read_text()
            current_md = args.md_out.read_text()
        except OSError as exc:
            print(f"missing audit output: {exc}")
            return 1
        if current_json != json_text or current_md != md_text:
            print("stale streaming retrieval receipt audit")
            return 1
        print("streaming_retrieval_receipt_audit_up_to_date")
        return 0

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json_text)
    args.md_out.write_text(md_text)
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
