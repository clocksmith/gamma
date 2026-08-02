#!/usr/bin/env python3
"""Run the frozen WIKIBACK incoming-anchor-context QH0 ceiling.

The decoder builds an index only from fully decoded earlier pages.  When the
current page title closes, it freezes the prior incoming-link lexical context
for that title.  At every later decoder-visible PROSE_WORD event boundary the
side stream codes either an exact WRT event from that snapshot or an escape to
the JANUS-plus-quotient residual stream.

This tool is a zero-score-credit trace ceiling.  It does not implement the
native state-preserving Gamma update path and cannot change the forecast.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from typing import Any, Iterable, Mapping, Sequence
import zlib

import numpy as np

from causal_state_screen import WikiState
from janus_paid_residual_mdl_oracle import range_encode
from mobius2_tessera_self_annotation_graph import ROLE_IDS, role_id
from mobius2_tessera_typed_fiber_ceiling import (
    Distribution,
    SideDecoder,
    SideEncoder,
    read_p1,
)
from sibyl_page_prompt_oracle import archive_payload, page_intervals, write_page_map
from wrt_exact import (
    CAPITALIZED,
    END_UPPER,
    ESCAPE,
    TEXT_SEGMENT,
    UPPERCASE,
    ParsedStore,
    WrtDecoderState,
    WrtEvent,
    parse_store,
    read_dictionary_words,
    token_index,
    wrt_byte_transform,
)


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CANDIDATE_ID = "wikiback_incoming_anchor_context_qh0_v1"
VARIANTS = ("Cblind", "Cprior", "Ctarget", "Wfull")
VARIANT_IDS = {name: index + 1 for index, name in enumerate(VARIANTS)}
VARIANT_BY_ID = {value: key for key, value in VARIANT_IDS.items()}
SPLIT_NAMES = ("development", "selection", "opened_confirmation")

PAGE_OPEN = b"<page>"
PAGE_CLOSE = b"</page>"
TITLE_OPEN = b"<title>"
TITLE_CLOSE = b"</title>"
LINK_OPEN = b"[["
LINK_CLOSE = b"]]"
TAIL_BYTES = 64
CONTEXT_EVENTS = 16
SIDE_TOTAL = 1 << 24
SIDE_MASK = SIDE_TOTAL - 1
FRAME_MAGIC = b"WIKIBK1\0"
FRAME_STRUCT = struct.Struct("<8sBBIQQQQ32s")
FRAME_VERSION = 1
GROSS_GATE_BYTES = 30_000
NET_GATE_BYTES_PER_MILLION = 2_100.0
SOURCE_CEILING_BYTES = 196_608
SOURCE_FRAMING_ALLOWANCE_BYTES = 64
FORECAST_BYTES = 109_389_323
FORECAST_DEBT_BYTES = 1_389_323

BOUND_SOURCE_FILES = (
    "projects/enwiki9/docs/wikiback_incoming_anchor_context_qh0_plan.md",
    "projects/enwiki9/tools/wikiback_incoming_anchor_context_qh0.py",
    "projects/enwiki9/tools/causal_state_screen.py",
    "projects/enwiki9/tools/janus_paid_residual_mdl_oracle.py",
    "projects/enwiki9/tools/mobius2_tessera_self_annotation_graph.py",
    "projects/enwiki9/tools/mobius2_tessera_typed_fiber_ceiling.py",
    "projects/enwiki9/tools/sibyl_page_prompt_oracle.py",
    "projects/enwiki9/tools/wrt_exact.py",
)

FROZEN_CONFIG = {
    "schema": "wikiback_incoming_anchor_context_config_v1",
    "candidate_id": CANDIDATE_ID,
    "context_events_each_side": CONTEXT_EVENTS,
    "context_event_kind": "exact WRT token events",
    "full_alphabet": (
        "target tokens plus last 16 tokens before [[ plus first 16 tokens "
        "after the target terminator"
    ),
    "normalization": (
        "strip fragment at first #; ASCII lowercase; underscore-to-space; "
        "ASCII whitespace collapse"
    ),
    "opportunity": (
        "decoder-visible PROSE_WORD boundary after complete title with a "
        "nonempty Wfull prior-page snapshot"
    ),
    "index_commit": "only after completed </page>",
    "snapshot_time": "only after completed </title>",
    "tag_coder": (
        "per-variant, per-page add-half counters initialized hit=escape=0; "
        "Q24 weights are 2*count+1; score tag then update after the event"
    ),
    "rank_coder": "frozen occurrence counts projected exactly into Q24",
    "matched_control": (
        "causal completed-page source with enough distinct identities; nearest "
        "unique-count bit-length and earliest ordinal ties; injective identities "
        "receive Wfull's exact weight multiset"
    ),
    "prior_control": (
        "immediately previous completed page exact lexical reservoir; injective "
        "identities receive Wfull's exact weight multiset"
    ),
    "unmatched_control_policy": (
        "deactivate the page for every variant if Cblind or Cprior cannot supply "
        "the Wfull unique count injectively"
    ),
    "trailing_partial_page": (
        "complete-page limit transmitted in the counted frame; later partial "
        "page is residual-only and never committed"
    ),
    "link_grammar": (
        "one non-nested [[...]] link; target ends at first |, #, or ]]; label "
        "ends at first ]]; nested open delimiters are ordinary link content"
    ),
    "variants": list(VARIANTS),
    "population_splits": (
        "first 60%, next 20%, and final 20% of complete pages; all are opened"
    ),
    "source_allowance": (
        "zlib-9 canonical Git-bound plan/tool/direct-donor bundle plus 64 bytes"
    ),
    "gross_gate_bytes": GROSS_GATE_BYTES,
    "net_gate_bytes_per_million": NET_GATE_BYTES_PER_MILLION,
    "score_credit_bytes": 0,
}
CONFIG_BYTES = json.dumps(
    FROZEN_CONFIG, sort_keys=True, separators=(",", ":")
).encode("utf-8")
CONFIG_SHA256 = hashlib.sha256(CONFIG_BYTES).digest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def bind_source_bundle() -> tuple[bytes, dict[str, object]]:
    """Bind and canonically compress every direct incremental source donor."""
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    bundle = bytearray(b"WIKIBACK-SOURCE-BUNDLE-V1\0")
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
            raise ValueError(f"bound WIKIBACK source differs from HEAD: {relative}")
        name = relative.encode("utf-8")
        bundle.extend(len(name).to_bytes(4, "little"))
        bundle.extend(name)
        bundle.extend(len(current).to_bytes(8, "little"))
        bundle.extend(current)
        files[relative] = {
            "bytes": len(current),
            "sha256": sha256_bytes(current),
        }
    compressed = zlib.compress(bytes(bundle), level=9)
    return compressed, {
        "git_commit": commit,
        "bundle_raw_bytes": len(bundle),
        "bundle_zlib9_bytes": len(compressed),
        "bundle_zlib9_sha256": sha256_bytes(compressed),
        "framing_allowance_bytes": SOURCE_FRAMING_ALLOWANCE_BYTES,
        "counted_allowance_bytes": len(compressed) + SOURCE_FRAMING_ALLOWANCE_BYTES,
        "tracked_files": files,
    }


def normalize_title(value: bytes) -> bytes:
    """Apply the frozen decoder-local title/link-target normalization."""
    without_fragment = value.split(b"#", 1)[0]
    return b" ".join(without_fragment.replace(b"_", b" ").lower().split())


def split_for_page(page_ordinal: int, page_count: int) -> int:
    development_end = page_count * 3 // 5
    selection_end = page_count * 4 // 5
    if page_ordinal < development_end:
        return 0
    if page_ordinal < selection_end:
        return 1
    return 2


def project_weights(symbol_weights: Mapping[int, int]) -> Distribution:
    """Project positive integer weights into a canonical nonzero Q24 CDF."""
    ordered = tuple(sorted(int(symbol) for symbol in symbol_weights))
    if not ordered or len(ordered) > SIDE_TOTAL:
        raise ValueError("invalid WIKIBACK Q24 alphabet")
    weights = [int(symbol_weights[symbol]) for symbol in ordered]
    if any(weight <= 0 for weight in weights):
        raise ValueError("WIKIBACK Q24 weights must be positive")
    total_weight = sum(weights)
    distributable = SIDE_TOTAL - len(ordered)
    frequencies: list[int] = []
    remainders: list[int] = []
    for weight in weights:
        quotient, remainder = divmod(distributable * weight, total_weight)
        frequencies.append(1 + quotient)
        remainders.append(remainder)
    missing = SIDE_TOTAL - sum(frequencies)
    order = sorted(
        range(len(ordered)), key=lambda index: (-remainders[index], ordered[index])
    )
    for index in order[:missing]:
        frequencies[index] += 1
    cdf = [0]
    for frequency in frequencies:
        cdf.append(cdf[-1] + frequency)
    if cdf[-1] != SIDE_TOTAL or any(frequency <= 0 for frequency in frequencies):
        raise ValueError("invalid WIKIBACK projected Q24 distribution")
    return Distribution(ordered, tuple(frequencies), tuple(cdf))


def kt_tag_distribution(hits: int, escapes: int) -> Distribution:
    if hits < 0 or escapes < 0:
        raise ValueError("WIKIBACK add-half counters cannot be negative")
    return project_weights({0: 2 * escapes + 1, 1: 2 * hits + 1})


def event_kind(encoded: bytes) -> str:
    if not encoded:
        raise ValueError("empty WRT event")
    first = wrt_byte_transform(encoded[0])
    if first == ESCAPE:
        if len(encoded) != 2:
            raise ValueError("invalid escaped WRT event")
        return "escaped_literal"
    if first in (UPPERCASE, END_UPPER, CAPITALIZED):
        if len(encoded) != 1:
            raise ValueError("invalid WRT control event")
        return "control"
    if first >= 0x80:
        expected = 1
        if first > 0xCF:
            expected = 2
            if len(encoded) >= 2 and wrt_byte_transform(encoded[1]) > 0xCF:
                expected = 3
        if len(encoded) != expected:
            raise ValueError("invalid WRT token event length")
        return "token"
    if len(encoded) != 1:
        raise ValueError("invalid WRT literal event")
    return "literal"


def decode_event_bytes(
    encoded: bytes, state: WrtDecoderState, dictionary_words: Sequence[bytes]
) -> bytes:
    kind = event_kind(encoded)
    first = wrt_byte_transform(encoded[0])
    if kind == "escaped_literal":
        return state.escaped(wrt_byte_transform(encoded[1]))
    if kind == "control":
        state.control(first)
        return b""
    if kind == "token":
        code = bytes(wrt_byte_transform(value) for value in encoded)
        index = token_index(code)
        if index >= len(dictionary_words):
            raise ValueError("WIKIBACK token exceeds dictionary")
        return state.word(dictionary_words[index])
    return state.literal(first)


def strip_decoded_suffix(
    events: Sequence[WrtEvent], byte_count: int
) -> tuple[WrtEvent, ...] | None:
    retained = list(events)
    remaining = byte_count
    while remaining > 0 and retained:
        event = retained.pop()
        decoded_bytes = len(event.decoded)
        if decoded_bytes == 0:
            continue
        if decoded_bytes > remaining:
            return None
        remaining -= decoded_bytes
    if remaining:
        return None
    return tuple(retained)


def decoded_suffix_is_event_aligned(
    events: Sequence[WrtEvent], byte_count: int
) -> bool:
    """Return whether a decoded suffix ends only on whole WRT events."""
    remaining = byte_count
    for event in reversed(events):
        decoded_bytes = len(event.decoded)
        if decoded_bytes == 0:
            continue
        if decoded_bytes > remaining:
            return False
        remaining -= decoded_bytes
        if remaining == 0:
            return True
    return False


def token_codes(events: Iterable[WrtEvent]) -> tuple[bytes, ...]:
    return tuple(event.encoded for event in events if event.kind == "token")


@dataclass(frozen=True)
class LinkRecord:
    target_key: bytes
    target_codes: tuple[bytes, ...]
    anchor_codes: tuple[bytes, ...]
    open_event: int
    target_end_event: int
    close_event: int


@dataclass(frozen=True)
class PageSignal:
    title_key: bytes | None = None
    page_closed: bool = False


@dataclass
class PageStage:
    ordinal: int
    events: list[WrtEvent] = field(default_factory=list)
    links: list[LinkRecord] = field(default_factory=list)
    tail: bytearray = field(default_factory=bytearray)
    title_mode: bool = False
    title_capture: list[WrtEvent] = field(default_factory=list)
    title_key: bytes = b""
    title_complete: bool = False
    link_phase: str = "none"
    link_capture: list[WrtEvent] = field(default_factory=list)
    link_target_events: tuple[WrtEvent, ...] = ()
    link_open_event: int = -1
    link_target_end_event: int = -1
    discarded_boundaries: int = 0
    wfull_snapshot: "Snapshot | None" = None

    def _reset_link(self) -> None:
        self.link_phase = "none"
        self.link_capture.clear()
        self.link_target_events = ()
        self.link_open_event = -1
        self.link_target_end_event = -1

    def _discard_link(self) -> None:
        self.discarded_boundaries += 1
        self._reset_link()

    def _finish_link(
        self, close_event: int, label_events: Sequence[WrtEvent] = ()
    ) -> None:
        target_raw = b"".join(event.decoded for event in self.link_target_events)
        target_key = normalize_title(target_raw)
        if target_key:
            self.links.append(
                LinkRecord(
                    target_key=target_key,
                    target_codes=token_codes(self.link_target_events),
                    anchor_codes=token_codes(label_events),
                    open_event=self.link_open_event,
                    target_end_event=self.link_target_end_event,
                    close_event=close_event,
                )
            )
        self._reset_link()

    def observe(self, event: WrtEvent) -> PageSignal:
        self.events.append(event)
        if self.title_mode:
            self.title_capture.append(event)
        if self.link_phase != "none":
            self.link_capture.append(event)

        self.tail.extend(event.decoded)
        if len(self.tail) > TAIL_BYTES:
            del self.tail[: len(self.tail) - TAIL_BYTES]
        tail = bytes(self.tail)
        title_signal: bytes | None = None

        if self.title_mode and tail.endswith(TITLE_CLOSE):
            sequence = strip_decoded_suffix(self.title_capture, len(TITLE_CLOSE))
            self.title_mode = False
            self.title_capture.clear()
            if sequence is None:
                self.discarded_boundaries += 1
            else:
                self.title_key = normalize_title(
                    b"".join(captured.decoded for captured in sequence)
                )
                self.title_complete = True
                title_signal = self.title_key

        if self.link_phase == "target":
            if tail.endswith(LINK_CLOSE):
                sequence = strip_decoded_suffix(self.link_capture, len(LINK_CLOSE))
                if sequence is None:
                    self._discard_link()
                else:
                    self.link_target_events = sequence
                    self.link_target_end_event = len(self.events) - 1
                    self._finish_link(len(self.events) - 1)
            elif tail.endswith(b"|"):
                sequence = strip_decoded_suffix(self.link_capture, 1)
                if sequence is None:
                    self._discard_link()
                else:
                    self.link_target_events = sequence
                    self.link_target_end_event = len(self.events) - 1
                    self.link_phase = "label"
                    self.link_capture.clear()
            elif tail.endswith(b"#"):
                sequence = strip_decoded_suffix(self.link_capture, 1)
                if sequence is None:
                    self._discard_link()
                else:
                    self.link_target_events = sequence
                    self.link_target_end_event = len(self.events) - 1
                    self.link_phase = "fragment"
                    self.link_capture.clear()
        elif self.link_phase == "fragment":
            if tail.endswith(b"|"):
                if strip_decoded_suffix(self.link_capture, 1) is None:
                    self._discard_link()
                else:
                    self.link_phase = "label"
                    self.link_capture.clear()
            elif tail.endswith(LINK_CLOSE):
                if strip_decoded_suffix(self.link_capture, len(LINK_CLOSE)) is None:
                    self._discard_link()
                else:
                    self._finish_link(len(self.events) - 1)
        elif self.link_phase == "label" and tail.endswith(LINK_CLOSE):
            label = strip_decoded_suffix(self.link_capture, len(LINK_CLOSE))
            if label is None:
                self._discard_link()
            else:
                self._finish_link(len(self.events) - 1, label)

        if not self.title_mode and tail.endswith(TITLE_OPEN):
            self.title_mode = True
            self.title_capture.clear()
        if self.link_phase == "none" and tail.endswith(LINK_OPEN):
            if not decoded_suffix_is_event_aligned(self.events, len(LINK_OPEN)):
                self.discarded_boundaries += 1
            else:
                self.link_phase = "target"
                self.link_capture.clear()
                self.link_target_events = ()
                self.link_open_event = len(self.events) - 1
                self.link_target_end_event = -1

        return PageSignal(
            title_key=title_signal,
            page_closed=tail.endswith(PAGE_CLOSE),
        )

    def all_token_counter(self) -> Counter[bytes]:
        return Counter(token_codes(self.events))

    def backlink_counters(self) -> list[tuple[bytes, Counter[bytes], Counter[bytes]]]:
        output: list[tuple[bytes, Counter[bytes], Counter[bytes]]] = []
        for link in self.links:
            if link.target_end_event < 0:
                raise ValueError("completed WIKIBACK link lacks a target-end boundary")
            before = token_codes(self.events[: link.open_event])[-CONTEXT_EVENTS:]
            after = token_codes(self.events[link.target_end_event + 1 :])[:CONTEXT_EVENTS]
            full = Counter(before + link.target_codes + after)
            target = Counter(link.target_codes)
            if full:
                output.append((link.target_key, full, target))
        return output


@dataclass(frozen=True)
class Snapshot:
    codes: tuple[bytes, ...]
    counts: tuple[int, ...]
    distribution: Distribution | None
    total: int

    @classmethod
    def empty(cls) -> "Snapshot":
        return cls((), (), None, 0)

    @classmethod
    def from_counter(cls, counter: Mapping[bytes, int]) -> "Snapshot":
        entries = tuple(
            (bytes(code), int(count))
            for code, count in sorted(counter.items())
            if int(count) > 0
        )
        if not entries:
            return cls.empty()
        codes = tuple(code for code, _ in entries)
        counts = tuple(count for _, count in entries)
        distribution = project_weights(
            {rank: count for rank, count in enumerate(counts)}
        )
        return cls(codes, counts, distribution, sum(counts))

    def rank(self, code: bytes) -> int | None:
        index = bisect_left(self.codes, code)
        if index >= len(self.codes) or self.codes[index] != code:
            return None
        return index

    def code(self, rank: int) -> bytes:
        if not 0 <= rank < len(self.codes):
            raise ValueError("WIKIBACK rank outside frozen snapshot")
        return self.codes[rank]

    def counter(self) -> Counter[bytes]:
        return Counter(dict(zip(self.codes, self.counts, strict=True)))


def injective_weight_match(
    source: Mapping[bytes, int], reference: Snapshot
) -> Snapshot | None:
    """Assign the reference weight multiset to distinct causal source codes."""
    if reference.total <= 0:
        return Snapshot.empty()
    source_entries = sorted(
        (
            (bytes(code), int(count))
            for code, count in source.items()
            if int(count) > 0
        ),
        key=lambda item: (-item[1], item[0]),
    )
    if len(source_entries) < len(reference.codes):
        return None
    selected = source_entries[: len(reference.codes)]
    weights = sorted(reference.counts, reverse=True)
    matched = Counter(
        {
            code: weight
            for (code, _), weight in zip(selected, weights, strict=True)
        }
    )
    snapshot = Snapshot.from_counter(matched)
    if (
        len(snapshot.codes) != len(reference.codes)
        or sorted(snapshot.counts) != sorted(reference.counts)
        or snapshot.total != reference.total
    ):
        raise ValueError("injective WIKIBACK control matching changed the weight multiset")
    return snapshot


def update_digest_with_counter(
    digest: "hashlib._Hash", key: bytes, counter: Mapping[bytes, int]
) -> None:
    digest.update(len(key).to_bytes(4, "little"))
    digest.update(key)
    entries = [(bytes(code), int(count)) for code, count in sorted(counter.items()) if count]
    digest.update(len(entries).to_bytes(4, "little"))
    for code, count in entries:
        digest.update(len(code).to_bytes(2, "little"))
        digest.update(code)
        digest.update(count.to_bytes(8, "little"))


@dataclass
class CausalBacklinkMachine:
    page_count: int
    wiki: WikiState = field(default_factory=WikiState)
    global_tail: bytearray = field(default_factory=bytearray)
    page: PageStage | None = None
    full_index: dict[bytes, Counter[bytes]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    target_index: dict[bytes, Counter[bytes]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    completed_snapshots: list[tuple[int, Snapshot]] = field(default_factory=list)
    previous_page_tokens: Counter[bytes] = field(default_factory=Counter)
    snapshots: dict[str, Snapshot] = field(
        default_factory=lambda: {name: Snapshot.empty() for name in VARIANTS}
    )
    committed_pages: int = 0
    completed_links: int = 0
    discarded_boundaries: int = 0
    snapshot_queries: int = 0
    nonempty_queries: int = 0
    exact_bin_matches: int = 0
    nearest_bin_matches: int = 0
    missing_blind_sources: int = 0
    missing_prior_sources: int = 0
    all_variant_deactivations: int = 0
    blind_unique_shortfalls: int = 0
    prior_unique_shortfalls: int = 0
    page_commits_after_close: int = 0
    trailing_partial_page_open: bool = False
    trailing_partial_events: int = 0

    def current_split(self) -> int:
        if self.page is None:
            return -1
        if self.page.ordinal >= self.page_count:
            return -1
        return split_for_page(self.page.ordinal, self.page_count)

    def opportunity(self) -> bool:
        return (
            self.page is not None
            and self.page.ordinal < self.page_count
            and self.page.title_complete
            and self.snapshots["Wfull"].total > 0
            and role_id(self.wiki) == ROLE_IDS["PROSE_WORD"]
        )

    def snapshot(self, variant: str) -> Snapshot:
        return self.snapshots[variant]

    def _blind_snapshot(self, reference: Snapshot) -> Snapshot | None:
        if reference.total <= 0:
            return Snapshot.empty()
        eligible = [
            row
            for row in self.completed_snapshots
            if len(row[1].codes) >= len(reference.codes)
        ]
        if not eligible:
            if reference.total:
                self.missing_blind_sources += 1
                self.blind_unique_shortfalls += 1
            return None
        target_bin = len(reference.codes).bit_length()
        _, source = min(
            eligible,
            key=lambda row: (
                abs(len(row[1].codes).bit_length() - target_bin),
                row[0],
            ),
        )
        if len(source.codes).bit_length() == target_bin:
            self.exact_bin_matches += 1
        else:
            self.nearest_bin_matches += 1
        return injective_weight_match(source.counter(), reference)

    def _freeze_snapshots(self, title_key: bytes) -> None:
        full_counter = self.full_index.get(title_key, Counter())
        target_counter = self.target_index.get(title_key, Counter())
        full = Snapshot.from_counter(full_counter)
        target = Snapshot.from_counter(target_counter)
        blind = self._blind_snapshot(full)
        prior = injective_weight_match(self.previous_page_tokens, full)
        if full.total and prior is None:
            self.missing_prior_sources += 1
            self.prior_unique_shortfalls += 1
        if full.total and (blind is None or prior is None):
            self.all_variant_deactivations += 1
            self.snapshots = {name: Snapshot.empty() for name in VARIANTS}
        else:
            self.snapshots = {
                "Cblind": blind if blind is not None else Snapshot.empty(),
                "Cprior": prior if prior is not None else Snapshot.empty(),
                "Ctarget": target,
                "Wfull": full,
            }
        self.snapshot_queries += 1
        if full.total:
            self.nonempty_queries += 1
        if self.page is None:
            raise ValueError("title snapshot completed outside a page")
        self.page.wfull_snapshot = full

    def _commit_page(self) -> None:
        if self.page is None:
            raise ValueError("cannot commit an absent page")
        stage = self.page
        if stage.ordinal >= self.page_count:
            raise ValueError("WIKIBACK complete-page limit would be exceeded")
        for target_key, full, target in stage.backlink_counters():
            self.full_index[target_key].update(full)
            self.target_index[target_key].update(target)
            self.completed_links += 1
        self.previous_page_tokens = stage.all_token_counter()
        if stage.wfull_snapshot is not None and stage.wfull_snapshot.total:
            self.completed_snapshots.append((stage.ordinal, stage.wfull_snapshot))
        self.discarded_boundaries += stage.discarded_boundaries
        if stage.ordinal != self.committed_pages:
            raise ValueError("nonchronological WIKIBACK page commit")
        self.committed_pages += 1
        self.page_commits_after_close += 1
        self.page = None
        self.snapshots = {name: Snapshot.empty() for name in VARIANTS}

    def observe(self, event: WrtEvent) -> None:
        self.global_tail.extend(event.decoded)
        if len(self.global_tail) > TAIL_BYTES:
            del self.global_tail[: len(self.global_tail) - TAIL_BYTES]

        signal = PageSignal()
        if self.page is None:
            if bytes(self.global_tail).endswith(PAGE_OPEN):
                self.page = PageStage(ordinal=self.committed_pages)
                self.page.events.append(event)
                self.page.tail.extend(self.global_tail)
                if self.committed_pages == self.page_count:
                    self.trailing_partial_page_open = True
                elif self.committed_pages > self.page_count:
                    raise ValueError("decoded pages exceed the transmitted complete-page limit")
        else:
            signal = self.page.observe(event)
            if self.page.ordinal >= self.page_count:
                self.trailing_partial_events += 1

        for byte in event.decoded:
            self.wiki.update(byte)

        if signal.title_key is not None:
            self._freeze_snapshots(signal.title_key)
        if signal.page_closed:
            if self.page is not None and self.page.ordinal >= self.page_count:
                raise ValueError("transmitted complete-page limit hides a completed page")
            self._commit_page()

    def validate_complete(self) -> None:
        if self.committed_pages != self.page_count:
            raise ValueError(
                f"WIKIBACK page count mismatch: {self.committed_pages} != {self.page_count}"
            )
        if self.page is not None and self.page.ordinal != self.page_count:
            raise ValueError("WIKIBACK replay ended in an unexpected page state")
        if (self.page is not None) != self.trailing_partial_page_open:
            raise ValueError("WIKIBACK trailing-partial-page state is inconsistent")

    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.committed_pages.to_bytes(8, "little"))
        digest.update(self.completed_links.to_bytes(8, "little"))
        digest.update(int(self.trailing_partial_page_open).to_bytes(1, "little"))
        digest.update(self.trailing_partial_events.to_bytes(8, "little"))
        for key in sorted(self.full_index):
            update_digest_with_counter(digest, b"F" + key, self.full_index[key])
        for key in sorted(self.target_index):
            update_digest_with_counter(digest, b"T" + key, self.target_index[key])
        update_digest_with_counter(digest, b"P", self.previous_page_tokens)
        for ordinal, snapshot in self.completed_snapshots:
            digest.update(ordinal.to_bytes(8, "little"))
            update_digest_with_counter(digest, b"S", snapshot.counter())
        return digest.hexdigest()

    def receipt(self) -> dict[str, int | str]:
        return {
            "committed_pages": self.committed_pages,
            "page_commits_after_close": self.page_commits_after_close,
            "completed_links": self.completed_links,
            "discarded_non_event_aligned_boundaries": self.discarded_boundaries,
            "full_index_keys": len(self.full_index),
            "target_index_keys": len(self.target_index),
            "completed_page_snapshot_pool": len(self.completed_snapshots),
            "snapshot_queries": self.snapshot_queries,
            "nonempty_snapshot_queries": self.nonempty_queries,
            "exact_support_bin_matches": self.exact_bin_matches,
            "nearest_support_bin_matches": self.nearest_bin_matches,
            "missing_blind_sources": self.missing_blind_sources,
            "missing_prior_sources": self.missing_prior_sources,
            "blind_unique_shortfalls": self.blind_unique_shortfalls,
            "prior_unique_shortfalls": self.prior_unique_shortfalls,
            "all_variant_deactivations": self.all_variant_deactivations,
            "trailing_partial_page_open": int(self.trailing_partial_page_open),
            "trailing_partial_events": self.trailing_partial_events,
            "state_sha256": self.digest(),
        }


@dataclass
class VariantEncoderState:
    name: str
    wrt_bytes: int
    main: SideEncoder = field(default_factory=SideEncoder)
    split_encoders: tuple[SideEncoder, SideEncoder, SideEncoder] = field(
        default_factory=lambda: (SideEncoder(), SideEncoder(), SideEncoder())
    )
    skip_bytes: np.ndarray = field(init=False)
    page_ordinal: int = -1
    hits: int = 0
    escapes: int = 0
    opportunities: int = 0
    rank_symbols: int = 0
    split_hits: list[int] = field(default_factory=lambda: [0, 0, 0])
    split_escapes: list[int] = field(default_factory=lambda: [0, 0, 0])
    split_opportunities: list[int] = field(default_factory=lambda: [0, 0, 0])

    def __post_init__(self) -> None:
        self.skip_bytes = np.zeros(self.wrt_bytes, dtype=np.bool_)

    def reset_page_if_needed(self, page_ordinal: int) -> None:
        if self.page_ordinal != page_ordinal:
            self.page_ordinal = page_ordinal
            self.hits = 0
            self.escapes = 0

    def encode_opportunity(
        self, event: WrtEvent, snapshot: Snapshot, split: int
    ) -> bool:
        if not 0 <= split < len(SPLIT_NAMES):
            raise ValueError("WIKIBACK opportunity lies outside a complete-page split")
        rank = snapshot.rank(event.encoded) if event.kind == "token" else None
        hit = rank is not None
        tag_dist = kt_tag_distribution(self.hits, self.escapes)
        tag = int(hit)
        self.main.encode(tag_dist, tag)
        self.split_encoders[split].encode(tag_dist, tag)
        self.opportunities += 1
        self.split_opportunities[split] += 1
        if hit:
            if snapshot.distribution is None or rank is None:
                raise ValueError("WIKIBACK hit has no frozen rank distribution")
            self.main.encode(snapshot.distribution, rank)
            self.split_encoders[split].encode(snapshot.distribution, rank)
            self.skip_bytes[event.start : event.end] = True
            self.rank_symbols += 1
        return hit

    def update_after_event(self, hit: bool, split: int) -> None:
        """Update KT weights only after the current event has completed."""
        if hit:
            self.hits += 1
            self.split_hits[split] += 1
        else:
            self.escapes += 1
            self.split_escapes[split] += 1

    def finish(self) -> tuple[bytes, tuple[bytes, bytes, bytes], dict[str, Any]]:
        side = self.main.finish()
        split_sides = tuple(encoder.finish() for encoder in self.split_encoders)
        return side, split_sides, {
            "opportunities": self.opportunities,
            "hit_events": sum(self.split_hits),
            "escapes": sum(self.split_escapes),
            "skipped_wrt_bytes": int(np.count_nonzero(self.skip_bytes)),
            "rank_symbols": self.rank_symbols,
            "side_symbols": self.main.symbols,
            "split_opportunities": dict(zip(SPLIT_NAMES, self.split_opportunities, strict=True)),
            "split_hits": dict(zip(SPLIT_NAMES, self.split_hits, strict=True)),
            "split_escapes": dict(zip(SPLIT_NAMES, self.split_escapes, strict=True)),
        }


@dataclass
class BuildResult:
    sides: dict[str, bytes]
    split_sides: dict[str, tuple[bytes, bytes, bytes]]
    skip_bytes: dict[str, np.ndarray]
    stats: dict[str, dict[str, Any]]
    machine_receipt: dict[str, int | str]
    opportunity_sha256: str
    opportunity_count: int


def build_side_streams(parsed: ParsedStore, page_count: int) -> BuildResult:
    machine = CausalBacklinkMachine(page_count=page_count)
    variants = {
        name: VariantEncoderState(name=name, wrt_bytes=len(parsed.stream))
        for name in VARIANTS
    }
    opportunity_digest = hashlib.sha256()
    opportunity_count = 0
    for event in parsed.events:
        outcomes: dict[str, bool] = {}
        active_split = -1
        if machine.opportunity():
            if machine.page is None:
                raise ValueError("active WIKIBACK opportunity has no current page")
            split = machine.current_split()
            page_ordinal = machine.page.ordinal
            opportunity_digest.update(page_ordinal.to_bytes(8, "little"))
            opportunity_digest.update(event.start.to_bytes(8, "little"))
            opportunity_digest.update(role_id(machine.wiki).to_bytes(2, "little"))
            opportunity_count += 1
            active_split = split
            for name, state in variants.items():
                state.reset_page_if_needed(page_ordinal)
                outcomes[name] = state.encode_opportunity(
                    event, machine.snapshot(name), split
                )
        machine.observe(event)
        if outcomes:
            for name, hit in outcomes.items():
                variants[name].update_after_event(hit, active_split)
    machine.validate_complete()

    sides: dict[str, bytes] = {}
    split_sides: dict[str, tuple[bytes, bytes, bytes]] = {}
    skips: dict[str, np.ndarray] = {}
    stats: dict[str, dict[str, Any]] = {}
    for name, state in variants.items():
        side, split_side, receipt = state.finish()
        if receipt["opportunities"] != opportunity_count:
            raise ValueError("WIKIBACK controls received different opportunity counts")
        sides[name] = side
        split_sides[name] = split_side
        skips[name] = state.skip_bytes
        stats[name] = receipt
    return BuildResult(
        sides=sides,
        split_sides=split_sides,
        skip_bytes=skips,
        stats=stats,
        machine_receipt=machine.receipt(),
        opportunity_sha256=opportunity_digest.hexdigest(),
        opportunity_count=opportunity_count,
    )


class BinaryRangeEncoder:
    """Streaming form of the receipt-bound 16-bit P1 range encoder."""

    def __init__(self) -> None:
        self.low = 0
        self.high = 0xFFFFFFFF
        self.output = bytearray()
        self.bits = 0

    def encode(self, p1: int, bit: int) -> None:
        if not 1 <= p1 <= 65535 or bit not in (0, 1):
            raise ValueError("illegal WIKIBACK residual probability or bit")
        delta = self.high - self.low
        midpoint = self.low + (delta >> 16) * p1 + (
            ((delta & 0xFFFF) * p1) >> 16
        )
        if bit:
            self.high = midpoint
        else:
            self.low = midpoint + 1
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.output.append((self.high >> 24) & 0xFF)
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) & 0xFFFFFFFF) + 255
        self.bits += 1

    def finish(self) -> bytes:
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.output.append((self.high >> 24) & 0xFF)
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) & 0xFFFFFFFF) + 255
        self.output.append((self.high >> 24) & 0xFF)
        return bytes(self.output)


class BinaryRangeDecoder:
    def __init__(self, payload: bytes) -> None:
        if len(payload) < 4:
            raise ValueError("WIKIBACK residual payload is too short")
        self.payload = payload
        self.low = 0
        self.high = 0xFFFFFFFF
        self.code = int.from_bytes(payload[:4], "big")
        self.cursor = 4
        self.bits = 0

    def decode(self, p1: int) -> int:
        if not 1 <= p1 <= 65535:
            raise ValueError("illegal WIKIBACK residual probability")
        delta = self.high - self.low
        midpoint = self.low + (delta >> 16) * p1 + (
            ((delta & 0xFFFF) * p1) >> 16
        )
        if self.code <= midpoint:
            bit = 1
            self.high = midpoint
        else:
            bit = 0
            self.low = midpoint + 1
        while ((self.low ^ self.high) & 0xFF000000) == 0:
            self.low = (self.low << 8) & 0xFFFFFFFF
            self.high = ((self.high << 8) & 0xFFFFFFFF) + 255
            value = self.payload[self.cursor] if self.cursor < len(self.payload) else 0
            self.cursor += 1
            self.code = ((self.code << 8) & 0xFFFFFFFF) + value
        self.bits += 1
        return bit


def frame_archive(
    variant: str,
    complete_page_limit: int,
    raw_bytes: int,
    wrt_bytes: int,
    side: bytes,
    residual: bytes,
) -> bytes:
    return FRAME_STRUCT.pack(
        FRAME_MAGIC,
        FRAME_VERSION,
        VARIANT_IDS[variant],
        complete_page_limit,
        raw_bytes,
        wrt_bytes,
        len(side),
        len(residual),
        CONFIG_SHA256,
    ) + side + residual


@dataclass
class DecodeResult:
    stream: bytes
    raw: bytes
    stats: dict[str, Any]


def decode_archive(
    archive: bytes,
    variant: str,
    p1: Sequence[int],
    dictionary_words: Sequence[bytes],
) -> DecodeResult:
    if len(archive) < FRAME_STRUCT.size:
        raise ValueError("WIKIBACK archive is truncated")
    (
        magic,
        version,
        variant_id,
        complete_page_limit,
        raw_bytes,
        wrt_bytes,
        side_bytes,
        residual_bytes,
        config_sha,
    ) = FRAME_STRUCT.unpack_from(archive)
    if (
        magic != FRAME_MAGIC
        or version != FRAME_VERSION
        or VARIANT_BY_ID.get(variant_id) != variant
        or complete_page_limit <= 0
        or config_sha != CONFIG_SHA256
    ):
        raise ValueError("WIKIBACK archive frame identity failed")
    if len(archive) != FRAME_STRUCT.size + side_bytes + residual_bytes:
        raise ValueError("WIKIBACK archive lengths do not sum to archive size")
    side_payload = archive[FRAME_STRUCT.size : FRAME_STRUCT.size + side_bytes]
    residual_payload = archive[-residual_bytes:]
    side_decoder = SideDecoder(side_payload)
    side_reencoder = SideEncoder()
    residual_decoder = BinaryRangeDecoder(residual_payload)
    residual_reencoder = BinaryRangeEncoder()
    machine = CausalBacklinkMachine(page_count=complete_page_limit)
    wrt_state = WrtDecoderState()
    stream = bytearray()
    raw = bytearray()
    row = 0
    page_ordinal = -1
    hits = 0
    escapes = 0
    opportunities = 0
    page_hits = 0
    page_escapes = 0
    opportunity_digest = hashlib.sha256()

    def residual_bit() -> int:
        nonlocal row
        if row >= len(p1):
            raise ValueError("WIKIBACK residual exceeds parent P1 rows")
        probability = int(p1[row])
        bit = residual_decoder.decode(probability)
        residual_reencoder.encode(probability, bit)
        row += 1
        return bit

    def residual_byte() -> int:
        value = 0
        for _ in range(8):
            value = (value << 1) | residual_bit()
        return value

    def residual_event() -> bytes:
        encoded = bytearray((residual_byte(),))
        first = wrt_byte_transform(encoded[0])
        if first == ESCAPE:
            encoded.append(residual_byte())
        elif first > 0xCF:
            encoded.append(residual_byte())
            if wrt_byte_transform(encoded[1]) > 0xCF:
                encoded.append(residual_byte())
        return bytes(encoded)

    for _ in range(6):
        stream.append(residual_byte())
    if stream[0] != TEXT_SEGMENT or stream[5] != TEXT_SEGMENT:
        raise ValueError("WIKIBACK reconstructed WRT header is invalid")
    declared_raw = int.from_bytes(stream[1:5], "big")
    if declared_raw != raw_bytes:
        raise ValueError("WIKIBACK frame/raw header length mismatch")

    while len(stream) < wrt_bytes:
        tag_outcome: int | None = None
        if machine.opportunity():
            if machine.page is None:
                raise ValueError("decoded WIKIBACK opportunity has no page")
            if page_ordinal != machine.page.ordinal:
                page_ordinal = machine.page.ordinal
                page_hits = 0
                page_escapes = 0
            opportunity_digest.update(page_ordinal.to_bytes(8, "little"))
            opportunity_digest.update(len(stream).to_bytes(8, "little"))
            opportunity_digest.update(role_id(machine.wiki).to_bytes(2, "little"))
            snapshot = machine.snapshot(variant)
            tag_dist = kt_tag_distribution(page_hits, page_escapes)
            tag = side_decoder.decode(tag_dist)
            side_reencoder.encode(tag_dist, tag)
            opportunities += 1
            if tag:
                if snapshot.distribution is None:
                    raise ValueError("WIKIBACK side hit has an empty snapshot")
                rank = side_decoder.decode(snapshot.distribution)
                side_reencoder.encode(snapshot.distribution, rank)
                encoded = snapshot.code(rank)
                skipped_rows = 8 * len(encoded)
                if row + skipped_rows > len(p1):
                    raise ValueError("WIKIBACK side hit exceeds parent P1 rows")
                row += skipped_rows
                hits += 1
            else:
                encoded = residual_event()
                escapes += 1
            tag_outcome = tag
        else:
            encoded = residual_event()

        start = len(stream)
        stream.extend(encoded)
        if len(stream) > wrt_bytes:
            raise ValueError("WIKIBACK event exceeds declared WRT length")
        decoded = decode_event_bytes(encoded, wrt_state, dictionary_words)
        raw.extend(decoded)
        machine.observe(
            WrtEvent(
                start=start,
                end=len(stream),
                encoded=encoded,
                decoded=decoded,
                kind=event_kind(encoded),
            )
        )
        if tag_outcome is not None:
            if tag_outcome:
                page_hits += 1
            else:
                page_escapes += 1

    machine.validate_complete()
    if row != len(p1):
        raise ValueError("WIKIBACK decoder did not account for every parent P1 row")
    if len(raw) != raw_bytes:
        raise ValueError("WIKIBACK reconstructed raw length differs from frame")
    side_reencoded = side_reencoder.finish()
    residual_reencoded = residual_reencoder.finish()
    if side_reencoded != side_payload:
        raise ValueError("WIKIBACK side stream is not canonically consumed")
    if residual_reencoded != residual_payload:
        raise ValueError("WIKIBACK residual stream is not canonically consumed")
    return DecodeResult(
        stream=bytes(stream),
        raw=bytes(raw),
        stats={
            "variant": variant,
            "opportunities": opportunities,
            "hits": hits,
            "escapes": escapes,
            "side_symbols": side_decoder.symbols,
            "residual_bits": residual_decoder.bits,
            "accounted_parent_rows": row,
            "opportunity_sha256": opportunity_digest.hexdigest(),
            "machine": machine.receipt(),
            "side_reencode_sha256": sha256_bytes(side_reencoded),
            "residual_reencode_sha256": sha256_bytes(residual_reencoded),
        },
    )


def byte_mask_to_rows(mask: np.ndarray) -> np.ndarray:
    return np.repeat(mask, 8)


def split_byte_masks(
    intervals: Sequence[tuple[int, int, int, int]], wrt_bytes: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    masks = tuple(np.zeros(wrt_bytes, dtype=np.bool_) for _ in SPLIT_NAMES)
    page_count = len(intervals)
    for ordinal, (_, _, row_start, row_end) in enumerate(intervals):
        masks[split_for_page(ordinal, page_count)][row_start // 8 : row_end // 8] = True
    return masks


def build_residual(
    p1: np.ndarray, truth: np.ndarray, skip_bytes: np.ndarray
) -> tuple[bytes, int]:
    keep_rows = byte_mask_to_rows(~skip_bytes)
    residual_p1 = np.asarray(p1[keep_rows], dtype=np.uint16)
    residual_truth = truth[keep_rows]
    if len(residual_p1) != len(residual_truth):
        raise ValueError("WIKIBACK residual probability/truth lengths differ")
    payload = range_encode(residual_p1, residual_truth)
    return payload, len(residual_truth)


def verify_bound_artifact(
    name: str, observed: Mapping[str, object], expected: Mapping[str, object]
) -> None:
    if (observed["bytes"], observed["sha256"]) != (
        expected["bytes"],
        expected["sha256"],
    ):
        raise ValueError(f"{name} differs from its receipt binding")


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
        default=ROOT
        / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
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
        "--backend",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/cmix.bin"
        ),
    )
    parser.add_argument(
        "--trace-recovery-decision",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/decision.json",
    )
    parser.add_argument(
        "--joint-decision",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_10m_v1/joint/decision.json",
    )
    parser.add_argument(
        "--inverse-receipt",
        type=Path,
        default=ROOT / "results/endpoint428_wrt_store_inverse_10m_v1/decision.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        existing = sorted(
            path.name
            for path in output_dir.iterdir()
            if not (path.name.startswith("quarantine_") and path.is_dir())
        )
        if existing:
            raise RuntimeError(
                "non-quarantined prior WIKIBACK artifacts forbid startup: "
                + ", ".join(existing)
            )
    else:
        output_dir.mkdir(parents=True)
    decision_path = output_dir / "decision.json"
    compressed_source, source_binding = bind_source_bundle()

    trace_decision = json.loads(args.trace_recovery_decision.read_text())
    joint_decision = json.loads(args.joint_decision.read_text())
    inverse_receipt = json.loads(args.inverse_receipt.read_text())
    if trace_decision.get("decision", {}).get("verdict") != "exact_joint_p1_trace_recovered":
        raise ValueError("joint P1 trace recovery is not certified")
    if not joint_decision.get("exactness", {}).get("candidate_a_decode"):
        raise ValueError("joint candidate receipt lacks exact arithmetic decode")
    if inverse_receipt.get("verdict") != "PASS" or not inverse_receipt.get(
        "proof", {}
    ).get("exact_raw_inverse"):
        raise ValueError("official inverse receipt is not valid")

    inputs = {
        "joint_p1": artifact(args.joint_p1),
        "joint_payload": artifact(args.joint_payload),
        "wrt_store": artifact(args.wrt_store),
        "raw_input": artifact(args.raw_input),
        "dictionary": artifact(args.dictionary),
        "backend": artifact(args.backend),
        "trace_recovery_decision": artifact(args.trace_recovery_decision),
        "joint_decision": artifact(args.joint_decision),
        "inverse_receipt": artifact(args.inverse_receipt),
    }
    verify_bound_artifact("joint P1", inputs["joint_p1"], trace_decision["artifact"]["joint_p1"])
    verify_bound_artifact(
        "joint payload",
        inputs["joint_payload"],
        joint_decision["payloads"]["JQ_context_quotient"],
    )
    for name in ("wrt_store", "raw_input", "dictionary", "backend"):
        verify_bound_artifact(name, inputs[name], inverse_receipt["artifacts"][name])

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("receipt-bound WRT inverse differs from canonical raw input")
    intervals = page_intervals(parsed)
    if not intervals:
        raise ValueError("WIKIBACK population has no complete pages")
    page_open_markers = raw.count(PAGE_OPEN)
    page_close_markers = raw.count(PAGE_CLOSE)
    if page_close_markers != len(intervals) or page_open_markers != len(intervals) + 1:
        raise ValueError("canonical WIKIBACK trailing-partial-page contract changed")
    page_map_path = output_dir / "page_map.bin"
    write_page_map(page_map_path, intervals)

    truth = np.unpackbits(np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big")
    joint_p1 = read_p1(args.joint_p1, len(truth))
    joint_payload = args.joint_payload.read_bytes()
    replay_parent = range_encode(joint_p1, truth)
    if replay_parent != joint_payload:
        raise ValueError("joint parent P1 does not replay its exact payload")

    first = build_side_streams(parsed, len(intervals))
    second = build_side_streams(parsed, len(intervals))
    if (
        first.sides != second.sides
        or first.split_sides != second.split_sides
        or first.stats != second.stats
        or first.machine_receipt != second.machine_receipt
        or first.opportunity_sha256 != second.opportunity_sha256
    ):
        raise ValueError("repeated WIKIBACK model/side replay differs")
    for name in VARIANTS:
        if not np.array_equal(first.skip_bytes[name], second.skip_bytes[name]):
            raise ValueError(f"repeated {name} skip schedule differs")

    residuals: dict[str, bytes] = {}
    residual_rows: dict[str, int] = {}
    archives: dict[str, bytes] = {}
    second_archives: dict[str, bytes] = {}
    for name in VARIANTS:
        residual, rows = build_residual(joint_p1, truth, first.skip_bytes[name])
        second_residual, second_rows = build_residual(
            joint_p1, truth, second.skip_bytes[name]
        )
        if residual != second_residual or rows != second_rows:
            raise ValueError(f"repeated {name} residual stream differs")
        residuals[name] = residual
        residual_rows[name] = rows
        archives[name] = frame_archive(
            name,
            len(intervals),
            len(raw),
            len(parsed.stream),
            first.sides[name],
            residual,
        )
        second_archives[name] = frame_archive(
            name,
            len(intervals),
            len(raw),
            len(parsed.stream),
            second.sides[name],
            second_residual,
        )
        if archives[name] != second_archives[name]:
            raise ValueError(f"repeated {name} archive differs")
        (output_dir / f"{name.lower()}.side").write_bytes(first.sides[name])
        (output_dir / f"{name.lower()}.residual").write_bytes(residual)
        (output_dir / f"{name.lower()}.archive").write_bytes(archives[name])

    dictionary_words = read_dictionary_words(args.dictionary)
    decodes: dict[str, DecodeResult] = {}
    for name in VARIANTS:
        decoded = decode_archive(
            archives[name], name, joint_p1, dictionary_words
        )
        if decoded.stream != parsed.stream or decoded.raw != raw:
            raise ValueError(f"{name} full WRT/raw reconstruction failed")
        if decoded.stats["opportunity_sha256"] != first.opportunity_sha256:
            raise ValueError(f"{name} decoder opportunities differ from encoder")
        if decoded.stats["machine"] != first.machine_receipt:
            raise ValueError(f"{name} decoder-built causal index differs")
        decodes[name] = decoded

    reconstructed_store = (
        parsed.stored[: parsed.storage_header_bytes] + decodes["Wfull"].stream
    )
    if reconstructed_store != parsed.stored:
        raise ValueError("WIKIBACK reconstructed full WRT store differs")
    reconstructed_store_path = output_dir / "wfull.wrt_store.bin"
    restored_raw_path = output_dir / "wfull.restored.raw"
    reconstructed_store_path.write_bytes(reconstructed_store)
    with (output_dir / "wfull_inverse.stdout.log").open("wb") as stdout, (
        output_dir / "wfull_inverse.stderr.log"
    ).open("wb") as stderr:
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
    official_inverse_ok = (
        inverse.returncode == 0
        and restored_raw_path.is_file()
        and restored_raw_path.read_bytes() == raw
    )
    if not official_inverse_ok:
        raise ValueError("official WIKIBACK WRT inverse failed")

    source_allowance = int(source_binding["counted_allowance_bytes"])
    if source_allowance > SOURCE_CEILING_BYTES:
        raise ValueError("WIKIBACK compressed source exceeds proposal ceiling")
    (output_dir / "source_bundle.zlib").write_bytes(compressed_source)

    split_masks = split_byte_masks(intervals, len(parsed.stream))
    split_receipts: dict[str, Any] = {}
    for split, split_name in enumerate(SPLIT_NAMES):
        scope_bytes = split_masks[split]
        scope_rows = byte_mask_to_rows(scope_bytes)
        parent_split = range_encode(
            np.asarray(joint_p1[scope_rows], dtype=np.uint16), truth[scope_rows]
        )
        raw_split = sum(
            raw_end - raw_start
            for ordinal, (raw_start, raw_end, _, _) in enumerate(intervals)
            if split_for_page(ordinal, len(intervals)) == split
        )
        variant_rows: dict[str, Any] = {}
        for name in VARIANTS:
            keep = scope_bytes & ~first.skip_bytes[name]
            keep_rows = byte_mask_to_rows(keep)
            residual = range_encode(
                np.asarray(joint_p1[keep_rows], dtype=np.uint16), truth[keep_rows]
            )
            side = first.split_sides[name][split]
            candidate = frame_archive(
                name,
                len(intervals),
                raw_split,
                int(np.count_nonzero(scope_bytes)),
                side,
                residual,
            )
            gain = len(parent_split) - len(candidate)
            variant_rows[name] = {
                "total_bytes": len(candidate),
                "side_bytes": len(side),
                "residual_bytes": len(residual),
                "gain_bytes": gain,
                "gain_bytes_per_million_raw": gain * 1_000_000.0 / raw_split,
                "opportunities": first.stats[name]["split_opportunities"][split_name],
                "hits": first.stats[name]["split_hits"][split_name],
                "escapes": first.stats[name]["split_escapes"][split_name],
                "archive_sha256": sha256_bytes(candidate),
            }
        split_receipts[split_name] = {
            "pages": sum(
                split_for_page(ordinal, len(intervals)) == split
                for ordinal in range(len(intervals))
            ),
            "raw_bytes": raw_split,
            "wrt_bytes": int(np.count_nonzero(scope_bytes)),
            "parent_payload_bytes": len(parent_split),
            "variants": variant_rows,
            "state_policy": (
                "side distributions and backlink state carried causally through the full "
                "chronological replay; only diagnostic coders are independently terminated"
            ),
        }

    controls: dict[str, Any] = {
        "G0_joint_parent": {
            "total_bytes": len(joint_payload),
            "sha256": sha256_bytes(joint_payload),
        }
    }
    for name in VARIANTS:
        archive_bytes = len(archives[name])
        gross_gain = len(joint_payload) - archive_bytes
        counted_total = archive_bytes + source_allowance
        controls[name] = {
            "archive_bytes": archive_bytes,
            "counted_total_bytes": counted_total,
            "frame_bytes": FRAME_STRUCT.size,
            "side_bytes": len(first.sides[name]),
            "residual_bytes": len(residuals[name]),
            "residual_rows": residual_rows[name],
            "gross_archive_gain_bytes": gross_gain,
            "counted_10m_gain_after_source_bytes": len(joint_payload) - counted_total,
            "archive_sha256": sha256_bytes(archives[name]),
            "side_sha256": sha256_bytes(first.sides[name]),
            "residual_sha256": sha256_bytes(residuals[name]),
            **first.stats[name],
        }

    gross_gain = controls["Wfull"]["gross_archive_gain_bytes"]
    counted_gain = controls["Wfull"]["counted_10m_gain_after_source_bytes"]
    gross_bpm = gross_gain * 1_000_000.0 / len(raw)
    projected_net_bpm = gross_bpm - source_allowance / 1000.0
    split_positive = all(
        split_receipts[name]["variants"]["Wfull"]["gain_bytes"] > 0
        for name in SPLIT_NAMES
    )
    control_ordering = all(
        controls["Wfull"]["counted_total_bytes"]
        < controls[name]["counted_total_bytes"]
        for name in ("Cblind", "Cprior", "Ctarget")
    )
    exactness = {
        "joint_parent_payload_identity": replay_parent == joint_payload,
        "repeated_model_index_identity": first.machine_receipt == second.machine_receipt,
        "repeated_opportunity_identity": first.opportunity_sha256 == second.opportunity_sha256,
        "repeated_side_identity": first.sides == second.sides,
        "repeated_residual_identity": True,
        "repeated_archive_identity": archives == second_archives,
        "all_side_streams_canonically_decoded": all(
            decodes[name].stats["side_reencode_sha256"]
            == sha256_bytes(first.sides[name])
            for name in VARIANTS
        ),
        "all_residual_streams_canonically_decoded": all(
            decodes[name].stats["residual_reencode_sha256"]
            == sha256_bytes(residuals[name])
            for name in VARIANTS
        ),
        "complete_wrt_reconstruction": all(
            decodes[name].stream == parsed.stream for name in VARIANTS
        ),
        "complete_raw_reconstruction": all(decodes[name].raw == raw for name in VARIANTS),
        "official_raw_inverse": official_inverse_ok,
        "all_probabilities_legal_nonzero": True,
        "all_q24_cdfs_legal_nonzero": True,
        "identical_pretruth_control_opportunities": all(
            decodes[name].stats["opportunity_sha256"] == first.opportunity_sha256
            for name in VARIANTS
        ),
    }
    causality = {
        "opportunities_evaluated_before_current_event": True,
        "title_snapshot_only_after_completed_title_close": True,
        "backlink_records_committed_only_after_completed_page_close": True,
        "right_anchor_context_hidden_until_page_commit": True,
        "current_page_cannot_seed_its_snapshot": True,
        "no_future_or_full_corpus_title_map": True,
        "decoder_receives_no_page_map_or_skip_mask": True,
        "controls_use_only_completed_prior_pages": True,
        "trailing_partial_page_residual_only": all(
            decodes[name].stats["machine"]["trailing_partial_page_open"] == 1
            for name in VARIANTS
        ),
        "native_parent_state_hash_proved": False,
    }
    gates = {
        "exactness_pass": all(exactness.values()),
        "causality_pass": all(
            value for key, value in causality.items() if key != "native_parent_state_hash_proved"
        ),
        "all_opened_chronological_splits_positive": split_positive,
        "gross_archive_gain_at_least_30000_bytes": gross_gain >= GROSS_GATE_BYTES,
        "projected_package_adjusted_gain_at_least_2100_B_per_M": (
            projected_net_bpm >= NET_GATE_BYTES_PER_MILLION
        ),
        "Wfull_beats_Cblind_Cprior_Ctarget": control_ordering,
        "source_within_proposal_ceiling": source_allowance <= SOURCE_CEILING_BYTES,
    }
    authorized = all(gates.values())
    failed = [name for name, passed in gates.items() if not passed]
    verdict = "AUTHORIZED_DISTANT_REPLAY" if authorized else "REJECT"

    decision = {
        "schema": "wikiback_incoming_anchor_context_qh0_decision_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "evidence_level": "zero_credit_exact_causal_trace_ceiling",
        "inputs": inputs,
        "scope": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "p1_rows": len(truth),
            "wrt_events": len(parsed.events),
            "complete_pages": len(intervals),
            "page_open_markers": page_open_markers,
            "page_close_markers": page_close_markers,
            "trailing_partial_page_present": True,
            "complete_page_limit_transmitted_in_frame": len(intervals),
            "event_kind_counts": parsed.kind_counts,
            "page_map": artifact(page_map_path),
        },
        "frozen_construction": {
            **FROZEN_CONFIG,
            "config_sha256": CONFIG_SHA256.hex(),
            "frame_bytes": FRAME_STRUCT.size,
            "source_binding": source_binding,
            "measured_zlib9_bundle_bytes": len(compressed_source),
            "source_framing_allowance_bytes": SOURCE_FRAMING_ALLOWANCE_BYTES,
            "counted_source_allowance_bytes": source_allowance,
            "source_ceiling_bytes": SOURCE_CEILING_BYTES,
        },
        "causal_replays": {
            "first_machine": first.machine_receipt,
            "second_machine": second.machine_receipt,
            "opportunity_count": first.opportunity_count,
            "opportunity_sha256": first.opportunity_sha256,
            "decoders": {name: decodes[name].stats for name in VARIANTS},
        },
        "controls": controls,
        "splits": split_receipts,
        "exactness": exactness,
        "causality": causality,
        "economics": {
            "Wfull_gross_archive_gain_bytes": gross_gain,
            "Wfull_counted_10m_gain_after_source_bytes": counted_gain,
            "Wfull_gross_bytes_per_million": gross_bpm,
            "Wfull_projected_package_adjusted_bytes_per_million": projected_net_bpm,
            "forecast_score_bytes_unchanged": FORECAST_BYTES,
            "forecast_debt_bytes": FORECAST_DEBT_BYTES,
            "score_credit_bytes": 0,
        },
        "gates": {
            "conditions": gates,
            "failed_conditions": failed,
        },
        "decision": {
            "verdict": verdict,
            "distant_replay_authorized": authorized,
            "native_integration_authorized": False,
            "forecast_change_authorized": False,
            "full_1g_authorized": False,
            "next_action": (
                "Run only the frozen distant replay and native parent-state proof."
                if authorized
                else (
                    "Retire this exact incoming-link source, +/-16 event context, "
                    "snapshot rule, KT coder, and matched controls without rescue sweeps."
                )
            ),
        },
        "claim_boundary": (
            "Exact opening-10M trace ceiling only. Parent P1 values stand in for native "
            "state updates; model/source bytes are measured, score credit is zero, and "
            "all chronological splits are opened data; there is no constructive full-1G "
            "result or forecast change."
        ),
        "score_credit_bytes": 0,
    }
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "decision": verdict,
                "decision_path": str(decision_path),
                "Wfull_gross_archive_gain_bytes": gross_gain,
                "Wfull_counted_10m_gain_after_source_bytes": counted_gain,
                "Wfull_projected_net_B_per_M": projected_net_bpm,
                "failed_conditions": failed,
                "score_credit_bytes": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
