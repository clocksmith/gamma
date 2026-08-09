#!/usr/bin/env python3
"""Price a causal NNCP dictionary-boundary class marginal."""

from __future__ import annotations

from collections import Counter, deque
import hashlib
import json
import lzma
import math
from pathlib import Path
import resource
import struct

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_dictionary_boundary_class_marginal_qm0_v1"
TRACE = Path(
    "/home/x/enwiki9-nonproof/results/nncp_teacher_causal_trace_10k_v1/"
    "teacher_trace.bin"
)
DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/results/nncp_preprocess_opening_1m_v1/"
    "dictionary.bin"
)
SYMBOLS = Path(
    "/home/x/enwiki9-nonproof/results/nncp_preprocess_opening_1m_v1/"
    "preprocessed.bin"
)
TEACHER_RECEIPT = ROOT / "results/nncp_teacher_causal_trace_10k_v1/receipt.json"
PLAN = ROOT / "docs/nncp_dictionary_boundary_class_marginal_qm0_plan.md"

TRACE_MAGIC = b"NNTCHD2\0"
TRACE_HEADER = struct.Struct("<8sQ")
TRACE_ROW = struct.Struct("<QQQQIHHI")
EXPECTED_ROWS = 10_000
EXPECTED_DICTIONARY_ENTRIES = 329
EXPECTED_VOCABULARY = 336
WINDOW = 32
CLASS_CONCENTRATION = 16.0
BASE_MIXTURE_WEIGHT = 16.0
CLASS_MIXTURE_WEIGHT = 1.0
ROTATION = 37
GAIN_GATE_BYTES = 250.0
CONTROL_MARGIN_BYTES = 100.0
SOURCE_LIMIT_BYTES = 65_536
NORMALIZATION_TOLERANCE = 2e-5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_dictionary(path: Path) -> list[bytes]:
    data = path.read_bytes()
    words: list[bytes] = []
    current = bytearray()
    index = 0
    while index < len(data):
        value = data[index]
        index += 1
        if value == 10:
            if current:
                words.append(bytes(current))
            current.clear()
            continue
        if value == 92:
            if index >= len(data):
                raise ValueError("truncated dictionary escape")
            value = data[index]
            index += 1
            if value == ord("n"):
                value = 10
            elif value != 92:
                raise ValueError("invalid dictionary escape")
        current.append(value)
    if current:
        words.append(bytes(current))
    return words


def byte_category(value: int) -> int:
    if 65 <= value <= 90 or 97 <= value <= 122:
        return 0
    if 48 <= value <= 57:
        return 1
    if value in (32, 9, 10, 13):
        return 2
    if value in b"<>/={}[]|:&;!?.,_-+*#":
        return 3
    if value < 32 or value >= 127:
        return 4
    return 5


def length_bucket(length: int) -> int:
    return min(7, (length - 1).bit_length())


def class_map(words: list[bytes]) -> tuple[np.ndarray, int]:
    identifiers: dict[tuple[int, int, int], int] = {}
    classes: list[int] = []
    for word in words:
        signature = (
            byte_category(word[0]),
            byte_category(word[-1]),
            length_bucket(len(word)),
        )
        if signature not in identifiers:
            identifiers[signature] = len(identifiers)
        classes.append(identifiers[signature])
    structural_count = len(identifiers)
    while len(classes) < EXPECTED_VOCABULARY:
        classes.append(structural_count + len(classes) - len(words))
    return np.asarray(classes, dtype=np.int32), structural_count


def load_truth() -> np.ndarray:
    return np.asarray(
        np.memmap(SYMBOLS, mode="r", dtype=">u2")[:EXPECTED_ROWS],
        dtype=np.uint16,
    )


def evaluate(classes: np.ndarray, truth: np.ndarray) -> dict[str, object]:
    rotated = np.roll(classes, ROTATION)
    histories: dict[int, deque[int]] = {}
    counts: dict[int, Counter[tuple[str, int]]] = {}
    arms = ("base", "class_direct", "rotated_direct", "class_mix", "rotated_mix")
    losses = {arm: 0.0 for arm in arms}
    third_losses = {arm: [0.0, 0.0, 0.0] for arm in arms}
    maximum_normalization_error = 0.0
    prior_after: int | None = None

    with TRACE.open("rb") as source:
        header = source.read(TRACE_HEADER.size)
        if len(header) != TRACE_HEADER.size:
            raise ValueError("truncated trace header")
        magic, row_count = TRACE_HEADER.unpack(header)
        if magic != TRACE_MAGIC or row_count != EXPECTED_ROWS:
            raise ValueError("unexpected trace identity")

        for execution in range(row_count):
            fixed_raw = source.read(TRACE_ROW.size)
            if len(fixed_raw) != TRACE_ROW.size:
                raise ValueError("truncated trace row")
            (
                original,
                execution_row,
                before,
                after,
                _local,
                stream,
                symbol,
                vocabulary,
            ) = TRACE_ROW.unpack(fixed_raw)
            if execution_row != execution or original != execution:
                raise ValueError("trace order differs from frozen population")
            if vocabulary != EXPECTED_VOCABULARY or int(truth[original]) != symbol:
                raise ValueError("trace truth or vocabulary mismatch")
            if prior_after is not None and before != prior_after:
                raise ValueError("trace coder counts are discontinuous")
            if after < before:
                raise ValueError("trace coder count decreased")
            prior_after = after

            distribution_raw = source.read(4 * vocabulary)
            if len(distribution_raw) != 4 * vocabulary:
                raise ValueError("truncated trace distribution")
            distribution = np.frombuffer(distribution_raw, dtype="<f4").astype(np.float64)
            if not np.all(np.isfinite(distribution)) or not np.all(distribution > 0.0):
                raise ValueError("invalid teacher distribution")
            normalization_error = abs(math.fsum(distribution) - 1.0)
            maximum_normalization_error = max(
                maximum_normalization_error, normalization_error
            )
            if normalization_error > NORMALIZATION_TOLERANCE:
                raise ValueError("teacher distribution is not normalized")
            distribution /= math.fsum(distribution)

            history = histories.setdefault(stream, deque())
            count = counts.setdefault(stream, Counter())
            population = len(history)
            base_probability = float(distribution[symbol])

            structural_mass = np.bincount(
                classes,
                weights=distribution,
                minlength=int(classes.max()) + 1,
            )
            structural_class = int(classes[symbol])
            class_probability = (
                (
                    count[("class", structural_class)]
                    + CLASS_CONCENTRATION * structural_mass[structural_class]
                )
                / (population + CLASS_CONCENTRATION)
                * base_probability
                / structural_mass[structural_class]
            )

            rotated_mass = np.bincount(
                rotated,
                weights=distribution,
                minlength=int(rotated.max()) + 1,
            )
            rotated_class = int(rotated[symbol])
            rotated_probability = (
                (
                    count[("rotated", rotated_class)]
                    + CLASS_CONCENTRATION * rotated_mass[rotated_class]
                )
                / (population + CLASS_CONCENTRATION)
                * base_probability
                / rotated_mass[rotated_class]
            )

            class_mix = (
                BASE_MIXTURE_WEIGHT * base_probability
                + CLASS_MIXTURE_WEIGHT * class_probability
            ) / (BASE_MIXTURE_WEIGHT + CLASS_MIXTURE_WEIGHT)
            rotated_mix = (
                BASE_MIXTURE_WEIGHT * base_probability
                + CLASS_MIXTURE_WEIGHT * rotated_probability
            ) / (BASE_MIXTURE_WEIGHT + CLASS_MIXTURE_WEIGHT)
            probabilities = {
                "base": base_probability,
                "class_direct": class_probability,
                "rotated_direct": rotated_probability,
                "class_mix": class_mix,
                "rotated_mix": rotated_mix,
            }
            third = min(2, original * 3 // row_count)
            for arm, probability in probabilities.items():
                if not 0.0 < probability <= 1.0:
                    raise ValueError(f"illegal {arm} probability")
                loss = -math.log2(probability)
                losses[arm] += loss
                third_losses[arm][third] += loss

            history.append(symbol)
            count[("class", structural_class)] += 1
            count[("rotated", rotated_class)] += 1
            if len(history) > WINDOW:
                old = history.popleft()
                count[("class", int(classes[old]))] -= 1
                count[("rotated", int(rotated[old]))] -= 1

        if source.read(1):
            raise ValueError("trailing trace bytes")

    gain = (losses["base"] - losses["class_mix"]) / 8.0
    rotated_gain = (losses["base"] - losses["rotated_mix"]) / 8.0
    third_gains = [
        (third_losses["base"][index] - third_losses["class_mix"][index]) / 8.0
        for index in range(3)
    ]
    return {
        "loss_bits": losses,
        "gain_bytes": gain,
        "rotated_control_gain_bytes": rotated_gain,
        "specificity_margin_bytes": gain - rotated_gain,
        "chronological_third_gain_bytes": third_gains,
        "maximum_normalization_error": maximum_normalization_error,
        "final_teacher_coder_bits": prior_after,
    }


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output: {output_dir}")

    teacher_receipt = json.loads(TEACHER_RECEIPT.read_text())
    if (
        teacher_receipt.get("evidence_level")
        != "archive_neutral_full_distribution_teacher_zero_credit"
        or teacher_receipt.get("proof", {}).get("archive_identity") is not True
        or teacher_receipt.get("proof", {}).get("rows") != EXPECTED_ROWS
    ):
        raise ValueError("teacher receipt does not bind the frozen trace")
    expected_trace_hash = teacher_receipt["artifacts"]["teacher_trace"]["sha256"]
    if sha256_file(TRACE) != expected_trace_hash:
        raise ValueError("teacher trace hash mismatch")

    words = parse_dictionary(DICTIONARY)
    if len(words) != EXPECTED_DICTIONARY_ENTRIES:
        raise ValueError("unexpected dictionary population")
    classes, structural_count = class_map(words)
    truth = load_truth()
    evaluation = evaluate(classes, truth)

    proposal_paths = list(
        (ROOT / "operations/adaptive/proposals/developed").glob(
            f"*_{CANDIDATE_ID}.json"
        )
    )
    if len(proposal_paths) != 1:
        raise ValueError("candidate proposal provenance is ambiguous")
    source_paths = (
        Path(__file__),
        PLAN,
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        proposal_paths[0],
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)

    conditions = {
        "gain_at_least_250_bytes": evaluation["gain_bytes"] >= GAIN_GATE_BYTES,
        "all_chronological_thirds_positive": all(
            value > 0.0 for value in evaluation["chronological_third_gain_bytes"]
        ),
        "specificity_margin_at_least_100_bytes": (
            evaluation["specificity_margin_bytes"] >= CONTROL_MARGIN_BYTES
        ),
        "source_package_at_most_65536_bytes": len(source_package)
        <= SOURCE_LIMIT_BYTES,
    }
    authorized = all(conditions.values())

    output_dir.mkdir(parents=True)
    source_path = output_dir / "diagnostic_source_package.lzma"
    source_path.write_bytes(source_package)
    decision = {
        "schema": "enwiki9_nncp_dictionary_boundary_class_marginal_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": (
            "AUTHORIZED_NATIVE_CLASS_MARGINAL"
            if authorized
            else "RETIRED_DICTIONARY_BOUNDARY_CLASS_MARGINAL"
        ),
        "epistemic_tier": "archive_neutral_full_distribution_ideal_screen_zero_score_credit",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Ideal codelength over an archive-neutral external NNCP distribution "
            "trace. No finite arithmetic stream, native decoder, package forecast, "
            "eligibility result, or Hutter score exists."
        ),
        "model": {
            "dictionary_entries": len(words),
            "rounded_vocabulary": EXPECTED_VOCABULARY,
            "structural_classes": structural_count,
            "dummy_classes": EXPECTED_VOCABULARY - len(words),
            "window": WINDOW,
            "class_concentration": CLASS_CONCENTRATION,
            "base_mixture_weight": BASE_MIXTURE_WEIGHT,
            "class_mixture_weight": CLASS_MIXTURE_WEIGHT,
            "control_rotation": ROTATION,
        },
        "population": {
            "symbols": EXPECTED_ROWS,
            "full_distribution_vocabulary": EXPECTED_VOCABULARY,
        },
        "evaluation": evaluation,
        "conditions": conditions,
        "failed_conditions": [name for name, passed in conditions.items() if not passed],
        "next_action": (
            "materialize one finite native same-object class-marginal gate"
            if authorized
            else "do not build a native dictionary-class descendant"
        ),
        "proof": {
            "target_class_not_observed_before_symbol": True,
            "full_distribution_class_mass_normalized": True,
            "counts_decoder_rebuilt": True,
            "counts_updated_after_truth": True,
            "trace_archive_neutral": True,
            "trace_truth_exact": True,
        },
        "artifacts": {
            "teacher_trace": {
                "path": str(TRACE),
                "bytes": TRACE.stat().st_size,
                "sha256": sha256_file(TRACE),
            },
            "dictionary": {
                "path": str(DICTIONARY),
                "bytes": DICTIONARY.stat().st_size,
                "sha256": sha256_file(DICTIONARY),
            },
            "symbols": {
                "path": str(SYMBOLS),
                "bytes": SYMBOLS.stat().st_size,
                "sha256": sha256_file(SYMBOLS),
            },
            "diagnostic_source_package": {
                "path": str(source_path.relative_to(ROOT)),
                "bytes": len(source_package),
                "sha256": sha256_file(source_path),
            },
        },
        "resource": {
            "max_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
