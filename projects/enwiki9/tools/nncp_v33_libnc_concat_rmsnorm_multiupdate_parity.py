#!/usr/bin/env python3
"""Validate the analytic LibNC concat-RMSNorm rule across eight updates."""

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

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_concat_rmsnorm_backward_contract as analytic
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_tail_backward_composition as tail
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_concat_rmsnorm_multiupdate_parity_v1"
BYTES = 32
SEGMENT = 4
UPDATES = BYTES // SEGMENT
TOLERANCE = 2e-5


def compile_native(
    libnc_root: Path,
    save_hook_source: Path,
    exporter_source: Path,
    temporary: Path,
) -> tuple[Path, Path, Path, dict[str, object]]:
    compiler = os.environ.get("CC", "cc")
    nncp_object = temporary / "nncp_multiupdate.o"
    executable = temporary / "nncp_multiupdate"
    save_hook = temporary / "libnncp_save_hook.so"
    exporter = temporary / "nncp_libnc_export"
    commands: list[list[str]] = []
    stderrs: list[str] = []
    command = [
        compiler,
        "-O3",
        "-Wall",
        "-Wpointer-arith",
        "-g",
        "-fno-math-errno",
        "-fno-trapping-math",
        '-DCONFIG_VERSION="2024-06-05"',
        "-DLIBNC_CONFIG_FULL",
        f"-I{libnc_root}",
        "-c",
        str(libnc_root / "nncp.c"),
        "-o",
        str(nncp_object),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    commands.append(command)
    stderrs.append(completed.stderr)

    command = [
        compiler,
        f"-Wl,-rpath,{libnc_root}",
        "-o",
        str(executable),
        str(nncp_object),
        *[
            str(libnc_root / name)
            for name in ("cmdopt.o", "cp_utils.o", "arith.o", "preprocess.o", "cutils.o")
        ],
        str(libnc_root / "libnc.so"),
        "-lz",
        "-lm",
        "-lpthread",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    commands.append(command)
    stderrs.append(completed.stderr)

    command = [
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
        str(save_hook_source),
        f"-L{libnc_root}",
        f"-Wl,-rpath,{libnc_root}",
        "-lnc",
        "-ldl",
        "-o",
        str(save_hook),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    commands.append(command)
    stderrs.append(completed.stderr)

    command = [
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
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    commands.append(command)
    stderrs.append(completed.stderr)
    return executable, save_hook, exporter, {
        "commands": commands,
        "stderrs": stderrs,
        "upstream_source_sha256": internal.sha256(libnc_root / "nncp.c"),
        "upstream_coefficient_load_calls_disabled": True,
        "executable_sha256": internal.sha256(executable),
        "save_hook_sha256": internal.sha256(save_hook),
        "exporter_sha256": internal.sha256(exporter),
    }


def command_prefix(executable: Path, initial_coefs: Path) -> list[str]:
    prefix = tail.command_prefix(executable, initial_coefs)
    index = prefix.index("--max_size") + 1
    if prefix[index] != "4":
        raise ValueError("unexpected inherited maximum-size contract")
    prefix[index] = str(BYTES)
    load_index = prefix.index("--load_coefs")
    if Path(prefix[load_index + 1]) != initial_coefs:
        raise ValueError("unexpected inherited coefficient path")
    del prefix[load_index : load_index + 2]
    return prefix


def native_run(
    label: str,
    temporary: Path,
    prefix: list[str],
    save_hook: Path,
    input_path: Path,
) -> dict[str, object]:
    directory = temporary / label
    directory.mkdir()
    archive = directory / "archive.bin"
    trace = directory / "teacher.bin"
    final_coefs = directory / "final.coefs"
    environment = dict(os.environ)
    environment["LD_PRELOAD"] = str(save_hook)
    environment["NNCP_TEACHER_TRACE"] = str(trace)
    environment["NNCP_SAVE_COEFS"] = str(final_coefs)
    command = [*prefix, "c", str(input_path), str(archive)]
    completed = subprocess.run(
        command, check=True, capture_output=True, text=True, env=environment
    )
    if not all(path.is_file() for path in (archive, trace, final_coefs)):
        raise RuntimeError("native run omitted archive, trace, or final coefs")
    return {
        "directory": directory,
        "archive": archive,
        "trace": trace,
        "final_coefs": final_coefs,
        "command": command,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }


def export_coefs(exporter: Path, coefs: Path, output: Path) -> None:
    subprocess.run(
        [str(exporter), str(coefs), str(output)],
        check=True,
        capture_output=True,
        text=True,
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
        "--save-hook-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_save_hook.c",
    )
    parser.add_argument(
        "--exporter-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_export.c",
    )
    parser.add_argument(
        "--analytic-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_concat_rmsnorm_backward_contract_v1/decision.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    parser.add_argument("--learning-rate", type=float, default=0.00016)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    args = parser.parse_args()

    libnc_root = args.libnc_root.resolve()
    required = [
        libnc_root / "nncp.c",
        libnc_root / "libnc.h",
        libnc_root / "libnc.so",
        args.raw_input,
        args.initial_coefs,
        args.initial_export / "manifest.json",
        args.save_hook_source,
        args.exporter_source,
        args.analytic_decision,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing source, corpus, coefficients, or parent decision")
    parent = json.loads(args.analytic_decision.read_text())
    if parent.get("status") != "PASS":
        raise ValueError("analytic backward contract did not authorize this gate")
    if args.raw_input.stat().st_size < BYTES:
        raise ValueError("raw input is shorter than the frozen population")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-multiupdate-") as temp:
        temporary = Path(temp)
        input_path = temporary / "enwik9.prefix32"
        with args.raw_input.open("rb") as source:
            input_bytes = source.read(BYTES)
        if len(input_bytes) != BYTES:
            raise RuntimeError("failed to read the frozen raw prefix")
        input_path.write_bytes(input_bytes)
        executable, save_hook, exporter, build = compile_native(
            libnc_root,
            args.save_hook_source.resolve(),
            args.exporter_source.resolve(),
            temporary,
        )
        prefix = command_prefix(executable, args.initial_coefs.resolve())
        native_runs = [
            native_run(label, temporary, prefix, save_hook, input_path)
            for label in ("first", "second")
        ]
        archive_hashes = [internal.sha256(run["archive"]) for run in native_runs]
        trace_hashes = [internal.sha256(run["trace"]) for run in native_runs]
        coefs_hashes = [internal.sha256(run["final_coefs"]) for run in native_runs]
        native_repeat = (
            archive_hashes[0] == archive_hashes[1]
            and trace_hashes[0] == trace_hashes[1]
            and coefs_hashes[0] == coefs_hashes[1]
        )
        if not native_repeat:
            raise RuntimeError("native archive, trace, or final coefs did not repeat")

        restored = temporary / "restored.bin"
        decode_command = [
            *prefix,
            "d",
            str(native_runs[0]["archive"]),
            str(restored),
        ]
        decode_trace = temporary / "decode_teacher.bin"
        decode_environment = dict(os.environ)
        decode_environment["NNCP_TEACHER_TRACE"] = str(decode_trace)
        decoded = subprocess.run(
            decode_command,
            check=False,
            capture_output=True,
            text=True,
            env=decode_environment,
        )
        restored_bytes = restored.read_bytes() if restored.is_file() else b""
        roundtrip = decoded.returncode == 0 and restored_bytes == input_bytes
        mismatch_limit = min(len(input_bytes), len(restored_bytes))
        first_mismatch = next(
            (
                index
                for index in range(mismatch_limit)
                if input_bytes[index] != restored_bytes[index]
            ),
            None,
        )
        if first_mismatch is None and len(input_bytes) != len(restored_bytes):
            first_mismatch = mismatch_limit

        export_directories: list[Path] = []
        for index, run in enumerate(native_runs):
            output = temporary / f"final_export_{index}"
            export_coefs(exporter, run["final_coefs"], output)
            export_directories.append(output)
        export_hashes = [internal.dump_sha256(path) for path in export_directories]
        export_repeat = export_hashes[0] == export_hashes[1]
        if not export_repeat:
            raise RuntimeError("native final tensor exports did not repeat")

        symbols, distributions = base.load_trace(native_runs[0]["trace"])
        if len(symbols) != BYTES or not np.array_equal(
            symbols, np.frombuffer(input_bytes, dtype=np.uint8).astype(np.int64)
        ):
            raise RuntimeError("native trace symbols do not match raw prefix")
        teacher_probabilities = torch.from_numpy(np.stack(distributions))
        teacher_final, _ = base.load_export(export_directories[0])
        initial, exported_types = base.load_export(args.initial_export)
        analytic_runs = [
            analytic.analytic_update_run(
                initial, symbols, args.learning_rate, args.gradient_clip
            )
            for _ in range(2)
        ]
        first_probabilities, first_final, first_losses = analytic_runs[0]
        second_probabilities, second_final, second_losses = analytic_runs[1]
        probability_error = (first_probabilities - teacher_probabilities).abs()
        final_errors = {
            name: float((first_final[name] - teacher_final[name]).abs().max())
            for name in sorted(teacher_final)
        }
        maximum_final_error = max(final_errors.values())
        first_final_hash = gelu_replay.final_hash(first_final)
        second_final_hash = gelu_replay.final_hash(second_final)
        analytic_repeat = (
            first_final_hash == second_final_hash
            and torch.equal(first_probabilities, second_probabilities)
            and first_losses == second_losses
        )
        segment_probability_errors = [
            float(probability_error[start : start + SEGMENT].max())
            for start in range(0, BYTES, SEGMENT)
        ]
        passed = (
            native_repeat
            and export_repeat
            and roundtrip
            and float(probability_error.max()) <= TOLERANCE
            and maximum_final_error <= TOLERANCE
            and analytic_repeat
        )
        result = {
            "schema": "gamma.nncp_v33_libnc_concat_rmsnorm_multiupdate_parity.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "PASS" if passed else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "raw_bytes": BYTES,
                "segment": SEGMENT,
                "updates": UPDATES,
                "population": "raw_enwik9_prefix_0_32",
                "learning_rate": args.learning_rate,
                "gradient_clip": args.gradient_clip,
                "tolerance": TOLERANCE,
                "backward_formula": parent["contract"]["formula"],
                "captured_adjoint_used": False,
                "native_model_initialization": "upstream_deterministic_seed",
                "analytic_initialization": "source_bound_seed_export",
                "exported_parameter_types": exported_types,
            },
            "inputs": {
                "raw_corpus_sha256": internal.sha256(args.raw_input),
                "raw_prefix_sha256": hashlib.sha256(input_bytes).hexdigest(),
                "initial_coefs_sha256": internal.sha256(args.initial_coefs),
                "initial_manifest_sha256": internal.sha256(
                    args.initial_export / "manifest.json"
                ),
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
                "analytic_decision_sha256": internal.sha256(
                    args.analytic_decision
                ),
                "script_sha256": internal.sha256(Path(__file__).resolve()),
            },
            "build": build,
            "native_proof": {
                "command": native_runs[0]["command"],
                "decode_command": decode_command,
                "archive_sha256": archive_hashes,
                "trace_sha256": trace_hashes,
                "final_coefs_sha256": coefs_hashes,
                "final_export_sha256": export_hashes,
                "archive_bytes": native_runs[0]["archive"].stat().st_size,
                "native_repeat_byte_identical": native_repeat,
                "export_repeat_byte_identical": export_repeat,
                "roundtrip_ok": roundtrip,
                "decode_returncode": decoded.returncode,
                "decode_trace_sha256": (
                    internal.sha256(decode_trace) if decode_trace.is_file() else None
                ),
                "restored_bytes": len(restored_bytes),
                "first_roundtrip_mismatch": first_mismatch,
                "restored_prefix_hex": restored_bytes[:BYTES].hex(),
                "decode_stdout_sha256": hashlib.sha256(
                    decoded.stdout.encode()
                ).hexdigest(),
                "decode_stderr_sha256": hashlib.sha256(
                    decoded.stderr.encode()
                ).hexdigest(),
            },
            "analytic_proof": {
                "maximum_absolute_probability_error": float(
                    probability_error.max()
                ),
                "mean_absolute_probability_error": float(
                    probability_error.mean()
                ),
                "segment_maximum_probability_errors": segment_probability_errors,
                "maximum_absolute_parameter_error": maximum_final_error,
                "parameter_maximum_errors": final_errors,
                "segment_losses": first_losses,
                "first_final_tensor_sha256": first_final_hash,
                "second_final_tensor_sha256": second_final_hash,
                "repeat_byte_identical": analytic_repeat,
            },
            "decision": {
                "promotion_authorized": passed,
                "authorized_next_action": (
                    "run the smallest faithful-profile constructive prefix gate"
                    if passed
                    else "retire analytic concat-RMSNorm as a multi-update parity solution"
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
