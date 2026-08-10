#!/usr/bin/env python3
"""Build the frozen production NNCP forward fixture and open parity gate.

The LibNC execution in this file is a zero-credit oracle.  It advances the
exact passing 65,536-symbol parent trajectory to stream 0's first segment with
a completely populated 256-symbol memory, exports that pre-forward state, and
terminates after the selected forward probabilities and truth paths are bound.
The final parity executable is built independently from the counted GGML source
closure and has no LibNC runtime dependency.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import nncp_ggml_open_cpu_kernel_closure_qm0 as common
import numpy as np


CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm0_v1"
ROOT = common.ROOT
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
LIBNC_ROOT = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05")
PREPROCESSED = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin"
)
DICTIONARY = Path(
    "/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/dictionary.bin"
)
EXPORTER_SOURCE = ROOT / "tools/nncp_libnc_export.c"
HOOK_SOURCE = ROOT / "tools/nncp_production_fixture_hook.c"
BRIDGE_DECISION = (
    ROOT
    / "results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/decision.json"
)

EXPECTED = {
    LIBNC_ROOT / "nncp.c": "9a44757c26fba57bcbd854e50201deef53c85fd86a3bb142a198d518144a138a",
    LIBNC_ROOT / "libnc.so": "1836cdfd7b42ca49efec6421cfce8a7728e8b7d9f3fcd193094c27a38af36d3e",
    PREPROCESSED: "c82bfca1cb00f04ab17603ba9d40def7a0e71fc0db1f018a4282dbe501d60a5",
    DICTIONARY: "950683b4d0ab597f2e4f877f221c54f22564596b85f05d2ae0ee968858cda0a1",
    BRIDGE_DECISION: "74f7c9ab5057d2e51f314012cb9be10d04ea49171f4875741b072404230e4d8",
}

PROFILE = {
    "layers": 20,
    "d_model": 1024,
    "heads": 8,
    "d_key": 128,
    "d_value": 128,
    "d_inner": 3072,
    "mem_len": 256,
    "segment": 64,
    "d_pos": 320,
    "vocabulary": 16392,
    "batch_size": 32,
    "seed": 123,
    "parameter_type": "BF16",
    "target_stream": 0,
    "target_block_position": 256,
    "target_original_symbol_start": 256,
    "target_original_symbol_end": 320,
}
SOURCE_CEILING = 2_000_000
TOLERANCE = 1.0e-5


CAPTURE_HELPER = r'''
static int gamma_fixture_active;
static FILE *gamma_branch_file;

static void gamma_put_le32(FILE *file, uint32_t value)
{
    int index;
    for (index = 0; index < 4; index++)
        fputc((value >> (8 * index)) & 255, file);
}

static void gamma_fixture_path(char *path, size_t size, const char *name)
{
    const char *directory = getenv("NNCP_PRODUCTION_FIXTURE_DIR");
    if (!directory || !directory[0]) {
        fprintf(stderr, "NNCP_PRODUCTION_FIXTURE_DIR is required\n");
        abort();
    }
    snprintf(path, size, "%s/%s", directory, name);
}

static void gamma_dump_layer_tensor(int layer, const char *name,
                                    const NCTensor *tensor)
{
    char label[128];
    snprintf(label, sizeof(label), "layer_%02d_%s", layer, name);
    nc_dump_tensor_hash(label, tensor);
}

static void gamma_fixture_begin(NNCPModelState *state, const NCTensor *input,
                                DataSymbol *block_buf, int block_stride,
                                int block_rem, int block_idx)
{
    TransformerModel *model = (TransformerModel *)state;
    char path[4096], name[80];
    FILE *file;
    NCTensor *selected;
    int layer, position, symbol;

    if (block_idx != 256 || gamma_fixture_active)
        return;
    if (model->n_layer != 20 || model->d_model != 1024 ||
        model->n_head != 8 || model->d_key != 128 ||
        model->d_value != 128 || model->d_inner != 3072 ||
        model->d_pos != 320 || model->mem_len != 256 ||
        model->train_len != 64 || model->n_symbols != 16392 ||
        model->n_streams != 32 || model->param_type != NC_TYPE_BF16) {
        fprintf(stderr, "production fixture geometry mismatch\n");
        abort();
    }

    gamma_fixture_path(path, sizeof(path), "parameters.coefs");
    nc_save_coefs(&model->param_list, path);
    gamma_fixture_path(path, sizeof(path), "state.params");
    file = fopen(path, "wb");
    if (!file) {
        perror(path);
        abort();
    }
    nc_save_param_header(file, "gamma.nncp.production.forward.fixture.v1");
    selected = nc_slice(nc_dup_tensor(input), 0, 0, 1);
    nc_save_param(file, selected, "input_stream_0");
    nc_free_tensor(selected);
    for (layer = 0; layer < model->n_layer; layer++) {
        selected = nc_slice(nc_dup_tensor(model->mem_h[layer]), 1, 0, 1);
        snprintf(name, sizeof(name), "mem_h_%d_stream_0", layer);
        nc_save_param(file, selected, name);
        nc_free_tensor(selected);
    }
    nc_save_param(file, model->layers[0].attn_mask, "attention_mask");
    if (fclose(file)) {
        perror("state.params close");
        abort();
    }

    gamma_fixture_path(path, sizeof(path), "target_symbols.u16le");
    file = fopen(path, "wb");
    if (!file) {
        perror(path);
        abort();
    }
    for (position = 0; position < 64; position++) {
        symbol = get_symb(block_buf, block_stride, block_rem, 0,
                          block_idx + position);
        fputc(symbol & 255, file);
        fputc((symbol >> 8) & 255, file);
    }
    if (fclose(file)) {
        perror("target_symbols close");
        abort();
    }

    gamma_fixture_path(path, sizeof(path), "tree_path.u32le");
    gamma_branch_file = fopen(path, "wb");
    if (!gamma_branch_file) {
        perror(path);
        abort();
    }
    fwrite("NNPTREE1", 1, 8, gamma_branch_file);
    gamma_put_le32(gamma_branch_file, 64);
    gamma_put_le32(gamma_branch_file, 16392);

    gamma_fixture_path(path, sizeof(path), "capture.marker");
    file = fopen(path, "wb");
    if (!file || fwrite("ACTIVE\n", 1, 7, file) != 7 || fclose(file)) {
        perror(path);
        abort();
    }
    gamma_fixture_active = 1;
}

static void gamma_dump_tree_path(const float *prob_table, int n_symbols,
                                 int symbol, uint32_t local_position,
                                 uint16_t stream_index)
{
    int start, range, range0, prob0, bit, depth;
    float p, p0;

    if (!gamma_fixture_active || stream_index != 0 || local_position < 256 ||
        local_position >= 320 || n_symbols != 16392)
        return;
    start = 0;
    range = n_symbols;
    p = 1.0f;
    depth = 0;
    while (range > 1) {
        range0 = range >> 1;
        p0 = vec_sum_f32(prob_table + start, range0);
        prob0 = lrintf(p0 * PROB_UNIT / p);
        prob0 = clamp_int(prob0, 1, PROB_UNIT - 1);
        bit = symbol >= start + range0;
        gamma_put_le32(gamma_branch_file, local_position - 256);
        gamma_put_le32(gamma_branch_file, symbol);
        gamma_put_le32(gamma_branch_file, depth);
        gamma_put_le32(gamma_branch_file, start);
        gamma_put_le32(gamma_branch_file, range);
        gamma_put_le32(gamma_branch_file, range0);
        gamma_put_le32(gamma_branch_file, prob0);
        gamma_put_le32(gamma_branch_file, bit);
        if (bit) {
            start += range0;
            range -= range0;
            p -= p0;
        } else {
            range = range0;
            p = p0;
        }
        depth++;
    }
}

static void gamma_fixture_finish(void)
{
    char path[4096];
    FILE *file;

    if (!gamma_fixture_active)
        return;
    if (!gamma_branch_file || fclose(gamma_branch_file)) {
        perror("tree_path close");
        abort();
    }
    gamma_branch_file = NULL;
    gamma_fixture_path(path, sizeof(path), "complete.marker");
    file = fopen(path, "wb");
    if (!file || fwrite("COMPLETE\n", 1, 9, file) != 9 || fclose(file)) {
        perror(path);
        abort();
    }
}

'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"expected one patch marker, found {count}: {old[:80]!r}")
    return source.replace(old, new, 1)


def replace_first_of(source: str, old: str, new: str, expected_count: int) -> str:
    count = source.count(old)
    if count != expected_count:
        raise ValueError(
            f"expected {expected_count} patch markers, found {count}: {old[:80]!r}"
        )
    return source.replace(old, new, 1)


def patch_teacher(source: str) -> str:
    source = replace_once(
        source,
        "static NCTensor *trf_eval(NNCPModelState *s1, int output_index, const NCTensor *input)\n",
        "static void gamma_dump_layer_tensor(int layer, const char *name,\n"
        "                                    const NCTensor *tensor);\n\n"
        "static NCTensor *trf_eval(NNCPModelState *s1, int output_index, const NCTensor *input)\n",
    )
    source = replace_once(
        source,
        "static FILE *teacher_trace_file;\n",
        CAPTURE_HELPER + "static FILE *teacher_trace_file;\n",
    )
    source = replace_once(
        source,
        "    teacher_trace_init();\n    execution_row = teacher_trace_rows;",
        "    teacher_trace_init();\n"
        "    gamma_dump_tree_path(prob_table, n_symbols, symbol, local_position,\n"
        "                         stream_index);\n"
        "    execution_row = teacher_trace_rows;",
    )
    source = replace_first_of(
        source,
        "            output_host = s->model_class->model_eval(s, -1, input);",
        "            gamma_fixture_begin(s, input, block_buf, block_stride,\n"
        "                                block_rem, block_idx);\n"
        "            output_host = s->model_class->model_eval(s, -1, input);",
        2,
    )
    source = replace_once(
        source,
        "            nc_free_tensor(output_host);\n        }\n\n        lr = get_interp_param(&s->lr, s->train_step);",
        "            nc_free_tensor(output_host);\n"
        "            if (gamma_fixture_active) {\n"
        "                gamma_fixture_finish();\n"
        "                exit(0);\n"
        "            }\n"
        "        }\n\n"
        "        lr = get_interp_param(&s->lr, s->train_step);",
    )

    source = replace_once(
        source,
        "    if (s->dropout_enabled) {\n        layer_input = dropout_mul(layer_input, s->dropout_prob, s->common.rnd_state);\n    }\n    \n    for(layer_idx = 0; layer_idx < s->n_layer; layer_idx++) {",
        "    if (s->dropout_enabled) {\n"
        "        layer_input = dropout_mul(layer_input, s->dropout_prob, s->common.rnd_state);\n"
        "    }\n"
        "#ifdef DUMP_HASH\n"
        "    nc_dump_tensor_hash(\"embedding_input\", layer_input);\n"
        "#endif\n"
        "    \n"
        "    for(layer_idx = 0; layer_idx < s->n_layer; layer_idx++) {",
    )
    source = replace_once(
        source,
        "        /* save the matrix input */",
        "#ifdef DUMP_HASH\n"
        "        gamma_dump_layer_tensor(layer_idx, \"attention_input\", layer_input1);\n"
        "#endif\n\n"
        "        /* save the matrix input */",
    )
    source = replace_once(
        source,
        "        value = split_head(value, s->n_head);\n        \n        if (output_index <= 0 && !s->rotary_pos_embed) {",
        "        value = split_head(value, s->n_head);\n"
        "#ifdef DUMP_HASH\n"
        "        gamma_dump_layer_tensor(layer_idx, \"key_state\", key);\n"
        "        gamma_dump_layer_tensor(layer_idx, \"value_state\", value);\n"
        "#endif\n"
        "        \n"
        "        if (output_index <= 0 && !s->rotary_pos_embed) {",
    )
    source = replace_once(
        source,
        "        if (output_index < 0) {\n            if (s->rotary_pos_embed) {",
        "#ifdef DUMP_HASH\n"
        "        if (!s->rotary_pos_embed) {\n"
        "            gamma_dump_layer_tensor(layer_idx, \"relative_weight\", tl->tmp_w_r);\n"
        "            gamma_dump_layer_tensor(layer_idx, \"relative_bias\", tl->tmp_b_r);\n"
        "        }\n"
        "#endif\n\n"
        "        if (output_index < 0) {\n"
        "            if (s->rotary_pos_embed) {",
    )
    source = replace_once(
        source,
        "            t0 = nc_soft_max(t0);\n            if (s->dropout_enabled) {",
        "            t0 = nc_soft_max(t0);\n"
        "#ifdef DUMP_HASH\n"
        "            gamma_dump_layer_tensor(layer_idx, \"attention_probability\", t0);\n"
        "#endif\n"
        "            if (s->dropout_enabled) {",
    )
    for old_label, new_label in (
        ("attn_out_bl", "attention_residual"),
        ("attn_out", "attention_output"),
        ("ff1_out", "ff1_output"),
        ("ff2_in", "geglu_output"),
        ("ff_out_bl", "feedforward_residual"),
        ("ff_out", "layer_hidden"),
    ):
        source = replace_once(
            source,
            f'        nc_dump_tensor_hash("{old_label}", t0);',
            f'        gamma_dump_layer_tensor(layer_idx, "{new_label}", t0);',
        )
    source = replace_once(
        source,
        "    if (s->dropout_enabled) {\n        layer_input = dropout_mul(layer_input, s->dropout_prob, s->common.rnd_state);\n    }\n\n    t0 = layer_input;",
        "#ifdef DUMP_HASH\n"
        "    nc_dump_tensor_hash(\"final_hidden\", layer_input);\n"
        "#endif\n"
        "    if (s->dropout_enabled) {\n"
        "        layer_input = dropout_mul(layer_input, s->dropout_prob, s->common.rnd_state);\n"
        "    }\n\n"
        "    t0 = layer_input;",
    )
    source = replace_once(
        source,
        "    if (s->out_bias)\n        t0 = nc_add(t0, nc_dup_tensor(s->out_bias));\n    t0 = nc_convert(t0, NC_TYPE_F32);",
        "    if (s->out_bias)\n"
        "        t0 = nc_add(t0, nc_dup_tensor(s->out_bias));\n"
        "#ifdef DUMP_HASH\n"
        "    nc_dump_tensor_hash(\"logits\", t0);\n"
        "#endif\n"
        "    t0 = nc_convert(t0, NC_TYPE_F32);",
    )
    return source


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, check=True, text=True, capture_output=True, **kwargs
    )


def compile_oracle(temporary: Path) -> tuple[Path, Path, Path, dict[str, object]]:
    compiler = os.environ.get("CC", "cc")
    patched_source = temporary / "nncp_production_fixture.c"
    patched_source.write_text(patch_teacher((LIBNC_ROOT / "nncp.c").read_text()))
    nncp_object = temporary / "nncp_production_fixture.o"
    executable = temporary / "nncp_production_fixture"
    exporter = temporary / "nncp_libnc_export"
    hook = temporary / "nncp_production_fixture_hook.so"
    commands = [
        [
            compiler,
            "-O3",
            "-Wall",
            "-Wpointer-arith",
            "-g",
            "-fno-math-errno",
            "-fno-trapping-math",
            '-DCONFIG_VERSION="2024-06-05"',
            "-DLIBNC_CONFIG_FULL",
            "-DDUMP_HASH",
            f"-I{LIBNC_ROOT}",
            "-c",
            str(patched_source),
            "-o",
            str(nncp_object),
        ],
        [
            compiler,
            f"-Wl,-rpath,{LIBNC_ROOT}",
            "-o",
            str(executable),
            str(nncp_object),
            *[
                str(LIBNC_ROOT / name)
                for name in (
                    "cmdopt.o",
                    "cp_utils.o",
                    "arith.o",
                    "preprocess.o",
                    "cutils.o",
                )
            ],
            str(LIBNC_ROOT / "libnc.so"),
            "-lz",
            "-lm",
            "-lpthread",
        ],
        [
            compiler,
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            f"-I{LIBNC_ROOT}",
            str(EXPORTER_SOURCE),
            f"-L{LIBNC_ROOT}",
            f"-Wl,-rpath,{LIBNC_ROOT}",
            "-lnc",
            "-lm",
            "-ldl",
            "-lpthread",
            "-o",
            str(exporter),
        ],
        [
            compiler,
            "-std=gnu11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-unused-parameter",
            "-shared",
            "-fPIC",
            f"-I{LIBNC_ROOT}",
            str(HOOK_SOURCE),
            f"-L{LIBNC_ROOT}",
            f"-Wl,-rpath,{LIBNC_ROOT}",
            "-lnc",
            "-ldl",
            "-o",
            str(hook),
        ],
    ]
    stderrs = []
    for command in commands:
        stderrs.append(run(command).stderr)
    return executable, exporter, hook, {
        "commands": commands,
        "stderrs": stderrs,
        "patched_source_sha256": sha256(patched_source),
        "executable_sha256": sha256(executable),
        "exporter_sha256": sha256(exporter),
        "hook_sha256": sha256(hook),
    }


def parse_meta(path: Path) -> dict[str, object]:
    fields: dict[str, object] = {}
    for line in path.read_text().splitlines():
        key, value = line.split("=", 1)
        if key in {"index", "item_size"}:
            fields[key] = int(value)
        elif key in {"source_dims", "selected_dims", "source_strides"}:
            fields[key] = [int(item) for item in value.split(",")]
        else:
            fields[key] = value
    return fields


def bind_directory(directory: Path, suffix: str) -> list[dict[str, object]]:
    records = []
    for path in sorted(directory.glob(f"*{suffix}")):
        record = parse_meta(path.with_suffix(".meta")) if suffix == ".f32" else {}
        record.update(
            {
                "payload": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "byte_order": "little",
            }
        )
        records.append(record)
    return records


def augment_export(directory: Path) -> dict[str, object]:
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    expected_indexes = list(range(manifest["tensor_count"]))
    observed_indexes = [entry["index"] for entry in manifest["tensors"]]
    if observed_indexes != expected_indexes:
        raise ValueError(f"reordered tensor export: {directory}")
    for entry in manifest["tensors"]:
        payload = directory / entry["payload"]
        if not payload.is_file() or payload.stat().st_size != entry["bytes"]:
            raise ValueError(f"missing or size-inconsistent tensor: {payload}")
        entry["sha256"] = sha256(payload)
        entry["byte_order"] = "little"
        item_size = {"f32": 4, "bf16": 2, "i32": 4, "i8": 1}.get(
            entry["type"]
        )
        if item_size is None:
            raise ValueError(f"unsupported exported item type: {entry['type']}")
        entry["logical_strides"] = [item_size]
        for dimension in entry["dims"][:-1]:
            entry["logical_strides"].append(
                entry["logical_strides"][-1] * dimension
            )
    manifest["manifest_sha256_before_binding"] = sha256(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def expected_internal_labels() -> list[str]:
    labels = ["embedding_input"]
    layer_labels = (
        "attention_input",
        "key_state",
        "value_state",
        "relative_weight",
        "relative_bias",
        "attention_probability",
        "attention_residual",
        "attention_output",
        "ff1_output",
        "geglu_output",
        "feedforward_residual",
        "layer_hidden",
    )
    for layer in range(20):
        labels.extend(f"layer_{layer:02d}_{label}" for label in layer_labels)
    labels.extend(("final_hidden", "logits", "output"))
    return labels


def write_tensor_index(
    fixture: Path,
    parameters: dict[str, object],
    state: dict[str, object],
    internal: list[dict[str, object]],
) -> Path:
    lines = [
        "category\tindex\tname\ttype\tdims\tstrides\tbytes\tsha256\tpayload"
    ]
    for category, directory, manifest in (
        ("parameter", "parameters", parameters),
        ("state", "state", state),
    ):
        for entry in manifest["tensors"]:
            lines.append(
                "\t".join(
                    (
                        category,
                        str(entry["index"]),
                        entry["name"],
                        entry["type"].upper(),
                        ",".join(str(value) for value in entry["dims"]),
                        ",".join(
                            str(value) for value in entry["logical_strides"]
                        ),
                        str(entry["bytes"]),
                        entry["sha256"],
                        f"{directory}/{entry['payload']}",
                    )
                )
            )
    for entry in internal:
        lines.append(
            "\t".join(
                (
                    "internal",
                    str(entry["index"]),
                    entry["label"],
                    "F32",
                    ",".join(str(value) for value in entry["selected_dims"]),
                    "dense-axis0-fastest",
                    str(entry["bytes"]),
                    entry["sha256"],
                    f"internal/{entry['payload']}",
                )
            )
        )
    index_path = fixture / "tensor_index.tsv"
    index_path.write_text("\n".join(lines) + "\n")
    return index_path


def extract_fixture(
    temporary: Path, executable: Path, exporter: Path, hook: Path
) -> tuple[Path, dict[str, object]]:
    fixture = temporary / "fixture"
    internal_dir = fixture / "internal"
    parameter_dir = fixture / "parameters"
    state_dir = fixture / "state"
    fixture.mkdir()
    internal_dir.mkdir()
    parameter_dir.mkdir()
    state_dir.mkdir()
    marker = fixture / "capture.marker"
    archive = temporary / "discarded_partial_archive.nncp"
    environment = os.environ.copy()
    environment.update(
        {
            "LD_LIBRARY_PATH": str(LIBNC_ROOT),
            "LD_PRELOAD": str(hook),
            "NNCP_PRODUCTION_FIXTURE_DIR": str(fixture),
            "NNCP_PRODUCTION_FIXTURE_INTERNAL_DIR": str(internal_dir),
            "NNCP_PRODUCTION_FIXTURE_MARKER": str(marker),
        }
    )
    command = [
        str(executable),
        "-q",
        "-T",
        "4",
        "--profile",
        "enwik9",
        "--n_symb",
        "16392",
        "--dict",
        str(DICTIONARY),
        "--max_size",
        "65536",
        "c",
        str(PREPROCESSED),
        str(archive),
    ]
    completed = run(command, env=environment, cwd=temporary)
    if not (fixture / "complete.marker").is_file():
        raise ValueError("teacher fixture did not reach the selected evaluation")
    run([str(exporter), str(fixture / "parameters.coefs"), str(parameter_dir)])
    run([str(exporter), str(fixture / "state.params"), str(state_dir)])
    parameter_manifest = augment_export(parameter_dir)
    state_manifest = augment_export(state_dir)
    internal = bind_directory(internal_dir, ".f32")
    labels = [entry["label"] for entry in internal]
    if labels != expected_internal_labels():
        raise ValueError("missing, extra, or reordered internal fixture tensors")
    tree_path = fixture / "tree_path.u32le"
    targets = fixture / "target_symbols.u16le"
    if tree_path.read_bytes()[:8] != b"NNPTREE1" or targets.stat().st_size != 128:
        raise ValueError("invalid branch path or target symbol fixture")
    tensor_index = write_tensor_index(
        fixture, parameter_manifest, state_manifest, internal
    )
    manifest = {
        "schema": "gamma.nncp.production.forward.fixture.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "epistemic_tier": "zero_credit_libnc_oracle_fixture",
        "runtime_dependency": False,
        "profile": PROFILE,
        "selection": {
            "reason": "earliest complete segment with all 256 memory positions populated",
            "startup_padding": False,
            "remainder_behavior": False,
            "input_original_symbol_start": 255,
            "input_original_symbol_end": 319,
            "truth_original_symbol_start": 256,
            "truth_original_symbol_end": 320,
        },
        "identity": {str(path): expected for path, expected in EXPECTED.items()},
        "oracle_build": {
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
        "parameters": parameter_manifest,
        "state": state_manifest,
        "internal": internal,
        "tree_path": {
            "payload": tree_path.name,
            "bytes": tree_path.stat().st_size,
            "sha256": sha256(tree_path),
            "format": "8-byte magic, u32 symbol_count, u32 vocabulary, repeated 8*u32 branch rows",
        },
        "target_symbols": {
            "payload": targets.name,
            "bytes": targets.stat().st_size,
            "sha256": sha256(targets),
            "type": "U16",
            "byte_order": "little",
            "count": 64,
        },
        "tensor_index": {
            "payload": tensor_index.name,
            "bytes": tensor_index.stat().st_size,
            "sha256": sha256(tensor_index),
        },
    }
    fixture_manifest = fixture / "fixture_manifest.json"
    fixture_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return fixture, manifest


def aggregate(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.iterdir() if item.is_file()):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def compare_forward(
    fixture: Path, manifest: dict[str, object], observed: Path
) -> tuple[list[dict[str, object]], dict[str, object]]:
    comparisons = []
    expected_output_names = {
        f"{entry['label']}.f32" for entry in manifest["internal"]
    } | {"tree_path.u32le", "complete.marker"}
    observed_output_names = {
        path.name for path in observed.iterdir() if path.is_file()
    }
    if observed_output_names != expected_output_names:
        raise ValueError(
            "missing or extra open-forward outputs: "
            f"expected={sorted(expected_output_names - observed_output_names)} "
            f"extra={sorted(observed_output_names - expected_output_names)}"
        )
    for expected in manifest["internal"]:
        label = expected["label"]
        expected_path = fixture / "internal" / expected["payload"]
        observed_path = observed / f"{label}.f32"
        if not observed_path.is_file():
            raise ValueError(f"open forward omitted tensor: {label}")
        reference = np.fromfile(expected_path, dtype="<f4")
        candidate = np.fromfile(observed_path, dtype="<f4")
        if reference.shape != candidate.shape or not np.isfinite(candidate).all():
            raise ValueError(f"invalid open tensor: {label}")
        difference = candidate.astype(np.float64) - reference.astype(np.float64)
        comparisons.append(
            {
                "label": label,
                "elements": int(reference.size),
                "maximum_absolute_error": float(np.abs(difference).max(initial=0.0)),
                "mean_absolute_error": float(np.abs(difference).mean()),
                "expected_sha256": expected["sha256"],
                "observed_sha256": sha256(observed_path),
            }
        )

    expected_tree = (fixture / "tree_path.u32le").read_bytes()
    observed_tree = (observed / "tree_path.u32le").read_bytes()
    if expected_tree[:16] != observed_tree[:16] or len(expected_tree) != len(observed_tree):
        raise ValueError("tree header or row-count mismatch")
    expected_rows = np.frombuffer(expected_tree[16:], dtype="<u4").reshape((-1, 8))
    observed_rows = np.frombuffer(observed_tree[16:], dtype="<u4").reshape((-1, 8))
    topology_columns = [0, 1, 2, 3, 4, 5, 7]
    topology_disagreements = int(
        np.count_nonzero(expected_rows[:, topology_columns] != observed_rows[:, topology_columns])
    )
    truth_path_disagreements = int(
        np.count_nonzero(expected_rows[:, 7] != observed_rows[:, 7])
    )
    maximum_probability_count_difference = int(
        np.abs(
            expected_rows[:, 6].astype(np.int64) - observed_rows[:, 6].astype(np.int64)
        ).max(initial=0)
    )
    branch = {
        "rows": int(expected_rows.shape[0]),
        "tree_topology_and_symbol_order_disagreements": topology_disagreements,
        "truth_path_disagreements": truth_path_disagreements,
        "maximum_integer_probability_count_difference": maximum_probability_count_difference,
        "expected_sha256": sha256(fixture / "tree_path.u32le"),
        "observed_sha256": sha256(observed / "tree_path.u32le"),
    }
    return comparisons, branch


def build_open_forward(temporary: Path) -> tuple[Path, Path, dict[str, object]]:
    source = temporary / "open_source"
    source.mkdir()
    source_tar = temporary / "ggml_source.tar"
    source_tar.write_bytes(
        subprocess.check_output(
            ["git", "archive", "--format=tar", "HEAD", "LICENSE", "ggml"],
            cwd=common.GGML_REPO,
        )
    )
    common.run(["tar", "-xf", str(source_tar), "-C", str(source)])
    shutil.copy2(PROGRAM / "CMakeLists.txt", source / "CMakeLists.txt")
    shutil.copy2(
        PROGRAM / "profile_forward_parity.cpp",
        source / "profile_forward_parity.cpp",
    )
    source_package = temporary / "ggml_profile_forward_source_closure.tar.xz"
    common.run(
        [
            "tar",
            "--sort=name",
            "--mtime=@0",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "-cJf",
            str(source_package),
            "-C",
            str(source),
            ".",
        ]
    )
    build = temporary / "open_build"
    configure = common.run(
        [
            "cmake",
            "-S",
            str(source),
            "-B",
            str(build),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_SHARED_LIBS=OFF",
            "-DGGML_NATIVE=OFF",
            "-DGGML_OPENMP=OFF",
            "-DGGML_BLAS=OFF",
            "-DGGML_LLAMAFILE=OFF",
            "-DGGML_CCACHE=OFF",
        ]
    )
    compiled = common.run(
        [
            "cmake",
            "--build",
            str(build),
            "--target",
            "nncp_ggml_profile_forward_parity",
            "-j4",
        ]
    )
    binaries = [
        path
        for path in build.rglob("nncp_ggml_profile_forward_parity")
        if path.is_file()
    ]
    if len(binaries) != 1:
        raise RuntimeError("open profile-forward binary is not unique")
    binary = binaries[0]
    ldd = common.run(["ldd", str(binary)]).stdout
    forbidden = [
        line
        for line in ldd.splitlines()
        if any(
            token in line.lower()
            for token in ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")
        )
    ]
    return binary, source_package, {
        "configure_stdout": configure.stdout,
        "configure_stderr": configure.stderr,
        "build_stdout": compiled.stdout,
        "build_stderr": compiled.stderr,
        "binary_bytes": binary.stat().st_size,
        "binary_sha256": sha256(binary),
        "source_package_bytes": source_package.stat().st_size,
        "source_package_sha256": sha256(source_package),
        "ldd": ldd,
        "forbidden_dynamic_dependencies": forbidden,
    }


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    for path, expected in EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen input identity mismatch: {path}")
    bridge = json.loads(BRIDGE_DECISION.read_text())
    if bridge.get("verdict") != "authorize_production_P_K_O_OK_F_S_attribution":
        raise ValueError("production bridge authorization is absent")
    ggml_commit = run(["git", "rev-parse", "HEAD"], cwd=common.GGML_REPO).stdout.strip()
    ggml_dirty = run(["git", "status", "--porcelain"], cwd=common.GGML_REPO).stdout
    if ggml_commit != common.EXPECTED_COMMIT or ggml_dirty:
        raise ValueError("GGML source identity mismatch")

    RESULT.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="nncp-production-parity-") as name:
        temporary = Path(name)
        executable, exporter, hook, oracle_build = compile_oracle(temporary)
        fixture, manifest = extract_fixture(temporary, executable, exporter, hook)
        fixture_package = RESULT / "production_forward_fixture.tar.xz"
        common.run(
            [
                "tar",
                "--sort=name",
                "--mtime=@0",
                "--owner=0",
                "--group=0",
                "--numeric-owner",
                "-cJf",
                str(fixture_package),
                "-C",
                str(fixture),
                ".",
            ]
        )

        binary, source_package, open_build = build_open_forward(temporary)
        run_a = temporary / "open_run_a"
        run_b = temporary / "open_run_b"
        run_a.mkdir()
        run_b.mkdir()
        clean_environment = {
            "HOME": str(temporary / "home"),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        }
        Path(clean_environment["HOME"]).mkdir()
        open_a = common.run(
            [str(binary), str(fixture), str(run_a)],
            cwd=temporary,
            env=clean_environment,
        )
        open_b = common.run(
            [str(binary), str(fixture), str(run_b)],
            cwd=temporary,
            env=clean_environment,
        )
        repeat_identical = aggregate(run_a) == aggregate(run_b)
        comparisons, branch = compare_forward(fixture, manifest, run_a)
        maximum_tensor_error = max(
            item["maximum_absolute_error"] for item in comparisons
        )
        tensor_pass = maximum_tensor_error <= TOLERANCE
        branch_pass = (
            branch["tree_topology_and_symbol_order_disagreements"] == 0
            and branch["truth_path_disagreements"] == 0
            and branch["maximum_integer_probability_count_difference"] <= 1
        )
        source_ceiling_pass = open_build["source_package_bytes"] <= SOURCE_CEILING
        dynamic_dependency_pass = not open_build["forbidden_dynamic_dependencies"]
        overall_pass = all(
            (
                tensor_pass,
                branch_pass,
                repeat_identical,
                source_ceiling_pass,
                dynamic_dependency_pass,
            )
        )
        shutil.copy2(source_package, RESULT / source_package.name)
        decision = {
            "schema": "gamma.nncp.ggml.profile_forward_parity.qm0.v1",
            "candidate_id": CANDIDATE_ID,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epistemic_tier": "zero_credit_open_forward_parity",
            "score_credit_bytes": 0,
            "profile": PROFILE,
            "fixture_manifest_sha256": sha256(fixture / "fixture_manifest.json"),
            "fixture_package_bytes": fixture_package.stat().st_size,
            "fixture_package_sha256": sha256(fixture_package),
            "oracle_build": oracle_build,
            "ggml_commit": ggml_commit,
            "tolerance": TOLERANCE,
            "source_ceiling_bytes": SOURCE_CEILING,
            "source_ceiling_pass": source_ceiling_pass,
            "open_build": open_build,
            "open_run_stdout": open_a.stdout,
            "open_run_stderr": open_a.stderr,
            "repeat_open_outputs_byte_identical": repeat_identical,
            "open_run_aggregate_sha256": aggregate(run_a),
            "tensor_comparisons": comparisons,
            "maximum_tensor_absolute_error": maximum_tensor_error,
            "tensor_tolerance_pass": tensor_pass,
            "branch_comparison": branch,
            "branch_pass": branch_pass,
            "dynamic_dependency_pass": dynamic_dependency_pass,
            "overall_pass": overall_pass,
            "verdict": (
                "authorize_production_P_K_O_OK_F_S_attribution"
                if overall_pass
                else "retire_exact_open_profile_forward_port"
            ),
            "fixture_complete": True,
            "fixture_runtime_dependency": manifest["runtime_dependency"],
        }
        (RESULT / "decision.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n"
        )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
