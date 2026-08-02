#!/usr/bin/env python3
"""Capture and compose the source-bound LibNC FF2 output adjoint."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import torch

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_named_gradient_trajectory as named
import nncp_v33_libnc_tail_backward_composition as tail


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_ff2_output_adjoint_trajectory_v1"
THRESHOLD = 2e-6
STATES = 4
LAYER = 0

DECLARATIONS = """void nncp_named_gradient_set_param_list(NCParamList *parameters);
void nncp_named_gradient_dump(void *parameter_opaque, NCTensor *gradient);
void nncp_ff2_input_dump(NCTensor *value, int layer, int state);
NCTensor *nncp_ff2_probe_attach(NCTensor *value, int layer, int state);
int nncp_ff2_probe_capture(void *opaque, NCTensor *gradient,
                           NCTensor *column_index);

"""


def patch_source(source: str) -> str:
    declaration_marker = "static NCTensor *layer_norm("
    callback_marker = (
        "static void backward_cb(void *opaque, NCTensor *yg, "
        "NCTensor *get_col_index)"
    )
    update_marker = "    sgd_opt_update_var(opaque, yg, get_col_index);"
    backward_marker = (
        "    nc_backward(loss, nc_new_f32(s->common.device, 1.0), backward_cb,\n"
    )
    ff2_marker = "        t0 = nc_matmul(nc_dup_tensor(tl->ff2), t0);"
    bias_marker = (
        "        if (tl->ff_bias2)\n"
        "            t0 = nc_add(t0, nc_dup_tensor(tl->ff_bias2));"
    )
    for marker in (
        declaration_marker,
        callback_marker,
        update_marker,
        backward_marker,
        ff2_marker,
        bias_marker,
    ):
        if source.count(marker) != 1:
            raise ValueError(f"source patch marker count is not one: {marker!r}")
    source = source.replace(
        declaration_marker, DECLARATIONS + declaration_marker
    )
    source = source.replace(
        update_marker,
        "    if (nncp_ff2_probe_capture(opaque, yg, get_col_index))\n"
        "        return;\n"
        "    nncp_named_gradient_dump(opaque, yg);\n"
        + update_marker,
    )
    source = source.replace(
        backward_marker,
        "    nncp_named_gradient_set_param_list(&s->param_list);\n"
        + backward_marker,
    )
    source = source.replace(
        ff2_marker,
        "        nncp_ff2_input_dump(t0, layer_idx, output_index);\n"
        + ff2_marker,
    )
    source = source.replace(
        bias_marker,
        bias_marker
        + "\n        t0 = nncp_ff2_probe_attach(t0, layer_idx, output_index);",
    )
    return source


def compile_instrumented(
    libnc_root: Path,
    named_helper: Path,
    adjoint_helper: Path,
    temporary: Path,
) -> tuple[Path, dict[str, object]]:
    patched_source = temporary / "nncp_ff2_adjoint.c"
    patched_source.write_text(patch_source((libnc_root / "nncp.c").read_text()))
    objects: list[Path] = []
    commands: list[list[str]] = []
    stderrs: list[str] = []
    compiler = os.environ.get("CC", "cc")
    nncp_object = temporary / "nncp_ff2_adjoint.o"
    nncp_command = [
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
    completed = subprocess.run(
        nncp_command, check=True, capture_output=True, text=True
    )
    commands.append(nncp_command)
    stderrs.append(completed.stderr)
    objects.append(nncp_object)
    for label, helper in (("named", named_helper), ("adjoint", adjoint_helper)):
        output = temporary / f"{label}.o"
        command = [
            compiler,
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            f"-I{libnc_root}",
            "-c",
            str(helper),
            "-o",
            str(output),
        ]
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        commands.append(command)
        stderrs.append(completed.stderr)
        objects.append(output)
    executable = temporary / "nncp_ff2_adjoint"
    link_command = [
        compiler,
        f"-Wl,-rpath,{libnc_root}",
        "-o",
        str(executable),
        *map(str, objects),
        *[
            str(libnc_root / name)
            for name in ("cmdopt.o", "cp_utils.o", "arith.o", "preprocess.o", "cutils.o")
        ],
        str(libnc_root / "libnc.so"),
        "-lz",
        "-lm",
        "-lpthread",
    ]
    completed = subprocess.run(
        link_command, check=True, capture_output=True, text=True
    )
    return executable, {
        "patched_source_sha256": internal.sha256(patched_source),
        "compile_commands": commands,
        "compile_stderr": stderrs,
        "link_command": link_command,
        "link_stderr": completed.stderr,
        "executable_sha256": internal.sha256(executable),
    }


def run_capture(
    label: str,
    temporary: Path,
    executable: Path,
    prefix: list[str],
    bound_dir: Path,
) -> dict[str, Path]:
    run_dir = temporary / label
    gradients = run_dir / "gradients"
    probes = run_dir / "probes"
    gradients.mkdir(parents=True)
    probes.mkdir()
    archive = run_dir / "archive.bin"
    trace = run_dir / "teacher.bin"
    environment = dict(os.environ)
    environment["NNCP_TEACHER_TRACE"] = str(trace)
    environment["NNCP_NAMED_GRADIENT_DIR"] = str(gradients)
    environment["NNCP_FF2_ADJOINT_DIR"] = str(probes)
    command = [
        *prefix,
        "c",
        str(bound_dir / "input.bin"),
        str(archive),
    ]
    completed = subprocess.run(
        command, check=True, capture_output=True, text=True, env=environment
    )
    (run_dir / "stdout.log").write_text(completed.stdout)
    (run_dir / "stderr.log").write_text(completed.stderr)
    return {"archive": archive, "trace": trace, "gradients": gradients, "probes": probes}


def directory_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_file():
            digest.update(path.name.encode("utf-8") + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def read_probe(directory: Path, kind: str) -> np.ndarray:
    columns: list[np.ndarray] = []
    for state in range(STATES):
        stem = f"{kind}_l{LAYER:02d}_s{state:03d}"
        metadata = directory / f"{stem}.meta"
        data_path = directory / f"{stem}.bin"
        if not metadata.is_file() or not data_path.is_file():
            raise RuntimeError(f"missing probe artifact {stem}")
        fields = dict(
            line.split("=", 1) for line in metadata.read_text().splitlines()
        )
        dimensions = tuple(int(value) for value in fields["dims"].split(","))
        values = np.fromfile(data_path, dtype="<f4").reshape(dimensions, order="F")
        columns.append(values.reshape(-1, 1, order="F"))
    expected_files = STATES * 2
    if len(
        [
            path
            for path in directory.iterdir()
            if path.is_file() and path.name.startswith(f"{kind}_")
        ]
    ) != expected_files:
        raise RuntimeError(f"unexpected {kind} probe artifact count")
    return np.concatenate(columns, axis=1)


def pytorch_run_with_adjoint(
    export: Path, trace: Path
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray]:
    loaded, _ = base.load_export(export)
    weights = {
        name: value.detach().clone().requires_grad_(True)
        for name, value in loaded.items()
    }
    symbols, _ = base.load_trace(trace)
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    token = torch.from_numpy(inputs)
    memory = torch.zeros(4, 32, dtype=torch.float32)
    outputs: list[torch.Tensor] = []
    hidden_inputs: list[torch.Tensor] = []
    original_linear = decoder_graph.F.linear

    def capture_linear(
        input_value: torch.Tensor,
        weight: torch.Tensor,
        bias: torch.Tensor | None = None,
    ) -> torch.Tensor:
        output = original_linear(input_value, weight, bias)
        if weight is weights["ff2_0"]:
            output.retain_grad()
            outputs.append(output)
            hidden_inputs.append(input_value)
        return output

    decoder_graph.F.linear = capture_linear
    try:
        logits, _ = decoder_graph.decoder_graph_segment(
            weights, token, memory, 4, 4, 2, 8, 8
        )
    finally:
        decoder_graph.F.linear = original_linear
    target = torch.from_numpy(symbols)
    loss = torch.nn.functional.cross_entropy(logits, target, reduction="mean")
    loss.backward()
    if len(outputs) != STATES or any(value.grad is None for value in outputs):
        raise RuntimeError("PyTorch FF2 adjoint capture is incomplete")
    gradients = {
        name: value.grad.detach().numpy().copy()
        for name, value in weights.items()
        if value.grad is not None
    }
    adjoint = np.concatenate(
        [value.grad.detach().numpy().T.copy() for value in outputs], axis=1
    )
    hidden = np.concatenate(
        [value.detach().numpy().T.copy() for value in hidden_inputs], axis=1
    )
    probabilities = torch.softmax(logits, dim=-1).detach().numpy()
    return probabilities, gradients, adjoint, hidden


def matches(metrics: dict[str, object]) -> bool:
    return (
        metrics["maximum_absolute_error"] <= THRESHOLD
        and metrics["sign_mismatches"] == 0
    )


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
        "--named-helper",
        type=Path,
        default=ROOT / "tools/nncp_libnc_named_gradient_capture.c",
    )
    parser.add_argument(
        "--adjoint-helper",
        type=Path,
        default=ROOT / "tools/nncp_libnc_ff2_output_adjoint_capture.c",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()

    libnc_root = args.libnc_root.resolve()
    named_decision_path = ROOT / "results/nncp_v33_libnc_named_gradient_trajectory_v1/decision.json"
    required = [
        libnc_root / "nncp.c",
        libnc_root / "libnc.h",
        libnc_root / "libnc.so",
        args.bound_dir / "input.bin",
        args.bound_dir / "archive.bin",
        args.bound_dir / "teacher.bin",
        args.initial_coefs,
        args.initial_export / "manifest.json",
        args.named_helper,
        args.adjoint_helper,
        named_decision_path,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, bound receipt, or helper input")
    manifest_names, manifest_dimensions = named.manifest_contract(args.initial_export)
    named_decision = json.loads(named_decision_path.read_text())
    index_by_name = {
        item["name"]: item["index"]
        for item in named_decision["identity"]["positional_receipt_identity"]
    }
    old_gradient_dir = args.bound_dir / "gradients"
    bound_gradients = {
        name: np.fromfile(
            old_gradient_dir / f"unknown_{index_by_name[name]:04d}.bin",
            dtype="<f4",
        ).reshape(manifest_dimensions[name], order="F")
        for name in manifest_names
    }

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-ff2-adjoint-") as temp:
        temporary = Path(temp)
        executable, build = compile_instrumented(
            libnc_root,
            args.named_helper.resolve(),
            args.adjoint_helper.resolve(),
            temporary,
        )
        prefix = tail.command_prefix(executable, args.initial_coefs.resolve())
        runs = [
            run_capture(label, temporary, executable, prefix, args.bound_dir)
            for label in ("first", "second")
        ]
        archive_hashes = [internal.sha256(item["archive"]) for item in runs]
        trace_hashes = [internal.sha256(item["trace"]) for item in runs]
        gradient_hashes = [directory_sha256(item["gradients"]) for item in runs]
        probe_hashes = [directory_sha256(item["probes"]) for item in runs]
        source_identity = (
            archive_hashes == [internal.BOUND_ARCHIVE_SHA256] * 2
            and trace_hashes == [internal.BOUND_TRACE_SHA256] * 2
            and runs[0]["archive"].read_bytes() == (args.bound_dir / "archive.bin").read_bytes()
            and runs[0]["trace"].read_bytes() == (args.bound_dir / "teacher.bin").read_bytes()
            and gradient_hashes[0] == gradient_hashes[1]
            and probe_hashes[0] == probe_hashes[1]
        )
        if not source_identity:
            raise RuntimeError("source, named-gradient, or probe identity failed")
        named_records = named.read_named_gradients(runs[0]["gradients"])
        named_by_name = {item["name"]: item["values"] for item in named_records}
        named_identity = (
            len(named_records) == len(manifest_names)
            and set(named_by_name) == set(manifest_names)
            and all(
                np.array_equal(named_by_name[name], bound_gradients[name])
                for name in manifest_names
            )
        )
        if not named_identity:
            raise RuntimeError("FF2 adjoint probe changed a bound named gradient")
        native_input = read_probe(runs[0]["probes"], "input")
        native_adjoint = read_probe(runs[0]["probes"], "adjoint")
        if native_input.shape != (64, 4) or native_adjoint.shape != (32, 4):
            raise RuntimeError(
                f"unexpected FF2 capture shapes {native_input.shape} {native_adjoint.shape}"
            )

        probabilities, pytorch_gradients, pytorch_adjoint, pytorch_input = (
            pytorch_run_with_adjoint(args.initial_export, args.bound_dir / "teacher.bin")
        )
        _, distributions = base.load_trace(args.bound_dir / "teacher.bin")
        probability_metrics = named.metrics(np.stack(distributions), probabilities)
        if probability_metrics["maximum_absolute_error"] > THRESHOLD:
            raise RuntimeError("PyTorch control failed teacher probability identity")
        pytorch_ff2_reconstructed = np.asarray(
            pytorch_adjoint @ pytorch_input.T, dtype=np.float32
        )
        pytorch_bias_reconstructed = np.asarray(
            pytorch_adjoint.sum(axis=1), dtype=np.float32
        )
        pytorch_algebra_exact = (
            matches(named.metrics(pytorch_gradients["ff2_0"], pytorch_ff2_reconstructed))
            and matches(
                named.metrics(
                    pytorch_gradients["ff_bias2_0"], pytorch_bias_reconstructed
                )
            )
        )
        if not pytorch_algebra_exact:
            raise RuntimeError("PyTorch FF2 adjoint algebra control failed")

        native_ff2_reconstructed = np.asarray(
            native_adjoint @ native_input.T, dtype=np.float32
        )
        native_bias_reconstructed = np.asarray(
            native_adjoint.sum(axis=1), dtype=np.float32
        )
        comparisons = {
            "native_adjoint_vs_pytorch": named.metrics(
                pytorch_adjoint, native_adjoint
            ),
            "native_input_vs_pytorch": named.metrics(pytorch_input, native_input),
            "native_reconstructed_ff2_vs_bound": named.metrics(
                bound_gradients["ff2_0"], native_ff2_reconstructed
            ),
            "native_reconstructed_bias_vs_bound": named.metrics(
                bound_gradients["ff_bias2_0"], native_bias_reconstructed
            ),
            "native_reconstructed_ff2_vs_pytorch": named.metrics(
                pytorch_gradients["ff2_0"], native_ff2_reconstructed
            ),
            "native_reconstructed_bias_vs_pytorch": named.metrics(
                pytorch_gradients["ff_bias2_0"], native_bias_reconstructed
            ),
            "bound_ff2_vs_pytorch": named.metrics(
                pytorch_gradients["ff2_0"], bound_gradients["ff2_0"]
            ),
            "bound_bias_vs_pytorch": named.metrics(
                pytorch_gradients["ff_bias2_0"], bound_gradients["ff_bias2_0"]
            ),
        }
        adjoint_matches_pytorch = matches(comparisons["native_adjoint_vs_pytorch"])
        reconstruction_matches_bound = (
            matches(comparisons["native_reconstructed_ff2_vs_bound"])
            and matches(comparisons["native_reconstructed_bias_vs_bound"])
        )
        reconstruction_matches_pytorch = (
            matches(comparisons["native_reconstructed_ff2_vs_pytorch"])
            and matches(comparisons["native_reconstructed_bias_vs_pytorch"])
        )
        if not adjoint_matches_pytorch and reconstruction_matches_bound:
            status = "UPSTREAM_ADJOINT_LOCALIZED"
            next_action = "apply the captured LibNC FF2-output adjoint contract in one bound update child"
            promotion = True
        elif adjoint_matches_pytorch and reconstruction_matches_pytorch and not reconstruction_matches_bound:
            status = "CONCAT_MATMUL_BACKWARD_LOCALIZED"
            next_action = "localize concat-optimized FF2 parameter-gradient accumulation directly"
            promotion = True
        else:
            status = "UNRESOLVED"
            next_action = "retire this observation boundary without a parity repair"
            promotion = False

        result = {
            "schema": "gamma.nncp_v33_libnc_ff2_output_adjoint_trajectory.v1",
            "candidate_id": CANDIDATE_ID,
            "status": status,
            "score_credit_bytes": 0,
            "contract": {
                "states": STATES,
                "layer": LAYER,
                "threshold": THRESHOLD,
                "probe": "zero_parameter_addition_after_ff2_bias",
                "composition": "adjoint_times_transposed_ff2_input",
            },
            "inputs": {
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_header_sha256": internal.sha256(libnc_root / "libnc.h"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
                "named_helper_sha256": internal.sha256(args.named_helper),
                "adjoint_helper_sha256": internal.sha256(args.adjoint_helper),
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "named_decision_sha256": internal.sha256(named_decision_path),
            },
            "build": build,
            "identity": {
                "source_identity": source_identity,
                "archive_sha256": archive_hashes,
                "trace_sha256": trace_hashes,
                "named_gradient_sha256": gradient_hashes,
                "probe_sha256": probe_hashes,
                "all_bound_named_gradients_byte_identical": named_identity,
                "pytorch_probability_vs_teacher": probability_metrics,
                "pytorch_adjoint_algebra_control": pytorch_algebra_exact,
            },
            "capture": {
                "native_input_shape": list(native_input.shape),
                "native_adjoint_shape": list(native_adjoint.shape),
                "native_input_sha256": hashlib.sha256(
                    native_input.astype("<f4").tobytes(order="F")
                ).hexdigest(),
                "native_adjoint_sha256": hashlib.sha256(
                    native_adjoint.astype("<f4").tobytes(order="F")
                ).hexdigest(),
                "native_adjoint_f32le_fortran_base64": base64.b64encode(
                    native_adjoint.astype("<f4").tobytes(order="F")
                ).decode("ascii"),
            },
            "comparisons": comparisons,
            "gate": {
                "adjoint_matches_pytorch": adjoint_matches_pytorch,
                "reconstruction_matches_bound": reconstruction_matches_bound,
                "reconstruction_matches_pytorch": reconstruction_matches_pytorch,
                "localized": promotion,
            },
            "decision": {
                "promotion_authorized": promotion,
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
