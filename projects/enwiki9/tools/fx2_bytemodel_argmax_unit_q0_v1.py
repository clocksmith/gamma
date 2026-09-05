#!/usr/bin/env python3
"""Guarded synthetic argmax comparison; no model, corpus or codec execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_bytemodel_argmax_unit_q0_v1"
RESULT = ROOT / "results" / ID
CONTRACT = ROOT / "operations/adaptive/experiments" / (ID + ".json")
ADAPTER = ROOT / "operations/provenance/public_fx2_argmax_adapter_v1.json"
UPSTREAM = ROOT / "external/fx2-cmix-transformer-v1"


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def checked_bytes(path: Path, expected: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("expected regular frozen source: " + str(path))
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected.removeprefix("sha256:"):
        raise ValueError("frozen source changed: " + str(path))
    return data


def prepare_sources() -> tuple[dict, dict[str, bytes]]:
    contract = json.loads(CONTRACT.read_text())
    for row in contract["inputs"]:
        checked_bytes(ROOT / row["path"], row["sha256"])
    adapter = json.loads(ADAPTER.read_text())
    sources = {}
    for row in adapter["files"]:
        original = checked_bytes(UPSTREAM / row["source_path"], row["source_sha256"])
        patched = original.decode()
        for change in row["replacements"]:
            if patched.count(change["before"]) != 1:
                raise ValueError("adapter preimage is not unique")
            patched = patched.replace(change["before"], change["after"], 1)
        data = patched.encode()
        if hashlib.sha256(data).hexdigest() != row["patched_sha256"]:
            raise ValueError("patched source hash differs")
        sources["original/" + row["source_path"]] = original
        sources["patched/" + row["source_path"]] = data
    model = next(row for row in adapter["source_closure"] if row["path"].endswith("/model.h"))
    model_bytes = checked_bytes(ROOT / model["path"], model["sha256"])
    sources["original/src/models/model.h"] = model_bytes
    sources["patched/src/models/model.h"] = model_bytes
    probe = adapter["probe"]
    sources["probe.cpp"] = checked_bytes(ROOT / probe["path"], probe["sha256"])
    toolchain = json.loads((ROOT / "operations/provenance/public_fx2_gcc15_toolchain_20260905.json").read_text())
    for row in toolchain["toolchain"]:
        if sha(Path(row["path"])) != row["sha256"]:
            raise ValueError("pinned toolchain changed: " + row["name"])
    compiler = next(row for row in toolchain["toolchain"] if row["name"] == "g++")
    if Path("/usr/bin/g++").resolve() != Path(compiler["path"]):
        raise ValueError("g++ no longer resolves to the pinned compiler")
    return contract, sources


def verify_materialized(sources: dict[str, bytes], work: Path) -> None:
    for name, expected in sources.items():
        actual = checked_bytes(work / name, hashlib.sha256(expected).hexdigest())
        if actual != expected:
            raise ValueError("retained source bytes differ: " + name)


def marker(phase: str, event: str) -> None:
    path = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    with path.open("a") as handle:
        handle.write(json.dumps({"phase": phase, "event": event}) + "\n")


def execute(phase: str, command: list[str], cap: int, work: Path) -> dict:
    from lib.artifacts import atomic_write_json
    command = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=2", str(cap), *command]
    marker(phase, "start")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    with (RESULT / (phase + ".stdout")).open("xb") as out, (RESULT / (phase + ".stderr")).open("xb") as err:
        done = subprocess.run(command, cwd=work,
                              env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(work / "tmp")},
                              stdout=out, stderr=err)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt = {"phase": phase, "command": command, "returncode": done.returncode,
               "elapsed_seconds": time.monotonic() - start, "elapsed_cap_seconds": cap,
               "user_cpu_seconds": after.ru_utime - before.ru_utime,
               "system_cpu_seconds": after.ru_stime - before.ru_stime,
               "timing_authority": "shared-host diagnostic; not isolated argmax or codec timing"}
    atomic_write_json(RESULT / (phase + ".execution.json"), receipt)
    marker(phase, "end")
    if done.returncode:
        raise RuntimeError(phase + " exited " + str(done.returncode))
    return receipt


def validate_probe(value: dict) -> None:
    expected = {"status": "pass", "cpu": 2, "repeats": 2, "row_families": 32,
                "truth_paths_per_row": 256, "predicts_per_bit": 2, "repeat_exact": True,
                "exact_state_checks_per_repeat": 819200,
                "exact_probability_row_checks_per_repeat": 8388608,
                "exact_repeat_reference_words": 1024000}
    for name, wanted in expected.items():
        if value.get(name) != wanted:
            raise ValueError("unit coverage or equality differs: " + name)
    if len(value["rows"]) != 32 or len({row["row"] for row in value["rows"]}) != 32:
        raise ValueError("row coverage differs")
    parent = cached = hits = fallbacks = 0
    for row in value["rows"]:
        arms = row["arms"]
        if set(arms) != {"P", "K", "D", "C"}:
            raise ValueError("arm population differs")
        for name, arm in arms.items():
            if arm["predict_calls"] != 4096 or arm["scans"] + arm["cache_hits"] != 4096:
                raise ValueError("prediction accounting differs")
            if name != "D" and (arm["argmax_comparisons"] != 257024 or arm["cache_hits"] != 0):
                raise ValueError("control departed from original scan")
            if arm["forced_invalidations"] != (4096 if name == "C" else 0):
                raise ValueError("forced invalidation control differs")
        parent += arms["P"]["argmax_comparisons"]
        cached += arms["D"]["argmax_comparisons"]
        hits += arms["D"]["cache_hits"]
        fallbacks += arms["D"]["nan_bot_fallbacks"]
    if not 0 < cached < parent or not hits or not fallbacks:
        raise ValueError("cache reduction or NaN control missing")
    for key, observed in (("parent_argmax_comparisons_per_repeat", parent),
                          ("cached_argmax_comparisons_per_repeat", cached),
                          ("cached_hits_per_repeat", hits), ("nan_fallbacks_per_repeat", fallbacks)):
        if value[key] != observed:
            raise ValueError("counter summary differs: " + key)


def finalize(job_id: str) -> int:
    from lib.artifacts import artifact_ref, atomic_write_json
    matches = [path for state in ("completed", "failed", "cancelled")
               for path in (ROOT / "operations/adaptive" / state).glob("*" + job_id + ".json")]
    if len(matches) != 1 or (RESULT / "decision.json").exists():
        raise ValueError("require one terminal job and a new final decision")
    job = json.loads(matches[0].read_text())
    if job["candidate_id"] != ID:
        raise ValueError("terminal job belongs to another candidate")
    guard_path = ROOT / job["execution_resources"]["guard_path"]
    guard = json.loads(guard_path.read_text())
    stage = json.loads((RESULT / "stage-decision.json").read_text())
    budget = job["resource_budget"]
    guarded = (job["state"] == "completed" and job["returncode"] == 0
               and guard["returncode"] == 0 and guard["status"] == "complete"
               and not any(guard["guards"].values()) and all(guard["measurements"].values())
               and job["execution_resources"]["cleanup_complete"]
               and budget["cpus"] == [2] and budget["memory_bytes"] == 536870912
               and budget["scratch_bytes"] == 67108864 and budget["swap_bytes"] == 0
               and budget["wall_seconds"] == 150
               and guard["cgroup"]["memory_max_bytes"] == 536870912
               and guard["peaks"]["cgroup_memory_peak_bytes"] <= 536870912
               and guard["peaks"]["max_sampled_scratch_logical_bytes"] <= 67108864
               and guard["peaks"]["max_sampled_scratch_allocated_bytes"] <= 67108864
               and guard["peak_sample"]["allowed_cpu_union"] == [2])
    passed = stage["status"] == "passed" and guarded
    receipt = {**stage, "schema": "gamma.enwiki9.fx2-argmax-terminal.v1",
               "status": "passed" if passed else "failed", "job_id": job_id,
               "job": artifact_ref(matches[0], ROOT), "guard": artifact_ref(guard_path, ROOT),
               "candidate_revision": job["candidate_revision"],
               "candidate_tree_sha256": job["candidate_tree_sha256"],
               "experiment": job["experiment"], "guards_pass": guarded,
               "resource_peaks": guard["peaks"], "missing_diagnostics": job["execution_resources"].get("missing_diagnostics", []),
               "resource_qualification": False, "decision": "hold",
               "decision_scope": "Synthetic exact state equivalence and comparisons only; native codec and uninstrumented runtime require a separate contract.",
               "artifacts": [artifact_ref(path, ROOT) for path in sorted(RESULT.rglob("*")) if path.is_file()]}
    atomic_write_json(RESULT / "decision.json", receipt)
    print(json.dumps({"candidate_id": ID, "status": receipt["status"], "guards_pass": guarded,
                      "decision": str((RESULT / "decision.json").relative_to(ROOT))}))
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--finalize", metavar="JOB_ID")
    args = parser.parse_args()
    contract, sources = prepare_sources()
    if args.validate_only:
        print(json.dumps({"valid": True, "frozen_inputs_verified": len(contract["inputs"]),
                          "retained_source_files": len(sources),
                          "retained_source_bytes": sum(map(len, sources.values())),
                          "compile_or_probe_executed": False, "memory_cap_bytes": 536870912,
                          "scratch_cap_bytes": 67108864, "compile_cap_seconds": 60,
                          "probe_cap_seconds": 30, "aggregate_cap_seconds": 150}))
        return 0
    sys.path.insert(0, str(ROOT))
    from lib.artifacts import artifact_ref, atomic_write_json
    if args.finalize:
        return finalize(args.finalize)
    if os.sched_getaffinity(0) != {2}:
        raise RuntimeError("pin the parent lab process to CPU 2 before launch")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError("canonical executor must provide an empty result directory")
    work = RESULT / "work"
    (work / "tmp").mkdir(parents=True)
    stage = {"schema": "gamma.enwiki9.fx2-argmax-stage.v1", "candidate_id": ID,
             "status": "running", "scope_symbols": 8192, "objective_credit_bytes": 0,
             "full_corpus_score_bytes": None, "Gamma_compression_gain_bytes": None,
             "production_speedup": None, "larger_gate_authorized": False,
             "continuous_guard_decision": "pending canonical outer guard closure"}
    try:
        for name, data in sources.items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o444)
        verify_materialized(sources, work)
        atomic_write_json(RESULT / "source-manifest.json", [artifact_ref(work / name, ROOT) for name in sources])
        adapter = json.loads(ADAPTER.read_text())
        values = {"original": str(work / "original"), "patched": str(work / "patched"),
                  "probe": str(work / "probe.cpp"), "output": str(work)}
        compile_argv = [arg.format(**values) for arg in adapter["compile_argv_template"]]
        execute("compile", compile_argv, 60, work)
        verify_materialized(sources, work)
        binary = work / "fx2_bytemodel_argmax_probe"
        binary.chmod(0o555)
        binary_ref = artifact_ref(binary, ROOT)
        atomic_write_json(RESULT / "build.json", {"binary": binary_ref, "source_manifest": artifact_ref(RESULT / "source-manifest.json", ROOT),
                          "compiler_flags": compile_argv, "instrumentation": "comparison counts enabled; no production speed claim"})
        for phase in ("unit", "repeat"):
            checked_bytes(binary, binary_ref["sha256"])
            verify_materialized(sources, work)
            execute(phase, [str(binary), "--all-arms"], 30, work)
            value = json.loads((RESULT / (phase + ".stdout")).read_text())
            validate_probe(value)
            atomic_write_json(RESULT / (phase + ".json"), value)
        if (RESULT / "unit.stdout").read_bytes() != (RESULT / "repeat.stdout").read_bytes():
            raise ValueError("independent process receipt repeat differs")
        verify_materialized(sources, work)
        checked_bytes(binary, binary_ref["sha256"])
        unit = json.loads((RESULT / "unit.json").read_text())
        stage.update({"status": "passed", "exact_state_agreement": True, "repeat_exact": True,
                      "parent_comparisons_per_repeat": unit["parent_argmax_comparisons_per_repeat"],
                      "cached_comparisons_per_repeat": unit["cached_argmax_comparisons_per_repeat"],
                      "comparisons_avoided_per_repeat": unit["parent_argmax_comparisons_per_repeat"] - unit["cached_argmax_comparisons_per_repeat"],
                      "state_checks_per_repeat": unit["exact_state_checks_per_repeat"],
                      "probability_row_checks_per_repeat": unit["exact_probability_row_checks_per_repeat"],
                      "row_families": 32, "independent_processes": 2, "internal_repeats_per_process": 2})
    except Exception as error:
        stage.update({"status": "execution_failed", "error": type(error).__name__ + ": " + str(error)})
    atomic_write_json(RESULT / "stage-decision.json", stage)
    return 0 if stage["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
