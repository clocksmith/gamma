import torch
from torch import Tensor, inference_mode, tensor, zeros, no_grad, maximum
from torch.nn import Module, Parameter
from torch.autograd import Function
from torch.autograd.function import FunctionCtx
from math import sqrt, prod
from dataclasses import dataclass, replace
from typing import Literal
ScaleInit = Literal['scaled_mean', 'scaled_max']

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
        return (qmin, qmax)

    @property
    def qmin(self) -> int:
        return self.int_range[0]

    @property
    def qmax(self) -> int:
        return self.int_range[1]

    def __post_init__(self) -> None:
        assert self.buckets != 2, "the code is incorrect for 1 bit quantization but it's not used so i didn't fix it"

class Quantize(Module):

    def __init__(self, quant: Quantization, size: tuple[int, ...], batched: bool, scale_weight_dtype: torch.dtype, flatten_scale: bool) -> None:
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

    def initialize_scale(self, sample_blocks: Tensor, steps: int) -> None:
        with no_grad():
            scale: Tensor
            if self.quant.scale_init == 'scaled_mean':
                k: float = 2 / sqrt(self.quant.qmax)
                scale = k * sample_blocks.type_as(self.scale).abs().mean((0, -1))
                scale = scale.reshape(self.scale.shape).type_as(self.scale)
                self.scale.add_(scale / steps)
            elif self.quant.scale_init == 'scaled_max':
                k: float = 1 / self.quant.qmax
                scale = k * sample_blocks.type_as(self.scale).abs().amax((0, -1))
                scale = scale.reshape(self.scale.shape).type_as(self.scale)
                maximum(self.scale, scale, out=self.scale)
            else:
                raise ValueError(f"unknown scale init '{self.quant.scale_init}'")

    def reshape_input(self, input: Tensor) -> Tensor:
        assert self.quant.block_size is not None
        if not self.batched:
            assert input.shape == self.size
            return input.view(1, self.n_blocks, self.quant.block_size)
        assert len(input.shape) >= len(self.size)
        assert input.shape[-len(self.size):] == self.size
        return input.view(-1, self.n_blocks, self.quant.block_size)

    def forward(self, input: Tensor, initialize_scales_steps: int | None, return_ints: bool) -> Tensor:
        assert self.quant.block_size is not None
        blocks = self.reshape_input(input)
        if initialize_scales_steps is not None:
            self.initialize_scale(blocks, steps=initialize_scales_steps)
            return input
        fake_quantized: Tensor = QuantizeFunction.apply(blocks, self.scale.view(-1), self.quant, return_ints)
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
_STRETCHED_ELASTIC_CLIP_VAL: float = 1 - 0.01

def _stretched_elastic_params(buckets: int) -> tuple[float, float]:
    if buckets == 3:
        return (1.5, 0.0)
    if buckets == 4:
        return (2.0, 0.5)
    raise ValueError(f'no StretchedElasticQuant params for buckets={buckets}')

class QuantizeFunction(Function):

    @staticmethod
    def forward(ctx: FunctionCtx, blocks: Tensor, flat_scale: Tensor, quant: Quantization, return_ints: bool) -> Tensor:
        assert quant.block_size is not None
        assert quant.buckets >= 2
        input_dtype = blocks.dtype
        blocks = blocks.to(quant.arithmetic_dtype)
        assert blocks.ndim == 3
        assert flat_scale.ndim == 1
        assert blocks.size(1) == flat_scale.numel()
        assert blocks.size(2) == quant.block_size
        scale: Tensor = flat_scale.unsqueeze(0).unsqueeze(-1)
        scale = scale.to(quant.scale_dtype).type_as(blocks)
        if quant.epsilon is not None:
            epsilon = tensor(quant.epsilon, dtype=scale.dtype, device=scale.device)
            scale = (2 * (scale >= 0).type_as(scale) - 1) * scale.abs().maximum(epsilon)
        scaled_blocks = blocks / scale
        if quant.buckets == 2:
            quantized_blocks = nonzero_sign(scaled_blocks)
            dequantized_blocks = scale * quantized_blocks
        elif quant.buckets in (3, 4):
            n_levels, shift = _stretched_elastic_params(quant.buckets)
            clamped = scaled_blocks.clamp(-_STRETCHED_ELASTIC_CLIP_VAL, _STRETCHED_ELASTIC_CLIP_VAL)
            quantized_blocks = ((clamped * n_levels - shift).round() + shift) / n_levels
            dequantized_blocks = scale * quantized_blocks
        else:
            quantized_blocks = scaled_blocks.round().clamp(quant.qmin, quant.qmax)
            dequantized_blocks = scale * quantized_blocks
        ctx.save_for_backward(scaled_blocks)
        ctx.quant = quant
        if return_ints:
            return quantized_blocks.to(torch.int64)
        return dequantized_blocks.to(input_dtype)

    @staticmethod
    def backward(ctx: FunctionCtx, grad_out: Tensor) -> tuple[Tensor, Tensor, None, None]:
        scaled_blocks: Tensor
        scaled_blocks, = ctx.saved_tensors
        quant: Quantization = ctx.quant
        grad_dtype = grad_out.dtype
        grad_out = grad_out.to(quant.arithmetic_dtype)
        if quant.buckets == 2:
            too_small: Tensor = scaled_blocks < -1
            too_big: Tensor = 1 < scaled_blocks
            within_bounds: Tensor = too_small.logical_not().logical_and(too_big.logical_not())
            grad_input: Tensor = grad_out * within_bounds.type_as(grad_out)
            grad_flat_scale: Tensor = (grad_out * nonzero_sign(scaled_blocks)).sum(0).sum(-1)
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
            grad_flat_scale = (grad_out * (too_small.type_as(grad_out) * qn_paper + too_big.type_as(grad_out) * qp_paper + within_bounds.type_as(grad_out) * middle)).sum(0).sum(-1)
            grad_flat_scale = grad_flat_scale / sqrt(scaled_blocks.numel())
        else:
            too_small = scaled_blocks < quant.qmin
            too_big = quant.qmax < scaled_blocks
            within_bounds = too_small.logical_not().logical_and(too_big.logical_not())
            grad_input = grad_out * within_bounds.type_as(grad_out)
            grad_flat_scale = (grad_out * (too_small.type_as(grad_out) * quant.qmin + too_big.type_as(grad_out) * quant.qmax + within_bounds.type_as(grad_out) * (scaled_blocks.round() - scaled_blocks))).sum(0).sum(-1)
            grad_flat_scale = grad_flat_scale / sqrt(scaled_blocks.numel() * quant.qmax)
        return (grad_input.to(grad_dtype), grad_flat_scale.to(grad_dtype), None, None)

def nonzero_sign(x: Tensor) -> Tensor:
    return 2 * (x >= 0).type_as(x) - 1
