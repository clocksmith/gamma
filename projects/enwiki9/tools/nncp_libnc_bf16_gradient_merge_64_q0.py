#!/usr/bin/env python3
"""Measure LibNC's BF16 shared-tensor gradient merge."""

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
import nncp_libnc_ff1_bias_state_reduce_64_q0 as libbase
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
EVALUATOR_SOURCE = PROGRAM / "gradient_merge.c"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / "tools/nncp_libnc_bf16_gradient_merge_64_q0_materializer.py"
PARENT_ID = "nncp_open_top_pre_ff_raw_branch_join_64_q0_v1"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T144129Z_cbf5902ca5.json"
)
FIXTURE_ROOT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
BRANCH = ROOT / (
    "results/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1/"
    "open-pre-ff-rms-output-order-adjoint.bf16"
)
DIRECT = ROOT / (
    "results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/"
    "open-final-norm-input-residual.bf16"
)
SOURCE_TOTAL = ROOT / (
    "results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/"
    "source-pre-ff-hidden-adjoint.bf16"
)
LIBNC = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/libnc.so")
LIBNC_INCLUDE = LIBNC.parent
EXPECTED_LIBNC_SHA256 = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
MODES = (
    "branch", "direct", "branch-left", "direct-left",
    "negated-branch-left",
)
ELEMENTS = 2_097_152
SOURCE_CEILING = 500_000
ORACLE_GRAPH = "two nc_mul branches sharing one BF16 parameter"
PARAMETER_GRADIENT_TYPES = ["BF16"]


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        EVALUATOR_SOURCE.resolve(),
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
        raise ValueError("gradient-merge source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("exact-branch-adjoint", BRANCH),
        ("exact-direct-adjoint", DIRECT),
        ("source-total-adjoint", SOURCE_TOTAL),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != libbase.reference(path, identifier):
            raise ValueError(f"gradient-merge input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is False
        and parent["measurements"]["branchAdjointMismatchCount"] == 0
        and parent["measurements"]["totalAdjointMismatchCount"] == 167_635
        and reflection["validity"]["valid"] is True
        and reflection["hypothesis"]["verdict"] == "refuted"
        and reflection["decision"]["verdict"] == "mutate"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureComplete"] is True
    ):
        raise ValueError("gradient-merge antecedents are not satisfied")


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
        raise ValueError("gradient-merge experiment identifies another candidate")
    if libbase.reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and gradient-merge experiment differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("gradient-merge result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("gradient-merge work root was not fresh")
    if libbase.sha256(LIBNC) != EXPECTED_LIBNC_SHA256:
        raise ValueError("LibNC digest differs from attributed library")
    binary = WORK / "gradient-merge"
    build = libbase.execute([
        os.environ.get("CC", "cc"), "-std=gnu11", "-O2", "-Wall",
        "-Wextra", "-Werror", f"-I{LIBNC_INCLUDE}", str(EVALUATOR_SOURCE),
        str(LIBNC), f"-Wl,-rpath,{LIBNC_INCLUDE}", "-lm", "-lpthread",
        "-o", str(binary),
    ], ROOT)
    ldd = libbase.execute(["ldd", str(binary)], ROOT)
    if str(LIBNC) not in ldd["stdout"]:
        raise ValueError("gradient-merge evaluator resolved another LibNC")
    evaluations = []
    for replay in ("a", "b"):
        directory = WORK / replay
        directory.mkdir()
        outputs = {mode: directory / f"{mode}.bf16" for mode in MODES}
        receipts = {
            mode: libbase.execute([
                str(binary), str(BRANCH), str(DIRECT), str(outputs[mode]), mode
            ], WORK)
            for mode in MODES
        }
        if any(path.stat().st_size != ELEMENTS * 2 for path in outputs.values()):
            raise ValueError("gradient-merge output geometry differs")
        evaluations.append({
            "outputs": outputs,
            "receipts": receipts,
            "sha256": {mode: libbase.sha256(path) for mode, path in outputs.items()},
        })
    replay = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    comparisons = {
        "branch": libbase.compare_bf16(evaluations[0]["outputs"]["branch"], BRANCH),
        "direct": libbase.compare_bf16(evaluations[0]["outputs"]["direct"], DIRECT),
        "branchLeft": libbase.compare_bf16(
            evaluations[0]["outputs"]["branch-left"], SOURCE_TOTAL
        ),
        "directLeft": libbase.compare_bf16(
            evaluations[0]["outputs"]["direct-left"], SOURCE_TOTAL
        ),
        "negated": libbase.compare_bf16(
            evaluations[0]["outputs"]["negated-branch-left"], SOURCE_TOTAL
        ),
    }
    merge_rows = {
        "branch-left": comparisons["branchLeft"],
        "direct-left": comparisons["directLeft"],
    }
    selected_mode, selected_comparison = min(
        merge_rows.items(), key=lambda item: item[1]["mismatchCount"]
    )
    exact_count = sum(
        row["mismatchCount"] == 0 for row in merge_rows.values()
    )
    retained = RESULT / "libnc-gradient-merge-treatment.bf16"
    shutil.copyfile(evaluations[0]["outputs"][selected_mode], retained)
    source_closure = RESULT / "incremental_source.tar.xz"
    source_package(source_closure)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(json.dumps({
        "build": build,
        "comparisons": comparisons,
        "evaluations": [
            {"receipts": item["receipts"], "sha256": item["sha256"]}
            for item in evaluations
        ],
        "ldd": ldd,
        "librarySha256": EXPECTED_LIBNC_SHA256,
        "selectedMode": selected_mode,
        "sourceAttribution": {
            "forwardResidualOperation": "nncp.c:nc_add(t0, ff_input)",
            "oracleGraph": ORACLE_GRAPH,
            "parameterGradientTypes": PARAMETER_GRADIENT_TYPES,
        },
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "elementCount": ELEMENTS,
        "branchControlMismatchCount": comparisons["branch"]["mismatchCount"],
        "directControlMismatchCount": comparisons["direct"]["mismatchCount"],
        "branchLeftMismatchCount": comparisons["branchLeft"]["mismatchCount"],
        "directLeftMismatchCount": comparisons["directLeft"]["mismatchCount"],
        "minimumMergeMismatchCount": selected_comparison["mismatchCount"],
        "maximumSelectedAbsoluteError": selected_comparison["maximumAbsoluteError"],
        "exactMergeVariantCount": exact_count,
        "negatedControlMismatchCount": comparisons["negated"]["mismatchCount"],
        "evaluationReplayIdentical": replay,
        "sourceLibraryDigestBound": True,
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = libbase.evaluate(experiment["promotionPredicates"], measurements)
    kill = libbase.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": libbase.reference(experiment_path),
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
            libbase.reference(execution_path, "execution"),
            libbase.reference(retained, "libnc-gradient-merge-treatment"),
            libbase.reference(source_closure, "incremental-source-package"),
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
