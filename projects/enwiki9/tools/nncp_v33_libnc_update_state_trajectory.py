#!/usr/bin/env python3
"""Localize the first evolving-state divergence in the LibNC NNCP replay."""

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
import nncp_v33_libnc_concat_rmsnorm_backward_contract as analytic
import nncp_v33_libnc_concat_rmsnorm_multiupdate_parity as multi
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_tanh_gelu_online_update_parity as gelu_replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_update_state_trajectory_v1"
BYTES = 32
SEGMENT = 4
UPDATES = BYTES // SEGMENT
PARAMETER_TOLERANCE = 2e-5
MEMORY_TOLERANCE = 2e-6
PROBABILITY_TOLERANCE = 2e-5


CAPTURE_HELPER = r'''
static unsigned gamma_update_state_step;

static void gamma_dump_update_state(TransformerModel *s)
{
    const char *directory = getenv("NNCP_UPDATE_STATE_DIR");
    char filename[4096];
    FILE *file;
    int layer_idx;

    if (!directory || !directory[0])
        return;
    snprintf(filename, sizeof(filename), "%s/step_%02u.coefs",
             directory, gamma_update_state_step);
    nc_save_coefs(&s->param_list, filename);

    snprintf(filename, sizeof(filename), "%s/step_%02u.memory",
             directory, gamma_update_state_step);
    file = fopen(filename, "wb");
    if (!file) {
        perror("NNCP_UPDATE_STATE_DIR memory");
        abort();
    }
    nc_save_param_header(file, "gamma.nncp_v33_update_state.v1");
    for (layer_idx = 0; layer_idx < s->n_layer; layer_idx++) {
        char name[64];
        snprintf(name, sizeof(name), "mem_h_%d", layer_idx);
        nc_save_param(file, s->mem_h[layer_idx], name);
        snprintf(name, sizeof(name), "train_h_%d", layer_idx);
        nc_save_param(file, s->train_h[layer_idx], name);
    }
    if (fclose(file)) {
        perror("NNCP_UPDATE_STATE_DIR close");
        abort();
    }
    gamma_update_state_step++;
}

'''


def patch_source(source: str) -> str:
    declaration_marker = "/* update with coefficients */\nstatic void trf_update"
    if source.count(declaration_marker) != 1:
        raise ValueError("unexpected LibNC update declaration marker count")
    source = source.replace(
        declaration_marker,
        CAPTURE_HELPER + declaration_marker,
        1,
    )
    call_marker = "    /* shift the memory */\n    mem_update(s);\n    \n    prof_end(PROF_UPDATE);"
    if source.count(call_marker) != 1:
        raise ValueError("unexpected LibNC update call marker count")
    return source.replace(
        call_marker,
        "    /* shift the memory */\n"
        "    mem_update(s);\n"
        "    gamma_dump_update_state(s);\n"
        "    \n"
        "    prof_end(PROF_UPDATE);",
        1,
    )


def compile_native(
    libnc_root: Path, exporter_source: Path, temporary: Path
) -> tuple[Path, Path, dict[str, object]]:
    compiler = os.environ.get("CC", "cc")
    patched_source = temporary / "nncp_update_state.c"
    patched_source.write_text(patch_source((libnc_root / "nncp.c").read_text()))
    nncp_object = temporary / "nncp_update_state.o"
    executable = temporary / "nncp_update_state"
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
        str(patched_source),
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
    return executable, exporter, {
        "commands": commands,
        "stderrs": stderrs,
        "upstream_source_sha256": internal.sha256(libnc_root / "nncp.c"),
        "patched_source_sha256": internal.sha256(patched_source),
        "executable_sha256": internal.sha256(executable),
        "exporter_sha256": internal.sha256(exporter),
    }


def native_run(
    label: str,
    temporary: Path,
    command_prefix: list[str],
    input_path: Path,
) -> dict[str, object]:
    directory = temporary / label
    state_directory = directory / "states"
    directory.mkdir()
    state_directory.mkdir()
    archive = directory / "archive.bin"
    trace = directory / "teacher.bin"
    environment = dict(os.environ)
    environment["NNCP_TEACHER_TRACE"] = str(trace)
    environment["NNCP_UPDATE_STATE_DIR"] = str(state_directory)
    command = [*command_prefix, "c", str(input_path), str(archive)]
    completed = subprocess.run(
        command, check=True, capture_output=True, text=True, env=environment
    )
    coefs = [state_directory / f"step_{step:02d}.coefs" for step in range(UPDATES)]
    memories = [state_directory / f"step_{step:02d}.memory" for step in range(UPDATES)]
    if not archive.is_file() or not trace.is_file() or not all(
        path.is_file() for path in (*coefs, *memories)
    ):
        raise RuntimeError("native update-state capture is incomplete")
    return {
        "archive": archive,
        "trace": trace,
        "coefs": coefs,
        "memories": memories,
        "command": command,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }


def export_file(exporter: Path, source: Path, output: Path) -> dict[str, torch.Tensor]:
    subprocess.run(
        [str(exporter), str(source), str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    tensors, _ = base.load_export(output)
    return tensors


def canonical_memory(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.ndim != 3 or tensor.shape[1] != 1:
        raise ValueError(f"unexpected LibNC memory shape {tuple(tensor.shape)}")
    return tensor[:, 0, :].T.contiguous()


def analytic_trajectory(
    initial: dict[str, torch.Tensor],
    symbols: np.ndarray,
    learning_rate: float,
    gradient_clip: float,
) -> tuple[torch.Tensor, list[dict[str, torch.Tensor]], list[torch.Tensor]]:
    parameters = {
        name: torch.nn.Parameter(value.detach().clone())
        for name, value in initial.items()
    }
    first_moments = {name: torch.zeros_like(value) for name, value in parameters.items()}
    second_moments = {name: torch.zeros_like(value) for name, value in parameters.items()}
    beta1 = 0.0
    beta2 = 0.9999
    epsilon = 1e-8
    memory = torch.zeros(SEGMENT, 32, dtype=torch.float32)
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    forward = analytic.make_analytic_forward()
    probabilities: list[torch.Tensor] = []
    parameter_states: list[dict[str, torch.Tensor]] = []
    memory_states: list[torch.Tensor] = []

    for start in range(0, len(symbols), SEGMENT):
        token = torch.from_numpy(inputs[start : start + SEGMENT])
        target = torch.from_numpy(symbols[start : start + SEGMENT])
        for parameter in parameters.values():
            parameter.grad = None
        logits, next_memory = forward(
            parameters, token, memory, SEGMENT, SEGMENT, 2, 8, 8
        )
        probabilities.append(torch.softmax(logits.detach(), dim=-1))
        loss = F.cross_entropy(logits, target, reduction="mean")
        loss.backward()
        for parameter in parameters.values():
            if parameter.grad is None:
                continue
            norm = torch.linalg.vector_norm(parameter.grad)
            if norm > gradient_clip:
                parameter.grad.mul_(gradient_clip / norm)
        step = start // SEGMENT + 1
        beta1_correction = 1.0 - beta1**step
        beta2_correction = 1.0 - beta2**step
        epsilon_squared = (epsilon * beta2_correction**0.5) ** 2
        step_size = learning_rate * beta2_correction**0.5 / beta1_correction
        with torch.no_grad():
            for name, parameter in parameters.items():
                gradient = parameter.grad
                if gradient is None:
                    continue
                first_moments[name].mul_(beta1).add_(gradient, alpha=1.0 - beta1)
                second_moments[name].mul_(beta2).addcmul_(
                    gradient, gradient, value=1.0 - beta2
                )
                denominator = torch.sqrt(second_moments[name] + epsilon_squared)
                parameter.addcdiv_(first_moments[name], denominator, value=-step_size)
        memory = next_memory.detach()
        parameter_states.append(
            {name: value.detach().clone() for name, value in parameters.items()}
        )
        memory_states.append(memory.clone())
    return torch.cat(probabilities), parameter_states, memory_states


def tensor_map_hash(values: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(values):
        digest.update(name.encode())
        digest.update(values[name].detach().numpy().astype("<f4").tobytes())
    return digest.hexdigest()


def tensor_hash(value: torch.Tensor) -> str:
    return hashlib.sha256(
        value.detach().numpy().astype("<f4").tobytes()
    ).hexdigest()


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
        "--parent-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_libnc_concat_rmsnorm_multiupdate_parity_v1/decision.json",
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
    required = (
        libnc_root / "nncp.c",
        libnc_root / "libnc.so",
        args.raw_input,
        args.initial_export / "manifest.json",
        args.exporter_source,
        args.parent_decision,
    )
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, corpus, export, or parent receipt")
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an update-state decision")
    parent = json.loads(args.parent_decision.read_text())
    if parent.get("status") != "REJECT":
        raise ValueError("unexpected parent multi-update status")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-update-state-") as temp:
        temporary = Path(temp)
        input_path = temporary / "enwik9.prefix32"
        with args.raw_input.open("rb") as source:
            input_bytes = source.read(BYTES)
        input_path.write_bytes(input_bytes)
        executable, exporter, build = compile_native(
            libnc_root, args.exporter_source.resolve(), temporary
        )
        prefix = multi.command_prefix(executable, Path("unused.initial.coefs"))
        runs = [
            native_run(label, temporary, prefix, input_path)
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
        source_repeat = (
            archive_hashes[0] == archive_hashes[1]
            and trace_hashes[0] == trace_hashes[1]
            and coefs_hashes[0] == coefs_hashes[1]
            and memory_hashes[0] == memory_hashes[1]
        )
        parent_archive_hash = parent["native_proof"]["archive_sha256"][0]
        parent_trace_hash = parent["native_proof"]["trace_sha256"][0]
        observation_neutral = (
            archive_hashes[0] == parent_archive_hash
            and trace_hashes[0] == parent_trace_hash
        )
        if not source_repeat or not observation_neutral:
            raise RuntimeError("source captures changed or failed to repeat archive/P1")

        source_parameters: list[dict[str, torch.Tensor]] = []
        source_memories: list[torch.Tensor] = []
        source_train_states: list[torch.Tensor] = []
        for step in range(UPDATES):
            parameters = export_file(
                exporter,
                runs[0]["coefs"][step],
                temporary / f"source_step_{step:02d}_coefs",
            )
            memories = export_file(
                exporter,
                runs[0]["memories"][step],
                temporary / f"source_step_{step:02d}_memory",
            )
            source_parameters.append(parameters)
            source_memories.append(canonical_memory(memories["mem_h_0"]))
            source_train_states.append(canonical_memory(memories["train_h_0"]))

        symbols, distributions = base.load_trace(runs[0]["trace"])
        if len(symbols) != BYTES or not np.array_equal(
            symbols, np.frombuffer(input_bytes, dtype=np.uint8).astype(np.int64)
        ):
            raise RuntimeError("native trace symbols do not bind the raw prefix")
        teacher_probabilities = torch.from_numpy(np.stack(distributions))
        initial, _ = base.load_export(args.initial_export)
        analytic_runs = [
            analytic_trajectory(
                initial, symbols, args.learning_rate, args.gradient_clip
            )
            for _ in range(2)
        ]
        first_probabilities, first_parameters, first_memories = analytic_runs[0]
        second_probabilities, second_parameters, second_memories = analytic_runs[1]
        analytic_repeat = (
            torch.equal(first_probabilities, second_probabilities)
            and [tensor_map_hash(values) for values in first_parameters]
            == [tensor_map_hash(values) for values in second_parameters]
            and [tensor_hash(value) for value in first_memories]
            == [tensor_hash(value) for value in second_memories]
        )

        probability_error = (first_probabilities - teacher_probabilities).abs()
        segment_probability_errors = [
            float(probability_error[start : start + SEGMENT].max())
            for start in range(0, BYTES, SEGMENT)
        ]
        step_rows: list[dict[str, object]] = []
        for step in range(UPDATES):
            names = sorted(set(source_parameters[step]) & set(first_parameters[step]))
            parameter_errors = {
                name: float(
                    (source_parameters[step][name] - first_parameters[step][name])
                    .abs()
                    .max()
                )
                for name in names
            }
            source_memory = source_memories[step]
            analytic_memory = first_memories[step]
            memory_error = float((source_memory - analytic_memory).abs().max())
            train_error = float(
                (source_train_states[step] - analytic_memory).abs().max()
            )
            step_rows.append(
                {
                    "step": step + 1,
                    "parameter_maximum_absolute_error": max(parameter_errors.values()),
                    "parameter_maximum_errors": parameter_errors,
                    "memory_maximum_absolute_error": memory_error,
                    "train_h_maximum_absolute_error": train_error,
                    "source_parameter_sha256": tensor_map_hash(source_parameters[step]),
                    "analytic_parameter_sha256": tensor_map_hash(first_parameters[step]),
                    "source_memory_sha256": tensor_hash(source_memory),
                    "analytic_memory_sha256": tensor_hash(analytic_memory),
                    "source_train_h_sha256": tensor_hash(source_train_states[step]),
                }
            )

        first_parameter_divergence = next(
            (
                row["step"]
                for row in step_rows
                if row["parameter_maximum_absolute_error"] > PARAMETER_TOLERANCE
            ),
            None,
        )
        first_memory_divergence = next(
            (
                row["step"]
                for row in step_rows
                if row["memory_maximum_absolute_error"] > MEMORY_TOLERANCE
                or row["train_h_maximum_absolute_error"] > MEMORY_TOLERANCE
            ),
            None,
        )
        first_probability_divergence = next(
            (
                index + 1
                for index, value in enumerate(segment_probability_errors)
                if value > PROBABILITY_TOLERANCE
            ),
            None,
        )
        if first_parameter_divergence == 1:
            localization = "parameter_update"
        elif first_memory_divergence == 1:
            localization = "persistent_memory"
        elif (
            first_probability_divergence is not None
            and first_probability_divergence > 1
            and first_parameter_divergence != 1
            and first_memory_divergence != 1
        ):
            localization = "evolving_state_forward_operation"
        else:
            localization = "ambiguous"
        localized = localization != "ambiguous"

        result = {
            "schema": "gamma.nncp_v33_libnc_update_state_trajectory.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "STATE_DIVERGENCE_LOCALIZED" if localized else "REJECT",
            "score_credit_bytes": 0,
            "provenance_correction": {
                "prior_artifact_label": "final_coefs",
                "actual_capture_boundary": "nc_param_list_end before first evaluation",
                "prior_final_parameter_comparison_valid": False,
                "prior_probability_trajectory_comparison_valid": True,
            },
            "contract": {
                "raw_bytes": BYTES,
                "segment": SEGMENT,
                "updates": UPDATES,
                "parameter_tolerance": PARAMETER_TOLERANCE,
                "memory_tolerance": MEMORY_TOLERANCE,
                "probability_tolerance": PROBABILITY_TOLERANCE,
                "learning_rate": args.learning_rate,
                "gradient_clip": args.gradient_clip,
                "captured_state_used_as_replay_input": False,
            },
            "inputs": {
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "raw_corpus_sha256": internal.sha256(args.raw_input),
                "raw_prefix_sha256": hashlib.sha256(input_bytes).hexdigest(),
                "initial_manifest_sha256": internal.sha256(
                    args.initial_export / "manifest.json"
                ),
                "parent_decision_sha256": internal.sha256(args.parent_decision),
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
                "source_repeat_byte_identical": source_repeat,
                "observation_neutral_archive_and_trace": observation_neutral,
            },
            "analytic_proof": {
                "repeat_byte_identical": analytic_repeat,
                "segment_maximum_probability_errors": segment_probability_errors,
                "steps": step_rows,
            },
            "localization": {
                "first_parameter_divergence_step": first_parameter_divergence,
                "first_memory_divergence_step": first_memory_divergence,
                "first_probability_divergence_segment": first_probability_divergence,
                "boundary": localization,
                "unique": localized,
            },
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": (
                    f"freeze one {localization} component-level parity child"
                    if localized
                    else "retire this update-state localization realization"
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
