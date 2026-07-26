#!/usr/bin/env python3
"""Screen causal hierarchical retrieval states against fx2 residual traces.

This is the RAG/embedding idea converted into a Hutter-admissible test.  Large
embedding models may be used offline as teachers, but the state scored here is
derived only from already-decoded enwiki9 bytes: page title, section, template,
parameter, link, URL, and a tiny learned schema predictor.

The tool does not compress.  It measures whether those deterministic retrieval
states can correct fx2 bit probabilities with a causal KT table.  A positive
held-out residual slope is the proof needed before moving anything into C++.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

from causal_state_screen import WikiState, bucket, char_class
from fx2_shadow_residual_coder import iter_rows as iter_residual_rows


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "hierarchical_retrieval_shadow" / "latest.json"
DEFAULT_BASELINE_SCORE = 110_181_114
DEFAULT_TARGET_SCORE = 109_000_000
DEFAULT_SCOPE_BYTES = 1_000_000_000
PAIR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^ \t]+)")
PREFIX = "FX2_RESIDUAL_ROW "
TOTAL = 1 << 16
FNV_OFFSET = 2166136261
FNV_PRIME = 16777619


def parse_value(value: str) -> Any:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def parse_row(line: str) -> dict[str, Any] | None:
    if PREFIX not in line:
        return None
    payload = line.split(PREFIX, 1)[1]
    pairs = PAIR_RE.findall(payload)
    if not pairs:
        return None
    return {key: parse_value(value) for key, value in pairs}


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp_p1(p1: int | float) -> int:
    return max(1, min(TOTAL - 1, int(p1)))


def prob_bucket(p1: int, buckets: int) -> int:
    if buckets <= 1:
        return 0
    return min(buckets - 1, (clamp_p1(p1) * buckets) >> 16)


def qbits_for(bit: int, p1: int | float) -> int:
    p1 = clamp_p1(p1)
    prob = p1 / TOTAL if bit else (TOTAL - p1) / TOTAL
    return int((-math.log2(prob)) * 256.0 + 0.5)


def fnv_update(h: int, byte: int) -> int:
    return ((h ^ byte) * FNV_PRIME) & 0xFFFFFFFF


def fnv_bytes(data: bytes) -> int:
    h = FNV_OFFSET
    for byte in data:
        h = fnv_update(h, byte)
    return h


def stable_bucket(value: int, bits: int) -> int:
    if bits <= 0:
        return 0
    return value & ((1 << bits) - 1)


def is_name_byte(byte: int) -> bool:
    return (
        48 <= byte <= 57
        or 65 <= byte <= 90
        or 97 <= byte <= 122
        or byte in (45, 95)
    )


def section_kind(text: bytes) -> int:
    text = re.sub(rb"\s+", b" ", text.strip().lower())
    if not text:
        return 0
    if b"reference" in text or b"bibliograph" in text or b"further reading" in text:
        return 1
    if b"external link" in text or text in {b"links", b"weblinks"}:
        return 2
    if b"see also" in text or b"related" in text:
        return 3
    if b"history" in text or b"origin" in text or b"background" in text:
        return 4
    if b"geograph" in text or b"climate" in text or b"location" in text:
        return 5
    if b"demograph" in text or b"population" in text or b"people" in text:
        return 6
    if b"government" in text or b"politic" in text or b"law" in text:
        return 7
    if b"transport" in text or b"econom" in text or b"industry" in text:
        return 8
    if b"culture" in text or b"religion" in text or b"society" in text:
        return 9
    if b"early life" in text or b"career" in text or b"personal life" in text:
        return 10
    if b"plot" in text or b"characters" in text or b"synopsis" in text:
        return 11
    if b"works" in text or b"publications" in text or b"filmography" in text:
        return 12
    if b"awards" in text or b"honours" in text or b"legacy" in text:
        return 13
    if b"table" in text or b"statistics" in text or b"data" in text:
        return 14
    return 15


@dataclass
class SchemaEdge:
    counts: dict[int, int] = field(default_factory=dict)

    def best(self) -> int:
        if not self.counts:
            return 0
        return max(self.counts.items(), key=lambda item: (item[1], -item[0]))[0]

    def update(self, value: int) -> None:
        self.counts[value] = self.counts.get(value, 0) + 1


@dataclass
class HierarchicalRetrievalState:
    """Byte-causal page/chunk memory learned from decoded history."""

    wiki: WikiState = field(default_factory=WikiState)
    tail: bytearray = field(default_factory=bytearray)
    page_title_hash: int = 0
    section_hash: int = 0
    section_kind: int = 0
    template_hash: int = 0
    template_name_hash: int = 0
    param_hash: int = 0
    link_hash: int = 0
    url_domain_hash: int = 0
    current_title: bytearray = field(default_factory=bytearray)
    current_section: bytearray = field(default_factory=bytearray)
    current_template_name: bytearray = field(default_factory=bytearray)
    current_param_name: bytearray = field(default_factory=bytearray)
    current_link: bytearray = field(default_factory=bytearray)
    current_url_domain: bytearray = field(default_factory=bytearray)
    capture_title: bool = False
    capture_template_name: bool = False
    capture_param_name: bool = False
    capture_link: bool = False
    capture_section: bool = False
    capture_url_domain: bool = False
    line_eq_prefix: int = 0
    line_started_with_eq: bool = False
    last_param_hash: int = 0
    schema_table: dict[tuple[int, int], SchemaEdge] = field(default_factory=dict)

    def features(self) -> dict[str, Any]:
        base = self.wiki.features()
        page_title = stable_bucket(self.page_title_hash, 10)
        section = stable_bucket(self.section_hash, 10)
        template = stable_bucket(self.template_hash or self.template_name_hash, 10)
        param = stable_bucket(self.param_hash, 10)
        link = stable_bucket(self.link_hash, 10)
        url_domain = stable_bucket(self.url_domain_hash, 8)
        schema_expect = self.schema_expectation()
        chunk_kind = (
            base["field"],
            base["mode"],
            base["slot"],
            bucket(self.wiki.column, (0, 4, 16, 48, 96)),
        )
        topic_bucket = stable_bucket(
            (self.page_title_hash * 1315423911)
            ^ (self.section_hash * 2654435761)
            ^ (self.template_hash * 2246822519),
            12,
        )
        retrieval16 = stable_bucket(
            (page_title * 1_000_003)
            ^ (section * 100_019)
            ^ (template * 10_007)
            ^ (param * 1_009)
            ^ (link * 101)
            ^ (url_domain * 31)
            ^ schema_expect,
            12,
        )
        base.update(
            {
                "page_title": page_title,
                "section": section,
                "section_kind": self.section_kind,
                "template": template,
                "param": param,
                "link": link,
                "url_domain": url_domain,
                "schema_expect": schema_expect,
                "chunk_kind": chunk_kind,
                "topic_bucket": topic_bucket,
                "retrieval16": retrieval16,
                "field_mode_retrieval": (base["field"], base["mode"], retrieval16),
                "template_schema": (template, schema_expect),
                "section_topic": (section, topic_bucket),
                "section_kind_topic": (self.section_kind, topic_bucket),
                "link_topic": (link, topic_bucket),
                "url_slot": (url_domain, base["slot"]),
            }
        )
        return base

    def schema_expectation(self) -> int:
        template = stable_bucket(self.template_hash or self.template_name_hash, 12)
        prev_param = stable_bucket(self.last_param_hash, 12)
        edge = self.schema_table.get((template, prev_param))
        return stable_bucket(edge.best() if edge else 0, 10)

    def _tail_endswith(self, value: bytes) -> bool:
        return bytes(self.tail).lower().endswith(value)

    def _finish_param_name(self) -> None:
        if not self.current_param_name:
            return
        new_param = fnv_bytes(bytes(self.current_param_name).lower())
        template = stable_bucket(self.template_hash or self.template_name_hash, 12)
        prev_param = stable_bucket(self.last_param_hash, 12)
        self.schema_table.setdefault((template, prev_param), SchemaEdge()).update(
            stable_bucket(new_param, 12)
        )
        self.last_param_hash = new_param
        self.param_hash = new_param
        self.current_param_name.clear()

    def _reset_page(self) -> None:
        self.section_hash = 0
        self.section_kind = 0
        self.template_hash = 0
        self.template_name_hash = 0
        self.param_hash = 0
        self.link_hash = 0
        self.url_domain_hash = 0
        self.current_section.clear()
        self.current_template_name.clear()
        self.current_param_name.clear()
        self.current_link.clear()
        self.current_url_domain.clear()
        self.last_param_hash = 0

    def update(self, byte: int) -> None:
        prev1 = self.wiki.prev1
        prev2 = self.wiki.prev2
        self.tail.append(byte)
        if len(self.tail) > 192:
            del self.tail[:64]
        lower_tail = bytes(self.tail).lower()

        if lower_tail.endswith(b"<page>"):
            self._reset_page()
            self.page_title_hash = 0

        if lower_tail.endswith(b"<title>"):
            self.capture_title = True
            self.current_title.clear()
        elif self.capture_title and lower_tail.endswith(b"</title>"):
            title = bytes(self.current_title[:-7]).strip().lower()
            self.page_title_hash = fnv_bytes(title)
            self.capture_title = False
            self.current_title.clear()
        elif self.capture_title:
            self.current_title.append(byte)

        if self.wiki.line_start and byte == 61:
            self.capture_section = True
            self.line_started_with_eq = True
            self.line_eq_prefix = 1
            self.current_section.clear()
        elif self.capture_section:
            if byte == 10:
                text = bytes(self.current_section).strip(b"= \t\r").lower()
                if text:
                    self.section_hash = fnv_bytes(text)
                    self.section_kind = section_kind(text)
                self.capture_section = False
                self.line_started_with_eq = False
                self.line_eq_prefix = 0
                self.current_section.clear()
            else:
                if self.line_started_with_eq and byte == 61:
                    self.line_eq_prefix = min(6, self.line_eq_prefix + 1)
                elif byte not in (61, 32, 9, 13) or self.current_section:
                    self.line_started_with_eq = False
                    if len(self.current_section) < 96:
                        self.current_section.append(byte)

        if prev1 == 123 and byte == 123:
            self.capture_template_name = True
            self.current_template_name.clear()
            self.template_name_hash = 0
            self.param_hash = 0
            self.last_param_hash = 0
        elif self.capture_template_name:
            if byte in (124, 10, 125):
                name = bytes(self.current_template_name).strip().lower()
                if name:
                    self.template_hash = fnv_bytes(name)
                    self.template_name_hash = self.template_hash
                self.capture_template_name = False
                self.current_template_name.clear()
                if byte == 124:
                    self.capture_param_name = True
                    self.current_param_name.clear()
            elif len(self.current_template_name) < 96:
                self.current_template_name.append(byte)

        if self.wiki.template_depth > 0:
            if byte == 124:
                self._finish_param_name()
                self.capture_param_name = True
                self.current_param_name.clear()
            elif self.capture_param_name:
                if byte == 61:
                    self._finish_param_name()
                    self.capture_param_name = False
                elif is_name_byte(byte) or byte in (32,):
                    if len(self.current_param_name) < 64:
                        self.current_param_name.append(byte)
                elif byte not in (9, 13):
                    self.capture_param_name = False
                    self.current_param_name.clear()
        elif self.capture_param_name:
            self._finish_param_name()
            self.capture_param_name = False

        if prev1 == 91 and byte == 91:
            self.capture_link = True
            self.current_link.clear()
            self.link_hash = 0
        elif self.capture_link:
            if byte in (124, 93, 10):
                link = bytes(self.current_link).strip().lower()
                if link:
                    self.link_hash = fnv_bytes(link)
                if byte != 124:
                    self.capture_link = False
                    self.current_link.clear()
            elif len(self.current_link) < 128:
                self.current_link.append(byte)
        if prev1 == 93 and byte == 93:
            self.capture_link = False
            self.current_link.clear()

        if lower_tail.endswith(b"http://") or lower_tail.endswith(b"https://"):
            self.capture_url_domain = True
            self.current_url_domain.clear()
            self.url_domain_hash = 0
        elif self.capture_url_domain:
            if byte in (47, 32, 9, 10, 13, 124, 93, 125, 60):
                domain = bytes(self.current_url_domain).strip().lower()
                if domain:
                    self.url_domain_hash = fnv_bytes(domain)
                self.capture_url_domain = False
                self.current_url_domain.clear()
            elif len(self.current_url_domain) < 96:
                self.current_url_domain.append(byte)

        if prev2 == 125 and prev1 == 125:
            self.template_hash = 0
            self.param_hash = 0
            self.last_param_hash = 0
            self.capture_template_name = False
            self.capture_param_name = False
            self.current_template_name.clear()
            self.current_param_name.clear()

        self.wiki.update(byte)
        _ = char_class(byte)


@dataclass
class BitCounter:
    zeros: int = 0
    ones: int = 0

    def p1(self, alpha: float) -> float:
        total = self.zeros + self.ones
        return TOTAL * (self.ones + alpha) / (total + 2.0 * alpha)

    def update(self, bit: int) -> None:
        if bit:
            self.ones += 1
        else:
            self.zeros += 1


@dataclass
class Totals:
    rows: int = 0
    baseline_qbits: int = 0
    corrected_qbits: int = 0

    @property
    def gain_bits(self) -> float:
        return (self.baseline_qbits - self.corrected_qbits) / 256.0

    @property
    def gain_bits_per_bit(self) -> float:
        return self.gain_bits / self.rows if self.rows else 0.0


@dataclass
class Model:
    fields: tuple[str, ...]
    p_buckets: int
    blend_ppm: int
    alpha: float
    counters: dict[tuple[Any, ...], BitCounter] = field(default_factory=dict)
    totals: dict[str, Totals] = field(
        default_factory=lambda: {"train": Totals(), "test": Totals(), "all": Totals()}
    )

    @property
    def name(self) -> str:
        return ",".join(self.fields)

    def make_key(self, row: dict[str, Any], features: dict[str, Any], p1: int) -> tuple[Any, ...]:
        values: list[Any] = []
        for field_name in self.fields:
            if field_name == "p_bucket":
                values.append(prob_bucket(p1, self.p_buckets))
            elif field_name in features:
                values.append(features[field_name])
            else:
                values.append(row.get(field_name, 0))
        return tuple(values)

    def update(self, row: dict[str, Any], features: dict[str, Any], split: str) -> None:
        bit = as_int(row, "bit", -1)
        if bit not in {0, 1}:
            return
        base_p1 = clamp_p1(as_int(row, "p1", 32768))
        base_qbits = as_int(row, "baseline_qbits", qbits_for(bit, base_p1))
        key = self.make_key(row, features, base_p1)
        counter = self.counters.setdefault(key, BitCounter())
        blend = max(0.0, min(1.0, self.blend_ppm / 1_000_000.0))
        corrected_p1 = base_p1 + (counter.p1(self.alpha) - base_p1) * blend
        corrected_qbits = qbits_for(bit, corrected_p1)

        for name in (split, "all"):
            total = self.totals[name]
            total.rows += 1
            total.baseline_qbits += base_qbits
            total.corrected_qbits += corrected_qbits
            if split == "all":
                break
        counter.update(bit)

    def to_json(self, scope_bytes: int, code_cost_bytes: int, rank_split: str) -> dict[str, Any]:
        splits: dict[str, dict[str, Any]] = {}
        for name, total in self.totals.items():
            projected_gain_bytes = total.gain_bits_per_bit * scope_bytes
            splits[name] = {
                "rows": total.rows,
                "baseline_bits": total.baseline_qbits / 256.0,
                "corrected_bits": total.corrected_qbits / 256.0,
                "gain_bits": total.gain_bits,
                "gain_bytes": total.gain_bits / 8.0,
                "gain_bits_per_bit": total.gain_bits_per_bit,
                "projected_gain_1g_bytes_non_proof": projected_gain_bytes,
                "projected_net_after_code_1g_bytes_non_proof": projected_gain_bytes
                - code_cost_bytes,
            }
        ranked = splits[rank_split]
        return {
            "key": self.name,
            "p_buckets": self.p_buckets,
            "blend_ppm": self.blend_ppm,
            "alpha": self.alpha,
            "unique_contexts": len(self.counters),
            "updates_per_context": self.totals["all"].rows / len(self.counters)
            if self.counters
            else 0.0,
            "splits": splits,
            "rank_gain_bits": ranked["gain_bits"],
            "rank_projected_net_bytes_non_proof": ranked[
                "projected_net_after_code_1g_bytes_non_proof"
            ],
        }


def default_specs() -> list[tuple[str, ...]]:
    return [
        ("p_bucket", "bit_pos"),
        ("p_bucket", "bit_pos", "field", "mode"),
        ("p_bucket", "bit_pos", "field", "mode", "char_class"),
        ("p_bucket", "bit_pos", "chunk_kind"),
        ("p_bucket", "bit_pos", "page_title"),
        ("p_bucket", "bit_pos", "section"),
        ("p_bucket", "bit_pos", "section_kind"),
        ("p_bucket", "bit_pos", "template"),
        ("p_bucket", "bit_pos", "param"),
        ("p_bucket", "bit_pos", "schema_expect"),
        ("p_bucket", "bit_pos", "template_schema"),
        ("p_bucket", "bit_pos", "link"),
        ("p_bucket", "bit_pos", "url_domain"),
        ("p_bucket", "bit_pos", "topic_bucket"),
        ("p_bucket", "bit_pos", "retrieval16"),
        ("p_bucket", "bit_pos", "field_mode_retrieval"),
        ("p_bucket", "bit_pos", "section_topic"),
        ("p_bucket", "bit_pos", "section_kind_topic"),
        ("p_bucket", "bit_pos", "link_topic"),
        ("p_bucket", "bit_pos", "url_slot"),
        ("bit_pos", "retrieval16"),
        ("bit_pos", "template_schema"),
    ]


def parse_specs(values: list[str]) -> list[tuple[str, ...]]:
    if not values:
        return default_specs()
    specs: list[tuple[str, ...]] = []
    for value in values:
        fields = tuple(part for part in value.split(",") if part)
        if fields:
            specs.append(fields)
    return specs


def split_for(pos: int, train_bytes: int) -> str:
    if train_bytes <= 0:
        return "all"
    return "train" if pos < train_bytes else "test"


def advance_state(state: HierarchicalRetrievalState, data: bytes, next_pos: int, current_pos: int) -> int:
    if next_pos < current_pos:
        raise ValueError("residual rows must be nondecreasing by pos")
    while current_pos < next_pos:
        if current_pos >= len(data):
            raise ValueError(f"residual row position {next_pos} exceeds data length {len(data)}")
        state.update(data[current_pos])
        current_pos += 1
    return current_pos


def run_residual(args: argparse.Namespace) -> dict[str, Any]:
    data = args.data.read_bytes()
    if args.data_limit > 0:
        data = data[: args.data_limit]

    specs = parse_specs(args.spec)
    p_buckets = [int(part) for part in args.p_buckets.split(",") if part]
    blends = [int(part) for part in args.blend_ppm.split(",") if part]
    models = [
        Model(fields=spec, p_buckets=buckets, blend_ppm=blend, alpha=args.alpha)
        for spec in specs
        for buckets in p_buckets
        for blend in blends
    ]
    state = HierarchicalRetrievalState()
    current_pos = 0
    rows = 0
    min_pos: int | None = None
    max_pos: int | None = None

    for row in iter_residual_rows(args.log):
            pos = as_int(row, "pos", -1)
            if pos < 0:
                continue
            if args.max_rows > 0 and rows >= args.max_rows:
                break
            current_pos = advance_state(state, data, pos, current_pos)
            features = state.features()
            split = split_for(pos, args.train_bytes)
            for model in models:
                model.update(row, features, split)
            rows += 1
            min_pos = pos if min_pos is None else min(min_pos, pos)
            max_pos = pos if max_pos is None else max(max_pos, pos)

    rank_split = args.rank_split
    if rank_split == "test" and args.train_bytes <= 0:
        rank_split = "all"
    ranked = [
        model.to_json(
            scope_bytes=args.scope_bytes,
            code_cost_bytes=args.code_cost_bytes,
            rank_split=rank_split,
        )
        for model in models
    ]
    ranked.sort(
        key=lambda item: (
            -float(item["splits"][rank_split]["gain_bits"]),
            int(item["unique_contexts"]),
            item["key"],
            int(item["p_buckets"]),
            int(item["blend_ppm"]),
        )
    )
    required_net_bytes = args.baseline_score - args.target_score
    return {
        "mode": "fx2_residual_hierarchical_retrieval_shadow",
        "log": str(args.log),
        "data": str(args.data),
        "data_bytes_loaded": len(data),
        "rows": rows,
        "position_span": {"min_pos": min_pos, "max_pos": max_pos},
        "train_bytes": args.train_bytes,
        "rank_split": rank_split,
        "causality": (
            "state is built from data bytes strictly before row.pos; all bits of "
            "the current byte share the same pre-byte parser/retrieval state"
        ),
        "target": {
            "baseline_score": args.baseline_score,
            "target_score": args.target_score,
            "required_net_gain_bytes": required_net_bytes,
            "required_net_gain_bits": required_net_bytes * 8,
            "scope_bytes": args.scope_bytes,
            "code_cost_bytes_assumed": args.code_cost_bytes,
        },
        "teacher_policy": {
            "embedding_models": "allowed offline only",
            "decoder_state": "page/template/link/schema buckets derived from decoded bytes",
            "counted_payload_rule": "model weights are not assumed to be in the decompressor",
        },
        "specs_tested": len(ranked),
        "top": ranked[: args.top],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=pathlib.Path)
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--data-limit", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--spec", action="append", default=[])
    parser.add_argument("--p-buckets", default="16,32")
    parser.add_argument("--blend-ppm", default="25000,50000,125000")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--train-bytes", type=int, default=0)
    parser.add_argument("--rank-split", choices=["all", "train", "test"], default="test")
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--baseline-score", type=int, default=DEFAULT_BASELINE_SCORE)
    parser.add_argument("--target-score", type=int, default=DEFAULT_TARGET_SCORE)
    parser.add_argument("--scope-bytes", type=int, default=DEFAULT_SCOPE_BYTES)
    parser.add_argument("--code-cost-bytes", type=int, default=4096)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"missing log: {args.log}")
    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")
    if args.baseline_score < args.target_score:
        raise SystemExit("--baseline-score must be >= --target-score")
    if args.scope_bytes <= 0:
        raise SystemExit("--scope-bytes must be positive")
    if args.code_cost_bytes < 0:
        raise SystemExit("--code-cost-bytes must be non-negative")

    result = run_residual(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    if args.print_summary:
        print(
            f"rows={result['rows']} specs_tested={result['specs_tested']} "
            f"rank_split={result['rank_split']}"
        )
        for i, item in enumerate(result["top"][:10], 1):
            split = item["splits"][result["rank_split"]]
            print(
                f"{i}. key={item['key']} buckets={item['p_buckets']} "
                f"blend={item['blend_ppm']} gain_bits={split['gain_bits']:.6f} "
                f"gain_bpb={split['gain_bits_per_bit']:.9f} "
                f"projected_net={split['projected_net_after_code_1g_bytes_non_proof']:.2f} "
                f"contexts={item['unique_contexts']}"
            )
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
