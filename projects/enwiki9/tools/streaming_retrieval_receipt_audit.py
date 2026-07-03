#!/usr/bin/env python3
"""Audit SRSTC streaming-retrieval shadow receipts.

The audit is deliberately conservative: a positive shadow receipt is not marked
promotion-ready unless it has held-out savings, alignment safety, bounded
online state, and complete block-regression evidence.
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
    return {
        "path": rel(path),
        "verdict": str(receipt.get("verdict") or "incomplete"),
        "method": str(receipt.get("method") or "unknown"),
        "base_trace": str(receipt.get("base_trace") or "unknown"),
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
        "complete_block_rerun_command": rerun_command,
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
        "substrate_summary": substrate_summary,
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
                "Add `--run` only when the helper reports that the cmix heavy lock is clear,",
                "or pass `--allow-while-heavy-lock` intentionally.",
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
            "- A promotion-ready receipt requires complete block evidence before any compressor integration.",
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
