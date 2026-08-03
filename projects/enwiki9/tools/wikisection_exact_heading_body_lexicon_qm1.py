#!/usr/bin/env python3
"""Run the frozen WIKISECTION exact-heading body-lexicon QM1 ceiling.

This is a zero-credit causal candidate-universe test.  All decoder-built
indices are prefix-only, but membership and model costs are deliberately free.
The output is Q256 byte-equivalent displaced from the exact
JANUS-plus-quotient trajectory, not an archive saving.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from build_heading_state_map import classify
from causal_state_screen import WikiState
from janus_paid_residual_mdl_oracle import range_encode
from mobius2_tessera_self_annotation_graph import ROLE_IDS, role_id
from mobius2_tessera_typed_fiber_ceiling import byte_qbits, qbit_tables, read_p1
from sibyl_page_prompt_oracle import archive_payload, page_intervals
from wrt_exact import ParsedStore, WrtEvent, parse_store


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CANDIDATE_ID = "wikisection_exact_heading_body_lexicon_qm1_v1"
LANES = ("Hblind", "Hprior", "Hcoarse", "Hexact")
CONTROLS = LANES[:-1]
SPLITS = ("development", "selection", "opened_confirmation")
TEXT_OPEN = b'<text xml:space="preserve">'
TEXT_CLOSE = b"</text>"
PAGE_OPEN = b"<page>"
PAGE_CLOSE = b"</page>"
QBIT_DENOMINATOR = 2048
REJECT_BYTES = 30_000
AUTHORIZE_BYTES = 60_000
CONTROL_MARGIN_BYTES = 10_000
SPLIT_GATE_BYTES_PER_MILLION = 5_000
FORECAST_BYTES = 109_389_323
FORECAST_DEBT_BYTES = 1_389_323

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
BOUND_SOURCE_FILES = (
    "projects/enwiki9/docs/wikisection_exact_heading_body_lexicon_qm1_plan.md",
    "projects/enwiki9/tools/wikisection_exact_heading_body_lexicon_qm1.py",
    "projects/enwiki9/tools/build_heading_state_map.py",
    "projects/enwiki9/tools/causal_state_screen.py",
    "projects/enwiki9/tools/mobius2_tessera_self_annotation_graph.py",
    "projects/enwiki9/tools/mobius2_tessera_typed_fiber_ceiling.py",
    "projects/enwiki9/tools/sibyl_page_prompt_oracle.py",
    "projects/enwiki9/tools/wrt_exact.py",
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
    expected = EXPECTED[name]
    if (observed["bytes"], observed["sha256"]) != expected:
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
        files[relative] = {"bytes": len(current), "sha256": sha256_bytes(current)}
    return {"git_commit": commit, "tracked_files": files, "score_charge_bytes": 0}


def normalize_heading(body: bytes) -> bytes:
    body = body.replace(b"_", b" ")
    body = body.translate(bytes.maketrans(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ", b"abcdefghijklmnopqrstuvwxyz"))
    return b" ".join(body.split())


def parse_heading(line: bytes) -> tuple[bytes, int] | None:
    """Return the exact normalized key and frozen coarse class for a line."""
    if not line.endswith(b"\n"):
        return None
    text = line[:-1]
    if text.endswith(b"\r"):
        text = text[:-1]
    if not text or text[:1] in (b" ", b"\t"):
        return None
    opening = 0
    while opening < len(text) and text[opening] == ord("="):
        opening += 1
    if not 2 <= opening <= 6:
        return None
    stripped = text.rstrip(b" \t")
    closing = 0
    while closing < len(stripped) and stripped[len(stripped) - closing - 1] == ord("="):
        closing += 1
    if closing != opening or len(stripped) < opening + closing:
        return None
    body = stripped[opening : len(stripped) - closing].strip(b" \t")
    key = normalize_heading(body)
    if not key:
        return None
    coarse = classify(line)
    if coarse is None:
        raise ValueError("accepted exact heading lacks frozen coarse class")
    return key, int(coarse)


def split_for_page(ordinal: int, count: int) -> int:
    if ordinal < count * 3 // 5:
        return 0
    if ordinal < count * 4 // 5:
        return 1
    return 2


def update_counter_digest(digest: Any, counter: Mapping[bytes, int]) -> None:
    entries = tuple((bytes(code), int(count)) for code, count in sorted(counter.items()) if count > 0)
    digest.update(len(entries).to_bytes(4, "little"))
    for code, count in entries:
        digest.update(len(code).to_bytes(2, "little"))
        digest.update(code)
        digest.update(count.to_bytes(8, "little"))


def top_identities(counter: Mapping[bytes, int], count: int) -> frozenset[bytes] | None:
    if count < 0:
        raise ValueError("negative candidate capacity")
    entries = sorted(
        ((bytes(code), int(weight)) for code, weight in counter.items() if weight > 0),
        key=lambda row: (-row[1], row[0]),
    )
    if len(entries) < count:
        return None
    return frozenset(code for code, _ in entries[:count])


@dataclass(frozen=True)
class SectionRecord:
    page: int
    section: int
    key: bytes
    coarse: int
    counter: Counter[bytes]


@dataclass
class ActiveSection:
    ordinal: int
    key: bytes
    coarse: int
    counter: Counter[bytes] = field(default_factory=Counter)
    candidates: dict[str, frozenset[bytes]] = field(default_factory=dict)
    active: bool = False
    capacity: int = 0


@dataclass
class PageStage:
    ordinal: int
    split: int
    sections: list[SectionRecord] = field(default_factory=list)
    current: ActiveSection | None = None
    next_section: int = 0
    in_text: bool = False
    line: bytearray = field(default_factory=bytearray)
    line_events: list[tuple[int, int, int, WrtEvent]] = field(default_factory=list)
    line_event_ids: set[int] = field(default_factory=set)
    line_start_raw: int = -1
    scheduled_events: set[int] = field(default_factory=set)


@dataclass(frozen=True)
class RunResult:
    qbits: dict[str, int]
    split_qbits: dict[str, tuple[int, int, int]]
    stats: dict[str, object]
    parser_sha256: str
    index_sha256: str
    opportunity_sha256: str
    control_sha256: str


class SectionMachine:
    def __init__(self, parsed: ParsedStore, intervals: Sequence[tuple[int, int, int, int]], event_qbits: np.ndarray):
        self.parsed = parsed
        self.intervals = intervals
        self.event_qbits = event_qbits
        self.wiki = WikiState()
        self.page_starts = {row_start // 8: (i, raw_start) for i, (raw_start, _, row_start, _) in enumerate(intervals)}
        self.page_ends = {row_end // 8: (i, raw_end) for i, (_, raw_end, _, row_end) in enumerate(intervals)}
        self.page_count = len(intervals)
        partial_raw_start = parsed.decoded.rfind(PAGE_OPEN)
        raw_cursor = 0
        for event in parsed.events:
            if raw_cursor == partial_raw_start:
                self.page_starts[event.start] = (self.page_count, partial_raw_start)
                break
            raw_cursor += len(event.decoded)
        else:
            raise ValueError("trailing partial-page opener cuts a WRT event")
        self.page: PageStage | None = None
        self.raw_position = 0
        self.exact_index: dict[bytes, Counter[bytes]] = defaultdict(Counter)
        self.coarse_total: dict[int, Counter[bytes]] = defaultdict(Counter)
        self.coarse_exact: dict[tuple[int, bytes], Counter[bytes]] = defaultdict(Counter)
        self.blind_buckets: dict[int, list[SectionRecord]] = defaultdict(list)
        self.previous_page = Counter()
        self.qbits = {lane: 0 for lane in LANES}
        self.split_qbits = {lane: [0, 0, 0] for lane in LANES}
        self.hits = {lane: 0 for lane in LANES}
        self.split_hits = {lane: [0, 0, 0] for lane in LANES}
        self.opportunities = 0
        self.active_sections = 0
        self.deactivated_sections = 0
        self.accepted_headings = 0
        self.committed_sections = 0
        self.committed_pages = 0
        self.heading_token_opportunity_violations = 0
        self.boundary_crossing_tokens_excluded = 0
        self.blind_same_key_exclusions = 0
        self.blind_selected_key_violations = 0
        self.parser_digest = hashlib.sha256()
        self.index_digest = hashlib.sha256()
        self.opportunity_digest = hashlib.sha256()
        self.control_digest = hashlib.sha256()

    def _blind_source(self, key: bytes, capacity: int) -> SectionRecord | None:
        if capacity <= 0:
            return None
        target_bin = capacity.bit_length()
        for width in range(target_bin, max(self.blind_buckets, default=target_bin - 1) + 1):
            for record in self.blind_buckets.get(width, ()):
                if record.key == key:
                    self.blind_same_key_exclusions += 1
                    continue
                if len(record.counter) >= capacity:
                    return record
        return None

    def _freeze_candidates(self, active: ActiveSection) -> None:
        exact_counter = self.exact_index.get(active.key, Counter())
        capacity = len(exact_counter)
        active.capacity = capacity
        if not capacity:
            return
        blind = self._blind_source(active.key, capacity)
        prior = top_identities(self.previous_page, capacity)
        coarse_counter = self.coarse_total.get(active.coarse, Counter()).copy()
        coarse_counter.subtract(self.coarse_exact.get((active.coarse, active.key), Counter()))
        coarse_counter = Counter({code: count for code, count in coarse_counter.items() if count > 0})
        coarse = top_identities(coarse_counter, capacity)
        if blind is None or prior is None or coarse is None:
            self.deactivated_sections += 1
            return
        blind_codes = top_identities(blind.counter, capacity)
        if blind_codes is None:
            raise ValueError("eligible blind section failed injective capacity")
        if blind.key == active.key:
            self.blind_selected_key_violations += 1
            raise ValueError("Hblind selected an equal heading key")
        active.candidates = {
            "Hblind": blind_codes,
            "Hprior": prior,
            "Hcoarse": coarse,
            "Hexact": frozenset(exact_counter),
        }
        if any(len(active.candidates[lane]) != capacity for lane in LANES):
            raise ValueError("matched controls changed candidate capacity")
        active.active = True
        self.active_sections += 1
        self.control_digest.update(active.key)
        self.control_digest.update(active.coarse.to_bytes(2, "little"))
        self.control_digest.update(capacity.to_bytes(4, "little"))
        self.control_digest.update(blind.page.to_bytes(4, "little"))
        self.control_digest.update(blind.section.to_bytes(4, "little"))
        self.control_digest.update(blind.key)
        for lane in LANES:
            for code in sorted(active.candidates[lane]):
                self.control_digest.update(len(code).to_bytes(2, "little"))
                self.control_digest.update(code)

    def _close_section(self) -> None:
        if self.page is None or self.page.current is None:
            return
        current = self.page.current
        record = SectionRecord(
            page=self.page.ordinal, section=current.ordinal, key=current.key,
            coarse=current.coarse, counter=current.counter.copy(),
        )
        self.page.sections.append(record)
        self.page.current = None

    def _open_section(self, key: bytes, coarse: int) -> None:
        if self.page is None:
            raise ValueError("heading completed outside a page")
        self._close_section()
        active = ActiveSection(self.page.next_section, key, coarse)
        self.page.next_section += 1
        self._freeze_candidates(active)
        self.page.current = active
        self.accepted_headings += 1
        self.parser_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.parser_digest.update(active.ordinal.to_bytes(4, "little"))
        self.parser_digest.update(coarse.to_bytes(2, "little"))
        self.parser_digest.update(len(key).to_bytes(2, "little"))
        self.parser_digest.update(key)

    def _append_body_tokens(self, content_end: int) -> None:
        if self.page is None or self.page.current is None:
            return
        for _, start, end, event in self.page.line_events:
            if event.kind != "token":
                continue
            if start >= self.page.line_start_raw and end <= content_end:
                self.page.current.counter[event.encoded] += 1
            elif start < content_end < end:
                self.boundary_crossing_tokens_excluded += 1

    def _finish_line(self, newline_end_raw: int) -> None:
        if self.page is None:
            raise ValueError("line completed outside a page")
        line = bytes(self.page.line)
        parsed_heading = parse_heading(line)
        content_end = newline_end_raw - 1
        if line.endswith(b"\r\n"):
            content_end -= 1
        if parsed_heading is None:
            self._append_body_tokens(content_end)
        else:
            scheduled_tokens = sum(
                1 for index, _, _, event in self.page.line_events
                if index in self.page.scheduled_events and event.kind == "token"
            )
            self.heading_token_opportunity_violations += scheduled_tokens
            if scheduled_tokens:
                raise ValueError("accepted heading contained scheduled token opportunities")
            self._open_section(*parsed_heading)
        self.page.line.clear()
        self.page.line_events.clear()
        self.page.line_event_ids.clear()
        self.page.scheduled_events.clear()
        self.page.line_start_raw = newline_end_raw

    def _finish_text(self, close_start_raw: int) -> None:
        if self.page is None:
            raise ValueError("text closed outside a page")
        if not bytes(self.page.line).endswith(TEXT_CLOSE):
            raise ValueError("text closer missing from pending line")
        self._append_body_tokens(close_start_raw)
        self._close_section()
        self.page.in_text = False
        self.page.line.clear()
        self.page.line_events.clear()
        self.page.line_event_ids.clear()
        self.page.scheduled_events.clear()
        self.page.line_start_raw = -1

    def _commit_page(self, ordinal: int) -> None:
        if self.page is None or self.page.ordinal != ordinal:
            raise ValueError("page close does not match current stage")
        if self.page.in_text:
            raise ValueError("page closed while text field remains open")
        page_counter: Counter[bytes] = Counter()
        for record in self.page.sections:
            self.exact_index[record.key].update(record.counter)
            self.coarse_total[record.coarse].update(record.counter)
            self.coarse_exact[(record.coarse, record.key)].update(record.counter)
            self.blind_buckets[len(record.counter).bit_length()].append(record)
            page_counter.update(record.counter)
            self.index_digest.update(record.page.to_bytes(4, "little"))
            self.index_digest.update(record.section.to_bytes(4, "little"))
            self.index_digest.update(record.coarse.to_bytes(2, "little"))
            self.index_digest.update(len(record.key).to_bytes(2, "little"))
            self.index_digest.update(record.key)
            update_counter_digest(self.index_digest, record.counter)
            self.committed_sections += 1
        self.previous_page = page_counter
        self.committed_pages += 1
        self.page = None

    def _score_pre_event(self, index: int, event: WrtEvent) -> None:
        if self.page is None or self.page.current is None:
            return
        active = self.page.current
        if (
            self.page.split < 0
            or not active.active
            or self.wiki.field_id != 6
            or role_id(self.wiki) != ROLE_IDS["PROSE_WORD"]
        ):
            return
        self.opportunities += 1
        self.page.scheduled_events.add(index)
        self.opportunity_digest.update(self.page.ordinal.to_bytes(4, "little"))
        self.opportunity_digest.update(active.ordinal.to_bytes(4, "little"))
        self.opportunity_digest.update(index.to_bytes(8, "little"))
        self.opportunity_digest.update(active.capacity.to_bytes(4, "little"))
        if event.kind != "token":
            return
        cost = int(self.event_qbits[index])
        for lane in LANES:
            if event.encoded in active.candidates[lane]:
                self.qbits[lane] += cost
                self.split_qbits[lane][self.page.split] += cost
                self.hits[lane] += 1
                self.split_hits[lane][self.page.split] += 1

    def run(self) -> RunResult:
        for index, event in enumerate(self.parsed.events):
            page_start = self.page_starts.get(event.start)
            if page_start is not None:
                ordinal, expected_raw = page_start
                if self.page is not None or self.raw_position != expected_raw:
                    raise ValueError("page-open event alignment changed")
                split = split_for_page(ordinal, self.page_count) if ordinal < self.page_count else -1
                self.page = PageStage(ordinal, split)

            self._score_pre_event(index, event)
            event_raw_start = self.raw_position
            event_added_to_line = False
            for offset, byte in enumerate(event.decoded):
                before = self.wiki.field_id
                absolute = event_raw_start + offset
                if before == 6:
                    if self.page is None:
                        raise ValueError("text byte observed outside a complete page")
                    if not self.page.in_text:
                        raise ValueError("WikiState text visibility differs from line parser")
                    self.page.line.append(byte)
                    if not event_added_to_line:
                        self.page.line_events.append(
                            (index, event_raw_start, event_raw_start + len(event.decoded), event)
                        )
                        self.page.line_event_ids.add(index)
                        event_added_to_line = True
                self.wiki.update(byte)
                after = self.wiki.field_id
                if before != 6 and after == 6:
                    if self.page is None or self.page.in_text:
                        raise ValueError("malformed text opener transition")
                    self.page.in_text = True
                    self.page.line_start_raw = absolute + 1
                elif before == 6 and byte == 10:
                    self._finish_line(absolute + 1)
                if before == 6 and after != 6:
                    self._finish_text(absolute + 1 - len(TEXT_CLOSE))
            self.raw_position += len(event.decoded)

            page_end = self.page_ends.get(event.end)
            if page_end is not None:
                ordinal, expected_raw = page_end
                if self.raw_position != expected_raw:
                    raise ValueError("page-close event alignment changed")
                raw_start = self.intervals[ordinal][0]
                page_bytes = self.parsed.decoded[raw_start:expected_raw]
                if not page_bytes.startswith(PAGE_OPEN) or not page_bytes.endswith(PAGE_CLOSE):
                    raise ValueError("page interval does not bind exact XML tags")
                self._commit_page(ordinal)

        if self.raw_position != len(self.parsed.decoded):
            raise ValueError("section replay did not consume the decoded stream")
        if self.committed_pages != self.page_count:
            raise ValueError("section replay did not commit every complete page")
        return RunResult(
            qbits=dict(self.qbits),
            split_qbits={lane: tuple(values) for lane, values in self.split_qbits.items()},
            stats={
                "accepted_headings": self.accepted_headings,
                "active_sections": self.active_sections,
                "deactivated_sections": self.deactivated_sections,
                "committed_pages": self.committed_pages,
                "committed_sections": self.committed_sections,
                "opportunities": self.opportunities,
                "hits": dict(self.hits),
                "split_hits": {lane: list(values) for lane, values in self.split_hits.items()},
                "heading_token_opportunity_violations": self.heading_token_opportunity_violations,
                "boundary_crossing_tokens_excluded": self.boundary_crossing_tokens_excluded,
                "blind_same_key_exclusions": self.blind_same_key_exclusions,
                "blind_selected_key_violations": self.blind_selected_key_violations,
                "trailing_partial_page_uncommitted": self.page is not None,
            },
            parser_sha256=self.parser_digest.hexdigest(),
            index_sha256=self.index_digest.hexdigest(),
            opportunity_sha256=self.opportunity_digest.hexdigest(),
            control_sha256=self.control_digest.hexdigest(),
        )


def event_costs(parsed: ParsedStore, costs: np.ndarray) -> np.ndarray:
    result = np.zeros(len(parsed.events), dtype=np.int64)
    for index, event in enumerate(parsed.events):
        if event.kind == "token":
            result[index] = int(costs[event.start:event.end].sum())
    return result


def receipt_run(run: RunResult, split_raw: Sequence[int]) -> dict[str, object]:
    lanes: dict[str, object] = {}
    for lane in LANES:
        qbits = run.qbits[lane]
        split_rows = []
        for name, raw_bytes, value in zip(SPLITS, split_raw, run.split_qbits[lane], strict=True):
            split_rows.append({
                "name": name,
                "raw_bytes": raw_bytes,
                "qbits": value,
                "byte_equivalent": value / QBIT_DENOMINATOR,
                "bytes_per_million": value * 1_000_000 / (QBIT_DENOMINATOR * raw_bytes),
            })
        lanes[lane] = {
            "qbits": qbits,
            "byte_equivalent": qbits / QBIT_DENOMINATOR,
            "hits": run.stats["hits"][lane],
            "splits": split_rows,
        }
    return {
        "lanes": lanes,
        "stats": run.stats,
        "digests": {
            "parser_sha256": run.parser_sha256,
            "index_sha256": run.index_sha256,
            "opportunity_sha256": run.opportunity_sha256,
            "control_sha256": run.control_sha256,
        },
    }


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
        raise RuntimeError("nonempty WIKISECTION output directory forbids startup")
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
        raise ValueError("WRT inverse differs from canonical raw input")
    intervals = page_intervals(parsed)
    if len(intervals) != 1325 or raw.count(PAGE_OPEN) != 1326 or raw.count(PAGE_CLOSE) != 1325:
        raise ValueError("complete-page/trailing-tail population changed")
    page_receipt = json.loads(args.page_receipt.read_text())
    population = next(row for row in page_receipt["populations"] if row["label"] == "opening10m")
    if population["page_open_offsets"] != [row[0] for row in intervals] + [raw.rfind(PAGE_OPEN)]:
        raise ValueError("derived page opens differ from bound receipt")
    if population["page_close_end_offsets"] != [row[1] for row in intervals]:
        raise ValueError("derived page closes differ from bound receipt")

    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    p1 = read_p1(args.joint_p1, len(truth))
    parent_payload = args.joint_payload.read_bytes()
    replayed_parent = range_encode(p1, truth)
    if replayed_parent != parent_payload:
        raise ValueError("joint P1 did not reproduce parent payload")

    zero, one = qbit_tables()
    qbit_hashes = (sha256_bytes(zero.astype("<i4", copy=False).tobytes()), sha256_bytes(one.astype("<i4", copy=False).tobytes()))
    if qbit_hashes != EXPECTED_QBIT_HASHES:
        raise ValueError("Q256 table hashes differ from frozen contract")
    byte_cost = byte_qbits(p1, truth, zero, one)
    costs = event_costs(parsed, byte_cost)

    first = SectionMachine(parsed, intervals, costs).run()
    second = SectionMachine(parsed, intervals, costs).run()
    if first != second:
        raise ValueError("repeated parser/index/opportunity/control replay differs")

    split_raw = [0, 0, 0]
    for ordinal, (raw_start, raw_end, _, _) in enumerate(intervals):
        split_raw[split_for_page(ordinal, len(intervals))] += raw_end - raw_start
    result = receipt_run(first, split_raw)
    exact = first.qbits["Hexact"]
    max_control = max(first.qbits[name] for name in CONTROLS)
    full_margin = exact - max_control
    split_scale_pass = all(
        first.split_qbits["Hexact"][i] * 1_000_000
        >= SPLIT_GATE_BYTES_PER_MILLION * QBIT_DENOMINATOR * split_raw[i]
        for i in range(3)
    )
    split_margin_pass = all(
        first.split_qbits["Hexact"][i] > first.split_qbits[control][i]
        for control in CONTROLS for i in range(3)
    )
    upper = exact >= AUTHORIZE_BYTES * QBIT_DENOMINATOR
    attribution = full_margin >= CONTROL_MARGIN_BYTES * QBIT_DENOMINATOR and split_margin_pass
    if exact < REJECT_BYTES * QBIT_DENOMINATOR:
        verdict = "REJECT"
    elif upper and split_scale_pass and attribution:
        verdict = "AUTHORIZE_Q0"
    else:
        verdict = "PARK"

    decision = {
        "schema": "wikisection_exact_heading_body_lexicon_qm1_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_causal_truth_aware_candidate_universe_ceiling",
        "claim_boundary": "Q256 truth-aware membership ceiling only; index, counts, selector, ranks, source, framing, and termination are free. This is not an archive or score result.",
        "inputs": inputs,
        "source_binding": source_binding,
        "scope": {
            "raw_bytes": len(raw), "wrt_bytes": len(parsed.stream),
            "complete_pages": len(intervals), "trailing_partial_page_present": True,
            "split_raw_bytes": dict(zip(SPLITS, split_raw, strict=True)),
        },
        "parent": {
            "payload_bytes": len(parent_payload),
            "payload_sha256": sha256_bytes(parent_payload),
            "replay_identity": True,
        },
        "q256": {
            "denominator_qbits_per_byte": QBIT_DENOMINATOR,
            "zero_table_sha256": qbit_hashes[0], "one_table_sha256": qbit_hashes[1],
        },
        "result": result,
        "economics": {
            "Hexact_qbits": exact,
            "Hexact_byte_equivalent": exact / QBIT_DENOMINATOR,
            "strongest_control": max(CONTROLS, key=lambda name: first.qbits[name]),
            "strongest_control_qbits": max_control,
            "control_margin_qbits": full_margin,
            "control_margin_byte_equivalent": full_margin / QBIT_DENOMINATOR,
            "forecast_score_bytes_unchanged": FORECAST_BYTES,
            "forecast_debt_bytes": FORECAST_DEBT_BYTES,
            "score_credit_bytes": 0,
        },
        "exactness": {
            "input_identities": True, "parent_payload_identity": True,
            "wrt_raw_inverse": True, "page_receipt_binding": True,
            "q256_table_hashes": True, "repeated_parser_index_opportunity_control_digests": True,
            "all_sources_prior_closed_pages": True,
            "accepted_heading_zero_scheduled_token_events": first.stats["heading_token_opportunity_violations"] == 0,
            "closer_and_line_crossing_events_excluded": True,
            "Hblind_source_key_inequality": first.stats["blind_selected_key_violations"] == 0,
        },
        "gates": {
            "conditions": {
                "Hexact_at_least_60000_byte_equivalent": upper,
                "Hexact_each_split_at_least_5000_B_per_M": split_scale_pass,
                "Hexact_control_margin_at_least_10000_byte_equivalent": full_margin >= CONTROL_MARGIN_BYTES * QBIT_DENOMINATOR,
                "Hexact_control_margin_positive_each_split": split_margin_pass,
            },
            "failed_conditions": [
                name for name, passed in {
                    "Hexact_at_least_60000_byte_equivalent": upper,
                    "Hexact_each_split_at_least_5000_B_per_M": split_scale_pass,
                    "Hexact_control_margin_at_least_10000_byte_equivalent": full_margin >= CONTROL_MARGIN_BYTES * QBIT_DENOMINATOR,
                    "Hexact_control_margin_positive_each_split": split_margin_pass,
                }.items() if not passed
            ],
        },
        "decision": {
            "verdict": verdict,
            "paid_q0_authorized": verdict == "AUTHORIZE_Q0",
            "forecast_change_authorized": False,
            "full_1g_authorized": False,
            "next_action": (
                "Materialize only the frozen paid side/residual Q0." if verdict == "AUTHORIZE_Q0"
                else "Park the exact frozen family without Q0 or rescue sweeps." if verdict == "PARK"
                else "Retire the exact heading grammar, normalization, section-body universe, page-close publication, and matched controls without rescue sweeps."
            ),
        },
        "score_credit_bytes": 0,
    }
    (output_dir / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID, "decision": verdict,
        "Hexact_byte_equivalent": exact / QBIT_DENOMINATOR,
        "control_margin_byte_equivalent": full_margin / QBIT_DENOMINATOR,
        "score_credit_bytes": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
