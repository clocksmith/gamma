#!/usr/bin/env python3
"""Frozen P/K/D raw-discovery comparisons through the existing bounded driver.

All repeats start from independently decoded raw bytes. A successful inverse or
plain fallback is not a strict archive improvement or confirmation permission.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = "tools/dualstream_literal_first_gate_v1.py"
CODEC = "tools/dualstream_literal_first_v1.py"
PLAIN = "tools/dualstream_grammar_argtokens_v2.py"
DECODER = "tools/dualstream_grammar_decode_dispatch_v1.py"
SHARED_DRIVER = "tools/dualstream_grammar_gate_v1.py"
TESTS = "tests/test_dualstream_literal_first_gate_v1.py"
PACKAGE = [CODEC, PLAIN, "tools/dualstream_grammar_v1.py", DECODER]
spec = importlib.util.spec_from_file_location(__name__ + "_driver", ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF, driver.CODEC = SELF, CODEC
require = driver.require
SCHEMA = "gamma.enwiki9.literal-first-gate-plan.v1"
ARMS = [dict(id="P", mode="plain"), dict(id="K", mode="K"), dict(id="D", mode="D")]
LEGACY_COSTS = ("literal_definition_bytes", "structure_bytes", "content_bytes",
                "argument_reference_bytes", "exception_bytes", "framing_bytes")
COSTS = {"deflate_payload", "framing"}
REPRESENTATION_COSTS = {"definitions", "program_calls", "arguments", "literal_runs", "representation_framing"}
ENCODER_ONLY = ("mode", "search_spec", "repeat_scope", "raw_encoder_repeat_proved")


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def is_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def valid_reference(row):
    path = Path(row["path"])
    require(set(row) == {"path", "bytes", "sha256"} and not path.is_absolute()
            and ".." not in path.parts and str(path) == row["path"]
            and integer(row["bytes"], 1, driver.codec.MAX_ARCHIVE) and is_hash(row["sha256"]),
            "invalid frozen artifact reference")


def validate_plan(plan, candidate):
    required = {"schema", "candidate_id", "stage", "population", "arms", "frame_size", "resources",
                "phase_wall_seconds", "phase_cpu_seconds", "phase_address_bytes", "runtime_files",
                "search_spec", "kernel_basis", "plain_archive"}
    require(set(plan) == required, "literal-first plan fields differ")
    require(plan["schema"] == SCHEMA and plan["candidate_id"] == candidate and plan["stage"] == "development"
            and plan["arms"] == ARMS, "frozen P/K/D comparison differs")
    valid_reference(plan["population"])
    valid_reference(plan["plain_archive"])
    require(plan["population"]["bytes"] == 250000 and plan["plain_archive"]["bytes"] == 89041
            and plan["frame_size"] == 65536, "opening population, retained baseline or frame partition differs")
    caps = plan["resources"]
    require(set(caps) == {"cpus", "memory_bytes", "scratch_bytes", "swap_bytes", "wall_seconds"}
            and caps["cpus"] == [2] and caps["memory_bytes"] == 1073741824
            and caps["scratch_bytes"] == 67108864 and caps["swap_bytes"] == 0
            and integer(caps["wall_seconds"], 1, 1800), "resource policy differs")
    require(integer(plan["phase_cpu_seconds"], 1, min(120, caps["wall_seconds"]))
            and integer(plan["phase_wall_seconds"], plan["phase_cpu_seconds"], min(180, caps["wall_seconds"]))
            and plan["phase_address_bytes"] == 536870912, "phase bounds differ")
    require(isinstance(plan["runtime_files"], list) and plan["runtime_files"] and plan["kernel_basis"],
            "runtime or measured search basis missing")
    codec = importlib.import_module("tools.dualstream_literal_first_v1")
    require(plan["search_spec"] == codec.SEARCH_SPEC, "frozen search specification differs")


driver.validate_plan = validate_plan


def authenticate(candidate, validate_only=False):
    require(isinstance(candidate, str) and re.fullmatch(r"[a-z0-9_]+", candidate), "invalid candidate")
    prospective = driver.read_json(ROOT / "operations/adaptive/experiments" / (candidate + ".json"))
    require({SELF, SHARED_DRIVER, TESTS, *PACKAGE}.issubset({row["path"] for row in prospective["inputs"]}),
            "literal-first source closure unbound")
    contract, reference, plan = driver.authenticate(candidate, validate_only)
    inputs = {row["path"]: row for row in contract["inputs"]}
    require({SELF, SHARED_DRIVER, TESTS, *PACKAGE}.issubset(inputs), "literal-first source closure unbound")
    row = plan["plain_archive"]
    bound = inputs.get(row["path"])
    path = ROOT / row["path"]
    require(bound is not None and bound["sha256"].removeprefix("sha256:") == row["sha256"]
            and path.stat().st_size == row["bytes"], "retained plain archive unbound")
    with path.open("rb") as stream:
        require(stream.read(8) == b"D2GRAM02", "retained plain frontend differs")
    executable = Path(sys.executable).resolve()
    require(any(Path(row["path"]).resolve() == executable for row in plan["runtime_files"]),
            "current interpreter is not frozen")
    return contract, reference, plan


def checked_wrapper(wrapper):
    require(wrapper["complete_package_bytes"] is None and wrapper["full_corpus_score_bytes"] is None,
            "unsupported package or score credit")
    for field in ("cpu_seconds", "elapsed_seconds"):
        require(type(wrapper[field]) in (int, float) and math.isfinite(wrapper[field]) and wrapper[field] >= 0,
                "invalid child timing")
    require(integer(wrapper["peak_process_rss_kib"], 1, 2**40), "invalid child RSS")
    return wrapper["result"]


def common_report(report):
    """Only discovery diagnostics and the encoder request are not transmitted."""
    result = copy.deepcopy(report)
    for key in ENCODER_ONLY:
        result.pop(key, None)
    for frame in result["frames"]:
        frame.pop("search", None)
    return result


def checked_report(report, arm, archive, plan, raw):
    is_plain = arm["id"] == "P"
    if is_plain:
        legacy = {key: report[key] for key in LEGACY_COSTS}
        require(all(type(value) is int and value >= 0 for value in legacy.values()), "invalid plain costs")
        costs = dict(deflate_payload=sum(legacy.values()) - legacy["framing_bytes"], framing=legacy["framing_bytes"])
        require(report["requested_mode"] == "plain" and report["backend"] == "zlib9", "plain encoder differs")
    else:
        costs = report["costs"]
        require(report["raw_sha256"] == hashlib.sha256(raw).hexdigest()
                and report["archive_sha256"] == driver.sha(archive)
                and report["search_spec"] == plan["search_spec"] and report["mode"] == arm["id"]
                and report["backend"] == "zlib9" and report["raw_encoder_repeat_proved"] is False
                and report["repeat_scope"] == "raw-discovery-and-encoding"
                and report["complete_package_bytes"] is None and report["full_corpus_score_bytes"] is None,
                "raw/archive identity, search or report scope differs")
    require(set(costs) == COSTS and all(type(value) is int and value >= 0 for value in costs.values())
            and sum(costs.values()) == archive.stat().st_size == report["complete_archive_bytes"],
            "complete archive accounting differs")
    frame_size = plan["frame_size"]
    require(report["raw_bytes"] == len(raw) == plan["population"]["bytes"]
            and hashlib.sha256(raw).hexdigest() == plan["population"]["sha256"]
            and report["frame_size"] == frame_size
            and len(report["frames"]) == (len(raw) + frame_size - 1) // frame_size,
            "raw population or frame count differs")
    frames = []
    for index, frame in enumerate(report["frames"]):
        part = raw[index * frame_size:(index + 1) * frame_size]
        require(frame["raw_bytes"] == len(part), "frame raw partition differs")
        if is_plain:
            require(frame["mode"] == "plain" and frame["templates"] == 0
                    and frame["supplied_arguments"] == 0 and frame["repeated_argument_references"] == 0,
                    "plain frame is not plain")
            frame_cost = {key: frame[key] for key in LEGACY_COSTS}
            require(all(type(value) is int and value >= 0 for value in frame_cost.values())
                    and sum(frame_cost.values()) == frame["complete_archive_bytes"], "plain frame accounting differs")
            frames.append(dict(raw_bytes=len(part), raw_sha256=hashlib.sha256(part).hexdigest(), mode="plain",
                complete_frame_bytes=frame["complete_archive_bytes"], selected_rules=0, calls=0, repeated_argument_references=0,
                costs=dict(deflate_payload=sum(frame_cost.values()) - frame_cost["framing_bytes"], framing=frame_cost["framing_bytes"])))
        else:
            require(frame["raw_sha256"] == frame["output_sha256"] == hashlib.sha256(part).hexdigest()
                    and all(is_hash(frame[key]) for key in ("representation_sha256", "program_sha256", "boundary_sha256"))
                    and integer(frame["execution_steps"], 0, 16 * frame_size)
                    and frame["mode"] in ("plain", "template"),
                    "frame reconstruction or representation identity differs")
            require(all(integer(frame[key], 0, 16 * frame_size) for key in
                        ("selected_rules", "calls", "repeated_argument_references")), "invalid selected program counts")
            require((frame["mode"] == "template") == bool(frame["selected_rules"]),
                    "frame mode and selected program differ")
            require(set(frame["costs"]) == COSTS
                    and all(type(value) is int and value >= 0 for value in frame["costs"].values())
                    and sum(frame["costs"].values()) == frame["complete_frame_bytes"], "frame archive accounting differs")
            require(set(frame["representation_costs"]) == REPRESENTATION_COSTS
                    and all(type(value) is int and value >= 0 for value in frame["representation_costs"].values()),
                    "invalid pre-Deflate representation costs")
            search = frame["search"]
            require(isinstance(search, dict) and search["discovery_from_raw"] is True
                    and search["admission_enabled"] is (arm["id"] == "D")
                    and integer(search["spans"], 0, plan["search_spec"]["max_spans"])
                    and integer(search["proposals"], 0, plan["search_spec"]["max_proposals"])
                    and is_hash(search["proposal_sha256"])
                    and search["admitted"] == frame["selected_rules"], "raw discovery evidence differs")
            require(isinstance(search["evaluations"], list) and len(search["evaluations"])
                    <= plan["search_spec"]["max_proposals"] * plan["search_spec"]["max_selected_rules"],
                    "search evaluation bound differs")
            for evaluation in search["evaluations"]:
                require(integer(evaluation["round"], 0, plan["search_spec"]["max_selected_rules"] - 1)
                        and integer(evaluation["proposal"], 0, search["proposals"] - 1)
                        and integer(evaluation["uses"], 2, plan["search_spec"]["max_spans"])
                        and integer(evaluation["before"], 1, driver.codec.MAX_ARCHIVE)
                        and integer(evaluation["candidate"], 1, driver.codec.MAX_ARCHIVE)
                        and type(evaluation["delta"]) is int
                        and evaluation["delta"] == evaluation["before"] - evaluation["candidate"]
                        and type(evaluation["accepted"]) is bool and is_hash(evaluation["candidate_sha256"]),
                        "invalid complete-cost search evaluation")
            if arm["id"] == "K":
                require(frame["selected_rules"] == frame["calls"] == frame["repeated_argument_references"] == 0,
                        "disabled control admitted a template")
            frames.append(frame)
    for category in COSTS:
        require(costs[category] == sum(frame["costs"][category] for frame in frames)
                + (driver.codec.HEADER.size if category == "framing" else 0), "global framing or frame costs differ")
    return costs, frames


def classify_failure(error, last, plan):
    if last and last["timeout"]:
        error = subprocess.TimeoutExpired(last["argv"], plan["phase_wall_seconds"])
    elif last and last["error"]:
        error = OSError(last["error"])
    return driver.classification(error, last["returncode"] if last else None)


def comparison_table(rows, plan):
    by_id = {row["arm"]["id"]: row for row in rows}
    require(len(rows) == 3 and set(by_id) == {"P", "K", "D"}, "incomplete three-arm table")
    sizes = {key: row["archive_bytes"] for key, row in by_id.items()}
    require({row["backend"] for row in rows} == {"zlib9"} and len({row["zlib_version"] for row in rows}) == 1,
            "paired Deflate backend differs")
    require(sizes["P"] == sizes["K"] and sizes["D"] <= sizes["P"], "plain-control or selective whole-cost invariant differs")
    for index, baseline in enumerate(by_id["P"]["frames"]):
        k, d = by_id["K"]["frames"][index], by_id["D"]["frames"][index]
        require(k["complete_frame_bytes"] == baseline["complete_frame_bytes"], "disabled control frame cost differs")
        require(all(k["search"][key] == d["search"][key] for key in ("spans", "proposals", "proposal_sha256")),
                "K/D discovery proposal pool differs")
        first_round = lambda f: [{key: value for key, value in row.items() if key != "accepted"}
                                 for row in f["search"]["evaluations"] if row["round"] == 0]
        require(first_round(k) == first_round(d), "K/D first complete-cost measurements differ")
        for frame in (k, d):
            accepted = [row for row in frame["search"]["evaluations"] if row["accepted"]]
            require(len(accepted) == frame["selected_rules"], "selected admission count differs")
            before = baseline["complete_frame_bytes"]
            for round_index, row in enumerate(accepted):
                require(row["round"] == round_index and row["before"] == before
                        and row["delta"] >= plan["search_spec"]["min_frame_benefit"],
                        "non-strict or discontinuous frame admission")
                before = row["candidate"]
            require(before == frame["complete_frame_bytes"], "final admitted frame cost differs")
        if d["selected_rules"]:
            require(d["calls"] > 0 and d["complete_frame_bytes"] < baseline["complete_frame_bytes"],
                    "admitted frame is not strictly smaller")
        else:
            require(d["calls"] == d["repeated_argument_references"] == 0
                    and d["complete_frame_bytes"] == baseline["complete_frame_bytes"], "fallback frame differs")
    return dict(schema="gamma.enwiki9.literal-first-costs.v1", raw_bytes=plan["population"]["bytes"], archive_bytes=sizes,
                p_minus_k_bytes=sizes["P"] - sizes["K"], p_minus_d_bytes=sizes["P"] - sizes["D"],
                k_minus_d_bytes=sizes["K"] - sizes["D"], strict_d_improvement=sizes["D"] < sizes["P"],
                confirmation_eligible=sizes["D"] < sizes["P"], confirmation_requires_separately_frozen_gate=True,
                fallback_equality_authorizes_confirmation=False, raw_encoder_repeat_proved=True,
                cells=[dict(arm=row["arm"], archive_bytes=row["archive_bytes"], accounting=row["accounting"]) for row in rows],
                package_source=[driver.artifact(ROOT / path) for path in PACKAGE],
                known_source_bytes=sum((ROOT / path).stat().st_size for path in PACKAGE), complete_package_bytes=None,
                full_corpus_score_bytes=None, objective_credit_bytes=0, resource_qualified=False,
                package_gaps=["runtime distribution and license closure", "accepted source and option accounting"],
                evidence_scope="opening development raw-discovery comparison; no full-corpus score")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    _, reference, plan = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status="preflight_pass", executed=False, native_phases=9)))
        return 0
    directory = ROOT / "results" / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), "nonempty output")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    population = ROOT / plan["population"]["path"]
    raw = population.read_bytes()
    stage = dict(schema="gamma.enwiki9.literal-first-stage.v1", candidate_id=args.candidate, experiment=reference,
                 status="running", arms=[], commands=[], objective_credit_bytes=0, complete_package_bytes=None,
                 full_corpus_score_bytes=None, resource_qualified=False, selection_stage=plan["stage"])
    last, table = None, None
    try:
        for arm in ARMS:
            paths = {key: directory / (arm["id"] + suffix) for key, suffix in
                     (("archive", ".d2g"), ("restored", ".raw"), ("repeat", ".repeat.d2g"))}
            for phase, operation, inp, out in (("encode", "encode", population, paths["archive"]),
                    ("decode", "decode", paths["archive"], paths["restored"]),
                    ("repeat", "encode", paths["restored"], paths["repeat"])):
                tool = (PLAIN if operation == "encode" else DECODER) if arm["id"] == "P" else CODEC
                command = [sys.executable, str(ROOT / tool), operation, str(inp), str(out)]
                if operation == "encode":
                    command += ["--mode", arm["mode"], "--frame-size", str(plan["frame_size"])]
                last = driver.run_phase(directory, arm["id"] + "-" + phase, command, plan, marker)
                stage["commands"].append(last)
                require(last["returncode"] == 0 and not last["timeout"] and last["error"] is None,
                        "phase failed: " + last["phase"])
            require(paths["restored"].read_bytes() == raw, "independent inverse differs")
            require(paths["archive"].read_bytes() == paths["repeat"].read_bytes(), "raw-discovery repeat differs")
            wrappers = {phase: driver.read_json(directory / (arm["id"] + "-" + phase + ".stdout"))
                        for phase in ("encode", "decode", "repeat")}
            reports = {phase: checked_wrapper(wrapper) for phase, wrapper in wrappers.items()}
            report = reports["encode"]
            require(report == reports["repeat"], "raw-discovery repeat report differs")
            if arm["id"] == "P":
                require(driver.sha(paths["archive"]) == plan["plain_archive"]["sha256"]
                        and paths["archive"].stat().st_size == plan["plain_archive"]["bytes"], "retained P diagonal differs")
                require(reports["decode"]["raw_bytes"] == len(raw) and reports["decode"]["frontend"] == "D2GRAM02",
                        "independent plain decoder differs")
            else:
                require(common_report(report) == common_report(reports["decode"]), "independent decoder projection differs")
                if arm["id"] == "K":
                    require(paths["archive"].read_bytes() == (directory / "P.d2g").read_bytes(), "P/K archive identity differs")
            costs, frames = checked_report(report, arm, paths["archive"], plan, raw)
            if arm["id"] == "D" and not any(frame["selected_rules"] for frame in frames):
                require(paths["archive"].read_bytes() == (directory / "P.d2g").read_bytes(),
                        "all-plain D fallback archive differs")
            row = dict(arm=arm, archive_bytes=report["complete_archive_bytes"], accounting=costs, frames=frames,
                       backend=report["backend"], zlib_version=report["zlib_version"],
                       exact_inverse=True, deterministic_repeat=True, raw_encoder_repeat_proved=True,
                       repeat_scope="raw-discovery-and-encoding", selected_rules=sum(frame["selected_rules"] for frame in frames),
                       calls=sum(frame["calls"] for frame in frames),
                       repeated_argument_references=sum(frame["repeated_argument_references"] for frame in frames),
                       phase_resources={phase: {key: wrappers[phase][key] for key in
                           ("cpu_seconds", "elapsed_seconds", "peak_process_rss_kib")} for phase in wrappers},
                       artifacts={key: driver.artifact(path) for key, path in paths.items()})
            driver.write_json(directory / (arm["id"] + ".result.json"), row)
            stage["arms"].append(row)
        table = comparison_table(stage["arms"], plan)
        stage.update(status="passed", correctness_pass=True, accounting_pass=True, p_k_archive_identity_pass=True,
                     raw_encoder_repeat_proved=True, native_phases=len(stage["commands"]))
    except Exception as error:
        stage.update(status="failed", correctness_pass=False, accounting_pass=False, native_phases=len(stage["commands"]),
                     failure_class=classify_failure(error, last, plan), error=type(error).__name__ + ": " + str(error))
    try:
        authenticate(args.candidate)
        stage["frozen_inputs_reverified"] = True
        if stage["correctness_pass"]:
            driver.write_json(directory / "costs-table.json", table)
            stage["costs"] = table
    except Exception as error:
        stage.update(status="failed", correctness_pass=False, accounting_pass=False, frozen_inputs_reverified=False,
                     failure_class="infrastructure-failure", error="Final authentication or table publication: " + str(error))
    files = [driver.artifact(path) for path in sorted(directory.iterdir()) if path.is_file()]
    driver.write_json(directory / "artifacts.json", dict(complete=stage["correctness_pass"], files=files))
    driver.write_json(directory / "stage-decision.json", stage)
    print(json.dumps(dict(status=stage["status"], arms_closed=len(stage["arms"]), native_phases=stage["native_phases"])))
    return 0 if stage["correctness_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
