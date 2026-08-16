#!/usr/bin/env python3
"""Identify the exact production BF16 final-RMSNorm backward order."""

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
import nncp_libnc_top_ff2_adjoint_64_q0 as source_parent
import nncp_open_profile_top_ff2_gradient_64_q0_retry_v1 as open_parent
import research_contracts


base = source_parent.base
ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_final_rmsnorm_order_64_q0_v1"
PARENT_ID = "nncp_libnc_top_ff2_adjoint_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T065037Z_1d8853ab41.json"
)
SOURCE_ADJOINT = PARENT_RESULT / "source-top-ff2-adjoint.bf16"
OPEN_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
OPEN_RESULT = ROOT / "results" / OPEN_ID
OPEN_DECISION = OPEN_RESULT / "decision.json"
OPEN_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json"
)
INCOMING_RESIDUAL = OPEN_RESULT / "open-final-hidden-residual.bf16"
OPEN_INPUT_ADJOINT = OPEN_RESULT / "open-final-norm-input-residual.bf16"
FIXTURE_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_ROOT = ROOT / "results" / FIXTURE_ID
FIXTURE_DECISION = FIXTURE_ROOT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_ROOT / "guard.json"
FIXTURE_HOOK = ROOT / "tools/nncp_profile_update_fixture_hook_q3.c"
PROBE_SOURCE = PROGRAM / "final_rmsnorm_probe.inc.c"
EVALUATOR_SOURCE = PROGRAM / "final_rmsnorm_order.cpp"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
MATERIALIZER = ROOT / "tools/nncp_libnc_final_rmsnorm_order_64_q0_materializer.py"
SOURCE_CEILING = 2_000_000
STATES = 64
STREAMS = 32
WIDTH = 1024
VARIANTS = (
    "centered_fma_precenter",
    "centered_fma_postcenter",
    "centered_split_precenter",
    "centered_split_grouped",
    "standard_fma",
    "standard_split",
)


sha256 = source_parent.sha256
reference = source_parent.reference
execute = source_parent.execute
replace_once = source_parent.replace_once
parse_meta = source_parent.parse_meta


def patch_teacher(source: str) -> str:
    source = base.patch_teacher(source)
    source = replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_final_rms_set_block(block_idx);\n",
    )
    final_norm = (
        "    if (s->ln_flags & LN_FINAL) {\n"
        "        layer_input = layer_norm(layer_input, s->ln_g, s->ln_b, s->ln_flags);\n"
        "    }"
    )
    instrumented = (
        "    if (s->ln_flags & LN_FINAL) {\n"
        "        gamma_final_rms_dump(\"input\", output_index, layer_input);\n"
        "        layer_input = layer_norm(layer_input, s->ln_g, s->ln_b, s->ln_flags);\n"
        "        gamma_final_rms_dump(\"output\", output_index, layer_input);\n"
        "    }"
    )
    return replace_once(source, final_norm, instrumented)


def compile_tools(scratch: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    compiler = os.environ.get("CC", "cc")
    cxx = os.environ.get("CXX", "g++")
    patched = scratch / "nncp_final_rmsnorm_order.c"
    patched.write_text(patch_teacher((base.LIBNC_ROOT / "nncp.c").read_text()))
    nncp_object = scratch / "nncp_final_rmsnorm_order.o"
    executable = scratch / "nncp_final_rmsnorm_order"
    hook = scratch / "nncp_profile_update_fixture_hook_q3.so"
    evaluator = scratch / "final_rmsnorm_order"
    commands = [
        [
            compiler,
            "-O3",
            "-Wall",
            "-Wpointer-arith",
            "-g",
            "-fno-math-errno",
            "-fno-trapping-math",
            '-DCONFIG_VERSION="2024-06-05"',
            "-DLIBNC_CONFIG_FULL",
            f"-I{base.LIBNC_ROOT}",
            "-c",
            str(patched),
            "-o",
            str(nncp_object),
        ],
        [
            compiler,
            f"-Wl,-rpath,{base.LIBNC_ROOT}",
            "-o",
            str(executable),
            str(nncp_object),
            *[
                str(base.LIBNC_ROOT / name)
                for name in (
                    "cmdopt.o",
                    "cp_utils.o",
                    "arith.o",
                    "preprocess.o",
                    "cutils.o",
                )
            ],
            str(base.LIBNC_ROOT / "libnc.so"),
            "-lz",
            "-lm",
            "-lpthread",
        ],
        [
            compiler,
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            "-shared",
            "-fPIC",
            f"-I{base.LIBNC_ROOT}",
            str(FIXTURE_HOOK),
            f"-L{base.LIBNC_ROOT}",
            f"-Wl,-rpath,{base.LIBNC_ROOT}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ],
        [
            cxx,
            "-std=c++17",
            "-O3",
            "-mavx2",
            "-mfma",
            "-ffp-contract=off",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(EVALUATOR_SOURCE),
            "-o",
            str(evaluator),
        ],
    ]
    receipts = [execute(command, ROOT) for command in commands]
    return executable, hook, evaluator, {
        "commands": receipts,
        "patchedSourceSha256": sha256(patched),
        "executableSha256": sha256(executable),
        "hookSha256": sha256(hook),
        "evaluatorSha256": sha256(evaluator),
    }


def combine_probe(directory: Path, kind: str, output: Path) -> None:
    with output.open("wb") as destination:
        for state in range(STATES):
            stem = f"final_rms_{kind}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": kind,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": f"{WIDTH},{STREAMS}",
                "byte_order": "little",
            }
            if (
                not payload.is_file()
                or payload.stat().st_size != WIDTH * STREAMS * 2
                or not metadata.is_file()
                or parse_meta(metadata) != expected_meta
            ):
                raise ValueError(
                    f"production final RMSNorm {kind} state differs: {state}"
                )
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != STATES * STREAMS * WIDTH * 2:
        raise ValueError(f"combined final RMSNorm {kind} geometry differs")


def fixture_identity(
    observed: dict[str, Any], parent_manifest: dict[str, Any]
) -> tuple[bool, list[str]]:
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    observed_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in observed["files"]
        if not row["path"].startswith("final_rms_")
    }
    paths = sorted(set(parent_rows) | set(observed_rows))
    mismatches = [
        path for path in paths if parent_rows.get(path) != observed_rows.get(path)
    ]
    return not mismatches, mismatches


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((Path(__file__), MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        EVALUATOR_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        FIXTURE_HOOK.resolve(),
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
        raise ValueError("final RMSNorm order source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-source-decision", PARENT_DECISION),
        ("parent-source-reflection", PARENT_REFLECTION),
        ("parent-source-adjoint", SOURCE_ADJOINT),
        ("open-tail-decision", OPEN_DECISION),
        ("open-tail-reflection", OPEN_REFLECTION),
        ("open-incoming-residual", INCOMING_RESIDUAL),
        ("open-input-adjoint", OPEN_INPUT_ADJOINT),
        ("production-fixture-decision", FIXTURE_DECISION),
        ("production-fixture-manifest", FIXTURE_MANIFEST),
        ("production-fixture-guard", FIXTURE_GUARD),
        ("probe-source", PROBE_SOURCE),
        ("evaluator-source", EVALUATOR_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    open_decision = json.loads(OPEN_DECISION.read_text())
    open_reflection = json.loads(OPEN_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["sourceFf2MismatchCount"] == 0
        and parent["measurements"]["openAdjointMismatchCount"] == 8
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and parent_reflection["decision"]["verdict"] == "promote"
        and open_decision["promotionPass"] is False
        and open_decision["measurements"]["topFf2MismatchCount"] == 184
        and open_decision["measurements"]["openBackwardDeterministic"] is True
        and open_reflection["validity"]["valid"] is True
        and open_reflection["decision"]["verdict"] == "retry"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture["measurements"]["targetBlockBefore"] == 256
    ):
        raise ValueError("final RMSNorm order antecedents are not satisfied")
    for path, expected in base.EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen source input identity differs: {path}")


def evaluate_run(
    evaluator: Path, input_path: Path, output_path: Path, directory: Path
) -> dict[str, Any]:
    directory.mkdir()
    receipt = execute(
        [
            str(evaluator),
            str(input_path),
            str(output_path),
            str(INCOMING_RESIDUAL),
            str(directory),
        ],
        WORK,
    )
    files = {
        name: directory / f"{name}.bf16"
        for name in ("forward", *VARIANTS, "negated_control")
    }
    expected_bytes = STATES * STREAMS * WIDTH * 2
    if any(
        not path.is_file() or path.stat().st_size != expected_bytes
        for path in files.values()
    ):
        raise ValueError("final RMSNorm evaluator output geometry differs")
    return {
        "receipt": receipt,
        "files": files,
        "sha256": {name: sha256(path) for name, path in files.items()},
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
        raise ValueError("job and final-RMSNorm experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("final RMSNorm order result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("final RMSNorm order work root was not fresh")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, evaluator, build = compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        base.capture(executable, hook, directory) for directory in captures
    ]
    manifests = [base.directory_manifest(directory) for directory in captures]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        fixture_identity(manifest, parent_manifest) for manifest in manifests
    ]

    combined = []
    evaluations = []
    for label, directory in zip(("a", "b"), captures, strict=True):
        input_path = WORK / f"{label}-source-final-rms-input.bf16"
        output_path = WORK / f"{label}-source-final-rms-output.bf16"
        combine_probe(directory, "input", input_path)
        combine_probe(directory, "output", output_path)
        combined.append({"input": input_path, "output": output_path})
        evaluations.append(
            evaluate_run(
                evaluator,
                input_path,
                output_path,
                WORK / f"evaluation-{label}",
            )
        )

    capture_repeat = (
        manifests[0]["aggregateSha256"] == manifests[1]["aggregateSha256"]
    )
    combined_repeat = all(
        combined[0][kind].read_bytes() == combined[1][kind].read_bytes()
        for kind in ("input", "output")
    )
    evaluation_repeat = evaluations[0]["sha256"] == evaluations[1]["sha256"]
    parent_fixture_identity = all(identity[0] for identity in identities)
    comparisons = {
        name: open_parent.parent.compare_bf16(
            evaluations[0]["files"][name], SOURCE_ADJOINT
        )
        for name in VARIANTS
    }
    exact_variants = [name for name in VARIANTS if comparisons[name][0] == 0]
    forward_comparison = open_parent.parent.compare_bf16(
        evaluations[0]["files"]["forward"], combined[0]["output"]
    )
    open_comparison = open_parent.parent.compare_bf16(
        SOURCE_ADJOINT, OPEN_INPUT_ADJOINT
    )
    control_comparison = open_parent.parent.compare_bf16(
        evaluations[0]["files"]["negated_control"], SOURCE_ADJOINT
    )

    artifacts = {
        "source-final-rms-input": RESULT / "source-final-rms-input.bf16",
        "source-final-rms-output": RESULT / "source-final-rms-output.bf16",
    }
    shutil.copyfile(combined[0]["input"], artifacts["source-final-rms-input"])
    shutil.copyfile(combined[0]["output"], artifacts["source-final-rms-output"])
    incremental_source = RESULT / "incremental_source.tar.xz"
    source_package(incremental_source)
    execution_path = RESULT / "execution.json"
    execution_path.write_text(
        json.dumps(
            {
                "build": build,
                "captures": executions,
                "captureAggregateSha256": [
                    manifest["aggregateSha256"] for manifest in manifests
                ],
                "captureFileCount": [
                    manifest["fileCount"] for manifest in manifests
                ],
                "captureTotalBytes": [
                    manifest["totalBytes"] for manifest in manifests
                ],
                "parentFixtureIdentity": [identity[0] for identity in identities],
                "parentFixtureMismatches": [
                    identity[1] for identity in identities
                ],
                "combinedSha256": [
                    {kind: sha256(item[kind]) for kind in ("input", "output")}
                    for item in combined
                ],
                "evaluations": [
                    {"receipt": item["receipt"], "sha256": item["sha256"]}
                    for item in evaluations
                ],
                "variantComparisons": {
                    name: {
                        "mismatchCount": value[0],
                        "maximumAbsoluteError": value[1],
                    }
                    for name, value in comparisons.items()
                },
                "exactVariants": exact_variants,
                "forwardComparison": {
                    "mismatchCount": forward_comparison[0],
                    "maximumAbsoluteError": forward_comparison[1],
                },
                "openInputAdjointComparison": {
                    "mismatchCount": open_comparison[0],
                    "maximumAbsoluteError": open_comparison[1],
                },
                "negatedControlComparison": {
                    "mismatchCount": control_comparison[0],
                    "maximumAbsoluteError": control_comparison[1],
                },
                "externalInputSha256": {
                    str(path): sha256(path) for path in base.EXPECTED
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    shutil.rmtree(WORK)

    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "sourceCaptureRepeatIdentical": capture_repeat,
        "combinedReplayIdentical": combined_repeat,
        "evaluationReplayIdentical": evaluation_repeat,
        "parentFixtureIdentity": parent_fixture_identity,
        "capturedStateCount": STATES,
        "sourceInputElementCount": artifacts[
            "source-final-rms-input"
        ].stat().st_size
        // 2,
        "sourceOutputElementCount": artifacts[
            "source-final-rms-output"
        ].stat().st_size
        // 2,
        "forwardMismatchCount": forward_comparison[0],
        "maximumForwardAbsoluteError": forward_comparison[1],
        "openInputAdjointMismatchCount": open_comparison[0],
        "currentVariantMismatchCount": comparisons[
            "centered_fma_precenter"
        ][0],
        "exactVariantCount": len(exact_variants),
        "negatedControlDiffers": control_comparison[0] > 0,
        "incrementalSourceBytes": incremental_source.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = open_parent.evaluate(
        experiment["promotionPredicates"], measurements
    )
    kill = open_parent.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": candidate_revision,
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
            else "retire"
            if kill_pass
            else "retry"
        ),
        "artifacts": [
            reference(execution_path, "execution"),
            *(
                reference(path, identifier)
                for identifier, path in artifacts.items()
            ),
            reference(incremental_source, "incremental-source-package"),
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
