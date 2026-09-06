#!/usr/bin/env python3
"""Bounded P/K/F/S replay of the unchanged open MIDAS codec.

Corpus execution requires a frozen adaptive contract, published inputs and the
existing canonical job/cgroup admission. This runner creates no experiment or
promotion authority. Native returncodes are retained by NativeGate: the older
standalone execute() API collapses those codes into a single ValueError.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
SELF = "tools/midas_open_corpus_gate_v1.py"
CODEC = "tools/midas_open_codec_v1.py"
EVIDENCE = "operations/evidence/20260906_midas_relocatable_source_bundle_unit.json"
RUNTIME_EVIDENCE = "operations/evidence/20260905_parallel_native_cache_standalone_midas_unit.json"
PLAN_SCHEMA = "gamma.enwiki9.midas-open-corpus-gate-plan.v1"
ARMS = "PKFS"
MAX_RAW = 250000
MAX_FILE = 32 * 1024**2
NATIVE_AS = 512 * 1024**2
PHASE_STOP = 120
STATE_NAMES = ("complete_predictor", "parent_identity_projection", "normalized_coder", "reference_model_projection")


class EvidenceFailure(ValueError):
    """Missing, changed or contradictory execution evidence."""


def require(condition, message):
    if not condition:
        raise EvidenceFailure(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def bounded_read(path, maximum=MAX_FILE):
    """Read a regular, unaliased file once and verify the opened identity."""
    path = Path(os.path.abspath(path))
    require(path.resolve() == path, "aliased input or artifact: " + str(path))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, "unbounded or nonregular file: " + str(path))
        data = handle.read(maximum + 1)
        after = os.fstat(handle.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(len(data) == before.st_size and identity(before) == identity(after) == identity(path.stat()),
            "file changed during read: " + str(path))
    return data


def reference_bytes(root, ref, maximum=MAX_FILE):
    name = ref["path"]
    require(isinstance(name, str) and not Path(name).is_absolute() and ".." not in Path(name).parts,
            "reference escapes project")
    data = bounded_read(root / name, maximum)
    require(digest(data) == ref["sha256"].removeprefix("sha256:") and
            ("bytes" not in ref or len(data) == ref["bytes"]), "reference differs: " + name)
    return data


def contract_inputs(contract):
    rows = contract["inputs"]
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), "invalid inputs")
    inputs = {row["path"]: row for row in rows}
    require(len(inputs) == len(rows) and len({row["id"] for row in rows}) == len(rows), "duplicate input binding")
    return inputs


def bound_contract(candidate, *, validate=False):
    require(re.fullmatch(r"[a-z0-9_]+", candidate) is not None, "invalid candidate identity")
    name = "operations/adaptive/experiments/" + candidate + ".json"
    data = bounded_read(ROOT / name, 8 * 1024**2)
    reference = {"path": name, "sha256": "sha256:" + digest(data)}
    if not validate:
        require(json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) == reference, "canonical experiment is absent or changed")
    contract = json.loads(data)
    require(contract["status"] == "frozen" and contract["experimentId"] == candidate and
            contract["objectiveCreditBytes"] == 0 and contract["registrationTiming"] == "prospective",
            "experiment is not a prospectively frozen diagnostic")
    inputs = contract_inputs(contract)
    plans = [row for row in inputs.values() if row["id"] == "midas-gate-plan"]
    require(len(plans) == 1, "exactly one bound midas-gate-plan is required")
    plan = json.loads(reference_bytes(ROOT, plans[0], 1024**2))
    validate_plan(plan, candidate)
    return contract, inputs, plan


def validate_plan(plan, candidate):
    require(set(plan) == {"schema", "candidate_id", "population", "cached_manifest", "cached_binary",
                          "resources", "phase_wall_seconds"}, "unexpected gate plan fields")
    require(plan["schema"] == PLAN_SCHEMA and plan["candidate_id"] == candidate, "plan identity differs")
    require(type(plan["population"]["bytes"]) is int and 1 <= plan["population"]["bytes"] <= MAX_RAW,
            "population must contain 1..250000 published raw bytes")
    caps = plan["resources"]
    require(set(caps) == {"cpus", "memory_bytes", "scratch_bytes", "swap_bytes", "wall_seconds"} and
            caps["cpus"] == [2] and type(caps["swap_bytes"]) is int and caps["swap_bytes"] == 0 and
            type(caps["memory_bytes"]) is int and NATIVE_AS <= caps["memory_bytes"] <= 2 * 1024**3 and
            type(caps["scratch_bytes"]) is int and 1 <= caps["scratch_bytes"] <= 2 * 1024**3 and
            type(caps["wall_seconds"]) is int and 1 <= caps["wall_seconds"] <= 3600,
            "invalid canonical resource envelope")
    require(type(plan["phase_wall_seconds"]) is int and 1 <= plan["phase_wall_seconds"] <= PHASE_STOP,
            "phase wall stop must be positive and at most120 seconds")


def load_bound_modules(inputs):
    """Use verified source buffers for the standalone driver and its helpers."""
    names = (("lib.artifacts", "lib/artifacts.py"),
             ("lib.native_fixture_build_cache", "lib/native_fixture_build_cache.py"),
             ("bound_midas_codec", CODEC), ("bound_native_gate", "lib/fx2_native_gate_v1.py"))
    reference_bytes(ROOT, inputs[SELF])
    buffers = {name: reference_bytes(ROOT, inputs[path], 1024**2) for name, path in names}
    package = types.ModuleType("lib")
    package.__path__ = [str(ROOT / "lib")]
    sys.modules["lib"] = package
    loaded = {}
    for name, path in names:
        module = types.ModuleType(name)
        module.__file__ = str(ROOT / path)
        sys.modules[name] = module
        exec(compile(buffers[name], module.__file__, "exec"), module.__dict__)
        loaded[name] = module
    return loaded["bound_midas_codec"], loaded["bound_native_gate"]


def verify_build_sources(codec, manifest, inputs):
    require(manifest["schema"] == "gamma.native_fixture_build_cache.v1" and
            manifest["key"] == digest(canonical(manifest["identity"])) and
            manifest["manifest_sha256"] == digest(canonical({k: v for k, v in manifest.items() if k != "manifest_sha256"})),
            "cached build manifest authentication failed")
    identity = manifest["identity"]
    require(identity["cwd"] == str(ROOT) and identity["sources"] == [str(path) for path in codec.SOURCES] and
            identity["flags"] == [*codec.FLAGS, "-Werror=date-time"], "cached build law or source root differs")
    compiler = identity["compiler"]
    records = [*identity["dependencies"], compiler["executable"],
               *(row for row in compiler["toolchain_files"] if "path" in row)]
    for row in records:
        path = Path(row["path"])
        observed = codec.file_record(path)
        require(all(observed[key] == row[key] for key in ("path", "bytes", "sha256")), "cached dependency changed: " + str(path))
        if path.is_relative_to(ROOT):
            name = str(path.relative_to(ROOT))
            require(name in inputs and inputs[name]["sha256"].removeprefix("sha256:") == row["sha256"],
                    "local build dependency lacks an experiment binding: " + name)


def validate_authorities(codec, contract, inputs, plan):
    for key in ("population", "cached_manifest", "cached_binary"):
        ref = plan[key]
        require(ref["path"] in inputs and inputs[ref["path"]]["sha256"].removeprefix("sha256:") ==
                ref["sha256"].removeprefix("sha256:"), "plan input is not contract-bound: " + key)
        reference_bytes(ROOT, ref)
    require(contract["population"]["scopeBytes"] == plan["population"]["bytes"] and
            contract["population"]["scopeSymbols"] == 8 * plan["population"]["bytes"], "raw/bit coordinates differ")
    evidence = json.loads(reference_bytes(ROOT, inputs[EVIDENCE], 1024**2))
    require(evidence["id"] == "midas_relocatable_source_bundle_unit_20260906" and
            evidence["objective_credit_bytes"] == 0 and evidence["artifacts"]["relocated_binary_exact"] is True,
            "source reconstruction authority differs")
    for row in evidence["source_bindings"]:
        if row["path"] == "../../LICENSE":
            data = bounded_read(ROOT.parent.parent / "LICENSE", 1024**2)
            require(digest(data) == row["sha256"], "Gamma license changed")
        else:
            require(row["path"] in inputs and inputs[row["path"]]["sha256"].removeprefix("sha256:") == row["sha256"],
                    "unit source authority is not bound: " + row["path"])
            reference_bytes(ROOT, row, 1024**2)
    manifest = json.loads(reference_bytes(ROOT, plan["cached_manifest"], 4 * 1024**2))
    verify_build_sources(codec, manifest, inputs)
    binary = reference_bytes(ROOT, plan["cached_binary"])
    expected = {"bytes": len(binary), "sha256": digest(binary)}
    require(expected == manifest["binary"] == evidence["artifacts"]["original_binary"], "cached native binary lacks unit authority")
    reference = evidence["retained_reference"]
    require(reference["path"] == RUNTIME_EVIDENCE, "runtime authority path differs")
    runtime = json.loads(reference_bytes(ROOT, inputs[RUNTIME_EVIDENCE], 1024**2))
    require(digest(reference_bytes(ROOT, reference, 1024**2)) == reference["sha256"], "runtime evidence differs")
    return manifest, runtime["measured_inventory"]


def verify_inventory(codec, built, expected):
    observed = codec.inventory(built)
    require(observed["runtime"]["missing"] == [] and expected["runtime"]["missing"] == [], "runtime dependency evidence is incomplete")
    for field in ("local_source_files", "local_source_bytes", "toolchain_system_dependency_files"):
        require(observed[field] == expected[field], "standalone inventory changed: " + field)
    require(observed["runtime"]["files"] == expected["runtime"]["files"], "runtime files differ from unit authority")
    return observed


def state_parts(codec, path):
    components = codec.state_records(path)
    data = bounded_read(path, 8 * 1024**2)
    offset, parts = 5, {}
    for name in STATE_NAMES:
        size = struct.unpack_from("<Q", data, offset)[0]
        offset += 8
        parts[name] = data[offset:offset + size]
        require({"bytes": size, "sha256": digest(parts[name])} == components[name], "state component differs")
        offset += size
    require(offset == len(data), "state envelope has trailing bytes")
    return data, parts


def state_equal(gate, left, right, comparison):
    if left == right:
        return True
    first = next((index for index, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))
    begin = max(0, first - 16)
    if not (gate.result / "first-state-divergence.json").exists():
        gate.write("first-state-divergence.json", {"comparison": comparison, "first_byte": first,
                   "left_bytes": len(left), "right_bytes": len(right), "window_first_byte": begin,
                   "left_hex": left[begin:first + 17].hex(), "right_hex": right[begin:first + 17].hex(),
                   "scope": "terminal serialized state only; no intermediate boundary trace"})
    return False


def operation_evidence(gate, codec, arm, phase, output, raw_bytes, raw_limit):
    require(set(path.name for path in output.iterdir()) == {"data", "state.bin", "summary.json"}, "native output set differs")
    summary = json.loads(bounded_read(output / "summary.json", 65536))
    stdout = json.loads(bounded_read(gate.result / (arm + "-" + phase + ".stdout"), 65536))
    operation = "decode" if phase == "decode" else "encode"
    expected_updates = raw_bytes // 64 + (raw_bytes // 64 + (raw_bytes % 64 >= 32) if arm in "FS" else 0)
    require(summary == stdout and summary["schema"] == "midas_open_codec_operation_v1" and
            summary["operation"] == operation and summary["arm"] == arm and summary["frontend"] == "raw_identity_v1" and
            summary["raw_bytes"] == raw_bytes and summary["max_raw_bytes"] == raw_limit and
            summary["model_updates"] == expected_updates and summary["objective_credit_bytes"] == 0 and
            summary["resource_qualified"] is False, "native operation summary or causal update count differs")
    data = bounded_read(output / "data")
    state, parts = state_parts(codec, output / "state.bin")
    require(summary["state_bytes"] == len(state) and
            (len(data) == raw_bytes if operation == "decode" else len(data) == summary["archive_bytes"]), "native sizes differ")
    refs = {name: gate.artifact(output / name) for name in ("data", "state.bin", "summary.json")}
    gate.required.update(output / name for name in refs)
    return {"summary": summary, "files": refs}, data, state, parts


def compare_arms(gate, codec, built, population, phase_stop):
    """Twelve native phases; no archive-size stop suppresses a control."""
    raw = bounded_read(population, MAX_RAW)
    require(1 <= len(raw) <= MAX_RAW, "empty or over-bound population")
    gate.binaries[str(built.binary)] = digest(bounded_read(built.binary))
    outcomes, archives, states = {}, {}, {}
    for arm in ARMS:
        outputs, data, full, parts = {}, {}, {}, {}
        (gate.result / arm).mkdir()
        for phase in ("encode", "decode", "repeat"):
            source = population if phase == "encode" else gate.result / arm / ("encode" if phase == "decode" else "decode") / "data"
            output = gate.result / arm / phase
            operation = "decode" if phase == "decode" else "encode"
            gate.required.update(gate.result / (arm + "-" + phase + suffix)
                                 for suffix in (".stdout", ".stderr", ".execution.json"))
            gate.run(arm + "-" + phase, [str(built.binary), operation, arm, str(len(raw)), str(source), str(output)],
                     phase_stop, {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
            outputs[phase], data[phase], full[phase], parts[phase] = operation_evidence(
                gate, codec, arm, phase, output, len(raw), len(raw))
        require(data["decode"] == raw, arm + " raw inverse differs")
        require(data["repeat"] == data["encode"], arm + " archive repeat differs")
        require(state_equal(gate, full["encode"], full["decode"], arm + " encode/decode") and
                state_equal(gate, full["encode"], full["repeat"], arm + " encode/repeat"), arm + " complete final state differs")
        require(all(outputs[p]["summary"]["archive_bytes"] == len(data["encode"]) for p in outputs), arm + " archive sizes disagree")
        archives[arm], states[arm] = data["encode"], parts["encode"]
        outcomes[arm] = {"archive_bytes": len(data["encode"]), "operations": outputs,
                         "roundtrip_ok": True, "repeat_ok": True, "full_state_identity": True}
    pk_archive = archives["P"] == archives["K"]
    pk_parent = state_equal(gate, states["P"]["parent_identity_projection"], states["K"]["parent_identity_projection"], "P/K terminal parent projection")
    pk_reference = state_equal(gate, states["P"]["reference_model_projection"], states["K"]["reference_model_projection"], "P/K terminal reference projection")
    directional = len(archives["F"]) < len(archives["S"])
    gain = len(archives["P"]) - len(archives["F"])
    controls = pk_archive and pk_parent and pk_reference and directional
    verdict = "causal_control_failed" if not controls else "compression_loss" if gain <= 0 else "positive_component"
    return {"infrastructure_pass": True, "arms": outcomes, "pk_archive_identity": pk_archive,
            "pk_parent_projection_identity": pk_parent, "pk_reference_projection_identity": pk_reference,
            "all_arm_roundtrip": True, "all_arm_repeat": True, "all_arm_full_state_identity": True,
            "F_beats_S_archive": directional, "F_vs_P_archive_saved_bytes": gain,
            "F_vs_S_archive_saved_bytes": len(archives["S"]) - len(archives["F"]),
            "causal_controls_pass": controls, "compression_positive": gain > 0,
            "scientific_outcomes": {"causal_control": "passed" if controls else "failed",
                                    "compression": "positive" if gain > 0 else "loss_or_tie"},
            "scientific_verdict": verdict, "native_phases": 12, "raw_bytes": len(raw)}


def classify(error, commands=()):
    category = getattr(error, "category", None)
    code = commands[-1].get("returncode") if commands else None
    # A vanished process does not establish which resource, actor or fault
    # caused SIGKILL. Preserve the uncertainty independently of known stops.
    if category == "resource_or_signal_stop" or code in (137, -9):
        return "resource_or_signal_stop"
    # timeout preserves fatal child signals as128+signal. SIGXCPU/SIGXFSZ
    # specifically identify the codec's fixed CPU/file ceilings.
    if category == "budget_exhausted" or isinstance(error, TimeoutError) or (
            category == "execution_failed" and code in (124, 152, 153, -24, -25)):
        return "budget_exhausted"
    return "implementation_or_infrastructure_failure"


def finalize(gate, stage, verify):
    """Publish a non-passing checkpoint before indexing closed owned evidence."""
    stage["child_closure_ok"] = False
    try:
        gate.closure()
        stage["child_closure_ok"] = True
        verify()
        gate.verify()
    except Exception as error:
        stage.update(status="failed", infrastructure_pass=False, failure_class=classify(error), final_verification_error=str(error))
    # Verification includes a bounded ldd subprocess. Recheck closure even when
    # that verification failed, before reading any owned execution artifacts.
    try:
        gate.closure()
        stage["child_closure_ok"] = True
    except Exception as error:
        stage.update(status="failed", infrastructure_pass=False, child_closure_ok=False,
                     failure_class=classify(error), closure_error=str(error))
    stage["commands"] = gate.commands
    gate.write("stage-decision.json", {**stage, "status": "publishing", "infrastructure_pass": False})
    errors, artifacts = [], []
    if stage["child_closure_ok"]:
        try:
            def enumeration_error(error):
                errors.append({"path": str(error.filename), "error": str(error)})
            for directory, directories, names in os.walk(gate.result, followlinks=False, onerror=enumeration_error):
                base = Path(directory)
                for name in directories:
                    require(not (base / name).is_symlink(), "artifact directory is an alias")
                for name in sorted(names):
                    path = base / name
                    if path in (gate.result / "stage-decision.json", gate.result / "artifacts.json"):
                        continue
                    try:
                        bounded_read(path)
                        artifacts.append(gate.artifact(path))
                    except Exception as error:
                        errors.append({"path": str(path), "error": str(error)})
            indexed = {row["path"] for row in artifacts}
            for path in sorted(gate.required):
                if str(path.relative_to(gate.root)) not in indexed:
                    errors.append({"path": str(path), "error": "mandatory artifact has no successful fingerprint"})
        except Exception as error:
            errors.append({"path": str(gate.result), "error": str(error)})
    else:
        errors.append({"path": str(gate.result), "error": "artifact reads skipped because child closure failed"})
    try:
        gate.write("artifacts.json", {"complete": not errors, "files": sorted(artifacts, key=lambda row: row["path"]), "errors": errors})
        stage["artifacts"] = gate.artifact(gate.result / "artifacts.json")
    except Exception as error:
        errors.append({"path": "artifacts.json", "error": str(error)})
    stage["artifact_index_complete"] = not errors
    if errors:
        stage.update(status="failed", infrastructure_pass=False, artifact_index_errors=errors)
        stage.setdefault("failure_class", "implementation_or_infrastructure_failure")
    gate.write("stage-decision.json", stage)
    return stage


def seeded_cached_build(codec, inputs, plan, manifest):
    """Validate an existing entry without any compilation or miss fallback."""
    work = ROOT / "results" / plan["candidate_id"] / "work"
    require(work.is_dir() and work.resolve() == work, "missing or aliased preparation workspace")
    entry = work / "cache/entries" / manifest["key"]
    require(bounded_read(entry / "manifest.json", 4 * 1024**2) ==
            reference_bytes(ROOT, plan["cached_manifest"], 4 * 1024**2), "seeded cache manifest bytes differ")
    require(bounded_read(entry / "program") == reference_bytes(ROOT, plan["cached_binary"]), "seeded cache program bytes differ")
    verify_build_sources(codec, manifest, inputs)
    # Reuse the existing cache verifier, not build_cpp_cached(), whose miss
    # branch is intentionally capable of compiling. A miss here only fails.
    cache = sys.modules["lib.native_fixture_build_cache"]
    observed, reason = cache._cached(entry, manifest["identity"], manifest["key"])
    require(observed == manifest and reason == "verified", "frozen cache entry failed validation: " + reason)
    return cache.CachedCppBuild(entry / "program", True, reason, manifest)


def prepare(codec, inputs, plan, manifest, runtime):
    built = seeded_cached_build(codec, inputs, plan, manifest)
    inventory = verify_inventory(codec, built, runtime)
    verify_build_sources(codec, built.manifest, inputs)
    result = {"schema": "midas_open_gate_preparation_v1", "cache_hit": True,
              "manifest": built.manifest, "binary": codec.file_record(built.binary), "inventory": inventory}
    print(json.dumps(result, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--internal-prepare", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    require(not (args.validate_only and args.internal_prepare), "conflicting actions")
    contract, inputs, plan = bound_contract(args.candidate, validate=args.validate_only)
    codec, helper = load_bound_modules(inputs)
    manifest, runtime = validate_authorities(codec, contract, inputs, plan)
    if args.internal_prepare:
        prepare(codec, inputs, plan, manifest, runtime)
        return 0
    gate = helper.NativeGate(ROOT, args.candidate, plan["resources"], args.validate_only)
    if args.validate_only:
        print(json.dumps({"status": "preflight_pass", "raw_bytes": plan["population"]["bytes"],
                          "planned_phases": 13, "native_phases": 12, "corpus_executed": False}))
        return 0
    gate.required = {gate.result / arm / phase / name for arm in ARMS for phase in ("encode", "decode", "repeat")
                     for name in ("data", "state.bin", "summary.json")}
    gate.required.add(gate.result / "preparation.json")
    stage = {"schema": "gamma.enwiki9.midas-open-corpus-stage.v1", "candidate_id": args.candidate,
             "experiment": gate.reference, "objective": contract["objective"], "status": "running",
             "infrastructure_pass": False, "objective_credit_bytes": 0, "full_corpus_score_bytes": None,
             "complete_package_bytes": None, "complete_package_qualified": False, "resource_qualified": False,
             "larger_gate_authorized": False, "continuous_guard_decision": "pending canonical outer closure",
             "promotion_authorized": False,
             "synchronization_scope": "Exact complete terminal witnesses per arm, P/K terminal parent projections, raw inverses and repeated archives",
             "probability_boundary_trace_complete": False, "detailed_boundary_trace": None,
             "missing_diagnostics": ["Immutable standalone driver emits no every-midpoint or per-bit probability trace; terminal equality does not establish those unobserved boundaries"],
             "unphased_diagnostic_children": [],
             "native_bounds": {"raw_bytes": MAX_RAW, "address_space_bytes": NATIVE_AS,
                               "cpu_seconds": 120, "per_file_bytes": MAX_FILE, "threads": 1},
             "timing_authority": "shared-host diagnostic", "native_compression_is_infrastructure_requirement": False}
    built = None
    try:
        gate.retain_sources()
        population = gate.work / "population.raw"
        gate.copy(plan["population"]["path"], population)
        population.chmod(0o400)
        gate.retained[population] = digest(bounded_read(population, MAX_RAW))
        entry = gate.work / "cache/entries" / manifest["key"]
        gate.copy(plan["cached_manifest"]["path"], entry / "manifest.json")
        gate.copy(plan["cached_binary"]["path"], entry / "program")
        (entry / "program").chmod(0o500)
        gate.retained[entry / "manifest.json"] = plan["cached_manifest"]["sha256"].removeprefix("sha256:")
        gate.retained[entry / "program"] = plan["cached_binary"]["sha256"].removeprefix("sha256:")
        gate.run("prepare-cache-inventory", [sys.executable, "-I", "-S", "-B", str(ROOT / SELF),
                 "--candidate", args.candidate, "--internal-prepare"], min(PHASE_STOP, plan["phase_wall_seconds"]),
                 {"GAMMA_ENWIKI9_EXPERIMENT_JSON": json.dumps(gate.reference)}, work=ROOT)
        preparation = json.loads(bounded_read(gate.result / "prepare-cache-inventory.stdout", 4 * 1024**2))
        require(preparation["cache_hit"] is True and preparation["manifest"] == manifest and
                preparation["binary"]["sha256"] == manifest["binary"]["sha256"], "preparation differs from frozen build")
        gate.write("preparation.json", preparation)
        stage["measured_inventory"] = {"native_binary_bytes": manifest["binary"]["bytes"],
                                       "binary_plus_observed_runtime_bytes": preparation["inventory"]["binary_plus_observed_runtime_bytes"],
                                       "local_codec_source_bytes": preparation["inventory"]["local_source_bytes"],
                                       "additional_diagnostic_runner_source": gate.artifact(ROOT / SELF),
                                       "meaning": "Separate observed components; no selected submission form, source/runtime sum or complete package claim."}
        built = types.SimpleNamespace(binary=entry / "program", cache_hit=True, manifest=manifest)
        stage.update(compare_arms(gate, codec, built, population, plan["phase_wall_seconds"]), status="passed")
        require(len(gate.commands) == 13, "comparison phase population differs")
    except Exception as error:
        stage.update(status="failed", infrastructure_pass=False, failure_class=classify(error, gate.commands),
                     error=type(error).__name__ + ": " + str(error), failure_detail=getattr(error, "category", None))
    def verify():
        validate_authorities(codec, contract, inputs, plan)
        if built is not None:
            closed_build = seeded_cached_build(codec, inputs, plan, manifest)
            stage["unphased_diagnostic_children"].append({"tool": "/usr/bin/ldd", "scope": "final runtime inventory verification",
                                                          "wall_stop_seconds": 30, "covered_by_outer_guard": True,
                                                          "part_of_thirteen_measured_phases": False})
            verify_inventory(codec, closed_build, runtime)
    finalize(gate, stage, verify)
    return 0 if stage["infrastructure_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
