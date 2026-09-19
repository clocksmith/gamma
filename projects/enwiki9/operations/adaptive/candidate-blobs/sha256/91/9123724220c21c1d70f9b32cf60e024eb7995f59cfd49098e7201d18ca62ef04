#!/usr/bin/env python3
"""Authenticate one FIFO128 discovery gate and close the existing driver comparison.

No arm subprocess runner or scientific ledger is created here. The candidate shim
must emit DECODE_MARKER followed by its independent decoder statistics and bound
each codec call with a 180-second alarm. The canonical envelope owns aggregate
memory, scratch, CPU affinity and elapsed-stop enforcement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib import driver
from tools import causal_wordcode_fifo128_bz2_v1 as codec

ARMS = {"parent": "P", "bookkeeping": "K", "treatment": "T", "literal_control": "L"}
DECODE_MARKER = "CAUSAL_WORDCODE_DECODE "
SELF = "tools/causal_wordcode_fifo128_gate_v1.py"
CORE = "tools/causal_wordcode_fifo128_bz2_v1.py"
PARENT = "programs/opcode_word_bz2_v1/program.py"
PLAN = "operations/provenance/causal_wordcode_fifo128_bz2_q0_v1_plan.json"
PINS = {CORE: "b544258134ad41d0235a744a0aff1fa8b42131c01230a7ddb9b45580d838f508",
        PARENT: "105af140b519896047cafbc41827e073100782ff1b212573279fa38a39c8c6d0",
        PLAN: "0bf50b68dc69a175e658cb161f523e6451d641842281734637ef4e455a4d023f"}
POPULATION = {"path": "operations/evidence/fixtures/dualstream_opening250k_v1.raw", "bytes": 250000,
              "sha256": "665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3"}
P_HASH = "2302f0c966ba4b5e4edce5b9ce672898f5846d6d71016c9826c1dcdef20f781e"
CAPS = {"cpus": [4], "memory_bytes": 536870912, "scratch_bytes": 67108864,
        "swap_bytes": 0, "wall_seconds": 600}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return driver._sha256_file(Path(path))


def read(path):
    return json.loads(Path(path).read_text())


def path_in_root(name):
    path = ROOT / name
    require(not Path(name).is_absolute() and ".." not in Path(name).parts
            and path.resolve() == path and path.is_file(), "aliased or missing input: " + name)
    return path


def check_reference(reference):
    path = path_in_root(reference["path"])
    require(sha(path) == reference["sha256"].removeprefix("sha256:"), "changed input: " + reference["path"])
    return path


def authenticate_live(candidate, reference, plan):
    require(json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) == reference,
            "canonical experiment invocation is absent")
    require(os.sched_getaffinity(0) == {4}, "worker must inherit CPU4")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    job_id = marker.parent.name.removesuffix(".resources")
    require(marker == ROOT / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl")
            and marker.resolve() == marker, "phase marker ownership differs")
    jobs = list((ROOT / "operations/adaptive/running").glob("*" + job_id + ".json"))
    require(len(jobs) == 1, "canonical running job is missing or ambiguous")
    job = read(jobs[0])
    require(job["job_id"] == job_id and job["candidate_id"] == candidate and job["experiment"] == reference
            and job["state"] == "running" and job["execution_mode"] == "discovery"
            and all(job["resource_budget"].get(k) == v for k, v in CAPS.items()), "job authority differs")
    require(job["runner"] == {"path": SELF, "sha256": "sha256:" + sha(ROOT / SELF)}, "runner binding differs")
    check_reference(job["execution_guard"])
    bound = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    require(bound == {"candidateId": candidate, "candidateTreeSha256": job["candidate_tree_sha256"],
                      "receipt": job["candidate_revision"]}, "candidate revision invocation differs")
    check_reference(job["candidate_revision"])
    resources = job["execution_resources"]
    require(resources["boot_id"] == Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "foreign boot")
    pid = job["worker_pid"]
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    require(fields[0] not in {"Z", "X", "x"} and int(fields[19]) == job["worker_proc_start_ticks"]
            and hashlib.sha256(Path(f"/proc/{pid}/cmdline").read_bytes().rstrip(b"\0")).hexdigest()
            == resources["guard_command_sha256"], "guard process identity differs")
    ancestor = os.getpid()
    while ancestor > 1 and ancestor != pid:
        ancestor = int(Path(f"/proc/{ancestor}/stat").read_text().rsplit(")", 1)[1].split()[1])
    require(ancestor == pid, "runner is not a descendant of its canonical guard")
    group = Path(resources["cgroup_path"])
    membership = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
    require(group == Path("/sys/fs/cgroup" + membership) and group.stat().st_ino == resources["cgroup_inode"],
            "cgroup identity differs")
    require((group / "memory.max").read_text().strip() == str(CAPS["memory_bytes"])
            and (group / "memory.swap.max").read_text().strip() == "0", "cgroup memory enforcement differs")
    guard_path = path_in_root(resources["guard_path"])
    require(guard_path == marker.parent / "guard.json", "guard receipt ownership differs")
    guard = read(guard_path)
    require(guard["status"] == "running" and guard["label"] == job_id and guard["phase"] == "diagnostic"
            and guard["cgroup"]["path"] == str(group) and guard["cgroup"]["inode"] == group.stat().st_ino
            and guard["cgroup"]["requested_memory_max_bytes"] == CAPS["memory_bytes"]
            and guard["temporary_disk_limit_bytes"] == CAPS["scratch_bytes"]
            and guard["max_logical_cpus"] == 1 and not any(guard["guards"].values()), "active guard differs or failed")
    return job_id


def authenticate(candidate, *, live=True):
    require(re.fullmatch(r"[a-z0-9_]+", candidate), "unsafe candidate identity")
    contract_path = path_in_root("operations/adaptive/experiments/" + candidate + ".json")
    driver.research_contracts.validate_artifact(contract_path)
    contract = read(contract_path)
    reference = {"path": str(contract_path.relative_to(ROOT)), "sha256": "sha256:" + sha(contract_path)}
    require(contract["experimentId"] == candidate and contract["status"] == "frozen"
            and contract["registrationTiming"] == "prospective" and contract["objectiveCreditBytes"] == 0,
            "prospective frozen contract is required")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]) and SELF in inputs, "input identities differ")
    for row in inputs.values():
        check_reference(row)
    require(all(name in inputs and sha(ROOT / name) == digest for name, digest in PINS.items()), "measured source or plan changed")
    plans = [row for row in inputs.values() if row["id"] == "wordcode-gate-plan"]
    require(len(plans) == 1, "one frozen wordcode-gate-plan is required")
    plan = read(ROOT / plans[0]["path"])
    require(plan["candidate_id"] == candidate and plan["population"] == POPULATION
            and plan["resources"] == CAPS and plan["specification"]["arms"] == ARMS,
            "frozen population, resources or P/K/T/L selection differs")
    require(contract["population"]["scopeBytes"] == POPULATION["bytes"] and POPULATION["path"] in inputs,
            "opening population is unbound")
    require((ROOT / POPULATION["path"]).stat().st_size == POPULATION["bytes"], "opening fixture length differs")
    require(plan["historical_parent_program_bytes"] == 1448, "historical package baseline differs")
    runtime = plan["runtime_files"]
    import _bz2
    require({str(Path(sys.executable).resolve()), str(Path(_bz2.__file__).resolve())}
            <= {row["path"] for row in runtime}, "Python and BZip2 runtime bindings are required")
    for row in runtime:
        path = Path(row["path"])
        require(path.is_absolute() and path.resolve() == path and path.stat().st_size == row["bytes"]
                and sha(path) == row["sha256"].removeprefix("sha256:"), "runtime changed")
    candidate_dir = driver._candidate_program_dir(candidate)
    source = candidate_dir / "program.py"
    candidate_name = "programs/" + candidate + "/program.py"
    expected_source = plan["candidate_source"]
    require(set(expected_source) == {"path", "sha256", "bytes"} and expected_source["path"] == candidate_name,
            "prospective candidate source identity differs")
    for actual in (source, path_in_root(candidate_name)):
        require(actual.is_file() and not actual.is_symlink() and actual.stat().st_size == expected_source["bytes"]
                and sha(actual) == expected_source["sha256"].removeprefix("sha256:"), "candidate source differs from frozen plan")
    def canonical(path):
        return (Path("programs") / candidate / path.relative_to(candidate_dir)).as_posix() if path.is_relative_to(candidate_dir) else path.relative_to(ROOT).as_posix()
    closure = set(driver._comparison_source_closure(source))
    for path in closure:
        name = canonical(path)
        if name == candidate_name:
            continue  # Prospective plan binds this future file before develop materializes it.
        require(name in inputs and sha(path) == inputs[name]["sha256"].removeprefix("sha256:"), "unbound actual driver source: " + name)
    files = plan["local_package_files"]
    require(len(set(files)) == len(files) and {CORE, PARENT, "programs/" + candidate + "/program.py"} <= set(files), "codec source accounting is incomplete")
    counted = driver._program_package_inventory(candidate_dir, driver._load_program_metadata(candidate))[1]["counted_files"]
    require(all("programs/" + candidate + "/" + row["path"] in files for row in counted), "candidate package member omitted")
    require(all(name in inputs or name == candidate_name for name in files), "package member is unbound")
    harness = set(driver._comparison_source_closure(ROOT / "lib/driver.py"))
    require(all(canonical(path) in files for path in closure - harness), "codec dependency omitted from local package")
    plan["measured_local_package_bytes"] = sum(path_in_root(name).stat().st_size for name in files)
    require(max(0, plan["measured_local_package_bytes"] - 1448) <= 32768, "local source reserve exceeded")
    job_id = authenticate_live(candidate, reference, plan) if live else None
    return plan, reference, job_id


def close_comparison(directory, plan, *, historical=True):
    """Independently validate the driver's closed artifacts and mandatory states."""
    decision = read(directory / "decision.json")
    require(all(decision.get(key) is True for key in ("source_stable", "same_candidate_build", "same_input_population",
            "artifact_closure_valid", "exact_roundtrips_and_repeats", "parent_bookkeeping_identity")), "driver comparison is incomplete")
    require(not decision["errors"] and set(decision["arms"]) == set(ARMS), "driver arms differ or failed")
    build = read(directory / "build.json")
    require(sha(directory / "build.json") == decision["frozen_build"]["sha256"], "build manifest changed")
    require(not driver._verify_frozen_build({"root": directory / "build", "manifest_path": directory / "build.json",
            "manifest": build, "sha256": decision["frozen_build"]["sha256"]}), "frozen build changed")
    rows, states, pids = {}, set(), set()
    for role, arm in ARMS.items():
        folder = directory / arm
        row = read(folder / "result.json")
        require(decision["arms"][role] == {"arm": arm, "result": arm + "/result.json", "result_sha256": sha(folder / "result.json")}
                and not driver._verify_arm_artifacts(folder, row), "closed arm artifact changed")
        require(row["data_size"] == plan["population"]["bytes"] and row["data_sha256"] == plan["population"]["sha256"], "arm population differs")
        archive = folder / "archive.bin"
        archive_hash, size = sha(archive), archive.stat().st_size
        with archive.open("rb") as stream:
            header = stream.read(5)
        require(5 <= size <= codec.MAX_ARCHIVE and (header[:4] == b"OWB1" if arm in "PK" else
                header == (b"OWF1t" if arm == "T" else b"OWF1l")), "archive header or size differs")
        require(sha(folder / "restored.bin") == plan["population"]["sha256"] and sha(folder / "repeat.bin") == archive_hash, "inverse or repeat differs")
        reports = []
        for phase in ("encode", "decode", "repeat"):
            execution = row["phase_execution"][phase]
            detail = read(folder / (phase + ".json"))
            require(execution["returncode"] == 0 and detail["codec_complete"] is True and detail["pid"] == execution["pid"], "phase did not finish independently")
            pids.add(detail["pid"])
            loaded = read(folder / (phase + ".sources.json"))
            require(loaded["pid"] == detail["pid"] and loaded["build_manifest_sha256"] == decision["frozen_build"]["sha256"]
                    and loaded["loaded_sources"] == execution["loaded_sources"]
                    and loaded["loaded_sources"].get("projects/enwiki9/" + CORE) == PINS[CORE], "independent loaded source receipt differs")
            if phase == "decode":
                lines = (folder / "decode.stdout.log").read_text().splitlines()
                records = [line[len(DECODE_MARKER):] for line in lines if line.startswith(DECODE_MARKER)]
                require(len(records) == 1, "mandatory independent decoder state is absent or ambiguous")
                report = json.loads(records[0])
            else:
                report = detail.get("program_stats")
            require(isinstance(report, dict), "mandatory codec state is missing")
            require(report["arm"] == arm and report["raw_sha256"] == plan["population"]["sha256"]
                    and report["raw_bytes"] == plan["population"]["bytes"] and report["archive_sha256"] == archive_hash
                    and report["complete_archive_bytes"] == size and report["framing_bytes"] == 5
                    and report["framing_bytes"] + report["compressed_payload_bytes"] == size
                    and report["parent_source_sha256"] == PINS[PARENT], "codec identity or complete byte accounting differs")
            require(all(re.fullmatch(r"[0-9a-f]{64}", report[key]) for key in ("state_digest", "transition_digest")), "state digest malformed")
            states.add((report["state_digest"], report["transition_digest"]))
            reports.append(report)
        require(reports[0] == reports[2], "repeated encoder accounting differs")
        rows[arm] = {"archive_bytes": size, "archive_sha256": archive_hash, "state_digest": reports[0]["state_digest"],
                     "transition_digest": reports[0]["transition_digest"], "framing_bytes": 5,
                     "payload_bytes": size - 5, "codec_seconds": {p: row["phase_execution"][p]["codec_time_s"] for p in ("encode", "decode", "repeat")}}
    require(len(pids) == 12 and len(states) == 1, "independent process or complete state agreement failed")
    require(rows["P"]["archive_sha256"] == rows["K"]["archive_sha256"], "P/K payload identity differs")
    if historical:
        require(rows["P"]["archive_sha256"] == P_HASH and rows["P"]["archive_bytes"] == 71887, "historical P archive differs")
    increment = max(0, plan["measured_local_package_bytes"] - plan["historical_parent_program_bytes"])
    paying = all(rows["T"]["archive_bytes"] + increment < rows[arm]["archive_bytes"] for arm in ("P", "L"))
    return {"correctness_pass": True, "processes": 12, "arms": rows, "local_package_bytes": plan["measured_local_package_bytes"],
            "incremental_local_source_bytes": increment, "local_cost_predicate_pass": paying,
            "status": "measured-local-improvement" if paying else "held-nonpaying-realization"}


def run_comparison(candidate, population, destination, plan, reference, *, reauthenticate, synthetic=False):
    """Synthetic callers supply a fixture and mock authority; the CLI never bypasses admission."""
    require(destination.is_dir() and not any(destination.iterdir()), "result directory must exist and be empty")
    require(plan["specification"]["arms"] == ARMS, "P/K/T/L specification differs")
    require(population.stat().st_size == plan["population"]["bytes"] <= (32768 if synthetic else 250000), "population bound differs")
    require(sha(population) == plan["population"]["sha256"], "population hash differs")
    reauthenticate()
    stage = {"schema": "gamma.enwiki9.causal-wordcode-stage.v1", "candidate_id": candidate,
             "experiment": reference, "synthetic_only": synthetic, "timing_authority": "diagnostic",
             "complete_package_bytes": None, "qualification_complete": False, "promotion_authorized": False,
             "objective_credit_bytes": 0, "correctness_pass": False}
    phase = "comparison"
    try:
        driver.compare(candidate, population, plan["population"]["bytes"], plan["specification"],
                       destination / "comparison", mode="discovery", record_ledger=False)
        phase = "evidence-validation"
        stage.update(close_comparison(destination / "comparison", plan, historical=not synthetic))
        require(sha(population) == plan["population"]["sha256"], "population changed after execution")
        phase = "reauthentication"
        reauthenticate()
        stage["frozen_inputs_reverified"] = True
    except Exception as error:
        codes = []
        for path in (destination / "comparison").glob("*/result.json"):
            codes.extend(row["returncode"] for row in read(path).get("phase_execution", {}).values())
        failure = "mandatory-evidence-failure" if phase == "evidence-validation" else "implementation-failure"
        if phase == "reauthentication" or isinstance(error, OSError):
            failure = "infrastructure-failure"
        if -signal.SIGKILL in codes:
            failure = "process-killed-cause-unresolved"
        if any(code in (-signal.SIGXCPU, -signal.SIGALRM, -signal.SIGXFSZ) for code in codes):
            failure = "budget-exhausted"
        stage.update(correctness_pass=False, status="failed", failure_class=failure,
                     error=type(error).__name__ + ": " + str(error))
    decision = destination / "comparison/decision.json"
    if decision.is_file():
        stage["comparison"] = {"path": "comparison/decision.json", "sha256": sha(decision)}
    payload = (json.dumps(stage, sort_keys=True, indent=2) + "\n").encode()
    codec.publish(destination / "stage-decision.json", payload)
    return stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    plan, reference, _ = authenticate(args.candidate, live=not args.validate_only)
    if args.validate_only:
        print(json.dumps({"preflight_pass": True, "executed": False, "launch_authorized": False}))
        return 0
    for which, cap in ((resource.RLIMIT_CPU, 60), (resource.RLIMIT_AS, 536870912), (resource.RLIMIT_FSIZE, 33554432)):
        old = resource.getrlimit(which)
        resource.setrlimit(which, (min(old[0], cap) if old[0] != resource.RLIM_INFINITY else cap,
                                  min(old[1], cap) if old[1] != resource.RLIM_INFINITY else cap))
    result = run_comparison(args.candidate, ROOT / plan["population"]["path"], ROOT / "results" / args.candidate,
                            plan, reference, reauthenticate=lambda: authenticate(args.candidate))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["correctness_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
