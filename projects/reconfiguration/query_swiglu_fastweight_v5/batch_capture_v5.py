"""Compare isolated-line serial and padded-batch readout compilation on local Qwen3, CPU only."""
import argparse
import hashlib
import json
import math
import platform
import subprocess
import tempfile
import time
from collections import defaultdict
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

from tasks_v5 import build_tasks


HERE = Path(__file__).resolve().parent


@dataclass
class CaptureInput:
    ids: list[int]
    positions: list[int]


def support_inputs(tokenizer, header, support):
    """Get all answer and stop positions from support text alone, in isolated and table contexts."""
    def encode(text):
        return tokenizer.encode(text, add_special_tokens=False)

    header_ids = encode(header)
    if not support.startswith(header):
        raise ValueError("Support must start with the declared header")
    newline, = encode("\n")
    whole = CaptureInput(header_ids.copy(), [])
    isolated, labels = [], []
    for line in support[len(header):].splitlines(keepends=True):
        prefix, delimiter, _ = line.rpartition(" => ")
        line_ids = encode(line)
        marker_end = encode(prefix + " =>")
        if not delimiter or line_ids[:len(marker_end)] != marker_end or line_ids[-1] != newline:
            raise ValueError(f"Tokenizer changed an answer or newline boundary in {line!r}")
        # The marker predicts the first code token. The last code token predicts the newline.
        offsets = range(len(marker_end) - 1, len(line_ids) - 1)
        line_prompt = header_ids + line_ids[:-1]
        if line_prompt != encode(header + line.removesuffix("\n")):
            raise ValueError("Isolated tokenization differs from the header plus a complete line")
        isolated.append(CaptureInput(line_prompt, [len(header_ids) + p for p in offsets]))
        whole.positions.extend(len(whole.ids) + p for p in offsets)
        labels.extend(line_ids[p + 1] for p in offsets)
        whole.ids.extend(line_ids)
    if whole.ids != encode(support):
        raise ValueError("Line-wise tokenization differs from the complete support table")
    return isolated, whole, labels


def capture(model, lines, batch_size, pad_id):
    """Right-padding and a separate attention mask per line preserve independent causal histories."""
    zs, hs = [], []
    actual, padded = 0, 0
    for begin in range(0, len(lines), batch_size):
        batch = lines[begin:begin + batch_size]
        length = max(len(line.ids) for line in batch)
        ids = torch.full((len(batch), length), pad_id, dtype=torch.long)
        mask = torch.zeros_like(ids)
        owners, positions = [], []
        for i, line in enumerate(batch):
            ids[i, :len(line.ids)] = torch.tensor(line.ids)
            mask[i, :len(line.ids)] = 1
            owners.extend([i] * len(line.positions))
            positions.extend(line.positions)
            actual += len(line.ids)
        padded += ids.numel()
        select = (torch.tensor(owners), torch.tensor(positions))

        def save(target):
            def hook(_module, inputs):
                target.append(inputs[0][select].contiguous())
            return hook

        with ExitStack() as hooks:
            layer = model.model.layers[-1]
            hooks.enter_context(layer.mlp.down_proj.register_forward_pre_hook(save(zs)))
            hooks.enter_context(model.model.norm.register_forward_pre_hook(save(hs)))
            model.model(input_ids=ids, attention_mask=mask, use_cache=False)
    return torch.cat(zs), torch.cat(hs), {"calls": math.ceil(len(lines) / batch_size),
                                          "tokens": actual, "padded_tokens": padded}


def compile_table(model, tokenizer, header, support, batch_size):
    start = time.perf_counter()
    isolated, whole, labels = support_inputs(tokenizer, header, support)
    iso_start = time.perf_counter()
    zi, hi, work = capture(model, isolated, batch_size, tokenizer.eos_token_id)
    iso_s = time.perf_counter() - iso_start
    zc, hc, _ = capture(model, [whole], 1, tokenizer.eos_token_id)
    # Match run_v5's ordering, with the isolated row then its full-table counterpart.
    z = torch.stack((zi, zc), dim=1).flatten(0, 1)
    h = torch.stack((hi, hc), dim=1).flatten(0, 1)
    next_tokens = [token for token in labels for _ in range(2)]
    tokens = sorted(set(labels))
    rms = h.square().mean(1).sqrt().sort().values[len(h) // 2].item()
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        meta = {"nextTokens": next_tokens, "dInter": z.shape[1], "dHidden": h.shape[1],
                "layer": len(model.model.layers) - 1, "hiddenRms": rms}
        (directory / "capture.json").write_text(json.dumps(meta))
        for name, tensor in (("z", z), ("head", model.get_output_embeddings().weight[tokens]),
                             ("norm", model.model.norm.weight)):
            tensor.numpy().astype("<f4", copy=False).tofile(directory / f"{name}.f32")
        subprocess.run(["node", HERE / "compile_readout_files_v5.mjs", directory], check=True)
        a = torch.from_numpy(np.fromfile(directory / "a.f32", "<f4").reshape(z.shape[1], len(tokens)))
        b = torch.from_numpy(np.fromfile(directory / "b.f32", "<f4").reshape(len(tokens), h.shape[1]))
    timing = {**work, "iso_seconds": iso_s, "full_compile_seconds": time.perf_counter() - start,
              "full_table_tokens": len(whole.ids), "fit_rows": len(z), "adapter_bytes": 4 * (a.numel() + b.numel())}
    return (a, b), (zi, hi), timing


def decode(model, tokenizer, prompt, limit, factors=None, first_tokens=None):
    ids = torch.tensor([tokenizer.encode(prompt, add_special_tokens=False)])
    newline, = tokenizer.encode("\n", add_special_tokens=False)
    first_choice = {}
    processors = []
    if first_tokens is not None:
        allowed = torch.tensor(sorted(first_tokens), dtype=torch.long)

        def restrict_first(input_ids, scores):
            if input_ids.shape[1] != ids.shape[1]:
                return scores
            raw = scores[0].argmax().item()
            best = allowed[scores[0, allowed].argmax()].item()
            first_choice.update(raw=raw, best_allowed=best, logit_gap=(scores[0, raw] - scores[0, best]).item())
            masked = torch.full_like(scores, -torch.inf)
            masked[:, allowed] = scores[:, allowed]
            return masked

        processors.append(restrict_first)
    with ExitStack() as hooks:
        if factors is not None:
            a, b = factors
            def write(_module, inputs, output):
                return output + (inputs[0] @ a) @ b
            hooks.enter_context(model.model.layers[-1].mlp.down_proj.register_forward_hook(write))
        # Greedy, full-vocabulary decoding includes the model's own answer termination.
        seq = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=limit,
                             do_sample=False, eos_token_id=[newline, tokenizer.eos_token_id],
                             pad_token_id=tokenizer.eos_token_id, use_cache=True, logits_processor=processors)
    new = seq[0, ids.shape[1]:].tolist()
    answer = tokenizer.decode(new, skip_special_tokens=True).strip().split("\n")[0].strip()
    result = {"tokens": new, "answer": answer}
    if first_tokens is not None:
        result["first_choice"] = first_choice
    return result


def error(actual, reference):
    delta = actual - reference
    return {"relative_l2": (delta.norm() / reference.norm().clamp_min(1e-12)).item(),
            "max_abs": delta.abs().max().item()}


def sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=1104)
    parser.add_argument("--tables", type=int, default=2)
    parser.add_argument("--shots", type=int, default=3)
    parser.add_argument("--queries", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--first-token-control", action="store_true",
                        help="Also decode both the base and readout with the first token restricted to support code starts")
    args = parser.parse_args()
    if min(args.tables, args.shots, args.queries, args.threads) < 1 or args.batch_size < 2:
        parser.error("Counts must be positive and the batch size must be at least two")
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False,
                                              fix_mistral_regex=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, local_files_only=True, trust_remote_code=False,
                                                dtype=torch.float32, attn_implementation="sdpa").cpu().eval()
    if model.config.model_type != "qwen3":
        raise ValueError("This CPU capture targets the Qwen3 pre-norm down projection")
    tables = defaultdict(list)
    for task in build_tasks(args.seed, "dev", args.tables, args.shots, args.queries):
        tables[task["specialty_id"]].append(task)
    receipt = {"scope": "development CPU capture comparison", "seed": args.seed, "split": "dev",
               "shots": args.shots, "queries_per_group": args.queries, "batch_size": args.batch_size,
               "model": args.model.name, "torch": str(torch.__version__), "transformers": transformers.__version__,
               "platform": platform.platform(), "python": platform.python_version(), "device": "cpu",
               "dtype": "float32", "threads": args.threads, "torch_interop_threads": 1,
               "first_token_control": args.first_token_control,
               "source_sha256": {f: sha256(HERE / f) for f in ("batch_capture_v5.py", "tasks_v5.py",
                                  "compile_readout_files_v5.mjs", "readout_adapter_v5.mjs")},
               "model_file_sha256": {f.name: sha256(f) for f in sorted(args.model.iterdir())
                                     if f.suffix == ".safetensors" or f.name in {"config.json", "tokenizer.json",
                                     "tokenizer_config.json", "generation_config.json"}},
               "tables": []}
    # Warm the model before timing. Alternate which method runs first across tables.
    for i, (name, tasks) in enumerate(tables.items()):
        header, support = tasks[0]["header_text"], tasks[0]["support_text"]
        isolated, _, _ = support_inputs(tokenizer, header, support)
        first_tokens = sorted({line.ids[line.positions[0] + 1] for line in isolated})
        if i == 0:
            capture(model, isolated[:args.batch_size], args.batch_size, tokenizer.eos_token_id)
            capture(model, isolated[:1], 1, tokenizer.eos_token_id)
        factors, activations, timing = {}, {}, {}
        for arm in (("serial", "batch") if i % 2 == 0 else ("batch", "serial")):
            factors[arm], activations[arm], timing[arm] = compile_table(
                model, tokenizer, header, support, 1 if arm == "serial" else args.batch_size)
        diff = {key: error(b, s) for key, b, s in zip(("z", "h", "a", "b"),
                activations["batch"] + factors["batch"], activations["serial"] + factors["serial"])}
        answers = []
        for q in tasks:
            base = decode(model, tokenizer, q["prompt"], q["max_new_tokens"])
            bare = {arm: decode(model, tokenizer, q["bare_prompt"], q["max_new_tokens"], factors[arm])
                    for arm in ("serial", "batch")}
            row = {"task_id": q["task_id"], "expected": q["expected"], "base_table": base, **bare}
            if args.first_token_control:
                row["base_table_first"] = decode(model, tokenizer, q["prompt"], q["max_new_tokens"],
                                                 first_tokens=first_tokens)
                row["batch_first"] = decode(model, tokenizer, q["bare_prompt"], q["max_new_tokens"],
                                            factors["batch"], first_tokens)
                for arm in ("base_table", "batch"):
                    first = row[arm + "_first"]
                    raw = row[arm]["tokens"]
                    if first["first_choice"]["raw"] != raw[0] or first["tokens"][0] not in first_tokens:
                        raise ValueError("First-token control differs before restriction or emitted an invalid start")
                    if raw[0] in first_tokens and first["tokens"] != raw:
                        raise ValueError("The control changed a decode whose first token was already allowed")
            answers.append(row)
        passed = (max(diff[k]["relative_l2"] for k in ("z", "h", "a", "b")) <= 1e-4
                  and all(r["serial"]["tokens"] == r["batch"]["tokens"] for r in answers))
        arms = ["base_table", "serial", "batch"]
        if args.first_token_control:
            arms.extend(("base_table_first", "batch_first"))
        correct = {arm: sum(row[arm]["answer"] == row["expected"] for row in answers) for arm in arms}
        receipt["tables"].append({"specialty_id": name, "timing": timing, "error": diff, "answers": answers,
                                  "exact_correct": correct, "codes": tasks[0]["codes"], "support_first_tokens": first_tokens,
                                  "guess_valid_code_rate": 1 / len(tasks[0]["codes"]), "parity_pass": passed})
        print(name, json.dumps(timing), "parity", passed, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    if not all(row["parity_pass"] for row in receipt["tables"]):
        raise SystemExit("Batch parity failed; see receipt")


if __name__ == "__main__":
    main()
