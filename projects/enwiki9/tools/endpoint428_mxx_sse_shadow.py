#!/usr/bin/env python3
"""Test tiny causal SSE endpoints keyed by FX2's decoder-rebuilt ``mxx``.

FX2 layer-0 mixer 5 is keyed by ``ContextManager::mxx`` and has positive
residual gain over endpoint428, but its full raw-model input universe is too
expensive to inherit blindly.  This tool asks the narrower constructive
question: can a small online calibration table using only endpoint428's
probability and the exact decoder-visible ``mxx`` state retain enough gain?

Every candidate predicts before learning the current truth bit.  Candidate
selection reads development rows only.  The selected configuration is then
replayed from row zero, arithmetic-coded exactly, and audited on sealed
holdout blocks.  Bit-position-only calibrators are matched controls and cannot
be selected as the mxx candidate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import struct
from typing import Any, Iterable

import numpy as np

from fx2_attribution_external_base_screen import (
    P1_HEADER_BYTES,
    PPM,
    PROBABILITY_TOTAL,
    artifact,
    cmix_archive_header_bytes,
    exact_block_audit,
    exact_replay,
    qbit_tables,
    read_p1_header,
)


MASK64 = (1 << 64) - 1
QBITS_PER_BYTE = 256 * 8
DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "external"
    / "fx2-cmix"
    / "src"
    / "models"
    / "fxcmv1.cpp"
)
CONTROL_SCHEMES = {"global", "bitpos"}
CANDIDATE_SCHEMES = {"mxx", "mxx_bitpos"}
ALL_SCHEMES = CONTROL_SCHEMES | CANDIDATE_SCHEMES


@dataclass(frozen=True)
class CalibrationConfig:
    name: str
    context_scheme: str
    probability_buckets: int
    estimator: str
    parameter: int
    minimum_observations: int = 1
    strength_ppm: int = PPM

    @property
    def is_control(self) -> bool:
        return self.context_scheme in CONTROL_SCHEMES


DEFAULT_CONFIGS = (
    CalibrationConfig("control_global_p32_mean128", "global", 32, "mean", 128),
    CalibrationConfig("control_bitpos_p32_mean128", "bitpos", 32, "mean", 128),
    CalibrationConfig("mxx_p16_mean32", "mxx", 16, "mean", 32),
    CalibrationConfig("mxx_p16_mean128", "mxx", 16, "mean", 128),
    CalibrationConfig("mxx_p16_mean512", "mxx", 16, "mean", 512),
    CalibrationConfig("mxx_p32_mean32", "mxx", 32, "mean", 32),
    CalibrationConfig("mxx_p32_mean128", "mxx", 32, "mean", 128),
    CalibrationConfig("mxx_p32_mean512", "mxx", 32, "mean", 512),
    CalibrationConfig("mxx_p16_ema8", "mxx", 16, "ema", 8),
    CalibrationConfig(
        "mxx_bitpos_p16_mean128", "mxx_bitpos", 16, "mean", 128
    ),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_unsigned_char_array(source: str, name: str) -> tuple[int, ...]:
    """Parse one pinned 256-entry C array without relying on a C preprocessor."""

    pattern = re.compile(
        rf"(?:const\s+)?(?:U8|unsigned\s+char)\s+{re.escape(name)}"
        r"\s*\[\s*256\s*\]\s*=\s*\{(.*?)\}\s*;",
        re.DOTALL,
    )
    match = pattern.search(source)
    if match is None:
        raise ValueError(f"unable to locate {name}[256]")
    body = re.sub(r"//[^\n]*|/\*.*?\*/", "", match.group(1), flags=re.DOTALL)
    values = tuple(int(token, 0) for token in re.findall(r"0[xX][0-9a-fA-F]+|\d+", body))
    if len(values) != 256 or any(not 0 <= value <= 255 for value in values):
        raise ValueError(f"{name} must contain exactly 256 byte values")
    return values


def load_wrt_tables(source_path: Path) -> tuple[tuple[int, ...], tuple[int, ...]]:
    source = source_path.read_text(errors="strict")
    return (
        parse_unsigned_char_array(source, "wrt_2b"),
        parse_unsigned_char_array(source, "wrt_3b"),
    )


@dataclass
class MxxState:
    wrt_2b: tuple[int, ...]
    wrt_3b: tuple[int, ...]
    bit_context: int = 1
    long_bit_context: int = 1
    bpos: int = 0
    b2stream: int = 0
    b3stream: int = 0
    stream2b_r: int = 0
    old_2b_state: int = 0
    old_3b_state: int = 0
    stream3b_r: int = 0
    mxx: int = 0

    def observe(self, bit: int) -> None:
        """Learn one decoded bit and construct the context for the next bit."""

        self.bit_context += self.bit_context + bit
        self.long_bit_context = self.bit_context
        if self.bit_context >= 256:
            self.bit_context -= 256
            self.long_bit_context = 1
            value = self.bit_context
            if value in (ord("R"), ord("P"), ord("]")):
                self.b3stream = (self.b3stream & ~7) + 3
            elif value == ord("M"):
                self.b3stream = (self.b3stream & ~7) + 4

            next_2b = self.wrt_2b[value]
            self.b2stream = (self.b2stream * 4 + next_2b) & MASK64
            next_3b = self.wrt_3b[value]
            self.b3stream = (self.b3stream * 8 + next_3b) & MASK64
            if self.old_3b_state != next_3b:
                self.stream3b_r = (self.stream3b_r * 8 + next_3b) & MASK64
                self.old_3b_state = next_3b
            if value in (10, ord(")")):
                self.b3stream = (self.b3stream << 6) & MASK64
            if value == ord("Q"):
                self.b3stream = (
                    self.b3stream * 8 + self.wrt_3b[value]
                ) & MASK64
            if self.old_2b_state != next_2b:
                self.stream2b_r = (self.stream2b_r * 4 + next_2b) & MASK64
                self.old_2b_state = next_2b

        self.bpos = (self.bpos + 1) & 7
        if self.bpos == 0:
            self.mxx = (self.stream2b_r & 63) * 8 + (self.b3stream & 7)
        elif self.bpos > 3:
            partial = (self.long_bit_context << (8 - self.bpos)) & 255
            self.mxx = (
                ((self.b2stream << 2) & 63)
                + self.wrt_2b[partial] * 8
                + (self.b3stream & 7)
            )
        else:
            self.mxx = (self.stream2b_r & 63) * 8 + (self.b3stream & 7)


def reconstruct_mxx(
    truth_bytes: bytes,
    wrt_2b: tuple[int, ...],
    wrt_3b: tuple[int, ...],
    *,
    pretrained_bytes: bytes = b"",
) -> tuple[np.ndarray, np.ndarray]:
    """Return the exact pre-bit mxx and bpos streams."""

    contexts = np.empty(len(truth_bytes) * 8, dtype=np.uint16)
    bit_positions = np.empty(len(truth_bytes) * 8, dtype=np.uint8)
    state = MxxState(wrt_2b=wrt_2b, wrt_3b=wrt_3b)
    for value in pretrained_bytes:
        for shift in range(7, -1, -1):
            state.observe((value >> shift) & 1)
    row = 0
    for value in truth_bytes:
        for shift in range(7, -1, -1):
            contexts[row] = state.mxx
            bit_positions[row] = state.bpos
            state.observe((value >> shift) & 1)
            row += 1
    return contexts, bit_positions


def signed_round_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    if numerator >= 0:
        return (numerator + denominator // 2) // denominator
    return -((-numerator + denominator // 2) // denominator)


def context_ids(
    scheme: str, mxx: np.ndarray, bit_positions: np.ndarray
) -> tuple[np.ndarray, int]:
    if scheme == "global":
        return np.zeros(len(mxx), dtype=np.uint16), 1
    if scheme == "bitpos":
        return bit_positions.astype(np.uint16, copy=False), 8
    if scheme == "mxx":
        return mxx, int(mxx.max(initial=0)) + 1
    if scheme == "mxx_bitpos":
        values = mxx.astype(np.uint32) * 8 + bit_positions
        return values, int(values.max(initial=0)) + 1
    raise ValueError(f"unknown context scheme: {scheme}")


class OnlineCalibrator:
    def __init__(self, config: CalibrationConfig, context_count: int) -> None:
        if config.context_scheme not in ALL_SCHEMES:
            raise ValueError("invalid calibration context scheme")
        if config.estimator not in {"mean", "ema"}:
            raise ValueError("estimator must be mean or ema")
        if config.probability_buckets < 1 or config.parameter < 1:
            raise ValueError("bucket and estimator parameters must be positive")
        if not 0 < config.strength_ppm <= PPM:
            raise ValueError("strength must be within 1..1000000")
        self.config = config
        size = context_count * config.probability_buckets
        self.counts = np.zeros(size, dtype=np.uint32)
        self.residuals = np.zeros(size, dtype=np.int64)

    def key(self, context: int, base_p1: int) -> int:
        bucket = min(
            self.config.probability_buckets - 1,
            (base_p1 * self.config.probability_buckets) >> 16,
        )
        return context * self.config.probability_buckets + bucket

    def predict(self, context: int, base_p1: int) -> int:
        key = self.key(context, base_p1)
        observations = int(self.counts[key])
        if observations < self.config.minimum_observations:
            return base_p1
        if self.config.estimator == "mean":
            correction = signed_round_div(
                int(self.residuals[key]), observations + self.config.parameter
            )
        else:
            correction = int(self.residuals[key])
        correction = signed_round_div(
            correction * self.config.strength_ppm, PPM
        )
        return min(PROBABILITY_TOTAL - 1, max(1, base_p1 + correction))

    def update(self, context: int, base_p1: int, truth: int) -> None:
        key = self.key(context, base_p1)
        target_residual = truth * PROBABILITY_TOTAL - base_p1
        if self.config.estimator == "mean":
            self.residuals[key] += target_residual
        else:
            current = int(self.residuals[key])
            self.residuals[key] = current + signed_round_div(
                target_residual - current, 1 << self.config.parameter
            )
        if self.counts[key] != np.iinfo(np.uint32).max:
            self.counts[key] += 1

    def predict_then_update(self, context: int, base_p1: int, truth: int) -> int:
        prediction = self.predict(context, base_p1)
        self.update(context, base_p1, truth)
        return prediction


def split_gain(
    gains_qbits: tuple[int, int, int],
    boundaries: tuple[int, int, int],
    raw_scope_bytes: int,
) -> dict[str, Any]:
    labels = ("train", "dev", "holdout")
    starts = (0, boundaries[0], boundaries[1])
    ends = (boundaries[0], boundaries[1], boundaries[2])
    return {
        label: {
            "start_row": start,
            "end_row": end,
            "gain_qbits": int(gain),
            "estimated_saved_bytes": gain / QBITS_PER_BYTE,
            "estimated_saved_bytes_per_1m_raw": (
                gain / QBITS_PER_BYTE * 1_000_000 / raw_scope_bytes
            ),
        }
        for label, start, end, gain in zip(
            labels, starts, ends, gains_qbits, strict=True
        )
    }


def evaluate_config(
    config: CalibrationConfig,
    base: np.ndarray,
    truth: np.ndarray,
    contexts: np.ndarray,
    dev_start: int,
    holdout_start: int,
    loss0: np.ndarray,
    loss1: np.ndarray,
) -> tuple[int, int]:
    ids, context_count = context_ids(config.context_scheme, contexts[0], contexts[1])
    state = OnlineCalibrator(config, context_count)
    dev_gain = 0
    for row in range(holdout_start):
        base_p1 = int(base[row])
        bit = int(truth[row])
        candidate_p1 = state.predict_then_update(int(ids[row]), base_p1, bit)
        if row >= dev_start:
            table = loss1 if bit else loss0
            dev_gain += int(table[base_p1]) - int(table[candidate_p1])
    return dev_gain, int(np.count_nonzero(state.counts))


def replay_selected(
    config: CalibrationConfig,
    base: np.ndarray,
    truth: np.ndarray,
    contexts: tuple[np.ndarray, np.ndarray],
    dev_start: int,
    holdout_start: int,
    loss0: np.ndarray,
    loss1: np.ndarray,
) -> tuple[np.ndarray, tuple[int, int, int], int]:
    ids, context_count = context_ids(config.context_scheme, contexts[0], contexts[1])
    state = OnlineCalibrator(config, context_count)
    candidate = np.empty(len(base), dtype=np.uint16)
    gains = [0, 0, 0]
    for row in range(len(base)):
        base_p1 = int(base[row])
        bit = int(truth[row])
        candidate_p1 = state.predict_then_update(int(ids[row]), base_p1, bit)
        candidate[row] = candidate_p1
        split = 0 if row < dev_start else 1 if row < holdout_start else 2
        table = loss1 if bit else loss0
        gains[split] += int(table[base_p1]) - int(table[candidate_p1])
    return candidate, tuple(gains), int(np.count_nonzero(state.counts))


def write_p1(path: Path, magic: bytes, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as target:
        target.write(magic)
        target.write(struct.pack("<Q", len(values)))
        target.write(np.asarray(values, dtype="<u2").tobytes())
    os.replace(temporary, path)


def normalized_bytes(saved_bytes: int, raw_scope_bytes: int) -> float:
    return saved_bytes * 1_000_000 / raw_scope_bytes


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not 0 < args.dev_start_ppm < args.holdout_start_ppm < PPM:
        raise ValueError("split boundaries must be ordered")
    if args.raw_scope_bytes < 1 or args.provisional_code_bytes < 0:
        raise ValueError("scope and code accounting are invalid")
    if args.remaining_debt_bytes_per_1m < 0:
        raise ValueError("remaining debt cannot be negative")

    magic, rows = read_p1_header(args.base_p1)
    stored = args.wrt_store.read_bytes()
    if len(stored) < 5 or (len(stored) - 5) * 8 != rows:
        raise ValueError("WRT store and base P1 rows do not align")
    wrt_2b, wrt_3b = load_wrt_tables(args.fx2_source)
    dictionary = args.dictionary.read_bytes()
    dictionary_size = len(dictionary)
    dictionary_header = bytes(
        (
            0,
            (dictionary_size >> 24) & 255,
            (dictionary_size >> 16) & 255,
            (dictionary_size >> 8) & 255,
            dictionary_size & 255,
        )
    )
    normalized_dictionary = dictionary.replace(b"\n", b" ")
    pretrained_bytes = dictionary_header + normalized_dictionary
    mxx, bit_positions = reconstruct_mxx(
        stored[5:],
        wrt_2b,
        wrt_3b,
        pretrained_bytes=pretrained_bytes,
    )
    if len(mxx) != rows:
        raise AssertionError("mxx reconstruction row count changed")

    base = np.memmap(
        args.base_p1,
        dtype="<u2",
        mode="r",
        offset=P1_HEADER_BYTES,
        shape=(rows,),
    )
    truth = np.unpackbits(
        np.frombuffer(stored, dtype=np.uint8, offset=5), bitorder="big"
    )
    dev_start = rows * args.dev_start_ppm // PPM
    holdout_start = rows * args.holdout_start_ppm // PPM
    loss0, loss1 = qbit_tables()
    contexts = (mxx, bit_positions)

    screen_rows: list[dict[str, Any]] = []
    for config in DEFAULT_CONFIGS:
        dev_gain, populated = evaluate_config(
            config,
            base,
            truth,
            contexts,
            dev_start,
            holdout_start,
            loss0,
            loss1,
        )
        screen_rows.append(
            {
                "config": asdict(config),
                "is_control": config.is_control,
                "dev_gain_qbits": dev_gain,
                "dev_estimated_saved_bytes": dev_gain / QBITS_PER_BYTE,
                "dev_estimated_saved_bytes_per_1m_raw": (
                    dev_gain / QBITS_PER_BYTE * 1_000_000 / args.raw_scope_bytes
                ),
                "populated_cells": populated,
            }
        )

    candidate_rows = [row for row in screen_rows if not row["is_control"]]
    selected_row = max(
        candidate_rows,
        key=lambda row: (row["dev_gain_qbits"], -len(row["config"]["name"])),
    )
    selected = next(
        config
        for config in DEFAULT_CONFIGS
        if config.name == selected_row["config"]["name"]
    )
    best_control = max(screen_rows, key=lambda row: row["dev_gain_qbits"] if row["is_control"] else -(1 << 62))

    candidate, gains, populated = replay_selected(
        selected,
        base,
        truth,
        contexts,
        dev_start,
        holdout_start,
        loss0,
        loss1,
    )
    exact_full, replayed_base_payload, candidate_payload = exact_replay(
        truth, base, candidate
    )
    exact_holdout, _, _ = exact_replay(
        truth[holdout_start:], base[holdout_start:], candidate[holdout_start:]
    )
    block_audit = exact_block_audit(
        truth[holdout_start:],
        base[holdout_start:],
        candidate[holdout_start:],
        args.holdout_blocks,
    )
    base_archive = args.base_archive.read_bytes()
    header_bytes = cmix_archive_header_bytes(base_archive)
    base_payload = base_archive[header_bytes:]
    base_identity = replayed_base_payload == base_payload

    if args.candidate_payload:
        args.candidate_payload.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_payload.write_bytes(candidate_payload)
    if args.candidate_p1:
        write_p1(args.candidate_p1, magic, candidate)

    full_rate = normalized_bytes(exact_full["saved_bytes"], args.raw_scope_bytes)
    holdout_raw_bytes = args.raw_scope_bytes * (rows - holdout_start) / rows
    holdout_rate = normalized_bytes(
        exact_holdout["saved_bytes"], max(1, round(holdout_raw_bytes))
    )
    code_rate = args.provisional_code_bytes * 1_000_000 / 1_000_000_000
    required_rate = args.remaining_debt_bytes_per_1m + code_rate
    control_rate = best_control["dev_estimated_saved_bytes_per_1m_raw"]

    validations = {
        "base_payload_byte_identical": base_identity,
        "selected_from_development_only": True,
        "holdout_read_after_selection": True,
        "predict_before_current_truth_update": True,
        "mxx_rebuilt_from_decoded_prefix_only": True,
        "matched_control_present": True,
        "selected_beats_best_control_on_dev": (
            selected_row["dev_estimated_saved_bytes_per_1m_raw"] > control_rate
        ),
    }
    economic_pass = (
        base_identity
        and full_rate >= required_rate
        and exact_holdout["saved_bytes"] > 0
        and block_audit["regressing_blocks"] == 0
        and validations["selected_beats_best_control_on_dev"]
    )
    if not base_identity:
        verdict = "invalid_base_payload_identity"
    elif economic_pass:
        verdict = "causal_mxx_sse_pass_requires_native_integration"
    else:
        verdict = "negative_or_insufficient_retire_mxx_sse_family"

    return {
        "schema": "endpoint428-mxx-sse-shadow-v1",
        "hypothesis": (
            "A small online residual calibrator keyed by FX2's decoder-rebuilt "
            "mxx and endpoint428 probability bucket retains layer0 mixer 5's "
            "target-closing complement without inheriting its raw model universe."
        ),
        "baseline": {
            "name": "cmix21_lstm200_fx2lite428_context_recovery_10m_v1",
            "counted_forecast_bytes": 109_557_404,
            "remaining_target_debt_bytes": 57_404,
            "base_p1": artifact(args.base_p1),
            "base_archive": artifact(args.base_archive),
            "archive_header_bytes": header_bytes,
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "raw_scope_bytes": args.raw_scope_bytes,
            "rows": rows,
        },
        "source_contract": {
            "fx2_source": artifact(args.fx2_source),
            "wrt_2b_sha256": sha256_bytes(bytes(wrt_2b)),
            "wrt_3b_sha256": sha256_bytes(bytes(wrt_3b)),
            "structural_sidecar_assumed": 0,
            "pretraining_schedule": (
                "five-byte big-endian dictionary length followed by dictionary "
                "bytes with newline replaced by space"
            ),
            "pretrained_bytes": len(pretrained_bytes),
            "mxx_context_min": int(mxx.min(initial=0)),
            "mxx_context_max": int(mxx.max(initial=0)),
            "mxx_distinct_contexts": int(len(np.unique(mxx))),
        },
        "split": {
            "dev_start_row": dev_start,
            "holdout_start_row": holdout_start,
            "dev_start_ppm": args.dev_start_ppm,
            "holdout_start_ppm": args.holdout_start_ppm,
        },
        "economics": {
            "target_score_bytes": 109_500_000,
            "remaining_debt_bytes_per_1m": args.remaining_debt_bytes_per_1m,
            "provisional_code_bytes": args.provisional_code_bytes,
            "provisional_code_bytes_per_1m": code_rate,
            "required_saved_bytes_per_1m": required_rate,
            "full_exact_saved_bytes_per_1m": full_rate,
            "holdout_exact_saved_bytes_per_1m": holdout_rate,
            "margin_over_required_bytes_per_1m": full_rate - required_rate,
        },
        "screen": sorted(
            screen_rows,
            key=lambda row: row["dev_gain_qbits"],
            reverse=True,
        ),
        "selection": {
            "selected": selected_row,
            "best_control": best_control,
            "selected_replay_populated_cells": populated,
        },
        "selected_split_gain": split_gain(
            gains, (dev_start, holdout_start, rows), args.raw_scope_bytes
        ),
        "exact_replay": {
            "full": exact_full,
            "holdout": exact_holdout,
            "holdout_block_audit": block_audit,
            "base_payload_sha256": sha256_bytes(replayed_base_payload),
            "candidate_payload_sha256": sha256_bytes(candidate_payload),
        },
        "validations": validations,
        "verdict": verdict,
        "promotion_authorized": False,
        "claim_boundary": (
            "Development-selected causal exact trace replay at the opening 1M "
            "scope. A passing result still requires native integration, counted "
            "source compression, disjoint scopes, exact larger replay, roundtrip, "
            "determinism, RSS/runtime compliance, and full 1G official accounting."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--fx2-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path)
    parser.add_argument("--candidate-p1", type=Path)
    parser.add_argument("--dev-start-ppm", type=int, default=600_000)
    parser.add_argument("--holdout-start-ppm", type=int, default=800_000)
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument(
        "--remaining-debt-bytes-per-1m", type=float, default=57.404
    )
    parser.add_argument("--provisional-code-bytes", type=int, default=12_000)
    args = parser.parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(receipt["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
