#!/usr/bin/env python3
"""Evaluate LibNC output-order RMSNorm backward on the sealed pre-FF oracle."""

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
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as comparator
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0 as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
TREATMENT_MATERIALIZER = PROGRAM / "materialize_output_order.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_materializer.py"
)
STATE_ID = "nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
STATE_RESULT = ROOT / "results" / STATE_ID
STATE_DECISION = STATE_RESULT / "decision.json"
STATE_EXECUTION = STATE_RESULT / "execution.json"
STATE_GUARD = STATE_RESULT / "guard.json"
STATE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T133105Z_4b045b57ce.json"
)
STATE_MATERIALIZER = ROOT / (
    "programs/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/"
    "materialize_pre_ff_backward.py"
)
BASE_BACKWARD = ROOT / (
    "programs/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "final_norm_backward.cpp"
)
ORACLE_ID = "nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2"
ORACLE_RESULT = ROOT / "results" / ORACLE_ID
ORACLE_DECISION = ORACLE_RESULT / "decision.json"
ORACLE_EXECUTION = ORACLE_RESULT / "execution.json"
ORACLE_GUARD = ORACLE_RESULT / "guard.json"
ORACLE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T142138Z_ac31397e1d.json"
)
SEALED_INPUT = ORACLE_RESULT / "source-pre-ff-norm-input.bf16"
SEALED_BRANCH = ORACLE_RESULT / "source-pre-ff-norm-branch-adjoint.bf16"
NORMALIZED_ADJOINT = ROOT / (
    "results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/"
    "source-exact-ff1-input-adjoint.bf16"
)
DIRECT_ADJOINT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
FIXTURE = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture"
PARAMETERS = FIXTURE / "parameters_initial.coefs"
GAIN_COMPARATOR = FIXTURE / "gradients/0003_ln_g_39.bin"
BIAS_COMPARATOR = FIXTURE / "gradients/0004_ln_b_39.bin"
RMS_ORDER_DECISION = ROOT / (
    "results/nncp_v33_libnc_rmsnorm_backward_order_parity_v1/decision.json"
)
SOURCE_CEILING = 2_000_000
SAMPLES = 2_048
WIDTH = 1_024


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return base.reference(path, identifier)


def execute(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
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
        *local_source_closure((RUNNER, FREEZER)),
        PROGRAM_DESCRIPTOR.resolve(),
        TREATMENT_MATERIALIZER.resolve(),
        STATE_MATERIALIZER.resolve(),
        BASE_BACKWARD.resolve(),
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
        raise ValueError("output-order source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("state-decision", STATE_DECISION),
        ("state-execution", STATE_EXECUTION),
        ("state-guard", STATE_GUARD),
        ("state-reflection", STATE_REFLECTION),
        ("branch-oracle-decision", ORACLE_DECISION),
        ("branch-oracle-execution", ORACLE_EXECUTION),
        ("branch-oracle-guard", ORACLE_GUARD),
        ("branch-oracle-reflection", ORACLE_REFLECTION),
        ("sealed-pre-ff-input", SEALED_INPUT),
        ("sealed-pre-ff-branch-adjoint", SEALED_BRANCH),
        ("normalized-adjoint", NORMALIZED_ADJOINT),
        ("direct-adjoint", DIRECT_ADJOINT),
        ("initial-parameters", PARAMETERS),
        ("retained-gain-gradient", GAIN_COMPARATOR),
        ("retained-bias-gradient", BIAS_COMPARATOR),
        ("rms-output-order-lemma", RMS_ORDER_DECISION),
        ("base-backward-source", BASE_BACKWARD),
        ("state-backward-materializer", STATE_MATERIALIZER),
        ("output-order-materializer", TREATMENT_MATERIALIZER),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"output-order input drifted: {identifier}")
    state = json.loads(STATE_DECISION.read_text())
    oracle = json.loads(ORACLE_DECISION.read_text())
    reflection = json.loads(ORACLE_REFLECTION.read_text())
    lemma = json.loads(RMS_ORDER_DECISION.read_text())
    if not (
        state["promotionPass"] is False
        and state["measurements"]["gainGradientMismatchCount"] == 0
        and state["measurements"]["biasGradientMismatchCount"] == 0
        and oracle["promotionPass"] is True
        and oracle["measurements"]["inputMismatchCount"] == 0
        and oracle["measurements"]["openBranchMismatchCount"] == 1_988_737
        and reflection["validity"]["valid"] is True
        and reflection["decision"]["verdict"] == "mutate"
        and lemma["status"] == "PASS"
        and lemma["gate"]["matching_contracts"]
        == ["libnc_output_order_backward"]
    ):
        raise ValueError("output-order antecedents are not satisfied")


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
        raise ValueError("output-order experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and output-order experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("output-order result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("output-order work root was not fresh")
    state_source = WORK / "state-reduced.cpp"
    treatment_source = WORK / "output-order.cpp"
    binary = WORK / "output-order"
    executions: dict[str, Any] = {}
    executions["materializeState"] = execute([
        "python3", str(STATE_MATERIALIZER), str(BASE_BACKWARD), str(state_source)
    ])
    executions["materializeTreatment"] = execute([
        "python3", str(TREATMENT_MATERIALIZER), str(state_source),
        str(treatment_source)
    ])
    executions["compile"] = execute([
        os.environ.get("CXX", "c++"), "-std=c++20", "-O3", "-mavx2", "-mfma",
        "-Wall", "-Wextra", str(treatment_source), "-o", str(binary)
    ])
    executions["ldd"] = execute(["ldd", str(binary)])
    forbidden = [
        line for line in executions["ldd"]["stdout"].splitlines()
        if any(token in line.lower() for token in (
            "libnc", "ggml", "cuda", "openmp", "gomp", "blas"
        ))
    ]

    def run(label: str) -> dict[str, Path]:
        outputs = {
            name: WORK / f"{label}-{name}.bf16"
            for name in (
                "gain", "bias", "branch", "total", "direct", "negated-branch"
            )
        }
        executions[f"treatment-{label}"] = execute([
            str(binary), str(PARAMETERS), str(SEALED_INPUT),
            str(NORMALIZED_ADJOINT), str(DIRECT_ADJOINT),
            *(str(outputs[name]) for name in (
                "gain", "bias", "branch", "total", "direct", "negated-branch"
            )),
        ])
        return outputs

    populations = [run("a"), run("b")]
    treatment = comparator.compare_bf16(populations[0]["branch"], SEALED_BRANCH)
    gain = comparator.compare_bf16(populations[0]["gain"], GAIN_COMPARATOR)
    bias = comparator.compare_bf16(populations[0]["bias"], BIAS_COMPARATOR)
    negated = comparator.compare_bf16(
        populations[0]["negated-branch"], SEALED_BRANCH
    )
    replay = all(
        populations[0][name].read_bytes() == populations[1][name].read_bytes()
        for name in populations[0]
    )
    retained = RESULT / "open-pre-ff-rms-output-order-adjoint.bf16"
    shutil.copyfile(populations[0]["branch"], retained)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "comparisons": {
            "bias": list(bias),
            "gain": list(gain),
            "negatedBranch": list(negated),
            "treatment": list(treatment),
        },
        "executions": executions,
        "forbiddenDynamicDependencies": forbidden,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    oracle = json.loads(ORACLE_DECISION.read_text())
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "elementCount": retained.stat().st_size // 2,
        "baselineMismatchCount": oracle["measurements"]["openBranchMismatchCount"],
        "treatmentMismatchCount": treatment[0],
        "maximumTreatmentAbsoluteError": treatment[1],
        "gainGradientMismatchCount": gain[0],
        "biasGradientMismatchCount": bias[0],
        "negatedControlMismatchCount": negated[0],
        "evaluationReplayIdentical": replay,
        "forbiddenDynamicDependencyCount": len(forbidden),
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = base.oracle.evaluate(experiment["promotionPredicates"], measurements)
    kill = base.oracle.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
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
            "authorize-successor" if promotion_pass
            else "retire" if kill_pass
            else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            reference(retained, "open-rms-output-order-adjoint"),
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
