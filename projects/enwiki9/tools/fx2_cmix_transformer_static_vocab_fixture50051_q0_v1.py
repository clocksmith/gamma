#!/usr/bin/env python3
"""Prospective GCC diagnostic on one immutable public profiling fixture."""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
ID = "fx2_cmix_transformer_static_vocab_fixture50051_q0_v1"
RESULT = PROJECT / "results" / ID
AUDIT = PROJECT / "operations/provenance/public_fx2_cmix_transformer_v1.json"
AUDIT_SHA256 = "4e55dc96f722f769dd52dd9e518472f348e923e8c2b706a46ba0d1bbd972ae79"
SOURCE = PROJECT / "external/fx2-cmix-transformer-v1"
GUARD = PROJECT / "tools/run_with_resource_guard_q0_v13.py"
MEMORY_BYTES = 9899999232
DISK_BYTES = 16000000000
SEPARATOR = [8, 8, 37, 172, 101, 39, 5, 8, 8, 8, 8, 37, 172, 104, 39]
FAST = "-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections"
BUILD = ["/usr/bin/make", "-j1", "cmix", "CC=/usr/bin/g++",
         "CPPFLAGS_PART-THAT-SHOULD-BE-FAST=" + FAST + " -O3",
         "CPPFLAGS_PART-THAT-CAN-BE-SLOW=" + FAST + " -Os"]
TF_OBJECTS = ["tf_weights_io.o", "tf_weights_io_compressed.o", "tf_qmat_dense.o", "tf_qmat_sparse.o",
              "tf_attn.o", "tf_kda.o", "tf_glue.o", "tf_arena_build.o", "tf_model_opt.o"]
KERNEL_SOURCE_SHA256 = "857e0395cf09d7a88802d11279ee01e765b8f8c188573bc0808257ab040d0f19"


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path: Path, value: object) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def artifact(path: Path) -> dict:
    return {"path": str(path.relative_to(PROJECT)), "bytes": path.stat().st_size,
            "sha256": digest(path)}


def verify() -> dict:
    if digest(AUDIT) != AUDIT_SHA256:
        raise RuntimeError("public source audit identity drift")
    audit = json.loads(AUDIT.read_text())
    for row in audit["build_source_files"]:
        path = SOURCE / row["path"]
        if path.is_symlink() or not path.is_file() or path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise RuntimeError("public source identity drift: " + row["path"])
    return audit


def marker(phase: str, event: str) -> None:
    path = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    with path.open("a") as handle:
        handle.write(json.dumps({"phase": phase, "event": event}) + "\n")


def run_command(name: str, command: list[str], cwd: Path, seconds: int, expected_code: int = 0) -> dict:
    marker(name, "start")
    begin = time.monotonic()
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    full = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5", str(seconds), *command]
    with (RESULT / (name + ".stdout")).open("xb") as stdout, (RESULT / (name + ".stderr")).open("xb") as stderr:
        completed = subprocess.run(full, cwd=cwd, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, stdout=stdout, stderr=stderr)
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    report = {"command": full, "cwd": str(cwd.relative_to(PROJECT)), "returncode": completed.returncode,
              "elapsed_seconds": time.monotonic() - begin, "elapsed_cap_seconds": seconds,
              "user_cpu_seconds": usage_after.ru_utime - usage_before.ru_utime,
              "system_cpu_seconds": usage_after.ru_stime - usage_before.ru_stime,
              "expected_returncode": expected_code, "timing_authority": "shared-host diagnostic only"}
    write(RESULT / (name + ".execution.json"), report)
    marker(name, "end")
    if completed.returncode != expected_code:
        raise RuntimeError(name + " failed; no automatic retry")
    return report


def check_population(payload: bytes, vocabulary: dict) -> dict:
    if len(payload) < 21:
        raise ValueError("transformed fixture is truncated")
    observed = sorted(set(payload[5:]))
    vocab = vocabulary["vocabulary_bytes"]
    mapping = {byte: i for i, byte in enumerate(vocab)}
    indices = [mapping.get(byte) for byte in payload[6:21]]
    return {"preprocessed_bytes": len(payload), "observed_vocabulary_size": len(observed),
            "authenticated_vocabulary_size": len(vocab), "literal_first_block_header_hex": payload[:5].hex(),
            "coded_population_bytes": len(payload) - 5, "observed_vocabulary_bytes": observed,
            "authenticated_vocabulary_bytes": vocab, "first_block_type": payload[0],
            "dictionary_transform_marker": payload[5], "first_separator_indices": indices,
            "required_first_separator_indices": SEPARATOR,
            "mapping_gate_pass": len(payload) >= 10000 and len(vocab) == 205 and len(set(vocab)) == 205
            and set(observed) <= set(vocab) and payload[0] == 7 and payload[5] == 7 and indices == SEPARATOR}


def check_archive_header(header: bytes, payload: bytes, vocabulary: dict) -> None:
    if len(header) != 46 or header[:4] != b"GFV1" or header[4:9] != payload[:5]:
        raise ValueError("literal framing was not retained exactly")
    if header[14:46].hex() != vocabulary["vocabulary_bitmap_hex"]:
        raise ValueError("archive did not carry the authenticated static vocabulary")
    if not header[9] & 128 or (int.from_bytes(header[9:14], "big") & ((1 << 39) - 1)) != len(payload) - 5:
        raise ValueError("archive dictionary flag or coded size differs")


def stage() -> int:
    os.sched_setaffinity(0, {2})
    if os.sched_getaffinity(0) != {2}:
        raise RuntimeError("CPU2 affinity did not bind")
    audit = verify()
    work = RESULT / "work"
    materializer_path = PROJECT / "tools/fx2_cmix_transformer_gcc_fixture50051_q0_v4_materializer.py"
    if digest(materializer_path) != "f57ad54c7edac5e29d69d9f2c60430f48548ad727c0e5b7cf7a8864045d324a6":
        raise RuntimeError("materializer source identity drift before import")
    spec = importlib.util.spec_from_file_location("public_fx2_v4_materializer", materializer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.materialize(SOURCE, work, audit["build_source_files"])
    adapter_path = PROJECT / "operations/provenance/public_fx2_static_vocab_adapter_v1.json"
    if digest(adapter_path) != "151b0b8756613d75801a2c4eb93b27fb9628afd486431f08039fdb2a31939994":
        raise RuntimeError("static vocabulary adapter identity drift")
    adapter = json.loads(adapter_path.read_text())
    vocabulary_path = PROJECT / adapter["vocabulary_receipt"]["path"]
    if digest(vocabulary_path) != adapter["vocabulary_receipt"]["sha256"]:
        raise RuntimeError("authenticated vocabulary receipt changed")
    vocabulary = json.loads(vocabulary_path.read_text())
    runner_source = work / adapter["source_path"]
    if digest(runner_source) != adapter["source_sha256"]:
        raise RuntimeError("public runner source differs before adaptation")
    source_text = runner_source.read_text()
    for replacement in adapter["replacements"]:
        if source_text.count(replacement["before"]) != 1:
            raise RuntimeError("static vocabulary adapter is not unique")
        source_text = source_text.replace(replacement["before"], replacement["after"])
    runner_source.write_text(source_text)
    if digest(runner_source) != adapter["patched_sha256"]:
        raise RuntimeError("adapted runner source differs")
    write(RESULT / "adapter.json", {"patch": artifact(adapter_path), "vocabulary": artifact(vocabulary_path),
                                   "patched_source": artifact(runner_source), "decoder_changed": True, "frontend_identity": adapter["frontend_identity"]})
    decision = {"schema": "gamma.enwiki9.public-fx2-fixture-diagnostic.v1", "candidate_id": ID,
                "status": "running", "scope_bytes": 50051, "scope": "upstream public prof_input/input; not a canonical prefix",
                "objective_credit_bytes": 0, "roundtrip_ok": None, "deterministic_ok": None,
                "mapping_gate_pass": None, "complete_trained_mapping_equivalence": False,
                "larger_gate_authorized": False, "input": artifact(work / "prof_input/input"), "commands": []}
    try:
        probe_source = PROJECT / "tools/fx2_transformer_kernel_probe_v1.cpp"
        if digest(probe_source) != KERNEL_SOURCE_SHA256:
            raise RuntimeError("kernel probe source changed")
        decision["commands"].append(run_command("compile-transformer", BUILD[:2] + BUILD[3:] + TF_OBJECTS, work, 600))
        probe = work / "fx2_kernel_probe"
        probe_build = ["/usr/bin/g++", "-m64", "-O3", "-std=c++17", "-Wall", "-Wextra", "-fno-fast-math", "-fno-math-errno",
                       "-march=x86-64-v3", "-mtune=generic", "-mrecip=none", "-fdata-sections", "-ffunction-sections",
                       "-Wl,--gc-sections", "-Icpp_infer/src", str(probe_source), *TF_OBJECTS, "-o", str(probe), "-lm"]
        decision["commands"].append(run_command("compile-kernel", probe_build, work, 120))
        object_bindings = [artifact(work / name) for name in TF_OBJECTS]
        probabilities = RESULT / "kernel.probabilities.f32le"
        decision["commands"].append(run_command("kernel", [str(probe), str(work / "models/6m-q4-fp32.tfwc2"), str(probabilities)], work, 30))
        kernel = json.loads((RESULT / "kernel.stdout").read_text())
        probability_bytes = probabilities.read_bytes()
        if len(probability_bytes) != 839680 or probability_bytes[:419840] != probability_bytes[419840:]:
            raise RuntimeError("kernel probability repetitions differ")
        kernel.update({"source": artifact(probe_source), "binary": artifact(probe), "objects": object_bindings,
                       "probabilities": artifact(probabilities), "half_sha256": hashlib.sha256(probability_bytes[:419840]).hexdigest()})
        write(RESULT / "kernel.json", kernel)
        decision["kernel_repeat_ok"] = True
        decision["kernel_evidence"] = artifact(RESULT / "kernel.json")
        decision["commands"].append(run_command("compile", BUILD, work, 600))
        binary = work / "cmix"
        decision["binary"] = artifact(binary)
        dis = subprocess.run(["/usr/bin/objdump", "-d", "--insn-width=16", str(binary)], capture_output=True, text=True, check=True).stdout
        forbidden = [line for line in dis.splitlines() if re.search(r"\b(v?rcpps|v?rcpss|v?rsqrtps|v?rsqrtss)\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ", line)]
        write(RESULT / "instruction-audit.json", {"reciprocal_and_avx2_check_pass": not forbidden, "forbidden_lines": forbidden[:32], "binary": artifact(binary)})
        if forbidden:
            raise RuntimeError("portable instruction guard failed")
        dictionary = work / "dictionary/english.dic"
        weights = work / "models/6m-q4-fp32.tfwc2"
        fixture = work / "prof_input/input"
        options = "-c dictionary/english.dic input archive --transformer models/6m-q4-fp32.tfwc2\n-d dictionary/english.dic archive output --transformer models/6m-q4-fp32.tfwc2\n"
        write(RESULT / "package.json", {"schema": "gamma.enwiki9.local-codec-package-inventory.v1",
              "runtime_members": [artifact(path) for path in (binary, dictionary, weights)],
              "runtime_member_bytes": sum(path.stat().st_size for path in (binary, dictionary, weights)),
              "option_text": options, "option_bytes": len(options.encode()),
              "source_members": [artifact(work / row["path"]) for row in audit["build_source_files"]],
              "source_member_bytes": sum((work / row["path"]).stat().st_size for row in audit["build_source_files"]),
              "package_ceiling_bytes": 10000000, "complete_submission_package": False,
              "unresolved": ["separate model licensing clarification", "missing referenced third-party license text",
                  "transitive system dependency closure", "upstream submission packaging and compiler equivalence"],
              "attribution": "External FX2/CMIX and trained transformer remain upstream work; Gamma contributes the explicit counted framing/static-vocabulary adapter."})
        package = json.loads((RESULT / "package.json").read_text())
        decision["conservative_local_package_bytes"] = package["runtime_member_bytes"] + package["source_member_bytes"] + package["option_bytes"]
        if decision["conservative_local_package_bytes"] > package["package_ceiling_bytes"]:
            raise RuntimeError("local package inventory exceeds frozen ceiling")
        stored = work / "fixture.stored"
        decision["commands"].append(run_command("preprocess", [str(binary), "-s", str(dictionary), str(fixture), str(stored)], work, 120))
        storage = stored.read_bytes()
        if storage[:5] != bytes([128, 0, 0, 0, 0]):
            raise RuntimeError("unexpected dictionary storage header")
        payload = storage[5:]
        mapping_report = {**check_population(payload, vocabulary), "stored": artifact(stored),
                          "frontend_identity": adapter["frontend_identity"], "full_trained_mapping_equivalence": False,
                          "scope": "Exact public submission alphabet bound to pinned embedded model; fixture bytes must lie in that map."}
        write(RESULT / "vocabulary-gate.json", mapping_report)
        decision["mapping_gate_pass"] = mapping_report["mapping_gate_pass"]
        if not decision["mapping_gate_pass"]:
            decision["status"] = "mapping_rejected"
            decision["reason"] = "Public fixture does not satisfy the frozen transformer vocabulary and separator checks; compression was not invoked."
        else:
            archive = work / "fixture.cmix"
            restored = work / "restored"
            replay = work / "replay.cmix"
            decision["commands"].append(run_command("encode", [str(binary), "-c", str(dictionary), str(fixture), str(archive), "--transformer", str(weights)], work, 120))
            check_archive_header(archive.read_bytes()[:46], payload, vocabulary)
            decision["archive_vocabulary_matches_public_submission"] = True
            decision["commands"].append(run_command("decode", [str(binary), "-d", str(dictionary), str(archive), str(restored), "--transformer", str(weights)], work, 120))
            decision["commands"].append(run_command("reencode", [str(binary), "-c", str(dictionary), str(fixture), str(replay), "--transformer", str(weights)], work, 120))
            decision["roundtrip_ok"] = fixture.read_bytes() == restored.read_bytes()
            decision["deterministic_ok"] = archive.read_bytes() == replay.read_bytes()
            decision["outputs"] = {name: artifact(path) for name, path in [("archive", archive), ("restored", restored), ("replay", replay)]}
            invalid = work / "invalid-magic.cmix"
            invalid.write_bytes(b"FAIL" + archive.read_bytes()[4:])
            decision["commands"].append(run_command("invalid-envelope", [str(binary), "-d", str(dictionary), str(invalid), str(work / "invalid-output"), "--transformer", str(weights)], work, 10, expected_code=1))
            decision["invalid_envelope_rejected"] = "invalid Gamma static vocabulary envelope" in (RESULT / "invalid-envelope.stderr").read_text()
            if not decision["invalid_envelope_rejected"]:
                raise RuntimeError("negative control failed for an unexpected reason")
            decision["package_inventory"] = artifact(RESULT / "package.json")
            decision["coded_population_bytes"] = len(payload) - 5
            decision["framing_and_header_bytes"] = 46
            decision["codec_phase_costs"] = [{"phase": name, **json.loads((RESULT / (name + ".execution.json")).read_text())}
                                              for name in ("encode", "decode", "reencode")]
            decision["status"] = "passed" if decision["roundtrip_ok"] and decision["deterministic_ok"] else "failed"
    except Exception as exc:
        decision["status"] = "execution_failed"
        decision["error"] = type(exc).__name__ + ": " + str(exc)
    write(RESULT / "stage-decision.json", decision)
    return 0 if decision["status"] in {"passed", "mapping_rejected"} else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--cgroup-path", type=Path)
    args = parser.parse_args()
    audit = verify()
    if args.validate_only:
        print(json.dumps({"source_binding_pass": True, "files": len(audit["build_source_files"]), "no_build_or_codec_execution": True, "build_argv": BUILD}))
        return 0
    if args.stage:
        return stage()
    if args.cgroup_path is None:
        parser.error("--cgroup-path is required for canonical tool execution")
    expected_cgroup = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-fx2-transformer-static-vocab-fixture50051-q0-v1")
    if args.cgroup_path != expected_cgroup:
        raise RuntimeError("cgroup path must equal the prospectively isolated candidate path")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError("canonical executor must materialize an empty result directory")
    phases = RESULT / "phases.jsonl"
    phases.touch(exist_ok=False)
    command = [sys.executable, str(GUARD), "--limit-kib", str(MEMORY_BYTES // 1024), "--official-decimal-limit-kib", str(MEMORY_BYTES // 1024),
               "--cgroup-memory-max-bytes", str(MEMORY_BYTES), "--cgroup-path", str(args.cgroup_path),
               "--temporary-disk-limit-bytes", str(DISK_BYTES), "--scratch-path", str(RESULT), "--phase-marker-path", str(phases),
               "--guard-json", str(RESULT / "guard.json"), "--label", ID, "--max-logical-cpus", "1", "--",
               "/usr/bin/taskset", "-c", "2", "/usr/bin/timeout", "--kill-after=5", "1100", sys.executable, str(Path(__file__).resolve()), "--stage"]
    with (RESULT / "guard.stdout").open("xb") as stdout, (RESULT / "guard.stderr").open("xb") as stderr:
        completed = subprocess.run(command, cwd=PROJECT, stdout=stdout, stderr=stderr, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    stage_path = RESULT / "stage-decision.json"
    decision = json.loads(stage_path.read_text()) if stage_path.is_file() else {"status": "guard_terminated_without_stage_decision", "roundtrip_ok": None, "deterministic_ok": None, "mapping_gate_pass": None}
    decision.update({"schema": "gamma.enwiki9.public-fx2-fixture-diagnostic.v1", "candidate_id": ID, "guard_returncode": completed.returncode,
                     "guard": artifact(RESULT / "guard.json") if (RESULT / "guard.json").is_file() else None,
                     "objective_credit_bytes": 0, "larger_gate_authorized": False, "guard_command": command})
    if completed.returncode:
        decision["status"] = "execution_failed"
    write(RESULT / "decision.json", decision)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
