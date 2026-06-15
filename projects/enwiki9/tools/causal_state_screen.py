#!/usr/bin/env python3
"""Rank causal XML/wiki parser states by online predictive information gain.

This is a fast Lane B screening tool, not a compressor.  It tests whether a
deterministic state that can be reconstructed from already-decoded bytes has
predictive value for the next byte after controlling for a simple local-history
baseline.  Promising states become candidates for fx2 SSE/mixer soft inputs.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DEFAULT = ROOT / "data" / "enwik9"
OUT_DEFAULT = ROOT / "causal_state_screen.json"
STRICT_TARGET_GAP_BYTES = 681_114


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
    3: "xml_or_ref_tag",
    4: "table",
}

SLOT_NAMES = {
    0: "none",
    1: "category",
    2: "file",
    3: "cite",
    4: "infobox",
    5: "ref",
    6: "ref_name",
    7: "url",
    8: "title_param",
    9: "references_section",
}


def char_class(byte: int) -> int:
    if 65 <= byte <= 90:
        return 1
    if 97 <= byte <= 122:
        return 2
    if 48 <= byte <= 57:
        return 3
    if byte in (9, 10, 13, 32):
        return 4
    if byte in (60, 62, 47, 34, 38, 59, 61):
        return 5
    if byte in (91, 93, 123, 124, 125):
        return 6
    if byte >= 128:
        return 7
    return 0


def bucket(value: int, cuts: tuple[int, ...]) -> int:
    for index, cut in enumerate(cuts):
        if value <= cut:
            return index
    return len(cuts)


@dataclass
class WikiState:
    """Causal parser state updated after each observed byte."""

    field_id: int = 0
    mode: int = 0
    slot: int = 0
    page_kind: int = 0
    link_depth: int = 0
    template_depth: int = 0
    table_depth: int = 0
    tag_depth: int = 0
    ref_depth: int = 0
    column: int = 0
    line_start: bool = True
    prev1: int = 0
    prev2: int = 0
    prev3: int = 0
    prev_class: int = 0
    word_len: int = 0
    word_class: int = 0
    title_seen: bool = False
    tail: bytearray = field(default_factory=bytearray)

    def features(self) -> dict[str, Any]:
        depth_sig = (
            bucket(self.link_depth, (0, 1, 2)),
            bucket(self.template_depth, (0, 1, 2)),
            bucket(self.table_depth, (0, 1)),
            bucket(self.ref_depth, (0, 1)),
        )
        col_bucket = bucket(self.column, (0, 4, 16, 48, 96))
        word_sig = (bucket(self.word_len, (0, 1, 3, 7, 15)), self.word_class)
        field_mode = (self.field_id, self.mode)
        mode_slot = (self.mode, self.slot)
        field_slot = (self.field_id, self.slot)
        return {
            "field": self.field_id,
            "mode": self.mode,
            "slot": self.slot,
            "page_kind": self.page_kind,
            "depth_sig": depth_sig,
            "field_mode": field_mode,
            "field_slot": field_slot,
            "mode_slot": mode_slot,
            "field_mode_slot": (self.field_id, self.mode, self.slot),
            "field_depth": (self.field_id, depth_sig),
            "mode_depth": (self.mode, depth_sig),
            "slot_depth": (self.slot, depth_sig),
            "column_bucket": col_bucket,
            "field_column": (self.field_id, col_bucket),
            "mode_column": (self.mode, col_bucket),
            "word_sig": word_sig,
            "field_word": (self.field_id, word_sig),
            "mode_word": (self.mode, word_sig),
            "prev_class": self.prev_class,
            "field_prev_class": (self.field_id, self.prev_class),
            "mode_prev_class": (self.mode, self.prev_class),
            "page_field_mode": (self.page_kind, self.field_id, self.mode),
        }

    def update(self, byte: int) -> None:
        self.tail.append(byte)
        if len(self.tail) > 160:
            del self.tail[:64]
        tail = bytes(self.tail)
        lower = tail.lower()

        if byte == 10:
            self.column = 0
            self.line_start = True
        else:
            self.column = min(255, self.column + 1)
            if byte not in (9, 13, 32):
                self.line_start = False

        if self.prev1 == 91 and byte == 91:
            self.link_depth = min(7, self.link_depth + 1)
            self.mode = 1
        elif self.prev1 == 93 and byte == 93:
            self.link_depth = max(0, self.link_depth - 1)
            if self.link_depth == 0 and self.mode == 1:
                self.mode = 0
                if self.slot in (1, 2):
                    self.slot = 0
        elif self.prev1 == 123 and byte == 123:
            self.template_depth = min(7, self.template_depth + 1)
            self.mode = 2
        elif self.prev1 == 125 and byte == 125:
            self.template_depth = max(0, self.template_depth - 1)
            if self.template_depth == 0 and self.mode == 2:
                self.mode = 0
                if self.slot in (3, 4, 7, 8):
                    self.slot = 0
        elif self.prev1 == 123 and byte == 124:
            self.table_depth = min(3, self.table_depth + 1)
            self.mode = 4
        elif self.prev1 == 124 and byte == 125:
            self.table_depth = max(0, self.table_depth - 1)
            if self.table_depth == 0 and self.mode == 4:
                self.mode = 0
        elif self.prev1 == 60:
            self.tag_depth = min(3, self.tag_depth + 1)
            self.mode = 3
        elif byte == 62 and self.tag_depth:
            self.tag_depth = max(0, self.tag_depth - 1)
            if self.tag_depth == 0 and self.mode == 3 and self.ref_depth == 0:
                self.mode = 0

        if lower.endswith(b"[[category:"):
            self.slot = 1
        elif lower.endswith(b"[[image:") or lower.endswith(b"[[file:"):
            self.slot = 2
        elif lower.endswith(b"{{cite"):
            self.slot = 3
        elif lower.endswith(b"{{infobox"):
            self.slot = 4
        elif lower.endswith(b"<ref"):
            self.slot = 5
            self.ref_depth = min(3, self.ref_depth + 1)
            self.mode = 3
        elif lower.endswith(b'name="') or lower.endswith(b"name='"):
            if self.slot == 5:
                self.slot = 6
        elif self.mode == 2 and lower.endswith(b"url="):
            self.slot = 7
        elif self.mode == 2 and lower.endswith(b"title="):
            self.slot = 8
        elif lower.endswith(b"==references=="):
            self.slot = 9
        elif lower.endswith(b"</ref>"):
            self.ref_depth = max(0, self.ref_depth - 1)
            if self.ref_depth == 0:
                self.slot = 0
                if self.mode == 3:
                    self.mode = 0

        if tail.endswith(b"<title>"):
            self.field_id = 1
            self.title_seen = False
        elif tail.endswith(b"</title>"):
            title_tail = lower[-120:]
            if b"list of" in title_tail:
                self.page_kind = 2
            elif b"disambiguation" in title_tail:
                self.page_kind = 3
            else:
                self.page_kind = 4
            self.field_id = 0
            self.title_seen = True
        elif tail.endswith(b"<id>"):
            self.field_id = 2
        elif tail.endswith(b"</id>"):
            self.field_id = 0
        elif tail.endswith(b"<timestamp>"):
            self.field_id = 3
        elif tail.endswith(b"</timestamp>"):
            self.field_id = 0
        elif tail.endswith(b"<username>"):
            self.field_id = 4
        elif tail.endswith(b"</username>"):
            self.field_id = 0
        elif tail.endswith(b"<comment>"):
            self.field_id = 5
        elif tail.endswith(b"</comment>"):
            self.field_id = 0
        elif tail.endswith(b'<text xml:space="preserve">'):
            self.field_id = 6
            self.slot = 0
            self.mode = 0
        elif tail.endswith(b"</text>"):
            self.field_id = 0
            self.slot = 0
            self.mode = 0
            self.link_depth = 0
            self.template_depth = 0
            self.table_depth = 0
            self.ref_depth = 0

        cls = char_class(byte)
        if cls in (1, 2):
            self.word_len = min(31, self.word_len + 1)
            self.word_class = cls
        elif cls == 3:
            self.word_len = min(31, self.word_len + 1)
            self.word_class = 3
        else:
            self.word_len = 0
            self.word_class = cls

        self.prev3 = self.prev2
        self.prev2 = self.prev1
        self.prev1 = byte
        self.prev_class = cls


class AdaptiveByteModel:
    def __init__(self, alpha: int = 1):
        self.alpha = alpha
        self.contexts: dict[Any, list[int]] = {}

    def loss_then_update(self, key: Any, byte: int) -> float:
        counts = self.contexts.get(key)
        if counts is None:
            counts = [0] * 257
            self.contexts[key] = counts
        total = counts[256]
        count = counts[byte]
        loss = math.log2((total + 256 * self.alpha) / (count + self.alpha))
        counts[byte] = count + 1
        counts[256] = total + 1
        return loss


@dataclass
class Candidate:
    name: str
    fn: Callable[[WikiState], Any]
    model: AdaptiveByteModel = field(default_factory=AdaptiveByteModel)
    bits: float = 0.0
    unique_values: set[Any] = field(default_factory=set)
    unique_contexts: set[Any] = field(default_factory=set)


def make_candidates() -> list[Candidate]:
    names = [
        "field",
        "mode",
        "slot",
        "page_kind",
        "depth_sig",
        "field_mode",
        "field_slot",
        "mode_slot",
        "field_mode_slot",
        "field_depth",
        "mode_depth",
        "slot_depth",
        "column_bucket",
        "field_column",
        "mode_column",
        "word_sig",
        "field_word",
        "mode_word",
        "prev_class",
        "field_prev_class",
        "mode_prev_class",
        "page_field_mode",
    ]

    def build(name: str) -> Candidate:
        return Candidate(name=name, fn=lambda state, key=name: state.features()[key])

    return [build(name) for name in names]


def screen(data: bytes, limit: int, alpha: int) -> dict[str, Any]:
    raw = data[:limit]
    state = WikiState()
    base = AdaptiveByteModel(alpha=alpha)
    candidates = make_candidates()
    base_bits = 0.0

    for byte in raw:
        base_key = state.prev1
        base_bits += base.loss_then_update(base_key, byte)
        for cand in candidates:
            value = cand.fn(state)
            key = (base_key, value)
            cand.bits += cand.model.loss_then_update(key, byte)
            cand.unique_values.add(value)
            cand.unique_contexts.add(key)
        state.update(byte)

    rows = []
    for cand in candidates:
        bits_saved = base_bits - cand.bits
        bpb_saved = bits_saved / len(raw) if raw else 0.0
        projected_bytes = bpb_saved * 1_000_000_000 / 8
        rows.append(
            {
                "candidate": cand.name,
                "bits_saved": round(bits_saved, 6),
                "bits_per_byte_saved": round(bpb_saved, 9),
                "projected_archive_saving_1g_bytes": round(projected_bytes, 2),
                "max_added_program_bytes_for_10_95": math.floor(
                    projected_bytes - STRICT_TARGET_GAP_BYTES
                ),
                "unique_state_values": len(cand.unique_values),
                "unique_contexts": len(cand.unique_contexts),
                "updates_per_context": round(len(raw) / len(cand.unique_contexts), 4)
                if cand.unique_contexts
                else 0.0,
                "verdict": "fx2_candidate"
                if projected_bytes > STRICT_TARGET_GAP_BYTES
                else "below_10_95_proxy_threshold",
            }
        )

    rows.sort(
        key=lambda row: (
            row["projected_archive_saving_1g_bytes"],
            row["updates_per_context"],
        ),
        reverse=True,
    )
    return {
        "data_size": len(raw),
        "baseline_model": "adaptive prev_byte byte distribution, alpha=1",
        "candidate_model": "adaptive (prev_byte, causal_state) byte distribution",
        "causality": "state is read before the current byte and updated after the byte",
        "target": {
            "strict_10_95_score": 109_500_000,
            "current_projected_path": 110_181_114,
            "required_net_gain_bytes": STRICT_TARGET_GAP_BYTES,
            "required_bits_per_byte_before_program_cost": round(
                STRICT_TARGET_GAP_BYTES * 8 / 1_000_000_000, 9
            ),
        },
        "base_bits": round(base_bits, 6),
        "base_bits_per_byte": round(base_bits / len(raw), 9) if raw else 0.0,
        "ranked_states": rows,
        "top_states": rows[:8],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    parser.add_argument("--limit", type=int, default=250_000)
    parser.add_argument("--alpha", type=int, default=1)
    parser.add_argument("--json-out", type=pathlib.Path, default=OUT_DEFAULT)
    parser.add_argument("--print-top", type=int, default=12)
    args = parser.parse_args()

    if args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.alpha <= 0:
        raise SystemExit("--alpha must be positive")
    if not args.data.exists():
        raise SystemExit(f"dataset missing: {args.data}")

    result = screen(args.data.read_bytes(), args.limit, args.alpha)
    args.json_out.write_text(json.dumps(result, indent=2) + "\n")

    for row in result["ranked_states"][: args.print_top]:
        print(
            f"{row['candidate']:>18} "
            f"saved_bpb={row['bits_per_byte_saved']:.9f} "
            f"projected_1g_bytes={row['projected_archive_saving_1g_bytes']:.2f} "
            f"values={row['unique_state_values']} "
            f"contexts={row['unique_contexts']} "
            f"verdict={row['verdict']}"
        )
    print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
