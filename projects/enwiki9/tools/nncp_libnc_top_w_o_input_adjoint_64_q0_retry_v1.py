#!/usr/bin/env python3
"""Finalize the completed layer-19 w_o source capture without rerunning it."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_ff1_bias_state_reduce_64_q0 as oracle
import nncp_libnc_top_w_o_input_adjoint_64_q0_v1 as source
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
SOURCE_ID = "nncp_libnc_top_w_o_input_adjoint_64_q0_v1"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_WORK = SOURCE_RESULT / "work"
SOURCE_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{SOURCE_ID}.json"
SOURCE_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T160641Z_9c2e81181b.json"
)
SOURCE_STAGED = SOURCE_RESULT / "decision.precleanup.json"
SOURCE_EXECUTION = SOURCE_RESULT / "execution.json"
SOURCE_GUARD = SOURCE_RESULT / "guard.json"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T160641Z_9c2e81181b.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
ARTIFACT_NAMES = (
    "source-w-o-input.bf16",
    "source-w-o-input-adjoint.bf16",
    "source-initial-w-o-19.bf16",
)
SOURCE_PACKAGE = SOURCE_RESULT / "incremental_source.tar.xz"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"reference is not a project file: {path}")
    result = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        result["id"] = identifier
    return result


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
        raise ValueError("top w_o receipt-salvage source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("source-experiment", SOURCE_EXPERIMENT),
        ("source-failed-job", SOURCE_JOB),
        ("source-staged-decision", SOURCE_STAGED),
        ("source-execution", SOURCE_EXECUTION),
        ("source-guard", SOURCE_GUARD),
        ("source-reflection", SOURCE_REFLECTION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("source-incremental-package", SOURCE_PACKAGE),
        *(
            (name.removesuffix(".bf16"), SOURCE_RESULT / name)
            for name in ARTIFACT_NAMES
        ),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    job = json.loads(SOURCE_JOB.read_text())
    staged = json.loads(SOURCE_STAGED.read_text())
    guard = json.loads(SOURCE_GUARD.read_text())
    reflection = json.loads(SOURCE_REFLECTION.read_text())
    if not (
        job["state"] == "failed"
        and job["returncode"] == 1
        and staged["candidateId"] == SOURCE_ID
        and staged["promotionPass"] is False
        and staged["killPass"] is False
        and staged["decision"] == "retry"
        and staged["measurements"]["sourceCaptureDeterministic"] is True
        and staged["measurements"]["declaredProbePopulationExact"] is True
        and staged["measurements"]["fixturePayloadMismatchCount"] == 0
        and staged["measurements"]["inputLive"] is True
        and staged["measurements"]["adjointLive"] is True
        and staged["measurements"]["guardedWorkRootPass"] is False
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
        and reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
    ):
        raise ValueError("top w_o receipt-salvage antecedents are not satisfied")


def build_result(
    experiment_path: Path,
    experiment: dict[str, Any],
    revision: dict[str, Any],
    measurements: dict[str, bool | int | float],
    artifacts: list[dict[str, str]],
) -> dict[str, Any]:
    promotion = oracle.evaluate(experiment["promotionPredicates"], measurements)
    kill = oracle.evaluate(experiment["killPredicates"], measurements)
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
        raise ValueError("job and top w_o receipt-salvage bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("top w_o receipt-salvage result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("top w_o receipt-salvage work root is not fresh")
    if not SOURCE_WORK.is_dir():
        raise ValueError("completed source work root is unavailable for salvage")

    source_execution = json.loads(SOURCE_EXECUTION.read_text())
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    raw_manifest_exact = True
    raw_probe_exact = True
    raw_non_probe_identical = True
    raw_probe_mismatches = 0
    raw_verifications: list[dict[str, Any]] = []
    sealed_input = SOURCE_RESULT / "source-w-o-input.bf16"
    sealed_adjoint = SOURCE_RESULT / "source-w-o-input-adjoint.bf16"
    for index, label in enumerate(("a", "b")):
        directory = SOURCE_WORK / f"capture-{label}"
        observed_manifest = source.source_capture.capture.base.directory_manifest(
            directory
        )
        manifest_exact = observed_manifest == source_execution["captureManifests"][
            index
        ]
        identity = source.fixture_identity(observed_manifest, parent_manifest)
        combined_input = WORK / f"{label}-source-w-o-input.bf16"
        combined_adjoint = WORK / f"{label}-source-w-o-input-adjoint.bf16"
        source.combine_probe(directory, "input", combined_input)
        source.combine_probe(directory, "adjoint", combined_adjoint)
        input_mismatches, input_maximum = source.source_capture.compare_bf16(
            combined_input, sealed_input
        )
        adjoint_mismatches, adjoint_maximum = source.source_capture.compare_bf16(
            combined_adjoint, sealed_adjoint
        )
        raw_manifest_exact = raw_manifest_exact and manifest_exact
        raw_probe_exact = (
            raw_probe_exact and identity["declaredProbePopulationExact"]
        )
        raw_non_probe_identical = (
            raw_non_probe_identical and identity["nonProbeIdentical"]
        )
        raw_probe_mismatches += input_mismatches + adjoint_mismatches
        raw_verifications.append(
            {
                "capture": label,
                "manifestExact": manifest_exact,
                "fixtureIdentity": identity,
                "inputMismatchCount": input_mismatches,
                "maximumInputAbsoluteError": input_maximum,
                "adjointMismatchCount": adjoint_mismatches,
                "maximumAdjointAbsoluteError": adjoint_maximum,
            }
        )

    staged = json.loads(SOURCE_STAGED.read_text())
    matrix_digest_exact = (
        sha256(SOURCE_RESULT / "source-initial-w-o-19.bf16")
        == source_execution["initialMatrix"]["sha256"]
    )
    copied: dict[str, Path] = {}
    for name in ARTIFACT_NAMES:
        destination = RESULT / name
        shutil.copyfile(SOURCE_RESULT / name, destination)
        copied[name.removesuffix(".bf16")] = destination
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "matrixDigestExact": matrix_digest_exact,
                "rawCaptureVerification": raw_verifications,
                "sourceExecution": reference(SOURCE_EXECUTION),
                "sourceStagedDecision": reference(SOURCE_STAGED),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    source_work_bytes = sum(
        path.stat().st_size for path in SOURCE_WORK.rglob("*") if path.is_file()
    )
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": staged["measurements"]["captureCount"],
        "sampleCount": staged["measurements"]["sampleCount"],
        "sourceInputElementCount": staged["measurements"][
            "sourceInputElementCount"
        ],
        "sourceAdjointElementCount": staged["measurements"][
            "sourceAdjointElementCount"
        ],
        "initialMatrixElementCount": staged["measurements"][
            "initialMatrixElementCount"
        ],
        "sourceCaptureDeterministic": staged["measurements"][
            "sourceCaptureDeterministic"
        ],
        "declaredProbeFileCount": staged["measurements"][
            "declaredProbeFileCount"
        ],
        "declaredProbePopulationExact": raw_probe_exact,
        "fixturePayloadIdentical": raw_non_probe_identical,
        "fixturePayloadMismatchCount": sum(
            len(row["fixtureIdentity"]["nonProbeMismatches"])
            for row in raw_verifications
        ),
        "inputLive": staged["measurements"]["inputLive"],
        "adjointLive": staged["measurements"]["adjointLive"],
        "rawCaptureManifestExact": raw_manifest_exact,
        "rawProbeTensorMismatchCount": raw_probe_mismatches,
        "initialMatrixDigestExact": matrix_digest_exact,
        "resourceGuardsPass": True,
        "sourceWorkBytesBeforeCleanup": source_work_bytes,
        "sourceWorkRootRemoved": False,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": False,
    }
    artifacts = [
        reference(execution_path, "execution"),
        *(
            reference(path, identifier)
            for identifier, path in sorted(copied.items())
        ),
        reference(incremental_source, "incremental-source-package"),
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
