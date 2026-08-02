#!/usr/bin/env python3
"""Localize nonzero-memory attention arithmetic in the second LibNC segment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import torch
import torch.nn.functional as F

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_concat_rmsnorm_multiupdate_parity as multi
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_second_segment_forward_trajectory as forward
import nncp_v33_libnc_update_state_trajectory as update_state


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_second_segment_attention_trajectory_v1"
BYTES = 32
SEGMENT = 4
TOLERANCE = 2e-6


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"unexpected source marker count for {old[:60]!r}")
    return source.replace(old, new, 1)


def patch_attention_source(source: str) -> str:
    source = update_state.patch_source(source)
    source = replace_once(
        source,
        "    for(layer_idx = 0; layer_idx < s->n_layer; layer_idx++) {\n"
        "        TransformerLayer *tl = &s->layers[layer_idx];",
        "#ifdef DUMP_HASH\n"
        "    if (output_index == 0) nc_dump_tensor_hash(\"a_embed\", layer_input);\n"
        "#endif\n"
        "    for(layer_idx = 0; layer_idx < s->n_layer; layer_idx++) {\n"
        "        TransformerLayer *tl = &s->layers[layer_idx];",
    )
    source = replace_once(
        source,
        "        /* save the matrix input */\n",
        "#ifdef DUMP_HASH\n"
        "        if (output_index == 0) nc_dump_tensor_hash(\"a_norm\", layer_input1);\n"
        "#endif\n\n"
        "        /* save the matrix input */\n",
    )
    source = replace_once(
        source,
        "        t0 = nc_matmul(nc_dup_tensor(tl->w_kv), layer_input1);\n"
        "        key = nc_slice(nc_dup_tensor(t0), 0, 0, s->n_head * s->d_key);",
        "        t0 = nc_matmul(nc_dup_tensor(tl->w_kv), layer_input1);\n"
        "#ifdef DUMP_HASH\n"
        "        if (output_index == 0) {\n"
        "            nc_dump_tensor_hash(\"a_query\", query);\n"
        "            nc_dump_tensor_hash(\"a_current_kv\", t0);\n"
        "        }\n"
        "#endif\n"
        "        key = nc_slice(nc_dup_tensor(t0), 0, 0, s->n_head * s->d_key);",
    )
    source = replace_once(
        source,
        "            t0 = nc_matmul(nc_dup_tensor(tl->w_kv), t0);\n"
        "            \n"
        "            key0 = nc_slice(nc_dup_tensor(t0), 0, 0, s->n_head * s->d_key);",
        "            t0 = nc_matmul(nc_dup_tensor(tl->w_kv), t0);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_memory_kv\", t0);\n"
        "#endif\n"
        "            \n"
        "            key0 = nc_slice(nc_dup_tensor(t0), 0, 0, s->n_head * s->d_key);",
    )
    source = replace_once(
        source,
        "        value = split_head(value, s->n_head);\n"
        "        \n"
        "        if (output_index <= 0 && !s->rotary_pos_embed) {",
        "        value = split_head(value, s->n_head);\n"
        "#ifdef DUMP_HASH\n"
        "        if (output_index == 0) {\n"
        "            nc_dump_tensor_hash(\"a_current_key_heads\", key);\n"
        "            nc_dump_tensor_hash(\"a_query_heads\", query);\n"
        "            nc_dump_tensor_hash(\"a_current_value_heads\", value);\n"
        "        }\n"
        "#endif\n"
        "        \n"
        "        if (output_index <= 0 && !s->rotary_pos_embed) {",
    )
    source = replace_once(
        source,
        "            value = nc_dup_tensor(tl->mem_value);\n"
        "            \n"
        "            /* cross product term */",
        "            value = nc_dup_tensor(tl->mem_value);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) {\n"
        "                nc_dump_tensor_hash(\"a_all_key\", key);\n"
        "                nc_dump_tensor_hash(\"a_all_value\", value);\n"
        "            }\n"
        "#endif\n"
        "            \n"
        "            /* cross product term */",
    )
    source = replace_once(
        source,
        "            t0 = nc_matmul_add(key, nc_dup_tensor(query), NULL, TRUE, FALSE, 1.0);\n"
        "            node = nc_get_node(t0);",
        "            t0 = nc_matmul_add(key, nc_dup_tensor(query), NULL, TRUE, FALSE, 1.0);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_content\", t0);\n"
        "#endif\n"
        "            node = nc_get_node(t0);",
    )
    source = replace_once(
        source,
        "            rd = nc_rel_shift(rd, -(s->train_len - 1 - output_index), 1);\n"
        "            t0 = nc_add(rd, t0);",
        "            rd = nc_rel_shift(rd, -(s->train_len - 1 - output_index), 1);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_relative\", rd);\n"
        "#endif\n"
        "            t0 = nc_add(rd, t0);",
    )
    source = replace_once(
        source,
        "            t0 = nc_masked_fill(t0, t1, -INFINITY, 0);\n"
        "            \n"
        "            t1 = nc_soft_max(t0);",
        "            t0 = nc_masked_fill(t0, t1, -INFINITY, 0);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_score\", t0);\n"
        "#endif\n"
        "            \n"
        "            t1 = nc_soft_max(t0);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_attention\", t1);\n"
        "#endif",
    )
    source = replace_once(
        source,
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));\n"
        "            node = nc_get_node(t0);",
        "            t0 = nc_matmul(value, nc_dup_tensor(t1));\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_attended_heads\", t0);\n"
        "#endif\n"
        "            node = nc_get_node(t0);",
    )
    source = replace_once(
        source,
        "            t0 = concat_head(t0);\n"
        "        \n"
        "            /* linear layer */\n"
        "            t0 = nc_matmul(nc_dup_tensor(tl->w_o), t0);",
        "            t0 = concat_head(t0);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_attended_concat\", t0);\n"
        "#endif\n"
        "        \n"
        "            /* linear layer */\n"
        "            t0 = nc_matmul(nc_dup_tensor(tl->w_o), t0);\n"
        "#ifdef DUMP_HASH\n"
        "            if (output_index == 0) nc_dump_tensor_hash(\"a_projection\", t0);\n"
        "#endif",
    )
    return source


def compile_native(
    libnc_root: Path,
    exporter_source: Path,
    hook_source: Path,
    temporary: Path,
) -> tuple[Path, Path, Path, dict[str, object]]:
    compiler = os.environ.get("CC", "cc")
    patched_source = temporary / "nncp_attention.c"
    patched_source.write_text(
        patch_attention_source((libnc_root / "nncp.c").read_text())
    )
    nncp_object = temporary / "nncp_attention.o"
    executable = temporary / "nncp_attention"
    exporter = temporary / "nncp_libnc_export"
    hook = temporary / "tensor_hook.so"
    commands = [
        [
            compiler, "-O3", "-Wall", "-Wpointer-arith", "-g",
            "-fno-math-errno", "-fno-trapping-math",
            '-DCONFIG_VERSION="2024-06-05"', "-DLIBNC_CONFIG_FULL",
            "-DDUMP_HASH", f"-I{libnc_root}", "-c", str(patched_source),
            "-o", str(nncp_object),
        ],
        [
            compiler, f"-Wl,-rpath,{libnc_root}", "-o", str(executable),
            str(nncp_object),
            *[str(libnc_root / name) for name in (
                "cmdopt.o", "cp_utils.o", "arith.o", "preprocess.o", "cutils.o"
            )],
            str(libnc_root / "libnc.so"), "-lz", "-lm", "-lpthread",
        ],
        [
            compiler, "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-Wno-unused-parameter", f"-I{libnc_root}", str(exporter_source),
            f"-L{libnc_root}", f"-Wl,-rpath,{libnc_root}", "-lnc", "-lm",
            "-ldl", "-lpthread", "-o", str(exporter),
        ],
        [
            compiler, "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-Wno-unused-parameter", "-shared", "-fPIC", f"-I{libnc_root}",
            str(hook_source), f"-L{libnc_root}", f"-Wl,-rpath,{libnc_root}",
            "-lnc", "-ldl", "-o", str(hook),
        ],
    ]
    stderrs = []
    for command in commands:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        stderrs.append(completed.stderr)
    return executable, exporter, hook, {
        "commands": commands,
        "stderrs": stderrs,
        "upstream_source_sha256": internal.sha256(libnc_root / "nncp.c"),
        "patched_source_sha256": internal.sha256(patched_source),
        "executable_sha256": internal.sha256(executable),
        "exporter_sha256": internal.sha256(exporter),
        "hook_sha256": internal.sha256(hook),
    }


def split_segments(records: list[tuple[str, np.ndarray]]) -> list[list[tuple[str, np.ndarray]]]:
    segments: list[list[tuple[str, np.ndarray]]] = []
    current: list[tuple[str, np.ndarray]] = []
    outputs = 0
    for record in records:
        current.append(record)
        if record[0] == "output":
            outputs += 1
            if outputs == SEGMENT:
                segments.append(current)
                current = []
                outputs = 0
    if current or len(segments) != BYTES // SEGMENT:
        raise ValueError("internal dump does not split into eight segments")
    return segments


def attention_trajectory(
    weights: dict[str, torch.Tensor], input_symbol: int, memory: torch.Tensor
) -> list[tuple[str, np.ndarray]]:
    heads = 2
    d_key = 8
    d_value = 8
    d_model = 32
    layer_input = weights["embed"][:, input_symbol].unsqueeze(0) * math.sqrt(d_model)
    normalized = decoder_graph.libnc_rms_norm(
        layer_input, weights["ln_g_0"], weights["ln_b_0"]
    )
    query_linear = F.linear(normalized, weights["w_q_0"])
    current_kv = F.linear(normalized, weights["w_kv_0"])
    current_key, current_value = torch.split(current_kv, (16, 16), dim=-1)
    memory_kv = F.linear(memory, weights["w_kv_0"])
    memory_key, memory_value = torch.split(memory_kv, (16, 16), dim=-1)
    query_heads = query_linear.view(1, heads, d_key).permute(1, 0, 2)
    current_key_heads = current_key.view(1, heads, d_key).permute(1, 0, 2)
    current_value_heads = current_value.view(1, heads, d_value).permute(1, 0, 2)
    memory_key_heads = memory_key.view(SEGMENT, heads, d_key).permute(1, 0, 2)
    memory_value_heads = memory_value.view(SEGMENT, heads, d_value).permute(1, 0, 2)
    all_key = torch.cat(
        (memory_key_heads, current_key_heads, torch.zeros(heads, 3, d_key)), dim=1
    )
    all_value = torch.cat(
        (memory_value_heads, current_value_heads, torch.zeros(heads, 3, d_value)), dim=1
    )
    content = torch.einsum("hkd,htd->htk", all_key, query_heads)
    relative_weight = weights["w_r_0"].permute(2, 1, 0)
    raw_relative = torch.einsum("hkd,htd->htk", relative_weight, query_heads)
    raw_relative = raw_relative + (
        weights["b_r_0"].T[:, None, :] * math.sqrt(d_key * d_model)
    )
    relative = decoder_graph.shifted_relative_row(raw_relative[:, 0, :], 0, SEGMENT)
    score = (content + relative) / math.sqrt(d_key)
    score = score.clone()
    score[:, :, SEGMENT + 1 :] = -torch.inf
    attention = torch.softmax(score, dim=-1)
    attended_heads = torch.einsum("htk,hkd->htd", attention, all_value)
    attended_concat = attended_heads.permute(1, 0, 2).reshape(1, heads * d_value)
    projection = F.linear(attended_concat, weights["w_o_0"])
    return [
        ("a_embed", layer_input.detach().numpy().ravel()),
        ("a_norm", normalized.detach().numpy().ravel()),
        ("a_query", query_linear.detach().numpy().ravel()),
        ("a_current_kv", current_kv.detach().numpy().ravel()),
        ("a_memory_kv", memory_kv.detach().numpy().ravel()),
        ("a_current_key_heads", current_key_heads.detach().numpy().ravel()),
        ("a_query_heads", query_heads.detach().numpy().ravel()),
        ("a_current_value_heads", current_value_heads.detach().numpy().ravel()),
        ("a_all_key", all_key.detach().numpy().ravel()),
        ("a_all_value", all_value.detach().numpy().ravel()),
        ("a_content", content.detach().numpy().ravel()),
        ("a_relative", relative.detach().numpy().ravel()),
        ("a_score", score.detach().numpy().ravel()),
        ("a_attention", attention.detach().numpy().ravel()),
        ("a_attended_heads", attended_heads.detach().numpy().ravel()),
        ("a_attended_concat", attended_concat.detach().numpy().ravel()),
        ("a_projection", projection.detach().numpy().ravel()),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libnc-root", type=Path, default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05"))
    parser.add_argument("--raw-input", type=Path, default=Path("/home/x/deco/256one/enwiki9/data/enwik9"))
    parser.add_argument("--initial-export", type=Path, default=Path("/home/x/enwiki9-nonproof/results/nncp_v33_relative_parity_v1/run_05/export"))
    parser.add_argument("--exporter-source", type=Path, default=ROOT / "tools/nncp_libnc_export.c")
    parser.add_argument("--hook-source", type=Path, default=ROOT / "tools/nncp_libnc_internal_tensor_hook.c")
    parser.add_argument("--parent-decision", type=Path, default=ROOT / "results/nncp_v33_libnc_second_segment_forward_trajectory_v1/decision.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / CANDIDATE_ID / "decision.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an attention decision")
    libnc_root = args.libnc_root.resolve()
    required = (libnc_root / "nncp.c", libnc_root / "libnc.so", args.raw_input,
                args.initial_export / "manifest.json", args.exporter_source,
                args.hook_source, args.parent_decision)
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, corpus, export, hook, or parent")
    parent = json.loads(args.parent_decision.read_text())
    if parent.get("status") != "FORWARD_LOCALIZED":
        raise ValueError("unexpected forward parent status")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-attention-") as temp:
        temporary = Path(temp)
        input_path = temporary / "enwik9.prefix32"
        with args.raw_input.open("rb") as source:
            raw = source.read(BYTES)
        input_path.write_bytes(raw)
        executable, exporter, hook, build = compile_native(
            libnc_root, args.exporter_source.resolve(), args.hook_source.resolve(), temporary
        )
        prefix = multi.command_prefix(executable, Path("unused.initial.coefs"))
        runs = [forward.native_run(label, temporary, prefix, input_path, hook)
                for label in ("first", "second")]
        archive_hashes = [internal.sha256(run["archive"]) for run in runs]
        trace_hashes = [internal.sha256(run["trace"]) for run in runs]
        coefs_hashes = [[internal.sha256(path) for path in run["coefs"]] for run in runs]
        memory_hashes = [[internal.sha256(path) for path in run["memories"]] for run in runs]
        dump_hashes = [internal.dump_sha256(run["dump"]) for run in runs]
        all_records = [internal.parse_dump(run["dump"]) for run in runs]
        segments = [split_segments(records) for records in all_records]
        repeat = (archive_hashes[0] == archive_hashes[1]
                  and trace_hashes[0] == trace_hashes[1]
                  and coefs_hashes[0] == coefs_hashes[1]
                  and memory_hashes[0] == memory_hashes[1]
                  and dump_hashes[0] == dump_hashes[1])
        neutral = (archive_hashes[0] == parent["native_proof"]["archive_sha256"][0]
                   and trace_hashes[0] == parent["native_proof"]["trace_sha256"][0]
                   and coefs_hashes[0] == parent["native_proof"]["post_update_coefs_sha256"][0]
                   and memory_hashes[0] == parent["native_proof"]["post_update_memory_sha256"][0])
        if not repeat or not neutral:
            raise RuntimeError("attention observations changed or failed to repeat source")
        source_parameters = update_state.export_file(
            exporter, runs[0]["coefs"][0], temporary / "source_step_00_coefs"
        )
        memory_export = update_state.export_file(
            exporter, runs[0]["memories"][0], temporary / "source_step_00_memory"
        )
        source_memory = update_state.canonical_memory(memory_export["mem_h_0"])
        symbols, _ = base.load_trace(runs[0]["trace"])
        reference = [(label, value) for label, value in segments[0][1]
                     if label.startswith("a_")]
        candidate_runs = [attention_trajectory(
            source_parameters, int(symbols[SEGMENT - 1]), source_memory
        ) for _ in range(2)]
        comparisons = internal.compare_trajectory(reference, candidate_runs[0])
        first = next((row for row in comparisons
                      if row["maximum_absolute_error"] > TOLERANCE), None)
        repeated_replay = forward.trajectory_hash(candidate_runs[0]) == forward.trajectory_hash(candidate_runs[1])
        localized = first is not None
        result = {
            "schema": "gamma.nncp_v33_libnc_second_segment_attention_trajectory.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "ATTENTION_OPERATION_LOCALIZED" if localized else "REJECT",
            "score_credit_bytes": 0,
            "contract": {"raw_bytes": BYTES, "segment": 2, "state": 0,
                         "threshold": TOLERANCE, "layout_selection": "fixed_from_libnc_dimensions"},
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
            "native_proof": {
                "command": runs[0]["command"], "archive_sha256": archive_hashes,
                "trace_sha256": trace_hashes, "post_update_coefs_sha256": coefs_hashes,
                "post_update_memory_sha256": memory_hashes, "attention_dump_sha256": dump_hashes,
                "record_count": [len(value) for value in all_records],
                "segment_record_count": [[len(item) for item in value] for value in segments],
                "repeat_byte_identical": repeat, "observation_neutral": neutral,
            },
            "analytic_replay": {
                "repeat_byte_identical": repeated_replay,
                "trajectory_sha256": [forward.trajectory_hash(value) for value in candidate_runs],
                "first_divergence": first, "trajectory": comparisons,
            },
            "localization": {
                "boundary": f"attention_operation:{first['label']}" if first else "unresolved_after_projection",
                "unique": localized,
            },
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": (f"freeze one contract child for {first['label']}" if first
                                           else "retire this attention localization realization"),
                "forecast_bytes": 109_389_323, "verified_full_1g_score_bytes": None,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
