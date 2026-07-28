#!/usr/bin/env python3
"""Single-pass maturity gate for the shifted-input batched ROCm teacher."""

from __future__ import annotations

import argparse
from array import array
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time


ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)


def ensure_rocm() -> None:
    if os.environ.get("NNCP_BATCH_SCALE_REEXEC") == "1":
        return
    environment = os.environ.copy()
    environment["NNCP_BATCH_SCALE_REEXEC"] = "1"
    environment["AMD_SERIALIZE_KERNEL"] = "3"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    ensure_rocm()

    import numpy as np
    import torch
    import torch.nn.functional as F

    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import nncp_rocm_q0_teacher_gate as q0

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preprocessed", required=True, type=Path)
    parser.add_argument("--symbol-map", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--raw-input", required=True, type=Path)
    parser.add_argument("--nncp-binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    if not torch.cuda.is_available() or torch.version.hip is None:
        raise SystemExit("a PyTorch ROCm device is required")
    if args.symbols != 102871:
        raise ValueError("Q1 is frozen at exactly 102,871 symbols")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = q0.Config()
    source = np.memmap(args.preprocessed, mode="r", dtype=">u2")
    symbols = np.asarray(source[: args.symbols], dtype=np.uint16)
    if len(symbols) != args.symbols:
        raise ValueError("preprocessed stream is too short")
    if int(symbols.max()) >= config.vocabulary:
        raise ValueError("symbol exceeds frozen vocabulary")

    torch.use_deterministic_algorithms(True)
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    device = torch.device("cuda")
    torch.cuda.reset_peak_memory_stats(device)
    model = q0.RocmTeacher(config).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        betas=(config.adam_beta1, config.adam_beta2),
        eps=config.adam_epsilon,
    )

    target_a = torch.arange(
        config.segment_length, device=device
    ).remainder(config.vocabulary)
    target_b = target_a.clone()
    target_b[8] = (target_b[8] + 17) % config.vocabulary
    input_a = torch.empty_like(target_a)
    input_b = torch.empty_like(target_b)
    input_a[0] = 0
    input_b[0] = 0
    input_a[1:] = target_a[:-1]
    input_b[1:] = target_b[:-1]
    with torch.no_grad(), torch.autocast(
        device_type="cuda", dtype=torch.bfloat16
    ):
        audit_outputs = []
        for values in (input_a, input_b):
            memories = model.empty_memory(device, torch.bfloat16)
            logits, _ = model(
                values[None, :], memories, detach_memory=False
            )
            audit_outputs.append(logits)
    audit_error = float(
        (audit_outputs[0][:, :9] - audit_outputs[1][:, :9])
        .abs()
        .max()
        .cpu()
    )
    if audit_error != 0.0:
        raise ValueError("shifted batched causal audit failed")

    model.train()
    memories = model.empty_memory(device, torch.bfloat16)
    previous = np.empty_like(symbols)
    previous[0] = 0
    previous[1:] = symbols[:-1]
    encoder = q0.RangeEncoder()
    branch_trace = array("H")
    loss_sum = 0.0
    started = time.monotonic()
    for start in range(0, len(symbols), config.segment_length):
        end = min(start + config.segment_length, len(symbols))
        input_tensor = torch.from_numpy(
            previous[start:end].astype(np.int64, copy=False)
        )[None, :].to(device)
        target_tensor = torch.from_numpy(
            symbols[start:end].astype(np.int64, copy=False)
        )[None, :].to(device)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(
            device_type="cuda", dtype=torch.bfloat16
        ):
            logits, next_memories = model(
                input_tensor, memories, detach_memory=False
            )
            loss = F.cross_entropy(
                logits.reshape(-1, config.vocabulary),
                target_tensor.reshape(-1),
            )
        probability = (
            torch.softmax(logits.detach(), dim=-1)[0].cpu().numpy()
        )
        q0.encode_distribution(
            encoder, probability, symbols[start:end], branch_trace
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(), config.gradient_clip
        )
        optimizer.step()
        memories = [memory.detach() for memory in next_memories]
        loss_sum += float(loss.detach().cpu()) * (end - start)
        if end % 8192 == 0 or end == len(symbols):
            torch.cuda.synchronize(device)
            print(
                json.dumps(
                    {
                        "event": "maturity_checkpoint",
                        "symbols": end,
                        "total_symbols": len(symbols),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    payload = encoder.finish()
    torch.cuda.synchronize(device)
    elapsed = time.monotonic() - started
    decoded = q0.decode_with_trace(
        payload, branch_trace, args.symbols, config.vocabulary
    )
    if not np.array_equal(decoded, symbols):
        raise ValueError("trace-driven symbol reconstruction failed")

    archive_path = args.output_dir / "teacher_payload.bin"
    archive_path.write_bytes(payload)
    trace_path = args.output_dir / "teacher_branch_trace.bin"
    q0.write_trace(trace_path, branch_trace, args.symbols)
    decoded_path = args.output_dir / "decoded_symbols.bin"
    decoded.astype(">u2").tofile(decoded_path)

    mapped = np.memmap(
        args.symbol_map,
        mode="r",
        dtype=np.dtype(
            [
                ("raw_start", "<u8"),
                ("raw_end", "<u8"),
                ("symbol", "<u2"),
            ]
        ),
        offset=16,
        shape=(args.symbols,),
    )
    raw_bytes = int(mapped["raw_end"][-1])
    restored = args.output_dir / "restored.raw"
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(args.nncp_binary.parent)
    subprocess.run(
        [
            str(args.nncp_binary),
            "--dict",
            str(args.dictionary),
            "pd",
            str(decoded_path),
            str(restored),
        ],
        check=True,
        env=environment,
    )
    expected = args.raw_input.open("rb").read(raw_bytes)
    if restored.read_bytes() != expected:
        raise ValueError("official inverse differs from raw prefix")

    decision = {
        "schema": "nncp_rocm_batched_teacher_scale_gate_v1",
        "candidate": "nncp_rocm_batched_causal_teacher_v1",
        "status": "PASS",
        "score_credit_bytes": 0,
        "archive": {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "branch_trace": {
            "branches": len(branch_trace),
            "bytes": trace_path.stat().st_size,
            "sha256": sha256(trace_path),
        },
        "causality": {
            "maximum_prefix_error": audit_error,
            "shifted_inputs_only": True,
        },
        "claims": {
            "deterministic_second_archive": False,
            "libnc_parity": False,
            "model_decoder_constructive": False,
            "score_credit": False,
            "trace_driven_arithmetic_roundtrip": True,
        },
        "config": asdict(config),
        "environment": {
            "device": torch.cuda.get_device_name(device),
            "hip": torch.version.hip,
            "python": platform.python_version(),
            "script_sha256": sha256(Path(__file__).resolve()),
            "torch": torch.__version__,
        },
        "input": {
            "dictionary_sha256": sha256(args.dictionary),
            "preprocessed_sha256": sha256(args.preprocessed),
            "raw_prefix_bytes": raw_bytes,
            "raw_prefix_sha256": hashlib.sha256(expected).hexdigest(),
            "symbols": args.symbols,
        },
        "model": {
            "final_fingerprint": q0.model_fingerprint(model),
            "mean_cross_entropy_nats": loss_sum / len(symbols),
            "parameters": sum(
                parameter.numel() for parameter in model.parameters()
            ),
        },
        "resource": {
            "elapsed_seconds": elapsed,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(
                device
            ),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        },
        "roundtrip": {
            "official_raw_inverse": True,
            "symbol_identity": True,
        },
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
