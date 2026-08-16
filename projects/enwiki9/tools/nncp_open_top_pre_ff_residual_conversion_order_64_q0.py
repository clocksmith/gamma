#!/usr/bin/env python3
"""Resolve BF16 conversion placement at the layer-19 pre-FF residual join."""

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
import nncp_libnc_top_ff2_input_adjoint_64_q0_v1 as comparator
import nncp_open_top_pre_ff_rmsnorm_backward_64_q0 as base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T133105Z_4b045b57ce.json"
)
SOURCE_RESULT = ROOT / "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2"
SOURCE_HIDDEN = SOURCE_RESULT / "source-pre-ff-hidden.bf16"
SOURCE_TOTAL = SOURCE_RESULT / "source-pre-ff-hidden-adjoint.bf16"
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
GAIN = FIXTURE / "gradients/0003_ln_g_39.bin"
BIAS = FIXTURE / "gradients/0004_ln_b_39.bin"
FINAL_SOURCE = ROOT / (
    "programs/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/"
    "final_norm_backward.cpp"
)
STATE_MATERIALIZER = ROOT / (
    "programs/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/"
    "materialize_pre_ff_backward.py"
)
CONVERSION_MATERIALIZER = PROGRAM / "materialize_conversion_probe.py"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_top_pre_ff_residual_conversion_order_64_q0_materializer.py"
)
ELEMENTS = 64 * 32 * 1024
SOURCE_CEILING = 1_000_000


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return base.reference(path, identifier)


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("conversion-parent-decision", PARENT_RESULT / "decision.json"),
        ("conversion-parent-execution", PARENT_RESULT / "execution.json"),
        ("conversion-parent-guard", PARENT_RESULT / "guard.json"),
        ("conversion-parent-reflection", PARENT_REFLECTION),
        ("source-pre-ff-hidden", SOURCE_HIDDEN),
        ("source-pre-ff-hidden-adjoint", SOURCE_TOTAL),
        ("normalized-ff1-input-adjoint", NORMALIZED_ADJOINT),
        ("direct-residual-adjoint", DIRECT_ADJOINT),
        ("initial-parameters", PARAMETERS),
        ("retained-ln-g-39-gradient", GAIN),
        ("retained-ln-b-39-gradient", BIAS),
        ("exact-final-backward-source", FINAL_SOURCE),
        ("state-backward-materializer", STATE_MATERIALIZER),
        ("conversion-probe-materializer", CONVERSION_MATERIALIZER),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"conversion-order experiment input drifted: {identifier}")
    decision = json.loads((PARENT_RESULT / "decision.json").read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        decision["promotionPass"] is False
        and decision["measurements"]["gainGradientMismatchCount"] == 0
        and decision["measurements"]["biasGradientMismatchCount"] == 0
        and decision["measurements"]["totalAdjointMismatchCount"] == 1_093_739
        and decision["measurements"]["openReplayIdentical"] is True
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
    ):
        raise ValueError("conversion-order antecedents are not satisfied")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, FREEZER)),
        FINAL_SOURCE.resolve(),
        STATE_MATERIALIZER.resolve(),
        CONVERSION_MATERIALIZER.resolve(),
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
        raise ValueError("conversion-order source closure exceeds ceiling")


def run_probe(binary: Path, directory: Path) -> dict[str, Any]:
    directory.mkdir()
    outputs = {
        name: directory / f"{name}.bf16"
        for name in (
            "gain", "bias", "norm-input", "fused-total",
            "preconverted-total", "direct-only", "negated-total",
        )
    }
    receipt = base.forward_parent.profile.base.execute(
        [
            str(binary), str(PARAMETERS), str(SOURCE_HIDDEN),
            str(NORMALIZED_ADJOINT), str(DIRECT_ADJOINT),
            *(str(outputs[name]) for name in outputs),
        ],
        WORK,
        {"HOME": str(WORK / "home"), "LANG": "C", "LC_ALL": "C",
         "PATH": "/usr/bin:/bin"},
    )
    expected = {
        "gain": 1024 * 2,
        "bias": 1024 * 2,
        **{name: ELEMENTS * 2 for name in outputs if name not in {"gain", "bias"}},
    }
    for name, output in outputs.items():
        if not output.is_file() or output.stat().st_size != expected[name]:
            raise ValueError(f"conversion-order output geometry differs: {name}")
    return {"receipt": receipt, "outputs": outputs}


def compare(left: Path, right: Path) -> tuple[int, float]:
    return comparator.compare_bf16(left, right)


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
        raise ValueError("conversion-order experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and conversion-order experiment bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("conversion-order result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("conversion-order work root was not fresh")
    (WORK / "home").mkdir()
    state_source = WORK / "state-backward.cpp"
    probe_source = WORK / "conversion-probe.cpp"
    binary = WORK / "conversion-probe"
    execute = base.forward_parent.profile.base.execute
    executions = {
        "materialize-state": execute(
            ["python3", str(STATE_MATERIALIZER), str(FINAL_SOURCE),
             str(state_source)], ROOT
        ),
        "materialize-probe": execute(
            ["python3", str(CONVERSION_MATERIALIZER), str(state_source),
             str(probe_source)], ROOT
        ),
        "compile": execute(
            [os.environ.get("CXX", "g++"), "-std=c++17", "-O3", "-mavx2",
             "-mfma", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
             str(probe_source), "-o", str(binary)], ROOT
        ),
    }
    executions["ldd"] = execute(["ldd", str(binary)], ROOT)
    forbidden = [
        line for line in executions["ldd"]["stdout"].splitlines()
        if any(token in line.lower() for token in (
            "libnc", "ggml", "cuda", "openmp", "gomp", "blas"
        ))
    ]
    runs = [run_probe(binary, WORK / label) for label in ("run-a", "run-b")]
    replay = all(
        runs[0]["outputs"][name].read_bytes()
        == runs[1]["outputs"][name].read_bytes()
        for name in runs[0]["outputs"]
    )
    comparisons = {
        "gain": compare(runs[0]["outputs"]["gain"], GAIN),
        "bias": compare(runs[0]["outputs"]["bias"], BIAS),
        "fused": compare(runs[0]["outputs"]["fused-total"], SOURCE_TOTAL),
        "preconverted": compare(
            runs[0]["outputs"]["preconverted-total"], SOURCE_TOTAL
        ),
        "direct": compare(runs[0]["outputs"]["direct-only"], SOURCE_TOTAL),
        "negated": compare(runs[0]["outputs"]["negated-total"], SOURCE_TOTAL),
    }
    treatment = RESULT / "source-exact-pre-ff-total-adjoint.bf16"
    shutil.copyfile(runs[0]["outputs"]["fused-total"], treatment)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "executions": executions,
        "probeRuns": [run["receipt"] for run in runs],
        "comparisons": {name: list(value) for name, value in comparisons.items()},
        "forbiddenDynamicDependencies": forbidden,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "elementCount": ELEMENTS,
        "gainGradientMismatchCount": comparisons["gain"][0],
        "biasGradientMismatchCount": comparisons["bias"][0],
        "fusedTotalMismatchCount": comparisons["fused"][0],
        "maximumFusedTotalAbsoluteError": comparisons["fused"][1],
        "preconvertedTotalMismatchCount": comparisons["preconverted"][0],
        "directOnlyControlMismatchCount": comparisons["direct"][0],
        "negatedControlMismatchCount": comparisons["negated"][0],
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
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": [
            reference(execution_path, "execution"),
            reference(treatment, "source-exact-pre-ff-total-adjoint"),
            reference(source_closure, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0
        ).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
