#!/usr/bin/env python3
"""Prospective, guarded P/L/D/C replay of two published raw Wiki slices.

This is a diagnostic driver using NativeGate and the shared artifact primitives.
Each codec invocation is a fresh CLI process. Worker stage decisions remain
provisional until the canonical outer job and resource guard close.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
ID = "wiki_schema_exact_transfer250k_q0_v1"
SELF = "tools/" + ID + ".py"
CODEC = "tools/wiki_schema_exact_codec_v1.py"
TESTS = "tests/test_wiki_schema_exact_codec.py"
UNIT = "operations/evidence/20260906_wiki_schema_exact_unit.json"
PINNED = {
    CODEC: "6b9666e4ae7e0fc08518ec62b2a086a0e1a4f4d21b2b5b0ac5a87d771b40bfac",
    TESTS: "fddf4a17f0aaffc2fcaac6033e4f815494de48b13e2d9644e7dd3526079bbb04",
}
ARMS, PHASES = "PLDC", ("encode", "decode", "repeat")
OPTIONS = {"block_size": 4096, "max_record": 4096, "max_rules": 256,
           "max_dictionary_bytes": 1048576}
CAPS = {"cpus": [2], "memory_bytes": 2 * 1024**3, "scratch_bytes": 256 * 1024**2,
        "swap_bytes": 0, "wall_seconds": 1800}
MAX_FILE, PYTHON_AS, PHASE_STOP = 32 * 1024**2, 512 * 1024**2, 120
POPULATIONS = [
    {"name": "opening", "offset": 0, "bytes": 250000,
     "path": "results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.raw",
     "sha256": "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"},
    {"name": "distant", "offset": 500000000, "bytes": 250000,
     "path": "results/fx2_weight_native_transfer250k_q0_v1/work/native/distant.raw",
     "sha256": "f0d01801279f29e353d1dd932a43133e191ea905da6626575b1ee174957717b8"},
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path, maximum=MAX_FILE):
    """Bounded regular-file read; shared artifact helper fingerprints afterward."""
    path = Path(os.path.abspath(path))
    require(path.resolve() == path, "aliased file: " + str(path))
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, "nonregular or oversized file: " + str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        data = handle.read(maximum + 1)
        after = os.fstat(handle.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(len(data) == before.st_size and identity(before) == identity(opened) == identity(after) == identity(path.lstat()),
            "file changed while read: " + str(path))
    return data


def file_record(path):
    data = read_bytes(path)
    return {"path": str(path), "bytes": len(data), "sha256": digest(data)}


def bound_bytes(inputs, name):
    require(name in inputs and not Path(name).is_absolute() and ".." not in Path(name).parts, "unbound project input: " + name)
    data = read_bytes(ROOT / name)
    ref = inputs[name]
    require(digest(data) == ref["sha256"].removeprefix("sha256:") and
            ("bytes" not in ref or len(data) == ref["bytes"]), "changed bound input: " + name)
    return data


def load_module(name, source, content):
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / source)
    sys.modules[name] = module
    exec(compile(content, module.__file__, "exec"), module.__dict__)
    return module


def bootstrap(validate=False):
    name = "operations/adaptive/experiments/" + ID + ".json"
    content = read_bytes(ROOT / name)
    reference = {"path": name, "sha256": "sha256:" + digest(content)}
    if not validate:
        require(json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) == reference, "canonical experiment binding differs")
    contract = json.loads(content)
    require(contract["experimentId"] == ID and contract["status"] == "frozen" and
            contract["registrationTiming"] == "prospective" and contract["objectiveCreditBytes"] == 0 and
            contract["parent"] is None, "candidate is not a frozen independent diagnostic")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]) and len({r["id"] for r in inputs.values()}) == len(inputs), "duplicate bindings")
    # Admit every input before the immutable helper performs its own once-read
    # loading. This prevents an unbound/special file reaching helper bootstrap.
    buffers = {path: bound_bytes(inputs, path) for path in inputs}
    plans = [path for path, ref in inputs.items() if ref["id"] == "schema-gate-plan"]
    require(len(plans) == 1, "exactly one schema-gate-plan binding is required")
    plan = json.loads(buffers[plans[0]])
    validate_plan(plan)
    require(SELF in buffers and "lib/artifacts.py" in buffers, "runner/artifact source binding missing")
    for path, expected in PINNED.items():
        require(digest(buffers[path]) == expected, "reviewed schema source changed: " + path)
    unit = json.loads(buffers[UNIT])
    require(unit["id"] == "wiki_schema_exact_unit_20260906" and unit["validation"]["returncode"] == 0 and
            unit["validation"]["tests_passed"] == 14 and unit["corpus_executed"] is False,
            "synthetic authority is missing or failed")
    unit_sources = {row["path"]: row for row in unit["source_bindings"]}
    require(set(unit_sources) == set(PINNED), "synthetic source population differs")
    for path, expected in PINNED.items():
        require(unit_sources[path]["sha256"] == expected and unit_sources[path]["bytes"] == len(buffers[path]),
                "unit source binding differs")
    for population in POPULATIONS:
        data = buffers[population["path"]]
        require(len(data) == population["bytes"] and digest(data) == population["sha256"], "raw population differs")
    helper = load_module("bound_schema_native_gate", "lib/fx2_native_gate_v1.py", buffers["lib/fx2_native_gate_v1.py"])
    codec = load_module("bound_schema_codec", CODEC, buffers[CODEC])
    verify_runtime(plan)
    return contract, plan, helper, codec


def validate_plan(plan):
    require(set(plan) == {"schema", "candidate_id", "populations", "codec_options", "resources",
                          "phase_wall_seconds", "python_executable", "runtime_files"}, "gate plan fields differ")
    require(plan["schema"] == "gamma.enwiki9.wiki-schema-exact-gate-plan.v1" and plan["candidate_id"] == ID,
            "gate plan identity differs")
    require(plan["populations"] == POPULATIONS and plan["codec_options"] == OPTIONS and
            plan["resources"] == CAPS and type(plan["phase_wall_seconds"]) is int and
            plan["phase_wall_seconds"] == PHASE_STOP, "frozen population/options/resource law differs")
    rows = plan["runtime_files"]
    require(isinstance(rows, list) and rows and all(set(row) == {"path", "bytes", "sha256"} for row in rows),
            "runtime file inventory differs")
    require(len({row["path"] for row in rows}) == len(rows), "duplicate runtime paths")
    require(all(Path(row["path"]).is_absolute() and type(row["bytes"]) is int and 0 < row["bytes"] <= MAX_FILE for row in rows),
            "runtime file is not bounded and absolute")
    required = {str(Path(path).resolve()) for path in (sys.executable, "/usr/bin/prlimit", "/usr/bin/timeout")}
    require(plan["python_executable"] == str(Path(sys.executable).resolve()) and
            required <= {row["path"] for row in rows}, "Python or process supervisor is unbound")


def observed_runtime_paths():
    """Observe this supervisor after loading the same codec, without a child."""
    paths = {str(Path(sys.executable).resolve())}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename and Path(filename).is_absolute():
            path = Path(filename).resolve()
            if not path.is_relative_to(ROOT):
                paths.add(str(path))
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[5].startswith("/"):
            require(not fields[5].endswith(" (deleted)"), "loaded runtime mapping was deleted")
            path = Path(fields[5]).resolve()
            if not path.is_relative_to(ROOT):
                paths.add(str(path))
    return paths


def verify_runtime(plan):
    validate_plan(plan)
    refs = {row["path"]: row for row in plan["runtime_files"]}
    for path, expected in refs.items():
        require(file_record(Path(path)) == expected, "bound runtime changed: " + path)
    observed = observed_runtime_paths()
    require(observed <= refs.keys(), "observed supervisor runtime is unbound: " + ", ".join(sorted(observed - refs.keys())))
    return {"declared_files": plan["runtime_files"], "observed_supervisor_paths": sorted(observed),
            "declared_unique_bytes": sum(row["bytes"] for row in refs.values()),
            "scope": "Supervisor module files and mapped libraries after importing the identical codec; child import closure not independently traced",
            "child_runtime_closure_complete": False, "complete_submission_package_bytes": None}


def same_bytes(gate, left, right, label):
    if left == right:
        return
    first = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))
    start = max(0, first - 32)
    gate.write("first-divergence.json", {"comparison": label, "first_byte": first,
               "left_bytes": len(left), "right_bytes": len(right), "context_first_byte": start,
               "left_hex": left[start:start+96].hex(), "right_hex": right[start:start+96].hex()})
    raise ValueError(label + " differs at byte " + str(first))


def dictionary_projection(receipt):
    return [{key: row[key] for key in ("index", "mode", "dictionary_before", "dictionary_after")}
            for row in receipt["blocks"]]


def validate_accounting(receipt, archive_bytes, raw_bytes):
    n = (raw_bytes + OPTIONS["block_size"] - 1) // OPTIONS["block_size"]
    rows, account = receipt["blocks"], receipt["accounting"]
    require(len(rows) == n and [row["index"] for row in rows] == list(range(n)), "block population differs")
    require([row["raw_bytes"] for row in rows] == [min(OPTIONS["block_size"], raw_bytes-i*OPTIONS["block_size"]) for i in range(n)], "raw block lengths differ")
    padding, common = 8*((n+7)//8)-n, 8*(72+40*n) + 8*((n+7)//8)-n
    require(account["archive_bits"] == 8*archive_bytes and account["mode_bits"] == n and
            account["bitmap_padding_bits"] == padding and account["H_bits"] == common,
            "framing accounting differs")
    require(8*archive_bytes == sum(row["selected_bits"] for row in rows) + n + common,
            "selected body accounting differs")
    baseline = 72+(n+7)//8+40*n+sum(row["baseline_bits"] for row in rows)//8
    require(account["equivalent_framed_baseline_bytes"] == baseline, "framed baseline accounting differs")
    for row in rows:
        require(row["mode"] in (0, 1) and row["baseline_bits"] % 8 == 0 and row["selected_bits"] % 8 == 0,
                "invalid block mode/body bit count")
        if receipt["arm"] == "P":
            require(row["mode"] == 0 and row["grammar_bits"] is None and row["selected_bits"] == row["baseline_bits"], "P baseline differs")
        else:
            require(row["grammar_bits"] % 8 == 0 and row["mode"] == int(row["grammar_bits"] < row["baseline_bits"]) and
                    row["selected_bits"] == min(row["baseline_bits"], row["grammar_bits"]), "fallback selection differs")
    if receipt["arm"] == "P":
        require(account["bound_applies"] is False and account["bound_pass"] is None, "P claims a treatment bound")
    else:
        rhs = sum(min(row["baseline_bits"], row["grammar_bits"]) for row in rows) + n + common
        require(account["bound_applies"] is True and account["bound_pass"] is True and
                account["sum_min_Bj_Gj_plus_N_plus_H_bits"] == rhs == 8*archive_bytes,
                "exact block fallback bound failed")
    return baseline


def compare_population(gate, codec_path, plan, population):
    name, raw_path = population["name"], gate.work / (population["name"] + ".raw")
    raw = read_bytes(raw_path, 250000)
    require(len(raw) == population["bytes"] and digest(raw) == population["sha256"], "materialized population differs")
    arms, archives, projections = {}, {}, {}
    for arm in ARMS:
        directory = gate.result / name / arm
        directory.mkdir(parents=True)
        data, receipts, outputs = {}, {}, {}
        for phase in PHASES:
            label = name + "-" + arm + "-" + phase
            output = directory / (phase + ".bin")
            receipt_path = directory / (phase + ".receipt.json")
            operation = "decode" if phase == "decode" else "encode"
            source = directory / "encode.bin" if phase == "decode" else raw_path
            pycache = gate.work / "tmp" / (label + "-pycache")
            pycache.mkdir()
            require(read_bytes(codec_path) == gate.buffers[CODEC], "retained codec source changed before phase")
            argv = ["/usr/bin/prlimit", "--as=" + str(PYTHON_AS), "--cpu=120", "--fsize=" + str(MAX_FILE), "--",
                    plan["python_executable"], "-I", "-S", "-B", "-X", "pycache_prefix=" + str(pycache),
                    str(codec_path), operation, str(source), str(output), "--receipt", str(receipt_path)]
            if operation == "encode":
                argv += ["--arm", arm]
                for option, value in OPTIONS.items():
                    argv += ["--" + option.replace("_", "-"), str(value)]
            gate.run(label, argv, PHASE_STOP)
            require(read_bytes(codec_path) == gate.buffers[CODEC], "retained codec source changed")
            data[phase] = read_bytes(output)
            receipt = json.loads(read_bytes(receipt_path))
            require(receipt == json.loads(read_bytes(gate.result / (label + ".stdout"))), "stdout/receipt differ: " + label)
            require(receipt["schema"] == "gamma.wiki-schema-exact-codec.v1" and receipt["arm"] == arm and
                    receipt["raw_bytes"] == len(raw) and receipt["raw_sha256"] == digest(raw) and
                    receipt["score_credit_bytes"] == 0 and receipt["full_corpus_score_bytes"] is None and
                    receipt["complete_executable_package_bytes"] is None and
                    receipt["uninterrupted_fx2_equivalence_claimed"] is False, "codec receipt scope differs")
            archive = data["encode"] if phase == "decode" else data[phase]
            require(receipt["archive_bytes"] == len(archive) and receipt["archive_sha256"] == digest(archive), "archive receipt differs")
            if operation == "encode":
                validate_accounting(receipt, len(archive), len(raw))
            receipts[phase] = receipt
            outputs[phase] = {"data": gate.artifact(output), "receipt": gate.artifact(receipt_path)}
        same_bytes(gate, data["decode"], raw, name + "/" + arm + " raw inverse")
        same_bytes(gate, data["repeat"], data["encode"], name + "/" + arm + " archive repeat")
        require(receipts["repeat"] == receipts["encode"], "independent encode receipt differs")
        projection = dictionary_projection(receipts["encode"])
        require(all(dictionary_projection(receipts[p]) == projection for p in PHASES), "same-arm block dictionary digests differ")
        selected = [row for row in receipts["encode"]["blocks"] if row["mode"] == 1]
        counts = {key: sum(row["grammar_proposal"][key] for row in selected)
                  for key in ("references", "exceptions", "shuffled_queries", "shuffled_associations")}
        arms[arm] = {"archive_bytes": len(data["encode"]), "roundtrip_ok": True, "deterministic_ok": True,
                     "block_dictionary_digests_equal": True, "selected_grammar_blocks": len(selected),
                     "selected_grammar_counts": counts, "operations": outputs}
        archives[arm], projections[arm] = len(data["encode"]), projection
        require(receipts["encode"]["accounting"]["equivalent_framed_baseline_bytes"] == archives["P"], "arm uses a different framed baseline")
    states = lambda arm: [(r["dictionary_before"], r["dictionary_after"]) for r in projections[arm]]
    require(all(states(arm) == states("P") for arm in ARMS), "cross-arm reconstructed dictionary states differ")
    comparisons = {"D_lt_" + arm: archives["D"] < archives[arm] for arm in "PLC"}
    active = arms["C"]["selected_grammar_counts"]["shuffled_associations"] > 0
    return {"population": population, "arms": arms, **comparisons,
            "D_saved_bytes": {arm: archives[arm]-archives["D"] for arm in "PLC"},
            "D_framed_P_bound_pass": archives["D"] <= archives["P"],
            "selected_C_control_active": active, "selected_D_reference_active": arms["D"]["selected_grammar_counts"]["references"] > 0,
            "all_arm_dictionary_states_equal": True,
            "control_outcome": "inactive" if not active else "D_smaller" if comparisons["D_lt_C"] else "no_directional_gain",
            "compression_outcome": "smaller_than_framed_P" if comparisons["D_lt_P"] else "tie_or_larger",
            "population_scope": "Previously examined cold raw slice, no statistical holdout or mature-history claim"}


def classify(error, commands=()):
    category = getattr(error, "category", None)
    code = commands[-1].get("returncode") if commands else None
    if category == "resource_or_signal_stop" or code in (137, -9):
        return "resource_or_signal_stop"
    if category == "budget_exhausted" or isinstance(error, TimeoutError) or (
            category == "execution_failed" and code in (124, 152, 153, -24, -25)):
        return "budget_exhausted"
    return "implementation_or_infrastructure_failure"


def finalize(gate, stage, plan):
    stage["child_closure_ok"] = False
    try:
        gate.closure()
        stage["child_closure_ok"] = True
        gate.verify()
        stage["runtime_inventory"] = verify_runtime(plan)
    except Exception as error:
        stage.update(status="failed", infrastructure_pass=False, failure_class=classify(error), final_verification_error=str(error))
    stage["commands"] = gate.commands
    gate.write("stage-decision.json", {**stage, "status": "publishing", "infrastructure_pass": False})
    errors, artifacts = [], []
    if stage["child_closure_ok"]:
        def enumeration_error(error):
            errors.append({"path": str(error.filename), "error": str(error)})
        for directory, directories, names in os.walk(gate.result, followlinks=False, onerror=enumeration_error):
            base = Path(directory)
            for name in list(directories):
                if (base / name).is_symlink():
                    directories.remove(name)
                    errors.append({"path": str(base / name), "error": "artifact directory is an alias"})
            for name in sorted(names):
                path = base / name
                if path.name in ("stage-decision.json", "artifacts.json") and path.parent == gate.result:
                    continue
                try:
                    read_bytes(path)
                    artifacts.append(gate.artifact(path))
                except Exception as error:
                    errors.append({"path": str(path), "error": str(error)})
        indexed = {row["path"] for row in artifacts}
        for path in sorted(gate.required):
            if str(path.relative_to(ROOT)) not in indexed:
                errors.append({"path": str(path), "error": "mandatory output lacks fingerprint"})
    else:
        errors.append({"path": str(gate.result), "error": "artifact reads skipped because owned children remain"})
    try:
        gate.write("artifacts.json", {"files": artifacts, "complete": not errors, "errors": errors})
        stage["artifacts"] = gate.artifact(gate.result / "artifacts.json")
    except Exception as error:
        errors.append({"path": "artifacts.json", "error": str(error)})
    stage["artifact_index_complete"] = not errors
    if errors:
        stage.update(status="failed", infrastructure_pass=False, artifact_index_errors=errors)
        stage.setdefault("failure_class", "implementation_or_infrastructure_failure")
    gate.write("stage-decision.json", stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    contract, plan, helper, codec = bootstrap(args.validate_only)
    gate = helper.NativeGate(ROOT, ID, CAPS, args.validate_only)
    if args.validate_only:
        print(json.dumps({"status": "preflight_pass", "populations": POPULATIONS, "planned_phases": 24,
                          "corpus_executed": False, "complete_package_bytes": None}, sort_keys=True))
        return 0
    gate.required = {gate.result / p["name"] / arm / (phase + suffix)
                     for p in POPULATIONS for arm in ARMS for phase in PHASES
                     for suffix in (".bin", ".receipt.json")}
    gate.required.update(gate.result / (p["name"] + "-" + arm + "-" + phase + suffix)
                         for p in POPULATIONS for arm in ARMS for phase in PHASES
                         for suffix in (".stdout", ".stderr", ".execution.json"))
    stage = {"schema": "gamma.enwiki9.wiki-schema-exact-transfer-stage.v1", "candidate_id": ID,
             "experiment": gate.reference, "objective": contract["objective"], "status": "running",
             "infrastructure_pass": False, "objective_credit_bytes": 0, "full_corpus_score_bytes": None,
             "complete_package_bytes": None, "promotion_authorized": False, "larger_gate_authorized": False,
             "resource_qualified": False, "continuous_guard_decision": "pending canonical outer job and guard closure",
             "timing_authority": "shared-host diagnostic", "planned_phases": 24, "populations": {},
             "frontend": "raw_identity_v1", "fx2_archive_or_trace_reuse": False,
             "dictionary_equality_scope": "SHA256 of the complete serialized learned state at every block boundary; not a Python heap witness",
             "savings_bound_scope": "Exact archive bound relative to identically framed independently reset zlib blocks; excludes package",
             "economic_result_is_infrastructure_requirement": False,
             "control_scope": "C rotates the target-selected best prior schema; tests association disruption, not independent predictive evidence"}
    try:
        gate.retain_sources()
        codec_path = gate.work / "source" / CODEC
        for population in POPULATIONS:
            path = gate.work / (population["name"] + ".raw")
            gate.copy(population["path"], path)
            path.chmod(0o400)
            gate.retained[path] = population["sha256"]
        inventory = verify_runtime(plan)
        runtime_refs = {row["path"]: row for row in plan["runtime_files"]}
        for executable in ("/usr/bin/prlimit", plan["python_executable"]):
            gate.binaries[executable] = runtime_refs[str(Path(executable).resolve())]["sha256"]
        option_text = json.dumps(OPTIONS, sort_keys=True, separators=(",", ":"))
        stage["package_inventory"] = {"codec_source": gate.artifact(codec_path),
            "diagnostic_runner_source": gate.artifact(ROOT / SELF), "test_source": gate.artifact(ROOT / TESTS),
            "codec_source_plus_option_bytes": len(gate.buffers[CODEC])+len(option_text.encode()),
            "option_text": option_text, "runtime": inventory, "complete_package_bytes": None,
            "unknown_items": ["independently observed child dependency closure", "selected standalone packaging form and licenses", "isolated resource qualification"],
            "meaning": "Separate explicit source/options and observed runtime inventories; no source/runtime sum or earned package credit"}
        for population in POPULATIONS:
            stage["populations"][population["name"]] = compare_population(gate, codec_path, plan, population)
        require(len(gate.commands) == 24 and all(row["returncode"] == 0 for row in gate.commands), "phase population differs")
        stage.update(status="passed", infrastructure_pass=True, roundtrip_ok=True, deterministic_ok=True,
                     all_block_dictionary_digests_equal=True)
    except Exception as error:
        stage.update(status="failed", infrastructure_pass=False, failure_class=classify(error, gate.commands),
                     error=type(error).__name__ + ": " + str(error), failure_detail=getattr(error, "category", None))
    finalize(gate, stage, plan)
    return 0 if stage["infrastructure_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
