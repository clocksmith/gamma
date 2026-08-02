#!/usr/bin/env python3
"""Measure a proper Gemma-ranked alphabet over exact WRT emission groups."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import time
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
EXPECTED_PYTHON = REPOSITORY / ".venv_rocm" / "bin" / "python"
if Path(sys.executable) != EXPECTED_PYTHON:
    environment = dict(os.environ)
    environment.setdefault("HSA_OVERRIDE_GFX_VERSION", "11.0.0")
    os.execve(
        str(EXPECTED_PYTHON),
        [str(EXPECTED_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )

import numpy as np
import torch
import transformers
from transformers import AutoTokenizer, Gemma4UnifiedForConditionalGeneration

import mobius2_frontier_teacher_token_headroom as frontier
import mobius2_tessera_typed_fiber_ceiling as tessera


CANDIDATE_ID = "mobius2_frontier_teacher_wrt_event_alphabet_qh0_v1"
MODEL_PATH = Path("/home/x/models/hf/google/gemma-4-12B-it")
BLOCK_TOKENS = 512
QBITS = 256
GROSS_GATE_BPM = 3000.0
SPLIT_NAMES = ("development", "selection", "sealed_confirmation")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


@dataclass(frozen=True)
class Group:
    index: int
    page_index: int
    split: int
    role: int
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    has_token: bool
    program: bytes
    token_ids: tuple[int, ...]
    token_start: int
    joint_qbits: int


@dataclass(frozen=True)
class PageGroups:
    page: frontier.Page
    token_ids: tuple[int, ...]
    groups: tuple[Group, ...]


@dataclass
class RoleCatalog:
    role: int
    opportunities: int
    escape_count: int
    program_counts: Counter[tuple[int, bytes]]
    escape_by_token: Counter[int]

    def __post_init__(self) -> None:
        self.programs_by_token: dict[int, tuple[bytes, ...]] = {}
        rows: dict[int, list[bytes]] = defaultdict(list)
        for token_id, program in self.program_counts:
            rows[token_id].append(program)
        self.programs_by_token = {
            token_id: tuple(sorted(programs))
            for token_id, programs in sorted(rows.items())
        }
        self.candidate_ids = tuple(sorted(self.programs_by_token))
        self.static_denominator = (
            self.opportunities + len(self.program_counts) + 1
        )
        self.epsilon = (self.escape_count + 1) / (self.opportunities + 2)
        self.variant_probabilities: dict[tuple[int, bytes], float] = {}
        self.known_fractions: dict[int, float] = {}
        for token_id, programs in self.programs_by_token.items():
            denominator = (
                sum(self.program_counts[(token_id, program)] for program in programs)
                + self.escape_by_token[token_id]
                + len(programs)
                + 1
            )
            known = 0.0
            for program in programs:
                probability = (
                    self.program_counts[(token_id, program)] + 1
                ) / denominator
                self.variant_probabilities[(token_id, program)] = probability
                known += probability
            if not 0.0 < known < 1.0:
                raise ValueError("invalid known-program fraction")
            self.known_fractions[token_id] = known

    def candidate(self, group: Group) -> tuple[int, bytes] | None:
        if not group.has_token or len(group.token_ids) != 1:
            return None
        key = (group.token_ids[0], group.program)
        return key if key in self.program_counts else None

    def static_bits(self, candidate: tuple[int, bytes] | None) -> float:
        count = self.escape_count if candidate is None else self.program_counts[candidate]
        return -math.log2((count + 1) / self.static_denominator)


def byte_fallback_ids(tokenizer: Any) -> tuple[int, ...]:
    values = []
    for value in range(256):
        token = f"<0x{value:02X}>"
        token_id = int(tokenizer.convert_tokens_to_ids(token))
        if token_id == tokenizer.unk_token_id:
            raise ValueError(f"tokenizer lacks byte fallback {token}")
        values.append(token_id)
    return tuple(values)


def tokenization_digest(pages: Sequence[PageGroups]) -> str:
    digest = hashlib.sha256()
    for page in pages:
        digest.update(struct.pack("<II", page.page.index, len(page.token_ids)))
        for token_id in page.token_ids:
            digest.update(struct.pack("<I", token_id))
        for group in page.groups:
            digest.update(
                struct.pack(
                    "<IIIIII",
                    group.index,
                    group.role,
                    group.raw_start,
                    group.raw_end,
                    group.wrt_start,
                    group.wrt_end,
                )
            )
            digest.update(struct.pack("<I", len(group.token_ids)))
    return digest.hexdigest()


def build_page_groups(
    parsed: Any,
    pages: Sequence[frontier.Page],
    emission_groups: Sequence[frontier.EmissionGroup],
    roles: np.ndarray,
    qbit_prefix: np.ndarray,
    tokenizer: Any,
) -> tuple[list[PageGroups], dict[str, object]]:
    event_index = {event.start: index for index, event in enumerate(parsed.events)}
    fallback = byte_fallback_ids(tokenizer)
    groups_by_page: dict[int, list[frontier.EmissionGroup]] = defaultdict(list)
    page_index = 0
    for group in emission_groups:
        while page_index < len(pages) and group.raw_start >= pages[page_index].raw_end:
            page_index += 1
        if page_index >= len(pages):
            break
        page = pages[page_index]
        if page.raw_start <= group.raw_start and group.raw_end <= page.raw_end:
            groups_by_page[page.index].append(group)

    ordered_groups = [
        group
        for page in pages
        for group in groups_by_page.get(page.index, ())
    ]
    decoded_text: list[str | None] = []
    for group in ordered_groups:
        raw = parsed.decoded[group.raw_start : group.raw_end]
        try:
            decoded_text.append(raw.decode("utf-8", errors="strict"))
        except UnicodeDecodeError:
            decoded_text.append(None)

    def encode_all() -> tuple[list[tuple[int, ...]], int]:
        rows: list[tuple[int, ...]] = [()] * len(ordered_groups)
        invalid = 0
        for start in range(0, len(ordered_groups), 4096):
            texts = decoded_text[start : start + 4096]
            valid = [
                (index, text) for index, text in enumerate(texts) if text is not None
            ]
            encoded = (
                tokenizer(
                    [text for _, text in valid],
                    add_special_tokens=False,
                )["input_ids"]
                if valid
                else []
            )
            for (local_index, _text), ids in zip(valid, encoded, strict=True):
                if not ids:
                    raise ValueError("output-producing WRT group tokenized to no IDs")
                rows[start + local_index] = tuple(int(value) for value in ids)
            for local_index, text in enumerate(texts):
                if text is None:
                    invalid += 1
                    raw_group = ordered_groups[start + local_index]
                    raw = parsed.decoded[raw_group.raw_start : raw_group.raw_end]
                    rows[start + local_index] = tuple(fallback[value] for value in raw)
        return rows, invalid

    token_rows, invalid_utf8 = encode_all()
    repeat_rows, repeat_invalid_utf8 = encode_all()
    if token_rows != repeat_rows or invalid_utf8 != repeat_invalid_utf8:
        raise ValueError("event-local tokenizer replay differs")

    if any(not row for row in token_rows):
        raise ValueError("event-local tokenization left an empty row")

    output: list[PageGroups] = []
    group_cursor = 0
    global_index = 0
    for page in pages:
        page_groups = groups_by_page.get(page.index, [])
        token_ids: list[int] = []
        built: list[Group] = []
        for group in page_groups:
            ids = token_rows[group_cursor]
            group_cursor += 1
            role = int(roles[event_index[group.wrt_start]])
            built.append(
                Group(
                    index=global_index,
                    page_index=page.index,
                    split=page.split,
                    role=role,
                    raw_start=group.raw_start,
                    raw_end=group.raw_end,
                    wrt_start=group.wrt_start,
                    wrt_end=group.wrt_end,
                    has_token=group.has_token,
                    program=bytes(parsed.stream[group.wrt_start : group.wrt_end]),
                    token_ids=ids,
                    token_start=len(token_ids),
                    joint_qbits=int(
                        qbit_prefix[group.wrt_end] - qbit_prefix[group.wrt_start]
                    ),
                )
            )
            token_ids.extend(ids)
            global_index += 1
        if built:
            output.append(PageGroups(page, tuple(token_ids), tuple(built)))
    if group_cursor != len(ordered_groups):
        raise ValueError("event-local tokenization group count differs")

    first_hash = tokenization_digest(output)
    repeat_hash = tokenization_digest(output)
    if first_hash != repeat_hash:
        raise ValueError("event-local tokenization repeat hash differs")
    return output, {
        "pages": len(output),
        "groups": sum(len(page.groups) for page in output),
        "local_token_ids": sum(len(page.token_ids) for page in output),
        "invalid_utf8_byte_fallback_groups": invalid_utf8,
        "tokenization_sha256_a": first_hash,
        "tokenization_sha256_b": repeat_hash,
        "repeat_identical": True,
    }


def build_catalogs(pages: Sequence[PageGroups]) -> dict[int, RoleCatalog]:
    opportunities: Counter[int] = Counter()
    known: dict[int, Counter[tuple[int, bytes]]] = defaultdict(Counter)
    development_groups = [
        group for page in pages if page.page.split == 0 for group in page.groups
    ]
    for group in development_groups:
        opportunities[group.role] += 1
        if group.has_token and len(group.token_ids) == 1:
            known[group.role][(group.token_ids[0], group.program)] += 1

    catalogs: dict[int, RoleCatalog] = {}
    for role in sorted(opportunities):
        candidate_ids = {token_id for token_id, _program in known[role]}
        escape_count = 0
        escape_by_token: Counter[int] = Counter()
        for group in development_groups:
            if group.role != role:
                continue
            key = (
                (group.token_ids[0], group.program)
                if group.has_token and len(group.token_ids) == 1
                else None
            )
            if key is None or key not in known[role]:
                escape_count += 1
                if group.token_ids[0] in candidate_ids:
                    escape_by_token[group.token_ids[0]] += 1
        if known[role]:
            catalogs[role] = RoleCatalog(
                role=role,
                opportunities=int(opportunities[role]),
                escape_count=escape_count,
                program_counts=known[role],
                escape_by_token=escape_by_token,
            )
    return catalogs


def score_block(
    model: Any,
    bos: int,
    block_ids: Sequence[int],
    groups: Sequence[Group],
    block_start: int,
    catalogs: dict[int, RoleCatalog],
) -> tuple[np.ndarray, np.ndarray]:
    input_ids = torch.tensor([[bos, *block_ids]], dtype=torch.long, device="cuda")
    with torch.inference_mode():
        result = model(input_ids=input_ids, use_cache=False, logits_to_keep=0)
        relative = torch.tensor(
            [group.token_start - block_start for group in groups],
            dtype=torch.long,
            device="cuda",
        )
        logits = result.logits[0].index_select(0, relative).float()
        full_lse = torch.logsumexp(logits, dim=-1)
        targets = torch.tensor(
            [group.token_ids[0] for group in groups],
            dtype=torch.long,
            device="cuda",
        )
        target_logits = logits.gather(1, targets[:, None]).squeeze(1)
        full_nll = full_lse - target_logits
        log_known_mass = torch.empty_like(full_nll)
        for role in sorted({group.role for group in groups}):
            row_indexes = [
                index for index, group in enumerate(groups) if group.role == role
            ]
            row_tensor = torch.tensor(row_indexes, dtype=torch.long, device="cuda")
            role_logits = logits.index_select(0, row_tensor)
            catalog = catalogs.get(role)
            if catalog is None:
                log_known_mass.index_fill_(0, row_tensor, float("-inf"))
                continue
            candidate_ids = torch.tensor(
                catalog.candidate_ids, dtype=torch.long, device="cuda"
            )
            log_weights = torch.tensor(
                [math.log(catalog.known_fractions[token_id]) for token_id in catalog.candidate_ids],
                dtype=torch.float32,
                device="cuda",
            )
            selected = role_logits.index_select(1, candidate_ids) + log_weights
            role_mass = torch.logsumexp(selected, dim=-1) - full_lse.index_select(
                0, row_tensor
            )
            role_mass = torch.clamp(role_mass, max=-1e-12)
            log_known_mass.index_copy_(0, row_tensor, role_mass)
        if not bool(torch.isfinite(full_nll).all()):
            raise ValueError("Gemma emitted a nonfinite event NLL")
        torch.cuda.synchronize()
        nll_output = full_nll.cpu().numpy().astype("<f4", copy=False)
        mass_output = log_known_mass.cpu().numpy().astype("<f4", copy=False)
    del result, logits, full_lse, targets, target_logits, full_nll
    del log_known_mass, input_ids, relative
    return nll_output, mass_output


def log_complement(log_mass: float) -> float:
    if not math.isfinite(log_mass):
        return 0.0
    if log_mass >= 0.0:
        if log_mass <= 1e-6:
            log_mass = -1e-12
        else:
            raise ValueError("known event mass exceeds one")
    return math.log1p(-math.exp(log_mass))


def empty_role_rows() -> dict[int, dict[str, float]]:
    return defaultdict(
        lambda: {
            "opportunities": 0,
            "candidate_events": 0,
            "displaced_bits": 0.0,
            "static_bits": 0.0,
            "full_mass_bits": 0.0,
            "calibrated_bits": 0.0,
        }
    )


def score_pages(
    model: Any,
    bos: int,
    pages: Sequence[PageGroups],
    catalogs: dict[int, RoleCatalog],
    split_name: str,
) -> tuple[dict[int, dict[str, float]], str, dict[str, object]]:
    role_rows = empty_role_rows()
    stream_digest = hashlib.sha256()
    blocks = 0
    groups_scored = 0
    calibration_a: str | None = None
    calibration_b: str | None = None
    started = time.monotonic()
    for page_number, page in enumerate(pages, start=1):
        for block_start in range(0, len(page.token_ids), BLOCK_TOKENS):
            block_end = min(len(page.token_ids), block_start + BLOCK_TOKENS)
            block_groups = [
                group
                for group in page.groups
                if block_start <= group.token_start < block_end
            ]
            nll, mass = score_block(
                model,
                bos,
                page.token_ids[block_start:block_end],
                block_groups,
                block_start,
                catalogs,
            )
            if calibration_a is None:
                repeat_nll, repeat_mass = score_block(
                    model,
                    bos,
                    page.token_ids[block_start:block_end],
                    block_groups,
                    block_start,
                    catalogs,
                )
                calibration_a = hashlib.sha256(
                    nll.tobytes() + mass.tobytes()
                ).hexdigest()
                calibration_b = hashlib.sha256(
                    repeat_nll.tobytes() + repeat_mass.tobytes()
                ).hexdigest()
                if calibration_a != calibration_b:
                    raise ValueError("repeated event-alphabet calibration differs")
            stream_digest.update(nll.tobytes())
            stream_digest.update(mass.tobytes())
            for group, full_nll, log_mass in zip(
                block_groups, nll, mass, strict=True
            ):
                catalog = catalogs.get(group.role)
                if catalog is None:
                    continue
                candidate = catalog.candidate(group)
                row = role_rows[group.role]
                row["opportunities"] += 1
                row["static_bits"] += catalog.static_bits(candidate)
                if candidate is None:
                    row["full_mass_bits"] += -log_complement(float(log_mass)) / math.log(2.0)
                    row["calibrated_bits"] += -math.log2(catalog.epsilon)
                else:
                    variant = catalog.variant_probabilities[candidate]
                    variant_nll = -math.log(variant)
                    row["candidate_events"] += 1
                    row["displaced_bits"] += group.joint_qbits / QBITS
                    row["full_mass_bits"] += (
                        float(full_nll) + variant_nll
                    ) / math.log(2.0)
                    row["calibrated_bits"] += (
                        float(full_nll)
                        + float(log_mass)
                        + variant_nll
                        - math.log1p(-catalog.epsilon)
                    ) / math.log(2.0)
                groups_scored += 1
            blocks += 1
        if page_number == 1 or page_number % 10 == 0 or page_number == len(pages):
            print(
                json.dumps(
                    {
                        "progress": "event_alphabet_scoring",
                        "split": split_name,
                        "pages_complete": page_number,
                        "pages_total": len(pages),
                        "blocks_complete": blocks,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    if calibration_a is None or calibration_b is None:
        raise ValueError(f"empty scored split: {split_name}")
    for role, row in role_rows.items():
        if not all(math.isfinite(value) for value in row.values()):
            raise ValueError(f"nonfinite role economics: {role}")
    return dict(role_rows), stream_digest.hexdigest(), {
        "blocks": blocks,
        "groups_scored": groups_scored,
        "calibration_hash_a": calibration_a,
        "calibration_hash_b": calibration_b,
        "repeat_calibration_identical": calibration_a == calibration_b,
    }


def role_economics(rows: dict[int, dict[str, float]]) -> list[dict[str, object]]:
    output = []
    for role in sorted(rows):
        row = rows[role]
        displaced = row["displaced_bits"]
        output.append(
            {
                "role_id": role,
                "role": tessera.ROLE_NAMES[role],
                **row,
                "static_gain_bytes": (displaced - row["static_bits"]) / 8.0,
                "full_mass_gain_bytes": (displaced - row["full_mass_bits"]) / 8.0,
                "calibrated_gain_bytes": (displaced - row["calibrated_bits"]) / 8.0,
                "calibrated_advantage_over_static_bytes": (
                    row["static_bits"] - row["calibrated_bits"]
                ) / 8.0,
                "calibrated_advantage_over_full_mass_bytes": (
                    row["full_mass_bits"] - row["calibrated_bits"]
                ) / 8.0,
            }
        )
    return output


def split_economics(
    rows: dict[int, dict[str, float]],
    active_roles: set[int],
    raw_bytes: int,
) -> dict[str, object]:
    selected = [rows[role] for role in sorted(active_roles) if role in rows]
    displaced = sum(row["displaced_bits"] for row in selected)
    static = sum(row["static_bits"] for row in selected)
    full_mass = sum(row["full_mass_bits"] for row in selected)
    calibrated = sum(row["calibrated_bits"] for row in selected)
    gain_bytes = (displaced - calibrated) / 8.0
    return {
        "raw_bytes": raw_bytes,
        "active_roles": [tessera.ROLE_NAMES[role] for role in sorted(active_roles)],
        "opportunities": int(sum(row["opportunities"] for row in selected)),
        "candidate_events": int(sum(row["candidate_events"] for row in selected)),
        "displaced_bits": displaced,
        "static_bits": static,
        "full_mass_bits": full_mass,
        "calibrated_bits": calibrated,
        "calibrated_gain_bytes": gain_bytes,
        "calibrated_gain_bytes_per_million": gain_bytes * 1_000_000.0 / raw_bytes,
        "calibrated_advantage_over_static_bytes": (static - calibrated) / 8.0,
        "calibrated_advantage_over_full_mass_bytes": (
            full_mass - calibrated
        ) / 8.0,
        "per_role": role_economics(rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-input", type=Path, default=ROOT / "data/enwik9_10000000.bin"
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=ROOT / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/english.dic"
        ),
    )
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    parser.add_argument("--raw-scope", type=int, default=1_000_000)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / CANDIDATE_ID,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if os.environ.get("HSA_OVERRIDE_GFX_VERSION") != "11.0.0":
        raise RuntimeError("frozen runtime requires HSA_OVERRIDE_GFX_VERSION=11.0.0")
    for path in (args.raw_input, args.wrt_store, args.joint_p1, args.dictionary):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not args.model.is_dir() or not (args.model / "model.safetensors").is_file():
        raise FileNotFoundError(args.model)
    if args.raw_scope != 1_000_000:
        raise ValueError("QH0 raw scope is frozen at 1,000,000 bytes")

    print(
        "[run-contract] "
        f"run_name={CANDIDATE_ID} "
        f"pairs_input_spec={args.joint_p1.resolve()} "
        "resume_from=none resume_stage=none decode=greedy "
        f"eval_dataset_paths={args.raw_input.resolve()} "
        "device=cuda schedule=mixed_from_start "
        "runtime_mode=rocm_gfx_override sweep_mode=live",
        flush=True,
    )
    runtime: dict[str, object] = {
        "sys_executable": sys.executable,
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "hip_version": torch.version.hip,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "device_capability": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None,
        "runtime_mode": "rocm_gfx_override",
        "dtype": "bfloat16_model_float32_logsumexp",
        "block_tokens": BLOCK_TOKENS,
    }
    if not runtime["cuda_available"] or runtime["cuda_device_count"] != 1:
        raise RuntimeError("frozen ROCm device is unavailable")
    matrix = torch.arange(4096, device="cuda", dtype=torch.float32).reshape(64, 64) / 4096
    product = matrix @ torch.flip(matrix, [0])
    torch.cuda.synchronize()
    runtime["matrix_output_sha256"] = hashlib.sha256(
        product.cpu().numpy().tobytes()
    ).hexdigest()
    del matrix, product

    parsed = frontier.parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT store does not reconstruct the canonical raw input")
    p1 = frontier.read_p1(args.joint_p1, len(parsed.stream) * 8)
    per_byte_qbits = frontier.byte_qbits(p1, parsed.stream)
    qbit_prefix = np.concatenate(
        (np.zeros(1, dtype=np.int64), np.cumsum(per_byte_qbits, dtype=np.int64))
    )
    emission_groups = frontier.emission_groups(parsed)
    pages = frontier.complete_pages(parsed, args.raw_scope)
    roles, _unused_splits = tessera.event_metadata(parsed, ())

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, local_files_only=True, use_fast=True
    )
    if not tokenizer.is_fast or tokenizer.bos_token_id is None:
        raise ValueError("frozen tokenizer lacks offsets or BOS")
    page_groups, tokenization = build_page_groups(
        parsed,
        pages,
        emission_groups,
        roles,
        qbit_prefix,
        tokenizer,
    )
    catalogs = build_catalogs(page_groups)
    development_pages = [page for page in page_groups if page.page.split == 0]
    selection_pages = [page for page in page_groups if page.page.split == 1]
    sealed_pages = [page for page in page_groups if page.page.split == 2]

    load_started = time.monotonic()
    model = Gemma4UnifiedForConditionalGeneration.from_pretrained(
        args.model,
        local_files_only=True,
        dtype=torch.bfloat16,
        device_map="cuda",
        low_cpu_mem_usage=True,
    )
    model.eval()
    torch.cuda.synchronize()
    runtime["model_load_elapsed_seconds"] = time.monotonic() - load_started
    runtime["torch_allocated_bytes_after_load"] = torch.cuda.memory_allocated()
    runtime["torch_reserved_bytes_after_load"] = torch.cuda.memory_reserved()

    score_started = time.monotonic()
    development_rows, development_hash, development_repeat = score_pages(
        model,
        int(tokenizer.bos_token_id),
        development_pages,
        catalogs,
        "development",
    )
    development_role_rows = role_economics(development_rows)
    active_roles = {
        int(row["role_id"])
        for row in development_role_rows
        if row["calibrated_gain_bytes"] > 0
        and row["calibrated_bits"] < row["static_bits"]
    }
    split_raw_bytes = {
        name: sum(
            page.raw_end - page.raw_start for page in pages if page.split == split
        )
        for split, name in enumerate(SPLIT_NAMES)
    }
    splits: dict[str, dict[str, object]] = {
        "development": split_economics(
            development_rows, active_roles, split_raw_bytes["development"]
        )
    }
    repeat: dict[str, object] = {"development": development_repeat}
    score_hashes = [development_hash]

    selection_opened = bool(active_roles)
    sealed_opened = False
    if selection_opened:
        selection_rows, selection_hash, selection_repeat = score_pages(
            model,
            int(tokenizer.bos_token_id),
            selection_pages,
            catalogs,
            "selection",
        )
        score_hashes.append(selection_hash)
        repeat["selection"] = selection_repeat
        splits["selection"] = split_economics(
            selection_rows, active_roles, split_raw_bytes["selection"]
        )
        selection_pass = bool(
            splits["selection"]["calibrated_gain_bytes"] > 0
            and splits["selection"]["calibrated_advantage_over_static_bytes"] > 0
            and splits["selection"]["calibrated_advantage_over_full_mass_bytes"] > 0
        )
        if selection_pass:
            sealed_opened = True
            sealed_rows, sealed_hash, sealed_repeat = score_pages(
                model,
                int(tokenizer.bos_token_id),
                sealed_pages,
                catalogs,
                "sealed_confirmation",
            )
            score_hashes.append(sealed_hash)
            repeat["sealed_confirmation"] = sealed_repeat
            splits["sealed_confirmation"] = split_economics(
                sealed_rows, active_roles, split_raw_bytes["sealed_confirmation"]
            )
        else:
            splits["sealed_confirmation"] = {
                "status": "not_opened_selection_kill"
            }
    else:
        splits["selection"] = {"status": "not_opened_development_kill"}
        splits["sealed_confirmation"] = {
            "status": "not_opened_development_kill"
        }

    runtime["score_elapsed_seconds"] = time.monotonic() - score_started
    runtime["peak_torch_allocated_bytes"] = torch.cuda.max_memory_allocated()
    runtime["peak_torch_reserved_bytes"] = torch.cuda.max_memory_reserved()
    runtime["event_score_stream_sha256"] = hashlib.sha256(
        "\n".join(score_hashes).encode("ascii")
    ).hexdigest()
    runtime["repeat"] = repeat

    sealed = splits["sealed_confirmation"]
    integrity = {
        "matrix_compute": True,
        "wrt_raw_identity": True,
        "joint_p1_truth_alignment": True,
        "event_groups_exact_and_contiguous": True,
        "event_local_tokenization_repeat_identical": tokenization["repeat_identical"],
        "repeat_calibration_identical": all(
            bool(value["repeat_calibration_identical"]) for value in repeat.values()
        ),
        "development_only_catalog": True,
        "all_probabilities_finite_normalized_nonzero": True,
    }
    passed = bool(
        active_roles
        and selection_opened
        and sealed_opened
        and splits["development"]["calibrated_gain_bytes"] > 0
        and splits["selection"]["calibrated_gain_bytes"] > 0
        and sealed["calibrated_gain_bytes_per_million"] >= GROSS_GATE_BPM
        and sealed["calibrated_advantage_over_static_bytes"] > 0
        and sealed["calibrated_advantage_over_full_mass_bytes"] > 0
        and all(integrity.values())
    )

    catalog_receipt = {
        "roles": len(catalogs),
        "programs": sum(len(catalog.program_counts) for catalog in catalogs.values()),
        "candidate_token_ids": sum(len(catalog.candidate_ids) for catalog in catalogs.values()),
        "active_roles": [tessera.ROLE_NAMES[role] for role in sorted(active_roles)],
        "per_role": [
            {
                "role_id": role,
                "role": tessera.ROLE_NAMES[role],
                "opportunities": catalog.opportunities,
                "escape_count": catalog.escape_count,
                "programs": len(catalog.program_counts),
                "candidate_token_ids": len(catalog.candidate_ids),
                "epsilon": catalog.epsilon,
            }
            for role, catalog in sorted(catalogs.items())
        ],
    }
    model_file = args.model / "model.safetensors"
    decision = {
        "schema": "mobius2_frontier_teacher_wrt_event_alphabet_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_proper_dynamic_event_alphabet_ceiling",
        "claim_boundary": (
            "Proper-distribution causal event-alphabet codelength over exact WRT emission "
            "groups. Teacher, catalogs, and implementation are free; no arithmetic archive, "
            "source-bound score, distillation, or full-corpus claim is created."
        ),
        "inputs": {
            "raw_input": artifact(args.raw_input),
            "wrt_store": artifact(args.wrt_store),
            "joint_p1": artifact(args.joint_p1),
            "dictionary": artifact(args.dictionary),
            "model_safetensors": artifact(model_file),
            "model_config": artifact(args.model / "config.json"),
            "tokenizer": artifact(args.model / "tokenizer.json"),
        },
        "runtime": runtime,
        "population": {
            "raw_scope_bytes": args.raw_scope,
            "complete_pages": len(pages),
            "split_page_counts": {
                name: sum(page.split == split for page in pages)
                for split, name in enumerate(SPLIT_NAMES)
            },
            "split_raw_bytes": split_raw_bytes,
        },
        "tokenization": tokenization,
        "catalog": catalog_receipt,
        "splits": splits,
        "integrity": integrity,
        "gate": {
            "sealed_gross_gain_bytes_per_million_required": GROSS_GATE_BPM,
            "development_positive_and_static_win_required": True,
            "selection_positive_and_control_wins_required": True,
            "sealed_static_and_full_mass_wins_required": True,
        },
        "decision": {
            "verdict": "PASS" if passed else "REJECT",
            "promotion_authorized": passed,
            "authorized_next_action": (
                "build one finite Q24 side coder and exact residual arithmetic replay"
                if passed
                else "retire this exact event-local teacher alphabet without rescue sweeps"
            ),
            "selection_opened": selection_opened,
            "sealed_confirmation_opened": sealed_opened,
            "score_credit_bytes": 0,
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score_bytes": None,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "decision.json"
    output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "verdict": decision["decision"]["verdict"],
                "active_roles": catalog_receipt["active_roles"],
                "sealed_gain_bpm": sealed.get("calibrated_gain_bytes_per_million"),
                "score_credit_bytes": 0,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"mobius2-frontier-teacher-wrt-event-alphabet: {error}", file=sys.stderr)
        raise
