#!/usr/bin/env python3
"""Capture source-authoritative LibNC parameter names for bound gradients."""

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
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_tail_backward_composition as tail


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_named_gradient_trajectory_v1"
THRESHOLD = 2e-6

DECLARATIONS = """void nncp_named_gradient_set_param_list(NCParamList *parameters);
void nncp_named_gradient_dump(void *parameter_opaque, NCTensor *gradient);

"""


def patch_source(source: str) -> str:
    callback_marker = (
        "static void backward_cb(void *opaque, NCTensor *yg, "
        "NCTensor *get_col_index)"
    )
    update_marker = "    sgd_opt_update_var(opaque, yg, get_col_index);"
    backward_marker = (
        "    nc_backward(loss, nc_new_f32(s->common.device, 1.0), backward_cb,\n"
    )
    for marker in (callback_marker, update_marker, backward_marker):
        if source.count(marker) != 1:
            raise ValueError(f"source patch marker count is not one: {marker!r}")
    source = source.replace(callback_marker, DECLARATIONS + callback_marker)
    source = source.replace(
        update_marker,
        "    nncp_named_gradient_dump(opaque, yg);\n" + update_marker,
    )
    source = source.replace(
        backward_marker,
        "    nncp_named_gradient_set_param_list(&s->param_list);\n"
        + backward_marker,
    )
    return source


def compile_instrumented(
    libnc_root: Path,
    helper_source: Path,
    temporary: Path,
) -> tuple[Path, dict[str, object]]:
    original_source = libnc_root / "nncp.c"
    patched_source = temporary / "nncp_named_gradient.c"
    patched_source.write_text(patch_source(original_source.read_text()))
    nncp_object = temporary / "nncp_named_gradient.o"
    helper_object = temporary / "named_gradient_capture.o"
    executable = temporary / "nncp_named_gradient"
    compile_nncp = [
        os.environ.get("CC", "cc"),
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
    nncp_result = subprocess.run(
        compile_nncp, check=True, capture_output=True, text=True
    )
    compile_helper = [
        os.environ.get("CC", "cc"),
        "-std=gnu11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-Wno-unused-parameter",
        f"-I{libnc_root}",
        "-c",
        str(helper_source),
        "-o",
        str(helper_object),
    ]
    helper_result = subprocess.run(
        compile_helper, check=True, capture_output=True, text=True
    )
    link_command = [
        os.environ.get("CC", "cc"),
        f"-Wl,-rpath,{libnc_root}",
        "-o",
        str(executable),
        str(nncp_object),
        str(helper_object),
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
    return executable, {
        "patched_source_sha256": internal.sha256(patched_source),
        "nncp_object_command": compile_nncp,
        "nncp_object_stderr": nncp_result.stderr,
        "helper_object_command": compile_helper,
        "helper_object_stderr": helper_result.stderr,
        "link_command": link_command,
        "link_stderr": link_result.stderr,
        "executable_sha256": internal.sha256(executable),
    }


def run_capture(
    label: str,
    temporary: Path,
    executable: Path,
    prefix: list[str],
    bound_dir: Path,
) -> dict[str, object]:
    run_dir = temporary / label
    gradient_dir = run_dir / "gradients"
    gradient_dir.mkdir(parents=True)
    archive = run_dir / "archive.bin"
    trace = run_dir / "teacher.bin"
    environment = os.environ.copy()
    environment["NNCP_NAMED_GRADIENT_DIR"] = str(gradient_dir)
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
        "gradients": gradient_dir,
        "command": command,
        "stdout_sha256": hashlib.sha256(
            completed.stdout.encode("utf-8")
        ).hexdigest(),
        "stderr_sha256": hashlib.sha256(
            completed.stderr.encode("utf-8")
        ).hexdigest(),
    }


def manifest_contract(export: Path) -> tuple[list[str], dict[str, tuple[int, ...]]]:
    manifest = json.loads((export / "manifest.json").read_text())
    names = [item["name"] for item in manifest["tensors"]]
    dimensions = {
        item["name"]: tuple(int(value) for value in item["dims"])
        for item in manifest["tensors"]
    }
    return names, dimensions


def read_named_gradients(
    directory: Path,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for metadata in sorted(directory.glob("*.meta")):
        fields = dict(
            line.split("=", 1) for line in metadata.read_text().splitlines()
        )
        dimensions = tuple(int(value) for value in fields["dims"].split(","))
        data_path = metadata.with_suffix(".bin")
        values = np.fromfile(data_path, dtype="<f4").reshape(
            dimensions, order="F"
        )
        records.append(
            {
                "index": int(fields["index"]),
                "name": fields["name"],
                "dimensions": dimensions,
                "data_path": data_path,
                "values": values,
                "sha256": internal.sha256(data_path),
            }
        )
    if [item["index"] for item in records] != list(range(len(records))):
        raise ValueError("named-gradient callback indices are not consecutive")
    return records


def pytorch_run(
    export: Path,
    trace: Path,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    loaded, _ = base.load_export(export)
    weights = {
        name: value.detach().clone().requires_grad_(True)
        for name, value in loaded.items()
    }
    symbols, _ = base.load_trace(trace)
    inputs = np.concatenate((np.zeros(1, dtype=np.int64), symbols[:-1]))
    token = torch.from_numpy(inputs)
    memory = torch.zeros(4, 32, dtype=torch.float32)
    logits, _ = decoder_graph.decoder_graph_segment(
        weights, token, memory, 4, 4, 2, 8, 8
    )
    target = torch.from_numpy(symbols)
    loss = torch.nn.functional.cross_entropy(logits, target, reduction="mean")
    loss.backward()
    gradients: dict[str, np.ndarray] = {}
    for name, value in weights.items():
        if value.grad is None:
            raise RuntimeError(f"missing PyTorch gradient for {name}")
        gradients[name] = value.grad.detach().numpy().copy()
    return torch.softmax(logits, dim=-1).detach().numpy(), gradients


def gradient_sha256(gradients: dict[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for name in sorted(gradients):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(np.asarray(gradients[name], dtype="<f4").tobytes(order="F"))
    return digest.hexdigest()


def metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    difference = candidate.astype(np.float64) - reference.astype(np.float64)
    reference_norm = float(np.linalg.norm(reference.astype(np.float64)))
    signs = np.signbit(reference) != np.signbit(candidate)
    sign_magnitudes = np.minimum(np.abs(reference), np.abs(candidate))[signs]
    return {
        "elements": int(reference.size),
        "maximum_absolute_error": float(np.abs(difference).max()),
        "mean_absolute_error": float(np.abs(difference).mean()),
        "reference_l2_norm": reference_norm,
        "candidate_l2_norm": float(
            np.linalg.norm(candidate.astype(np.float64))
        ),
        "relative_l2_error": (
            float(np.linalg.norm(difference)) / reference_norm
            if reference_norm
            else None
        ),
        "sign_mismatches": int(signs.sum()),
        "largest_sign_mismatch_minimum_magnitude": (
            float(sign_magnitudes.max()) if sign_magnitudes.size else 0.0
        ),
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
        "--helper-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_named_gradient_capture.c",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()

    libnc_root = args.libnc_root.resolve()
    old_gradient_dir = args.bound_dir / "gradients"
    required = [
        libnc_root / "nncp.c",
        libnc_root / "libnc.h",
        libnc_root / "libnc.so",
        args.bound_dir / "input.bin",
        args.bound_dir / "archive.bin",
        args.bound_dir / "teacher.bin",
        args.initial_coefs,
        args.initial_export / "manifest.json",
        args.helper_source,
        *[old_gradient_dir / f"unknown_{index:04d}.bin" for index in range(18)],
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, bound receipt, or capture input")

    manifest_names, manifest_dimensions = manifest_contract(args.initial_export)
    with tempfile.TemporaryDirectory(prefix="nncp-libnc-named-gradient-") as temp:
        temporary = Path(temp)
        executable, build = compile_instrumented(
            libnc_root, args.helper_source.resolve(), temporary
        )
        prefix = tail.command_prefix(executable, args.initial_coefs.resolve())
        runs = [
            run_capture(
                label, temporary, executable, prefix, args.bound_dir
            )
            for label in ("first", "second")
        ]
        archive_hashes = [internal.sha256(item["archive"]) for item in runs]
        trace_hashes = [internal.sha256(item["trace"]) for item in runs]
        gradient_hashes = [
            internal.dump_sha256(item["gradients"]) for item in runs
        ]
        source_identity = (
            archive_hashes
            == [internal.BOUND_ARCHIVE_SHA256, internal.BOUND_ARCHIVE_SHA256]
            and trace_hashes
            == [internal.BOUND_TRACE_SHA256, internal.BOUND_TRACE_SHA256]
            and runs[0]["archive"].read_bytes()
            == (args.bound_dir / "archive.bin").read_bytes()
            and runs[0]["trace"].read_bytes()
            == (args.bound_dir / "teacher.bin").read_bytes()
        )
        if not source_identity or gradient_hashes[0] != gradient_hashes[1]:
            raise RuntimeError("named-gradient source identity or repeat failed")

        records = read_named_gradients(runs[0]["gradients"])
        record_names = [item["name"] for item in records]
        if (
            len(records) != len(manifest_names)
            or set(record_names) != set(manifest_names)
            or len(set(record_names)) != len(record_names)
            or any(item["name"] == "UNMAPPED" for item in records)
        ):
            raise RuntimeError(
                "named callbacks do not cover the manifest exactly: "
                f"callbacks={record_names!r} manifest={manifest_names!r}"
            )
        for item in records:
            if item["dimensions"] != manifest_dimensions[item["name"]]:
                raise RuntimeError(f"gradient dimensions mismatch for {item['name']}")

        positional_identity: list[dict[str, object]] = []
        for item in records:
            old_path = old_gradient_dir / f"unknown_{item['index']:04d}.bin"
            identical = old_path.read_bytes() == item["data_path"].read_bytes()
            positional_identity.append(
                {
                    "index": item["index"],
                    "name": item["name"],
                    "old_sha256": internal.sha256(old_path),
                    "named_sha256": item["sha256"],
                    "byte_identical": identical,
                }
            )
        if not all(item["byte_identical"] for item in positional_identity):
            raise RuntimeError("named gradients do not match the prior positional receipt")

        first_probabilities, first_pytorch = pytorch_run(
            args.initial_export, args.bound_dir / "teacher.bin"
        )
        second_probabilities, second_pytorch = pytorch_run(
            args.initial_export, args.bound_dir / "teacher.bin"
        )
        pytorch_repeated = (
            gradient_sha256(first_pytorch) == gradient_sha256(second_pytorch)
            and np.array_equal(first_probabilities, second_probabilities)
        )
        if not pytorch_repeated:
            raise RuntimeError("matched PyTorch gradient replay is nondeterministic")
        _, distributions = base.load_trace(args.bound_dir / "teacher.bin")
        probability_metrics = metrics(
            np.stack(distributions), first_probabilities
        )
        if probability_metrics["maximum_absolute_error"] > THRESHOLD:
            raise RuntimeError("matched PyTorch probabilities failed the bound trace")

        comparisons: list[dict[str, object]] = []
        for item in records:
            name = item["name"]
            comparison = metrics(item["values"], first_pytorch[name])
            comparisons.append(
                {
                    "callback_index": item["index"],
                    "name": name,
                    **comparison,
                }
            )
        first_divergence = next(
            (
                item
                for item in comparisons
                if item["maximum_absolute_error"] > THRESHOLD
                or item["sign_mismatches"] > 0
            ),
            None,
        )
        localized = first_divergence is not None
        result = {
            "schema": "gamma.nncp_v33_libnc_named_gradient_trajectory.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "LOCALIZED" if localized else "GRADIENTS_MATCH",
            "score_credit_bytes": 0,
            "contract": {
                "threshold": THRESHOLD,
                "expected_parameters": len(manifest_names),
                "source_patch": [
                    "set live NCParamList before nc_backward",
                    "map callback opaque pointer directly to NCParam",
                    "serialize gradient before sgd_opt_update_var",
                ],
                "command": prefix,
            },
            "inputs": {
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_header_sha256": internal.sha256(libnc_root / "libnc.h"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
                "helper_source_sha256": internal.sha256(args.helper_source),
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "tail_tool_sha256": internal.sha256(Path(tail.__file__).resolve()),
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
            },
            "build": build,
            "identity": {
                "source_identity": source_identity,
                "bound_archive_sha256": internal.BOUND_ARCHIVE_SHA256,
                "run_archive_sha256": archive_hashes,
                "bound_trace_sha256": internal.BOUND_TRACE_SHA256,
                "run_trace_sha256": trace_hashes,
                "named_gradient_run_sha256": gradient_hashes,
                "named_gradient_repeat_byte_identical": (
                    gradient_hashes[0] == gradient_hashes[1]
                ),
                "manifest_names": manifest_names,
                "callback_names": record_names,
                "positional_receipt_identity": positional_identity,
                "pytorch_repeat_byte_identical": pytorch_repeated,
                "pytorch_gradient_sha256": gradient_sha256(first_pytorch),
                "pytorch_probability_vs_teacher": probability_metrics,
            },
            "gradient_trajectory": comparisons,
            "first_divergence": first_divergence,
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": (
                    "freeze one direct named-backward subgraph child"
                    if localized
                    else "retire backward localization and inspect Adam"
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
