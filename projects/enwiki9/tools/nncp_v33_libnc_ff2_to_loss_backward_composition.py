#!/usr/bin/env python3
"""Test LibNC's shared FF2-to-loss composition against named bound gradients."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import torch
import torch.nn.functional as F

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_decoder_graph_update_parity as decoder_graph
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_tail_backward_composition as tail


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_ff2_to_loss_backward_composition_v1"
FEATURES = 32
HIDDEN = 64
CLASSES = 256
STATES = 4
TARGETS = np.asarray([60, 109, 101, 100], dtype=np.int64)
THRESHOLD = 2e-6


def aggregate_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in (
        "probabilities.bin",
        "ff2_gradient.bin",
        "bias_gradient.bin",
    ):
        digest.update(name.encode("ascii") + b"\0")
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def labeled_paths(directory: Path, label: str, elements: int) -> list[Path]:
    result: list[Path] = []
    for metadata in sorted(directory.glob("*.meta")):
        fields = dict(
            line.split("=", 1) for line in metadata.read_text().splitlines()
        )
        if fields["label"] != label:
            continue
        path = metadata.with_suffix(".bin")
        if path.stat().st_size != elements * 4:
            raise ValueError(f"unexpected {label} byte count: {path}")
        result.append(path)
    if len(result) != STATES:
        raise ValueError(f"expected {STATES} {label} tensors, got {len(result)}")
    return result


def run_probe(
    executable: Path,
    residuals: list[Path],
    hidden: list[Path],
    export: Path,
    output: Path,
) -> list[str]:
    output.mkdir(parents=True)
    command = [
        str(executable),
        *[str(path) for path in residuals],
        *[str(path) for path in hidden],
        str(export / "00007.bin"),
        str(export / "00008.bin"),
        str(export / "00013.bin"),
        str(export / "00014.bin"),
        str(export / "00016.bin"),
        str(export / "00017.bin"),
        str(output),
    ]
    subprocess.run(command, check=True)
    return command


def torch_block(
    residuals: np.ndarray,
    hidden: np.ndarray,
    weights: dict[str, torch.Tensor],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ff2 = weights["ff2_0"].detach().clone().requires_grad_(True)
    ff_bias2 = weights["ff_bias2_0"].detach().clone().requires_grad_(True)
    value = F.linear(torch.from_numpy(hidden), ff2, ff_bias2)
    value = value + torch.from_numpy(residuals)
    value = decoder_graph.libnc_rms_norm(
        value, weights["ln_g_2"], weights["ln_b_2"]
    )
    logits = F.linear(value, weights["embed_out"], weights["out_bias"])
    probabilities = torch.softmax(logits, dim=-1)
    target = torch.from_numpy(TARGETS)
    selected = probabilities[torch.arange(STATES), target]
    (-torch.log(selected).sum() / STATES).backward()
    if ff2.grad is None or ff_bias2.grad is None:
        raise RuntimeError("PyTorch FF2 block did not produce both gradients")
    return (
        probabilities.detach().numpy(),
        ff2.grad.detach().numpy(),
        ff_bias2.grad.detach().numpy(),
    )


def matched(comparison: dict[str, object]) -> bool:
    return (
        comparison["maximum_absolute_error"] <= THRESHOLD
        and comparison["sign_mismatches"] == 0
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
        "--hook-source",
        type=Path,
        default=ROOT / "tools/nncp_libnc_internal_tensor_hook.c",
    )
    parser.add_argument(
        "--probe-source",
        type=Path,
        default=(
            ROOT
            / "tools/nncp_libnc_ff2_to_loss_backward_composition_probe.c"
        ),
    )
    parser.add_argument(
        "--named-decision",
        type=Path,
        default=(
            ROOT
            / "results/nncp_v33_libnc_named_gradient_trajectory_v1/decision.json"
        ),
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
        args.bound_dir / "gradients/unknown_0001.bin",
        args.bound_dir / "gradients/unknown_0006.bin",
        args.initial_coefs,
        args.initial_export / "manifest.json",
        args.hook_source,
        args.probe_source,
        args.named_decision,
    ]
    if not all(path.is_file() for path in required):
        raise SystemExit("missing LibNC source, bound receipt, or probe input")
    named_decision = json.loads(args.named_decision.read_text())
    mapping = {
        item["index"]: item["name"]
        for item in named_decision["identity"]["positional_receipt_identity"]
    }
    if mapping.get(1) != "ff2_0" or mapping.get(6) != "ff_bias2_0":
        raise RuntimeError("named-gradient receipt does not bind FF2 inputs")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-ff2-block-") as temp:
        temporary = Path(temp)
        instrumented, hook, instrumented_build = tail.compile_instrumented_nncp(
            libnc_root, args.hook_source.resolve(), temporary
        )
        probe, probe_build = tail.compile_tail_probe(
            libnc_root, args.probe_source.resolve(), temporary
        )
        prefix = tail.command_prefix(instrumented, args.initial_coefs.resolve())
        captures = [
            tail.capture_run(
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

        probe_directories = [temporary / "block_first", temporary / "block_second"]
        probe_commands = [
            run_probe(
                probe,
                labeled_paths(capture["dump"], "attn_out", FEATURES),
                labeled_paths(capture["dump"], "ff2_in", HIDDEN),
                args.initial_export,
                directory,
            )
            for capture, directory in zip(captures, probe_directories)
        ]
        probe_hashes = [aggregate_sha256(path) for path in probe_directories]
        probe_repeated = probe_hashes[0] == probe_hashes[1]
        if not probe_repeated:
            raise RuntimeError("direct LibNC FF2 block did not repeat")

        direct_probabilities = np.fromfile(
            probe_directories[0] / "probabilities.bin", dtype="<f4"
        ).reshape((CLASSES, 1, STATES), order="F")[:, 0, :].T
        direct_ff2 = np.fromfile(
            probe_directories[0] / "ff2_gradient.bin", dtype="<f4"
        ).reshape((FEATURES, HIDDEN), order="F")
        direct_bias = np.fromfile(
            probe_directories[0] / "bias_gradient.bin", dtype="<f4"
        )
        _, distributions = base.load_trace(args.bound_dir / "teacher.bin")
        teacher_probabilities = np.stack(distributions)
        direct_probability_comparison = tail.comparison(
            teacher_probabilities, direct_probabilities
        )
        if direct_probability_comparison["maximum_absolute_error"] > THRESHOLD:
            raise RuntimeError("direct FF2 block probabilities failed identity")

        residuals = np.stack(
            [
                np.fromfile(path, dtype="<f4")
                for path in labeled_paths(
                    captures[0]["dump"], "attn_out", FEATURES
                )
            ]
        )
        hidden = np.stack(
            [
                np.fromfile(path, dtype="<f4")
                for path in labeled_paths(
                    captures[0]["dump"], "ff2_in", HIDDEN
                )
            ]
        )
        weights, exported_types = base.load_export(args.initial_export)
        torch_probabilities, torch_ff2, torch_bias = torch_block(
            residuals, hidden, weights
        )
        bound_ff2 = np.fromfile(
            args.bound_dir / "gradients/unknown_0001.bin", dtype="<f4"
        ).reshape((FEATURES, HIDDEN), order="F")
        bound_bias = np.fromfile(
            args.bound_dir / "gradients/unknown_0006.bin", dtype="<f4"
        )

        comparisons = {
            "direct_libnc_ff2_vs_bound": tail.comparison(bound_ff2, direct_ff2),
            "direct_libnc_bias_vs_bound": tail.comparison(bound_bias, direct_bias),
            "pytorch_ff2_vs_bound": tail.comparison(bound_ff2, torch_ff2),
            "pytorch_bias_vs_bound": tail.comparison(bound_bias, torch_bias),
            "direct_libnc_ff2_vs_pytorch": tail.comparison(direct_ff2, torch_ff2),
            "direct_libnc_bias_vs_pytorch": tail.comparison(
                direct_bias, torch_bias
            ),
        }
        direct_matches = matched(comparisons["direct_libnc_ff2_vs_bound"]) and matched(
            comparisons["direct_libnc_bias_vs_bound"]
        )
        torch_matches = matched(comparisons["pytorch_ff2_vs_bound"]) and matched(
            comparisons["pytorch_bias_vs_bound"]
        )
        if direct_matches and not torch_matches:
            status = "FF2_BLOCK_LOCALIZED"
            promotion = True
            next_action = "replay the bound update with the proved FF2 block contract"
        elif direct_matches:
            status = "FORWARD_ROUNDING_AMPLIFICATION"
            promotion = False
            next_action = "retire a distinct FF2 block backward contract"
        else:
            status = "FF2_BLOCK_NOT_REPRODUCED"
            promotion = False
            next_action = (
                "retire FF2-to-loss composition as sufficient and move the "
                "direct boundary earlier"
            )

        result = {
            "schema": "gamma.nncp_v33_libnc_ff2_to_loss_backward_composition.v1",
            "candidate_id": CANDIDATE_ID,
            "status": status,
            "score_credit_bytes": 0,
            "contract": {
                "features": FEATURES,
                "hidden": HIDDEN,
                "classes": CLASSES,
                "states": STATES,
                "targets": TARGETS.tolist(),
                "threshold": THRESHOLD,
                "block": [
                    "shared FF2 matrix",
                    "shared FF2 bias",
                    "captured residual join",
                    "final RMSNorm, projection, softmax, and loss tail",
                    "four-state concat optimization",
                ],
            },
            "inputs": {
                "libnc_source_sha256": internal.sha256(libnc_root / "nncp.c"),
                "libnc_header_sha256": internal.sha256(libnc_root / "libnc.h"),
                "libnc_library_sha256": internal.sha256(libnc_root / "libnc.so"),
                "hook_source_sha256": internal.sha256(args.hook_source),
                "probe_source_sha256": internal.sha256(args.probe_source),
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "named_decision_sha256": internal.sha256(args.named_decision),
                "initial_coefs_sha256": internal.sha256(args.initial_coefs),
                "initial_manifest_sha256": internal.sha256(
                    args.initial_export / "manifest.json"
                ),
                "bound_ff2_gradient_sha256": internal.sha256(
                    args.bound_dir / "gradients/unknown_0001.bin"
                ),
                "bound_ff_bias2_gradient_sha256": internal.sha256(
                    args.bound_dir / "gradients/unknown_0006.bin"
                ),
                "exported_parameter_types": exported_types,
            },
            "build": {
                "instrumented_nncp": instrumented_build,
                "block_probe": probe_build,
            },
            "identity": {
                "capture_bound_identity": capture_identity,
                "bound_archive_sha256": internal.BOUND_ARCHIVE_SHA256,
                "run_archive_sha256": archive_hashes,
                "bound_trace_sha256": internal.BOUND_TRACE_SHA256,
                "run_trace_sha256": trace_hashes,
                "run_dump_sha256": dump_hashes,
                "dump_repeat_byte_identical": dump_hashes[0] == dump_hashes[1],
                "block_run_sha256": probe_hashes,
                "block_repeat_byte_identical": probe_repeated,
                "block_commands": probe_commands,
                "direct_probability_vs_teacher": direct_probability_comparison,
                "pytorch_probability_vs_teacher": tail.comparison(
                    teacher_probabilities, torch_probabilities
                ),
            },
            "gradients": comparisons,
            "gate": {
                "direct_libnc_matches_both_bound_gradients": direct_matches,
                "pytorch_matches_both_bound_gradients": torch_matches,
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
