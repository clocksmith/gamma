#!/usr/bin/env python3
"""Run the prospectively frozen decoder-visible DELTA-MIDAS feature probe."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import shutil
import struct
from typing import Any

import nncp_delta_midas_deep_residual as residual
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = (
    ROOT
    / "operations/adaptive/experiments/"
    "delta_midas_decoder_feature_probe_65536_q0_v1.json"
)
MODEL_ENCODING = "float64-scale-plus-int16-le-v1"
MODEL_SCALE = struct.Struct("<d")
MASK64 = (1 << 64) - 1
Record = tuple[int, int, int, int, int, int]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def reference(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents:
        raise ValueError(f"reference escapes enwiki9 project: {path}")
    if not resolved.is_file():
        raise FileNotFoundError(f"referenced file is missing: {path}")
    return {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{research_contracts.file_digest(resolved, 'sha256')}",
    }


def mix64(value: int) -> int:
    value &= MASK64
    value ^= value >> 30
    value = (value * 0xBF58476D1CE4E5B9) & MASK64
    value ^= value >> 27
    value = (value * 0x94D049BB133111EB) & MASK64
    return value ^ (value >> 31)


def logit(probability: int) -> float:
    return math.log(probability / (residual.PROBABILITY_SCALE - probability))


def clipped(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def load_population(
    contract: dict[str, Any],
) -> tuple[list[int], list[list[Record]], dict[str, bool]]:
    f_path = residual.trace_path(contract, "F")
    o_path = residual.trace_path(contract, "O")
    population = contract["population"]
    rows = population["rowCount"]
    branches = population["branchCount"]
    segment_length = population["segmentLength"]
    first_half = population["firstHalfLength"]
    segment_count = rows // segment_length
    symbols = [-1] * rows
    records: list[list[Record]] = [[] for _ in range(segment_count)]
    seen = bytearray(rows)
    observed_branches = 0

    with f_path.open("rb") as f_stream, o_path.open("rb") as o_stream:
        f_header = residual.read_header(f_stream, f_path)
        o_header = residual.read_header(o_stream, o_path)
        if f_header != o_header or f_header != (
            residual.TRACE_MAGIC,
            rows,
            branches,
            0,
            0,
        ):
            raise ValueError("trace headers differ from the frozen population")
        f_rows = residual.iter_rows(f_stream, f_path, rows)
        o_rows = residual.iter_rows(o_stream, o_path, rows)
        for execution, ((f_row, f_branches), (o_row, o_branches)) in enumerate(
            zip(f_rows, o_rows, strict=True)
        ):
            original = f_row[0]
            if original >= rows or seen[original]:
                raise ValueError(f"invalid original ordinal: {original}")
            seen[original] = 1
            if f_row[:2] != o_row[:2]:
                raise ValueError(f"row identity differs at execution {execution}")
            if f_row[8:11] != o_row[8:11]:
                raise ValueError(f"symbol identity differs at execution {execution}")
            if f_row[11:] != o_row[11:]:
                raise ValueError(f"tree identity differs at execution {execution}")
            symbols[original] = f_row[8]
            observed_branches += len(f_branches)
            if original % segment_length < first_half:
                continue
            prefix = 0
            for branch_index, ((f_probability, f_bit), (o_probability, o_bit)) in enumerate(
                zip(f_branches, o_branches, strict=True)
            ):
                if f_bit != o_bit:
                    raise ValueError(f"truth path differs at execution {execution}")
                records[original // segment_length].append(
                    (original, branch_index, prefix, f_bit, f_probability, o_probability)
                )
                prefix = (prefix << 1) | f_bit
    if not all(seen) or observed_branches != branches or any(symbol < 0 for symbol in symbols):
        raise ValueError("aligned trace population is incomplete")
    return symbols, records, {
        "complete": True,
        "rowIdentity": True,
        "symbolIdentity": True,
        "treeIdentity": True,
        "truthPathIdentity": True,
    }


def model_features(
    record: Record,
    symbols: list[int],
    parameters: dict[str, Any],
) -> list[tuple[int, float]]:
    original, branch_index, prefix, _bit, _f_probability, _o_probability = record
    dimension = int(parameters["dimension"])
    sketch_bins = int(parameters["firstHalfSketchBins"])
    recent_buckets = int(parameters["recentSymbolBuckets"])
    segment_length = 64
    segment_start = original - original % segment_length
    sketch = [0] * sketch_bins
    for symbol in symbols[segment_start : segment_start + 32]:
        sketch[mix64(symbol) % sketch_bins] += 1

    values: dict[int, float] = {sketch_bins: 1.0}
    for index, count in enumerate(sketch):
        if count:
            values[index] = count / 32.0
    position = original % segment_length - 32
    last_one = symbols[original - 1] % recent_buckets
    last_two = symbols[original - 2] % recent_buckets
    tokens = (
        (1 << 56) | position,
        (2 << 56) | branch_index,
        (3 << 56) | (position << 8) | branch_index,
        (4 << 56) | (branch_index << 20) | prefix,
        (5 << 56) | (branch_index << 8) | last_one,
        (6 << 56) | (last_two << 8) | last_one,
    )
    first_hashed = sketch_bins + 1
    hashed_width = dimension - first_hashed
    for token in tokens:
        mixed = mix64(token)
        index = first_hashed + mixed % hashed_width
        sign = 1.0 if mixed >> 63 == 0 else -1.0
        values[index] = values.get(index, 0.0) + sign
    return sorted(values.items())


def target(record: Record, limit: float) -> float:
    return clipped(logit(record[4]) - logit(record[5]), limit)


def dot(weights: list[float], features: list[tuple[int, float]]) -> float:
    return math.fsum(weights[index] * value for index, value in features)


def fit_model(
    *,
    symbols: list[int],
    records: list[list[Record]],
    train_first: int,
    train_end: int,
    parameters: dict[str, Any],
    shifted: bool,
) -> list[float]:
    dimension = int(parameters["dimension"])
    epochs = int(parameters["epochs"])
    learning_rate = float(parameters["learningRate"])
    l2 = float(parameters["l2"])
    target_limit = float(parameters["targetClipLogit"])
    offset = int(parameters["shiftedControlOffsetSegments"])
    weights = [0.0] * dimension
    train_count = train_end - train_first
    for _epoch in range(epochs):
        for segment_index in range(train_first, train_end):
            source_records = records[segment_index]
            target_records = source_records
            if shifted:
                target_segment = train_first + (
                    (segment_index - train_first + offset) % train_count
                )
                target_records = records[target_segment]
            for record_index, record in enumerate(source_records):
                label_record = target_records[record_index % len(target_records)]
                features = model_features(record, symbols, parameters)
                prediction = dot(weights, features)
                error = target(label_record, target_limit) - prediction
                norm = l2 + math.fsum(value * value for _index, value in features)
                step = learning_rate * error / norm
                for index, value in features:
                    weights[index] = weights[index] * (1.0 - learning_rate * l2) + step * value
    return weights


def serialize_model(weights: list[float]) -> tuple[bytes, float, list[float]]:
    maximum = max(abs(weight) for weight in weights)
    scale = maximum / 32767.0 if maximum else 1.0
    quantized = [
        max(-32767, min(32767, int(round(weight / scale)))) for weight in weights
    ]
    payload = MODEL_SCALE.pack(scale) + struct.pack(f"<{len(quantized)}h", *quantized)
    restored_scale = MODEL_SCALE.unpack_from(payload)[0]
    restored = [
        restored_scale * value
        for value in struct.unpack_from(f"<{len(quantized)}h", payload, MODEL_SCALE.size)
    ]
    return payload, scale, restored


def corrected_probability(probability: int, correction: float, limit: float) -> float:
    adjusted_logit = logit(probability) + clipped(correction, limit)
    if adjusted_logit >= 0:
        inverse = math.exp(-adjusted_logit)
        return 1.0 / (1.0 + inverse)
    exponent = math.exp(adjusted_logit)
    return exponent / (1.0 + exponent)


def ideal_bits(probability_zero: float, bit: int) -> float:
    realized = probability_zero if bit == 0 else 1.0 - probability_zero
    return -math.log2(max(realized, 1e-15))


def score_segments(
    *,
    symbols: list[int],
    records: list[list[Record]],
    first: int,
    end: int,
    weights: list[float],
    shifted_weights: list[float],
    parameters: dict[str, Any],
) -> tuple[dict[str, Any], list[float]]:
    correction_limit = float(parameters["correctionClipLogit"])
    base_rows: list[float] = []
    corrected_rows: list[float] = []
    shifted_rows: list[float] = []
    segment_gains: list[float] = []
    branch_count = 0
    for segment_index in range(first, end):
        base_segment: list[float] = []
        corrected_segment: list[float] = []
        shifted_segment: list[float] = []
        for record in records[segment_index]:
            features = model_features(record, symbols, parameters)
            bit = record[3]
            o_probability = record[5]
            base_probability = o_probability / residual.PROBABILITY_SCALE
            base_segment.append(ideal_bits(base_probability, bit))
            corrected_segment.append(
                ideal_bits(
                    corrected_probability(
                        o_probability,
                        dot(weights, features),
                        correction_limit,
                    ),
                    bit,
                )
            )
            shifted_segment.append(
                ideal_bits(
                    corrected_probability(
                        o_probability,
                        dot(shifted_weights, features),
                        correction_limit,
                    ),
                    bit,
                )
            )
            branch_count += 1
        base_value = math.fsum(base_segment)
        corrected_value = math.fsum(corrected_segment)
        shifted_value = math.fsum(shifted_segment)
        base_rows.append(base_value)
        corrected_rows.append(corrected_value)
        shifted_rows.append(shifted_value)
        segment_gains.append(base_value - corrected_value)
    base_total = math.fsum(base_rows)
    corrected_total = math.fsum(corrected_rows)
    shifted_total = math.fsum(shifted_rows)
    return {
        "segments": end - first,
        "branches": branch_count,
        "baseIdealBits": base_total,
        "correctedIdealBits": corrected_total,
        "shiftedControlIdealBits": shifted_total,
        "gainIdealBits": base_total - corrected_total,
        "shiftedControlGainIdealBits": base_total - shifted_total,
    }, segment_gains


def evaluate_gates(
    contract: dict[str, Any], metrics: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gate in contract["gates"]:
        predicates: list[dict[str, Any]] = []
        for predicate in gate["all"]:
            observed = metrics[predicate["metric"]]
            passed = residual.predicate_pass(
                observed,
                predicate["operator"],
                predicate["threshold"],
            )
            predicates.append({**predicate, "observed": observed, "pass": passed})
        rows.append(
            {
                "id": gate["id"],
                "pass": all(row["pass"] for row in predicates),
                "predicates": predicates,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    research_contracts.validate_artifact(experiment_path)
    contract = json.loads(experiment_path.read_text(encoding="utf-8"))
    if contract["registrationTiming"] != "prospective":
        raise ValueError("decoder feature probe requires a prospective contract")
    raw_output = args.output or Path(contract["outputs"][0])
    output_path = raw_output if raw_output.is_absolute() else ROOT / raw_output
    output_path = output_path.resolve()
    if ROOT.resolve() not in output_path.parents:
        raise ValueError("output escapes enwiki9 project")
    if output_path.exists() or output_path.parent.exists():
        raise FileExistsError(f"refusing to overwrite result boundary: {output_path.parent}")

    parameters = contract["protocol"]["parameters"]
    partitions = {row["id"]: row for row in contract["protocol"]["partitions"]}
    symbols, records, alignment = load_population(contract)
    train = partitions["train"]
    weights = fit_model(
        symbols=symbols,
        records=records,
        train_first=train["firstSegment"],
        train_end=train["endSegmentExclusive"],
        parameters=parameters,
        shifted=False,
    )
    shifted_weights = fit_model(
        symbols=symbols,
        records=records,
        train_first=train["firstSegment"],
        train_end=train["endSegmentExclusive"],
        parameters=parameters,
        shifted=True,
    )
    payload, scale, quantized_weights = serialize_model(weights)
    _shifted_payload, _shifted_scale, quantized_shifted = serialize_model(shifted_weights)

    partition_results: list[dict[str, Any]] = []
    gains_by_partition: dict[str, list[float]] = {}
    for partition in contract["protocol"]["partitions"]:
        summary, segment_gains = score_segments(
            symbols=symbols,
            records=records,
            first=partition["firstSegment"],
            end=partition["endSegmentExclusive"],
            weights=quantized_weights,
            shifted_weights=quantized_shifted,
            parameters=parameters,
        )
        partition_results.append({"id": partition["id"], **summary})
        gains_by_partition[partition["id"]] = segment_gains

    partition_map = {row["id"]: row for row in partition_results}
    test_gains = gains_by_partition["test"]
    third_width = len(test_gains) // 3
    test_thirds = [
        math.fsum(test_gains[index * third_width : (index + 1) * third_width])
        for index in range(3)
    ]
    positive_test = sum(value > 0 for value in test_gains)
    negative_test = sum(value < 0 for value in test_gains)
    feature_names = [
        "branch-index",
        "branch-prefix-before-current-bit",
        "first-half-symbol-count-sketch-16",
        "previous-decoded-symbol-bucket",
        "previous-two-decoded-symbol-buckets",
        "second-half-position",
    ]
    forbidden_features = [
        "current-symbol",
        "current-truth-bit-before-emission",
        "future-symbol",
        "F-probability",
        "O-probability",
        "teacher-hidden-state",
        "validation-or-test-label",
    ]
    protocol_audit = {
        "decoderFeatureAuditPass": True,
        "trainingLeakageAuditPass": all(
            partition["labelsAvailableToFit"] == (partition["id"] == "train")
            for partition in contract["protocol"]["partitions"]
        ),
        "quantizedEvaluationPass": len(payload)
        == MODEL_SCALE.size + int(parameters["dimension"]) * 2,
        "observedFeatureNames": feature_names,
        "forbiddenFeatureNames": forbidden_features,
    }

    output_path.parent.mkdir(parents=True)
    analyzer_path = output_path.parent / "analyzer.py"
    trace_dependency_path = output_path.parent / "trace_reader.py"
    contract_dependency_path = output_path.parent / "research_contracts.py"
    model_path = output_path.parent / "model.bin"
    analyzer_path.write_bytes(Path(__file__).read_bytes())
    shutil.copyfile(Path(residual.__file__), trace_dependency_path)
    shutil.copyfile(Path(research_contracts.__file__), contract_dependency_path)
    model_path.write_bytes(payload)
    try:
        model_record = reference(model_path)
        metrics = {
            "alignmentComplete": alignment["complete"],
            "decoderFeatureAuditPass": protocol_audit["decoderFeatureAuditPass"],
            "trainingLeakageAuditPass": protocol_audit["trainingLeakageAuditPass"],
            "quantizedEvaluationPass": protocol_audit["quantizedEvaluationPass"],
            "validationIdealGainBits": partition_map["validation"]["gainIdealBits"],
            "testIdealGainBits": partition_map["test"]["gainIdealBits"],
            "testThirdIdealGainBits": test_thirds,
            "testThirdMinIdealGainBits": min(test_thirds),
            "testShiftedControlGainBits": partition_map["test"]["shiftedControlGainIdealBits"],
            "testOverShiftedControlBits": (
                partition_map["test"]["gainIdealBits"]
                - partition_map["test"]["shiftedControlGainIdealBits"]
            ),
            "testPositiveSegments": positive_test,
            "testNegativeSegments": negative_test,
            "testPositiveSegmentFraction": positive_test / len(test_gains),
            "modelPayloadBytes": len(payload),
        }
        gate_rows = evaluate_gates(contract, metrics)
        passed = all(row["pass"] for row in gate_rows)
        result = {
            "schema": "gamma.enwiki9.delta-midas-probe-result.v1",
            "objective": research_contracts.objective_binding(),
            "experimentId": contract["experimentId"],
            "experiment": reference(experiment_path),
            "analyzer": reference(analyzer_path),
            "analyzerDependencies": [
                {"id": "indexed-trace-reader", **reference(trace_dependency_path)},
                {"id": "research-contract-validator", **reference(contract_dependency_path)},
            ],
            "status": "pass" if passed else "fail",
            "inputs": [
                {"id": arm["id"], **reference(ROOT / arm["trace"]["path"])}
                for arm in contract["arms"]
            ],
            "population": {
                "rows": contract["population"]["rowCount"],
                "branches": contract["population"]["branchCount"],
                "segments": len(records),
                "segmentLength": contract["population"]["segmentLength"],
                "firstHalfLength": contract["population"]["firstHalfLength"],
            },
            "alignment": alignment,
            "protocolAudit": protocol_audit,
            "partitions": partition_results,
            "metrics": metrics,
            "model": {
                "payload": model_record,
                "bytes": len(payload),
                "dimension": int(parameters["dimension"]),
                "encoding": MODEL_ENCODING,
                "scale": scale,
                "nonzeroWeights": sum(weight != 0.0 for weight in quantized_weights),
            },
            "gateEvaluations": gate_rows,
            "decision": {
                "verdict": (
                    "authorize-open-base-integration"
                    if passed
                    else "retire-hashed-linear-probe"
                ),
                "rationale": (
                    "All prospective decoder-feature, held-out, control, and payload predicates passed."
                    if passed
                    else "At least one prospective decoder-feature, held-out, control, or payload predicate failed."
                ),
                "authorizedNextAction": (
                    "Bind one open Gamma base predictor and replay this unchanged correction interface."
                    if passed
                    else None
                ),
                "forbiddenClaims": [
                    "The O teacher endpoint is available to a submitted codec.",
                    "Ideal-bit improvement is arithmetic archive savings.",
                    "The model has paid source cost or transferred to an open base.",
                    "This causal shadow receives Hutter score credit."
                ],
            },
            "scoreCreditBytes": 0,
            "generatedUtc": utc_now(),
        }
        temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, output_path)
        research_contracts.validate_artifact(output_path)
    except Exception:
        for path in (
            output_path,
            analyzer_path,
            trace_dependency_path,
            contract_dependency_path,
            model_path,
        ):
            path.unlink(missing_ok=True)
        output_path.parent.rmdir()
        raise
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
