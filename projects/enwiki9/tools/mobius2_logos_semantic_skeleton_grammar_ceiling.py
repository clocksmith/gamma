#!/usr/bin/env python3
"""Run the frozen LOGOS semantic skeleton grammar free-description ceiling."""

from __future__ import annotations

import argparse
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
from typing import Any, Sequence
import zlib

import numpy as np

import mobius2_logos_semantic_sentence_edit_bypass as base
from endpoint428_parent_recovery_gate import observed_artifact
from janus_paid_residual_mdl_oracle import range_decode, range_encode
from radix_island_oracle import EmissionGroup, emission_groups
from wrt_exact import parse_store_bytes, read_dictionary_words


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_logos_semantic_skeleton_grammar_ceiling_qh0_v1"
PROPOSAL_ID = "mobius2_logos_semantic_skeleton_grammar_ceiling_v1"
PROGRAM = PROJECT / "programs" / CANDIDATE_ID / "program.py"
PLAN = PROJECT / "docs/mobius2_logos_semantic_skeleton_grammar_ceiling_qh0_plan.md"
SCHEMA = (
    PROJECT
    / "docs/mobius2_logos_semantic_skeleton_grammar_ceiling_qh0_decision.schema.json"
)
PREDECESSOR_DIR = (
    PROJECT / "results/mobius2_logos_semantic_sentence_edit_bypass_qh0_v1"
)
PREDECESSOR_DECISION = PREDECESSOR_DIR / "decision.json"
FRAME = struct.Struct("<8sQQQ5x")
FRAME_MAGIC = b"LGSKEL1\0"
PLAN_HEADER = struct.Struct("<8sQ")
PLAN_MAGIC = b"LGSKPL1\0"
PLAN_ROW = struct.Struct("<IIQQQ")
GROSS_GATE_BPM = 3_000.0

EXPECTED_PREDECESSOR = {
    "decision": "54b38ec7ee8bd182e1252d147a4c9100842e50f6f7c8734a40f00b4484cafc5e",
    "LEX": "157a0558e49cf8b3ea856e45f05cc98a88824adb941a3ec75452fa7a80930a6b",
    "SEM": "b2e41bb7fee41a735cc907c7e3aa5532bbea5f6b2e4d174f01fba2b7d72b8fca",
    "ROT": "001ec37a08b18e0c54417701cc1932216abfdf928f6a46edd01acb34c1490eb0",
}


@dataclass(frozen=True)
class ClauseSequence:
    clause: base.ClauseSpan
    group_indices: tuple[int, ...]
    symbols: tuple[bytes, ...]


@dataclass(frozen=True)
class FreeCopy:
    target_start: int
    source_start: int
    length: int


@dataclass(frozen=True)
class FreePlan:
    target_index: int
    prototype_index: int
    displaced_qbits: int
    copies: tuple[FreeCopy, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bind(path: Path, expected: str, label: str) -> dict[str, Any]:
    row = observed_artifact(path.resolve())
    if row["sha256"] != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {row['sha256']}")
    return row


def read_candidates(path: Path, expected_rows: int) -> list[tuple[int, ...]]:
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError(f"candidate blob is truncated: {path}")
    magic, count = struct.unpack_from("<8sI", data)
    if magic != b"LGSCND1\0" or count != expected_rows:
        raise ValueError(f"candidate blob header differs: {path}")
    cursor = 12
    output: list[tuple[int, ...]] = []
    for target in range(count):
        if cursor >= len(data):
            raise ValueError(f"candidate row is truncated: {path}")
        row_count = data[cursor]
        cursor += 1
        if cursor + row_count * 4 > len(data):
            raise ValueError(f"candidate identities are truncated: {path}")
        row = struct.unpack_from(f"<{row_count}I", data, cursor) if row_count else ()
        cursor += row_count * 4
        if row_count > base.NEIGHBORS or len(set(row)) != row_count:
            raise ValueError(f"candidate row opportunity differs: {path}")
        if any(source >= target for source in row):
            raise ValueError(f"candidate row contains a nonprior source: {path}")
        output.append(tuple(int(value) for value in row))
    if cursor != len(data):
        raise ValueError(f"candidate blob has trailing bytes: {path}")
    return output


def clause_sequences(
    clauses: Sequence[base.ClauseSpan],
    groups: Sequence[EmissionGroup],
    wrt: bytes,
) -> list[ClauseSequence]:
    starts = [group.stream_start for group in groups]
    output: list[ClauseSequence] = []
    for clause in clauses:
        first = bisect_left(starts, clause.wrt_start)
        if first >= len(groups) or groups[first].stream_start != clause.wrt_start:
            raise ValueError("clause start is not an emission-group boundary")
        indices: list[int] = []
        cursor = first
        while cursor < len(groups) and groups[cursor].stream_end <= clause.wrt_end:
            indices.append(cursor)
            if groups[cursor].stream_end == clause.wrt_end:
                break
            cursor += 1
        if not indices or groups[indices[-1]].stream_end != clause.wrt_end:
            raise ValueError("clause end is not an emission-group boundary")
        symbols = tuple(
            wrt[groups[index].stream_start : groups[index].stream_end]
            for index in indices
        )
        output.append(ClauseSequence(clause, tuple(indices), symbols))
    return output


def merge_copies(rows: Sequence[FreeCopy]) -> tuple[FreeCopy, ...]:
    output: list[FreeCopy] = []
    for row in rows:
        if row.length <= 0 or row.source_start + row.length > row.target_start:
            raise ValueError("free skeleton copy is not decoder-visible")
        if output and row.target_start < output[-1].target_start + output[-1].length:
            raise ValueError("free skeleton copies overlap")
        if (
            output
            and output[-1].target_start + output[-1].length == row.target_start
            and output[-1].source_start + output[-1].length == row.source_start
        ):
            previous = output[-1]
            output[-1] = FreeCopy(
                previous.target_start,
                previous.source_start,
                previous.length + row.length,
            )
        else:
            output.append(row)
    return tuple(output)


def align_pair(
    target: ClauseSequence,
    prototype: ClauseSequence,
    groups: Sequence[EmissionGroup],
    cost_prefix: np.ndarray,
) -> FreePlan | None:
    matcher = SequenceMatcher(
        None, target.symbols, prototype.symbols, autojunk=False
    )
    copies: list[FreeCopy] = []
    displaced = 0
    for block in matcher.get_matching_blocks():
        if block.size == 0:
            continue
        target_first = target.group_indices[block.a]
        target_last = target.group_indices[block.a + block.size - 1]
        source_first = prototype.group_indices[block.b]
        source_last = prototype.group_indices[block.b + block.size - 1]
        target_start = groups[target_first].stream_start
        target_end = groups[target_last].stream_end
        source_start = groups[source_first].stream_start
        source_end = groups[source_last].stream_end
        if target_end - target_start != source_end - source_start:
            raise ValueError("matching emission groups differ in encoded length")
        if wrt_slice(groups, target_first, target_last) != wrt_slice(
            groups, source_first, source_last
        ):
            raise ValueError("matching emission groups differ in WRT bytes")
        copies.append(FreeCopy(target_start, source_start, target_end - target_start))
        displaced += int(cost_prefix[target_end] - cost_prefix[target_start])
    merged = merge_copies(copies)
    if not merged or displaced <= 0:
        return None
    return FreePlan(
        target.clause.index,
        prototype.clause.index,
        displaced,
        merged,
    )


_CURRENT_WRT: bytes | None = None


def wrt_slice(
    groups: Sequence[EmissionGroup], first: int, last: int
) -> bytes:
    if _CURRENT_WRT is None:
        raise RuntimeError("WRT comparison source is not initialized")
    return _CURRENT_WRT[groups[first].stream_start : groups[last].stream_end]


def better(current: FreePlan | None, row: FreePlan | None) -> FreePlan | None:
    if row is None:
        return current
    if current is None or row.displaced_qbits > current.displaced_qbits:
        return row
    if (
        row.displaced_qbits == current.displaced_qbits
        and row.prototype_index < current.prototype_index
    ):
        return row
    return current


def choose_plans(
    sequences: Sequence[ClauseSequence],
    candidate_rows: dict[str, Sequence[Sequence[int]]],
    groups: Sequence[EmissionGroup],
    cost_prefix: np.ndarray,
) -> tuple[dict[str, list[FreePlan]], int]:
    output: dict[str, list[FreePlan]] = {name: [] for name in candidate_rows}
    evaluations = 0
    for target in sequences:
        sources = sorted(
            {
                source
                for rows in candidate_rows.values()
                for source in rows[target.clause.index]
            }
        )
        pair_rows: dict[int, FreePlan | None] = {}
        for source in sources:
            pair_rows[source] = align_pair(
                target, sequences[source], groups, cost_prefix
            )
            evaluations += 1
        for name, rows in candidate_rows.items():
            selected: FreePlan | None = None
            for source in rows[target.clause.index]:
                selected = better(selected, pair_rows[source])
            if selected is not None:
                output[name].append(selected)
        if (target.clause.index + 1) % 256 == 0 or target.clause.index + 1 == len(sequences):
            active = " ".join(
                f"{name}={len(output[name])}" for name in sorted(output)
            )
            print(
                f"[logos-skeleton] align={target.clause.index + 1}/{len(sequences)} "
                f"pairs={evaluations} {active}",
                flush=True,
            )
    return output, evaluations


def serialize_plans(plans: Sequence[FreePlan]) -> bytes:
    output = bytearray(PLAN_HEADER.pack(PLAN_MAGIC, len(plans)))
    for plan in sorted(plans, key=lambda value: value.target_index):
        output += struct.pack("<III", plan.target_index, plan.prototype_index, len(plan.copies))
        for copy in plan.copies:
            output += PLAN_ROW.pack(
                plan.target_index,
                plan.prototype_index,
                copy.target_start,
                copy.source_start,
                copy.length,
            )
    return bytes(output)


def build_variant(
    name: str,
    plans: Sequence[FreePlan],
    wrt: bytes,
    probabilities: np.ndarray,
    parent_total: int,
    output_dir: Path,
    write_artifacts: bool,
) -> tuple[dict[str, Any], bytes]:
    copies = sorted(
        (copy for plan in plans for copy in plan.copies),
        key=lambda value: value.target_start,
    )
    previous_end = 0
    literal_bytes = np.ones(len(wrt), dtype=bool)
    for copy in copies:
        if copy.target_start < previous_end or copy.source_start + copy.length > copy.target_start:
            raise ValueError(f"{name} free plan overlaps or uses future bytes")
        literal_bytes[copy.target_start : copy.target_start + copy.length] = False
        previous_end = copy.target_start + copy.length
    literal_rows = np.repeat(literal_bytes, 8)
    truth = np.unpackbits(np.frombuffer(wrt, dtype=np.uint8), bitorder="big")
    residual_p1 = np.asarray(probabilities[literal_rows], dtype=np.uint16)
    residual_truth = truth[literal_rows]
    payload = range_encode(residual_p1, residual_truth)
    decoded_literal = range_decode(payload, residual_p1)
    copy_by_start = {copy.target_start: copy for copy in copies}
    output = bytearray(len(wrt))
    literal_cursor = 0
    position = 0
    while position < len(wrt):
        copy = copy_by_start.get(position)
        if copy is not None:
            output[position : position + copy.length] = output[
                copy.source_start : copy.source_start + copy.length
            ]
            position += copy.length
            continue
        bits = decoded_literal[literal_cursor : literal_cursor + 8]
        if len(bits) != 8:
            raise ValueError(f"{name} literal stream ended early")
        output[position] = int(np.packbits(bits, bitorder="big")[0])
        literal_cursor += 8
        position += 1
    if literal_cursor != len(decoded_literal):
        raise ValueError(f"{name} literal stream has unused bits")
    reconstructed = bytes(output)
    archive = FRAME.pack(
        FRAME_MAGIC, len(wrt), len(residual_truth), len(payload)
    ) + payload
    second_payload = range_encode(residual_p1, residual_truth)
    second_archive = FRAME.pack(
        FRAME_MAGIC, len(wrt), len(residual_truth), len(second_payload)
    ) + second_payload
    plan_blob = serialize_plans(plans)
    if write_artifacts:
        (output_dir / f"{name.lower()}.archive").write_bytes(archive)
        (output_dir / f"{name.lower()}.free_plan.bin").write_bytes(plan_blob)
    receipt = {
        "name": name,
        "archive_bytes": len(archive),
        "archive_sha256": sha256_bytes(archive),
        "gain_bytes": parent_total - len(archive),
        "frame_bytes": FRAME.size,
        "residual_payload_bytes": len(payload),
        "literal_bits": len(residual_truth),
        "active_sentences": len(plans),
        "copy_fragments": len(copies),
        "generated_wrt_bytes": sum(copy.length for copy in copies),
        "predicted_displaced_qbits": sum(plan.displaced_qbits for plan in plans),
        "free_plan_bytes_uncharged": len(plan_blob),
        "free_plan_sha256": sha256_bytes(plan_blob),
        "all_sources_strictly_prior": all(
            copy.source_start + copy.length <= copy.target_start for copy in copies
        ),
        "arithmetic_decode": np.array_equal(decoded_literal, residual_truth),
        "wrt_roundtrip": reconstructed == wrt,
        "second_archive_identity": archive == second_archive,
    }
    if not all(
        (
            receipt["all_sources_strictly_prior"],
            receipt["arithmetic_decode"],
            receipt["wrt_roundtrip"],
            receipt["second_archive_identity"],
        )
    ):
        raise ValueError(f"{name} exact free skeleton replay failed")
    return receipt, reconstructed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint-p1", type=Path, default=PROJECT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1")
    parser.add_argument("--joint-payload", type=Path, default=PROJECT / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload")
    parser.add_argument("--wrt-store", type=Path, default=PROJECT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin")
    parser.add_argument("--page-map", type=Path, default=PROJECT / "results/mobius2_tessera_typed_fiber_ceiling_qh0_v1/page_map.bin")
    parser.add_argument("--trace-decision", type=Path, default=PROJECT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/decision.json")
    parser.add_argument("--raw-input", type=Path, default=PROJECT / "data/enwik9_10000000.bin")
    parser.add_argument("--dictionary", type=Path, default=base.SOURCE_ROOT / "english.dic")
    parser.add_argument("--backend", type=Path, default=base.SOURCE_ROOT / "cmix.bin")
    parser.add_argument("--predecessor-decision", type=Path, default=PREDECESSOR_DECISION)
    parser.add_argument("--lex-candidates", type=Path, default=PREDECESSOR_DIR / "lex_candidates.bin")
    parser.add_argument("--sem-candidates", type=Path, default=PREDECESSOR_DIR / "sem_candidates.bin")
    parser.add_argument("--rot-candidates", type=Path, default=PREDECESSOR_DIR / "rot_candidates.bin")
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "results" / CANDIDATE_ID)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError(f"refusing to overwrite {decision_path}")

    paths = {
        "backend": args.backend,
        "dictionary": args.dictionary,
        "joint_p1": args.joint_p1,
        "joint_payload": args.joint_payload,
        "wrt_store": args.wrt_store,
        "page_map": args.page_map,
        "trace_decision": args.trace_decision,
        "raw_input": args.raw_input,
    }
    inputs = {
        name: bind(path, base.EXPECTED_SHA256[name], name)
        for name, path in paths.items()
    }
    predecessor_inputs = {
        "decision": bind(
            args.predecessor_decision, EXPECTED_PREDECESSOR["decision"], "predecessor decision"
        ),
        "LEX": bind(args.lex_candidates, EXPECTED_PREDECESSOR["LEX"], "LEX candidate blob"),
        "SEM": bind(args.sem_candidates, EXPECTED_PREDECESSOR["SEM"], "SEM candidate blob"),
        "ROT": bind(args.rot_candidates, EXPECTED_PREDECESSOR["ROT"], "ROT candidate blob"),
    }
    predecessor = json.loads(args.predecessor_decision.read_text())
    if predecessor.get("decision", {}).get("verdict") != "REJECT":
        raise ValueError("semantic edit predecessor is not terminal")
    if not all(predecessor.get("proof", {}).get("conditions", {}).values()):
        raise ValueError("semantic edit predecessor lacks an exact proof")

    pages, raw_bytes, wrt_bytes = base.read_pages(args.page_map)
    full_store = args.wrt_store.read_bytes()
    full_raw = args.raw_input.read_bytes()
    wrt = full_store[5 : 5 + wrt_bytes]
    patched = bytearray(wrt)
    patched[1:5] = raw_bytes.to_bytes(4, "big")
    parsed = parse_store_bytes(
        base.STORE_HEADER + bytes(patched), read_dictionary_words(args.dictionary)
    )
    if parsed.decoded != full_raw[:raw_bytes]:
        raise ValueError("patched prefix parse differs from the complete-page raw prefix")
    groups = emission_groups(parsed)
    populations = base.text_populations(parsed.decoded, pages, groups)
    clauses, scanned = base.discover_clauses(parsed.decoded, groups, populations)
    if len(clauses) != predecessor["population"]["eligible_sentence_spans"]:
        raise ValueError("eligible sentence universe differs from the predecessor")
    sequences = clause_sequences(clauses, groups, wrt)
    candidate_rows = {
        "LEX": read_candidates(args.lex_candidates, len(clauses)),
        "SEM": read_candidates(args.sem_candidates, len(clauses)),
        "ROT": read_candidates(args.rot_candidates, len(clauses)),
    }

    all_p1 = base.read_p1(args.joint_p1)
    probabilities = np.asarray(all_p1[: base.FROZEN_ROWS], dtype=np.uint16)
    if len(probabilities) != len(wrt) * 8 or np.any(probabilities == 0):
        raise ValueError("joint prefix probability contract differs")
    parent_payload = base.candidate.range_encode(wrt, probabilities)
    parent_total = base.CMIX_HEADER_BYTES + len(parent_payload)
    truth = np.unpackbits(np.frombuffer(wrt, dtype=np.uint8), bitorder="big")
    parent_decoder = base.candidate.RangeDecoder(parent_payload)
    decoded_parent = np.fromiter(
        (parent_decoder.decode(value) for value in probabilities),
        dtype=np.uint8,
        count=len(probabilities),
    )
    if not np.array_equal(decoded_parent, truth):
        raise ValueError("joint prefix parent arithmetic decode failed")
    byte_costs = base.qbit_costs(probabilities, wrt)
    cost_prefix = np.concatenate(
        (np.zeros(1, dtype=np.int64), np.cumsum(byte_costs, dtype=np.int64))
    )

    global _CURRENT_WRT
    _CURRENT_WRT = wrt
    chosen, pair_evaluations = choose_plans(
        sequences, candidate_rows, groups, cost_prefix
    )
    variants: dict[str, dict[str, Any]] = {}
    semantic_wrt = wrt
    for name in ("LEX", "SEM", "ROT"):
        variants[name], decoded = build_variant(
            name,
            chosen[name],
            wrt,
            probabilities,
            parent_total,
            args.output_dir,
            True,
        )
        if name == "SEM":
            semantic_wrt = decoded

    splits: dict[str, dict[str, Any]] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        split_plans = [
            plan
            for plan in chosen["SEM"]
            if clauses[plan.target_index].split == split
        ]
        splits[split], _decoded = build_variant(
            f"SEM_{split}",
            split_plans,
            wrt,
            probabilities,
            parent_total,
            args.output_dir,
            False,
        )

    reconstructed_store = full_store[:5] + semantic_wrt + full_store[5 + wrt_bytes :]
    if reconstructed_store != full_store:
        raise ValueError("semantic skeleton prefix replacement differs from parent")
    reconstructed_path = args.output_dir / "semantic_skeleton_full.wrt"
    restored_path = args.output_dir / "semantic_skeleton_full.raw"
    reconstructed_path.write_bytes(reconstructed_store)
    with (args.output_dir / "inverse.stdout.log").open("wb") as stdout, (
        args.output_dir / "inverse.stderr.log"
    ).open("wb") as stderr:
        inverse = subprocess.run(
            [str(args.backend), "-d", str(args.dictionary), str(reconstructed_path), str(restored_path)],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    raw_roundtrip = (
        inverse.returncode == 0
        and restored_path.is_file()
        and sha256_file(restored_path) == base.EXPECTED_SHA256["raw_input"]
    )
    if not raw_roundtrip:
        raise ValueError("official semantic skeleton inverse failed")

    required_gain = math.ceil(raw_bytes * GROSS_GATE_BPM / 1_000_000.0)
    gross_bpm = variants["SEM"]["gain_bytes"] * 1_000_000.0 / raw_bytes
    exact_conditions = {
        "predecessor_and_inputs_exact": True,
        "joint_prefix_parent_decode": True,
        "all_sources_strictly_prior": all(row["all_sources_strictly_prior"] for row in variants.values()),
        "all_arithmetic_decodes": all(row["arithmetic_decode"] for row in variants.values()),
        "all_wrt_roundtrips": all(row["wrt_roundtrip"] for row in variants.values()),
        "all_second_archives_identical": all(row["second_archive_identity"] for row in variants.values()),
        "all_split_wrt_roundtrips": all(row["wrt_roundtrip"] for row in splits.values()),
        "all_split_archives_identical": all(row["second_archive_identity"] for row in splits.values()),
        "official_raw_inverse": raw_roundtrip,
    }
    economic_conditions = {
        "SEM_gross_at_least_3000_BPM": variants["SEM"]["gain_bytes"] >= required_gain,
        "development_gain_positive": splits["development"]["gain_bytes"] > 0,
        "selection_gain_positive": splits["selection"]["gain_bytes"] > 0,
        "sealed_confirmation_gain_positive": splits["sealed_confirmation"]["gain_bytes"] > 0,
        "SEM_beats_LEX": variants["SEM"]["archive_bytes"] < variants["LEX"]["archive_bytes"],
        "SEM_beats_ROT": variants["SEM"]["archive_bytes"] < variants["ROT"]["archive_bytes"],
    }
    conditions = {**exact_conditions, **economic_conditions}
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    verdict = "AUTHORIZED_PAID_GRAMMAR_Q1" if authorized else "REJECT"
    source_bytes = len(
        zlib.compress(Path(__file__).read_bytes() + PROGRAM.read_bytes(), level=9)
    )
    decision = {
        "schema": "gamma.mobius2_logos_semantic_skeleton_grammar_ceiling_qh0.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "claim_boundary": (
            "Exact opening-prefix zero-description-cost skeleton ceiling. Prototype, "
            "matching schedule, rules, and invocations are supplied out of band; "
            "framing and the terminated residual are paid. No constructive grammar, "
            "native state hash, package, forecast credit, or full-1G score is claimed."
        ),
        "inputs": {
            **inputs,
            "predecessor": predecessor_inputs,
            "candidate_program": observed_artifact(PROGRAM),
            "plan": observed_artifact(PLAN),
            "decision_schema": observed_artifact(SCHEMA),
            "tool": observed_artifact(Path(__file__).resolve()),
        },
        "population": {
            "complete_pages": len(pages),
            "raw_equivalent_bytes": raw_bytes,
            "wrt_bytes": wrt_bytes,
            "p1_rows": len(probabilities),
            "emission_groups": len(groups),
            "sentence_segments_scanned": scanned,
            "eligible_sentence_spans": len(clauses),
            "sentence_splits": {
                split: sum(row.split == split for row in clauses)
                for split in ("development", "selection", "sealed_confirmation")
            },
        },
        "construction": {
            "alignment": "difflib.SequenceMatcher",
            "autojunk": False,
            "symbol": "exact WRT emission-group bytes",
            "prototype_identity_cost_bytes": 0,
            "matching_schedule_cost_bytes": 0,
            "rule_definition_cost_bytes": 0,
            "invocation_cost_bytes": 0,
            "candidate_frame_bytes": FRAME.size,
            "pair_evaluations": pair_evaluations,
            "selection": "maximum rounded-Q256 displaced parent loss with lower-source tie",
        },
        "parent": {
            "payload_bytes": len(parent_payload),
            "payload_sha256": sha256_bytes(parent_payload),
            "total_bytes": parent_total,
        },
        "variants": variants,
        "splits": splits,
        "source_accounting": {
            "compressed_tool_plus_candidate_bytes": source_bytes,
            "charged_at_qh0": False,
        },
        "economics": {
            "required_gross_gain_bytes": required_gain,
            "required_gross_gain_bytes_per_million": GROSS_GATE_BPM,
            "SEM_gross_gain_bytes": variants["SEM"]["gain_bytes"],
            "SEM_gross_gain_bytes_per_million": gross_bpm,
            "forecast_bytes_unchanged": 109_389_323,
            "remaining_target_debt_bytes": 1_389_323,
        },
        "proof": {
            "conditions": exact_conditions,
            "reconstructed_prefix_equals_parent": semantic_wrt == wrt,
            "reconstructed_full_store_equals_parent": reconstructed_store == full_store,
            "official_inverse_returncode": inverse.returncode,
            "official_raw_sha256": sha256_file(restored_path),
            "native_predictor_state_hash_proved": False,
        },
        "gates": {
            "conditions": conditions,
            "failed_conditions": failed,
        },
        "decision": {
            "verdict": verdict,
            "promotion_authorized": authorized,
            "forecast_bytes": 109_389_323,
            "score_credit_bytes": 0,
            "next_action": (
                "freeze a paid shared-rule grammar Q1 and charge every rule and invocation"
                if authorized
                else "retire this exact semantic skeleton grammar ceiling without alignment or retrieval sweeps"
            ),
        },
        "score_credit_bytes": 0,
    }
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "verdict": verdict,
                "SEM_gain_bytes": variants["SEM"]["gain_bytes"],
                "SEM_gain_BPM": gross_bpm,
                "LEX_gain_bytes": variants["LEX"]["gain_bytes"],
                "ROT_gain_bytes": variants["ROT"]["gain_bytes"],
                "failed_conditions": failed,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
