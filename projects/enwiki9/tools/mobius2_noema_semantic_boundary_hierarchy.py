#!/usr/bin/env python3
"""Run the frozen NOEMA semantic-boundary hierarchy QH0 gate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
from typing import Any, Sequence
import zlib

import numpy as np

from bifrons_reverse_causal_joint_ceiling import read_page_map, read_p1
from endpoint428_parent_recovery_gate import observed_artifact
from mobius2_noema_binary_carry_headroom import (
    probability_logits,
    quantized_probabilities,
    range_decode,
    range_encode,
)
from radix_island_oracle import emission_groups
from wrt_exact import parse_store_bytes, read_dictionary_words


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
CANDIDATE_ID = "mobius2_noema_semantic_boundary_hierarchy_qh0_v1"
PROPOSAL_ID = "mobius2_noema_semantic_boundary_hierarchy_v1"
PROGRAM = PROJECT / "programs" / CANDIDATE_ID / "program.py"
PLAN = PROJECT / "docs/mobius2_noema_semantic_boundary_hierarchy_qh0_plan.md"
SCHEMA = (
    PROJECT
    / "docs/mobius2_noema_semantic_boundary_hierarchy_qh0_decision.schema.json"
)
TRACE_DECISION = (
    PROJECT
    / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/decision.json"
)
JOINT_P1 = (
    PROJECT
    / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1"
)
JOINT_PAYLOAD = (
    PROJECT
    / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload"
)
WRT_STORE = (
    PROJECT
    / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin"
)
PAGE_MAP = (
    PROJECT / "results/mobius2_tessera_typed_fiber_ceiling_qh0_v1/page_map.bin"
)
RAW_INPUT = PROJECT / "data/enwik9_10000000.bin"
SOURCE_ROOT = Path(
    "/home/x/enwiki9-nonproof/results/"
    "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
    "clean-build-b/build"
)
DICTIONARY = SOURCE_ROOT / "english.dic"
BACKEND = SOURCE_ROOT / "cmix.bin"
ROCM_PYTHON = REPO / ".venv_rocm/bin/python"

RAW_LIMIT = 1_000_000
FROZEN_PAGES = 171
FROZEN_RAW_BYTES = 984_835
FROZEN_WRT_BYTES = 591_230
FROZEN_ROWS = FROZEN_WRT_BYTES * 8
PATCH_BYTES = 128
FIXED_SEGMENT_BYTES = 16
BOUNDARY_LAG_PATCHES = 31
SPLITS = ("development", "selection", "sealed_confirmation")
MODES = ("flat", "fixed", "lagged", "semantic")
EPOCHS = 6
BATCH_SIZE = 16
SEED = 428
LEARNING_RATE = 0.002
WEIGHT_DECAY = 0.000001
GRADIENT_CLIP = 1.0
DECODER_ALLOWANCE_BYTES = 65_536
FRAMING_ALLOWANCE_BYTES = 32
PACKAGE_CEILING_BYTES = 131_072
GROSS_GATE_BPM = 3_000.0
NET_GATE_BPM = 2_100.0
STORE_HEADER = b"\x80\x00\x00\x00\x00"

EXPECTED_SHA256 = {
    "backend": "ce71136ad210092bcbe0a9ff6c388767611482ea24c60849455ae70d36e84e97",
    "dictionary": "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a",
    "joint_p1": "b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719",
    "joint_payload": "5ffaa128fa9e86e3883896a6d16b6c49e23693f5abdf14f1718e0e006533dca9",
    "wrt_store": "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b",
    "page_map": "bbd7997af61a3d1a968f245377ec651d581c97720aa12a3f5b96fd98fa6e2e79",
    "trace_decision": "a8e098f1e658d91e16275bb17ad950d0249c5aafbd9841458a18b41cdc5daa9e",
    "raw_input": "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97",
}


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str


@dataclass(frozen=True)
class Patch:
    index: int
    page_index: int
    wrt_start: int
    wrt_end: int
    split: str


@dataclass(frozen=True)
class Partition:
    name: str
    positions: np.ndarray
    lengths: np.ndarray
    counts: np.ndarray
    byte_segment: np.ndarray
    byte_offset: np.ndarray
    length_rows: tuple[tuple[int, ...], ...]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def bind(path: Path, expected: str, label: str) -> dict[str, Any]:
    row = observed_artifact(path.resolve())
    if row["sha256"] != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {row['sha256']}")
    return row


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import candidate module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ensure_rocm_runtime() -> None:
    if not ROCM_PYTHON.is_file():
        raise FileNotFoundError(f"missing ROCm Python: {ROCM_PYTHON}")
    if Path(sys.prefix).resolve() == (REPO / ".venv_rocm").resolve():
        if os.environ.get("HSA_OVERRIDE_GFX_VERSION") != "11.0.0":
            raise RuntimeError("ROCm runtime lacks frozen HSA GFX override")
        return
    if os.environ.get("NOEMA_SEMANTIC_REEXEC") == "1":
        raise RuntimeError("failed to enter the frozen ROCm runtime")
    environment = os.environ.copy()
    environment["NOEMA_SEMANTIC_REEXEC"] = "1"
    environment["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    environment["AMD_SERIALIZE_KERNEL"] = "3"
    environment["PYTHONUNBUFFERED"] = "1"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def runtime_probe(torch: Any) -> dict[str, Any]:
    if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
        raise RuntimeError("ROCm PyTorch exposes no CUDA-compatible device")
    torch.cuda.reset_peak_memory_stats()
    left = torch.arange(16, dtype=torch.float32, device="cuda:0").reshape(4, 4)
    right = torch.eye(4, dtype=torch.float32, device="cuda:0")
    result = left @ right
    torch.cuda.synchronize()
    host = result.cpu().numpy().astype("<f4", copy=False).tobytes()
    if not np.array_equal(
        np.frombuffer(host, dtype="<f4").reshape(4, 4),
        np.arange(16, dtype=np.float32).reshape(4, 4),
    ):
        raise RuntimeError("ROCm matrix probe returned the wrong result")
    return {
        "sys_executable": sys.executable,
        "sys_executable_resolved": str(Path(sys.executable).resolve()),
        "sys_prefix": sys.prefix,
        "torch_version": torch.__version__,
        "hip_version": torch.version.hip,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
        "device_name": torch.cuda.get_device_name(0),
        "device_architecture": str(torch.cuda.get_device_properties(0).gcnArchName),
        "runtime_mode": "rocm_gfx_override",
        "matrix_input_sha256": sha256_bytes(
            np.arange(16, dtype="<f4").tobytes()
        ),
        "matrix_output_sha256": sha256_bytes(host),
        "explicit_synchronization": True,
    }


def read_pages(path: Path) -> list[Page]:
    rows = [row for row in read_page_map(path) if row[1] <= RAW_LIMIT]
    if len(rows) != FROZEN_PAGES:
        raise ValueError(f"complete-page count changed: {len(rows)}")
    development_end = len(rows) * 3 // 5
    selection_end = len(rows) * 4 // 5
    pages: list[Page] = []
    for index, (raw_start, raw_end, row_start, row_end) in enumerate(rows):
        if row_start % 8 or row_end % 8:
            raise ValueError("page-map record is not WRT-byte aligned")
        split = (
            "development"
            if index < development_end
            else "selection"
            if index < selection_end
            else "sealed_confirmation"
        )
        pages.append(
            Page(index, raw_start, raw_end, row_start // 8, row_end // 8, split)
        )
    if pages[-1].raw_end != FROZEN_RAW_BYTES or pages[-1].wrt_end != FROZEN_WRT_BYTES:
        raise ValueError("frozen opening population boundary changed")
    return pages


def build_patches(pages: Sequence[Page]) -> list[Patch]:
    patches: list[Patch] = []
    for page in pages:
        stop = page.wrt_start + (
            (page.wrt_end - page.wrt_start) // PATCH_BYTES
        ) * PATCH_BYTES
        for start in range(page.wrt_start, stop, PATCH_BYTES):
            patches.append(
                Patch(
                    len(patches),
                    page.index,
                    start,
                    start + PATCH_BYTES,
                    page.split,
                )
            )
    if not patches:
        raise ValueError("frozen population contains no complete patches")
    return patches


def semantic_length_rows(
    wrt: bytes,
    raw_prefix: bytes,
    raw_bytes: int,
    dictionary: Path,
    patches: Sequence[Patch],
) -> tuple[list[list[int]], dict[str, Any]]:
    patched = bytearray(wrt)
    patched[1:5] = raw_bytes.to_bytes(4, "big")
    parsed = parse_store_bytes(
        STORE_HEADER + bytes(patched), read_dictionary_words(dictionary)
    )
    if parsed.decoded != raw_prefix:
        raise ValueError("patched complete-page prefix does not parse exactly")
    groups = emission_groups(parsed)
    boundary = np.zeros(len(wrt), dtype=np.bool_)
    punctuation = b".?!;"
    boundary_groups = 0
    for group in groups:
        visible = (
            any(value in group.decoded for value in punctuation)
            or b"\n" in group.decoded
            or b"</" in group.decoded
        )
        if visible and 0 < group.stream_end <= len(wrt):
            boundary[group.stream_end - 1] = True
            boundary_groups += 1

    rows: list[list[int]] = []
    for patch in patches:
        ends = [
            offset + 1
            for offset, value in enumerate(boundary[patch.wrt_start : patch.wrt_end])
            if value
        ]
        if not ends or ends[-1] != PATCH_BYTES:
            ends.append(PATCH_BYTES)
        starts = [0, *ends[:-1]]
        lengths = [end - start for start, end in zip(starts, ends) if end > start]
        if sum(lengths) != PATCH_BYTES or any(length <= 0 for length in lengths):
            raise ValueError("semantic partition does not cover its patch")
        rows.append(lengths)
    return rows, {
        "emission_groups": len(groups),
        "boundary_groups": boundary_groups,
        "boundary_bytes": int(np.count_nonzero(boundary)),
        "boundary_rule": "group-final byte after . ? ! ; newline or closing markup",
    }


def make_partition(name: str, length_rows: Sequence[Sequence[int]]) -> Partition:
    canonical = tuple(tuple(int(value) for value in row) for row in length_rows)
    if not canonical or any(sum(row) != PATCH_BYTES for row in canonical):
        raise ValueError(f"{name} partition contains an invalid row")
    max_segments = max(len(row) for row in canonical)
    max_length = max(max(row) for row in canonical)
    patch_count = len(canonical)
    positions = np.zeros((patch_count, max_segments, max_length), dtype=np.int16)
    lengths = np.zeros((patch_count, max_segments), dtype=np.int16)
    counts = np.empty(patch_count, dtype=np.int16)
    byte_segment = np.empty((patch_count, PATCH_BYTES), dtype=np.int16)
    byte_offset = np.empty((patch_count, PATCH_BYTES), dtype=np.int16)
    for patch_index, row in enumerate(canonical):
        counts[patch_index] = len(row)
        cursor = 0
        for segment_index, length in enumerate(row):
            lengths[patch_index, segment_index] = length
            positions[patch_index, segment_index, :length] = np.arange(
                cursor, cursor + length, dtype=np.int16
            )
            byte_segment[patch_index, cursor : cursor + length] = segment_index
            byte_offset[patch_index, cursor : cursor + length] = np.arange(
                length, dtype=np.int16
            )
            cursor += length
    return Partition(
        name,
        positions,
        lengths,
        counts,
        byte_segment,
        byte_offset,
        canonical,
    )


def partition_receipt(partition: Partition) -> dict[str, Any]:
    serialized = json.dumps(
        partition.length_rows, separators=(",", ":")
    ).encode("ascii")
    lengths = [length for row in partition.length_rows for length in row]
    counts = [len(row) for row in partition.length_rows]
    return {
        "patches": len(partition.length_rows),
        "segments": len(lengths),
        "mean_segments_per_patch": sum(counts) / len(counts),
        "maximum_segments_per_patch": max(counts),
        "mean_segment_bytes": sum(lengths) / len(lengths),
        "maximum_segment_bytes": max(lengths),
        "length_schedule_sha256": sha256_bytes(serialized),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint-p1", type=Path, default=JOINT_P1)
    parser.add_argument("--joint-payload", type=Path, default=JOINT_PAYLOAD)
    parser.add_argument("--wrt-store", type=Path, default=WRT_STORE)
    parser.add_argument("--page-map", type=Path, default=PAGE_MAP)
    parser.add_argument("--trace-decision", type=Path, default=TRACE_DECISION)
    parser.add_argument("--raw-input", type=Path, default=RAW_INPUT)
    parser.add_argument("--dictionary", type=Path, default=DICTIONARY)
    parser.add_argument("--backend", type=Path, default=BACKEND)
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT / "results" / CANDIDATE_ID
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_rocm_runtime()

    import torch
    from torch import nn

    runtime = runtime_probe(torch)
    print(
        f"python={runtime['sys_executable']} sys.prefix={runtime['sys_prefix']} "
        f"resolved_python={runtime['sys_executable_resolved']} "
        f"torch={runtime['torch_version']} "
        f"HIP={runtime['hip_version']} device={runtime['device_name']}"
    )
    print("torch.cuda.is_available()=True torch.cuda.device_count()=1 DEVICE=cuda")
    print("gpu_compute_probe=pass runtime_mode=rocm_gfx_override", flush=True)
    print(
        "[run-contract] "
        f"run_name={CANDIDATE_ID} pairs_input_spec={args.joint_p1} "
        "resume_from=none resume_stage=none decode=greedy "
        "eval_dataset_paths=development,selection,sealed_confirmation "
        "device=cuda schedule=development_then_selection "
        "runtime_mode=rocm_gfx_override sweep_mode=live",
        flush=True,
    )

    required = {
        "backend": args.backend,
        "dictionary": args.dictionary,
        "joint_p1": args.joint_p1,
        "joint_payload": args.joint_payload,
        "wrt_store": args.wrt_store,
        "page_map": args.page_map,
        "trace_decision": args.trace_decision,
        "raw_input": args.raw_input,
        "candidate_program": PROGRAM,
        "plan": PLAN,
        "decision_schema": SCHEMA,
    }
    for label, path in required.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing {label}: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError(f"refusing to overwrite {decision_path}")

    inputs: dict[str, Any] = {}
    for label, path in required.items():
        expected = EXPECTED_SHA256.get(label)
        inputs[label] = (
            bind(path, expected, label) if expected else observed_artifact(path.resolve())
        )
    trace_decision = json.loads(args.trace_decision.read_text())
    required_antecedent = (
        trace_decision.get("decision", {}).get("verdict")
        == "exact_joint_p1_trace_recovered"
        and all(
            trace_decision.get("proof", {}).get(key) is True
            for key in (
                "complete_wrt_truth_identity",
                "exact_arithmetic_decode",
                "joint_payload_identity_a",
                "joint_payload_identity_b",
                "repeated_adjusted_p1_identity",
            )
        )
    )
    if not required_antecedent:
        raise ValueError("joint P1 antecedent lacks its exact proof")

    candidate = load_module("noema_semantic_boundary_candidate", PROGRAM)
    if candidate.PATCH_BYTES != PATCH_BYTES:
        raise ValueError("candidate patch size differs from the frozen plan")

    pages = read_pages(args.page_map)
    patches = build_patches(pages)
    full_store = args.wrt_store.read_bytes()
    full_raw = args.raw_input.read_bytes()
    if full_store[:5] != STORE_HEADER or len(full_raw) != 10_000_000:
        raise ValueError("canonical 10M input or WRT store has an invalid frame")
    wrt = full_store[5 : 5 + FROZEN_WRT_BYTES]
    raw_prefix = full_raw[:FROZEN_RAW_BYTES]
    semantic_rows, boundary_receipt = semantic_length_rows(
        wrt,
        raw_prefix,
        FROZEN_RAW_BYTES,
        args.dictionary,
        patches,
    )
    flat_rows = [[PATCH_BYTES] for _patch in patches]
    fixed_rows = [
        [FIXED_SEGMENT_BYTES] * (PATCH_BYTES // FIXED_SEGMENT_BYTES)
        for _patch in patches
    ]
    lagged_rows: list[list[int]] = []
    for index in range(len(patches)):
        if index < BOUNDARY_LAG_PATCHES:
            lagged_rows.append(list(fixed_rows[index]))
        else:
            lagged_rows.append(list(semantic_rows[index - BOUNDARY_LAG_PATCHES]))
    partitions = {
        "flat": make_partition("flat", flat_rows),
        "fixed": make_partition("fixed", fixed_rows),
        "lagged": make_partition("lagged", lagged_rows),
        "semantic": make_partition("semantic", semantic_rows),
    }

    patch_positions = np.asarray(
        [
            np.arange(patch.wrt_start, patch.wrt_end, dtype=np.int64)
            for patch in patches
        ]
    )
    patch_values = np.frombuffer(wrt, dtype=np.uint8)[patch_positions]
    all_truth = np.unpackbits(np.frombuffer(wrt, dtype=np.uint8), bitorder="big")
    all_p1 = read_p1(args.joint_p1)
    if len(all_p1) != trace_decision["artifact"]["rows"]:
        raise ValueError("joint P1 row count differs from its certificate")
    p1 = np.asarray(all_p1[:FROZEN_ROWS], dtype=np.uint16)
    if np.any(p1 == 0):
        raise ValueError("joint prefix contains an illegal zero probability")
    parent_payload = range_encode(p1, all_truth)
    if not np.array_equal(range_decode(parent_payload, p1), all_truth):
        raise ValueError("joint prefix arithmetic parent does not decode exactly")
    if range_encode(p1, all_truth) != parent_payload:
        raise ValueError("joint prefix parent replay is nondeterministic")

    p1_by_byte = p1.reshape(FROZEN_WRT_BYTES, 8)
    patch_parent_p1 = p1_by_byte[patch_positions]
    patch_base_logits = probability_logits(patch_parent_p1)
    patch_bits = np.unpackbits(
        patch_values[..., None], axis=2, bitorder="big"
    ).astype(np.float32)
    patch_nodes = np.empty_like(patch_bits, dtype=np.int64)
    for bit_position in range(8):
        prefix = (
            np.zeros_like(patch_values, dtype=np.int64)
            if bit_position == 0
            else patch_values.astype(np.int64) >> (8 - bit_position)
        )
        patch_nodes[:, :, bit_position] = (1 << bit_position) - 1 + prefix

    split_patch_ids = {
        split: np.asarray(
            [patch.index for patch in patches if patch.split == split],
            dtype=np.int64,
        )
        for split in SPLITS
    }
    split_raw_bytes = {
        split: sum(
            page.raw_end - page.raw_start for page in pages if page.split == split
        )
        for split in SPLITS
    }
    split_parent_payloads = {
        split: range_encode(
            patch_parent_p1[ids].reshape(-1),
            patch_bits[ids].astype(np.uint8).reshape(-1),
        )
        for split, ids in split_patch_ids.items()
    }

    device = torch.device("cuda:0")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    def reset_seeds() -> None:
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)

    def model_from_state(state: dict[str, Any]) -> Any:
        model = candidate.build_model(torch)
        model.load_state_dict(state)
        return model.to(device)

    def batch_inputs(ids: np.ndarray, partition: Partition) -> tuple[Any, ...]:
        maximum_segments = int(np.max(partition.counts[ids]))
        maximum_length = int(
            np.max(partition.lengths[ids, :maximum_segments])
        )
        return (
            torch.from_numpy(patch_values[ids]).to(device=device, dtype=torch.long),
            torch.from_numpy(
                partition.positions[ids, :maximum_segments, :maximum_length].astype(
                    np.int64
                )
            ).to(device),
            torch.from_numpy(
                partition.lengths[ids, :maximum_segments].astype(np.int64)
            ).to(device),
            torch.from_numpy(partition.byte_segment[ids].astype(np.int64)).to(device),
            torch.from_numpy(partition.byte_offset[ids].astype(np.int64)).to(device),
        )

    def infer(model: Any, ids: np.ndarray, partition: Partition) -> np.ndarray:
        probabilities = np.empty((len(ids), PATCH_BYTES, 8), dtype=np.uint16)
        model.eval()
        with torch.no_grad():
            for offset in range(0, len(ids), BATCH_SIZE):
                batch_ids = ids[offset : offset + BATCH_SIZE]
                model_args = batch_inputs(batch_ids, partition)
                nodes = torch.from_numpy(patch_nodes[batch_ids]).to(device)
                residuals = model(*model_args)
                selected = torch.gather(residuals, 2, nodes)
                probabilities[offset : offset + len(batch_ids)] = (
                    quantized_probabilities(
                        patch_base_logits[batch_ids],
                        selected.cpu().numpy().astype(np.float32),
                    )
                )
        return probabilities

    def selection_payload(model: Any, partition: Partition) -> bytes:
        ids = split_patch_ids["selection"]
        probabilities = infer(model, ids, partition)
        return range_encode(
            probabilities.reshape(-1),
            patch_bits[ids].astype(np.uint8).reshape(-1),
        )

    def fit_once(mode: str, run_index: int) -> dict[str, Any]:
        partition = partitions[mode]
        reset_seeds()
        model = candidate.build_model(torch).to(device)
        parameter_count = candidate.parameter_count(model)
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
        )
        rng = np.random.default_rng(SEED)
        development_ids = split_patch_ids["development"]
        best_payload_bytes = math.inf
        best_epoch = 0
        best_blob: bytes | None = None
        best_state: dict[str, Any] | None = None
        history: list[dict[str, Any]] = []

        for epoch in range(1, EPOCHS + 1):
            model.train()
            ordering = rng.permutation(development_ids)
            weighted_loss = 0.0
            truth_count = 0
            for offset in range(0, len(ordering), BATCH_SIZE):
                ids = ordering[offset : offset + BATCH_SIZE]
                model_args = batch_inputs(ids, partition)
                nodes = torch.from_numpy(patch_nodes[ids]).to(device)
                base = torch.from_numpy(patch_base_logits[ids]).to(device)
                truth = torch.from_numpy(patch_bits[ids]).to(device)
                residuals = model(*model_args)
                selected = torch.gather(residuals, 2, nodes)
                loss = nn.functional.binary_cross_entropy_with_logits(
                    base + selected, truth
                )
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
                optimizer.step()
                count = truth.numel()
                weighted_loss += float(loss.detach().cpu()) * count
                truth_count += count

            blob, dequantized = candidate.quantize_model(torch, model)
            quantized_model = model_from_state(dequantized)
            selected_payload = selection_payload(quantized_model, partition)
            row = {
                "epoch": epoch,
                "development_nats_per_bit": weighted_loss / truth_count,
                "selection_parent_payload_bytes": len(
                    split_parent_payloads["selection"]
                ),
                "selection_candidate_payload_bytes": len(selected_payload),
                "selection_gain_bytes": len(split_parent_payloads["selection"])
                - len(selected_payload),
                "quantized_model_sha256": sha256_bytes(blob),
            }
            history.append(row)
            print(
                f"mode={mode} run={run_index} epoch={epoch} "
                f"train={row['development_nats_per_bit']:.9f} "
                f"selection_gain={row['selection_gain_bytes']}",
                flush=True,
            )
            if len(selected_payload) < best_payload_bytes:
                best_payload_bytes = len(selected_payload)
                best_epoch = epoch
                best_blob = blob
                best_state = {
                    name: tensor.detach().cpu().clone()
                    for name, tensor in dequantized.items()
                }
            del quantized_model

        if best_blob is None or best_state is None:
            raise RuntimeError(f"{mode} training selected no checkpoint")
        return {
            "mode": mode,
            "run_index": run_index,
            "selected_epoch": best_epoch,
            "model_blob": best_blob,
            "model_state": best_state,
            "history": history,
            "parameter_count": parameter_count,
        }

    def full_candidate_p1(patch_probabilities: np.ndarray) -> np.ndarray:
        result = p1.copy()
        result.reshape(FROZEN_WRT_BYTES, 8)[patch_positions.reshape(-1)] = (
            patch_probabilities.reshape(-1, 8)
        )
        return result

    def complete_fit(mode: str) -> dict[str, Any]:
        print(f"phase=fit_{mode}", flush=True)
        run_a = fit_once(mode, 1)
        run_b = fit_once(mode, 2)
        model_a = model_from_state(run_a["model_state"])
        model_b = model_from_state(run_b["model_state"])
        all_ids = np.arange(len(patches), dtype=np.int64)
        probabilities_a = infer(model_a, all_ids, partitions[mode])
        probabilities_b = infer(model_b, all_ids, partitions[mode])
        candidate_p1_a = full_candidate_p1(probabilities_a)
        candidate_p1_b = full_candidate_p1(probabilities_b)
        payload_a = range_encode(candidate_p1_a, all_truth)
        payload_b = range_encode(candidate_p1_b, all_truth)
        determinism = {
            "selected_epoch_identity": run_a["selected_epoch"]
            == run_b["selected_epoch"],
            "training_history_identity": run_a["history"] == run_b["history"],
            "model_blob_identity": run_a["model_blob"] == run_b["model_blob"],
            "adjusted_p1_identity": np.array_equal(candidate_p1_a, candidate_p1_b),
            "payload_identity": payload_a == payload_b,
        }
        if not all(determinism.values()):
            raise ValueError(f"{mode} repeated fit differs: {determinism}")
        return {
            "run": run_a,
            "model": model_a,
            "patch_probabilities": probabilities_a,
            "candidate_p1": candidate_p1_a,
            "payload": payload_a,
            "determinism": determinism,
        }

    fitted = {mode: complete_fit(mode) for mode in MODES}
    parameter_counts = {row["run"]["parameter_count"] for row in fitted.values()}
    if len(parameter_counts) != 1:
        raise ValueError("control parameter counts differ")

    def control_receipt(mode: str) -> dict[str, Any]:
        row = fitted[mode]
        output: dict[str, Any] = {
            "name": mode,
            "selected_epoch": row["run"]["selected_epoch"],
            "full_payload_bytes": len(row["payload"]),
            "full_payload_sha256": sha256_bytes(row["payload"]),
            "full_gain_bytes": len(parent_payload) - len(row["payload"]),
            "splits": {},
        }
        for split in SPLITS:
            ids = split_patch_ids[split]
            candidate_payload = range_encode(
                row["patch_probabilities"][ids].reshape(-1),
                patch_bits[ids].astype(np.uint8).reshape(-1),
            )
            parent_bytes = len(split_parent_payloads[split])
            gain = parent_bytes - len(candidate_payload)
            output["splits"][split] = {
                "raw_page_bytes": split_raw_bytes[split],
                "modeled_patches": len(ids),
                "modeled_wrt_bytes": len(ids) * PATCH_BYTES,
                "parent_payload_bytes": parent_bytes,
                "candidate_payload_bytes": len(candidate_payload),
                "candidate_payload_sha256": sha256_bytes(candidate_payload),
                "gain_bytes": gain,
                "gross_gain_bytes_per_million_raw": gain
                * 1_000_000.0
                / split_raw_bytes[split],
            }
        return output

    controls = {mode: control_receipt(mode) for mode in MODES}
    compressed_models = {
        mode: zlib.compress(fitted[mode]["run"]["model_blob"], level=9)
        for mode in MODES
    }
    matched_model_bytes = max(len(value) for value in compressed_models.values())
    package_bytes = (
        matched_model_bytes + DECODER_ALLOWANCE_BYTES + FRAMING_ALLOWANCE_BYTES
    )
    semantic_sealed = controls["semantic"]["splits"]["sealed_confirmation"]
    gross_bpm = semantic_sealed["gross_gain_bytes_per_million_raw"]
    net_bpm = gross_bpm - package_bytes / 1000.0

    semantic_p1 = fitted["semantic"]["candidate_p1"]
    semantic_payload = fitted["semantic"]["payload"]
    decoded_truth = range_decode(semantic_payload, semantic_p1)
    candidate_arithmetic_decode = np.array_equal(decoded_truth, all_truth)
    if not candidate_arithmetic_decode:
        raise ValueError("semantic adjusted arithmetic stream does not decode")
    decoded_wrt = np.packbits(decoded_truth, bitorder="big").tobytes()
    if decoded_wrt != wrt:
        raise ValueError("semantic adjusted stream reconstructs different WRT bytes")
    second_payload = range_encode(semantic_p1, all_truth)
    if second_payload != semantic_payload:
        raise ValueError("semantic selected payload is not byte-identical on replay")

    reconstructed_store = full_store[:5] + decoded_wrt + full_store[5 + len(wrt) :]
    if reconstructed_store != full_store:
        raise ValueError("reconstructed WRT store differs from the canonical store")
    store_path = args.output_dir / "semantic_reconstructed_full.wrt"
    restored_path = args.output_dir / "semantic_reconstructed_full.raw"
    store_path.write_bytes(reconstructed_store)
    with (args.output_dir / "inverse.stdout.log").open("wb") as stdout, (
        args.output_dir / "inverse.stderr.log"
    ).open("wb") as stderr:
        inverse = subprocess.run(
            [
                str(args.backend),
                "-d",
                str(args.dictionary),
                str(store_path),
                str(restored_path),
            ],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    raw_roundtrip = (
        inverse.returncode == 0
        and restored_path.is_file()
        and sha256_file(restored_path) == EXPECTED_SHA256["raw_input"]
    )
    if not raw_roundtrip:
        raise ValueError("official inverse of semantic replay failed")

    for mode in MODES:
        (args.output_dir / f"{mode}.payload").write_bytes(fitted[mode]["payload"])
        (args.output_dir / f"{mode}_model.bin.zlib").write_bytes(
            compressed_models[mode]
        )

    runtime.update(
        {
            "max_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "max_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        }
    )
    proofs = {
        "joint_antecedent_exact": required_antecedent,
        "prefix_parent_arithmetic_decode": True,
        "prefix_parent_second_payload_identity": True,
        "candidate_arithmetic_decode": candidate_arithmetic_decode,
        "complete_wrt_reconstruction": decoded_wrt == wrt,
        "reconstructed_full_store_identity": reconstructed_store == full_store,
        "official_raw_inverse": raw_roundtrip,
        "second_candidate_payload_identity": second_payload == semantic_payload,
        "all_probability_values_legal_nonzero": bool(
            np.all((semantic_p1 > 0) & (semantic_p1 < 65536))
        ),
        "all_repeated_fits_identical": all(
            all(row["determinism"].values()) for row in fitted.values()
        ),
        "matched_parameter_counts": len(parameter_counts) == 1,
    }
    if not all(proofs.values()):
        raise ValueError(f"exact proof failure: {proofs}")

    conditions = {
        **proofs,
        "development_semantic_gain_positive": controls["semantic"]["splits"][
            "development"
        ]["gain_bytes"]
        > 0,
        "selection_semantic_gain_positive": controls["semantic"]["splits"][
            "selection"
        ]["gain_bytes"]
        > 0,
        "sealed_semantic_gross_at_least_3000_BPM": gross_bpm >= GROSS_GATE_BPM,
        "sealed_semantic_net_at_least_2100_BPM": net_bpm >= NET_GATE_BPM,
        "sealed_semantic_beats_flat": semantic_sealed["candidate_payload_bytes"]
        < controls["flat"]["splits"]["sealed_confirmation"][
            "candidate_payload_bytes"
        ],
        "sealed_semantic_beats_fixed": semantic_sealed["candidate_payload_bytes"]
        < controls["fixed"]["splits"]["sealed_confirmation"][
            "candidate_payload_bytes"
        ],
        "sealed_semantic_beats_lagged": semantic_sealed["candidate_payload_bytes"]
        < controls["lagged"]["splits"]["sealed_confirmation"][
            "candidate_payload_bytes"
        ],
        "matched_package_within_ceiling": package_bytes <= PACKAGE_CEILING_BYTES,
    }
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    verdict = "AUTHORIZED_DISTANT_REPLAY" if authorized else "REJECT"

    decision = {
        "schema": "mobius2_noema_semantic_boundary_hierarchy_qh0_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_exact_semantic_boundary_headroom",
        "claim_boundary": (
            "Exact opening-prefix semantic-boundary residual headroom over the "
            "exported JANUS-plus-quotient trajectory; no deterministic integer "
            "runtime, native integration, distant transfer, forecast, or score credit."
        ),
        "inputs": inputs,
        "population": {
            "complete_pages": len(pages),
            "raw_equivalent_bytes": FROZEN_RAW_BYTES,
            "wrt_bytes": FROZEN_WRT_BYTES,
            "p1_rows": FROZEN_ROWS,
            "complete_patches": len(patches),
            "modeled_wrt_bytes": len(patches) * PATCH_BYTES,
            "unmodeled_wrt_bytes": FROZEN_WRT_BYTES
            - len(patches) * PATCH_BYTES,
            "page_splits": {
                split: sum(page.split == split for page in pages) for split in SPLITS
            },
            "patch_splits": {
                split: len(split_patch_ids[split]) for split in SPLITS
            },
            "boundary_receipt": boundary_receipt,
            "partitions": {
                name: partition_receipt(value)
                for name, value in partitions.items()
            },
        },
        "architecture": {
            "parameter_count": next(iter(parameter_counts)),
            "patch_bytes": PATCH_BYTES,
            "byte_embedding_width": candidate.BYTE_EMBEDDING_WIDTH,
            "summary_width": candidate.SUMMARY_WIDTH,
            "level_count": candidate.LEVEL_COUNT,
            "level_embedding_width": candidate.LEVEL_EMBEDDING_WIDTH,
            "prefix_nodes": candidate.PREFIX_NODES,
            "shared_transition": "one GRU reused within and across segments",
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "seed": SEED,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "gradient_clip": GRADIENT_CLIP,
            "quantization": "canonical symmetric signed int8 per tensor",
            "selection": "minimum exact selection payload; earliest epoch tie",
        },
        "runtime": runtime,
        "parent": {
            "prefix_payload_bytes": len(parent_payload),
            "prefix_payload_sha256": sha256_bytes(parent_payload),
            "full_joint_payload_artifact": inputs["joint_payload"],
        },
        "controls": controls,
        "training": {
            mode: {
                "selected_epoch": fitted[mode]["run"]["selected_epoch"],
                "history": fitted[mode]["run"]["history"],
                "determinism": fitted[mode]["determinism"],
                "canonical_model_bytes": len(fitted[mode]["run"]["model_blob"]),
                "canonical_model_sha256": sha256_bytes(
                    fitted[mode]["run"]["model_blob"]
                ),
                "zlib9_model_bytes": len(compressed_models[mode]),
                "zlib9_model_sha256": sha256_bytes(compressed_models[mode]),
            }
            for mode in MODES
        },
        "package": {
            "matched_model_charge_bytes": matched_model_bytes,
            "decoder_allowance_bytes": DECODER_ALLOWANCE_BYTES,
            "framing_allowance_bytes": FRAMING_ALLOWANCE_BYTES,
            "matched_total_bytes": package_bytes,
            "ceiling_bytes": PACKAGE_CEILING_BYTES,
            "amortized_bytes_per_million": package_bytes / 1000.0,
        },
        "economics": {
            "sealed_semantic_gross_bytes_per_million": gross_bpm,
            "sealed_semantic_package_adjusted_bytes_per_million": net_bpm,
            "gross_gate_bytes_per_million": GROSS_GATE_BPM,
            "net_gate_bytes_per_million": NET_GATE_BPM,
            "forecast_bytes_unchanged": 109_389_323,
            "remaining_target_debt_bytes": 1_389_323,
        },
        "proof": proofs,
        "gates": {"conditions": conditions, "failed_conditions": failed},
        "decision": {
            "verdict": verdict,
            "promotion_authorized": authorized,
            "forecast_bytes": 109_389_323,
            "score_credit_bytes": 0,
            "next_action": (
                "run one frozen distant semantic-boundary replay"
                if authorized
                else "retire this exact semantic-boundary hierarchy without width, boundary, optimizer, epoch, or quantization sweeps"
            ),
        },
        "score_credit_bytes": 0,
    }
    temporary = decision_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    temporary.replace(decision_path)
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "verdict": verdict,
                "semantic_full_gain_bytes": controls["semantic"]["full_gain_bytes"],
                "semantic_sealed_gain_bytes": semantic_sealed["gain_bytes"],
                "semantic_sealed_gross_BPM": gross_bpm,
                "semantic_sealed_net_BPM": net_bpm,
                "flat_sealed_gain_bytes": controls["flat"]["splits"][
                    "sealed_confirmation"
                ]["gain_bytes"],
                "fixed_sealed_gain_bytes": controls["fixed"]["splits"][
                    "sealed_confirmation"
                ]["gain_bytes"],
                "lagged_sealed_gain_bytes": controls["lagged"]["splits"][
                    "sealed_confirmation"
                ]["gain_bytes"],
                "failed_conditions": failed,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
