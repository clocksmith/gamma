#!/usr/bin/env python3
"""One canonical observation-only scan; no arithmetic coding or model inference."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_causal_field_opportunity_q0_v1"
SELF = "tools/causal_field_opportunity_gate_v1.py"
OBSERVER = "tools/causal_field_opportunity_v1.py"
CAPS = {"cpus": [2], "memory_bytes": 536870912, "scratch_bytes": 33554432,
        "swap_bytes": 0, "wall_seconds": 120}


def require(value, message):
    if not value:
        raise ValueError(message)


def bound_read(root, reference, maximum=8 * 1024**2):
    name = reference["path"]
    path = root / name
    require(not Path(name).is_absolute() and ".." not in Path(name).parts
            and path.resolve() == path, "aliased input")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(len(data) <= maximum and identity(before) == identity(after) == identity(path.stat()),
            "input replaced or exceeds read bound")
    require(hashlib.sha256(data).hexdigest() == reference["sha256"].removeprefix("sha256:"),
            "input digest changed: " + name)
    return data


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
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
    reference = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    contract = json.loads(bound_read(ROOT, reference))
    require(contract["experimentId"] == ID and contract["status"] == "frozen", "wrong experiment")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    job_id = marker.parent.name.removesuffix(".resources")
    require(marker == ROOT / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl"), "wrong phase owner")
    paths = list((ROOT / "operations/adaptive/running").glob("*" + job_id + ".json"))
    require(len(paths) == 1, "ambiguous running owner")
    job = json.loads(paths[0].read_text())
    require(job["candidate_id"] == ID and job["state"] == "running" and job["experiment"] == reference
            and job["execution_mode"] == "discovery"
            and all(job["resource_budget"].get(k) == v for k, v in CAPS.items()), "job binding differs")
    require(os.sched_getaffinity(0) == {2} and job["worker_pid"] == os.getppid(), "guard ancestry or CPU differs")
    # Reuse canonical exact worker/guard identity checks before reading population bytes.
    import enwiki9_lab as lab
    require(lab.worker_pid_matches_job(job), "canonical live guard identity differs")
    group = Path(job["execution_resources"]["cgroup_path"])
    membership = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
    require(group == Path("/sys/fs/cgroup" + membership)
            and group.stat().st_ino == job["execution_resources"]["cgroup_inode"], "cgroup differs")
    require((group / "memory.max").read_text().strip() == str(CAPS["memory_bytes"])
            and (group / "memory.swap.max").read_text().strip() == "0", "memory allocation differs")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]), "duplicate inputs")
    require(inputs[SELF]["sha256"] == job["runner"]["sha256"] and job["runner"]["path"] == SELF, "runner differs")
    buffers = {name: bound_read(ROOT, ref) for name, ref in inputs.items()}
    result = ROOT / "results" / ID
    require(result.is_dir() and result.resolve() == result and not any(result.iterdir()), "output is not empty")
    module = ModuleType("field_opportunity_bound")
    module.__file__ = str(ROOT / OBSERVER)
    sys.modules[module.__name__] = module
    exec(compile(buffers[OBSERVER], module.__file__, "exec"), module.__dict__)
    population = contract["observationPopulation"]
    words = module.base.wrt.read_dictionary_words(ROOT / population["dictionary_path"])
    require(bound_read(ROOT, inputs[population["dictionary_path"]]) == buffers[population["dictionary_path"]], "dictionary changed")
    expected = json.loads(buffers[population["terminal_result_path"]])["program_stats"]["phase"]["adapter"]
    with marker.open("a") as stream:
        stream.write(json.dumps({"phase": "diagnostic", "event": "opportunity_scan_start"}) + "\n")
    report = scan(module, buffers[population["modeled_path"]], words, population["raw_bytes"], population["raw_sha256"], expected)
    for name, ref in inputs.items():
        bound_read(ROOT, ref)
    require(time.monotonic() - started < CAPS["wall_seconds"], "aggregate elapsed budget exhausted")
    report.update(experiment=reference, candidate_id=ID, job_id=job_id, cpu_affinity=sorted(os.sched_getaffinity(0)),
                  elapsed_seconds=time.monotonic() - started, cpu_seconds=time.process_time(),
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  timing_authority="shared-host diagnostic", continuous_guard_decision="await outer closure")
    temporary = result / "report.tmp"
    with temporary.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(result / "report.json")
    with marker.open("a") as stream:
        stream.write(json.dumps({"phase": "diagnostic", "event": "opportunity_scan_complete"}) + "\n")


if __name__ == "__main__":
    main()
