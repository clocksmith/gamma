#!/usr/bin/env python3
"""Canonical bounded FX2 field diagnostic, with an external parent Q16 stream.

--validate-only authenticates metadata and source without opening corpus, model,
dictionary or trace payloads. It grants no launch authority. Normal execution
uses NativeGate admission and lib.driver; the decoder CLI has no truth input.
Archive deltas are conditional predictive diagnostics, not standalone scores.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_causal_field_wrt_replay250k_q0_v1"
SELF = "tools/" + ID + ".py"
CORE = "tools/fx2_causal_field_replay_v1.py"
PLAN_ID = "field-wrt-gate-plan"
ARMS = ("P", "K", "T", "R", "S")
PHASES = ("encode", "decode", "repeat")
CAPS = {"cpus": [2], "memory_bytes": 1073741824, "scratch_bytes": 268435456,
        "swap_bytes": 0, "wall_seconds": 900}
PHASE_WALL = 180
ANCESTOR = "fx2_weight_native_transfer250k_q0_v1"
BASE = "results/" + ANCESTOR + "/"
AUDIT = "operations/provenance/public_fx2_weight_native_transfer_terminal_20260905.json"
REFLECTION = "operations/adaptive/reflections/20260905T233740Z_c2a28dc2f7.json"
FIXED = {
    AUDIT: "a085b5e5d4f9b79312067329cf1dfef7e03e8c3106f8cd1a467e2fb26a4e074b",
    REFLECTION: "203e514646f50b7f1c341c3fb0ec84f8135e9dcce0ec7d61535acba83d0c8b6c",
}
POPULATION = {
    "raw_path": (BASE + "work/native/opening.raw", 250000,
                 "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"),
    "stored_path": (BASE + "work/native/opening.stored", 151220,
                    "9cc29963608bb990b820bc88e836532b4c2a1cfc1a5b633a14b1c3bad78765ab"),
    "trace_path": (BASE + "work/native/opening-P-encode.trace", 33871040,
                   "a5a0afbf0715a9c5371d5f097aaa1b478c1c6a2c030448c79b4ca70f1279c716"),
    "parent_archive_path": (BASE + "opening/P/archive.bin", 33429,
                            "70325310e96b83b48677d76d53141e69ddb47519b4cdffd1c85f51fe2c444dbe"),
    "dictionary_path": (BASE + "work/native/dictionary/english.dic", 411996,
                        "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
}
MEANINGFUL = (
    "arm", "raw_bytes", "raw_sha256", "modeled_bytes", "modeled_sha256",
    "archive_bytes", "archive_sha256", "prefix_bytes", "payload_bytes",
    "probability_digest", "synchronization_digest", "synchronization_rows",
    "adapter_state_digest", "mixture_state_digest", "changed_probability_bits",
    "donor_present_bits", "adapter", "external_parent_q16_bytes",
    "external_parent_q16_sha256", "exact_raw_inverse", "standalone_decoder",
    "objective_credit_bytes", "complete_package_bytes", "full_corpus_score_bytes",
    "source_sha256", "dictionary_sha256", "synchronization_file_sha256",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def reference_digest(ref):
    value = ref["sha256"].removeprefix("sha256:")
    require(len(value) == 64 and all(c in "0123456789abcdef" for c in value), "invalid reference digest")
    return value


def local_path(root, name):
    path = root / name
    require(isinstance(name, str) and name and not Path(name).is_absolute()
            and ".." not in Path(name).parts and path.resolve() == path,
            "aliased or escaping local path: " + str(name))
    return path


def read_ref(root, ref):
    path = local_path(root, ref["path"])
    require(stat.S_ISREG(path.lstat().st_mode), "input is not a regular file")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        data = stream.read()
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(after) == identity(path.stat()), "input replaced while reading")
    require(digest(data) == reference_digest(ref), "input hash differs: " + ref["path"])
    require("bytes" not in ref or len(data) == ref["bytes"], "input byte count differs")
    return data


def require_ref(inputs, ref):
    require(ref["path"] in inputs, "missing frozen input: " + ref["path"])
    bound = inputs[ref["path"]]
    require(reference_digest(bound) == reference_digest(ref), "conflicting reference: " + ref["path"])
    if "bytes" in bound and "bytes" in ref:
        require(bound["bytes"] == ref["bytes"], "conflicting byte count")


def declared_outputs(inputs=()):
    """Mandatory result-relative paths; source copies derive from frozen inputs."""
    paths = ["projection.json", "package.json", "comparison.json", "stage-decision.json",
             "artifacts.json", "artifact-index-diagnostics.json", "work/raw.bin",
             "work/modeled.bin", "work/q16.bin", "work/dictionary.bin"]
    for arm in ARMS:
        paths += [arm + "/" + name for name in ("archive.bin", "restored.bin", "repeat.bin", "result.json")]
        paths.append(arm + "-synchronization.json")
        for phase in PHASES:
            name = arm + "-" + phase
            paths += [name + suffix for suffix in (".stdout", ".stderr", ".execution.json")]
            paths += ["work/" + name + suffix for suffix in (".bin", ".sync")]
    for ref in inputs:
        name = ref["path"]
        if Path(name).suffix in (".py", ".cpp", ".h", ".hpp") or Path(name).name == "LICENSE":
            paths.append("work/source/" + name)
    return sorted(set(paths))


def check_runtime(plan):
    rows = plan["runtime_files"]
    require(rows and len({row["path"] for row in rows}) == len(rows), "runtime inventory missing or duplicated")
    for ref in rows:
        path = Path(ref["path"])
        require(path.is_absolute() and path.resolve() == path and path.is_file(), "runtime path is not canonical")
        require(path.stat().st_size == ref["bytes"] and file_sha(path) == reference_digest(ref), "runtime changed")
    python = Path(plan["python_executable"])
    require(python.is_absolute() and str(python.resolve()) in {row["path"] for row in rows}, "Python executable is not inventoried")
    require(os.access(python, os.X_OK), "Python executable unavailable")


def authenticate(root=ROOT, *, execution=False):
    """Authenticate only metadata/source here; NativeGate owns payload admission."""
    contract_name = "operations/adaptive/experiments/" + ID + ".json"
    contract_data = local_path(root, contract_name).read_bytes()
    reference = {"path": contract_name, "sha256": "sha256:" + digest(contract_data)}
    if execution:
        require(json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) == reference, "experiment reference differs")
    contract = json.loads(contract_data)
    require(contract["experimentId"] == ID and contract["status"] == "frozen", "experiment is not frozen")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]), "duplicate contract input")
    plans = [row for row in contract["inputs"] if row.get("id") == PLAN_ID]
    require(len(plans) == 1, "missing unique execution plan")
    plan = json.loads(read_ref(root, plans[0]))
    require(plan["candidate_id"] == ID and plan["resources"] == CAPS, "execution plan identity or resources differ")
    pop = plan["population"]
    require(pop["raw_bytes"] == 250000 and pop["modeled_bytes"] == 151210, "population coordinates differ")
    for field, (name, size, value) in POPULATION.items():
        require(pop[field] == name, "population path differs")
        require_ref(inputs, {"path": name, "bytes": size, "sha256": value})
    # The import resolver is itself authenticated before being executed. It
    # statically resolves the tools closure; the existing driver owns all lib.
    resolver = "tools/enwiki9_python_source_closure.py"
    buffers = {name: read_ref(root, inputs[name]) for name in
               (SELF, CORE, resolver, "lib/fx2_native_gate_v1.py", "lib/artifacts.py", "lib/driver.py")}
    namespace = {"__file__": str(root / resolver), "__name__": "_field_source_closure"}
    exec(compile(buffers[resolver], str(root / resolver), "exec"), namespace)
    sources = namespace["local_source_closure"]([root / CORE, root / "tools/research_contracts.py"])
    sources += list((root / "lib").glob("*.py")) + [root / SELF]
    for path in sources:
        name = path.relative_to(root).as_posix()
        buffers[name] = read_ref(root, inputs[name])
    for ref in plan["local_package_files"]:
        require_ref(inputs, ref)
        read_ref(root, ref)
    require(plan["local_package_files"] and len({r["path"] for r in plan["local_package_files"]})
            == len(plan["local_package_files"]), "source inventory missing or duplicated")
    package_names = {ref["path"] for ref in plan["local_package_files"]}
    core_sources = namespace["local_source_closure"]([root / CORE])
    require(all(path.relative_to(root).as_posix() in package_names for path in core_sources),
            "local codec dependency omitted from package inventory")
    require("tools/causal_field_dependency_v1.py" in package_names,
            "AST-loaded frozen parser omitted from package inventory")
    adapter_name = "tools/causal_field_wrt_adapter_v1.py"
    adapter_tree = ast.parse(read_ref(root, inputs[adapter_name]), filename=adapter_name)
    pin_nodes = [node.value for node in adapter_tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "PINS" for target in node.targets)]
    require(len(pin_nodes) == 1, "adapter does not declare unique frozen source pins")
    pins = ast.literal_eval(pin_nodes[0])
    for name in ("causal_field_dependency_v1.py", "wrt_exact.py"):
        require_ref(inputs, {"path": "tools/" + name, "sha256": pins[name]})
    for name, value in FIXED.items():
        ref = {"path": name, "sha256": value}
        require_ref(inputs, ref)
        buffers[name] = read_ref(root, ref)
    audit, reflection = (json.loads(buffers[name]) for name in (AUDIT, REFLECTION))
    require(audit["candidate_id"] == reflection["candidateId"] == ANCESTOR
            and audit["validity"] == "valid" and reflection["validity"]["valid"] is True,
            "native ancestor is not valid")
    require(reflection["decision"]["promotionPredicatesPass"] is True, "native ancestry is not selectable")
    require(any(ref["path"] == AUDIT and reference_digest(ref) == FIXED[AUDIT]
                for ref in reflection["evidence"]), "reflection does not bind terminal audit")
    require(contract["objective"] == reflection["objective"] and contract["objective"]["targetScoreBytes"] == 99000000,
            "objective differs")
    require(audit["source_bindings"]["all_inputs_match"] is True, "native source audit failed")
    indexed = {row["path"]: row for row in audit["artifacts"]}
    require(len(indexed) == len(audit["artifacts"]), "native artifact index repeats a path")
    for name, size, value in POPULATION.values():
        require(name in indexed and indexed[name]["bytes"] == size
                and reference_digest(indexed[name]) == value, "population lacks native terminal binding")
    resources = audit["resources"]
    require(resources["cleanup_complete"] and resources["closed_process_list_empty"]
            and not any(resources["guard_flags"].values()), "native guard was not cleanly closed")
    for ref in [resources["job"], resources["guard"], *plan["antecedents"]]:
        require_ref(inputs, ref)
        buffers[ref["path"]] = read_ref(root, ref)
    job = json.loads(buffers[resources["job"]["path"]])
    require(job["candidate_id"] == ANCESTOR and job["state"] == "completed"
            and job["job_id"] == audit["job_id"] and job["returncode"] == 0, "native terminal job differs")
    guard = json.loads(buffers[resources["guard"]["path"]])
    require(guard["label"] == job["job_id"] and guard["status"] == "complete"
            and guard["returncode"] == 0 and not any(guard["guards"].values()), "native guard identity or terminal state differs")
    require(job["execution_resources"]["cleanup_complete"] is True
            and job["execution_resources"]["guard_path"] == resources["guard"]["path"]
            and job["execution_resources"]["cgroup_path"] == guard["cgroup"]["path"]
            and job["execution_resources"]["cgroup_inode"] == guard["cgroup"]["inode"], "native guard resource identity differs")
    require(isinstance(guard["command"], list) and guard["command"]
            and all(isinstance(arg, str) for arg in guard["command"])
            and digest(b"\0".join(os.fsencode(arg) for arg in guard["command"])) == guard["command_sha256"],
            "native guard command digest differs")
    require_ref(inputs, reflection["job"])
    check_runtime(plan)
    return contract, plan, buffers, reference


def admit_before_payloads(root, reference):
    """Repeat NativeGate's metadata admission before its eager input buffering.

    The sealed helper verifies these identities again after buffering. This
    precheck closes its earlier-read boundary without changing sealed source.
    """
    require(os.sched_getaffinity(0) == {2}, "canonical parent must already use CPU2")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    job_id = marker.parent.name.removesuffix(".resources")
    require(marker == root / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl")
            and marker.resolve() == marker, "wrong canonical phase marker")
    paths = list((root / "operations/adaptive/running").glob("*" + job_id + ".json"))
    require(len(paths) == 1, "missing or ambiguous canonical running job")
    path = paths[0]
    require(path.resolve() == path and stat.S_ISREG(path.lstat().st_mode), "aliased canonical job")
    job = json.loads(path.read_text())
    require(job["job_id"] == job_id and job["candidate_id"] == ID and job["state"] == "running"
            and job["experiment"] == reference and job["execution_mode"] == "discovery", "canonical running job identity differs")
    require(all(job["resource_budget"].get(key) == value for key, value in CAPS.items()), "canonical budget differs")
    group = Path(job["execution_resources"]["cgroup_path"])
    memberships = [line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::")]
    require(len(memberships) == 1 and group == Path("/sys/fs/cgroup" + memberships[0]), "current cgroup is not the admitted group")
    require(group.stat().st_ino == job["execution_resources"]["cgroup_inode"], "canonical cgroup inode differs")
    require((group / "memory.max").read_text().strip() == str(CAPS["memory_bytes"])
            and (group / "memory.swap.max").read_text().strip() == "0", "canonical memory limits differ")
    require({int(value) for value in (group / "cgroup.procs").read_text().split()} == {os.getpid()}, "canonical group has foreign processes")
    check_live_controller(root, job, marker)


def check_live_controller(root, job, marker):
    """Metadata/proc identity checks used by the existing wordcode gate too."""
    require(job["runner"] == {"path": SELF, "sha256": "sha256:" + file_sha(root / SELF)}, "canonical runner binding differs")
    read_ref(root, job["execution_guard"])
    bound = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    require(bound == {"candidateId": ID, "candidateTreeSha256": job["candidate_tree_sha256"],
                      "receipt": job["candidate_revision"]}, "canonical candidate invocation differs")
    read_ref(root, job["candidate_revision"])
    resources = job["execution_resources"]
    require(resources["boot_id"] == Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "foreign canonical guard boot")
    pid = job["worker_pid"]
    require(type(pid) is int and pid > 1, "invalid canonical guard PID")
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    require(fields[0] not in {"Z", "X", "x"} and int(fields[19]) == job["worker_proc_start_ticks"]
            and digest(Path(f"/proc/{pid}/cmdline").read_bytes().rstrip(b"\0")) == resources["guard_command_sha256"],
            "canonical guard process identity differs")
    ancestor = os.getpid()
    seen = set()
    while ancestor > 1 and ancestor != pid:
        require(ancestor not in seen and len(seen) < 256, "invalid process ancestry")
        seen.add(ancestor)
        ancestor = int(Path(f"/proc/{ancestor}/stat").read_text().rsplit(")", 1)[1].split()[1])
    require(ancestor == pid, "runner is not a descendant of its canonical guard")
    guard_path = local_path(root, resources["guard_path"])
    require(guard_path == marker.parent / "guard.json", "active guard receipt ownership differs")
    guard = json.loads(guard_path.read_text())
    require(guard["status"] == "running" and guard["label"] == job["job_id"] and guard["phase"] == "diagnostic"
            and guard["cgroup"]["path"] == resources["cgroup_path"] and guard["cgroup"]["inode"] == resources["cgroup_inode"]
            and guard["cgroup"]["requested_memory_max_bytes"] == CAPS["memory_bytes"]
            and guard["temporary_disk_limit_bytes"] == CAPS["scratch_bytes"]
            and guard["wall_time_limit_seconds"] == CAPS["wall_seconds"]
            and guard["max_logical_cpus"] == 1 and not any(guard["guards"].values()), "active guard differs or failed")


def checked_report(report, operation, arm, expected):
    require(all(key in report for key in MEANINGFUL), "child report omits mandatory evidence")
    require(report["operation"] == operation and report["arm"] == arm, "child operation identity differs")
    for key, value in expected.items():
        require(report[key] == value, "child binding differs: " + key)
    require(report["exact_raw_inverse"] is True and report["standalone_decoder"] is False
            and report["objective_credit_bytes"] == 0 and report["complete_package_bytes"] is None
            and report["full_corpus_score_bytes"] is None, "child diagnostic scope differs")
    require(report["prefix_bytes"] == 46 and report["archive_bytes"] == 46 + report["payload_bytes"], "archive accounting differs")
    require(report["synchronization_rows"] == report["modeled_bytes"], "state synchronization is incomplete")
    require(type(report["pid"]) is int and report["pid"] > 0, "child identity missing")
    for key in ("changed_probability_bits", "donor_present_bits"):
        require(type(report[key]) is int and 0 <= report[key] <= report["modeled_bytes"] * 8, "invalid activity count")
    require(report["changed_probability_bits"] <= report["donor_present_bits"], "changed bits lack donor opportunity")
    return {key: report[key] for key in MEANINGFUL}


def compare_bytes(gate, actual, expected, label, record_bytes=1):
    if actual != expected:
        first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
        start = max(0, first // record_bytes - 2) * record_bytes
        gate.write("first-divergence.json", {"kind": label, "first_byte": first,
                   "record_bytes": record_bytes, "first_record": first // record_bytes,
                   "actual_bytes": len(actual), "expected_bytes": len(expected),
                   "actual_sha256": digest(actual), "expected_sha256": digest(expected),
                   "context_start": start, "actual_hex": actual[start:start + 5 * record_bytes].hex(),
                   "expected_hex": expected[start:start + 5 * record_bytes].hex()})
        raise ValueError(label + " differs at byte " + str(first))


class Codec:
    def __init__(self, gate, plan, arm, prefix, raw, q16, modeled):
        self.gate, self.plan, self.arm, self.prefix = gate, plan, arm, prefix
        self.raw, self.q16, self.modeled = raw, q16, modeled
        self.reports, self.projections, self.syncs = {}, {}, {}
        self.calls = 0

    def invoke(self, operation, input_path):
        gate = self.gate
        name = self.arm + "-" + operation
        output, sync = (gate.work / (name + suffix) for suffix in (".bin", ".sync"))
        command = [self.plan["python_executable"], "-B", str(gate.root / CORE), operation,
                   str(input_path), str(output), "--sync", str(sync), "--q16", str(gate.work / "q16.bin"),
                   "--dictionary", str(gate.work / "dictionary.bin"), "--arm", self.arm,
                   "--prefix", self.prefix.hex(), "--raw-bytes", str(len(self.raw)), "--raw-sha256", digest(self.raw)]
        gate.verify()
        check_runtime(self.plan)
        admit_before_payloads(gate.root, gate.reference)
        gate.run(name, command, PHASE_WALL, env={"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                 "MKL_NUM_THREADS": "1", "PYTHONHASHSEED": "0"})
        gate.verify()
        check_runtime(self.plan)
        admit_before_payloads(gate.root, gate.reference)
        report = json.loads((gate.result / (name + ".stdout")).read_text())
        expected = {"raw_bytes": len(self.raw), "raw_sha256": digest(self.raw),
                    "modeled_bytes": len(self.modeled), "modeled_sha256": digest(self.modeled),
                    "external_parent_q16_bytes": len(self.q16), "external_parent_q16_sha256": digest(self.q16),
                    "source_sha256": reference_digest(gate.inputs[CORE]),
                    "dictionary_sha256": reference_digest(gate.inputs[self.plan["population"]["dictionary_path"]]),
                    "cpu_affinity": CAPS["cpus"]}
        projection = checked_report(report, operation, self.arm, expected)
        payload, states = output.read_bytes(), sync.read_bytes()
        require(len(states) == len(self.modeled) * 32 and digest(states) == report["synchronization_file_sha256"],
                "synchronization artifact differs")
        require(bool(states) and states[-32:].hex() == report["synchronization_digest"], "terminal state differs from retained chain")
        expected_output = self.raw if operation == "decode" else None
        if expected_output is not None:
            compare_bytes(gate, payload, expected_output, name + "-raw")
        else:
            require(len(payload) == report["archive_bytes"] and digest(payload) == report["archive_sha256"], "archive artifact differs")
        self.reports[operation], self.projections[operation], self.syncs[operation] = report, projection, states
        return payload

    def compress(self, raw):
        require(raw == self.raw and self.calls < 2, "unexpected compression input or call")
        operation = "encode" if self.calls == 0 else "repeat"
        self.calls += 1
        return self.invoke(operation, self.gate.work / "modeled.bin")

    def decompress(self, archive):
        require(self.calls == 1 and "decode" not in self.reports, "unexpected decode call")
        path = self.gate.work / (self.arm + "-encode.bin")
        compare_bytes(self.gate, archive, path.read_bytes(), self.arm + "-decode-input")
        return self.invoke("decode", path)

    def stats(self):
        return {"scope": "external-parent-q16-replay", "standalone_decoder": False,
                "complete_package_bytes": None, "objective_credit_bytes": 0,
                "phase": self.reports.get("encode")}

    def finish(self):
        require(tuple(self.reports) == PHASES, "missing or reordered child phases")
        # Sequential independent processes are proved by gate execution records,
        # not PID uniqueness: kernels may legitimately reuse a PID after exit.
        for phase in PHASES[1:]:
            require(self.projections[phase] == self.projections["encode"], "complete child state report differs")
            compare_bytes(self.gate, self.syncs[phase], self.syncs["encode"], self.arm + "-" + phase + "-state", 32)
        record = {"arm": self.arm, "record_bytes": 32, "records": len(self.modeled),
                  "every_modeled_byte_identical": True, "report_projection_identical": True,
                  "independent_operations": list(PHASES), "probability_digest": self.reports["encode"]["probability_digest"],
                  "artifacts": [self.gate.artifact(self.gate.work / (self.arm + "-" + phase + ".sync")) for phase in PHASES]}
        self.gate.write(self.arm + "-synchronization.json", record)
        return self.reports["encode"]


def scientific_comparison(reports, source_bytes, dependency_bytes):
    require(set(reports) == set(ARMS), "comparison lacks arms")
    p, k, t = (reports[arm] for arm in ("P", "K", "T"))
    require(all(p[key] == k[key] for key in ("archive_bytes", "archive_sha256", "probability_digest")), "bookkeeping changes parent coding")
    require(p["changed_probability_bits"] == k["changed_probability_bits"] == 0, "parent or bookkeeping injects donor")
    active = {arm: reports[arm]["changed_probability_bits"] > 0
              and reports[arm]["adapter"]["selected_values"] > 0 for arm in ("T", "R", "S")}
    saved = p["archive_bytes"] - t["archive_bytes"]
    controls = all(t["archive_bytes"] < reports[arm]["archive_bytes"] for arm in ("R", "S"))
    classification = ("inconclusive_inactive_opportunities_or_controls" if not all(active.values()) else
                      "failed_causal_controls" if not controls else
                      "weak_compression" if saved <= 0 else "conditional_archive_gain")
    return {"archive_bytes": {arm: reports[arm]["archive_bytes"] for arm in ARMS},
            "archive_saved_bytes": saved, "required_controls_active": active,
            "treatment_beats_controls": controls, "failure_class": classification,
            "local_source_bytes": source_bytes, "external_decode_dependency_bytes": dependency_bytes,
            "local_source_paying": saved > source_bytes,
            "standalone_decoder": False, "complete_package_bytes": None,
            "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
            "larger_gate_authorized": False,
            "scope": "Fresh arithmetic archives conditional on retained parent Q16; native parent prediction is not independently reproduced"}


def execute(gate, plan):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(gate.root))
    sys.path.insert(0, str(gate.root / "tools"))
    from lib import driver
    import fx2_causal_field_replay_v1 as core
    gate.retain_sources()
    pop = plan["population"]
    raw, stored, trace, parent = (gate.buffers[pop[key]] for key in
                                  ("raw_path", "stored_path", "trace_path", "parent_archive_path"))
    require(len(raw) == pop["raw_bytes"] and len(stored) == pop["modeled_bytes"] + 10,
            "bound population lengths differ")
    require(stored[:10] == b"\x80\0\0\0\0\x07" + len(raw).to_bytes(4, "big"), "retained WRT header differs")
    q16, projection = core.project_trace(trace, stored[10:], parent, len(raw))
    require(projection["native_intervals_and_payload_exact"] is True
            and projection["decoder_receives_truth_trace"] is False, "parent projection failed")
    gate.write("projection.json", projection)
    gate.copy(pop["raw_path"], gate.work / "raw.bin")
    gate.copy(pop["dictionary_path"], gate.work / "dictionary.bin")
    core.publish(gate.work / "modeled.bin", stored[10:])
    core.publish(gate.work / "q16.bin", q16)
    local_files = plan["local_package_files"]
    sources = sum(ref["bytes"] for ref in local_files)
    dependencies = [gate.artifact(gate.work / name) for name in ("q16.bin", "dictionary.bin")]
    package = {"counted_files": local_files, "counted_bytes": sources,
               "external_decode_dependencies": dependencies,
               "external_decode_dependency_bytes": sum(ref["bytes"] for ref in dependencies),
               "runtime_inventory": plan["runtime_files"], "python_executable": plan["python_executable"],
               "dependency_closure_complete": False, "complete_package_bytes": None,
               "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
               "scope": "Local raw source inventory; external Q16 and dictionary accounted separately; compiler/runtime licensing and standalone parent excluded"}
    gate.write("package.json", package)
    reports, rows = {}, {}
    for arm in ARMS:
        codec = Codec(gate, plan, arm, parent[:46], raw, q16, stored[10:])
        output = gate.result / arm
        row = driver.run(ID, gate.work / "raw.bin", len(raw), True, module=codec, artifact_dir=output,
                         run_purpose="diagnostic", run_scope_label="opening250k-" + arm,
                         run_source="canonical-tool", run_tags=["arm:" + arm, "external-parent-q16-replay"],
                         run_context="Conditional field diagnostic; external parent probabilities are a decoder dependency",
                         package_inventory=([(ref["path"], ref["bytes"]) for ref in local_files], package))
        require(row["roundtrip_ok"] is True and row["determinism"]["single_host_byte_equal"] is True,
                "driver inversion or repeat failed")
        reports[arm] = codec.finish()
        compare_bytes(gate, (output / "restored.bin").read_bytes(), raw, arm + "-driver-inverse")
        for kind in ("archive", "repeat"):
            archive = (output / (kind + ".bin")).read_bytes()
            require(digest(archive) == reports[arm]["archive_sha256"], "driver archive differs from child")
            if arm in ("P", "K"):
                compare_bytes(gate, archive, parent, arm + "-native-parent")
        rows[arm] = {"result": gate.artifact(output / "result.json"),
                     **{name: gate.artifact(output / (name + ".bin")) for name in ("archive", "restored", "repeat")},
                     "synchronization": gate.artifact(gate.result / (arm + "-synchronization.json"))}
    require(len(gate.commands) == len(ARMS) * len(PHASES), "child phase count differs")
    comparison = scientific_comparison(reports, sources, package["external_decode_dependency_bytes"])
    return {**comparison, "arms": rows, "reports": reports, "exact_raw_inverse": True,
            "deterministic_repeat": True, "every_byte_state_synchronization": True,
            "parent_archive_identical": True, "bookkeeping_probability_identity": True,
            "raw_bytes": len(raw), "modeled_bytes": len(stored) - 10}


def index_artifacts(gate, *, successful):
    excluded = {"artifacts.json", "artifact-index-diagnostics.json", "stage-decision.json", "comparison.json"}
    rows, errors = [], []
    for directory, directories, files in os.walk(gate.result, followlinks=False):
        for name in directories + files:
            path = Path(directory) / name
            if path.relative_to(gate.result).as_posix() in excluded:
                continue
            try:
                mode = path.lstat().st_mode
                require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), "nonregular artifact")
                if stat.S_ISREG(mode):
                    rows.append(gate.artifact(path))
            except (OSError, ValueError) as error:
                errors.append({"path": str(path), "error": str(error)})
    if successful:
        indexed = {row["path"] for row in rows}
        for name in declared_outputs(gate.inputs.values()):
            if name not in excluded and (gate.result / name).relative_to(gate.root).as_posix() not in indexed:
                errors.append({"path": name, "error": "mandatory artifact missing"})
    return rows, {"complete": not errors, "errors": errors,
                  "index_metadata_excluded": sorted(excluded), "indexed_files": len(rows)}


def finish_gate(gate, plan):
    stage = {"schema": "gamma.enwiki9.fx2-causal-field-wrt-stage.v1", "candidate_id": ID,
             "experiment": gate.reference, "objective_credit_bytes": 0, "complete_package_bytes": None,
             "full_corpus_score_bytes": None, "larger_gate_authorized": False,
             "continuous_guard_decision": "pending canonical outer guard closure"}
    comparison = None
    try:
        comparison = execute(gate, plan)
        gate.closure()
        gate.verify()
        check_runtime(plan)
        authenticate(gate.root, execution=True)
        stage.update(status="passed", child_closure_ok=True)
    except Exception as error:
        category = getattr(error, "category", "missing_or_unreadable_evidence" if isinstance(error, (OSError, KeyError, json.JSONDecodeError)) else "invariant_failed")
        stage.update(status="execution_failed", failure_class=category,
                     error=type(error).__name__ + ": " + str(error))
    try:
        gate.closure()
        stage["child_closure_ok"] = True
    except Exception as error:
        stage.update(status="execution_failed", child_closure_ok=False, closure_error=str(error))
    artifacts, diagnostics = index_artifacts(gate, successful=stage["status"] == "passed")
    if not diagnostics["complete"]:
        stage.update(status="execution_failed", failure_class="missing_or_unreadable_evidence")
    gate.write("artifacts.json", artifacts)
    gate.write("artifact-index-diagnostics.json", diagnostics)
    try:
        stage.update(commands=gate.commands, artifacts=gate.artifact(gate.result / "artifacts.json"),
                     artifact_index_diagnostics=gate.artifact(gate.result / "artifact-index-diagnostics.json"))
    except Exception as error:
        stage.update(status="execution_failed", failure_class="artifact_index_fingerprint_failed", error=str(error))
    # Publish the scientific table only after closure, source/runtime rechecks,
    # and complete artifact indexing. An interrupted run has no positive table.
    if stage["status"] == "passed":
        try:
            gate.verify()
            check_runtime(plan)
            gate.closure()
            for ref in artifacts:
                read_ref(gate.root, ref)
            require(isinstance(comparison["failure_class"], str), "comparison classification missing")
            gate.write("comparison.json", comparison)
            stage.update(comparison=gate.artifact(gate.result / "comparison.json"),
                         failure_class=comparison["failure_class"])
        except Exception as error:
            stage.update(status="execution_failed", failure_class="final_evidence_revalidation_failed", error=str(error))
            quarantine_comparison(gate, stage)
    try:
        gate.write("stage-decision.json", stage)
    except Exception:
        quarantine_comparison(gate, stage)
        raise
    return stage


def quarantine_comparison(gate, stage):
    table = gate.result / "comparison.json"
    if table.exists():
        # This is this run's newly written table, never prior measured evidence.
        # Preserve its bytes outside the published pathname on a failed close.
        quarantine = gate.result / "unpublished-comparison.json"
        require(not quarantine.exists(), "comparison quarantine already exists")
        table.rename(quarantine)
        stage["unpublished_comparison"] = str(quarantine.relative_to(gate.root))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--validate-only", action="store_true")
    choice.add_argument("--describe-outputs", action="store_true")
    args = parser.parse_args(argv)
    if args.describe_outputs:
        print(json.dumps({"candidate_id": ID, "result_relative_paths": declared_outputs(),
                          "additional_source_copies": "declared_outputs(contract['inputs'])", "codec_executed": False}, indent=2))
        return 0
    contract, plan, buffers, reference = authenticate(execution=not args.validate_only)
    if args.validate_only:
        print(json.dumps({"status": "metadata_preflight_pass", "experiment": reference,
                          "payloads_opened": False, "codec_executed": False, "launch_authorized": False,
                          "child_processes_planned": len(ARMS) * len(PHASES)}))
        return 0
    admit_before_payloads(ROOT, reference)
    namespace = {"__name__": "_field_native_gate"}
    name = "lib/fx2_native_gate_v1.py"
    exec(compile(buffers[name], str(ROOT / name), "exec"), namespace)
    gate = namespace["NativeGate"](ROOT, ID, CAPS)
    stage = finish_gate(gate, plan)
    print(json.dumps(stage, sort_keys=True))
    return 0 if stage["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
