#!/usr/bin/env python3
"""Finalize staged same-run attribution without recomputing tensor science."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_pre_ff_same_run_contributions_64_q0_v1 as science
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as comparator
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3"
PARENT_ID = "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v2.json"
)
FAILED_JOB = ROOT / (
    "operations/adaptive/failed/000_20260816T154402Z_74511ffe59.json"
)
FAILED_GUARD = PARENT_RESULT / "guard.json"
FAILED_LOG = ROOT / "run_logs/adaptive/20260816T154402Z_74511ffe59.log"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T154402Z_74511ffe59.json"
)
STAGED_DECISION = PARENT_RESULT / "decision.staged.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_SOURCE = PARENT_RESULT / "incremental_source.tar.xz"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3_materializer.py"
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
CORRECTED_OPEN_DIRECT = ROOT / (
    "results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
PARENT_ARTIFACTS = {
    "same-run-input": PARENT_RESULT / "same-run-pre-ff-input.bf16",
    "same-run-total": PARENT_RESULT / "same-run-pre-ff-total-adjoint.bf16",
    "same-run-branch": PARENT_RESULT / "same-run-pre-ff-branch-adjoint.bf16",
    "same-run-direct": PARENT_RESULT / "same-run-pre-ff-direct-adjoint.bf16",
    "same-run-composed": PARENT_RESULT / "same-run-pre-ff-composed-adjoint.bf16",
}
SOURCE_CEILING = 500_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return science.reference(path, identifier or path.stem)


def result_reference(path: Path) -> dict[str, str]:
    value = reference(path)
    return {key: value[key] for key in ("path", "sha256")}


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
        raise ValueError("receipt-only source closure exceeds ceiling")


def require_inputs(experiment: dict[str, object]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-experiment", PARENT_EXPERIMENT),
        ("failed-job", FAILED_JOB),
        ("failed-guard", FAILED_GUARD),
        ("failed-log", FAILED_LOG),
        ("failed-reflection", FAILED_REFLECTION),
        ("staged-decision", STAGED_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-source-package", PARENT_SOURCE),
        ("source-input", SOURCE_INPUT),
        ("source-total", SOURCE_TOTAL),
        ("source-branch", SOURCE_BRANCH),
        ("stale-open-direct", STALE_OPEN_DIRECT),
        ("corrected-open-direct", CORRECTED_OPEN_DIRECT),
        *((identifier, path) for identifier, path in PARENT_ARTIFACTS.items()),
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("program-descriptor", PROGRAM_DESCRIPTOR),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"receipt-only input drifted: {identifier}")
    failed = json.loads(FAILED_JOB.read_text())
    guard = json.loads(FAILED_GUARD.read_text())
    reflection = json.loads(FAILED_REFLECTION.read_text())
    if not (
        failed["state"] == "failed"
        and failed["returncode"] == 1
        and guard["status"] == "complete"
        and guard["returncode"] == 1
        and reflection["validity"]["classification"]
        == "implementation-failure"
        and reflection["hypothesis"]["verdict"] == "not-tested"
        and reflection["decision"]["verdict"] == "retry"
    ):
        raise ValueError("receipt-only antecedents are not satisfied")


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
        raise ValueError("receipt-only experiment identifies another candidate")
    expected_experiment = json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    )
    if result_reference(experiment_path) != expected_experiment:
        raise ValueError("job and receipt-only experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("receipt-only result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("receipt-only work root was not fresh")

    staged = json.loads(STAGED_DECISION.read_text())
    parent_experiment_reference = result_reference(PARENT_EXPERIMENT)
    staged_experiment = dict(staged["experiment"])
    removed_id = staged_experiment.pop("id", None)
    staged_bound = (
        staged["candidateId"] == PARENT_ID
        and staged["promotionPass"] is True
        and staged["killPass"] is False
        and staged["decision"] == "authorize-successor"
        and removed_id == "experiment"
        and staged_experiment == parent_experiment_reference
    )
    parent_execution = json.loads(PARENT_EXECUTION.read_text())
    comparisons = parent_execution["comparisons"]
    measurements = dict(staged["measurements"])
    execution_consistent = (
        comparisons["sourceInput"][0]
        == measurements["sourceInputMismatchCount"]
        and comparisons["sealedTotal"][0]
        == measurements["sealedTotalMismatchCount"]
        and comparisons["sealedBranch"][0]
        == measurements["sealedBranchMismatchCount"]
        and comparisons["staleOpenDirect"][0]
        == measurements["openDirectMismatchCount"]
        and comparisons["correctedOpenDirect"][0]
        == measurements["correctedOpenDirectMismatchCount"]
        and comparisons["composedTotal"][0]
        == measurements["composedTotalMismatchCount"]
        and comparisons["negated"][0]
        == measurements["negatedControlMismatchCount"]
    )
    compare = comparator.compare_bf16
    durable_comparisons = {
        "sourceInput": compare(PARENT_ARTIFACTS["same-run-input"], SOURCE_INPUT),
        "sourceTotal": compare(PARENT_ARTIFACTS["same-run-total"], SOURCE_TOTAL),
        "sourceBranch": compare(
            PARENT_ARTIFACTS["same-run-branch"], SOURCE_BRANCH
        ),
        "staleOpenDirect": compare(
            PARENT_ARTIFACTS["same-run-direct"], STALE_OPEN_DIRECT
        ),
        "correctedOpenDirect": compare(
            PARENT_ARTIFACTS["same-run-direct"], CORRECTED_OPEN_DIRECT
        ),
        "composedTotal": compare(
            PARENT_ARTIFACTS["same-run-composed"],
            PARENT_ARTIFACTS["same-run-total"],
        ),
    }
    durable_exact = (
        durable_comparisons["sourceInput"][0] == 0
        and durable_comparisons["sourceTotal"][0] == 0
        and durable_comparisons["sourceBranch"][0] == 0
        and durable_comparisons["staleOpenDirect"][0] == 8
        and durable_comparisons["correctedOpenDirect"][0] == 0
        and durable_comparisons["composedTotal"][0] == 0
    )

    retained = {
        identifier: RESULT / path.name
        for identifier, path in PARENT_ARTIFACTS.items()
    }
    for identifier, destination in retained.items():
        shutil.copyfile(PARENT_ARTIFACTS[identifier], destination)
    receipt_replay = all(
        destination.read_bytes() == PARENT_ARTIFACTS[identifier].read_bytes()
        for identifier, destination in retained.items()
    )
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "durableComparisons": {
            key: list(value) for key, value in durable_comparisons.items()
        },
        "parentExecution": reference(PARENT_EXECUTION, "parent-execution"),
        "stagedDecision": reference(STAGED_DECISION, "staged-decision"),
        "stagedDecisionBound": staged_bound,
        "stagedExecutionConsistent": execution_consistent,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements.update({
        "stagedDecisionBound": staged_bound,
        "stagedExecutionConsistent": execution_consistent,
        "durableArtifactComparisonsExact": durable_exact,
        "receiptOnlyReplayIdentical": receipt_replay,
        "parentArtifactCount": len(PARENT_ARTIFACTS),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    })
    evaluate = science.total_parent.source_parent.source_capture.open_parent.evaluate
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": result_reference(experiment_path),
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
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
