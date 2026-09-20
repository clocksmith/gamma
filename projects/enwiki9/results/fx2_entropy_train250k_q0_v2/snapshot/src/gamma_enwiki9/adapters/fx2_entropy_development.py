"""Bounded CPU development step for the existing full FX2 predictor.

Called by a frozen lab recipe; no corpus or workspace discovery, no downloads.
Training windows deliberately use truncated causal warmup. Only fresh native
replay can validate the resulting checkpoint's full recurrent trajectory.
"""
from __future__ import annotations

import importlib
import json
import math
from pathlib import Path

from .fx2_training_reference import materialize, load_package, load_model
from .fx2_training_capture import validate_rows
from .fx2_weight_training import combined_objective, export_entries, quantized_weight_rate_bits


def train(*, upstream: Path, checkpoint: Path, parent_packed: Path,
          token_path: Path, prior_path: Path, output: Path, plan: dict):
    import numpy as np
    import torch

    torch.set_num_threads(1)
    torch.manual_seed(plan["seed"])
    torch.use_deterministic_algorithms(True)
    if plan["device"] != "cpu" or plan["model_copies"] != 2:
        raise ValueError("this frozen implementation supports CPU and two-copy planning only")
    raw = token_path.read_bytes()
    rows = validate_rows(raw, prior_path.stat().st_size)
    tokens = np.frombuffer(raw[::2], dtype=np.uint8).copy()
    markers = np.frombuffer(raw[1::2], dtype=np.uint8)
    priors = np.memmap(prior_path, dtype="<f2", mode="r", shape=(len(tokens), 205))
    if not np.isfinite(priors).all() or (priors < 0).any():
        raise ValueError("invalid native prior rows")
    warmup, predicted = plan["warmup_tokens"], plan["loss_tokens"]
    length = warmup + predicted
    windows = []
    for start in plan["window_starts"]:
        end = start + length
        if start < 0 or end >= len(tokens) or 2 in markers[start:end] or 1 in markers[start + 1:end + 1]:
            raise ValueError(f"frozen training window crosses a native reset or EOF: {start}")
        windows.append((start, end))
    if not windows or plan["steps"] <= 0 or plan["steps"] > 32:
        raise ValueError("development budget differs")
    output.mkdir(parents=True, exist_ok=False)
    adapted = output / "reference"
    adaptation = materialize(upstream, adapted)
    package = load_package(adapted)
    model = load_model(package, checkpoint)
    packed = importlib.import_module(package + ".weights_compress")
    template = packed.read_tensor_file_v2(str(parent_packed))
    parent_entries = export_entries(model, template, package)
    if any(not np.array_equal(a, template[n][1]) for n, _, a in parent_entries):
        raise ValueError("checkpoint is not the native parent before training")
    initial = {n: p.detach().clone() for n, p in model.named_parameters()}
    optimizer = torch.optim.AdamW(model.parameters(), lr=plan["learning_rate"],
                                  betas=(.9, .999), eps=1e-8, weight_decay=0.)
    history = []
    with (output / "metrics.jsonl").open("x") as metrics:
        for step in range(plan["steps"]):
            start, end = windows[step % len(windows)]
            inputs = torch.from_numpy(tokens[start:end].astype(np.int64)).reshape(1, -1)
            targets = torch.from_numpy(tokens[start + 1:end + 1].astype(np.int64))
            prior = torch.from_numpy(priors[start:end].astype(np.float32)).unsqueeze(0)
            bounds = torch.tensor([[0, length]], dtype=torch.int32)
            optimizer.zero_grad(set_to_none=True)
            logits = model.compute_logits(inputs, prior, bounds)
            data_bits = torch.nn.functional.cross_entropy(
                logits[0, warmup:], targets[warmup:]) / math.log(2)
            rate = quantized_weight_rate_bits(model)
            objective = combined_objective(data_bits, rate, model_copies=plan["model_copies"],
                                            represented_symbols=plan["represented_symbols"])
            if not torch.isfinite(objective):
                raise ValueError("nonfinite training objective")
            objective.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
            if any(not torch.isfinite(p).all() for p in model.parameters()):
                raise ValueError("nonfinite checkpoint")
            row = {"step": step + 1, "window": [start, end], "loss_tokens": predicted,
                   "data_bits_per_token": data_bits.item(), "weight_surrogate_bits": rate.item(),
                   "combined_surrogate": objective.item(), "gradient_norm": gradient_norm.item()}
            metrics.write(json.dumps(row, sort_keys=True) + "\n")
            metrics.flush()
            print(json.dumps(row, sort_keys=True), flush=True)
            history.append(row)
    changed = [n for n, p in model.named_parameters() if not torch.equal(p, initial[n])]
    if not any(n.startswith("blocks.") and n.endswith(".weight") for n in changed):
        raise ValueError("training did not change the hidden representation")
    torch.save(model.state_dict(), output / "checkpoint.tch")
    entries = export_entries(model, template, package)
    changed_native = [n for n, _, a in entries if not np.array_equal(a, template[n][1])]
    if not changed_native:
        raise ValueError("training changed no exported native tensors")
    destination = output / "weights.tfwc2"
    packed.write_tensor_file_v2(str(destination), entries)
    decoded = packed.read_tensor_file_v2(str(destination))
    if any(k != decoded[n][0] or not np.array_equal(a, decoded[n][1]) for n, k, a in entries):
        raise ValueError("trained weight container did not invert exactly")
    receipt = {"schema": "gamma.enwiki9.fx2-entropy-training.v1", "plan": plan,
               "runtime": {"python": __import__("sys").version, "torch": torch.__version__,
                           "device": "cpu", "profile": adaptation["profile"]},
               "native_capture": rows, "changed_parameters": changed,
               "changed_native_tensors": changed_native, "packed_bytes": destination.stat().st_size,
               "parent_packed_bytes": parent_packed.stat().st_size,
               "steps": len(history), "training_loss_tokens": len(history) * predicted,
               "native_archive_status": "not_run", "objective_credit_bytes": 0}
    (output / "training.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
