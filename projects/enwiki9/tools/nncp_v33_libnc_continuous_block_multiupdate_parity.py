#!/usr/bin/env python3
"""Test LibNC multi-update parity inside one continuous process block."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np
import torch

import nncp_libnc_relative_parity as base
import nncp_v33_libnc_concat_rmsnorm_multiupdate_parity as multi
import nncp_v33_libnc_internal_forward_trajectory as internal
import nncp_v33_libnc_update_state_trajectory as update_state


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_v33_libnc_continuous_block_multiupdate_parity_v1"
BYTES = 32
SEGMENT = 4
UPDATES = 8
PROBABILITY_TOLERANCE = 2e-5
PARAMETER_TOLERANCE = 2e-5
MEMORY_TOLERANCE = 2e-6


def continuous_prefix(executable: Path) -> list[str]:
    command = multi.command_prefix(executable, Path("unused.initial.coefs"))
    index = command.index("--block_len")
    if command[index + 1] != "4":
        raise ValueError("unexpected miniature parent block length")
    command[index + 1] = str(BYTES)
    return command


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
        / "results/nncp_v33_libnc_process_block_reset_multiupdate_parity_v1/decision.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID / "decision.json",
    )
    parser.add_argument("--learning-rate", type=float, default=0.00016)
    parser.add_argument("--gradient-clip", type=float, default=0.05)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite a continuous decision")
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
        raise SystemExit("missing LibNC source, corpus, export, or parent")
    parent = json.loads(args.parent_decision.read_text())
    if parent.get("status") != "REJECT":
        raise ValueError("unexpected reset-parent status")

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-continuous-") as temp:
        temporary = Path(temp)
        input_path = temporary / "enwik9.prefix32"
        with args.raw_input.open("rb") as source:
            raw = source.read(BYTES)
        input_path.write_bytes(raw)
        executable, exporter, build = update_state.compile_native(
            libnc_root, args.exporter_source.resolve(), temporary
        )
        prefix = continuous_prefix(executable)
        runs = [
            update_state.native_run(label, temporary, prefix, input_path)
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
        if not source_repeat:
            raise RuntimeError("continuous native captures failed to repeat")

        source_parameters: list[dict[str, torch.Tensor]] = []
        source_memories: list[torch.Tensor] = []
        source_train_states: list[torch.Tensor] = []
        for step in range(UPDATES):
            parameters = update_state.export_file(
                exporter,
                runs[0]["coefs"][step],
                temporary / f"source_step_{step:02d}_coefs",
            )
            memories = update_state.export_file(
                exporter,
                runs[0]["memories"][step],
                temporary / f"source_step_{step:02d}_memory",
            )
            source_parameters.append(parameters)
            source_memories.append(
                update_state.canonical_memory(memories["mem_h_0"])
            )
            source_train_states.append(
                update_state.canonical_memory(memories["train_h_0"])
            )
        symbols, distributions = base.load_trace(runs[0]["trace"])
        if len(symbols) != BYTES or not np.array_equal(
            symbols, np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
        ):
            raise RuntimeError("continuous source symbols do not bind raw prefix")
        teacher_probabilities = torch.from_numpy(np.stack(distributions))
        initial, _ = base.load_export(args.initial_export)
        analytic_runs = [
            update_state.analytic_trajectory(
                initial, symbols, args.learning_rate, args.gradient_clip
            )
            for _ in range(2)
        ]
        first_probabilities, first_parameters, first_memories = analytic_runs[0]
        second_probabilities, second_parameters, second_memories = analytic_runs[1]
        analytic_repeat = (
            torch.equal(first_probabilities, second_probabilities)
            and [update_state.tensor_map_hash(value) for value in first_parameters]
            == [update_state.tensor_map_hash(value) for value in second_parameters]
            and [update_state.tensor_hash(value) for value in first_memories]
            == [update_state.tensor_hash(value) for value in second_memories]
        )
        probability_error = (first_probabilities - teacher_probabilities).abs()
        probability_rows = [
            {
                "segment": start // SEGMENT + 1,
                "maximum_absolute_error": float(
                    probability_error[start : start + SEGMENT].max()
                ),
            }
            for start in range(0, BYTES, SEGMENT)
        ]
        step_rows = []
        for step in range(UPDATES):
            names = sorted(
                set(source_parameters[step]) & set(first_parameters[step])
            )
            parameter_errors = {
                name: float(
                    (
                        source_parameters[step][name]
                        - first_parameters[step][name]
                    )
                    .abs()
                    .max()
                )
                for name in names
            }
            step_rows.append(
                {
                    "step": step + 1,
                    "parameter_maximum_absolute_error": max(
                        parameter_errors.values()
                    ),
                    "parameter_maximum_errors": parameter_errors,
                    "memory_maximum_absolute_error": float(
                        (source_memories[step] - first_memories[step]).abs().max()
                    ),
                    "train_h_maximum_absolute_error": float(
                        (source_train_states[step] - first_memories[step]).abs().max()
                    ),
                    "source_parameter_sha256": update_state.tensor_map_hash(
                        source_parameters[step]
                    ),
                    "analytic_parameter_sha256": update_state.tensor_map_hash(
                        first_parameters[step]
                    ),
                    "source_memory_sha256": update_state.tensor_hash(
                        source_memories[step]
                    ),
                    "analytic_memory_sha256": update_state.tensor_hash(
                        first_memories[step]
                    ),
                }
            )
        maximum_probability_error = max(
            row["maximum_absolute_error"] for row in probability_rows
        )
        maximum_parameter_error = max(
            row["parameter_maximum_absolute_error"] for row in step_rows
        )
        maximum_memory_error = max(
            row["memory_maximum_absolute_error"] for row in step_rows
        )
        maximum_train_error = max(
            row["train_h_maximum_absolute_error"] for row in step_rows
        )
        probabilities_legal = bool(
            torch.isfinite(first_probabilities).all()
            and (first_probabilities > 0).all()
            and torch.allclose(
                first_probabilities.sum(dim=-1),
                torch.ones(BYTES),
                atol=1e-6,
                rtol=0,
            )
        )
        passed = (
            source_repeat
            and analytic_repeat
            and probabilities_legal
            and maximum_probability_error <= PROBABILITY_TOLERANCE
            and maximum_parameter_error <= PARAMETER_TOLERANCE
            and maximum_memory_error <= MEMORY_TOLERANCE
            and maximum_train_error <= MEMORY_TOLERANCE
        )
        result = {
            "schema": "gamma.nncp_v33_libnc_continuous_block_multiupdate_parity.v1",
            "candidate_id": CANDIDATE_ID,
            "status": "PASS" if passed else "REJECT",
            "score_credit_bytes": 0,
            "contract": {
                "raw_bytes": BYTES,
                "block_len": BYTES,
                "segment": SEGMENT,
                "updates": UPDATES,
                "state_schedule": "continuous_inside_one_process_block",
                "probability_tolerance": PROBABILITY_TOLERANCE,
                "parameter_tolerance": PARAMETER_TOLERANCE,
                "memory_tolerance": MEMORY_TOLERANCE,
                "learning_rate": args.learning_rate,
                "gradient_clip": args.gradient_clip,
            },
            "inputs": {
                "script_sha256": internal.sha256(Path(__file__).resolve()),
                "raw_corpus_sha256": internal.sha256(args.raw_input),
                "raw_prefix_sha256": hashlib.sha256(raw).hexdigest(),
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
            },
            "analytic_proof": {
                "repeat_byte_identical": analytic_repeat,
                "probabilities_legal": probabilities_legal,
                "maximum_probability_error": maximum_probability_error,
                "maximum_parameter_error": maximum_parameter_error,
                "maximum_memory_error": maximum_memory_error,
                "maximum_train_h_error": maximum_train_error,
                "probability_segments": probability_rows,
                "steps": step_rows,
            },
            "decision": {
                "promotion_authorized": passed,
                "authorized_next_action": (
                    "freeze the smallest source-bound continuous-profile prefix gate"
                    if passed
                    else "retire continuous-block multi-update parity"
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
