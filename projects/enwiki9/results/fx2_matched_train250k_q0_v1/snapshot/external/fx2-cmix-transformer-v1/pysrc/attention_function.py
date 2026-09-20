from torch.nn.functional import scaled_dot_product_attention
from torch.nn.attention.flex_attention import flex_attention, BlockMask
from torch import Tensor, arange
import torch
from dataclasses import dataclass
from jaxtyping import Float, Int, Bool
from typing import Literal


flex_attention = torch.compile(flex_attention)


_flash_attn = None


def get_flash_attn():
    global _flash_attn
    if _flash_attn is not None:
        return _flash_attn

    import flash_attn  # type: ignore

    _flash_attn = flash_attn
    return _flash_attn


AttentionImplementation = Literal["sdpa", "flash_attention_2", "flex_attention"]


HeadTensor = Float[Tensor, "batch position n_heads d_head"]


@dataclass(frozen=True, slots=True)
class AttentionFunctionArguments:
    implementation: AttentionImplementation
    queries: Float[Tensor, "batch position n_heads d_head"]
    keys: Float[Tensor, "batch position n_heads d_head"]
    values: Float[Tensor, "batch position n_heads d_head"]
    cumulative_sequence_lengths: Int[Tensor, "batch document"] | None
    max_variable_sequence_length: int | None
    window_size: int | Int[Tensor, ""] | None
    scale: float | None
    dropout: float
    flex_attention_block_mask: BlockMask | None

    @property
    def batch_size(self) -> int:
        return self.queries.size(0)

    @property
    def sequence_length(self) -> int:
        return self.queries.size(1)

    @property
    def device(self) -> torch.device:
        return self.queries.device


def attention_function(
    args: AttentionFunctionArguments,
) -> Float[Tensor, "batch position n_heads d_head"]:
    validate_attention_arguments(args)

    is_variable_length: bool = args.cumulative_sequence_lengths is not None
    match (args.implementation, is_variable_length):
        case ("sdpa", _):
            return sdpa_attention_function(args)

        case ("flash_attention_2", False):
            return flash_attention_2_fixed_length_attention_function(args)

        case ("flash_attention_2", True):
            return flash_attention_2_variable_length_attention_function(args)

        case ("flex_attention", True):
            return flex_attention_variable_length_attention_function(args)

        case ("flex_attention", False):
            assert False, "flex_attention only supports variable sequence lengths"

        case _:
            assert False, (
                f'invalid attention (implementation, is_variable_length) combination ("{args.implementation}", {is_variable_length})'
            )


def validate_attention_arguments(args: AttentionFunctionArguments) -> None:
    assert args.queries.ndim == 4
    assert args.keys.ndim == 4
    assert args.values.ndim == 4
    assert args.keys.shape == args.values.shape
    assert args.queries.shape[0] == args.keys.shape[0]
    assert args.queries.shape[1] == args.keys.shape[1]
    assert args.queries.shape[3] == args.keys.shape[3]
    assert args.queries.shape[2] % args.keys.shape[2] == 0
    if args.cumulative_sequence_lengths is not None:
        assert args.cumulative_sequence_lengths.ndim == 2
        assert args.cumulative_sequence_lengths.size(0) == args.batch_size
        assert args.cumulative_sequence_lengths.dtype == torch.int32
    if args.max_variable_sequence_length is not None:
        assert isinstance(args.max_variable_sequence_length, int)
    if args.window_size is not None:
        assert isinstance(args.window_size, (int, Tensor))
    if isinstance(args.window_size, Tensor):
        assert args.window_size.ndim == 0
        assert args.window_size.dtype in [torch.int32, torch.int64]
    if args.scale is not None:
        assert isinstance(args.scale, float)
    assert isinstance(args.dropout, float)
    assert (args.flex_attention_block_mask is not None) == (
        args.implementation == "flex_attention"
    )


def sdpa_attention_function(
    args: AttentionFunctionArguments,
) -> Float[Tensor, "batch position n_heads d_head"]:
    mask: (
        Bool[Tensor, "query_position key_value_position"]
        | Bool[Tensor, "batch query_position key_position"]
        | None
    )
    if args.window_size is None and args.cumulative_sequence_lengths is None:
        mask = None
    else:
        mask = causal_mask(sequence_length=args.sequence_length, device=args.device)
        if args.window_size is not None:
            mask = mask & window_mask(
                sequence_length=args.sequence_length,
                window_size=args.window_size,
                device=args.device,
            )
        if args.cumulative_sequence_lengths is not None:
            mask = mask & document_mask(
                sequence_length=args.sequence_length,
                cumulative_sequence_lengths=args.cumulative_sequence_lengths,
                device=args.device,
            )

    return scaled_dot_product_attention(
        query=args.queries.transpose(-2, -3),
        key=args.keys.transpose(-2, -3),
        value=args.values.transpose(-2, -3),
        attn_mask=mask,
        scale=args.scale,
        dropout_p=args.dropout,
        is_causal=mask is None,
        enable_gqa=args.queries.size(-2) != args.keys.size(-2),
    ).transpose(-2, -3)


def causal_mask(
    sequence_length: int, device: torch.device
) -> Bool[Tensor, "query_position key_value_position"]:
    positions: Int[Tensor, " position"] = arange(
        0, sequence_length, dtype=torch.int32, device=device
    )
    query_positions: Int[Tensor, "position 1"] = positions.unsqueeze(-1)
    key_value_positions: Int[Tensor, "1 position"] = positions.unsqueeze(-2)
    return key_value_positions <= query_positions


def window_mask(
    sequence_length: int, window_size: int | Int[Tensor, ""], device: torch.device
) -> Bool[Tensor, "query_position key_value_position"]:
    positions: Int[Tensor, " position"] = arange(
        0, sequence_length, dtype=torch.int32, device=device
    )
    query_positions: Int[Tensor, "position 1"] = positions.unsqueeze(-1)
    key_value_positions: Int[Tensor, "1 position"] = positions.unsqueeze(-2)
    return query_positions - key_value_positions < window_size


def document_indices(
    sequence_length: int,
    cumulative_sequence_lengths: Int[Tensor, "batch document"],
    device: torch.device,
) -> Bool[Tensor, "batch position"]:
    positions: Int[Tensor, "1 position 1"] = (
        arange(sequence_length, dtype=torch.int32, device=device)
        .unsqueeze(0)
        .unsqueeze(-1)
    )
    expanded_cumulative_sequence_lengths: Int[Tensor, "batch 1 document"] = (
        cumulative_sequence_lengths.unsqueeze(-2)
    )
    return (positions >= expanded_cumulative_sequence_lengths).to(torch.int32).sum(-1)


def document_mask(
    sequence_length: int,
    cumulative_sequence_lengths: Int[Tensor, "batch document"],
    device: torch.device,
) -> Bool[Tensor, "batch query_position key_value_position"]:
    document_ids: Int[Tensor, "batch position"] = document_indices(
        sequence_length=sequence_length,
        cumulative_sequence_lengths=cumulative_sequence_lengths,
        device=device,
    )
    return document_ids.unsqueeze(-1) == document_ids.unsqueeze(-2)


def flash_attention_2_fixed_length_attention_function(
    args: AttentionFunctionArguments,
) -> Float[Tensor, "batch position n_heads d_head"]:
    assert args.cumulative_sequence_lengths is None
    assert not isinstance(args.window_size, Tensor), (
        "flash_attention_2 does not support dynamic attention window sizes"
    )

    return get_flash_attn().flash_attn_func(  # type: ignore
        q=args.queries,
        k=args.keys,
        v=args.values,
        window_size=(args.window_size - 1, 0)
        if args.window_size is not None
        else (-1, -1),
        softmax_scale=args.scale,
        dropout_p=args.dropout,
        causal=True,
    )


def flash_attention_2_variable_length_attention_function(
    args: AttentionFunctionArguments,
) -> Float[Tensor, "batch position n_heads d_head"]:
    assert args.cumulative_sequence_lengths is not None
    assert not isinstance(args.window_size, Tensor), (
        "flash_attention_2 does not support dynamic attention window sizes"
    )
    assert args.batch_size == 1, (
        "with variable length flash_attention_2, batch size must be 1"
    )
    assert args.max_variable_sequence_length is not None, (
        "with variable length flash_attention_2, max_variable_sequence_length must be provided"
    )

    return get_flash_attn().flash_attn_varlen_func(  # type: ignore
        q=args.queries.squeeze(0),
        k=args.keys.squeeze(0),
        v=args.values.squeeze(0),
        cu_seqlens_q=args.cumulative_sequence_lengths.squeeze(0),
        cu_seqlens_k=args.cumulative_sequence_lengths.squeeze(0),
        max_seqlen_q=args.max_variable_sequence_length,
        max_seqlen_k=args.max_variable_sequence_length,
        dropout_p=args.dropout,
        window_size=(args.window_size - 1, 0)
        if args.window_size is not None
        else (-1, -1),
        softmax_scale=args.scale,
        causal=True,
    )


def divide_evenly(x: int, y: int) -> int:
    assert x % y == 0
    return x // y


def causal_block_mask(
    sequence_length: int, block_size: int, full: bool, device: torch.device
) -> Bool[Tensor, "query_block key_value_block"]:
    sequence_length_in_blocks: int = divide_evenly(sequence_length, block_size)
    positions: Int[Tensor, " position"] = arange(
        0, sequence_length_in_blocks, dtype=torch.int32, device=device
    )
    query_positions: Int[Tensor, "position 1"] = positions.unsqueeze(-1)
    key_value_positions: Int[Tensor, "1 position"] = positions.unsqueeze(-2)
    if full and block_size != 1:
        return key_value_positions < query_positions
    else:
        return key_value_positions <= query_positions


def window_block_mask(
    sequence_length: int,
    block_size: int,
    window_size: int | Int[Tensor, ""],
    full: bool,
    device: torch.device,
) -> Bool[Tensor, "query_block key_value_block"]:
    sequence_length_in_blocks: int = divide_evenly(sequence_length, block_size)

    positions: Int[Tensor, " position"] = arange(
        0, sequence_length_in_blocks, dtype=torch.int32, device=device
    )
    query_positions: Int[Tensor, "position 1"] = positions.unsqueeze(-1)
    key_value_positions: Int[Tensor, "1 position"] = positions.unsqueeze(-2)
    diff: Int[Tensor, "query_position key_value_position"] = (
        query_positions - key_value_positions
    )
    if full:
        return (diff + 1) * block_size - 1 < window_size
    else:
        return (diff - 1) * block_size + 1 < window_size


def document_block_mask(
    document_ids: Int[Tensor, " position"], full: bool, block_size: int
) -> Int[Tensor, " query_block key_value_block"]:
    min_document_ids: Int[Tensor, " block"] = document_ids.view(-1, block_size).amin(-1)
    max_document_ids: Int[Tensor, " block"] = document_ids.view(-1, block_size).amax(-1)
    if full:
        return (
            (min_document_ids.unsqueeze(-1) == max_document_ids.unsqueeze(-1))
            & (min_document_ids.unsqueeze(-2) == max_document_ids.unsqueeze(-2))
            & (min_document_ids.unsqueeze(-1) == min_document_ids.unsqueeze(-2))
        )
    else:
        return (min_document_ids.unsqueeze(-1) <= max_document_ids.unsqueeze(-2)) & (
            min_document_ids.unsqueeze(-2) <= max_document_ids.unsqueeze(-1)
        )


def block_mask(
    sequence_length: int,
    document_ids: Int[Tensor, " position"],
    window_size: int | Int[Tensor, ""] | None,
    full: bool,
    block_size: int,
    device: torch.device,
) -> Int[Tensor, " query_block key_value_block"]:
    block_mask: Bool[Tensor, "query_block key_value_block"] = causal_block_mask(
        sequence_length=sequence_length,
        block_size=block_size,
        full=full,
        device=device,
    )

    if window_size is not None:
        block_mask = block_mask & window_block_mask(
            sequence_length=sequence_length,
            block_size=block_size,
            window_size=window_size,
            full=full,
            device=device,
        )

    block_mask = block_mask & document_block_mask(
        document_ids=document_ids, full=full, block_size=block_size
    )

    return block_mask


def dense_mask_to_ordered(dense_mask):
    num_blocks = dense_mask.sum(dim=-1, dtype=torch.int32)
    indices = dense_mask.argsort(dim=-1, descending=True, stable=True).to(torch.int32)
    return num_blocks[None, None].contiguous(), indices[None, None].contiguous()


def make_flex_attention_block_mask(
    cumulative_sequence_lengths: Int[Tensor, "batch document"] | None,
    sequence_length: int,
    window_size: int | Int[Tensor, ""] | None,
    device: torch.device,
) -> BlockMask:
    assert cumulative_sequence_lengths is not None, (
        "with flex_attention, only variable length attention is supported"
    )

    batch_size, n_documents = cumulative_sequence_lengths.shape

    assert batch_size == 1, "with variable length flex attention, batch size must be 1"

    BLOCK_SIZE: int = 128

    document_ids: Int[Tensor, " position"] = document_indices(
        sequence_length=sequence_length,
        cumulative_sequence_lengths=cumulative_sequence_lengths,
        device=device,
    ).squeeze(0)

    nonzero_block_mask: Int[Tensor, " query_block key_value_block"] = block_mask(
        sequence_length=sequence_length,
        document_ids=document_ids,
        window_size=window_size,
        full=False,
        block_size=BLOCK_SIZE,
        device=device,
    )
    full_block_mask: Int[Tensor, " query_block key_value_block"] = block_mask(
        sequence_length=sequence_length,
        document_ids=document_ids,
        window_size=window_size,
        full=True,
        block_size=BLOCK_SIZE,
        device=device,
    )

    kv_num_blocks, kv_indices = dense_mask_to_ordered(
        nonzero_block_mask & ~full_block_mask
    )
    full_kv_num_blocks, full_kv_indices = dense_mask_to_ordered(full_block_mask)

    def mask(b, h, query_position, key_value_position):
        causal_mask = query_position >= key_value_position

        mask = causal_mask

        if window_size is not None:
            window_mask = query_position - key_value_position < window_size
            mask = mask & window_mask

        block_mask = document_ids[query_position] == document_ids[key_value_position]
        mask = mask & block_mask

        return mask

    return BlockMask.from_kv_blocks(
        kv_num_blocks=kv_num_blocks,
        kv_indices=kv_indices,
        full_kv_num_blocks=full_kv_num_blocks,
        full_kv_indices=full_kv_indices,
        BLOCK_SIZE=BLOCK_SIZE,
        mask_mod=mask,
    )


def flex_attention_variable_length_attention_function(
    args: AttentionFunctionArguments,
) -> Float[Tensor, "batch position n_heads d_head"]:
    assert args.cumulative_sequence_lengths is not None
    assert args.flex_attention_block_mask is not None

    assert args.max_variable_sequence_length is None, (
        "flex_attention with variable sequence lengths does not require max_variable_sequence_length"
    )
    assert args.dropout == 0.0, "dropout is not supported with flex_attention"

    return (
        flex_attention(
            query=args.queries.transpose(-2, -3),
            key=args.keys.transpose(-2, -3),
            value=args.values.transpose(-2, -3),
            block_mask=args.flex_attention_block_mask,
            scale=args.scale,
            enable_gqa=args.queries.size(-2) != args.keys.size(-2),
        )
        .transpose(-2, -3)  # type: ignore
        .contiguous()
    )


# ruff: noqa: F722
