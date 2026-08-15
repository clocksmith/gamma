#!/usr/bin/env python3
"""Validate the canonical enwik9 objective and its fail-closed receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import jsonschema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parents[1]
CONTRACT_ROOT = PROJECT_ROOT / "contracts" / "research" / "v1"
OBJECTIVE_PATH = CONTRACT_ROOT / "objective-contract.json"
SCHEMA_PATH = CONTRACT_ROOT / "objective-contract.schema.json"
SCHEMA_PATHS = {
    "gamma.enwiki9.adaptive-experiment-contract.v1": (
        CONTRACT_ROOT / "adaptive-experiment-contract.schema.json"
    ),
    "gamma.enwiki9.adaptive-job.v3": CONTRACT_ROOT / "adaptive-job.schema.json",
    "gamma.enwiki9.algorithm-proposal.v2": (
        CONTRACT_ROOT / "algorithm-proposal.schema.json"
    ),
    "gamma.enwiki9.objective-contract.v1": SCHEMA_PATH,
    "gamma.enwiki9.candidate-revision.v1": (
        CONTRACT_ROOT / "candidate-revision.schema.json"
    ),
    "gamma.enwiki9.dependency-closure.v1": (
        CONTRACT_ROOT / "dependency-closure.schema.json"
    ),
    "gamma.enwiki9.delta-midas-probe-result.v1": (
        CONTRACT_ROOT / "delta-midas-probe-result.schema.json"
    ),
    "gamma.enwiki9.experiment-contract.v1": (
        CONTRACT_ROOT / "experiment-contract.schema.json"
    ),
    "gamma.enwiki9.experiment-result.v1": (
        CONTRACT_ROOT / "experiment-result.schema.json"
    ),
    "gamma.enwiki9.mechanism-graph.v1": (
        CONTRACT_ROOT / "mechanism-graph.schema.json"
    ),
    "gamma.enwiki9.resource-guard-receipt.v2": (
        CONTRACT_ROOT / "resource-guard-receipt.schema.json"
    ),
    "gamma.enwiki9.reflection-receipt.v1": (
        CONTRACT_ROOT / "reflection-receipt.schema.json"
    ),
    "gamma.enwiki9.run-receipt.v1": CONTRACT_ROOT / "run-receipt.schema.json",
    "gamma.enwiki9.search-policy.v1": CONTRACT_ROOT / "search-policy.schema.json",
}
UNCOUNTED_PLATFORM_DEPENDENCY_KINDS = {
    "standard-library",
    "system",
    "toolchain",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def validate_objective(verify_corpus: bool = False) -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    objective = load_json(OBJECTIVE_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(objective)

    corpus = objective["corpus"]
    if objective["correctness"]["restoredSha256"] != corpus["sha256"]:
        raise ValueError("restored corpus SHA-256 differs from objective corpus")
    if objective["correctness"]["restoredBytes"] != corpus["bytes"]:
        raise ValueError("restored corpus size differs from objective corpus")

    if verify_corpus:
        corpus_path = REPOSITORY_ROOT / corpus["repositoryPath"]
        if not corpus_path.is_file():
            raise ValueError(f"canonical corpus is missing: {corpus_path}")
        if corpus_path.stat().st_size != corpus["bytes"]:
            raise ValueError(f"canonical corpus size differs: {corpus_path}")
        if file_digest(corpus_path, "md5") != corpus["md5"]:
            raise ValueError(f"canonical corpus MD5 differs: {corpus_path}")
        if file_digest(corpus_path, "sha256") != corpus["sha256"]:
            raise ValueError(f"canonical corpus SHA-256 differs: {corpus_path}")

    return objective


def objective_binding(verify_corpus: bool = False) -> dict[str, Any]:
    objective = validate_objective(verify_corpus)
    digest = hashlib.sha256(canonical_bytes(objective)).hexdigest()
    return {
        "objectiveId": objective["objectiveId"],
        "objectiveDigest": f"sha256:{digest}",
        "objectivePath": "contracts/research/v1/objective-contract.json",
        "targetScoreBytes": objective["score"]["targetBytes"],
        "corpusBytes": objective["corpus"]["bytes"],
        "corpusSha256": objective["corpus"]["sha256"],
    }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_schema(value: Any, schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(value)


def validate_schemas() -> None:
    for schema_path in set(SCHEMA_PATHS.values()):
        jsonschema.Draft202012Validator.check_schema(load_json(schema_path))


def _validate_objective_binding(value: dict[str, Any], context: str) -> None:
    _require(
        value == objective_binding(),
        f"{context}: objective binding differs from the canonical objective",
    )


def _relative_path(base: Path, raw_path: str, context: str) -> Path:
    path = Path(raw_path)
    _require(not path.is_absolute(), f"{context}: absolute paths are not reproducible")
    return (base / path).resolve()


def _verify_file_record(base: Path, record: dict[str, Any], context: str) -> None:
    relative_path = Path(record["path"])
    _require(
        not relative_path.is_absolute(),
        f"{context}: absolute paths are not reproducible",
    )
    unresolved_path = base / relative_path
    _require(
        not unresolved_path.is_symlink(),
        f"{context}: symlinks require explicit packaging",
    )
    path = unresolved_path.resolve()
    _require(path.is_file(), f"{context}: file is missing: {path}")
    _require(
        path.stat().st_size == record["bytes"],
        f"{context}: size differs: {path}",
    )
    _require(
        file_digest(path, "sha256") == record["sha256"],
        f"{context}: SHA-256 differs: {path}",
    )


def candidate_tree_digest(counted_files: list[dict[str, Any]]) -> str:
    identity = [
        {
            "bytes": record["bytes"],
            "path": record["path"],
            "sha256": record["sha256"],
        }
        for record in sorted(counted_files, key=lambda item: item["path"])
    ]
    return f"sha256:{hashlib.sha256(canonical_bytes(identity)).hexdigest()}"


def _project_receipt_reference(
    reference: dict[str, Any],
    expected_schema: str,
    context: str,
) -> tuple[Path, dict[str, Any]]:
    path = _relative_path(PROJECT_ROOT, reference["path"], context)
    _require(path.is_file(), f"{context}: referenced receipt is missing: {path}")
    _require(
        f"sha256:{file_digest(path, 'sha256')}" == reference["sha256"],
        f"{context}: referenced receipt digest differs: {path}",
    )
    value = load_json(path)
    _require(
        value.get("schema") == expected_schema,
        f"{context}: referenced receipt has wrong schema: {path}",
    )
    _validate_schema(value, SCHEMA_PATHS[expected_schema])
    _validate_objective_binding(value["objective"], str(path))
    return path, value


def _project_file_reference(
    reference: dict[str, Any],
    context: str,
) -> Path:
    path = _relative_path(PROJECT_ROOT, reference["path"], context)
    _require(path.is_file(), f"{context}: referenced evidence is missing: {path}")
    _require(
        f"sha256:{file_digest(path, 'sha256')}" == reference["sha256"],
        f"{context}: referenced evidence digest differs: {path}",
    )
    return path


def validate_project_reference(
    reference: dict[str, Any],
    expected_schemas: set[str],
    context: str,
) -> tuple[Path, dict[str, Any]]:
    path = _project_file_reference(reference, context)
    value = load_json(path)
    _require(
        value.get("schema") in expected_schemas,
        f"{context}: referenced artifact has wrong schema: {path}",
    )
    validate_artifact(path)
    return path, value


def _validate_candidate_revision(
    value: dict[str, Any],
    artifact_path: Path,
    verify_files: bool,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    records = value["files"]
    paths = [record["path"] for record in records]
    _require(len(paths) == len(set(paths)), f"{artifact_path}: duplicate source path")
    _require("meta.json" in paths, f"{artifact_path}: candidate revision lacks metadata")
    for record in records:
        expected_normalization = (
            "semantic-meta-v1" if record["path"] == "meta.json" else "verbatim"
        )
        _require(
            record["normalization"] == expected_normalization,
            f"{artifact_path}: unexpected normalization for {record['path']}",
        )
    _require(
        candidate_tree_digest(records) == value["candidateTreeSha256"],
        f"{artifact_path}: candidate tree digest differs from its file manifest",
    )
    expected_provenance = (
        "legacy-current-state"
        if value["change"]["kind"] == "legacy-adoption"
        else "native"
    )
    _require(
        value["provenanceClass"] == expected_provenance,
        f"{artifact_path}: provenance class differs from change kind",
    )
    parent = value["parentRevision"]
    if value["change"]["kind"] == "mutate":
        _require(parent is not None, f"{artifact_path}: mutation lacks parent revision")
    if parent is not None:
        _require(
            parent["candidateId"] != value["candidateId"],
            f"{artifact_path}: candidate cannot be its own parent",
        )
        _, parent_value = _project_receipt_reference(
            parent["receipt"],
            "gamma.enwiki9.candidate-revision.v1",
            f"{artifact_path}: parentRevision",
        )
        _require(
            parent_value["candidateId"] == parent["candidateId"]
            and parent_value["candidateTreeSha256"]
            == parent["candidateTreeSha256"],
            f"{artifact_path}: parent revision identity differs from its receipt",
        )
    previous = value["previousRevision"]
    if previous is not None:
        _, previous_value = _project_receipt_reference(
            previous,
            "gamma.enwiki9.candidate-revision.v1",
            f"{artifact_path}: previousRevision",
        )
        _require(
            previous_value["candidateId"] == value["candidateId"],
            f"{artifact_path}: previous revision identifies another candidate",
        )
        _require(
            previous_value["candidateTreeSha256"] != value["candidateTreeSha256"],
            f"{artifact_path}: duplicate revision identity",
        )
    elif value["change"]["kind"] in {"implementation", "proposal-development"}:
        raise ValueError(f"{artifact_path}: edit revision lacks previous revision")

    if verify_files:
        blob_root = (PROJECT_ROOT / "operations/adaptive/candidate-blobs/sha256").resolve()
        for record in records:
            blob = _relative_path(PROJECT_ROOT, record["blobPath"], str(artifact_path))
            _require(
                blob_root == blob.parent.parent or blob_root in blob.parents,
                f"{artifact_path}: blob path escapes the content-addressed store",
            )
            expected_blob = blob_root / record["sha256"][:2] / record["sha256"]
            _require(
                blob == expected_blob,
                f"{artifact_path}: blob path differs from its content address",
            )
            _require(blob.is_file(), f"{artifact_path}: immutable blob is missing: {blob}")
            _require(
                blob.stat().st_size == record["bytes"]
                and file_digest(blob, "sha256") == record["sha256"],
                f"{artifact_path}: immutable blob content differs: {blob}",
            )
    return {
        "candidateId": value["candidateId"],
        "candidateTreeSha256": value["candidateTreeSha256"],
        "filesVerified": verify_files,
        "provenanceClass": value["provenanceClass"],
    }


def json_pointer(value: Any, pointer: str, context: str = "artifact") -> Any:
    current = value
    for raw_token in pointer.lstrip("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ValueError(f"{context}: JSON pointer does not resolve: {pointer}")
    return current


def _validate_reflection_receipt(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    candidate = value["candidateRevision"]
    _require(
        candidate["candidateId"] == value["candidateId"],
        f"{artifact_path}: candidate revision identifies another candidate",
    )
    _, candidate_receipt = _project_receipt_reference(
        candidate["receipt"],
        "gamma.enwiki9.candidate-revision.v1",
        f"{artifact_path}: candidateRevision",
    )
    _require(
        candidate_receipt["candidateId"] == value["candidateId"]
        and candidate_receipt["candidateTreeSha256"]
        == candidate["candidateTreeSha256"],
        f"{artifact_path}: candidate revision identity differs from receipt",
    )

    job_path = _project_file_reference(value["job"], f"{artifact_path}: job")
    job = load_json(job_path)
    _require(
        job.get("schema") in {
            "enwiki9_adaptive_job_v2",
            "gamma.enwiki9.adaptive-job.v3",
        },
        f"{artifact_path}: reflection requires a revision-bound v2 or v3 job",
    )
    _require(
        job.get("candidate_id") == value["candidateId"]
        and job.get("candidate_tree_sha256") == candidate["candidateTreeSha256"]
        and job.get("candidate_revision") == candidate["receipt"],
        f"{artifact_path}: job and candidate revision bindings differ",
    )
    _require(
        job.get("state") in {"completed", "failed", "cancelled"},
        f"{artifact_path}: job is not terminal",
    )
    _require(
        job_path.parent.name == job.get("state"),
        f"{artifact_path}: job state differs from its queue directory",
    )
    experiment_path = _project_file_reference(
        value["experiment"],
        f"{artifact_path}: experiment",
    )
    experiment = load_json(experiment_path)
    _require(
        experiment.get("schema") in {
            "gamma.enwiki9.experiment-contract.v1",
            "gamma.enwiki9.adaptive-experiment-contract.v1",
        },
        f"{artifact_path}: experiment has an unsupported schema",
    )
    validate_artifact(experiment_path)
    if job.get("schema") == "gamma.enwiki9.adaptive-job.v3":
        _require(
            job.get("experiment") == value["experiment"],
            f"{artifact_path}: reflection and job experiment bindings differ",
        )
    evidence_paths = {
        _project_file_reference(reference, f"{artifact_path}: evidence")
        for reference in value["evidence"]
    }

    validity = value["validity"]
    _require(
        validity["valid"] == (validity["classification"] == "valid"),
        f"{artifact_path}: validity boolean and classification differ",
    )
    if validity["valid"]:
        _require(
            job.get("state") == "completed" and job.get("returncode") == 0,
            f"{artifact_path}: valid reflection requires successful process completion",
        )

    assertions = value["measurementAssertions"]
    assertion_fields = [assertion["field"] for assertion in assertions]
    _require(
        len(assertion_fields) == len(set(assertion_fields)),
        f"{artifact_path}: duplicate measurement assertion field",
    )
    for assertion in assertions:
        source_path = _project_file_reference(
            assertion["source"],
            f"{artifact_path}: measurement assertion",
        )
        _require(
            source_path in evidence_paths,
            f"{artifact_path}: measurement assertion source is not listed evidence",
        )
        source_value = load_json(source_path)
        measured_value = json_pointer(
            source_value,
            assertion["pointer"],
            f"{artifact_path}: {assertion['field']}",
        )
        _require(
            isinstance(measured_value, (int, float))
            and not isinstance(measured_value, bool)
            and measured_value == value["measurements"][assertion["field"]],
            f"{artifact_path}: asserted measurement differs from source evidence",
        )
    for field, measured_value in value["measurements"].items():
        _require(
            (measured_value is None) == (field not in assertion_fields),
            f"{artifact_path}: measurement {field} lacks exactly one source assertion",
        )

    decision = value["decision"]
    hypothesis = value["hypothesis"]
    attribution = value["attribution"]
    invalid_attribution = {
        "implementation-failure": "implementation-failure",
        "infrastructure-failure": "infrastructure-failure",
        "invalid-experiment": "invalid-experiment",
        "incomplete-evidence": "inconclusive",
    }
    if not validity["valid"]:
        _require(
            attribution["failureClass"]
            == invalid_attribution[validity["classification"]],
            f"{artifact_path}: invalidity and attribution classes differ",
        )
        _require(
            decision["verdict"] in {"retry", "hold"},
            f"{artifact_path}: invalid experiment cannot change algorithm status",
        )
        _require(
            hypothesis["verdict"] in {"inconclusive", "not-tested"},
            f"{artifact_path}: invalid experiment cannot support or refute hypothesis",
        )
    else:
        _require(
            attribution["failureClass"]
            not in {
                "implementation-failure",
                "infrastructure-failure",
                "invalid-experiment",
            },
            f"{artifact_path}: valid experiment has a process-failure attribution",
        )
    if decision["verdict"] in {"promote", "next-gate"}:
        _require(
            validity["valid"]
            and hypothesis["verdict"] == "supported"
            and attribution["failureClass"] == "algorithmic-gain"
            and attribution["controlsEquivalent"] is True
            and decision["promotionPredicatesPass"] is True
            and decision["killPredicatesPass"] is False,
            f"{artifact_path}: promotion decision lacks causal gate antecedents",
        )
    if decision["verdict"] == "retire":
        _require(
            validity["valid"] and decision["killPredicatesPass"] is True,
            f"{artifact_path}: retirement requires a valid kill predicate",
        )
    _require(
        (decision["verdict"] == "next-gate")
        == (decision["nextGateBytes"] is not None),
        f"{artifact_path}: next gate is present for the wrong decision",
    )
    return {
        "candidateId": value["candidateId"],
        "decision": decision["verdict"],
        "jobId": job.get("job_id"),
        "netBytesSaved": value["measurements"]["netBytesSaved"],
        "validExperiment": validity["valid"],
    }


def _validate_adaptive_experiment_contract(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    parent = value["parent"]
    if parent is not None:
        _, revision = _project_receipt_reference(
            parent["revision"],
            "gamma.enwiki9.candidate-revision.v1",
            f"{artifact_path}: parent revision",
        )
        _require(
            revision["candidateId"] == parent["candidateId"],
            f"{artifact_path}: parent candidate differs from revision receipt",
        )
    input_ids = [item["id"] for item in value["inputs"]]
    _require(
        len(input_ids) == len(set(input_ids)),
        f"{artifact_path}: duplicate input identity",
    )
    for item in value["inputs"]:
        _project_file_reference(item, f"{artifact_path}: input {item['id']}")
    control_ids = [item["id"] for item in value["controls"]]
    _require(
        len(control_ids) == len(set(control_ids)),
        f"{artifact_path}: duplicate control identity",
    )
    roles = {item["role"] for item in value["controls"]}
    _require(
        {"treatment", "comparator"}.issubset(roles),
        f"{artifact_path}: treatment and comparator controls are required",
    )
    population = value["population"]
    _require(
        population["scopeBytes"] is not None
        or population["scopeSymbols"] is not None,
        f"{artifact_path}: population has no exact byte or symbol scope",
    )
    budget = value["budget"]
    _require(
        budget["expectedNetSavingsBytes"]
        == budget["expectedGrossSavingsBytes"]
        - budget["maximumAddedPackageBytes"],
        f"{artifact_path}: expected net savings differs from gross less package cost",
    )
    measurement_ids = [item["id"] for item in value["measurements"]]
    _require(
        len(measurement_ids) == len(set(measurement_ids)),
        f"{artifact_path}: duplicate measurement identity",
    )
    known_measurements = set(measurement_ids)
    predicate_ids: list[str] = []
    for predicate_class in ("promotionPredicates", "killPredicates"):
        for predicate in value[predicate_class]:
            predicate_ids.append(predicate["id"])
            _require(
                predicate["measurement"] in known_measurements,
                f"{artifact_path}: predicate names an unknown measurement",
            )
    _require(
        len(predicate_ids) == len(set(predicate_ids)),
        f"{artifact_path}: duplicate predicate identity",
    )
    return {
        "experimentId": value["experimentId"],
        "proposalId": value["proposalId"],
        "expectedNetSavingsBytes": budget["expectedNetSavingsBytes"],
    }


def _validate_algorithm_proposal(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    _, experiment = validate_project_reference(
        value["experiment"],
        {"gamma.enwiki9.adaptive-experiment-contract.v1"},
        f"{artifact_path}: experiment",
    )
    _require(
        experiment["proposalId"] == value["proposal_id"],
        f"{artifact_path}: proposal and experiment identities differ",
    )
    experiment_parent = experiment["parent"]
    experiment_parent_id = (
        experiment_parent["candidateId"] if experiment_parent is not None else None
    )
    _require(
        experiment_parent_id == value["parent"],
        f"{artifact_path}: proposal and experiment parents differ",
    )
    budget = experiment["budget"]
    _require(
        value["expected_savings_bytes"] == budget["expectedGrossSavingsBytes"]
        and value["max_program_bytes"] == budget["maximumAddedPackageBytes"],
        f"{artifact_path}: proposal and experiment budgets differ",
    )
    _require(
        value["hypothesis"] == experiment["hypothesis"]["claim"],
        f"{artifact_path}: proposal and experiment hypotheses differ",
    )
    for evidence in value["evidence"]:
        _project_file_reference(evidence, f"{artifact_path}: evidence")
    return {
        "proposalId": value["proposal_id"],
        "experimentId": experiment["experimentId"],
        "state": value["state"],
    }


def _validate_adaptive_job(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _, revision = _project_receipt_reference(
        value["candidate_revision"],
        "gamma.enwiki9.candidate-revision.v1",
        f"{artifact_path}: candidate revision",
    )
    _require(
        revision["candidateId"] == value["candidate_id"]
        and revision["candidateTreeSha256"] == value["candidate_tree_sha256"],
        f"{artifact_path}: candidate identity differs from revision receipt",
    )
    _, experiment = validate_project_reference(
        value["experiment"],
        {"gamma.enwiki9.adaptive-experiment-contract.v1"},
        f"{artifact_path}: experiment",
    )
    _require(
        experiment["proposalId"] == value["proposal_id"],
        f"{artifact_path}: job and experiment proposal identities differ",
    )
    return {
        "jobId": value["job_id"],
        "candidateId": value["candidate_id"],
        "experimentId": experiment["experimentId"],
    }


def _validate_experiment_contract(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    _require(
        value["population"]["firstHalfLength"] * 2
        == value["population"]["segmentLength"],
        f"{artifact_path}: midpoint does not divide the segment into equal halves",
    )
    antecedent_ids = [item["id"] for item in value["antecedents"]]
    _require(
        len(antecedent_ids) == len(set(antecedent_ids)),
        f"{artifact_path}: duplicate antecedent identity",
    )
    for antecedent in value["antecedents"]:
        _project_file_reference(antecedent, f"{artifact_path}: antecedent")

    arm_ids = [arm["id"] for arm in value["arms"]]
    _require(
        len(arm_ids) == len(set(arm_ids)),
        f"{artifact_path}: duplicate arm identity",
    )
    roles = {arm["role"] for arm in value["arms"]}
    _require(
        {"treatment", "comparator"}.issubset(roles),
        f"{artifact_path}: experiment requires treatment and comparator arms",
    )
    for arm in value["arms"]:
        _project_file_reference(arm["trace"], f"{artifact_path}: arm {arm['id']}")

    measurement_ids = [item["id"] for item in value["measurements"]]
    _require(
        len(measurement_ids) == len(set(measurement_ids)),
        f"{artifact_path}: duplicate measurement identity",
    )
    gate_ids = [gate["id"] for gate in value["gates"]]
    _require(
        len(gate_ids) == len(set(gate_ids)),
        f"{artifact_path}: duplicate gate identity",
    )
    known_measurements = set(measurement_ids)
    for gate in value["gates"]:
        for predicate in gate["all"]:
            _require(
                predicate["metric"] in known_measurements,
                f"{artifact_path}: gate references undeclared measurement "
                f"{predicate['metric']}",
            )
    protocol = value.get("protocol")
    if protocol is not None:
        partitions = protocol["partitions"]
        partition_ids = [partition["id"] for partition in partitions]
        _require(
            len(partition_ids) == len(set(partition_ids)),
            f"{artifact_path}: duplicate partition identity",
        )
        expected_first = 0
        for partition in partitions:
            _require(
                partition["firstSegment"] == expected_first
                and partition["endSegmentExclusive"] > expected_first,
                f"{artifact_path}: partitions must be ordered and contiguous",
            )
            expected_first = partition["endSegmentExclusive"]
        expected_segments = (
            value["population"]["rowCount"]
            // value["population"]["segmentLength"]
        )
        _require(
            expected_first == expected_segments,
            f"{artifact_path}: partitions do not cover the frozen population",
        )
        control_ids = [control["id"] for control in protocol["controls"]]
        _require(
            len(control_ids) == len(set(control_ids)),
            f"{artifact_path}: duplicate control identity",
        )
    return {
        "experimentId": value["experimentId"],
        "evidenceClass": value["evidenceClass"],
        "registrationTiming": value["registrationTiming"],
    }


def _predicate_pass(observed: Any, operator: str, threshold: Any) -> bool:
    operations = {
        "eq": lambda: observed == threshold,
        "gt": lambda: observed > threshold,
        "gte": lambda: observed >= threshold,
        "lt": lambda: observed < threshold,
        "lte": lambda: observed <= threshold,
    }
    try:
        return bool(operations[operator]())
    except TypeError as exc:
        raise ValueError(
            f"cannot compare observed {observed!r} {operator} {threshold!r}"
        ) from exc


def _validate_experiment_result(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    _, experiment = _project_receipt_reference(
        value["experiment"],
        "gamma.enwiki9.experiment-contract.v1",
        f"{artifact_path}: experiment",
    )
    _require(
        value["experimentId"] == experiment["experimentId"],
        f"{artifact_path}: result identifies another experiment",
    )
    _project_file_reference(value["analyzer"], f"{artifact_path}: analyzer")

    expected_inputs = {
        arm["id"]: {"path": arm["trace"]["path"], "sha256": arm["trace"]["sha256"]}
        for arm in experiment["arms"]
    }
    observed_inputs = {
        item["id"]: {"path": item["path"], "sha256": item["sha256"]}
        for item in value["inputs"]
    }
    _require(
        observed_inputs == expected_inputs,
        f"{artifact_path}: result inputs differ from frozen experiment arms",
    )
    for item in value["inputs"]:
        _project_file_reference(item, f"{artifact_path}: input {item['id']}")

    population = value["population"]
    contract_population = experiment["population"]
    expected_population = {
        "rows": contract_population["rowCount"],
        "branches": contract_population["branchCount"],
        "segments": contract_population["rowCount"]
        // contract_population["segmentLength"],
        "segmentLength": contract_population["segmentLength"],
        "firstHalfLength": contract_population["firstHalfLength"],
    }
    _require(
        population == expected_population,
        f"{artifact_path}: measured population differs from frozen contract",
    )
    metrics = value["metrics"]
    _require(
        value["alignment"]["complete"]
        == all(value["alignment"][field] for field in (
            "rowIdentity",
            "symbolIdentity",
            "treeIdentity",
            "truthPathIdentity",
        ))
        == metrics["alignmentComplete"],
        f"{artifact_path}: alignment claims differ",
    )
    _require(
        metrics["changedBranchCount"] + metrics["unchangedBranchCount"]
        == population["branches"],
        f"{artifact_path}: branch-change totals differ from population",
    )
    _require(
        metrics["secondHalfPositiveSegments"]
        + metrics["secondHalfNegativeSegments"]
        <= population["segments"],
        f"{artifact_path}: segment-sign totals exceed the population",
    )
    _require(
        math.isclose(
            metrics["secondHalfPositiveSegmentFraction"],
            metrics["secondHalfPositiveSegments"] / population["segments"],
            rel_tol=1e-15,
            abs_tol=0.0,
        ),
        f"{artifact_path}: positive-segment fraction differs from counts",
    )
    _require(
        metrics["secondHalfThirdMinSavingsBits"]
        == min(metrics["secondHalfThirdSavingsBits"]),
        f"{artifact_path}: minimum third savings differs from third values",
    )
    _require(
        math.isclose(
            metrics["allIdealSavingsBits"],
            metrics["firstHalfIdealSavingsBits"]
            + metrics["secondHalfIdealSavingsBits"],
            rel_tol=1e-12,
            abs_tol=1e-9,
        ),
        f"{artifact_path}: total ideal savings differs from half totals",
    )

    expected_gate_rows: list[dict[str, Any]] = []
    for gate in experiment["gates"]:
        predicates: list[dict[str, Any]] = []
        for predicate in gate["all"]:
            observed = metrics[predicate["metric"]]
            passed = _predicate_pass(
                observed,
                predicate["operator"],
                predicate["threshold"],
            )
            predicates.append({**predicate, "observed": observed, "pass": passed})
        expected_gate_rows.append(
            {
                "id": gate["id"],
                "pass": all(item["pass"] for item in predicates),
                "predicates": predicates,
            }
        )
    _require(
        value["gateEvaluations"] == expected_gate_rows,
        f"{artifact_path}: gate evaluations differ from frozen predicates",
    )
    all_gates_pass = all(row["pass"] for row in expected_gate_rows)
    expected_status = (
        "invalid"
        if not value["alignment"]["complete"]
        else "pass"
        if all_gates_pass
        else "fail"
    )
    _require(
        value["status"] == expected_status,
        f"{artifact_path}: status differs from alignment and gate evidence",
    )
    expected_verdict = {
        "pass": "authorize-deep-feature-instrumentation",
        "fail": "retire-deep-residual-lineage",
        "invalid": "invalid-experiment",
    }[expected_status]
    _require(
        value["decision"]["verdict"] == expected_verdict,
        f"{artifact_path}: decision differs from experiment status",
    )
    return {
        "experimentId": value["experimentId"],
        "status": value["status"],
        "verdict": value["decision"]["verdict"],
    }


def _validate_delta_midas_probe_result(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    _, experiment = _project_receipt_reference(
        value["experiment"],
        "gamma.enwiki9.experiment-contract.v1",
        f"{artifact_path}: experiment",
    )
    _require(
        value["experimentId"] == experiment["experimentId"]
        and experiment["registrationTiming"] == "prospective"
        and experiment.get("protocol") is not None,
        f"{artifact_path}: probe requires its prospective protocol contract",
    )
    _project_file_reference(value["analyzer"], f"{artifact_path}: analyzer")
    dependency_ids = [item["id"] for item in value["analyzerDependencies"]]
    _require(
        len(dependency_ids) == len(set(dependency_ids)),
        f"{artifact_path}: duplicate analyzer dependency",
    )
    for dependency in value["analyzerDependencies"]:
        _project_file_reference(
            dependency,
            f"{artifact_path}: analyzer dependency {dependency['id']}",
        )

    expected_inputs = {
        arm["id"]: {"path": arm["trace"]["path"], "sha256": arm["trace"]["sha256"]}
        for arm in experiment["arms"]
    }
    observed_inputs = {
        item["id"]: {"path": item["path"], "sha256": item["sha256"]}
        for item in value["inputs"]
    }
    _require(
        observed_inputs == expected_inputs,
        f"{artifact_path}: result inputs differ from frozen experiment arms",
    )
    for item in value["inputs"]:
        _project_file_reference(item, f"{artifact_path}: input {item['id']}")

    contract_population = experiment["population"]
    expected_population = {
        "rows": contract_population["rowCount"],
        "branches": contract_population["branchCount"],
        "segments": contract_population["rowCount"]
        // contract_population["segmentLength"],
        "segmentLength": contract_population["segmentLength"],
        "firstHalfLength": contract_population["firstHalfLength"],
    }
    _require(
        value["population"] == expected_population,
        f"{artifact_path}: measured population differs from frozen contract",
    )
    alignment = value["alignment"]
    metrics = value["metrics"]
    _require(
        alignment["complete"]
        == all(alignment[field] for field in (
            "rowIdentity",
            "symbolIdentity",
            "treeIdentity",
            "truthPathIdentity",
        ))
        == metrics["alignmentComplete"],
        f"{artifact_path}: alignment claims differ",
    )
    audit = value["protocolAudit"]
    for field in (
        "decoderFeatureAuditPass",
        "trainingLeakageAuditPass",
        "quantizedEvaluationPass",
    ):
        _require(
            audit[field] == metrics[field],
            f"{artifact_path}: protocol audit and metric differ for {field}",
        )

    contract_partitions = experiment["protocol"]["partitions"]
    expected_partition_segments = {
        partition["id"]: (
            partition["endSegmentExclusive"] - partition["firstSegment"]
        )
        for partition in contract_partitions
    }
    partition_rows = {row["id"]: row for row in value["partitions"]}
    _require(
        set(partition_rows) == set(expected_partition_segments),
        f"{artifact_path}: result partitions differ from frozen protocol",
    )
    for partition_id, segment_count in expected_partition_segments.items():
        row = partition_rows[partition_id]
        _require(
            row["segments"] == segment_count,
            f"{artifact_path}: partition size differs for {partition_id}",
        )
        _require(
            math.isclose(
                row["gainIdealBits"],
                row["baseIdealBits"] - row["correctedIdealBits"],
                rel_tol=1e-12,
                abs_tol=1e-9,
            )
            and math.isclose(
                row["shiftedControlGainIdealBits"],
                row["baseIdealBits"] - row["shiftedControlIdealBits"],
                rel_tol=1e-12,
                abs_tol=1e-9,
            ),
            f"{artifact_path}: partition gain arithmetic differs for {partition_id}",
        )
    _require(
        metrics["validationIdealGainBits"] == partition_rows["validation"]["gainIdealBits"]
        and metrics["testIdealGainBits"] == partition_rows["test"]["gainIdealBits"]
        and metrics["testShiftedControlGainBits"]
        == partition_rows["test"]["shiftedControlGainIdealBits"],
        f"{artifact_path}: summary gains differ from partition evidence",
    )
    _require(
        metrics["testThirdMinIdealGainBits"]
        == min(metrics["testThirdIdealGainBits"]),
        f"{artifact_path}: minimum test-third gain differs",
    )
    _require(
        math.isclose(
            metrics["testOverShiftedControlBits"],
            metrics["testIdealGainBits"] - metrics["testShiftedControlGainBits"],
            rel_tol=1e-12,
            abs_tol=1e-9,
        ),
        f"{artifact_path}: shifted-control margin differs",
    )
    test_segments = expected_partition_segments["test"]
    _require(
        metrics["testPositiveSegments"] + metrics["testNegativeSegments"]
        <= test_segments
        and math.isclose(
            metrics["testPositiveSegmentFraction"],
            metrics["testPositiveSegments"] / test_segments,
            rel_tol=1e-15,
            abs_tol=0.0,
        ),
        f"{artifact_path}: test segment-sign evidence differs",
    )

    model = value["model"]
    model_path = _project_file_reference(model["payload"], f"{artifact_path}: model")
    _require(
        model_path.stat().st_size == model["bytes"]
        == metrics["modelPayloadBytes"]
        and model["dimension"] == experiment["protocol"]["parameters"]["dimension"],
        f"{artifact_path}: model payload accounting differs",
    )

    expected_gate_rows: list[dict[str, Any]] = []
    for gate in experiment["gates"]:
        predicates: list[dict[str, Any]] = []
        for predicate in gate["all"]:
            observed = metrics[predicate["metric"]]
            passed = _predicate_pass(
                observed,
                predicate["operator"],
                predicate["threshold"],
            )
            predicates.append({**predicate, "observed": observed, "pass": passed})
        expected_gate_rows.append(
            {
                "id": gate["id"],
                "pass": all(item["pass"] for item in predicates),
                "predicates": predicates,
            }
        )
    _require(
        value["gateEvaluations"] == expected_gate_rows,
        f"{artifact_path}: gate evaluations differ from frozen predicates",
    )
    all_gates_pass = all(row["pass"] for row in expected_gate_rows)
    expected_status = "pass" if all_gates_pass else "fail"
    expected_verdict = (
        "authorize-open-base-integration"
        if all_gates_pass
        else "retire-hashed-linear-probe"
    )
    _require(
        value["status"] == expected_status
        and value["decision"]["verdict"] == expected_verdict,
        f"{artifact_path}: status or decision differs from gate evidence",
    )
    return {
        "experimentId": value["experimentId"],
        "status": value["status"],
        "verdict": value["decision"]["verdict"],
    }


def _validate_mechanism_graph(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    components = {component["id"]: component for component in value["components"]}
    _require(
        len(components) == len(value["components"]),
        f"{artifact_path}: duplicate component identity",
    )
    for component in components.values():
        if component["role"] != "open-codec":
            _require(
                component["scoreCreditBytes"] == 0,
                f"{artifact_path}: non-codec component received score credit",
            )
        for evidence in component["evidence"]:
            _project_file_reference(
                evidence,
                f"{artifact_path}: component {component['id']}",
            )

    interaction_ids: set[str] = set()
    for interaction in value["interactions"]:
        _require(
            interaction["id"] not in interaction_ids,
            f"{artifact_path}: duplicate interaction identity",
        )
        interaction_ids.add(interaction["id"])
        _require(
            set(interaction["components"]).issubset(components),
            f"{artifact_path}: interaction references an unknown component",
        )
        if interaction["sharedProbabilityBoundary"] or interaction["overlappingCost"]:
            _require(
                interaction["jointReplayRequired"],
                f"{artifact_path}: shared boundary or cost requires joint replay",
            )

    composition = value["composition"]
    selected = [components[component_id] for component_id in composition["componentIds"]]
    _require(
        len(selected) == len(composition["componentIds"]),
        f"{artifact_path}: composition references an unknown component",
    )
    exact_replay = composition["status"] == "exact-replay-present"
    _require(
        exact_replay == (composition["jointReplay"] is not None),
        f"{artifact_path}: exact composition status differs from joint replay",
    )
    if exact_replay:
        _require(
            composition["candidateId"] is not None and selected,
            f"{artifact_path}: exact composition lacks candidate or components",
        )
        _require(
            not any(component["closedTeacherDependency"] for component in selected),
            f"{artifact_path}: exact prize composition retains a closed teacher",
        )
        _project_receipt_reference(
            composition["jointReplay"],
            "gamma.enwiki9.run-receipt.v1",
            f"{artifact_path}: joint replay",
        )
    if any(component["state"] == "retired" for component in selected):
        _require(
            composition["status"] == "prohibited",
            f"{artifact_path}: composition includes a retired component",
        )
    if composition["status"] == "prohibited":
        _require(
            composition["candidateId"] is None,
            f"{artifact_path}: prohibited composition names a candidate",
        )
    return {
        "graphId": value["graphId"],
        "components": len(components),
        "compositionStatus": composition["status"],
    }


def validate_search_policy() -> dict[str, Any]:
    path = CONTRACT_ROOT / "search-policy.json"
    value = load_json(path)
    _validate_schema(value, SCHEMA_PATHS["gamma.enwiki9.search-policy.v1"])
    _validate_objective_binding(value["objective"], str(path))
    return value


def _validate_dependency_closure(
    value: dict[str, Any],
    artifact_path: Path,
    verify_files: bool,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    counted_files = value["countedFiles"]
    paths = [record["path"] for record in counted_files]
    _require(len(paths) == len(set(paths)), f"{artifact_path}: duplicate counted path")
    _require(
        value["entryPoint"] in set(paths),
        f"{artifact_path}: entry point is not a counted file",
    )
    _require(
        sum(record["bytes"] for record in counted_files) == value["totalPackageBytes"],
        f"{artifact_path}: totalPackageBytes differs from counted file bytes",
    )
    _require(
        candidate_tree_digest(counted_files) == value["candidateTreeSha256"],
        f"{artifact_path}: candidate tree digest differs from counted files",
    )

    dependency_keys = [
        (dependency["name"], dependency["provider"])
        for dependency in value["dependencies"]
    ]
    _require(
        len(dependency_keys) == len(set(dependency_keys)),
        f"{artifact_path}: duplicate dependency identity",
    )
    uncounted = [
        dependency["name"]
        for dependency in value["dependencies"]
        if not dependency["counted"]
        and dependency["kind"] not in UNCOUNTED_PLATFORM_DEPENDENCY_KINDS
    ]
    unresolved = list(value["missing"]) + [
        f"uncounted dependency: {name}" for name in uncounted
    ]
    if value["complete"]:
        _require(not unresolved, f"{artifact_path}: complete closure has unresolved inputs")
    else:
        _require(
            bool(unresolved),
            f"{artifact_path}: incomplete closure does not identify what is missing",
        )

    if verify_files:
        candidate_root = _relative_path(
            artifact_path.parent,
            value["candidateRoot"],
            f"{artifact_path}: candidateRoot",
        )
        _require(candidate_root.is_dir(), f"{artifact_path}: candidate root is missing")
        actual_paths: list[str] = []
        for path in sorted(candidate_root.rglob("*")):
            relative_path = path.relative_to(candidate_root).as_posix()
            _require(
                not path.is_symlink(),
                f"{artifact_path}: candidate tree contains symlink: {relative_path}",
            )
            if path.is_file():
                actual_paths.append(relative_path)
        _require(
            actual_paths == sorted(paths),
            f"{artifact_path}: counted files do not exactly cover the candidate root",
        )
        for record in counted_files:
            _verify_file_record(
                candidate_root,
                record,
                f"{artifact_path}: countedFiles",
            )

    return {
        "candidateId": value["candidateId"],
        "complete": value["complete"],
        "filesVerified": verify_files,
        "totalPackageBytes": value["totalPackageBytes"],
    }


def _resource_guard_checks(value: dict[str, Any]) -> dict[str, bool]:
    objective = validate_objective()
    resources = objective["resources"]
    wall_time_complete = value["wall_time_measurement_complete"]
    wall_time_pass = (
        wall_time_complete
        and not value["wall_time_exceeded"]
        and value["wall_time_limit_seconds"] is not None
        and value["elapsed_s"] < value["wall_time_limit_seconds"]
    )
    memory_pass = (
        value["limit_mode"] == "tree"
        and value["official_decimal_limit_kib"]
        == resources["memory"]["linuxGuardKiB"]
        and not value["rss_guard_exceeded"]
        and not value["official_decimal_memory_exceeded"]
        and value["max_sampled_tree_rss_kib"]
        < resources["memory"]["linuxGuardKiB"]
    )
    temporary_disk_pass = (
        value["temporary_disk_measurement_complete"]
        and value["temporary_disk_limit_bytes"]
        == resources["temporaryDisk"]["maximumBytes"]
        and not value["temporary_disk_guard_exceeded"]
        and value["max_sampled_temporary_disk_bytes"]
        < resources["temporaryDisk"]["maximumBytes"]
    )
    single_core_pass = (
        value["max_logical_cpus"]
        == resources["cpu"]["maximumPhysicalCores"]
        and value["affinity_measurement_complete"]
        and not value["logical_cpu_guard_exceeded"]
        and 0 < value["max_sampled_allowed_cpu_count"] <= 1
    )
    command_pass = value["status"] == "complete" and value["returncode"] == 0
    return {
        "command": command_pass,
        "memory": memory_pass,
        "singleCore": single_core_pass,
        "temporaryDisk": temporary_disk_pass,
        "wallTime": wall_time_pass,
    }


def _validate_resource_guard(
    value: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    objective = validate_objective()
    score = value["geekbench5_single_core_score"]
    expected_wall_limit = (
        objective["resources"]["wallTime"]["maximumSecondsNumerator"] / score
        if score is not None
        else None
    )
    _require(
        value["wall_time_measurement_complete"]
        == (value["phase"] in {"compression", "decompression"} and score is not None),
        f"{artifact_path}: wall-time completeness differs from phase and score evidence",
    )
    if expected_wall_limit is None:
        _require(
            value["wall_time_limit_seconds"] is None,
            f"{artifact_path}: wall-time limit lacks a Geekbench score",
        )
    else:
        _require(
            value["wall_time_limit_seconds"] is not None
            and math.isclose(
                value["wall_time_limit_seconds"],
                expected_wall_limit,
                rel_tol=1e-12,
            ),
            f"{artifact_path}: wall-time limit differs from the objective formula",
        )

    official_limit = value["official_decimal_limit_kib"]
    expected_over = (
        max(0, value["max_sampled_tree_rss_kib"] - official_limit)
        if official_limit is not None
        else None
    )
    _require(
        value["official_decimal_over_limit_kib"] == expected_over,
        f"{artifact_path}: official memory overage is inconsistent",
    )
    expected_flags = {
        "rss_guard_exceeded": (
            value["max_sampled_tree_rss_kib"] > value["limit_kib"]
            if value["limit_mode"] == "tree"
            else value["max_sampled_single_rss_kib"] > value["limit_kib"]
        ),
        "official_decimal_memory_exceeded": (
            official_limit is not None
            and value["max_sampled_tree_rss_kib"] >= official_limit
        ),
        "temporary_disk_guard_exceeded": (
            value["temporary_disk_limit_bytes"] is not None
            and value["max_sampled_temporary_disk_bytes"]
            >= value["temporary_disk_limit_bytes"]
        ),
        "logical_cpu_guard_exceeded": (
            value["max_logical_cpus"] is not None
            and value["max_sampled_allowed_cpu_count"] > value["max_logical_cpus"]
        ),
        "wall_time_exceeded": (
            value["wall_time_limit_seconds"] is not None
            and value["elapsed_s"] >= value["wall_time_limit_seconds"]
        ),
    }
    if value["status"] != "running":
        for field, expected in expected_flags.items():
            _require(
                value[field] == expected,
                f"{artifact_path}: {field} is inconsistent with measured maxima",
            )
        expected_status = "complete"
        for field, status in (
            ("rss_guard_exceeded", "rss_guard_exceeded"),
            (
                "official_decimal_memory_exceeded",
                "aborted_official_decimal_memory_limit",
            ),
            ("temporary_disk_guard_exceeded", "temporary_disk_guard_exceeded"),
            ("logical_cpu_guard_exceeded", "logical_cpu_guard_exceeded"),
            ("wall_time_exceeded", "wall_time_guard_exceeded"),
        ):
            if value[field]:
                expected_status = status
                break
        _require(
            value["status"] == expected_status,
            f"{artifact_path}: status differs from guard flags",
        )
        _require(value["returncode"] is not None, f"{artifact_path}: final receipt lacks return code")
    else:
        _require(value["returncode"] is None, f"{artifact_path}: running receipt has return code")

    checks = _resource_guard_checks(value)
    return {
        "checks": checks,
        "phase": value["phase"],
        "promotionReady": all(checks.values()),
        "status": value["status"],
    }


def _verify_reference(
    receipt_path: Path,
    reference: dict[str, Any],
    expected_schema: str,
    verify_files: bool,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    path = _relative_path(receipt_path.parent, reference["path"], str(receipt_path))
    _require(path.is_file(), f"{receipt_path}: referenced receipt is missing: {path}")
    _require(
        f"sha256:{file_digest(path, 'sha256')}" == reference["sha256"],
        f"{receipt_path}: referenced receipt digest differs: {path}",
    )
    value = load_json(path)
    _require(
        value.get("schema") == expected_schema,
        f"{receipt_path}: referenced receipt has the wrong schema: {path}",
    )
    result = validate_artifact(path, verify_files=verify_files)
    return path, value, result


def _verify_run_artifact(
    receipt_path: Path,
    record: dict[str, Any],
    context: str,
) -> None:
    _verify_file_record(receipt_path.parent, record, context)


def _validate_run_receipt(
    value: dict[str, Any],
    artifact_path: Path,
    verify_files: bool,
) -> dict[str, Any]:
    _validate_objective_binding(value["objective"], str(artifact_path))
    binding = objective_binding()
    _require(
        value["corpus"]["bytes"] == binding["corpusBytes"]
        and value["corpus"]["sha256"] == binding["corpusSha256"],
        f"{artifact_path}: corpus is not the canonical full enwik9",
    )
    _require(
        value["correctness"]["restored"]["bytes"] == binding["corpusBytes"]
        and value["correctness"]["restored"]["sha256"] == binding["corpusSha256"],
        f"{artifact_path}: restored corpus identity differs from the objective",
    )

    manifest_reference = {
        "path": value["package"]["manifestPath"],
        "sha256": value["package"]["manifestSha256"],
    }
    _, manifest, manifest_result = _verify_reference(
        artifact_path,
        manifest_reference,
        "gamma.enwiki9.dependency-closure.v1",
        verify_files,
    )
    _require(
        manifest["candidateId"] == value["candidateId"]
        and manifest["candidateTreeSha256"] == value["candidateTreeSha256"],
        f"{artifact_path}: package manifest identifies a different candidate",
    )
    _require(
        value["package"]["bytes"] == manifest["totalPackageBytes"],
        f"{artifact_path}: package bytes differ from dependency closure",
    )
    _require(
        value["package"]["dependencyClosureComplete"] == manifest["complete"],
        f"{artifact_path}: package closure status differs from its manifest",
    )

    accounting = value["accounting"]
    expected_score = (
        accounting["packageBytes"]
        + accounting["archiveBytes"]
        + accounting["requiredOptionBytes"]
    )
    _require(
        accounting["packageBytes"] == value["package"]["bytes"],
        f"{artifact_path}: accounting package bytes differ",
    )
    _require(
        accounting["archiveBytes"] == value["archive"]["bytes"],
        f"{artifact_path}: accounting archive bytes differ",
    )
    _require(
        accounting["requiredOptionBytes"] == manifest["requiredOptionBytes"],
        f"{artifact_path}: required option bytes differ",
    )
    _require(
        accounting["officialScoreBytes"] == expected_score,
        f"{artifact_path}: official score formula differs",
    )
    _require(
        accounting["targetDebtBytes"]
        == accounting["officialScoreBytes"] - binding["targetScoreBytes"],
        f"{artifact_path}: target debt differs from the objective",
    )
    _require(
        accounting["complete"] == manifest["complete"],
        f"{artifact_path}: complete accounting requires complete dependency closure",
    )

    _, compression_guard, compression_result = _verify_reference(
        artifact_path,
        value["resources"]["compressionGuard"],
        "gamma.enwiki9.resource-guard-receipt.v2",
        verify_files,
    )
    _, decompression_guard, decompression_result = _verify_reference(
        artifact_path,
        value["resources"]["decompressionGuard"],
        "gamma.enwiki9.resource-guard-receipt.v2",
        verify_files,
    )
    _require(
        compression_guard["phase"] == "compression",
        f"{artifact_path}: compression guard has wrong phase",
    )
    _require(
        decompression_guard["phase"] == "decompression",
        f"{artifact_path}: decompression guard has wrong phase",
    )
    guard_results = (compression_result["checks"], decompression_result["checks"])
    expected_resources = {
        "wallTimePass": all(result["wallTime"] for result in guard_results),
        "memoryPass": all(result["memory"] for result in guard_results),
        "temporaryDiskPass": all(
            result["temporaryDisk"] for result in guard_results
        ),
        "singleCorePass": all(result["singleCore"] for result in guard_results),
    }
    for field, expected in expected_resources.items():
        _require(
            value["resources"][field] == expected,
            f"{artifact_path}: {field} differs from guard evidence",
        )
    expected_resource_complete = all(expected_resources.values()) and all(
        result["command"] for result in guard_results
    )
    _require(
        value["resources"]["complete"] == expected_resource_complete,
        f"{artifact_path}: resource completeness differs from guard evidence",
    )

    if verify_files:
        _verify_run_artifact(artifact_path, value["corpus"], "corpus")
        _verify_run_artifact(artifact_path, value["archive"], "archive")
        _verify_run_artifact(
            artifact_path,
            value["correctness"]["restored"],
            "restored corpus",
        )

    correctness = value["correctness"]
    distribution = value["distribution"]
    objective_criteria = [
        accounting["complete"],
        accounting["officialScoreBytes"] <= binding["targetScoreBytes"],
        value["package"]["dependencyClosureComplete"],
        correctness["roundtripOk"],
        correctness["determinismOk"],
        correctness["independentDecodeOk"],
        value["resources"]["complete"],
        distribution["selfContained"],
        distribution["cleanRoomReplayOk"],
        not distribution["networkUsed"],
        not distribution["gpuUsed"],
        not distribution["hiddenInputs"],
        distribution["licenseAuditOk"],
        value["verification"]["crossHostArchiveIdentityOk"],
    ]
    if value["verdict"] == "objective-achieved":
        _require(
            all(objective_criteria),
            f"{artifact_path}: objective-achieved verdict lacks required evidence",
        )
    return {
        "candidateId": value["candidateId"],
        "filesVerified": verify_files and manifest_result["filesVerified"],
        "officialScoreBytes": accounting["officialScoreBytes"],
        "objectiveCriteriaPass": all(objective_criteria),
        "verdict": value["verdict"],
    }


def validate_artifact(path: Path, verify_files: bool = True) -> dict[str, Any]:
    artifact_path = path.resolve()
    value = load_json(artifact_path)
    _require(isinstance(value, dict), f"{artifact_path}: artifact must be an object")
    schema_id = value.get("schema")
    _require(
        schema_id in SCHEMA_PATHS,
        f"{artifact_path}: unknown schema {schema_id!r}",
    )
    _validate_schema(value, SCHEMA_PATHS[schema_id])
    if schema_id == "gamma.enwiki9.adaptive-experiment-contract.v1":
        result = _validate_adaptive_experiment_contract(value, artifact_path)
    elif schema_id == "gamma.enwiki9.adaptive-job.v3":
        result = _validate_adaptive_job(value, artifact_path)
    elif schema_id == "gamma.enwiki9.algorithm-proposal.v2":
        result = _validate_algorithm_proposal(value, artifact_path)
    elif schema_id == "gamma.enwiki9.objective-contract.v1":
        _require(
            value == validate_objective(),
            f"{artifact_path}: objective differs from canonical contract",
        )
        result: dict[str, Any] = {"objectiveId": value["objectiveId"]}
    elif schema_id == "gamma.enwiki9.candidate-revision.v1":
        result = _validate_candidate_revision(value, artifact_path, verify_files)
    elif schema_id == "gamma.enwiki9.dependency-closure.v1":
        result = _validate_dependency_closure(value, artifact_path, verify_files)
    elif schema_id == "gamma.enwiki9.delta-midas-probe-result.v1":
        result = _validate_delta_midas_probe_result(value, artifact_path)
    elif schema_id == "gamma.enwiki9.experiment-contract.v1":
        result = _validate_experiment_contract(value, artifact_path)
    elif schema_id == "gamma.enwiki9.experiment-result.v1":
        result = _validate_experiment_result(value, artifact_path)
    elif schema_id == "gamma.enwiki9.mechanism-graph.v1":
        result = _validate_mechanism_graph(value, artifact_path)
    elif schema_id == "gamma.enwiki9.resource-guard-receipt.v2":
        result = _validate_resource_guard(value, artifact_path)
    elif schema_id == "gamma.enwiki9.reflection-receipt.v1":
        result = _validate_reflection_receipt(value, artifact_path)
    elif schema_id == "gamma.enwiki9.search-policy.v1":
        _require(
            value == validate_search_policy(),
            f"{artifact_path}: search policy differs from canonical policy",
        )
        result = {"ordering": value["ordering"]}
    elif schema_id == "gamma.enwiki9.run-receipt.v1":
        result = _validate_run_receipt(value, artifact_path, verify_files)
    else:
        raise AssertionError(schema_id)
    return {"path": str(path), "schema": schema_id, "valid": True, **result}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify-corpus",
        action="store_true",
        help="also hash the local one-billion-byte corpus",
    )
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help="validate receipt structure without hashing referenced payload files",
    )
    parser.add_argument("artifacts", nargs="*", type=Path)
    args = parser.parse_args()
    try:
        validate_schemas()
        binding = objective_binding(args.verify_corpus)
        artifacts = [
            validate_artifact(path, verify_files=not args.structure_only)
            for path in args.artifacts
        ]
    except (OSError, ValueError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
        print(f"research contract validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                **binding,
                "artifacts": artifacts,
                "corpusVerified": args.verify_corpus,
                "valid": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
