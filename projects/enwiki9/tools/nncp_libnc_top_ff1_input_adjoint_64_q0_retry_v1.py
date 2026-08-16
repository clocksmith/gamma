#!/usr/bin/env python3
"""Correct the sealed top-FF1 probe fixture-manifest accounting."""

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
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
SOURCE_ID = "nncp_libnc_top_ff1_input_adjoint_64_q0_v1"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_DECISION = SOURCE_RESULT / "decision.json"
SOURCE_EXECUTION = SOURCE_RESULT / "execution.json"
SOURCE_GUARD = SOURCE_RESULT / "guard.json"
SOURCE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T121911Z_d066eaf1cf.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
ARTIFACT_NAMES = (
    "source-ff1-input.bf16",
    "source-ff1-input-adjoint.bf16",
    "source-initial-ff1-19.bf16",
)
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"artifact is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def expected_probe_paths() -> set[str]:
    return {
        f"top_ff1_{kind}_s{state:03d}.{extension}"
        for kind in ("input", "adjoint")
        for state in range(64)
        for extension in ("bin", "meta")
    }


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
        raise ValueError("FF1 manifest-correction source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("source-decision", SOURCE_DECISION),
        ("source-execution", SOURCE_EXECUTION),
        ("source-guard", SOURCE_GUARD),
        ("source-reflection", SOURCE_REFLECTION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        *(
            (name.removesuffix(".bf16"), SOURCE_RESULT / name)
            for name in ARTIFACT_NAMES
        ),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    decision = json.loads(SOURCE_DECISION.read_text())
    reflection = json.loads(SOURCE_REFLECTION.read_text())
    guard = json.loads(SOURCE_GUARD.read_text())
    if not (
        decision["promotionPass"] is False
        and decision["killPass"] is False
        and decision["decision"] == "retry"
        and decision["measurements"]["sourceCaptureDeterministic"] is True
        and decision["measurements"]["fixturePayloadMismatchCount"] == 512
        and decision["measurements"]["sourceInputMismatchCount"] == 0
        and decision["measurements"]["comparatorLive"] is True
        and reflection["validity"]["classification"] == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "inconclusive"
        and reflection["decision"]["verdict"] == "retry"
        and guard["returncode"] == 0
        and guard["rss_guard_exceeded"] is False
        and guard["temporary_disk_guard_exceeded"] is False
    ):
        raise ValueError("FF1 manifest-correction antecedents are not satisfied")


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
    if oracle.reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and manifest-correction experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("FF1 manifest-correction result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("FF1 manifest-correction work root is not fresh")

    source_decision = json.loads(SOURCE_DECISION.read_text())
    source_execution = json.loads(SOURCE_EXECUTION.read_text())
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    expected_probe = expected_probe_paths()
    corrected: list[dict[str, Any]] = []
    total_probe_files = 0
    total_non_probe_mismatches = 0
    probe_populations_exact = True
    for manifest in source_execution["captureManifests"]:
        probe_rows = {
            row["path"]
            for row in manifest["files"]
            if row["path"].startswith("top_ff1_")
        }
        observed_rows = {
            row["path"]: (row["bytes"], row["sha256"])
            for row in manifest["files"]
            if not row["path"].startswith("top_ff1_")
        }
        paths = sorted(set(parent_rows) | set(observed_rows))
        mismatches = [
            path
            for path in paths
            if parent_rows.get(path) != observed_rows.get(path)
        ]
        probe_exact = probe_rows == expected_probe
        corrected.append(
            {
                "nonProbeIdentical": not mismatches,
                "nonProbeMismatches": mismatches,
                "declaredProbeFileCount": len(probe_rows),
                "declaredProbePopulationExact": probe_exact,
            }
        )
        total_probe_files += len(probe_rows)
        total_non_probe_mismatches += len(mismatches)
        probe_populations_exact = probe_populations_exact and probe_exact
    recorded_paths = {
        path
        for identity in source_execution["fixtureIdentity"]
        for path in identity["mismatches"]
    }
    recorded_mismatches_are_probe_only = recorded_paths == expected_probe

    artifacts: dict[str, Path] = {}
    for name in ARTIFACT_NAMES:
        destination = RESULT / name
        shutil.copyfile(SOURCE_RESULT / name, destination)
        artifacts[name.removesuffix(".bf16")] = destination
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "correctedFixtureIdentity": corrected,
                "declaredProbeNamespace": "top_ff1_",
                "recordedMismatchesAreDeclaredProbeOnly": (
                    recorded_mismatches_are_probe_only
                ),
                "sourceDecision": reference(SOURCE_DECISION, "source-decision"),
                "sourceExecution": reference(SOURCE_EXECUTION, "source-execution"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)
    measurements = dict(source_decision["measurements"])
    measurements.update(
        {
            "fixturePayloadIdentical": total_non_probe_mismatches == 0,
            "fixturePayloadMismatchCount": total_non_probe_mismatches,
            "declaredProbeFileCount": total_probe_files,
            "declaredProbePopulationExact": probe_populations_exact,
            "recordedMismatchesAreDeclaredProbeOnly": (
                recorded_mismatches_are_probe_only
            ),
            "incrementalSourceBytes": source_closure.stat().st_size,
            "guardedWorkRootPass": not WORK.exists(),
        }
    )
    promotion = oracle.evaluate(experiment["promotionPredicates"], measurements)
    kill = oracle.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": oracle.reference(experiment_path),
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
        "artifacts": [
            reference(execution_path, "execution"),
            *(
                reference(path, identifier)
                for identifier, path in sorted(artifacts.items())
            ),
            reference(source_closure, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
