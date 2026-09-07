#!/usr/bin/env python3
"""Five frozen raw/grammar event comparisons through the existing queue driver.

Only R repeats a raw encoding. P/B/G/X retain their selected input archives;
their repeats do not establish repeated grammar discovery. Archive arithmetic is
complete, while source/runtime inventory is not a complete prize package.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = "tools/dualstream_event_gate_v1.py"
SHARED_DRIVER = "tools/dualstream_grammar_gate_v1.py"
CODEC = "tools/dualstream_event_codec_v1.py"
CODER = "tools/dualstream_event_coder_v1.py"
RESERIALIZER = "tools/dualstream_grammar_reserialize_v1.py"
DECODER = "tools/dualstream_grammar_decode_dispatch_v1.py"
TESTS = "tests/test_dualstream_event_gate_v1.py"
PACKAGE = [CODEC, CODER, "tools/dualstream_grammar_v1.py",
           "tools/dualstream_grammar_argtokens_v2.py", RESERIALIZER, DECODER]
spec = importlib.util.spec_from_file_location(__name__ + "_driver", ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF, driver.CODEC = SELF, CODEC
require = driver.require
SCHEMA = "gamma.enwiki9.event-gate-plan.v1"
ARMS = [dict(id="P", selection="plain", backend="deflate", storage="new"),
        dict(id="B", selection="old", backend="deflate", storage="old"),
        dict(id="R", selection="raw", backend="event", context_enabled=False),
        dict(id="G", selection="old", backend="event", context_enabled=False),
        dict(id="X", selection="old", backend="event", context_enabled=True)]
LEGACY_COSTS = ("literal_definition_bytes", "structure_bytes", "content_bytes",
                "argument_reference_bytes", "exception_bytes", "framing_bytes")
EVENT_COSTS = ("definitions", "program", "content", "arguments", "framing")
FRAME_IDENTITY = ("raw_bytes", "raw_sha256", "model_sha256", "repeated_argument_references")
HEADER_BYTES = struct.calcsize("<8sBIIQ")
FRAME_BYTES = struct.calcsize("<IBI32s32s")


def is_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def valid_reference(row):
    path = Path(row["path"])
    require(set(row) == {"path", "bytes", "sha256"} and not path.is_absolute()
            and ".." not in path.parts and str(path) == row["path"]
            and integer(row["bytes"], 1, driver.codec.MAX_ARCHIVE) and is_hash(row["sha256"]),
            "invalid frozen artifact reference")


def validate_plan(plan, candidate):
    required = {"schema", "candidate_id", "stage", "population", "arms", "frame_size",
                "resources", "phase_wall_seconds", "phase_cpu_seconds", "phase_address_bytes",
                "runtime_files", "selected_archives", "model_spec", "kernel_basis", "expected_frames"}
    require(set(plan) == required, "event plan fields differ")
    require(plan["schema"] == SCHEMA and plan["candidate_id"] == candidate
            and plan["stage"] == "development" and plan["arms"] == ARMS, "frozen event comparison differs")
    valid_reference(plan["population"])
    require(plan["population"]["bytes"] == 250000 and plan["frame_size"] == 65536,
            "opening population or frame partition differs")
    require(set(plan["selected_archives"]) == {"plain", "old"}, "selected frontends differ")
    for row in plan["selected_archives"].values():
        valid_reference(row)
    caps = plan["resources"]
    require(set(caps) == {"cpus", "memory_bytes", "scratch_bytes", "swap_bytes", "wall_seconds"}
            and caps["cpus"] == [2] and caps["memory_bytes"] == 1073741824
            and caps["scratch_bytes"] == 67108864 and caps["swap_bytes"] == 0
            and integer(caps["wall_seconds"], 1, 1800), "resource policy differs")
    require(integer(plan["phase_cpu_seconds"], 1, caps["wall_seconds"])
            and integer(plan["phase_wall_seconds"], plan["phase_cpu_seconds"], caps["wall_seconds"])
            and plan["phase_address_bytes"] == 536870912, "phase bounds differ")
    require(isinstance(plan["runtime_files"], list) and plan["runtime_files"]
            and plan["kernel_basis"], "runtime or measured kernel basis missing")
    kernel = importlib.import_module("tools.dualstream_event_coder_v1")
    require(plan["model_spec"] == kernel.MODEL_SPEC, "frozen categorical model differs")
    frames = plan["expected_frames"]
    require(isinstance(frames, list) and len(frames) == 4, "four selected frame identities required")
    for index, frame in enumerate(frames):
        require(set(frame) == set(FRAME_IDENTITY)
                and frame["raw_bytes"] == min(65536, 250000 - 65536 * index)
                and is_hash(frame["raw_sha256"]) and is_hash(frame["model_sha256"])
                and integer(frame["repeated_argument_references"], 0, 16 * 65536),
                "invalid selected frame identity")
    require([f["repeated_argument_references"] for f in frames] == [0, 0, 12, 0],
            "frozen repeated bindings differ")


driver.validate_plan = validate_plan


def authenticate(candidate, validate_only=False):
    require(isinstance(candidate, str) and re.fullmatch(r"[a-z0-9_]+", candidate), "invalid candidate")
    prospective = driver.read_json(ROOT / "operations/adaptive/experiments" / (candidate + ".json"))
    require({SELF, SHARED_DRIVER, TESTS, *PACKAGE}.issubset({row["path"] for row in prospective["inputs"]}),
            "event source closure unbound")
    contract, reference, plan = driver.authenticate(candidate, validate_only)
    inputs = {row["path"]: row for row in contract["inputs"]}
    require({SELF, SHARED_DRIVER, TESTS, *PACKAGE}.issubset(inputs), "event source closure unbound")
    for name, row in plan["selected_archives"].items():
        bound = inputs.get(row["path"])
        path = ROOT / row["path"]
        require(bound is not None and bound["sha256"].removeprefix("sha256:") == row["sha256"]
                and path.stat().st_size == row["bytes"], "selected archive unbound")
        with path.open("rb") as stream:
            magic = stream.read(8)
        require(magic == (b"D2GRAM02" if name == "plain" else b"D2GRAM01"),
                "selected diagonal frontend differs")
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


def checked_report(report, arm, archive, plan, raw):
    event = arm["backend"] == "event"
    costs = report["costs"] if event else {key: report[key] for key in LEGACY_COSTS}
    require(set(costs) == set(EVENT_COSTS if event else LEGACY_COSTS)
            and all(type(value) is int and value >= 0 for value in costs.values())
            and sum(costs.values()) == archive.stat().st_size == report["complete_archive_bytes"],
            "complete archive accounting differs")
    frame_size = plan["frame_size"]
    require(report["raw_bytes"] == len(raw) == plan["population"]["bytes"]
            and report["raw_sha256"] == hashlib.sha256(raw).hexdigest() == plan["population"]["sha256"]
            and report["frame_size"] == frame_size
            and len(report["frames"]) == (len(raw) + frame_size - 1) // frame_size,
            "raw population or frame count differs")
    for index, frame in enumerate(report["frames"]):
        part = raw[index * frame_size:(index + 1) * frame_size]
        require(frame["raw_bytes"] == len(part) and frame["raw_sha256"] == hashlib.sha256(part).hexdigest()
                and is_hash(frame["model_sha256"])
                and integer(frame["repeated_argument_references"], 0, 16 * frame_size), "frame identity differs")
        if arm["id"] in ("B", "G", "X"):
            require({key: frame[key] for key in FRAME_IDENTITY} == plan["expected_frames"][index],
                    "selected frame graph or repeated bindings differ")
        if event:
            require(set(frame["costs"]) == set(EVENT_COSTS)
                    and all(type(value) is int and value >= 0 for value in frame["costs"].values()),
                    "frame accounting differs")
            sync = frame["synchronization"]
            require(isinstance(sync, dict) and sync and integer(sync["payload_bytes"], 37, driver.codec.MAX_ARCHIVE)
                    and set(sync["actual_bytes_by_category"]).issubset(EVENT_COSTS)
                    and all(type(value) is int and value >= 0 for value in sync["actual_bytes_by_category"].values())
                    and sum(sync["actual_bytes_by_category"].values()) == sync["payload_bytes"],
                    "synchronization accounting differs")
            require(sync["mode"] == arm["id"] and sync["canonical_reencode_pass"] is True
                    and sync["emitted_bytes"] == frame["raw_bytes"] and sync["output_sha256"] == frame["raw_sha256"]
                    and integer(sync["events"], 0, plan["model_spec"]["max_events"])
                    and integer(sync["binary_events"], 0, plan["model_spec"]["max_binary_events"])
                    and all(is_hash(sync[key]) for key in ("model_state_digest", "probability_trace_sha256",
                                                          "sync_trace_sha256", "state_digest"))
                    and isinstance(sync["common_coder_state"], list) and sync["common_coder_state"]
                    and all(type(value) is int and value >= 0 for value in sync["common_coder_state"]),
                    "complete synchronization evidence differs")
            require(all(frame["costs"][key] == sync["actual_bytes_by_category"].get(key, 0)
                        + (FRAME_BYTES if key == "framing" else 0) for key in EVENT_COSTS),
                    "frame header or payload attribution differs")
            require(is_hash(frame["interpreter_sha256"])
                    and is_hash(frame["boundary_sha256"])
                    and integer(frame["boundary_count"], 0, 2 * frame_size + 1)
                    and integer(frame["execution_steps"], 0, 16 * 65536)
                    and integer(frame["stored_nodes"], 0, 16 * 65536), "interpreter evidence missing")
    if event:
        require(report["mode"] == arm["id"] and report["context_enabled"] is arm["context_enabled"]
                and report["model_spec"] == plan["model_spec"], "event model or context flag differs")
        require(report["raw_encoder_repeat_proved"] is (arm["id"] == "R")
                and report["repeat_scope"] == ("raw-context-encoding" if arm["id"] == "R" else "fixed-graph-event-encoding")
                and report["complete_package_bytes"] is None and report["full_corpus_score_bytes"] is None,
                "event scope differs")
        for category in EVENT_COSTS:
            frame_sum = sum(frame["costs"][category] for frame in report["frames"])
            require(costs[category] == frame_sum + (HEADER_BYTES if category == "framing" else 0),
                    "global framing or frame costs differ")
    else:
        selected = plan["selected_archives"][arm["selection"]]
        require(report["storage_version"] == arm["storage"] and report["selection_version"] == arm["storage"]
                and report["input_archive_sha256"] == selected["sha256"]
                and report["program_identity_pass"] is True and report["fixed_sections_pass"] is True
                and report["raw_encoder_repeat_proved"] is False
                and report["repeat_scope"] == "fixed-program-reserialization", "baseline identity or repeat scope differs")
    return costs


def classify_failure(error, last, plan):
    if last and last["timeout"]:
        error = subprocess.TimeoutExpired(last["argv"], plan["phase_wall_seconds"])
    elif last and last["error"]:
        error = OSError(last["error"])
    return driver.classification(error, last["returncode"] if last else None)


def comparison_table(rows, plan):
    by_id = {row["arm"]["id"]: row for row in rows}
    require(len(rows) == 5 and set(by_id) == {arm["id"] for arm in ARMS}, "incomplete five-arm table")
    for index, baseline in enumerate(by_id["B"]["frames"]):
        for identity in ("G", "X"):
            frame = by_id[identity]["frames"][index]
            require(all(frame[key] == baseline[key] for key in FRAME_IDENTITY)
                    and frame["mode"] == driver.codec.MODES[baseline["mode"]], "paired graph or frontend differs")
        g, x = by_id["G"]["frames"][index], by_id["X"]["frames"][index]
        require(all(g[key] == x[key] for key in ("interpreter_sha256", "execution_steps", "stored_nodes",
                                               "boundary_sha256", "boundary_count")),
                "G/X execution schedule differs")
        require(all(g["synchronization"][key] == x["synchronization"][key]
                    for key in ("events", "binary_events", "emitted_bytes", "output_sha256")),
                "G/X typed event counts differ")
    sizes = {key: row["archive_bytes"] for key, row in by_id.items()}
    return dict(schema="gamma.enwiki9.event-costs.v1", raw_bytes=plan["population"]["bytes"], archive_bytes=sizes,
                context_saved_bytes=sizes["G"] - sizes["X"], grammar_vs_raw_event_saved_bytes=sizes["R"] - sizes["X"],
                event_vs_plain_deflate_saved_bytes=sizes["P"] - sizes["X"],
                event_vs_selected_deflate_saved_bytes=sizes["B"] - sizes["X"],
                context_improved=sizes["X"] < sizes["G"], beats_G_R_P=all(sizes["X"] < sizes[key] for key in ("G", "R", "P")),
                cells=[dict(arm=row["arm"], archive_bytes=row["archive_bytes"], accounting=row["accounting"]) for row in rows],
                package_source=[driver.artifact(ROOT / path) for path in PACKAGE],
                known_source_bytes=sum((ROOT / path).stat().st_size for path in PACKAGE),
                complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                package_gaps=["runtime distribution and license closure", "accepted source and option accounting"],
                evidence_scope="opening development archive comparison; fixed selected grammar; no full-corpus score")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    _, reference, plan = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status="preflight_pass", executed=False, native_phases=15)))
        return 0
    directory = ROOT / "results" / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), "nonempty output")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    raw = (ROOT / plan["population"]["path"]).read_bytes()
    stage = dict(schema="gamma.enwiki9.event-stage.v1", candidate_id=args.candidate, experiment=reference,
                 status="running", arms=[], commands=[], objective_credit_bytes=0, complete_package_bytes=None,
                 full_corpus_score_bytes=None, resource_qualified=False, selection_stage=plan["stage"])
    last, table = None, None
    try:
        for arm in ARMS:
            source = ROOT / (plan["population"]["path"] if arm["selection"] == "raw"
                             else plan["selected_archives"][arm["selection"]]["path"])
            paths = {key: directory / (arm["id"] + suffix) for key, suffix in
                     (("archive", ".d2g"), ("restored", ".raw"), ("repeat", ".repeat.d2g"))}
            repeat_source = paths["restored"] if arm["id"] == "R" else source
            for phase, operation, inp, out in (("encode", "encode", source, paths["archive"]),
                    ("decode", "decode", paths["archive"], paths["restored"]),
                    ("repeat", "encode", repeat_source, paths["repeat"])):
                tool = CODEC if arm["backend"] == "event" else RESERIALIZER if operation == "encode" else DECODER
                command = [sys.executable, str(ROOT / tool), operation, str(inp), str(out)]
                if operation == "encode":
                    command += ["--mode", arm["id"]] if arm["backend"] == "event" else ["--storage", arm["storage"]]
                last = driver.run_phase(directory, arm["id"] + "-" + phase, command, plan, marker)
                stage["commands"].append(last)
                require(last["returncode"] == 0 and not last["timeout"] and last["error"] is None,
                        "phase failed: " + last["phase"])
            require(paths["restored"].read_bytes() == raw, "independent inverse differs")
            require(paths["archive"].read_bytes() == paths["repeat"].read_bytes(), "deterministic repeat differs")
            wrappers = {phase: driver.read_json(directory / (arm["id"] + "-" + phase + ".stdout"))
                        for phase in ("encode", "decode", "repeat")}
            reports = {phase: checked_wrapper(wrapper) for phase, wrapper in wrappers.items()}
            report = reports["encode"]
            require(report == reports["repeat"], "repeat report differs")
            if arm["backend"] == "event":
                require(report == reports["decode"], "independent decoder report or synchronization differs")
            else:
                require(paths["archive"].read_bytes() == source.read_bytes(), "retained diagonal archive differs")
                require(reports["decode"]["raw_bytes"] == len(raw)
                        and reports["decode"]["frontend"] == ("D2GRAM02" if arm["id"] == "P" else "D2GRAM01"),
                        "independent baseline decoder differs")
            costs = checked_report(report, arm, paths["archive"], plan, raw)
            row = dict(arm=arm, archive_bytes=report["complete_archive_bytes"], accounting=costs, frames=report["frames"],
                       exact_inverse=True, deterministic_repeat=True, raw_encoder_repeat_proved=arm["id"] == "R",
                       repeat_scope=report["repeat_scope"], diagonal_archive_identity=arm["id"] in ("P", "B"),
                       common_decoder_report_identity=arm["backend"] == "event",
                       repeated_argument_references=sum(frame["repeated_argument_references"] for frame in report["frames"]),
                       phase_resources={phase: {key: wrappers[phase][key] for key in
                           ("cpu_seconds", "elapsed_seconds", "peak_process_rss_kib")} for phase in wrappers},
                       artifacts={key: driver.artifact(path) for key, path in paths.items()})
            driver.write_json(directory / (arm["id"] + ".result.json"), row)
            stage["arms"].append(row)
        table = comparison_table(stage["arms"], plan)
        stage.update(status="passed", correctness_pass=True, accounting_pass=True,
                     paired_program_identity_pass=True, native_phases=len(stage["commands"]))
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
