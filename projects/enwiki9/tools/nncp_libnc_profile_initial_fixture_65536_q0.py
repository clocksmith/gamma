#!/usr/bin/env python3
"""Materialize the exact block-zero NNCP state for the open MIDAS replay.

The external LibNC process is a zero-credit initialization oracle.  The
patched process exits before its first model forward, gradient, update, or
encoded symbol.  It retains only deterministic initial parameters, optimizer
state, recurrent memory, the first causal input/target batch, and the exact
65,536-symbol population consumed by the open candidate.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import lzma
import mmap
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
import tempfile
import time
from typing import Any, Iterable

from enwiki9_python_source_closure import local_source_closure


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_profile_initial_fixture_65536_q0_v1"
PARENT_ID = "nncp_libnc_profile_update_fixture_64_q3_v1"
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"
)
INTEGRATED_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    "nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/"
    "20260904T203102394482Z_cc0c7f3c292e.json"
)
OBJECTIVE_CONTRACT = ROOT / "contracts/research/v1/objective-contract.json"
OBJECTIVE_DIGEST = "sha256:ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8"
LIBNC_ROOT = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05")
PREPROCESSED = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "preprocessed.bin"
)
DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/"
    "dictionary.bin"
)
EXPECTED_EXTERNAL = {
    LIBNC_ROOT / "nncp.c":
        "9a44757c4837607b0be9abc0bb2780dbe006b381728549481eedc339599a138a",
    LIBNC_ROOT / "libnc.so":
        "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e",
    LIBNC_ROOT / "cmdopt.o":
        "07f1dafcffc4fac0f277017f7298b5ddeca93739453fc8bd7c9767cb7a231d39",
    LIBNC_ROOT / "cp_utils.o":
        "fd48a5599db170e2ac5f4ef9e3de6bfd1ee9946f33d47f3e8fc17367048d610d",
    LIBNC_ROOT / "arith.o":
        "d4e2560389e5955ad576269cd4987ec3702a5e376fd917548ac1ed50cdde20dc",
    LIBNC_ROOT / "preprocess.o":
        "6e846c1dfcec7a3e5d0f27c489f6e7d5c9581c98fcaa01fb8c5e90d779508ed4",
    LIBNC_ROOT / "cutils.o":
        "0513a31ad64187207bbba52e39d0fb3bf62461ad7008fdf0eae9e683e711a09e",
    PREPROCESSED:
        "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5",
    DICTIONARY:
        "950683b44e6c7696f6daa896296365eb54bce8cc05ae15fff7acb5715936a0a1",
}

SYMBOLS = 65_536
SYMBOL_BYTES = SYMBOLS * 2
STREAMS = 32
STATES = 64
STREAM_STRIDE = SYMBOLS // STREAMS
LAYERS = 20
MODEL = 1024
MEMORY = 256
HEADS = 8
HEAD_WIDTH = 128
INNER = 3072
POSITIONS = MEMORY + STATES
VOCABULARY = 16_392
PARAMETERS = 246
OPTIMIZER_TENSORS = 491
STATE_TENSORS = 22
EXPECTED_LEARNING_RATE = "0x1.4f8b58p-13"
SOURCE_CEILING = 2_000_000

TYPE_SIZES = {0: 4, 1: 2, 2: 2, 3: 1, 4: 2, 5: 4, 6: 1, 7: 2, 8: 4}


CAPTURE_HELPER = r'''
static void gamma_initial_fixture_path(char *path, size_t size,
                                       const char *name)
{
    const char *directory = getenv("NNCP_PROFILE_INITIAL_FIXTURE_DIR");
    if (!directory || !directory[0]) {
        fprintf(stderr, "NNCP_PROFILE_INITIAL_FIXTURE_DIR is required\n");
        abort();
    }
    snprintf(path, size, "%s/%s", directory, name);
}

static void gamma_save_initial_optimizer(TransformerModel *model)
{
    struct list_head *element;
    char path[4096];
    FILE *file;

    gamma_initial_fixture_path(path, sizeof(path), "optimizer_initial.params");
    file = fopen(path, "wb");
    if (!file) {
        perror(path);
        abort();
    }
    nc_save_param_header(file, "gamma.nncp.production.initial.optimizer.v1");
    list_for_each(element, &model->param_list.param_list) {
        NCParam *parameter = list_entry(element, NCParam, link);
        nc_save_param_opt(file, parameter);
    }
    if (fclose(file))
        abort();
}

static void gamma_save_initial_state(TransformerModel *model,
                                     const NCTensor *input,
                                     const NCTensor *expected)
{
    char path[4096], tensor_name[80];
    FILE *file;
    int layer;

    gamma_initial_fixture_path(path, sizeof(path), "state_initial.params");
    file = fopen(path, "wb");
    if (!file) {
        perror(path);
        abort();
    }
    nc_save_param_header(file, "gamma.nncp.production.initial.state.v1");
    nc_save_param(file, input, "input_all_streams");
    nc_save_param(file, expected, "target_all_streams");
    for (layer = 0; layer < model->n_layer; layer++) {
        snprintf(tensor_name, sizeof(tensor_name), "mem_h_%d", layer);
        nc_save_param(file, model->mem_h[layer], tensor_name);
    }
    if (fclose(file))
        abort();
}

static void gamma_capture_initial_fixture(NNCPModelState *state,
                                          NCTensor *input,
                                          NCTensor *expected,
                                          const DataSymbol *block_buf,
                                          int block_stride, int block_rem)
{
    TransformerModel *model = (TransformerModel *)state;
    char path[4096];
    FILE *file;
    float learning_rate;
    int stream_idx, cur_state, offset, symbol;

    if (model->n_layer != 20 || model->d_model != 1024 ||
        model->n_head != 8 || model->d_key != 128 ||
        model->d_value != 128 || model->d_inner != 3072 ||
        model->d_pos != 320 || model->mem_len != 256 ||
        model->train_len != 64 || model->n_symbols != 16392 ||
        model->n_streams != 32 || model->param_type != NC_TYPE_BF16 ||
        model->use_sparse_grad || state->train_step != 0 ||
        block_stride != 2048 || block_rem != 0) {
        fprintf(stderr, "production initial fixture geometry mismatch\n");
        abort();
    }

    for (cur_state = 0; cur_state < 64; cur_state++) {
        for (stream_idx = 0; stream_idx < 32; stream_idx++) {
            offset = block_stride * stream_idx + cur_state;
            symbol = cur_state == 0 ? 0 : block_buf[offset - 1];
            nc_set1_i32_2d(input, stream_idx, cur_state, symbol);
            nc_set1_i32_2d(expected, stream_idx, cur_state,
                           block_buf[offset]);
        }
    }

    gamma_initial_fixture_path(path, sizeof(path), "parameters_initial.coefs");
    nc_save_coefs(&model->param_list, path);
    gamma_save_initial_optimizer(model);
    gamma_save_initial_state(model, input, expected);
    learning_rate = get_interp_param(&state->lr, state->train_step);
    gamma_initial_fixture_path(path, sizeof(path), "boundary.txt");
    file = fopen(path, "w");
    if (!file)
        abort();
    fprintf(file,
            "block_idx=0\ntrain_step_before=%lld\nlearning_rate=%a\n"
            "forward_calls=0\ngradient_calls=0\nupdate_calls=0\n",
            (long long)state->train_step, learning_rate);
    if (fclose(file))
        abort();
    gamma_initial_fixture_path(path, sizeof(path), "complete.marker");
    file = fopen(path, "wb");
    if (!file || fwrite("COMPLETE\n", 1, 9, file) != 9 || fclose(file))
        abort();
    exit(0);
}

'''


@dataclass(frozen=True)
class TensorRecord:
    item_type: int
    dimensions: tuple[int, ...]
    offset: int
    byte_count: int


class TensorContainer:
    """Bounds-checked, duplicate-refusing reader for LibNC tensor files."""

    def __init__(self, path: Path):
        self.path = path
        self._file = path.open("rb")
        self._mapping = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        self.configuration = ""
        self.records: dict[str, TensorRecord] = {}
        self.order: list[str] = []
        try:
            self._parse()
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        if getattr(self, "_mapping", None) is not None:
            self._mapping.close()
            self._mapping = None
        if getattr(self, "_file", None) is not None:
            self._file.close()
            self._file = None

    def __enter__(self) -> TensorContainer:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _u32(self, offset: int) -> tuple[int, int]:
        if offset < 0 or offset + 4 > len(self._mapping):
            raise ValueError(f"truncated u32 in {self.path}")
        return struct.unpack_from("<I", self._mapping, offset)[0], offset + 4

    def _parse(self) -> None:
        if len(self._mapping) < 8:
            raise ValueError(f"truncated tensor container: {self.path}")
        offset = 0
        magic, offset = self._u32(offset)
        if magic != 0x23F4AEFB:
            raise ValueError(f"tensor container magic differs: {self.path}")
        config_size, offset = self._u32(offset)
        if config_size > len(self._mapping) - offset:
            raise ValueError(f"truncated tensor configuration: {self.path}")
        raw_configuration = self._mapping[offset : offset + config_size]
        if b"\0" in raw_configuration:
            raise ValueError(f"NUL in tensor configuration: {self.path}")
        self.configuration = raw_configuration.decode("utf-8")
        offset += config_size
        while offset < len(self._mapping):
            marker, offset = self._u32(offset)
            item_type, offset = self._u32(offset)
            rank, offset = self._u32(offset)
            name_size, offset = self._u32(offset)
            if marker != 0x23F4AEFA or item_type not in TYPE_SIZES:
                raise ValueError(f"invalid tensor header: {self.path}")
            if rank == 0 or rank > 8 or name_size == 0 or name_size > 4096:
                raise ValueError(f"invalid tensor rank or name size: {self.path}")
            dimensions: list[int] = []
            elements = 1
            for _ in range(rank):
                dimension, offset = self._u32(offset)
                if dimension == 0 or elements > (1 << 63) // dimension:
                    raise ValueError(f"invalid tensor dimensions: {self.path}")
                dimensions.append(dimension)
                elements *= dimension
            if name_size > len(self._mapping) - offset:
                raise ValueError(f"truncated tensor name: {self.path}")
            raw_name = self._mapping[offset : offset + name_size]
            if b"\0" in raw_name:
                raise ValueError(f"NUL in tensor name: {self.path}")
            name = raw_name.decode("utf-8")
            offset += name_size
            byte_count = elements * TYPE_SIZES[item_type]
            if byte_count > len(self._mapping) - offset or name in self.records:
                raise ValueError(f"invalid tensor payload or duplicate: {name}")
            self.records[name] = TensorRecord(
                item_type, tuple(dimensions), offset, byte_count
            )
            self.order.append(name)
            offset += byte_count
        if offset != len(self._mapping):
            raise ValueError(f"tensor container has trailing bytes: {self.path}")

    def payload(self, name: str) -> bytes:
        try:
            record = self.records[name]
        except KeyError as error:
            raise ValueError(f"missing tensor {name} in {self.path}") from error
        return self._mapping[record.offset : record.offset + record.byte_count]

    def payload_is_zero(self, name: str) -> bool:
        record = self.records[name]
        start = record.offset
        stop = start + record.byte_count
        chunk = 8 * 1024 * 1024
        return all(
            not any(self._mapping[offset : min(offset + chunk, stop)])
            for offset in range(start, stop, chunk)
        )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"reference is not a project file: {path}")
    result = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        result["id"] = identifier
    return result


def objective_binding() -> dict[str, Any]:
    objective = json.loads(OBJECTIVE_CONTRACT.read_text())
    canonical = json.dumps(
        objective, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    digest = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
    if (
        digest != OBJECTIVE_DIGEST
        or objective.get("objectiveId") != "gamma-enwiki9-hutter-105m-v1"
        or objective.get("status") != "active"
        or objective.get("score", {}).get("targetBytes") != 105_000_000
        or objective.get("corpus", {}).get("bytes") != 1_000_000_000
        or objective.get("corpus", {}).get("sha256")
        != "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"
    ):
        raise ValueError("objective contract binding differs")
    return {
        "objectiveId": objective["objectiveId"],
        "objectiveDigest": digest,
        "objectivePath": "contracts/research/v1/objective-contract.json",
        "targetScoreBytes": objective["score"]["targetBytes"],
        "corpusBytes": objective["corpus"]["bytes"],
        "corpusSha256": objective["corpus"]["sha256"],
    }


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"expected one teacher patch marker, found {count}")
    return source.replace(old, new, 1)


def patch_teacher(source: str) -> str:
    source = replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        CAPTURE_HELPER + "static FILE *teacher_trace_file;\n",
    )
    return replace_once(
        source,
        "    s->model_class->model_reset(s);\n    \n    /* normal batches */",
        "    s->model_class->model_reset(s);\n"
        "    gamma_capture_initial_fixture(s, input, expected_output, block_buf,\n"
        "                                  block_stride, block_rem);\n"
        "    \n"
        "    /* normal batches */",
    )


def run(command: list[str], **kwargs: Any) -> tuple[subprocess.CompletedProcess[bytes], dict[str, Any]]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        **kwargs,
    )
    receipt = {
        "command": command,
        "elapsedSeconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderrSha256": hashlib.sha256(completed.stderr).hexdigest(),
    }
    if completed.returncode != 0:
        receipt["stderrTail"] = completed.stderr[-4096:].decode(errors="replace")
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return completed, receipt


def compile_oracle(scratch: Path) -> tuple[Path, dict[str, Any]]:
    compiler_name = os.environ.get("CC", "cc")
    compiler_lookup = shutil.which(compiler_name)
    if compiler_lookup is None:
        raise FileNotFoundError(f"compiler not found: {compiler_name}")
    compiler = Path(compiler_lookup).resolve()
    if not compiler.is_file():
        raise ValueError("resolved compiler is not a regular file")
    patched = scratch / "nncp_profile_initial_fixture.c"
    patched.write_text(patch_teacher((LIBNC_ROOT / "nncp.c").read_text()))
    obj = scratch / "nncp_profile_initial_fixture.o"
    executable = scratch / "nncp_profile_initial_fixture"
    commands = [
        [
            str(compiler), "-O3", "-Wall", "-Wpointer-arith", "-g",
            "-fno-math-errno", "-fno-trapping-math",
            '-DCONFIG_VERSION="2024-06-05"', "-DLIBNC_CONFIG_FULL",
            f"-I{LIBNC_ROOT}", "-c", str(patched), "-o", str(obj),
        ],
        [
            str(compiler), f"-Wl,-rpath,{LIBNC_ROOT}", "-o", str(executable),
            str(obj),
            *[
                str(LIBNC_ROOT / name)
                for name in ("cmdopt.o", "cp_utils.o", "arith.o", "preprocess.o", "cutils.o")
            ],
            str(LIBNC_ROOT / "libnc.so"), "-lz", "-lm", "-lpthread",
        ],
    ]
    receipts = []
    for command in commands:
        _, receipt = run(command)
        receipts.append(receipt)
    _, version = run([str(compiler), "--version"])
    linked, linked_receipt = run(["ldd", str(executable)])
    linked_receipt["stdout"] = linked.stdout.decode(errors="strict")
    return executable, {
        "compilerPath": str(compiler),
        "compilerSha256": sha256(compiler),
        "commands": receipts,
        "compilerVersion": version,
        "linkedDependencies": linked_receipt,
        "patchedSourceSha256": sha256(patched),
        "executableSha256": sha256(executable),
    }


def write_symbol_population(path: Path) -> list[int]:
    if path.exists():
        raise FileExistsError(path)
    with PREPROCESSED.open("rb") as source, path.open("xb") as output:
        remaining = SYMBOL_BYTES
        payload = bytearray()
        while remaining:
            chunk = source.read(min(1 << 20, remaining))
            if not chunk:
                raise ValueError("preprocessed population is truncated")
            output.write(chunk)
            payload.extend(chunk)
            remaining -= len(chunk)
    if len(payload) != SYMBOL_BYTES:
        raise ValueError("symbol population byte count differs")
    symbols = [value[0] for value in struct.iter_unpack(">H", payload)]
    if len(symbols) != SYMBOLS or any(value >= VOCABULARY for value in symbols):
        raise ValueError("symbol population geometry or vocabulary differs")
    return symbols


def expected_parameter_layout() -> dict[str, tuple[int, tuple[int, ...]]]:
    expected: dict[str, tuple[int, tuple[int, ...]]] = {
        "b_r_0": (1, (POSITIONS, HEADS)),
    }
    for layer in range(LAYERS):
        expected.update({
            f"w_r_{layer}": (1, (HEAD_WIDTH, POSITIONS, HEADS)),
            f"w_q_{layer}": (1, (MODEL, MODEL)),
            f"w_kv_{layer}": (1, (2 * MODEL, MODEL)),
            f"w_o_{layer}": (1, (MODEL, MODEL)),
            f"ff1_{layer}": (1, (2 * INNER, MODEL)),
            f"ff_bias1_{layer}": (1, (2 * INNER,)),
            f"ff2_{layer}": (1, (MODEL, INNER)),
            f"ff_bias2_{layer}": (1, (MODEL,)),
            f"ln_g_{2 * layer}": (1, (MODEL,)),
            f"ln_b_{2 * layer}": (1, (MODEL,)),
            f"ln_g_{2 * layer + 1}": (1, (MODEL,)),
            f"ln_b_{2 * layer + 1}": (1, (MODEL,)),
        })
    expected.update({
        f"ln_g_{2 * LAYERS}": (1, (MODEL,)),
        f"ln_b_{2 * LAYERS}": (1, (MODEL,)),
        "embed": (0, (MODEL, VOCABULARY)),
        "embed_out": (1, (VOCABULARY, MODEL)),
        "out_bias": (1, (VOCABULARY,)),
    })
    if len(expected) != PARAMETERS:
        raise AssertionError("internal parameter topology differs")
    return expected


def require_layout(
    container: TensorContainer,
    expected: dict[str, tuple[int, tuple[int, ...]]],
    label: str,
) -> None:
    if len(container.records) != len(expected) or set(container.records) != set(expected):
        raise ValueError(f"{label} tensor population differs")
    for name, (item_type, dimensions) in expected.items():
        observed = container.records[name]
        if observed.item_type != item_type or observed.dimensions != dimensions:
            raise ValueError(f"{label} tensor geometry differs: {name}")


def validate_fixture(directory: Path, symbols: list[int]) -> dict[str, Any]:
    required = {
        "parameters_initial.coefs",
        "optimizer_initial.params",
        "state_initial.params",
        "symbols_65536.be16",
        "boundary.txt",
        "complete.marker",
    }
    root_files = {path.name for path in directory.iterdir() if path.is_file()}
    if root_files != required:
        raise ValueError("initial fixture output closure differs")
    if (directory / "complete.marker").read_bytes() != b"COMPLETE\n":
        raise ValueError("initial fixture completion marker differs")
    boundary_lines = (directory / "boundary.txt").read_text().splitlines()
    if any("=" not in line for line in boundary_lines):
        raise ValueError("initial fixture boundary is malformed")
    boundary = dict(line.split("=", 1) for line in boundary_lines)
    expected_boundary = {
        "block_idx": "0",
        "train_step_before": "0",
        "learning_rate": EXPECTED_LEARNING_RATE,
        "forward_calls": "0",
        "gradient_calls": "0",
        "update_calls": "0",
    }
    if boundary != expected_boundary:
        raise ValueError(f"initial fixture boundary differs: {boundary}")

    parameter_layout = expected_parameter_layout()
    optimizer_layout: dict[str, tuple[int, tuple[int, ...]]] = {}
    for name, (item_type, dimensions) in parameter_layout.items():
        optimizer_layout[f"{name}.grad_v"] = (item_type, dimensions)
        if item_type == 1:
            optimizer_layout[f"{name}.low"] = (7, dimensions)
    if len(optimizer_layout) != OPTIMIZER_TENSORS:
        raise AssertionError("internal optimizer topology differs")
    state_layout = {
        "input_all_streams": (5, (STREAMS, STATES)),
        "target_all_streams": (5, (STREAMS, STATES)),
        **{
            f"mem_h_{layer}": (1, (MODEL, STREAMS, MEMORY))
            for layer in range(LAYERS)
        },
    }

    with TensorContainer(directory / "parameters_initial.coefs") as parameters:
        if parameters.configuration != "{}":
            raise ValueError("initial parameter configuration differs")
        require_layout(parameters, parameter_layout, "initial parameter")
    with TensorContainer(directory / "optimizer_initial.params") as optimizer:
        if optimizer.configuration != "gamma.nncp.production.initial.optimizer.v1":
            raise ValueError("initial optimizer configuration differs")
        require_layout(optimizer, optimizer_layout, "initial optimizer")
    with TensorContainer(directory / "state_initial.params") as state:
        if state.configuration != "gamma.nncp.production.initial.state.v1":
            raise ValueError("initial state configuration differs")
        require_layout(state, state_layout, "initial state")
        expected_targets: list[int] = []
        expected_inputs: list[int] = []
        for state_index in range(STATES):
            for stream in range(STREAMS):
                original = stream * STREAM_STRIDE + state_index
                expected_targets.append(symbols[original])
                expected_inputs.append(0 if state_index == 0 else symbols[original - 1])
        observed_inputs = [
            value[0]
            for value in struct.iter_unpack("<I", state.payload("input_all_streams"))
        ]
        observed_targets = [
            value[0]
            for value in struct.iter_unpack("<I", state.payload("target_all_streams"))
        ]
        if observed_inputs != expected_inputs or observed_targets != expected_targets:
            raise ValueError("initial state does not match symbol population batch zero")
        memory_zero = all(
            state.payload_is_zero(f"mem_h_{layer}") for layer in range(LAYERS)
        )
        if not memory_zero:
            raise ValueError("block-zero recurrent memory is not canonical zero")
    return {
        "parameterTensorCount": len(parameter_layout),
        "optimizerTensorCount": len(optimizer_layout),
        "stateTensorCount": len(state_layout),
        "activationTensorCount": sum(name.startswith("train_h_") for name in state_layout),
        "batchZeroMappingExact": True,
        "initialMemoryAllZero": True,
        "learningRateExact": True,
        "preForwardBoundary": True,
    }


def directory_manifest(directory: Path) -> dict[str, Any]:
    files = []
    aggregate = hashlib.sha256()
    for path in sorted(item for item in directory.iterdir() if item.is_file()):
        relative = path.name
        file_hash = sha256(path)
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": file_hash})
        aggregate.update(relative.encode() + b"\0" + bytes.fromhex(file_hash))
    return {
        "files": files,
        "fileCount": len(files),
        "totalBytes": sum(row["bytes"] for row in files),
        "aggregateSha256": aggregate.hexdigest(),
    }


def capture(executable: Path, directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    directory.mkdir()
    symbols = write_symbol_population(directory / "symbols_65536.be16")
    archive = directory.parent / f"{directory.name}.partial.nncp"
    if archive.exists():
        raise FileExistsError(archive)
    environment = dict(os.environ)
    environment.update({
        "LD_LIBRARY_PATH": str(LIBNC_ROOT),
        "NNCP_PROFILE_INITIAL_FIXTURE_DIR": str(directory),
    })
    command = [
        str(executable), "-q", "-T", "4", "--profile", "enwik9",
        "--seed", "123", "--n_symb", str(VOCABULARY),
        "--dict", str(DICTIONARY), "--max_size", str(SYMBOLS),
        "c", str(PREPROCESSED), str(archive),
    ]
    _, execution = run(command, env=environment, cwd=directory.parent)
    execution.update({
        "partialArchiveBytes": archive.stat().st_size if archive.exists() else 0,
        "partialArchiveSha256": sha256(archive) if archive.exists() else None,
    })
    archive.unlink(missing_ok=True)
    validation = validate_fixture(directory, symbols)
    return execution, validation


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = sorted(
        {*local_source_closure((Path(__file__),)), OBJECTIVE_CONTRACT.resolve()},
        key=lambda item: item.relative_to(ROOT).as_posix(),
    )
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        record = declared.get(relative, {})
        if record != reference(member, record.get("id")):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    with path.open("xb") as output:
        output.write(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > SOURCE_CEILING:
        raise ValueError("source closure exceeds the frozen package ceiling")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    required = (
        ("q3-decision", PARENT_DECISION),
        ("q3-reflection", PARENT_REFLECTION),
        ("integrated-revision", INTEGRATED_REVISION),
        ("objective-contract", OBJECTIVE_CONTRACT),
    )
    for identifier, path in required:
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    if not (
        parent.get("promotionPass") is True
        and parent.get("decision") == "authorize-successor"
        and parent.get("measurements", {}).get("fixtureRepeatByteIdentical") is True
        and parent.get("measurements", {}).get("parameterPopulation") == PARAMETERS
    ):
        raise ValueError("q3 fixture parent does not authorize initialization reuse")
    reflection = json.loads(PARENT_REFLECTION.read_text())
    if not (
        reflection.get("validity", {}).get("valid") is True
        and reflection.get("decision", {}).get("verdict") == "promote"
    ):
        raise ValueError("q3 fixture reflection is not a valid promotion")
    integrated = json.loads(INTEGRATED_REVISION.read_text())
    if not (
        integrated.get("candidateId")
        == "nncp_open_integrated_midpoint_segment_replay_65536_q0_v2"
        and integrated.get("candidateTreeSha256")
        == "sha256:cc0c7f3c292ee97eac4acea145fb5086247411bcc08f098980c7c312e4fb8789"
    ):
        raise ValueError("integrated MIDAS consumer revision differs")


def evaluate(
    predicates: Iterable[dict[str, Any]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, Any]]:
    operators = {
        "eq": lambda value, threshold: value == threshold,
        "gt": lambda value, threshold: value > threshold,
        "gte": lambda value, threshold: value >= threshold,
        "lt": lambda value, threshold: value < threshold,
        "lte": lambda value, threshold: value <= threshold,
    }
    rows = []
    for predicate in predicates:
        observed = measurements[predicate["measurement"]]
        passed = operators[predicate["operator"]](observed, predicate["threshold"])
        rows.append({**predicate, "observed": observed, "passed": bool(passed)})
    return rows


def run_self_test() -> int:
    marker = "static FILE *teacher_trace_file;\n"
    reset = "    s->model_class->model_reset(s);\n    \n    /* normal batches */"
    patched = patch_teacher(marker + reset)
    if patched.count("gamma_capture_initial_fixture") != 2:
        raise AssertionError("initial capture helper/call population differs")
    if patched.index("gamma_capture_initial_fixture(s") > patched.index("/* normal batches */"):
        raise AssertionError("initial capture is not before the first forward loop")
    if "train_h" in CAPTURE_HELPER or "model_eval_gradient" in CAPTURE_HELPER:
        raise AssertionError("forbidden teacher activation or gradient entered capture helper")
    try:
        patch_teacher(marker + marker + reset)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate patch marker was accepted")
    if len(expected_parameter_layout()) != PARAMETERS:
        raise AssertionError("parameter topology self-test differs")
    with tempfile.TemporaryDirectory(prefix="nncp-initial-fixture-selftest-") as raw:
        path = Path(raw) / "tiny.params"
        payload = bytearray(struct.pack("<II", 0x23F4AEFB, 4) + b"test")
        payload.extend(struct.pack("<IIII", 0x23F4AEFA, 5, 1, 1))
        payload.extend(struct.pack("<I", 2) + b"x" + struct.pack("<II", 7, 9))
        path.write_bytes(payload)
        with TensorContainer(path) as container:
            if container.configuration != "test" or container.payload("x") != struct.pack("<II", 7, 9):
                raise AssertionError("tensor parser self-test differs")
    print("NNCP_PROFILE_INITIAL_FIXTURE_SELFTEST_OK")
    return 0


def production_main(experiment_path: Path, output: Path) -> int:
    experiment_path = experiment_path.resolve()
    output = output.resolve()
    experiment = json.loads(experiment_path.read_text())
    if (
        experiment.get("schema")
        != "gamma.enwiki9.adaptive-experiment-contract.v1"
        or experiment.get("status") != "frozen"
        or experiment.get("registrationTiming") != "prospective"
        or experiment.get("evidenceClass") != "oracle"
        or experiment.get("objectiveCreditBytes") != 0
        or experiment.get("objective") != objective_binding()
        or experiment.get("experimentId") != CANDIDATE_ID
        or experiment.get("proposalId") != CANDIDATE_ID
    ):
        raise ValueError("experiment identifies another candidate")
    job_binding = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    if reference(experiment_path) != job_binding:
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision.get("candidateId") != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    for path, expected in EXPECTED_EXTERNAL.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen external input identity mismatch: {path}")
    result_root = (ROOT / "results" / CANDIDATE_ID).resolve()
    if output.parent != result_root or output.exists():
        raise ValueError("decision output is outside a fresh candidate result boundary")
    for relative in experiment["outputs"]:
        path = (ROOT / relative).resolve()
        if path.parent != result_root or path.exists():
            raise ValueError(f"output is outside a fresh result boundary: {relative}")

    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = output.parent / "scratch"
    scratch.mkdir()
    executable, build = compile_oracle(scratch)
    fixture = output.parent / "fixture"
    repeat = output.parent / "fixture-repeat"
    first_execution, first_validation = capture(executable, fixture)
    second_execution, second_validation = capture(executable, repeat)
    first_manifest = directory_manifest(fixture)
    repeat_manifest = directory_manifest(repeat)
    repeat_identical = first_manifest["aggregateSha256"] == repeat_manifest["aggregateSha256"]
    if first_validation != second_validation:
        raise ValueError("independent fixture validations differ")
    shutil.rmtree(repeat)
    shutil.rmtree(scratch)

    manifest_path = output.parent / "fixture-manifest.json"
    manifest = {
        "schema": "gamma.nncp.production-profile-initial-fixture.v1",
        "epistemicTier": "zero-credit-libnc-initialization-oracle",
        "candidateId": CANDIDATE_ID,
        "externalInputs": {str(path): value for path, value in EXPECTED_EXTERNAL.items()},
        "build": build,
        "executions": [first_execution, second_execution],
        "validation": first_validation,
        "fixture": first_manifest,
        "repeatFixture": repeat_manifest,
        "rawFixturePath": fixture.relative_to(ROOT).as_posix(),
        "rawFixtureRetainedLocal": True,
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    execution_path = output.parent / "execution.json"
    execution_path.write_text(
        json.dumps(
            {"build": build, "runs": [first_execution, second_execution]},
            indent=2,
            sort_keys=True,
        ) + "\n"
    )
    package = output.parent / "incremental_source.tar.xz"
    source_package(package, experiment)

    measurements: dict[str, bool | int | float] = {
        "parentPass": True,
        "integratedRevisionBound": True,
        "externalInputsBound": True,
        "capturePatchUnique": True,
        "fixtureComplete": first_manifest["fileCount"] == 6,
        "fixtureRepeatByteIdentical": repeat_identical,
        "parameterTensorCount": int(first_validation["parameterTensorCount"]),
        "optimizerTensorCount": int(first_validation["optimizerTensorCount"]),
        "stateTensorCount": int(first_validation["stateTensorCount"]),
        "activationTensorCount": int(first_validation["activationTensorCount"]),
        "batchZeroMappingExact": bool(first_validation["batchZeroMappingExact"]),
        "initialMemoryAllZero": bool(first_validation["initialMemoryAllZero"]),
        "learningRateExact": bool(first_validation["learningRateExact"]),
        "preForwardBoundary": bool(first_validation["preForwardBoundary"]),
        "populationSymbols": SYMBOLS,
        "symbolBytes": SYMBOL_BYTES,
        "streamPopulation": STREAMS,
        "streamStride": STREAM_STRIDE,
        "segmentPopulation": STATES,
        "layerPopulation": LAYERS,
        "trainStepBefore": 0,
        "targetBlock": 0,
        "fixtureBytes": int(first_manifest["totalBytes"]),
        "sourceClosureBytes": package.stat().st_size,
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": candidate_revision,
        "evidenceClass": experiment["evidenceClass"],
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": (
            "authorize-integrated-replay" if promotion_pass
            else "retire-fixture-law" if kill_pass
            else "retry-infrastructure"
        ),
        "artifacts": [
            reference(manifest_path, "fixture-manifest"),
            reference(execution_path, "execution"),
            reference(package, "source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if promotion_pass else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.experiment is not None or args.output is not None:
            parser.error("--self-test cannot be combined with production arguments")
        return run_self_test()
    if args.experiment is None or args.output is None:
        parser.error("--experiment and --output are required")
    return production_main(args.experiment, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
