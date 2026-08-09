#!/usr/bin/env python3
"""Build and screen the KAIROS-105 post-head dyadic correction opening."""

from __future__ import annotations

import hashlib
import io
import json
import lzma
import math
import os
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from fx2_attribution_external_base_screen import (  # noqa: E402
    CmixRangeEncoder,
    cmix_archive_header_bytes,
)

CANDIDATE_ID = "kairos105_final_head_dyadic_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
EXTERNAL = Path("/home/x/enwiki9-nonproof/results") / CANDIDATE_ID
DONOR = Path("/home/x/enwiki9-nonproof/cmix-obias-native-build-v1")
BASE_PACKAGED = DONOR / "run/cmix.head_assets"
HEAD = DONOR / "models/bitlstm32/refit_golden256_fp16.blob"
CANONICAL = ROOT / "data/enwik9"
PATCH = ROOT / "programs" / CANDIDATE_ID / "post_head_complete_trace.patch"
META = ROOT / "programs" / CANDIDATE_ID / "meta.json"
PLAN = ROOT / "docs/kairos105_final_head_dyadic_qm0_plan.md"
SOURCE = Path(__file__).resolve()

RAW_SCOPE = 1_000_000
RECORD_BYTES = 56
ATOMIC_BITS = 1 << 18
RANK = 8
Q = 256
LOGIT_BOUND = 4096
PROB_TOTAL = 65536
OPENING_GROSS_REFERENCE = 4_500
OPENING_CONTROL_REFERENCE = 500
SCHEDULE_LIMIT = 128 * 1024
EXPECTED_BASE_BINARY_SHA256 = (
    "aee602b8145f7f04c9a6ea9107cf44bc5c94677723101eec3288a78377ddad97"
)
EXPECTED_HEAD_SHA256 = (
    "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"
)
FEATURE_NAMES = (
    "intercept",
    "centered_final_probability",
    "raw_final_mixer_logit",
    "fxcm_stage1",
    "byte_lstm_stage1",
    "layer0_mean",
    "layer0_spread",
    "byte_minus_fxcm",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, *, hash_file: bool = True) -> dict[str, Any]:
    row: dict[str, Any] = {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
    }
    if hash_file:
        row["sha256"] = sha256(path)
    return row


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    stdout_path: Path | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    merged = os.environ.copy()
    if env:
        merged.update(env)
    if stdout_path is None:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=merged,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = completed.stdout
    else:
        with stdout_path.open("wb") as stream:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=merged,
                check=False,
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
        output = b""
    receipt = {
        "command": command,
        "cwd": str(cwd.resolve()),
        "elapsed_seconds_diagnostic": time.monotonic() - started,
        "returncode": completed.returncode,
    }
    if stdout_path is None:
        receipt["output_sha256"] = hashlib.sha256(output).hexdigest()
        receipt["output_tail"] = output[-4000:].decode("utf-8", "replace")
    else:
        receipt["log"] = artifact(stdout_path)
    if completed.returncode:
        raise RuntimeError(json.dumps(receipt, indent=2))
    return receipt


def clean_transients(directory: Path) -> None:
    names = (
        "ppm.temp",
        ".coda",
        ".dict",
        ".dict.comp",
        ".intro",
        ".main",
        ".main_phda9prepr",
        ".main_reordered",
        ".new_article_order",
        ".new_article_order.comp",
        ".ready4cmix",
        "test.dat",
        "un1",
    )
    for name in names:
        path = directory / name
        if path.is_file():
            path.unlink()


def make_input() -> Path:
    target = EXTERNAL / "input/enwik1m"
    target.parent.mkdir(parents=True, exist_ok=True)
    with CANONICAL.open("rb") as source, target.open("wb") as output:
        remaining = RAW_SCOPE
        while remaining:
            block = source.read(min(8 << 20, remaining))
            if not block:
                raise ValueError("canonical input ended before opening scope")
            output.write(block)
            remaining -= len(block)
    return target


def copy_source_tree() -> Path:
    build = EXTERNAL / "build"
    if build.exists():
        raise FileExistsError(build)

    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = {name for name in names if name.endswith(".o")}
        ignored.update(
            name
            for name in names
            if name in {"cmix", "cmix_orig", "run", "build_scratch", "ppm.temp"}
        )
        return ignored

    shutil.copytree(
        DONOR,
        build,
        ignore=ignore,
        ignore_dangling_symlinks=True,
    )
    return build


def build_observer(build: Path) -> tuple[Path, list[dict[str, Any]]]:
    receipts: list[dict[str, Any]] = []
    receipts.append(
        run_command(
            ["patch", "-p1", "-i", str(PATCH)],
            cwd=build,
        )
    )
    defines = (
        "-DSEED=923 -DUPDATE_LIMIT=3000 -DLSTM_NUM_CELLS=256 "
        "-DKH_BITLSTM32 -DKH_OBIAS -DKH_OBIAS_CONST_GATE=0.15f"
    )
    receipts.append(
        run_command(
            [
                "make",
                "prof_use",
                "CC=clang++-17",
                f"CFLAGS_DEFINES={defines}",
                "KH_BITLSTM32_ARCHIVE=1",
                "KH_TRACE=1",
                "-j4",
            ],
            cwd=build,
        )
    )
    binary = build / "cmix"
    if not binary.is_file():
        raise FileNotFoundError(binary)
    return binary, receipts


def package_binary(raw_binary: Path, directory: Path) -> tuple[Path, list[dict[str, Any]]]:
    directory.mkdir(parents=True, exist_ok=True)
    target_raw = directory / "cmix_orig"
    shutil.copy2(raw_binary, target_raw)
    target_raw.chmod(0o755)
    shutil.copy2(HEAD, directory / "head.blob")
    env = {"KH_BITLSTM32": str((directory / "head.blob").resolve())}
    receipts = [
        run_command(
            ["./cmix_orig", "-c", str(DONOR / "dictionary/english.dic"), "comp_dict"],
            cwd=directory,
            env=env,
        ),
        run_command(
            [
                "./cmix_orig",
                "-c",
                str(DONOR / "src/readalike_prepr/data/new_article_order"),
                "comp_order",
            ],
            cwd=directory,
            env=env,
        ),
    ]
    dict_size = (directory / "comp_dict").stat().st_size
    order_size = (directory / "comp_order").stat().st_size
    receipts.append(
        run_command(
            ["./cmix_orig", "-h", str(dict_size), str(order_size), "0"],
            cwd=directory,
            env=env,
        )
    )
    packaged = directory / "cmix"
    with packaged.open("wb") as output:
        for name in ("cmix_orig", "comp_dict", "comp_order", "header.dat"):
            output.write((directory / name).read_bytes())
    packaged.chmod(0o755)
    clean_transients(directory)
    return packaged, receipts


def run_encode(binary: Path, directory: Path, input_path: Path, trace: bool) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    local = directory / "cmix"
    if binary.resolve() != local.resolve():
        shutil.copy2(binary, local)
        local.chmod(0o755)
    shutil.copy2(HEAD, directory / "head.blob")
    env = {
        "KH_BITLSTM32": str((directory / "head.blob").resolve()),
        "CMIX_PPM_RSS_MB": "8500",
    }
    trace_dir = directory / "trace"
    if trace:
        trace_dir.mkdir(parents=True, exist_ok=True)
        env["KH_TRACE_DIR"] = str(trace_dir.resolve())
    receipt = run_command(
        ["./cmix", "-e", str(input_path.resolve()), "out.cmix"],
        cwd=directory,
        env=env,
        stdout_path=directory / "encode.log",
    )
    receipt["payload"] = artifact(directory / "out.cmix")
    receipt["archive"] = artifact(directory / "archive9")
    clean_transients(directory)
    return receipt


def source_package() -> dict[str, Any]:
    package = RESULT / "source_package.tar.lzma"
    members = (SOURCE, PATCH, PLAN, META)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for member in sorted(members, key=lambda value: str(value)):
            info = tarfile.TarInfo(str(member.relative_to(ROOT)))
            payload = member.read_bytes()
            info.size = len(payload)
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(payload))
    package.write_bytes(lzma.compress(raw.getvalue(), preset=9 | lzma.PRESET_EXTREME))
    return artifact(package)


def trace_dtype() -> np.dtype[Any]:
    return np.dtype(
        [
            ("p", "<u2"),
            ("flags", "u1"),
            ("reserved", "u1"),
            ("half", "<f2", (26,)),
        ]
    )


def probability_tables() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    index = np.arange(PROB_TOTAL, dtype=np.float64)
    probability = np.clip(index / PROB_TOTAL, 1 / PROB_TOTAL, (PROB_TOTAL - 1) / PROB_TOTAL)
    logit = np.rint((np.log(probability) - np.log1p(-probability)) * Q)
    logit = np.clip(logit, -LOGIT_BOUND, LOGIT_BOUND).astype(np.int16)
    grid = np.arange(-LOGIT_BOUND, LOGIT_BOUND + 1, dtype=np.float64) / Q
    sigmoid = np.rint((1.0 / (1.0 + np.exp(-grid))) * PROB_TOTAL)
    sigmoid = np.clip(sigmoid, 1, PROB_TOTAL - 1).astype(np.uint16)
    loss0 = np.zeros(PROB_TOTAL, dtype=np.int32)
    loss1 = np.zeros(PROB_TOTAL, dtype=np.int32)
    for p in range(1, PROB_TOTAL):
        loss0[p] = int(-math.log2((PROB_TOTAL - p) / PROB_TOTAL) * Q + 0.5)
        loss1[p] = int(-math.log2(p / PROB_TOTAL) * Q + 0.5)
    return logit, sigmoid, loss0, loss1


def materialize_features(trace: np.memmap, chunk_rows: int = 262_144) -> tuple[np.ndarray, ...]:
    rows = len(trace)
    p = np.asarray(trace["p"], dtype=np.uint16).copy()
    flags = np.asarray(trace["flags"], dtype=np.uint8).copy()
    truth = (flags & 1).astype(np.uint8)
    raw = (flags & 4) != 0
    override = (flags & 2) != 0
    eligible = ~(raw | override)
    xq = np.zeros((rows, RANK), dtype=np.int16)
    for start in range(0, rows, chunk_rows):
        end = min(rows, start + chunk_rows)
        half = np.asarray(trace["half"][start:end], dtype=np.float32)
        stage = half[:, :25]
        local = np.zeros((end - start, RANK), dtype=np.float64)
        local[:, 0] = 1.0
        local[:, 1] = (p[start:end].astype(np.float64) - 32768.0) / 32768.0
        local[:, 2] = half[:, 25] / 8.0
        local[:, 3] = stage[:, 23] / 8.0
        local[:, 4] = stage[:, 24] / 8.0
        local[:, 5] = stage[:, :23].mean(axis=1, dtype=np.float64) / 8.0
        local[:, 6] = (
            stage[:, :23].max(axis=1) - stage[:, :23].min(axis=1)
        ) / 8.0
        local[:, 7] = (stage[:, 24] - stage[:, 23]) / 8.0
        quantized = np.rint(np.clip(local, -4.0, 4.0) * Q).astype(np.int16)
        quantized[~eligible[start:end]] = 0
        xq[start:end] = quantized
    return p, truth, raw, override, eligible, xq


@dataclass(frozen=True)
class Node:
    start_leaf: int
    end_leaf: int
    left: "Node | None" = None
    right: "Node | None" = None


def tree(start: int, end: int) -> Node:
    if end - start == 1:
        return Node(start, end)
    middle = (start + end) // 2
    return Node(start, end, tree(start, middle), tree(middle, end))


def bit_bounds(node: Node, rows: int) -> tuple[int, int]:
    return node.start_leaf * ATOMIC_BITS, min(rows, node.end_leaf * ATOMIC_BITS)


def correction(
    p: np.ndarray,
    xq: np.ndarray,
    coefficient: np.ndarray,
    logit: np.ndarray,
    sigmoid: np.ndarray,
) -> np.ndarray:
    dot = xq.astype(np.int64) @ coefficient.astype(np.int64)
    delta = np.floor_divide(dot + np.where(dot >= 0, Q // 2, -(Q // 2)), Q)
    qlogit = np.clip(logit[p].astype(np.int64) + delta, -LOGIT_BOUND, LOGIT_BOUND)
    return sigmoid[(qlogit + LOGIT_BOUND).astype(np.int64)]


def fit_leaf_stats(
    p: np.ndarray,
    truth: np.ndarray,
    xq: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    leaves = (len(p) + ATOMIC_BITS - 1) // ATOMIC_BITS
    gradients = np.zeros((leaves, RANK), dtype=np.float64)
    hessians = np.zeros((leaves, RANK, RANK), dtype=np.float64)
    for leaf in range(leaves):
        start = leaf * ATOMIC_BITS
        end = min(len(p), start + ATOMIC_BITS)
        x = xq[start:end].astype(np.float64) / Q
        probability = p[start:end].astype(np.float64) / PROB_TOTAL
        error = probability - truth[start:end].astype(np.float64)
        weight = probability * (1.0 - probability)
        gradients[leaf] = x.T @ error
        hessians[leaf] = x.T @ (x * weight[:, None])
    return gradients, hessians


def quantized_coefficient(gradient: np.ndarray, hessian: np.ndarray) -> np.ndarray:
    ridge = np.eye(len(gradient), dtype=np.float64) * 1.0e-3
    try:
        value = np.linalg.solve(hessian + ridge, -gradient)
    except np.linalg.LinAlgError:
        value = np.linalg.lstsq(hessian + ridge, -gradient, rcond=None)[0]
    return np.rint(np.clip(value, -4.0, 4.0) * Q).astype(np.int16)


def node_models(
    root: Node,
    gradients: np.ndarray,
    hessians: np.ndarray,
    p: np.ndarray,
    truth: np.ndarray,
    xq: np.ndarray,
    logit: np.ndarray,
    sigmoid: np.ndarray,
    loss0: np.ndarray,
    loss1: np.ndarray,
    rank: int,
) -> dict[tuple[int, int], dict[str, Any]]:
    models: dict[tuple[int, int], dict[str, Any]] = {}

    def visit(node: Node) -> tuple[np.ndarray, np.ndarray]:
        if node.left is None:
            gradient = gradients[node.start_leaf, :rank].copy()
            hessian = hessians[node.start_leaf, :rank, :rank].copy()
        else:
            left_g, left_h = visit(node.left)
            right_g, right_h = visit(node.right)  # type: ignore[arg-type]
            gradient = left_g + right_g
            hessian = left_h + right_h
        coefficient = quantized_coefficient(gradient, hessian)
        start, end = bit_bounds(node, len(p))
        candidate = correction(
            p[start:end], xq[start:end, :rank], coefficient, logit, sigmoid
        )
        bits = truth[start:end]
        loss = int(np.where(bits, loss1[candidate], loss0[candidate]).sum(dtype=np.int64))
        models[(node.start_leaf, node.end_leaf)] = {
            "coefficient": coefficient,
            "loss_qbits": loss,
        }
        return gradient, hessian

    visit(root)
    return models


def select_tree(
    root: Node,
    models: dict[tuple[int, int], dict[str, Any]],
    rank: int,
) -> tuple[dict[tuple[int, int], np.ndarray], int]:
    selected: dict[tuple[int, int], np.ndarray] = {}
    flag_qbits = 8 * Q
    coefficient_qbits = rank * 2 * 8 * Q

    def choose(node: Node) -> tuple[int, dict[tuple[int, int], np.ndarray]]:
        key = (node.start_leaf, node.end_leaf)
        keep_cost = models[key]["loss_qbits"] + flag_qbits + coefficient_qbits
        keep = {key: models[key]["coefficient"]}
        if node.left is None:
            return keep_cost, keep
        left_cost, left = choose(node.left)
        right_cost, right = choose(node.right)  # type: ignore[arg-type]
        split_cost = flag_qbits + left_cost + right_cost
        if keep_cost <= split_cost:
            return keep_cost, keep
        merged = dict(left)
        merged.update(right)
        return split_cost, merged

    cost, selected = choose(root)
    return selected, cost


def schedule_candidate(
    p: np.ndarray,
    xq: np.ndarray,
    selected: dict[tuple[int, int], np.ndarray],
    logit: np.ndarray,
    sigmoid: np.ndarray,
) -> np.ndarray:
    candidate = p.copy()
    for (start_leaf, end_leaf), coefficient in sorted(selected.items()):
        start = start_leaf * ATOMIC_BITS
        end = min(len(p), end_leaf * ATOMIC_BITS)
        candidate[start:end] = correction(
            p[start:end], xq[start:end, : len(coefficient)], coefficient, logit, sigmoid
        )
    return candidate


def serialize_schedule(
    root: Node,
    selected: dict[tuple[int, int], np.ndarray],
    rank: int,
    rows: int,
) -> bytes:
    output = bytearray(struct.pack("<8sQII", b"KAI105Q0", rows, ATOMIC_BITS, rank))

    def emit(node: Node) -> None:
        key = (node.start_leaf, node.end_leaf)
        if key in selected:
            output.append(0)
            coefficient = np.asarray(selected[key], dtype="<i2")
            output.extend(coefficient.tobytes())
            return
        if node.left is None:
            raise AssertionError("leaf absent from selected schedule")
        output.append(1)
        emit(node.left)
        emit(node.right)  # type: ignore[arg-type]

    emit(root)
    return bytes(output)


def rotate_schedule(selected: dict[tuple[int, int], np.ndarray]) -> dict[tuple[int, int], np.ndarray]:
    keys = sorted(selected)
    values = [selected[key] for key in keys]
    if len(values) > 1:
        values = values[-1:] + values[:-1]
    return {key: value.copy() for key, value in zip(keys, values, strict=True)}


def shuffled_schedule(selected: dict[tuple[int, int], np.ndarray]) -> dict[tuple[int, int], np.ndarray]:
    rng = np.random.default_rng(105)
    keys = sorted(selected)
    output = {key: selected[key].copy() for key in keys}
    groups: dict[int, list[tuple[int, int]]] = {}
    for key in keys:
        groups.setdefault(key[1] - key[0], []).append(key)
    changed = False
    for group in groups.values():
        if len(group) < 2:
            continue
        order = rng.permutation(len(group))
        values = [selected[group[int(index)]].copy() for index in order]
        for key, value in zip(group, values, strict=True):
            changed |= not np.array_equal(output[key], value)
            output[key] = value
    if not changed and len(keys) > 1:
        values = [selected[key].copy() for key in keys]
        values = values[1:] + values[:1]
        output = {key: value for key, value in zip(keys, values, strict=True)}
    return output


class RangeDecoder:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.offset = 0
        self.x1 = 0
        self.x2 = 0xFFFFFFFF
        self.x = 0
        for _ in range(4):
            self.x = ((self.x << 8) + self.read_byte()) & 0xFFFFFFFF

    def read_byte(self) -> int:
        if self.offset >= len(self.payload):
            return 0
        value = self.payload[self.offset]
        self.offset += 1
        return value

    def decode(self, p1: int) -> int:
        span = (self.x2 - self.x1) & 0xFFFFFFFF
        midpoint = (
            self.x1 + (span >> 16) * p1 + (((span & 0xFFFF) * p1) >> 16)
        ) & 0xFFFFFFFF
        if self.x <= midpoint:
            bit = 1
            self.x2 = midpoint
        else:
            bit = 0
            self.x1 = (midpoint + 1) & 0xFFFFFFFF
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.x1 = (self.x1 << 8) & 0xFFFFFFFF
            self.x2 = ((self.x2 << 8) + 255) & 0xFFFFFFFF
            self.x = ((self.x << 8) + self.read_byte()) & 0xFFFFFFFF
        return bit


def exact_payload(truth: np.ndarray, probabilities: np.ndarray) -> bytes:
    coder = CmixRangeEncoder()
    for bit, p1 in zip(truth, probabilities, strict=True):
        coder.encode(int(bit), int(p1))
    return coder.finish()


def decode_exact(payload: bytes, probabilities: np.ndarray, truth: np.ndarray) -> bool:
    decoder = RangeDecoder(payload)
    for expected, p1 in zip(truth, probabilities, strict=True):
        if decoder.decode(int(p1)) != int(expected):
            return False
    return True


def split_gains(truth: np.ndarray, base: np.ndarray, candidate: np.ndarray) -> list[int]:
    gains: list[int] = []
    for third in range(3):
        start = len(truth) * third // 3
        end = len(truth) * (third + 1) // 3
        gains.append(
            len(exact_payload(truth[start:end], base[start:end]))
            - len(exact_payload(truth[start:end], candidate[start:end]))
        )
    return gains


def arm_receipt(
    name: str,
    truth: np.ndarray,
    base_payload: bytes,
    probabilities: np.ndarray,
    schedule_raw: bytes,
    lookup_compressed_bytes: int,
) -> tuple[dict[str, Any], bytes]:
    payload = exact_payload(truth, probabilities)
    compressed = lzma.compress(schedule_raw, preset=9 | lzma.PRESET_EXTREME)
    row = {
        "arm": name,
        "payload_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "gross_gain_bytes": len(base_payload) - len(payload),
        "schedule_raw_bytes": len(schedule_raw),
        "schedule_compressed_bytes": len(compressed),
        "lookup_compressed_bytes": lookup_compressed_bytes,
        "paid_gain_before_source_bytes": (
            len(base_payload) - len(payload) - len(compressed) - lookup_compressed_bytes
        ),
        "arithmetic_decode_exact": decode_exact(payload, probabilities, truth),
    }
    return row, payload


def screen(trace_path: Path, native_payload_path: Path) -> dict[str, Any]:
    size = trace_path.stat().st_size
    if size % RECORD_BYTES:
        raise ValueError("trace size is not record aligned")
    trace = np.memmap(trace_path, dtype=trace_dtype(), mode="r")
    p, truth, raw, override, eligible, xq = materialize_features(trace)
    logit, sigmoid, loss0, loss1 = probability_tables()
    lookup_material = logit.astype("<i2").tobytes() + sigmoid.astype("<u2").tobytes()
    lookup_compressed = lzma.compress(
        lookup_material, preset=9 | lzma.PRESET_EXTREME
    )
    gradients, hessians = fit_leaf_stats(p, truth, xq)
    leaves = len(gradients)
    root = tree(0, leaves)

    models = node_models(
        root, gradients, hessians, p, truth, xq, logit, sigmoid, loss0, loss1, RANK
    )
    selected, _ = select_tree(root, models, RANK)
    selected_repeat, _ = select_tree(root, models, RANK)
    if any(
        not np.array_equal(selected[key], selected_repeat[key])
        for key in selected
    ) or set(selected) != set(selected_repeat):
        raise AssertionError("second K0 model fit differs")

    p_models = node_models(
        root,
        gradients[:, :1],
        hessians[:, :1, :1],
        p,
        truth,
        xq[:, :1],
        logit,
        sigmoid,
        loss0,
        loss1,
        1,
    )
    p_selected, _ = select_tree(root, p_models, 1)
    global_coefficient = models[(0, leaves)]["coefficient"]
    global_selected = {(0, leaves): global_coefficient}
    o_selected = {
        (leaf, leaf + 1): models[(leaf, leaf + 1)]["coefficient"]
        for leaf in range(leaves)
    }
    rotated = rotate_schedule(selected)
    shuffled = shuffled_schedule(selected)

    schedules = {
        "G0": global_selected,
        "K0": selected,
        "P0": p_selected,
        "R0": rotated,
        "S0": shuffled,
        "O0": o_selected,
    }
    ranks = {"G0": RANK, "K0": RANK, "P0": 1, "R0": RANK, "S0": RANK, "O0": RANK}
    candidates = {
        name: schedule_candidate(p, xq, schedule, logit, sigmoid)
        for name, schedule in schedules.items()
    }

    base_payload = exact_payload(truth, p)
    native_payload = native_payload_path.read_bytes()
    header_bytes = cmix_archive_header_bytes(native_payload)
    native_suffix = native_payload[header_bytes:]
    base_identity = base_payload == native_suffix
    arms: dict[str, Any] = {
        "B0": {
            "payload_bytes": len(base_payload),
            "payload_sha256": hashlib.sha256(base_payload).hexdigest(),
            "arithmetic_decode_exact": decode_exact(base_payload, p, truth),
        }
    }
    payloads: dict[str, bytes] = {}
    for name in ("G0", "K0", "P0", "R0", "S0", "O0"):
        schedule_raw = serialize_schedule(root, schedules[name], ranks[name], len(p))
        arms[name], payloads[name] = arm_receipt(
            name,
            truth,
            base_payload,
            candidates[name],
            schedule_raw,
            len(lookup_compressed),
        )
        arms[name]["leaves"] = len(schedules[name])
        arms[name]["chronological_third_gains_bytes"] = split_gains(
            truth, p, candidates[name]
        )
        if name == "O0":
            arms[name]["credit_boundary"] = "free_atomic_leaf_ceiling_zero_credit"

    k_schedule = serialize_schedule(root, selected, RANK, len(p))
    k_payload_repeat = exact_payload(truth, candidates["K0"])
    deterministic = (
        k_schedule == serialize_schedule(root, selected_repeat, RANK, len(p))
        and payloads["K0"] == k_payload_repeat
    )
    control_margins = {
        name: arms["K0"]["gross_gain_bytes"] - arms[name]["gross_gain_bytes"]
        for name in ("G0", "P0", "R0", "S0")
    }
    opening_references = {
        "gross_gain_bytes": OPENING_GROSS_REFERENCE,
        "control_margin_bytes": OPENING_CONTROL_REFERENCE,
    }
    gates = {
        "native_traced_payload_matches_frozen_parent": base_identity,
        "B0_arithmetic_decode_exact": arms["B0"]["arithmetic_decode_exact"],
        "K0_arithmetic_decode_exact": arms["K0"]["arithmetic_decode_exact"],
        "second_model_and_payload_identical": deterministic,
        "all_probabilities_legal": all(
            int(candidate.min()) >= 1 and int(candidate.max()) <= 65535
            for candidate in candidates.values()
        ),
        "K0_schedule_within_128KiB": arms["K0"]["schedule_compressed_bytes"] <= SCHEDULE_LIMIT,
        "K0_gross_meets_scaled_reference": arms["K0"]["gross_gain_bytes"] >= OPENING_GROSS_REFERENCE,
        "K0_thirds_positive": all(
            gain > 0 for gain in arms["K0"]["chronological_third_gains_bytes"]
        ),
        "K0_control_margins_meet_scaled_reference": all(
            margin >= OPENING_CONTROL_REFERENCE for margin in control_margins.values()
        ),
    }
    plumbing = all(
        gates[name]
        for name in (
            "native_traced_payload_matches_frozen_parent",
            "B0_arithmetic_decode_exact",
            "K0_arithmetic_decode_exact",
            "second_model_and_payload_identical",
            "all_probabilities_legal",
            "K0_schedule_within_128KiB",
        )
    )
    signal = all(gates.values())
    verdict = (
        "authorize_compact_full_stream_observer_only"
        if plumbing and signal
        else "opening_plumbing_pass_full_stream_signal_unproved"
        if plumbing
        else "retire_observer_realization_integrity_failure"
    )
    return {
        "schema": "enwiki9_kairos105_final_head_dyadic_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "epistemic_tier": "opening_same_stream_paid_replay_zero_score_credit",
        "claim_boundary": (
            "Exact 1M same-stream arithmetic replay and paid opening schedules only. "
            "No full-stream transfer, native KAIROS decode, isolated runtime, memory-negative "
            "substitution, official score, or prize claim."
        ),
        "population": {
            "raw_scope_bytes": RAW_SCOPE,
            "arithmetic_rows": len(p),
            "modeled_rows": int(np.count_nonzero(~raw)),
            "eligible_correction_rows": int(np.count_nonzero(eligible)),
            "raw_rows": int(np.count_nonzero(raw)),
            "override_rows": int(np.count_nonzero(override)),
            "atomic_bits": ATOMIC_BITS,
            "atomic_leaves": leaves,
        },
        "fixed_point": {
            "rank": RANK,
            "q_scale": Q,
            "feature_names": FEATURE_NAMES,
            "logit_bound_q8": LOGIT_BOUND,
            "lookup_raw_bytes": len(lookup_material),
            "lookup_compressed_bytes": len(lookup_compressed),
        },
        "native_suffix_identity": {
            "cmix_header_bytes": header_bytes,
            "native_suffix_bytes": len(native_suffix),
            "native_suffix_sha256": hashlib.sha256(native_suffix).hexdigest(),
            "replayed_B0_sha256": hashlib.sha256(base_payload).hexdigest(),
            "byte_identical": base_identity,
        },
        "arms": arms,
        "K0_control_gross_margin_bytes": control_margins,
        "opening_references_not_promotion_gates": opening_references,
        "gates": gates,
        "promotion_authorized": False,
        "score_credit_bytes": 0,
        "verdict": verdict,
    }


def main() -> int:
    if (RESULT.exists() and any(RESULT.iterdir())) or EXTERNAL.exists():
        raise FileExistsError(f"refusing overwrite: {RESULT} or {EXTERNAL}")
    if sha256(BASE_PACKAGED) != EXPECTED_BASE_BINARY_SHA256:
        raise ValueError("frozen packaged donor hash mismatch")
    if sha256(HEAD) != EXPECTED_HEAD_SHA256:
        raise ValueError("frozen BitLSTM head hash mismatch")
    RESULT.mkdir(parents=True)
    EXTERNAL.mkdir(parents=True)
    input_path = make_input()
    build = copy_source_tree()
    observer_binary, build_receipts = build_observer(build)
    trace_run = EXTERNAL / "trace_run"
    packaged_observer, package_receipts = package_binary(observer_binary, trace_run)

    baseline_run = EXTERNAL / "baseline_run"
    baseline = run_encode(BASE_PACKAGED, baseline_run, input_path, False)
    traced = run_encode(packaged_observer, trace_run, input_path, True)
    payload_identity = (
        baseline["payload"]["bytes"] == traced["payload"]["bytes"]
        and baseline["payload"]["sha256"] == traced["payload"]["sha256"]
    )
    if not payload_identity:
        raise ValueError("post-head complete trace changed the native payload")

    trace_files = sorted((trace_run / "trace").glob("enc.*.res"))
    if not trace_files:
        raise FileNotFoundError("observer emitted no .res trace")
    trace_path = max(trace_files, key=lambda path: path.stat().st_size)
    screen_receipt = screen(trace_path, trace_run / "out.cmix")
    screen_receipt["inputs"] = {
        "canonical": artifact(CANONICAL),
        "opening_input": artifact(input_path),
        "frozen_packaged_parent": artifact(BASE_PACKAGED),
        "head": artifact(HEAD),
        "observation_patch": artifact(PATCH),
    }
    screen_receipt["observer"] = {
        "binary": artifact(observer_binary),
        "packaged_binary": artifact(packaged_observer),
        "trace": artifact(trace_path),
        "native_payload_identity": payload_identity,
        "baseline_encode": baseline,
        "traced_encode": traced,
        "build": build_receipts,
        "package": package_receipts,
    }
    screen_receipt["program_accounting"] = {
        "source_package": source_package(),
    }
    decision = RESULT / "decision.json"
    decision.write_text(json.dumps(screen_receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "K0_gross_gain_bytes": screen_receipt["arms"]["K0"]["gross_gain_bytes"],
                "K0_paid_gain_before_source_bytes": screen_receipt["arms"]["K0"]["paid_gain_before_source_bytes"],
                "O0_gross_gain_bytes": screen_receipt["arms"]["O0"]["gross_gain_bytes"],
                "verdict": screen_receipt["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
