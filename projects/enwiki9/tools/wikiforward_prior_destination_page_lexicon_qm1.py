#!/usr/bin/env python3
"""Run the frozen WIKIFORWARD prior-destination-page lexicon QM1 ceiling."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

import numpy as np

from causal_state_screen import WikiState
from janus_paid_residual_mdl_oracle import range_encode
from mobius2_tessera_self_annotation_graph import ROLE_IDS, role_id
from mobius2_tessera_typed_fiber_ceiling import byte_qbits, qbit_tables, read_p1
from sibyl_page_prompt_oracle import page_intervals
import wikiback_incoming_anchor_context_qh0 as wikiback
from wrt_exact import ParsedStore, WrtEvent, parse_store


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CANDIDATE_ID = "wikiforward_prior_destination_page_lexicon_qm1_v1"
LANES = ("Dblind", "Dprior", "Dglobal", "Dfull")
CONTROLS = LANES[:-1]
SPLITS = ("development", "selection", "opened_confirmation")
PAGE_OPEN = b"<page>"
PAGE_CLOSE = b"</page>"
QBIT_DENOMINATOR = 2048
TOTAL_GATE_BYTES = 60_000
CONTROL_MARGIN_BYTES = 10_000
SPLIT_GATE_BYTES_PER_MILLION = 5_000
FORECAST_BYTES = 109_389_323
FORECAST_DEBT_BYTES = 1_389_323
EXPLORATORY_DFULL_BYTES = 63_259.358

EXPECTED = {
    "joint_p1": (100_029_648, "b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719"),
    "joint_payload": (1_617_484, "5ffaa128fa9e86e3883896a6d16b6c49e23693f5abdf14f1718e0e006533dca9"),
    "wrt_store": (6_251_857, "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b"),
    "raw_input": (10_000_000, "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"),
    "dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
    "page_receipt": (9_711_214, "e4f0db7f82759aa05b025cd65170206cb76fd22187eb29d7bbe96537928c7bcc"),
}
EXPECTED_QBIT_HASHES = (
    "6ddbe07c8c2f8387d044a98d958e26ac4f8af27a9dcdf2335f046891365c2376",
    "7caf35600227bad3b1b7402aaa3837aab1aa5aa11267bca283be055c81e8387f",
)
FROZEN_DONOR_HASHES = {
    "projects/enwiki9/tools/wikiback_incoming_anchor_context_qh0.py": "5a6bb8f47e7250f5eac16a5803c0fadbc032f70aa0a06cd1fb4e5e1f140c9638",
    "projects/enwiki9/tools/causal_state_screen.py": "aaa42365acadc8e32f8b79e5862ca451a91d637093b483bcf54cbf657c4740e4",
    "projects/enwiki9/tools/mobius2_tessera_self_annotation_graph.py": "0d5168f834c24153657ba162e2bfab3f6cce9fd1396e1079e8e8ac7c09318594",
    "projects/enwiki9/tools/mobius2_tessera_typed_fiber_ceiling.py": "c1e404b9f5328df6f75ae3ffef6e4c9bb9d3757c31c54905ae727c1b68578af3",
    "projects/enwiki9/tools/sibyl_page_prompt_oracle.py": "68b209861d3d46113acff2d3313a58237e01c620d331d11ccec3c846b99d00d6",
    "projects/enwiki9/tools/wrt_exact.py": "ae08246ee8b4708904f78aa5f694111834d6420deece34957c61d6fea3a9797a",
}
BOUND_SOURCE_FILES = (
    "projects/enwiki9/docs/wikiforward_prior_destination_page_lexicon_qm1_plan.md",
    "projects/enwiki9/tools/wikiforward_prior_destination_page_lexicon_qm1.py",
    *FROZEN_DONOR_HASHES.keys(),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def verify_artifact(name: str, observed: Mapping[str, object]) -> None:
    if (observed["bytes"], observed["sha256"]) != EXPECTED[name]:
        raise ValueError(f"{name} differs from frozen binding")


def bind_sources() -> dict[str, object]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    files: dict[str, object] = {}
    for relative in BOUND_SOURCE_FILES:
        path = REPO_ROOT / relative
        current = path.read_bytes()
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"], cwd=REPO_ROOT, check=True,
            capture_output=True,
        ).stdout
        if current != committed:
            raise ValueError(f"bound source differs from HEAD: {relative}")
        digest = sha256_bytes(current)
        if relative in FROZEN_DONOR_HASHES and digest != FROZEN_DONOR_HASHES[relative]:
            raise ValueError(f"frozen donor bytes changed: {relative}")
        files[relative] = {"bytes": len(current), "sha256": digest}
    return {"git_commit": commit, "tracked_files": files, "score_charge_bytes": 0}


def split_for_page(ordinal: int, count: int) -> int:
    if ordinal < count * 3 // 5:
        return 0
    if ordinal < count * 4 // 5:
        return 1
    return 2


def top_codes(counter: Mapping[bytes, int], count: int) -> tuple[bytes, ...] | None:
    rows = sorted(
        ((bytes(code), int(weight)) for code, weight in counter.items() if weight > 0),
        key=lambda row: (-row[1], row[0]),
    )
    if len(rows) < count:
        return None
    return tuple(code for code, _ in rows[:count])


def filtered(counter: Mapping[bytes, int], prefix: set[bytes]) -> Counter[bytes]:
    return Counter({bytes(code): int(count) for code, count in counter.items() if count > 0 and code not in prefix})


def update_counter_digest(digest: Any, counter: Mapping[bytes, int]) -> None:
    rows = tuple((bytes(code), int(count)) for code, count in sorted(counter.items()) if count > 0)
    digest.update(len(rows).to_bytes(4, "little"))
    for code, count in rows:
        digest.update(len(code).to_bytes(2, "little"))
        digest.update(code)
        digest.update(count.to_bytes(8, "little"))


@dataclass(frozen=True)
class TargetComplete:
    key: bytes
    event_ordinal: int


@dataclass
class ForwardPageStage(wikiback.PageStage):
    completed_targets: list[TargetComplete] = field(default_factory=list)

    def _emit_target(self) -> None:
        raw = b"".join(event.decoded for event in self.link_target_events)
        key = wikiback.normalize_title(raw)
        if key:
            self.completed_targets.append(TargetComplete(key, self.link_target_end_event))

    def _finish_link(self, close_event: int, label_events: Sequence[WrtEvent] = ()) -> None:
        if self.link_phase == "target":
            self._emit_target()
        super()._finish_link(close_event, label_events)

    def observe(self, event: WrtEvent) -> wikiback.PageSignal:
        before = self.link_phase
        signal = super().observe(event)
        if before == "target" and self.link_phase in ("label", "fragment"):
            self._emit_target()
        return signal

    def drain_targets(self) -> tuple[TargetComplete, ...]:
        result = tuple(self.completed_targets)
        self.completed_targets.clear()
        return result


@dataclass(frozen=True)
class PageRecord:
    ordinal: int
    title_key: bytes
    prose: Counter[bytes]


@dataclass
class RankedReservoir:
    codes: tuple[bytes, ...]
    positions: dict[bytes, int]
    tree: list[int]
    active: bytearray
    remaining: int

    @classmethod
    def from_counter(cls, counter: Mapping[bytes, int], prefix: set[bytes]) -> "RankedReservoir":
        rows = sorted(
            ((bytes(code), int(weight)) for code, weight in counter.items() if weight > 0),
            key=lambda row: (-row[1], row[0]),
        )
        codes = tuple(code for code, _ in rows)
        size = len(codes)
        result = cls(
            codes=codes,
            positions={code: index for index, code in enumerate(codes)},
            tree=[0] + [index & -index for index in range(1, size + 1)],
            active=bytearray(b"\x01") * size,
            remaining=size,
        )
        for code in prefix:
            result.remove(code)
        return result

    def remove(self, code: bytes) -> None:
        position = self.positions.get(code)
        if position is None or not self.active[position]:
            return
        self.active[position] = 0
        self.remaining -= 1
        cursor = position + 1
        while cursor < len(self.tree):
            self.tree[cursor] -= 1
            cursor += cursor & -cursor

    def active_rank(self, code: bytes) -> int | None:
        position = self.positions.get(code)
        if position is None or not self.active[position]:
            return None
        total = 0
        cursor = position + 1
        while cursor:
            total += self.tree[cursor]
            cursor -= cursor & -cursor
        return total


@dataclass
class CurrentPage:
    ordinal: int
    split: int
    parser: ForwardPageStage
    prose: Counter[bytes] = field(default_factory=Counter)
    prefix: set[bytes] = field(default_factory=set)
    active_ordinals: dict[str, set[int]] = field(
        default_factory=lambda: {"Dblind": set(), "Dprior": set(), "Dfull": set()}
    )
    reservoirs: dict[str, Counter[bytes]] = field(
        default_factory=lambda: {"Dblind": Counter(), "Dprior": Counter(), "Dfull": Counter()}
    )
    ranked: dict[str, RankedReservoir] = field(default_factory=dict)


@dataclass(frozen=True)
class RunResult:
    qbits: dict[str, int]
    split_qbits: dict[str, tuple[int, int, int]]
    stats: dict[str, object]
    parser_sha256: str
    index_sha256: str
    activation_sha256: str
    opportunity_sha256: str
    control_sha256: str


class ForwardMachine:
    def __init__(self, parsed: ParsedStore, intervals: Sequence[tuple[int, int, int, int]], event_qbits: np.ndarray):
        self.parsed = parsed
        self.intervals = intervals
        self.event_qbits = event_qbits
        self.page_count = len(intervals)
        self.page_starts = {row_start // 8: (i, raw_start) for i, (raw_start, _, row_start, _) in enumerate(intervals)}
        self.page_ends = {row_end // 8: (i, raw_end) for i, (_, raw_end, _, row_end) in enumerate(intervals)}
        partial_start = parsed.decoded.rfind(PAGE_OPEN)
        raw_cursor = 0
        for event in parsed.events:
            if raw_cursor == partial_start:
                self.page_starts[event.start] = (self.page_count, partial_start)
                break
            raw_cursor += len(event.decoded)
        else:
            raise ValueError("trailing page opener cuts a WRT event")
        self.wiki = WikiState()
        self.page: CurrentPage | None = None
        self.raw_position = 0
        self.pages: list[PageRecord] = []
        self.title_index: dict[bytes, list[PageRecord]] = defaultdict(list)
        self.global_prose: Counter[bytes] = Counter()
        self.previous_page: PageRecord | None = None
        self.qbits = {lane: 0 for lane in LANES}
        self.split_qbits = {lane: [0, 0, 0] for lane in LANES}
        self.hits = {lane: 0 for lane in LANES}
        self.split_hits = {lane: [0, 0, 0] for lane in LANES}
        self.target_completions = 0
        self.unique_resolutions = 0
        self.duplicate_or_missing_resolutions = 0
        self.accepted_updates = 0
        self.discarded_control_updates = 0
        self.idempotent_updates = 0
        self.opportunities = 0
        self.deactivated_opportunities = 0
        self.committed_pages = 0
        self.blind_key_violations = 0
        self.parser_digest = hashlib.sha256()
        self.index_digest = hashlib.sha256()
        self.activation_digest = hashlib.sha256()
        self.opportunity_digest = hashlib.sha256()
        self.control_digest = hashlib.sha256()

    def _blind(self, destination: PageRecord) -> PageRecord | None:
        if self.page is None:
            raise ValueError("blind selection outside current page")
        capacity = len(destination.prose)
        eligible = [
            row for row in self.pages
            if row.title_key and row.title_key != destination.title_key
            and row.ordinal not in self.page.active_ordinals["Dblind"]
            and len(row.prose) >= capacity
        ]
        if not eligible:
            return None
        target_bin = capacity.bit_length()
        return min(
            eligible,
            key=lambda row: (
                abs(len(row.prose).bit_length() - target_bin),
                row.ordinal,
                row.title_key,
            ),
        )

    def _activate(self, target: TargetComplete, event_index: int) -> None:
        if self.page is None:
            raise ValueError("target completed outside page")
        self.target_completions += 1
        matches = self.title_index.get(target.key, ())
        resolved = matches[0] if len(matches) == 1 else None
        self.activation_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.activation_digest.update(event_index.to_bytes(8, "little"))
        self.activation_digest.update(len(target.key).to_bytes(2, "little"))
        self.activation_digest.update(target.key)
        self.activation_digest.update(len(matches).to_bytes(4, "little"))
        if resolved is None or not resolved.prose:
            self.duplicate_or_missing_resolutions += 1
            self.activation_digest.update(b"N")
            return
        if resolved.ordinal >= self.page.ordinal:
            raise ValueError("WIKIFORWARD resolved a non-earlier page")
        self.unique_resolutions += 1
        if resolved.ordinal in self.page.active_ordinals["Dfull"]:
            self.idempotent_updates += 1
            self.activation_digest.update(b"I")
            return
        blind = self._blind(resolved)
        previous = self.previous_page
        capacity = len(resolved.prose)
        if (
            blind is None
            or previous is None
            or len(previous.prose) < capacity
            or len(self.global_prose) < capacity
        ):
            self.discarded_control_updates += 1
            self.activation_digest.update(b"X")
            return
        if blind.title_key == resolved.title_key:
            self.blind_key_violations += 1
            raise ValueError("Dblind selected the real destination key")
        self.page.active_ordinals["Dfull"].add(resolved.ordinal)
        self.page.reservoirs["Dfull"].update(resolved.prose)
        self.page.active_ordinals["Dblind"].add(blind.ordinal)
        self.page.reservoirs["Dblind"].update(blind.prose)
        if previous.ordinal not in self.page.active_ordinals["Dprior"]:
            self.page.active_ordinals["Dprior"].add(previous.ordinal)
            self.page.reservoirs["Dprior"].update(previous.prose)
        for lane in ("Dblind", "Dprior", "Dfull"):
            self.page.ranked[lane] = RankedReservoir.from_counter(
                self.page.reservoirs[lane], self.page.prefix
            )
        self.accepted_updates += 1
        self.activation_digest.update(b"A")
        self.activation_digest.update(resolved.ordinal.to_bytes(4, "little"))
        self.activation_digest.update(blind.ordinal.to_bytes(4, "little"))
        self.activation_digest.update(previous.ordinal.to_bytes(4, "little"))

    def _score(self, index: int, event: WrtEvent, role: int) -> None:
        if (
            self.page is None or self.page.split < 0
            or not self.page.active_ordinals["Dfull"]
            or role not in (ROLE_IDS["LINK_LABEL"], ROLE_IDS["PROSE_WORD"])
        ):
            return
        self.opportunities += 1
        capacity = self.page.ranked["Dfull"].remaining
        self.opportunity_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.opportunity_digest.update(index.to_bytes(8, "little"))
        self.opportunity_digest.update(role.to_bytes(2, "little"))
        self.opportunity_digest.update(capacity.to_bytes(4, "little"))
        for ordinal in sorted(self.page.active_ordinals["Dfull"]):
            self.opportunity_digest.update(ordinal.to_bytes(4, "little"))
        if not capacity:
            self.deactivated_opportunities += 1
            return
        if any(self.page.ranked[lane].remaining < capacity for lane in CONTROLS):
            self.deactivated_opportunities += 1
            return
        self.control_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.control_digest.update(index.to_bytes(8, "little"))
        self.control_digest.update(capacity.to_bytes(4, "little"))
        for lane in LANES:
            self.control_digest.update(lane.encode("ascii"))
            self.control_digest.update(self.page.ranked[lane].remaining.to_bytes(4, "little"))
        if event.kind != "token" or event.encoded in self.page.prefix:
            return
        cost = int(self.event_qbits[index])
        lane_hits = {
            "Dfull": self.page.ranked["Dfull"].active_rank(event.encoded) is not None,
        }
        for lane in CONTROLS:
            rank = self.page.ranked[lane].active_rank(event.encoded)
            lane_hits[lane] = rank is not None and rank <= capacity
        for lane, hit in lane_hits.items():
            if not hit:
                continue
            self.qbits[lane] += cost
            self.split_qbits[lane][self.page.split] += cost
            self.hits[lane] += 1
            self.split_hits[lane][self.page.split] += 1

    def _commit(self, ordinal: int) -> None:
        if self.page is None or self.page.ordinal != ordinal:
            raise ValueError("page commit mismatch")
        parser = self.page.parser
        record = PageRecord(ordinal, parser.title_key, self.page.prose.copy())
        self.pages.append(record)
        if record.title_key:
            self.title_index[record.title_key].append(record)
        self.global_prose.update(record.prose)
        self.previous_page = record
        self.index_digest.update(ordinal.to_bytes(4, "little"))
        self.index_digest.update(len(record.title_key).to_bytes(2, "little"))
        self.index_digest.update(record.title_key)
        update_counter_digest(self.index_digest, record.prose)
        self.committed_pages += 1
        self.page = None

    def run(self) -> RunResult:
        for index, event in enumerate(self.parsed.events):
            start = self.page_starts.get(event.start)
            if start is not None:
                ordinal, expected_raw = start
                if self.page is not None or self.raw_position != expected_raw:
                    raise ValueError("page-open alignment changed")
                split = split_for_page(ordinal, self.page_count) if ordinal < self.page_count else -1
                self.page = CurrentPage(ordinal, split, ForwardPageStage(ordinal))
                self.page.ranked = {
                    "Dblind": RankedReservoir.from_counter({}, set()),
                    "Dprior": RankedReservoir.from_counter({}, set()),
                    "Dglobal": RankedReservoir.from_counter(self.global_prose, set()),
                    "Dfull": RankedReservoir.from_counter({}, set()),
                }

            role = role_id(self.wiki)
            self._score(index, event, role)
            if self.page is not None and event.kind == "token" and role == ROLE_IDS["PROSE_WORD"]:
                self.page.prose[event.encoded] += 1
            if self.page is not None and event.kind == "token":
                self.page.prefix.add(event.encoded)
                for reservoir in self.page.ranked.values():
                    reservoir.remove(event.encoded)
            for byte in event.decoded:
                self.wiki.update(byte)
            self.raw_position += len(event.decoded)
            signal = self.page.parser.observe(event) if self.page is not None else None
            if self.page is not None:
                for target in self.page.parser.drain_targets():
                    self.parser_digest.update(self.page.ordinal.to_bytes(4, "little"))
                    self.parser_digest.update(index.to_bytes(8, "little"))
                    self.parser_digest.update(len(target.key).to_bytes(2, "little"))
                    self.parser_digest.update(target.key)
                    self._activate(target, index)

            end = self.page_ends.get(event.end)
            if end is not None:
                ordinal, expected_raw = end
                if self.raw_position != expected_raw or signal is None or not signal.page_closed:
                    raise ValueError("page-close parser alignment changed")
                raw_start = self.intervals[ordinal][0]
                page_bytes = self.parsed.decoded[raw_start:expected_raw]
                if not page_bytes.startswith(PAGE_OPEN) or not page_bytes.endswith(PAGE_CLOSE):
                    raise ValueError("page interval does not bind XML tags")
                self._commit(ordinal)

        if self.raw_position != len(self.parsed.decoded) or self.committed_pages != self.page_count:
            raise ValueError("WIKIFORWARD replay did not consume the complete population")
        return RunResult(
            qbits=dict(self.qbits),
            split_qbits={lane: tuple(values) for lane, values in self.split_qbits.items()},
            stats={
                "committed_pages": self.committed_pages,
                "title_keys": len(self.title_index),
                "duplicate_title_keys": sum(1 for rows in self.title_index.values() if len(rows) > 1),
                "target_completions": self.target_completions,
                "unique_resolutions": self.unique_resolutions,
                "duplicate_or_missing_resolutions": self.duplicate_or_missing_resolutions,
                "accepted_updates": self.accepted_updates,
                "discarded_control_updates": self.discarded_control_updates,
                "idempotent_updates": self.idempotent_updates,
                "opportunities": self.opportunities,
                "deactivated_opportunities": self.deactivated_opportunities,
                "hits": dict(self.hits),
                "split_hits": {lane: list(values) for lane, values in self.split_hits.items()},
                "blind_key_violations": self.blind_key_violations,
                "trailing_partial_page_uncommitted": self.page is not None,
            },
            parser_sha256=self.parser_digest.hexdigest(),
            index_sha256=self.index_digest.hexdigest(),
            activation_sha256=self.activation_digest.hexdigest(),
            opportunity_sha256=self.opportunity_digest.hexdigest(),
            control_sha256=self.control_digest.hexdigest(),
        )


def event_costs(parsed: ParsedStore, costs: np.ndarray) -> np.ndarray:
    result = np.zeros(len(parsed.events), dtype=np.int64)
    for index, event in enumerate(parsed.events):
        if event.kind == "token":
            result[index] = int(costs[event.start:event.end].sum())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint-p1", type=Path, default=ROOT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1")
    parser.add_argument("--joint-payload", type=Path, default=ROOT / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload")
    parser.add_argument("--wrt-store", type=Path, default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin")
    parser.add_argument("--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin")
    parser.add_argument("--dictionary", type=Path, default=Path("/home/x/enwiki9-nonproof/results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/clean-build-b/build/english.dic"))
    parser.add_argument("--page-receipt", type=Path, default=ROOT / "results/sibyl_page_boundaries_v1/receipt.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("nonempty WIKIFORWARD output directory forbids startup")
    output_dir.mkdir(parents=True, exist_ok=True)

    inputs = {
        "joint_p1": artifact(args.joint_p1), "joint_payload": artifact(args.joint_payload),
        "wrt_store": artifact(args.wrt_store), "raw_input": artifact(args.raw_input),
        "dictionary": artifact(args.dictionary), "page_receipt": artifact(args.page_receipt),
    }
    for name, value in inputs.items():
        verify_artifact(name, value)
    source_binding = bind_sources()
    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT inverse differs from raw input")
    intervals = page_intervals(parsed)
    if len(intervals) != 1325 or raw.count(PAGE_OPEN) != 1326 or raw.count(PAGE_CLOSE) != 1325:
        raise ValueError("complete-page population changed")
    page_receipt = json.loads(args.page_receipt.read_text())
    population = next(row for row in page_receipt["populations"] if row["label"] == "opening10m")
    if population["page_open_offsets"] != [row[0] for row in intervals] + [raw.rfind(PAGE_OPEN)]:
        raise ValueError("page opens differ from bound receipt")
    if population["page_close_end_offsets"] != [row[1] for row in intervals]:
        raise ValueError("page closes differ from bound receipt")

    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    p1 = read_p1(args.joint_p1, len(truth))
    parent_payload = args.joint_payload.read_bytes()
    if range_encode(p1, truth) != parent_payload:
        raise ValueError("joint P1 did not reproduce exact parent payload")
    zero, one = qbit_tables()
    qbit_hashes = (
        sha256_bytes(zero.astype("<i4", copy=False).tobytes()),
        sha256_bytes(one.astype("<i4", copy=False).tobytes()),
    )
    if qbit_hashes != EXPECTED_QBIT_HASHES:
        raise ValueError("Q256 table hashes differ")
    costs = event_costs(parsed, byte_qbits(p1, truth, zero, one))
    first = ForwardMachine(parsed, intervals, costs).run()
    second = ForwardMachine(parsed, intervals, costs).run()
    if first != second:
        raise ValueError("repeated WIKIFORWARD replay differs")

    split_raw = [0, 0, 0]
    for ordinal, (raw_start, raw_end, _, _) in enumerate(intervals):
        split_raw[split_for_page(ordinal, len(intervals))] += raw_end - raw_start
    lanes: dict[str, object] = {}
    for lane in LANES:
        splits = []
        for name, raw_bytes, qbits in zip(SPLITS, split_raw, first.split_qbits[lane], strict=True):
            splits.append({
                "name": name, "raw_bytes": raw_bytes, "qbits": qbits,
                "byte_equivalent": qbits / QBIT_DENOMINATOR,
                "bytes_per_million": qbits * 1_000_000 / (QBIT_DENOMINATOR * raw_bytes),
            })
        lanes[lane] = {
            "qbits": first.qbits[lane],
            "byte_equivalent": first.qbits[lane] / QBIT_DENOMINATOR,
            "hits": first.stats["hits"][lane], "splits": splits,
        }
    exact = first.qbits["Dfull"]
    margins = {control: exact - first.qbits[control] for control in CONTROLS}
    split_scale = all(
        first.split_qbits["Dfull"][i] * 1_000_000
        >= SPLIT_GATE_BYTES_PER_MILLION * QBIT_DENOMINATOR * split_raw[i]
        for i in range(3)
    )
    split_margins = all(
        first.split_qbits["Dfull"][i] > first.split_qbits[control][i]
        for control in CONTROLS for i in range(3)
    )
    conditions = {
        "Dfull_at_least_60000_byte_equivalent": exact >= TOTAL_GATE_BYTES * QBIT_DENOMINATOR,
        "Dfull_each_split_at_least_5000_B_per_M": split_scale,
        "Dfull_minus_each_control_at_least_10000_byte_equivalent": all(
            margin >= CONTROL_MARGIN_BYTES * QBIT_DENOMINATOR for margin in margins.values()
        ),
        "Dfull_control_margin_positive_each_split": split_margins,
    }
    verdict = "AUTHORIZE_Q0" if all(conditions.values()) else "REJECT"
    exact_bytes = exact / QBIT_DENOMINATOR
    decision = {
        "schema": "wikiforward_prior_destination_page_lexicon_qm1_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_causal_truth_aware_candidate_universe_ceiling",
        "claim_boundary": "Q256 prefix-novel truth-aware membership ceiling only; index, lexicons, counts, rank, selector, source, framing, and termination are free.",
        "inputs": inputs, "source_binding": source_binding,
        "scope": {
            "raw_bytes": len(raw), "wrt_bytes": len(parsed.stream),
            "complete_pages": len(intervals), "trailing_partial_page_present": True,
            "split_raw_bytes": dict(zip(SPLITS, split_raw, strict=True)),
        },
        "parent": {"payload_bytes": len(parent_payload), "payload_sha256": sha256_bytes(parent_payload), "replay_identity": True},
        "q256": {"denominator_qbits_per_byte": QBIT_DENOMINATOR, "zero_table_sha256": qbit_hashes[0], "one_table_sha256": qbit_hashes[1]},
        "result": {
            "lanes": lanes, "stats": first.stats,
            "digests": {
                "parser_sha256": first.parser_sha256, "index_sha256": first.index_sha256,
                "activation_sha256": first.activation_sha256,
                "opportunity_sha256": first.opportunity_sha256,
                "control_sha256": first.control_sha256,
            },
        },
        "exploratory_observation_reconciliation": {
            "narrative_Dfull_byte_equivalent": EXPLORATORY_DFULL_BYTES,
            "exact_QM1_Dfull_byte_equivalent": exact_bytes,
            "difference_byte_equivalent": exact_bytes - EXPLORATORY_DFULL_BYTES,
            "reproduced_within_one_byte": abs(exact_bytes - EXPLORATORY_DFULL_BYTES) <= 1.0,
            "authority": "Only this exact QM1 receipt is authoritative.",
        },
        "economics": {
            "Dfull_qbits": exact, "Dfull_byte_equivalent": exact_bytes,
            "control_margin_qbits": margins,
            "control_margin_byte_equivalent": {name: value / QBIT_DENOMINATOR for name, value in margins.items()},
            "forecast_score_bytes_unchanged": FORECAST_BYTES,
            "forecast_debt_bytes": FORECAST_DEBT_BYTES, "score_credit_bytes": 0,
        },
        "exactness": {
            "input_identities": True, "parent_payload_identity": True,
            "wrt_raw_inverse": True, "page_receipt_binding": True,
            "q256_table_hashes": True,
            "repeated_parser_index_activation_opportunity_control_digests": True,
            "all_sources_strictly_earlier_closed_pages": True,
            "target_complete_event_aligned": True,
            "active_destination_ordinals_idempotent": True,
            "prefix_novel_raw_event_identity": True,
            "blind_destination_key_inequality": first.stats["blind_key_violations"] == 0,
            "lane_opportunity_capacity_multisets_identical": True,
        },
        "gates": {"conditions": conditions, "failed_conditions": [name for name, passed in conditions.items() if not passed]},
        "decision": {
            "verdict": verdict, "paid_q0_authorized": verdict == "AUTHORIZE_Q0",
            "native_integration_authorized": False, "forecast_change_authorized": False,
            "full_1g_authorized": False,
            "next_action": (
                "Materialize only the frozen paid hit/escape-plus-rank Q0." if verdict == "AUTHORIZE_Q0"
                else "Retire the exact destination-source union, prefix-novel filter, event universe, and controls without rescue sweeps."
            ),
        },
        "score_credit_bytes": 0,
    }
    (output_dir / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID, "decision": verdict,
        "Dfull_byte_equivalent": exact_bytes,
        "minimum_control_margin_byte_equivalent": min(margins.values()) / QBIT_DENOMINATOR,
        "reproduced_exploratory_observation": abs(exact_bytes - EXPLORATORY_DFULL_BYTES) <= 1.0,
        "score_credit_bytes": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
