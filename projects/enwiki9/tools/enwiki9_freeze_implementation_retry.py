#!/usr/bin/env python3
"""Freeze an implementation retry without drifting scientific predicates."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"artifact must be a project file: {path}")
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    result = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{digest}",
    }
    if identifier is not None:
        result["id"] = identifier
    return result


def parse_evidence(specification: str) -> tuple[str, Path]:
    if "=" not in specification:
        raise ValueError("--evidence must use ID=PROJECT_PATH")
    identifier, path = specification.split("=", 1)
    if not identifier or not path:
        raise ValueError("--evidence must use ID=PROJECT_PATH")
    return identifier, Path(path)


def parse_measurement(specification: str) -> dict[str, str]:
    parts = specification.split("=", 2)
    if len(parts) != 3 or not all(parts):
        raise ValueError(
            "--additional-measurement must use ID=UNIT=DEFINITION"
        )
    identifier, unit, definition = parts
    return {"id": identifier, "unit": unit, "definition": definition}


def source_identifier(path: Path) -> str:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    digest = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"python-source-{path.stem}-{digest}"


def freeze(args: argparse.Namespace) -> dict[str, Any]:
    parent_experiment_path = args.parent_experiment.resolve()
    research_contracts.validate_artifact(parent_experiment_path)
    parent_experiment = load_object(parent_experiment_path)
    if parent_experiment["schema"] != "gamma.enwiki9.adaptive-experiment-contract.v1":
        raise ValueError("parent is not an adaptive experiment contract")
    parent_proposal_id = parent_experiment["proposalId"]

    revision_path = args.parent_revision.resolve()
    revision_result = research_contracts.validate_artifact(revision_path)
    revision = load_object(revision_path)
    if revision_result["candidateId"] != parent_proposal_id:
        raise ValueError("parent revision and experiment identify different candidates")

    experiment = copy.deepcopy(parent_experiment)
    experiment["experimentId"] = args.experiment_id
    experiment["proposalId"] = args.candidate_id
    experiment["parent"] = {
        "candidateId": parent_proposal_id,
        "revision": reference(revision_path),
    }
    experiment["changedMechanism"] = args.changed_mechanism

    inherited_source_ids = {
        item["id"]
        for item in experiment["inputs"]
        if item["id"].startswith("python-source-")
    }
    retained_inputs = [
        value
        for value in experiment["inputs"]
        if value["id"] not in {"runner", "materializer"}
        and value["id"] not in inherited_source_ids
    ]
    evidence = [
        reference(path, identifier)
        for identifier, path in map(parse_evidence, args.evidence)
    ]
    input_ids = [value["id"] for value in retained_inputs]
    for value in evidence:
        if value["id"] in input_ids:
            raise ValueError(f"duplicate inherited evidence id: {value['id']}")
        input_ids.append(value["id"])
    experiment.pop("pythonSourceClosureEntries", None)
    experiment["inputs"] = [
        reference(args.runner, "runner"),
        reference(args.materializer, "materializer"),
        *retained_inputs,
        *evidence,
    ]
    bind_python_source_closure = args.bind_python_source_closure or all(
        path.suffix == ".py" for path in (args.runner, args.materializer)
    )
    if bind_python_source_closure:
        existing_paths = {value["path"] for value in experiment["inputs"]}
        for path in local_source_closure((args.runner, args.materializer)):
            relative = path.relative_to(ROOT).as_posix()
            if relative not in existing_paths:
                experiment["inputs"].append(reference(path, source_identifier(path)))
                existing_paths.add(relative)
        experiment["pythonSourceClosureEntries"] = ["runner", "materializer"]
    measurement_ids = {value["id"] for value in experiment["measurements"]}
    for specification in args.additional_measurement:
        measurement = parse_measurement(specification)
        if measurement["id"] in measurement_ids:
            raise ValueError(
                f"duplicate implementation-retry measurement: {measurement['id']}"
            )
        experiment["measurements"].append(measurement)
        measurement_ids.add(measurement["id"])
    experiment["controls"] = [
        *experiment["controls"],
        {
            "id": args.negative_control_id,
            "role": "negative",
            "definition": args.negative_control_definition,
        },
    ]
    experiment["outputs"] = [
        value.replace(parent_proposal_id, args.candidate_id)
        for value in experiment["outputs"]
    ]
    for output in args.additional_output:
        if output in experiment["outputs"]:
            raise ValueError(f"duplicate implementation-retry output: {output}")
        experiment["outputs"].append(output)
    experiment["outputManifestPolicy"] = "complete-result-artifacts-v1"
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )

    destination = args.output.resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite frozen contract: {destination}")
    if ROOT.resolve() not in destination.parents:
        raise ValueError("output must remain inside the enwiki9 project")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(experiment, indent=2) + "\n")
    os.replace(temporary, destination)
    try:
        research_contracts.validate_artifact(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-experiment", type=Path, required=True)
    parser.add_argument("--parent-revision", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--materializer", type=Path, required=True)
    parser.add_argument("--changed-mechanism", required=True)
    parser.add_argument("--negative-control-id", required=True)
    parser.add_argument("--negative-control-definition", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--additional-output", action="append", default=[])
    parser.add_argument("--additional-measurement", action="append", default=[])
    parser.add_argument("--strict-output-manifest", action="store_true")
    parser.add_argument("--bind-python-source-closure", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
