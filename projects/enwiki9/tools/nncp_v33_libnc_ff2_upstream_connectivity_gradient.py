#!/usr/bin/env python3
"""Test FF2 upstream graph connectivity with forward-identical source cuts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_named_gradient_trajectory as named
import nncp_v33_libnc_tail_backward_composition as tail


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_ff2_upstream_connectivity_gradient_v1"
THRESHOLD = 2e-6
VARIANTS = ("none", "hidden_stop", "residual_stop", "both_stop")
RESIDUAL_MARKER = "        ff_input = nc_dup_tensor(t0);"
HIDDEN_MARKER = "        t0 = nc_matmul(nc_dup_tensor(tl->ff2), t0);"
DECLARATION_MARKER = "static NCTensor *layer_norm("


def variant_source(source: str, variant: str) -> str:
    if variant not in VARIANTS:
        raise ValueError(f"unknown connectivity variant: {variant}")
    if (
        source.count(RESIDUAL_MARKER) != 1
        or source.count(HIDDEN_MARKER) != 1
        or source.count(DECLARATION_MARKER) != 1
    ):
        raise ValueError("FF2 connectivity source marker count is not one")
    source = source.replace(
        DECLARATION_MARKER,
        "NCTensor *nncp_constant_copy(NCTensor *source);\n\n"
        + DECLARATION_MARKER,
    )
    if variant in ("residual_stop", "both_stop"):
        source = source.replace(
            RESIDUAL_MARKER,
            RESIDUAL_MARKER
            + "\n        ff_input = nncp_constant_copy(ff_input);",
        )
    if variant in ("hidden_stop", "both_stop"):
        source = source.replace(
            HIDDEN_MARKER,
            "        t0 = nncp_constant_copy(t0);\n" + HIDDEN_MARKER,
        )
    return named.patch_source(source)


def compile_variant(
    libnc_root: Path,
    helper_source: Path,
    constant_copy_source: Path,
    temporary: Path,
    variant: str,
) -> tuple[Path, dict[str, object]]:
    variant_dir = temporary / f"build_{variant}"
    variant_dir.mkdir()
    patched_source = variant_dir / "nncp.c"
    patched_source.write_text(
        variant_source((libnc_root / "nncp.c").read_text(), variant)
    )
    nncp_object = variant_dir / "nncp.o"
    helper_object = variant_dir / "capture.o"
    constant_copy_object = variant_dir / "constant_copy.o"
    executable = variant_dir / "nncp"
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
    compile_constant_copy = [
        os.environ.get("CC", "cc"),
        "-std=gnu11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-Wno-unused-parameter",
        f"-I{libnc_root}",
        "-c",
        str(constant_copy_source),
        "-o",
        str(constant_copy_object),
    ]
    constant_copy_result = subprocess.run(
        compile_constant_copy, check=True, capture_output=True, text=True
    )
    link_command = [
        os.environ.get("CC", "cc"),
        f"-Wl,-rpath,{libnc_root}",
        "-o",
        str(executable),
        str(nncp_object),
        str(helper_object),
        str(constant_copy_object),
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
        "variant": variant,
        "patched_source_sha256": internal.sha256(patched_source),
        "nncp_object_command": compile_nncp,
        "nncp_object_stderr": nncp_result.stderr,
        "helper_object_command": compile_helper,
        "helper_object_stderr": helper_result.stderr,
        "constant_copy_object_command": compile_constant_copy,
        "constant_copy_object_stderr": constant_copy_result.stderr,
        "link_command": link_command,
        "link_stderr": link_result.stderr,
        "executable_sha256": internal.sha256(executable),
    }


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
        "--helper-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_named_gradient_capture.c",
    )
    parser.add_argument(
        "--constant-copy-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_constant_copy.c",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    args = parser.parse_args()

    libnc_root = args.libnc_root.resolve()
    old_gradient_dir = args.bound_dir / "gradients"
    named_decision_path = (
        ROOT
        / "results/nncp_v33_libnc_named_gradient_trajectory_v1/decision.json"
    )
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
        args.constant_copy_source,
        named_decision_path,
        *[old_gradient_dir / f"unknown_{index:04d}.bin" for index in range(18)],
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, bound receipt, or gradient input")
    manifest_names, manifest_dimensions = named.manifest_contract(
        args.initial_export
    )
    named_decision = json.loads(named_decision_path.read_text())
    index_by_name = {
        item["name"]: item["index"]
        for item in named_decision["identity"]["positional_receipt_identity"]
    }
    old_by_name = {
        name: np.fromfile(
            old_gradient_dir / f"unknown_{index_by_name[name]:04d}.bin",
            dtype="<f4",
        ).reshape(manifest_dimensions[name], order="F")
        for name in manifest_names
    }

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-connectivity-") as temp:
        temporary = Path(temp)
        variant_receipts: dict[str, dict[str, object]] = {}
        variant_gradients: dict[str, dict[str, np.ndarray]] = {}
        builds: dict[str, object] = {}
        for variant in VARIANTS:
            executable, build = compile_variant(
                libnc_root,
                args.helper_source.resolve(),
                args.constant_copy_source.resolve(),
                temporary,
                variant,
            )
            builds[variant] = build
            prefix = tail.command_prefix(executable, args.initial_coefs.resolve())
            runs = [
                named.run_capture(
                    f"{variant}_{label}",
                    temporary,
                    executable,
                    prefix,
                    args.bound_dir,
                )
                for label in ("first", "second")
            ]
            archive_hashes = [internal.sha256(item["archive"]) for item in runs]
            trace_hashes = [internal.sha256(item["trace"]) for item in runs]
            gradient_hashes = [
                internal.dump_sha256(item["gradients"]) for item in runs
            ]
            identity = (
                archive_hashes
                == [internal.BOUND_ARCHIVE_SHA256, internal.BOUND_ARCHIVE_SHA256]
                and trace_hashes
                == [internal.BOUND_TRACE_SHA256, internal.BOUND_TRACE_SHA256]
                and runs[0]["archive"].read_bytes()
                == (args.bound_dir / "archive.bin").read_bytes()
                and runs[0]["trace"].read_bytes()
                == (args.bound_dir / "teacher.bin").read_bytes()
                and gradient_hashes[0] == gradient_hashes[1]
            )
            if not identity:
                raise RuntimeError(f"identity or repeat failed for {variant}")
            records = named.read_named_gradients(runs[0]["gradients"])
            gradients = {item["name"]: item["values"] for item in records}
            required_names = {
                "embed_out",
                "ff2_0",
                "ff_bias2_0",
                "ln_g_2",
                "ln_b_2",
                "out_bias",
            }
            if not required_names.issubset(gradients):
                raise RuntimeError(f"downstream names missing for {variant}")
            if len(gradients) != len(records):
                raise RuntimeError(f"duplicate callback names for {variant}")
            for item in records:
                if item["dimensions"] != manifest_dimensions[item["name"]]:
                    raise RuntimeError(
                        f"gradient dimensions mismatch for {variant}:{item['name']}"
                    )
            variant_gradients[variant] = gradients
            variant_receipts[variant] = {
                "source_identity": identity,
                "archive_sha256": archive_hashes,
                "trace_sha256": trace_hashes,
                "gradient_sha256": gradient_hashes,
                "gradient_repeat_byte_identical": (
                    gradient_hashes[0] == gradient_hashes[1]
                ),
                "callback_names": [item["name"] for item in records],
            }

        full_identity = all(
            np.array_equal(variant_gradients["none"][name], old_by_name[name])
            for name in manifest_names
        )
        if not full_identity:
            raise RuntimeError("uncut variant failed prior named-gradient identity")
        pytorch_probabilities, pytorch_gradients = named.pytorch_run(
            args.initial_export, args.bound_dir / "teacher.bin"
        )
        _, distributions = base.load_trace(args.bound_dir / "teacher.bin")
        probability_metrics = named.metrics(
            np.stack(distributions), pytorch_probabilities
        )
        if probability_metrics["maximum_absolute_error"] > THRESHOLD:
            raise RuntimeError("PyTorch control failed teacher probability identity")

        comparisons: dict[str, object] = {}
        variant_gate: dict[str, object] = {}
        for variant in VARIANTS:
            ff2_vs_bound = named.metrics(
                old_by_name["ff2_0"], variant_gradients[variant]["ff2_0"]
            )
            bias_vs_bound = named.metrics(
                old_by_name["ff_bias2_0"],
                variant_gradients[variant]["ff_bias2_0"],
            )
            ff2_vs_pytorch = named.metrics(
                pytorch_gradients["ff2_0"], variant_gradients[variant]["ff2_0"]
            )
            bias_vs_pytorch = named.metrics(
                pytorch_gradients["ff_bias2_0"],
                variant_gradients[variant]["ff_bias2_0"],
            )
            comparisons[variant] = {
                "ff2_vs_bound": ff2_vs_bound,
                "bias_vs_bound": bias_vs_bound,
                "ff2_vs_pytorch": ff2_vs_pytorch,
                "bias_vs_pytorch": bias_vs_pytorch,
            }
            variant_gate[variant] = {
                "matches_bound": matches(ff2_vs_bound) and matches(bias_vs_bound),
                "matches_pytorch": (
                    matches(ff2_vs_pytorch) and matches(bias_vs_pytorch)
                ),
            }

        transition = next(
            (
                variant
                for variant in ("hidden_stop", "residual_stop", "both_stop")
                if variant_gate[variant]["matches_pytorch"]
            ),
            None,
        )
        localized = (
            variant_gate["none"]["matches_bound"]
            and variant_gate["both_stop"]["matches_pytorch"]
            and not variant_gate["both_stop"]["matches_bound"]
            and transition is not None
        )
        result = {
            "schema": (
                "gamma.nncp_v33_libnc_ff2_upstream_connectivity_gradient.v1"
            ),
            "candidate_id": CANDIDATE_ID,
            "status": "CONNECTIVITY_LOCALIZED" if localized else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "variants": list(VARIANTS),
                "threshold": THRESHOLD,
                "frozen_stop_sets": {
                    "none": [],
                    "hidden_stop": ["ff2_hidden"],
                    "residual_stop": ["residual"],
                    "both_stop": ["ff2_hidden", "residual"],
                },
                "symbols": 4,
            },
            "inputs": {
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_header_sha256": internal.sha256(libnc_root / "libnc.h"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
                "helper_source_sha256": internal.sha256(args.helper_source),
                "constant_copy_source_sha256": internal.sha256(
                    args.constant_copy_source
                ),
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "named_decision_sha256": internal.sha256(named_decision_path),
                "initial_coefs_sha256": internal.sha256(args.initial_coefs),
                "initial_manifest_sha256": internal.sha256(
                    args.initial_export / "manifest.json"
                ),
            },
            "builds": builds,
            "identity": {
                "bound_archive_sha256": internal.BOUND_ARCHIVE_SHA256,
                "bound_trace_sha256": internal.BOUND_TRACE_SHA256,
                "uncut_named_gradient_byte_identity": full_identity,
                "variants": variant_receipts,
                "pytorch_probability_vs_teacher": probability_metrics,
            },
            "comparisons": comparisons,
            "gate": {
                "variants": variant_gate,
                "minimal_pytorch_matching_stop_set": transition,
                "connectivity_localized": localized,
            },
            "decision": {
                "promotion_authorized": localized,
                "authorized_next_action": (
                    f"freeze the {transition} connectivity parity child"
                    if localized
                    else "retire FF2 upstream connectivity as the isolated cause"
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
