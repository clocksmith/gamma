#!/usr/bin/env python3
"""Run the frozen opening-1M NOEMA binary-carry hierarchy QH0 gate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
from typing import Any, Sequence
import zlib


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "mobius2_noema_binary_carry_headroom_qh0_v1"
PROPOSAL_ID = "mobius2_noema_binary_carry_headroom_v1"
CANDIDATE_PROGRAM = ROOT / "programs" / CANDIDATE_ID / "program.py"
PLAN_PATH = ROOT / "docs" / "mobius2_noema_binary_carry_headroom_plan.md"
SCHEMA_PATH = (
    ROOT / "docs" / "mobius2_noema_binary_carry_headroom_decision.schema.json"
)
ROCM_PYTHON = Path(
    "/home/x/enwiki9-nonproof/external/rocm-pytorch-venv/bin/python"
)
DEFAULT_P1 = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_online_native_1m_v1/native.p1"
)
DEFAULT_WRT = Path("/home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin")
DEFAULT_RAW = Path(
    "/home/x/enwiki9-nonproof/results/"
    "fx2_full_attribution_trace_1m_v1.restored"
)
DEFAULT_ARCHIVE = Path(
    "/home/x/enwiki9-nonproof/results/"
    "endpoint428_pair_layer0_online_native_1m_v1/archive.bin"
)
DEFAULT_DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/"
    "cmix21-lstm200-plus-fx2lite428-onlinepairlayer0-v17/english.dic"
)
DEFAULT_BACKEND = Path(
    "/home/x/enwiki9-nonproof/results/"
    "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
    "clean-build-b/build/cmix.bin"
)
DEFAULT_MANIFEST = ROOT / "results" / "endpoint_final_trace_1m_v1" / "manifest.json"
DEFAULT_NATIVE_RECEIPT = (
    ROOT / "results" / "endpoint428_pair_layer0_online_native_1m_v1" / "receipt.json"
)
DEFAULT_PAGE_MAP = ROOT / "results" / "endpoint_final_trace_1m_v1" / "page_map.bin"
P1_MAGIC = b"CMX21P1\0"
PAGE_MAP_MAGIC = b"SIBMAP1\0"
PAGE_MAP_RECORD = struct.Struct("<QQQQ")
SPLITS = ("development", "selection", "sealed_confirmation")
EPOCHS = 8
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
    split: str
    wrt_start: int
    wrt_end: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def bind_artifact(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    if path.stat().st_size != expected.get("bytes"):
        raise ValueError(f"{label} size differs from bound manifest")
    if sha256_file(path) != expected.get("sha256"):
        raise ValueError(f"{label} SHA-256 differs from bound manifest")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ensure_rocm() -> None:
    if os.environ.get("NOEMA_ROCM_REEXEC"):
        return
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    environment = os.environ.copy()
    environment["NOEMA_ROCM_REEXEC"] = "normal"
    environment["NOEMA_RUNTIME_MODE"] = "normal_rocm"
    environment["AMD_SERIALIZE_KERNEL"] = "3"
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def prove_gpu_compute(torch: Any) -> str:
    try:
        left = torch.arange(16, dtype=torch.float32, device="cuda").reshape(4, 4)
        right = torch.eye(4, dtype=torch.float32, device="cuda")
        result = (left @ right).cpu()
        if not torch.equal(result, torch.arange(16).reshape(4, 4).float()):
            raise RuntimeError("ROCm matmul result differs from exact identity product")
        torch.cuda.synchronize()
        return os.environ.get("NOEMA_RUNTIME_MODE", "normal_rocm")
    except RuntimeError as error:
        message = str(error)
        if (
            "invalid device function" in message
            and "HSA_OVERRIDE_GFX_VERSION" not in os.environ
        ):
            environment = os.environ.copy()
            environment["NOEMA_ROCM_REEXEC"] = "override"
            environment["NOEMA_RUNTIME_MODE"] = "rocm_gfx_override"
            environment["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
            environment["AMD_SERIALIZE_KERNEL"] = "3"
            os.execve(
                str(ROCM_PYTHON),
                [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
                environment,
            )
        raise


def read_p1(path: Path, expected_rows: int):
    import numpy as np

    with path.open("rb") as source:
        header = source.read(16)
    if len(header) != 16 or header[:8] != P1_MAGIC:
        raise ValueError("invalid CMIX P1 header")
    rows = struct.unpack_from("<Q", header, 8)[0]
    if rows != expected_rows or path.stat().st_size != 16 + rows * 2:
        raise ValueError("P1 rows differ from the exact WRT truth stream")
    return header, np.memmap(
        path, mode="r", dtype="<u2", offset=16, shape=(rows,)
    ).copy()


def parent_payload(archive: bytes, wrt_bytes: int) -> tuple[bytes, int]:
    if len(archive) < 5:
        raise ValueError("parent archive is truncated")
    declared = archive[0] & 0x7F
    for value in archive[1:5]:
        declared = (declared << 8) | value
    if declared != wrt_bytes:
        raise ValueError("parent archive declares a different WRT length")
    header_bytes = 5 if declared < 10_000 else 37
    if len(archive) <= header_bytes:
        raise ValueError("parent archive has no arithmetic payload")
    return archive[header_bytes:], header_bytes


def read_pages(path: Path, expected_sha256: str, wrt_bytes: int) -> list[Page]:
    if sha256_file(path) != expected_sha256:
        raise ValueError("page map differs from bound manifest")
    data = path.read_bytes()
    if len(data) < 16 or data[:8] != PAGE_MAP_MAGIC:
        raise ValueError("invalid page-map header")
    count = struct.unpack_from("<Q", data, 8)[0]
    if len(data) != 16 + count * PAGE_MAP_RECORD.size:
        raise ValueError("page-map length differs from declared records")
    development_end = count * 3 // 5
    selection_end = count * 4 // 5
    pages: list[Page] = []
    previous_raw_end = 0
    previous_wrt_end = 0
    for index in range(count):
        raw_start, raw_end, row_start, row_end = PAGE_MAP_RECORD.unpack_from(
            data, 16 + index * PAGE_MAP_RECORD.size
        )
        if row_start % 8 or row_end % 8:
            raise ValueError("page map is not WRT-byte aligned")
        split = (
            "development"
            if index < development_end
            else "selection"
            if index < selection_end
            else "sealed_confirmation"
        )
        page = Page(
            index=index,
            raw_start=raw_start,
            raw_end=raw_end,
            wrt_start=row_start // 8,
            wrt_end=row_end // 8,
            split=split,
        )
        if not 0 <= previous_raw_end <= raw_start < raw_end:
            raise ValueError("raw page intervals are not chronological")
        if not 0 <= previous_wrt_end <= page.wrt_start < page.wrt_end <= wrt_bytes:
            raise ValueError("WRT page intervals are invalid")
        pages.append(page)
        previous_raw_end = raw_end
        previous_wrt_end = page.wrt_end
    return pages


def range_encode(probabilities, truth_bits) -> bytes:
    output = bytearray()
    x1 = 0
    x2 = 0xFFFFFFFF
    for probability, truth in zip(probabilities, truth_bits):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if int(truth):
            x2 = midpoint
        else:
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            output.append((x2 >> 24) & 0xFF)
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    while ((x1 ^ x2) & 0xFF000000) == 0:
        output.append((x2 >> 24) & 0xFF)
        x1 = (x1 << 8) & 0xFFFFFFFF
        x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
    output.append((x2 >> 24) & 0xFF)
    return bytes(output)


def range_decode(payload: bytes, probabilities):
    import numpy as np

    if len(payload) < 4:
        raise ValueError("range payload is too short")
    cursor = 4
    code = int.from_bytes(payload[:4], "big")
    x1 = 0
    x2 = 0xFFFFFFFF
    truth = np.empty(len(probabilities), dtype=np.uint8)
    for index, probability in enumerate(probabilities):
        p1 = int(probability)
        delta = x2 - x1
        midpoint = x1 + (delta >> 16) * p1 + (
            (delta & 0xFFFF) * p1 >> 16
        )
        if code <= midpoint:
            truth[index] = 1
            x2 = midpoint
        else:
            truth[index] = 0
            x1 = midpoint + 1
        while ((x1 ^ x2) & 0xFF000000) == 0:
            x1 = (x1 << 8) & 0xFFFFFFFF
            x2 = ((x2 << 8) & 0xFFFFFFFF) + 255
            next_byte = payload[cursor] if cursor < len(payload) else 0
            cursor += 1
            code = ((code << 8) & 0xFFFFFFFF) + next_byte
    return truth


def probability_logits(probabilities):
    import numpy as np

    values = np.clip(probabilities.astype(np.float64), 1, 65535) / 65536.0
    return (np.log(values) - np.log1p(-values)).astype(np.float32)


def quantized_probabilities(base_logits, residuals):
    import numpy as np

    logits = np.clip(
        base_logits.astype(np.float64) + residuals.astype(np.float64),
        -20.0,
        20.0,
    )
    values = 65536.0 / (1.0 + np.exp(-logits))
    return np.clip(np.rint(values), 1, 65535).astype(np.uint16)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1", type=Path, default=DEFAULT_P1)
    parser.add_argument("--wrt-store", type=Path, default=DEFAULT_WRT)
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--parent-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--backend", type=Path, default=DEFAULT_BACKEND)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--native-receipt", type=Path, default=DEFAULT_NATIVE_RECEIPT)
    parser.add_argument("--page-map", type=Path, default=DEFAULT_PAGE_MAP)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_rocm()

    import numpy as np
    import torch
    from torch import nn

    if not torch.cuda.is_available():
        raise SystemExit("receipt-bound ROCm PyTorch has no visible GPU")
    runtime_mode = prove_gpu_compute(torch)
    print(f"python={Path(sys.executable).resolve()} torch={torch.__version__}")
    print(f"torch.cuda.is_available()={torch.cuda.is_available()}")
    print(f"torch.cuda.device_count()={torch.cuda.device_count()} DEVICE=cuda")
    print(f"gpu_compute_probe=pass runtime_mode={runtime_mode}")
    print(
        "[run-contract] "
        f"run_name={CANDIDATE_ID} pairs_input_spec={args.p1} "
        "resume_from=none resume_stage=none decode=greedy "
        "eval_dataset_paths=development,selection,sealed_confirmation "
        f"device=cuda schedule=development_then_selection runtime_mode={runtime_mode} "
        "sweep_mode=live",
        flush=True,
    )

    required = (
        args.p1,
        args.wrt_store,
        args.raw_input,
        args.parent_archive,
        args.dictionary,
        args.backend,
        args.manifest,
        args.native_receipt,
        args.page_map,
        CANDIDATE_PROGRAM,
        PLAN_PATH,
        SCHEMA_PATH,
    )
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing required artifact: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=False)

    candidate = load_module("mobius2_noema_binary_carry_candidate", CANDIDATE_PROGRAM)
    if candidate.PATCH_BYTES != 128 or candidate.LEVEL_COUNT != 7:
        raise ValueError("candidate constants differ from the frozen QH0 plan")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    bound = manifest.get("artifacts")
    if not isinstance(bound, dict):
        raise ValueError("trace manifest has no artifact bindings")
    for label, path in (
        ("p1_trace", args.p1),
        ("wrt_store", args.wrt_store),
        ("raw_input", args.raw_input),
        ("archive", args.parent_archive),
        ("dictionary", args.dictionary),
        ("page_map", args.page_map),
    ):
        expected = bound.get(label)
        if not isinstance(expected, dict):
            raise ValueError(f"trace manifest does not bind {label}")
        bind_artifact(path, expected, label)

    stored = args.wrt_store.read_bytes()
    if len(stored) <= 5 or stored[:5] != b"\x80\0\0\0\0":
        raise ValueError("invalid outer WRT store header")
    wrt = np.frombuffer(stored, dtype=np.uint8, offset=5).copy()
    raw = args.raw_input.read_bytes()
    wrt_exact = load_module("mobius2_noema_wrt_exact", ROOT / "tools" / "wrt_exact.py")
    parsed = wrt_exact.parse_store(args.wrt_store, args.dictionary)
    if parsed.stream != wrt.tobytes() or parsed.decoded != raw:
        raise ValueError("exact WRT parser does not reproduce the bound raw input")

    p1_header, p1 = read_p1(args.p1, len(wrt) * 8)
    all_truth = np.unpackbits(wrt, bitorder="big")
    archive = args.parent_archive.read_bytes()
    receipt_parent_payload, parent_header_bytes = parent_payload(archive, len(wrt))
    replay_parent_payload = range_encode(p1, all_truth)
    if replay_parent_payload != receipt_parent_payload:
        raise ValueError("N0 parent payload is not byte-identical")
    if not np.array_equal(range_decode(replay_parent_payload, p1), all_truth):
        raise ValueError("N0 parent arithmetic decode failed")

    pages = read_pages(args.page_map, bound["page_map"]["sha256"], len(wrt))
    patches: list[Patch] = []
    page_patch_ids: dict[int, list[int]] = {page.index: [] for page in pages}
    for page in pages:
        stop = page.wrt_start + (
            (page.wrt_end - page.wrt_start) // candidate.PATCH_BYTES
        ) * candidate.PATCH_BYTES
        for start in range(page.wrt_start, stop, candidate.PATCH_BYTES):
            patch = Patch(
                index=len(patches),
                page_index=page.index,
                split=page.split,
                wrt_start=start,
                wrt_end=start + candidate.PATCH_BYTES,
            )
            patches.append(patch)
            page_patch_ids[page.index].append(patch.index)
    if not patches or any(not page_patch_ids[page.index] for page in pages):
        raise ValueError("every complete page must contribute a modeled patch")

    patch_positions = np.asarray(
        [
            np.arange(patch.wrt_start, patch.wrt_end, dtype=np.int64)
            for patch in patches
        ]
    )
    patch_values = wrt[patch_positions]
    p1_by_byte = p1.reshape(len(wrt), 8)
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
    split_pages = {
        split: [page for page in pages if page.split == split] for split in SPLITS
    }
    split_raw_bytes = {
        split: sum(page.raw_end - page.raw_start for page in split_pages[split])
        for split in SPLITS
    }
    split_parent_payloads: dict[str, bytes] = {}
    for split in SPLITS:
        ids = split_patch_ids[split]
        split_parent_payloads[split] = range_encode(
            patch_parent_p1[ids].reshape(-1),
            patch_bits[ids].astype(np.uint8).reshape(-1),
        )

    device = torch.device("cuda")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    def reset_seeds() -> None:
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)

    def model_from_state(mode: str, state: dict[str, Any]):
        model = candidate.build_model(torch, mode)
        model.load_state_dict(state)
        return model.to(device)

    def infer(
        model: Any,
        ids: np.ndarray,
        *,
        include_states: bool = False,
    ):
        probabilities = np.empty(
            (len(ids), candidate.PATCH_BYTES, 8), dtype=np.uint16
        )
        state_output = (
            np.empty(
                (len(ids), candidate.PATCH_BYTES, candidate.SUMMARY_WIDTH),
                dtype=np.float32,
            )
            if include_states
            else None
        )
        model.eval()
        with torch.no_grad():
            for offset in range(0, len(ids), BATCH_SIZE):
                batch_ids = ids[offset : offset + BATCH_SIZE]
                values = torch.from_numpy(patch_values[batch_ids]).to(device)
                nodes = torch.from_numpy(patch_nodes[batch_ids]).to(device)
                if include_states:
                    residuals, states = model(values, return_states=True)
                    state_output[offset : offset + len(batch_ids)] = (
                        states.cpu().numpy().astype(np.float32)
                    )
                else:
                    residuals = model(values)
                selected = torch.gather(residuals, 2, nodes)
                host = selected.cpu().numpy().astype(np.float32)
                probabilities[offset : offset + len(batch_ids)] = (
                    quantized_probabilities(
                        patch_base_logits[batch_ids], host
                    )
                )
        return probabilities, state_output

    def selection_payload(model: Any) -> bytes:
        ids = split_patch_ids["selection"]
        probabilities, _states = infer(model, ids)
        return range_encode(
            probabilities.reshape(-1),
            patch_bits[ids].astype(np.uint8).reshape(-1),
        )

    def fit_once(mode: str, run_index: int) -> dict[str, Any]:
        reset_seeds()
        model = candidate.build_model(torch, mode).to(device)
        expected_parameters = candidate.expected_parameter_count()
        actual_parameters = candidate.parameter_count(model)
        if actual_parameters != expected_parameters:
            raise ValueError(
                f"{mode} parameter count {actual_parameters} != {expected_parameters}"
            )
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=LEARNING_RATE,
            weight_decay=WEIGHT_DECAY,
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
                values = torch.from_numpy(patch_values[ids]).to(device)
                nodes = torch.from_numpy(patch_nodes[ids]).to(device)
                base = torch.from_numpy(patch_base_logits[ids]).to(device)
                truth = torch.from_numpy(patch_bits[ids]).to(device)
                residuals = model(values)
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

            blob, dequantized = candidate.quantize_model(torch, model, mode)
            quantized_model = model_from_state(mode, dequantized)
            selected_payload = selection_payload(quantized_model)
            row = {
                "epoch": epoch,
                "development_nats_per_bit": weighted_loss / truth_count,
                "selection_parent_payload_bytes": len(
                    split_parent_payloads["selection"]
                ),
                "selection_candidate_payload_bytes": len(selected_payload),
                "selection_gain_bytes": len(
                    split_parent_payloads["selection"]
                )
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
            "parameter_count": actual_parameters,
        }

    def full_candidate_p1(patch_probabilities) -> Any:
        result = p1.copy()
        result_by_byte = result.reshape(len(wrt), 8)
        result_by_byte[patch_positions.reshape(-1)] = patch_probabilities.reshape(
            -1, 8
        )
        return result

    def complete_fit(mode: str) -> dict[str, Any]:
        run_a = fit_once(mode, 1)
        run_b = fit_once(mode, 2)
        model_a = model_from_state(mode, run_a["model_state"])
        model_b = model_from_state(mode, run_b["model_state"])
        all_ids = np.arange(len(patches), dtype=np.int64)
        probabilities_a, states_a = infer(
            model_a, all_ids, include_states=mode == "hierarchy"
        )
        probabilities_b, _states_b = infer(model_b, all_ids)
        candidate_p1_a = full_candidate_p1(probabilities_a)
        candidate_p1_b = full_candidate_p1(probabilities_b)
        payload_a = range_encode(candidate_p1_a, all_truth)
        payload_b = range_encode(candidate_p1_b, all_truth)
        determinism = {
            "selected_epoch_identity": (
                run_a["selected_epoch"] == run_b["selected_epoch"]
            ),
            "training_history_identity": run_a["history"] == run_b["history"],
            "model_blob_identity": run_a["model_blob"] == run_b["model_blob"],
            "adjusted_p1_identity": np.array_equal(
                candidate_p1_a, candidate_p1_b
            ),
            "payload_identity": payload_a == payload_b,
        }
        if not all(determinism.values()):
            raise ValueError(f"{mode} A/B determinism failed: {determinism}")
        return {
            "run": run_a,
            "model": model_a,
            "patch_probabilities": probabilities_a,
            "states": states_a,
            "candidate_p1": candidate_p1_a,
            "payload": payload_a,
            "determinism": determinism,
        }

    print("phase=fit_N1_matched_flat", flush=True)
    n1 = complete_fit("flat")
    print("phase=fit_N2_binary_carry", flush=True)
    n2 = complete_fit("hierarchy")

    if n2["states"] is None:
        raise ValueError("N2 inference did not expose hierarchy states")
    rotated_states = np.empty_like(n2["states"])
    for split in SPLITS:
        pages_in_split = split_pages[split]
        for page_offset, target_page in enumerate(pages_in_split):
            source_page = pages_in_split[(page_offset + 1) % len(pages_in_split)]
            target_ids = page_patch_ids[target_page.index]
            source_ids = page_patch_ids[source_page.index]
            for patch_offset, target_id in enumerate(target_ids):
                source_id = source_ids[patch_offset % len(source_ids)]
                rotated_states[target_id] = n2["states"][source_id]

    def readout_rotated_states(model: Any, states) -> Any:
        residuals = np.empty(
            (len(states), candidate.PATCH_BYTES, candidate.PREFIX_NODES),
            dtype=np.float32,
        )
        model.eval()
        readout_batch_size = BATCH_SIZE * 4
        with torch.no_grad():
            for offset in range(0, len(states), readout_batch_size):
                stop = min(offset + readout_batch_size, len(states))
                batch = torch.from_numpy(states[offset:stop]).to(device)
                residuals[offset:stop] = (
                    model.readout_states(batch).cpu().numpy().astype(np.float32)
                )
        selected = np.take_along_axis(residuals, patch_nodes, axis=2)
        return quantized_probabilities(patch_base_logits, selected)

    print("phase=NS_page_rotated_state_control", flush=True)
    ns_patch_probabilities = readout_rotated_states(n2["model"], rotated_states)
    ns_candidate_p1 = full_candidate_p1(ns_patch_probabilities)
    ns_payload = range_encode(ns_candidate_p1, all_truth)

    def control_row(name: str, patch_probabilities, payload: bytes) -> dict[str, Any]:
        rows: dict[str, Any] = {
            "name": name,
            "full_payload_bytes": len(payload),
            "full_payload_sha256": sha256_bytes(payload),
            "full_gain_bytes": len(receipt_parent_payload) - len(payload),
            "splits": {},
        }
        for split in SPLITS:
            ids = split_patch_ids[split]
            candidate_payload = range_encode(
                patch_probabilities[ids].reshape(-1),
                patch_bits[ids].astype(np.uint8).reshape(-1),
            )
            parent_bytes = len(split_parent_payloads[split])
            gain = parent_bytes - len(candidate_payload)
            raw_bytes = split_raw_bytes[split]
            rows["splits"][split] = {
                "raw_page_bytes": raw_bytes,
                "modeled_patches": len(ids),
                "modeled_wrt_bytes": len(ids) * candidate.PATCH_BYTES,
                "parent_payload_bytes": parent_bytes,
                "candidate_payload_bytes": len(candidate_payload),
                "candidate_payload_sha256": sha256_bytes(candidate_payload),
                "gain_bytes": gain,
                "gross_gain_bytes_per_million_raw": (
                    gain * 1_000_000.0 / raw_bytes
                ),
            }
        return rows

    n1_control = control_row("N1", n1["patch_probabilities"], n1["payload"])
    n2_control = control_row("N2_NM", n2["patch_probabilities"], n2["payload"])
    ns_control = control_row("NS", ns_patch_probabilities, ns_payload)

    n1_compressed = zlib.compress(n1["run"]["model_blob"], level=9)
    n2_compressed = zlib.compress(n2["run"]["model_blob"], level=9)
    matched_model_bytes = max(len(n1_compressed), len(n2_compressed))
    matched_package_bytes = (
        matched_model_bytes + DECODER_ALLOWANCE_BYTES + FRAMING_ALLOWANCE_BYTES
    )
    sealed = n2_control["splits"]["sealed_confirmation"]
    sealed_gross_bpm = sealed["gross_gain_bytes_per_million_raw"]
    sealed_net_bpm = sealed_gross_bpm - matched_package_bytes / 1000.0

    n2_second_payload = range_encode(n2["candidate_p1"], all_truth)
    decoded_bits = range_decode(n2["payload"], n2["candidate_p1"])
    arithmetic_roundtrip = np.array_equal(decoded_bits, all_truth)
    decoded_wrt = np.packbits(decoded_bits, bitorder="big").tobytes()
    wrt_roundtrip = decoded_wrt == wrt.tobytes()
    reconstructed_store = stored[:5] + decoded_wrt
    reconstructed_store_path = args.output_dir / "n2.wrt_store.bin"
    reconstructed_store_path.write_bytes(reconstructed_store)
    restored_raw_path = args.output_dir / "n2.restored.raw"
    inverse_stdout = args.output_dir / "n2_inverse.stdout.log"
    inverse_stderr = args.output_dir / "n2_inverse.stderr.log"
    with inverse_stdout.open("wb") as stdout, inverse_stderr.open("wb") as stderr:
        inverse = subprocess.run(
            [
                str(args.backend),
                "-d",
                str(args.dictionary),
                str(reconstructed_store_path),
                str(restored_raw_path),
            ],
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    raw_roundtrip = (
        inverse.returncode == 0
        and restored_raw_path.is_file()
        and restored_raw_path.read_bytes() == raw
    )

    (args.output_dir / "n1_model.bin.zlib").write_bytes(n1_compressed)
    (args.output_dir / "n2_model.bin.zlib").write_bytes(n2_compressed)
    (args.output_dir / "n1.payload").write_bytes(n1["payload"])
    (args.output_dir / "n2.payload").write_bytes(n2["payload"])
    (args.output_dir / "ns.payload").write_bytes(ns_payload)

    conditions = {
        "parent_payload_identity": replay_parent_payload == receipt_parent_payload,
        "development_N2_gain_positive": (
            n2_control["splits"]["development"]["gain_bytes"] > 0
        ),
        "selection_N2_gain_positive": (
            n2_control["splits"]["selection"]["gain_bytes"] > 0
        ),
        "sealed_N2_gross_at_least_3000_BPM": sealed_gross_bpm >= GROSS_GATE_BPM,
        "sealed_N2_net_at_least_2100_BPM": sealed_net_bpm >= NET_GATE_BPM,
        "sealed_N2_beats_matched_N1": (
            sealed["candidate_payload_bytes"]
            < n1_control["splits"]["sealed_confirmation"]["candidate_payload_bytes"]
        ),
        "sealed_N2_beats_page_rotated_NS": (
            sealed["candidate_payload_bytes"]
            < ns_control["splits"]["sealed_confirmation"]["candidate_payload_bytes"]
        ),
        "matched_package_within_131072_bytes": (
            matched_package_bytes <= PACKAGE_CEILING_BYTES
        ),
        "N1_repeated_fit_identity": all(n1["determinism"].values()),
        "N2_repeated_fit_identity": all(n2["determinism"].values()),
        "full_arithmetic_decode": arithmetic_roundtrip,
        "WRT_reconstruction": wrt_roundtrip,
        "official_raw_inverse": raw_roundtrip,
        "second_payload_byte_identical": n2_second_payload == n2["payload"],
    }
    failed_conditions = [name for name, passed in conditions.items() if not passed]
    authorized = not failed_conditions
    verdict = (
        "authorize_frozen_distant_reset_replay"
        if authorized
        else "retire_exact_binary_carry_hierarchy"
    )

    native_receipt = json.loads(args.native_receipt.read_text(encoding="utf-8"))
    decision = {
        "schema": "mobius2_noema_binary_carry_headroom_qh0_v1",
        "candidate_id": CANDIDATE_ID,
        "proposal_id": PROPOSAL_ID,
        "evidence_level": "zero_credit_exact_hierarchy_headroom",
        "claim_boundary": (
            "Exact opening-1M float32/dequantized-int8 hierarchy headroom only. "
            "This is not a deterministic integer runtime, distant transfer, "
            "native Gamma integration, forecast update, or full-corpus score."
        ),
        "inputs": {
            "p1_trace": artifact(args.p1),
            "wrt_store": artifact(args.wrt_store),
            "raw_input": artifact(args.raw_input),
            "parent_archive": artifact(args.parent_archive),
            "dictionary": artifact(args.dictionary),
            "backend": artifact(args.backend),
            "manifest": artifact(args.manifest),
            "native_receipt": artifact(args.native_receipt),
            "page_map": artifact(args.page_map),
            "candidate_program": artifact(CANDIDATE_PROGRAM),
            "plan": artifact(PLAN_PATH),
            "decision_schema": artifact(SCHEMA_PATH),
            "p1_magic_hex": p1_header[:8].hex(),
        },
        "population": {
            "raw_bytes": len(raw),
            "wrt_bytes": len(wrt),
            "complete_pages": len(pages),
            "complete_patches": len(patches),
            "modeled_wrt_bytes": len(patches) * candidate.PATCH_BYTES,
            "unmodeled_wrt_bytes": len(wrt)
            - len(patches) * candidate.PATCH_BYTES,
            "pages_by_split": {
                split: len(split_pages[split]) for split in SPLITS
            },
            "patches_by_split": {
                split: len(split_patch_ids[split]) for split in SPLITS
            },
            "raw_page_bytes_by_split": split_raw_bytes,
        },
        "architecture": {
            "patch_bytes": candidate.PATCH_BYTES,
            "byte_embedding_width": candidate.BYTE_EMBEDDING_WIDTH,
            "summary_width": candidate.SUMMARY_WIDTH,
            "level_count": candidate.LEVEL_COUNT,
            "level_embedding_width": candidate.LEVEL_EMBEDDING_WIDTH,
            "prefix_nodes": candidate.PREFIX_NODES,
            "parameter_count": n2["run"]["parameter_count"],
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "seed": SEED,
            "optimizer": "AdamW",
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "gradient_clip": GRADIENT_CLIP,
            "selection": "minimum exact quantized selection payload; earlier epoch tie",
            "quantization": "symmetric signed int8 per tensor; dequantized float32 ROCm oracle",
            "N2_summary": "binary prefix decomposition with one shared GRUCell merge across seven levels",
            "surprise_memory": "disabled; N2 is the NM ablation",
            "runtime_mode": runtime_mode,
            "torch_version": torch.__version__,
        },
        "training": {
            "N1_selected_epoch": n1["run"]["selected_epoch"],
            "N2_selected_epoch": n2["run"]["selected_epoch"],
            "N1_history": n1["run"]["history"],
            "N2_history": n2["run"]["history"],
        },
        "controls": {
            "N0": {
                "archive_bytes": len(archive),
                "archive_sha256": sha256_bytes(archive),
                "parent_header_bytes": parent_header_bytes,
                "parent_payload_bytes": len(receipt_parent_payload),
                "parent_payload_sha256": sha256_bytes(receipt_parent_payload),
                "native_receipt_archive_bytes": native_receipt.get(
                    "archive_bytes"
                ),
            },
            "N1": n1_control,
            "N2_NM": n2_control,
            "NS": ns_control,
        },
        "package": {
            "N1_canonical_model_bytes": len(n1["run"]["model_blob"]),
            "N1_zlib9_model_bytes": len(n1_compressed),
            "N1_model_sha256": sha256_bytes(n1["run"]["model_blob"]),
            "N2_canonical_model_bytes": len(n2["run"]["model_blob"]),
            "N2_zlib9_model_bytes": len(n2_compressed),
            "N2_model_sha256": sha256_bytes(n2["run"]["model_blob"]),
            "matched_model_charge_bytes": matched_model_bytes,
            "decoder_allowance_bytes": DECODER_ALLOWANCE_BYTES,
            "framing_allowance_bytes": FRAMING_ALLOWANCE_BYTES,
            "matched_total_package_bytes": matched_package_bytes,
            "package_ceiling_bytes": PACKAGE_CEILING_BYTES,
            "oracle_source_gzip9_bytes_not_charged": len(
                gzip.compress(
                    Path(__file__).read_bytes() + CANDIDATE_PROGRAM.read_bytes(),
                    compresslevel=9,
                )
            ),
        },
        "economics": {
            "target_score_bytes": 108_000_000,
            "forecast_score_bytes_unchanged": 109_389_323,
            "forecast_debt_bytes": 1_389_323,
            "sealed_N2_gross_gain_bytes_per_million_raw": sealed_gross_bpm,
            "package_amortized_bytes_per_million": matched_package_bytes / 1000.0,
            "sealed_N2_net_gain_bytes_per_million_raw": sealed_net_bpm,
            "score_credit_bytes": 0,
        },
        "proof": {
            "manifest_bindings_verified": True,
            "exact_WRT_parse_equals_raw": True,
            "parent_payload_identity": replay_parent_payload
            == receipt_parent_payload,
            "N1_determinism": n1["determinism"],
            "N2_determinism": n2["determinism"],
            "full_arithmetic_decode": arithmetic_roundtrip,
            "WRT_reconstruction": wrt_roundtrip,
            "reconstructed_store_sha256": sha256_bytes(reconstructed_store),
            "official_inverse_returncode": inverse.returncode,
            "raw_roundtrip": raw_roundtrip,
            "raw_reconstruction_sha256": (
                sha256_file(restored_raw_path) if restored_raw_path.is_file() else None
            ),
            "second_payload_byte_identical": n2_second_payload == n2["payload"],
            "adjusted_N2_p1_sha256": sha256_bytes(
                n2["candidate_p1"].astype("<u2").tobytes(order="C")
            ),
        },
        "gates": {
            "gross_gate_bytes_per_million": GROSS_GATE_BPM,
            "net_gate_bytes_per_million": NET_GATE_BPM,
            "conditions": conditions,
            "failed_conditions": failed_conditions,
        },
        "decision": {
            "promotion_authorized": authorized,
            "verdict": verdict,
            "next_action": (
                "run one frozen distant reset-population replay before integer runtime work"
                if authorized
                else "retire this exact binary-carry hierarchy without rescue sweeps; semantic-boundary hierarchy and materially different information sources remain unsettled"
            ),
        },
        "score_credit_bytes": 0,
        "limitations": [
            "The oracle executes dequantized float32 weights on ROCm.",
            "No deterministic dyadic integer runtime exists.",
            "Opening-1M chronological confirmation is not distant transfer.",
            "The page map is supplied to QH0 and is not yet decoder-reconstructed.",
            "Package allowance is frozen research accounting, not a counted submission.",
            "This receipt has zero forecast and score credit.",
        ],
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "N1_full_gain": n1_control["full_gain_bytes"],
                "N2_full_gain": n2_control["full_gain_bytes"],
                "NS_full_gain": ns_control["full_gain_bytes"],
                "sealed_gross_BPM": sealed_gross_bpm,
                "sealed_net_BPM": sealed_net_bpm,
                "failed_conditions": failed_conditions,
                "verdict": verdict,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
