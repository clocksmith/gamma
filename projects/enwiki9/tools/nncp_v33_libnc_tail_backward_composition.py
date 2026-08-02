#!/usr/bin/env python3
"""Test the exact LibNC decoder-tail gradient against the bound miniature."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import torch
import torch.nn.functional as F

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_internal_forward_trajectory as internal


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_tail_backward_composition_v1"
FEATURES = 32
CLASSES = 256
STATES = 4
TARGETS = np.asarray([60, 109, 101, 100], dtype=np.int64)
THRESHOLD = 2e-6


def aggregate_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in ("probabilities.bin", "tail_gradient.bin"):
        digest.update(name.encode("ascii") + b"\0")
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def compile_instrumented_nncp(
    libnc_root: Path,
    hook_source: Path,
    temporary: Path,
) -> tuple[Path, Path, dict[str, object]]:
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
        str(hook_source),
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
    return executable, hook, {
        "object_command": compile_object,
        "object_stderr": object_result.stderr,
        "link_command": link_command,
        "link_stderr": link_result.stderr,
        "hook_command": hook_command,
        "hook_stderr": hook_result.stderr,
        "executable_sha256": internal.sha256(executable),
        "hook_sha256": internal.sha256(hook),
    }


def compile_tail_probe(
    libnc_root: Path,
    probe_source: Path,
    temporary: Path,
) -> tuple[Path, dict[str, object]]:
    executable = temporary / "tail_probe"
    command = [
        os.environ.get("CC", "cc"),
        "-std=gnu11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-Wno-unused-parameter",
        f"-I{libnc_root}",
        str(probe_source),
        f"-L{libnc_root}",
        f"-Wl,-rpath,{libnc_root}",
        "-lnc",
        "-lm",
        "-ldl",
        "-lpthread",
        "-o",
        str(executable),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return executable, {
        "command": command,
        "stderr": result.stderr,
        "executable_sha256": internal.sha256(executable),
    }


def command_prefix(executable: Path, initial_coefs: Path) -> list[str]:
    return [
        str(executable),
        "-q",
        "-p",
        "enwik9",
        "--max_size",
        "4",
        "--load_coefs",
        str(initial_coefs),
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


def capture_run(
    label: str,
    temporary: Path,
    executable: Path,
    hook: Path,
    prefix: list[str],
    bound_dir: Path,
) -> dict[str, object]:
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
        *prefix,
        "c",
        str(bound_dir / "input.bin"),
        str(archive),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return {
        "label": label,
        "archive": archive,
        "trace": trace,
        "dump": dump_dir,
        "command": command,
        "stdout_sha256": hashlib.sha256(
            completed.stdout.encode("utf-8")
        ).hexdigest(),
        "stderr_sha256": hashlib.sha256(
            completed.stderr.encode("utf-8")
        ).hexdigest(),
    }


def ff_out_paths(directory: Path) -> list[Path]:
    result: list[Path] = []
    for metadata in sorted(directory.glob("*.meta")):
        fields = dict(
            line.split("=", 1) for line in metadata.read_text().splitlines()
        )
        if fields["label"] == "ff_out_bl":
            if fields["dims"] not in ("32", "32,1"):
                raise ValueError(f"unexpected ff_out_bl dims: {fields['dims']}")
            result.append(metadata.with_suffix(".bin"))
    if len(result) != STATES:
        raise ValueError(f"expected {STATES} ff_out_bl tensors, got {len(result)}")
    return result


def run_tail_probe(
    executable: Path,
    pre_final: list[Path],
    export: Path,
    output: Path,
) -> list[str]:
    output.mkdir(parents=True)
    command = [
        str(executable),
        *[str(path) for path in pre_final],
        str(export / "00013.bin"),
        str(export / "00014.bin"),
        str(export / "00016.bin"),
        str(export / "00017.bin"),
        str(output),
    ]
    subprocess.run(command, check=True)
    return command


def torch_tail(
    pre_final: np.ndarray,
    weights: dict[str, torch.Tensor],
) -> tuple[np.ndarray, np.ndarray]:
    value = torch.tensor(pre_final, dtype=torch.float32)
    delta = torch.zeros(FEATURES, dtype=torch.float32, requires_grad=True)
    value = value + delta
    value = decoder_graph.libnc_rms_norm(
        value, weights["ln_g_2"], weights["ln_b_2"]
    )
    logits = F.linear(value, weights["embed_out"], weights["out_bias"])
    probabilities = torch.softmax(logits, dim=-1)
    target = torch.from_numpy(TARGETS)
    selected = probabilities[torch.arange(STATES), target]
    (-torch.log(selected).sum() / STATES).backward()
    if delta.grad is None:
        raise RuntimeError("PyTorch tail did not produce the shared gradient")
    return probabilities.detach().numpy(), delta.grad.detach().numpy()


def comparison(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    difference = candidate.astype(np.float64) - reference.astype(np.float64)
    reference_norm = float(np.linalg.norm(reference.astype(np.float64)))
    candidate_norm = float(np.linalg.norm(candidate.astype(np.float64)))
    signs = np.signbit(reference) != np.signbit(candidate)
    return {
        "elements": int(reference.size),
        "maximum_absolute_error": float(np.abs(difference).max()),
        "mean_absolute_error": float(np.abs(difference).mean()),
        "reference_l2_norm": reference_norm,
        "candidate_l2_norm": candidate_norm,
        "relative_l2_error": (
            float(np.linalg.norm(difference)) / reference_norm
            if reference_norm
            else None
        ),
        "sign_mismatches": int(signs.sum()),
        "reference_zero_count": int(np.count_nonzero(reference == 0)),
        "candidate_zero_count": int(np.count_nonzero(candidate == 0)),
    }


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
            "/home/x/enwiki9-nonproof/results/"
            "nncp_v33_online_update_parity_v1/run_07_bound"
        ),
    )
    parser.add_argument(
        "--initial-coefs",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "nncp_v33_relative_parity_v1/run_05/mini.coefs"
        ),
    )
    parser.add_argument(
        "--initial-export",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "nncp_v33_relative_parity_v1/run_05/export"
        ),
    )
    parser.add_argument(
        "--hook-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_internal_tensor_hook.c",
    )
    parser.add_argument(
        "--probe-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_tail_backward_composition_probe.c",
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
        args.bound_dir / "gradients/unknown_0006.bin",
        args.initial_coefs,
        args.initial_export / "manifest.json",
        args.hook_source,
        args.probe_source,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, bound receipt, or probe input")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-tail-") as temp:
        temporary = Path(temp)
        instrumented, hook, instrumented_build = compile_instrumented_nncp(
            libnc_root, args.hook_source.resolve(), temporary
        )
        probe, probe_build = compile_tail_probe(
            libnc_root, args.probe_source.resolve(), temporary
        )
        prefix = command_prefix(instrumented, args.initial_coefs.resolve())
        captures = [
            capture_run(
                label, temporary, instrumented, hook, prefix, args.bound_dir
            )
            for label in ("first", "second")
        ]
        archive_hashes = [internal.sha256(item["archive"]) for item in captures]
        trace_hashes = [internal.sha256(item["trace"]) for item in captures]
        dump_hashes = [internal.dump_sha256(item["dump"]) for item in captures]
        capture_identity = (
            archive_hashes
            == [internal.BOUND_ARCHIVE_SHA256, internal.BOUND_ARCHIVE_SHA256]
            and trace_hashes
            == [internal.BOUND_TRACE_SHA256, internal.BOUND_TRACE_SHA256]
            and dump_hashes[0] == dump_hashes[1]
            and captures[0]["archive"].read_bytes()
            == (args.bound_dir / "archive.bin").read_bytes()
            and captures[0]["trace"].read_bytes()
            == (args.bound_dir / "teacher.bin").read_bytes()
        )
        if not capture_identity:
            raise RuntimeError("instrumented source failed bound identity")

        tail_directories = [temporary / "tail_first", temporary / "tail_second"]
        tail_commands = [
            run_tail_probe(
                probe,
                ff_out_paths(capture["dump"]),
                args.initial_export,
                directory,
            )
            for capture, directory in zip(captures, tail_directories)
        ]
        tail_hashes = [aggregate_sha256(path) for path in tail_directories]
        tail_repeated = tail_hashes[0] == tail_hashes[1]
        if not tail_repeated:
            raise RuntimeError("direct LibNC tail did not repeat byte-identically")

        direct_probabilities = np.fromfile(
            tail_directories[0] / "probabilities.bin", dtype="<f4"
        ).reshape((CLASSES, 1, STATES), order="F")[:, 0, :].T
        direct_gradient = np.fromfile(
            tail_directories[0] / "tail_gradient.bin", dtype="<f4"
        )
        if direct_gradient.shape != (FEATURES,):
            raise RuntimeError("unexpected direct tail-gradient shape")
        symbols, distributions = base.load_trace(args.bound_dir / "teacher.bin")
        if symbols.tolist() != TARGETS.tolist():
            raise RuntimeError("bound symbols do not match the frozen tail targets")
        teacher_probabilities = np.stack(distributions)
        probability_comparison = comparison(
            teacher_probabilities, direct_probabilities
        )
        if probability_comparison["maximum_absolute_error"] > THRESHOLD:
            raise RuntimeError("direct tail probabilities failed teacher identity")

        pre_final = np.stack(
            [
                np.fromfile(path, dtype="<f4")
                for path in ff_out_paths(captures[0]["dump"])
            ]
        )
        if pre_final.shape != (STATES, FEATURES):
            raise RuntimeError("unexpected captured pre-final shape")
        weights, exported_types = base.load_export(args.initial_export)
        torch_probabilities, torch_gradient = torch_tail(pre_final, weights)
        bound_gradient = np.fromfile(
            args.bound_dir / "gradients/unknown_0006.bin", dtype="<f4"
        )
        if bound_gradient.shape != (FEATURES,):
            raise RuntimeError("unexpected bound ff_bias2-gradient shape")

        direct_vs_bound = comparison(bound_gradient, direct_gradient)
        torch_vs_bound = comparison(bound_gradient, torch_gradient)
        direct_vs_torch = comparison(direct_gradient, torch_gradient)
        torch_probability_comparison = comparison(
            teacher_probabilities, torch_probabilities
        )
        direct_matches_bound = (
            direct_vs_bound["maximum_absolute_error"] <= THRESHOLD
            and direct_vs_bound["sign_mismatches"] == 0
        )
        torch_matches_bound = (
            torch_vs_bound["maximum_absolute_error"] <= THRESHOLD
            and torch_vs_bound["sign_mismatches"] == 0
        )
        if direct_matches_bound and not torch_matches_bound:
            status = "TAIL_BACKWARD_LOCALIZED"
            promotion_authorized = True
            next_action = (
                "localize the composed LibNC tail reduction order without "
                "changing the proved forward trajectory"
            )
        elif direct_matches_bound:
            status = "FORWARD_ROUNDING_AMPLIFICATION"
            promotion_authorized = False
            next_action = (
                "retire a distinct tail-backward contract and quantify "
                "first-step sign sensitivity to source-bound forward rounding"
            )
        else:
            status = "TAIL_NOT_REPRODUCED"
            promotion_authorized = False
            next_action = (
                "reject the assumed ff_bias2 mapping or direct-tail graph; "
                "do not alter a forward primitive"
            )

        result = {
            "schema": "gamma.nncp_v33_libnc_tail_backward_composition.v1",
            "candidate_id": CANDIDATE_ID,
            "status": status,
            "score_credit_bytes": 0,
            "contract": {
                "features": FEATURES,
                "classes": CLASSES,
                "states": STATES,
                "targets": TARGETS.tolist(),
                "threshold": THRESHOLD,
                "tail": [
                    "shared zero delta",
                    "RMSNorm epsilon 1e-5",
                    "final gain and bias",
                    "256 by 32 output projection and bias",
                    "F32 conversion",
                    "per-state softmax",
                    "four-state concat optimization",
                    "indexed log and negative mean",
                ],
            },
            "inputs": {
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_header_sha256": internal.sha256(libnc_root / "libnc.h"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
                "hook_source_sha256": internal.sha256(args.hook_source),
                "probe_source_sha256": internal.sha256(args.probe_source),
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "internal_forward_tool_sha256": internal.sha256(
                    Path(internal.__file__).resolve()
                ),
                "decoder_graph_tool_sha256": internal.sha256(
                    Path(decoder_graph.__file__).resolve()
                ),
                "initial_coefs_sha256": internal.sha256(args.initial_coefs),
                "initial_manifest_sha256": internal.sha256(
                    args.initial_export / "manifest.json"
                ),
                "bound_input_sha256": internal.sha256(
                    args.bound_dir / "input.bin"
                ),
                "bound_ff_bias2_gradient_sha256": internal.sha256(
                    args.bound_dir / "gradients/unknown_0006.bin"
                ),
                "exported_parameter_types": exported_types,
            },
            "build": {
                "instrumented_nncp": instrumented_build,
                "tail_probe": probe_build,
            },
            "identity": {
                "capture_bound_identity": capture_identity,
                "bound_archive_sha256": internal.BOUND_ARCHIVE_SHA256,
                "run_archive_sha256": archive_hashes,
                "bound_trace_sha256": internal.BOUND_TRACE_SHA256,
                "run_trace_sha256": trace_hashes,
                "run_dump_sha256": dump_hashes,
                "dump_repeat_byte_identical": dump_hashes[0] == dump_hashes[1],
                "tail_run_sha256": tail_hashes,
                "tail_repeat_byte_identical": tail_repeated,
                "tail_commands": tail_commands,
                "direct_probability_vs_teacher": probability_comparison,
                "pytorch_probability_vs_teacher": torch_probability_comparison,
            },
            "gradient": {
                "bound_mapping": "unknown_0006.bin -> ff_bias2_0",
                "direct_libnc_vs_bound_ff_bias2": direct_vs_bound,
                "pytorch_tail_vs_bound_ff_bias2": torch_vs_bound,
                "direct_libnc_vs_pytorch_tail": direct_vs_torch,
                "direct_libnc_matches_bound": direct_matches_bound,
                "pytorch_tail_matches_bound": torch_matches_bound,
            },
            "decision": {
                "promotion_authorized": promotion_authorized,
                "authorized_next_action": next_action,
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
