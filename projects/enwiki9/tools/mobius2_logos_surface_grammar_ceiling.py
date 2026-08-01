#!/usr/bin/env python3
"""Run the exact opening-1M MOBIUS-2 LOGOS surface-grammar ceiling."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
from typing import Any, Sequence

import numpy as np

from radix_island_oracle import emission_groups
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_logos_surface_grammar_ceiling_q0_v1"
PROPOSAL_ID = "mobius2_logos_surface_grammar_ceiling_v1"
CANDIDATE_PROGRAM = ROOT / "programs" / CANDIDATE_ID / "program.py"
WIKIIR_PROGRAM = ROOT / "programs" / "wikiir_template_grammar_v1" / "program.py"
PLAN_PATH = ROOT / "docs" / "mobius2_logos_surface_grammar_ceiling_plan.md"
SCHEMA_PATH = (
    ROOT / "docs" / "mobius2_logos_surface_grammar_ceiling_decision.schema.json"
)
DEFAULT_P1 = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_online_native_1m_v1/native.p1"
)
DEFAULT_WRT = Path("/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin")
DEFAULT_RAW = Path(
    "/home/x/enwiki9-nonproof/results/"
    "fx2_full_attribution_trace_1m_v1.restored"
)
DEFAULT_ARCHIVE = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_online_native_1m_v1/archive.bin"
)
DEFAULT_DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/"
    "cmix21-lstm200-plus-fx2lite428-onlinepairlayer0-v17/english.dic"
)
DEFAULT_BACKEND = Path(
    "/home/x/enwiki9-nonproof/results/"
    "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
    "clean-build-b/build/cmix.bin"
)
DEFAULT_MANIFEST = ROOT / "results" / "endpoint_final_trace_1m_v1" / "manifest.json"
DEFAULT_NATIVE_RECEIPT = (
    ROOT / "results" / "endpoint428_pair_layer0_online_native_1m_v1" / "receipt.json"
)
DEFAULT_PAGE_MAP = ROOT / "results" / "endpoint_final_trace_1m_v1" / "page_map.bin"
P1_MAGIC = b"CMX21P1\0"
PAGE_MAP_MAGIC = b"SIBMAP1\0"
PAGE_MAP_RECORD = struct.Struct("<QQQQ")
QBITS_PER_BIT = 256
QBITS_PER_BYTE = 2048
GROSS_GATE_BYTES_PER_MILLION = 3000.0
NET_GATE_BYTES_PER_MILLION = 2100.0


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


candidate = load_module("mobius2_logos_candidate", CANDIDATE_PROGRAM)
wikiir = load_module("mobius2_logos_wikiir_discovery", WIKIIR_PROGRAM)
Rule = candidate.Rule
Invocation = candidate.Invocation


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str


@dataclass(frozen=True)
class Occurrence:
    page_index: int
    split: str
    raw_start: int
    raw_end: int
    target_start: int
    target_end: int
    segments: tuple[bytes, ...]
    hole_lengths: tuple[int, ...]
    fixed_qbits: int

    @property
    def key(self) -> tuple[bytes, ...]:
        return self.segments

    @property
    def fixed_bytes(self) -> int:
        return sum(map(len, self.segments))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def bind_artifact(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    if path.stat().st_size != expected.get("bytes"):
        raise ValueError(f"{label} size differs from bound manifest")
    if sha256_file(path) != expected.get("sha256"):
        raise ValueError(f"{label} SHA-256 differs from bound manifest")


def read_p1(path: Path, expected_rows: int) -> np.memmap:
    with path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid CMX21P1 trace header")
    rows = int.from_bytes(header[8:16], "little")
    if rows != expected_rows or path.stat().st_size != 16 + rows * 2:
        raise ValueError("P1 rows differ from the exact WRT truth stream")
    return np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))


def parent_payload(archive: bytes, wrt_bytes: int) -> tuple[bytes, int]:
    if len(archive) < 5:
        raise ValueError("parent archive is truncated")
    declared = archive[0] & 0x7F
    for value in archive[1:5]:
        declared = (declared << 8) | value
    if declared != wrt_bytes:
        raise ValueError("parent archive declares a different WRT length")
    header_bytes = 5 if declared < 10_000 else 37
    if len(archive) <= header_bytes:
        raise ValueError("parent archive has no arithmetic payload")
    return archive[header_bytes:], header_bytes


def read_pages(path: Path, expected_sha256: str, wrt_bytes: int) -> list[Page]:
    if sha256_file(path) != expected_sha256:
        raise ValueError("page map differs from bound manifest")
    data = path.read_bytes()
    if len(data) < 16 or data[:8] != PAGE_MAP_MAGIC:
        raise ValueError("invalid page-map header")
    count = struct.unpack_from("<Q", data, 8)[0]
    if len(data) != 16 + count * PAGE_MAP_RECORD.size:
        raise ValueError("page-map length differs from declared records")
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    pages: list[Page] = []
    for index in range(count):
        raw_start, raw_end, row_start, row_end = PAGE_MAP_RECORD.unpack_from(
            data, 16 + index * PAGE_MAP_RECORD.size
        )
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not WRT-byte aligned")
        split = (
            "development"
            if index < development_end
            else "selection"
            if index < selection_end
            else "sealed_confirmation"
        )
        page = Page(
            index,
            raw_start,
            raw_end,
            row_start // 8,
            row_end // 8,
            split,
        )
        if not 0 <= page.wrt_start < page.wrt_end <= wrt_bytes:
            raise ValueError("page map exceeds WRT stream")
        pages.append(page)
    return pages


def qbit_costs(probabilities: np.ndarray, truth: bytes) -> np.ndarray:
    values = np.arange(65536, dtype=np.float64) / 65536.0
    one = np.clip(values, 1.0 / 65536.0, 65535.0 / 65536.0)
    zero = 1.0 - one
    one_table = np.rint(-np.log2(one) * QBITS_PER_BIT).astype(np.int32)
    zero_table = np.rint(-np.log2(zero) * QBITS_PER_BIT).astype(np.int32)
    bits = np.unpackbits(np.frombuffer(truth, dtype=np.uint8), bitorder="big")
    selected = np.where(bits != 0, one_table[probabilities], zero_table[probabilities])
    return selected.reshape(len(truth), 8).sum(axis=1, dtype=np.int64)


def raw_to_wrt_boundaries(parsed: Any) -> dict[int, int]:
    groups = emission_groups(parsed)
    boundaries: dict[int, int] = {0: 6}
    for group in groups:
        if boundaries.setdefault(group.raw_start, group.stream_start) != group.stream_start:
            raise ValueError("ambiguous raw-to-WRT start boundary")
        if boundaries.setdefault(group.raw_end, group.stream_end) != group.stream_end:
            raise ValueError("ambiguous raw-to-WRT end boundary")
    if boundaries.get(len(parsed.decoded)) != len(parsed.stream):
        raise ValueError("raw-to-WRT boundaries do not cover the stream")
    return boundaries


def page_for_span(pages: Sequence[Page], starts: Sequence[int], start: int, end: int) -> Page | None:
    index = bisect_right(starts, start) - 1
    if index < 0:
        return None
    page = pages[index]
    return page if page.raw_start <= start < end <= page.raw_end else None


def map_occurrences(
    raw: bytes,
    wrt: bytes,
    parsed: Any,
    pages: Sequence[Page],
    byte_costs: np.ndarray,
) -> tuple[list[Occurrence], dict[str, int]]:
    boundaries = raw_to_wrt_boundaries(parsed)
    page_starts = [page.raw_start for page in pages]
    mapped: list[Occurrence] = []
    outside_pages = 0
    unaligned = 0
    unparameterized = 0
    for raw_start, raw_end, raw_segments, raw_holes in wikiir._scan(raw):
        page = page_for_span(pages, page_starts, raw_start, raw_end)
        if page is None:
            outside_pages += 1
            continue
        if len(raw_segments) != len(raw_holes) + 2:
            raise ValueError("WikiIR ordered-template arity contract differs")
        if not raw_holes:
            unparameterized += 1
            continue
        ordered_segments = (
            raw_segments[0] + raw_segments[1],
            *raw_segments[2:],
        )
        cursor = raw_start
        segment_spans: list[tuple[int, int]] = []
        hole_spans: list[tuple[int, int]] = []
        valid = True
        for index, segment in enumerate(ordered_segments):
            segment_end = cursor + len(segment)
            if raw[cursor:segment_end] != segment:
                raise ValueError("WikiIR segment does not match raw input")
            if cursor not in boundaries or segment_end not in boundaries:
                valid = False
                break
            segment_spans.append((boundaries[cursor], boundaries[segment_end]))
            cursor = segment_end
            if index < len(raw_holes):
                hole = raw_holes[index]
                hole_end = cursor + len(hole)
                if raw[cursor:hole_end] != hole:
                    raise ValueError("WikiIR hole does not match raw input")
                if cursor not in boundaries or hole_end not in boundaries:
                    valid = False
                    break
                hole_spans.append((boundaries[cursor], boundaries[hole_end]))
                cursor = hole_end
        if not valid or cursor != raw_end:
            unaligned += 1
            continue
        segments = tuple(wrt[start:end] for start, end in segment_spans)
        if any(not segment for segment in segments):
            unaligned += 1
            continue
        hole_lengths = tuple(end - start for start, end in hole_spans)
        target_start = segment_spans[0][0]
        target_end = segment_spans[-1][1]
        rebuilt = bytearray()
        for index, segment in enumerate(segments):
            rebuilt += segment
            if index < len(hole_spans):
                start, end = hole_spans[index]
                rebuilt += wrt[start:end]
        if bytes(rebuilt) != wrt[target_start:target_end]:
            raise ValueError("mapped grammar occurrence does not cover exact WRT bytes")
        fixed_qbits = sum(
            int(byte_costs[start:end].sum()) for start, end in segment_spans
        )
        mapped.append(
            Occurrence(
                page.index,
                page.split,
                raw_start,
                raw_end,
                target_start,
                target_end,
                segments,
                hole_lengths,
                fixed_qbits,
            )
        )
    return mapped, {
        "raw_templates_parsed": len(wikiir._scan(raw)),
        "mapped_occurrences": len(mapped),
        "outside_complete_pages": outside_pages,
        "unaligned_occurrences": unaligned,
        "unparameterized_occurrences": unparameterized,
    }


def grouped_occurrences(
    occurrences: Sequence[Occurrence],
) -> dict[tuple[bytes, ...], list[Occurrence]]:
    groups: dict[tuple[bytes, ...], list[Occurrence]] = defaultdict(list)
    for occurrence in occurrences:
        groups[occurrence.key].append(occurrence)
    return dict(groups)


def ordered_candidate_keys(
    groups: dict[tuple[bytes, ...], list[Occurrence]],
) -> list[tuple[bytes, ...]]:
    keys = [
        key
        for key, rows in groups.items()
        if sum(row.split == "development" for row in rows) >= 2
    ]
    return sorted(keys, key=lambda key: min(row.target_start for row in groups[key]))


def invocation_for(occurrence: Occurrence, rule_id: int) -> Any:
    return Invocation(occurrence.target_start, rule_id, occurrence.hole_lengths)


def select_paid_rules(
    groups: dict[tuple[bytes, ...], list[Occurrence]],
    candidate_keys: Sequence[tuple[bytes, ...]],
) -> tuple[tuple[Any, ...], tuple[Any, ...], dict[int, Occurrence], dict[str, Any]]:
    active = list(candidate_keys)
    iterations = 0
    while True:
        iterations += 1
        key_to_id = {key: index for index, key in enumerate(active)}
        retained: list[tuple[bytes, ...]] = []
        for key in active:
            rule_id = key_to_id[key]
            rule = Rule(key)
            net = -candidate.rule_definition_bytes(rule) * QBITS_PER_BYTE
            paying_development = 0
            for row in groups[key]:
                if row.split != "development":
                    continue
                invocation = invocation_for(row, rule_id)
                local = row.fixed_qbits - candidate.invocation_bytes(invocation) * QBITS_PER_BYTE
                if local > 0:
                    net += local
                    paying_development += 1
            if paying_development >= 2 and net > 0:
                retained.append(key)
        if retained == active:
            break
        active = retained
        if not active or iterations > len(candidate_keys) + 1:
            break

    rules = tuple(Rule(key) for key in active)
    key_to_id = {key: index for index, key in enumerate(active)}
    selected: list[Any] = []
    occurrence_by_start: dict[int, Occurrence] = {}
    local_net_qbits = 0
    for key in active:
        rule_id = key_to_id[key]
        for row in groups[key]:
            invocation = invocation_for(row, rule_id)
            local = row.fixed_qbits - candidate.invocation_bytes(invocation) * QBITS_PER_BYTE
            if local <= 0:
                continue
            selected.append(invocation)
            occurrence_by_start[row.target_start] = row
            local_net_qbits += local
    selected.sort(key=lambda invocation: invocation.target_start)
    invocations = tuple(selected)
    definition_bytes = sum(candidate.rule_definition_bytes(rule) for rule in rules)
    return rules, invocations, occurrence_by_start, {
        "selection_iterations": iterations,
        "selected_rules": len(rules),
        "selected_invocations": len(invocations),
        "definition_bytes_without_counts": definition_bytes,
        "local_net_qbits_before_definitions": local_net_qbits,
        "predicted_net_qbits_after_definitions": (
            local_net_qbits - definition_bytes * QBITS_PER_BYTE
        ),
    }


def build_control(
    name: str,
    wrt: bytes,
    probabilities: np.ndarray,
    rules: Sequence[Any],
    invocations: Sequence[Any],
    generate: bool,
    output_dir: Path,
) -> tuple[dict[str, Any], bytes, bytes]:
    archive = candidate.build_archive(wrt, probabilities, rules, invocations, generate)
    decoded, decoded_rules, decoded_invocations = candidate.decode_archive(
        archive, probabilities
    )
    second = candidate.build_archive(wrt, probabilities, rules, invocations, generate)
    control = candidate.encode_control(rules, invocations, len(wrt))
    header = candidate.HEADER.unpack_from(archive)
    literal_bits = int(header[5])
    literal_payload_bytes = int(header[6])
    result = {
        "name": name,
        "mode": "generate" if generate else "forced_literal",
        "archive_bytes": len(archive),
        "archive_sha256": sha256_bytes(archive),
        "frame_bytes": candidate.HEADER.size,
        "control_bytes": len(control),
        "control_sha256": sha256_bytes(control),
        "rule_count": len(rules),
        "invocation_count": len(invocations),
        "fixed_wrt_bytes": sum(
            len(segment)
            for invocation in invocations
            for segment in rules[invocation.rule_id].segments
        ),
        "literal_bits": literal_bits,
        "literal_payload_bytes": literal_payload_bytes,
        "control_roundtrip_ok": (
            decoded_rules == tuple(rules)
            and decoded_invocations == tuple(invocations)
            and candidate.encode_control(decoded_rules, decoded_invocations, len(wrt))
            == control
        ),
        "wrt_roundtrip_ok": decoded == wrt,
        "deterministic_archive_ok": second == archive,
    }
    (output_dir / f"{name.lower()}.archive").write_bytes(archive)
    return result, archive, decoded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1)
    parser.add_argument("--wrt-store", type=Path, default=DEFAULT_WRT)
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--parent-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--backend", type=Path, default=DEFAULT_BACKEND)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--native-receipt", type=Path, default=DEFAULT_NATIVE_RECEIPT)
    parser.add_argument("--page-map", type=Path, default=DEFAULT_PAGE_MAP)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required = (
        args.p1,
        args.wrt_store,
        args.raw_input,
        args.parent_archive,
        args.dictionary,
        args.backend,
        args.manifest,
        args.native_receipt,
        args.page_map,
        CANDIDATE_PROGRAM,
        WIKIIR_PROGRAM,
        PLAN_PATH,
        SCHEMA_PATH,
    )
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing required artifact: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=False)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    native_receipt = json.loads(args.native_receipt.read_text(encoding="utf-8"))
    bound = manifest.get("artifacts")
    if not isinstance(bound, dict):
        raise ValueError("trace manifest has no artifact bindings")
    for label, path in (
        ("p1_trace", args.p1),
        ("wrt_store", args.wrt_store),
        ("raw_input", args.raw_input),
        ("archive", args.parent_archive),
        ("dictionary", args.dictionary),
        ("page_map", args.page_map),
    ):
        expected = bound.get(label)
        if not isinstance(expected, dict):
            raise ValueError(f"trace manifest does not bind {label}")
        bind_artifact(path, expected, label)

    stored = args.wrt_store.read_bytes()
    if len(stored) <= 5 or stored[:5] != b"\x80\0\0\0\0":
        raise ValueError("invalid outer WRT store header")
    wrt = stored[5:]
    raw = args.raw_input.read_bytes()
    parsed = parse_store(args.wrt_store, args.dictionary)
    if parsed.stream != wrt or parsed.decoded != raw:
        raise ValueError("exact WRT parse does not reproduce bound raw input")
    probabilities = read_p1(args.p1, len(wrt) * 8)
    parent_archive_data = args.parent_archive.read_bytes()
    receipt_parent_payload, parent_header_bytes = parent_payload(
        parent_archive_data, len(wrt)
    )
    replay_payload = candidate.range_encode(wrt, probabilities)
    if replay_payload != receipt_parent_payload:
        raise ValueError("E0 final-P1 replay is not parent-payload identical")

    pages = read_pages(args.page_map, bound["page_map"]["sha256"], len(wrt))
    byte_costs = qbit_costs(probabilities, wrt)
    occurrences, mapping_stats = map_occurrences(
        raw, wrt, parsed, pages, byte_costs
    )
    groups = grouped_occurrences(occurrences)
    candidate_keys = ordered_candidate_keys(groups)
    candidate_rules = tuple(Rule(key) for key in candidate_keys)
    candidate_key_to_id = {key: index for index, key in enumerate(candidate_keys)}
    oracle_invocations = tuple(
        sorted(
            (
                invocation_for(row, candidate_key_to_id[key])
                for key in candidate_keys
                for row in groups[key]
            ),
            key=lambda invocation: invocation.target_start,
        )
    )
    oracle_payload, oracle_literal_bits = candidate.encode_literal_payload(
        wrt,
        probabilities,
        candidate_rules,
        oracle_invocations,
        True,
    )
    optimistic_exact_gain = len(receipt_parent_payload) - len(oracle_payload)
    optimistic_qbits = sum(
        row.fixed_qbits for key in candidate_keys for row in groups[key]
    )

    rules, invocations, selected_rows, selection_stats = select_paid_rules(
        groups, candidate_keys
    )
    s1, _s1_archive, decoded_s1 = build_control(
        "S1", wrt, probabilities, rules, invocations, True, args.output_dir
    )
    sl, _sl_archive, _decoded_sl = build_control(
        "SL", wrt, probabilities, rules, invocations, False, args.output_dir
    )
    s1["gross_saved_bytes_vs_parent_archive"] = len(parent_archive_data) - s1["archive_bytes"]
    sl["gross_saved_bytes_vs_parent_archive"] = len(parent_archive_data) - sl["archive_bytes"]
    s1["generated_gain_vs_forced_literal_bytes"] = sl["archive_bytes"] - s1["archive_bytes"]

    split_controls: dict[str, dict[str, Any]] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        split_invocations = tuple(
            invocation
            for invocation in invocations
            if selected_rows[invocation.target_start].split == split
        )
        generated, _archive, _decoded = build_control(
            f"S1_{split}",
            wrt,
            probabilities,
            rules,
            split_invocations,
            True,
            args.output_dir,
        )
        literal, _literal_archive, _literal_decoded = build_control(
            f"SL_{split}",
            wrt,
            probabilities,
            rules,
            split_invocations,
            False,
            args.output_dir,
        )
        generated["forced_literal_archive_bytes"] = literal["archive_bytes"]
        generated["generated_gain_vs_forced_literal_bytes"] = (
            literal["archive_bytes"] - generated["archive_bytes"]
        )
        split_controls[split] = generated

    reconstructed_store = stored[:5] + decoded_s1
    reconstructed_store_path = args.output_dir / "s1.wrt_store.bin"
    reconstructed_store_path.write_bytes(reconstructed_store)
    restored_raw_path = args.output_dir / "s1.restored.raw"
    inverse_stdout = args.output_dir / "s1_inverse.stdout.log"
    inverse_stderr = args.output_dir / "s1_inverse.stderr.log"
    with inverse_stdout.open("wb") as stdout, inverse_stderr.open("wb") as stderr:
        inverse = subprocess.run(
            [
                str(args.backend),
                "-d",
                str(args.dictionary),
                str(reconstructed_store_path),
                str(restored_raw_path),
            ],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    raw_roundtrip = (
        inverse.returncode == 0
        and restored_raw_path.is_file()
        and restored_raw_path.read_bytes() == raw
    )

    source_rows = {
        "candidate_program_gzip9_bytes": len(
            gzip.compress(CANDIDATE_PROGRAM.read_bytes(), compresslevel=9)
        ),
        "gate_tool_gzip9_bytes": len(
            gzip.compress(Path(__file__).read_bytes(), compresslevel=9)
        ),
        "discovery_parser_gzip9_bytes": len(
            gzip.compress(WIKIIR_PROGRAM.read_bytes(), compresslevel=9)
        ),
    }
    measured_source = sum(source_rows.values())
    gross_bpm = float(s1["gross_saved_bytes_vs_parent_archive"])
    projected_full_net = gross_bpm * 1000.0 - measured_source
    net_bpm = projected_full_net / 1000.0
    source_rows.update(
        {
            "measured_source_allowance_bytes": measured_source,
            "proposal_source_ceiling_bytes": 60_000,
            "full_corpus_amortization_raw_bytes": 1_000_000_000,
            "projected_full_net_saved_bytes": projected_full_net,
        }
    )

    native_artifacts = native_receipt.get("artifacts", {})
    first_native = native_artifacts.get("archive", {})
    second_native = native_artifacts.get("archive_second", {})
    e0 = {
        "archive_bytes": len(parent_archive_data),
        "archive_sha256": sha256_bytes(parent_archive_data),
        "parent_header_bytes": parent_header_bytes,
        "parent_payload_bytes": len(receipt_parent_payload),
        "parent_payload_sha256": sha256_bytes(receipt_parent_payload),
        "parent_payload_identity": replay_payload == receipt_parent_payload,
        "deterministic_archive_ok": (
            first_native.get("sha256")
            == second_native.get("sha256")
            == sha256_bytes(parent_archive_data)
        ),
    }
    conditions = {
        "optimistic_exact_ceiling_at_least_3000_B_per_M": (
            optimistic_exact_gain >= GROSS_GATE_BYTES_PER_MILLION
        ),
        "paid_gross_gain_at_least_3000_B_per_M": (
            gross_bpm >= GROSS_GATE_BYTES_PER_MILLION
        ),
        "paid_net_after_source_at_least_2100_B_per_M": (
            net_bpm >= NET_GATE_BYTES_PER_MILLION
        ),
        "S1_beats_forced_literal_SL": s1["archive_bytes"] < sl["archive_bytes"],
        "development_generated_gain_positive": (
            split_controls["development"]["generated_gain_vs_forced_literal_bytes"] > 0
        ),
        "selection_generated_gain_positive": (
            split_controls["selection"]["generated_gain_vs_forced_literal_bytes"] > 0
        ),
        "sealed_confirmation_generated_gain_positive": (
            split_controls["sealed_confirmation"]["generated_gain_vs_forced_literal_bytes"] > 0
        ),
        "parent_payload_identity": e0["parent_payload_identity"],
        "all_control_roundtrips": all(
            control["control_roundtrip_ok"] for control in (s1, sl)
        ),
        "all_WRT_roundtrips": all(
            control["wrt_roundtrip_ok"] for control in (s1, sl)
        ),
        "raw_roundtrip": raw_roundtrip,
        "all_archives_deterministic": all(
            control["deterministic_archive_ok"] for control in (s1, sl)
        ),
        "all_split_control_roundtrips": all(
            control["control_roundtrip_ok"]
            for control in split_controls.values()
        ),
        "all_split_WRT_roundtrips": all(
            control["wrt_roundtrip_ok"] for control in split_controls.values()
        ),
        "all_split_archives_deterministic": all(
            control["deterministic_archive_ok"]
            for control in split_controls.values()
        ),
        "source_within_proposal_ceiling": measured_source <= 60_000,
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    ceiling_passed = conditions["optimistic_exact_ceiling_at_least_3000_B_per_M"]
    verdict = (
        "authorize_logos_semantic_rule_discovery"
        if authorized
        else "retire_surface_rule_command_format"
        if ceiling_passed
        else "retire_ordered_template_surface_logos_ceiling"
    )

    rule_rows = []
    for rule_id, rule in enumerate(rules):
        rows = [row for row in occurrences if row.key == rule.segments]
        chosen = [
            invocation
            for invocation in invocations
            if invocation.rule_id == rule_id
        ]
        rule_rows.append(
            {
                "rule_id": rule_id,
                "segment_count": len(rule.segments),
                "fixed_definition_bytes": sum(map(len, rule.segments)),
                "definition_command_bytes": candidate.rule_definition_bytes(rule),
                "mapped_occurrences": len(rows),
                "selected_invocations": len(chosen),
                "split_occurrences": {
                    split: sum(row.split == split for row in rows)
                    for split in ("development", "selection", "sealed_confirmation")
                },
                "split_selected": {
                    split: sum(
                        selected_rows[invocation.target_start].split == split
                        for invocation in chosen
                    )
                    for split in ("development", "selection", "sealed_confirmation")
                },
            }
        )

    decision = {
        "schema": "mobius2_logos_surface_grammar_ceiling_q0_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_exact_surface_grammar_ceiling",
        "claim_boundary": (
            "Exact opening-1M surface-template grammar evidence only. It does not "
            "measure semantic LOGOS, NOEMA, native predictor-state hashes, larger "
            "scope transfer, or a full-corpus score."
        ),
        "inputs": {
            "p1_trace": artifact(args.p1),
            "wrt_store": artifact(args.wrt_store),
            "raw_input": artifact(args.raw_input),
            "parent_archive": artifact(args.parent_archive),
            "dictionary": artifact(args.dictionary),
            "backend": artifact(args.backend),
            "manifest": artifact(args.manifest),
            "native_receipt": artifact(args.native_receipt),
            "page_map": artifact(args.page_map),
            "wikiir_discovery_parser": artifact(WIKIIR_PROGRAM),
        },
        "population": {
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "wrt_bytes": len(wrt),
            "complete_pages": len(pages),
            "page_splits": {
                split: sum(page.split == split for page in pages)
                for split in ("development", "selection", "sealed_confirmation")
            },
            "mapping": mapping_stats,
        },
        "discovery": {
            "candidate_rule_keys_repeated_twice_in_development": len(candidate_keys),
            "candidate_occurrences": len(oracle_invocations),
            "selected_rule_rows": rule_rows,
            **selection_stats,
        },
        "optimistic_ceiling": {
            "control_bytes_charged": 0,
            "source_bytes_charged": 0,
            "candidate_rules": len(candidate_rules),
            "candidate_invocations": len(oracle_invocations),
            "fixed_wrt_bytes": sum(
                len(segment)
                for invocation in oracle_invocations
                for segment in candidate_rules[invocation.rule_id].segments
            ),
            "parent_fixed_qbits": optimistic_qbits,
            "parent_fixed_qbit_bytes": optimistic_qbits / QBITS_PER_BYTE,
            "literal_bits": oracle_literal_bits,
            "residual_payload_bytes": len(oracle_payload),
            "exact_payload_gain_bytes": optimistic_exact_gain,
            "exact_payload_gain_bytes_per_million": float(optimistic_exact_gain),
        },
        "controls": {"E0": e0, "S1": s1, "SL": sl},
        "split_controls": split_controls,
        "source_accounting": source_rows,
        "economics": {
            "target_score_bytes": 108_000_000,
            "forecast_score_bytes_unchanged": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
            "S1_gross_exact_bytes_per_million": gross_bpm,
            "S1_net_bytes_per_million_after_source": net_bpm,
        },
        "proof": {
            "manifest_bindings_verified": True,
            "exact_WRT_parse_equals_raw": True,
            "parent_payload_identity": e0["parent_payload_identity"],
            "S1_reconstructed_store_equals_parent": reconstructed_store == stored,
            "S1_reconstructed_store_sha256": sha256_bytes(reconstructed_store),
            "official_inverse_returncode": inverse.returncode,
            "raw_roundtrip": raw_roundtrip,
            "raw_reconstruction_sha256": (
                sha256_file(restored_raw_path) if restored_raw_path.is_file() else None
            ),
            "native_predictor_state_hash_proved": False,
        },
        "gates": {
            "gross_gate_bytes_per_million": GROSS_GATE_BYTES_PER_MILLION,
            "net_gate_bytes_per_million": NET_GATE_BYTES_PER_MILLION,
            "conditions": conditions,
        },
        "decision": {
            "promotion_authorized": authorized,
            "failed_conditions": failed,
            "verdict": verdict,
            "next_action": (
                "materialize the separately frozen semantic-rule discovery lane"
                if authorized
                else "retire this paid surface-rule format but preserve the optimistic ceiling"
                if ceiling_passed
                else "retire ordered-template surface LOGOS and require a semantic-rule information certificate"
            ),
        },
        "score_credit_bytes": 0,
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "mapped_occurrences": len(occurrences),
                "candidate_rules": len(candidate_rules),
                "optimistic_exact_gain_B_per_M": optimistic_exact_gain,
                "selected_rules": len(rules),
                "selected_invocations": len(invocations),
                "S1_archive_bytes": s1["archive_bytes"],
                "S1_gross_B_per_M": gross_bpm,
                "S1_net_B_per_M_after_source": net_bpm,
                "failed_conditions": failed,
                "verdict": verdict,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
