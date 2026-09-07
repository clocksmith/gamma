#!/usr/bin/env python3
"""One admitted observation scan with independent bounded execution.

A schema-valid adaptive contract binds a separate execution plan. Local source
closure and the interpreter authenticate before lab imports or population reads.
Reports remain diagnostic until the outer canonical job and guard close.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_causal_field_opportunity_q0_v1"
SELF = "tools/causal_field_opportunity_gate_v2.py"
OBSERVER = "tools/causal_field_opportunity_v1.py"
LAB = "tools/enwiki9_lab.py"
GUARD = "tools/run_with_resource_guard_v3.py"
RESOLVER = "tools/enwiki9_python_source_closure.py"
PLAN = "operations/provenance/fx2_causal_field_opportunity_q0_v1_execution.json"
CAPS = {"cpus": [2], "memory_bytes": 536870912, "scratch_bytes": 33554432,
        "swap_bytes": 0, "wall_seconds": 120}
MANDATORY_SOURCES = {SELF, OBSERVER, LAB, GUARD, RESOLVER,
                     "tools/causal_field_wrt_adapter_v1.py",
                     "tools/causal_field_dependency_v1.py", "tools/wrt_exact.py"}
MAX_INPUT_BYTES = 8 * 1024**2
MAX_TOTAL_INPUT_BYTES = 64 * 1024**2
MAX_INPUTS = 512
MAX_REPORT_BYTES = 1024**2


def require(value, message):
    if not value:
        raise ValueError(message)


def identity(row):
    return row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns


def regular_read(path, maximum):
    """Reject special files both before open and after race-safe nonblocking open."""
    require(path.is_absolute() and path.resolve() == path, "aliased input")
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "input is not a regular file")
    require(before.st_size <= maximum, "input exceeds read bound")
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode), "opened input is not a regular file")
        require(identity(before) == identity(opened), "input replaced before read")
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    require(len(data) <= maximum and identity(before) == identity(after) == identity(path.lstat()),
            "input replaced or exceeds read bound")
    return data


def bound_read(root, reference, maximum=MAX_INPUT_BYTES):
    name = reference["path"]
    require(isinstance(name, str) and name and not Path(name).is_absolute()
            and ".." not in Path(name).parts, "aliased input")
    data = regular_read(root / name, maximum)
    require(hashlib.sha256(data).hexdigest() == reference["sha256"].removeprefix("sha256:"),
            "input digest changed: " + name)
    require("bytes" not in reference or len(data) == reference["bytes"], "input byte count differs")
    return data


def arm_wall_deadline(seconds):
    """An independent process wall stop, including time blocked on I/O."""
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, seconds)


def load_module(name, path, source):
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def verify_runtime(reference):
    path = Path(reference["path"])
    require(path.is_absolute() and path.resolve() == path
            and Path(sys.executable).resolve() == path
            and Path("/proc/self/exe").resolve() == path, "runtime executable differs")
    data = regular_read(path, 64 * 1024**2)
    require(len(data) == reference["bytes"]
            and hashlib.sha256(data).hexdigest() == reference["sha256"].removeprefix("sha256:"),
            "runtime bytes or digest differ")


def import_lab(root):
    import enwiki9_lab as lab
    require(Path(lab.__file__).resolve() == root / LAB and lab.ROOT.resolve() == root,
            "imported lab location differs")
    return lab


def check_guard(root, job, marker, lab):
    resources = job["execution_resources"]
    require(os.sched_getaffinity(0) == {2} and job["worker_pid"] == os.getppid(),
            "guard ancestry or CPU differs")
    require(lab.worker_pid_matches_job(job), "canonical live guard identity differs")
    require(all(resources["budget"].get(key) == value for key, value in CAPS.items()),
            "guard resource budget differs")
    group = Path(resources["cgroup_path"])
    membership = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines()
                      if line.startswith("0::"))
    require(group == Path("/sys/fs/cgroup" + membership) and group.resolve() == group
            and group.parent == Path(job["resource_budget"]["cgroup_parent"])
            and group.name == "gamma-enwiki9-" + job["job_id"]
            and group.stat().st_ino == resources["cgroup_inode"], "cgroup differs")
    require((group / "memory.max").read_text().strip() == str(CAPS["memory_bytes"])
            and (group / "memory.swap.max").read_text().strip() == "0", "memory allocation differs")
    require(resources["guard_path"] == str((marker.parent / "guard.json").relative_to(root)),
            "guard receipt owner differs")


def append_marker(marker, event):
    before = marker.lstat()
    require(marker.resolve() == marker and stat.S_ISREG(before.st_mode)
            and before.st_size < MAX_REPORT_BYTES, "invalid phase marker")
    fd = os.open(marker, os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        require(identity(before) == identity(os.fstat(fd)), "phase marker replaced")
        raw = (json.dumps({"phase": "diagnostic", "event": event}) + "\n").encode()
        require(os.write(fd, raw) == len(raw), "incomplete phase marker write")
    finally:
        os.close(fd)


def scan(observer, modeled, words, raw_bytes, raw_sha256, expected_stats=None):
    """Compare inherited state and emissions after every byte; stop at first divergence."""
    require(type(raw_bytes) is int and 0 <= raw_bytes <= observer.base.MAX_RAW, "raw bound")
    require(len(modeled) <= 4 * raw_bytes + 4096, "modeled bound")
    parent = observer.base.Adapter(words, "T", raw_bytes)
    instrumented = observer.Adapter(words, "T", raw_bytes, first_event_limit=32)
    raw_hash, chain = hashlib.sha256(), hashlib.sha256(b"field-opportunity-state-chain-v1\0")
    raw_count = 0
    for offset, byte in enumerate(modeled):
        original = parent.feed(byte)
        observed = instrumented.feed(byte)
        require(original == observed, "raw emission divergence at modeled byte " + str(offset))
        left, right = parent.state_digest(), instrumented.state_digest()
        require(left == right, "state divergence at modeled byte " + str(offset))
        require((parent.donor, parent.activation_id) == (instrumented.donor, instrumented.activation_id),
                "donor divergence at modeled byte " + str(offset))
        raw_hash.update(original)
        raw_count += len(original)
        chain.update(bytes.fromhex(left))
    parent.finish()
    instrumented.finish()
    stats = parent.stats()
    require(stats == instrumented.stats(), "terminal adapter divergence")
    require(raw_count == raw_bytes and raw_hash.hexdigest() == raw_sha256, "raw identity mismatch")
    if expected_stats is not None:
        require(stats == expected_stats, "retained corpus adapter counters or state differ")
    diagnostics = instrumented.diagnostics()
    require(sum(diagnostics["eligibility"].values()) == diagnostics["start_values"], "eligibility partition")
    for name in ("conditional", "recency", "rotated"):
        require(sum(diagnostics[name].values()) == diagnostics["eligibility"]["eligible"], name + " partition")
    return {"schema": "gamma.enwiki9.causal-field-opportunity-scan.v1", "raw_bytes": raw_count,
            "raw_sha256": raw_hash.hexdigest(), "modeled_bytes": len(modeled),
            "modeled_sha256": hashlib.sha256(modeled).hexdigest(), "state_chain_sha256": chain.hexdigest(),
            "every_byte_state_agreement": True, "exact_raw_identity": True,
            "retained_terminal_state_agreement": expected_stats is not None,
            "adapter": stats, "diagnostics": diagnostics,
            "archive_bytes": None, "complete_package_bytes": None, "objective_credit_bytes": 0}


def main():
    started = time.monotonic()
    arm_wall_deadline(CAPS["wall_seconds"])
    resource.setrlimit(resource.RLIMIT_AS, (CAPS["memory_bytes"], CAPS["memory_bytes"]))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (CAPS["scratch_bytes"], CAPS["scratch_bytes"]))
    reference = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    contract_bytes = bound_read(ROOT, reference)
    contract = json.loads(contract_bytes)
    require(contract["experimentId"] == ID and contract["status"] == "frozen"
            and contract["schema"] == "gamma.enwiki9.adaptive-experiment-contract.v1", "wrong experiment")
    require(0 < len(contract["inputs"]) <= MAX_INPUTS, "input count bound")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]), "duplicate inputs")
    require(PLAN in inputs, "execution plan is not bound")
    plan = json.loads(bound_read(ROOT, inputs[PLAN]))
    require(plan["candidate_id"] == ID and plan["bounds"] == CAPS, "execution plan differs")
    sources = plan["source_paths"]
    require(isinstance(sources, list) and all(isinstance(name, str) for name in sources)
            and len(sources) == len(set(sources))
            and MANDATORY_SOURCES <= set(sources) <= set(inputs), "mandatory source closure missing")
    population = plan["population"]
    population_paths = {population[name] for name in ("modeled_path", "dictionary_path", "terminal_result_path")}
    require(len(population_paths) == 3 and population_paths <= set(inputs)
            and not population_paths & set(sources), "population bindings differ")
    require(all(Path(name).suffix in {".py", ".cpp", ".h", ".hpp"}
                or name.startswith("contracts/research/") and Path(name).suffix == ".json"
                for name in sources), "non-source file in source closure")

    # Only metadata and explicitly declared source closure have been read here.
    source_buffers, source_bytes = {}, 0
    for name in sources:
        data = bound_read(ROOT, inputs[name])
        source_bytes += len(data)
        require(source_bytes <= MAX_TOTAL_INPUT_BYTES, "source bytes bound")
        source_buffers[name] = data
    resolver = load_module("field_opportunity_bound_resolver", ROOT / RESOLVER, source_buffers[RESOLVER])
    closure = {str(path.relative_to(ROOT)) for path in resolver.local_source_closure(
        [ROOT / SELF, ROOT / LAB, ROOT / GUARD])}
    require(closure <= set(sources), "transitive local source closure missing")
    verify_runtime(plan["runtime"])

    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    job_id = marker.parent.name.removesuffix(".resources")
    require(marker == ROOT / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl")
            and marker.resolve() == marker, "wrong phase owner")
    paths = list((ROOT / "operations/adaptive/running").glob("*" + job_id + ".json"))
    require(len(paths) == 1, "ambiguous running owner")
    job_bytes = regular_read(paths[0], MAX_INPUT_BYTES)
    job = json.loads(job_bytes)
    require(job["job_id"] == job_id and job["candidate_id"] == ID and job["state"] == "running"
            and job["experiment"] == reference and job["execution_mode"] == "discovery"
            and all(job["resource_budget"].get(key) == value for key, value in CAPS.items()), "job binding differs")
    require(job["runner"] == {"path": SELF, "sha256": inputs[SELF]["sha256"]}
            and job["execution_guard"] == {"path": GUARD, "sha256": inputs[GUARD]["sha256"]},
            "runner or guard source differs")
    candidate = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    require(candidate == {"candidateId": ID, "candidateTreeSha256": job["candidate_tree_sha256"],
                          "receipt": job["candidate_revision"]}, "candidate invocation differs")
    revision = json.loads(bound_read(ROOT, job["candidate_revision"]))
    require(revision["candidateId"] == ID and revision["candidateTreeSha256"] == job["candidate_tree_sha256"],
            "candidate revision differs")
    lab = import_lab(ROOT)
    check_guard(ROOT, job, marker, lab)
    result = ROOT / "results" / ID
    require(result.is_dir() and result.resolve() == result and not any(result.iterdir()), "output is not empty")

    # Population reads begin only after the canonical job, runtime and guard bind.
    buffers = {}
    total = 0
    for name, ref in inputs.items():
        data = source_buffers[name] if name in source_buffers else bound_read(ROOT, ref)
        total += len(data)
        require(total <= MAX_TOTAL_INPUT_BYTES, "total input bytes bound")
        buffers[name] = data
    module = load_module("field_opportunity_bound", ROOT / OBSERVER, buffers[OBSERVER])
    dictionary = buffers[population["dictionary_path"]]
    words = module.base.wrt.read_dictionary_words(SimpleNamespace(read_bytes=lambda: dictionary))
    expected = json.loads(buffers[population["terminal_result_path"]])["program_stats"]["phase"]["adapter"]
    append_marker(marker, "opportunity_scan_start")
    report = scan(module, buffers[population["modeled_path"]], words, population["raw_bytes"],
                  population["raw_sha256"], expected)

    for name, ref in inputs.items():
        require(bound_read(ROOT, ref) == buffers[name], "frozen input changed during scan")
    require(regular_read(paths[0], MAX_INPUT_BYTES) == job_bytes, "running job changed during scan")
    bound_read(ROOT, job["candidate_revision"])
    require(bound_read(ROOT, reference) == contract_bytes, "contract changed during scan")
    verify_runtime(plan["runtime"])
    check_guard(ROOT, job, marker, lab)
    require(time.monotonic() - started < CAPS["wall_seconds"], "aggregate elapsed budget exhausted")
    report.update(experiment=reference, candidate_id=ID, job_id=job_id,
                  execution_plan=inputs[PLAN], runtime=plan["runtime"],
                  candidate_revision=candidate, local_source_paths=sorted(sources),
                  cpu_affinity=sorted(os.sched_getaffinity(0)), elapsed_seconds=time.monotonic() - started,
                  cpu_seconds=time.process_time(), peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  timing_authority="shared-host diagnostic", continuous_guard_decision="await outer closure",
                  independent_wall_limit_seconds=CAPS["wall_seconds"], input_bytes=total)
    raw = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    require(len(raw) <= MAX_REPORT_BYTES, "report bound exceeded")
    require(not any(result.iterdir()), "output changed before publication")
    append_marker(marker, "opportunity_scan_complete")
    temporary = result / "report.tmp"
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    # The canonical job exclusively owns this initially empty output directory.
    # Keep rename as the final fallible operation; failed preparation leaves only
    # unpublished temporary evidence, never a positive report followed by failure.
    require(not (result / "report.json").exists(), "report already exists")
    temporary.replace(result / "report.json")
    return report


if __name__ == "__main__":
    main()
