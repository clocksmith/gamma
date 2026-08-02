#!/usr/bin/env python3
"""Exact 65,536-symbol constructive headroom gate for the ROCm NNCP profile."""

from __future__ import annotations

import argparse
from array import array
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
ROCM_PYTHON = Path("/home/x/deco/gamma/.venv_rocm/bin/python")
os.environ.setdefault("AMD_SERIALIZE_KERNEL", "3")
os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", "11.0.0")
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        os.environ.copy(),
    )

import numpy as np
import torch

import nncp_v33_rocm_constructive_causal_replay_q0 as q0
from janus_paid_residual_mdl_oracle import range_decode, range_encode
from radix_island_oracle import emission_groups
from wrt_exact import parse_store


core = q0.core
CANDIDATE_ID = "nncp_v33_rocm_constructive_65536_headroom_q1_v1"
SYMBOL_COUNT = 65_536
STREAM_LENGTH = SYMBOL_COUNT // core.Config.streams
P1_MAGIC = b"CMX21P1\0"
GROSS_GATE_BPM = 3_000.0


def tensor_bytes(value: torch.Tensor) -> bytes:
    host = value.detach().contiguous().cpu()
    if host.dtype == torch.bfloat16:
        return host.view(torch.uint16).numpy().tobytes()
    return host.numpy().tobytes()


def optimizer_hash(
    model: torch.nn.Module, optimizer: torch.optim.Optimizer
) -> str:
    digest = hashlib.sha256()
    for index, parameter in enumerate(model.parameters()):
        digest.update(struct.pack("<I", index))
        state = optimizer.state.get(parameter, {})
        for key in sorted(state):
            digest.update(str(key).encode("ascii") + b"\0")
            value = state[key]
            if torch.is_tensor(value):
                digest.update(str(value.dtype).encode("ascii") + b"\0")
                digest.update(tensor_bytes(value))
            else:
                digest.update(repr(value).encode("ascii") + b"\0")
    return digest.hexdigest()


def memory_hash(memories: list[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for index, memory in enumerate(memories):
        digest.update(struct.pack("<I", index))
        digest.update(tensor_bytes(memory))
    return digest.hexdigest()


def complete_state_hash(
    model_hash: str, optimizer_state_hash: str, persistent_memory_hash: str
) -> str:
    return hashlib.sha256(
        bytes.fromhex(model_hash)
        + bytes.fromhex(optimizer_state_hash)
        + bytes.fromhex(persistent_memory_hash)
    ).hexdigest()


def run_once(
    symbols: np.ndarray,
    config: core.Config,
    device: torch.device,
    mode: str,
    payload: bytes | None = None,
) -> dict[str, object]:
    if mode not in ("encode_first", "encode_second", "decode"):
        raise ValueError(f"invalid run mode: {mode}")
    print(json.dumps({"event": "run_start", "mode": mode}), flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    model = core.make_model(config, device)
    optimizer = core.optimizer_for(model, config)
    memories = model.empty_memory(device)
    source_matrix = symbols.reshape(config.streams, STREAM_LENGTH)
    if mode == "decode":
        values = torch.zeros(
            config.streams,
            STREAM_LENGTH,
            dtype=torch.long,
            device=device,
        )
        coder = core.RangeDecoder(payload or b"")
    else:
        values = torch.from_numpy(source_matrix.astype(np.int64)).to(device)
        coder = core.RangeEncoder()
    trace = array("H")
    losses: list[float] = []
    started = time.monotonic()
    segment_count = STREAM_LENGTH // config.segment_length

    for segment in range(segment_count):
        segment_start = segment * config.segment_length
        segment_end = segment_start + config.segment_length
        inputs = torch.zeros(
            config.streams,
            config.segment_length,
            dtype=torch.long,
            device=device,
        )
        if segment:
            inputs[:, 0] = values[:, segment_start - 1]
        final_logits = None
        next_memories = None
        for state in range(config.segment_length):
            if state:
                inputs[:, state] = values[:, segment_start + state - 1]
            if state + 1 == config.segment_length:
                optimizer.zero_grad(set_to_none=True)
                logits, next_memories = model(inputs, memories)
                final_logits = logits
            else:
                with torch.no_grad():
                    logits, _ = model(inputs, memories)
            probability = torch.softmax(
                logits[:, state, :].detach(), dim=-1
            ).cpu().numpy()
            if mode == "decode":
                for stream in range(config.streams):
                    values[stream, segment_start + state] = (
                        core.branch_decode_one(
                            coder, probability[stream], trace
                        )
                    )
            else:
                core.branch_encode(
                    coder,
                    probability,
                    source_matrix[:, segment_start + state],
                    trace,
                )
            if state + 1 != config.segment_length:
                del logits
            del probability

        if final_logits is None or next_memories is None:
            raise AssertionError("missing segment-final differentiable state")
        targets = values[:, segment_start:segment_end]
        losses.append(
            core.update_model(model, optimizer, final_logits, targets, config)
        )
        memories = [memory.detach() for memory in next_memories]
        del final_logits, next_memories, targets, inputs
        if (segment + 1) % 4 == 0:
            torch.cuda.synchronize(device)
            print(
                json.dumps(
                    {
                        "elapsed_seconds": time.monotonic() - started,
                        "event": "run_checkpoint",
                        "mode": mode,
                        "segments": segment + 1,
                        "total_segments": segment_count,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    archive = coder.finish() if mode != "decode" else payload
    torch.cuda.synchronize(device)
    model_state = core.parameter_state_hash(model)
    adam_state = optimizer_hash(model, optimizer)
    persistent_state = memory_hash(memories)
    complete_state = complete_state_hash(
        model_state, adam_state, persistent_state
    )
    result = {
        "archive": archive,
        "branch_trace": trace,
        "complete_state_sha256": complete_state,
        "decoded": (
            values.detach().cpu().numpy().astype(np.uint16)
            if mode == "decode"
            else None
        ),
        "elapsed_seconds": time.monotonic() - started,
        "losses": losses,
        "model_sha256": model_state,
        "optimizer_sha256": adam_state,
        "persistent_memory_sha256": persistent_state,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
    }
    del optimizer, model, memories, values
    torch.cuda.empty_cache()
    print(
        json.dumps(
            {
                "complete_state_sha256": complete_state,
                "event": "run_complete",
                "mode": mode,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return result


def read_joint_p1(path: Path, rows: int) -> np.memmap:
    with path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid joint P1 header")
    declared = struct.unpack_from("<Q", header, 8)[0]
    if declared != rows or path.stat().st_size != 16 + 2 * rows:
        raise ValueError("joint P1 row binding failed")
    values = np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))
    if np.any(values == 0):
        raise ValueError("joint P1 contains an illegal zero probability")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preprocessed",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
            "preprocessed.bin"
        ),
    )
    parser.add_argument(
        "--symbol-map",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
            "symbol_raw_map.bin"
        ),
    )
    parser.add_argument(
        "--nncp-dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
            "dictionary.bin"
        ),
    )
    parser.add_argument(
        "--nncp-binary",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp"),
    )
    parser.add_argument(
        "--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin"
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT
        / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--wrt-dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/english.dic"
        ),
    )
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/"
        "joint_candidate.p1",
    )
    parser.add_argument(
        "--q0-decision",
        type=Path,
        default=ROOT
        / "results/nncp_v33_rocm_constructive_causal_replay_q0_v1/decision.json",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "results" / CANDIDATE_ID
    )
    args = parser.parse_args()
    required = (
        args.preprocessed,
        args.symbol_map,
        args.nncp_dictionary,
        args.nncp_binary,
        args.raw_input,
        args.wrt_store,
        args.wrt_dictionary,
        args.joint_p1,
        args.q0_decision,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    q0_decision = json.loads(args.q0_decision.read_text())
    if q0_decision.get("status") != "AUTHORIZED_65536_HEADROOM":
        raise ValueError("constructive Q0 does not authorize Q1")
    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("PyTorch ROCm is required")

    config = core.Config()
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda")
    matrix_sha256 = core.matrix_probe(device)
    source = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    symbols = np.asarray(source[:SYMBOL_COUNT], dtype=np.uint16)
    if len(symbols) != SYMBOL_COUNT or int(symbols.max()) >= config.vocabulary:
        raise ValueError("frozen preprocessed population is invalid")

    first = run_once(symbols, config, device, "encode_first")
    second = run_once(symbols, config, device, "encode_second")
    decoded = run_once(
        symbols, config, device, "decode", first["archive"]
    )
    first_trace = core.trace_bytes(first["branch_trace"])
    second_trace = core.trace_bytes(second["branch_trace"])
    decoded_trace = core.trace_bytes(decoded["branch_trace"])
    reconstructed = decoded["decoded"].reshape(-1)
    archive_repeat = first["archive"] == second["archive"]
    frequency_identity = first_trace == second_trace == decoded_trace
    symbol_identity = np.array_equal(reconstructed, symbols)
    state_identity = (
        first["complete_state_sha256"]
        == second["complete_state_sha256"]
        == decoded["complete_state_sha256"]
    )
    loss_identity = first["losses"] == second["losses"] == decoded["losses"]
    if not all(
        (archive_repeat, frequency_identity, symbol_identity, state_identity, loss_identity)
    ):
        raise ValueError("65,536-symbol constructive identity failed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / "archive.bin"
    archive_path.write_bytes(first["archive"])
    trace_path = args.output_dir / "branch_trace.bin"
    trace_path.write_bytes(first_trace)
    decoded_path = args.output_dir / "decoded_symbols.bin"
    reconstructed.astype(">u2").tofile(decoded_path)

    map_dtype = np.dtype(
        [("raw_start", "<u8"), ("raw_end", "<u8"), ("symbol", "<u2")]
    )
    mapped = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=map_dtype,
        offset=16,
        shape=(SYMBOL_COUNT,),
    )
    if not np.array_equal(np.asarray(mapped["symbol"]), symbols):
        raise ValueError("symbol map differs from preprocessed population")
    raw_bytes = int(mapped["raw_end"][-1])
    restored_path = args.output_dir / "restored.raw"
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(args.nncp_binary.parent)
    subprocess.run(
        [
            str(args.nncp_binary),
            "--dict",
            str(args.nncp_dictionary),
            "pd",
            str(decoded_path),
            str(restored_path),
        ],
        check=True,
        env=environment,
        capture_output=True,
    )
    raw = args.raw_input.read_bytes()
    expected_raw = raw[:raw_bytes]
    raw_identity = restored_path.read_bytes() == expected_raw
    if not raw_identity:
        raise ValueError("official NNCP inverse differs from raw prefix")

    parsed = parse_store(args.wrt_store, args.wrt_dictionary)
    if parsed.decoded != raw:
        raise ValueError("WRT store differs from raw input")
    groups = emission_groups(parsed)
    matching_groups = [group for group in groups if group.raw_end == raw_bytes]
    if len(matching_groups) != 1:
        raise ValueError("NNCP boundary is not one exact WRT group boundary")
    joint_rows = matching_groups[0].stream_end * 8
    wrt = np.frombuffer(args.wrt_store.read_bytes(), dtype=np.uint8, offset=5)
    truth = np.unpackbits(wrt, bitorder="big")
    joint_p1 = read_joint_p1(args.joint_p1, len(truth))
    joint_prefix = range_encode(joint_p1[:joint_rows], truth[:joint_rows])
    if not np.array_equal(
        range_decode(joint_prefix, joint_p1[:joint_rows]), truth[:joint_rows]
    ):
        raise ValueError("terminated joint prefix does not decode exactly")
    joint_path = args.output_dir / "joint_prefix.payload"
    joint_path.write_bytes(joint_prefix)

    gain_bytes = len(joint_prefix) - len(first["archive"])
    gain_bpm = gain_bytes * 1_000_000.0 / raw_bytes
    peak_allocated = max(
        first["peak_allocated_bytes"],
        second["peak_allocated_bytes"],
        decoded["peak_allocated_bytes"],
    )
    memory_pass = peak_allocated < 10_000_000_000
    exactness_pass = all(
        (
            archive_repeat,
            frequency_identity,
            symbol_identity,
            state_identity,
            loss_identity,
            raw_identity,
            memory_pass,
        )
    )
    promotion = exactness_pass and gain_bpm >= GROSS_GATE_BPM
    decision = {
        "schema": "gamma.nncp_v33_rocm_constructive_65536_headroom_q1.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_MATURE_DESIGN" if promotion else "REJECT",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact constructive 65,536-symbol gross headroom only; no LibNC "
            "parity, package/forecast credit, or full-corpus claim."
        ),
        "config": asdict(config),
        "runtime": {
            "device": torch.cuda.get_device_name(device),
            "hip": torch.version.hip,
            "matrix_output_sha256": matrix_sha256,
            "runtime_mode": "rocm_gfx_override",
            "torch": torch.__version__,
        },
        "population": {
            "symbols": SYMBOL_COUNT,
            "raw_bytes": raw_bytes,
            "streams": config.streams,
            "symbols_per_stream": STREAM_LENGTH,
            "update_segments": STREAM_LENGTH // config.segment_length,
            "joint_wrt_rows": joint_rows,
        },
        "archive": {
            "nncp_bytes": len(first["archive"]),
            "nncp_sha256": hashlib.sha256(first["archive"]).hexdigest(),
            "joint_prefix_bytes": len(joint_prefix),
            "joint_prefix_sha256": hashlib.sha256(joint_prefix).hexdigest(),
            "branch_frequencies": len(first["branch_trace"]),
            "branch_trace_sha256": hashlib.sha256(first_trace).hexdigest(),
            "gross_gain_bytes": gain_bytes,
            "gross_gain_bytes_per_raw_million": gain_bpm,
            "required_bytes_per_raw_million": GROSS_GATE_BPM,
        },
        "state": {
            "complete_sha256": first["complete_state_sha256"],
            "model_sha256": first["model_sha256"],
            "optimizer_sha256": first["optimizer_sha256"],
            "persistent_memory_sha256": first["persistent_memory_sha256"],
            "segment_losses": first["losses"],
        },
        "integrity": {
            "archive_repeat_byte_identical": archive_repeat,
            "branch_frequency_identity": frequency_identity,
            "decoded_symbol_identity": symbol_identity,
            "complete_state_identity": state_identity,
            "loss_identity": loss_identity,
            "official_nncp_raw_inverse": raw_identity,
            "joint_boundary_exact": True,
            "joint_prefix_arithmetic_decode": True,
            "all_probabilities_legal_nonzero": True,
        },
        "resource": {
            "first_encode_seconds": first["elapsed_seconds"],
            "second_encode_seconds": second["elapsed_seconds"],
            "decode_seconds": decoded["elapsed_seconds"],
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": max(
                first["peak_reserved_bytes"],
                second["peak_reserved_bytes"],
                decoded["peak_reserved_bytes"],
            ),
            "decimal_10gb_allocated_pass": memory_pass,
        },
        "inputs": {
            "preprocessed_sha256": core.sha256(args.preprocessed),
            "symbol_map_sha256": core.sha256(args.symbol_map),
            "nncp_dictionary_sha256": core.sha256(args.nncp_dictionary),
            "nncp_binary_sha256": core.sha256(args.nncp_binary),
            "raw_input_sha256": core.sha256(args.raw_input),
            "wrt_store_sha256": core.sha256(args.wrt_store),
            "wrt_dictionary_sha256": core.sha256(args.wrt_dictionary),
            "joint_p1_sha256": core.sha256(args.joint_p1),
            "q0_decision_sha256": core.sha256(args.q0_decision),
            "script_sha256": core.sha256(Path(__file__).resolve()),
        },
        "decision": {
            "promotion_authorized": promotion,
            "forecast_bytes": 109389323,
            "verified_full_1g_score_bytes": None,
        },
    }
    decision_path = args.output_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-v33-rocm-headroom-q1: {error}", file=sys.stderr)
        raise
