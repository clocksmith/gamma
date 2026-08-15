#!/usr/bin/env python3
"""Measure the frozen F-minus-O midpoint branch residual without rerunning NNCP."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import struct
from typing import Any, BinaryIO, Iterator

import research_contracts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = (
    ROOT
    / "operations/adaptive/experiments/delta_midas_deep_residual_65536_q0_v1.json"
)
TRACE_HEADER = struct.Struct("<8sQQQQ")
TRACE_ROW = struct.Struct("<QQQQQQQQHHBBB")
TRACE_BRANCH = struct.Struct("<HB")
TRACE_MAGIC = b"NNNTR4\0\0"
PROBABILITY_SCALE = 32768


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


def load_contract(path: Path) -> dict[str, Any]:
    research_contracts.validate_artifact(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if value["schema"] != "gamma.enwiki9.experiment-contract.v1":
        raise ValueError("expected an enwiki9 experiment contract")
    return value


def trace_path(contract: dict[str, Any], arm_id: str) -> Path:
    matches = [arm for arm in contract["arms"] if arm["id"] == arm_id]
    if len(matches) != 1:
        raise ValueError(f"contract must contain exactly one {arm_id} arm")
    return (ROOT / matches[0]["trace"]["path"]).resolve()


def read_header(stream: BinaryIO, path: Path) -> tuple[bytes, int, int, int, int]:
    raw = stream.read(TRACE_HEADER.size)
    if len(raw) != TRACE_HEADER.size:
        raise ValueError(f"truncated trace header: {path}")
    header = TRACE_HEADER.unpack(raw)
    if header[0] != TRACE_MAGIC:
        raise ValueError(f"unexpected indexed trace format: {path}")
    return header


def iter_rows(
    stream: BinaryIO,
    path: Path,
    row_count: int,
) -> Iterator[tuple[tuple[int, ...], list[tuple[int, int]]]]:
    for execution in range(row_count):
        raw = stream.read(TRACE_ROW.size)
        if len(raw) != TRACE_ROW.size:
            raise ValueError(f"truncated trace row {execution}: {path}")
        row = TRACE_ROW.unpack(raw)
        if row[1] != execution:
            raise ValueError(f"execution ordinal mismatch at row {execution}: {path}")
        branches: list[tuple[int, int]] = []
        for branch_index in range(row[10]):
            raw_branch = stream.read(TRACE_BRANCH.size)
            if len(raw_branch) != TRACE_BRANCH.size:
                raise ValueError(
                    f"truncated branch {branch_index} at row {execution}: {path}"
                )
            probability, bit = TRACE_BRANCH.unpack(raw_branch)
            if not 1 <= probability < PROBABILITY_SCALE or bit not in (0, 1):
                raise ValueError(
                    f"illegal branch probability or bit at row {execution}: {path}"
                )
            branches.append((probability, bit))
        yield row, branches
    if stream.read(1):
        raise ValueError(f"trace has trailing bytes: {path}")


def realized_probability(probability: int, bit: int) -> int:
    return probability if bit == 0 else PROBABILITY_SCALE - probability


def branch_logit(probability: int) -> float:
    return math.log(probability / (PROBABILITY_SCALE - probability))


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot summarize an empty segment population")

    def select(fraction: float) -> float:
        index = int((len(ordered) - 1) * fraction + 0.5)
        return ordered[index]

    return {
        "min": ordered[0],
        "p05": select(0.05),
        "p25": select(0.25),
        "p50": select(0.50),
        "p75": select(0.75),
        "p95": select(0.95),
        "max": ordered[-1],
    }


def compare_traces(
    contract: dict[str, Any],
    treatment_path: Path,
    comparator_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    population = contract["population"]
    expected_rows = population["rowCount"]
    expected_branches = population["branchCount"]
    segment_length = population["segmentLength"]
    first_half_length = population["firstHalfLength"]
    seen = bytearray(expected_rows)
    half_row_savings: list[list[float]] = [[], []]
    second_half_thirds: list[list[float]] = [[], [], []]
    segment_savings: list[list[float]] = [
        [] for _ in range(expected_rows // segment_length)
    ]
    changed_branches = 0
    unchanged_branches = 0
    absolute_probability_delta = 0
    maximum_probability_delta = 0
    maximum_logit_delta = 0.0
    observed_branches = 0

    with treatment_path.open("rb") as treatment, comparator_path.open("rb") as comparator:
        treatment_header = read_header(treatment, treatment_path)
        comparator_header = read_header(comparator, comparator_path)
        if treatment_header != comparator_header:
            raise ValueError("F and O trace headers differ")
        magic, rows, branches, trees, checkpoints = treatment_header
        if (
            magic != TRACE_MAGIC
            or rows != expected_rows
            or branches != expected_branches
            or trees != 0
            or checkpoints != 0
        ):
            raise ValueError("trace header differs from the frozen population")

        treatment_rows = iter_rows(treatment, treatment_path, expected_rows)
        comparator_rows = iter_rows(comparator, comparator_path, expected_rows)
        for execution, ((f_row, f_branches), (o_row, o_branches)) in enumerate(
            zip(treatment_rows, comparator_rows, strict=True)
        ):
            original = f_row[0]
            if original >= expected_rows or seen[original]:
                raise ValueError(f"invalid or duplicate original ordinal: {original}")
            seen[original] = 1
            if f_row[:2] != o_row[:2]:
                raise ValueError(f"row identity differs at execution {execution}")
            if f_row[8:11] != o_row[8:11]:
                raise ValueError(f"symbol or vocabulary differs at execution {execution}")
            if f_row[11:] != o_row[11:]:
                raise ValueError(f"tree metadata differs at execution {execution}")
            if len(f_branches) != len(o_branches):
                raise ValueError(f"branch count differs at execution {execution}")

            row_savings: list[float] = []
            for (f_probability, f_bit), (o_probability, o_bit) in zip(
                f_branches,
                o_branches,
                strict=True,
            ):
                if f_bit != o_bit:
                    raise ValueError(f"truth path differs at execution {execution}")
                f_realized = realized_probability(f_probability, f_bit)
                o_realized = realized_probability(o_probability, o_bit)
                row_savings.append(math.log2(f_realized / o_realized))
                probability_delta = abs(f_probability - o_probability)
                absolute_probability_delta += probability_delta
                maximum_probability_delta = max(
                    maximum_probability_delta,
                    probability_delta,
                )
                maximum_logit_delta = max(
                    maximum_logit_delta,
                    abs(branch_logit(f_probability) - branch_logit(o_probability)),
                )
                if probability_delta:
                    changed_branches += 1
                else:
                    unchanged_branches += 1
                observed_branches += 1

            savings = math.fsum(row_savings)
            position = original % segment_length
            half = 0 if position < first_half_length else 1
            half_row_savings[half].append(savings)
            if half == 1:
                third = min(2, original * 3 // expected_rows)
                second_half_thirds[third].append(savings)
                segment_savings[original // segment_length].append(savings)

    if not all(seen) or observed_branches != expected_branches:
        raise ValueError("trace population is incomplete")
    first_half_savings = math.fsum(half_row_savings[0])
    second_half_savings = math.fsum(half_row_savings[1])
    third_savings = [math.fsum(values) for values in second_half_thirds]
    segment_totals = [math.fsum(values) for values in segment_savings]
    if any(len(values) != segment_length - first_half_length for values in segment_savings):
        raise ValueError("second-half segment coverage is incomplete")
    positive_segments = sum(value > 0 for value in segment_totals)
    negative_segments = sum(value < 0 for value in segment_totals)
    alignment = {
        "complete": True,
        "rowIdentity": True,
        "symbolIdentity": True,
        "treeIdentity": True,
        "truthPathIdentity": True,
    }
    metrics = {
        "alignmentComplete": True,
        "allIdealSavingsBits": first_half_savings + second_half_savings,
        "firstHalfIdealSavingsBits": first_half_savings,
        "secondHalfIdealSavingsBits": second_half_savings,
        "secondHalfThirdSavingsBits": third_savings,
        "secondHalfThirdMinSavingsBits": min(third_savings),
        "secondHalfPositiveSegments": positive_segments,
        "secondHalfNegativeSegments": negative_segments,
        "secondHalfPositiveSegmentFraction": positive_segments / len(segment_totals),
        "changedBranchCount": changed_branches,
        "unchangedBranchCount": unchanged_branches,
        "maximumAbsoluteProbabilityDeltaCounts": maximum_probability_delta,
        "meanAbsoluteProbabilityDeltaCounts": (
            absolute_probability_delta / observed_branches
        ),
        "maximumAbsoluteDerivedLogitDelta": maximum_logit_delta,
        "secondHalfSegmentSavingsBitsQuantiles": quantiles(segment_totals),
    }
    return alignment, metrics


def predicate_pass(observed: Any, operator: str, threshold: Any) -> bool:
    if operator == "eq":
        return observed == threshold
    if operator == "gt":
        return observed > threshold
    if operator == "gte":
        return observed >= threshold
    if operator == "lt":
        return observed < threshold
    if operator == "lte":
        return observed <= threshold
    raise ValueError(f"unsupported predicate operator: {operator}")


def evaluate_gates(
    contract: dict[str, Any],
    metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    evaluations: list[dict[str, Any]] = []
    for gate in contract["gates"]:
        predicates: list[dict[str, Any]] = []
        for predicate in gate["all"]:
            observed = metrics[predicate["metric"]]
            passed = predicate_pass(
                observed,
                predicate["operator"],
                predicate["threshold"],
            )
            predicates.append({**predicate, "observed": observed, "pass": passed})
        evaluations.append(
            {
                "id": gate["id"],
                "pass": all(item["pass"] for item in predicates),
                "predicates": predicates,
            }
        )
    return evaluations


def build_result(
    experiment_path: Path,
    contract: dict[str, Any],
    analyzer_path: Path,
) -> dict[str, Any]:
    treatment_path = trace_path(contract, "F")
    comparator_path = trace_path(contract, "O")
    alignment, metrics = compare_traces(
        contract,
        treatment_path,
        comparator_path,
    )
    gates = evaluate_gates(contract, metrics)
    passed = alignment["complete"] and all(gate["pass"] for gate in gates)
    status = "pass" if passed else "fail"
    verdict = (
        "authorize-deep-feature-instrumentation"
        if passed
        else "retire-deep-residual-lineage"
    )
    population = contract["population"]
    return {
        "schema": "gamma.enwiki9.experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experimentId": contract["experimentId"],
        "experiment": reference(experiment_path),
        "analyzer": reference(analyzer_path),
        "status": status,
        "inputs": [
            {"id": arm_id, **reference(path)}
            for arm_id, path in (("F", treatment_path), ("O", comparator_path))
        ],
        "population": {
            "rows": population["rowCount"],
            "branches": population["branchCount"],
            "segments": population["rowCount"] // population["segmentLength"],
            "segmentLength": population["segmentLength"],
            "firstHalfLength": population["firstHalfLength"],
        },
        "alignment": alignment,
        "metrics": metrics,
        "gateEvaluations": gates,
        "decision": {
            "verdict": verdict,
            "rationale": (
                "All frozen residual-structure predicates passed; only a new "
                "prospective decoder-visible feature-capture experiment is authorized."
                if passed
                else "At least one frozen residual-structure predicate failed; the "
                "deep residual lineage is retired on this population."
            ),
            "authorizedNextAction": (
                "Freeze a prospective deep-feature attribution contract before "
                "instrumenting or executing the closed teacher."
                if passed
                else None
            ),
            "forbiddenClaims": [
                "The ideal-bit delta is a realizable arithmetic archive gain.",
                "DELTA-MIDAS is an implemented or promoted codec.",
                "This retained teacher trace receives Hutter score credit.",
                "The result transfers beyond the frozen 65,536-symbol population."
            ],
        },
        "scoreCreditBytes": 0,
        "generatedUtc": utc_now(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    contract = load_contract(experiment_path)
    raw_output = args.output or Path(contract["outputs"][0])
    output_path = raw_output if raw_output.is_absolute() else ROOT / raw_output
    output_path = output_path.resolve()
    if ROOT.resolve() not in output_path.parents:
        raise ValueError("output escapes enwiki9 project")
    if output_path.exists() or output_path.parent.exists():
        raise FileExistsError(f"refusing to overwrite result boundary: {output_path.parent}")

    output_path.parent.mkdir(parents=True)
    analyzer_path = output_path.parent / "analyzer.py"
    analyzer_path.write_bytes(Path(__file__).read_bytes())
    try:
        result = build_result(experiment_path, contract, analyzer_path)
        temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, output_path)
        research_contracts.validate_artifact(output_path)
    except Exception:
        output_path.unlink(missing_ok=True)
        analyzer_path.unlink(missing_ok=True)
        output_path.parent.rmdir()
        raise
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
