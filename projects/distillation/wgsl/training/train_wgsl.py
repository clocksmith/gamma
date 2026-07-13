#!/usr/bin/env python3
"""ROCm training backend for Doppler's replacement-only WGSL program."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import random
from typing import Any


PROTOCOL = "gamma_wgsl_trainer_json_v1"
SUPPORTED_ACTIONS = {
    "preflight",
    "sft",
    "dpo",
    "rollout",
    "grpo_update",
    "parity_microstep",
}
PARITY_ADAPTER_PATHS = (
    "layers.0.self_attn.q_proj",
    "layers.0.self_attn.k_proj",
    "layers.0.self_attn.v_proj",
    "layers.0.self_attn.o_proj",
    "layers.0.mlp.gate_proj",
    "layers.0.mlp.up_proj",
    "layers.0.mlp.down_proj",
)


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be an object")
    return value


def _require_string(value: Any, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise RuntimeError(f"{label} is required")
    return normalized


def _require_text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{label} must be a string")
    if not allow_empty and not value.strip():
        raise RuntimeError(f"{label} is required")
    return value


def _require_int(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise RuntimeError(f"{label} must be an integer >= {minimum}")
    parsed = int(value)
    if parsed < minimum or parsed != float(value):
        raise RuntimeError(f"{label} must be an integer >= {minimum}")
    return parsed


def _require_float(value: Any, label: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise RuntimeError(f"{label} must be finite")
    return parsed


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise RuntimeError(f"{path}:{line_number} must be a JSON object")
        rows.append(row)
    if not rows:
        raise RuntimeError(f"{path} contains no rows")
    return rows


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _hash_tree(root: Path) -> str:
    entries: list[dict[str, str]] = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        entries.append({"path": str(path.relative_to(root)), "sha256": _sha256_file(path)})
    if not entries:
        raise RuntimeError(f"adapter output has no files: {root}")
    return _sha256_text(_stable_json(entries))


def _version_tuple(value: str) -> tuple[int, ...]:
    head = value.split("+", 1)[0].split("-", 1)[0]
    return tuple(int(part) for part in head.split(".") if part.isdigit())


def _runtime_imports() -> dict[str, Any]:
    try:
        import torch
        import torch.nn.functional as functional
        from huggingface_hub import snapshot_download
        from peft import LoraConfig, TaskType, PeftModel, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
        try:
            from transformers import AutoModelForMultimodalLM
        except ImportError:
            AutoModelForMultimodalLM = None
    except ImportError as exc:
        raise RuntimeError(
            f"missing verifier-training dependency: {exc}; "
            "install requirements/verifier-training.txt after the ROCm torch build"
        ) from exc
    transformers_version = importlib.metadata.version("transformers")
    if _version_tuple(transformers_version) < (5, 13, 1):
        raise RuntimeError(
            f"transformers>=5.13.1 is required for Qwen3.5; found {transformers_version}"
        )
    return {
        "torch": torch,
        "functional": functional,
        "snapshot_download": snapshot_download,
        "LoraConfig": LoraConfig,
        "TaskType": TaskType,
        "PeftModel": PeftModel,
        "get_peft_model": get_peft_model,
        "AutoModelForCausalLM": AutoModelForCausalLM,
        "AutoModelForMultimodalLM": AutoModelForMultimodalLM,
        "AutoTokenizer": AutoTokenizer,
        "transformersVersion": transformers_version,
    }


def _resolve_model_path(model: dict[str, Any], runtime: dict[str, Any]) -> Path:
    local_path = str(model.get("localPath") or "").strip()
    if local_path:
        resolved = Path(local_path).expanduser().resolve()
        if not resolved.is_dir():
            raise RuntimeError(f"model.localPath is not a directory: {resolved}")
        return resolved
    model_id = _require_string(model.get("modelId"), "model.modelId")
    revision = str(model.get("revision") or "main")
    try:
        resolved = runtime["snapshot_download"](
            repo_id=model_id,
            revision=revision,
            local_files_only=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"model_not_provisioned:{model_id}@{revision}; provide model.localPath or a local HF snapshot"
        ) from exc
    return Path(resolved).resolve()


def _dtype_from_name(torch: Any, value: str) -> Any:
    mapping = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    if value not in mapping:
        raise RuntimeError(f"unsupported dtype: {value}")
    return mapping[value]


def _prove_rocm(runtime: dict[str, Any], dtype_name: str) -> dict[str, Any]:
    torch = runtime["torch"]
    if not torch.cuda.is_available():
        raise RuntimeError("rocm_device_unavailable: torch.cuda.is_available() is false")
    if not getattr(torch.version, "hip", None):
        raise RuntimeError("rocm_build_required: torch.version.hip is empty")
    dtype = _dtype_from_name(torch, dtype_name)
    left = torch.randn((256, 256), device="cuda", dtype=dtype)
    right = torch.randn((256, 256), device="cuda", dtype=dtype)
    result = left @ right
    probe = float(result[0, 0].float().item())
    if not math.isfinite(probe):
        raise RuntimeError("rocm_matmul_probe_nonfinite")
    properties = torch.cuda.get_device_properties(0)
    return {
        "torchVersion": torch.__version__,
        "hipVersion": str(torch.version.hip),
        "transformersVersion": runtime["transformersVersion"],
        "deviceName": torch.cuda.get_device_name(0),
        "deviceTotalMemory": int(properties.total_memory),
        "dtype": dtype_name,
        "matmulProbe": probe,
    }


def _load_tokenizer(model_path: Path, runtime: dict[str, Any]) -> Any:
    tokenizer = runtime["AutoTokenizer"].from_pretrained(
        str(model_path),
        local_files_only=True,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            raise RuntimeError("tokenizer requires eos_token_id or pad_token_id")
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def _load_base_model(
    model_path: Path,
    runtime: dict[str, Any],
    dtype_name: str,
    gradient_checkpointing: bool,
) -> Any:
    torch = runtime["torch"]
    dtype = _dtype_from_name(torch, dtype_name)
    classes = [runtime["AutoModelForMultimodalLM"], runtime["AutoModelForCausalLM"]]
    errors: list[str] = []
    model = None
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
            )
            break
        except Exception as exc:
            errors.append(f"{model_class.__name__}: {exc}")
    if model is None:
        raise RuntimeError("unable to load model: " + " | ".join(errors))
    model.to("cuda")
    if hasattr(model.config, "use_cache"):
        model.config.use_cache = False
    if gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
    return model


def _attach_lora(model: Any, adapter: dict[str, Any], runtime: dict[str, Any]) -> Any:
    config = runtime["LoraConfig"](
        task_type=runtime["TaskType"].CAUSAL_LM,
        r=_require_int(adapter.get("rank"), "adapter.rank", 1),
        lora_alpha=_require_int(adapter.get("alpha"), "adapter.alpha", 1),
        lora_dropout=_require_float(adapter.get("dropout"), "adapter.dropout"),
        target_modules=[str(value) for value in adapter.get("targetModules", [])],
        bias="none",
    )
    if not config.target_modules:
        raise RuntimeError("adapter.targetModules must not be empty")
    peft_model = runtime["get_peft_model"](model, config)
    trainable = sum(parameter.numel() for parameter in peft_model.parameters() if parameter.requires_grad)
    if trainable < 1:
        raise RuntimeError("LoRA attached zero trainable parameters")
    return peft_model


def _load_policy(
    request: dict[str, Any],
    runtime: dict[str, Any],
    *,
    for_generation: bool = False,
) -> tuple[Any, Any, Path]:
    model_config = _require_object(request.get("model"), "model")
    training = _require_object(request.get("training"), "training")
    dtype_name = _require_string(training.get("dtype"), "training.dtype")
    policy_mode = str(request.get("policyMode") or "adapter").strip().lower()
    if policy_mode not in {"adapter", "base"}:
        raise RuntimeError("policyMode must be adapter or base")
    adapter_path = str(request.get("adapterPath") or "").strip()
    if policy_mode == "base" and adapter_path:
        raise RuntimeError("policyMode=base cannot be combined with adapterPath")
    model_path = _resolve_model_path(model_config, runtime)
    tokenizer = _load_tokenizer(model_path, runtime)
    model = _load_base_model(
        model_path,
        runtime,
        dtype_name,
        bool(training.get("gradientCheckpointing")) and not for_generation,
    )
    model_config_runtime = getattr(model, "config", None)
    if for_generation and hasattr(model_config_runtime, "use_cache"):
        model_config_runtime.use_cache = True
    if adapter_path:
        model = runtime["PeftModel"].from_pretrained(
            model,
            str(Path(adapter_path).resolve()),
            is_trainable=True,
        )
    elif policy_mode == "adapter":
        model = _attach_lora(model, _require_object(request.get("adapter"), "adapter"), runtime)
    return model, tokenizer, model_path


def _rollout_policy_identity(request: dict[str, Any]) -> tuple[Path | None, str]:
    adapter_path = str(request.get("adapterPath") or "").strip()
    if adapter_path:
        resolved = Path(adapter_path).resolve()
        return resolved, _hash_tree(resolved)
    if str(request.get("policyMode") or "").strip().lower() != "base":
        raise RuntimeError("rollout requires adapterPath or policyMode=base")
    policy_hash = _require_string(request.get("policyHash"), "policyHash").lower()
    if len(policy_hash) != 64 or any(character not in "0123456789abcdef" for character in policy_hash):
        raise RuntimeError("policyHash must be a SHA-256 digest")
    return None, policy_hash


def _row_text(row: dict[str, Any], field: str) -> str:
    aliases = {"prompt": ("prompt", "source"), "completion": ("completion", "target")}
    for key in aliases[field]:
        if isinstance(row.get(key), str) and row[key]:
            return row[key]
    raise RuntimeError(f"dataset row requires {field}")


def _encode_pair(tokenizer: Any, prompt: str, completion: str, max_length: int) -> dict[str, Any]:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
    completion_ids = tokenizer.encode(completion, add_special_tokens=False)
    if tokenizer.eos_token_id is not None:
        completion_ids.append(tokenizer.eos_token_id)
    if len(completion_ids) >= max_length:
        completion_ids = completion_ids[:max_length]
        prompt_ids = []
    else:
        prompt_ids = prompt_ids[-(max_length - len(completion_ids)) :]
    input_ids = prompt_ids + completion_ids
    completion_mask = [0] * len(prompt_ids) + [1] * len(completion_ids)
    labels = [-100] * len(prompt_ids) + completion_ids
    if not any(completion_mask):
        raise RuntimeError("encoded row has zero completion tokens")
    return {
        "inputIds": input_ids,
        "labels": labels,
        "completionMask": completion_mask,
        "completionTokenCount": sum(completion_mask),
    }


def _tensorize(encoded: dict[str, Any], torch: Any) -> dict[str, Any]:
    return {
        "input_ids": torch.tensor([encoded["inputIds"]], dtype=torch.long, device="cuda"),
        "attention_mask": torch.ones((1, len(encoded["inputIds"])), dtype=torch.long, device="cuda"),
        "labels": torch.tensor([encoded["labels"]], dtype=torch.long, device="cuda"),
    }


def _completion_logprobs(model: Any, tensors: dict[str, Any], torch: Any, functional: Any) -> Any:
    return torch.cat(_completion_logprobs_by_row(model, tensors, torch, functional))


def _completion_logprobs_by_row(
    model: Any,
    tensors: dict[str, Any],
    torch: Any,
    functional: Any,
) -> list[Any]:
    outputs = model(input_ids=tensors["input_ids"], attention_mask=tensors["attention_mask"])
    logits = outputs.logits[:, :-1, :].float()
    labels = tensors["labels"][:, 1:]
    mask = labels.ne(-100)
    safe_labels = labels.masked_fill(~mask, 0)
    token_logprobs = functional.log_softmax(logits, dim=-1).gather(
        -1, safe_labels.unsqueeze(-1)
    ).squeeze(-1)
    return [token_logprobs[index][mask[index]] for index in range(token_logprobs.shape[0])]


def _optimizer(model: Any, training: dict[str, Any], torch: Any) -> Any:
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    return torch.optim.AdamW(
        parameters,
        lr=_require_float(training.get("learningRate"), "training.learningRate"),
        weight_decay=_require_float(training.get("weightDecay"), "training.weightDecay"),
    )


def _write_metric(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _save_adapter(model: Any, output_root: Path) -> tuple[Path, str]:
    adapter_path = output_root / "adapter"
    adapter_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_path), safe_serialization=True)
    return adapter_path, _hash_tree(adapter_path)


def _seed_everything(seed: int, runtime: dict[str, Any]) -> None:
    random.seed(seed)
    torch = runtime["torch"]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _order_sft_rows(
    rows: list[dict[str, Any]],
    training: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_order = str(training.get("rowOrder") or "dataset_order").strip()
    if row_order == "dataset_order":
        ordered = list(rows)
    elif row_order == "seed_hash_sorted_v1":
        seed = _require_int(training.get("seed"), "training.seed")
        keyed: list[tuple[str, int, dict[str, Any]]] = []
        for index, row in enumerate(rows):
            row_id = _require_string(
                row.get("rowId") or row.get("taskId") or row.get("id"),
                f"training row {index + 1} identity",
            )
            key = _sha256_text(f"{seed}\0{row_id}")
            keyed.append((key, index, row))
        ordered = [entry[2] for entry in sorted(keyed)]
    else:
        raise RuntimeError(
            "training.rowOrder must be dataset_order or seed_hash_sorted_v1"
        )
    ordered_ids = [
        _require_string(
            row.get("rowId") or row.get("taskId") or row.get("id") or f"index-{index}",
            f"ordered training row {index + 1} identity",
        )
        for index, row in enumerate(ordered)
    ]
    return ordered, {
        "rowOrder": row_order,
        "rowOrderSha256": _sha256_text(_stable_json(ordered_ids)),
    }


def _run_sft(request: dict[str, Any], runtime: dict[str, Any], output_root: Path) -> dict[str, Any]:
    torch = runtime["torch"]
    training = _require_object(request.get("training"), "training")
    rows = _read_jsonl(Path(_require_string(request.get("datasetPath"), "datasetPath")))
    model, tokenizer, model_path = _load_policy(request, runtime)
    model.train()
    optimizer = _optimizer(model, training, torch)
    steps = _require_int(training.get("steps"), "training.steps", 1)
    accumulation = _require_int(training.get("gradientAccumulationSteps"), "training.gradientAccumulationSteps", 1)
    max_length = _require_int(training.get("maxLength"), "training.maxLength", 2)
    max_grad_norm = _require_float(training.get("maxGradNorm"), "training.maxGradNorm")
    seed = _require_int(training.get("seed"), "training.seed")
    rows, row_order_receipt = _order_sft_rows(rows, training)
    _seed_everything(seed, runtime)
    metrics_path = output_root / "metrics.jsonl"
    optimizer.zero_grad(set_to_none=True)
    losses: list[float] = []
    for step in range(steps):
        row = rows[step % len(rows)]
        encoded = _encode_pair(
            tokenizer,
            _row_text(row, "prompt"),
            _row_text(row, "completion"),
            max_length,
        )
        tensors = _tensorize(encoded, torch)
        outputs = model(**tensors)
        loss = outputs.loss / accumulation
        if not torch.isfinite(loss):
            raise RuntimeError(f"nonfinite SFT loss at step {step + 1}")
        loss.backward()
        if (step + 1) % accumulation == 0 or step + 1 == steps:
            grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm).item())
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        else:
            grad_norm = 0.0
        raw_loss = float(loss.detach().item() * accumulation)
        losses.append(raw_loss)
        _write_metric(metrics_path, {
            "step": step + 1,
            "loss": raw_loss,
            "gradNorm": grad_norm,
            "completionTokens": encoded["completionTokenCount"],
        })
    adapter_path, policy_hash = _save_adapter(model, output_root)
    return {
        "modelPath": str(model_path),
        "adapterPath": str(adapter_path),
        "policyHash": policy_hash,
        "checkpointStep": steps,
        "metrics": {
            "loss": losses[-1],
            "meanLoss": sum(losses) / len(losses),
            "steps": steps,
            "datasetRows": len(rows),
            "distinctRowsVisited": min(steps, len(rows)),
            **row_order_receipt,
        },
        "metricsPath": str(metrics_path),
    }


def _parity_tensor_contract(value: Any, label: str) -> dict[str, Any]:
    spec = _require_object(value, label)
    shape_value = spec.get("shape")
    data_value = spec.get("data")
    if not isinstance(shape_value, list) or not shape_value:
        raise RuntimeError(f"{label}.shape must be a non-empty array")
    shape = [
        _require_int(dimension, f"{label}.shape[{index}]", 1)
        for index, dimension in enumerate(shape_value)
    ]
    if not isinstance(data_value, list):
        raise RuntimeError(f"{label}.data must be an array")
    expected = math.prod(shape)
    if len(data_value) != expected:
        raise RuntimeError(
            f"{label}.data length mismatch: expected {expected}, got {len(data_value)}"
        )
    data = [
        _require_float(item, f"{label}.data[{index}]")
        for index, item in enumerate(data_value)
    ]
    return {"shape": shape, "data": data}


def _load_parity_fixture(request: dict[str, Any]) -> tuple[dict[str, Any], Path, str]:
    fixture_path = Path(
        _require_string(request.get("fixturePath"), "fixturePath")
    ).resolve()
    fixture = _require_object(_read_json(fixture_path), "parity fixture")
    if fixture.get("artifactType") != "qwen_sft_backend_parity_fixture":
        raise RuntimeError("parity fixture artifactType mismatch")
    if fixture.get("schemaVersion") != 1:
        raise RuntimeError("parity fixture schemaVersion must be 1")
    precision = _require_object(fixture.get("precisionContract"), "precisionContract")
    if _require_float(precision.get("adapterDropout"), "adapterDropout") != 0:
        raise RuntimeError("parity fixture requires zero adapter dropout")
    adapters = _require_object(fixture.get("adapters"), "adapters")
    if set(adapters) != set(PARITY_ADAPTER_PATHS):
        raise RuntimeError("parity fixture adapter paths do not match the frozen contract")
    return fixture, fixture_path, _sha256_file(fixture_path)


def _parity_torch_tensor(
    value: Any,
    label: str,
    torch: Any,
    *,
    requires_grad: bool = False,
) -> Any:
    contract = _parity_tensor_contract(value, label)
    tensor = torch.tensor(contract["data"], dtype=torch.float32, device="cuda")
    tensor = tensor.reshape(contract["shape"])
    if requires_grad:
        tensor = torch.nn.Parameter(tensor)
    return tensor


def _parity_rms_norm(value: Any, weight: Any, eps: float, torch: Any) -> Any:
    inverse_rms = torch.rsqrt(value.square().mean(dim=-1, keepdim=True) + eps)
    return value * inverse_rms * (1 + weight)


def _parity_projection(
    value: Any,
    weight: Any,
    adapter: dict[str, Any],
) -> Any:
    base = value @ weight.transpose(0, 1)
    return base + ((value @ adapter["A"] @ adapter["B"])
                   * (adapter["alpha"] / adapter["rank"]))


def _parity_partial_rope(
    value: Any,
    cosine: Any,
    sine: Any,
    layer: dict[str, Any],
    torch: Any,
) -> Any:
    head_dim = _require_int(layer.get("headDim"), "layer.headDim", 1)
    rotary_dim = _require_int(layer.get("rotaryDim"), "layer.rotaryDim", 1)
    pair_span = _require_int(layer.get("pairSpanDim"), "layer.pairSpanDim", 1)
    interleaved = layer.get("interleaved") is True
    if rotary_dim % 2 or pair_span % 2 or rotary_dim > head_dim or pair_span > head_dim:
        raise RuntimeError("invalid parity partial-RoPE geometry")
    components = [value[..., index] for index in range(head_dim)]
    for pair in range(rotary_dim // 2):
        first = pair * 2 if interleaved else pair
        second = (pair * 2) + 1 if interleaved else pair + (pair_span // 2)
        first_value = value[..., first]
        second_value = value[..., second]
        pair_cosine = cosine[:, pair].unsqueeze(1)
        pair_sine = sine[:, pair].unsqueeze(1)
        components[first] = (first_value * pair_cosine) - (second_value * pair_sine)
        components[second] = (first_value * pair_sine) + (second_value * pair_cosine)
    return torch.stack(components, dim=-1)


def _parity_values(value: Any) -> list[float]:
    return [float(item) for item in value.detach().float().cpu().reshape(-1).tolist()]


def _run_parity_microstep(
    request: dict[str, Any],
    runtime: dict[str, Any],
    _output_root: Path,
) -> dict[str, Any]:
    torch = runtime["torch"]
    functional = runtime["functional"]
    fixture, _fixture_path, fixture_hash = _load_parity_fixture(request)
    model = _require_object(fixture.get("model"), "fixture.model")
    layer = _require_object(fixture.get("layer"), "fixture.layer")
    optimizer_config = _require_object(fixture.get("optimizer"), "fixture.optimizer")
    if optimizer_config.get("type") != "adamw":
        raise RuntimeError("parity fixture optimizer.type must be adamw")
    if hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "matmul"):
        torch.backends.cuda.matmul.allow_tf32 = False
    if hasattr(torch, "set_float32_matmul_precision"):
        torch.set_float32_matmul_precision("highest")

    frozen_specs = _require_object(fixture.get("frozen"), "fixture.frozen")
    frozen = {
        name: _parity_torch_tensor(spec, f"frozen.{name}", torch)
        for name, spec in frozen_specs.items()
    }
    adapter_specs = _require_object(fixture.get("adapters"), "fixture.adapters")
    adapters: dict[str, dict[str, Any]] = {}
    parameters: dict[str, Any] = {}
    for adapter_path in PARITY_ADAPTER_PATHS:
        adapter_spec = _require_object(
            adapter_specs.get(adapter_path), f"adapters.{adapter_path}"
        )
        rank = _require_int(adapter_spec.get("rank"), f"{adapter_path}.rank", 1)
        alpha = _require_float(adapter_spec.get("alpha"), f"{adapter_path}.alpha")
        pair = {"rank": rank, "alpha": alpha}
        for kind in ("A", "B"):
            parameter = _parity_torch_tensor(
                adapter_spec.get(kind),
                f"adapters.{adapter_path}.{kind}",
                torch,
                requires_grad=True,
            )
            pair[kind] = parameter
            parameters[f"{adapter_path}.lora_{kind}"] = parameter
        if pair["A"].shape[1] != rank or pair["B"].shape[0] != rank:
            raise RuntimeError(f"{adapter_path} does not match rank {rank}")
        adapters[adapter_path] = pair

    token_ids_value = fixture.get("tokenIds")
    targets_value = fixture.get("targets")
    unmasked_value = fixture.get("unmaskedTargets")
    if not all(isinstance(value, list) for value in (token_ids_value, targets_value, unmasked_value)):
        raise RuntimeError("parity fixture tokenIds and targets must be arrays")
    token_ids = torch.tensor(token_ids_value, dtype=torch.long, device="cuda")
    targets = torch.tensor(targets_value, dtype=torch.long, device="cuda")
    unmasked_targets = torch.tensor(unmasked_value, dtype=torch.long, device="cuda")
    num_tokens = _require_int(model.get("numTokens"), "model.numTokens", 1)
    hidden_size = _require_int(model.get("hiddenSize"), "model.hiddenSize", 1)
    intermediate_size = _require_int(
        model.get("intermediateSize"), "model.intermediateSize", 1
    )
    vocab_size = _require_int(model.get("vocabSize"), "model.vocabSize", 2)
    active_tokens = _require_int(
        model.get("activeTokenCount"), "model.activeTokenCount", 1
    )
    if token_ids.numel() != num_tokens or targets.numel() != num_tokens:
        raise RuntimeError("parity token count mismatch")
    if int(targets.ne(-100).sum().item()) != active_tokens:
        raise RuntimeError("parity active-token count mismatch")
    eps = _require_float(model.get("rmsEps"), "model.rmsEps")
    num_heads = _require_int(layer.get("numHeads"), "layer.numHeads", 1)
    num_kv_heads = _require_int(layer.get("numKVHeads"), "layer.numKVHeads", 1)
    head_dim = _require_int(layer.get("headDim"), "layer.headDim", 1)
    if num_heads % num_kv_heads:
        raise RuntimeError("parity numHeads must be divisible by numKVHeads")
    query_size = num_heads * head_dim

    hidden = frozen["embedding"].index_select(0, token_ids)
    input_norm = _parity_rms_norm(hidden, frozen["inputNorm"], eps, torch)
    q_projection = _parity_projection(
        input_norm, frozen["qWeight"], adapters["layers.0.self_attn.q_proj"]
    )
    q_split = q_projection.reshape(num_tokens, num_heads, 2, head_dim)
    query = q_split[:, :, 0, :]
    output_gate = q_split[:, :, 1, :]
    key = _parity_projection(
        input_norm, frozen["kWeight"], adapters["layers.0.self_attn.k_proj"]
    ).reshape(num_tokens, num_kv_heads, head_dim)
    value = _parity_projection(
        input_norm, frozen["vWeight"], adapters["layers.0.self_attn.v_proj"]
    ).reshape(num_tokens, num_kv_heads, head_dim)
    query = _parity_rms_norm(query, frozen["qNorm"], eps, torch)
    key = _parity_rms_norm(key, frozen["kNorm"], eps, torch)
    query = _parity_partial_rope(
        query, frozen["cosine"], frozen["sine"], layer, torch
    )
    key = _parity_partial_rope(
        key, frozen["cosine"], frozen["sine"], layer, torch
    )
    heads_per_kv = num_heads // num_kv_heads
    kv_indices = torch.arange(num_heads, device="cuda") // heads_per_kv
    key_by_head = key[:, kv_indices, :]
    value_by_head = value[:, kv_indices, :]
    scores = torch.einsum("thd,shd->hts", query, key_by_head) / math.sqrt(head_dim)
    causal_mask = torch.triu(
        torch.ones((num_tokens, num_tokens), dtype=torch.bool, device="cuda"),
        diagonal=1,
    )
    probabilities = torch.softmax(scores.masked_fill(causal_mask.unsqueeze(0), -torch.inf), dim=-1)
    attention = torch.einsum("hts,shd->thd", probabilities, value_by_head)
    gated_attention = (attention * torch.sigmoid(output_gate)).reshape(num_tokens, query_size)
    attention_output = _parity_projection(
        gated_attention,
        frozen["oWeight"],
        adapters["layers.0.self_attn.o_proj"],
    )
    normalized_attention = _parity_rms_norm(
        attention_output, frozen["postAttentionNorm"], eps, torch
    )
    post_attention = hidden + normalized_attention
    gate = _parity_projection(
        post_attention, frozen["gateWeight"], adapters["layers.0.mlp.gate_proj"]
    )
    up = _parity_projection(
        post_attention, frozen["upWeight"], adapters["layers.0.mlp.up_proj"]
    )
    activated = functional.silu(gate) * up
    if activated.shape != (num_tokens, intermediate_size):
        raise RuntimeError("parity MLP activation shape mismatch")
    down = _parity_projection(
        activated, frozen["downWeight"], adapters["layers.0.mlp.down_proj"]
    )
    layer_output = post_attention + down
    final_norm = _parity_rms_norm(layer_output, frozen["finalNorm"], eps, torch)
    logits = final_norm @ frozen["lmHead"].transpose(0, 1)
    if logits.shape != (num_tokens, vocab_size):
        raise RuntimeError("parity logits shape mismatch")
    loss = functional.cross_entropy(logits, targets, ignore_index=-100, reduction="mean")
    unmasked_loss = functional.cross_entropy(logits, unmasked_targets, reduction="mean")
    if not torch.isfinite(loss) or not torch.isfinite(unmasked_loss):
        raise RuntimeError("parity loss is non-finite")

    initial = {name: parameter.detach().clone() for name, parameter in parameters.items()}
    optimizer = torch.optim.AdamW(
        list(parameters.values()),
        lr=_require_float(optimizer_config.get("lr"), "optimizer.lr"),
        betas=(
            _require_float(optimizer_config.get("beta1"), "optimizer.beta1"),
            _require_float(optimizer_config.get("beta2"), "optimizer.beta2"),
        ),
        eps=_require_float(optimizer_config.get("eps"), "optimizer.eps"),
        weight_decay=_require_float(
            optimizer_config.get("weightDecay"), "optimizer.weightDecay"
        ),
        foreach=False,
        fused=False,
    )
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradients = {}
    for name, parameter in parameters.items():
        if parameter.grad is None or not torch.isfinite(parameter.grad).all():
            raise RuntimeError(f"parity gradient missing or non-finite for {name}")
        gradients[name] = parameter.grad.detach().clone()
    optimizer.step()

    tensors = {}
    every_parameter_changed = True
    all_gradients_nonzero = True
    for name, parameter in parameters.items():
        state = optimizer.state[parameter]
        gradient = gradients[name]
        every_parameter_changed = every_parameter_changed and bool(
            torch.any(parameter.detach() != initial[name]).item()
        )
        all_gradients_nonzero = all_gradients_nonzero and bool(
            torch.any(gradient != 0).item()
        )
        tensors[name] = {
            "shape": list(parameter.shape),
            "initial": _parity_values(initial[name]),
            "gradient": _parity_values(gradient),
            "parameter": _parity_values(parameter),
            "moment1": _parity_values(state["exp_avg"]),
            "moment2": _parity_values(state["exp_avg_sq"]),
        }
    return {
        "fixtureSha256": fixture_hash,
        "precisionContract": fixture["precisionContract"],
        "rank": next(iter(adapters.values()))["rank"],
        "alpha": next(iter(adapters.values()))["alpha"],
        "activeTokenCount": active_tokens,
        "parameterCount": len(parameters),
        "parameterNames": list(parameters),
        "optimizerStepCount": 1,
        "meanLoss": float(loss.detach().item()),
        "unmaskedMeanLoss": float(unmasked_loss.detach().item()),
        "allGradientsNonzero": all_gradients_nonzero,
        "everyParameterChanged": every_parameter_changed,
        "tensors": tensors,
        "claimBoundary": "Gamma PyTorch/ROCm reference for one tiny rank-32, zero-dropout, token-aligned completion-masked Qwen full-layer microstep; not production Qwen geometry, Hugging Face causal-label shifting, V12 dropout, sustained training, or capability evidence.",
    }


def _sequence_logprob(
    model: Any,
    tokenizer: Any,
    prompt: str,
    completion: str,
    max_length: int,
    runtime: dict[str, Any],
) -> Any:
    torch = runtime["torch"]
    encoded = _encode_pair(tokenizer, prompt, completion, max_length)
    tensors = _tensorize(encoded, torch)
    return _completion_logprobs(
        model, tensors, torch, runtime["functional"]
    ).sum()


def _run_dpo(request: dict[str, Any], runtime: dict[str, Any], output_root: Path) -> dict[str, Any]:
    torch = runtime["torch"]
    functional = runtime["functional"]
    training = _require_object(request.get("training"), "training")
    rows = _read_jsonl(Path(_require_string(request.get("datasetPath"), "datasetPath")))
    input_adapter_path = Path(_require_string(request.get("adapterPath"), "adapterPath")).resolve()
    input_policy_hash = _hash_tree(input_adapter_path)
    model, tokenizer, model_path = _load_policy(request, runtime)
    model.train()
    optimizer = _optimizer(model, training, torch)
    steps = _require_int(training.get("steps"), "training.steps", 1)
    max_length = _require_int(training.get("maxLength"), "training.maxLength", 2)
    beta = _require_float(training.get("beta"), "training.beta")
    max_grad_norm = _require_float(training.get("maxGradNorm"), "training.maxGradNorm")
    _seed_everything(_require_int(training.get("seed"), "training.seed"), runtime)
    metrics_path = output_root / "metrics.jsonl"
    losses: list[float] = []
    prepared_rows = []
    reference_context = (
        model.disable_adapter() if hasattr(model, "disable_adapter") else nullcontext()
    )
    with torch.no_grad(), reference_context:
        for row in rows:
            prompt = _require_text(row.get("prompt"), "DPO row.prompt")
            chosen = _require_text(row.get("chosen"), "DPO row.chosen", allow_empty=True)
            rejected = _require_text(row.get("rejected"), "DPO row.rejected", allow_empty=True)
            prepared_rows.append({
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "chosenReference": float(_sequence_logprob(
                    model, tokenizer, prompt, chosen, max_length, runtime
                ).item()),
                "rejectedReference": float(_sequence_logprob(
                    model, tokenizer, prompt, rejected, max_length, runtime
                ).item()),
            })
    for step in range(steps):
        row = prepared_rows[step % len(prepared_rows)]
        chosen_policy = _sequence_logprob(
            model, tokenizer, row["prompt"], row["chosen"], max_length, runtime
        )
        rejected_policy = _sequence_logprob(
            model, tokenizer, row["prompt"], row["rejected"], max_length, runtime
        )
        chosen_reference = torch.tensor(
            row["chosenReference"], dtype=chosen_policy.dtype, device=chosen_policy.device
        )
        rejected_reference = torch.tensor(
            row["rejectedReference"], dtype=rejected_policy.dtype, device=rejected_policy.device
        )
        margin = (chosen_policy - rejected_policy) - (chosen_reference - rejected_reference)
        loss = -functional.logsigmoid(beta * margin)
        if not torch.isfinite(loss):
            raise RuntimeError(f"nonfinite DPO loss at step {step + 1}")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm).item())
        optimizer.step()
        raw_loss = float(loss.detach().item())
        losses.append(raw_loss)
        _write_metric(metrics_path, {
            "step": step + 1,
            "loss": raw_loss,
            "margin": float(margin.detach().item()),
            "gradNorm": grad_norm,
        })
    adapter_path, policy_hash = _save_adapter(model, output_root)
    return {
        "modelPath": str(model_path),
        "adapterPath": str(adapter_path),
        "inputPolicyHash": input_policy_hash,
        "policyHash": policy_hash,
        "checkpointStep": steps,
        "metrics": {
            "loss": losses[-1],
            "meanLoss": sum(losses) / len(losses),
            "steps": steps,
            "referenceCacheRows": len(prepared_rows),
        },
        "metricsPath": str(metrics_path),
    }


def _sample_completion(
    model: Any,
    tokenizer: Any,
    prompt: str,
    sampling: dict[str, Any],
    runtime: dict[str, Any],
    *,
    include_logprobs: bool = True,
) -> dict[str, Any]:
    torch = runtime["torch"]
    input_ids = tokenizer.encode(prompt, add_special_tokens=True, return_tensors="pt").to("cuda")
    attention_mask = torch.ones_like(input_ids)
    torch.manual_seed(_require_int(sampling.get("seed"), "sampling.seed"))
    torch.cuda.manual_seed_all(_require_int(sampling.get("seed"), "sampling.seed"))
    with torch.no_grad():
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=True,
            temperature=_require_float(sampling.get("temperature"), "sampling.temperature"),
            top_p=_require_float(sampling.get("topP"), "sampling.topP"),
            max_new_tokens=_require_int(sampling.get("maxTokens"), "sampling.maxTokens", 1),
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    sequence = generated[0]
    prompt_length = input_ids.shape[1]
    completion_ids = sequence[prompt_length:]
    result = {
        "prompt": prompt,
        "completion": tokenizer.decode(completion_ids, skip_special_tokens=True),
        "tokenIds": [int(value) for value in sequence.tolist()],
        "completionMask": [0] * prompt_length + [1] * int(completion_ids.numel()),
        "stopReason": "eos" if tokenizer.eos_token_id in completion_ids.tolist() else "length",
    }
    if include_logprobs:
        labels = torch.full_like(sequence, -100).unsqueeze(0)
        labels[:, prompt_length:] = sequence[prompt_length:]
        tensors = {
            "input_ids": sequence.unsqueeze(0),
            "attention_mask": torch.ones((1, sequence.numel()), dtype=torch.long, device="cuda"),
            "labels": labels,
        }
        with torch.no_grad():
            policy_logprobs = _completion_logprobs(
                model, tensors, torch, runtime["functional"]
            )
            if hasattr(model, "disable_adapter"):
                with model.disable_adapter():
                    reference_logprobs = _completion_logprobs(
                        model, tensors, torch, runtime["functional"]
                    )
            else:
                reference_logprobs = policy_logprobs
        result["policyTokenLogprobs"] = [
            float(value) for value in policy_logprobs.cpu().tolist()
        ]
        result["referenceTokenLogprobs"] = [
            float(value) for value in reference_logprobs.cpu().tolist()
        ]
    return result


class _PerRowSeededTopPSampler:
    def __init__(
        self,
        torch: Any,
        seeds: list[int],
        temperature: float,
        top_p: float,
        device: Any,
    ) -> None:
        self.torch = torch
        self.temperature = temperature
        self.top_p = top_p
        self.generators = []
        for seed in seeds:
            generator = torch.Generator(device=device)
            generator.manual_seed(seed)
            self.generators.append(generator)

    def __call__(self, _input_ids: Any, scores: Any) -> Any:
        if scores.shape[0] != len(self.generators):
            raise RuntimeError("per-row sampler batch size changed during generation")
        processed = scores / self.temperature
        sorted_logits, sorted_indices = self.torch.sort(processed, descending=False)
        cumulative_probs = sorted_logits.softmax(dim=-1).cumsum(dim=-1)
        sorted_indices_to_remove = cumulative_probs <= (1 - self.top_p)
        sorted_indices_to_remove[..., -1:] = 0
        indices_to_remove = sorted_indices_to_remove.scatter(
            1,
            sorted_indices,
            sorted_indices_to_remove,
        )
        processed = processed.masked_fill(indices_to_remove, -float("inf"))
        probabilities = processed.softmax(dim=-1)
        selected = self.torch.stack([
            self.torch.multinomial(
                probabilities[row_index],
                num_samples=1,
                generator=generator,
            )
            for row_index, generator in enumerate(self.generators)
        ])
        forced = self.torch.full_like(processed, -float("inf"))
        return forced.scatter(1, selected, 0.0)


def _sample_group_completions(
    model: Any,
    tokenizer: Any,
    prompt: str,
    samplings: list[dict[str, Any]],
    runtime: dict[str, Any],
) -> list[dict[str, Any]]:
    torch = runtime["torch"]
    input_ids = tokenizer.encode(prompt, add_special_tokens=True, return_tensors="pt").to("cuda")
    prompt_length = input_ids.shape[1]
    batch_size = len(samplings)
    batched_input_ids = input_ids.repeat(batch_size, 1)
    attention_mask = torch.ones_like(batched_input_ids)
    seeds = [_require_int(sampling.get("seed"), "sampling.seed") for sampling in samplings]
    temperatures = {
        _require_float(sampling.get("temperature"), "sampling.temperature")
        for sampling in samplings
    }
    top_ps = {
        _require_float(sampling.get("topP"), "sampling.topP")
        for sampling in samplings
    }
    max_tokens = {
        _require_int(sampling.get("maxTokens"), "sampling.maxTokens", 1)
        for sampling in samplings
    }
    if len(temperatures) != 1 or len(top_ps) != 1 or len(max_tokens) != 1:
        raise RuntimeError("grouped rollout samples must share temperature, topP, and maxTokens")
    temperature = temperatures.pop()
    top_p = top_ps.pop()
    if temperature <= 0 or top_p <= 0 or top_p > 1:
        raise RuntimeError("grouped rollout requires temperature > 0 and 0 < topP <= 1")
    sampler = _PerRowSeededTopPSampler(
        torch,
        seeds,
        temperature,
        top_p,
        batched_input_ids.device,
    )
    torch.manual_seed(seeds[0])
    torch.cuda.manual_seed_all(seeds[0])
    with torch.no_grad():
        generated = model.generate(
            input_ids=batched_input_ids,
            attention_mask=attention_mask,
            do_sample=True,
            logits_processor=[sampler],
            max_new_tokens=max_tokens.pop(),
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    eos_token_ids = tokenizer.eos_token_id
    if not isinstance(eos_token_ids, (list, tuple, set)):
        eos_token_ids = [eos_token_ids]
    samples = []
    for row_index in range(batch_size):
        completion_ids = generated[row_index, prompt_length:]
        eos_mask = torch.zeros_like(completion_ids, dtype=torch.bool)
        for eos_token_id in eos_token_ids:
            eos_mask |= completion_ids == int(eos_token_id)
        eos_positions = eos_mask.nonzero(as_tuple=False)
        stopped = eos_positions.numel() > 0
        if stopped:
            completion_ids = completion_ids[: int(eos_positions[0].item()) + 1]
        sequence = torch.cat([input_ids[0], completion_ids])
        samples.append({
            "prompt": prompt,
            "completion": tokenizer.decode(completion_ids, skip_special_tokens=True),
            "tokenIds": [int(value) for value in sequence.tolist()],
            "completionMask": [0] * prompt_length + [1] * int(completion_ids.numel()),
            "stopReason": "eos" if stopped else "length",
        })
    return samples


def _attach_batched_completion_logprobs(
    model: Any,
    tokenizer: Any,
    samples: list[dict[str, Any]],
    runtime: dict[str, Any],
    batch_size: int,
) -> None:
    torch = runtime["torch"]
    functional = runtime["functional"]
    for start in range(0, len(samples), batch_size):
        chunk = samples[start : start + batch_size]
        max_length = max(len(sample["tokenIds"]) for sample in chunk)
        input_ids = torch.full(
            (len(chunk), max_length),
            int(tokenizer.pad_token_id),
            dtype=torch.long,
            device="cuda",
        )
        attention_mask = torch.zeros_like(input_ids)
        labels = torch.full_like(input_ids, -100)
        for row_index, sample in enumerate(chunk):
            token_ids = [int(value) for value in sample["tokenIds"]]
            completion_mask = [int(value) for value in sample["completionMask"]]
            if len(token_ids) != len(completion_mask):
                raise RuntimeError("rollout tokenIds/completionMask length mismatch")
            row_length = len(token_ids)
            input_ids[row_index, :row_length] = torch.tensor(
                token_ids,
                dtype=torch.long,
                device="cuda",
            )
            attention_mask[row_index, :row_length] = 1
            labels[row_index, :row_length] = torch.tensor(
                [token if mask else -100 for token, mask in zip(token_ids, completion_mask)],
                dtype=torch.long,
                device="cuda",
            )
        tensors = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }
        with torch.no_grad():
            policy_rows = _completion_logprobs_by_row(model, tensors, torch, functional)
            policy_values = [
                [float(value) for value in row.cpu().tolist()]
                for row in policy_rows
            ]
            if hasattr(model, "disable_adapter"):
                with model.disable_adapter():
                    reference_rows = _completion_logprobs_by_row(
                        model,
                        tensors,
                        torch,
                        functional,
                    )
                reference_values = [
                    [float(value) for value in row.cpu().tolist()]
                    for row in reference_rows
                ]
            else:
                reference_values = policy_values
        for sample, policy_logprobs, reference_logprobs in zip(
            chunk,
            policy_values,
            reference_values,
        ):
            sample["policyTokenLogprobs"] = policy_logprobs
            sample["referenceTokenLogprobs"] = reference_logprobs


def _prepare_rollout_output(
    output_root: Path,
    state: dict[str, Any],
    tasks: list[dict[str, Any]],
    sampling: dict[str, Any],
    group_size: int,
) -> tuple[Path, list[dict[str, Any]]]:
    state_path = output_root / "rollout-state.json"
    rollout_path = output_root / "raw-rollouts.jsonl"
    if state_path.exists():
        existing_state = _require_object(_read_json(state_path), "rollout state")
        if _stable_json(existing_state) != _stable_json(state):
            raise RuntimeError("stale_rollout: existing rollout state does not match request")
    else:
        if rollout_path.exists():
            raise RuntimeError("stale_rollout: raw rollouts exist without a state receipt")
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if not rollout_path.exists():
        return rollout_path, []
    groups = _read_jsonl(rollout_path)
    if len(groups) > len(tasks):
        raise RuntimeError("stale_rollout: existing rollout has more groups than tasks")
    base_seed = _require_int(sampling.get("seed"), "sampling.seed")
    for task_index, group in enumerate(groups):
        task_id = _require_string(
            tasks[task_index].get("taskId") or tasks[task_index].get("id"),
            "task.taskId",
        )
        if _require_string(group.get("taskId"), "rollout group.taskId") != task_id:
            raise RuntimeError("stale_rollout: existing rollout task order differs")
        samples = group.get("samples")
        if not isinstance(samples, list) or len(samples) != group_size:
            raise RuntimeError("stale_rollout: existing rollout group size differs")
        expected_sampling = {
            **sampling,
            "seed": base_seed + (task_index * group_size),
        }
        if _stable_json(group.get("sampling")) != _stable_json(expected_sampling):
            raise RuntimeError("stale_rollout: existing rollout sampling differs")
    return rollout_path, groups


def _capture_rollout_logprobs(request: dict[str, Any]) -> bool:
    generation = request.get("generation")
    if generation is None:
        return True
    generation = _require_object(generation, "generation")
    value = generation.get("captureLogprobs")
    if value is None:
        return True
    if not isinstance(value, bool):
        raise RuntimeError("generation.captureLogprobs must be a boolean")
    return value


def _run_rollout(request: dict[str, Any], runtime: dict[str, Any], output_root: Path) -> dict[str, Any]:
    dataset_path = Path(_require_string(request.get("datasetPath"), "datasetPath")).resolve()
    tasks = _read_jsonl(dataset_path)
    sampling = _require_object(request.get("sampling"), "sampling")
    group_size = _require_int(sampling.get("groupSize"), "sampling.groupSize", 2)
    base_seed = _require_int(sampling.get("seed"), "sampling.seed")
    if sampling.get("taskLimit") is not None:
        tasks = tasks[: _require_int(sampling.get("taskLimit"), "sampling.taskLimit", 1)]
    adapter_path, policy_hash = _rollout_policy_identity(request)
    capture_logprobs = _capture_rollout_logprobs(request)
    rollout_state = {
        "schemaVersion": 1,
        "model": _require_object(request.get("model"), "model"),
        "policyMode": str(request.get("policyMode") or "adapter").strip().lower(),
        "adapterPath": str(adapter_path) if adapter_path else None,
        "policyHash": policy_hash,
        "datasetPath": str(dataset_path),
        "datasetSha256": _sha256_file(dataset_path),
        "taskCount": len(tasks),
        "sampling": sampling,
        "training": _require_object(request.get("training"), "training"),
        "generation": {
            "useCache": True,
            "gradientCheckpointing": False,
            "sampleBatchSize": group_size,
            "logprobBatchSize": group_size,
            "captureLogprobs": capture_logprobs,
        },
    }
    rollout_path, existing_groups = _prepare_rollout_output(
        output_root,
        rollout_state,
        tasks,
        sampling,
        group_size,
    )
    model_path = _resolve_model_path(rollout_state["model"], runtime)
    if len(existing_groups) == len(tasks):
        rollout_tokens = sum(
            sum(int(value) for value in sample.get("completionMask", []))
            for group in existing_groups
            for sample in group.get("samples", [])
        )
        return {
            "modelPath": str(model_path),
            "adapterPath": str(adapter_path) if adapter_path else None,
            "policyHash": policy_hash,
            "rolloutPath": str(rollout_path),
            "metrics": {
                "tasks": len(tasks),
                "groupSize": group_size,
                "rolloutTokens": rollout_tokens,
                "resumedGroups": len(existing_groups),
            },
        }
    model, tokenizer, model_path = _load_policy(request, runtime, for_generation=True)
    model.eval()
    rollout_tokens = sum(
        sum(int(value) for value in sample.get("completionMask", []))
        for group in existing_groups
        for sample in group.get("samples", [])
    )
    for task_index in range(len(existing_groups), len(tasks)):
        task = tasks[task_index]
        task_id = _require_string(task.get("taskId") or task.get("id"), "task.taskId")
        prompt = _require_string(task.get("prompt"), "task.prompt")
        sample_samplings = [
            {
                **sampling,
                "seed": base_seed + (task_index * group_size) + sample_index,
            }
            for sample_index in range(group_size)
        ]
        samples = _sample_group_completions(
            model,
            tokenizer,
            prompt,
            sample_samplings,
            runtime,
        )
        for sample_index, sample in enumerate(samples):
            sample["sampleId"] = f"{task_id}-sample-{sample_index + 1}"
            rollout_tokens += sum(sample["completionMask"])
        if capture_logprobs:
            _attach_batched_completion_logprobs(
                model,
                tokenizer,
                samples,
                runtime,
                group_size,
            )
        _write_metric(rollout_path, {
            "schemaVersion": 1,
            "taskId": task_id,
            "groupId": f"{task_id}-group-1",
            "sampling": {**sampling, "seed": base_seed + (task_index * group_size)},
            "samples": samples,
        })
    return {
        "modelPath": str(model_path),
        "adapterPath": str(adapter_path) if adapter_path else None,
        "policyHash": policy_hash,
        "rolloutPath": str(rollout_path),
        "metrics": {
            "tasks": len(tasks),
            "groupSize": group_size,
            "rolloutTokens": rollout_tokens,
            "resumedGroups": len(existing_groups),
            "captureLogprobs": capture_logprobs,
        },
    }


def _seed_shuffled_grpo_samples(
    groups: list[dict[str, Any]],
    seed: int,
) -> list[dict[str, Any]]:
    samples = [
        sample
        for group in groups
        for sample in group.get("samples", [])
        if _require_float(sample.get("advantage"), "GRPO sample.advantage") != 0
    ]
    random.Random(seed).shuffle(samples)
    return samples


def _grpo_update_contract(training: dict[str, Any]) -> tuple[int, int]:
    updates_per_rollout_batch = _require_int(
        training.get("updatesPerRolloutBatch"),
        "training.updatesPerRolloutBatch",
        1,
    )
    maximum_stale_policy_updates = _require_int(
        training.get("maximumStalePolicyUpdates"),
        "training.maximumStalePolicyUpdates",
    )
    if updates_per_rollout_batch != 1 or maximum_stale_policy_updates != 0:
        raise RuntimeError(
            "GRPO trainer supports exactly one update per rollout batch and zero stale-policy updates"
        )
    return updates_per_rollout_batch, maximum_stale_policy_updates


def _run_grpo_update(request: dict[str, Any], runtime: dict[str, Any], output_root: Path) -> dict[str, Any]:
    torch = runtime["torch"]
    training = _require_object(request.get("training"), "training")
    groups = _read_jsonl(Path(_require_string(request.get("datasetPath"), "datasetPath")))
    model, tokenizer, model_path = _load_policy(request, runtime)
    del tokenizer
    input_policy_hash = _hash_tree(Path(_require_string(request.get("adapterPath"), "adapterPath")).resolve())
    for group in groups:
        if _require_string(group.get("policyHash"), "rollout group.policyHash") != input_policy_hash:
            raise RuntimeError("stale_policy: rollout policyHash does not match input adapter")
    optimizer = _optimizer(model, training, torch)
    clip_lower = _require_float(training.get("clipLower"), "training.clipLower")
    clip_upper = _require_float(training.get("clipUpper"), "training.clipUpper")
    kl_coefficient = _require_float(training.get("klCoefficient"), "training.klCoefficient")
    max_grad_norm = _require_float(training.get("maxGradNorm"), "training.maxGradNorm")
    steps = _require_int(training.get("steps"), "training.steps", 1)
    updates_per_rollout_batch, maximum_stale_policy_updates = _grpo_update_contract(training)
    training_seed = _require_int(training.get("seed"), "training.seed")
    _seed_everything(training_seed, runtime)
    model.eval()
    metrics_path = output_root / "metrics.jsonl"
    losses: list[float] = []
    samples = _seed_shuffled_grpo_samples(groups, training_seed)
    if not samples:
        raise RuntimeError("GRPO rollout groups contain no nonzero-advantage samples")
    nonzero_advantage_steps = 0
    optimizer.zero_grad(set_to_none=True)
    for step in range(steps):
        sample = samples[step % len(samples)]
        token_ids = [int(value) for value in sample.get("tokenIds", [])]
        completion_mask = [int(value) for value in sample.get("completionMask", [])]
        if len(token_ids) < 2 or len(token_ids) != len(completion_mask):
            raise RuntimeError("GRPO sample tokenIds/completionMask contract failed")
        completion_count = sum(completion_mask[1:])
        old = [float(value) for value in sample.get("policyTokenLogprobs", [])]
        reference = [float(value) for value in sample.get("referenceTokenLogprobs", [])]
        if len(old) != completion_count or len(reference) != completion_count:
            raise RuntimeError("GRPO sample log-probability lengths do not match completion mask")
        input_ids = torch.tensor([token_ids], dtype=torch.long, device="cuda")
        labels = torch.tensor(
            [[token if mask else -100 for token, mask in zip(token_ids, completion_mask)]],
            dtype=torch.long,
            device="cuda",
        )
        tensors = {
            "input_ids": input_ids,
            "attention_mask": torch.ones_like(input_ids),
            "labels": labels,
        }
        current = _completion_logprobs(model, tensors, torch, runtime["functional"])
        old_tensor = torch.tensor(old, dtype=current.dtype, device="cuda")
        reference_tensor = torch.tensor(reference, dtype=current.dtype, device="cuda")
        advantage = _require_float(sample.get("advantage"), "GRPO sample.advantage")
        if advantage != 0:
            nonzero_advantage_steps += 1
        ratios = torch.exp(current - old_tensor)
        unclipped = ratios * advantage
        clipped = torch.clamp(ratios, 1 - clip_lower, 1 + clip_upper) * advantage
        policy_objective = torch.minimum(unclipped, clipped)
        reference_delta = reference_tensor - current
        kl = torch.exp(reference_delta) - reference_delta - 1
        loss = -(policy_objective - (kl_coefficient * kl)).mean()
        if not torch.isfinite(loss):
            raise RuntimeError(f"nonfinite GRPO loss at step {step + 1}")
        (loss / steps).backward()
        raw_loss = float(loss.detach().item())
        losses.append(raw_loss)
        _write_metric(metrics_path, {
            "step": step + 1,
            "loss": raw_loss,
            "advantage": advantage,
            "meanRatio": float(ratios.detach().mean().item()),
            "meanKl": float(kl.detach().mean().item()),
            "optimizerStep": 0,
        })
    grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm).item())
    optimizer.step()
    _write_metric(metrics_path, {
        "optimizerStep": 1,
        "microsteps": steps,
        "meanLoss": sum(losses) / len(losses),
        "gradNorm": grad_norm,
    })
    adapter_path, output_policy_hash = _save_adapter(model, output_root)
    return {
        "modelPath": str(model_path),
        "adapterPath": str(adapter_path),
        "inputPolicyHash": input_policy_hash,
        "policyHash": output_policy_hash,
        "checkpointStep": 1,
        "metrics": {
            "loss": losses[-1],
            "meanLoss": sum(losses) / len(losses),
            "steps": steps,
            "optimizerSteps": 1,
            "updatesPerRolloutBatch": updates_per_rollout_batch,
            "maximumStalePolicyUpdates": maximum_stale_policy_updates,
            "dropoutDisabled": True,
            "sampleOrder": "seed_shuffled",
            "signalSampleCount": len(samples),
            "nonzeroAdvantageSteps": nonzero_advantage_steps,
            "gradNorm": grad_norm,
        },
        "metricsPath": str(metrics_path),
    }


def _preflight(request: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    training = _require_object(request.get("training"), "training")
    model_path = _resolve_model_path(_require_object(request.get("model"), "model"), runtime)
    config_path = model_path / "config.json"
    if not config_path.is_file():
        raise RuntimeError(f"provisioned model has no config.json: {model_path}")
    config = _read_json(config_path)
    return {
        "modelPath": str(model_path),
        "modelConfigSha256": _sha256_file(config_path),
        "modelType": config.get("model_type"),
        "architectures": config.get("architectures", []),
        "runtime": _prove_rocm(runtime, _require_string(training.get("dtype"), "training.dtype")),
    }


def execute(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol") != PROTOCOL:
        raise RuntimeError(f"request.protocol must be {PROTOCOL}")
    action = _require_string(request.get("action"), "request.action")
    if action not in SUPPORTED_ACTIONS:
        raise RuntimeError(f"unsupported action: {action}")
    run_id = _require_string(request.get("runId"), "request.runId")
    output_root = Path(_require_string(request.get("outputRoot"), "request.outputRoot")).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    runtime = _runtime_imports()
    training = _require_object(request.get("training"), "training")
    runtime_receipt = _prove_rocm(runtime, _require_string(training.get("dtype"), "training.dtype"))
    if action == "preflight":
        result = _preflight(request, runtime)
    elif action == "sft":
        result = _run_sft(request, runtime, output_root)
    elif action == "dpo":
        result = _run_dpo(request, runtime, output_root)
    elif action == "rollout":
        result = _run_rollout(request, runtime, output_root)
    elif action == "parity_microstep":
        result = _run_parity_microstep(request, runtime, output_root)
    else:
        result = _run_grpo_update(request, runtime, output_root)
    return {
        "protocol": PROTOCOL,
        "schemaVersion": 1,
        "ok": True,
        "runId": run_id,
        "action": action,
        "requestHash": _sha256_text(_stable_json(request)),
        "runtime": runtime_receipt,
        "result": result,
        "claimBoundary": "Training mechanics and artifacts only; Doppler owns capability promotion.",
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    request_path = Path(args.request).resolve()
    response_path = Path(args.response).resolve()
    try:
        response = execute(_require_object(_read_json(request_path), "request"))
        exit_code = 0
    except Exception as exc:
        response = {
            "protocol": PROTOCOL,
            "schemaVersion": 1,
            "ok": False,
            "error": str(exc),
            "errorType": type(exc).__name__,
            "claimBoundary": "Failed preflight or training is not capability evidence.",
        }
        exit_code = 1
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_text(json.dumps(response, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(response, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
