#!/usr/bin/env python3
"""Print canonical terminal records only after explicit closed-job authorization.

This is a read-only normalizer, not a launcher or codec replay. Supply the exact
completed job and closed guard hashes provided by ROOT after closure. Stdout is
one JSON object mapping publication paths to canonical JSON strings; ROOT owns
publication and reflection. No running result is read during module import.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import stat
import sys

ROOT = Path(__file__).resolve().parents[3]
CID = "midas_open_observed_sha_opening250k_q0_v1"
JID = "20260907T201808Z_5c99705f63"
CONTRACT = "operations/adaptive/experiments/" + CID + ".json"
CONTRACT_SHA = "5f2a16552c89b45aa280752911430de930b23538f04e77722a3bcca2feb51398"
DEST = "operations/provenance/midas_open_observed_sha_opening250k_terminal_20260907"
SELF = DEST + "/record.py"
RESULT = "results/" + CID + "/"
HISTORICAL = "results/midas_open_incremental_corpus250k_q0_v1/"
HISTORICAL_TERMINAL = "operations/provenance/midas_open_incremental_corpus250k_terminal_20260906.json"
ARMS = "PKFS"
PHASES = ("reference", "encode", "decode", "repeat")
MAX_FILE = 32 * 1024**2
GENERATED = {RESULT + arm + "/result.json" for arm in ARMS} | {
    RESULT + "decision.json", RESULT + "historical-comparison.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    path = ROOT / path
    require(path.resolve() == path, "aliased path: " + str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= MAX_FILE,
                "not a bounded regular file: " + str(path))
        data = stream.read(MAX_FILE + 1)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(len(data) == before.st_size and identity(before) == identity(after) == identity(path.lstat()),
            "file changed while read: " + str(path))
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def load(path):
    return json.loads(read(path))


def ref(path, data=None, sized=False):
    data = read(path) if data is None else data
    result = {"path": path, "sha256": "sha256:" + sha(data)}
    if sized:
        result["bytes"] = len(data)
    return result


def verify(row):
    data = read(row["path"])
    require(sha(data) == row["sha256"].removeprefix("sha256:") and
            ("bytes" not in row or len(data) == row["bytes"]), "binding differs: " + row["path"])
    return data


def files_below():
    found = set()
    for directory, subdirs, names in os.walk(ROOT / RESULT, followlinks=False):
        for name in subdirs:
            require(not (Path(directory) / name).is_symlink(), "result directory is an alias")
        for name in names:
            path = Path(directory) / name
            require(stat.S_ISREG(path.lstat().st_mode), "nonregular result file")
            found.add(str(path.relative_to(ROOT)))
    return found


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def closed_authority(args):
    """No result-directory read is permitted before this returns."""
    path = args.closed_job
    require(Path(path).parent == Path("operations/adaptive/completed") and
            Path(path).name.endswith("_" + JID + ".json"), "not the authorized completed job")
    job = json.loads(verify({"path": path, "sha256": args.job_sha256}))
    require(job["job_id"] == JID and job["candidate_id"] == CID and job["state"] == "completed" and
            job["returncode"] == 0 and job.get("finished_at"), "job is not successfully terminal")
    resources = job["execution_resources"]
    require(resources["cleanup_complete"] is True, "canonical cleanup is incomplete")
    guard_path = "run_logs/adaptive/" + JID + ".resources/guard.json"
    require(resources["guard_path"] == guard_path, "guard path differs")
    guard = json.loads(verify({"path": guard_path, "sha256": args.guard_sha256}))
    require(guard["label"] == JID and guard["status"] == "complete" and guard["returncode"] == 0 and
            guard["guards"] and all(v is False for v in guard["guards"].values()) and
            guard["latest_sample"]["processes"] == [], "guard is not cleanly closed")
    require(guard["cgroup"]["path"] == resources["cgroup_path"] and
            guard["cgroup"]["inode"] == resources["cgroup_inode"] and
            not Path(resources["cgroup_path"]).exists(), "owned cgroup closure differs")
    contract = json.loads(verify({"path": CONTRACT, "sha256": CONTRACT_SHA}))
    require(job["experiment"] == ref(CONTRACT) and contract["experimentId"] == CID and
            contract["status"] == "frozen" and contract["registrationTiming"] == "prospective" and
            contract["objectiveCreditBytes"] == 0, "frozen experiment identity differs")
    inputs = {r["path"]: r for r in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]) == 366, "input closure differs")
    # Authenticate the import closure before importing project helpers. Full
    # authentication below also rehashes every other frozen input and runtime.
    for name, row in inputs.items():
        if name.endswith(".py"):
            verify(row)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    from tools import midas_open_observed_sha_gate_v1 as gate
    from tools import research_contracts
    research_contracts.validate_artifact(ROOT / CONTRACT, verify_files=True)
    verified_contract, plan, manifests = gate.authenticate(CID, validate=True)
    require(verified_contract == contract, "contract changed during authentication")
    require(job["tool"] == gate.SELF and job["tool_args"] == ["--candidate", CID], "job runner differs")
    for field in ("runner", "execution_guard"):
        row = job[field]
        require(row["path"] in inputs and verify(row) == verify(inputs[row["path"]]), "unbound job source")
    revision = json.loads(verify(job["candidate_revision"]))
    require(revision["candidateId"] == CID and revision["candidateTreeSha256"] == job["candidate_tree_sha256"],
            "candidate revision differs")
    research_contracts.validate_artifact(ROOT / job["candidate_revision"]["path"], verify_files=True)
    proposal = json.loads(verify(job["proposal"]))
    require(proposal["candidate_id"] == proposal["proposal_id"] == job["proposal_id"] == CID and
            proposal["owner"] == "root_explore" and proposal["experiment"] == job["experiment"] and
            proposal["parent"] == contract["parent"]["candidateId"] and
            revision["parentRevision"]["receipt"] == contract["parent"]["revision"],
            "proposal owner, experiment or revision ancestry differs")
    require(revision["immutableBlobsComplete"] is True and
            {r["path"] for r in revision["files"]} == {"meta.json", "program.py"}, "candidate blob population differs")
    blobs = {}
    for row in revision["files"]:
        blobs[row["path"]] = verify({"path": row["blobPath"], "bytes": row["bytes"], "sha256": row["sha256"]})
    metadata = json.loads(blobs["meta.json"])
    require(metadata["id"] == CID and metadata["omega"]["experiment"] == job["experiment"] and
            metadata["omega"]["proposal_id"] == CID and metadata["parent"] == proposal["parent"],
            "immutable candidate metadata association differs")
    marker = {node.targets[0].id: ast.literal_eval(node.value)
              for node in ast.parse(blobs["program.py"]).body
              if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    require(marker == {"CANDIDATE_ID": CID, "SCOPE_BYTES": 250000, "SCOPE_SYMBOLS": 2000000,
                       "OBJECTIVE_CREDIT_BYTES": 0, "TOOL_SHA256": inputs[gate.SELF]["sha256"].removeprefix("sha256:")},
            "immutable candidate marker differs")
    for budget in (job["resource_budget"], resources["budget"]):
        require({k: budget[k] for k in plan["resources"]} == plan["resources"], "canonical budget differs")
    budget = plan["resources"]
    require(budget == {"cpus": [2], "memory_bytes": 2147483648, "scratch_bytes": 536870912,
                       "swap_bytes": 0, "wall_seconds": 3600}, "frozen resource population differs")
    require(guard["cgroup"]["memory_max_bytes"] == budget["memory_bytes"] and
            guard["temporary_disk_limit_bytes"] == budget["scratch_bytes"] and
            guard["max_logical_cpus"] == 1 and guard["limit_kib"] * 1024 == budget["memory_bytes"],
            "guard caps differ")
    require(guard["elapsed_s"] <= budget["wall_seconds"] and
            job["elapsed_seconds"] <= budget["wall_seconds"], "aggregate elapsed stop exceeded")
    peaks = guard["peaks"]
    require(peaks["max_sampled_tree_rss_kib"] * 1024 <= budget["memory_bytes"] and
            peaks["cgroup_memory_peak_bytes"] <= budget["memory_bytes"] and
            peaks["max_sampled_scratch_logical_bytes"] <= budget["scratch_bytes"] and
            peaks["max_sampled_allowed_cpu_count"] <= 1, "closed peak exceeds budget")
    require(guard["measurements"]["phase_markers_complete"] and
            guard["measurements"]["cgroup_v2_complete"] and guard["measurements"]["affinity_complete"],
            "mandatory guard measurements incomplete")
    require(guard["command"][-3:] == [str(ROOT / gate.SELF), "--candidate", CID], "guard command differs")
    return job, guard, guard_path, contract, inputs, plan, manifests, gate, research_contracts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closed-job", required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--guard-sha256", required=True)
    parser.add_argument("--closure-authorized", required=True, action="store_true",
                        help="ROOT has explicitly authorized closed-result inspection")
    args = parser.parse_args()
    job, guard, guard_path, contract, inputs, plan, manifests, gate, contracts = closed_authority(args)
    observer = gate.original.observer
    stage_path, artifact_path = RESULT + "stage-decision.json", RESULT + "artifacts.json"
    stage, indexed = load(stage_path), load(artifact_path)
    terminal_snapshot = [ref(p, sized=True) for p in (stage_path, artifact_path, SELF)]
    current_revision = load(job["candidate_revision"]["path"])
    revision_blobs = [{"path": r["blobPath"], "bytes": r["bytes"], "sha256": r["sha256"]}
                      for r in current_revision["files"]]
    require(stage["candidate_id"] == CID and stage["experiment"] == ref(CONTRACT) and
            stage["objective"] == contract["objective"] and stage["status"] == "passed", "stage identity/status differs")
    validity = ("infrastructure_pass", "all_boundaries_equal", "all_reference_archives_equal",
                "all_reference_final_states_equal", "pk_identity", "child_closure_ok", "artifact_index_complete")
    require(all(stage[k] is True for k in validity), "stage lacks required correctness evidence")
    require(stage["native_phases"] == len(stage["commands"]) == 16 and stage["raw_bytes"] == 250000 and
            stage["population_kind"] == "corpus" and stage["objective_credit_bytes"] == 0 and
            stage["complete_package_bytes"] is None and stage["full_corpus_score_bytes"] is None and
            stage["resource_qualified"] is False, "stage scope differs")
    require(indexed["complete"] is True and indexed["errors"] == [] and len(indexed["files"]) == 150,
            "worker index is incomplete")
    verify(stage["artifacts"])
    require(stage["artifacts"]["path"] == artifact_path, "stage names another index")
    for row in indexed["files"]:
        verify(row)
    declared, actual = set(contract["outputs"]), files_below()
    require(len(declared) == len(contract["outputs"]) == 158 and GENERATED <= declared and
            declared - GENERATED <= actual <= declared, "declared output population differs")
    require({r["path"] for r in indexed["files"]} == declared - GENERATED - {stage_path, artifact_path},
            "worker index population differs")
    raw = verify(plan["population"])
    require(len(raw) == 250000 and read(RESULT + "work/population.raw") == raw, "retained population differs")
    for name, bindings in plan["builds"].items():
        for key, filename in (("binary", "program"), ("manifest", "manifest.json")):
            require(read(RESULT + "work/" + name + "/" + filename) == verify(bindings[key]),
                    "retained build differs")
    expected_phases = [arm + "-" + phase for arm in ARMS for phase in PHASES]
    require([p["phase"] for p in stage["commands"]] == expected_phases, "phase order/population differs")
    marker_path = "run_logs/adaptive/" + JID + ".resources/phases.jsonl"
    markers = [json.loads(line) for line in read(marker_path).splitlines()]
    native_markers = [r for r in markers if r["phase"] != "diagnostic"]
    require([(r["phase"], r["event"]) for r in native_markers] ==
            [(phase, event) for phase in expected_phases for event in ("start", "end")], "phase markers differ")
    require([(r["phase"], r["event"]) for r in guard["phase_markers"]] ==
            [(r["phase"], r["event"]) for r in markers], "guard omitted phase markers")
    require(Path(guard["phase_marker_path"]) == ROOT / marker_path, "guard marker path differs")
    commands = {}
    for command in stage["commands"]:
        phase = command["phase"]
        arm, operation = phase.split("-")
        require(load(RESULT + phase + ".execution.json") == command, "execution receipt differs: " + phase)
        require(command["returncode"] == 0 and command["launch_error"] is None and
                command["accepted_returncodes"] == [0] and command["environment"] == {} and
                command["elapsed_cap_seconds"] == plan["phase_wall_seconds"] == 120 and
                command["elapsed_seconds"] <= 120, "native phase failed or exceeded stop: " + phase)
        require(all(finite_nonnegative(command[k]) for k in
                    ("elapsed_seconds", "user_cpu_seconds", "system_cpu_seconds")), "invalid phase cost")
        directory = RESULT + arm + "/"
        binary = "parent" if operation == "reference" else "observer"
        source = RESULT + "work/population.raw" if operation in ("reference", "encode") else (
            directory + ("encode" if operation == "decode" else "decode") + "/data")
        expected = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=2", "120",
                    str(ROOT / RESULT / "work" / binary / "program"),
                    "decode" if operation == "decode" else "encode", arm, "250000",
                    str(ROOT / source), str(ROOT / directory / operation)]
        if operation != "reference":
            expected.append("digest")
        require(command["command"] == expected, "native invocation differs: " + phase)
        commands[phase] = command
    require(Path("/usr/bin/timeout").resolve() in {Path(r["path"]) for r in plan["runtime_files"]},
            "phase timeout executable is unbound")

    historical_terminal = json.loads(verify(inputs[HISTORICAL_TERMINAL]))
    for name in ("job", "guard", "candidate_revision", "input_contract"):
        verify(historical_terminal["bindings"][name])
    old_job = load(historical_terminal["bindings"]["job"]["path"])
    old_guard = load(historical_terminal["bindings"]["guard"]["path"])
    require(old_job["state"] == "completed" and old_job["returncode"] == 0 and
            old_job["execution_resources"]["cleanup_complete"] and old_guard["status"] == "complete" and
            not any(old_guard["guards"].values()), "historical terminal is not closed")
    outputs, table, comparisons, historical_rows = {}, {}, {}, []
    revision = {"candidateId": CID, "candidateTreeSha256": job["candidate_tree_sha256"],
                "receipt": job["candidate_revision"]}
    index = {"schema": "gamma.enwiki9.terminal-result-index.v1", "job": ref(args.closed_job),
             "guard": ref(guard_path), "arms": [], "evidence": []}
    archives = {}
    for arm in ARMS:
        directory = RESULT + arm + "/"
        bundle = {}
        for phase in ("encode", "decode", "repeat"):
            path = ROOT / directory / phase
            require({p.name for p in path.iterdir()} == set(observer.FILES), "observer bundle population differs")
            bundle[phase] = observer.validate_bundle(path)
            summary = bundle[phase]["summary"]
            require(summary == load(RESULT + arm + "-" + phase + ".stdout") and
                    summary["arm"] == arm and summary["operation"] == ("decode" if phase == "decode" else "encode") and
                    summary["frontend"] == "raw_identity_v1" and summary["raw_bytes"] == summary["max_raw_bytes"] == 250000 and
                    summary["probability_records"] == 2000000 and summary["boundary_records"] == 7814 and
                    summary["exact_snapshots"] is False and summary["resource_qualified"] is False and
                    summary["complete_package_bytes"] is None and summary["objective_credit_bytes"] == 0,
                    "observer summary coordinates/scope differ")
        encoded = read(directory + "encode/data")
        archives[arm] = encoded
        require(read(directory + "decode/data") == raw and read(directory + "repeat/data") == encoded,
                "inverse or renewed raw encoding differs: " + arm)
        require(read(directory + "reference/data") == encoded and
                read(directory + "reference/state.bin") == read(directory + "encode/state.bin"),
                "fresh unobserved reference differs: " + arm)
        reference_summary = load(directory + "reference/summary.json")
        require(reference_summary == load(RESULT + arm + "-reference.stdout") and
                reference_summary["schema"] == "midas_open_codec_operation_v1" and
                reference_summary["arm"] == arm and reference_summary["operation"] == "encode" and
                reference_summary["frontend"] == "raw_identity_v1" and
                reference_summary["raw_bytes"] == reference_summary["max_raw_bytes"] == 250000 and
                reference_summary["archive_bytes"] == len(encoded) and
                reference_summary["state_bytes"] == len(read(directory + "reference/state.bin")) and
                reference_summary["objective_credit_bytes"] == 0 and reference_summary["resource_qualified"] is False,
                "fresh reference summary differs")
        require(load(RESULT + arm + "-reference-comparison.json") ==
                {"equal": True, "archive_and_complete_terminal_state_equal": True}, "reference comparison differs")
        for phase in ("decode", "repeat"):
            observed = observer.compare(ROOT / directory / "encode", ROOT / directory / phase)
            require(observed["equal"] is True and observed == load(RESULT + arm + "-" + phase + "-comparison.json"),
                    "probability/boundary comparison differs: " + arm + "-" + phase)
            require(read(directory + "encode/state.bin") == read(directory + phase + "/state.bin"),
                    "complete final state differs")
            comparisons[arm + "-" + phase] = observed
        for phase in ("encode", "decode", "repeat"):
            for filename in ("data", "state.bin"):
                old = HISTORICAL + arm + "/" + phase + "/" + filename
                new = directory + phase + "/" + filename
                require(old in inputs, "historical pair lacks a frozen binding: " + old)
                before, after = verify(inputs[old]), read(new)
                require(before == after, "historical bytes differ: " + new)
                historical_rows.append({"arm": arm, "phase": phase, "artifact": filename,
                                        "historical": ref(old, before, True), "observed": ref(new, after, True),
                                        "equal": True, "comparison": "direct complete byte equality"})
        costs = {phase: {k: commands[arm + "-" + phase][k] for k in
                        ("elapsed_seconds", "user_cpu_seconds", "system_cpu_seconds")} for phase in PHASES}
        outcome = stage["arms"][arm]
        require(outcome["archive_bytes"] == len(encoded) and outcome["archive_sha256"] == sha(encoded) and
                outcome["costs"] == costs and all(outcome[k] is True for k in
                ("exact_inverse", "exact_repeat", "unchanged_parent_archive_and_state", "all_boundaries_equal")),
                "stage arm outcome differs")
        require(all(row["summary"]["archive_bytes"] == len(encoded) for row in bundle.values()), "archive accounting differs")
        cpu = lambda phase: costs[phase]["user_cpu_seconds"] + costs[phase]["system_cpu_seconds"]
        table[arm] = {"archive_bytes": len(encoded), "archive_sha256": sha(encoded), "costs": costs,
                      "observer_encode_to_reference_cpu_ratio": cpu("encode") / cpu("reference"),
                      "probability_records_per_observed_phase": 2000000, "boundary_records_per_observed_phase": 7814,
                      "phase_summary_refs": {p: ref(directory + p + "/summary.json") for p in PHASES}}
        artifacts = {name: ref(directory + phase + "/data", sized=True) for name, phase in
                     (("archive", "encode"), ("restored", "decode"), ("repeat", "repeat"))}
        result = {"schema": "gamma.enwiki9.driver-result.v2", "program_id": CID,
            "program_name": "MIDAS observed SHA opening250KB " + arm, "arm": arm, "candidate_revision": revision,
            "objective": contract["objective"], "timestamp": job["finished_at"], "run_source": args.closed_job,
            "run_purpose": "diagnostic", "run_scope_label": "opening250k-missing-boundary-replay-" + arm,
            "run_tags": ["midas", "raw_identity_v1", "sha-boundary-observation", "historical-replay", arm],
            "data_path": plan["population"]["path"], "data_size": len(raw), "data_sha256": sha(raw),
            "data_md5": hashlib.md5(raw).hexdigest(), "compressed_size": len(encoded), "compressed_sha256": sha(encoded),
            "compressed_md5": hashlib.md5(encoded).hexdigest(), "bits_per_byte": 8 * len(encoded) / len(raw),
            "program_size": None, "hutter_score": None, "hutter_score_kind": "incomplete-dependency-closure",
            "complete_package_bytes": None, "full_corpus_score_bytes": None, "prize_claimable": False,
            "score_accounting_complete": False, "resource_evidence_complete": False, "qualification_status": "not-certified",
            "execution_mode": "discovery", "timing_authority": "diagnostic", "roundtrip_ok": True,
            "determinism": {"single_host_byte_equal": True, "first_divergence_byte": None,
                "first_run_sha256": sha(encoded), "second_run_sha256": sha(encoded),
                "first_run_md5": hashlib.md5(encoded).hexdigest(), "second_run_md5": hashlib.md5(encoded).hexdigest()},
            "raw_encoder_repeat_proved": True, "repeat_scope": "cold native encoder repeated from independent decoded raw",
            "compress_time_s": costs["encode"]["elapsed_seconds"], "decompress_time_s": costs["decode"]["elapsed_seconds"],
            "encoding_cpu_seconds": cpu("encode"), "decoding_cpu_seconds": cpu("decode"),
            "repeat_time_s": costs["repeat"]["elapsed_seconds"], "run_time_s": sum(c["elapsed_seconds"] for c in costs.values()),
            "run_time_scope": "Four separate bounded processes including unobserved reference, observation and publication.",
            "memory_kib": {"peak": max(v["summary"]["process_peak_rss_kib"] for v in bundle.values())},
            "host": {"machine": platform.machine(), "node": platform.node(), "python": platform.python_version(), "system": platform.system()},
            "artifacts": artifacts, "closed_job": ref(args.closed_job), "closed_guard": ref(guard_path),
            "missing_diagnostics": job["execution_resources"]["missing_diagnostics"],
            "run_context": "Previously examined opening250KB missing-boundary-evidence replay; no fresh confirmation, package or full-corpus credit.",
            "synchronization": {"all_pre_truth_q16_equal": True, "all_32_byte_and_final_witnesses_equal": True,
                "complete_terminal_bytes_equal": True, "exact_intermediate_snapshots_retained": False},
            "accounting_scope": "Complete finite archive file including its existing native framing; auxiliary traces are audit evidence."}
        row_path = directory + "result.json"
        outputs[row_path] = result
        index["arms"].append({"arm": arm, "result": ref(row_path, canonical(result).encode()), "artifacts": artifacts})

    require(set(stage["arms"]) == set(ARMS) and archives["P"] == archives["K"], "P/K or arm population differs")
    pk = observer.compare(ROOT / RESULT / "P/encode", ROOT / RESULT / "K/encode", projection="parent")
    require(pk["equal"] is True, "P/K authoritative parent/coder/probability projection differs")
    rows = [observer.boundary_rows(ROOT / RESULT / arm / "encode/boundaries.jsonl", len(raw)) for arm in "PK"]
    for a, b in zip(*rows, strict=True):
        projected = [next((p["bytes"], p["sha256"]) for p in row["parts"]
                          if p["name"] == "reference_model_projection") for row in (a, b)]
        require(projected[0] == projected[1], "P/K reference-model witness differs")
    pk.update(reference_model_projection_equal=True, archive_equal=True)
    require(pk == load(RESULT + "PK-comparison.json"), "retained P/K comparison differs")
    comparisons["PK"] = pk
    require(len(historical_rows) == 24, "historical comparison population incomplete")
    historical_path = RESULT + "historical-comparison.json"
    outputs[historical_path] = {"schema": "gamma.enwiki9.midas-historical-comparison.v1", "candidate_id": CID,
        "job": ref(args.closed_job), "guard": ref(guard_path), "experiment": ref(CONTRACT),
        "historical_terminal": ref(HISTORICAL_TERMINAL), "population": plan["population"],
        "comparisons": historical_rows, "comparison_count": 24, "data_file_comparisons": 12,
        "archive_comparisons": 8, "decoded_raw_comparisons": 4, "complete_state_comparisons": 12,
        "all_equal": True, "scope": "Missing-boundary-evidence replay, not fresh confirmation or new archive savings.",
        "objective_credit_bytes": 0, "complete_package_bytes": None, "full_corpus_score_bytes": None}
    measurements = {k: True for k in validity}
    measurements.update(continuous_guard_pass=True, native_phases=16, raw_bytes=len(raw),
        maximum_observed_phase_seconds=max(c["elapsed_seconds"] for c in stage["commands"] if not c["phase"].endswith("reference")),
        peak_tree_memory_bytes=guard["peaks"]["max_sampled_tree_rss_kib"] * 1024,
        peak_scratch_bytes=guard["peaks"]["max_sampled_scratch_logical_bytes"],
        F_vs_P_archive_saved_bytes=len(archives["P"]) - len(archives["F"]),
        F_vs_S_archive_saved_bytes=len(archives["S"]) - len(archives["F"]),
        historical_archives_equal=True, historical_terminal_states_equal=True, historical_comparison_complete=True,
        complete_package_qualified=False)
    for arm in ARMS:
        for phase in ("reference", "encode"):
            command = commands[arm + "-" + phase]
            measurements[arm + "-" + phase + "-cpu-seconds"] = command["user_cpu_seconds"] + command["system_cpu_seconds"]
    require(set(measurements) == {r["id"] for r in contract["measurements"]}, "measurement population differs")
    for key in ("F_vs_P_archive_saved_bytes", "F_vs_S_archive_saved_bytes"):
        require(measurements[key] == stage[key], "stage archive difference differs")
    def evaluations(field):
        return [{**p, "observed": measurements[p["measurement"]],
                 "passed": contracts._predicate_pass(measurements[p["measurement"]], p["operator"], p["threshold"])}
                for p in contract[field]]
    promotion, kill = evaluations("promotionPredicates"), evaluations("killPredicates")
    promotion_pass, kill_pass = all(p["passed"] for p in promotion), all(p["passed"] for p in kill)
    require(not (promotion_pass and kill_pass), "contradictory contract predicates")
    def output_ref(path):
        return ref(path, canonical(outputs[path]).encode()) if path in outputs else ref(path)
    decision_path = RESULT + "decision.json"
    artifacts = [{"id": "artifact-" + str(i), **output_ref(path)} for i, path in enumerate(sorted(declared)) if path != decision_path]
    outputs[decision_path] = {"schema": "gamma.enwiki9.adaptive-experiment-result.v1", "objective": contract["objective"],
        "experiment": ref(CONTRACT), "candidateId": CID, "candidateRevision": revision, "evidenceClass": contract["evidenceClass"],
        "objectiveCreditBytes": 0, "measurements": measurements, "promotionPredicates": promotion, "killPredicates": kill,
        "promotionPass": promotion_pass, "killPass": kill_pass,
        "decision": "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry",
        "artifacts": artifacts, "generatedUtc": job["finished_at"]}
    index["evidence"] = [output_ref(p) for p in (stage_path, artifact_path, historical_path, decision_path, SELF)]
    outputs[DEST + "/index.json"] = index
    native_sources = {}
    for manifest in manifests.values():
        for row in manifest["identity"]["dependencies"]:
            path = Path(row["path"])
            if path.is_relative_to(ROOT):
                name = str(path.relative_to(ROOT))
                require(name in inputs, "unbound native source dependency")
                native_sources[name] = ref(name, sized=True)
    package = {"parent_binary": plan["builds"]["parent"]["binary"], "sha_observer_binary": plan["builds"]["observer"]["binary"],
        "local_native_source_files": [native_sources[p] for p in sorted(native_sources)],
        "local_native_source_bytes": sum(r["bytes"] for r in native_sources.values()), "runtime_files": plan["runtime_files"],
        "complete_package_bytes": None, "netBytesSaved": None,
        "accounting": "Separate build, source and runtime inventories; no selected submission form or summed complete package. Observed archives include all native framing. Audit traces and state witnesses are auxiliary evidence, not decoder side inputs."}
    require(stage["package_components"] == {name: manifest["binary"]["bytes"] for name, manifest in manifests.items()},
            "stage binary inventory differs")
    outputs[DEST + ".json"] = {"schema": "gamma.enwiki9.midas-observed-corpus-terminal-audit.v1", "candidate_id": CID,
        "job_id": JID, "generated_at": job["finished_at"], "auditor": "Independent read-only terminal normalizer; no codec rerun",
        "bindings": {"contract": ref(CONTRACT), "job": ref(args.closed_job), "guard": ref(guard_path),
            "phase_markers": ref(marker_path), "stage": ref(stage_path), "artifact_index": ref(artifact_path),
            "normalizer": ref(SELF), "terminal_index": output_ref(DEST + "/index.json"),
            "proposal": job["proposal"], "candidate_revision": job["candidate_revision"]},
        "candidate_revision_blobs": revision_blobs,
        "canonical_decision": output_ref(decision_path), "historical_comparison": output_ref(historical_path),
        "objective": contract["objective"], "population_kind": "corpus", "scope_bytes": len(raw), "scope_symbols": len(raw) * 8,
        "table": table, "measurements": measurements, "comparisons": comparisons,
        "verified": {"closed_native_phases": 16, "exact_raw_inverses": 4, "renewed_raw_repeats": 4,
            "fresh_unobserved_reference_archive_and_state_pairs": 4, "complete_probability_and_boundary_comparisons": 8,
            "pk_authoritative_projection_comparisons": 1, "historical_pairs": 24, "frozen_inputs": len(inputs),
            "worker_closed_files": 152, "worker_indexed_files": 150, "required_final_outputs": 158},
        "resources": {"elapsed_seconds": guard["elapsed_s"], "guard_pass": True, "cleanup_complete": True,
            "peaks": guard["peaks"], "guards": guard["guards"], "sample_count": guard["sample_count"],
            "budget": plan["resources"], "native_limits": {"address_space_bytes": 536870912, "cpu_seconds": 120,
                "wall_seconds": 120, "file_bytes": 33554432}, "resource_qualified": False, "timing_authority": "shared-host diagnostic"},
        "package_inventory": package, "archive_saved_bytes": measurements["F_vs_P_archive_saved_bytes"],
        "controlBytesSaved": measurements["F_vs_S_archive_saved_bytes"], "netBytesSaved": None,
        "full_corpus_score_bytes": None, "complete_package_bytes": None, "objective_credit_bytes": 0,
        "hypothesis_verdict": "supported" if promotion_pass else "not-supported", "larger_gate_authorized": False,
        "conclusion": "The frozen missing-boundary replay passed its bounded predicates." if promotion_pass else "The frozen archive-benefit predicates did not all pass.",
        "limitations": ["Previously examined opening250KB; not a fresh holdout or new compression gain.",
            "Intermediate evidence is serialized SHA256 witnesses at initial/every32-byte/final boundaries; full intermediate snapshots are disabled.",
            "Every pre-truth Q16 and all retained terminal bytes were checked without rerunning the codec.",
            "No full-corpus extrapolation, combined component sum, complete package, calibrated resource or license qualification.",
            "Schema successor eligibility requires a validated reflection and a separately selected frozen gate; it launches nothing."],
        "antecedent_metadata": [ref(p) for p in sorted(inputs) if p.startswith("operations/adaptive/reflections/") or
                                (p.startswith("operations/provenance/") and "terminal_20260906.json" in p)],
        "final_output_inventory": [output_ref(p) for p in sorted(declared)]}
    # Final authentication and immutable-worker closure precede any positive
    # stdout. This does not modify the original worker index after ROOT additions.
    for row in (contract["inputs"] + plan["runtime_files"] + indexed["files"] + terminal_snapshot +
                revision_blobs + [job["candidate_revision"], job["proposal"]]):
        verify(row)
    require(ref(CONTRACT)["sha256"].removeprefix("sha256:") == CONTRACT_SHA and
            ref(args.closed_job)["sha256"].removeprefix("sha256:") == args.job_sha256.removeprefix("sha256:") and
            ref(guard_path)["sha256"].removeprefix("sha256:") == args.guard_sha256.removeprefix("sha256:") and
            files_below() == actual, "terminal authority changed during audit")
    for path in actual & GENERATED:
        require(read(path) == canonical(outputs[path]).encode(), "existing ROOT publication differs: " + path)
    require(set(outputs) == GENERATED | {DEST + "/index.json", DEST + ".json"}, "publication output population differs")
    contracts._validate_schema(outputs[decision_path], contracts.SCHEMA_PATHS[outputs[decision_path]["schema"]])
    print(json.dumps({path: canonical(value) for path, value in outputs.items()}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
