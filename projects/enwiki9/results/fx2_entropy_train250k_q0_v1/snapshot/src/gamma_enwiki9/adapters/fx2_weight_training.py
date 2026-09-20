"""Weight-cost surrogate and strict export for the existing FX2 architecture.

The surrogate is an order-zero symbol description, not the actual adaptive
container cost. Selection requires packing the checkpoint and native replay.
"""
from __future__ import annotations

import importlib
import math


def quantized_weight_rate_bits(model):
    """Differentiable smoothed histogram cost of the actual 15-level weights.

Forward counts use exact BF16-scale, FP32-division, half-even quantization.
Backward counts use linear interpolation between adjacent integer bins.
Scales, unquantized tensors, headers and the adaptive coder are NOT included;
the packed file must price those. One global alphabet matches the container's
single INT4 model, without claiming to reproduce its adaptive coding length.
"""
    import torch

    parameters = dict(model.named_parameters())
    counts = None
    for name, weight in parameters.items():
        if not name.endswith(".weight"):
            continue
        scale = parameters.get(name[:-7] + ".quantize_weight.scale")
        if scale is None:
            continue
        # Straight-through BF16 storage for the learned scales.
        stored = scale.to(torch.bfloat16).float()
        rounded_scale = scale + (stored - scale).detach()
        if not torch.isfinite(stored).all() or (stored == 0).any():
            raise ValueError(f"invalid stored scale: {name}")
        signed = (weight.float() / rounded_scale.reshape(-1, 1)).clamp(-7, 7).flatten()
        x = signed + 7
        lower = x.floor().long()
        upper = (lower + 1).clamp(max=14)
        fraction = x - lower
        soft = x.new_zeros(15).scatter_add(0, lower, 1 - fraction).scatter_add(0, upper, fraction)
        hard = torch.bincount(signed.round().long() + 7, minlength=15).to(x.dtype)
        histogram = soft + (hard - soft).detach()
        counts = histogram if counts is None else counts + histogram
    if counts is None:
        raise ValueError("no FX2 quantized weights")
    probability = (counts + 0.5) / (counts.sum() + 7.5)
    return -(counts * probability.log2()).sum()


def combined_objective(data_bits_per_symbol, weight_rate_bits, *, model_copies,
                       represented_symbols):
    """Normalize a declared full-population description objective per symbol.

represented_symbols is a frozen planning normalization, not a measured full
archive length. Never silently substitute the minibatch length.
"""
    if model_copies not in (1, 2) or not math.isfinite(represented_symbols) or represented_symbols <= 0:
        raise ValueError("declare model copies and a positive population normalization")
    return data_bits_per_symbol + model_copies * weight_rate_bits / represented_symbols


def export_entries(model, template, package):
    """Export changed tensors while preserving the parent's exact RoPE/config.

template is the decoded authenticated native weight container. Unexpected
names/shapes/dtypes fail closed; this exporter cannot silently drop metadata
parameters or accept a changed architecture. No GPU trigonometry is needed.
"""
    import numpy as np
    import torch

    exporter = importlib.import_module(package + ".export_weights")
    state = model.state_dict()
    modules = dict(model.named_modules())
    entries = {}
    for key, value in state.items():
        value = value.detach()
        if not torch.isfinite(value).all():
            raise ValueError(f"nonfinite tensor: {key}")
        prefix = key[:-7] if key.endswith(".weight") else ""
        scale = state.get(prefix + ".quantize_weight.scale") if prefix else None
        if scale is not None:
            ints, stored_scale = exporter.quantize_weight_rows(value, scale)
            if not torch.isfinite(stored_scale).all() or (stored_scale == 0).any():
                raise ValueError(f"invalid weight scale: {key}")
            module = modules[prefix].quantize_weight
            if not torch.equal(ints.long(), module(value, initialize_scales_steps=None, return_ints=True)):
                raise ValueError(f"quantizer mismatch: {key}")
            entries[key + ".q"] = (exporter.DTYPE_INT8, ints.cpu().numpy())
            entries[key + ".scale"] = (exporter.DTYPE_BF16_BITS, exporter.bf16_bits(scale))
        elif key.endswith(".quantize_weight.scale"):
            if key.removesuffix(".quantize_weight.scale") + ".weight" not in state:
                raise ValueError(f"orphan scale: {key}")
        elif key.endswith(exporter._ACTIVATION_SCALE_SUFFIXES):
            if not (value.to(torch.bfloat16).float() > 0).all():
                raise ValueError(f"invalid activation scale: {key}")
            entries[key] = (exporter.DTYPE_BF16_BITS, exporter.bf16_bits(value))
        elif key.endswith(exporter._UNQUANTIZED_FP32_SUFFIXES) and value.dtype == torch.float32:
            entries[key] = (exporter.DTYPE_FLOAT32, value.cpu().numpy())
        else:
            raise ValueError(f"unsupported model tensor: {key}")
    config = [model.cfg.vocabulary_size, model.cfg.d_model, model.cfg.n_layers,
              model.cfg.d_head, model.cfg.n_query_heads, model.cfg.d_mlp,
              model.cfg.window_size, model.cfg.kimi_linear_d_head,
              model.cfg.kimi_linear_n_heads, model.cfg.kimi_linear_convolution_size,
              model.cfg.rope_base]
    if not np.array_equal(template["config.ints"][1], config):
        raise ValueError("native model configuration mismatch")
    if not np.array_equal(template["config.kimi"][1], model.cfg.kimi_linear):
        raise ValueError("native recurrent layout mismatch")
    for key in ("rope.inv_freq", "rope.sin", "rope.cos", "config.ints", "config.kimi"):
        entries[key] = template[key]
    if entries.keys() != template.keys():
        raise ValueError("native tensor inventory mismatch")
    for key, (kind, value) in entries.items():
        old_kind, old_value = template[key]
        if kind != old_kind or value.shape != old_value.shape or value.dtype != old_value.dtype:
            raise ValueError(f"native tensor layout mismatch: {key}")
    return [(key, *entries[key]) for key in template]
