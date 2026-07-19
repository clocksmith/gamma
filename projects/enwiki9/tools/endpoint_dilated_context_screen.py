#!/usr/bin/env python3
"""Screen a small causal dilated-byte residual model over a paired fast endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from endpoint_sparse_gru_distill_screen import (
    TARGET_DEBT_BYTES,
    exact_payload,
    load_inputs,
    prefix_contexts,
    qbits,
)


LAGS = (1, 2, 4, 8, 16, 32, 64)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lagged_bytes(values: np.ndarray) -> np.ndarray:
    result = np.zeros((len(values), len(LAGS)), dtype=np.int64)
    for column, lag in enumerate(LAGS):
        result[lag:, column] = values[:-lag]
    return result


class DilatedContextModel(nn.Module):
    def __init__(self, embedding_dims: int, hidden_dims: int) -> None:
        super().__init__()
        self.embeddings = nn.ModuleList(
            nn.Embedding(256, embedding_dims) for _ in LAGS
        )
        self.projection = nn.Linear(len(LAGS) * embedding_dims, hidden_dims)
        self.context_head = nn.Embedding(256, hidden_dims)
        self.context_bias = nn.Embedding(256, 1)
        nn.init.zeros_(self.context_head.weight)
        nn.init.zeros_(self.context_bias.weight)

    def forward(
        self,
        lags: torch.Tensor,
        base_logits: torch.Tensor,
        contexts: torch.Tensor,
    ) -> torch.Tensor:
        embedded = torch.cat(
            [embedding(lags[:, index]) for index, embedding in enumerate(self.embeddings)],
            dim=-1,
        )
        state = torch.tanh(self.projection(embedded))
        heads = self.context_head(contexts)
        correction = (heads * state.unsqueeze(1)).sum(dim=-1) / math.sqrt(state.shape[-1])
        correction = correction + self.context_bias(contexts).squeeze(-1)
        return base_logits + correction


def predict(
    model: DilatedContextModel,
    lags: np.ndarray,
    base_logits: np.ndarray,
    contexts: np.ndarray,
    batch_size: int,
) -> np.ndarray:
    model.eval()
    output: list[np.ndarray] = []
    with torch.no_grad():
        for lo in range(0, len(lags), batch_size):
            hi = min(len(lags), lo + batch_size)
            logits = model(
                torch.from_numpy(lags[lo:hi]),
                torch.from_numpy(base_logits[lo:hi]),
                torch.from_numpy(contexts[lo:hi]),
            )
            probability = torch.sigmoid(logits).mul(65536).round().clamp(1, 65535)
            output.append(probability.to(torch.int32).numpy().astype("<u2"))
    return np.concatenate(output, axis=0)


def metrics(
    name: str,
    lo: int,
    hi: int,
    source_scope_bytes: int,
    values: np.ndarray,
    base: np.ndarray,
    candidate: np.ndarray,
) -> dict[str, Any]:
    raw_equivalent = source_scope_bytes * (hi - lo) / len(values)
    base_qbits = qbits(base[lo:hi], values[lo:hi])
    candidate_qbits = qbits(candidate[lo:hi], values[lo:hi])
    gain = (base_qbits - candidate_qbits) / 2048.0
    return {
        "split": name,
        "wrt_bytes": hi - lo,
        "source_equivalent_bytes": raw_equivalent,
        "base_qbits": base_qbits,
        "candidate_qbits": candidate_qbits,
        "candidate_gain_bytes": gain,
        "candidate_gain_bytes_per_million": gain / raw_equivalent * 1_000_000.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair-trace", type=Path, required=True)
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-scope-bytes", type=int, required=True)
    parser.add_argument("--embedding-dims", type=int, default=4)
    parser.add_argument("--hidden-dims", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--learning-rate", type=float, default=0.003)
    parser.add_argument("--seed", type=int, default=20260719)
    args = parser.parse_args()

    print(f"python={Path(torch.__file__).resolve()} torch={torch.__version__}")
    print(f"torch.cuda.is_available()={torch.cuda.is_available()}")
    print(f"torch.cuda.device_count()={torch.cuda.device_count()} DEVICE=cpu")
    print(
        "[run-contract] run_name=endpoint_dilated_context_screen "
        f"pairs_input_spec={args.pair_trace} resume_from=none resume_stage=none "
        "decode=greedy eval_dataset_paths=contiguous_dev,sealed_contiguous_holdout "
        "device=cpu schedule=truth_bce runtime_mode=cpu sweep_mode=live"
    )
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)

    pair, values = load_inputs(args.pair_trace, args.wrt_store)
    base = pair[:, :, 1]
    base_logits = np.log(base.astype(np.float32) / (65536.0 - base.astype(np.float32)))
    contexts = prefix_contexts(values)
    lags = lagged_bytes(values)
    truth = np.unpackbits(values, bitorder="big").reshape(-1, 8).astype(np.float32)
    train_end = len(values) * 3 // 5
    holdout_start = len(values) * 4 // 5
    dataset = TensorDataset(
        torch.from_numpy(lags[:train_end]),
        torch.from_numpy(base_logits[:train_end]),
        torch.from_numpy(contexts[:train_end]),
        torch.from_numpy(truth[:train_end]),
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(args.seed),
        num_workers=0,
    )
    model = DilatedContextModel(args.embedding_dims, args.hidden_dims)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-5)
    best_development_qbits = float("inf")
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None
    history = []
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        total_bits = 0
        for batch_lags, batch_base, batch_contexts, batch_truth in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_lags, batch_base, batch_contexts)
            loss = nn.functional.binary_cross_entropy_with_logits(logits, batch_truth)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += float(loss.detach()) * batch_truth.numel()
            total_bits += batch_truth.numel()
        candidate = predict(
            model,
            lags[train_end:holdout_start],
            base_logits[train_end:holdout_start],
            contexts[train_end:holdout_start],
            args.batch_size,
        )
        development = metrics(
            "development",
            train_end,
            holdout_start,
            args.source_scope_bytes,
            values,
            base,
            np.concatenate((base[:train_end], candidate), axis=0),
        )
        history.append(
            {
                "epoch": epoch + 1,
                "training_truth_bce": total_loss / total_bits,
                "development_gain_bytes": development["candidate_gain_bytes"],
                "development_gain_bytes_per_million": development[
                    "candidate_gain_bytes_per_million"
                ],
            }
        )
        print(json.dumps(history[-1], sort_keys=True), flush=True)
        if development["candidate_qbits"] < best_development_qbits:
            best_development_qbits = development["candidate_qbits"]
            best_epoch = epoch + 1
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
    if best_state is None:
        raise RuntimeError("training produced no selected checkpoint")
    model.load_state_dict(best_state)
    candidate = predict(model, lags, base_logits, contexts, args.batch_size)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    int8_payload_estimate = parameter_count + len(list(model.parameters())) * 8
    required_gain = (TARGET_DEBT_BYTES + int8_payload_estimate) / 1000.0
    splits = [
        metrics("train", 0, train_end, args.source_scope_bytes, values, base, candidate),
        metrics("development", train_end, holdout_start, args.source_scope_bytes, values, base, candidate),
        metrics("holdout", holdout_start, len(values), args.source_scope_bytes, values, base, candidate),
        metrics("all", 0, len(values), args.source_scope_bytes, values, base, candidate),
    ]
    baseline_payload = exact_payload(base, values)
    candidate_payload = exact_payload(candidate, values)
    gate = (
        splits[2]["candidate_gain_bytes_per_million"] >= required_gain
        and baseline_payload - candidate_payload >= required_gain
    )
    receipt = {
        "schema": "endpoint_dilated_context_screen_v1",
        "evidence_level": "causal_float_shadow",
        "hypothesis": (
            "Explicit power-of-two byte lags retain fast complementary sequence information "
            "that a small recurrent bottleneck and local lookup tables missed."
        ),
        "inputs": {
            "pair_trace": str(args.pair_trace.resolve()),
            "pair_trace_sha256": sha256(args.pair_trace),
            "wrt_store": str(args.wrt_store.resolve()),
            "wrt_store_sha256": sha256(args.wrt_store),
            "base_pair_endpoint": 1,
            "source_scope_bytes": args.source_scope_bytes,
            "wrt_bytes": len(values),
        },
        "implementation": {
            "source": str(Path(__file__).resolve()),
            "source_sha256": sha256(Path(__file__)),
            "torch_version": torch.__version__,
            "device": "cpu",
        },
        "selection": {
            "seed": args.seed,
            "objective": "truth_bce",
            "lags": list(LAGS),
            "train_fraction": 0.6,
            "development_fraction": 0.2,
            "holdout_fraction": 0.2,
            "holdout_reads_during_selection": False,
            "selected_epoch": best_epoch,
            "history": history,
        },
        "model": {
            "embedding_dims": args.embedding_dims,
            "hidden_dims": args.hidden_dims,
            "parameter_count": parameter_count,
            "float_parameter_bytes": parameter_count * 4,
            "estimated_int8_payload_bytes": int8_payload_estimate,
        },
        "economics": {
            "target_debt_bytes": TARGET_DEBT_BYTES,
            "required_gain_before_payload_bytes_per_million": TARGET_DEBT_BYTES / 1000.0,
            "required_gain_with_estimated_int8_payload_bytes_per_million": required_gain,
        },
        "splits": splits,
        "exact_full_scope_replay": {
            "baseline_payload_bytes": baseline_payload,
            "candidate_payload_bytes": candidate_payload,
            "candidate_saved_bytes": baseline_payload - candidate_payload,
        },
        "quantization_gate_passed": gate,
        "promotion_authorized": False,
        "decision": (
            "quantize one frozen model and replay fixed-point causally"
            if gate
            else "retire this dilated-context representation before native integration"
        ),
        "claim_boundary": (
            "Causal float shadow selected without holdout reads. Weights are not quantized or "
            "counted; no constructive archive, native resource, disjoint, or full-corpus claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "quantization_gate_passed": gate}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
