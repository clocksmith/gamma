"""Real nested-cgroup discovery acceptance; synthetic evidence carries zero score."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
FIXTURE = ROOT / "tests/fixtures/enwiki9_release_canary/package"
GUARD = ROOT / "tools/run_with_resource_guard_v3.py"
MIB = 1024 * 1024
MEMORY = 192 * MIB
INNER_MEMORY = 128 * MIB
SCRATCH = 64 * MIB
PARENT = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice")
CODEC_SHA256 = "80c1d249d50677a917538af5af6f5be1c443ace02cd5d56ce9a350f9fe4114ad"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def reference(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def identity() -> dict:
    text = Path("/proc/self/stat").read_text()
    return {"pid": os.getpid(), "start_ticks": int(text[text.rfind(")") + 2:].split()[19]),
            "affinity": sorted(os.sched_getaffinity(0)),
            "cgroup": Path("/proc/self/cgroup").read_text().strip()}


def marker(event: str) -> None:
    with open(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"], "a") as stream:
        stream.write(json.dumps({"phase": "diagnostic", "event": event,
                                 "detail": "synthetic discovery canary; zero objective credit"}) + "\n")


def payload(case: str, bundle: Path) -> int:
    """Run only the existing tiny codec or deliberate owned cleanup fixture."""
    marker("payload_start")
    os.environ["TMPDIR"] = str(bundle)
    write_json(bundle / "payload-identity.json", identity())
    if case == "deadline":
        pid = os.fork()
        if pid == 0:
            os.setsid()
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            write_json(bundle / "residual-identity.json", identity())
        while True:
            signal.pause()

    corpus = bundle / "synthetic.bin"
    corpus.write_bytes(bytes(range(256)) * 4 + b"A" * 4096 + b"\x00" * 2048 + b"canary\n" * 64)
    commands = []
    # Build independently for both encodes and for a separate decoder process.
    for name in ("encode-a", "encode-b", "decode"):
        directory = bundle / name
        directory.mkdir()
        source = directory / "codec.c"
        source.write_bytes((FIXTURE / "codec.c").read_bytes())
        (directory / "LICENSE").write_bytes((FIXTURE / "LICENSE").read_bytes())
        command = ["/usr/bin/gcc", "-std=c99", "-O2", str(source), "-o", str(directory / "codec")]
        subprocess.run(command, check=True, timeout=10, cwd=directory)
        commands.append(command)
        command = ([str(directory / "codec"), "d", str(bundle / "encode-a/archive.rle"),
                    str(directory / "restored.bin")] if name == "decode" else
                   [str(directory / "codec"), "c", str(corpus), str(directory / "archive.rle")])
        subprocess.run(command, check=True, timeout=10, cwd=directory)
        commands.append(command)
    archive_a = bundle / "encode-a/archive.rle"
    archive_b = bundle / "encode-b/archive.rle"
    restored = bundle / "decode/restored.bin"
    if archive_a.read_bytes() != archive_b.read_bytes() or restored.read_bytes() != corpus.read_bytes():
        raise AssertionError("synthetic repeat or roundtrip differs")
    write_json(bundle / "codec-result.json", {
        "evidenceClass": "synthetic-canary", "objectiveCredit": False, "fullCorpusProof": False,
        "officialScoreBytes": None, "commands": commands, "independentBuilds": 3,
        "separateDecodeProcess": True, "repeatArchiveIdentity": True, "exactRoundtrip": True,
        "input": reference(corpus), "archive": reference(archive_a),
        "repeat": reference(archive_b), "restored": reference(restored)})
    marker("payload_complete")
    return 0


def nested(case: str, bundle: Path, inner: Path) -> int:
    write_json(bundle / "coordinator-identity.json", identity())
    phase = bundle / "inner-phases.jsonl"
    phase.touch(exist_ok=False)
    command = [sys.executable, str(GUARD), "--limit-kib", str(INNER_MEMORY // 1024),
               "--official-decimal-limit-kib", str(INNER_MEMORY // 1024), "--limit-mode", "tree",
               "--cgroup-path", str(inner), "--cgroup-memory-max-bytes", str(INNER_MEMORY),
               "--temporary-disk-limit-bytes", str(SCRATCH), "--scratch-path", str(bundle),
               "--phase-marker-path", str(phase), "--max-logical-cpus", "1",
               "--guard-json", str(bundle / "inner-guard.json"), "--label", bundle.name,
               "--phase", "diagnostic", "--sample-interval", "0.1", "--",
               sys.executable, str(SELF), "--payload", case, "--bundle", str(bundle)]
    return subprocess.call(command, cwd=ROOT)


def check_dead(identity_record: dict) -> bool:
    """PID reuse is not evidence of a surviving original process."""
    try:
        text = Path(f"/proc/{identity_record['pid']}/stat").read_text()
    except FileNotFoundError:
        return True
    fields = text[text.rfind(")") + 2:].split()
    return int(fields[19]) != identity_record["start_ticks"] or fields[0] in {"Z", "X", "x"}


def validate_guard(path: Path, expected_memory: int) -> dict:
    value = json.loads(path.read_text())
    assert value["status"] == "complete" and value["returncode"] == 0, value
    assert not any(value["guards"].values()), value["guards"]
    assert value["cgroup"]["joined_before_exec"] is True
    assert value["cgroup"]["memory_max_bytes"] == expected_memory
    assert not any(value["cgroup_events"]["delta"].values())
    assert value["peaks"]["max_sampled_allowed_cpu_count"] <= 1
    assert value["peaks"]["cgroup_memory_peak_bytes"] < expected_memory
    assert value["peaks"]["max_sampled_scratch_allocated_bytes"] < SCRATCH
    assert value["measurements"]["phase_markers_complete"] is True
    return value


def run_case(lab, case: str, bundle: Path, parent: Path, cpu: int) -> dict:
    bundle.mkdir()
    token = uuid.uuid4().hex[:16]
    job_id = f"discovery-canary-{case}-{token}"
    inner = parent / f"gamma-enwiki9-{job_id}-inner"
    inner.mkdir()
    job = {"job_id": job_id, "candidate_id": bundle.parent.name,
           "execution_mode": "discovery", "timing_authority": "diagnostic",
           "execution_guard": lab.artifact_reference(GUARD),
           "resource_budget": {"cpus": [cpu], "memory_bytes": MEMORY,
                               "scratch_bytes": SCRATCH, "wall_seconds": 30 if case == "exact" else 3,
                               "swap_bytes": 0, "cgroup_parent": str(parent),
                               "existing_guard": {"path": str(inner), "inode": inner.stat().st_ino,
                                                  "memory_bytes": INNER_MEMORY}}}
    handles = []
    waited = False
    process = None
    try:
        command = [sys.executable, str(SELF), "--nested", case, "--bundle", str(bundle), "--inner", str(inner)]
        wrapped, handles = lab.prepare_execution_envelope(job, command, bundle)
        controls = []
        for handle in handles:
            path = Path(handle["path"])
            controls.append({**{k: v for k, v in handle.items() if k != "descriptor"},
                             "memory_max": int((path / "memory.max").read_text()),
                             "swap_max": int((path / "memory.swap.max").read_text()),
                             "kernel_cpuset_available": (path / "cpuset.cpus").is_file(),
                             "cpus": ((path / "cpuset.cpus").read_text().strip()
                                      if (path / "cpuset.cpus").is_file() else None),
                             "empty_before_launch": not (path / "cgroup.procs").read_text().strip()})
        assert sum(row["memory_max"] for row in controls) == MEMORY
        assert all(row["swap_max"] == 0 and row["empty_before_launch"] for row in controls)
        assert all(row["cpus"] in {None, str(cpu)} for row in controls)
        write_json(bundle / "controls.json", controls)
        log = lab.RUN_LOGS / f"{job_id}.log"
        with log.open("a") as stream:
            process = subprocess.Popen(wrapped, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            started = time.monotonic()
            waited = True  # wait_for_budgeted_worker owns handle closure, including its exceptions.
            code = lab.wait_for_budgeted_worker(process, job, handles)
        job["returncode"] = code
        job["observed_elapsed_seconds"] = time.monotonic() - started
        assert job["execution_resources"]["cleanup_complete"] is True
        assert all(not Path(handle["path"]).exists() for handle in handles)
        identities = {}
        for name, expected_group in (("coordinator", handles[-1]["path"]), ("payload", str(inner))):
            value = json.loads((bundle / f"{name}-identity.json").read_text())
            assert value["affinity"] == [cpu]
            assert value["cgroup"] == "0::" + expected_group.removeprefix("/sys/fs/cgroup")
            assert check_dead(value)
            identities[name] = value
        if case == "exact":
            assert code == 0 and not job.get("residual_processes_terminated"), job
            validate_guard(ROOT / job["execution_resources"]["guard_path"], MEMORY - INNER_MEMORY)
            validate_guard(bundle / "inner-guard.json", INNER_MEMORY)
            result = json.loads((bundle / "codec-result.json").read_text())
        else:
            assert code == 124 and job["wall_budget_exceeded"] is True
            assert job["residual_processes_terminated"] is True
            residual = json.loads((bundle / "residual-identity.json").read_text())
            assert residual["affinity"] == [cpu] and residual["cgroup"] == identities["payload"]["cgroup"]
            assert check_dead(residual)
            identities["residual"] = residual
            result = {"deadlineReturncode": code, "originalProcessesAbsentOrZombie": True,
                      "bothOwnedGroupsRemoved": True,
                      "guardFinalizationRequired": False,
                      "reason": "expected deadline interrupts guards; operational timeout evidence only"}
        write_json(bundle / "job.json", job)
        return {"case": case, "verdict": "pass", "result": result, "identities": identities,
                "job": reference(bundle / "job.json"), "controls": reference(bundle / "controls.json"),
                "log": reference(log), "outerGuard": reference(ROOT / job["execution_resources"]["guard_path"])}
    finally:
        if not waited:
            for handle in handles:
                if lab._group_populated(handle["descriptor"]):
                    lab._group_write(handle["descriptor"], "cgroup.kill", "1\n")
                os.close(handle["descriptor"])
                Path(handle["path"]).rmdir()
            if inner.exists():
                inner.rmdir()


def run_canary(bundle: Path, parent: Path, cpu: int) -> Path:
    sys.path.insert(0, str(ROOT / "tools"))
    import enwiki9_lab as lab
    if not bundle.is_relative_to(ROOT / "results") or bundle.parent != ROOT / "results":
        raise ValueError("bundle must be a fresh direct results/discovery_canary_* directory")
    if not bundle.name.startswith("discovery_canary_") or bundle.exists():
        raise ValueError("fresh discovery_canary_ namespace is required")
    if cpu not in os.sched_getaffinity(0):
        raise ValueError("assigned CPU is unavailable")
    os.sched_setaffinity(0, {cpu})
    # The harness and outer observer inherit this per-process address-space cap;
    # actual candidate groups additionally have an aggregate 192 MiB kernel cap.
    resource.setrlimit(resource.RLIMIT_AS, (128 * MIB, 128 * MIB))
    resource.setrlimit(resource.RLIMIT_FSIZE, (SCRATCH, SCRATCH))
    sources = [SELF, Path(lab.__file__), GUARD, ROOT / "tools/research_contracts.py",
               FIXTURE / "codec.c", FIXTURE / "LICENSE"]
    bindings = [reference(path) for path in sources]
    if reference(FIXTURE / "codec.c")["sha256"] != CODEC_SHA256:
        raise ValueError("frozen release canary codec source changed")
    for name in ("cgroup.controllers", "cgroup.subtree_control"):
        if not (parent / name).is_file():
            raise ValueError(f"delegated parent lacks required controller file: {parent / name}")
    bundle.mkdir()
    lab.RUN_LOGS.mkdir(parents=True, exist_ok=True)
    cases = []
    try:
        for case in ("exact", "deadline"):
            cases.append(run_case(lab, case, bundle / case, parent, cpu))
        assert [reference(path) for path in sources] == bindings, "source changed during canary"
        receipt = bundle / "discovery-canary.json"
        write_json(receipt, {"schema": "gamma.enwiki9.discovery-canary.v1",
                            "evidenceClass": "synthetic-infrastructure-canary", "objectiveCredit": False,
                            "fullCorpusProof": False, "officialScoreBytes": None, "verdict": "pass",
                            "sources": bindings, "resourceBudget": {"cpus": [cpu], "aggregateCgroupMemoryBytes": MEMORY,
                                "perProcessAddressSpaceBytes": 128 * MIB, "swapBytes": 0,
                                "scratchBytes": SCRATCH, "maximumCaseDeadlineSeconds": 30},
                            "cpuAuthority": {"kernelCpuSetAvailable": (parent / "cpuset.cpus.effective").is_file(),
                                             "tasksetInheritedAffinityVerified": True,
                                             "v3SampledAffinityGuardVerified": True,
                                             "timing": "diagnostic"},
                            "scope": "real nested guards and kernel containment; no corpus, candidate queue or score authority",
                            "cases": cases,
                            "reproduce": ["python3", str(SELF.relative_to(ROOT)), "--bundle", "results/discovery_canary_NEW",
                                          "--cgroup-parent", str(parent), "--cpu", str(cpu)]})
        return receipt
    except BaseException as exc:
        write_json(bundle / "failure.json", {"schema": "gamma.enwiki9.discovery-canary-failure.v1",
                                             "objectiveCredit": False, "verdict": "failure", "error": repr(exc),
                                             "sources": bindings, "completedCases": cases})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--cgroup-parent", type=Path, default=PARENT)
    parser.add_argument("--cpu", type=int, default=4)
    parser.add_argument("--nested", choices=("exact", "deadline"), help=argparse.SUPPRESS)
    parser.add_argument("--payload", choices=("exact", "deadline"), help=argparse.SUPPRESS)
    parser.add_argument("--inner", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.payload:
        raise SystemExit(payload(args.payload, args.bundle))
    if args.nested:
        raise SystemExit(nested(args.nested, args.bundle, args.inner))
    path = run_canary(args.bundle.resolve(), args.cgroup_parent, args.cpu)
    print(json.dumps(reference(path), indent=2))
