#!/usr/bin/env python3
"""Adjacent-field corpus integration with verified retained parent probabilities.

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
ID = "fx2_causal_preceding_wrt250k_q0_v1"
SELF = "tools/fx2_causal_field_preceding_gate_v1.py"
CORE = "tools/fx2_causal_field_preceding_replay_v1.py"
PLAN_ID = "preceding-field-gate-plan"
ARMS = ("P", "K", "T", "O", "R", "S")
PHASES = ("encode", "decode", "repeat")
CAPS = {"cpus": [2], "memory_bytes": 1073741824, "scratch_bytes": 268435456,
        "swap_bytes": 0, "wall_seconds": 900}
PHASE_WALL = 180
_ADMISSION_CONTEXT = None
_CONTROLLER_BINDING = None
ANCESTOR = "fx2_causal_field_wrt_replay250k_q0_v1"
BASE = "results/" + ANCESTOR + "/"
AUDIT = "operations/provenance/fx2_causal_field_wrt_terminal_20260907.json"
REFLECTION = "operations/adaptive/reflections/20260907T130508Z_c3d4b66329.json"
FIXED = {
    AUDIT: "72e07fab16ed2145459e0221afa3dc0c964ec466b2c4b4b0f7c09e69da644fcd",
    REFLECTION: "d90dfa7899003e192590f72db11869b3530b71a9b00dc38a44b03565b52fac27",
}
POPULATION = {
    "raw_path": (BASE + "work/raw.bin", 250000,
        "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"),
    "modeled_path": (BASE + "work/modeled.bin", 151210,
        "1cea99504a92cbb5602f0439902f1d128321fd5442e50ea1a9e6a6b2585f4a98"),
    "q16_path": (BASE + "work/q16.bin", 2419360,
        "571857e89c15942a86741d401adfe89d30dd045f1bb47fd8544f0c0c3af0667c"),
    "dictionary_path": (BASE + "work/dictionary.bin", 411996,
        "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
    "parent_archive_path": (BASE + "P/archive.bin", 33429,
        "70325310e96b83b48677d76d53141e69ddb47519b4cdffd1c85f51fe2c444dbe"),
    "original_archive_path": (BASE + "T/archive.bin", 33429,
        "70325310e96b83b48677d76d53141e69ddb47519b4cdffd1c85f51fe2c444dbe"),
    "original_result_path": (BASE + "T/result.json", 9725,
        "cba55dd3b511880e3cf632be9e47d3f2bc2d016b2ccb15d27883de66d64769bb"),
    "original_sync_path": (BASE + "work/T-encode.sync", 4838720,
        "c5a4465e1760f4a9c1059ae3fc342122b1d39d445f9f88313c17b38f554e61c6"),
    "projection_path": (BASE + "projection.json", 461,
        "492f4614bed8ec562ef2edbbf02f0ac98eea236d9e92cf5e4c3b1b74157c7d0e"),
}
# The private hash-loaded modules and AST-loaded parser are invisible to normal
# import discovery. Bind and account for them explicitly as well as static imports.
DYNAMIC_SOURCES = (
    "tools/causal_field_preceding_adapter250k_v1.py",
    "tools/causal_field_preceding_selector_v1.py",
    "tools/causal_field_wrt_adapter_v1.py",
    "tools/causal_field_dependency_v1.py",
    "tools/wrt_exact.py",
    "tools/causal_field_parent_coder_v1.py",
)
MEANINGFUL = (
    "arm", "raw_bytes", "raw_sha256", "modeled_bytes", "modeled_sha256",
    "archive_bytes", "archive_sha256", "prefix_bytes", "payload_bytes",
    "probability_digest", "synchronization_digest", "synchronization_rows",
    "adapter_state_digest", "mixture_state_digest", "changed_probability_bits",
    "donor_present_bits", "adapter", "external_parent_q16_bytes",
    "external_parent_q16_sha256", "exact_raw_inverse", "standalone_decoder",
    "objective_credit_bytes", "complete_package_bytes", "full_corpus_score_bytes",
    "source_sha256", "dictionary_sha256", "synchronization_file_sha256",
    "adapter_policy_id", "adapter_constructor_arm", "decoder_arm_option_bytes",
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
               (SELF, CORE, resolver, "lib/fx2_native_gate_v1.py", "lib/artifacts.py", "lib/driver.py", "tools/enwiki9_lab.py")}
    namespace = {"__file__": str(root / resolver), "__name__": "_field_source_closure"}
    exec(compile(buffers[resolver], str(root / resolver), "exec"), namespace)
    sources = namespace["local_source_closure"]([root / CORE, root / "tools/research_contracts.py"])
    sources += list((root / "lib").glob("*.py")) + [root / SELF]
    sources += [root / name for name in DYNAMIC_SOURCES]
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
    require(set(DYNAMIC_SOURCES) <= package_names,
            "dynamic codec dependency omitted from package inventory")
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
            and reflection["validity"]["valid"] is True, "field ancestor is not valid")
    # The original field experiment was held for inactive controls. Its exact
    # artifacts remain usable; this separate experiment does not promote it.
    require(reflection["decision"]["verdict"] == "hold", "field ancestry disposition differs")
    require(any(ref["path"] == AUDIT and reference_digest(ref) == FIXED[AUDIT]
                for ref in reflection["evidence"]), "reflection does not bind terminal audit")
    require(contract["objective"] == reflection["objective"]
            and contract["objective"]["targetScoreBytes"] == 99000000, "objective differs")
    for key in ("correctness_pass", "frozen_inputs_reverified", "artifact_closure_pass",
                "continuous_guard_pass", "accounting_pass", "state_agreement_pass",
                "parent_bookkeeping_identity_pass"):
        require(audit["measurements"][key] is True, "field terminal evidence failed: " + key)
    for ref in [audit["job"], audit["guard"], audit["decision"], *plan["antecedents"]]:
        require_ref(inputs, ref)
        buffers[ref["path"]] = read_ref(root, ref)
    require_ref(inputs, reflection["job"])
    require(reference_digest(reflection["job"]) == reference_digest(audit["job"]),
            "reflection job differs from terminal audit")
    decision = json.loads(buffers[audit["decision"]["path"]])
    require(decision["candidateId"] == ANCESTOR and decision["objective"] == contract["objective"],
            "prior decision identity differs")
    indexed = {row["path"]: row for row in decision["artifacts"]}
    require(len(indexed) == len(decision["artifacts"]), "prior artifact index repeats a path")
    for name, size, value in POPULATION.values():
        require(name in indexed and reference_digest(indexed[name]) == value,
                "population lacks closed field artifact binding")
        require("bytes" not in indexed[name] or indexed[name]["bytes"] == size,
                "prior artifact byte count differs")
    resources = audit["resource"]
    require(resources["cleanup_complete"] and not any(resources["guards"].values()),
            "field guard was not cleanly closed")
    job = json.loads(buffers[audit["job"]["path"]])
    require(job["candidate_id"] == ANCESTOR and job["state"] == "completed"
            and job["returncode"] == 0, "field terminal job differs")
    guard = json.loads(buffers[audit["guard"]["path"]])
    require(guard["label"] == job["job_id"] and guard["status"] == "complete"
            and guard["returncode"] == 0 and not any(guard["guards"].values()),
            "field guard identity or terminal state differs")
    require(job["execution_resources"]["cleanup_complete"] is True
            and job["execution_resources"]["guard_path"] == audit["guard"]["path"]
            and job["execution_resources"]["cgroup_path"] == guard["cgroup"]["path"]
            and job["execution_resources"]["cgroup_inode"] == guard["cgroup"]["inode"],
            "field guard resource identity differs")
    require(isinstance(guard["command"], list) and guard["command"]
            and all(isinstance(arg, str) for arg in guard["command"])
            and digest(b"\0".join(os.fsencode(arg) for arg in guard["command"])) == guard["command_sha256"],
            "field guard command digest differs")
    # The metadata pass intentionally does not open any population file, even
    # the retained projection/result. NativeGate opens them after admission.
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
            and guard["wall_time_limit_seconds"] in (None, CAPS["wall_seconds"])
            and guard["max_logical_cpus"] == 1 and not any(guard["guards"].values()), "active guard differs or failed")
    require(_ADMISSION_CONTEXT is not None, "outer controller admission context missing")
    check_outer_controller(root, job, int(fields[1]), _ADMISSION_CONTEXT["plan"], _ADMISSION_CONTEXT["inputs"])


def check_outer_controller(root, job, controller_pid, plan, inputs):
    """Bind the observed direct parent which owns wait_for_budgeted_worker.

    Job v3 has no presaved lab PID. The live guard's parent is therefore sampled
    prospectively, and the exact observed identity must remain stable. This is
    an operational process binding, not hardware or qualification attestation.
    """
    global _CONTROLLER_BINDING
    require(type(controller_pid) is int and controller_pid > 1, "outer lab controller is absent")
    resources, worker = job["execution_resources"], job["worker_pid"]
    require(resources["boot_id"] == Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "outer controller boot differs")
    directory = Path("/proc") / str(controller_pid)
    before = (directory / "stat").read_text().rsplit(")", 1)[1].split()
    require(before[0] not in {"Z", "X", "x"} and int(before[19]) <= job["worker_proc_start_ticks"],
            "outer lab controller is terminal or starts after guard")
    command = (directory / "cmdline").read_bytes()
    expected = [plan["python_executable"], str(root / "tools/enwiki9_lab.py"), "run", "--candidate", ID,
                "--max-workers", "1", "--min-free-mib", "16384", "--max-load", "24"]
    require(command == b"\0".join(os.fsencode(arg) for arg in expected) + b"\0", "outer lab controller argv differs")
    require((directory / "cwd").resolve() == root, "outer lab controller cwd differs")
    executable = Path(plan["python_executable"]).resolve()
    require((directory / "exe").resolve() == executable, "outer lab controller runtime differs")
    runtimes = [ref for ref in plan["runtime_files"] if ref["path"] == str(executable)]
    require(len(runtimes) == 1 and file_sha(executable) == reference_digest(runtimes[0])
            and executable.stat().st_size == runtimes[0]["bytes"], "outer runtime is not the frozen executable")
    source = inputs["tools/enwiki9_lab.py"]
    read_ref(root, source)
    after = (directory / "stat").read_text().rsplit(")", 1)[1].split()
    require(after[0] not in {"Z", "X", "x"} and (before[1], before[19]) == (after[1], after[19])
            and (directory / "cmdline").read_bytes() == command, "outer lab identity changed while sampled")
    guard_after = Path(f"/proc/{worker}/stat").read_text().rsplit(")", 1)[1].split()
    require(guard_after[0] not in {"Z", "X", "x"} and int(guard_after[1]) == controller_pid
            and int(guard_after[19]) == job["worker_proc_start_ticks"], "guard was orphaned or replaced during admission")
    observed = {"binding_kind": "observed prospective direct parent of frozen guard", "job_id": job["job_id"],
                "boot_id": resources["boot_id"], "pid": controller_pid, "proc_start_ticks": int(before[19]),
                "parent_pid": int(before[1]), "command": expected, "command_sha256": digest(command.rstrip(b"\0")),
                "cwd": str(root), "python_executable": runtimes[0], "controller_source": source,
                "guard_pid": worker, "guard_proc_start_ticks": job["worker_proc_start_ticks"],
                "job_wall_budget_seconds": CAPS["wall_seconds"], "timer_owner": "enwiki9_lab.wait_for_budgeted_worker",
                "guard_wall_limit_may_be_null": True, "qualification_authority": False}
    require(_CONTROLLER_BINDING is None or _CONTROLLER_BINDING == observed, "observed outer controller binding changed")
    _CONTROLLER_BINDING = observed
    return observed


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
    policy = ("causal-field-original-first-wrt-v1" if arm in ("P", "O")
              else "causal-field-immediately-preceding-wrt250k-v1")
    require(report["adapter_policy_id"] == policy
            and report["adapter_constructor_arm"] == ("T" if arm == "O" else arm)
            and type(report["decoder_arm_option_bytes"]) is int
            and report["decoder_arm_option_bytes"] == 1, "adapter policy or option accounting differs")
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
    controls = all(t["archive_bytes"] < reports[arm]["archive_bytes"] for arm in ("O", "R", "S"))
    classification = ("inconclusive_inactive_opportunities_or_controls" if not all(active.values()) else
                      "failed_causal_controls" if not controls else
                      "weak_compression" if saved <= 0 else "conditional_archive_gain")
    return {"archive_bytes": {arm: reports[arm]["archive_bytes"] for arm in ARMS},
            "archive_saved_bytes": saved, "required_controls_active": active,
            "treatment_beats_controls": controls, "failure_class": classification,
            "original_control_active": reports["O"]["changed_probability_bits"] > 0,
            "original_control_required_active": False,
            "decoder_arm_option_bytes_per_archive": 1,
            "local_source_bytes": source_bytes, "external_decode_dependency_bytes": dependency_bytes,
            "local_source_paying": saved > source_bytes + 1,
            "standalone_decoder": False, "complete_package_bytes": None,
            "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
            "larger_gate_authorized": False,
            "scope": "Fresh arithmetic archives conditional on retained parent Q16; native parent prediction is not independently reproduced"}


def execute(gate, plan):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(gate.root))
    sys.path.insert(0, str(gate.root / "tools"))
    from lib import driver
    import fx2_causal_field_preceding_replay_v1 as core
    gate.retain_sources()
    pop = plan["population"]
    raw, modeled, q16, parent = (gate.buffers[pop[key]] for key in
        ("raw_path", "modeled_path", "q16_path", "parent_archive_path"))
    require(len(raw) == pop["raw_bytes"] and len(modeled) == pop["modeled_bytes"],
            "bound population lengths differ")
    projection = json.loads(gate.buffers[pop["projection_path"]])
    require(projection["native_intervals_and_payload_exact"] is True
            and projection["decoder_receives_truth_trace"] is False
            and projection["q16_bytes"] == len(q16) == len(modeled) * 16
            and projection["q16_sha256"] == digest(q16)
            and projection["parent_archive_bytes"] == len(parent)
            and projection["parent_archive_sha256"] == digest(parent)
            and projection["parent_payload_bytes"] == len(parent) - 46
            and projection["records"] == len(modeled) * 8,
            "retained parent projection differs")
    original = json.loads(gate.buffers[pop["original_result_path"]])["program_stats"]["phase"]
    require(original["arm"] == "T" and original["raw_sha256"] == digest(raw)
            and original["modeled_sha256"] == digest(modeled)
            and original["external_parent_q16_sha256"] == digest(q16),
            "original first-field result coordinates differ")
    gate.write("projection.json", {"reused_projection": projection,
               "source": gate.inputs[pop["projection_path"]],
               "truth_trace_reprocessed": False, "native_prediction_rerun": False})
    for field, name in (("raw_path", "raw.bin"), ("modeled_path", "modeled.bin"),
                        ("q16_path", "q16.bin"), ("dictionary_path", "dictionary.bin")):
        gate.copy(pop[field], gate.work / name)
    local_files = plan["local_package_files"]
    sources = sum(ref["bytes"] for ref in local_files)
    dependencies = [gate.artifact(gate.work / name) for name in ("q16.bin", "dictionary.bin")]
    package = {"counted_files": local_files, "counted_bytes": sources,
               "external_decode_dependencies": dependencies,
               "external_decode_dependency_bytes": sum(ref["bytes"] for ref in dependencies),
               "runtime_inventory": plan["runtime_files"], "python_executable": plan["python_executable"],
               "decoder_arm_option_bytes_per_archive": 1,
               "dependency_closure_complete": False, "complete_package_bytes": None,
               "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
               "scope": "Local raw source inventory; external Q16 and dictionary accounted separately; compiler/runtime licensing and standalone parent excluded"}
    gate.write("package.json", package)
    reports, rows = {}, {}
    for arm in ARMS:
        codec = Codec(gate, plan, arm, parent[:46], raw, q16, modeled)
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
        if arm == "O":
            compare_bytes(gate, (output / "archive.bin").read_bytes(),
                          gate.buffers[pop["original_archive_path"]], "O-original-T-archive")
            compare_bytes(gate, codec.syncs["encode"], gate.buffers[pop["original_sync_path"]],
                          "O-original-T-state-chain", 32)
            for key in MEANINGFUL:
                if key not in {"arm", "source_sha256", "adapter_policy_id",
                               "adapter_constructor_arm", "decoder_arm_option_bytes"}:
                    require(reports[arm][key] == original[key], "original T control differs: " + key)
        rows[arm] = {"result": gate.artifact(output / "result.json"),
                     **{name: gate.artifact(output / (name + ".bin")) for name in ("archive", "restored", "repeat")},
                     "synchronization": gate.artifact(gate.result / (arm + "-synchronization.json"))}
    require(len(gate.commands) == len(ARMS) * len(PHASES), "child phase count differs")
    comparison = scientific_comparison(reports, sources, package["external_decode_dependency_bytes"])
    return {**comparison, "arms": rows, "reports": reports, "exact_raw_inverse": True,
            "deterministic_repeat": True, "every_byte_state_synchronization": True,
            "parent_archive_identical": True, "bookkeeping_probability_identity": True,
            "original_first_field_identity": True,
            "raw_bytes": len(raw), "modeled_bytes": len(modeled)}


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
    stage = {"schema": "gamma.enwiki9.fx2-causal-preceding-stage.v1", "candidate_id": ID,
             "experiment": gate.reference, "objective_credit_bytes": 0, "complete_package_bytes": None,
             "full_corpus_score_bytes": None, "larger_gate_authorized": False,
             "continuous_guard_decision": "pending canonical outer guard closure",
             "outer_controller_admission": _CONTROLLER_BINDING,
             "elapsed_stop_authority": {"outer_lab_seconds": 900, "native_gate_aggregate_seconds": 900,
                                        "child_phase_seconds": 180, "diagnostic_guard_wall_may_be_null": True}}
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
    global _ADMISSION_CONTEXT
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
    _ADMISSION_CONTEXT = {"plan": plan, "inputs": {row["path"]: row for row in contract["inputs"]}}
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
