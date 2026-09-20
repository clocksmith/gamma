"""export the reference checkpoint models/6m-q4-fp32.tch to
cpp_infer/data/weights.bin in the binary format of cpp_infer/SPEC.md section 4

run from the repository root:  .venv/bin/python -m pysrc.export_weights

every quantized weight is stored as the exact ints QuantizeFunction.forward
computes during training/eval (bfloat16-rounded scale, fp32 IEEE division,
round-half-even, clamp to [-7, 7]); the quantization arithmetic runs on CUDA on
the same fp32 parameter values the model uses, and the result is verified
bit-exactly against the model's own Quantize modules (both the ints and the
dequantized fake-quantized weights) before anything is written
"""

import struct

import numpy as np
import torch
from torch import Tensor, linspace

from pysrc.model import (
    MatmulQuantization,
    Transformer,
    TransformerConfig,
    make_rope_args,
)
from pysrc.quantization import Quantization

MODEL_FILENAME = "models/6m-q4-fp32.tch"
OUTPUT_FILENAME = "cpp_infer/data/weights.bin"
MAGIC = b"FX2TFW01"
ROPE_SEQUENCE_LENGTH = 131072

DTYPE_INT8 = 0
DTYPE_BF16_BITS = 1  # uint16 holding the raw bits of a bfloat16 value
DTYPE_FLOAT32 = 2
DTYPE_INT32 = 3

_DTYPE_TO_NUMPY = {
    DTYPE_INT8: np.int8,
    DTYPE_BF16_BITS: np.uint16,
    DTYPE_FLOAT32: np.float32,
    DTYPE_INT32: np.int32,
}

_ACTIVATION_SCALE_SUFFIXES = (
    ".quantize_activation.scale",
    ".quantize_queries.scale",
    ".quantize_keys.scale",
    ".quantize_values.scale",
)

# every state-dict tensor that is neither a quantized weight, a weight scale nor
# an activation scale must be one of these raw-fp32 tensors (SPEC section 4)
_UNQUANTIZED_FP32_SUFFIXES = (
    ".query_convolution.weight",
    ".key_convolution.weight",
    ".value_convolution.weight",
    ".beta_projection.weight",
    ".dt_bias",
    ".log_baseline_decay_rate",
    ".output_fused_norm_gate.weight",
    ".residual_stream_coefficient.value",
    ".token_embedding_coefficient.value",
    "skip_connection_weights.value",
)


def make_reference_config() -> TransformerConfig:
    """exactly the config of training_recipes/save_outputs.py"""
    quantization_block_size: int | None = None

    weight_quantization = Quantization(
        buckets=15,
        block_size=quantization_block_size,
        scale_dtype=torch.bfloat16,
        arithmetic_dtype=torch.float32,
        scale_init="scaled_max",
        epsilon=None,
    )
    activation_quantization = Quantization(
        buckets=256,
        block_size=quantization_block_size,
        scale_dtype=torch.bfloat16,
        arithmetic_dtype=torch.float32,
        scale_init="scaled_mean",
        epsilon=None,
    )
    matmul_quantization = MatmulQuantization(
        weight=weight_quantization, activation=activation_quantization
    )

    return TransformerConfig(
        vocabulary_size=205,
        prior_embedding=True,
        prior_logit_mixing=False,
        max_variable_sequence_length=None,
        n_layers=12,
        attention_weight_sharing_pattern=list(range(12)),
        mlp_weight_sharing_pattern=list(range(12)),
        d_model=192,
        kimi_linear=[True, True, True, False] * 3,
        window_size=1024,
        window_size_multipliers=None,
        n_query_heads=3,
        n_key_value_heads=3,
        d_head=64,
        d_mla=None,
        rope_base=10_000,
        half_truncate_rope=False,
        query_key_norm=True,
        kimi_linear_d_head=64,
        kimi_linear_n_heads=3,
        kimi_linear_convolution_size=4,
        value_embedding_pattern=None,
        prior_value_embedding=False,
        attention_scale=None,
        d_mlp=768,
        activation_function="relu_squared",
        embedding_norm=True,
        prior_embedding_norm=True,
        skip_connections=True,
        token_embedding_connections=True,
        prior_embedding_connections=False,
        dropout=0.0,
        logit_softcap=15.0,
        prior_logprob_cap=-12.0,
        prior_embedding_on_logprobs=False,
        gradient_checkpointing=False,
        embedding_init="normal",
        prior_embedding_init="normal",
        up_init="kaiming_uniform",
        down_init="kaiming_uniform",
        unembedding_init="kaiming_uniform",
        convolution_init="kaiming_uniform",
        logit_mixing_head_init="zero",
        activation_dtype=torch.float32,
        attention_dtype=torch.float32,
        logit_dtype=torch.float32,
        weight_dtype=torch.float32,
        mlp_quantization=matmul_quantization,
        attention_full_rank_quantization=matmul_quantization,
        attention_low_rank_quantization=matmul_quantization,
        qkv_quantization=activation_quantization,
        kimi_linear_full_rank_quantization=matmul_quantization,
        kimi_linear_low_rank_quantization=matmul_quantization,
        kimi_linear_beta_projection_quantization=None,
        kimi_linear_convolution_quantization=None,
        embedding_quantization=weight_quantization,
        prior_embedding_quantization=matmul_quantization,
        unembedding_quantization=matmul_quantization,
        logit_mixing_head_quantization=None,
        adamw_quantization_scales=True,
        attention_implementation="flex_attention",
    )


def load_reference_model(device: torch.device) -> Transformer:
    """the model exactly as training_recipes/save_outputs.py loads it"""
    model = Transformer(make_reference_config())
    model = model.to(device)
    model.load_state_dict(torch.load(MODEL_FILENAME))
    model.eval()
    return model


def quantize_weight_rows(
    weight: Tensor, scale_fp32: Tensor
) -> tuple[Tensor, Tensor]:
    """replicate QuantizeFunction.forward for the 15-bucket weight quantizer
    (per-output-row scales, fp32 arithmetic, no epsilon) on the weight's own
    device; returns (int8 ints of the weight's shape, the fp32 value of the
    bfloat16-rounded scale actually used in arithmetic, shape (d_out,))"""
    assert weight.dtype == torch.float32
    assert weight.ndim == 2
    assert scale_fp32.dtype == torch.float32
    assert scale_fp32.shape == (weight.shape[0],)

    scale = scale_fp32.to(torch.bfloat16).to(torch.float32)
    scaled = weight.float() / scale.unsqueeze(-1)  # IEEE fp32 division per row
    quantized = scaled.round().clamp(-7, 7)  # round half to even, then clamp
    return quantized.to(torch.int8), scale


def bf16_bits(x: Tensor) -> np.ndarray:
    """uint16 numpy array of the bfloat16 (round-to-nearest-even) bits of x"""
    assert x.dtype == torch.float32
    return x.detach().to(torch.bfloat16).view(torch.uint16).cpu().numpy()


def write_tensor_file(
    filename: str, entries: list[tuple[str, int, np.ndarray]]
) -> None:
    with open(filename, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<I", len(entries)))
        for name, dtype_code, array in entries:
            assert array.dtype == _DTYPE_TO_NUMPY[dtype_code], name
            data = np.ascontiguousarray(array)
            encoded = name.encode()
            f.write(struct.pack("<I", len(encoded)))
            f.write(encoded)
            f.write(struct.pack("<B", dtype_code))
            f.write(struct.pack("<I", data.ndim))
            f.write(struct.pack(f"<{data.ndim}I", *data.shape))
            f.write(data.tobytes())


def read_tensor_file(filename: str) -> dict[str, tuple[int, np.ndarray]]:
    with open(filename, "rb") as f:
        assert f.read(8) == MAGIC
        (n_tensors,) = struct.unpack("<I", f.read(4))
        tensors: dict[str, tuple[int, np.ndarray]] = {}
        for _ in range(n_tensors):
            (name_length,) = struct.unpack("<I", f.read(4))
            name = f.read(name_length).decode()
            (dtype_code,) = struct.unpack("<B", f.read(1))
            (ndim,) = struct.unpack("<I", f.read(4))
            shape = struct.unpack(f"<{ndim}I", f.read(4 * ndim))
            dtype = np.dtype(_DTYPE_TO_NUMPY[dtype_code])
            count = int(np.prod(shape))
            array = np.frombuffer(
                f.read(count * dtype.itemsize), dtype=dtype
            ).reshape(shape)
            assert name not in tensors
            tensors[name] = (dtype_code, array)
        assert f.read(1) == b""
        return tensors


@torch.inference_mode()
def export_weights(model: Transformer, output_filename: str) -> None:
    cfg = model.cfg
    state_dict = model.state_dict()  # cuda tensors, registration order
    modules = dict(model.named_modules())

    entries: list[tuple[str, int, np.ndarray]] = []

    quantized_weight_keys = {
        key
        for key in state_dict
        if key.endswith(".weight")
        and key[: -len(".weight")] + ".quantize_weight.scale" in state_dict
    }

    n_quantized = n_activation_scales = n_raw_fp32 = 0
    negative_scale_weights: list[tuple[str, int]] = []

    for key, value in state_dict.items():
        value = value.detach()

        if key in quantized_weight_keys:
            prefix = key[: -len(".weight")]
            scale_fp32 = state_dict[prefix + ".quantize_weight.scale"].detach()
            ints, scale_used = quantize_weight_rows(value, scale_fp32)

            # verify bit-exactly against the model's own quantizer on CUDA
            quantize_module = modules[prefix].quantize_weight
            ints_reference = quantize_module(
                value, initialize_scales_steps=None, return_ints=True
            )
            dequantized_reference = quantize_module(
                value, initialize_scales_steps=None, return_ints=False
            )
            assert ints_reference.dtype == torch.int64
            assert torch.equal(ints_reference, ints.to(torch.int64)), (
                f"int mismatch for {key}"
            )
            assert torch.equal(
                dequantized_reference,
                ints.to(torch.float32) * scale_used.unsqueeze(-1),
            ), f"dequantized mismatch for {key}"
            assert int(ints.abs().max().item()) <= 7

            n_negative = int((scale_used < 0).sum().item())
            if n_negative:
                negative_scale_weights.append((key, n_negative))

            entries.append((key + ".q", DTYPE_INT8, ints.cpu().numpy()))
            entries.append((key + ".scale", DTYPE_BF16_BITS, bf16_bits(scale_fp32)))
            n_quantized += 1
        elif key.endswith(".quantize_weight.scale"):
            assert key[: -len(".quantize_weight.scale")] + ".weight" in (
                quantized_weight_keys
            )  # written together with its weight above
        elif key.endswith(_ACTIVATION_SCALE_SUFFIXES):
            scale_used = value.to(torch.bfloat16).to(torch.float32)
            assert bool((scale_used > 0).all()), (
                f"activation scale not positive: {key}"
            )
            entries.append((key, DTYPE_BF16_BITS, bf16_bits(value)))
            n_activation_scales += 1
        else:
            assert key.endswith(_UNQUANTIZED_FP32_SUFFIXES), key
            assert value.dtype == torch.float32
            entries.append((key, DTYPE_FLOAT32, value.cpu().numpy()))
            n_raw_fp32 += 1

    # rope tables, computed exactly as pysrc.model.make_rope_args on CUDA
    assert cfg.rope_base is not None and not cfg.half_truncate_rope
    device = next(model.parameters()).device
    assert device.type == "cuda"
    rope_args = make_rope_args(
        sequence_length=ROPE_SEQUENCE_LENGTH, cfg=cfg, device=device
    )
    assert rope_args is not None
    assert rope_args.sines.dtype == torch.float32
    assert rope_args.sines.shape == (ROPE_SEQUENCE_LENGTH, cfg.d_head // 2)

    inv_freq = 1.0 / (
        cfg.rope_base
        ** linspace(
            0, 1, steps=cfg.d_head // 2, dtype=torch.float32, device=device
        )
    )
    # the tables really are outer(arange, inv_freq).sin()/.cos() of this inv_freq
    t = torch.arange(ROPE_SEQUENCE_LENGTH, dtype=torch.float32, device=device)
    freqs = torch.outer(t, inv_freq)
    assert torch.equal(freqs.sin(), rope_args.sines)
    assert torch.equal(freqs.cos(), rope_args.cosines)

    entries.append(("rope.inv_freq", DTYPE_FLOAT32, inv_freq.cpu().numpy()))
    entries.append(("rope.sin", DTYPE_FLOAT32, rope_args.sines.cpu().numpy()))
    entries.append(("rope.cos", DTYPE_FLOAT32, rope_args.cosines.cpu().numpy()))

    # config constants
    assert cfg.window_size is not None and cfg.kimi_linear is not None
    config_ints = np.array(
        [
            cfg.vocabulary_size,
            cfg.d_model,
            cfg.n_layers,
            cfg.d_head,
            cfg.n_query_heads,
            cfg.d_mlp,
            cfg.window_size,
            cfg.kimi_linear_d_head,
            cfg.kimi_linear_n_heads,
            cfg.kimi_linear_convolution_size,
            cfg.rope_base,
        ],
        dtype=np.int32,
    )
    assert config_ints.tolist() == [205, 192, 12, 64, 3, 768, 1024, 64, 3, 4, 10000]
    entries.append(("config.ints", DTYPE_INT32, config_ints))
    entries.append(
        (
            "config.kimi",
            DTYPE_INT32,
            np.array([int(k) for k in cfg.kimi_linear], dtype=np.int32),
        )
    )

    assert n_quantized == 111, n_quantized
    assert n_activation_scales == 119, n_activation_scales
    assert n_raw_fp32 == 88, n_raw_fp32
    assert len(entries) == 2 * n_quantized + n_activation_scales + n_raw_fp32 + 5

    write_tensor_file(output_filename, entries)

    # read the file back and compare everything bit-exactly
    read_back = read_tensor_file(output_filename)
    assert len(read_back) == len(entries)
    for name, dtype_code, array in entries:
        read_dtype_code, read_array = read_back[name]
        assert read_dtype_code == dtype_code, name
        assert read_array.shape == array.shape, name
        assert np.array_equal(read_array, array), name

    import os

    print(
        f"wrote {len(entries)} tensors to {output_filename} "
        f"({os.path.getsize(output_filename)} bytes): "
        f"{n_quantized} quantized weights (ints + bf16 row scales), "
        f"{n_activation_scales} bf16 activation scales, "
        f"{n_raw_fp32} raw fp32 tensors, rope tables and config"
    )
    print(
        "quantization verified bit-exactly against the model's Quantize modules "
        "on CUDA (ints and dequantized weights, max diff == 0)"
    )
    total_negative = sum(n for _, n in negative_scale_weights)
    print(
        f"weights with negative bf16 row scales: "
        f"{len(negative_scale_weights)} tensors, {total_negative} rows total"
    )
    for name, n_negative in negative_scale_weights:
        print(f"  {name}: {n_negative} negative row scales")
    print("all activation scales are positive")


def main() -> None:
    assert torch.cuda.is_available()
    import os

    os.makedirs("cpp_infer/data", exist_ok=True)
    model = load_reference_model(torch.device("cuda"))
    export_weights(model, OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
