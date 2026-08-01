#!/usr/bin/env python3
"""Run the exact opening-1M Route E state-preserving bypass Q0 gate."""

from __future__ import annotations

import argparse
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

from wrt_exact import parse_store


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "seal2_route_e_state_preserving_prototype_bypass_q0_v1"
PROPOSAL_ID = "seal2_route_e_state_preserving_prototype_bypass_v1"
CANDIDATE_PROGRAM = ROOT / "programs" / CANDIDATE_ID / "program.py"
PLAN_PATH = ROOT / "docs" / "seal2_route_e_state_preserving_prototype_bypass_plan.md"
SCHEMA_PATH = (
    ROOT
    / "docs"
    / "seal2_route_e_state_preserving_prototype_bypass_decision.schema.json"
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
MIN_COPY_BYTES = 8
QBITS_PER_BIT = 256
QBITS_PER_BYTE = 2048
GROSS_GATE_BYTES_PER_MILLION = 3000.0
NET_GATE_BYTES_PER_MILLION = 2100.0
NEGATIVE_INFINITY = -(1 << 120)


def load_candidate_program():
    spec = importlib.util.spec_from_file_location("route_e_candidate_program", CANDIDATE_PROGRAM)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Route E candidate program")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


candidate = load_candidate_program()
CopySpan = candidate.CopySpan
PagePlan = candidate.PagePlan


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str

    @property
    def raw_bytes(self) -> int:
        return self.raw_end - self.raw_start

    @property
    def wrt_bytes(self) -> int:
        return self.wrt_end - self.wrt_start


@dataclass(frozen=True)
class SelectedPlan:
    page_index: int
    prototype_index: int
    plan: Any
    displaced_qbits: int
    command_bytes: int
    predicted_net_qbits: int


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
    if rows != expected_rows or path.stat().st_size != 16 + 2 * rows:
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
    raw_rows = [
        PAGE_MAP_RECORD.unpack_from(data, 16 + index * PAGE_MAP_RECORD.size)
        for index in range(count)
    ]
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    pages: list[Page] = []
    for index, (raw_start, raw_end, row_start, row_end) in enumerate(raw_rows):
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not WRT-byte aligned")
        if index < development_end:
            split = "development"
        elif index < selection_end:
            split = "selection"
        else:
            split = "sealed_confirmation"
        page = Page(
            index=index,
            raw_start=raw_start,
            raw_end=raw_end,
            wrt_start=row_start // 8,
            wrt_end=row_end // 8,
            split=split,
        )
        if not 0 <= page.wrt_start < page.wrt_end <= wrt_bytes:
            raise ValueError("page map exceeds WRT truth stream")
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


class SuffixAutomaton:
    """Longest-prefix matcher over a frozen prototype page."""

    def __init__(self, prototype: bytes) -> None:
        self.prototype_length = len(prototype)
        transitions: list[dict[int, int]] = [{}]
        links = [-1]
        lengths = [0]
        maximum_end = [-1]
        last = 0
        for position, value in enumerate(reversed(prototype)):
            current = len(transitions)
            transitions.append({})
            lengths.append(lengths[last] + 1)
            links.append(0)
            maximum_end.append(position)
            cursor = last
            while cursor >= 0 and value not in transitions[cursor]:
                transitions[cursor][value] = current
                cursor = links[cursor]
            if cursor < 0:
                links[current] = 0
            else:
                target = transitions[cursor][value]
                if lengths[cursor] + 1 == lengths[target]:
                    links[current] = target
                else:
                    clone = len(transitions)
                    transitions.append(dict(transitions[target]))
                    lengths.append(lengths[cursor] + 1)
                    links.append(links[target])
                    maximum_end.append(-1)
                    while cursor >= 0 and transitions[cursor].get(value) == target:
                        transitions[cursor][value] = clone
                        cursor = links[cursor]
                    links[target] = clone
                    links[current] = clone
            last = current
        for state in sorted(range(1, len(transitions)), key=lengths.__getitem__, reverse=True):
            parent = links[state]
            if maximum_end[state] > maximum_end[parent]:
                maximum_end[parent] = maximum_end[state]
        self.transitions = transitions
        self.links = links
        self.lengths = lengths
        self.maximum_end = maximum_end

    def longest_starts(self, target: bytes) -> tuple[list[int], list[int]]:
        longest = [0] * len(target)
        sources = [0] * len(target)
        state = 0
        matched = 0
        for reverse_index, value in enumerate(reversed(target)):
            while state and value not in self.transitions[state]:
                state = self.links[state]
                matched = min(matched, self.lengths[state])
            next_state = self.transitions[state].get(value)
            if next_state is None:
                state = 0
                matched = 0
            else:
                state = next_state
                matched += 1
            target_start = len(target) - 1 - reverse_index
            if matched:
                source_start = self.prototype_length - 1 - self.maximum_end[state]
                usable = min(matched, len(target) - target_start)
                if not 0 <= source_start <= self.prototype_length - usable:
                    raise ValueError("suffix automaton produced an invalid source")
                longest[target_start] = usable
                sources[target_start] = source_start
        return longest, sources


class RangeMaximum:
    def __init__(self, length: int) -> None:
        size = 1
        while size < length:
            size <<= 1
        self.size = size
        self.values = [NEGATIVE_INFINITY] * (2 * size)
        self.indices = [-1] * (2 * size)

    @staticmethod
    def better(
        left_value: int,
        left_index: int,
        right_value: int,
        right_index: int,
    ) -> tuple[int, int]:
        if right_value > left_value:
            return right_value, right_index
        if right_value == left_value and right_index >= 0 and (
            left_index < 0 or right_index < left_index
        ):
            return right_value, right_index
        return left_value, left_index

    def update(self, index: int, value: int) -> None:
        cursor = self.size + index
        self.values[cursor] = value
        self.indices[cursor] = index
        cursor //= 2
        while cursor:
            value, selected = self.better(
                self.values[cursor * 2],
                self.indices[cursor * 2],
                self.values[cursor * 2 + 1],
                self.indices[cursor * 2 + 1],
            )
            self.values[cursor] = value
            self.indices[cursor] = selected
            cursor //= 2

    def query(self, start: int, stop: int) -> tuple[int, int]:
        if start >= stop:
            return NEGATIVE_INFINITY, -1
        start += self.size
        stop += self.size
        best_value = NEGATIVE_INFINITY
        best_index = -1
        while start < stop:
            if start & 1:
                best_value, best_index = self.better(
                    best_value,
                    best_index,
                    self.values[start],
                    self.indices[start],
                )
                start += 1
            if stop & 1:
                stop -= 1
                best_value, best_index = self.better(
                    best_value,
                    best_index,
                    self.values[stop],
                    self.indices[stop],
                )
            start //= 2
            stop //= 2
        return best_value, best_index


def length_groups(maximum: int) -> list[tuple[int, int, int]]:
    groups: list[tuple[int, int, int]] = []
    lower = MIN_COPY_BYTES
    encoded_bytes = candidate.uleb_size(lower)
    while lower <= maximum:
        upper_bound = (1 << (7 * encoded_bytes)) - 1
        upper = min(maximum, upper_bound)
        groups.append((lower, upper, encoded_bytes))
        lower = upper + 1
        encoded_bytes += 1
    return groups


def page_header_bytes(target: Page, prototype: Page) -> int:
    return (
        candidate.uleb_size(target.wrt_start)
        + candidate.uleb_size(target.wrt_bytes)
        + candidate.uleb_size(prototype.wrt_start)
        + candidate.uleb_size(prototype.wrt_bytes)
        + candidate.COUNT.size
    )


def exact_single_copy(
    longest: Sequence[int],
    sources: Sequence[int],
    cost_prefix: Sequence[int],
) -> tuple[tuple[Any, ...], int, int]:
    best_net = 0
    best_copy: Any | None = None
    best_displaced = 0
    best_command = 0
    for target_start, maximum in enumerate(longest):
        if maximum < MIN_COPY_BYTES:
            continue
        source_start = sources[target_start]
        for lower, upper, length_bytes in length_groups(maximum):
            del lower
            length = upper
            displaced = int(cost_prefix[target_start + length] - cost_prefix[target_start])
            command_bytes = (
                candidate.uleb_size(target_start)
                + candidate.uleb_size(source_start)
                + length_bytes
            )
            net = displaced - command_bytes * QBITS_PER_BYTE
            if net > best_net:
                best_net = net
                best_copy = CopySpan(target_start, source_start, length)
                best_displaced = displaced
                best_command = command_bytes
    return (() if best_copy is None else (best_copy,)), best_displaced, best_command


def exact_multiple_copies(
    longest: Sequence[int],
    sources: Sequence[int],
    cost_prefix: Sequence[int],
) -> tuple[tuple[Any, ...], int, int]:
    length = len(longest)
    optimum = [0] * (length + 1)
    choice: list[tuple[int, int] | None] = [None] * length
    maximum = RangeMaximum(length + 1)
    maximum.update(length, int(cost_prefix[length]))
    for target_start in range(length - 1, -1, -1):
        best = optimum[target_start + 1]
        best_choice: tuple[int, int] | None = None
        available = longest[target_start]
        if available >= MIN_COPY_BYTES:
            source_start = sources[target_start]
            fixed_command_bytes = (
                candidate.uleb_size(target_start)
                + candidate.uleb_size(source_start)
            )
            for lower, upper, length_bytes in length_groups(available):
                value, stop = maximum.query(
                    target_start + lower,
                    target_start + upper + 1,
                )
                candidate_value = (
                    value
                    - int(cost_prefix[target_start])
                    - (fixed_command_bytes + length_bytes) * QBITS_PER_BYTE
                )
                if candidate_value > best:
                    best = candidate_value
                    best_choice = (source_start, stop - target_start)
        optimum[target_start] = best
        choice[target_start] = best_choice
        maximum.update(target_start, int(cost_prefix[target_start]) + best)
    copies: list[Any] = []
    displaced = 0
    command_bytes = 0
    position = 0
    while position < length:
        selected = choice[position]
        if selected is None:
            position += 1
            continue
        source_start, copy_length = selected
        copies.append(CopySpan(position, source_start, copy_length))
        displaced += int(cost_prefix[position + copy_length] - cost_prefix[position])
        command_bytes += (
            candidate.uleb_size(position)
            + candidate.uleb_size(source_start)
            + candidate.uleb_size(copy_length)
        )
        position += copy_length
    return tuple(copies), displaced, command_bytes


def selected_plan(
    target: Page,
    prototype: Page,
    copies: tuple[Any, ...],
    displaced_qbits: int,
    copy_command_bytes: int,
) -> SelectedPlan | None:
    if not copies:
        return None
    command_bytes = page_header_bytes(target, prototype) + copy_command_bytes
    net = displaced_qbits - command_bytes * QBITS_PER_BYTE
    if net <= 0:
        return None
    return SelectedPlan(
        page_index=target.index,
        prototype_index=prototype.index,
        plan=PagePlan(
            target_start=target.wrt_start,
            target_length=target.wrt_bytes,
            prototype_start=prototype.wrt_start,
            prototype_length=prototype.wrt_bytes,
            copies=copies,
        ),
        displaced_qbits=displaced_qbits,
        command_bytes=command_bytes,
        predicted_net_qbits=net,
    )


def better_plan(current: SelectedPlan | None, candidate_plan: SelectedPlan | None) -> SelectedPlan | None:
    if candidate_plan is None:
        return current
    if current is None:
        return candidate_plan
    if candidate_plan.predicted_net_qbits > current.predicted_net_qbits:
        return candidate_plan
    if (
        candidate_plan.predicted_net_qbits == current.predicted_net_qbits
        and candidate_plan.prototype_index < current.prototype_index
    ):
        return candidate_plan
    return current


def evaluate_pair(
    target: Page,
    prototype: Page,
    target_bytes: bytes,
    automaton: SuffixAutomaton,
    byte_costs: np.ndarray,
) -> tuple[SelectedPlan | None, SelectedPlan | None]:
    longest, sources = automaton.longest_starts(target_bytes)
    page_costs = byte_costs[target.wrt_start : target.wrt_end]
    prefix = np.empty(len(page_costs) + 1, dtype=np.int64)
    prefix[0] = 0
    np.cumsum(page_costs, out=prefix[1:])
    e1_copies, e1_displaced, e1_commands = exact_single_copy(longest, sources, prefix)
    e2_copies, e2_displaced, e2_commands = exact_multiple_copies(longest, sources, prefix)
    return (
        selected_plan(target, prototype, e1_copies, e1_displaced, e1_commands),
        selected_plan(target, prototype, e2_copies, e2_displaced, e2_commands),
    )


def build_control(
    name: str,
    selected: Sequence[SelectedPlan],
    wrt: bytes,
    probabilities: np.ndarray,
    parent_archive_bytes: int,
    output_dir: Path,
) -> tuple[dict[str, Any], bytes]:
    plans = tuple(row.plan for row in sorted(selected, key=lambda row: row.page_index))
    archive = candidate.build_bypass_archive(wrt, probabilities, plans)
    decoded, decoded_plans = candidate.decode_bypass_archive(archive, probabilities)
    second = candidate.build_bypass_archive(wrt, probabilities, plans)
    commands = candidate.encode_commands(plans, len(wrt))
    header = candidate.BYPASS_HEADER.unpack_from(archive)
    literal_bits = int(header[4])
    literal_payload_bytes = int(header[5])
    copied_bytes = sum(copy.length for plan in plans for copy in plan.copies)
    command_roundtrip = decoded_plans == plans and candidate.encode_commands(
        decoded_plans, len(wrt)
    ) == commands
    result = {
        "name": name,
        "archive_bytes": len(archive),
        "archive_sha256": sha256_bytes(archive),
        "command_bytes": len(commands),
        "command_sha256": sha256_bytes(commands),
        "literal_bits": literal_bits,
        "literal_payload_bytes": literal_payload_bytes,
        "active_pages": len(plans),
        "copy_commands": sum(len(plan.copies) for plan in plans),
        "copied_wrt_bytes": copied_bytes,
        "gross_saved_bytes_vs_parent_archive": parent_archive_bytes - len(archive),
        "command_roundtrip_ok": command_roundtrip,
        "wrt_roundtrip_ok": decoded == wrt,
        "deterministic_archive_ok": second == archive,
        "predicted_displaced_qbits": sum(row.displaced_qbits for row in selected),
        "predicted_net_qbits_after_commands": sum(
            row.predicted_net_qbits for row in selected
        ) - candidate.COUNT.size * QBITS_PER_BYTE,
    }
    (output_dir / f"{name.lower()}.archive").write_bytes(archive)
    return result, decoded


def control_e0(
    parent_archive_path: Path,
    parent_payload_bytes: bytes,
    replay_payload: bytes,
    wrt: bytes,
    native_receipt: dict[str, Any],
) -> dict[str, Any]:
    artifacts = native_receipt.get("artifacts", {})
    first = artifacts.get("archive", {}) if isinstance(artifacts, dict) else {}
    second = artifacts.get("archive_second", {}) if isinstance(artifacts, dict) else {}
    return {
        "name": "E0_exact_parent_replay",
        "archive_bytes": parent_archive_path.stat().st_size,
        "archive_sha256": sha256_file(parent_archive_path),
        "command_bytes": 0,
        "literal_bits": len(wrt) * 8,
        "literal_payload_bytes": len(replay_payload),
        "active_pages": 0,
        "copy_commands": 0,
        "copied_wrt_bytes": 0,
        "gross_saved_bytes_vs_parent_archive": 0,
        "command_roundtrip_ok": True,
        "wrt_roundtrip_ok": True,
        "deterministic_archive_ok": (
            first.get("sha256") == second.get("sha256") == sha256_file(parent_archive_path)
        ),
        "parent_payload_identity": replay_payload == parent_payload_bytes,
        "parent_payload_sha256": sha256_bytes(replay_payload),
    }


def split_counts(pages: Sequence[Page]) -> dict[str, dict[str, int]]:
    names = ("development", "selection", "sealed_confirmation")
    return {
        name: {
            "pages": sum(page.split == name for page in pages),
            "raw_bytes": sum(page.raw_bytes for page in pages if page.split == name),
            "wrt_bytes": sum(page.wrt_bytes for page in pages if page.split == name),
        }
        for name in names
    }


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
    replay_payload = candidate.range_encode(wrt, probabilities)
    if replay_payload != receipt_parent_payload:
        raise ValueError("E0 final-P1 replay is not parent-payload identical")
    pages = read_pages(args.page_map, bound["page_map"]["sha256"], len(wrt))
    if not pages:
        raise ValueError("opening population has no complete pages")
    costs = qbit_costs(probabilities, wrt)

    automata = [SuffixAutomaton(wrt[page.wrt_start : page.wrt_end]) for page in pages]
    best_e1: list[SelectedPlan] = []
    best_e2: list[SelectedPlan] = []
    pair_evaluations = 0
    for target in pages:
        target_bytes = wrt[target.wrt_start : target.wrt_end]
        selected_e1: SelectedPlan | None = None
        selected_e2: SelectedPlan | None = None
        for prototype in pages[: target.index]:
            e1, e2 = evaluate_pair(
                target,
                prototype,
                target_bytes,
                automata[prototype.index],
                costs,
            )
            selected_e1 = better_plan(selected_e1, e1)
            selected_e2 = better_plan(selected_e2, e2)
            pair_evaluations += 1
        if selected_e1 is not None:
            best_e1.append(selected_e1)
        if selected_e2 is not None:
            best_e2.append(selected_e2)
        print(
            f"[route-e-q0] page={target.index + 1}/{len(pages)} "
            f"pairs={pair_evaluations} e1_active={len(best_e1)} "
            f"e2_active={len(best_e2)}",
            flush=True,
        )

    rotated: list[SelectedPlan] = []
    distances = [row.page_index - row.prototype_index for row in best_e2]
    rotated_distances = distances[-1:] + distances[:-1]
    for row, distance in zip(best_e2, rotated_distances, strict=True):
        target = pages[row.page_index]
        if target.index == 0:
            continue
        repaired_distance = 1 + ((distance - 1) % target.index)
        prototype = pages[target.index - repaired_distance]
        _e1, er = evaluate_pair(
            target,
            prototype,
            wrt[target.wrt_start : target.wrt_end],
            automata[prototype.index],
            costs,
        )
        if er is not None:
            rotated.append(er)

    e0 = control_e0(
        args.parent_archive,
        receipt_parent_payload,
        replay_payload,
        wrt,
        native_receipt,
    )
    e1, _decoded_e1 = build_control(
        "E1", best_e1, wrt, probabilities, len(parent_archive_data), args.output_dir
    )
    e2, decoded_e2 = build_control(
        "E2", best_e2, wrt, probabilities, len(parent_archive_data), args.output_dir
    )
    er, _decoded_er = build_control(
        "ER", rotated, wrt, probabilities, len(parent_archive_data), args.output_dir
    )

    split_controls: dict[str, dict[str, Any]] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        selected = [row for row in best_e2 if pages[row.page_index].split == split]
        split_control, _decoded = build_control(
            f"E2_{split}",
            selected,
            wrt,
            probabilities,
            len(parent_archive_data),
            args.output_dir,
        )
        split_controls[split] = split_control

    reconstructed_store = stored[:5] + decoded_e2
    reconstructed_store_path = args.output_dir / "e2.wrt_store.bin"
    reconstructed_store_path.write_bytes(reconstructed_store)
    restored_raw_path = args.output_dir / "e2.restored.raw"
    inverse_stdout = args.output_dir / "e2_inverse.stdout.log"
    inverse_stderr = args.output_dir / "e2_inverse.stderr.log"
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

    program_gzip = len(gzip.compress(CANDIDATE_PROGRAM.read_bytes(), compresslevel=9))
    gate_gzip = len(gzip.compress(Path(__file__).read_bytes(), compresslevel=9))
    measured_source = program_gzip + gate_gzip
    gross_bpm = float(e2["gross_saved_bytes_vs_parent_archive"])
    projected_full_net = gross_bpm * 1000.0 - measured_source
    net_bpm = projected_full_net / 1000.0
    conditions = {
        "gross_exact_gain_at_least_3000_B_per_M": (
            gross_bpm >= GROSS_GATE_BYTES_PER_MILLION
        ),
        "net_after_source_at_least_2100_B_per_M": (
            net_bpm >= NET_GATE_BYTES_PER_MILLION
        ),
        "E2_beats_E1": e2["archive_bytes"] < e1["archive_bytes"],
        "E2_beats_ER": e2["archive_bytes"] < er["archive_bytes"],
        "selection_exact_gain_positive": (
            split_controls["selection"]["gross_saved_bytes_vs_parent_archive"] > 0
        ),
        "sealed_confirmation_exact_gain_positive": (
            split_controls["sealed_confirmation"]["gross_saved_bytes_vs_parent_archive"] > 0
        ),
        "parent_payload_identity": e0["parent_payload_identity"],
        "all_command_roundtrips": all(
            control["command_roundtrip_ok"] for control in (e1, e2, er)
        ),
        "all_WRT_roundtrips": all(
            control["wrt_roundtrip_ok"] for control in (e1, e2, er)
        ),
        "raw_roundtrip": raw_roundtrip,
        "all_archives_deterministic": all(
            control["deterministic_archive_ok"] for control in (e0, e1, e2, er)
        ),
        "source_within_proposal_ceiling": measured_source <= 40_000,
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed

    page_rows = []
    e1_by_page = {row.page_index: row for row in best_e1}
    e2_by_page = {row.page_index: row for row in best_e2}
    for page in pages:
        row_e1 = e1_by_page.get(page.index)
        row_e2 = e2_by_page.get(page.index)
        page_rows.append(
            {
                "page_index": page.index,
                "split": page.split,
                "raw_bytes": page.raw_bytes,
                "wrt_bytes": page.wrt_bytes,
                "E1": None
                if row_e1 is None
                else {
                    "prototype_index": row_e1.prototype_index,
                    "copy_commands": len(row_e1.plan.copies),
                    "copied_wrt_bytes": sum(copy.length for copy in row_e1.plan.copies),
                    "predicted_net_qbits": row_e1.predicted_net_qbits,
                },
                "E2": None
                if row_e2 is None
                else {
                    "prototype_index": row_e2.prototype_index,
                    "copy_commands": len(row_e2.plan.copies),
                    "copied_wrt_bytes": sum(copy.length for copy in row_e2.plan.copies),
                    "literal_holes": max(len(row_e2.plan.copies) - 1, 0),
                    "predicted_net_qbits": row_e2.predicted_net_qbits,
                },
            }
        )

    decision = {
        "schema": "seal2_route_e_state_preserving_prototype_bypass_q0_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_exact_state_preserving_bypass_diagnostic",
        "claim_boundary": (
            "Exact opening-1M trace-level bypass evidence only. The fixed P1 trace "
            "proves parent replay and residual arithmetic accounting, but a native "
            "predictor-state hash, counted integration, larger-scope transfer, and "
            "full-corpus score remain unproved."
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
            "parent_archive_header_bytes": parent_header_bytes,
            "parent_arithmetic_payload_bytes": len(receipt_parent_payload),
        },
        "population": {
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "wrt_bytes": len(wrt),
            "complete_pages": len(pages),
            "complete_page_raw_bytes": sum(page.raw_bytes for page in pages),
            "complete_page_wrt_bytes": sum(page.wrt_bytes for page in pages),
            "splits": split_counts(pages),
        },
        "format": {
            "minimum_copy_bytes": MIN_COPY_BYTES,
            "prototype_count_per_page": 1,
            "prototype_universe": "all earlier complete pages",
            "pair_evaluations": pair_evaluations,
            "match_enumerator": (
                "reversed suffix automaton longest start match with minimum-source "
                "tie and every legal prefix length"
            ),
            "selection_objective": (
                "exact 1/256-bit parent qbits minus actual canonical-ULEB command bytes"
            ),
            "command_integer_code": "canonical ULEB128 plus fixed little-endian u32 counts",
            "archive_frame_bytes": candidate.BYPASS_HEADER.size,
            "range_coder_precision_bits": 32,
        },
        "controls": {
            "E0": e0,
            "E1": e1,
            "E2": e2,
            "ER": er,
        },
        "split_controls": split_controls,
        "page_results": page_rows,
        "source_accounting": {
            "candidate_program_gzip9_bytes": program_gzip,
            "gate_tool_gzip9_bytes": gate_gzip,
            "measured_source_allowance_bytes": measured_source,
            "proposal_source_ceiling_bytes": 40_000,
            "full_corpus_amortization_raw_bytes": 1_000_000_000,
            "projected_full_net_saved_bytes": projected_full_net,
        },
        "economics": {
            "forecast_score_bytes_unchanged": 109_389_323,
            "target_score_bytes": 108_000_000,
            "forecast_debt_bytes": 1_389_323,
            "forecast_debt_bytes_per_million": 1389.323,
            "E2_gross_exact_bytes_per_million": gross_bpm,
            "E2_net_bytes_per_million_after_source": net_bpm,
        },
        "proof": {
            "manifest_bindings_verified": True,
            "exact_WRT_parse_equals_raw": True,
            "parent_payload_identity": e0["parent_payload_identity"],
            "E2_reconstructed_store_sha256": sha256_bytes(reconstructed_store),
            "E2_reconstructed_store_equals_parent": reconstructed_store == stored,
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
            "verdict": (
                "authorize_frozen_route_e_10m_replay"
                if authorized
                else "retire_single_prototype_state_preserving_bypass_q0"
            ),
            "next_action": (
                "run one canonical 10M replay with the frozen format"
                if authorized
                else "record the terminal result; a successor requires a transmitted many-use corpus grammar bypass"
            ),
        },
        "score_credit_bytes": 0,
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "E0_archive_bytes": e0["archive_bytes"],
                "E1_archive_bytes": e1["archive_bytes"],
                "E2_archive_bytes": e2["archive_bytes"],
                "ER_archive_bytes": er["archive_bytes"],
                "E2_gross_B_per_M": gross_bpm,
                "E2_net_B_per_M_after_source": net_bpm,
                "failed_conditions": failed,
                "verdict": decision["decision"]["verdict"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
