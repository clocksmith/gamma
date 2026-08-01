#!/usr/bin/env python3
"""Run the exact opening-1M LOGOS gapped lexical-frame ceiling."""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
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
from typing import Any, Iterable, Sequence

import numpy as np

from radix_island_oracle import EmissionGroup, emission_groups
from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_logos_lexical_frame_ceiling_q0_v1"
PROPOSAL_ID = "mobius2_logos_lexical_frame_ceiling_v1"
CANDIDATE_PROGRAM = ROOT / "programs" / CANDIDATE_ID / "program.py"
PLAN_PATH = ROOT / "docs" / "mobius2_logos_lexical_frame_ceiling_plan.md"
SCHEMA_PATH = ROOT / "docs" / "mobius2_logos_lexical_frame_ceiling_decision.schema.json"
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
ANCHOR_GROUPS = 5
MIN_HOLE_GROUPS = 1
MAX_HOLE_GROUPS = 12
GROSS_GATE_BYTES_PER_MILLION = 3000.0
QBITS_PER_BIT = 256
ALLOWED_ANCHOR_BYTES = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ,.'-()"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


candidate = load_module("mobius2_logos_lexical_frame_candidate", CANDIDATE_PROGRAM)
FrameRule = candidate.FrameRule
FrameInvocation = candidate.FrameInvocation


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str


@dataclass(frozen=True)
class TextPopulation:
    page: Page
    raw_start: int
    raw_end: int
    group_start: int
    group_end: int


@dataclass
class DevelopmentStats:
    occurrences: int = 0
    first_page: int | None = None
    multiple_pages: bool = False
    first_hole: bytes | None = None
    multiple_holes: bool = False

    def observe(self, page_index: int, hole: bytes) -> None:
        self.occurrences += 1
        if self.first_page is None:
            self.first_page = page_index
        elif self.first_page != page_index:
            self.multiple_pages = True
        if self.first_hole is None:
            self.first_hole = hole
        elif self.first_hole != hole:
            self.multiple_holes = True


@dataclass(frozen=True)
class Occurrence:
    key: tuple[bytes, bytes]
    page_index: int
    split: str
    target_start: int
    target_end: int
    left_end: int
    right_start: int
    fixed_qbits: int

    @property
    def hole_length(self) -> int:
        return self.right_start - self.left_end

    @property
    def fixed_bytes(self) -> int:
        return len(self.key[0]) + len(self.key[1])


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
        raise ValueError("invalid CMIX P1 trace header")
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


def text_populations(
    raw: bytes,
    pages: Sequence[Page],
    groups: Sequence[EmissionGroup],
) -> tuple[list[TextPopulation], dict[str, int]]:
    starts = [group.raw_start for group in groups]
    populations: list[TextPopulation] = []
    missing_text = 0
    unaligned = 0
    for page in pages:
        opening = raw.find(b"<text", page.raw_start, page.raw_end)
        if opening < 0:
            missing_text += 1
            continue
        content_start = raw.find(b">", opening, page.raw_end)
        if content_start < 0:
            missing_text += 1
            continue
        content_start += 1
        content_end = raw.find(b"</text>", content_start, page.raw_end)
        if content_end < 0:
            missing_text += 1
            continue
        group_start = bisect_left(starts, content_start)
        group_end = bisect_left(starts, content_end)
        while group_start < len(groups) and groups[group_start].raw_start < content_start:
            group_start += 1
        while group_end > group_start and groups[group_end - 1].raw_end > content_end:
            group_end -= 1
        if group_start >= group_end:
            unaligned += 1
            continue
        first = groups[group_start]
        last = groups[group_end - 1]
        if first.raw_start < content_start or last.raw_end > content_end:
            unaligned += 1
            continue
        populations.append(
            TextPopulation(
                page,
                content_start,
                content_end,
                group_start,
                group_end,
            )
        )
    return populations, {
        "pages_with_text_population": len(populations),
        "pages_missing_text": missing_text,
        "pages_with_unaligned_empty_text": unaligned,
    }


def eligible_anchor(groups: Sequence[EmissionGroup], start: int) -> bool:
    selected = groups[start : start + ANCHOR_GROUPS]
    if len(selected) != ANCHOR_GROUPS:
        return False
    decoded = b"".join(group.decoded for group in selected)
    if not decoded or any(value not in ALLOWED_ANCHOR_BYTES for value in decoded):
        return False
    words = sum(
        len(group.decoded) >= 2 and group.decoded.isalpha()
        for group in selected
    )
    return words >= 2


def population_anchors(
    population: TextPopulation,
    groups: Sequence[EmissionGroup],
    wrt: bytes,
) -> dict[int, tuple[int, int, bytes]]:
    anchors: dict[int, tuple[int, int, bytes]] = {}
    stop = population.group_end - ANCHOR_GROUPS + 1
    for index in range(population.group_start, max(population.group_start, stop)):
        if not eligible_anchor(groups, index):
            continue
        start = groups[index].stream_start
        end = groups[index + ANCHOR_GROUPS - 1].stream_end
        if not population.page.wrt_start <= start < end <= population.page.wrt_end:
            continue
        anchors[index] = (start, end, wrt[start:end])
    return anchors


def iter_frame_rows(
    population: TextPopulation,
    groups: Sequence[EmissionGroup],
    wrt: bytes,
    hole_groups: Iterable[int],
):
    anchors = population_anchors(population, groups, wrt)
    for left_index in sorted(anchors):
        left_start, left_end, left = anchors[left_index]
        for gap in hole_groups:
            right_index = left_index + ANCHOR_GROUPS + gap
            right = anchors.get(right_index)
            if right is None:
                continue
            right_start, right_end, right_bytes = right
            yield (
                (left, right_bytes),
                left_start,
                left_end,
                right_start,
                right_end,
                wrt[left_end:right_start],
            )


def discover_development_keys(
    populations: Sequence[TextPopulation],
    groups: Sequence[EmissionGroup],
    wrt: bytes,
) -> tuple[set[tuple[bytes, bytes]], set[tuple[bytes, bytes]], dict[str, int]]:
    gapped: dict[tuple[bytes, bytes], DevelopmentStats] = {}
    contiguous: dict[tuple[bytes, bytes], DevelopmentStats] = {}
    gapped_rows = 0
    contiguous_rows = 0
    for population in populations:
        if population.page.split != "development":
            continue
        for key, _start, _left_end, _right_start, _end, hole in iter_frame_rows(
            population,
            groups,
            wrt,
            range(MIN_HOLE_GROUPS, MAX_HOLE_GROUPS + 1),
        ):
            gapped_rows += 1
            gapped.setdefault(key, DevelopmentStats()).observe(population.page.index, hole)
        for key, _start, _left_end, _right_start, _end, hole in iter_frame_rows(
            population, groups, wrt, (0,)
        ):
            contiguous_rows += 1
            contiguous.setdefault(key, DevelopmentStats()).observe(
                population.page.index, hole
            )
    gapped_keys = {
        key
        for key, stats in gapped.items()
        if stats.multiple_pages and stats.multiple_holes
    }
    contiguous_keys = {
        key for key, stats in contiguous.items() if stats.multiple_pages
    }
    return gapped_keys, contiguous_keys, {
        "development_gapped_rows_scanned": gapped_rows,
        "development_gapped_distinct_keys": len(gapped),
        "development_qualified_gapped_keys": len(gapped_keys),
        "development_contiguous_rows_scanned": contiguous_rows,
        "development_contiguous_distinct_keys": len(contiguous),
        "development_qualified_contiguous_keys": len(contiguous_keys),
    }


def rotated_right_keys(
    keys: set[tuple[bytes, bytes]],
) -> set[tuple[bytes, bytes]]:
    ordered = sorted(keys)
    if len(ordered) < 2:
        return set()
    rotated = {
        (key[0], ordered[(index + 1) % len(ordered)][1])
        for index, key in enumerate(ordered)
    }
    return rotated - keys


def collect_occurrences(
    populations: Sequence[TextPopulation],
    groups: Sequence[EmissionGroup],
    wrt: bytes,
    qbit_prefix: np.ndarray,
    gapped_keys: set[tuple[bytes, bytes]],
    contiguous_keys: set[tuple[bytes, bytes]],
    rotated_keys: set[tuple[bytes, bytes]],
) -> dict[str, list[Occurrence]]:
    rows: dict[str, list[Occurrence]] = {"L1": [], "L2": [], "LR": []}
    for population in populations:
        for key, start, left_end, right_start, end, _hole in iter_frame_rows(
            population,
            groups,
            wrt,
            range(MIN_HOLE_GROUPS, MAX_HOLE_GROUPS + 1),
        ):
            labels = []
            if key in gapped_keys:
                labels.append("L2")
            if key in rotated_keys:
                labels.append("LR")
            if not labels:
                continue
            fixed_qbits = int(
                qbit_prefix[left_end]
                - qbit_prefix[start]
                + qbit_prefix[end]
                - qbit_prefix[right_start]
            )
            occurrence = Occurrence(
                key,
                population.page.index,
                population.page.split,
                start,
                end,
                left_end,
                right_start,
                fixed_qbits,
            )
            for label in labels:
                rows[label].append(occurrence)
        for key, start, left_end, right_start, end, _hole in iter_frame_rows(
            population, groups, wrt, (0,)
        ):
            if key not in contiguous_keys:
                continue
            fixed_qbits = int(qbit_prefix[end] - qbit_prefix[start])
            rows["L1"].append(
                Occurrence(
                    key,
                    population.page.index,
                    population.page.split,
                    start,
                    end,
                    left_end,
                    right_start,
                    fixed_qbits,
                )
            )
    return rows


def weighted_interval_schedule(rows: Sequence[Occurrence]) -> list[Occurrence]:
    ordered = sorted(
        rows,
        key=lambda row: (
            row.target_end,
            row.target_start,
            row.key,
            row.hole_length,
        ),
    )
    ends = [row.target_end for row in ordered]
    previous = [
        bisect_right(ends, row.target_start, hi=index) - 1
        for index, row in enumerate(ordered)
    ]
    scores = [0] * (len(ordered) + 1)
    take = [False] * len(ordered)
    for index, row in enumerate(ordered):
        included = row.fixed_qbits + scores[previous[index] + 1]
        excluded = scores[index]
        if included > excluded:
            scores[index + 1] = included
            take[index] = True
        else:
            scores[index + 1] = excluded
    selected: list[Occurrence] = []
    index = len(ordered) - 1
    while index >= 0:
        if take[index]:
            selected.append(ordered[index])
            index = previous[index]
        else:
            index -= 1
    selected.reverse()
    return selected


def select_nonoverlapping(rows: Sequence[Occurrence]) -> list[Occurrence]:
    by_page: dict[int, list[Occurrence]] = defaultdict(list)
    for row in rows:
        by_page[row.page_index].append(row)
    selected = [
        row
        for page_index in sorted(by_page)
        for row in weighted_interval_schedule(by_page[page_index])
    ]
    selected.sort(key=lambda row: row.target_start)
    return selected


def materialize_plan(
    rows: Sequence[Occurrence],
) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    keys = sorted({row.key for row in rows})
    rules = tuple(FrameRule(*key) for key in keys)
    key_to_id = {key: index for index, key in enumerate(keys)}
    invocations = tuple(
        FrameInvocation(row.target_start, row.hole_length, key_to_id[row.key])
        for row in rows
    )
    return rules, invocations


def build_control(
    name: str,
    wrt: bytes,
    probabilities: np.ndarray,
    parent_payload_bytes: int,
    rows: Sequence[Occurrence],
    output_dir: Path,
) -> tuple[dict[str, Any], bytes]:
    rules, invocations = materialize_plan(rows)
    payload, literal_bits = candidate.encode_residual(
        wrt, probabilities, rules, invocations
    )
    decoded, decoded_literal_bits = candidate.decode_residual(
        len(wrt), probabilities, payload, rules, invocations
    )
    second, second_literal_bits = candidate.encode_residual(
        wrt, probabilities, rules, invocations
    )
    result = {
        "name": name,
        "payload_bytes": len(payload),
        "payload_sha256": sha256_bytes(payload),
        "exact_payload_gain_bytes": parent_payload_bytes - len(payload),
        "selected_rules": len(rules),
        "selected_invocations": len(invocations),
        "fixed_wrt_bytes": sum(row.fixed_bytes for row in rows),
        "fixed_parent_qbits": sum(row.fixed_qbits for row in rows),
        "fixed_parent_qbit_bytes": sum(row.fixed_qbits for row in rows)
        / (8 * QBITS_PER_BIT),
        "literal_bits": literal_bits,
        "wrt_roundtrip_ok": decoded == wrt,
        "literal_bit_count_ok": literal_bits
        == decoded_literal_bits
        == second_literal_bits,
        "deterministic_payload_ok": second == payload,
        "split_invocations": {
            split: sum(row.split == split for row in rows)
            for split in ("development", "selection", "sealed_confirmation")
        },
    }
    (output_dir / f"{name.lower()}.payload").write_bytes(payload)
    return result, decoded


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
    replay_payload, replay_literal_bits = candidate.encode_residual(
        wrt, probabilities, (), ()
    )
    if replay_payload != receipt_parent_payload:
        raise ValueError("E0 final-P1 replay is not parent-payload identical")

    pages = read_pages(args.page_map, bound["page_map"]["sha256"], len(wrt))
    groups = emission_groups(parsed)
    populations, text_stats = text_populations(raw, pages, groups)
    byte_costs = qbit_costs(probabilities, wrt)
    qbit_prefix = np.concatenate(
        (np.zeros(1, dtype=np.int64), np.cumsum(byte_costs, dtype=np.int64))
    )

    print("phase=development_frame_discovery", flush=True)
    gapped_keys, contiguous_keys, discovery_stats = discover_development_keys(
        populations, groups, wrt
    )
    rotated_keys = rotated_right_keys(gapped_keys)
    print(
        "phase=exact_occurrence_scan "
        f"gapped_keys={len(gapped_keys)} "
        f"contiguous_keys={len(contiguous_keys)} "
        f"rotated_keys={len(rotated_keys)}",
        flush=True,
    )
    occurrence_rows = collect_occurrences(
        populations,
        groups,
        wrt,
        qbit_prefix,
        gapped_keys,
        contiguous_keys,
        rotated_keys,
    )
    selected = {
        label: select_nonoverlapping(rows)
        for label, rows in occurrence_rows.items()
    }

    controls: dict[str, dict[str, Any]] = {}
    decoded_l2 = wrt
    for label in ("L1", "L2", "LR"):
        control, decoded = build_control(
            label,
            wrt,
            probabilities,
            len(receipt_parent_payload),
            selected[label],
            args.output_dir,
        )
        controls[label] = control
        if label == "L2":
            decoded_l2 = decoded

    split_controls: dict[str, dict[str, Any]] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        split_rows = [row for row in selected["L2"] if row.split == split]
        control, _decoded = build_control(
            f"L2_{split}",
            wrt,
            probabilities,
            len(receipt_parent_payload),
            split_rows,
            args.output_dir,
        )
        split_controls[split] = control

    reconstructed_store = stored[:5] + decoded_l2
    reconstructed_store_path = args.output_dir / "l2.wrt_store.bin"
    reconstructed_store_path.write_bytes(reconstructed_store)
    restored_raw_path = args.output_dir / "l2.restored.raw"
    inverse_stdout = args.output_dir / "l2_inverse.stdout.log"
    inverse_stderr = args.output_dir / "l2_inverse.stderr.log"
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
        "literal_bits": replay_literal_bits,
        "deterministic_archive_ok": (
            first_native.get("sha256")
            == second_native.get("sha256")
            == sha256_bytes(parent_archive_data)
        ),
    }
    controls["E0"] = e0

    conditions = {
        "L2_exact_gain_at_least_3000_B_per_M": (
            controls["L2"]["exact_payload_gain_bytes"]
            >= GROSS_GATE_BYTES_PER_MILLION
        ),
        "development_gain_positive": (
            split_controls["development"]["exact_payload_gain_bytes"] > 0
        ),
        "selection_gain_positive": (
            split_controls["selection"]["exact_payload_gain_bytes"] > 0
        ),
        "sealed_confirmation_gain_positive": (
            split_controls["sealed_confirmation"]["exact_payload_gain_bytes"] > 0
        ),
        "L2_beats_contiguous_L1": (
            controls["L2"]["payload_bytes"] < controls["L1"]["payload_bytes"]
        ),
        "L2_beats_rotated_LR": (
            controls["L2"]["payload_bytes"] < controls["LR"]["payload_bytes"]
        ),
        "parent_payload_identity": e0["parent_payload_identity"],
        "all_WRT_roundtrips": all(
            controls[label]["wrt_roundtrip_ok"] for label in ("L1", "L2", "LR")
        ),
        "all_payloads_deterministic": all(
            controls[label]["deterministic_payload_ok"]
            for label in ("L1", "L2", "LR")
        ),
        "all_split_WRT_roundtrips": all(
            control["wrt_roundtrip_ok"] for control in split_controls.values()
        ),
        "all_split_payloads_deterministic": all(
            control["deterministic_payload_ok"]
            for control in split_controls.values()
        ),
        "raw_roundtrip": raw_roundtrip,
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    verdict = (
        "authorize_paid_lexical_frame_grammar_q1"
        if authorized
        else "retire_exact_cross_page_lexical_frame_ceiling"
    )

    source_rows = {
        "candidate_program_gzip9_bytes": len(
            gzip.compress(CANDIDATE_PROGRAM.read_bytes(), compresslevel=9)
        ),
        "gate_tool_gzip9_bytes": len(
            gzip.compress(Path(__file__).read_bytes(), compresslevel=9)
        ),
        "q0_source_bytes_not_charged": True,
        "proposal_source_ceiling_bytes": 80_000,
    }
    source_rows["measured_q0_source_bytes"] = (
        source_rows["candidate_program_gzip9_bytes"]
        + source_rows["gate_tool_gzip9_bytes"]
    )

    decision = {
        "schema": "mobius2_logos_lexical_frame_ceiling_q0_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_exact_lexical_frame_ceiling",
        "claim_boundary": (
            "Exact opening-1M zero-cost prose lexical-frame information ceiling "
            "only. Rule and invocation descriptions are supplied out of band. "
            "This is not a paid grammar, native predictor-state proof, larger-"
            "scope result, forecast update, or full-corpus score."
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
        },
        "population": {
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "wrt_bytes": len(wrt),
            "emission_groups": len(groups),
            "complete_pages": len(pages),
            "page_splits": {
                split: sum(page.split == split for page in pages)
                for split in ("development", "selection", "sealed_confirmation")
            },
            **text_stats,
        },
        "construction": {
            "anchor_groups": ANCHOR_GROUPS,
            "minimum_hole_groups": MIN_HOLE_GROUPS,
            "maximum_hole_groups": MAX_HOLE_GROUPS,
            "development_minimum_distinct_pages": 2,
            "development_minimum_distinct_holes": 2,
            "anchor_allowed_ascii": bytes(sorted(ALLOWED_ANCHOR_BYTES)).decode("ascii"),
            "selection": "exact maximum-parent-qbit nonoverlapping interval schedule",
            "equal_score_tie": "exclude later interval",
        },
        "discovery": {
            **discovery_stats,
            "rotated_right_keys": len(rotated_keys),
            "matched_occurrences": {
                label: len(occurrence_rows[label]) for label in ("L1", "L2", "LR")
            },
            "selected_occurrences": {
                label: len(selected[label]) for label in ("L1", "L2", "LR")
            },
        },
        "controls": {
            "E0": controls["E0"],
            "L1": controls["L1"],
            "L2": controls["L2"],
            "LR": controls["LR"],
        },
        "split_controls": split_controls,
        "source_accounting": source_rows,
        "economics": {
            "target_score_bytes": 108_000_000,
            "forecast_score_bytes_unchanged": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
            "L2_zero_cost_exact_gain_bytes_per_million": float(
                controls["L2"]["exact_payload_gain_bytes"]
            ),
            "rule_invocation_frame_source_bytes_charged": 0,
        },
        "proof": {
            "manifest_bindings_verified": True,
            "exact_WRT_parse_equals_raw": True,
            "parent_payload_identity": e0["parent_payload_identity"],
            "L2_reconstructed_store_equals_parent": reconstructed_store == stored,
            "L2_reconstructed_store_sha256": sha256_bytes(reconstructed_store),
            "official_inverse_returncode": inverse.returncode,
            "raw_roundtrip": raw_roundtrip,
            "raw_reconstruction_sha256": (
                sha256_file(restored_raw_path) if restored_raw_path.is_file() else None
            ),
            "native_predictor_state_hash_proved": False,
        },
        "gates": {
            "gross_gate_bytes_per_million": GROSS_GATE_BYTES_PER_MILLION,
            "conditions": conditions,
        },
        "decision": {
            "promotion_authorized": authorized,
            "failed_conditions": failed,
            "verdict": verdict,
            "next_action": (
                "freeze and implement one paid finite lexical-frame grammar Q1"
                if authorized
                else "retire this exact lexical-frame construction; broader semantic LOGOS and NOEMA remain unsettled"
            ),
        },
        "score_credit_bytes": 0,
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "qualified_gapped_keys": len(gapped_keys),
                "L1_gain_bytes": controls["L1"]["exact_payload_gain_bytes"],
                "L2_gain_bytes": controls["L2"]["exact_payload_gain_bytes"],
                "LR_gain_bytes": controls["LR"]["exact_payload_gain_bytes"],
                "L2_selected_invocations": controls["L2"]["selected_invocations"],
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
