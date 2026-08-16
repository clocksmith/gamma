#!/usr/bin/env python3
"""Capture the production top attention-product values and adjoints."""

from __future__ import annotations

import argparse
from array import array
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import sys
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_ff1_bias_state_reduce_64_q0 as oracle
import nncp_libnc_top_w_o_input_adjoint_64_q0_v1 as capture_base
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_top_attention_product_oracle_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PARENT_ID = "nncp_open_top_w_o_input_forward_64_q0_retry_v2"
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json"
)
OPEN_PRE_W_O = PARENT_RESULT / "open-exact-w-o-input.bf16"
BACKWARD_RESULT = ROOT / "results/nncp_open_w_o_input_adjoint_block128_64_q0_v1"
BACKWARD_DECISION = BACKWARD_RESULT / "decision.json"
BACKWARD_EXECUTION = BACKWARD_RESULT / "execution.json"
BACKWARD_GUARD = BACKWARD_RESULT / "guard.json"
BACKWARD_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T164348Z_ff5718724e.json"
)
OPEN_PRE_W_O_ADJOINT = BACKWARD_RESULT / "source-exact-w-o-input-adjoint.bf16"
FIXTURE_RESULT = ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1"
FIXTURE_DECISION = FIXTURE_RESULT / "decision.json"
FIXTURE_MANIFEST = FIXTURE_RESULT / "fixture-manifest.json"
FIXTURE_GUARD = FIXTURE_RESULT / "guard.json"
FIXTURE_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
PROBE_SOURCE = ROOT / "tools/nncp_libnc_top_attention_product_probe_q0.c"
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_attention_product_oracle_64_q0_v1_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
STATES = 64
STREAMS = 32
HEADS = 8
HEAD_WIDTH = 128
POSITION = 320
ATTENDED_ELEMENTS = STATES * HEADS * STREAMS * HEAD_WIDTH
PROBABILITY_ELEMENTS = STATES * HEADS * STREAMS * POSITION
SOURCE_CEILING = 2_000_000
DECLARATIONS = """static NCTensor *gamma_top_attn_probe_attach(
    NCTensor *value, int layer, int state, enum GammaTopAttnKind kind);
static int gamma_top_attn_probe_capture(
    void *opaque, NCTensor *gradient, NCTensor *column_index);

"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return oracle.reference(path, identifier)


def patch_teacher(source: str) -> str:
    base = capture_base.source_capture.capture
    source = base.base.patch_teacher(source)
    source = base.replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        PROBE_SOURCE.read_text() + "\nstatic FILE *teacher_trace_file;\n",
    )
    source = base.replace_once(
        source,
        "static NCTensor *layer_norm(",
        DECLARATIONS + "static NCTensor *layer_norm(",
    )
    source = base.replace_once(
        source,
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n",
        "    while ((block_idx + n_states) <= block_stride) {\n"
        "        prof_start(PROF_TOTAL);\n"
        "        gamma_top_attn_probe_set_block(block_idx);\n",
    )
    source = base.replace_once(
        source,
        "            t1 = nc_soft_max(t0);\n"
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));",
        "            t1 = nc_soft_max(t0);\n"
        "            t1 = gamma_top_attn_probe_attach(\n"
        "                t1, layer_idx, output_index,\n"
        "                GAMMA_TOP_ATTN_PROBABILITY);\n"
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));",
    )
    source = base.replace_once(
        source,
        "            tl->va_nodes[output_index] = node;\n"
        "        }\n"
        "        \n"
        "        if (tl->w_o) {",
        "            tl->va_nodes[output_index] = node;\n"
        "            t0 = gamma_top_attn_probe_attach(\n"
        "                t0, layer_idx, output_index,\n"
        "                GAMMA_TOP_ATTN_ATTENDED);\n"
        "        }\n"
        "        \n"
        "        if (tl->w_o) {",
    )
    source = base.replace_once(
        source,
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
        "    if (gamma_top_attn_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    sgd_opt_update_var(opaque, yg, get_col_index);",
    )
    return source


capture_base.PROBE_SOURCE = PROBE_SOURCE
capture_base.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
capture_base.RUNNER = RUNNER
capture_base.MATERIALIZER = MATERIALIZER
capture_base.SOURCE_CEILING = SOURCE_CEILING
capture_base.patch_teacher = patch_teacher


def expected_probe_paths() -> set[str]:
    return {
        f"top_attn_{kind}_{phase}_s{state:03d}.{extension}"
        for kind in ("probability", "attended")
        for phase in ("input", "adjoint")
        for state in range(STATES)
        for extension in ("bin", "meta")
    }


def fixture_identity(
    observed: dict[str, Any], parent_manifest: dict[str, Any]
) -> dict[str, Any]:
    expected = expected_probe_paths()
    probes = {
        row["path"] for row in observed["files"]
        if row["path"].startswith("top_attn_")
    }
    parent_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in parent_manifest["fixture"]["files"]
    }
    observed_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in observed["files"]
        if not row["path"].startswith("top_attn_")
    }
    mismatches = [
        path for path in sorted(set(parent_rows) | set(observed_rows))
        if parent_rows.get(path) != observed_rows.get(path)
    ]
    return {
        "declaredProbeFileCount": len(probes),
        "declaredProbePopulationExact": probes == expected,
        "missingProbePaths": sorted(expected - probes),
        "unexpectedProbePaths": sorted(probes - expected),
        "nonProbeIdentical": not mismatches,
        "nonProbeMismatches": mismatches,
    }


def combine_probe(directory: Path, kind: str, phase: str, output: Path) -> None:
    geometry = {
        "attended": (f"{HEAD_WIDTH},1,{STREAMS},{HEADS}", ATTENDED_ELEMENTS),
        "probability": (f"{POSITION},1,{STREAMS},{HEADS}", PROBABILITY_ELEMENTS),
    }
    dimensions, elements = geometry[kind]
    bytes_per_state = elements * 2 // STATES
    with output.open("wb") as destination:
        for state in range(STATES):
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
            if (
                not payload.is_file()
                or payload.stat().st_size != bytes_per_state
                or not metadata.is_file()
                or capture_base.source_capture.capture.parse_meta(metadata)
                != expected_meta
            ):
                raise ValueError(
                    f"source top attention {kind} {phase} differs: {state}"
                )
            with payload.open("rb") as source:
                shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
    if output.stat().st_size != elements * 2:
        raise ValueError(f"combined top attention {kind} {phase} differs")


def attended_to_concat(source: Path, output: Path) -> None:
    words = array("H")
    words.frombytes(source.read_bytes())
    if sys.byteorder != "little":
        words.byteswap()
    if len(words) != ATTENDED_ELEMENTS:
        raise ValueError("attended-head input geometry differs")
    with output.open("wb") as destination:
        for state in range(STATES):
            state_base = state * HEADS * STREAMS * HEAD_WIDTH
            for stream in range(STREAMS):
                for head in range(HEADS):
                    begin = state_base + (head * STREAMS + stream) * HEAD_WIDTH
                    destination.write(words[begin : begin + HEAD_WIDTH].tobytes())
    if output.stat().st_size != ATTENDED_ELEMENTS * 2:
        raise ValueError("concat-mapped attended input geometry differs")


def source_package(path: Path) -> None:
    members = [
        *local_source_closure((RUNNER, MATERIALIZER)),
        PROBE_SOURCE.resolve(),
        PROGRAM_DESCRIPTOR.resolve(),
        capture_base.source_capture.capture.FIXTURE_HOOK.resolve(),
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
        raise ValueError("top attention oracle source closure exceeds ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("open-pre-w-o-input", OPEN_PRE_W_O),
        ("backward-decision", BACKWARD_DECISION),
        ("backward-execution", BACKWARD_EXECUTION),
        ("backward-guard", BACKWARD_GUARD),
        ("backward-reflection", BACKWARD_REFLECTION),
        ("open-pre-w-o-adjoint", OPEN_PRE_W_O_ADJOINT),
        ("fixture-decision", FIXTURE_DECISION),
        ("fixture-manifest", FIXTURE_MANIFEST),
        ("fixture-guard", FIXTURE_GUARD),
        ("fixture-reflection", FIXTURE_REFLECTION),
        ("probe-source", PROBE_SOURCE),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    parent_reflection = json.loads(PARENT_REFLECTION.read_text())
    backward = json.loads(BACKWARD_DECISION.read_text())
    backward_reflection = json.loads(BACKWARD_REFLECTION.read_text())
    fixture = json.loads(FIXTURE_DECISION.read_text())
    fixture_reflection = json.loads(FIXTURE_REFLECTION.read_text())
    if not (
        parent["promotionPass"] is True
        and parent["measurements"]["independentSourceMismatchCount"] == 0
        and parent_reflection["validity"]["valid"] is True
        and parent_reflection["hypothesis"]["verdict"] == "supported"
        and backward["promotionPass"] is True
        and backward["measurements"]["block128SourceMismatchCount"] == 0
        and backward_reflection["validity"]["valid"] is True
        and backward_reflection["hypothesis"]["verdict"] == "supported"
        and fixture["promotionPass"] is True
        and fixture["measurements"]["fixtureRepeatByteIdentical"] is True
        and fixture_reflection["validity"]["valid"] is True
    ):
        raise ValueError("top attention oracle antecedents are not satisfied")
    for path, expected in capture_base.source_capture.capture.base.EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen source input identity differs: {path}")


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
        raise ValueError("job and top attention bindings differ")
    revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or output.exists():
        raise ValueError("top attention result boundary is not fresh")
    if not WORK.is_dir() or any(WORK.iterdir()):
        raise ValueError("top attention work root is not fresh")

    scratch = WORK / "build"
    scratch.mkdir()
    executable, hook, build = capture_base.compile_tools(scratch)
    captures = [WORK / "capture-a", WORK / "capture-b"]
    executions = [
        capture_base.source_capture.capture.base.capture(
            executable, hook, directory
        )
        for directory in captures
    ]
    manifests = [
        capture_base.source_capture.capture.base.directory_manifest(directory)
        for directory in captures
    ]
    parent_manifest = json.loads(FIXTURE_MANIFEST.read_text())
    identities = [
        fixture_identity(manifest, parent_manifest) for manifest in manifests
    ]
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
        "probability-adjoint": RESULT / "source-attention-probability-adjoint.bf16",
    }
    for key, destination in artifacts_by_key.items():
        shutil.copyfile(combined[0][key], destination)
    concat_work = WORK / "source-attended-concat.bf16"
    attended_to_concat(combined[0]["attended-input"], concat_work)
    concat_comparison = oracle.compare_bf16(concat_work, OPEN_PRE_W_O)
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
                "build": build,
                "captureManifests": manifests,
                "concatComparison": concat_comparison,
                "executions": executions,
                "fixtureIdentity": identities,
                "tensorCoordinates": {
                    "attended": "state-major, head-major, stream-major, feature-major",
                    "probability": "state-major, head-major, stream-major, key-major",
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    probe_exact = all(row["declaredProbePopulationExact"] for row in identities)
    non_probe_identical = all(row["nonProbeIdentical"] for row in identities)
    probe_file_count = sum(row["declaredProbeFileCount"] for row in identities)
    non_probe_mismatch_count = sum(
        len(row["nonProbeMismatches"]) for row in identities
    )
    shutil.rmtree(WORK)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "captureCount": len(captures),
        "sampleCount": STATES * STREAMS,
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
        "declaredProbeFileCount": probe_file_count,
        "declaredProbePopulationExact": probe_exact,
        "fixturePayloadIdentical": non_probe_identical,
        "fixturePayloadMismatchCount": non_probe_mismatch_count,
        "attendedInputLive": any(artifacts_by_key["attended-input"].read_bytes()),
        "attendedAdjointLive": any(
            artifacts_by_key["attended-adjoint"].read_bytes()
        ),
        "probabilityInputLive": any(
            artifacts_by_key["probability-input"].read_bytes()
        ),
        "probabilityAdjointLive": any(
            artifacts_by_key["probability-adjoint"].read_bytes()
        ),
        "concatSourceMismatchCount": concat_comparison["mismatchCount"],
        "maximumConcatAbsoluteError": concat_comparison["maximumAbsoluteError"],
        "incrementalSourceBytes": source_closure.stat().st_size,
        "guardedWorkRootPass": not WORK.exists(),
    }
    promotion = oracle.evaluate(experiment["promotionPredicates"], measurements)
    kill = oracle.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    artifacts = [
        reference(execution_path, "execution"),
        *[
            reference(path, key)
            for key, path in artifacts_by_key.items()
        ],
        reference(source_closure, "incremental-source-package"),
    ]
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
            "authorize-successor"
            if promotion_pass
            else "retire" if kill_pass else "retry"
        ),
        "artifacts": artifacts,
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    return 0 if promotion_pass and not kill_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
