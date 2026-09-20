from fla.ops.kda import chunk_kda
from fla.modules import FusedRMSNormGated
from fla.modules.conv.causal_conv1d import causal_conv1d
from torch.nn.attention.flex_attention import BlockMask
import torch
from torch import (
    Tensor,
    tensor,
    empty,
    tanh,
    pow,
    arange,
    outer,
    stack,
    linspace,
    rand,
    where,
)
from torch.nn import Module, Parameter, ModuleList
from torch.nn.functional import (
    embedding,
    linear,
    gelu,
    dropout,
    cross_entropy,
    softplus,
)
from torch.nn.init import normal_, kaiming_uniform_, zeros_
from torch.utils.checkpoint import checkpoint
from collections import defaultdict
from math import sqrt, pi, log2, log
from dataclasses import dataclass
from jaxtyping import Float, Int, Bool
from typing import Literal, Callable, Any, cast

from pysrc.attention_function import (
    attention_function,
    AttentionFunctionArguments,
    AttentionImplementation,
    make_flex_attention_block_mask,
)
from pysrc.quantization import Quantize, Quantization


ActivationFunctionName = Literal["gelu", "new_gelu", "relu_squared"]
WeightInit = Literal["kaiming_uniform", "normal", "zero"]


@dataclass(frozen=True, slots=True)
class MatmulQuantization:
    weight: Quantization | None
    activation: Quantization | None


@dataclass(frozen=True, slots=True)
class TransformerConfig:
    vocabulary_size: int
    prior_embedding: bool
    prior_logit_mixing: bool
    max_variable_sequence_length: int | None
    n_layers: int
    attention_weight_sharing_pattern: list[int]
    mlp_weight_sharing_pattern: list[int]
    d_model: int
    kimi_linear: list[bool] | None
    window_size: int | None
    window_size_multipliers: list[int | None] | None
    n_query_heads: int
    n_key_value_heads: int
    d_head: int
    d_mla: int | None
    rope_base: int | None
    half_truncate_rope: bool
    query_key_norm: bool
    query_key_norm_gain: bool
    kimi_linear_d_head: int
    kimi_linear_n_heads: int
    kimi_linear_convolution_size: int
    value_embedding_pattern: list[int | None] | None
    prior_value_embedding: bool
    attention_scale: float | None
    d_mlp: int
    activation_function: ActivationFunctionName
    embedding_norm: bool
    prior_embedding_norm: bool
    skip_connections: bool
    token_embedding_connections: bool
    prior_embedding_connections: bool
    dropout: float
    logit_softcap: float | None
    prior_logprob_cap: float
    prior_embedding_on_logprobs: bool
    gradient_checkpointing: bool
    embedding_init: WeightInit
    prior_embedding_init: WeightInit
    up_init: WeightInit
    down_init: WeightInit
    convolution_init: WeightInit
    unembedding_init: WeightInit
    logit_mixing_head_init: WeightInit
    activation_dtype: torch.dtype
    attention_dtype: torch.dtype
    logit_dtype: torch.dtype
    weight_dtype: torch.dtype
    mlp_quantization: MatmulQuantization | None
    attention_full_rank_quantization: MatmulQuantization | None
    attention_low_rank_quantization: MatmulQuantization | None
    qkv_quantization: Quantization | None
    kimi_linear_full_rank_quantization: MatmulQuantization | None
    kimi_linear_low_rank_quantization: MatmulQuantization | None
    kimi_linear_beta_projection_quantization: MatmulQuantization | None
    kimi_linear_convolution_quantization: MatmulQuantization | None
    embedding_quantization: Quantization | None
    prior_embedding_quantization: MatmulQuantization | None
    unembedding_quantization: MatmulQuantization | None
    logit_mixing_head_quantization: MatmulQuantization | None
    adamw_quantization_scales: bool
    attention_implementation: AttentionImplementation

    def __post_init__(self) -> None:
        assert len(self.attention_weight_sharing_pattern) == self.n_layers
        assert len(self.mlp_weight_sharing_pattern) == self.n_layers
        assert set(self.attention_weight_sharing_pattern) == set(
            range(max(self.attention_weight_sharing_pattern) + 1)
        )
        assert set(self.mlp_weight_sharing_pattern) == set(
            range(max(self.mlp_weight_sharing_pattern) + 1)
        )
        assert self.n_query_heads * self.d_head == self.d_model
        assert self.n_query_heads % self.n_key_value_heads == 0
        assert self.kimi_linear_n_heads * self.kimi_linear_d_head == self.d_model
        if self.kimi_linear is not None:
            assert (
                len(self.kimi_linear) == max(self.attention_weight_sharing_pattern) + 1
            )
        if self.window_size_multipliers is not None:
            assert (
                len(self.window_size_multipliers)
                == max(self.attention_weight_sharing_pattern) + 1
            )
            if self.kimi_linear is not None:
                assert all(
                    (ws_mul is None) == kimi
                    for ws_mul, kimi in zip(
                        self.window_size_multipliers, self.kimi_linear, strict=True
                    )
                )
            else:
                assert all(
                    ws_mul is not None for ws_mul in self.window_size_multipliers
                )
        if self.d_mla is not None:
            assert self.n_query_heads == self.n_key_value_heads
        if self.value_embedding_pattern is not None:
            assert len(self.value_embedding_pattern) == self.n_layers
        if self.prior_value_embedding:
            assert self.prior_embedding
            assert self.value_embedding_pattern is not None
        if self.prior_embedding_connections:
            assert self.prior_embedding
        if self.query_key_norm_gain:
            assert self.query_key_norm


def rms_norm(x: Float[Tensor, "... d"]) -> Float[Tensor, "... d"]:
    return torch.nn.functional.rms_norm(x, normalized_shape=(x.size(-1),))


def make_mean_zero(x: Tensor, dim: int) -> Tensor:
    return x - x.mean(dim=dim, keepdim=True)


def initialize_weight(
    shape: tuple[int, ...], init: WeightInit, dtype: torch.dtype
) -> Tensor:
    weight = empty(size=shape, dtype=dtype)

    if init == "kaiming_uniform":
        assert len(shape) == 2, "can only initialize 2d matrices with kaiming uniform"
        # TODO: torch.nn.Linear passes a=sqrt(5) to kaiming_uniform_, should i do this to?
        # if so, pay attention that we also use kaiming_uinform_ to initialize convolution weights
        kaiming_uniform_(weight)
    elif init == "normal":
        normal_(weight)
    elif init == "zero":
        zeros_(weight)
    else:
        raise ValueError(f"unknown weight initialization '{init}'")

    return weight


@dataclass(frozen=True, slots=True)
class InitializeScales:
    weight_steps: int | None
    activation_steps: int | None


class CastedLinear(Module):
    def __init__(
        self,
        d_in: int,
        d_out: int,
        init: WeightInit,
        quantization: MatmulQuantization | None,
        cfg: TransformerConfig,
        bias: bool = False,
    ) -> None:
        super().__init__()

        self.cfg = cfg

        self.weight = Parameter(
            initialize_weight(shape=(d_out, d_in), init=init, dtype=cfg.weight_dtype)
        )

        if bias:
            self.bias = Parameter(empty((d_out,), dtype=cfg.weight_dtype))
            bound: float = 1 / sqrt(d_in)
            self.bias.data.uniform_(-bound, bound)
        else:
            self.bias = None

        self.quantize_weight = (
            Quantize(
                quantization.weight,
                size=self.weight.shape,
                batched=False,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            if quantization is not None and quantization.weight is not None
            else None
        )
        self.quantize_activation = (
            Quantize(
                quantization.activation,
                size=(d_in,),
                batched=True,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            if quantization is not None and quantization.activation is not None
            else None
        )

    def forward(
        self,
        x: Float[Tensor, "... d_in"],
        initialize_scales: InitializeScales,
    ) -> Float[Tensor, "... d_out"]:
        assert x.dtype == self.cfg.activation_dtype
        assert self.weight.dtype == self.cfg.weight_dtype

        if self.quantize_activation is not None:
            x = self.quantize_activation(
                x,
                initialize_scales_steps=initialize_scales.activation_steps,
                return_ints=False,
            )
            assert x.dtype == self.cfg.activation_dtype

        weight = self.weight
        assert weight.dtype == self.cfg.weight_dtype
        if self.quantize_weight is not None:
            weight = self.quantize_weight(
                weight,
                initialize_scales_steps=initialize_scales.weight_steps,
                return_ints=False,
            )
            assert weight.dtype == self.cfg.weight_dtype

        output = linear(x, weight.type_as(x))

        if self.bias is not None:
            output = output + self.bias.type_as(output)

        return output


class CastedEmbedding(Module):
    def __init__(
        self,
        vocabulary_size: int,
        d_out: int,
        init: WeightInit,
        quantization: Quantization | None,
        cfg: TransformerConfig,
    ) -> None:
        super().__init__()

        self.cfg = cfg

        self.weight = Parameter(
            initialize_weight(
                shape=(vocabulary_size, d_out), init=init, dtype=cfg.weight_dtype
            )
        )

        self.quantize_weight = (
            Quantize(
                quantization,
                size=self.weight.shape,
                batched=False,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            if quantization is not None
            else None
        )

    def forward(
        self, x: Int[Tensor, "..."], initialize_scales: InitializeScales
    ) -> Float[Tensor, "... d_out"]:
        weight = self.weight
        assert weight.dtype == self.cfg.weight_dtype
        if self.quantize_weight is not None:
            weight = self.quantize_weight(
                weight,
                initialize_scales_steps=initialize_scales.weight_steps,
                return_ints=False,
            )
            assert weight.dtype == self.cfg.weight_dtype

        return embedding(x, weight.to(self.cfg.activation_dtype))


class CastedConstant(Module):
    def __init__(self, value: Tensor | list[float], cfg: TransformerConfig) -> None:
        super().__init__()

        self.cfg = cfg

        if isinstance(value, list):
            assert all(isinstance(x, (float, int)) for x in value)
            value = tensor(value, dtype=cfg.weight_dtype)
        else:
            assert value.dtype == cfg.weight_dtype

        self.value = Parameter(value)

    def forward(self) -> Tensor:
        assert self.value.dtype == self.cfg.weight_dtype

        return self.value.to(self.cfg.activation_dtype)


class LowRankCastedLinear(Module):
    def __init__(
        self,
        d_in: int,
        rank: int,
        d_out: int,
        init: WeightInit,
        quantization: MatmulQuantization | None,
        cfg: TransformerConfig,
        bias: bool = False,
    ) -> None:
        super().__init__()

        self.up = CastedLinear(
            d_in, rank, init=init, quantization=quantization, cfg=cfg
        )
        self.down = CastedLinear(
            rank, d_out, init=init, quantization=quantization, cfg=cfg, bias=bias
        )

    def forward(
        self,
        x: Float[Tensor, "... d_in"],
        initialize_scales: InitializeScales,
    ) -> Float[Tensor, "... d_out"]:
        x = self.up(x, initialize_scales=initialize_scales)
        x = self.down(x, initialize_scales=initialize_scales)
        return x


class CastedFusedConvolutionSiLU(Module):
    def __init__(
        self,
        d: int,
        kernel_size: int,
        init: WeightInit,
        quantization: MatmulQuantization | None,
        cfg: TransformerConfig,
    ) -> None:
        super().__init__()

        self.cfg = cfg

        self.weight = Parameter(
            initialize_weight(
                shape=(d, kernel_size),
                init=init,
                dtype=cfg.weight_dtype,
            )
        )

        self.quantize_weight = (
            Quantize(
                quant=quantization.weight,
                size=self.weight.shape,
                batched=False,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            if quantization is not None and quantization.weight is not None
            else None
        )

        self.quantize_activation = (
            Quantize(
                quant=quantization.activation,
                size=(d,),
                batched=True,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            if quantization is not None and quantization.activation is not None
            else None
        )

    def forward(
        self,
        x: Float[Tensor, "batch position d_model"],
        initialize_scales: InitializeScales,
        cu_seqlens: Int[Tensor, " document_plus_one"] | None = None,
    ) -> Float[Tensor, "batch position d_model"]:
        assert x.dtype == self.cfg.activation_dtype
        if self.quantize_activation is not None:
            x = self.quantize_activation(
                x,
                initialize_scales_steps=initialize_scales.activation_steps,
                return_ints=False,
            )
            assert x.dtype == self.cfg.activation_dtype

        weight = self.weight
        assert weight.dtype == self.cfg.weight_dtype
        if self.quantize_weight is not None:
            weight = self.quantize_weight(
                weight,
                initialize_scales_steps=initialize_scales.weight_steps,
                return_ints=False,
            )
            assert weight.dtype == self.cfg.weight_dtype

        output, _ = causal_conv1d(  # pyright: ignore[reportCallIssue]
            x=x,
            weight=weight.type_as(x),
            activation="silu",
            cu_seqlens=cu_seqlens,
        )
        return output


@dataclass(frozen=True, slots=True)
class RoPEArgs:
    sines: Float[Tensor, "position d_head"]
    cosines: Float[Tensor, "position d_head"]


def make_rope_args(
    sequence_length: int,
    cfg: TransformerConfig,
    device: torch.device,
) -> RoPEArgs | None:
    if cfg.rope_base is None:
        return None

    if cfg.half_truncate_rope:
        assert cfg.d_head % 4 == 0
    assert cfg.d_head % 2 == 0

    inv_freq = 1.0 / (
        cfg.rope_base
        ** linspace(
            0,
            2 if cfg.half_truncate_rope else 1,
            steps=cfg.d_head // 2,
            dtype=torch.float32,
            device=device,
        )
    )
    if cfg.half_truncate_rope:
        inv_freq[cfg.d_head // 4 :] = 0
    t = arange(sequence_length, dtype=torch.float32, device=device)
    freqs = outer(t, inv_freq)

    sines = freqs.sin().to(cfg.activation_dtype)
    cosines = freqs.cos().to(cfg.activation_dtype)

    return RoPEArgs(sines=sines, cosines=cosines)


def rope(
    x: Float[Tensor, "batch position n_heads d_head"], args: RoPEArgs | None
) -> Float[Tensor, "batch position n_heads d_head"]:
    assert args is not None

    d_head = x.size(-1)
    assert d_head % 2 == 0
    assert args.sines.dtype == x.dtype
    assert args.cosines.dtype == x.dtype

    sines = args.sines[None, :, None, :]
    cosines = args.cosines[None, :, None, :]

    x0 = x[..., ::2]
    x1 = x[..., 1::2]
    y0 = x0 * cosines + x1 * sines
    y1 = x0 * (-sines) + x1 * cosines
    y = stack((y0, y1), -1).flatten(start_dim=-2)

    assert y.dtype == x.dtype
    assert y.shape == x.shape

    return y


class Attention(Module):
    def __init__(self, cfg: TransformerConfig) -> None:
        super().__init__()

        self.cfg = cfg

        if cfg.d_mla is not None:
            self.latent_projection = CastedLinear(
                cfg.d_model,
                cfg.d_mla,
                cfg.up_init,
                cfg.attention_low_rank_quantization,
                cfg,
            )

        self.query_projection = CastedLinear(
            cfg.d_model,
            cfg.n_query_heads * cfg.d_head,
            cfg.up_init,
            cfg.attention_full_rank_quantization,
            cfg,
        )
        self.key_projection = CastedLinear(
            cfg.d_model if cfg.d_mla is None else cfg.d_mla,
            cfg.n_key_value_heads * cfg.d_head,
            cfg.up_init,
            cfg.attention_low_rank_quantization
            if cfg.d_mla is not None
            else cfg.attention_full_rank_quantization,
            cfg,
        )
        self.value_projection = CastedLinear(
            cfg.d_model if cfg.d_mla is None else cfg.d_mla,
            cfg.n_key_value_heads * cfg.d_head,
            cfg.up_init,
            cfg.attention_low_rank_quantization
            if cfg.d_mla is not None
            else cfg.attention_full_rank_quantization,
            cfg,
        )

        if cfg.qkv_quantization is not None:
            self.quantize_queries = Quantize(
                quant=cfg.qkv_quantization,
                size=(cfg.n_query_heads, cfg.d_head),
                batched=True,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            self.quantize_keys = Quantize(
                quant=cfg.qkv_quantization,
                size=(cfg.n_key_value_heads, cfg.d_head),
                batched=True,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )
            self.quantize_values = Quantize(
                quant=cfg.qkv_quantization,
                size=(cfg.n_key_value_heads, cfg.d_head),
                batched=True,
                scale_weight_dtype=cfg.weight_dtype,
                flatten_scale=cfg.adamw_quantization_scales,
            )

        self.output_projection = CastedLinear(
            cfg.n_query_heads * cfg.d_head,
            cfg.d_model,
            cfg.down_init,
            cfg.attention_full_rank_quantization,
            cfg,
        )

        if cfg.value_embedding_pattern is not None:
            self.value_embedding_coefficients = CastedConstant([0.5, 0.5], cfg)

        if cfg.query_key_norm_gain:
            # gains must be flat and not square for adamw to optimize them and not muon
            self.query_norm_gain = CastedConstant(
                [1.0] * cfg.n_query_heads * cfg.d_head, cfg
            )
            self.key_norm_gain = CastedConstant(
                [1.0] * cfg.n_key_value_heads * cfg.d_head, cfg
            )

    def forward(
        self,
        x: Float[Tensor, "batch position d_model"],
        cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
        rope_args: RoPEArgs | None | None,
        value_embedding: Float[Tensor, "batch position n_heads d_head"] | None,
        window_size: int | Int[Tensor, ""] | None,
        flex_attention_block_mask: BlockMask | None,
        initialize_scales: InitializeScales,
        layer: int,
    ) -> Float[Tensor, "batch position d_model"]:
        batch_size, sequence_length, d_model = x.shape

        latent_or_x = (
            self.latent_projection(x, initialize_scales=initialize_scales)
            if self.cfg.d_mla is not None
            else x
        )

        q = self.query_projection(x, initialize_scales=initialize_scales).view(
            batch_size, sequence_length, self.cfg.n_query_heads, self.cfg.d_head
        )
        k = self.key_projection(latent_or_x, initialize_scales=initialize_scales).view(
            batch_size, sequence_length, self.cfg.n_key_value_heads, self.cfg.d_head
        )
        v = self.value_projection(
            latent_or_x, initialize_scales=initialize_scales
        ).view(batch_size, sequence_length, self.cfg.n_key_value_heads, self.cfg.d_head)

        if self.cfg.value_embedding_pattern is not None:
            coef = self.value_embedding_coefficients()
            if value_embedding is not None:
                v = coef[0] * v + coef[1] * value_embedding
            else:
                v = coef[0] * v

        if self.cfg.query_key_norm:
            q = rms_norm(q)
            k = rms_norm(k)
            if self.cfg.query_key_norm_gain:
                q_gain = self.query_norm_gain().view(
                    self.cfg.n_query_heads, self.cfg.d_head
                )
                k_gain = self.key_norm_gain().view(
                    self.cfg.n_key_value_heads, self.cfg.d_head
                )
                q = q * q_gain
                k = k * k_gain

        assert (rope_args is not None) == (self.cfg.rope_base is not None)
        if self.cfg.rope_base is not None:
            q = rope(q, rope_args)
            k = rope(k, rope_args)

        if self.cfg.qkv_quantization is not None:
            q = self.quantize_queries(
                q,
                initialize_scales_steps=initialize_scales.activation_steps,
                return_ints=False,
            )
            k = self.quantize_keys(
                k,
                initialize_scales_steps=initialize_scales.activation_steps,
                return_ints=False,
            )
            v = self.quantize_values(
                v,
                initialize_scales_steps=initialize_scales.activation_steps,
                return_ints=False,
            )

        window_size_multiplier: int | None = (
            self.cfg.window_size_multipliers[
                self.cfg.attention_weight_sharing_pattern[layer]
            ]
            if self.cfg.window_size_multipliers is not None
            else 1
        )
        assert window_size_multiplier is not None

        y = attention_function(
            AttentionFunctionArguments(
                implementation=self.cfg.attention_implementation,
                queries=q.to(self.cfg.attention_dtype),
                keys=k.to(self.cfg.attention_dtype),
                values=v.to(self.cfg.attention_dtype),
                cumulative_sequence_lengths=cumulative_sequence_lengths,
                max_variable_sequence_length=self.cfg.max_variable_sequence_length,
                window_size=window_size * window_size_multiplier
                if window_size is not None
                else None,
                scale=self.cfg.attention_scale,
                dropout=self.cfg.dropout if self.training else 0.0,
                flex_attention_block_mask=flex_attention_block_mask,
            )
        ).to(self.cfg.activation_dtype)

        y = self.output_projection(
            y.contiguous().view(
                batch_size, sequence_length, self.cfg.n_query_heads * self.cfg.d_head
            ),
            initialize_scales=initialize_scales,
        )

        if self.cfg.dropout != 0:
            y = dropout(y, self.cfg.dropout, training=self.training)

        return y


class KimiLinearAttention(Module):
    def __init__(self, cfg: TransformerConfig) -> None:
        super().__init__()

        self.cfg = cfg

        self.query_projection = CastedLinear(
            cfg.d_model,
            cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            init=cfg.up_init,
            quantization=cfg.kimi_linear_full_rank_quantization,
            cfg=cfg,
        )
        self.query_convolution = CastedFusedConvolutionSiLU(
            d=cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            kernel_size=cfg.kimi_linear_convolution_size,
            init=cfg.convolution_init,
            quantization=cfg.kimi_linear_convolution_quantization,
            cfg=cfg,
        )
        self.key_projection = CastedLinear(
            cfg.d_model,
            cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            init=cfg.up_init,
            quantization=cfg.kimi_linear_full_rank_quantization,
            cfg=cfg,
        )
        self.key_convolution = CastedFusedConvolutionSiLU(
            d=cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            kernel_size=cfg.kimi_linear_convolution_size,
            init=cfg.convolution_init,
            quantization=cfg.kimi_linear_convolution_quantization,
            cfg=cfg,
        )
        self.value_projection = CastedLinear(
            cfg.d_model,
            cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            init=cfg.up_init,
            quantization=cfg.kimi_linear_full_rank_quantization,
            cfg=cfg,
        )
        self.value_convolution = CastedFusedConvolutionSiLU(
            d=cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            kernel_size=cfg.kimi_linear_convolution_size,
            init=cfg.convolution_init,
            quantization=cfg.kimi_linear_convolution_quantization,
            cfg=cfg,
        )

        self.forget_gate_projection = LowRankCastedLinear(
            d_in=cfg.d_model,
            rank=cfg.kimi_linear_d_head,
            d_out=cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            init=cfg.up_init,
            quantization=cfg.kimi_linear_low_rank_quantization,
            cfg=cfg,
        )
        self.beta_projection = CastedLinear(
            cfg.d_model,
            cfg.kimi_linear_n_heads,
            init=cfg.up_init,
            quantization=cfg.kimi_linear_beta_projection_quantization,
            cfg=cfg,
        )

        # TODO: no weight decay on log_baseline_decay_rate and dt_bias

        self.log_baseline_decay_rate = Parameter(
            empty(cfg.kimi_linear_n_heads, dtype=torch.float32).uniform_(1, 16).log()
        )

        dt = rand(cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head, dtype=torch.float32)
        dt = dt * (log(0.1) - log(0.001)) + log(0.001)
        dt = dt.exp()
        dt = dt.clamp(min=1e-4)
        inv_dt = dt + (-(-dt).expm1()).log()
        assert dt.dtype == torch.float32
        assert dt.ndim == 1, (
            "dt should be flat because it should be optimized with adam"
        )
        self.dt_bias = Parameter(inv_dt)

        self.output_gate_projection = LowRankCastedLinear(
            d_in=cfg.d_model,
            rank=cfg.kimi_linear_d_head,
            d_out=cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            init=cfg.up_init,
            quantization=cfg.kimi_linear_low_rank_quantization,
            cfg=cfg,
        )
        self.output_fused_norm_gate = FusedRMSNormGated(
            hidden_size=cfg.kimi_linear_d_head, activation="sigmoid"
        )
        self.output_projection = CastedLinear(
            cfg.kimi_linear_n_heads * cfg.kimi_linear_d_head,
            cfg.d_model,
            init=cfg.down_init,
            quantization=cfg.kimi_linear_full_rank_quantization,
            cfg=cfg,
        )

    def forward(
        self,
        x: Float[Tensor, "batch position d_model"],
        cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
        value_embedding: Float[Tensor, "batch position n_heads d_head"] | None,
        initialize_scales: InitializeScales,
    ) -> Float[Tensor, "batch position d_model"]:
        assert value_embedding is None, (
            "TODO: support value embeddings for kimi linear attention"
        )

        batch_size, sequence_length, d_model = x.shape

        # fla's varlen convention (like flash_attn's): batch size 1, a flat
        # [document + 1] cu_seqlens tensor, state reset at every boundary.
        cu_seqlens: Int[Tensor, " document_plus_one"] | None = None
        if cumulative_sequence_lengths is not None:
            assert cumulative_sequence_lengths.ndim == 2
            assert cumulative_sequence_lengths.size(0) == 1 and batch_size == 1, (
                "with variable length kimi linear attention, batch size must be 1"
            )
            cu_seqlens = cumulative_sequence_lengths.squeeze(0)

        queries = self.query_projection(x, initialize_scales=initialize_scales)
        keys = self.key_projection(x, initialize_scales=initialize_scales)
        values = self.value_projection(x, initialize_scales=initialize_scales)

        queries = self.query_convolution(
            queries, initialize_scales=initialize_scales, cu_seqlens=cu_seqlens
        )
        keys = self.key_convolution(
            keys, initialize_scales=initialize_scales, cu_seqlens=cu_seqlens
        )
        values = self.value_convolution(
            values, initialize_scales=initialize_scales, cu_seqlens=cu_seqlens
        )

        forget_gate = self.forget_gate_projection(
            x, initialize_scales=initialize_scales
        )
        beta = self.beta_projection(x, initialize_scales=initialize_scales).sigmoid()
        output_gate = self.output_gate_projection(
            x, initialize_scales=initialize_scales
        )

        head_shape = (
            batch_size,
            sequence_length,
            self.cfg.kimi_linear_n_heads,
            self.cfg.kimi_linear_d_head,
        )
        queries = queries.view(head_shape)
        keys = keys.view(head_shape)
        values = values.view(head_shape)
        forget_gate = forget_gate.view(head_shape)
        output_gate = output_gate.view(head_shape)

        output, _ = cast(Any, chunk_kda)(
            q=queries,
            k=keys,
            v=values,
            g=forget_gate,
            beta=beta,
            A_log=self.log_baseline_decay_rate,  # do not cast A_log to cfg.activation_dtype like in the reference impleentation
            dt_bias=self.dt_bias,  # do not cast cfg.dt_bias to cfg.activation_dtype like in the reference impleentation
            use_qk_l2norm_in_kernel=True,
            use_gate_in_kernel=True,
            cu_seqlens=cu_seqlens,
        )

        output = self.output_fused_norm_gate(output, output_gate)

        output = output.view(
            batch_size,
            sequence_length,
            self.cfg.kimi_linear_n_heads * self.cfg.kimi_linear_d_head,
        )
        output = self.output_projection(output, initialize_scales=initialize_scales)

        return output


def new_gelu(x: Tensor) -> Tensor:
    return 0.5 * x * (1.0 + tanh(sqrt(2.0 / pi) * (x + 0.044715 * pow(x, 3.0))))


def relu_squared(x: Tensor) -> Tensor:
    return x.relu().square()


ACTIVATION_FUNCTIONS: dict[ActivationFunctionName, Callable[[Tensor], Tensor]] = {
    "gelu": gelu,
    "new_gelu": new_gelu,
    "relu_squared": relu_squared,
}


class MLP(Module):
    def __init__(self, cfg: TransformerConfig) -> None:
        super().__init__()

        self.cfg = cfg

        self.up = CastedLinear(
            cfg.d_model, cfg.d_mlp, cfg.up_init, cfg.mlp_quantization, cfg
        )
        self.down = CastedLinear(
            cfg.d_mlp, cfg.d_model, cfg.down_init, cfg.mlp_quantization, cfg
        )
        self.activation_function = ACTIVATION_FUNCTIONS[cfg.activation_function]

    def forward(
        self,
        x: Float[Tensor, "batch position d_model"],
        initialize_scales: InitializeScales,
    ) -> Float[Tensor, "batch position d_model"]:
        x = self.up(x, initialize_scales=initialize_scales)
        x = self.activation_function(x)
        x = self.down(x, initialize_scales=initialize_scales)
        if self.cfg.dropout != 0:
            x = dropout(x, self.cfg.dropout, training=self.training)
        return x


class Block(Module):
    def __init__(
        self,
        cfg: TransformerConfig,
        layer: int,
        attention: Attention | KimiLinearAttention,
        mlp: MLP,
    ) -> None:
        super().__init__()

        self.cfg = cfg
        self.layer = layer

        if cfg.token_embedding_connections or cfg.prior_embedding_connections:
            self.residual_stream_coefficient = CastedConstant([1.0], cfg)
        if cfg.token_embedding_connections:
            self.token_embedding_coefficient = CastedConstant([0.0], cfg)
        if cfg.prior_embedding_connections:
            self.prior_embedding_coefficient = CastedConstant([0.0], cfg)

        self.attention = attention
        self.mlp = mlp

    def forward(
        self,
        x: Float[Tensor, "batch position d_model"],
        cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
        rope_args: RoPEArgs | None | None,
        token_embeddings: Float[Tensor, "batch position d_model"],
        prior_embeddings: Float[Tensor, "batch position d_model"] | None,
        value_embedding: Float[Tensor, "batch position n_heads d_head"] | None,
        window_size: int | Int[Tensor, ""] | None,
        flex_attention_block_mask: BlockMask | None,
        initialize_scales: InitializeScales,
    ) -> Float[Tensor, "batch position d_model"]:
        if self.cfg.token_embedding_connections or self.cfg.prior_embedding_connections:
            x = self.residual_stream_coefficient() * x
        if self.cfg.token_embedding_connections:
            x = x + self.token_embedding_coefficient() * token_embeddings
        if self.cfg.prior_embedding_connections:
            assert prior_embeddings is not None
            x = x + self.prior_embedding_coefficient() * prior_embeddings

        if isinstance(self.attention, KimiLinearAttention):
            x = x + self.attention(
                rms_norm(x),
                cumulative_sequence_lengths=cumulative_sequence_lengths,
                value_embedding=value_embedding,
                initialize_scales=initialize_scales,
            )
        else:
            x = x + self.attention(
                rms_norm(x),
                cumulative_sequence_lengths=cumulative_sequence_lengths,
                rope_args=rope_args,
                value_embedding=value_embedding,
                window_size=window_size,
                flex_attention_block_mask=flex_attention_block_mask,
                initialize_scales=initialize_scales,
                layer=self.layer,
            )

        x = x + self.mlp(rms_norm(x), initialize_scales=initialize_scales)

        return x


class Transformer(Module):
    def __init__(self, cfg: TransformerConfig) -> None:
        super().__init__()

        self.cfg = cfg

        self.embedding = CastedEmbedding(
            cfg.vocabulary_size,
            cfg.d_model,
            cfg.embedding_init,
            cfg.embedding_quantization,
            cfg,
        )

        if cfg.value_embedding_pattern is not None:
            n_value_embeddings: int = (
                max(i for i in cfg.value_embedding_pattern if i is not None) + 1
            )

            self.value_embeddings = ModuleList(
                [
                    CastedEmbedding(
                        cfg.vocabulary_size,
                        cfg.n_key_value_heads * cfg.d_head,
                        cfg.embedding_init,
                        cfg.embedding_quantization,
                        cfg,
                    )
                    for _ in range(n_value_embeddings)
                ]
            )

        if cfg.prior_embedding:
            self.prior_embedding = CastedLinear(
                cfg.vocabulary_size,
                cfg.d_model,
                cfg.prior_embedding_init,
                cfg.prior_embedding_quantization,
                cfg,
            )

        if cfg.prior_embedding_connections:
            self.initial_prior_embedding_coefficient = CastedConstant([1.0], cfg)

        if cfg.prior_value_embedding:
            assert cfg.value_embedding_pattern is not None
            assert cfg.prior_embedding

            self.prior_value_embeddings = ModuleList(
                [
                    CastedLinear(
                        cfg.vocabulary_size,
                        cfg.n_key_value_heads * cfg.d_head,
                        cfg.prior_embedding_init,
                        cfg.prior_embedding_quantization,
                        cfg,
                    )
                    for _ in range(n_value_embeddings)  # type: ignore
                ]
            )

        if cfg.skip_connections:
            self.skip_connection_weights = CastedConstant(
                [1.0] * (cfg.n_layers // 2), cfg
            )

        n_mlps: int = max(cfg.mlp_weight_sharing_pattern) + 1
        n_attentions: int = max(cfg.attention_weight_sharing_pattern) + 1
        mlps = [MLP(cfg) for _ in range(n_mlps)]
        attentions = [
            KimiLinearAttention(cfg)
            if cfg.kimi_linear is not None and cfg.kimi_linear[i]
            else Attention(cfg)
            for i in range(n_attentions)
        ]
        self.blocks = ModuleList(
            [
                Block(
                    cfg=cfg,
                    layer=layer,
                    attention=attentions[cfg.attention_weight_sharing_pattern[layer]],
                    mlp=mlps[cfg.mlp_weight_sharing_pattern[layer]],
                )
                for layer in range(cfg.n_layers)
            ]
        )

        self.unembedding = CastedLinear(
            cfg.d_model,
            cfg.vocabulary_size,
            cfg.unembedding_init,
            cfg.unembedding_quantization,
            cfg,
        )

        if self.cfg.prior_logit_mixing:
            self.logit_mixing_head = CastedLinear(
                cfg.d_model,
                1,
                cfg.logit_mixing_head_init,
                cfg.logit_mixing_head_quantization,
                cfg,
            )

    def compute_last_activation(
        self,
        input_tokens: Int[Tensor, "batch position"],
        priors: Float[Tensor, "batch position vocabulary_size"] | None,
        cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
        override_window_size: int | Int[Tensor, ""] | None = None,
        initialize_scales: InitializeScales = InitializeScales(None, None),
    ) -> Float[Tensor, "batch position d_model"]:
        if self.cfg.prior_embedding_connections:
            print(  # don't care about graph breaks or device communication latency for this debug print
                " ".join(
                    f"{coef.value.data.item():.4g}"  # type: ignore
                    for coef in [self.initial_prior_embedding_coefficient]
                    + [block.prior_embedding_coefficient for block in self.blocks]
                )
            )

        assert input_tokens.ndim == 2
        batch_size, sequence_length = input_tokens.shape
        assert (priors is not None) == (
            self.cfg.prior_embedding or self.cfg.prior_logit_mixing
        )

        window_size: int | Int[Tensor, ""] | None = (
            override_window_size
            if override_window_size is not None
            else self.cfg.window_size
        )

        flex_attention_block_mask: BlockMask | None = (
            make_flex_attention_block_mask(
                cumulative_sequence_lengths=cumulative_sequence_lengths,
                sequence_length=sequence_length,
                window_size=window_size,
                device=input_tokens.device,
            )
            if self.cfg.attention_implementation == "flex_attention"
            else None
        )

        if priors is not None:
            priors = priors.to(self.cfg.activation_dtype)

        token_embeddings = self.embedding(
            input_tokens, initialize_scales=initialize_scales
        )
        if self.cfg.embedding_norm:
            token_embeddings = rms_norm(token_embeddings)
        if self.cfg.dropout != 0:
            token_embeddings = dropout(
                token_embeddings, self.cfg.dropout, training=self.training
            )
        x = token_embeddings

        if self.cfg.prior_embedding:
            assert priors is not None
            prior_embeddings = self.prior_embedding(
                self.prior_embedding_input(priors),
                initialize_scales=initialize_scales,
            )
            if self.cfg.prior_embedding_norm:
                prior_embeddings = rms_norm(prior_embeddings)
            if self.cfg.dropout != 0:
                prior_embeddings = dropout(
                    prior_embeddings, self.cfg.dropout, training=self.training
                )

            if self.cfg.prior_embedding_connections:
                x = x + self.initial_prior_embedding_coefficient() * prior_embeddings
            else:
                x = x + prior_embeddings
        else:
            prior_embeddings = None

        value_embeddings_by_layer: list[
            Float[Tensor, "batch position n_heads d_head"] | None
        ]
        if self.cfg.value_embedding_pattern is not None:
            head_shape = (
                batch_size,
                sequence_length,
                self.cfg.n_key_value_heads,
                self.cfg.d_head,
            )
            value_embeddings = [
                embedding(input_tokens, initialize_scales=initialize_scales).view(
                    head_shape
                )
                for embedding in self.value_embeddings
            ]
            if self.cfg.prior_value_embedding:
                assert len(value_embeddings) == len(self.prior_value_embeddings)
                for i, projection in enumerate(self.prior_value_embeddings):
                    value_embeddings[i] = value_embeddings[i] + projection(
                        priors, initialize_scales=initialize_scales
                    ).view(head_shape)
            value_embeddings_by_layer = [
                value_embeddings[self.cfg.value_embedding_pattern[layer]]  # type: ignore
                if self.cfg.value_embedding_pattern[layer] is not None
                else None
                for layer in range(self.cfg.n_layers)
            ]
        else:
            value_embeddings_by_layer = [None] * self.cfg.n_layers

        rope_args = make_rope_args(
            sequence_length=sequence_length, cfg=self.cfg, device=x.device
        )
        skip_connections = []

        skip_connection_source_layers: list[int] = list(range(self.cfg.n_layers // 2))
        skip_connection_destination_layers: list[int] = list(
            range((self.cfg.n_layers + 1) // 2, self.cfg.n_layers)
        )
        assert len(skip_connection_source_layers) == len(
            skip_connection_destination_layers
        )

        if self.cfg.skip_connections:
            skip_connection_weights = self.skip_connection_weights()

        for layer, (block, value_embeddings) in enumerate(
            zip(self.blocks, value_embeddings_by_layer, strict=True)
        ):
            if (
                self.cfg.skip_connections
                and layer in skip_connection_destination_layers
            ):
                skip_connection = skip_connections.pop()
                i_connection: int = skip_connection_destination_layers.index(layer)
                x = x + skip_connection_weights[i_connection] * skip_connection  # type: ignore

            x = self.maybe_checkpoint(
                block,
                x,
                cumulative_sequence_lengths=cumulative_sequence_lengths,
                rope_args=rope_args,
                token_embeddings=token_embeddings,
                prior_embeddings=prior_embeddings,
                value_embedding=value_embeddings,
                window_size=window_size,
                flex_attention_block_mask=flex_attention_block_mask,
                initialize_scales=initialize_scales,
            )

            if self.cfg.skip_connections and layer in skip_connection_source_layers:
                skip_connections.append(x)

        x = rms_norm(x)

        return x

    def last_activation_to_logits(
        self,
        last_activation: Float[Tensor, "batch position d_model"],
        priors: Float[Tensor, "batch position vocabulary_size"] | None,
        initialize_scales: InitializeScales = InitializeScales(None, None),
    ) -> Float[Tensor, "batch position vocabulary_size"]:
        logits: Float[Tensor, "batch position vocabulary_size"] = self.unembedding(
            last_activation, initialize_scales=initialize_scales
        )
        if self.cfg.logit_softcap is not None:
            logits = self.cfg.logit_softcap * (logits / self.cfg.logit_softcap).tanh()
        logits = logits.to(self.cfg.logit_dtype)

        if self.cfg.prior_logit_mixing:
            assert priors is not None

            softplus_inverse_of_one: float = 0.5413248546129181
            head_output = self.logit_mixing_head(
                last_activation, initialize_scales=initialize_scales
            ).to(self.cfg.logit_dtype)
            prior_weight: Float[Tensor, "batch position 1"] = softplus(
                head_output + softplus_inverse_of_one
            )

            prior_logprobs = priors.to(self.cfg.logit_dtype).log()
            clamped_prior_logprobs = prior_logprobs.clamp(
                min=self.cfg.prior_logprob_cap
            )
            clamped_prior_logprobs = make_mean_zero(clamped_prior_logprobs, dim=-1)

            logits = logits + prior_weight * clamped_prior_logprobs

        return logits

    def compute_logits(
        self,
        input_tokens: Int[Tensor, "batch position"],
        priors: Float[Tensor, "batch position vocabulary_size"] | None,
        cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
        override_window_size: int | Int[Tensor, ""] | None = None,
        initialize_scales: InitializeScales = InitializeScales(None, None),
    ) -> Float[Tensor, "batch position vocabulary_size"]:
        activation = self.compute_last_activation(
            input_tokens=input_tokens,
            priors=priors,
            cumulative_sequence_lengths=cumulative_sequence_lengths,
            override_window_size=override_window_size,
            initialize_scales=initialize_scales,
        )
        return self.last_activation_to_logits(
            activation, priors=priors, initialize_scales=initialize_scales
        )

    def forward(
        self,
        input_tokens: Int[Tensor, "batch position"],
        priors: Float[Tensor, "batch position vocabulary_size"] | None,
        loss_mask: Bool[Tensor, "batch position"],
        output_tokens: Int[Tensor, "batch position"],
        cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
        override_window_size: int | Int[Tensor, ""] | None = None,
        initialize_scales: InitializeScales = InitializeScales(None, None),
    ) -> Float[Tensor, ""]:
        assert input_tokens.shape == output_tokens.shape
        assert input_tokens.ndim == 2

        activation = self.compute_last_activation(
            input_tokens=input_tokens,
            priors=priors,
            cumulative_sequence_lengths=cumulative_sequence_lengths,
            override_window_size=override_window_size,
            initialize_scales=initialize_scales,
        )

        logits = self.last_activation_to_logits(
            activation, priors=priors, initialize_scales=initialize_scales
        )

        loss = cross_entropy(
            logits.view(-1, logits.size(-1)),
            output_tokens.flatten(),
            reduction="none",
        )

        return where(loss_mask.flatten(), loss.to(torch.float32), 0.0).sum()

    def prior_embedding_input(
        self, priors: Float[Tensor, "batch position vocabulary_size"]
    ) -> Float[Tensor, "batch position vocabulary_size"]:
        if not self.cfg.prior_embedding_on_logprobs:
            return priors

        logprobs = priors.log()
        logprobs = logprobs.clamp(min=self.cfg.prior_logprob_cap)
        logprobs = make_mean_zero(logprobs, dim=-1)
        return logprobs

    def maybe_checkpoint(self, f, *args, **kwargs) -> Tensor:
        if not self.cfg.gradient_checkpointing:
            return f(*args, **kwargs)
        return checkpoint(f, *args, use_reentrant=False, **kwargs)  # type: ignore


@dataclass(frozen=True, slots=True)
class PrecisionAndCount:
    n_parameters: int
    bits_per_parameter: float

    @property
    def bytes(self) -> float:
        return self.n_parameters * self.bits_per_parameter / 8


@dataclass(frozen=True, slots=True)
class ParameterCountsByPrecision:
    counts: list[PrecisionAndCount]

    @property
    def bytes(self) -> float:
        return sum(c.bytes for c in self.counts)

    @property
    def n_parameters(self) -> int:
        return sum(c.n_parameters for c in self.counts)


def parameter_counts_by_precision(
    module: Module, full_precision_bits_per_parameter: int
) -> ParameterCountsByPrecision:
    bits_per_parameter_to_count: dict[float, int] = defaultdict(lambda: 0)

    quantized_parameter_ids: set[int] = set()

    for submodule in module.modules():
        if not isinstance(
            submodule, (CastedLinear, CastedEmbedding, CastedFusedConvolutionSiLU)
        ):
            continue
        if submodule.quantize_weight is None:
            continue
        weight_quant = submodule.quantize_weight.quant
        if weight_quant is None:
            continue

        bits_per_quantized: float = log2(weight_quant.buckets)
        bits_per_scale: float = 8 * weight_quant.scale_dtype.itemsize
        assert weight_quant.block_size is not None
        bits_per_parameter: float = (
            bits_per_quantized + bits_per_scale / weight_quant.block_size
        )

        count: int = submodule.weight.numel()

        bits_per_parameter_to_count[bits_per_parameter] += count

        quantized_parameter_ids.add(id(submodule.weight))
        quantized_parameter_ids.add(id(submodule.quantize_weight.scale))

    full_precision_parameters: list[Parameter] = [
        p for p in module.parameters() if id(p) not in quantized_parameter_ids
    ]
    full_precision_parameter_count: int = sum(
        p.numel() for p in full_precision_parameters
    )

    bits_per_parameter_to_count[full_precision_bits_per_parameter] += (
        full_precision_parameter_count
    )

    return ParameterCountsByPrecision(
        counts=[
            PrecisionAndCount(n_parameters=count, bits_per_parameter=bits)
            for bits, count in bits_per_parameter_to_count.items()
        ]
    )


@dataclass(frozen=True, slots=True)
class TransformerParameterCounts:
    total: ParameterCountsByPrecision
    active: ParameterCountsByPrecision
    non_embedding_unembedding: ParameterCountsByPrecision


def transformer_parameter_counts(model: Transformer) -> TransformerParameterCounts:
    full_precision_bits_per_parameter: int = 8 * min(
        model.cfg.weight_dtype.itemsize, model.cfg.activation_dtype.itemsize
    )

    active_submodules: list[Module] = [model.blocks, model.unembedding]
    if model.cfg.skip_connections:
        active_submodules.append(model.skip_connection_weights)
    if model.cfg.value_embedding_pattern is not None:
        active_submodules.append(model.value_embeddings)
    if model.cfg.prior_embedding:
        active_submodules.append(model.prior_embedding)
    if model.cfg.prior_value_embedding:
        active_submodules.append(model.prior_value_embeddings)

    non_embedding_unembedding_submodules: list[Module] = [
        model.blocks,
        model.unembedding,
    ]

    return TransformerParameterCounts(
        total=parameter_counts_by_precision(
            model,
            full_precision_bits_per_parameter=full_precision_bits_per_parameter,
        ),
        active=parameter_counts_by_precision(
            ModuleList(active_submodules),
            full_precision_bits_per_parameter=full_precision_bits_per_parameter,
        ),
        non_embedding_unembedding=parameter_counts_by_precision(
            ModuleList(non_embedding_unembedding_submodules),
            full_precision_bits_per_parameter=full_precision_bits_per_parameter,
        ),
    )


def compile_transformer(model: Transformer) -> Transformer:
    model = torch.compile(model)  # type: ignore
    model.compute_last_activation = torch.compile(model.compute_last_activation)
    model.compute_logits = torch.compile(model.compute_logits)
    model.last_activation_to_logits = torch.compile(model.last_activation_to_logits)
    return model


# ruff: noqa: F722
