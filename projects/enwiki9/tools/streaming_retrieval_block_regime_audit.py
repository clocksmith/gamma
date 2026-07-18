#!/usr/bin/env python3
"""Describe the corpus regimes behind SRSTC winning and losing blocks.

This is an offline teacher-only audit.  It reads complete labeled blocks from a
cached shadow receipt, so its features are not admissible decoder state.  The
output exists to identify small causal parser/router features worth distilling.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import pathlib
import re
from collections import Counter
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT = (
    ROOT
    / "results"
    / "streaming_retrieval_shadow"
    / "raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json"
)
DEFAULT_JSON = ROOT / "docs" / "streaming_retrieval_block_regime_audit.json"
DEFAULT_MD = ROOT / "docs" / "streaming_retrieval_block_regime_audit.md"
DEFAULT_MANIFEST = ROOT / "docs" / "streaming_retrieval_block_teacher_manifest.jsonl"
CANONICAL_ENWIK9_SHA256 = (
    "a8dee03d6b1636a7ffe5912f91b23e475f321456505ea6e41e44b349353520c7"
)

MARKERS: dict[str, bytes] = {
    "page_open": b"<page",
    "page_close": b"</page",
    "title_open": b"<title>",
    "text_open": b"<text",
    "text_close": b"</text>",
    "wikilink_open": b"[[",
    "template_open": b"{{",
    "ref_open": b"<ref",
    "table_open": b"{|",
    "url_http": b"http",
    "entity_escape": b"&",
}

TITLE_RE = re.compile(rb"<title>(.*?)</title>", re.DOTALL)
HEADING_RE = re.compile(rb"(?m)^={2,5}[^\n]{1,160}?={2,5}\s*$")


def load_json(path: pathlib.Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_receipt_with_manifest_recovery(
    receipt_path: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if receipt_path.exists():
        return load_json(receipt_path), None
    if receipt_path.resolve() != DEFAULT_RECEIPT.resolve():
        raise FileNotFoundError(receipt_path)
    if not DEFAULT_MANIFEST.is_file():
        raise FileNotFoundError(
            f"missing source receipt and recovery manifest: {receipt_path}"
        )

    block_rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(DEFAULT_MANIFEST.read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"manifest row {line_number} is not an object")
        block_id = as_int(row.get("block_id"), -1)
        source_bytes = as_int(row.get("source_bytes"), 0)
        expected_offset = block_id * 16_384
        if block_id != len(block_rows):
            raise ValueError(
                f"manifest row {line_number} is not contiguous: {block_id}"
            )
        if as_int(row.get("offset_bytes"), -1) != expected_offset:
            raise ValueError(f"manifest row {line_number} has a bad offset")
        if source_bytes != 16_384:
            raise ValueError(f"manifest row {line_number} has a bad byte count")
        gain_bytes = float(row.get("gain_bytes", 0))
        if bool(row.get("regression_label")) != (gain_bytes < 0):
            raise ValueError(f"manifest row {line_number} has a bad label")
        block_rows.append(
            {
                "block_id": block_id,
                "gain_bytes": gain_bytes,
                "rows": source_bytes * 8,
            }
        )
    if len(block_rows) != 4_000:
        raise ValueError(f"unexpected recovery manifest rows: {len(block_rows)}")

    receipt = {
        "receipt_type": "streaming_retrieval_shadow",
        "sketch_schema": {"block_bytes": 16_384},
        "data": str(ROOT / "data" / "enwik9"),
        "data_sha256": CANONICAL_ENWIK9_SHA256,
        "block_rows": block_rows,
    }
    recovery = {
        "mode": "preserved_teacher_manifest",
        "reason": "original ignored result overlay is absent in this checkout",
        "manifest": DEFAULT_MANIFEST.resolve().relative_to(ROOT).as_posix(),
        "manifest_sha256": sha256(DEFAULT_MANIFEST),
        "rows": len(block_rows),
    }
    return receipt, recovery


def as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_text(value: bytes) -> str:
    return html.unescape(value.decode("utf-8", errors="replace")).strip()


def marker_counts(data: bytes) -> dict[str, int]:
    counts = {name: data.count(marker) for name, marker in MARKERS.items()}
    counts["headings"] = len(HEADING_RE.findall(data))
    counts["lines"] = data.count(b"\n")
    return counts


def byte_classes(data: bytes) -> dict[str, float]:
    size = max(1, len(data))
    classes = Counter()
    for byte in data:
        if 65 <= byte <= 90 or 97 <= byte <= 122:
            classes["alpha"] += 1
        elif 48 <= byte <= 57:
            classes["digit"] += 1
        elif byte in (9, 10, 13, 32):
            classes["whitespace"] += 1
        elif byte in b"<>/\"&;=[]{}|":
            classes["markup_punctuation"] += 1
        elif byte >= 128:
            classes["non_ascii"] += 1
        else:
            classes["other"] += 1
    return {name: count / size for name, count in sorted(classes.items())}


def read_span(path: pathlib.Path, offset: int, size: int) -> bytes:
    with path.open("rb") as source:
        source.seek(max(0, offset))
        return source.read(size)


def describe_block(
    data_path: pathlib.Path,
    block_id: int,
    block_bytes: int,
    gain_bytes: float,
    label: str,
) -> dict[str, Any]:
    offset = block_id * block_bytes
    data = read_span(data_path, offset, block_bytes)
    context_start = max(0, offset - 2 * block_bytes)
    context = read_span(data_path, context_start, 5 * block_bytes)
    prefix_sizes = (512, 2048)
    return {
        "block_id": block_id,
        "label": label,
        "gain_bytes": gain_bytes,
        "offset_bytes": offset,
        "source_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "nearby_titles_teacher_only": [
            clean_text(match) for match in TITLE_RE.findall(context)
        ],
        "headings_teacher_only": [
            clean_text(match) for match in HEADING_RE.findall(data)[:16]
        ],
        "full_block_teacher_only": {
            "marker_counts": marker_counts(data),
            "byte_class_shares": byte_classes(data),
        },
        "causal_prefix_checkpoints": {
            str(size): {
                "marker_counts": marker_counts(data[:size]),
                "byte_class_shares": byte_classes(data[:size]),
            }
            for size in prefix_sizes
        },
    }


def mean_marker_counts(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {}
    names = sorted(MARKERS) + ["headings", "lines"]
    return {
        name: sum(
            row["full_block_teacher_only"]["marker_counts"].get(name, 0)
            for row in rows
        )
        / len(rows)
        for name in names
    }


def teacher_split(block_id: int, block_count: int) -> str:
    train_end = block_count // 2
    validation_end = (block_count * 3) // 4
    if block_id < train_end:
        return "train"
    if block_id < validation_end:
        return "validation"
    return "test"


def build(receipt_path: pathlib.Path, control_count: int) -> dict[str, Any]:
    receipt, source_recovery = load_receipt_with_manifest_recovery(receipt_path)
    if receipt.get("receipt_type") != "streaming_retrieval_shadow":
        raise ValueError("receipt is not a streaming_retrieval_shadow")
    schema = receipt.get("sketch_schema")
    schema = schema if isinstance(schema, dict) else {}
    block_bytes = as_int(schema.get("block_bytes"), 16_384)
    data_path = pathlib.Path(str(receipt.get("data") or ROOT / "data" / "enwik9"))
    if not data_path.is_absolute():
        candidate = ROOT.parent.parent / data_path
        data_path = candidate if candidate.exists() else data_path
    if not data_path.exists():
        raise FileNotFoundError(data_path)
    raw_rows = receipt.get("block_rows")
    if not isinstance(raw_rows, list):
        raise ValueError("receipt has no complete block_rows")
    block_rows = [row for row in raw_rows if isinstance(row, dict)]
    block_count = len(block_rows)
    regressions = [row for row in block_rows if float(row.get("gain_bytes", 0)) < 0]
    positive = [row for row in block_rows if float(row.get("gain_bytes", 0)) > 0]
    positive.sort(key=lambda row: float(row.get("gain_bytes", 0)))
    controls = positive[: max(control_count, len(regressions))]

    regression_rows = [
        describe_block(
            data_path,
            as_int(row.get("block_id"), -1),
            block_bytes,
            float(row.get("gain_bytes", 0)),
            "regression",
        )
        for row in regressions
    ]
    control_rows = [
        describe_block(
            data_path,
            as_int(row.get("block_id"), -1),
            block_bytes,
            float(row.get("gain_bytes", 0)),
            "weak_positive_control",
        )
        for row in controls
    ]
    teacher_rows = []
    split_counts: Counter[str] = Counter()
    split_regressions: Counter[str] = Counter()
    for row in sorted(block_rows, key=lambda item: as_int(item.get("block_id"), -1)):
        block_id = as_int(row.get("block_id"), -1)
        gain_bytes = float(row.get("gain_bytes", 0))
        split = teacher_split(block_id, block_count)
        is_regression = gain_bytes < 0
        split_counts[split] += 1
        if is_regression:
            split_regressions[split] += 1
        teacher_rows.append(
            {
                "block_id": block_id,
                "offset_bytes": block_id * block_bytes,
                "source_bytes": as_int(row.get("rows"), block_bytes * 8) // 8,
                "gain_bytes": gain_bytes,
                "regression_label": is_regression,
                "split": split,
                "teacher_text_view": "full_block",
                "distillation_prefix_checkpoints_bytes": [512, 2048, 8192],
            }
        )
    return {
        "receipt_type": "streaming_retrieval_block_regime_audit",
        "evidence_level": "offline_teacher_only",
        "source_receipt": receipt_path.resolve().relative_to(ROOT).as_posix(),
        "source_receipt_recovery": source_recovery,
        "data": str(data_path),
        "data_sha256": receipt.get("data_sha256"),
        "block_bytes": block_bytes,
        "regression_count": len(regression_rows),
        "regression_bytes": sum(-row["gain_bytes"] for row in regression_rows),
        "regression_blocks": regression_rows,
        "weak_positive_controls": control_rows,
        "group_marker_means": {
            "regression": mean_marker_counts(regression_rows),
            "weak_positive_control": mean_marker_counts(control_rows),
        },
        "teacher_manifest_summary": {
            "rows": len(teacher_rows),
            "split_rows": dict(sorted(split_counts.items())),
            "split_regressions": dict(sorted(split_regressions.items())),
            "label": "continuous SRSTC gain_bytes plus regression_label",
            "split_policy": (
                "contiguous 50/25/25 block split; the three regressions land "
                "one each in train, validation, and test"
            ),
        },
        "_teacher_manifest_rows": teacher_rows,
        "claim_boundary": (
            "full-block labels, titles, headings, and counts are teacher-only; "
            "a final router may use only prefix checkpoints or a distilled "
            "decoder-rebuilt rule validated by exact replay"
        ),
    }


def render_md(payload: dict[str, Any]) -> str:
    rows = payload["regression_blocks"] + payload["weak_positive_controls"]
    lines = [
        "# Streaming Retrieval Block Regime Audit",
        "",
        "This is offline teacher evidence, not an admissible decoder feature table.",
        "",
        f"- Source receipt: `{payload['source_receipt']}`",
        f"- Block bytes: `{payload['block_bytes']:,}`",
        f"- Regression blocks: `{payload['regression_count']}`",
        f"- Total visible regression: `{payload['regression_bytes']:.3f}` bytes",
        f"- Teacher manifest rows: `{payload['teacher_manifest_summary']['rows']:,}`",
        f"- Teacher manifest: `{payload['teacher_manifest']}`",
    ]
    recovery = payload.get("source_receipt_recovery")
    if isinstance(recovery, dict):
        lines.append(
            "- Source recovery: preserved teacher manifest "
            f"`{recovery['manifest']}` (`{recovery['rows']:,}` rows)"
        )
    lines.extend(
        [
        "",
        "| Label | Block | Gain Bytes | Nearby Titles | Links | Templates | URLs | Headings | Pages |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        counts = row["full_block_teacher_only"]["marker_counts"]
        titles = "; ".join(row["nearby_titles_teacher_only"][:4]) or "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['label']}`",
                    str(row["block_id"]),
                    f"{row['gain_bytes']:.3f}",
                    titles.replace("|", "\\|"),
                    str(counts["wikilink_open"]),
                    str(counts["template_open"]),
                    str(counts["url_http"]),
                    str(counts["headings"]),
                    str(counts["page_open"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Readout",
            "",
            "The regressions are not confined to one XML delimiter mode. They include",
            "long prose spans with dense headings and links as well as a page-boundary",
            "block. Use these labels for teacher discovery, but distill only causal",
            "prefix rules and compare them against the block-posterior loss router.",
            "The JSONL manifest exposes all block offsets and continuous gain labels",
            "with one regression in each contiguous train/validation/test split.",
            "",
            f"Claim boundary: {payload['claim_boundary']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=pathlib.Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--control-count", type=int, default=3)
    parser.add_argument("--json-out", type=pathlib.Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=pathlib.Path, default=DEFAULT_MD)
    parser.add_argument("--manifest-out", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.control_count < 0:
        raise SystemExit("--control-count must be nonnegative")
    payload = build(args.receipt, args.control_count)
    teacher_rows = payload.pop("_teacher_manifest_rows")
    payload["teacher_manifest"] = args.manifest_out.resolve().relative_to(ROOT).as_posix()
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    md_text = render_md(payload)
    manifest_text = "".join(
        json.dumps(row, sort_keys=True) + "\n" for row in teacher_rows
    )
    if args.check:
        if (
            args.json_out.read_text() != json_text
            or args.md_out.read_text() != md_text
            or args.manifest_out.read_text() != manifest_text
        ):
            raise SystemExit("stale streaming retrieval block regime audit")
        print("streaming_retrieval_block_regime_audit_up_to_date")
        return 0
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json_text)
    args.md_out.write_text(md_text)
    args.manifest_out.write_text(manifest_text)
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    print(f"wrote {args.manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
