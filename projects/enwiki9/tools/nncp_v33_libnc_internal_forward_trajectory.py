#!/usr/bin/env python3
"""Capture and compare receipt-bound LibNC internal forward tensors."""

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
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_internal_forward_trajectory_v1"
THRESHOLD = 2e-6
BOUND_ARCHIVE_SHA256 = (
    "8dd5482e51e5c85b92aab8e0ca9dffc8fc7d3458a2bfd2d669c2e9b1330646da"
)
BOUND_TRACE_SHA256 = (
    "cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def dump_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.iterdir()):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def state_trajectory(
    weights: dict[str, torch.Tensor], symbols: np.ndarray
) -> list[tuple[str, np.ndarray]]:
    segment = 4
    memory_length = 4
    heads = 2
    d_key = 8
    d_value = 8
    d_model = 32
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    memory = torch.zeros(memory_length, d_model, dtype=torch.float32)
    memory_key_value = F.linear(memory, weights["w_kv_0"])
    memory_key, memory_value = torch.split(
        memory_key_value, (heads * d_key, heads * d_value), dim=-1
    )
    memory_key = memory_key.view(memory_length, heads, d_key).permute(1, 0, 2)
    memory_value = memory_value.view(memory_length, heads, d_value).permute(
        1, 0, 2
    )
    current_keys: list[torch.Tensor] = []
    current_values: list[torch.Tensor] = []
    result: list[tuple[str, np.ndarray]] = []
    relative_weight = weights["w_r_0"].permute(2, 1, 0)
    relative_scale = math.sqrt(d_key * d_model)

    for position in range(segment):
        layer_input = (
            weights["embed"][:, int(inputs[position])].unsqueeze(0)
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
        future = segment - position - 1
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
            raw_relative[:, 0, :], position, segment
        )
        score = (content + relative) / math.sqrt(d_key)
        if future:
            score = score.clone()
            score[:, :, memory_length + position + 1 :] = -torch.inf
        attention = torch.softmax(score, dim=-1)
        attended = torch.einsum("htk,hkd->htd", attention, all_value)
        attended = attended.permute(1, 0, 2).reshape(1, heads * d_value)
        layer_input = layer_input + F.linear(attended, weights["w_o_0"])
        result.append(("attn_out_bl", layer_input.detach().numpy().ravel()))
        result.append(("attn_out", layer_input.detach().numpy().ravel()))
        feedforward_input = decoder_graph.libnc_rms_norm(
            layer_input, weights["ln_g_1"], weights["ln_b_1"]
        )
        feedforward_output = F.linear(
            feedforward_input, weights["ff1_0"], weights["ff_bias1_0"]
        )
        result.append(("ff1_out", feedforward_output.detach().numpy().ravel()))
        gate, value_ff = feedforward_output.chunk(2, dim=-1)
        hidden = gelu_replay.libnc_gelu(gate) * value_ff
        result.append(("ff2_in", hidden.detach().numpy().ravel()))
        layer_input = layer_input + F.linear(
            hidden, weights["ff2_0"], weights["ff_bias2_0"]
        )
        raw = layer_input.detach().numpy().ravel()
        result.append(("ff_out_bl", raw))
        result.append(("ff_out", raw))
        final = decoder_graph.libnc_rms_norm(
            layer_input, weights["ln_g_2"], weights["ln_b_2"]
        )
        logits = F.linear(final, weights["embed_out"], weights["out_bias"])
        probabilities = torch.softmax(logits, dim=-1)
        result.append(("output", probabilities.detach().numpy().ravel()))
    return result


def parse_dump(directory: Path) -> list[tuple[str, np.ndarray]]:
    records: list[tuple[str, np.ndarray]] = []
    for metadata in sorted(directory.glob("*.meta")):
        fields = dict(
            line.split("=", 1) for line in metadata.read_text().splitlines()
        )
        data = metadata.with_suffix(".bin")
        records.append((fields["label"], np.fromfile(data, dtype="<f4")))
    return records


def compare_trajectory(
    reference: list[tuple[str, np.ndarray]],
    candidate: list[tuple[str, np.ndarray]],
) -> list[dict[str, object]]:
    if len(reference) != len(candidate):
        raise ValueError(
            f"trajectory length mismatch: {len(reference)} != {len(candidate)}"
        )
    comparisons: list[dict[str, object]] = []
    for index, ((left_label, left), (right_label, right)) in enumerate(
        zip(reference, candidate)
    ):
        if left_label != right_label or left.shape != right.shape:
            raise ValueError(
                f"trajectory record mismatch at {index}: "
                f"{left_label}{left.shape} != {right_label}{right.shape}"
            )
        difference = left - right
        denominator = float(np.dot(right.astype(np.float64), right.astype(np.float64)))
        scale = (
            float(np.dot(left.astype(np.float64), right.astype(np.float64)))
            / denominator
            if denominator
            else 1.0
        )
        scaled_error = np.abs(left - np.float32(scale) * right)
        left_norm = float(np.linalg.norm(left.astype(np.float64)))
        right_norm = float(np.linalg.norm(right.astype(np.float64)))
        comparisons.append(
            {
                "index": index,
                "state": index // 7,
                "label": left_label,
                "elements": int(left.size),
                "maximum_absolute_error": float(np.abs(difference).max()),
                "mean_absolute_error": float(np.abs(difference).mean()),
                "libnc_l2_norm": left_norm,
                "pytorch_l2_norm": right_norm,
                "libnc_over_pytorch_norm": (
                    left_norm / right_norm if right_norm else None
                ),
                "best_scalar": scale,
                "maximum_absolute_error_after_scalar": float(
                    scaled_error.max()
                ),
            }
        )
    return comparisons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--libnc-root",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05"),
    )
    parser.add_argument(
        "--bound-dir",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_online_update_parity_v1/"
            "run_07_bound"
        ),
    )
    parser.add_argument(
        "--initial-coefs",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_v33_relative_parity_v1/"
            "run_05/mini.coefs"
        ),
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
        "--hook-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_internal_tensor_hook.c",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()
    libnc_root = args.libnc_root.resolve()
    required = [
        libnc_root / "nncp.c",
        libnc_root / "libnc.h",
        libnc_root / "libnc.so",
        args.bound_dir / "input.bin",
        args.bound_dir / "archive.bin",
        args.bound_dir / "teacher.bin",
        args.initial_coefs,
        args.initial_export / "manifest.json",
        args.hook_source,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, bound receipt, or hook input")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-internal-") as temp:
        temporary = Path(temp)
        object_path = temporary / "nncp_dump.o"
        executable = temporary / "nncp_dump"
        hook = temporary / "tensor_hook.so"
        compile_object = [
            os.environ.get("CC", "cc"),
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
            str(libnc_root / "nncp.c"),
            "-o",
            str(object_path),
        ]
        object_result = subprocess.run(
            compile_object, check=True, capture_output=True, text=True
        )
        link_command = [
            os.environ.get("CC", "cc"),
            f"-Wl,-rpath,{libnc_root}",
            "-o",
            str(executable),
            str(object_path),
            *[
                str(libnc_root / name)
                for name in ("cmdopt.o", "cp_utils.o", "arith.o", "preprocess.o", "cutils.o")
            ],
            str(libnc_root / "libnc.so"),
            "-lz",
            "-lm",
            "-lpthread",
        ]
        link_result = subprocess.run(
            link_command, check=True, capture_output=True, text=True
        )
        hook_command = [
            os.environ.get("CC", "cc"),
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            "-shared",
            "-fPIC",
            f"-I{libnc_root}",
            str(args.hook_source),
            f"-L{libnc_root}",
            f"-Wl,-rpath,{libnc_root}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ]
        hook_result = subprocess.run(
            hook_command, check=True, capture_output=True, text=True
        )
        command_prefix = [
            str(executable),
            "-q",
            "-p",
            "enwik9",
            "--max_size",
            "4",
            "--load_coefs",
            str(args.initial_coefs),
            "--bf16",
            "0",
            "--batch_size",
            "1",
            "--block_len",
            "4",
            "--train_len",
            "4",
            "--lr",
            "0.00016",
            "--retrain_period",
            "0",
            "--n_symb",
            "256",
            "--n_layer",
            "1",
            "--d_model",
            "32",
            "--n_head",
            "2",
            "--d_key",
            "8",
            "--d_value",
            "8",
            "--mem_len",
            "4",
            "--d_pos",
            "8",
            "--d_inner",
            "64",
            "--query_bias",
            "0",
            "--rot_pos",
            "0",
            "--init_range",
            "0.79",
            "--tied_embed",
            "0",
            "--use_bias",
            "1",
            "--use_w_r",
            "1",
            "--tied_w_r",
            "0",
            "--tied_b_r",
            "1",
            "--ln_flags",
            "22",
            "--gradient_clip",
            "0.05",
            "--attn_len",
            "8",
            "--embed_mult",
            "1",
            "--retrain_dropout",
            "0",
            "--retrain_dropout_att",
            "0",
            "--ff_act",
            "2",
            "--sparse_grad",
            "0",
        ]
        runs = []
        for label in ("first", "second"):
            run_dir = temporary / label
            dump_dir = run_dir / "tensors"
            dump_dir.mkdir(parents=True)
            archive = run_dir / "archive.bin"
            trace = run_dir / "teacher.bin"
            environment = os.environ.copy()
            environment["LD_PRELOAD"] = str(hook)
            environment["NNCP_INTERNAL_DUMP_DIR"] = str(dump_dir)
            environment["NNCP_TEACHER_TRACE"] = str(trace)
            command = [
                *command_prefix,
                "c",
                str(args.bound_dir / "input.bin"),
                str(archive),
            ]
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            runs.append(
                {
                    "label": label,
                    "archive": archive,
                    "trace": trace,
                    "dump": dump_dir,
                    "stdout_sha256": hashlib.sha256(
                        completed.stdout.encode("utf-8")
                    ).hexdigest(),
                    "stderr_sha256": hashlib.sha256(
                        completed.stderr.encode("utf-8")
                    ).hexdigest(),
                }
            )
        archive_hashes = [sha256(item["archive"]) for item in runs]
        trace_hashes = [sha256(item["trace"]) for item in runs]
        dump_hashes = [dump_sha256(item["dump"]) for item in runs]
        identity = (
            archive_hashes == [BOUND_ARCHIVE_SHA256, BOUND_ARCHIVE_SHA256]
            and trace_hashes == [BOUND_TRACE_SHA256, BOUND_TRACE_SHA256]
            and dump_hashes[0] == dump_hashes[1]
            and (runs[0]["archive"].read_bytes() == (args.bound_dir / "archive.bin").read_bytes())
            and (runs[0]["trace"].read_bytes() == (args.bound_dir / "teacher.bin").read_bytes())
        )
        if not identity:
            raise RuntimeError("DUMP_HASH build failed bound identity or repeat")
        weights, _ = base.load_export(args.initial_export)
        symbols, _ = base.load_trace(args.bound_dir / "teacher.bin")
        reference = parse_dump(runs[0]["dump"])
        candidate = state_trajectory(weights, symbols)
        comparisons = compare_trajectory(reference, candidate)
        first_divergence = next(
            (
                item
                for item in comparisons
                if item["maximum_absolute_error"] > THRESHOLD
            ),
            None,
        )
        localized = first_divergence is not None
        result = {
            "schema": "gamma.nncp_v33_libnc_internal_forward_trajectory.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "LOCALIZED" if localized else "NO_FORWARD_DIVERGENCE",
            "score_credit_bytes": 0,
            "contract": {
                "threshold": THRESHOLD,
                "symbols": 4,
                "states": 4,
                "labels_per_state": 7,
                "command": command_prefix,
            },
            "inputs": {
                "libnc_source_sha256": sha256(libnc_root / "nncp.c"),
                "libnc_header_sha256": sha256(libnc_root / "libnc.h"),
                "libnc_library_sha256": sha256(libnc_root / "libnc.so"),
                "hook_source_sha256": sha256(args.hook_source),
                "script_sha256": sha256(Path(__file__).resolve()),
                "initial_coefs_sha256": sha256(args.initial_coefs),
                "initial_manifest_sha256": sha256(
                    args.initial_export / "manifest.json"
                ),
                "bound_input_sha256": sha256(args.bound_dir / "input.bin"),
            },
            "build": {
                "object_command": compile_object,
                "object_stderr": object_result.stderr,
                "link_command": link_command,
                "link_stderr": link_result.stderr,
                "hook_command": hook_command,
                "hook_stderr": hook_result.stderr,
                "executable_sha256": sha256(executable),
                "hook_sha256": sha256(hook),
            },
            "identity": {
                "bound_archive_sha256": BOUND_ARCHIVE_SHA256,
                "run_archive_sha256": archive_hashes,
                "bound_trace_sha256": BOUND_TRACE_SHA256,
                "run_trace_sha256": trace_hashes,
                "run_dump_sha256": dump_hashes,
                "archive_byte_identical": True,
                "trace_byte_identical": True,
                "dump_repeat_byte_identical": True,
            },
            "trajectory": comparisons,
            "first_divergence": first_divergence,
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": (
                    "freeze the uniquely localized forward-contract child"
                    if localized
                    else "do not alter another forward primitive"
                ),
                "forecast_bytes": 109389323,
                "verified_full_1g_score_bytes": None,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
