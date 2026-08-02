#!/usr/bin/env python3
"""Run the frozen LOGOS semantic sentence edit-bypass QH0 gate."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from typing import Any, Iterable, Sequence
import zlib

import numpy as np

from bifrons_reverse_causal_joint_ceiling import read_page_map, read_p1
from endpoint428_parent_recovery_gate import observed_artifact
from radix_island_oracle import EmissionGroup, emission_groups
from route_e_state_preserving_prototype_bypass_gate import (
    RangeMaximum,
    SuffixAutomaton,
)
from wrt_exact import parse_store_bytes, read_dictionary_words


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
CANDIDATE_ID = "mobius2_logos_semantic_sentence_edit_bypass_qh0_v1"
PROPOSAL_ID = "mobius2_logos_semantic_sentence_edit_bypass_v1"
PROGRAM = PROJECT / "programs" / CANDIDATE_ID / "program.py"
PLAN = PROJECT / "docs/mobius2_logos_semantic_sentence_edit_bypass_qh0_plan.md"
SCHEMA = (
    PROJECT
    / "docs/mobius2_logos_semantic_sentence_edit_bypass_qh0_decision.schema.json"
)
ROCM_PYTHON = REPO / ".venv_rocm/bin/python"
MODEL_SNAPSHOT = Path(
    "/home/x/.cache/huggingface/hub/"
    "models--google--embeddinggemma-300m/snapshots/"
    "57c266a740f537b4dc058e1b0cda161fd15afa75"
)
SOURCE_ROOT = Path(
    "/home/x/enwiki9-nonproof/results/"
    "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
    "clean-build-b/build"
)

RAW_LIMIT = 1_000_000
FROZEN_RAW_BYTES = 984_835
FROZEN_WRT_BYTES = 591_230
FROZEN_PAGES = 171
FROZEN_ROWS = FROZEN_WRT_BYTES * 8
STORE_HEADER = b"\x80\x00\x00\x00\x00"
CMIX_HEADER_BYTES = 37
QBITS_PER_BIT = 256
QBITS_PER_BYTE = 8 * QBITS_PER_BIT
MIN_COPY_BYTES = 8
MIN_GROUPS = 6
MAX_GROUPS = 128
MIN_RAW_BYTES = 24
MAX_RAW_BYTES = 512
MIN_ASCII_LETTERS = 12
NEIGHBORS = 8
ROTATION_LAG = 31
EMBEDDING_DIMENSION = 128
EMBEDDING_MAX_TOKENS = 128
EMBEDDING_BATCH = 32
EMBEDDING_PROMPT = "task: clustering | query: "
GROSS_GATE_BPM = 3_000.0
NEGATIVE_INFINITY = -(1 << 120)

PROHIBITED = (
    b"{{",
    b"}}",
    b"{|",
    b"|}",
    b"<ref",
    b"</ref",
    b"<gallery",
    b"</gallery",
    b"[[category:",
    b"[[file:",
    b"[[image:",
    b"<table",
)
WORD_RE = re.compile(rb"[a-z][a-z0-9'-]{1,}")

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


def load_program() -> Any:
    spec = importlib.util.spec_from_file_location(
        "mobius2_logos_semantic_sentence_edit_bypass_program", PROGRAM
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load candidate program: {PROGRAM}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


candidate = load_program()


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    split: str


@dataclass(frozen=True)
class TextPopulation:
    page: Page
    raw_start: int
    raw_end: int
    group_start: int
    group_end: int


@dataclass(frozen=True)
class ClauseSpan:
    index: int
    page_index: int
    split: str
    wrt_start: int
    wrt_end: int
    raw_start: int
    raw_end: int
    surface: bytes
    words: frozenset[bytes]

    @property
    def wrt_bytes(self) -> int:
        return self.wrt_end - self.wrt_start


@dataclass(frozen=True)
class PlanChoice:
    target_index: int
    prototype_index: int
    plan: Any
    displaced_qbits: int
    command_bytes: int
    predicted_net_qbits: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bind(path: Path, expected: str, label: str) -> dict[str, Any]:
    row = observed_artifact(path.resolve())
    if row["sha256"] != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {row['sha256']}")
    return row


def ensure_rocm_runtime() -> None:
    if not ROCM_PYTHON.is_file():
        raise FileNotFoundError(f"missing ROCm Python: {ROCM_PYTHON}")
    if Path(sys.prefix).resolve() == (REPO / ".venv_rocm").resolve():
        if os.environ.get("HSA_OVERRIDE_GFX_VERSION") != "11.0.0":
            raise RuntimeError("ROCm runtime lacks frozen HSA GFX override")
        return
    if os.environ.get("LOGOS_SEMANTIC_REEXEC") == "1":
        raise RuntimeError("failed to enter the frozen ROCm Python runtime")
    environment = os.environ.copy()
    environment["LOGOS_SEMANTIC_REEXEC"] = "1"
    environment["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    environment["PYTHONUNBUFFERED"] = "1"
    environment["TOKENIZERS_PARALLELISM"] = "false"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def model_manifest() -> tuple[list[dict[str, Any]], str]:
    relative_paths = (
        "config.json",
        "modules.json",
        "sentence_bert_config.json",
        "tokenizer.json",
        "tokenizer.model",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "added_tokens.json",
        "model.safetensors",
        "1_Pooling/config.json",
        "2_Dense/config.json",
        "2_Dense/model.safetensors",
        "3_Dense/config.json",
        "3_Dense/model.safetensors",
    )
    rows: list[dict[str, Any]] = []
    for relative in relative_paths:
        path = MODEL_SNAPSHOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        rows.append(
            {
                "relative_path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    serialized = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return rows, sha256_bytes(serialized)


def runtime_probe(torch: Any) -> dict[str, Any]:
    if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
        raise RuntimeError("ROCm CUDA-compatible device is not visible")
    device = torch.device("cuda:0")
    left = torch.arange(64 * 64, device=device, dtype=torch.float32).reshape(64, 64)
    right = torch.arange(64 * 64, device=device, dtype=torch.float32).reshape(64, 64)
    right = (right.remainder(97) - 48.0) / 97.0
    product = left @ right
    torch.cuda.synchronize()
    product_bytes = product.detach().cpu().numpy().astype("<f4", copy=False).tobytes()
    properties = torch.cuda.get_device_properties(0)
    return {
        "sys_executable": sys.executable,
        "torch_version": torch.__version__,
        "hip_runtime_version": torch.version.hip,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_visible_device_count": int(torch.cuda.device_count()),
        "device": str(device),
        "device_name": torch.cuda.get_device_name(0),
        "device_architecture": getattr(properties, "gcnArchName", None),
        "hsa_override_gfx_version": os.environ.get("HSA_OVERRIDE_GFX_VERSION"),
        "training_dtype": "none; inference torch.bfloat16 backbone and float32 projection",
        "matrix_shape": [64, 64],
        "matrix_output_sha256": sha256_bytes(product_bytes),
        "matrix_output_sum": float(product.sum().item()),
        "explicit_synchronization": True,
        "runtime_mode": "rocm_gfx_override",
    }


def embedding_blob(values: np.ndarray) -> bytes:
    if values.dtype != np.int16 or values.ndim != 2:
        raise ValueError("embedding serialization requires a two-dimensional int16 matrix")
    header = struct.pack("<8sII", b"LGSEMB1\0", values.shape[0], values.shape[1])
    return header + values.astype("<i2", copy=False).tobytes(order="C")


def encode_embeddings(
    texts: Sequence[str],
    tokenizer: Any,
    model: Any,
    dense_a: Any,
    dense_b: Any,
    torch: Any,
) -> np.ndarray:
    output: list[np.ndarray] = []
    device = torch.device("cuda:0")
    with torch.inference_mode():
        for start in range(0, len(texts), EMBEDDING_BATCH):
            rows = [EMBEDDING_PROMPT + value for value in texts[start : start + EMBEDDING_BATCH]]
            encoded = tokenizer(
                rows,
                padding=True,
                truncation=True,
                max_length=EMBEDDING_MAX_TOKENS,
                return_tensors="pt",
            )
            encoded = {name: value.to(device) for name, value in encoded.items()}
            state = model(**encoded, use_cache=False).last_hidden_state.float()
            mask = encoded["attention_mask"].unsqueeze(-1).float()
            pooled = (state * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
            projected = pooled @ dense_a.transpose(0, 1)
            projected = projected @ dense_b.transpose(0, 1)
            projected = torch.nn.functional.normalize(projected, p=2, dim=1)
            projected = projected[:, :EMBEDDING_DIMENSION]
            projected = torch.nn.functional.normalize(projected, p=2, dim=1)
            if not bool(torch.isfinite(projected).all().item()):
                raise ValueError("semantic embedding contains a nonfinite value")
            quantized = torch.clamp(
                torch.round(projected * 32767.0), -32767, 32767
            ).to(torch.int16)
            output.append(quantized.cpu().numpy())
            print(
                f"[logos-semantic] embedding={min(start + EMBEDDING_BATCH, len(texts))}/{len(texts)}",
                flush=True,
            )
    return np.concatenate(output, axis=0) if output else np.empty((0, EMBEDDING_DIMENSION), dtype=np.int16)


def build_embeddings(texts: Sequence[str]) -> tuple[np.ndarray, bytes, dict[str, Any], Any]:
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModel, AutoTokenizer

    runtime = runtime_probe(torch)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_SNAPSHOT, local_files_only=True)
    model = AutoModel.from_pretrained(
        MODEL_SNAPSHOT,
        local_files_only=True,
        torch_dtype=torch.bfloat16,
    ).eval().to("cuda:0")
    dense_a = load_file(str(MODEL_SNAPSHOT / "2_Dense/model.safetensors"))[
        "linear.weight"
    ].to(device="cuda:0", dtype=torch.float32)
    dense_b = load_file(str(MODEL_SNAPSHOT / "3_Dense/model.safetensors"))[
        "linear.weight"
    ].to(device="cuda:0", dtype=torch.float32)
    first = encode_embeddings(texts, tokenizer, model, dense_a, dense_b, torch)
    second = encode_embeddings(texts, tokenizer, model, dense_a, dense_b, torch)
    first_blob = embedding_blob(first)
    second_blob = embedding_blob(second)
    if first_blob != second_blob:
        raise RuntimeError("repeated quantized semantic embedding blob differs")
    runtime.update(
        {
            "transformers_version": __import__("transformers").__version__,
            "embedding_backbone_dtype": "torch.bfloat16",
            "projection_dtype": "torch.float32",
            "embedding_rows": len(first),
            "embedding_dimension": EMBEDDING_DIMENSION,
            "embedding_blob_sha256": sha256_bytes(first_blob),
            "embedding_repeat_identity": True,
            "max_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "max_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        }
    )
    del model, dense_a, dense_b, tokenizer
    torch.cuda.empty_cache()
    return first, first_blob, runtime, torch


def read_pages(path: Path) -> tuple[list[Page], int, int]:
    rows = [row for row in read_page_map(path) if row[1] <= RAW_LIMIT]
    if not rows:
        raise ValueError("no complete page within the frozen raw limit")
    count = len(rows)
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    pages: list[Page] = []
    for index, (raw_start, raw_end, row_start, row_end) in enumerate(rows):
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not WRT-byte aligned")
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
    raw_bytes = pages[-1].raw_end
    wrt_bytes = pages[-1].wrt_end
    if (count, raw_bytes, wrt_bytes) != (
        FROZEN_PAGES,
        FROZEN_RAW_BYTES,
        FROZEN_WRT_BYTES,
    ):
        raise ValueError("frozen opening population boundary changed")
    return pages, raw_bytes, wrt_bytes


def text_populations(
    raw: bytes, pages: Sequence[Page], groups: Sequence[EmissionGroup]
) -> list[TextPopulation]:
    starts = np.asarray([group.raw_start for group in groups], dtype=np.int64)
    output: list[TextPopulation] = []
    for page in pages:
        opening = raw.find(b"<text", page.raw_start, page.raw_end)
        content_start = raw.find(b">", opening, page.raw_end) if opening >= 0 else -1
        if content_start < 0:
            raise ValueError(f"page {page.index} has no complete text opening")
        content_start += 1
        content_end = raw.find(b"</text>", content_start, page.raw_end)
        if content_end < 0:
            raise ValueError(f"page {page.index} has no complete text closing")
        group_start = int(np.searchsorted(starts, content_start, side="left"))
        group_end = int(np.searchsorted(starts, content_end, side="left"))
        while group_start < len(groups) and groups[group_start].raw_start < content_start:
            group_start += 1
        while group_end > group_start and groups[group_end - 1].raw_end > content_end:
            group_end -= 1
        if group_start >= group_end:
            raise ValueError(f"page {page.index} has no aligned text groups")
        output.append(
            TextPopulation(page, content_start, content_end, group_start, group_end)
        )
    return output


def eligible_clause(
    raw: bytes,
    groups: Sequence[EmissionGroup],
    start: int,
    end: int,
) -> tuple[int, int, bytes, frozenset[bytes]] | None:
    while start < end and groups[start].decoded.isspace():
        start += 1
    while end > start and groups[end - 1].decoded.isspace():
        end -= 1
    if not MIN_GROUPS <= end - start <= MAX_GROUPS:
        return None
    raw_start = groups[start].raw_start
    raw_end = groups[end - 1].raw_end
    surface = raw[raw_start:raw_end]
    lower = surface.lower()
    if not MIN_RAW_BYTES <= len(surface) <= MAX_RAW_BYTES:
        return None
    letters = sum(
        ord("a") <= value <= ord("z") or ord("A") <= value <= ord("Z")
        for value in surface
    )
    if letters < MIN_ASCII_LETTERS:
        return None
    if b"<" in surface or any(token in lower for token in PROHIBITED):
        return None
    words = frozenset(WORD_RE.findall(lower))
    if len(words) < 2:
        return None
    return start, end, surface, words


def discover_clauses(
    raw: bytes,
    groups: Sequence[EmissionGroup],
    populations: Sequence[TextPopulation],
) -> tuple[list[ClauseSpan], int]:
    clauses: list[ClauseSpan] = []
    scanned = 0
    for population in populations:
        start = population.group_start
        for index in range(population.group_start, population.group_end):
            if not any(value in groups[index].decoded for value in b".!?;\n"):
                continue
            scanned += 1
            selected = eligible_clause(raw, groups, start, index + 1)
            start = index + 1
            if selected is None:
                continue
            group_start, group_end, surface, words = selected
            clauses.append(
                ClauseSpan(
                    len(clauses),
                    population.page.index,
                    population.page.split,
                    groups[group_start].stream_start,
                    groups[group_end - 1].stream_end,
                    groups[group_start].raw_start,
                    groups[group_end - 1].raw_end,
                    surface,
                    words,
                )
            )
        if start < population.group_end:
            scanned += 1
            selected = eligible_clause(raw, groups, start, population.group_end)
            if selected is not None:
                group_start, group_end, surface, words = selected
                clauses.append(
                    ClauseSpan(
                        len(clauses),
                        population.page.index,
                        population.page.split,
                        groups[group_start].stream_start,
                        groups[group_end - 1].stream_end,
                        groups[group_start].raw_start,
                        groups[group_end - 1].raw_end,
                        surface,
                        words,
                    )
                )
    for left, right in zip(clauses, clauses[1:]):
        if left.wrt_end > right.wrt_start:
            raise ValueError("eligible sentence spans overlap")
    return clauses, scanned


def canonical_text(surface: bytes) -> str:
    return " ".join(surface.decode("utf-8", errors="replace").split())


def semantic_candidates(values: np.ndarray, torch: Any) -> list[tuple[int, ...]]:
    if values.shape[1] != EMBEDDING_DIMENSION:
        raise ValueError("semantic embedding dimension differs")
    matrix = torch.from_numpy(values.astype(np.float32)).to("cuda:0")
    matrix = torch.nn.functional.normalize(matrix, p=2, dim=1)
    output: list[tuple[int, ...]] = []
    block = 256
    with torch.inference_mode():
        for start in range(0, len(values), block):
            end = min(start + block, len(values))
            scores = (matrix[start:end] @ matrix.transpose(0, 1)).cpu().numpy()
            for local, target in enumerate(range(start, end)):
                count = min(NEIGHBORS, target)
                if count == 0:
                    output.append(())
                    continue
                row = scores[local, :target]
                selected = (
                    np.arange(target, dtype=np.int64)
                    if count == target
                    else np.argpartition(-row, count - 1)[:count]
                )
                ordered = tuple(
                    sorted(
                        (int(value) for value in selected),
                        key=lambda value: (-float(row[value]), value),
                    )
                )
                output.append(ordered)
            print(f"[logos-semantic] retrieval={end}/{len(values)}", flush=True)
    del matrix
    torch.cuda.empty_cache()
    return output


def lexical_candidates(clauses: Sequence[ClauseSpan]) -> list[tuple[int, ...]]:
    document_frequency: Counter[bytes] = Counter()
    for clause in clauses:
        document_frequency.update(clause.words)
    maximum_frequency = max(2, len(clauses) // 5)
    filtered = [
        frozenset(word for word in clause.words if document_frequency[word] <= maximum_frequency)
        for clause in clauses
    ]
    postings: dict[bytes, list[int]] = defaultdict(list)
    output: list[tuple[int, ...]] = []
    for target, words in enumerate(filtered):
        intersections: Counter[int] = Counter()
        for word in words:
            intersections.update(postings[word])
        ranked = sorted(
            intersections,
            key=lambda source: (
                -intersections[source] / max(
                    1, len(words) + len(filtered[source]) - intersections[source]
                ),
                -intersections[source],
                source,
            ),
        )
        selected = ranked[: min(NEIGHBORS, target)]
        used = set(selected)
        cursor = target - 1
        while len(selected) < min(NEIGHBORS, target):
            if cursor not in used:
                selected.append(cursor)
                used.add(cursor)
            cursor -= 1
        output.append(tuple(selected))
        for word in words:
            postings[word].append(target)
    return output


def rotated_candidates(
    semantic: Sequence[Sequence[int]],
) -> list[tuple[int, ...]]:
    output: list[tuple[int, ...]] = []
    for target in range(len(semantic)):
        source_row = max(0, target - ROTATION_LAG)
        selected = [value for value in semantic[source_row] if value < target]
        selected = list(dict.fromkeys(selected))[: min(NEIGHBORS, target)]
        used = set(selected)
        cursor = target - 1
        while len(selected) < min(NEIGHBORS, target):
            if cursor not in used:
                selected.append(cursor)
                used.add(cursor)
            cursor -= 1
        output.append(tuple(selected))
    return output


def serialize_candidates(rows: Sequence[Sequence[int]]) -> bytes:
    output = bytearray(struct.pack("<8sI", b"LGSCND1\0", len(rows)))
    for row in rows:
        output += struct.pack("<B", len(row))
        for value in row:
            output += struct.pack("<I", int(value))
    return bytes(output)


def qbit_costs(probabilities: np.ndarray, truth: bytes) -> np.ndarray:
    values = np.arange(65536, dtype=np.float64) / 65536.0
    one = np.clip(values, 1.0 / 65536.0, 65535.0 / 65536.0)
    zero = 1.0 - one
    one_table = np.rint(-np.log2(one) * QBITS_PER_BIT).astype(np.int32)
    zero_table = np.rint(-np.log2(zero) * QBITS_PER_BIT).astype(np.int32)
    bits = np.unpackbits(np.frombuffer(truth, dtype=np.uint8), bitorder="big")
    selected = np.where(bits != 0, one_table[probabilities], zero_table[probabilities])
    return selected.reshape(len(truth), 8).sum(axis=1, dtype=np.int64)


def length_groups(maximum: int) -> list[tuple[int, int, int]]:
    groups: list[tuple[int, int, int]] = []
    lower = MIN_COPY_BYTES
    encoded_bytes = candidate.uleb_size(lower)
    while lower <= maximum:
        upper = min(maximum, (1 << (7 * encoded_bytes)) - 1)
        groups.append((lower, upper, encoded_bytes))
        lower = upper + 1
        encoded_bytes += 1
    return groups


def exact_multiple_copies(
    longest: Sequence[int],
    sources: Sequence[int],
    cost_prefix: Sequence[int],
) -> tuple[tuple[Any, ...], int, int]:
    length = len(longest)
    optimum = [0] * (length + 1)
    choice: list[tuple[int, int] | None] = [None] * length
    maximum = RangeMaximum(length + 1)
    maximum.update(length, int(cost_prefix[length]))
    for target_start in range(length - 1, -1, -1):
        best = optimum[target_start + 1]
        best_choice: tuple[int, int] | None = None
        available = longest[target_start]
        if available >= MIN_COPY_BYTES:
            source_start = sources[target_start]
            fixed_command_bytes = (
                candidate.uleb_size(target_start)
                + candidate.uleb_size(source_start)
            )
            for lower, upper, length_bytes in length_groups(available):
                value, stop = maximum.query(
                    target_start + lower, target_start + upper + 1
                )
                candidate_value = (
                    value
                    - int(cost_prefix[target_start])
                    - (fixed_command_bytes + length_bytes) * QBITS_PER_BYTE
                )
                if candidate_value > best:
                    best = candidate_value
                    best_choice = (source_start, stop - target_start)
        optimum[target_start] = best
        choice[target_start] = best_choice
        maximum.update(target_start, int(cost_prefix[target_start]) + best)
    copies: list[Any] = []
    displaced = 0
    command_bytes = 0
    position = 0
    while position < length:
        selected = choice[position]
        if selected is None:
            position += 1
            continue
        source_start, copy_length = selected
        copies.append(candidate.CopySpan(position, source_start, copy_length))
        displaced += int(cost_prefix[position + copy_length] - cost_prefix[position])
        command_bytes += (
            candidate.uleb_size(position)
            + candidate.uleb_size(source_start)
            + candidate.uleb_size(copy_length)
        )
        position += copy_length
    return tuple(copies), displaced, command_bytes


def evaluate_pair(
    target: ClauseSpan,
    prototype: ClauseSpan,
    target_bytes: bytes,
    automaton: SuffixAutomaton,
    byte_costs: np.ndarray,
) -> PlanChoice | None:
    longest, sources = automaton.longest_starts(target_bytes)
    costs = byte_costs[target.wrt_start : target.wrt_end]
    prefix = np.empty(len(costs) + 1, dtype=np.int64)
    prefix[0] = 0
    np.cumsum(costs, out=prefix[1:])
    copies, displaced, copy_command_bytes = exact_multiple_copies(
        longest, sources, prefix
    )
    if not copies:
        return None
    command_bytes = (
        candidate.uleb_size(target.wrt_start)
        + candidate.uleb_size(target.wrt_bytes)
        + candidate.uleb_size(prototype.wrt_start)
        + candidate.uleb_size(prototype.wrt_bytes)
        + candidate.COUNT.size
        + copy_command_bytes
    )
    net = displaced - command_bytes * QBITS_PER_BYTE
    if net <= 0:
        return None
    return PlanChoice(
        target.index,
        prototype.index,
        candidate.PagePlan(
            target.wrt_start,
            target.wrt_bytes,
            prototype.wrt_start,
            prototype.wrt_bytes,
            copies,
        ),
        displaced,
        command_bytes,
        net,
    )


def better(current: PlanChoice | None, row: PlanChoice | None) -> PlanChoice | None:
    if row is None:
        return current
    if current is None:
        return row
    if row.predicted_net_qbits > current.predicted_net_qbits:
        return row
    if (
        row.predicted_net_qbits == current.predicted_net_qbits
        and row.prototype_index < current.prototype_index
    ):
        return row
    return current


def choose_plans(
    clauses: Sequence[ClauseSpan],
    candidates_by_variant: dict[str, Sequence[Sequence[int]]],
    wrt: bytes,
    byte_costs: np.ndarray,
) -> tuple[dict[str, list[PlanChoice]], int]:
    automata = [
        SuffixAutomaton(wrt[row.wrt_start : row.wrt_end]) for row in clauses
    ]
    chosen: dict[str, list[PlanChoice]] = {name: [] for name in candidates_by_variant}
    evaluations = 0
    for target in clauses:
        source_union = sorted(
            {
                source
                for rows in candidates_by_variant.values()
                for source in rows[target.index]
            }
        )
        pair_rows: dict[int, PlanChoice | None] = {}
        target_bytes = wrt[target.wrt_start : target.wrt_end]
        for source in source_union:
            prototype = clauses[source]
            if prototype.wrt_end > target.wrt_start:
                raise ValueError("retrieval candidate is not strictly prior")
            pair_rows[source] = evaluate_pair(
                target,
                prototype,
                target_bytes,
                automata[source],
                byte_costs,
            )
            evaluations += 1
        for name, rows in candidates_by_variant.items():
            selected: PlanChoice | None = None
            for source in rows[target.index]:
                selected = better(selected, pair_rows[source])
            if selected is not None:
                chosen[name].append(selected)
        if (target.index + 1) % 256 == 0 or target.index + 1 == len(clauses):
            active = " ".join(
                f"{name}={len(chosen[name])}" for name in sorted(chosen)
            )
            print(
                f"[logos-semantic] align={target.index + 1}/{len(clauses)} "
                f"pairs={evaluations} {active}",
                flush=True,
            )
    return chosen, evaluations


def build_variant(
    name: str,
    rows: Sequence[PlanChoice],
    wrt: bytes,
    probabilities: np.ndarray,
    parent_total: int,
    output_path: Path | None,
) -> tuple[dict[str, Any], bytes]:
    plans = tuple(row.plan for row in sorted(rows, key=lambda value: value.plan.target_start))
    archive = candidate.build_bypass_archive(wrt, probabilities, plans)
    decoded, decoded_plans = candidate.decode_bypass_archive(archive, probabilities)
    second = candidate.build_bypass_archive(wrt, probabilities, plans)
    commands = candidate.encode_commands(plans, len(wrt))
    canonical_commands = candidate.encode_commands(decoded_plans, len(wrt))
    if output_path is not None:
        output_path.write_bytes(archive)
    header = candidate.BYPASS_HEADER.unpack_from(archive)
    receipt = {
        "name": name,
        "archive_bytes": len(archive),
        "archive_sha256": sha256_bytes(archive),
        "gain_bytes": parent_total - len(archive),
        "command_bytes": len(commands),
        "command_sha256": sha256_bytes(commands),
        "literal_bits": int(header[4]),
        "literal_payload_bytes": int(header[5]),
        "active_spans": len(plans),
        "copy_commands": sum(len(plan.copies) for plan in plans),
        "copied_wrt_bytes": sum(
            copy.length for plan in plans for copy in plan.copies
        ),
        "predicted_displaced_qbits": sum(row.displaced_qbits for row in rows),
        "predicted_net_qbits": sum(row.predicted_net_qbits for row in rows),
        "all_sources_strictly_prior": all(
            plan.prototype_start + plan.prototype_length <= plan.target_start
            for plan in plans
        ),
        "command_roundtrip": decoded_plans == plans and canonical_commands == commands,
        "wrt_roundtrip": decoded == wrt,
        "second_archive_identity": second == archive,
    }
    if not all(
        (
            receipt["all_sources_strictly_prior"],
            receipt["command_roundtrip"],
            receipt["wrt_roundtrip"],
            receipt["second_archive_identity"],
        )
    ):
        raise ValueError(f"{name} exact bypass replay failed")
    return receipt, decoded


def main() -> int:
    ensure_rocm_runtime()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=PROJECT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--joint-payload",
        type=Path,
        default=PROJECT
        / "results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=PROJECT
        / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--page-map",
        type=Path,
        default=PROJECT / "results/mobius2_tessera_typed_fiber_ceiling_qh0_v1/page_map.bin",
    )
    parser.add_argument(
        "--trace-decision",
        type=Path,
        default=PROJECT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/decision.json",
    )
    parser.add_argument("--raw-input", type=Path, default=PROJECT / "data/enwik9_10000000.bin")
    parser.add_argument("--dictionary", type=Path, default=SOURCE_ROOT / "english.dic")
    parser.add_argument("--backend", type=Path, default=SOURCE_ROOT / "cmix.bin")
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT / "results" / CANDIDATE_ID
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = args.output_dir / "decision.json"
    if decision_path.exists():
        raise FileExistsError(f"refusing to overwrite {decision_path}")

    paths = {
        "backend": args.backend,
        "dictionary": args.dictionary,
        "joint_p1": args.joint_p1,
        "joint_payload": args.joint_payload,
        "wrt_store": args.wrt_store,
        "page_map": args.page_map,
        "trace_decision": args.trace_decision,
        "raw_input": args.raw_input,
    }
    inputs = {
        name: bind(path, EXPECTED_SHA256[name], name) for name, path in paths.items()
    }
    trace_decision = json.loads(args.trace_decision.read_text())
    if trace_decision.get("decision", {}).get("verdict") != "exact_joint_p1_trace_recovered":
        raise ValueError("joint trace antecedent is not certified")
    required_proofs = (
        "complete_wrt_truth_identity",
        "exact_arithmetic_decode",
        "joint_payload_identity_a",
        "joint_payload_identity_b",
        "repeated_adjusted_p1_identity",
    )
    if not all(trace_decision.get("proof", {}).get(name) is True for name in required_proofs):
        raise ValueError("joint trace antecedent lacks an exact proof")

    pages, raw_bytes, wrt_bytes = read_pages(args.page_map)
    full_store = args.wrt_store.read_bytes()
    full_raw = args.raw_input.read_bytes()
    if full_store[:5] != STORE_HEADER or len(full_raw) != 10_000_000:
        raise ValueError("canonical WRT store or raw input has an invalid frame")
    wrt = full_store[5 : 5 + wrt_bytes]
    patched_wrt = bytearray(wrt)
    patched_wrt[1:5] = raw_bytes.to_bytes(4, "big")
    parsed = parse_store_bytes(
        STORE_HEADER + bytes(patched_wrt), read_dictionary_words(args.dictionary)
    )
    if parsed.decoded != full_raw[:raw_bytes]:
        raise ValueError("patched prefix parse differs from the complete-page raw prefix")
    groups = emission_groups(parsed)
    populations = text_populations(parsed.decoded, pages, groups)
    clauses, scanned = discover_clauses(parsed.decoded, groups, populations)
    if not clauses:
        raise ValueError("frozen population contains no eligible sentence spans")
    texts = [canonical_text(clause.surface) for clause in clauses]
    text_blob = json.dumps(texts, ensure_ascii=False, separators=(",", ":")).encode()

    print(
        f"[logos-semantic] pages={len(pages)} raw={raw_bytes} wrt={wrt_bytes} "
        f"clauses={len(clauses)} scanned={scanned}",
        flush=True,
    )
    manifest_rows, manifest_sha = model_manifest()
    embeddings, embeddings_blob, runtime, torch = build_embeddings(texts)
    embedding_path = args.output_dir / "semantic_embeddings.i16"
    embedding_path.write_bytes(embeddings_blob)
    semantic_rows = semantic_candidates(embeddings, torch)
    lexical_rows = lexical_candidates(clauses)
    rotated_rows = rotated_candidates(semantic_rows)
    retrieval_rows = {
        "LEX": lexical_rows,
        "SEM": semantic_rows,
        "ROT": rotated_rows,
    }
    retrieval_blobs = {
        name: serialize_candidates(rows) for name, rows in retrieval_rows.items()
    }
    for name, blob in retrieval_blobs.items():
        (args.output_dir / f"{name.lower()}_candidates.bin").write_bytes(blob)

    all_p1 = read_p1(args.joint_p1)
    if len(all_p1) != trace_decision["artifact"]["rows"]:
        raise ValueError("joint P1 row count differs from its certificate")
    probabilities = np.asarray(all_p1[:FROZEN_ROWS], dtype=np.uint16)
    if np.any(probabilities == 0):
        raise ValueError("joint prefix contains a zero probability")
    parent_payload = candidate.range_encode(wrt, probabilities)
    parent_total = CMIX_HEADER_BYTES + len(parent_payload)
    parent_decoder = candidate.RangeDecoder(parent_payload)
    parent_truth = np.unpackbits(np.frombuffer(wrt, dtype=np.uint8), bitorder="big")
    decoded_parent = np.fromiter(
        (parent_decoder.decode(value) for value in probabilities),
        dtype=np.uint8,
        count=len(probabilities),
    )
    if not np.array_equal(decoded_parent, parent_truth):
        raise ValueError("joint prefix arithmetic parent does not decode exactly")

    costs = qbit_costs(probabilities, wrt)
    chosen, pair_evaluations = choose_plans(
        clauses, retrieval_rows, wrt, costs
    )
    variants: dict[str, dict[str, Any]] = {}
    decoded_semantic = wrt
    for name in ("LEX", "SEM", "ROT"):
        receipt, decoded = build_variant(
            name,
            chosen[name],
            wrt,
            probabilities,
            parent_total,
            args.output_dir / f"{name.lower()}.archive",
        )
        variants[name] = receipt
        if name == "SEM":
            decoded_semantic = decoded

    split_receipts: dict[str, dict[str, Any]] = {}
    for split in ("development", "selection", "sealed_confirmation"):
        rows = [
            row for row in chosen["SEM"] if clauses[row.target_index].split == split
        ]
        split_receipts[split], _decoded = build_variant(
            f"SEM_{split}", rows, wrt, probabilities, parent_total, None
        )

    reconstructed_store = (
        full_store[:5] + decoded_semantic + full_store[5 + wrt_bytes :]
    )
    if reconstructed_store != full_store:
        raise ValueError("semantic prefix replacement differs from the canonical WRT store")
    reconstructed_path = args.output_dir / "semantic_reconstructed_full.wrt"
    restored_path = args.output_dir / "semantic_reconstructed_full.raw"
    reconstructed_path.write_bytes(reconstructed_store)
    with (args.output_dir / "inverse.stdout.log").open("wb") as stdout, (
        args.output_dir / "inverse.stderr.log"
    ).open("wb") as stderr:
        inverse = subprocess.run(
            [
                str(args.backend),
                "-d",
                str(args.dictionary),
                str(reconstructed_path),
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
        raise ValueError("official inverse of the reconstructed full store failed")

    required_gain = math.ceil(raw_bytes * GROSS_GATE_BPM / 1_000_000.0)
    gross_bpm = variants["SEM"]["gain_bytes"] * 1_000_000.0 / raw_bytes
    exact_conditions = {
        "joint_antecedent_exact": True,
        "joint_prefix_arithmetic_decode": True,
        "probabilities_legal_nonzero": True,
        "real_rocm_matrix_product": bool(runtime["matrix_output_sha256"]),
        "embedding_repeat_identity": runtime["embedding_repeat_identity"],
        "all_sources_strictly_prior": all(
            variants[name]["all_sources_strictly_prior"] for name in variants
        ),
        "all_command_roundtrips": all(
            variants[name]["command_roundtrip"] for name in variants
        ),
        "all_wrt_roundtrips": all(
            variants[name]["wrt_roundtrip"] for name in variants
        ),
        "all_second_archives_identical": all(
            variants[name]["second_archive_identity"] for name in variants
        ),
        "all_split_wrt_roundtrips": all(
            row["wrt_roundtrip"] for row in split_receipts.values()
        ),
        "all_split_archives_identical": all(
            row["second_archive_identity"] for row in split_receipts.values()
        ),
        "official_raw_inverse": raw_roundtrip,
    }
    economic_conditions = {
        "SEM_gross_at_least_3000_BPM": variants["SEM"]["gain_bytes"] >= required_gain,
        "development_gain_positive": split_receipts["development"]["gain_bytes"] > 0,
        "selection_gain_positive": split_receipts["selection"]["gain_bytes"] > 0,
        "sealed_confirmation_gain_positive": split_receipts["sealed_confirmation"]["gain_bytes"] > 0,
        "SEM_beats_LEX": variants["SEM"]["archive_bytes"] < variants["LEX"]["archive_bytes"],
        "SEM_beats_ROT": variants["SEM"]["archive_bytes"] < variants["ROT"]["archive_bytes"],
    }
    conditions = {**exact_conditions, **economic_conditions}
    failed = [name for name, passed in conditions.items() if not passed]
    authorized = not failed
    verdict = "AUTHORIZED_CANONICAL_10M" if authorized else "REJECT"

    source_blob = zlib.compress(
        Path(__file__).read_bytes() + PROGRAM.read_bytes(), level=9
    )
    decision = {
        "schema": "gamma.mobius2_logos_semantic_sentence_edit_bypass_qh0.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "claim_boundary": (
            "Exact opening-prefix representation ceiling with encoder-side semantic "
            "search supplied free. Decoder-visible commands, framing, and residual "
            "arithmetic are paid. The reconstructed prefix is inserted into the "
            "receipt-bound full store only for the official inverse. No native state "
            "hash, package, larger replay, forecast credit, or full-1G score is claimed."
        ),
        "inputs": {
            **inputs,
            "candidate_program": observed_artifact(PROGRAM),
            "plan": observed_artifact(PLAN),
            "decision_schema": observed_artifact(SCHEMA),
            "tool": observed_artifact(Path(__file__).resolve()),
            "embedding_model_snapshot": {
                "path": str(MODEL_SNAPSHOT),
                "manifest_sha256": manifest_sha,
                "files": manifest_rows,
            },
            "clause_texts_sha256": sha256_bytes(text_blob),
        },
        "runtime": runtime,
        "population": {
            "complete_pages": len(pages),
            "raw_equivalent_bytes": raw_bytes,
            "wrt_bytes": wrt_bytes,
            "p1_rows": len(probabilities),
            "emission_groups": len(groups),
            "sentence_segments_scanned": scanned,
            "eligible_sentence_spans": len(clauses),
            "page_splits": {
                split: sum(page.split == split for page in pages)
                for split in ("development", "selection", "sealed_confirmation")
            },
            "sentence_splits": {
                split: sum(row.split == split for row in clauses)
                for split in ("development", "selection", "sealed_confirmation")
            },
        },
        "format": {
            "minimum_groups": MIN_GROUPS,
            "maximum_groups": MAX_GROUPS,
            "minimum_raw_bytes": MIN_RAW_BYTES,
            "maximum_raw_bytes": MAX_RAW_BYTES,
            "minimum_ascii_letters": MIN_ASCII_LETTERS,
            "minimum_copy_bytes": MIN_COPY_BYTES,
            "neighbors_per_target": NEIGHBORS,
            "rotated_control_lag": ROTATION_LAG,
            "command_integer_code": "canonical ULEB128 plus little-endian u32 counts",
            "archive_frame_bytes": candidate.BYPASS_HEADER.size,
            "parent_frame_bytes": CMIX_HEADER_BYTES,
            "range_coder_precision_bits": 32,
            "one_prototype_per_target": True,
        },
        "retrieval": {
            "semantic": {
                "prompt": EMBEDDING_PROMPT,
                "maximum_tokens": EMBEDDING_MAX_TOKENS,
                "pooling": "attention-mask mean",
                "projection": "shipped 768->3072->768 dense modules",
                "mrl_dimension": EMBEDDING_DIMENSION,
                "quantization": "round-to-nearest signed int16",
                "candidate_blob_sha256": sha256_bytes(retrieval_blobs["SEM"]),
            },
            "lexical": {
                "signature": "lowercase word-set Jaccard excluding words present in more than 20 percent of spans",
                "candidate_blob_sha256": sha256_bytes(retrieval_blobs["LEX"]),
            },
            "rotated": {
                "construction": "semantic candidate identities shifted by causal lag 31 and filled by nearest prior spans",
                "candidate_blob_sha256": sha256_bytes(retrieval_blobs["ROT"]),
            },
            "pair_evaluations": pair_evaluations,
        },
        "parent": {
            "prefix_payload_bytes": len(parent_payload),
            "prefix_payload_sha256": sha256_bytes(parent_payload),
            "prefix_total_bytes": parent_total,
            "full_joint_payload_artifact_only": inputs["joint_payload"],
        },
        "variants": variants,
        "splits": split_receipts,
        "source_accounting": {
            "compressed_tool_plus_candidate_bytes": len(source_blob),
            "charged_at_qh0": False,
            "embedding_model_decoder_bytes": 0,
            "reason": "semantic model is encoder-side search only; selected decoder program is already paid in each archive",
        },
        "economics": {
            "required_gross_gain_bytes": required_gain,
            "required_gross_gain_bytes_per_million": GROSS_GATE_BPM,
            "SEM_gross_gain_bytes": variants["SEM"]["gain_bytes"],
            "SEM_gross_gain_bytes_per_million": gross_bpm,
            "forecast_bytes_unchanged": 109_389_323,
            "remaining_target_debt_bytes": 1_389_323,
        },
        "proof": {
            "conditions": exact_conditions,
            "reconstructed_prefix_sha256": sha256_bytes(decoded_semantic),
            "reconstructed_prefix_equals_parent": decoded_semantic == wrt,
            "reconstructed_full_store_equals_parent": reconstructed_store == full_store,
            "official_inverse_returncode": inverse.returncode,
            "official_raw_sha256": sha256_file(restored_path),
            "native_predictor_state_hash_proved": False,
        },
        "gates": {
            "conditions": conditions,
            "failed_conditions": failed,
        },
        "decision": {
            "verdict": verdict,
            "promotion_authorized": authorized,
            "forecast_bytes": 109_389_323,
            "score_credit_bytes": 0,
            "next_action": (
                "run one canonical 10M replay with the frozen semantic retrieval and edit format"
                if authorized
                else "retire this exact semantic sentence edit-bypass realization without retrieval or copy-parameter sweeps"
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
                "eligible_sentence_spans": len(clauses),
                "SEM_gain_bytes": variants["SEM"]["gain_bytes"],
                "SEM_gain_BPM": gross_bpm,
                "LEX_gain_bytes": variants["LEX"]["gain_bytes"],
                "ROT_gain_bytes": variants["ROT"]["gain_bytes"],
                "failed_conditions": failed,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
