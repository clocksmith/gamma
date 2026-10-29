#!/usr/bin/env python3
"""Capture deterministic Transformers/PEFT completions for WGSL writer candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
from contextlib import nullcontext
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_tree(root: Path) -> str:
    entries = [
        {
            "path": str(candidate.relative_to(root)),
            "sha256": sha256_file(candidate),
        }
        for candidate in sorted(root.rglob("*"))
        if candidate.is_file()
    ]
    if not entries:
        raise RuntimeError(f"adapter contains no files: {root}")
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return sha256_text(payload)


def parse_adapter(value: str) -> tuple[int, Path]:
    seed_text, separator, path_text = value.partition("=")
    if not separator or not seed_text.isdigit() or not path_text:
        raise argparse.ArgumentTypeError("--adapter must be seed=/path/to/adapter")
    path = Path(path_text).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"adapter directory does not exist: {path}")
    return int(seed_text), path


def parse_candidate(value: str) -> tuple[str, Path]:
    candidate_id, separator, path_text = value.partition("=")
    if not separator or not candidate_id or not path_text:
        raise argparse.ArgumentTypeError("--candidate must be id=/path/to/adapter")
    path = Path(path_text).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"adapter directory does not exist: {path}")
    return candidate_id, path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise RuntimeError(f"{path}:{line_number} must be an object")
        task_id = row.get("taskId") or row.get("rowId") or row.get("id")
        prompt = row.get("prompt")
        if not isinstance(task_id, str) or not task_id:
            raise RuntimeError(f"{path}:{line_number} has no taskId")
        if not isinstance(prompt, str) or not prompt:
            raise RuntimeError(f"{path}:{line_number} has no prompt")
        if row.get("promptSha256") not in {None, sha256_text(prompt)}:
            raise RuntimeError(f"{path}:{line_number} prompt hash mismatch")
        rows.append({"taskId": task_id, "prompt": prompt})
    if not rows:
        raise RuntimeError(f"{path} contains no rows")
    return rows


def load_runtime() -> dict[str, Any]:
    import peft
    import torch
    import transformers
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    try:
        from transformers import AutoModelForMultimodalLM
    except ImportError:
        AutoModelForMultimodalLM = None
    if not torch.cuda.is_available() or not getattr(torch.version, "hip", None):
        raise RuntimeError("a qualified ROCm torch runtime is required")
    version = tuple(int(part) for part in transformers.__version__.split(".")[:3])
    if version < (5, 13, 1):
        raise RuntimeError(
            f"transformers>=5.13.1 is required; found {transformers.__version__}"
        )
    return {
        "torch": torch,
        "peftModule": peft,
        "transformersModule": transformers,
        "PeftModel": PeftModel,
        "AutoModelForCausalLM": AutoModelForCausalLM,
        "AutoModelForMultimodalLM": AutoModelForMultimodalLM,
        "AutoTokenizer": AutoTokenizer,
    }


def load_base_model(model_path: Path, runtime: dict[str, Any], dtype: Any) -> Any:
    classes = [runtime["AutoModelForMultimodalLM"], runtime["AutoModelForCausalLM"]]
    errors: list[str] = []
    for model_class in classes:
        if model_class is None:
            continue
        try:
            model = model_class.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=False,
                dtype=dtype,
                low_cpu_mem_usage=True,
            ).to("cuda")
            model.eval()
            if hasattr(model.config, "use_cache"):
                model.config.use_cache = True
            return model
        except Exception as error:  # pragma: no cover - backend diagnostics
            errors.append(f"{model_class.__name__}: {error}")
    raise RuntimeError("unable to load model: " + " | ".join(errors))


def load_adapters(base_model: Any, adapters: list[tuple[int, Path]], runtime: dict[str, Any]) -> Any:
    first_seed, first_path = adapters[0]
    model = runtime["PeftModel"].from_pretrained(
        base_model,
        str(first_path),
        adapter_name=f"seed{first_seed}",
        is_trainable=False,
    )
    for seed, adapter_path in adapters[1:]:
        model.load_adapter(
            str(adapter_path),
            adapter_name=f"seed{seed}",
            is_trainable=False,
        )
    model.eval()
    return model


def top_k(logits: Any, tokenizer: Any, count: int) -> list[dict[str, Any]]:
    values, indices = logits.detach().float().topk(count)
    return [
        {
            "tokenId": int(token_id),
            "logit": float(value),
            "text": tokenizer.decode([int(token_id)], skip_special_tokens=False),
        }
        for value, token_id in zip(values.cpu().tolist(), indices.cpu().tolist())
    ]


def run_prompt(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int,
    torch: Any,
) -> dict[str, Any]:
    input_ids = tokenizer.encode(
        prompt,
        add_special_tokens=True,
        return_tensors="pt",
    ).to("cuda")
    attention_mask = torch.ones_like(input_ids)
    with torch.inference_mode():
        first_logits = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=False,
        ).logits[0, -1]
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
    completion = tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
    eos_ids = tokenizer.eos_token_id
    if not isinstance(eos_ids, (list, tuple, set)):
        eos_ids = [eos_ids]
    return {
        "promptTokenIds": [int(value) for value in input_ids[0].tolist()],
        "completionTokenIds": completion_ids,
        "completion": completion,
        "completionSha256": sha256_text(completion),
        "completionCharacterCount": len(completion),
        "selectedTokenId": int(first_logits.argmax().item()),
        "topK": top_k(first_logits, tokenizer, 20),
        "stopReason": "eos" if any(token in eos_ids for token in completion_ids) else "length",
    }


def run_prompts(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
    max_new_tokens: int,
    torch: Any,
) -> list[dict[str, Any]]:
    if len(prompts) == 1:
        return [run_prompt(model, tokenizer, prompts[0], max_new_tokens, torch)]
    previous_padding_side = tokenizer.padding_side
    tokenizer.padding_side = "left"
    try:
        inputs = tokenizer(
            prompts,
            add_special_tokens=True,
            padding=True,
            return_tensors="pt",
        ).to("cuda")
    finally:
        tokenizer.padding_side = previous_padding_side
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    with torch.inference_mode():
        first_logits = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=False,
        ).logits[:, -1]
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    eos_ids = tokenizer.eos_token_id
    if not isinstance(eos_ids, (list, tuple, set)):
        eos_ids = [eos_ids]
    eos_ids = set(eos_ids)
    results: list[dict[str, Any]] = []
    input_width = input_ids.shape[1]
    for index in range(len(prompts)):
        prompt_ids = input_ids[index][attention_mask[index].bool()].tolist()
        completion_ids = [int(value) for value in generated[index, input_width:].tolist()]
        first_eos = next(
            (offset for offset, token_id in enumerate(completion_ids) if token_id in eos_ids),
            None,
        )
        if first_eos is not None:
            completion_ids = completion_ids[: first_eos + 1]
        completion = tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
        results.append({
            "promptTokenIds": [int(value) for value in prompt_ids],
            "completionTokenIds": completion_ids,
            "completion": completion,
            "completionSha256": sha256_text(completion),
            "completionCharacterCount": len(completion),
            "selectedTokenId": int(first_logits[index].argmax().item()),
            "topK": top_k(first_logits[index], tokenizer, 20),
            "stopReason": "eos" if first_eos is not None else "length",
        })
    return results


def evaluate_candidates(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    adapters: list[tuple[int, Path]],
    max_new_tokens: int,
    batch_size: int,
    torch: Any,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for seed, adapter_path in adapters:
        model.set_adapter(f"seed{seed}")
        tasks = []
        completions = {}
        for offset in range(0, len(rows), batch_size):
            batch = rows[offset : offset + batch_size]
            print(
                f"seed {seed}: tasks {offset + 1}-{offset + len(batch)}/{len(rows)}",
                flush=True,
            )
            results = run_prompts(
                model,
                tokenizer,
                [row["prompt"] for row in batch],
                max_new_tokens,
                torch,
            )
            for row, result in zip(batch, results):
                completions[row["taskId"]] = result["completion"]
                tasks.append({
                    "taskId": row["taskId"],
                    "promptSha256": sha256_text(row["prompt"]),
                    **result,
                })
        candidates.append({
            "seed": seed,
            "adapterPath": str(adapter_path),
            "adapterTreeSha256": hash_tree(adapter_path),
            "adapterConfigSha256": sha256_file(adapter_path / "adapter_config.json"),
            "adapterWeightsSha256": sha256_file(adapter_path / "adapter_model.safetensors"),
            "completions": completions,
            "tasks": tasks,
        })
    return candidates


def evaluate_named_candidates(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    candidates: list[tuple[str, Path | None]],
    max_new_tokens: int,
    batch_size: int,
    torch: Any,
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for candidate_id, adapter_path in candidates:
        context = nullcontext()
        if adapter_path is None:
            context = model.disable_adapter() if hasattr(model, "disable_adapter") else nullcontext()
        else:
            model.set_adapter(candidate_id)
        tasks = []
        completions = {}
        with context:
            for offset in range(0, len(rows), batch_size):
                batch = rows[offset : offset + batch_size]
                print(
                    f"candidate {candidate_id}: tasks "
                    f"{offset + 1}-{offset + len(batch)}/{len(rows)}",
                    flush=True,
                )
                results = run_prompts(
                    model,
                    tokenizer,
                    [row["prompt"] for row in batch],
                    max_new_tokens,
                    torch,
                )
                for row, result in zip(batch, results):
                    completions[row["taskId"]] = result["completion"]
                    tasks.append({
                        "taskId": row["taskId"],
                        "promptSha256": sha256_text(row["prompt"]),
                        **result,
                    })
        receipts.append({
            "candidateId": candidate_id,
            "adapterPath": str(adapter_path) if adapter_path else None,
            "adapterTreeSha256": hash_tree(adapter_path) if adapter_path else None,
            "adapterConfigSha256": (
                sha256_file(adapter_path / "adapter_config.json") if adapter_path else None
            ),
            "adapterWeightsSha256": (
                sha256_file(adapter_path / "adapter_model.safetensors") if adapter_path else None
            ),
            "completions": completions,
            "tasks": tasks,
        })
    return receipts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--adapter", action="append", required=True, type=parse_adapter)
    parser.add_argument("--candidate", action="append", type=parse_candidate, default=[])
    parser.add_argument("--base-candidate", action="append", default=[])
    parser.add_argument("--experiment-id", default="doppler-wgsl-writer-v2")
    parser.add_argument("--dtype", required=True, choices=("bfloat16", "float32"))
    parser.add_argument("--max-new-tokens", required=True, type=int)
    parser.add_argument("--batch-size", default=1, type=int)
    parser.add_argument("--evaluation-role", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.batch_size < 1:
        raise RuntimeError("--batch-size must be >= 1")

    model_path = args.model.expanduser().resolve()
    dataset_path = args.dataset.expanduser().resolve()
    output_path = args.out.expanduser().resolve()
    adapters = sorted(args.adapter, key=lambda entry: entry[0])
    if len({seed for seed, _ in adapters}) != len(adapters):
        raise RuntimeError("adapter seeds must be unique")
    rows = read_jsonl(dataset_path)
    runtime = load_runtime()
    torch = runtime["torch"]
    dtype = {"bfloat16": torch.bfloat16, "float32": torch.float32}[args.dtype]
    tokenizer = runtime["AutoTokenizer"].from_pretrained(
        str(model_path),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = load_base_model(model_path, runtime, dtype)
    model = load_adapters(base_model, adapters, runtime)
    if args.candidate or args.base_candidate:
        named_adapters = list(args.candidate)
        existing_names = {name for name, _ in named_adapters}
        if len(existing_names) != len(named_adapters):
            raise RuntimeError("named candidate ids must be unique")
        for candidate_id, adapter_path in named_adapters:
            model.load_adapter(
                str(adapter_path),
                adapter_name=candidate_id,
                is_trainable=False,
            )
        named_candidates = [
            *((candidate_id, None) for candidate_id in args.base_candidate),
            *named_adapters,
        ]
        candidates = evaluate_named_candidates(
            model,
            tokenizer,
            rows,
            named_candidates,
            args.max_new_tokens,
            args.batch_size,
            torch,
        )
    else:
        candidates = evaluate_candidates(
            model,
            tokenizer,
            rows,
            adapters,
            args.max_new_tokens,
            args.batch_size,
            torch,
        )
    properties = torch.cuda.get_device_properties(0)
    receipt = {
        "schema": "doppler.wgsl-writer-peft-reference/v1",
        "experimentId": args.experiment_id,
        "evaluationRole": args.evaluation_role,
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
        "dataset": {
            "path": str(dataset_path),
            "sha256": sha256_file(dataset_path),
            "rows": len(rows),
        },
        "generation": {
            "mode": "greedy",
            "useChatTemplate": False,
            "maxNewTokens": args.max_new_tokens,
            "batchSize": args.batch_size,
        },
        "candidates": candidates,
        "claimBoundary": (
            "Deterministic Transformers/PEFT development evidence for the declared writer "
            "population only; semantic dispatch decides capability and this cannot promote."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
