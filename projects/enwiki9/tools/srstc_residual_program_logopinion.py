#!/usr/bin/env python3
"""Exact zero-command log-opinion consensus over causal residual programs."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
sys.path.insert(0, str(TOOLS))

import srstc_residual_program_ceiling as base  # noqa: E402
from causal_state_screen import WikiState  # noqa: E402


CANDIDATE_ID = "srstc_residual_program_logopinion_qh0_v1"
PROPOSAL_ID = "srstc_residual_program_logopinion_v1"
VARIANTS = ("F0", "R0", "RB", "RS")
DEFAULT_OUTPUT = PROJECT / f"results/{CANDIDATE_ID}/decision.json"


@dataclass
class ConsensusBuild:
    probabilities: dict[str, np.ndarray]
    blocks: int
    active_blocks: dict[str, int]
    nonzero_rows: dict[str, int]
    candidate_histogram: dict[str, int]
    blind_singleton_keys: int
    blind_redirected_keys: int
    snapshot_epochs: int
    programs: int
    live_keys_final: int
    evicted_keys: int


def consensus_q(programs: list[base.Program], rotation: int = 0) -> np.ndarray:
    if len(programs) < base.MIN_PROGRAMS:
        return np.zeros(base.PROGRAM_BITS, dtype=np.int8)
    matrix = np.stack([program.q for program in programs]).astype(np.int16)
    if rotation:
        indexes = (np.arange(base.PROGRAM_BITS) + rotation) % base.PROGRAM_BITS
        matrix = matrix[:, indexes]
    sums = matrix.sum(axis=0, dtype=np.int16)
    # np.trunc specifies the frozen toward-zero division for both signs.
    return np.trunc(sums.astype(np.float64) / len(programs)).astype(np.int8)


def blind_redirect(snapshot: dict[tuple[int, ...], tuple[int, ...]]) -> tuple[dict[tuple[int, ...], tuple[int, ...]], int, int]:
    strata: dict[tuple[int, int], list[tuple[int, ...]]] = defaultdict(list)
    for key, refs in snapshot.items():
        strata[(key[0], len(refs))].append(key)
    redirect: dict[tuple[int, ...], tuple[int, ...]] = {}
    singleton = 0
    redirected = 0
    for keys in strata.values():
        ordered = sorted(keys)
        if len(ordered) == 1:
            redirect[ordered[0]] = ordered[0]
            singleton += 1
            continue
        for index, key in enumerate(ordered):
            redirect[key] = ordered[(index + 1) % len(ordered)]
            redirected += 1
    return redirect, singleton, redirected


def global_candidates(table: base.ProgramTable, epoch_start: int) -> list[base.Program]:
    newest: dict[bytes, base.Program] = {}
    for program in table.programs.values():
        if program.completed_at > epoch_start:
            continue
        previous = newest.get(program.packed)
        if previous is None or program.ordinal > previous.ordinal:
            newest[program.packed] = program
    return sorted(newest.values(), key=lambda item: (-item.ordinal, item.packed))[: base.MAX_CANDIDATES]


def build_consensus(
    parsed: base.ParsedStore,
    parent: np.ndarray,
    truth: np.ndarray,
) -> ConsensusBuild:
    probabilities = {
        name: np.array(parent, dtype=np.uint16, copy=True) for name in VARIANTS
    }
    active_blocks = {name: 0 for name in VARIANTS}
    nonzero_rows = {name: 0 for name in VARIANTS}
    histogram: dict[str, int] = {}
    table = base.ProgramTable()
    recent: deque[bytes] = deque(maxlen=base.RECENT_PROGRAMS)
    event_chain: deque[bytes] = deque(maxlen=4)
    wiki = WikiState()
    events = parsed.events
    event_cursor = 0
    ordinal = 0
    blocks = 0
    current_epoch = -1
    blind: dict[tuple[int, ...], tuple[int, ...]] = {}
    flat: list[base.Program] = []
    blind_singletons = 0
    blind_redirected = 0

    for start in range(6, len(parsed.stream) - base.BLOCK_BYTES + 1, base.BLOCK_BYTES):
        end = start + base.BLOCK_BYTES
        blocks += 1
        while event_cursor < len(events) and events[event_cursor].end <= start:
            event = events[event_cursor]
            for byte in event.decoded:
                wiki.update(byte)
            event_chain.append(event.encoded)
            event_cursor += 1

        current_prefix = b""
        if event_cursor < len(events):
            event = events[event_cursor]
            if event.start <= start < event.end:
                current_prefix = parsed.stream[event.start:start]

        relative_start = start - 6
        epoch = relative_start // base.EPOCH_BYTES
        epoch_start = 6 + epoch * base.EPOCH_BYTES
        if epoch != current_epoch:
            table.open_epoch(epoch)
            blind, singleton, redirected = blind_redirect(table.snapshot)
            blind_singletons += singleton
            blind_redirected += redirected
            flat = global_candidates(table, epoch_start)
            current_epoch = epoch

        row_start = start * 8
        row_end = end * 8
        block_parent = np.asarray(parent[row_start:row_end])
        block_truth = truth[row_start:row_end]
        keys = base.make_keys(recent, wiki, current_prefix, event_chain, int(block_parent[0]))
        keyed = table.candidates(keys, epoch_start)
        histogram[str(len(keyed))] = histogram.get(str(len(keyed)), 0) + 1
        blind_keys = tuple(blind.get(key, key) for key in keys)
        blinded = table.candidates(blind_keys, epoch_start)
        program_sets = {
            "F0": flat,
            "R0": keyed,
            "RB": blinded,
            "RS": keyed,
        }
        for name, programs in program_sets.items():
            if len(programs) < base.MIN_PROGRAMS:
                continue
            rotation = base.PROGRAM_ROTATION if name == "RS" else 0
            q = consensus_q(programs, rotation)
            adjusted = base.adjust_p1(block_parent, q)
            probabilities[name][row_start:row_end] = adjusted
            active_blocks[name] += 1
            nonzero_rows[name] += int(np.count_nonzero(q))

        q, packed = base.residual_program(block_parent, block_truth)
        ordinal += 1
        table.insert(keys, base.Program(ordinal, q, packed, end))
        recent.append(packed)

    return ConsensusBuild(
        probabilities=probabilities,
        blocks=blocks,
        active_blocks=active_blocks,
        nonzero_rows=nonzero_rows,
        candidate_histogram=dict(sorted(histogram.items(), key=lambda item: int(item[0]))),
        blind_singleton_keys=blind_singletons,
        blind_redirected_keys=blind_redirected,
        snapshot_epochs=current_epoch + 1,
        programs=len(table.programs),
        live_keys_final=len(table.live),
        evicted_keys=table.evicted_keys,
    )


def exact_payloads(
    parent: np.ndarray,
    truth: np.ndarray,
    variants: dict[str, np.ndarray],
) -> tuple[dict[str, bytes], dict[str, bool]]:
    payloads = {"B0": base.range_encode(parent, truth)}
    decoded = {"B0": base.range_decode_equal(payloads["B0"], parent, truth)}
    for name, probabilities in variants.items():
        payloads[name] = base.range_encode(probabilities, truth)
        decoded[name] = base.range_decode_equal(payloads[name], probabilities, truth)
    return payloads, decoded


def split_receipt(
    pages: list[base.Page],
    split: str,
    parent: np.ndarray,
    truth: np.ndarray,
    variants: dict[str, np.ndarray],
) -> dict[str, Any]:
    parent_split, split_truth, raw_bytes, page_count = base.split_arrays(
        pages, split, parent, truth
    )
    parent_payload = base.range_encode(parent_split, split_truth)
    rows: dict[str, Any] = {}
    for name, probabilities in variants.items():
        candidate_split, _, _, _ = base.split_arrays(pages, split, probabilities, truth)
        payload = base.range_encode(candidate_split, split_truth)
        gain = len(parent_payload) - len(payload)
        rows[name] = {
            "payload_bytes": len(payload),
            "gain_bytes": gain,
            "gain_bytes_per_million": gain * 1_000_000.0 / raw_bytes,
        }
    return {
        "pages": page_count,
        "raw_bytes": raw_bytes,
        "parent_payload_bytes": len(parent_payload),
        "variants": rows,
    }


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    inputs = {
        "store": base.bind(args.store, "store"),
        "dictionary": base.bind(args.dictionary, "dictionary"),
        "p1": base.bind(args.p1, "p1"),
        "archive": base.bind(args.parent_archive, "archive"),
        "raw": base.bind(args.raw, "raw"),
        "page_map": base.bind(args.page_map, "page_map"),
    }
    parsed = base.parse_store(args.store, args.dictionary)
    raw = args.raw.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("official WRT inverse differs from canonical raw")
    truth = base.truth_bits(parsed.stream)
    parent = base.load_p1(args.p1, len(truth))
    pages = base.read_pages(args.page_map, len(parsed.stream))

    first = build_consensus(parsed, parent, truth)
    second = build_consensus(parsed, parent, truth)
    deterministic = (
        first.active_blocks == second.active_blocks
        and first.nonzero_rows == second.nonzero_rows
        and first.candidate_histogram == second.candidate_histogram
        and all(np.array_equal(first.probabilities[name], second.probabilities[name]) for name in VARIANTS)
    )
    if not deterministic:
        raise ValueError("log-opinion replay is nondeterministic")
    if any(np.any(values == 0) for values in first.probabilities.values()):
        raise ValueError("log-opinion emitted an illegal probability")

    payloads, decoded = exact_payloads(parent, truth, first.probabilities)
    if not all(decoded.values()):
        raise ValueError("an arithmetic control failed to decode")
    archive = args.parent_archive.read_bytes()
    parent_identity = archive[37:] == payloads["B0"]
    if not parent_identity:
        raise ValueError("parent payload identity failed")
    reconstructed = np.packbits(truth, bitorder="big").tobytes()
    if reconstructed != parsed.stream:
        raise ValueError("truth does not rebuild the WRT stream")

    splits = {
        name: split_receipt(pages, name, parent, truth, first.probabilities)
        for name in ("development", "selection", "sealed_confirmation")
    }
    full = {
        name: {
            "payload_bytes": len(payloads[name]),
            "gain_bytes": len(payloads["B0"]) - len(payloads[name]),
            "gain_bytes_per_million": float(len(payloads["B0"]) - len(payloads[name])),
        }
        for name in VARIANTS
    }
    r0_full = full["R0"]
    r0_development = splits["development"]["variants"]["R0"]
    r0_selection = splits["selection"]["variants"]["R0"]
    r0_sealed = splits["sealed_confirmation"]["variants"]["R0"]
    control_order = all(len(payloads["R0"]) < len(payloads[name]) for name in ("F0", "RB", "RS"))
    authorized = (
        r0_full["gain_bytes_per_million"] >= 3_000.0
        and r0_development["gain_bytes"] > 0
        and r0_selection["gain_bytes"] > 0
        and r0_sealed["gain_bytes_per_million"] >= 3_000.0
        and control_order
    )
    verdict = "AUTHORIZED_PAID_Q1" if authorized else "REJECT"
    return {
        "schema": "srstc_residual_program_logopinion_qh0_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_causal_source_supplied_ceiling",
        "inputs": inputs,
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(parsed.stream),
            "truth_rows": len(truth),
            "complete_pages": len(pages),
            "blocks": first.blocks,
        },
        "architecture": {
            "candidate_source": "preceding_epoch_K0_K1_K2_residual_programs",
            "consensus": "componentwise_integer_mean_truncated_toward_zero",
            "command_bits": 0,
            "odds_ladder": "(5/4)^r_integer_nearest_ties_upward",
            "controls": ["B0", "F0", "R0", "RB", "RS"],
            "rotation": base.PROGRAM_ROTATION,
        },
        "observer": {
            "programs": first.programs,
            "live_keys_final": first.live_keys_final,
            "evicted_keys": first.evicted_keys,
            "snapshot_epochs": first.snapshot_epochs,
            "candidate_count_histogram": first.candidate_histogram,
            "active_blocks": first.active_blocks,
            "nonzero_consensus_rows": first.nonzero_rows,
            "blind_singleton_keys": first.blind_singleton_keys,
            "blind_redirected_keys": first.blind_redirected_keys,
        },
        "economics": {
            "parent_payload_bytes": len(payloads["B0"]),
            "full": full,
            "splits": splits,
            "gross_gate_bytes_per_million": 3_000.0,
            "control_order_pass": control_order,
        },
        "proof": {
            "all_input_identities_exact": True,
            "parent_payload_byte_identity": parent_identity,
            "all_five_arithmetic_decodes": all(decoded.values()),
            "complete_wrt_reconstruction": reconstructed == parsed.stream,
            "official_raw_inverse": parsed.decoded == raw,
            "all_programs_preceding_epoch_causal": True,
            "all_probabilities_legal_nonzero": True,
            "second_state_p1_payload_replay_identical": deterministic,
            "valid_reject_exits_zero": True,
        },
        "decision": {
            "verdict": verdict,
            "paid_q1_authorized": authorized,
            "score_credit_bytes": 0,
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score": None,
            "next_action": (
                "measure complete canonical source/model allowance in paid Q1"
                if authorized
                else "retire this componentwise log-opinion operation without rescue sweeps"
            ),
        },
        "claim_boundary": (
            "QH0 supplies observer source and online tables for free. The P1 stream and "
            "arithmetic payload are exact, causal, and zero-command, but earn no forecast credit."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=base.DEFAULT_STORE)
    parser.add_argument("--dictionary", type=Path, default=base.DEFAULT_DICTIONARY)
    parser.add_argument("--p1", type=Path, default=base.DEFAULT_P1)
    parser.add_argument("--parent-archive", type=Path, default=base.DEFAULT_ARCHIVE)
    parser.add_argument("--raw", type=Path, default=base.DEFAULT_RAW)
    parser.add_argument("--page-map", type=Path, default=base.DEFAULT_PAGE_MAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    receipt = build_receipt(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    args.output.write_text(encoded)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
