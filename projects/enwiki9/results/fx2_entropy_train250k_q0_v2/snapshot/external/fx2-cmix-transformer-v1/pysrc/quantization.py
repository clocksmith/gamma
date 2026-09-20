import torch
from torch import Tensor, inference_mode, tensor, zeros, no_grad, maximum
from torch.nn import Module, Parameter
from torch.autograd import Function
from torch.autograd.function import FunctionCtx
from math import sqrt, prod
from dataclasses import dataclass, replace
from jaxtyping import Float, Bool
from typing import Literal


# TODO: quantize positive only tensors (after relu)


ScaleInit = Literal["scaled_mean", "scaled_max"]


@dataclass(frozen=True, slots=True)
class Quantization:
    buckets: int
    block_size: int | None
    scale_dtype: torch.dtype
    arithmetic_dtype: torch.dtype
    scale_init: ScaleInit
    epsilon: float | None

    @property
    def int_range(self) -> tuple[int, int]:
        qmin: int = -(self.buckets // 2)
        qmax: int = (self.buckets - 1) // 2
        assert qmax - qmin + 1 == self.buckets
        return qmin, qmax

    @property
    def qmin(self) -> int:
        return self.int_range[0]

    @property
    def qmax(self) -> int:
        return self.int_range[1]

    def __post_init__(self) -> None:
        assert self.buckets != 2, (
            "the code is incorrect for 1 bit quantization but it's not used so i didn't fix it"
        )


class Quantize(Module):
    def __init__(
        self,
        quant: Quantization,
        size: tuple[int, ...],
        batched: bool,
        scale_weight_dtype: torch.dtype,
        flatten_scale: bool,
    ) -> None:
        super().__init__()

        if quant.block_size is None:
            quant = replace(quant, block_size=size[-1])
            assert quant.block_size is not None

        self.quant = quant

        self.size = size
        self.batched = batched

        assert size[-1] % quant.block_size == 0
        self.n_blocks = prod(size) // quant.block_size

        scale_shape: tuple[int, ...] = size[:-1] + (size[-1] // quant.block_size,)
        if flatten_scale:
            scale_shape = (prod(scale_shape),)
        assert prod(scale_shape) == self.n_blocks

        self.scale = Parameter(zeros(size=scale_shape, dtype=scale_weight_dtype))

    def initialize_scale(
        self,
        sample_blocks: Float[Tensor, "batch n_blocks block_size"],
        steps: int,
    ) -> None:
        with no_grad():  # there is a small chance that decorating the function with `@no_grad()` will interact with torch.copile in ore cursed ways than `with no_grad()`. it should probabbly not happen because it's mostly only a thing in older versions of torch. but we use `with no_grad()` instead of `@no_grad()` just in case. also, `inference_mode` sometimes can  interact with torch.compile in more cursed ways than `no_grad`, though this is also mostly only a thing in older versions of torch
            scale: Float[Tensor, " n_blocks"]

            if self.quant.scale_init == "scaled_mean":
                k: float = 2 / sqrt(self.quant.qmax)
                scale = k * sample_blocks.type_as(self.scale).abs().mean((0, -1))
                scale = scale.reshape(self.scale.shape).type_as(self.scale)
                self.scale.add_(scale / steps)
            elif self.quant.scale_init == "scaled_max":
                k: float = 1 / self.quant.qmax
                scale = k * sample_blocks.type_as(self.scale).abs().amax((0, -1))
                scale = scale.reshape(self.scale.shape).type_as(self.scale)
                maximum(self.scale, scale, out=self.scale)
            else:
                raise ValueError(f"unknown scale init '{self.quant.scale_init}'")

    def reshape_input(
        self, input: Tensor
    ) -> Float[Tensor, "batch n_blocks block_size"]:
        assert self.quant.block_size is not None

        if not self.batched:
            assert input.shape == self.size
            return input.view(1, self.n_blocks, self.quant.block_size)

        assert len(input.shape) >= len(self.size)
        assert input.shape[-len(self.size) :] == self.size
        return input.view(-1, self.n_blocks, self.quant.block_size)

    def forward(
        self, input: Tensor, initialize_scales_steps: int | None, return_ints: bool
    ) -> Tensor:
        assert self.quant.block_size is not None

        blocks = self.reshape_input(input)

        if initialize_scales_steps is not None:
            self.initialize_scale(blocks, steps=initialize_scales_steps)
            return input

        fake_quantized: Tensor = QuantizeFunction.apply(  # type: ignore
            blocks, self.scale.view(-1), self.quant, return_ints
        )

        if return_ints:
            assert fake_quantized.dtype == torch.int64
        else:
            assert fake_quantized.dtype == input.dtype

        return fake_quantized.view(input.shape)

    @inference_mode()
    def serialize_scale(self) -> bytes:
        scale = self.scale.to(self.quant.scale_dtype)
        assert scale.dtype == torch.bfloat16
        return scale.cpu().detach().view(torch.uint16).numpy().tobytes()


_STRETCHED_ELASTIC_CLIP_VAL: float = 1 - 1e-2


def _stretched_elastic_params(buckets: int) -> tuple[float, float]:
    # n_levels, shift from https://arxiv.org/abs/2502.02631 (StretchedElasticQuant)
    if buckets == 3:
        return 1.5, 0.0
    if buckets == 4:
        return 2.0, 0.5
    raise ValueError(f"no StretchedElasticQuant params for buckets={buckets}")


class QuantizeFunction(Function):
    @staticmethod
    def forward(
        ctx: FunctionCtx,
        blocks: Float[Tensor, "batch n_blocks block_size"],
        flat_scale: Float[Tensor, " n_blocks"],
        quant: Quantization,
        return_ints: bool,
    ) -> Float[Tensor, "batch n_blocks block_size"]:
        assert quant.block_size is not None
        assert quant.buckets >= 2

        input_dtype = blocks.dtype
        blocks = blocks.to(quant.arithmetic_dtype)

        assert blocks.ndim == 3
        assert flat_scale.ndim == 1
        assert blocks.size(1) == flat_scale.numel()
        assert blocks.size(2) == quant.block_size

        scale: Float[Tensor, "1 n_blocks 1"] = flat_scale.unsqueeze(0).unsqueeze(-1)
        scale = scale.to(quant.scale_dtype).type_as(blocks)
        if quant.epsilon is not None:
            epsilon = tensor(quant.epsilon, dtype=scale.dtype, device=scale.device)
            scale = (2 * (scale >= 0).type_as(scale) - 1) * scale.abs().maximum(epsilon)

        scaled_blocks = blocks / scale

        if quant.buckets == 2:
            # 1-bit binary quantization from https://arxiv.org/abs/2502.02631
            quantized_blocks = nonzero_sign(scaled_blocks)
            dequantized_blocks = scale * quantized_blocks
        elif quant.buckets in (3, 4):
            # 1.58-bit / 2-bit StretchedElasticQuant from https://arxiv.org/abs/2502.02631
            n_levels, shift = _stretched_elastic_params(quant.buckets)
            clamped = scaled_blocks.clamp(
                -_STRETCHED_ELASTIC_CLIP_VAL, _STRETCHED_ELASTIC_CLIP_VAL
            )
            quantized_blocks = ((clamped * n_levels - shift).round() + shift) / n_levels
            dequantized_blocks = scale * quantized_blocks
        else:
            quantized_blocks = scaled_blocks.round().clamp(quant.qmin, quant.qmax)
            dequantized_blocks = scale * quantized_blocks

        ctx.save_for_backward(scaled_blocks)
        ctx.quant = quant  # type: ignore[attr-defined]

        if return_ints:
            return quantized_blocks.to(torch.int64)

        return dequantized_blocks.to(input_dtype)

    @staticmethod
    def backward(  # type: ignore[reportIncompatibleMethodOverride]
        ctx: FunctionCtx, grad_out: Float[Tensor, "batch n_blocks block_size"]
    ) -> tuple[
        Float[Tensor, "batch n_blocks bolck_size"],
        Float[Tensor, " n_blocks"],
        None,
        None,
    ]:
        scaled_blocks: Float[Tensor, "batch n_blocks block"]
        (scaled_blocks,) = ctx.saved_tensors  # type: ignore[attr-defined]
        quant: Quantization = ctx.quant  # type: ignore[attr-defined]

        grad_dtype = grad_out.dtype
        grad_out = grad_out.to(quant.arithmetic_dtype)

        if quant.buckets == 2:
            too_small: Bool[Tensor, "batch n_blocks block_size"] = scaled_blocks < -1
            too_big: Bool[Tensor, "batch n_blocks block_size"] = 1 < scaled_blocks
            within_bounds: Bool[Tensor, "batch n_blocks block_size"] = (
                too_small.logical_not().logical_and(too_big.logical_not())
            )

            grad_input: Float[Tensor, "batch n_blocks block_size"] = (
                grad_out * within_bounds.type_as(grad_out)
            )

            grad_flat_scale: Float[Tensor, " n_blocks"] = (
                (grad_out * nonzero_sign(scaled_blocks))
                .sum(0)  # sum along batch dimension
                .sum(-1)  # sum along block_size dimension
            )
            # paper grad_scale = 1 / sqrt(numel * Qp_initial) with Qp_initial = 1
            grad_flat_scale = grad_flat_scale / sqrt(scaled_blocks.numel())
        elif quant.buckets in (3, 4):
            n_levels, shift = _stretched_elastic_params(quant.buckets)
            clip_val = _STRETCHED_ELASTIC_CLIP_VAL
            qp_paper = (n_levels - shift) / n_levels
            qn_paper = -qp_paper

            too_small = scaled_blocks < -clip_val
            too_big = clip_val < scaled_blocks
            within_bounds = too_small.logical_not().logical_and(too_big.logical_not())

            grad_input = grad_out * within_bounds.type_as(grad_out)

            clamped = scaled_blocks.clamp(-clip_val, clip_val)
            rounded = ((clamped * n_levels - shift).round() + shift) / n_levels
            middle = rounded - scaled_blocks

            grad_flat_scale = (
                (
                    grad_out
                    * (
                        too_small.type_as(grad_out) * qn_paper
                        + too_big.type_as(grad_out) * qp_paper
                        + within_bounds.type_as(grad_out) * middle
                    )
                )
                .sum(0)
                .sum(-1)
            )
            # paper grad_scale = 1 / sqrt(numel * Qp_initial) with Qp_initial = 1
            grad_flat_scale = grad_flat_scale / sqrt(scaled_blocks.numel())
        else:
            too_small = scaled_blocks < quant.qmin
            too_big = quant.qmax < scaled_blocks
            within_bounds = too_small.logical_not().logical_and(too_big.logical_not())

            grad_input = grad_out * within_bounds.type_as(grad_out)

            grad_flat_scale = (
                (
                    grad_out
                    * (
                        too_small.type_as(grad_out) * quant.qmin
                        + too_big.type_as(grad_out) * quant.qmax
                        + within_bounds.type_as(grad_out)
                        * (scaled_blocks.round() - scaled_blocks)
                    )
                )
                .sum(0)  # sum along batch dimension
                .sum(-1)  # sum along block_size dimension
            )
            grad_flat_scale = grad_flat_scale / sqrt(scaled_blocks.numel() * quant.qmax)

        return grad_input.to(grad_dtype), grad_flat_scale.to(grad_dtype), None, None


def nonzero_sign(x: Tensor) -> Tensor:
    return 2 * (x >= 0).type_as(x) - 1


# ruff: noqa: F722
