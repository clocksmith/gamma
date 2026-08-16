#!/usr/bin/env python3
"""Materialize the exact 32-stream production update boundary from LibNC."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_ggml_profile_arithmetic_64_q0 as arithmetic
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_profile_update_fixture_64_q0_v1"
PARENT_DECISION = ROOT / "results/nncp_ggml_profile_memory_transition_64_q0_v1/decision.json"
PARENT_REFLECTION = ROOT / "operations/adaptive/reflections/20260815T231108Z_4912fe7f1f.json"
LIBNC_ROOT = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05")
PREPROCESSED = Path("/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/preprocessed.bin")
DICTIONARY = Path("/home/x/enwiki9-nonproof/results/nncp_full_symbol_map_v1_retry2/dictionary.bin")
HOOK = ROOT / "tools/nncp_profile_update_fixture_hook.c"
EXPECTED = {
    LIBNC_ROOT / "nncp.c": "9a44757c26fba57bcbd854e50201deef53c85fd86a3bb142a198d518144a138a",
    LIBNC_ROOT / "libnc.so": "1836cdfd7b42ca49efec6421cfce8a7728e8b7d9f3fcd193094c27a38af36d3e",
    PREPROCESSED: "c82bfca1cb00f04ab17603ba9d40def7a0e71fc0db1f018a4282dbe501d60a5",
    DICTIONARY: "950683b4d0ab597f2e4f877f221c54f22564596b85f05d2ae0ee968858cda0a1",
}
TARGET_BLOCK = 256
EXPECTED_PARAMETERS = 246
EXPECTED_STREAMS = 32
EXPECTED_SEGMENT = 64
EXPECTED_LAYERS = 20


CAPTURE_HELPER = r'''
static int gamma_update_fixture_active;

static void gamma_fixture_path(char *path, size_t size, const char *name)
{
    const char *directory = getenv("NNCP_PROFILE_UPDATE_FIXTURE_DIR");
    if (!directory || !directory[0]) {
        fprintf(stderr, "NNCP_PROFILE_UPDATE_FIXTURE_DIR is required\n");
        abort();
    }
    snprintf(path, size, "%s/%s", directory, name);
}

static void gamma_save_optimizer(TransformerModel *model, const char *name)
{
    struct list_head *element;
    char path[4096];
    FILE *file;

    gamma_fixture_path(path, sizeof(path), name);
    file = fopen(path, "wb");
    if (!file) {
        perror(path);
        abort();
    }
    nc_save_param_header(file, "gamma.nncp.production.update.optimizer.v1");
    list_for_each(element, &model->param_list.param_list) {
        NCParam *parameter = list_entry(element, NCParam, link);
        nc_save_param_opt(file, parameter);
    }
    if (fclose(file))
        abort();
}

static void gamma_save_state(TransformerModel *model, const NCTensor *input,
                             const NCTensor *expected, const char *name,
                             int include_batch)
{
    char path[4096], tensor_name[80];
    FILE *file;
    int layer;

    gamma_fixture_path(path, sizeof(path), name);
    file = fopen(path, "wb");
    if (!file) {
        perror(path);
        abort();
    }
    nc_save_param_header(file, "gamma.nncp.production.update.state.v1");
    if (include_batch) {
        nc_save_param(file, input, "input_all_streams");
        nc_save_param(file, expected, "target_all_streams");
    }
    for (layer = 0; layer < model->n_layer; layer++) {
        snprintf(tensor_name, sizeof(tensor_name), "mem_h_%d", layer);
        nc_save_param(file, model->mem_h[layer], tensor_name);
        snprintf(tensor_name, sizeof(tensor_name), "train_h_%d", layer);
        nc_save_param(file, model->train_h[layer], tensor_name);
    }
    if (fclose(file))
        abort();
}

static void gamma_update_fixture_begin(NNCPModelState *state,
                                       const NCTensor *input,
                                       const NCTensor *expected,
                                       int block_idx, float learning_rate)
{
    TransformerModel *model = (TransformerModel *)state;
    char path[4096];
    FILE *file;

    if (block_idx != 256 || gamma_update_fixture_active)
        return;
    if (model->n_layer != 20 || model->d_model != 1024 ||
        model->n_head != 8 || model->d_key != 128 ||
        model->d_value != 128 || model->d_inner != 3072 ||
        model->d_pos != 320 || model->mem_len != 256 ||
        model->train_len != 64 || model->n_symbols != 16392 ||
        model->n_streams != 32 || model->param_type != NC_TYPE_BF16 ||
        model->use_sparse_grad) {
        fprintf(stderr, "production update fixture geometry mismatch\n");
        abort();
    }
    gamma_fixture_path(path, sizeof(path), "parameters_initial.coefs");
    nc_save_coefs(&model->param_list, path);
    gamma_save_optimizer(model, "optimizer_initial.params");
    gamma_save_state(model, input, expected, "state_initial.params", 1);
    gamma_fixture_path(path, sizeof(path), "boundary.txt");
    file = fopen(path, "w");
    if (!file)
        abort();
    fprintf(file, "block_idx=%d\ntrain_step_before=%lld\nlearning_rate=%a\n",
            block_idx, (long long)state->train_step, learning_rate);
    if (fclose(file))
        abort();
    gamma_fixture_path(path, sizeof(path), "active.marker");
    file = fopen(path, "wb");
    if (!file || fwrite("ACTIVE\n", 1, 7, file) != 7 || fclose(file))
        abort();
    gamma_update_fixture_active = 1;
}

static void gamma_update_fixture_finish(NNCPModelState *state, int block_idx,
                                        float learning_rate)
{
    TransformerModel *model = (TransformerModel *)state;
    char path[4096];
    FILE *file;

    if (!gamma_update_fixture_active)
        return;
    gamma_fixture_path(path, sizeof(path), "parameters_final.coefs");
    nc_save_coefs(&model->param_list, path);
    gamma_save_optimizer(model, "optimizer_final.params");
    gamma_save_state(model, NULL, NULL, "state_final.params", 0);
    gamma_fixture_path(path, sizeof(path), "boundary.txt");
    file = fopen(path, "a");
    if (!file)
        abort();
    fprintf(file, "block_idx_after=%d\ntrain_step_after=%lld\nlearning_rate_after=%a\n",
            block_idx + model->train_len, (long long)state->train_step,
            learning_rate);
    if (fclose(file))
        abort();
    gamma_fixture_path(path, sizeof(path), "complete.marker");
    file = fopen(path, "wb");
    if (!file || fwrite("COMPLETE\n", 1, 9, file) != 9 || fclose(file))
        abort();
    exit(0);
}

'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    return arithmetic.reference(path, identifier)


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
    source = replace_once(
        source,
        "        s->model_class->model_set_lr(s, lr);\n        \n        s->model_class->model_eval_gradient(s, expected_output);",
        "        s->model_class->model_set_lr(s, lr);\n"
        "        gamma_update_fixture_begin(s, input, expected_output, block_idx, lr);\n"
        "        \n"
        "        s->model_class->model_eval_gradient(s, expected_output);",
    )
    source = replace_once(
        source,
        "        s->model_class->model_update(s);\n        s->train_step++;\n        block_idx += n_states;",
        "        s->model_class->model_update(s);\n"
        "        s->train_step++;\n"
        "        gamma_update_fixture_finish(s, block_idx, lr);\n"
        "        block_idx += n_states;",
    )
    return source


def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)


def compile_oracle(scratch: Path) -> tuple[Path, Path, dict[str, Any]]:
    compiler = os.environ.get("CC", "cc")
    patched = scratch / "nncp_profile_update_fixture.c"
    patched.write_text(patch_teacher((LIBNC_ROOT / "nncp.c").read_text()))
    obj = scratch / "nncp_profile_update_fixture.o"
    executable = scratch / "nncp_profile_update_fixture"
    hook = scratch / "nncp_profile_update_fixture_hook.so"
    commands = [
        [compiler, "-O3", "-Wall", "-Wpointer-arith", "-g", "-fno-math-errno",
         "-fno-trapping-math", '-DCONFIG_VERSION="2024-06-05"',
         "-DLIBNC_CONFIG_FULL", f"-I{LIBNC_ROOT}", "-c", str(patched), "-o", str(obj)],
        [compiler, f"-Wl,-rpath,{LIBNC_ROOT}", "-o", str(executable), str(obj),
         *[str(LIBNC_ROOT / name) for name in
           ("cmdopt.o", "cp_utils.o", "arith.o", "preprocess.o", "cutils.o")],
         str(LIBNC_ROOT / "libnc.so"), "-lz", "-lm", "-lpthread"],
        [compiler, "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror",
         "-Wno-unused-parameter", "-shared", "-fPIC", f"-I{LIBNC_ROOT}",
         str(HOOK), f"-L{LIBNC_ROOT}", f"-Wl,-rpath,{LIBNC_ROOT}",
         "-lnc", "-ldl", "-o", str(hook)],
    ]
    stderrs = [run(command).stderr for command in commands]
    return executable, hook, {
        "commands": commands,
        "stderrs": stderrs,
        "patchedSourceSha256": sha256(patched),
        "executableSha256": sha256(executable),
        "hookSha256": sha256(hook),
    }


def capture(executable: Path, hook: Path, directory: Path) -> dict[str, Any]:
    directory.mkdir()
    archive = directory.parent / f"{directory.name}.partial.nncp"
    environment = dict(os.environ)
    environment.update({
        "LD_LIBRARY_PATH": str(LIBNC_ROOT),
        "LD_PRELOAD": str(hook),
        "NNCP_PROFILE_UPDATE_FIXTURE_DIR": str(directory),
    })
    command = [str(executable), "-q", "-T", "4", "--profile", "enwik9",
               "--n_symb", "16392", "--dict", str(DICTIONARY),
               "--max_size", "65536", "c", str(PREPROCESSED), str(archive)]
    completed = run(command, env=environment, cwd=directory.parent)
    if not (directory / "complete.marker").is_file():
        raise ValueError("teacher did not complete the selected update boundary")
    return {
        "command": command,
        "stdoutSha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderrSha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "partialArchiveBytes": archive.stat().st_size if archive.exists() else 0,
        "partialArchiveSha256": sha256(archive) if archive.exists() else None,
    }


def directory_manifest(directory: Path) -> dict[str, Any]:
    files = []
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        relative = path.relative_to(directory).as_posix()
        file_hash = sha256(path)
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": file_hash})
        digest.update(relative.encode() + b"\0" + bytes.fromhex(file_hash))
    return {
        "files": files,
        "fileCount": len(files),
        "totalBytes": sum(row["bytes"] for row in files),
        "aggregateSha256": digest.hexdigest(),
    }


def parse_boundary(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines())


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [*local_source_closure((Path(__file__),)), HOOK.resolve()]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        if declared.get(relative) != reference(member, declared.get(relative, {}).get("id")):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(str(member), arcname=member.relative_to(ROOT).as_posix())
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > experiment["budget"]["maximumAddedPackageBytes"]:
        raise ValueError("source closure exceeds the frozen package budget")


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("parent-decision", PARENT_DECISION),
        ("parent-reflection", PARENT_REFLECTION),
        ("q18-decision", arithmetic.Q18_DECISION),
        ("q18-fixture", arithmetic.Q18_FIXTURE),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    if not (parent.get("promotionPass") is True and
            parent.get("measurements", {}).get("teacherOpenMemoryIdentity") is True):
        raise ValueError("memory-transition parent does not authorize this fixture")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    output = args.output.resolve()
    research_contracts.validate_artifact(experiment_path)
    experiment = json.loads(experiment_path.read_text())
    if experiment["proposalId"] != CANDIDATE_ID:
        raise ValueError("experiment identifies another candidate")
    if reference(experiment_path) != json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]):
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    for path, expected in EXPECTED.items():
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"frozen external input identity mismatch: {path}")
    result_root = (ROOT / "results" / CANDIDATE_ID).resolve()
    for relative in experiment["outputs"]:
        path = (ROOT / relative).resolve()
        if path.parent != result_root or path.exists():
            raise ValueError(f"output is outside a fresh result boundary: {relative}")

    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = output.parent / "scratch"
    scratch.mkdir()
    executable, hook, build = compile_oracle(scratch)
    fixture = output.parent / "fixture"
    repeat = output.parent / "fixture-repeat"
    executions = [capture(executable, hook, fixture), capture(executable, hook, repeat)]
    first_manifest = directory_manifest(fixture)
    repeat_manifest = directory_manifest(repeat)
    repeat_identical = first_manifest["aggregateSha256"] == repeat_manifest["aggregateSha256"]
    shutil.rmtree(repeat)
    boundary = parse_boundary(fixture / "boundary.txt")
    gradient_files = list((fixture / "gradients").glob("*.bin"))
    gradient_meta = list((fixture / "gradients").glob("*.meta"))
    required_files = {
        "parameters_initial.coefs", "optimizer_initial.params", "state_initial.params",
        "parameters_final.coefs", "optimizer_final.params", "state_final.params",
        "boundary.txt", "active.marker", "complete.marker",
    }
    root_files = {path.name for path in fixture.iterdir() if path.is_file()}
    fixture_complete = required_files <= root_files
    manifest_path = output.parent / "fixture-manifest.json"
    manifest = {
        "schema": "gamma.nncp.production-profile-update-fixture.v1",
        "epistemicTier": "zero-credit-libnc-oracle-fixture",
        "candidateId": CANDIDATE_ID,
        "externalInputs": {str(path): value for path, value in EXPECTED.items()},
        "build": build,
        "executions": executions,
        "boundary": boundary,
        "fixture": first_manifest,
        "repeatFixture": repeat_manifest,
        "rawFixturePath": fixture.relative_to(ROOT).as_posix(),
        "rawFixtureRetainedLocal": True,
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    execution_path = output.parent / "execution.json"
    execution_path.write_text(json.dumps({"build": build, "runs": executions}, indent=2, sort_keys=True) + "\n")
    package = output.parent / "incremental_source.tar.xz"
    source_package(package, experiment)
    shutil.rmtree(scratch)

    measurements: dict[str, bool | int | float] = {
        "parentPass": True,
        "fixtureComplete": fixture_complete,
        "fixtureRepeatByteIdentical": repeat_identical,
        "parameterPopulation": len(gradient_files),
        "gradientMetadataPopulation": len(gradient_meta),
        "streamPopulation": EXPECTED_STREAMS,
        "segmentPopulation": EXPECTED_SEGMENT,
        "layerPopulation": EXPECTED_LAYERS,
        "trainStepBefore": int(boundary["train_step_before"]),
        "trainStepAfter": int(boundary["train_step_after"]),
        "targetBlockBefore": int(boundary["block_idx"]),
        "targetBlockAfter": int(boundary["block_idx_after"]),
        "fixtureBytes": first_manifest["totalBytes"],
        "sourceClosureBytes": package.stat().st_size,
    }
    promotion = arithmetic.evaluate(experiment["promotionPredicates"], measurements)
    kill = arithmetic.evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
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
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": [reference(manifest_path, "fixture-manifest"),
                      reference(execution_path, "execution"),
                      reference(package, "source-package")],
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if promotion_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
