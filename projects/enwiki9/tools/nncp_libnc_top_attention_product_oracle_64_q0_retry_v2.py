#!/usr/bin/env python3
"""Finalize complete top-attention captures without teacher replay."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_attention_product_oracle_64_q0_v1 as source
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
SOURCE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_retry_v1"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_WORK = SOURCE_RESULT / "work"
SOURCE_EXPERIMENT = ROOT / (
    f"operations/adaptive/experiments/{SOURCE_ID}.json"
)
SOURCE_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T172814Z_45054e4c3f.json"
)
SOURCE_LOG = ROOT / "run_logs/adaptive/20260816T172814Z_45054e4c3f.log"
SOURCE_GUARD = SOURCE_RESULT / "guard.json"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T172814Z_45054e4c3f.json"
)
SEALED_MANIFESTS = SOURCE_RESULT / "sealed-capture-manifests.json"
OPEN_PRE_W_O = source.OPEN_PRE_W_O
FIXTURE_MANIFEST = source.FIXTURE_MANIFEST
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SOURCE_CEILING = 2_000_000
GEOMETRY = {
    "attended": ("128,1,8,32", source.ATTENDED_ELEMENTS),
    "probability": ("320,1,8,32", source.PROBABILITY_ELEMENTS),
}


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return source.reference(path, identifier)


def combine_probe(directory: Path, kind: str, phase: str, output: Path) -> None:
    dimensions, elements = GEOMETRY[kind]
    bytes_per_state = elements * 2 // source.STATES
    with output.open("wb") as destination:
        for state in range(source.STATES):
            stem = f"top_attn_{kind}_{phase}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": kind,
                "phase": phase,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": dimensions,
                "byte_order": "little",
            }
            observed_meta = (
                source.capture_base.source_capture.capture.parse_meta(metadata)
                if metadata.is_file()
                else None
            )
            if (
                not payload.is_file()
                or payload.stat().st_size != bytes_per_state
                or observed_meta != expected_meta
            ):
                raise ValueError(
                    f"preserved top attention {kind} {phase} differs: {state}"
                )
            with payload.open("rb") as raw:
                shutil.copyfileobj(raw, destination, 8 * 1024 * 1024)
    if output.stat().st_size != elements * 2:
        raise ValueError(f"combined top attention {kind} {phase} differs")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROGRAM_DESCRIPTOR.resolve(),
    ]
    members = sorted(
        set(members), key=lambda item: item.relative_to(ROOT).as_posix()
    )
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(
        lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    )
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise ValueError("top-attention salvage source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("source-experiment", SOURCE_EXPERIMENT),
        ("source-failed-job", SOURCE_JOB),
        ("source-log", SOURCE_LOG),
        ("source-guard", SOURCE_GUARD),
        ("source-reflection", SOURCE_REFLECTION),
        ("sealed-capture-manifests", SEALED_MANIFESTS),
        ("open-pre-w-o-input", OPEN_PRE_W_O),
        ("fixture-manifest", FIXTURE_MANIFEST),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"top-attention salvage input drifted: {identifier}")
    job = json.loads(SOURCE_JOB.read_text())
    guard = json.loads(SOURCE_GUARD.read_text())
    reflection = json.loads(SOURCE_REFLECTION.read_text())
    if not (
        job["state"] == "failed"
        and job["returncode"] == 1
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and guard["rss_guard_exceeded"] is False
        and guard["official_decimal_memory_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["classification"]
        == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
    ):
        raise ValueError("top-attention salvage antecedents are not satisfied")


def build_result(
    experiment_path: Path,
    experiment: dict[str, Any],
    revision: dict[str, Any],
    measurements: dict[str, bool | int | float],
    artifacts: list[dict[str, str]],
) -> dict[str, Any]:
    promotion = source.oracle.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = source.oracle.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    return {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": revision,
        "evidenceClass": experiment["evidenceClass"],
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": (
            "authorize-successor"
            if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": artifacts,
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    output = args.output.resolve()
    research_contracts.validate_artifact(experiment_path)
    experiment = json.loads(experiment_path.read_text())
    if experiment["proposalId"] != CANDIDATE_ID:
        raise ValueError("experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and top-attention salvage bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("top-attention salvage result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("top-attention salvage work root is not fresh")
    if not SOURCE_WORK.is_dir():
        raise ValueError("completed source work root is unavailable")

    frozen = json.loads(SEALED_MANIFESTS.read_text())
    capture_base = source.capture_base.source_capture.capture.base
    captures = [SOURCE_WORK / "capture-a", SOURCE_WORK / "capture-b"]
    manifests = [capture_base.directory_manifest(path) for path in captures]
    if frozen.get("captures") != manifests:
        raise ValueError("completed top-attention captures drifted after sealing")
    fixture = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [source.fixture_identity(row, fixture) for row in manifests]
    combined: list[dict[str, Path]] = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        paths: dict[str, Path] = {}
        for kind in ("attended", "probability"):
            for phase in ("input", "adjoint"):
                key = f"{kind}-{phase}"
                path = WORK / f"{label}-{key}.bf16"
                combine_probe(directory, kind, phase, path)
                paths[key] = path
        combined.append(paths)

    artifacts_by_key = {
        "attended-input": RESULT / "source-attended-heads-input.bf16",
        "attended-adjoint": RESULT / "source-attended-heads-adjoint.bf16",
        "probability-input": RESULT / "source-attention-probability-input.bf16",
        "probability-adjoint": RESULT
        / "source-attention-probability-adjoint.bf16",
    }
    for key, destination in artifacts_by_key.items():
        shutil.copyfile(combined[0][key], destination)
    direct_comparison = source.oracle.compare_bf16(
        combined[0]["attended-input"], OPEN_PRE_W_O
    )
    wrong_order = WORK / "head-major-control.bf16"
    source.attended_to_concat(combined[0]["attended-input"], wrong_order)
    control_comparison = source.oracle.compare_bf16(wrong_order, OPEN_PRE_W_O)
    repeat_identical = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
        and all(
            combined[0][key].read_bytes() == combined[1][key].read_bytes()
            for key in artifacts_by_key
        )
    )
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "captureManifests": manifests,
                "concatComparison": direct_comparison,
                "fixtureIdentity": identities,
                "frozenCaptureManifests": reference(
                    SEALED_MANIFESTS, "sealed-capture-manifests"
                ),
                "headMajorControlComparison": control_comparison,
                "observedTensorMetadata": {
                    "attended": "128,1,8,32",
                    "probability": "320,1,8,32",
                    "serialization": (
                        "state-major, stream-major, head-major, "
                        "feature-or-key-major"
                    ),
                },
                "teacherExecuted": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    source_work_bytes = sum(
        path.stat().st_size
        for path in SOURCE_WORK.rglob("*")
        if path.is_file()
    )
    guard = json.loads(SOURCE_GUARD.read_text())
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_mismatches = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "sampleCount": source.STATES * source.STREAMS,
        "attendedInputElementCount": artifacts_by_key[
            "attended-input"
        ].stat().st_size // 2,
        "attendedAdjointElementCount": artifacts_by_key[
            "attended-adjoint"
        ].stat().st_size // 2,
        "probabilityInputElementCount": artifacts_by_key[
            "probability-input"
        ].stat().st_size // 2,
        "probabilityAdjointElementCount": artifacts_by_key[
            "probability-adjoint"
        ].stat().st_size // 2,
        "sourceCaptureDeterministic": repeat_identical,
        "captureManifestsBound": True,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": probe_exact,
        "fixturePayloadIdentical": non_probe_mismatches == 0,
        "fixturePayloadMismatchCount": non_probe_mismatches,
        "attendedInputLive": any(
            artifacts_by_key["attended-input"].read_bytes()
        ),
        "attendedAdjointLive": any(
            artifacts_by_key["attended-adjoint"].read_bytes()
        ),
        "probabilityInputLive": any(
            artifacts_by_key["probability-input"].read_bytes()
        ),
        "probabilityAdjointLive": any(
            artifacts_by_key["probability-adjoint"].read_bytes()
        ),
        "concatSourceMismatchCount": direct_comparison["mismatchCount"],
        "maximumConcatAbsoluteError": direct_comparison[
            "maximumAbsoluteError"
        ],
        "headMajorControlMismatchCount": control_comparison["mismatchCount"],
        "teacherExecutionCount": 0,
        "resourceGuardsPass": (
            guard["rss_guard_exceeded"] is False
            and guard["official_decimal_memory_exceeded"] is False
            and guard["temporary_disk_guard_exceeded"] is False
        ),
        "sourceWorkBytesBeforeCleanup": source_work_bytes,
        "sourceWorkRootRemoved": False,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": False,
    }
    artifacts = [
        reference(execution_path, "execution"),
        *(
            reference(path, key)
            for key, path in artifacts_by_key.items()
        ),
        reference(source_closure, "incremental-source-package"),
    ]
    output.write_text(
        json.dumps(
            build_result(
                experiment_path, experiment, revision, measurements, artifacts
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    research_contracts.validate_artifact(output)
    shutil.rmtree(SOURCE_WORK)
    shutil.rmtree(WORK)
    measurements["sourceWorkRootRemoved"] = not SOURCE_WORK.exists()
    measurements["guardedWorkRootPass"] = not WORK.exists()
    result = build_result(
        experiment_path, experiment, revision, measurements, artifacts
    )
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
