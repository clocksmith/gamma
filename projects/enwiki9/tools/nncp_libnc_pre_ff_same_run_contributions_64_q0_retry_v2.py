#!/usr/bin/env python3
"""Salvage and validate completed same-run source contribution captures."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_pre_ff_same_run_contributions_64_q0_v1 as science
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as comparator
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2"
SOURCE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
SOURCE_WORK = SOURCE_RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SALVAGE_MANIFEST = PROGRAM / "salvage-source-manifest.json"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2_materializer.py"
)
COMPOSER_SOURCE = ROOT / (
    "programs/nncp_libnc_pre_ff_same_run_contributions_64_q0_v1/"
    "compose_bf16.cpp"
)
PROBE_SOURCE = ROOT / (
    "programs/nncp_libnc_pre_ff_same_run_contributions_64_q0_v1/"
    "same_run_probe.c"
)
FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T152537Z_f7e75c364c.json"
)
FAILED_GUARD = SOURCE_RESULT / "guard.json"
FAILED_LOG = ROOT / "run_logs/adaptive/20260816T152537Z_f7e75c364c.log"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T152537Z_f7e75c364c.json"
)
SOURCE_INPUT = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
SOURCE_BRANCH = ROOT / (
    "results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2/"
    "source-pre-ff-norm-branch-adjoint.bf16"
)
STALE_OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
CORRECTED_OPEN_RESULT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
)
CORRECTED_OPEN_DIRECT = (
    CORRECTED_OPEN_RESULT / "open-final-norm-input-residual.bf16"
)
CORRECTED_OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json"
)
FIXTURE_MANIFEST = ROOT / (
    "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"
)
SOURCE_CEILING = 2_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return science.reference(path, identifier or path.stem)


def execute(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, check=False
    )
    receipt = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROGRAM_DESCRIPTOR.resolve(),
        SALVAGE_MANIFEST.resolve(),
        COMPOSER_SOURCE.resolve(),
        PROBE_SOURCE.resolve(),
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
        raise ValueError("same-run salvage source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> dict[str, Any]:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("failed-job", FAILED_JOB),
        ("failed-guard", FAILED_GUARD),
        ("failed-log", FAILED_LOG),
        ("failed-reflection", FAILED_REFLECTION),
        ("salvage-source-manifest", SALVAGE_MANIFEST),
        ("source-input", SOURCE_INPUT),
        ("sealed-source-total", SOURCE_TOTAL),
        ("sealed-source-branch", SOURCE_BRANCH),
        ("stale-open-direct", STALE_OPEN_DIRECT),
        ("corrected-open-decision", CORRECTED_OPEN_RESULT / "decision.json"),
        ("corrected-open-execution", CORRECTED_OPEN_RESULT / "execution.json"),
        ("corrected-open-guard", CORRECTED_OPEN_RESULT / "guard.json"),
        ("corrected-open-reflection", CORRECTED_OPEN_REFLECTION),
        ("corrected-open-direct", CORRECTED_OPEN_DIRECT),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("composer-source", COMPOSER_SOURCE),
        ("probe-source", PROBE_SOURCE),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", PROGRAM_DESCRIPTOR),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"same-run salvage input drifted: {identifier}")
    failed = json.loads(FAILED_JOB.read_text())
    guard = json.loads(FAILED_GUARD.read_text())
    reflection = json.loads(FAILED_REFLECTION.read_text())
    corrected = json.loads(
        (CORRECTED_OPEN_RESULT / "decision.json").read_text()
    )
    corrected_reflection = json.loads(CORRECTED_OPEN_REFLECTION.read_text())
    if not (
        failed["state"] == "failed"
        and failed["returncode"] == 1
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and not guard["rss_guard_exceeded"]
        and not guard["official_decimal_memory_exceeded"]
        and not guard["temporary_disk_guard_exceeded"]
        and reflection["validity"]["classification"]
        == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
        and corrected["promotionPass"] is True
        and corrected["measurements"][
            "sourceFinalNormResidualMismatchCount"
        ] == 0
        and corrected_reflection["validity"]["valid"] is True
        and corrected_reflection["hypothesis"]["verdict"] == "supported"
    ):
        raise ValueError("same-run salvage antecedents are not satisfied")
    return guard


def validate_salvage_manifest() -> tuple[list[dict[str, Any]], bool]:
    declared = json.loads(SALVAGE_MANIFEST.read_text())
    directory_manifest = (
        science.total_parent.source_parent.source_capture.base
        .directory_manifest
    )
    captures = [
        directory_manifest(SOURCE_WORK / label)
        for label in ("capture-a", "capture-b")
    ]
    combined = {
        f"{label}-{kind}": reference(
            SOURCE_WORK / f"{label}-{kind}.bf16", f"{label}-{kind}"
        )
        for label in ("a", "b")
        for kind in science.KINDS
    }
    observed = {
        "captures": captures,
        "combined": combined,
        "sourceCandidateId": SOURCE_ID,
        "sourceFailedJob": reference(FAILED_JOB, "failed-job"),
    }
    expected = {
        key: declared[key]
        for key in ("captures", "combined", "sourceCandidateId", "sourceFailedJob")
    }
    return captures, observed == expected


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
        raise ValueError("same-run salvage identifies another candidate")
    if reference(experiment_path, "experiment") != {
        **json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]),
        "id": "experiment",
    }:
        raise ValueError("job and same-run salvage experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    failed_guard = require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("same-run salvage result boundary is not fresh")
    if not SOURCE_WORK.is_dir():
        raise ValueError("completed source work is unavailable")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("same-run salvage work root was not fresh")

    captures, salvage_manifest_pass = validate_salvage_manifest()
    parent_fixture = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        science.fixture_identity(manifest, parent_fixture)
        for manifest in captures
    ]
    combined: list[dict[str, Path]] = []
    captured_combined_exact = True
    for label, directory in zip(
        ("a", "b"),
        (SOURCE_WORK / "capture-a", SOURCE_WORK / "capture-b"),
        strict=True,
    ):
        current: dict[str, Path] = {}
        for kind in science.KINDS:
            destination = WORK / f"{label}-{kind}.bf16"
            science.combine_probe(directory, kind, destination)
            source_combined = SOURCE_WORK / f"{label}-{kind}.bf16"
            captured_combined_exact = (
                captured_combined_exact
                and destination.read_bytes() == source_combined.read_bytes()
            )
            current[kind] = destination
        combined.append(current)

    composer = WORK / "compose-bf16"
    executions: dict[str, Any] = {
        "compileComposer": execute([
            os.environ.get("CXX", "c++"), "-std=c++20", "-O3", "-Wall",
            "-Wextra", str(COMPOSER_SOURCE), "-o", str(composer),
        ])
    }
    compositions: list[dict[str, Path]] = []
    for label, current in zip(("a", "b"), combined, strict=True):
        composed = WORK / f"{label}-composed.bf16"
        negated = WORK / f"{label}-negated.bf16"
        executions[f"compose-{label}"] = execute([
            str(composer), str(current["branch"]), str(current["direct"]),
            str(composed), str(negated),
        ])
        compositions.append({"composed": composed, "negated": negated})

    compare = comparator.compare_bf16
    comparisons = {
        "sourceInput": compare(combined[0]["input"], SOURCE_INPUT),
        "sealedTotal": compare(combined[0]["total"], SOURCE_TOTAL),
        "sealedBranch": compare(combined[0]["branch"], SOURCE_BRANCH),
        "staleOpenDirect": compare(
            combined[0]["direct"], STALE_OPEN_DIRECT
        ),
        "correctedOpenDirect": compare(
            combined[0]["direct"], CORRECTED_OPEN_DIRECT
        ),
        "composedTotal": compare(
            compositions[0]["composed"], combined[0]["total"]
        ),
        "negated": compare(
            compositions[0]["negated"], combined[0]["total"]
        ),
    }
    replay = (
        captures[0]["aggregateSha256"] == captures[1]["aggregateSha256"]
        and all(
            combined[0][kind].read_bytes() == combined[1][kind].read_bytes()
            for kind in science.KINDS
        )
        and all(
            compositions[0][kind].read_bytes()
            == compositions[1][kind].read_bytes()
            for kind in ("composed", "negated")
        )
    )
    retained = {
        "same-run-input": RESULT / "same-run-pre-ff-input.bf16",
        "same-run-total": RESULT / "same-run-pre-ff-total-adjoint.bf16",
        "same-run-branch": RESULT / "same-run-pre-ff-branch-adjoint.bf16",
        "same-run-direct": RESULT / "same-run-pre-ff-direct-adjoint.bf16",
        "same-run-composed": RESULT / "same-run-pre-ff-composed-adjoint.bf16",
    }
    sources = {
        "same-run-input": combined[0]["input"],
        "same-run-total": combined[0]["total"],
        "same-run-branch": combined[0]["branch"],
        "same-run-direct": combined[0]["direct"],
        "same-run-composed": compositions[0]["composed"],
    }
    for identifier, destination in retained.items():
        shutil.copyfile(sources[identifier], destination)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "captureManifests": captures,
        "comparisons": {
            key: list(value) for key, value in comparisons.items()
        },
        "executions": executions,
        "fixtureIdentity": identities,
        "salvageSourceManifest": reference(
            SALVAGE_MANIFEST, "salvage-source-manifest"
        ),
        "sourceFailedJob": reference(FAILED_JOB, "failed-job"),
    }, indent=2, sort_keys=True) + "\n")

    source_guard_pass = (
        failed_guard["max_sampled_tree_rss_kib"]
        <= failed_guard["official_decimal_limit_kib"]
        and failed_guard["max_sampled_temporary_disk_bytes"]
        <= failed_guard["temporary_disk_limit_bytes"]
    )
    shutil.rmtree(SOURCE_WORK)
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "elementCount": science.ELEMENTS,
        "declaredProbeFileCount": sum(
            row["declaredProbeFileCount"] for row in identities
        ),
        "declaredProbePopulationExact": all(
            row["declaredProbePopulationExact"] for row in identities
        ),
        "nonProbeFixtureMismatchCount": sum(
            len(row["nonProbeMismatches"]) for row in identities
        ),
        "sourceInputMismatchCount": comparisons["sourceInput"][0],
        "sealedTotalMismatchCount": comparisons["sealedTotal"][0],
        "sealedBranchMismatchCount": comparisons["sealedBranch"][0],
        "openDirectMismatchCount": comparisons["staleOpenDirect"][0],
        "maximumOpenDirectAbsoluteError": comparisons[
            "staleOpenDirect"
        ][1],
        "correctedOpenDirectMismatchCount": comparisons[
            "correctedOpenDirect"
        ][0],
        "maximumCorrectedOpenDirectAbsoluteError": comparisons[
            "correctedOpenDirect"
        ][1],
        "composedTotalMismatchCount": comparisons["composedTotal"][0],
        "maximumComposedTotalAbsoluteError": comparisons[
            "composedTotal"
        ][1],
        "negatedControlMismatchCount": comparisons["negated"][0],
        "sourceCaptureDeterministic": replay,
        "capturedEvidenceManifestPass": salvage_manifest_pass,
        "capturedCombinedExact": captured_combined_exact,
        "sourceResourceGuardPass": source_guard_pass,
        "sourceWorkRootRemoved": not SOURCE_WORK.exists(),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    evaluate = science.total_parent.source_parent.source_capture.open_parent.evaluate
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path, "experiment"),
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
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            *(
                reference(path, identifier)
                for identifier, path in retained.items()
            ),
            reference(source_closure, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0).isoformat(),
    }
    staged = RESULT / "decision.staged.json"
    staged.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(staged)
    staged.replace(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
