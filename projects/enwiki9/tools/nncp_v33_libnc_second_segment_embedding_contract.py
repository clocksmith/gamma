#!/usr/bin/env python3
"""Resolve the LibNC second-segment input and embedding contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_concat_rmsnorm_multiupdate_parity as multi
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_second_segment_attention_trajectory as attention
import nncp_v33_libnc_second_segment_forward_trajectory as forward
import nncp_v33_libnc_update_state_trajectory as update_state


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_second_segment_embedding_contract_v1"
BYTES = 32
SEGMENT = 4
TOLERANCE = 2e-6
BASE_ATTENTION_PATCHER = attention.patch_attention_source


def patch_embedding_source(source: str) -> str:
    source = BASE_ATTENTION_PATCHER(source)
    marker = (
        "    t0 = nc_reshape_1d(t0, s->n_streams * seg_len);\n"
        "    \n"
        "    layer_input = nc_get_col(nc_dup_tensor(s->embed), t0);"
    )
    replacement = (
        "    t0 = nc_reshape_1d(t0, s->n_streams * seg_len);\n"
        "#ifdef DUMP_HASH\n"
        "    if (output_index == 0) {\n"
        "        size_t gamma_input_index = 0;\n"
        "        NCTensor *gamma_input_value = nc_new_f32(\n"
        "            d, (float)nc_get1_i32(t0, 1, &gamma_input_index));\n"
        "        nc_dump_tensor_hash(\"a_input\", gamma_input_value);\n"
        "        nc_free_tensor(gamma_input_value);\n"
        "    }\n"
        "#endif\n"
        "    \n"
        "    layer_input = nc_get_col(nc_dup_tensor(s->embed), t0);"
    )
    return attention.replace_once(source, marker, replacement)


def compile_variant(
    libnc_root: Path,
    exporter_source: Path,
    hook_source: Path,
    temporary: Path,
    patcher,
):
    original = attention.patch_attention_source
    attention.patch_attention_source = patcher
    try:
        return attention.compile_native(
            libnc_root, exporter_source, hook_source, temporary
        )
    finally:
        attention.patch_attention_source = original


def run_hashes(runs: list[dict[str, object]]) -> dict[str, list]:
    return {
        "archive": [internal.sha256(run["archive"]) for run in runs],
        "trace": [internal.sha256(run["trace"]) for run in runs],
        "coefs": [
            [internal.sha256(path) for path in run["coefs"]] for run in runs
        ],
        "memory": [
            [internal.sha256(path) for path in run["memories"]] for run in runs
        ],
        "dump": [internal.dump_sha256(run["dump"]) for run in runs],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--libnc-root",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05"),
    )
    parser.add_argument(
        "--raw-input",
        type=Path,
        default=Path("/home/x/deco/256one/enwiki9/data/enwik9"),
    )
    parser.add_argument(
        "--initial-export",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_relative_parity_v1/"
            "run_05/export"
        ),
    )
    parser.add_argument(
        "--exporter-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_export.c",
    )
    parser.add_argument(
        "--hook-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_internal_tensor_hook.c",
    )
    parser.add_argument(
        "--parent-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_second_segment_attention_trajectory_v1/decision.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an embedding decision")
    libnc_root = args.libnc_root.resolve()
    required = (
        libnc_root / "nncp.c",
        libnc_root / "libnc.so",
        args.raw_input,
        args.initial_export / "manifest.json",
        args.exporter_source,
        args.hook_source,
        args.parent_decision,
    )
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, corpus, export, hook, or parent")
    parent = json.loads(args.parent_decision.read_text())
    if parent.get("status") != "ATTENTION_OPERATION_LOCALIZED":
        raise ValueError("unexpected attention parent status")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-embedding-") as temp:
        temporary = Path(temp)
        control_build_dir = temporary / "control_build"
        observed_build_dir = temporary / "observed_build"
        control_build_dir.mkdir()
        observed_build_dir.mkdir()
        input_path = temporary / "enwik9.prefix32"
        with args.raw_input.open("rb") as source:
            raw = source.read(BYTES)
        input_path.write_bytes(raw)

        control_executable, _, control_hook, control_build = compile_variant(
            libnc_root,
            args.exporter_source.resolve(),
            args.hook_source.resolve(),
            control_build_dir,
            attention.patch_attention_source,
        )
        executable, exporter, hook, build = compile_variant(
            libnc_root,
            args.exporter_source.resolve(),
            args.hook_source.resolve(),
            observed_build_dir,
            patch_embedding_source,
        )
        control_prefix = multi.command_prefix(
            control_executable, Path("unused.initial.coefs")
        )
        prefix = multi.command_prefix(executable, Path("unused.initial.coefs"))
        control = forward.native_run(
            "control", temporary, control_prefix, input_path, control_hook
        )
        runs = [
            forward.native_run(label, temporary, prefix, input_path, hook)
            for label in ("first", "second")
        ]
        hashes = run_hashes(runs)
        control_hashes = run_hashes([control])
        records = [internal.parse_dump(run["dump"]) for run in runs]
        control_records = internal.parse_dump(control["dump"])
        stripped_records = [
            [(label, value) for label, value in run_records if label != "a_input"]
            for run_records in records
        ]
        observation_repeat = (
            hashes["archive"][0] == hashes["archive"][1]
            and hashes["trace"][0] == hashes["trace"][1]
            and hashes["coefs"][0] == hashes["coefs"][1]
            and hashes["memory"][0] == hashes["memory"][1]
            and hashes["dump"][0] == hashes["dump"][1]
        )
        observation_neutral = (
            hashes["archive"][0] == control_hashes["archive"][0]
            and hashes["trace"][0] == control_hashes["trace"][0]
            and hashes["coefs"][0] == control_hashes["coefs"][0]
            and hashes["memory"][0] == control_hashes["memory"][0]
            and forward.trajectory_hash(stripped_records[0])
            == forward.trajectory_hash(control_records)
            and hashes["archive"][0] == parent["native_proof"]["archive_sha256"][0]
            and hashes["trace"][0] == parent["native_proof"]["trace_sha256"][0]
            and hashes["coefs"][0]
            == parent["native_proof"]["post_update_coefs_sha256"][0]
            and hashes["memory"][0]
            == parent["native_proof"]["post_update_memory_sha256"][0]
        )
        if not observation_repeat or not observation_neutral:
            raise RuntimeError("input observation changed or failed to repeat source")

        segments = [attention.split_segments(value) for value in records]
        second_segment = segments[0][1]
        input_records = [value for label, value in second_segment if label == "a_input"]
        if len(input_records) != 1 or input_records[0].size != 1:
            raise RuntimeError("missing unique source input observation")
        observed_float = float(input_records[0][0])
        observed_symbol = int(observed_float)
        if observed_float != observed_symbol or not 0 <= observed_symbol < 256:
            raise RuntimeError("source input observation is not a legal exact symbol")

        source_parameters = update_state.export_file(
            exporter, runs[0]["coefs"][0], temporary / "source_step_00_coefs"
        )
        memory_export = update_state.export_file(
            exporter, runs[0]["memories"][0], temporary / "source_step_00_memory"
        )
        source_memory = update_state.canonical_memory(memory_export["mem_h_0"])
        symbols, _ = base.load_trace(runs[0]["trace"])
        assumed_symbol = int(symbols[SEGMENT - 1])
        source_reference = [
            (label, value)
            for label, value in second_segment
            if label.startswith("a_") and label != "a_input"
        ]
        candidate_runs = [
            attention.attention_trajectory(
                source_parameters, observed_symbol, source_memory
            )
            for _ in range(2)
        ]
        comparisons = internal.compare_trajectory(
            source_reference, candidate_runs[0]
        )
        first = next(
            (
                row
                for row in comparisons
                if row["maximum_absolute_error"] > TOLERANCE
            ),
            None,
        )
        replay_repeat = (
            forward.trajectory_hash(candidate_runs[0])
            == forward.trajectory_hash(candidate_runs[1])
        )
        embed_row = comparisons[0]
        if observed_symbol != assumed_symbol and embed_row["maximum_absolute_error"] <= TOLERANCE:
            boundary = "decoder_input_schedule"
        elif observed_symbol == assumed_symbol and embed_row["maximum_absolute_error"] > TOLERANCE:
            boundary = "live_embedding_state"
        else:
            boundary = "ambiguous"
        localized = boundary != "ambiguous"
        result = {
            "schema": "gamma.nncp_v33_libnc_second_segment_embedding_contract.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "EMBEDDING_CONTRACT_LOCALIZED" if localized else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "raw_bytes": BYTES,
                "segment": 2,
                "state": 0,
                "threshold": TOLERANCE,
                "observation": "integer decoder input after slice and reshape",
            },
            "inputs": {
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "raw_corpus_sha256": internal.sha256(args.raw_input),
                "raw_prefix_sha256": hashlib.sha256(raw).hexdigest(),
                "parent_decision_sha256": internal.sha256(args.parent_decision),
                "hook_source_sha256": internal.sha256(args.hook_source),
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
            },
            "build": build,
            "control_build": control_build,
            "native_proof": {
                "command": runs[0]["command"],
                "archive_sha256": hashes["archive"],
                "trace_sha256": hashes["trace"],
                "post_update_coefs_sha256": hashes["coefs"],
                "post_update_memory_sha256": hashes["memory"],
                "observed_dump_sha256": hashes["dump"],
                "control_dump_sha256": control_hashes["dump"],
                "record_count": [len(value) for value in records],
                "control_record_count": len(control_records),
                "repeat_byte_identical": observation_repeat,
                "observation_neutral": observation_neutral,
            },
            "embedding_replay": {
                "assumed_preceding_symbol": assumed_symbol,
                "observed_source_symbol": observed_symbol,
                "symbols_equal": observed_symbol == assumed_symbol,
                "repeat_byte_identical": replay_repeat,
                "trajectory_sha256": [
                    forward.trajectory_hash(value) for value in candidate_runs
                ],
                "embedding_maximum_absolute_error": embed_row[
                    "maximum_absolute_error"
                ],
                "first_divergence": first,
                "trajectory": comparisons,
            },
            "localization": {"boundary": boundary, "unique": localized},
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": (
                    f"freeze one constructive {boundary} child"
                    if localized
                    else "retire this embedding localization realization"
                ),
                "forecast_bytes": 109_389_323,
                "verified_full_1g_score_bytes": None,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
