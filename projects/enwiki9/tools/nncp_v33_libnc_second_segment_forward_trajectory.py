#!/usr/bin/env python3
"""Localize the first second-segment LibNC forward divergence."""

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
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay
import nncp_v33_libnc_update_state_trajectory as update_state


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_second_segment_forward_trajectory_v1"
BYTES = 32
SEGMENT = 4
LABELS_PER_STATE = 7
RECORDS_PER_SEGMENT = SEGMENT * LABELS_PER_STATE
TOLERANCE = 2e-6


def trajectory_hash(records: list[tuple[str, np.ndarray]]) -> str:
    digest = hashlib.sha256()
    for label, value in records:
        digest.update(label.encode("utf-8") + b"\0")
        digest.update(np.asarray(value, dtype="<f4").tobytes())
    return digest.hexdigest()


def state_trajectory(
    weights: dict[str, torch.Tensor],
    input_symbols: np.ndarray,
    memory: torch.Tensor,
) -> list[tuple[str, np.ndarray]]:
    """Replay one four-state decoder segment from an explicit source state."""
    if len(input_symbols) != SEGMENT or tuple(memory.shape) != (SEGMENT, 32):
        raise ValueError("unexpected segment input or memory shape")
    heads = 2
    d_key = 8
    d_value = 8
    d_model = 32
    memory_key_value = F.linear(memory, weights["w_kv_0"])
    memory_key, memory_value = torch.split(
        memory_key_value, (heads * d_key, heads * d_value), dim=-1
    )
    memory_key = memory_key.view(SEGMENT, heads, d_key).permute(1, 0, 2)
    memory_value = memory_value.view(SEGMENT, heads, d_value).permute(1, 0, 2)
    current_keys: list[torch.Tensor] = []
    current_values: list[torch.Tensor] = []
    records: list[tuple[str, np.ndarray]] = []
    relative_weight = weights["w_r_0"].permute(2, 1, 0)
    relative_scale = math.sqrt(d_key * d_model)

    for position in range(SEGMENT):
        layer_input = (
            weights["embed"][:, int(input_symbols[position])].unsqueeze(0)
            * math.sqrt(d_model)
        )
        normalized = decoder_graph.libnc_rms_norm(
            layer_input, weights["ln_g_0"], weights["ln_b_0"]
        )
        query = F.linear(normalized, weights["w_q_0"])
        key_value = F.linear(normalized, weights["w_kv_0"])
        key, value = torch.split(
            key_value, (heads * d_key, heads * d_value), dim=-1
        )
        query = query.view(1, heads, d_key).permute(1, 0, 2)
        key = key.view(1, heads, d_key).permute(1, 0, 2)
        value = value.view(1, heads, d_value).permute(1, 0, 2)
        current_keys.append(key)
        current_values.append(value)
        future = SEGMENT - position - 1
        key_parts = [memory_key, *current_keys]
        value_parts = [memory_value, *current_values]
        if future:
            key_parts.append(torch.zeros(heads, future, d_key))
            value_parts.append(torch.zeros(heads, future, d_value))
        all_key = torch.cat(key_parts, dim=1)
        all_value = torch.cat(value_parts, dim=1)
        content = torch.einsum("hkd,htd->htk", all_key, query)
        raw_relative = torch.einsum("hkd,htd->htk", relative_weight, query)
        raw_relative = raw_relative + (
            weights["b_r_0"].T[:, None, :] * relative_scale
        )
        relative = decoder_graph.shifted_relative_row(
            raw_relative[:, 0, :], position, SEGMENT
        )
        score = (content + relative) / math.sqrt(d_key)
        if future:
            score = score.clone()
            score[:, :, SEGMENT + position + 1 :] = -torch.inf
        attention = torch.softmax(score, dim=-1)
        attended = torch.einsum("htk,hkd->htd", attention, all_value)
        attended = attended.permute(1, 0, 2).reshape(1, heads * d_value)
        layer_input = layer_input + F.linear(attended, weights["w_o_0"])
        values = layer_input.detach().numpy().ravel()
        records.append(("attn_out_bl", values))
        records.append(("attn_out", values))
        feedforward_input = decoder_graph.libnc_rms_norm(
            layer_input, weights["ln_g_1"], weights["ln_b_1"]
        )
        feedforward_output = F.linear(
            feedforward_input, weights["ff1_0"], weights["ff_bias1_0"]
        )
        records.append(
            ("ff1_out", feedforward_output.detach().numpy().ravel())
        )
        gate, value_ff = feedforward_output.chunk(2, dim=-1)
        hidden = gelu_replay.libnc_gelu(gate) * value_ff
        records.append(("ff2_in", hidden.detach().numpy().ravel()))
        layer_input = layer_input + F.linear(
            hidden, weights["ff2_0"], weights["ff_bias2_0"]
        )
        values = layer_input.detach().numpy().ravel()
        records.append(("ff_out_bl", values))
        records.append(("ff_out", values))
        final = decoder_graph.libnc_rms_norm(
            layer_input, weights["ln_g_2"], weights["ln_b_2"]
        )
        logits = F.linear(final, weights["embed_out"], weights["out_bias"])
        probabilities = torch.softmax(logits, dim=-1)
        records.append(("output", probabilities.detach().numpy().ravel()))
    return records


def compile_native(
    libnc_root: Path,
    exporter_source: Path,
    hook_source: Path,
    temporary: Path,
) -> tuple[Path, Path, Path, dict[str, object]]:
    compiler = os.environ.get("CC", "cc")
    patched_source = temporary / "nncp_second_segment.c"
    patched_source.write_text(
        update_state.patch_source((libnc_root / "nncp.c").read_text())
    )
    nncp_object = temporary / "nncp_second_segment.o"
    executable = temporary / "nncp_second_segment"
    exporter = temporary / "nncp_libnc_export"
    hook = temporary / "tensor_hook.so"
    commands: list[list[str]] = []
    stderrs: list[str] = []

    commands.append(
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
            "-DDUMP_HASH",
            f"-I{libnc_root}",
            "-c",
            str(patched_source),
            "-o",
            str(nncp_object),
        ]
    )
    commands.append(
        [
            compiler,
            f"-Wl,-rpath,{libnc_root}",
            "-o",
            str(executable),
            str(nncp_object),
            *[
                str(libnc_root / name)
                for name in (
                    "cmdopt.o",
                    "cp_utils.o",
                    "arith.o",
                    "preprocess.o",
                    "cutils.o",
                )
            ],
            str(libnc_root / "libnc.so"),
            "-lz",
            "-lm",
            "-lpthread",
        ]
    )
    commands.append(
        [
            compiler,
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            f"-I{libnc_root}",
            str(exporter_source),
            f"-L{libnc_root}",
            f"-Wl,-rpath,{libnc_root}",
            "-lnc",
            "-lm",
            "-ldl",
            "-lpthread",
            "-o",
            str(exporter),
        ]
    )
    commands.append(
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
            f"-I{libnc_root}",
            str(hook_source),
            f"-L{libnc_root}",
            f"-Wl,-rpath,{libnc_root}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ]
    )
    for command in commands:
        completed = subprocess.run(
            command, check=True, capture_output=True, text=True
        )
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


def native_run(
    label: str,
    temporary: Path,
    command_prefix: list[str],
    input_path: Path,
    hook: Path,
) -> dict[str, object]:
    directory = temporary / label
    state_directory = directory / "states"
    dump_directory = directory / "tensors"
    state_directory.mkdir(parents=True)
    dump_directory.mkdir()
    archive = directory / "archive.bin"
    trace = directory / "teacher.bin"
    environment = dict(os.environ)
    environment["LD_PRELOAD"] = str(hook)
    environment["NNCP_TEACHER_TRACE"] = str(trace)
    environment["NNCP_UPDATE_STATE_DIR"] = str(state_directory)
    environment["NNCP_INTERNAL_DUMP_DIR"] = str(dump_directory)
    command = [*command_prefix, "c", str(input_path), str(archive)]
    completed = subprocess.run(
        command, check=True, capture_output=True, text=True, env=environment
    )
    coefs = [state_directory / f"step_{step:02d}.coefs" for step in range(8)]
    memories = [state_directory / f"step_{step:02d}.memory" for step in range(8)]
    if not all(path.is_file() for path in (archive, trace, *coefs, *memories)):
        raise RuntimeError("native second-segment capture is incomplete")
    return {
        "archive": archive,
        "trace": trace,
        "coefs": coefs,
        "memories": memories,
        "dump": dump_directory,
        "command": command,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }


def first_divergence(rows: list[dict[str, object]]) -> dict[str, object] | None:
    return next(
        (
            row
            for row in rows
            if row["maximum_absolute_error"] > TOLERANCE
        ),
        None,
    )


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
        / "results/nncp_v33_libnc_update_state_trajectory_v1/decision.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite a forward decision")
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
    if parent.get("status") != "STATE_DIVERGENCE_LOCALIZED":
        raise ValueError("unexpected update-state parent status")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-second-forward-") as temp:
        temporary = Path(temp)
        input_path = temporary / "enwik9.prefix32"
        with args.raw_input.open("rb") as source:
            raw = source.read(BYTES)
        input_path.write_bytes(raw)
        executable, exporter, hook, build = compile_native(
            libnc_root,
            args.exporter_source.resolve(),
            args.hook_source.resolve(),
            temporary,
        )
        prefix = multi.command_prefix(executable, Path("unused.initial.coefs"))
        runs = [
            native_run(label, temporary, prefix, input_path, hook)
            for label in ("first", "second")
        ]
        archive_hashes = [internal.sha256(run["archive"]) for run in runs]
        trace_hashes = [internal.sha256(run["trace"]) for run in runs]
        coefs_hashes = [
            [internal.sha256(path) for path in run["coefs"]] for run in runs
        ]
        memory_hashes = [
            [internal.sha256(path) for path in run["memories"]] for run in runs
        ]
        dump_hashes = [internal.dump_sha256(run["dump"]) for run in runs]
        records = [internal.parse_dump(run["dump"]) for run in runs]
        expected_records = (BYTES // SEGMENT) * RECORDS_PER_SEGMENT
        if any(len(value) != expected_records for value in records):
            raise RuntimeError("unexpected internal forward record count")
        source_repeat = (
            archive_hashes[0] == archive_hashes[1]
            and trace_hashes[0] == trace_hashes[1]
            and coefs_hashes[0] == coefs_hashes[1]
            and memory_hashes[0] == memory_hashes[1]
            and dump_hashes[0] == dump_hashes[1]
        )
        observation_neutral = (
            archive_hashes[0] == parent["native_proof"]["archive_sha256"][0]
            and trace_hashes[0] == parent["native_proof"]["trace_sha256"][0]
            and coefs_hashes[0]
            == parent["native_proof"]["post_update_coefs_sha256"][0]
            and memory_hashes[0]
            == parent["native_proof"]["post_update_memory_sha256"][0]
        )
        if not source_repeat or not observation_neutral:
            raise RuntimeError("forward observations changed or failed to repeat source")

        source_parameters = update_state.export_file(
            exporter, runs[0]["coefs"][0], temporary / "source_step_00_coefs"
        )
        source_memory_export = update_state.export_file(
            exporter,
            runs[0]["memories"][0],
            temporary / "source_step_00_memory",
        )
        source_memory = update_state.canonical_memory(
            source_memory_export["mem_h_0"]
        )
        symbols, _ = base.load_trace(runs[0]["trace"])
        if len(symbols) != BYTES or not np.array_equal(
            symbols, np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
        ):
            raise RuntimeError("source symbols do not bind the raw prefix")
        segment_inputs = symbols[SEGMENT - 1 : 2 * SEGMENT - 1]
        source_reference = records[0][RECORDS_PER_SEGMENT : 2 * RECORDS_PER_SEGMENT]
        source_replays = [
            state_trajectory(source_parameters, segment_inputs, source_memory)
            for _ in range(2)
        ]
        source_replay_repeat = (
            trajectory_hash(source_replays[0]) == trajectory_hash(source_replays[1])
        )
        source_comparison = internal.compare_trajectory(
            source_reference, source_replays[0]
        )

        initial, _ = base.load_export(args.initial_export)
        analytic_runs = [
            update_state.analytic_trajectory(initial, symbols[:SEGMENT], 0.00016, 0.05)
            for _ in range(2)
        ]
        analytic_parameters = analytic_runs[0][1][0]
        analytic_memory = analytic_runs[0][2][0]
        analytic_replays = [
            state_trajectory(analytic_parameters, segment_inputs, analytic_memory)
            for _ in range(2)
        ]
        analytic_replay_repeat = (
            trajectory_hash(analytic_replays[0])
            == trajectory_hash(analytic_replays[1])
        )
        analytic_comparison = internal.compare_trajectory(
            source_reference, analytic_replays[0]
        )
        source_first = first_divergence(source_comparison)
        analytic_first = first_divergence(analytic_comparison)
        source_matches = source_first is None
        localized = source_first is not None or (source_matches and analytic_first is not None)
        if source_first is not None:
            boundary = f"forward_block:{source_first['label']}"
            action = f"instrument arithmetic inside {source_first['label']}"
        elif analytic_first is not None:
            boundary = "exact_state_evolution"
            action = "freeze exact state-rounding and serialization contract"
        else:
            boundary = "ambiguous"
            action = "retire this localization realization"

        parameter_errors = {
            name: float(
                (source_parameters[name] - analytic_parameters[name]).abs().max()
            )
            for name in sorted(set(source_parameters) & set(analytic_parameters))
        }
        result = {
            "schema": "gamma.nncp_v33_libnc_second_segment_forward_trajectory.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "FORWARD_LOCALIZED" if localized else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "raw_bytes": BYTES,
                "segment": SEGMENT,
                "source_segment": 2,
                "states": SEGMENT,
                "labels_per_state": LABELS_PER_STATE,
                "threshold": TOLERANCE,
                "source_state_is_primary": True,
                "analytic_state_is_sensitivity_control": True,
            },
            "inputs": {
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "raw_corpus_sha256": internal.sha256(args.raw_input),
                "raw_prefix_sha256": hashlib.sha256(raw).hexdigest(),
                "initial_manifest_sha256": internal.sha256(
                    args.initial_export / "manifest.json"
                ),
                "parent_decision_sha256": internal.sha256(args.parent_decision),
                "hook_source_sha256": internal.sha256(args.hook_source),
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
            },
            "build": build,
            "native_proof": {
                "command": runs[0]["command"],
                "archive_sha256": archive_hashes,
                "trace_sha256": trace_hashes,
                "post_update_coefs_sha256": coefs_hashes,
                "post_update_memory_sha256": memory_hashes,
                "forward_dump_sha256": dump_hashes,
                "forward_record_count": [len(value) for value in records],
                "source_repeat_byte_identical": source_repeat,
                "observation_neutral": observation_neutral,
            },
            "source_state_replay": {
                "repeat_byte_identical": source_replay_repeat,
                "trajectory_sha256": [
                    trajectory_hash(value) for value in source_replays
                ],
                "first_divergence": source_first,
                "trajectory": source_comparison,
            },
            "analytic_state_control": {
                "repeat_byte_identical": analytic_replay_repeat,
                "trajectory_sha256": [
                    trajectory_hash(value) for value in analytic_replays
                ],
                "post_update_parameter_maximum_absolute_error": max(
                    parameter_errors.values()
                ),
                "post_update_parameter_maximum_errors": parameter_errors,
                "post_update_memory_maximum_absolute_error": float(
                    (source_memory - analytic_memory).abs().max()
                ),
                "first_divergence": analytic_first,
                "trajectory": analytic_comparison,
            },
            "localization": {
                "boundary": boundary,
                "unique": localized,
            },
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": action,
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
