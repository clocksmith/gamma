#!/usr/bin/env python3
"""Measure zero-credit Gemma lexical headroom over the exact joint trajectory."""

from __future__ import annotations

import argparse
from collections import Counter
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
from typing import Any, Sequence


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

from sibyl_page_prompt_oracle import page_intervals
from wrt_exact import ParsedStore, parse_store


CANDIDATE_ID = "mobius2_frontier_teacher_token_headroom_qh0_v1"
P1_MAGIC = b"CMX21P1\0"
QBITS = 256
BLOCK_TOKENS = 512
SPLIT_NAMES = ("development", "selection", "sealed_confirmation")
GROSS_GATE_BPM = 3000.0
MODEL_PATH = Path("/home/x/models/hf/google/gemma-4-12B-it")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path, *, include_sha256: bool = True) -> dict[str, object]:
    resolved = path.resolve()
    result: dict[str, object] = {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
    }
    if include_sha256:
        result["sha256"] = sha256_file(resolved)
    return result


def read_p1(path: Path, rows: int) -> np.memmap:
    with path.open("rb") as handle:
        header = handle.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError(f"invalid P1 trace: {path}")
    declared = struct.unpack_from("<Q", header, 8)[0]
    if declared != rows or path.stat().st_size != 16 + rows * 2:
        raise ValueError(f"P1 row binding failed: {path}")
    values = np.memmap(path, mode="r", dtype="<u2", offset=16, shape=(rows,))
    if np.any(values == 0):
        raise ValueError("joint P1 contains an illegal zero probability")
    return values


def byte_qbits(p1: np.ndarray, stream: bytes) -> np.ndarray:
    truth = np.unpackbits(np.frombuffer(stream, dtype=np.uint8), bitorder="big")
    if len(truth) != len(p1):
        raise ValueError("joint P1 and WRT truth rows differ")
    values = np.arange(65536, dtype=np.float64)
    values[0] = 1.0
    p_one = values / 65536.0
    zero = np.rint(-np.log2(1.0 - p_one) * QBITS).astype(np.int64)
    one = np.rint(-np.log2(p_one) * QBITS).astype(np.int64)
    output = np.empty(len(stream), dtype=np.int64)
    chunk_bytes = 1 << 17
    for byte_start in range(0, len(stream), chunk_bytes):
        byte_end = min(len(stream), byte_start + chunk_bytes)
        row_start = byte_start * 8
        row_end = byte_end * 8
        probabilities = np.asarray(p1[row_start:row_end], dtype=np.uint16)
        costs = np.where(truth[row_start:row_end] != 0, one[probabilities], zero[probabilities])
        output[byte_start:byte_end] = costs.reshape(-1, 8).sum(axis=1)
    return output


@dataclass(frozen=True)
class EmissionGroup:
    raw_start: int
    raw_end: int
    wrt_start: int
    wrt_end: int
    has_token: bool


def emission_groups(parsed: ParsedStore) -> list[EmissionGroup]:
    result: list[EmissionGroup] = []
    pending = []
    raw_cursor = 0
    for event in parsed.events:
        pending.append(event)
        if not event.decoded:
            continue
        decoded = b"".join(item.decoded for item in pending)
        result.append(
            EmissionGroup(
                raw_start=raw_cursor,
                raw_end=raw_cursor + len(decoded),
                wrt_start=pending[0].start,
                wrt_end=pending[-1].end,
                has_token=any(item.kind == "token" for item in pending),
            )
        )
        raw_cursor += len(decoded)
        pending.clear()
    if pending:
        raise ValueError("WRT stream ends with zero-output controls")
    if raw_cursor != len(parsed.decoded):
        raise ValueError("emission groups do not cover reconstructed raw bytes")
    for left, right in zip(result, result[1:]):
        if left.raw_end != right.raw_start or left.wrt_end != right.wrt_start:
            raise ValueError("emission groups are not contiguous")
    return result


@dataclass(frozen=True)
class Page:
    index: int
    raw_start: int
    raw_end: int
    split: int


@dataclass
class PageTokens:
    page: Page
    ids: list[int]
    eligible_events: list["TokenEvent"]


@dataclass(frozen=True)
class TokenEvent:
    token_start: int
    token_end: int
    qbits: int


def complete_pages(parsed: ParsedStore, raw_scope: int) -> list[Page]:
    eligible = [row for row in page_intervals(parsed) if row[1] <= raw_scope]
    development_end = len(eligible) * 3 // 5
    selection_end = len(eligible) * 4 // 5
    pages = []
    for index, (raw_start, raw_end, _row_start, _row_end) in enumerate(eligible):
        split = 0 if index < development_end else 1 if index < selection_end else 2
        pages.append(Page(index, raw_start, raw_end, split))
    if not pages or any(p.raw_start >= p.raw_end for p in pages):
        raise ValueError("no complete pages in declared raw scope")
    return pages


def char_to_byte_offsets(text: str) -> list[int]:
    offsets = [0]
    total = 0
    for character in text:
        total += len(character.encode("utf-8"))
        offsets.append(total)
    return offsets


def tokenize_pages(
    parsed: ParsedStore,
    pages: Sequence[Page],
    groups: Sequence[EmissionGroup],
    qbit_prefix: np.ndarray,
    tokenizer: Any,
) -> tuple[list[PageTokens], dict[str, int]]:
    group_by_start = {group.raw_start: index for index, group in enumerate(groups)}
    output: list[PageTokens] = []
    aligned = 0
    aligned_with_token = 0
    eligible_groups = 0
    normalized_events = 0
    for page in pages:
        raw_page = parsed.decoded[page.raw_start : page.raw_end]
        text = raw_page.decode("utf-8", errors="strict")
        encoded = tokenizer(
            text,
            add_special_tokens=False,
            return_offsets_mapping=True,
        )
        ids = [int(value) for value in encoded["input_ids"]]
        offsets = encoded["offset_mapping"]
        if not ids or len(ids) != len(offsets):
            raise ValueError(f"invalid tokenizer output on page {page.index}")
        reconstructed = tokenizer.decode(
            ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        ).encode("utf-8")
        if reconstructed != raw_page:
            raise ValueError(f"tokenizer roundtrip failed on page {page.index}")
        character_bytes = char_to_byte_offsets(text)
        token_events: list[tuple[int, int, int, int]] = []
        token_start = 0
        char_start, char_end = offsets[0]
        if not 0 <= char_start < char_end <= len(text):
            raise ValueError(f"invalid tokenizer offset on page {page.index}")
        for token_end, (next_start, next_end) in enumerate(offsets[1:], start=1):
            if not 0 <= next_start < next_end <= len(text):
                raise ValueError(f"invalid tokenizer offset on page {page.index}")
            if next_start < char_end:
                char_end = max(char_end, next_end)
                continue
            token_events.append((token_start, token_end, char_start, char_end))
            token_start = token_end
            char_start, char_end = next_start, next_end
        token_events.append((token_start, len(offsets), char_start, char_end))
        normalized_events += len(token_events)

        eligible_events: list[TokenEvent] = []
        previous_end = page.raw_start
        for token_start, token_end, char_start, char_end in token_events:
            raw_start = page.raw_start + character_bytes[char_start]
            raw_end = page.raw_start + character_bytes[char_end]
            if raw_start < previous_end:
                raise ValueError("overlapping normalized tokenizer events")
            previous_end = raw_end
            group_index = group_by_start.get(raw_start)
            if group_index is None:
                continue
            cursor = raw_start
            wrt_start = None
            wrt_end = None
            has_token = False
            covered = 0
            while group_index < len(groups) and cursor < raw_end:
                group = groups[group_index]
                if group.raw_start != cursor or group.raw_end > raw_end:
                    break
                wrt_start = group.wrt_start if wrt_start is None else wrt_start
                wrt_end = group.wrt_end
                has_token = has_token or group.has_token
                cursor = group.raw_end
                covered += 1
                group_index += 1
            if cursor != raw_end or wrt_start is None or wrt_end is None:
                continue
            aligned += 1
            if not has_token:
                continue
            aligned_with_token += 1
            eligible_groups += covered
            eligible_events.append(
                TokenEvent(
                    token_start=token_start,
                    token_end=token_end,
                    qbits=int(qbit_prefix[wrt_end] - qbit_prefix[wrt_start]),
                )
            )
        output.append(PageTokens(page=page, ids=ids, eligible_events=eligible_events))
    return output, {
        "tokenizer_tokens": sum(len(page.ids) for page in output),
        "normalized_tokenizer_events": normalized_events,
        "aligned_events": aligned,
        "eligible_events": aligned_with_token,
        "covered_wrt_emission_groups": eligible_groups,
    }


def score_block(model: Any, bos: int, block: Sequence[int]) -> np.ndarray:
    input_ids = torch.tensor([[bos, *block]], dtype=torch.long, device="cuda")
    with torch.inference_mode():
        result = model(input_ids=input_ids, use_cache=False, logits_to_keep=0)
        logits = result.logits[0, :-1].float()
        targets = input_ids[0, 1:]
        nll = torch.logsumexp(logits, dim=-1) - logits.gather(
            1, targets[:, None]
        ).squeeze(1)
        if not bool(torch.isfinite(nll).all()):
            raise ValueError("Gemma emitted an invalid NLL")
        torch.cuda.synchronize()
        output = nll.cpu().numpy().astype("<f4", copy=False)
    del result, logits, nll, input_ids, targets
    return output


def score_pages(model: Any, bos: int, pages: Sequence[PageTokens]) -> tuple[list[np.ndarray], str, dict[str, object]]:
    calibration_block = pages[0].ids[: min(BLOCK_TOKENS, len(pages[0].ids))]
    calibration_a = score_block(model, bos, calibration_block)
    calibration_b = score_block(model, bos, calibration_block)
    calibration_a_hash = hashlib.sha256(calibration_a.tobytes()).hexdigest()
    calibration_b_hash = hashlib.sha256(calibration_b.tobytes()).hexdigest()
    if calibration_a_hash != calibration_b_hash:
        raise ValueError("repeated calibration NLL hash differs")

    page_losses: list[np.ndarray] = []
    digest = hashlib.sha256()
    blocks = 0
    started = time.monotonic()
    for page_number, page in enumerate(pages, start=1):
        losses = np.empty(len(page.ids), dtype="<f4")
        for start in range(0, len(page.ids), BLOCK_TOKENS):
            end = min(len(page.ids), start + BLOCK_TOKENS)
            losses[start:end] = score_block(model, bos, page.ids[start:end])
            blocks += 1
        digest.update(losses.tobytes())
        page_losses.append(losses)
        if page_number == 1 or page_number % 10 == 0 or page_number == len(pages):
            print(
                json.dumps(
                    {
                        "progress": "teacher_scoring",
                        "pages_complete": page_number,
                        "pages_total": len(pages),
                        "blocks_complete": blocks,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    return page_losses, digest.hexdigest(), {
        "calibration_tokens": len(calibration_block),
        "calibration_hash_a": calibration_a_hash,
        "calibration_hash_b": calibration_b_hash,
        "repeat_calibration_identical": True,
        "scored_blocks": blocks,
    }


def unigram_model(
    pages: Sequence[PageTokens], vocab_size: int
) -> tuple[Counter[int], int, int]:
    development_counts: Counter[int] = Counter()
    development_tokens = 0
    for page in pages:
        if page.page.split == 0:
            development_counts.update(page.ids)
            development_tokens += len(page.ids)
    if development_tokens <= 0:
        raise ValueError("empty development token population")
    return development_counts, development_tokens, development_tokens + vocab_size

def one_split_economics(
    pages: Sequence[PageTokens],
    losses: Sequence[np.ndarray],
    development_counts: Counter[int],
    denominator: int,
) -> dict[str, object]:
    raw_bytes = 0
    eligible_tokens = 0
    joint_bits = 0.0
    gemma_bits = 0.0
    unigram_bits = 0.0
    positive_tokens = 0
    for page, page_losses in zip(pages, losses):
        raw_bytes += page.page.raw_end - page.page.raw_start
        for event in page.eligible_events:
            eligible_tokens += 1
            joint = event.qbits / QBITS
            gemma = float(
                np.sum(
                    page_losses[event.token_start : event.token_end],
                    dtype=np.float64,
                )
            ) / math.log(2.0)
            unigram = sum(
                -math.log2((development_counts[token_id] + 1) / denominator)
                for token_id in page.ids[event.token_start : event.token_end]
            )
            joint_bits += joint
            gemma_bits += gemma
            unigram_bits += unigram
            positive_tokens += int(gemma < joint)
    if raw_bytes <= 0 or eligible_tokens <= 0:
        raise ValueError("empty split economics population")
    gemma_gain_bytes = (joint_bits - gemma_bits) / 8.0
    unigram_gain_bytes = (joint_bits - unigram_bits) / 8.0
    return {
        "raw_bytes": raw_bytes,
        "eligible_tokens": eligible_tokens,
        "positive_gemma_tokens": positive_tokens,
        "joint_bits": joint_bits,
        "gemma_bits": gemma_bits,
        "unigram_bits": unigram_bits,
        "gemma_gain_bytes": gemma_gain_bytes,
        "gemma_gain_bytes_per_million": gemma_gain_bytes * 1_000_000.0 / raw_bytes,
        "unigram_gain_bytes": unigram_gain_bytes,
        "unigram_gain_bytes_per_million": unigram_gain_bytes * 1_000_000.0 / raw_bytes,
        "gemma_advantage_over_unigram_bytes": (unigram_bits - gemma_bits) / 8.0,
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
    runtime = {
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

    parsed = parse_store(args.wrt_store, args.dictionary)
    raw = args.raw_input.read_bytes()
    if parsed.decoded != raw:
        raise ValueError("WRT store does not reconstruct the canonical raw input")
    p1 = read_p1(args.joint_p1, len(parsed.stream) * 8)
    per_byte_qbits = byte_qbits(p1, parsed.stream)
    qbit_prefix = np.concatenate(
        (np.zeros(1, dtype=np.int64), np.cumsum(per_byte_qbits, dtype=np.int64))
    )
    groups = emission_groups(parsed)
    pages = complete_pages(parsed, args.raw_scope)

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, local_files_only=True, use_fast=True
    )
    if not tokenizer.is_fast or tokenizer.bos_token_id is None:
        raise ValueError("frozen tokenizer lacks offsets or BOS")
    development_page_specs = [page for page in pages if page.split == 0]
    later_page_specs = [page for page in pages if page.split != 0]
    development_pages, development_alignment = tokenize_pages(
        parsed, development_page_specs, groups, qbit_prefix, tokenizer
    )

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

    development_counts, _development_tokens, denominator = unigram_model(
        development_pages, int(tokenizer.vocab_size)
    )

    score_started = time.monotonic()
    development_losses, development_hash, development_repeat = score_pages(
        model, int(tokenizer.bos_token_id), development_pages
    )
    splits: dict[str, dict[str, object]] = {
        "development": one_split_economics(
            development_pages,
            development_losses,
            development_counts,
            denominator,
        )
    }
    development_positive = splits["development"]["gemma_gain_bytes"] > 0
    repeat: dict[str, object] = {"development": development_repeat}
    score_hashes = [development_hash]
    alignment: dict[str, object] = {"development": development_alignment}
    if development_positive:
        later_pages, later_alignment = tokenize_pages(
            parsed, later_page_specs, groups, qbit_prefix, tokenizer
        )
        alignment["selection_and_sealed"] = later_alignment
        later_losses, later_hash, later_repeat = score_pages(
            model, int(tokenizer.bos_token_id), later_pages
        )
        repeat["later_splits"] = later_repeat
        score_hashes.append(later_hash)
        for split, name in ((1, "selection"), (2, "sealed_confirmation")):
            selected_pages = [page for page in later_pages if page.page.split == split]
            selected_losses = [
                loss
                for page, loss in zip(later_pages, later_losses)
                if page.page.split == split
            ]
            splits[name] = one_split_economics(
                selected_pages,
                selected_losses,
                development_counts,
                denominator,
            )
    else:
        alignment["selection_and_sealed"] = {
            "status": "not_opened_development_kill"
        }
        splits["selection"] = {"status": "not_opened_development_kill"}
        splits["sealed_confirmation"] = {
            "status": "not_opened_development_kill"
        }

    runtime["score_elapsed_seconds"] = time.monotonic() - score_started
    runtime["peak_torch_allocated_bytes"] = torch.cuda.max_memory_allocated()
    runtime["peak_torch_reserved_bytes"] = torch.cuda.max_memory_reserved()
    runtime["nll_stream_sha256"] = hashlib.sha256(
        "\n".join(score_hashes).encode("ascii")
    ).hexdigest()
    runtime["repeat"] = repeat

    sealed = splits["sealed_confirmation"]
    integrity = {
        "matrix_compute": True,
        "wrt_raw_identity": True,
        "joint_p1_truth_alignment": True,
        "tokenizer_roundtrip_all_opened_pages": True,
        "eligible_spans_emission_group_exact": True,
        "repeat_calibration_identical": all(
            bool(value["repeat_calibration_identical"])
            for value in repeat.values()
        ),
        "all_model_nll_finite": True,
    }
    passed = bool(
        development_positive
        and splits["selection"]["gemma_gain_bytes"] > 0
        and sealed["gemma_gain_bytes_per_million"] >= GROSS_GATE_BPM
        and sealed["gemma_bits"] < sealed["unigram_bits"]
        and all(integrity.values())
    )

    model_file = args.model / "model.safetensors"
    decision = {
        "schema": "mobius2_frontier_teacher_token_headroom_decision_v1",
        "candidate_id": CANDIDATE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_level": "zero_credit_causal_frontier_teacher_headroom",
        "claim_boundary": (
            "Proper-distribution causal language-teacher codelength over exact aligned "
            "lexical events. The model and implementation are free; no archive, source-bound "
            "score, model distillation, or full-corpus claim is created."
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
            "split_raw_bytes": {
                name: sum(
                    page.raw_end - page.raw_start
                    for page in pages
                    if page.split == split
                )
                for split, name in enumerate(SPLIT_NAMES)
            },
        },
        "alignment": alignment,
        "splits": splits,
        "integrity": integrity,
        "gate": {
            "sealed_gross_gain_bytes_per_million_required": GROSS_GATE_BPM,
            "development_positive_required": True,
            "selection_positive_required": True,
            "gemma_beats_unigram_on_sealed_required": True,
        },
        "decision": {
            "verdict": "PASS" if passed else "REJECT",
            "promotion_authorized": passed,
            "authorized_next_action": (
                "attribute paying aligned tokens and freeze one deterministic compiled rule language"
                if passed
                else "retire this exact teacher checkpoint, alignment, and reset contract without sweeps"
            ),
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
                "sealed_gemma_gain_bpm": sealed.get("gemma_gain_bytes_per_million"),
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
        print(f"mobius2-frontier-teacher-token-headroom: {error}", file=sys.stderr)
        raise
