#!/usr/bin/env python3
"""Deterministic cross-size LoRA transport for related decoder families."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


LORA_KEY = re.compile(
    r"^(?P<prefix>.*language_model\.layers\.)(?P<layer>\d+)\."
    r"(?P<module>.+)\.lora_(?P<factor>[AB])(?:\.default)?\.weight$"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _stable_seed(seed: int, *parts: object) -> int:
    payload = "\0".join([str(seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "little")


def transport_projection_seed(
    seed: int,
    target_layer: int,
    module: str,
    source_layer: int,
) -> int:
    return _stable_seed(seed, target_layer, module, source_layer)


def _require_sha256(path: Path, expected: Any, label: str) -> None:
    normalized = str(expected or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise RuntimeError(f"{label} must be a SHA-256 digest")
    actual = _sha256_file(path)
    if actual != normalized:
        raise RuntimeError(f"{label} mismatch: expected {normalized}, got {actual}")


def countsketch_rows(tensor: Any, target_rows: int, seed: int, torch: Any) -> Any:
    source_rows = int(tensor.shape[0])
    if target_rows < 1:
        raise RuntimeError("CountSketch target_rows must be positive")
    if source_rows == target_rows:
        return tensor.clone()
    seed_bytes = hashlib.sha256(str(seed).encode("utf-8")).digest()
    bucket_multiplier = int.from_bytes(seed_bytes[:4], "little") | 1
    bucket_offset = int.from_bytes(seed_bytes[4:8], "little")
    sign_multiplier = int.from_bytes(seed_bytes[8:12], "little") | 1
    sign_offset = int.from_bytes(seed_bytes[12:16], "little")
    indices = torch.arange(source_rows, dtype=torch.int64, device=tensor.device)
    bucket_hash = (indices * bucket_multiplier) + bucket_offset
    bucket_hash = torch.bitwise_xor(bucket_hash, torch.bitwise_right_shift(bucket_hash, 16))
    bucket = torch.remainder(bucket_hash, target_rows)
    sign_hash = (indices * sign_multiplier) + sign_offset
    sign_hash = torch.bitwise_xor(sign_hash, torch.bitwise_right_shift(sign_hash, 13))
    sign_bits = torch.bitwise_and(torch.bitwise_right_shift(sign_hash, 7), 1)
    signs = sign_bits.to(dtype=tensor.dtype).mul_(2).sub_(1)
    output = torch.zeros(
        (target_rows, *tensor.shape[1:]),
        dtype=tensor.dtype,
        device=tensor.device,
    )
    scale_shape = (source_rows,) + ((1,) * (tensor.ndim - 1))
    output.index_add_(0, bucket, tensor * signs.reshape(scale_shape))
    counts = torch.zeros(target_rows, dtype=tensor.dtype, device=tensor.device)
    counts.index_add_(0, bucket, torch.ones_like(signs))
    divisor_shape = (target_rows,) + ((1,) * (tensor.ndim - 1))
    return output / counts.clamp_min(1).sqrt().reshape(divisor_shape)


def sketch_lora_factors(
    factor_a: Any,
    factor_b: Any,
    target_in: int,
    target_out: int,
    seed: int,
    torch: Any,
) -> tuple[Any, Any]:
    projected_a = countsketch_rows(
        factor_a.transpose(0, 1),
        target_in,
        _stable_seed(seed, "input"),
        torch,
    ).transpose(0, 1)
    projected_b = countsketch_rows(
        factor_b,
        target_out,
        _stable_seed(seed, "output"),
        torch,
    )
    return projected_a, projected_b


def compress_lora_terms(
    terms: list[tuple[Any, Any, float]],
    target_rank: int,
    target_scale: float,
    torch: Any,
) -> tuple[Any, Any, dict[str, float]]:
    if not terms:
        raise RuntimeError("LoRA compression requires at least one term")
    if target_rank < 1 or target_scale <= 0:
        raise RuntimeError("LoRA compression rank and scale must be positive")
    factors_a = []
    factors_b = []
    for factor_a, factor_b, coefficient in terms:
        if coefficient < 0 or not math.isfinite(coefficient):
            raise RuntimeError("LoRA transport coefficients must be finite and non-negative")
        root = math.sqrt(coefficient)
        factors_a.append(factor_a.float() * root)
        factors_b.append(factor_b.float() * root)
    combined_a = torch.cat(factors_a, dim=0)
    combined_b = torch.cat(factors_b, dim=1)
    q_b, r_b = torch.linalg.qr(combined_b, mode="reduced")
    q_a, r_a = torch.linalg.qr(combined_a.transpose(0, 1), mode="reduced")
    core = r_b @ r_a.transpose(0, 1)
    u_core, singular, vh_core = torch.linalg.svd(core, full_matrices=False)
    kept = min(target_rank, int(singular.numel()))
    singular_kept = singular[:kept].clamp_min(0)
    left = q_b @ u_core[:, :kept]
    right = vh_core[:kept, :] @ q_a.transpose(0, 1)
    balanced = torch.sqrt(singular_kept / target_scale)
    output_b = left * balanced.unsqueeze(0)
    output_a = balanced.unsqueeze(1) * right
    if kept < target_rank:
        output_a = torch.cat([
            output_a,
            torch.zeros(
                (target_rank - kept, output_a.shape[1]),
                dtype=output_a.dtype,
                device=output_a.device,
            ),
        ], dim=0)
        output_b = torch.cat([
            output_b,
            torch.zeros(
                (output_b.shape[0], target_rank - kept),
                dtype=output_b.dtype,
                device=output_b.device,
            ),
        ], dim=1)
    total_energy = float(singular.square().sum().item())
    kept_energy = float(singular_kept.square().sum().item())
    return output_a, output_b, {
        "inputRank": int(combined_a.shape[0]),
        "outputRank": target_rank,
        "retainedEnergy": 1.0 if total_energy == 0 else kept_energy / total_energy,
        "largestSingularValue": float(singular[0].item()) if singular.numel() else 0.0,
    }


def _model_text_config(model_root: Path) -> dict[str, Any]:
    config_path = model_root / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    text_config = config.get("text_config") or config
    if not isinstance(text_config, dict):
        raise RuntimeError(f"model text_config is invalid: {config_path}")
    return text_config


def _full_attention_layers(text_config: dict[str, Any]) -> list[int]:
    layer_types = text_config.get("layer_types")
    if not isinstance(layer_types, list):
        raise RuntimeError("model text_config.layer_types must be an array")
    return [index for index, value in enumerate(layer_types) if value == "full_attention"]


def _interpolated_layers(
    target_layer: int,
    target_layers: list[int],
    source_layers: list[int],
) -> list[tuple[int, float]]:
    if target_layer not in target_layers or not source_layers:
        raise RuntimeError(f"cannot map target layer {target_layer}")
    if len(target_layers) == 1 or len(source_layers) == 1:
        return [(source_layers[0], 1.0)]
    target_ordinal = target_layers.index(target_layer)
    position = target_ordinal * (len(source_layers) - 1) / (len(target_layers) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return [(source_layers[lower], 1.0)]
    upper_weight = position - lower
    return [
        (source_layers[lower], 1.0 - upper_weight),
        (source_layers[upper], upper_weight),
    ]


class _WeightStore:
    def __init__(self, root: Path, safe_open: Any) -> None:
        self.root = root
        self.safe_open = safe_open
        index_path = root / "model.safetensors.index.json"
        if not index_path.is_file():
            raise RuntimeError(f"model has no SafeTensors index: {index_path}")
        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.weight_map = index.get("weight_map") or {}

    def rms(self, key: str) -> float:
        filename = self.weight_map.get(key)
        if not filename:
            raise RuntimeError(f"model weight missing from index: {key}")
        with self.safe_open(str(self.root / filename), framework="pt", device="cpu") as handle:
            tensor = handle.get_tensor(key).float()
        return float(tensor.square().mean().sqrt().item())


def _adapter_inventory(adapter_spec: dict[str, Any], safe_open: Any) -> dict[str, Any]:
    adapter_root = Path(str(adapter_spec.get("path") or "")).expanduser().resolve()
    config_path = adapter_root / "adapter_config.json"
    weights_path = adapter_root / "adapter_model.safetensors"
    if not config_path.is_file() or not weights_path.is_file():
        raise RuntimeError(f"adapter is incomplete: {adapter_root}")
    _require_sha256(config_path, adapter_spec.get("configSha256"), "adapter config")
    _require_sha256(weights_path, adapter_spec.get("weightsSha256"), "adapter weights")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    tensors: dict[tuple[int, str], dict[str, Any]] = defaultdict(dict)
    with safe_open(str(weights_path), framework="pt", device="cpu") as handle:
        for key in handle.keys():
            match = LORA_KEY.match(key)
            if not match:
                continue
            identity = (int(match.group("layer")), match.group("module"))
            tensors[identity][match.group("factor")] = handle.get_tensor(key).float()
    for identity, factors in tensors.items():
        if set(factors) != {"A", "B"}:
            raise RuntimeError(f"adapter has incomplete LoRA factors for {identity}")
    return {
        "id": str(adapter_spec.get("id") or adapter_root.name),
        "root": adapter_root,
        "rank": int(config["r"]),
        "alpha": float(config["lora_alpha"]),
        "weight": float(adapter_spec.get("weight", 1.0)),
        "tensors": tensors,
    }


def _base_weight_key(layer: int, module: str) -> str:
    return f"model.language_model.layers.{layer}.{module}.weight"


def _target_module_inventory(
    target_config: dict[str, Any],
    source_config: dict[str, Any],
    source_inventories: list[dict[str, Any]],
) -> list[tuple[int, str, list[tuple[int, float]]]]:
    target_count = int(target_config["num_hidden_layers"])
    source_count = int(source_config["num_hidden_layers"])
    target_all = list(range(target_count))
    source_all = list(range(source_count))
    target_full = _full_attention_layers(target_config)
    source_full = _full_attention_layers(source_config)
    modules = sorted({module for inventory in source_inventories for _, module in inventory["tensors"]})
    output = []
    for module in modules:
        attention = module.startswith("self_attn.")
        target_layers = target_full if attention else target_all
        source_layers = source_full if attention else source_all
        for target_layer in target_layers:
            output.append((
                target_layer,
                module,
                _interpolated_layers(target_layer, target_layers, source_layers),
            ))
    return output


def transport_lora(request: dict[str, Any], runtime: dict[str, Any], output_root: Path) -> dict[str, Any]:
    torch = runtime["torch"]
    safe_open = runtime["safe_open"]
    save_file = runtime["save_safetensors"]
    source_model = request.get("sourceModel") or {}
    target_model = request.get("model") or {}
    source_root = Path(str(source_model.get("localPath") or "")).expanduser().resolve()
    target_root = Path(str(target_model.get("localPath") or "")).expanduser().resolve()
    if not source_root.is_dir() or not target_root.is_dir():
        raise RuntimeError("transport requires provisioned sourceModel.localPath and model.localPath")
    for root, spec, label in (
        (source_root, source_model, "source model"),
        (target_root, target_model, "target model"),
    ):
        _require_sha256(root / "config.json", spec.get("configSha256"), f"{label} config")
        _require_sha256(root / "tokenizer.json", spec.get("tokenizerSha256"), f"{label} tokenizer")
    if _sha256_file(source_root / "tokenizer.json") != _sha256_file(target_root / "tokenizer.json"):
        raise RuntimeError("source and target tokenizers are not byte-identical")

    adapter_specs = request.get("sourceAdapters")
    if adapter_specs is None:
        source_adapter_set = request.get("sourceAdapterSet") or {}
        source_request_path = Path(
            str(source_adapter_set.get("requestPath") or "")
        ).expanduser().resolve()
        if not source_request_path.is_file():
            raise RuntimeError("transport sourceAdapterSet.requestPath is not a file")
        _require_sha256(
            source_request_path,
            source_adapter_set.get("requestSha256"),
            "transport source adapter-set request",
        )
        source_request = json.loads(source_request_path.read_text(encoding="utf-8"))
        adapter_specs = source_request.get("sourceAdapters")
    if not isinstance(adapter_specs, list) or len(adapter_specs) < 2:
        raise RuntimeError("transport requires at least two sourceAdapters")
    inventories = [_adapter_inventory(spec, safe_open) for spec in adapter_specs]
    if any(inventory["weight"] <= 0 for inventory in inventories):
        raise RuntimeError("source adapter weights must be positive")
    weight_total = sum(inventory["weight"] for inventory in inventories)

    transport = request.get("transport") or {}
    if transport.get("method") != "lineage-weighted-sketch-compress-v2":
        raise RuntimeError("transport.method must be lineage-weighted-sketch-compress-v2")
    if transport.get("projection") != "signed-countsketch-v1":
        raise RuntimeError("transport.projection must be signed-countsketch-v1")
    if transport.get("layerMap") != "normalized-role-interpolation-v1":
        raise RuntimeError("transport.layerMap must be normalized-role-interpolation-v1")
    if transport.get("compression") != "factor-qr-svd-v1":
        raise RuntimeError("transport.compression must be factor-qr-svd-v1")
    if transport.get("baseScale") != "weight-rms-ratio-v1":
        raise RuntimeError("transport.baseScale must be weight-rms-ratio-v1")
    seed = int(transport["seed"])
    clamp_min = float(transport["baseScaleClamp"][0])
    clamp_max = float(transport["baseScaleClamp"][1])
    if not 0 < clamp_min <= clamp_max:
        raise RuntimeError("transport.baseScaleClamp must be positive and ordered")

    adapter = request.get("adapter") or {}
    target_rank = int(adapter["rank"])
    target_alpha = float(adapter["alpha"])
    target_scale = target_alpha / target_rank
    source_config = _model_text_config(source_root)
    target_config = _model_text_config(target_root)
    source_weights = _WeightStore(source_root, safe_open)
    target_weights = _WeightStore(target_root, safe_open)
    module_inventory = _target_module_inventory(
        target_config,
        source_config,
        inventories,
    )

    output_tensors = {}
    module_receipts = []
    for target_layer, module, source_layers in module_inventory:
        target_weight_key = _base_weight_key(target_layer, module)
        target_rms = target_weights.rms(target_weight_key)
        source_rms = sum(
            coefficient * source_weights.rms(_base_weight_key(source_layer, module))
            for source_layer, coefficient in source_layers
        )
        base_scale = min(clamp_max, max(clamp_min, target_rms / source_rms))
        target_shape = None
        terms = []
        contributing = []
        for inventory in inventories:
            adapter_weight = inventory["weight"] / weight_total
            for source_layer, layer_weight in source_layers:
                factors = inventory["tensors"].get((source_layer, module))
                if factors is None:
                    raise RuntimeError(
                        f"source adapter {inventory['id']} has no {module} at layer {source_layer}"
                    )
                factor_a = factors["A"]
                factor_b = factors["B"]
                if target_shape is None:
                    target_shape = target_weights_shape(
                        target_weights,
                        target_weight_key,
                        safe_open,
                    )
                projected_a, projected_b = sketch_lora_factors(
                    factor_a,
                    factor_b,
                    target_shape[1],
                    target_shape[0],
                    transport_projection_seed(seed, target_layer, module, source_layer),
                    torch,
                )
                coefficient = (
                    adapter_weight
                    * layer_weight
                    * (inventory["alpha"] / inventory["rank"])
                    * base_scale
                )
                terms.append((projected_a, projected_b, coefficient))
                contributing.append({
                    "adapterId": inventory["id"],
                    "sourceLayer": source_layer,
                    "coefficient": coefficient,
                })
        output_a, output_b, compression = compress_lora_terms(
            terms,
            target_rank,
            target_scale,
            torch,
        )
        prefix = f"base_model.model.model.language_model.layers.{target_layer}.{module}"
        output_tensors[f"{prefix}.lora_A.weight"] = output_a.contiguous()
        output_tensors[f"{prefix}.lora_B.weight"] = output_b.contiguous()
        module_receipts.append({
            "targetLayer": target_layer,
            "module": module,
            "targetShape": list(target_shape),
            "sourceLayers": [
                {"layer": layer, "weight": weight} for layer, weight in source_layers
            ],
            "targetBaseRms": target_rms,
            "sourceBaseRms": source_rms,
            "baseScale": base_scale,
            "contributingTerms": contributing,
            **compression,
        })

    adapter_root = output_root / "adapter"
    adapter_root.mkdir(parents=True, exist_ok=True)
    weights_path = adapter_root / "adapter_model.safetensors"
    save_file(output_tensors, str(weights_path), metadata={"format": "pt"})
    adapter_config = {
        "alpha_pattern": {},
        "auto_mapping": None,
        "base_model_name_or_path": str(target_root),
        "bias": "none",
        "exclude_modules": None,
        "fan_in_fan_out": False,
        "inference_mode": True,
        "init_lora_weights": True,
        "layer_replication": None,
        "layers_pattern": None,
        "layers_to_transform": None,
        "loftq_config": {},
        "lora_alpha": int(target_alpha),
        "lora_bias": False,
        "lora_dropout": float(adapter["dropout"]),
        "megatron_config": None,
        "megatron_core": "megatron.core",
        "modules_to_save": None,
        "peft_type": "LORA",
        "peft_version": runtime["peftVersion"],
        "r": target_rank,
        "rank_pattern": {},
        "revision": target_model.get("revision"),
        "target_modules": sorted(str(value) for value in adapter["targetModules"]),
        "target_parameters": None,
        "task_type": "CAUSAL_LM",
        "use_dora": False,
        "use_rslora": False,
    }
    config_path = adapter_root / "adapter_config.json"
    config_path.write_text(json.dumps(adapter_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema": "gamma.wgsl-lora-transport/v1",
        "method": "lineage-weighted-sketch-compress-v2",
        "sourceModel": source_model,
        "targetModel": target_model,
        "sourceAdapters": [
            {
                "id": inventory["id"],
                "path": str(inventory["root"]),
                "rank": inventory["rank"],
                "alpha": inventory["alpha"],
                "normalizedWeight": inventory["weight"] / weight_total,
            }
            for inventory in inventories
        ],
        "transport": transport,
        "adapter": adapter,
        "modules": module_receipts,
        "adapterConfigSha256": _sha256_file(config_path),
        "adapterWeightsSha256": _sha256_file(weights_path),
        "claimBoundary": "Initializer mechanics only; downstream training and executable evaluation decide capability.",
    }
    receipt_path = output_root / "transport-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "adapterPath": str(adapter_root),
        "adapterConfigSha256": receipt["adapterConfigSha256"],
        "adapterWeightsSha256": receipt["adapterWeightsSha256"],
        "receiptPath": str(receipt_path),
        "method": receipt["method"],
        "moduleCount": len(module_receipts),
        "meanRetainedEnergy": sum(
            module["retainedEnergy"] for module in module_receipts
        ) / len(module_receipts),
    }


def target_weights_shape(
    store: _WeightStore,
    key: str,
    safe_open: Any,
) -> tuple[int, int]:
    filename = store.weight_map.get(key)
    if not filename:
        raise RuntimeError(f"model weight missing from index: {key}")
    with safe_open(str(store.root / filename), framework="pt", device="cpu") as handle:
        shape = tuple(int(value) for value in handle.get_slice(key).get_shape())
    if len(shape) != 2:
        raise RuntimeError(f"target module is not a matrix: {key} {shape}")
    return shape
