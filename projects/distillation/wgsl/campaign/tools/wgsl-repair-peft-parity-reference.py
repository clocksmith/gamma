#!/usr/bin/env python3
"""Capture deterministic Transformers/PEFT reference evidence for WGSL adapters."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import platform
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_adapter(value: str) -> tuple[int, Path]:
    seed_text, separator, path_text = value.partition("=")
    if not separator or not seed_text.isdigit() or not path_text:
        raise argparse.ArgumentTypeError("--adapter must be seed=/path/to/adapter")
    return int(seed_text), Path(path_text).expanduser().resolve()


def read_jsonl_row(path: Path, row_index: int) -> dict[str, Any]:
    rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if row_index < 0 or row_index >= len(rows):
        raise RuntimeError(f"row index {row_index} is outside {path} ({len(rows)} rows)")
    row = json.loads(rows[row_index])
    if not isinstance(row, dict):
        raise RuntimeError("selected JSONL row must be an object")
    return row


def write_logits(logits: Any, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    values = logits.detach().float().cpu().contiguous().numpy().astype("<f4", copy=False)
    payload = values.tobytes()
    path.write_bytes(payload)
    return {
        "path": str(path),
        "dtype": "float32",
        "elementCount": int(values.size),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def top_k(logits: Any, tokenizer: Any, count: int = 20) -> list[dict[str, Any]]:
    import torch

    values, indices = torch.topk(logits.detach().float(), k=count)
    return [
        {
            "tokenId": int(token_id),
            "logit": float(value),
            "text": tokenizer.decode([int(token_id)], skip_special_tokens=False),
        }
        for value, token_id in zip(values.cpu().tolist(), indices.cpu().tolist())
    ]


def run_inference(
    model: Any,
    tokenizer: Any,
    input_ids: Any,
    attention_mask: Any,
    max_new_tokens: int,
    logits_path: Path,
    *,
    disable_adapter: bool,
) -> dict[str, Any]:
    import torch

    context = model.disable_adapter() if disable_adapter else nullcontext()
    with context, torch.inference_mode():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=False,
        )
        first_logits = outputs.logits[0, -1]
        logits_capture = write_logits(first_logits, logits_path)
        ranked = top_k(first_logits, tokenizer)
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    completion_ids = [int(value) for value in generated[0, input_ids.shape[1] :].tolist()]
    return {
        "logits": logits_capture,
        "topK": ranked,
        "selectedTokenId": ranked[0]["tokenId"],
        "completionTokenIds": completion_ids,
        "completionText": tokenizer.decode(completion_ids, skip_special_tokens=True).strip(),
    }


def load_runtime() -> dict[str, Any]:
    import peft
    import torch
    import transformers
    from peft import PeftModel
    from transformers import AutoModelForMultimodalLM, AutoTokenizer

    if not torch.cuda.is_available() or not getattr(torch.version, "hip", None):
        raise RuntimeError("a qualified ROCm torch runtime is required")
    return {
        "torch": torch,
        "peftModule": peft,
        "transformersModule": transformers,
        "PeftModel": PeftModel,
        "AutoModelForMultimodalLM": AutoModelForMultimodalLM,
        "AutoTokenizer": AutoTokenizer,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--row-index", required=True, type=int)
    parser.add_argument("--adapter", action="append", required=True, type=parse_adapter)
    parser.add_argument("--dtype", required=True, choices=("bfloat16", "float32"))
    parser.add_argument("--max-new-tokens", required=True, type=int)
    parser.add_argument("--logits-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    model_path = args.model.expanduser().resolve()
    dataset_path = args.dataset.expanduser().resolve()
    logits_dir = args.logits_dir.expanduser().resolve()
    output_path = args.out.expanduser().resolve()
    row = read_jsonl_row(dataset_path, args.row_index)
    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise RuntimeError("selected row has no prompt")

    runtime = load_runtime()
    torch = runtime["torch"]
    model_dtype = {
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[args.dtype]
    tokenizer = runtime["AutoTokenizer"].from_pretrained(
        str(model_path),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    input_ids = tokenizer.encode(
        prompt,
        add_special_tokens=True,
        return_tensors="pt",
    ).to("cuda")
    attention_mask = torch.ones_like(input_ids)

    base_model = runtime["AutoModelForMultimodalLM"].from_pretrained(
        str(model_path),
        local_files_only=True,
        trust_remote_code=False,
        dtype=model_dtype,
        low_cpu_mem_usage=True,
    ).to("cuda")
    base_model.eval()
    if hasattr(base_model.config, "use_cache"):
        base_model.config.use_cache = True

    adapters = sorted(args.adapter, key=lambda entry: entry[0])
    first_seed, first_path = adapters[0]
    first_name = f"seed{first_seed}"
    model = runtime["PeftModel"].from_pretrained(
        base_model,
        str(first_path),
        adapter_name=first_name,
        is_trainable=False,
    )
    for seed, adapter_path in adapters[1:]:
        model.load_adapter(str(adapter_path), adapter_name=f"seed{seed}", is_trainable=False)
    model.eval()

    base = run_inference(
        model,
        tokenizer,
        input_ids,
        attention_mask,
        args.max_new_tokens,
        logits_dir / "base.first-token-logits.f32",
        disable_adapter=True,
    )
    adapter_results: list[dict[str, Any]] = []
    for seed, adapter_path in adapters:
        model.set_adapter(f"seed{seed}")
        result = run_inference(
            model,
            tokenizer,
            input_ids,
            attention_mask,
            args.max_new_tokens,
            logits_dir / f"seed{seed}.first-token-logits.f32",
            disable_adapter=False,
        )
        result.update({
            "seed": seed,
            "adapterPath": str(adapter_path),
            "adapterConfigSha256": sha256_file(adapter_path / "adapter_config.json"),
            "adapterWeightsSha256": sha256_file(adapter_path / "adapter_model.safetensors"),
        })
        adapter_results.append(result)

    properties = torch.cuda.get_device_properties(0)
    receipt = {
        "schema": "doppler.wgsl-repair-peft-parity-reference/v1",
        "ok": True,
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "hip": str(torch.version.hip),
            "transformers": runtime["transformersModule"].__version__,
            "transformersModulePath": runtime["transformersModule"].__file__,
            "peft": runtime["peftModule"].__version__,
            "peftModulePath": runtime["peftModule"].__file__,
            "device": torch.cuda.get_device_name(0),
            "deviceTotalMemory": int(properties.total_memory),
            "dtype": args.dtype,
        },
        "model": {
            "path": str(model_path),
            "revision": args.model_revision,
            "configSha256": sha256_file(model_path / "config.json"),
            "tokenizerSha256": sha256_file(model_path / "tokenizer.json"),
        },
        "probe": {
            "datasetPath": str(dataset_path),
            "datasetSha256": sha256_file(dataset_path),
            "rowIndex": args.row_index,
            "rowId": row.get("rowId") or row.get("id"),
            "promptSha256": sha256_text(prompt),
            "promptTokenIds": [int(value) for value in input_ids[0].tolist()],
            "useChatTemplate": False,
            "maxNewTokens": args.max_new_tokens,
        },
        "base": base,
        "adapters": adapter_results,
        "claimBoundary": (
            f"Transformers/PEFT {args.dtype} diagnostic reference evidence only; this does not "
            "select a seed or establish Doppler parity, semantic correctness, or promotion."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
