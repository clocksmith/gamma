#!/usr/bin/env python3
"""Screen exact FX2 components as fixed blends over an external causal base.

The external base is typically the continuously evolved compact-CMIX endpoint.
Endpoint and weight selection reads development rows only.  Holdout and exact
range-coder replay are evaluated only after the configuration is frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


ATTRIBUTION_MAGIC = b"FX2ATV1\0"
ATTRIBUTION_HEADER_BYTES = 64
P1_MAGICS = {b"CMX21P1\0", b"FX2P1V1\0"}
P1_HEADER_BYTES = 16
PROBABILITY_TOTAL = 65_536
PPM = 1_000_000
QBITS_PER_BYTE = 256 * 8
GROUP_NAMES = (
    "bracket",
    "fxcm",
    "direct",
    "match",
    "indirect_ns",
    "indirect_run",
    "ppmd",
    "byte_mixer",
)
EXPECTED_GROUP_COUNTS = (1, 431, 1, 10, 15, 1, 1, 1)
DEFAULT_WEIGHTS = (31_250, 62_500, 125_000, 250_000, 375_000, 500_000)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, *, hash_file: bool = True) -> dict[str, Any]:
    resolved = path.resolve()
    row: dict[str, Any] = {"path": str(resolved), "bytes": resolved.stat().st_size}
    if hash_file:
        row["sha256"] = sha256(resolved)
    return row


def cmix_archive_header_bytes(archive: bytes) -> int:
    """Return the exact CMIX header width used by the native replay tools."""
    if len(archive) < 5:
        raise ValueError("base archive lacks its CMIX header")
    decoded_length = 0
    for index, value in enumerate(archive[:5]):
        if index == 0:
            value &= 0x7F
        decoded_length = (decoded_length << 8) + value
    header_bytes = 37 if decoded_length >= 10_000 else 5
    if len(archive) < header_bytes:
        raise ValueError("base archive CMIX header is truncated")
    return header_bytes


@dataclass(frozen=True)
class AttributionHeader:
    rows: int
    row_bytes: int
    raw_count: int
    layer0_count: int
    group_counts: tuple[int, ...]

    @property
    def words_per_row(self) -> int:
        return self.row_bytes // 2


def read_attribution_header(path: Path) -> AttributionHeader:
    with path.open("rb") as source:
        header = source.read(ATTRIBUTION_HEADER_BYTES)
    if len(header) != ATTRIBUTION_HEADER_BYTES or header[:8] != ATTRIBUTION_MAGIC:
        raise ValueError("invalid FX2 attribution trace header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    header_bytes, row_bytes, raw_count, layer0_count = struct.unpack_from(
        "<4I", header, 16
    )
    group_counts = struct.unpack_from("<8H", header, 32)
    flags = struct.unpack_from("<I", header, 48)[0]
    if header_bytes != ATTRIBUTION_HEADER_BYTES or row_bytes % 2:
        raise ValueError("unsupported FX2 attribution layout")
    if sum(group_counts) != raw_count or flags & 0x0F != 0x0F:
        raise ValueError("incomplete FX2 attribution component contract")
    if tuple(group_counts) != EXPECTED_GROUP_COUNTS:
        raise ValueError("unexpected FX2 attribution group layout")
    expected_row_bytes = 8 + 2 * (raw_count + layer0_count)
    if row_bytes != expected_row_bytes:
        raise ValueError("FX2 attribution row width is inconsistent")
    expected_bytes = ATTRIBUTION_HEADER_BYTES + rows * row_bytes
    if path.stat().st_size != expected_bytes:
        raise ValueError("FX2 attribution trace length mismatch")
    return AttributionHeader(
        rows=rows,
        row_bytes=row_bytes,
        raw_count=raw_count,
        layer0_count=layer0_count,
        group_counts=tuple(int(value) for value in group_counts),
    )


def read_p1_header(path: Path) -> tuple[bytes, int]:
    with path.open("rb") as source:
        header = source.read(P1_HEADER_BYTES)
    if len(header) != P1_HEADER_BYTES or header[:8] not in P1_MAGICS:
        raise ValueError("unsupported external P1 trace")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if path.stat().st_size != P1_HEADER_BYTES + 2 * rows:
        raise ValueError("external P1 trace length mismatch")
    return header[:8], rows


def endpoint_layout(header: AttributionHeader) -> tuple[list[str], np.ndarray]:
    names = ["fx2_final", "fx2_pre_sse", "fx2_post_sse"]
    columns = [0, 1, 2]
    raw_offset = 0
    for group, count in zip(GROUP_NAMES, header.group_counts, strict=True):
        names.extend(f"raw_{group}_{index}" for index in range(count))
        columns.extend(4 + raw_offset + index for index in range(count))
        raw_offset += count
    names.extend(f"layer0_mixer_{index}" for index in range(header.layer0_count))
    columns.extend(4 + header.raw_count + index for index in range(header.layer0_count))
    if len(names) != len(columns):
        raise AssertionError("endpoint names and columns diverged")
    return names, np.asarray(columns, dtype=np.int64)


def dependency_class(name: str) -> str:
    if name in {"fx2_final", "fx2_pre_sse", "fx2_post_sse"}:
        return "full_fx2_state"
    if name.startswith("layer0_mixer_"):
        return "full_fx2_raw_universe_plus_mixer_context"
    if name.startswith("raw_fxcm_"):
        return "compound_fxcm_plus_feedback_dependencies"
    if name.startswith("raw_ppmd_"):
        return "ppmd_only"
    if name.startswith("raw_byte_mixer_"):
        return "ppmd_plus_online_lstm"
    if name.startswith("raw_match_"):
        return "history_plus_selected_match_context"
    if name.startswith("raw_indirect_"):
        return "shared_indirect_map_plus_context_writer_closure"
    if name.startswith("raw_direct_"):
        return "direct_context_table"
    if name.startswith("raw_bracket_"):
        return "bracket_state"
    return "unknown"


def qbit_tables() -> tuple[np.ndarray, np.ndarray]:
    loss0 = np.zeros(PROBABILITY_TOTAL, dtype=np.int32)
    loss1 = np.zeros(PROBABILITY_TOTAL, dtype=np.int32)
    for p1 in range(1, PROBABILITY_TOTAL):
        loss0[p1] = int(
            -math.log2((PROBABILITY_TOTAL - p1) / PROBABILITY_TOTAL) * 256 + 0.5
        )
        loss1[p1] = int(-math.log2(p1 / PROBABILITY_TOTAL) * 256 + 0.5)
    return loss0, loss1


def mix_probabilities(base: np.ndarray, endpoint: np.ndarray, weight: int) -> np.ndarray:
    mixed = (
        base.astype(np.uint64) * (PPM - weight)
        + endpoint.astype(np.uint64) * weight
        + PPM // 2
    ) // PPM
    return np.clip(mixed, 1, PROBABILITY_TOTAL - 1).astype(np.uint16)


def mix_logit_probabilities(
    base: np.ndarray, endpoint: np.ndarray, weight: int
) -> np.ndarray:
    base_scaled = np.clip(
        base.astype(np.float64) / PROBABILITY_TOTAL,
        1 / PROBABILITY_TOTAL,
        (PROBABILITY_TOTAL - 1) / PROBABILITY_TOTAL,
    )
    endpoint_scaled = np.clip(
        endpoint.astype(np.float64) / PROBABILITY_TOTAL,
        1 / PROBABILITY_TOTAL,
        (PROBABILITY_TOTAL - 1) / PROBABILITY_TOTAL,
    )
    base_logit = np.log(base_scaled) - np.log1p(-base_scaled)
    endpoint_logit = np.log(endpoint_scaled) - np.log1p(-endpoint_scaled)
    mixed_logit = (
        base_logit * (PPM - weight) + endpoint_logit * weight
    ) / PPM
    mixed = 1.0 / (1.0 + np.exp(-np.clip(mixed_logit, -40, 40)))
    return np.clip(
        np.floor(mixed * PROBABILITY_TOTAL + 0.5),
        1,
        PROBABILITY_TOTAL - 1,
    ).astype(np.uint16)


def mix_endpoint(
    base: np.ndarray, endpoint: np.ndarray, weight: int, mix_space: str
) -> np.ndarray:
    if mix_space == "probability":
        return mix_probabilities(base, endpoint, weight)
    if mix_space == "logit":
        return mix_logit_probabilities(base, endpoint, weight)
    raise ValueError(f"unsupported mix space: {mix_space}")


class CmixRangeEncoder:
    def __init__(self) -> None:
        self.x1 = 0
        self.x2 = 0xFFFFFFFF
        self.output = bytearray()

    def encode(self, bit: int, p1: int) -> None:
        span = (self.x2 - self.x1) & 0xFFFFFFFF
        midpoint = (
            self.x1
            + (span >> 16) * p1
            + (((span & 0xFFFF) * p1) >> 16)
        ) & 0xFFFFFFFF
        if bit:
            self.x2 = midpoint
        else:
            self.x1 = (midpoint + 1) & 0xFFFFFFFF
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.output.append(self.x2 >> 24)
            self.x1 = (self.x1 << 8) & 0xFFFFFFFF
            self.x2 = ((self.x2 << 8) + 255) & 0xFFFFFFFF

    def finish(self) -> bytes:
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.output.append(self.x2 >> 24)
            self.x1 = (self.x1 << 8) & 0xFFFFFFFF
            self.x2 = ((self.x2 << 8) + 255) & 0xFFFFFFFF
        self.output.append(self.x2 >> 24)
        return bytes(self.output)


def exact_replay(
    truth: np.ndarray, base: np.ndarray, candidate: np.ndarray
) -> tuple[dict[str, int], bytes, bytes]:
    base_coder = CmixRangeEncoder()
    candidate_coder = CmixRangeEncoder()
    for bit, base_p1, candidate_p1 in zip(truth, base, candidate, strict=True):
        base_coder.encode(int(bit), int(base_p1))
        candidate_coder.encode(int(bit), int(candidate_p1))
    base_payload = base_coder.finish()
    candidate_payload = candidate_coder.finish()
    return (
        {
            "rows": len(truth),
            "base_payload_bytes": len(base_payload),
            "candidate_payload_bytes": len(candidate_payload),
            "saved_bytes": len(base_payload) - len(candidate_payload),
        },
        base_payload,
        candidate_payload,
    )


def exact_block_audit(
    truth: np.ndarray,
    base: np.ndarray,
    candidate: np.ndarray,
    blocks: int,
) -> dict[str, Any]:
    if blocks < 1 or blocks > len(truth):
        raise ValueError("holdout block count must be within the holdout rows")
    rows: list[dict[str, int]] = []
    for block in range(blocks):
        start = len(truth) * block // blocks
        end = len(truth) * (block + 1) // blocks
        replay, _, _ = exact_replay(
            truth[start:end], base[start:end], candidate[start:end]
        )
        rows.append(
            {
                "block": block,
                "start_row": start,
                "end_row": end,
                "saved_bytes": replay["saved_bytes"],
            }
        )
    regressions = [-row["saved_bytes"] for row in rows if row["saved_bytes"] < 0]
    return {
        "blocks": blocks,
        "regressing_blocks": len(regressions),
        "largest_regression_bytes": max(regressions, default=0),
        "total_regression_bytes": sum(regressions),
        "rows": rows,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not 0 < args.dev_start_ppm < args.holdout_start_ppm < PPM:
        raise ValueError("split PPM boundaries must be ordered")
    if args.shortlist < 2 or args.top_exact < 1 or args.chunk_rows < 1:
        raise ValueError("shortlist, top-exact, and chunk rows must be positive")
    weights = tuple(sorted(set(args.weights)))
    if not weights or any(weight <= 0 or weight > PPM for weight in weights):
        raise ValueError("weights must be in 1..1000000")

    header = read_attribution_header(args.attribution_trace)
    _, p1_rows = read_p1_header(args.base_p1)
    store_bytes = args.wrt_store.read_bytes()
    if len(store_bytes) < 5 or (len(store_bytes) - 5) * 8 != header.rows:
        raise ValueError("WRT store and attribution rows do not align")
    if p1_rows != header.rows:
        raise ValueError("external base and attribution rows do not align")
    if args.raw_scope_bytes <= 0:
        raise ValueError("raw scope must be positive")

    names, columns = endpoint_layout(header)
    endpoint_count = len(names)
    forced_endpoint = None
    if args.force_endpoint_name is not None:
        try:
            forced_endpoint = names.index(args.force_endpoint_name)
        except ValueError as exc:
            raise ValueError(
                f"unknown forced endpoint: {args.force_endpoint_name}"
            ) from exc
    trace = np.memmap(
        args.attribution_trace,
        dtype="<u2",
        mode="r",
        offset=ATTRIBUTION_HEADER_BYTES,
        shape=(header.rows, header.words_per_row),
    )
    base = np.memmap(
        args.base_p1,
        dtype="<u2",
        mode="r",
        offset=P1_HEADER_BYTES,
        shape=(header.rows,),
    )
    truth = np.unpackbits(
        np.frombuffer(store_bytes, dtype=np.uint8, offset=5), bitorder="big"
    )
    dev_start = header.rows * args.dev_start_ppm // PPM
    holdout_start = header.rows * args.holdout_start_ppm // PPM
    loss0, loss1 = qbit_tables()

    coarse_weight = 125_000
    coarse_gain = np.zeros(endpoint_count, dtype=np.int64)
    derivative = np.zeros(endpoint_count, dtype=np.float64)
    for start in range(dev_start, holdout_start, args.chunk_rows):
        end = min(holdout_start, start + args.chunk_rows)
        local_base = np.asarray(base[start:end], dtype=np.uint16)
        local_endpoints = np.asarray(trace[start:end, columns], dtype=np.uint16)
        bits = truth[start:end]
        base_loss = np.where(bits, loss1[local_base], loss0[local_base]).astype(
            np.int64, copy=False
        )
        mixed = mix_endpoint(
            local_base[:, None], local_endpoints, coarse_weight, args.mix_space
        )
        mixed_loss = np.where(
            bits[:, None], loss1[mixed], loss0[mixed]
        ).astype(np.int64, copy=False)
        coarse_gain += (base_loss[:, None] - mixed_loss).sum(axis=0, dtype=np.int64)

        probability = local_base.astype(np.float64) / PROBABILITY_TOTAL
        factor = (probability - bits.astype(np.float64)) / (
            probability * (1.0 - probability)
        )
        delta = (
            local_endpoints.astype(np.float64) - local_base[:, None]
        ) / PROBABILITY_TOTAL
        derivative += (delta * factor[:, None]).sum(axis=0, dtype=np.float64)

    half = max(1, args.shortlist // 2)
    coarse_order = np.argsort(-coarse_gain, kind="stable")
    derivative_order = np.argsort(derivative, kind="stable")
    shortlist: list[int] = []
    for endpoint in np.concatenate((coarse_order[:half], derivative_order[:half])):
        value = int(endpoint)
        if value not in shortlist:
            shortlist.append(value)
    for endpoint in coarse_order:
        if len(shortlist) >= args.shortlist:
            break
        value = int(endpoint)
        if value not in shortlist:
            shortlist.append(value)
    if forced_endpoint is not None and forced_endpoint not in shortlist:
        if len(shortlist) >= args.shortlist:
            shortlist[-1] = forced_endpoint
        else:
            shortlist.append(forced_endpoint)
    shortlist_array = np.asarray(shortlist, dtype=np.int64)

    dev_base_loss = 0
    refined_losses = np.zeros((len(weights), len(shortlist)), dtype=np.int64)
    for start in range(dev_start, holdout_start, args.chunk_rows):
        end = min(holdout_start, start + args.chunk_rows)
        local_base = np.asarray(base[start:end], dtype=np.uint16)
        local_endpoints = np.asarray(
            trace[start:end, columns[shortlist_array]], dtype=np.uint16
        )
        bits = truth[start:end]
        base_loss = np.where(bits, loss1[local_base], loss0[local_base]).astype(
            np.int64, copy=False
        )
        dev_base_loss += int(base_loss.sum(dtype=np.int64))
        for weight_index, weight in enumerate(weights):
            mixed = mix_endpoint(
                local_base[:, None], local_endpoints, weight, args.mix_space
            )
            refined_losses[weight_index] += np.where(
                bits[:, None], loss1[mixed], loss0[mixed]
            ).sum(axis=0, dtype=np.int64)

    configurations: list[dict[str, Any]] = []
    for local_index, endpoint in enumerate(shortlist):
        weight_index = int(np.argmin(refined_losses[:, local_index]))
        dev_gain = dev_base_loss - int(refined_losses[weight_index, local_index])
        configurations.append(
            {
                "endpoint": endpoint,
                "endpoint_name": names[endpoint],
                "dependency_class": dependency_class(names[endpoint]),
                "weight_ppm": weights[weight_index],
                "dev_gain_qbits": dev_gain,
                "dev_gain_bytes_per_proportional_1m_raw": (
                    dev_gain
                    / QBITS_PER_BYTE
                    * 1_000_000
                    / (args.raw_scope_bytes * (args.holdout_start_ppm - args.dev_start_ppm) / PPM)
                ),
                "coarse_125k_dev_gain_qbits": int(coarse_gain[endpoint]),
                "derivative_at_base": float(derivative[endpoint]),
            }
        )
    configurations.sort(key=lambda row: (-row["dev_gain_qbits"], row["endpoint"]))
    exact_configs = configurations[: min(args.top_exact, len(configurations))]
    if forced_endpoint is not None and all(
        row["endpoint"] != forced_endpoint for row in exact_configs
    ):
        forced_configuration = next(
            row for row in configurations if row["endpoint"] == forced_endpoint
        )
        if len(exact_configs) >= args.top_exact:
            exact_configs[-1] = forced_configuration
        else:
            exact_configs.append(forced_configuration)

    split_bounds = ((0, dev_start), (dev_start, holdout_start), (holdout_start, header.rows))
    split_names = ("train", "dev", "holdout")
    for configuration in exact_configs:
        endpoint = int(configuration["endpoint"])
        weight = int(configuration["weight_ppm"])
        split_gains: dict[str, int] = {}
        for split_name, (split_start, split_end) in zip(
            split_names, split_bounds, strict=True
        ):
            gain = 0
            for start in range(split_start, split_end, args.chunk_rows):
                end = min(split_end, start + args.chunk_rows)
                local_base = np.asarray(base[start:end], dtype=np.uint16)
                local_endpoint = np.asarray(
                    trace[start:end, columns[endpoint]], dtype=np.uint16
                )
                bits = truth[start:end]
                mixed = mix_endpoint(
                    local_base, local_endpoint, weight, args.mix_space
                )
                base_loss = np.where(bits, loss1[local_base], loss0[local_base])
                candidate_loss = np.where(bits, loss1[mixed], loss0[mixed])
                gain += int((base_loss - candidate_loss).sum(dtype=np.int64))
            split_gains[split_name] = gain
        configuration["split_gain_qbits"] = split_gains
        configuration["holdout_gain_bytes_per_proportional_1m_raw"] = (
            split_gains["holdout"]
            / QBITS_PER_BYTE
            * 1_000_000
            / (args.raw_scope_bytes * (PPM - args.holdout_start_ppm) / PPM)
        )

    selected = (
        next(
            row
            for row in exact_configs
            if row["endpoint"] == forced_endpoint
        )
        if forced_endpoint is not None
        else exact_configs[0]
    )
    selected_endpoint = int(selected["endpoint"])
    selected_weight = int(selected["weight_ppm"])
    base_all = np.asarray(base, dtype=np.uint16)
    endpoint_all = np.asarray(trace[:, columns[selected_endpoint]], dtype=np.uint16)
    candidate_all = mix_endpoint(
        base_all, endpoint_all, selected_weight, args.mix_space
    )
    exact_full, replayed_base_payload, candidate_payload = exact_replay(
        truth, base_all, candidate_all
    )
    exact_holdout, _, _ = exact_replay(
        truth[holdout_start:], base_all[holdout_start:], candidate_all[holdout_start:]
    )
    holdout_block_audit = exact_block_audit(
        truth[holdout_start:],
        base_all[holdout_start:],
        candidate_all[holdout_start:],
        args.holdout_blocks,
    )
    archive_bytes = args.base_archive.read_bytes()
    detected_archive_header_bytes = cmix_archive_header_bytes(archive_bytes)
    if (
        args.base_archive_header_bytes
        and args.base_archive_header_bytes != detected_archive_header_bytes
    ):
        raise ValueError(
            "explicit base archive header width disagrees with CMIX framing"
        )
    base_payload = archive_bytes[detected_archive_header_bytes:]
    base_identity = bool(
        len(replayed_base_payload) == len(base_payload)
        and hashlib.sha256(replayed_base_payload).hexdigest()
        == hashlib.sha256(base_payload).hexdigest()
    )
    if args.candidate_payload is not None:
        args.candidate_payload.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_payload.write_bytes(candidate_payload)

    full_rate = exact_full["saved_bytes"] * 1_000_000 / args.raw_scope_bytes
    holdout_rate = (
        exact_holdout["saved_bytes"]
        * 1_000_000
        / (args.raw_scope_bytes * (PPM - args.holdout_start_ppm) / PPM)
    )
    receipt = {
        "schema": "fx2_attribution_external_base_screen_v1",
        "evidence_level": (
            "development_weight_selected_forced_endpoint_exact_external_base_shadow"
            if forced_endpoint is not None
            else "development_selected_exact_external_base_shadow"
        ),
        "inputs": {
            "attribution_trace": artifact(args.attribution_trace, hash_file=False),
            "trace_inspection_receipt": (
                artifact(args.trace_inspection_receipt)
                if args.trace_inspection_receipt is not None
                else None
            ),
            "base_p1": artifact(args.base_p1),
            "base_archive": artifact(args.base_archive),
            "wrt_store": artifact(args.wrt_store),
        },
        "scope": {
            "raw_bytes": args.raw_scope_bytes,
            "rows": header.rows,
            "dev_start_row": dev_start,
            "holdout_start_row": holdout_start,
            "selection_reads_holdout": False,
            "forced_endpoint_name": args.force_endpoint_name,
        },
        "component_universe": {
            "endpoints": endpoint_count,
            "raw_components": header.raw_count,
            "layer0_mixers": header.layer0_count,
            "shortlisted_endpoints": len(shortlist),
            "weights_ppm": list(weights),
            "mix_space": args.mix_space,
        },
        "selected": selected,
        "ranked_configurations": exact_configs,
        "exact_replay": {
            "base_archive_header_bytes": detected_archive_header_bytes,
            "base_archive_payload_identity": base_identity,
            "full": exact_full,
            "holdout": exact_holdout,
            "holdout_block_audit": holdout_block_audit,
            "full_saved_bytes_per_1m_raw": full_rate,
            "holdout_saved_bytes_per_proportional_1m_raw": holdout_rate,
            "candidate_payload_path": (
                str(args.candidate_payload.resolve())
                if args.candidate_payload is not None
                else None
            ),
        },
        "economics": {
            "required_incremental_bytes_per_1m": args.required_incremental_bytes_per_1m,
            "discovery_headroom_bytes_per_1m": args.discovery_headroom_bytes_per_1m,
            "full_clears_required_incremental": (
                full_rate >= args.required_incremental_bytes_per_1m
            ),
            "holdout_clears_required_incremental": (
                holdout_rate >= args.required_incremental_bytes_per_1m
            ),
            "holdout_clears_discovery_headroom": (
                holdout_rate >= args.discovery_headroom_bytes_per_1m
            ),
        },
        "verdict": (
            "component_candidate_requires_dependency_rss_and_native_replay"
            if base_identity
            and full_rate >= args.required_incremental_bytes_per_1m
            and holdout_rate >= args.required_incremental_bytes_per_1m
            else "retire_measured_fx2_component_universe_over_external_base"
        ),
        "promotion_authorized": False,
        "claim_boundary": (
            "Development-selected matched shadow over an external causal base. "
            "Endpoint dependency closure, counted code/state, native replay, "
            "roundtrip, determinism, resources, and full-corpus accounting remain required."
        ),
    }
    return receipt

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attribution-trace", type=Path, required=True)
    parser.add_argument("--trace-inspection-receipt", type=Path)
    parser.add_argument("--base-p1", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument(
        "--base-archive-header-bytes",
        type=int,
        default=0,
        help="optional fail-closed assertion; zero auto-detects native CMIX framing",
    )
    parser.add_argument("--wrt-store", type=Path, required=True)
    parser.add_argument("--raw-scope-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path)
    parser.add_argument("--dev-start-ppm", type=int, default=600_000)
    parser.add_argument("--holdout-start-ppm", type=int, default=800_000)
    parser.add_argument("--chunk-rows", type=int, default=8_192)
    parser.add_argument("--shortlist", type=int, default=64)
    parser.add_argument("--top-exact", type=int, default=16)
    parser.add_argument("--force-endpoint-name")
    parser.add_argument("--holdout-blocks", type=int, default=16)
    parser.add_argument("--weights", type=int, nargs="+", default=DEFAULT_WEIGHTS)
    parser.add_argument(
        "--mix-space", choices=("probability", "logit"), default="probability"
    )
    parser.add_argument(
        "--required-incremental-bytes-per-1m", type=float, default=154.324
    )
    parser.add_argument(
        "--discovery-headroom-bytes-per-1m", type=float, default=300.0
    )
    args = parser.parse_args()
    receipt = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, args.output)
    print(receipt["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
