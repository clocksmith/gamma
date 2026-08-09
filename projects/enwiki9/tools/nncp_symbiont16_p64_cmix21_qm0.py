#!/usr/bin/env python3
"""Run the frozen SYMBIONT-16 I16/P64/P64R same-backend screen."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
import pathlib
import stat
import subprocess
import tempfile
import time


ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATE = "nncp_symbiont16_p64_cmix21_qm0_v1"
PROGRAM_DIR = ROOT / "programs" / CANDIDATE
RESULT_DIR = ROOT / "results" / CANDIDATE
SYMBOL_PATH = pathlib.Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin"
)
SYMBOL_FILE_SIZE = 401_217_922
SYMBOL_FILE_SHA256 = "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5"
CMIX_GZ_SHA256 = "7cfb71c21b6eccf3eeb6fb11df7e00024c37cdcd46730724c61c046bcc0596df"
SYMBOL_COUNT = 1_048_576
BLOCK_SYMBOLS = 64
RATE_GATE = 4.30


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_program():
    path = PROGRAM_DIR / "program.py"
    spec = importlib.util.spec_from_file_location("symbiont_program", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rotate_low_planes(planes: bytes) -> bytes:
    if len(planes) % (2 * BLOCK_SYMBOLS):
        raise ValueError("P64R population must contain complete 64-symbol blocks")
    blocks = [planes[pos : pos + 128] for pos in range(0, len(planes), 128)]
    output = bytearray(len(planes))
    for index, block in enumerate(blocks):
        high = block[:64]
        next_low = blocks[(index + 1) % len(blocks)][64:]
        start = index * 128
        output[start : start + 64] = high
        output[start + 64 : start + 128] = next_low
    return bytes(output)


def unrotate_low_planes(rotated: bytes) -> bytes:
    if len(rotated) % (2 * BLOCK_SYMBOLS):
        raise ValueError("P64R population must contain complete 64-symbol blocks")
    blocks = [rotated[pos : pos + 128] for pos in range(0, len(rotated), 128)]
    output = bytearray(len(rotated))
    for index, block in enumerate(blocks):
        start = index * 128
        output[start : start + 64] = block[:64]
        previous = blocks[(index - 1) % len(blocks)]
        output[start + 64 : start + 128] = previous[64:]
    return bytes(output)


def emit(event: str, **fields: object) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def run_cmix(binary: pathlib.Path, mode: str, source: bytes, arm: str, run: int) -> tuple[bytes, float]:
    with tempfile.TemporaryDirectory(prefix=f"symbiont-{arm}-{run}-") as raw:
        work = pathlib.Path(raw)
        source_path = work / "in"
        output_path = work / "out"
        source_path.write_bytes(source)
        env = os.environ.copy()
        env["CMIX_MMAP_ALLOC"] = "1"
        env["CMIX_MMAP_DIR"] = str(work)
        command = [str(binary), mode, str(source_path), str(output_path)]
        emit("cmix_start", arm=arm, run=run, mode=mode)
        started = time.monotonic()
        subprocess.run(
            command,
            cwd=work,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        elapsed = time.monotonic() - started
        output = output_path.read_bytes()
        emit("cmix_done", arm=arm, run=run, mode=mode, size=len(output), elapsed_seconds=elapsed)
        return output, elapsed


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    if SYMBOL_PATH.stat().st_size != SYMBOL_FILE_SIZE:
        raise RuntimeError("receipt-bound NNCP symbol file size mismatch")
    if sha256_file(SYMBOL_PATH) != SYMBOL_FILE_SHA256:
        raise RuntimeError("receipt-bound NNCP symbol file hash mismatch")
    cmix_gz = PROGRAM_DIR / "cmix.bin.gz"
    if sha256_file(cmix_gz) != CMIX_GZ_SHA256:
        raise RuntimeError("cmix backend hash mismatch")

    symbol_bytes = SYMBOL_PATH.read_bytes()[: 2 * SYMBOL_COUNT]
    program = load_program()
    p64 = program._plane64(symbol_bytes)
    p64r = rotate_low_planes(p64)
    if program._unplane64(p64) != symbol_bytes:
        raise RuntimeError("P64 local inverse mismatch")
    if program._unplane64(unrotate_low_planes(p64r)) != symbol_bytes:
        raise RuntimeError("P64R local inverse mismatch")

    with tempfile.TemporaryDirectory(prefix="symbiont-cmix-bin-") as raw:
        binary = pathlib.Path(raw) / "cmix"
        with gzip.open(cmix_gz, "rb") as source, binary.open("wb") as output:
            output.write(source.read())
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

        layouts = {"I16": symbol_bytes, "P64": p64, "P64R": p64r}
        archives: dict[str, bytes] = {}
        encode_seconds: dict[str, float] = {}
        for arm in ("I16", "P64", "P64R"):
            archives[arm], encode_seconds[arm] = run_cmix(binary, "-n", layouts[arm], arm, 1)
        p64_repeat, repeat_seconds = run_cmix(binary, "-n", p64, "P64", 2)
        deterministic = p64_repeat == archives["P64"]

        decoded_ok: dict[str, bool] = {}
        decode_seconds: dict[str, float] = {}
        for arm in ("I16", "P64", "P64R"):
            decoded, decode_seconds[arm] = run_cmix(binary, "-d", archives[arm], arm, 1)
            decoded_ok[arm] = decoded == layouts[arm]

    archive_sizes = {arm: len(data) for arm, data in archives.items()}
    bits_per_symbol = {
        arm: archive_sizes[arm] * 8.0 / SYMBOL_COUNT for arm in archive_sizes
    }
    inverse_ok = all(decoded_ok.values())
    control_order_ok = archive_sizes["P64"] < archive_sizes["I16"] and archive_sizes["P64"] < archive_sizes["P64R"]
    rate_ok = bits_per_symbol["P64"] <= RATE_GATE
    authorized = deterministic and inverse_ok and control_order_ok and rate_ok
    status = "AUTHORIZED_NATIVE_CMIX16" if authorized else "RETIRED_LAYOUT_CROSSING"
    receipt = {
        "schema": "nncp_symbiont16_p64_cmix21_qm0_decision_v1",
        "candidate_id": CANDIDATE,
        "status": status,
        "score_credit_bytes": 0,
        "population": {
            "symbol_count": SYMBOL_COUNT,
            "serialized_bytes": len(symbol_bytes),
            "source_path": str(SYMBOL_PATH),
            "source_file_size": SYMBOL_FILE_SIZE,
            "source_file_sha256": SYMBOL_FILE_SHA256,
            "population_sha256": sha256_bytes(symbol_bytes),
            "block_symbols": BLOCK_SYMBOLS,
        },
        "backend": {
            "mode": "-n",
            "compressed_binary_sha256": CMIX_GZ_SHA256,
        },
        "arms": {
            arm: {
                "archive_size": archive_sizes[arm],
                "archive_sha256": sha256_bytes(archives[arm]),
                "bits_per_symbol": bits_per_symbol[arm],
                "encode_seconds": encode_seconds[arm],
                "decode_seconds": decode_seconds[arm],
                "decoded_layout_exact": decoded_ok[arm],
            }
            for arm in ("I16", "P64", "P64R")
        },
        "p64_repeat": {
            "archive_size": len(p64_repeat),
            "archive_sha256": sha256_bytes(p64_repeat),
            "encode_seconds": repeat_seconds,
            "byte_identical": deterministic,
        },
        "gates": {
            "p64_rate_max_bits_per_symbol": RATE_GATE,
            "rate_ok": rate_ok,
            "p64_strictly_beats_i16_and_p64r": control_order_ok,
            "all_decoded_layouts_exact": inverse_ok,
            "p64_deterministic": deterministic,
            "memory_guard_external": True,
        },
        "decision": (
            "Authorize exactly one native CMIX16 branch-tree design; no byte-layout sweep."
            if authorized
            else "Retire NNCP byte-layout crossing; no endian, block, plane-width, or backend sweep."
        ),
    }
    decision_path = RESULT_DIR / "decision.json"
    decision_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    emit("decision", status=status, decision_path=str(decision_path), arms=receipt["arms"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
