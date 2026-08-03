#!/usr/bin/env python3
"""Run the frozen WIKIGRAPH causal co-link target QM1 ceiling."""

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

from janus_paid_residual_mdl_oracle import range_encode
from mobius2_tessera_typed_fiber_ceiling import byte_qbits, qbit_tables, read_p1
from sibyl_page_prompt_oracle import page_intervals
import wikiback_incoming_anchor_context_qh0 as wikiback
from wrt_exact import ParsedStore, WrtEvent, parse_store


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CANDIDATE_ID = "wikigraph_causal_colink_target_qm1_v1"
LANES = ("Cshuffle", "Cfreq", "Crecent", "Cprior", "G0")
CONTROLS = LANES[:-1]
SPLITS = ("development", "selection", "opened_confirmation")
PAGE_OPEN = b"<page>"
PAGE_CLOSE = b"</page>"
QBIT_DENOMINATOR = 2048
TOTAL_GATE_BYTES = 60_000
CONTROL_MARGIN_BYTES = 10_000
SPLIT_GATE_BYTES_PER_MILLION = 5_000
MAX_CANDIDATES = 64
FORECAST_BYTES = 109_389_323
FORECAST_DEBT_BYTES = 1_389_323

EXPECTED = {
    "joint_p1": (
        100_029_648,
        "b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719",
    ),
    "joint_payload": (
        1_617_484,
        "5ffaa128fa9e86e3883896a6d16b6c49e23693f5abdf14f1718e0e006533dca9",
    ),
    "wrt_store": (
        6_251_857,
        "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b",
    ),
    "raw_input": (
        10_000_000,
        "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97",
    ),
    "dictionary": (
        411_996,
        "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a",
    ),
    "page_receipt": (
        9_711_214,
        "e4f0db7f82759aa05b025cd65170206cb76fd22187eb29d7bbe96537928c7bcc",
    ),
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
    "projects/enwiki9/docs/wikigraph_causal_colink_target_qm1_plan.md",
    "projects/enwiki9/tools/wikigraph_causal_colink_target_qm1.py",
    *FROZEN_DONOR_HASHES.keys(),
)

FROZEN_CONFIG = {
    "schema": "wikigraph_causal_colink_target_qm1_config_v1",
    "candidate_id": CANDIDATE_ID,
    "graph_key": "wikiback.normalize_title over decoded title and link target",
    "candidate_identity": "tuple of complete exact WrtEvent.encoded values",
    "publication": "atomic only after complete source </page>",
    "opportunity": "immediately after event-aligned [[ and before target truth",
    "target_terminators": ["|", "#", "]]"],
    "candidate_capacity": MAX_CANDIDATES,
    "g0_ranking": [
        "descending distinct supporting closed pages",
        "descending global closed-prefix exact-program occurrences",
        "descending most recent supporting page ordinal",
        "ascending flattened exact WRT program bytes",
        "ascending canonical serialized program",
    ],
    "shuffle_serialization": (
        "WIKIGRAPH-CSHUFFLE-V1 NUL; u32le-length-prefixed title key; "
        "u32le page ordinal; u64le global opportunity ordinal; "
        "u32le-length-prefixed canonical source and candidate programs"
    ),
    "shuffle_bin": [
        "global occurrence_count.bit_length",
        "flattened exact-program byte length",
        "global distinct-source-page-count.bit_length",
    ],
    "lanes": list(LANES),
    "population_splits": "first 60%, next 20%, final 20% complete pages",
    "gross_gate_byte_equivalent": TOTAL_GATE_BYTES,
    "split_gate_bytes_per_million": SPLIT_GATE_BYTES_PER_MILLION,
    "control_margin_byte_equivalent": CONTROL_MARGIN_BYTES,
    "score_credit_bytes": 0,
}
CONFIG_BYTES = json.dumps(
    FROZEN_CONFIG, sort_keys=True, separators=(",", ":")
).encode("utf-8")
CONFIG_SHA256 = hashlib.sha256(CONFIG_BYTES).hexdigest()

Program = tuple[bytes, ...]


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
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def verify_artifact(name: str, observed: Mapping[str, object]) -> None:
    if (observed["bytes"], observed["sha256"]) != EXPECTED[name]:
        raise ValueError(f"{name} differs from frozen binding")


def bind_sources() -> dict[str, object]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    files: dict[str, object] = {}
    for relative in BOUND_SOURCE_FILES:
        path = REPO_ROOT / relative
        current = path.read_bytes()
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        if current != committed:
            raise ValueError(f"bound source differs from HEAD: {relative}")
        digest = sha256_bytes(current)
        if relative in FROZEN_DONOR_HASHES:
            if digest != FROZEN_DONOR_HASHES[relative]:
                raise ValueError(f"frozen donor bytes changed: {relative}")
        files[relative] = {"bytes": len(current), "sha256": digest}
    return {
        "git_commit": commit,
        "tracked_files": files,
        "config_sha256": CONFIG_SHA256,
        "score_charge_bytes": 0,
    }


def split_for_page(ordinal: int, count: int) -> int:
    if ordinal < count * 3 // 5:
        return 0
    if ordinal < count * 4 // 5:
        return 1
    return 2


def serialize_program(program: Program) -> bytes:
    output = bytearray(len(program).to_bytes(4, "little"))
    for encoded in program:
        output.extend(len(encoded).to_bytes(4, "little"))
        output.extend(encoded)
    return bytes(output)


def flattened(program: Program) -> bytes:
    return b"".join(program)


def program_order(program: Program) -> tuple[bytes, bytes]:
    return flattened(program), serialize_program(program)


def update_program_digest(digest: Any, program: Program) -> None:
    encoded = serialize_program(program)
    digest.update(len(encoded).to_bytes(4, "little"))
    digest.update(encoded)


def shuffle_hash(
    title_key: bytes,
    page_ordinal: int,
    opportunity_ordinal: int,
    source: Program,
    candidate: Program,
) -> bytes:
    digest = hashlib.sha256()
    digest.update(b"WIKIGRAPH-CSHUFFLE-V1\0")
    digest.update(len(title_key).to_bytes(4, "little"))
    digest.update(title_key)
    digest.update(page_ordinal.to_bytes(4, "little"))
    digest.update(opportunity_ordinal.to_bytes(8, "little"))
    for program in (source, candidate):
        encoded = serialize_program(program)
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
    return digest.digest()


@dataclass(frozen=True)
class FullLink:
    target_key: bytes
    program: Program
    start_local: int
    end_local: int
    link_ordinal: int


@dataclass
class GraphPageStage(wikiback.PageStage):
    completed_targets: list[FullLink] = field(default_factory=list)
    full_links: list[FullLink] = field(default_factory=list)

    def _finish_link(
        self, close_event: int, label_events: Sequence[WrtEvent] = ()
    ) -> None:
        raw = b"".join(event.decoded for event in self.link_target_events)
        key = wikiback.normalize_title(raw)
        program = tuple(event.encoded for event in self.link_target_events)
        if key and program:
            start_local = self.link_open_event + 1
            end_local = start_local + len(self.link_target_events)
            if end_local > len(self.events):
                raise ValueError("WIKIGRAPH target interval exceeds parser prefix")
            link = FullLink(
                target_key=key,
                program=program,
                start_local=start_local,
                end_local=end_local,
                link_ordinal=len(self.full_links),
            )
            self.full_links.append(link)
            self.completed_targets.append(link)
        super()._finish_link(close_event, label_events)

    def drain_targets(self) -> tuple[FullLink, ...]:
        result = tuple(self.completed_targets)
        self.completed_targets.clear()
        return result


@dataclass(frozen=True)
class PageRecord:
    ordinal: int
    title_key: bytes
    links: tuple[FullLink, ...]
    program_counts: tuple[tuple[Program, int], ...]


@dataclass(frozen=True)
class CandidateBase:
    candidates: dict[str, tuple[Program, ...]]
    g0_sources: tuple[int, ...]
    k: int


@dataclass(frozen=True)
class Opportunity:
    ordinal: int
    global_open_event: int
    candidates: dict[str, tuple[Program, ...]] | None
    k: int


@dataclass
class CurrentPage:
    ordinal: int
    split: int
    global_event_start: int
    parser: GraphPageStage
    base: CandidateBase | None = None
    pending: Opportunity | None = None
    opener_count: int = 0


@dataclass(frozen=True)
class RunResult:
    qbits: dict[str, int]
    split_qbits: dict[str, tuple[int, int, int]]
    stats: dict[str, object]
    parser_sha256: str
    graph_sha256: str
    opportunity_sha256: str
    candidate_sha256: str
    control_sha256: str
    totals_sha256: str


class GraphMachine:
    def __init__(
        self,
        parsed: ParsedStore,
        intervals: Sequence[tuple[int, int, int, int]],
        event_qbits: np.ndarray,
    ) -> None:
        self.parsed = parsed
        self.intervals = intervals
        self.event_qbits = event_qbits
        self.page_count = len(intervals)
        self.page_starts = {
            row_start // 8: (i, raw_start)
            for i, (raw_start, _, row_start, _) in enumerate(intervals)
        }
        self.page_ends = {
            row_end // 8: (i, raw_end)
            for i, (_, raw_end, _, row_end) in enumerate(intervals)
        }
        partial_start = parsed.decoded.rfind(PAGE_OPEN)
        raw_cursor = 0
        for event in parsed.events:
            if raw_cursor == partial_start:
                self.page_starts[event.start] = (self.page_count, partial_start)
                break
            raw_cursor += len(event.decoded)
        else:
            raise ValueError("trailing page opener cuts a WRT event")

        self.page: CurrentPage | None = None
        self.raw_position = 0
        self.pages: list[PageRecord] = []
        self.incoming_pages: dict[bytes, list[PageRecord]] = defaultdict(list)
        self.global_counts: Counter[Program] = Counter()
        self.global_page_counts: Counter[Program] = Counter()
        self.global_last: dict[Program, tuple[int, int]] = {}
        self.shuffle_bins: dict[tuple[int, int, int], tuple[Program, ...]] = {}

        self.qbits = {lane: 0 for lane in LANES}
        self.split_qbits = {lane: [0, 0, 0] for lane in LANES}
        self.hits = {lane: 0 for lane in LANES}
        self.split_hits = {lane: [0, 0, 0] for lane in LANES}
        self.committed_pages = 0
        self.committed_links = 0
        self.link_openers = 0
        self.completed_targets = 0
        self.invalid_or_incomplete_targets = 0
        self.graph_nonempty_opportunities = 0
        self.active_opportunities = 0
        self.deactivated_control_opportunities = 0
        self.max_k = 0
        self.strictly_earlier_sources = 0
        self.distinct_identity_checks = 0
        self.shuffle_checks = 0

        self.parser_digest = hashlib.sha256()
        self.graph_digest = hashlib.sha256()
        self.opportunity_digest = hashlib.sha256()
        self.candidate_digest = hashlib.sha256()
        self.control_digest = hashlib.sha256()
        self.totals_digest = hashlib.sha256()

    def _bin(self, program: Program) -> tuple[int, int, int]:
        return (
            int(self.global_counts[program]).bit_length(),
            len(flattened(program)),
            int(self.global_page_counts[program]).bit_length(),
        )

    def _rebuild_bins(self) -> None:
        buckets: dict[tuple[int, int, int], list[Program]] = defaultdict(list)
        for program in self.global_counts:
            buckets[self._bin(program)].append(program)
        self.shuffle_bins = {
            key: tuple(sorted(programs, key=program_order))
            for key, programs in buckets.items()
        }

    def _g0(self) -> tuple[tuple[Program, ...], tuple[int, ...]]:
        if self.page is None:
            raise ValueError("WIKIGRAPH candidate construction outside page")
        title_key = self.page.parser.title_key
        sources = tuple(self.incoming_pages.get(title_key, ()))
        support: dict[Program, set[int]] = defaultdict(set)
        recent: dict[Program, int] = {}
        for source in sources:
            if source.ordinal >= self.page.ordinal:
                raise ValueError("WIKIGRAPH source is not strictly earlier")
            self.strictly_earlier_sources += 1
            for link in source.links:
                if link.target_key == title_key:
                    continue
                support[link.program].add(source.ordinal)
                recent[link.program] = max(recent.get(link.program, -1), source.ordinal)
        ordered = sorted(
            support,
            key=lambda program: (
                -len(support[program]),
                -self.global_counts[program],
                -recent[program],
                *program_order(program),
            ),
        )
        return tuple(ordered[:MAX_CANDIDATES]), tuple(row.ordinal for row in sources)

    def _prior(self, k: int) -> tuple[Program, ...] | None:
        for page in reversed(self.pages):
            counts = dict(page.program_counts)
            if len(counts) < k:
                continue
            ordered = sorted(
                counts,
                key=lambda program: (-counts[program], *program_order(program)),
            )
            return tuple(ordered[:k])
        return None

    def _base(self) -> CandidateBase:
        g0, sources = self._g0()
        k = len(g0)
        if not k:
            return CandidateBase({}, sources, 0)
        freq = tuple(
            sorted(
                self.global_counts,
                key=lambda program: (
                    -self.global_counts[program],
                    *program_order(program),
                ),
            )[:k]
        )
        recent = tuple(
            sorted(
                self.global_last,
                key=lambda program: (
                    -self.global_last[program][0],
                    -self.global_last[program][1],
                    *program_order(program),
                ),
            )[:k]
        )
        prior = self._prior(k)
        if len(freq) != k or len(recent) != k or prior is None:
            return CandidateBase({}, sources, k)
        return CandidateBase(
            {"Cfreq": freq, "Crecent": recent, "Cprior": prior, "G0": g0},
            sources,
            k,
        )

    def _shuffle(
        self, g0: tuple[Program, ...], opportunity_ordinal: int
    ) -> tuple[Program, ...] | None:
        if self.page is None:
            raise ValueError("WIKIGRAPH shuffle outside page")
        excluded = set(g0)
        chosen: set[Program] = set()
        result: list[Program] = []
        for source in g0:
            candidates = (
                program
                for program in self.shuffle_bins.get(self._bin(source), ())
                if program not in excluded and program not in chosen
            )
            try:
                selected = min(
                    candidates,
                    key=lambda program: (
                        shuffle_hash(
                            self.page.parser.title_key,
                            self.page.ordinal,
                            opportunity_ordinal,
                            source,
                            program,
                        ),
                        *program_order(program),
                    ),
                )
            except ValueError:
                return None
            chosen.add(selected)
            result.append(selected)
        if len(result) != len(g0) or len(chosen) != len(g0) or chosen & excluded:
            raise ValueError("WIKIGRAPH shuffled control is not injective and blind")
        self.shuffle_checks += 1
        return tuple(result)

    def _freeze_opportunity(self, global_event: int) -> None:
        if self.page is None or self.page.pending is not None:
            raise ValueError("WIKIGRAPH opportunity state overlap")
        ordinal = self.link_openers
        self.link_openers += 1
        self.page.opener_count += 1
        if self.page.base is None:
            self.page.base = self._base()
        base = self.page.base
        self.opportunity_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.opportunity_digest.update(ordinal.to_bytes(8, "little"))
        self.opportunity_digest.update(global_event.to_bytes(8, "little"))
        self.opportunity_digest.update(len(self.page.parser.title_key).to_bytes(4, "little"))
        self.opportunity_digest.update(self.page.parser.title_key)
        self.opportunity_digest.update(base.k.to_bytes(4, "little"))
        for source_ordinal in base.g0_sources:
            self.opportunity_digest.update(source_ordinal.to_bytes(4, "little"))
        if not base.k:
            self.page.pending = Opportunity(ordinal, global_event, None, 0)
            return
        self.graph_nonempty_opportunities += 1
        shuffle = self._shuffle(base.candidates["G0"], ordinal)
        if shuffle is None or len(base.candidates) != 4:
            self.deactivated_control_opportunities += 1
            self.page.pending = Opportunity(ordinal, global_event, None, base.k)
            return
        candidates = dict(base.candidates)
        candidates["Cshuffle"] = shuffle
        if set(candidates) != set(LANES):
            raise ValueError("WIKIGRAPH lane set changed")
        if any(len(values) != base.k or len(set(values)) != base.k for values in candidates.values()):
            raise ValueError("WIKIGRAPH lane capacity or injectivity changed")
        if set(shuffle) & set(candidates["G0"]):
            raise ValueError("WIKIGRAPH shuffled control leaked G0 identity")
        self.active_opportunities += 1
        self.max_k = max(self.max_k, base.k)
        self.distinct_identity_checks += 1
        self.control_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.control_digest.update(ordinal.to_bytes(8, "little"))
        self.control_digest.update(base.k.to_bytes(4, "little"))
        for lane in LANES:
            self.candidate_digest.update(lane.encode("ascii"))
            self.candidate_digest.update(base.k.to_bytes(4, "little"))
            for rank, program in enumerate(candidates[lane]):
                self.candidate_digest.update(rank.to_bytes(4, "little"))
                update_program_digest(self.candidate_digest, program)
        self.page.pending = Opportunity(ordinal, global_event, candidates, base.k)

    def _complete_target(self, link: FullLink) -> None:
        if self.page is None or self.page.pending is None:
            raise ValueError("WIKIGRAPH completed target lacks frozen opportunity")
        pending = self.page.pending
        self.page.pending = None
        self.completed_targets += 1
        start = self.page.global_event_start + link.start_local
        end = self.page.global_event_start + link.end_local
        observed = tuple(event.encoded for event in self.parsed.events[start:end])
        if observed != link.program or not (pending.global_open_event < start <= end):
            raise ValueError("WIKIGRAPH target program interval changed")
        self.parser_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.parser_digest.update(pending.ordinal.to_bytes(8, "little"))
        self.parser_digest.update(start.to_bytes(8, "little"))
        self.parser_digest.update(end.to_bytes(8, "little"))
        self.parser_digest.update(len(link.target_key).to_bytes(4, "little"))
        self.parser_digest.update(link.target_key)
        update_program_digest(self.parser_digest, link.program)
        if pending.candidates is None or self.page.split < 0:
            return
        cost = int(self.event_qbits[start:end].sum())
        for lane in LANES:
            if link.program not in pending.candidates[lane]:
                continue
            self.qbits[lane] += cost
            self.split_qbits[lane][self.page.split] += cost
            self.hits[lane] += 1
            self.split_hits[lane][self.page.split] += 1
            self.totals_digest.update(lane.encode("ascii"))
            self.totals_digest.update(self.page.ordinal.to_bytes(4, "little"))
            self.totals_digest.update(pending.ordinal.to_bytes(8, "little"))
            self.totals_digest.update(cost.to_bytes(8, "little"))

    def _commit(self, ordinal: int) -> None:
        if self.page is None or self.page.ordinal != ordinal:
            raise ValueError("WIKIGRAPH page commit mismatch")
        if self.page.pending is not None:
            self.invalid_or_incomplete_targets += 1
            self.page.pending = None
        parser = self.page.parser
        counts = Counter(link.program for link in parser.full_links)
        record = PageRecord(
            ordinal=ordinal,
            title_key=parser.title_key,
            links=tuple(parser.full_links),
            program_counts=tuple(sorted(counts.items(), key=lambda row: program_order(row[0]))),
        )
        self.pages.append(record)
        linked_keys = {link.target_key for link in record.links}
        for key in sorted(linked_keys):
            self.incoming_pages[key].append(record)
        distinct = set(counts)
        for link in record.links:
            self.global_counts[link.program] += 1
            self.global_last[link.program] = (ordinal, link.link_ordinal)
        for program in distinct:
            self.global_page_counts[program] += 1
        self._rebuild_bins()

        self.graph_digest.update(ordinal.to_bytes(4, "little"))
        self.graph_digest.update(len(record.title_key).to_bytes(4, "little"))
        self.graph_digest.update(record.title_key)
        self.graph_digest.update(len(record.links).to_bytes(4, "little"))
        for link in record.links:
            self.graph_digest.update(link.link_ordinal.to_bytes(4, "little"))
            self.graph_digest.update(len(link.target_key).to_bytes(4, "little"))
            self.graph_digest.update(link.target_key)
            update_program_digest(self.graph_digest, link.program)
        self.committed_pages += 1
        self.committed_links += len(record.links)
        self.page = None

    def run(self) -> RunResult:
        for index, event in enumerate(self.parsed.events):
            start = self.page_starts.get(event.start)
            if start is not None:
                ordinal, expected_raw = start
                if self.page is not None or self.raw_position != expected_raw:
                    raise ValueError("page-open alignment changed")
                split = (
                    split_for_page(ordinal, self.page_count)
                    if ordinal < self.page_count
                    else -1
                )
                self.page = CurrentPage(
                    ordinal=ordinal,
                    split=split,
                    global_event_start=index,
                    parser=GraphPageStage(ordinal),
                )

            before_phase = self.page.parser.link_phase if self.page is not None else "none"
            self.raw_position += len(event.decoded)
            signal = self.page.parser.observe(event) if self.page is not None else None
            if self.page is not None:
                completed = self.page.parser.drain_targets()
                if completed:
                    if len(completed) != 1:
                        raise ValueError("multiple WIKIGRAPH targets completed in one event")
                    self._complete_target(completed[0])
                elif before_phase != "none" and self.page.parser.link_phase == "none":
                    if self.page.pending is None:
                        raise ValueError("discarded WIKIGRAPH target lacks opportunity")
                    self.page.pending = None
                    self.invalid_or_incomplete_targets += 1
                if (
                    self.page.parser.link_phase == "target"
                    and self.page.parser.link_open_event == len(self.page.parser.events) - 1
                ):
                    self._freeze_opportunity(index)

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

        if self.raw_position != len(self.parsed.decoded):
            raise ValueError("WIKIGRAPH replay did not consume the WRT inverse")
        if self.committed_pages != self.page_count:
            raise ValueError("WIKIGRAPH complete-page count changed")
        return RunResult(
            qbits=dict(self.qbits),
            split_qbits={lane: tuple(values) for lane, values in self.split_qbits.items()},
            stats={
                "committed_pages": self.committed_pages,
                "committed_links": self.committed_links,
                "incoming_graph_keys": len(self.incoming_pages),
                "global_distinct_programs": len(self.global_counts),
                "link_openers": self.link_openers,
                "completed_targets": self.completed_targets,
                "invalid_or_incomplete_targets": self.invalid_or_incomplete_targets,
                "graph_nonempty_opportunities": self.graph_nonempty_opportunities,
                "active_opportunities": self.active_opportunities,
                "deactivated_control_opportunities": self.deactivated_control_opportunities,
                "max_k": self.max_k,
                "strictly_earlier_source_checks": self.strictly_earlier_sources,
                "distinct_identity_checks": self.distinct_identity_checks,
                "shuffle_injectivity_checks": self.shuffle_checks,
                "hits": dict(self.hits),
                "split_hits": {lane: list(values) for lane, values in self.split_hits.items()},
                "trailing_partial_page_uncommitted": self.page is not None,
            },
            parser_sha256=self.parser_digest.hexdigest(),
            graph_sha256=self.graph_digest.hexdigest(),
            opportunity_sha256=self.opportunity_digest.hexdigest(),
            candidate_sha256=self.candidate_digest.hexdigest(),
            control_sha256=self.control_digest.hexdigest(),
            totals_sha256=self.totals_digest.hexdigest(),
        )


def event_costs(parsed: ParsedStore, costs: np.ndarray) -> np.ndarray:
    result = np.zeros(len(parsed.events), dtype=np.int64)
    for index, event in enumerate(parsed.events):
        result[index] = int(costs[event.start:event.end].sum())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--joint-payload",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin"
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/english.dic"
        ),
    )
    parser.add_argument(
        "--page-receipt",
        type=Path,
        default=ROOT / "results/sibyl_page_boundaries_v1/receipt.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("nonempty WIKIGRAPH output directory forbids startup")
    output_dir.mkdir(parents=True, exist_ok=True)

    inputs = {
        "joint_p1": artifact(args.joint_p1),
        "joint_payload": artifact(args.joint_payload),
        "wrt_store": artifact(args.wrt_store),
        "raw_input": artifact(args.raw_input),
        "dictionary": artifact(args.dictionary),
        "page_receipt": artifact(args.page_receipt),
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
    population = next(
        row for row in page_receipt["populations"] if row["label"] == "opening10m"
    )
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

    first = GraphMachine(parsed, intervals, costs).run()
    second = GraphMachine(parsed, intervals, costs).run()
    if first != second:
        raise ValueError("repeated WIKIGRAPH replay differs")

    split_raw = [0, 0, 0]
    for ordinal, (raw_start, raw_end, _, _) in enumerate(intervals):
        split_raw[split_for_page(ordinal, len(intervals))] += raw_end - raw_start

    lanes: dict[str, object] = {}
    for lane in LANES:
        splits = []
        for name, raw_bytes, qbits in zip(
            SPLITS, split_raw, first.split_qbits[lane], strict=True
        ):
            splits.append(
                {
                    "name": name,
                    "raw_bytes": raw_bytes,
                    "qbits": qbits,
                    "byte_equivalent": qbits / QBIT_DENOMINATOR,
                    "bytes_per_million": qbits
                    * 1_000_000
                    / (QBIT_DENOMINATOR * raw_bytes),
                }
            )
        lanes[lane] = {
            "qbits": first.qbits[lane],
            "byte_equivalent": first.qbits[lane] / QBIT_DENOMINATOR,
            "hits": first.stats["hits"][lane],
            "splits": splits,
        }

    exact = first.qbits["G0"]
    margins = {control: exact - first.qbits[control] for control in CONTROLS}
    conditions = {
        "G0_at_least_60000_byte_equivalent": exact
        >= TOTAL_GATE_BYTES * QBIT_DENOMINATOR,
        "G0_each_split_at_least_5000_B_per_M": all(
            first.split_qbits["G0"][index] * 1_000_000
            >= SPLIT_GATE_BYTES_PER_MILLION * QBIT_DENOMINATOR * split_raw[index]
            for index in range(3)
        ),
        "G0_minus_each_control_at_least_10000_byte_equivalent": all(
            margin >= CONTROL_MARGIN_BYTES * QBIT_DENOMINATOR
            for margin in margins.values()
        ),
        "G0_control_margin_positive_each_split": all(
            first.split_qbits["G0"][index]
            > first.split_qbits[control][index]
            for control in CONTROLS
            for index in range(3)
        ),
    }
    verdict = "AUTHORIZE_Q0" if all(conditions.values()) else "REJECT"
    exactness = {
        "input_identities": True,
        "parent_payload_identity": True,
        "wrt_raw_inverse": True,
        "page_receipt_binding": True,
        "q256_table_hashes": True,
        "frozen_donor_hashes": True,
        "repeated_parser_graph_candidate_control_total_digests": True,
        "all_sources_fully_closed_and_strictly_earlier": True,
        "all_candidates_frozen_before_first_target_bit": True,
        "target_complete_event_aligned": True,
        "legal_terminator_hits_only": True,
        "distinct_graph_node_and_exact_program_identities": True,
        "shuffle_injective_and_excludes_G0": True,
        "lane_opportunity_capacity_multisets_identical": True,
        "trailing_partial_page_never_published_or_scored": True,
    }
    decision = {
        "schema": "wikigraph_causal_colink_target_qm1_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_causal_truth_aware_candidate_universe_ceiling",
        "claim_boundary": (
            "Rounded-Q256 truth-aware exact-program membership ceiling only; "
            "hit/escape, rank, graph, source, framing, model, and termination are free."
        ),
        "config": {"value": FROZEN_CONFIG, "sha256": CONFIG_SHA256},
        "inputs": inputs,
        "source_binding": source_binding,
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "complete_pages": len(intervals),
            "trailing_partial_page_present": True,
            "split_raw_bytes": dict(zip(SPLITS, split_raw, strict=True)),
        },
        "parent": {
            "payload_bytes": len(parent_payload),
            "payload_sha256": sha256_bytes(parent_payload),
            "replay_identity": True,
        },
        "q256": {
            "denominator_qbits_per_byte": QBIT_DENOMINATOR,
            "zero_table_sha256": qbit_hashes[0],
            "one_table_sha256": qbit_hashes[1],
        },
        "result": {
            "lanes": lanes,
            "stats": first.stats,
            "digests": {
                "parser_sha256": first.parser_sha256,
                "graph_sha256": first.graph_sha256,
                "opportunity_sha256": first.opportunity_sha256,
                "candidate_sha256": first.candidate_sha256,
                "control_sha256": first.control_sha256,
                "totals_sha256": first.totals_sha256,
            },
        },
        "economics": {
            "G0_qbits": exact,
            "G0_byte_equivalent": exact / QBIT_DENOMINATOR,
            "control_margin_qbits": margins,
            "control_margin_byte_equivalent": {
                name: value / QBIT_DENOMINATOR for name, value in margins.items()
            },
            "forecast_score_bytes_unchanged": FORECAST_BYTES,
            "forecast_debt_bytes": FORECAST_DEBT_BYTES,
            "score_credit_bytes": 0,
        },
        "exactness": exactness,
        "gates": {
            "conditions": conditions,
            "failed_conditions": [
                name for name, passed in conditions.items() if not passed
            ],
        },
        "decision": {
            "verdict": verdict,
            "paid_q0_authorized": verdict == "AUTHORIZE_Q0",
            "native_integration_authorized": False,
            "forecast_change_authorized": False,
            "full_1g_authorized": False,
            "next_action": (
                "Materialize only the separately frozen finite hit/escape-plus-rank Q0."
                if verdict == "AUTHORIZE_Q0"
                else "Retire the exact co-link composition, 64-entry language, ranking, event universe, and controls without rescue sweeps."
            ),
        },
        "score_credit_bytes": 0,
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "decision": verdict,
                "G0_byte_equivalent": exact / QBIT_DENOMINATOR,
                "minimum_control_margin_byte_equivalent": min(margins.values())
                / QBIT_DENOMINATOR,
                "active_opportunities": first.stats["active_opportunities"],
                "score_credit_bytes": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
