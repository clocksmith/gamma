#!/usr/bin/env python3
"""Summarize typed-anchor state as a Lane B handoff for fx2 integration."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import lzma
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"
DATA_DEFAULT = ROOT / "data" / "enwik9"
DEFAULT_CANDIDATE = "opcode_typed_anchor_bitmix_v1"
DEFAULT_OUT = ROOT / "docs" / "handoffs" / "lane_b_typed_anchor_handoff.json"

FIELD_NAMES = {
    0: "outside",
    1: "title",
    2: "id",
    3: "timestamp",
    4: "username",
    5: "comment",
    6: "text",
}

MODE_NAMES = {
    0: "plain",
    1: "wikilink",
    2: "template",
    3: "ref_or_tag",
}

SLOT_NAMES = {
    0: "none",
    1: "category",
    2: "image_or_file",
    3: "cite_template",
    4: "infobox",
    5: "ref",
    6: "ref_name",
    7: "template_url",
    8: "template_title",
    9: "references_section",
}

PAGE_KIND_NAMES = {
    0: "unknown",
    2: "list",
    3: "disambiguation",
    4: "normal_title_seen",
}

CHAR_CLASS_NAMES = {
    0: "other",
    1: "upper",
    2: "lower",
    3: "digit",
    4: "space",
    5: "xml_punctuation",
    6: "wiki_punctuation",
    7: "high_byte",
}


def load_payload(candidate: str) -> dict[str, Any]:
    candidate_dir = PROGRAMS / candidate
    payload = candidate_dir / "p"
    if not payload.exists():
        raise SystemExit(f"missing payload: {payload}")
    source = lzma.decompress(payload.read_bytes(), format=lzma.FORMAT_ALONE).decode()
    namespace: dict[str, Any] = {"__file__": str(candidate_dir / "program.py")}
    exec(source, namespace)
    for name in ("oe", "GST", "LIT"):
        if name not in namespace:
            raise SystemExit(f"{candidate} payload missing {name}")
    return namespace


def load_meta(candidate: str) -> dict[str, Any]:
    path = PROGRAMS / candidate / "meta.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data if isinstance(data, dict) else {}


def pct(part: int, total: int) -> float:
    return round((100.0 * part / total), 4) if total else 0.0


def named_counts(counter: collections.Counter[int], names: dict[int, str], total: int) -> list[dict[str, Any]]:
    rows = []
    for key, count in counter.most_common():
        rows.append(
            {
                "id": key,
                "name": names.get(key, str(key)),
                "count": count,
                "percent": pct(count, total),
            }
        )
    return rows


def latest_gate(meta: dict[str, Any], data_size: int) -> dict[str, Any] | None:
    runs = list((meta.get("measured") or {}).get("lane0_triage_runs") or [])
    candidates: list[dict[str, Any]] = []
    triage = (meta.get("measured") or {}).get("lane0_triage")
    if isinstance(triage, dict):
        runs.append(triage)
    for run in runs:
        for gate in run.get("gates") or []:
            if gate.get("data_size") == data_size:
                candidates.append(gate)
    return candidates[-1] if candidates else None


def parse_family_list(value: str) -> set[int]:
    families: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        family = int(item)
        if family < 0 or family >= 12:
            raise argparse.ArgumentTypeError("context family must be between 0 and 11")
        families.add(family)
    if not families:
        raise argparse.ArgumentTypeError("at least one context family is required")
    return families


def scan_state(
    stream: bytes,
    tracker_cls: Any,
    literal_cls: Any,
    tracked_families: set[int],
) -> dict[str, Any]:
    tracker = tracker_cls()
    literal = literal_cls()
    total = len(stream)
    fields: collections.Counter[int] = collections.Counter()
    modes: collections.Counter[int] = collections.Counter()
    slots: collections.Counter[int] = collections.Counter()
    page_kinds: collections.Counter[int] = collections.Counter()
    classes: collections.Counter[int] = collections.Counter()
    field_slot: collections.Counter[tuple[int, int]] = collections.Counter()
    mode_slot: collections.Counter[tuple[int, int]] = collections.Counter()
    context_family_unique = [set() if index in tracked_families else None for index in range(12)]
    context_family_updates = [0] * 12
    sse_buckets: set[tuple[int, int, int, int]] = set()

    for byte in stream:
        fields[tracker.f] += 1
        modes[tracker.w] += 1
        slots[tracker.slot] += 1
        page_kinds[tracker.pg] += 1
        classes[tracker.c] += 1
        field_slot[(tracker.f, tracker.slot)] += 1
        mode_slot[(tracker.w, tracker.slot)] += 1

        prefix = 1
        for bit_index in range(8):
            bit = (byte >> (7 - bit_index)) & 1
            probability, keys, sse_bucket, mixed, stretches, weights = literal.predict(
                tracker, prefix, bit_index
            )
            del probability
            sse_buckets.add(sse_bucket)
            for index, key in enumerate(keys):
                if context_family_unique[index] is not None:
                    context_family_unique[index].add(key)
                    context_family_updates[index] += 1
            literal.update(keys, sse_bucket, mixed, stretches, weights, bit)
            prefix = (prefix << 1) | bit
        tracker.up(byte)

    return {
        "stream_size": len(stream),
        "stream_sha256": hashlib.sha256(stream).hexdigest(),
        "field_counts": named_counts(fields, FIELD_NAMES, total),
        "mode_counts": named_counts(modes, MODE_NAMES, total),
        "slot_counts": named_counts(slots, SLOT_NAMES, total),
        "page_kind_counts": named_counts(page_kinds, PAGE_KIND_NAMES, total),
        "char_class_counts": named_counts(classes, CHAR_CLASS_NAMES, total),
        "top_field_slot": [
            {
                "field": FIELD_NAMES.get(field, str(field)),
                "slot": SLOT_NAMES.get(slot, str(slot)),
                "count": count,
                "percent": pct(count, total),
            }
            for (field, slot), count in field_slot.most_common(16)
        ],
        "top_mode_slot": [
            {
                "mode": MODE_NAMES.get(mode, str(mode)),
                "slot": SLOT_NAMES.get(slot, str(slot)),
                "count": count,
                "percent": pct(count, total),
            }
            for (mode, slot), count in mode_slot.most_common(16)
        ],
        "context_family_cardinality": [
            {
                "family": index,
                "unique": len(values),
                "updates": context_family_updates[index],
                "updates_per_unique": round(
                    context_family_updates[index] / len(values), 4
                )
                if values
                else 0.0,
            }
            for index, values in enumerate(context_family_unique)
            if values is not None
        ],
        "tracked_context_families": sorted(tracked_families),
        "sse_unique_buckets": len(sse_buckets),
    }


def analyze(candidate: str, data: bytes, limit: int, tracked_families: set[int]) -> dict[str, Any]:
    namespace = load_payload(candidate)
    encode_opcode = namespace["oe"]
    tracker_cls = namespace["GST"]
    literal_cls = namespace["LIT"]

    raw = data[:limit]
    encoded = encode_opcode(raw)
    raw_state = scan_state(raw, tracker_cls, literal_cls, tracked_families)
    opcode_state = scan_state(encoded, tracker_cls, literal_cls, tracked_families)

    return {
        "candidate": candidate,
        "raw_size": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "opcode_size": len(encoded),
        "opcode_sha256": hashlib.sha256(encoded).hexdigest(),
        "opcode_size_delta": len(encoded) - len(raw),
        "raw_stream_state": raw_state,
        "opcode_stream_state": opcode_state,
        "state_interpretation": (
            "opcode_stream_state matches the standalone candidate's physical "
            "preprocess path; raw_stream_state is the Lane A side-state target "
            "because fx2 should keep the original bytes intact."
        ),
        **opcode_state,
    }


def handoff(meta: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    gate_250k = latest_gate(meta, 250000)
    gate_1m = latest_gate(meta, 1000000)
    return {
        "lane": "B",
        "handoff_target": "Lane A fx2 native predictor work",
        "mechanism": "typed_anchor_soft_state",
        "evidence_parent": analysis["candidate"],
        "interpretation": (
            "This is a Lane B density signal, not proof that the standalone "
            "opcode backend is competitive with fx2. The useful part is the "
            "small recomputable state extractor; fx2 should consume those "
            "fields as weak learned coordinates and ignore them when noisy."
        ),
        "first_fx2_candidate_id": "fx2_typed_anchor_soft_sse_v1",
        "evidence": {
            "status": meta.get("status"),
            "verdict": meta.get("verdict"),
            "gate_250k": gate_250k,
            "gate_1m": gate_1m,
        },
        "state_registers": [
            {"name": "field", "bits": 3, "source": "GST.f"},
            {"name": "wiki_mode", "bits": 2, "source": "GST.w"},
            {"name": "slot", "bits": 4, "source": "GST.slot"},
            {"name": "page_kind", "bits": 3, "source": "GST.pg"},
            {"name": "char_class", "bits": 3, "source": "GST.c"},
            {"name": "column_bucket", "bits": 5, "source": "GST.col >> 3"},
        ],
        "candidate_integrations": [
            {
                "id": "fx2_typed_anchor_soft_sse_v1",
                "priority": 1,
                "description": (
                    "Condition a narrow SSE/APM-side coordinate on prediction "
                    "bucket, bit position, field, and slot while preserving "
                    "the original byte stream."
                ),
                "state": ["prediction_bucket", "bit_position", "field", "slot"],
                "risk": "low",
            },
            {
                "id": "fx2_typed_anchor_soft_mixer_v1",
                "priority": 2,
                "description": (
                    "Add one weak mixer context keyed by field, slot, wiki mode, "
                    "char class, and long_bit_context_."
                ),
                "state": ["field", "slot", "wiki_mode", "char_class", "long_bit_context"],
                "risk": "medium",
            },
            {
                "id": "fx2_typed_anchor_soft_prior_input_v1",
                "priority": 3,
                "description": (
                    "Replace broad structural prior with a narrow field/slot byte prior "
                    "as an ordinary mixer input, not a direct output clamp."
                ),
                "state": ["field", "slot", "wiki_mode", "byte_prefix"],
                "risk": "medium",
            },
        ],
        "do_not_port_first": [
            "physical opcode rewrite",
            "hard XOR mutation of mature fx2 contexts",
            "chain-copy opcode path",
            "direct final-probability forcing",
        ],
        "promotion_rule": [
            "compile as a native fx2 candidate",
            "compare archive bytes against the same fx2 parent at each scope",
            "promote only if 1M archive improves and larger gates preserve the gain",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default=DEFAULT_CANDIDATE)
    parser.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument(
        "--context-families",
        type=parse_family_list,
        default=parse_family_list("0,1,7,8,9,10,11"),
        help="Comma-separated LIT context family indexes to track for unique-cardinality reporting.",
    )
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    if args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")

    with args.data.open("rb") as handle:
        data = handle.read(args.limit)
    if not data:
        raise SystemExit(f"empty data prefix: {args.data}")

    meta = load_meta(args.candidate)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "analysis": analyze(args.candidate, data, len(data), args.context_families),
    }
    payload["handoff"] = handoff(meta, payload["analysis"])

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.stdout:
        print(text, end="")
    else:
        args.out.write_text(text)
        print(json.dumps({"out": str(args.out), "candidate": args.candidate}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
