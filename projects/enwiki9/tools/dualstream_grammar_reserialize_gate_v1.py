#!/usr/bin/env python3
"""Measure a frozen 2x2 program-reserialization table through the canonical queue.

Each repeat starts from the same selected archive. It is not a repeated raw
encoding or renewed grammar discovery. This diagnostic grants no package,
qualification, full-corpus, or combined-component compression credit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SHARED_DRIVER = "tools/dualstream_grammar_gate_v1.py"
spec = importlib.util.spec_from_file_location(__name__ + "_driver", ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF = "tools/dualstream_grammar_reserialize_gate_v1.py"
driver.CODEC = "tools/dualstream_grammar_reserialize_v1.py"
require = driver.require
SCHEMA = "gamma.enwiki9.dualstream-reserialize-plan.v1"
ARMS = [dict(id=identity, selection=selection, storage=storage) for identity, selection, storage in
        (("OO", "old", "old"), ("ON", "old", "new"), ("NO", "new", "old"), ("NN", "new", "new"))]
DECODERS = {"old": "tools/dualstream_grammar_v1.py", "new": "tools/dualstream_grammar_argtokens_v2.py"}
ACCOUNTING = ("literal_definition_bytes", "structure_bytes", "content_bytes",
              "argument_reference_bytes", "exception_bytes", "framing_bytes")
REPEAT_SCOPE = "fixed-program-reserialization"


def validate_plan(plan, candidate):
    required = {"schema", "candidate_id", "stage", "population", "arms", "frame_size", "resources",
                "phase_wall_seconds", "phase_cpu_seconds", "phase_address_bytes", "runtime_files",
                "hypothesis", "stop_rule", "program_identity", "source_binding_policy", "owner",
                "repeat_scope", "package_policy", "kernel_basis", "selected_archives"}
    require(set(plan) == required, "reserialization plan fields differ")
    require(plan["schema"] == SCHEMA and plan["candidate_id"] == candidate, "plan identity differs")
    require(plan["stage"] == "development" and plan["arms"] == ARMS, "four fixed development cells required")
    require(plan["population"]["bytes"] == 250000 and plan["frame_size"] == 65536, "population or frame policy differs")
    require(plan["resources"] == dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864,
                                      swap_bytes=0, wall_seconds=120), "frozen resource envelope differs")
    require((plan["phase_cpu_seconds"], plan["phase_wall_seconds"], plan["phase_address_bytes"])
            == (15, 20, 536870912), "frozen child bounds differ")
    require(plan["runtime_files"], "runtime identity is missing")
    require(set(plan["selected_archives"]) == {"old", "new", "plain"}, "selected archive references differ")
    for name, reference in plan["selected_archives"].items():
        path = Path(reference["path"])
        require(set(reference) == {"path", "bytes", "sha256"} and not path.is_absolute()
                and ".." not in path.parts and type(reference["bytes"]) is int
                and 0 < reference["bytes"] <= driver.codec.MAX_ARCHIVE
                and re.fullmatch(r"[a-f0-9]{64}", reference["sha256"]), "invalid selected archive: " + name)


driver.validate_plan = validate_plan


def authenticate(candidate, validate_only=False):
    contract, reference, plan = driver.authenticate(candidate, validate_only)
    inputs = {row["path"]: row for row in contract["inputs"]}
    require({SHARED_DRIVER, *DECODERS.values()}.issubset(inputs), "shared driver and target decoders must be frozen inputs")
    for selected in plan["selected_archives"].values():
        bound = inputs.get(selected["path"])
        path = ROOT / selected["path"]
        require(bound is not None and bound["sha256"].removeprefix("sha256:") == selected["sha256"],
                "selected archive is not a frozen input")
        require(path.stat().st_size == selected["bytes"] and driver.sha(path) == selected["sha256"],
                "selected archive identity differs")
    return contract, reference, plan


def checked_report(wrapper, arm, selected, archive, plan, raw):
    report = wrapper["result"]
    require(report["repeat_scope"] == REPEAT_SCOPE, "repeat scope must name fixed program reserialization")
    require(report["raw_encoder_repeat_proved"] is False, "raw encoder repeat is not proved by this diagnostic")
    require(report["selection_version"] == arm["selection"] and report["storage_version"] == arm["storage"],
            "serializer or selection version differs")
    require(report["input_archive_sha256"] == selected["sha256"], "reported selected archive differs")
    require(report["program_identity_pass"] is True and report["fixed_sections_pass"] is True,
            "program or fixed-section preservation failed")
    require(report["complete_archive_bytes"] == archive.stat().st_size
            and all(type(report[key]) is int and report[key] >= 0 for key in ACCOUNTING)
            and sum(report[key] for key in ACCOUNTING) == report["complete_archive_bytes"],
            "complete archive accounting differs")
    require(isinstance(report["frames"], list) and report["frames"], "frame program fingerprints missing")
    frame_size = plan["frame_size"]
    require(report["frame_size"] == frame_size and report["raw_bytes"] == len(raw) == plan["population"]["bytes"]
            and report["raw_sha256"] == hashlib.sha256(raw).hexdigest()
            and len(report["frames"]) == (len(raw) + frame_size - 1) // frame_size,
            "raw population or frame count differs")
    for index, frame in enumerate(report["frames"]):
        offset = index * frame_size
        part = raw[offset:offset + frame_size]
        require(frame["raw_offset"] == offset and frame["raw_bytes"] == len(part)
                and frame["raw_sha256"] == hashlib.sha256(part).hexdigest()
                and frame["mode"] in driver.codec.MODES, "frame identity or contiguous partition differs")
        require(isinstance(frame["model_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", frame["model_sha256"]),
                "invalid frame model fingerprint")
        hashes = frame["fixed_sections_sha256"]
        require(set(hashes) == {"programs", "structure", "content"}
                and all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in hashes.values()),
                "fixed section fingerprints missing")
        require(all(type(frame[key]) is int and frame[key] >= 0
                    for key in ("repeated_argument_references", "supplied_arguments", "templates")),
                "invalid program or argument count")
    return report


def comparison_table(rows, plain):
    by_id = {row["arm"]["id"]: row for row in rows}
    require(set(by_id) == {arm["id"] for arm in ARMS} and len(rows) == 4, "incomplete diagnostic table")
    for left, right in (("OO", "ON"), ("NO", "NN")):
        for field in ("mode", "raw_offset", "raw_bytes", "raw_sha256", "model_sha256", "fixed_sections_sha256",
                      "repeated_argument_references", "supplied_arguments", "templates"):
            require([frame[field] for frame in by_id[left]["frames"]]
                    == [frame[field] for frame in by_id[right]["frames"]], "paired fixed program differs: " + field)
    sizes = {key: value["archive_bytes"] for key, value in by_id.items()}
    old_delta, new_delta = sizes["ON"] - sizes["OO"], sizes["NN"] - sizes["NO"]
    return dict(schema="gamma.enwiki9.dualstream-reserialize-costs.v1", archive_bytes=sizes,
                cells=[dict(arm=row["arm"], archive_bytes=row["archive_bytes"], accounting=row["accounting"])
                       for row in rows],
                plain_archive_reference=plain, plain_reference_redecoded_here=False,
                storage_delta_on_old_selection_bytes=old_delta, storage_delta_on_new_selection_bytes=new_delta,
                selection_delta_under_old_storage_bytes=sizes["NO"] - sizes["OO"],
                selection_delta_under_new_storage_bytes=sizes["NN"] - sizes["ON"],
                interaction_bytes=new_delta - old_delta, fixed_old_program_storage_improved=old_delta < 0,
                repeat_scope=REPEAT_SCOPE, package_bytes=None, objective_credit_bytes=0,
                promotion_authority=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    _, reference, plan = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status="preflight_pass", raw_bytes=plan["population"]["bytes"],
                              arms=4, native_phases=12, executed=False, repeat_scope=REPEAT_SCOPE)))
        return 0
    directory = ROOT / "results" / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()),
            "result directory must be empty")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    raw = (ROOT / plan["population"]["path"]).read_bytes()
    stage = dict(schema="gamma.enwiki9.dualstream-reserialize-stage.v1", candidate_id=args.candidate,
                 experiment=reference, selection_stage=plan["stage"], raw_bytes=len(raw), status="running",
                 arms=[], commands=[], repeat_scope=REPEAT_SCOPE, objective_credit_bytes=0,
                 complete_package_bytes=None, full_corpus_score_bytes=None, resource_qualified=False)
    last, table = None, None
    try:
        for arm in plan["arms"]:
            selected = plan["selected_archives"][arm["selection"]]
            source = ROOT / selected["path"]
            paths = {key: directory / (arm["id"] + suffix) for key, suffix in
                     (("archive", ".d2g"), ("restored", ".raw"), ("repeat", ".repeat.d2g"))}
            for phase, operation, inp, out in (("encode", "encode", source, paths["archive"]),
                    ("decode", "decode", paths["archive"], paths["restored"]),
                    ("repeat", "encode", source, paths["repeat"])):
                tool = driver.CODEC if operation == "encode" else DECODERS[arm["storage"]]
                command = [sys.executable, str(ROOT / tool), operation, str(inp), str(out)]
                if operation == "encode":
                    command += ["--storage", arm["storage"]]
                last = driver.run_phase(directory, arm["id"] + "-" + phase, command, plan, marker)
                stage["commands"].append(last)
                require(last["returncode"] == 0 and not last["timeout"] and last["error"] is None,
                        "reserialization phase failed: " + last["phase"])
            require(paths["restored"].read_bytes() == raw, "restored bytes differ from bound population")
            require(paths["archive"].read_bytes() == paths["repeat"].read_bytes(), "reserialization repeat differs")
            reports = {phase: driver.read_json(directory / (arm["id"] + "-" + phase + ".stdout"))
                       for phase in ("encode", "decode", "repeat")}
            require(reports["encode"]["result"] == reports["repeat"]["result"], "repeat accounting differs")
            report = checked_report(reports["encode"], arm, selected, paths["archive"], plan, raw)
            diagonal = arm["selection"] == arm["storage"]
            if diagonal:
                require(paths["archive"].read_bytes() == source.read_bytes(), "diagonal archive differs from selected source")
            row = dict(arm=arm, archive_bytes=report["complete_archive_bytes"],
                       accounting={key: report[key] for key in ACCOUNTING}, frames=report["frames"],
                       encode_cpu_seconds=reports["encode"]["cpu_seconds"], decode_cpu_seconds=reports["decode"]["cpu_seconds"],
                       encode_peak_rss_kib=reports["encode"]["peak_process_rss_kib"],
                       decode_peak_rss_kib=reports["decode"]["peak_process_rss_kib"],
                       exact_inverse=True, deterministic_reserialization_repeat=True, repeat_scope=REPEAT_SCOPE,
                       raw_encoder_repeat_proved=False,
                       diagonal_archive_identity=diagonal, selected_archive=selected,
                       repeated_argument_references=sum(frame["repeated_argument_references"] for frame in report["frames"]),
                       artifacts={key: driver.artifact(path) for key, path in paths.items()})
            driver.write_json(directory / (arm["id"] + ".result.json"), row)
            stage["arms"].append(row)
        table = comparison_table(stage["arms"], plan["selected_archives"]["plain"])
        stage.update(status="passed", correctness_pass=True, native_phases=len(stage["commands"]),
                     paired_program_identity_pass=True)
    except Exception as error:
        classified = error
        if last and last["timeout"]:
            classified = subprocess.TimeoutExpired(last["argv"], plan["phase_wall_seconds"])
        elif last and last["error"]:
            classified = OSError(last["error"])
        stage.update(status="failed", correctness_pass=False, native_phases=len(stage["commands"]),
                     failure_class=driver.classification(classified, last["returncode"] if last else None),
                     error=type(error).__name__ + ": " + str(error))
    try:
        authenticate(args.candidate)
        stage["frozen_inputs_reverified"] = True
        if stage["correctness_pass"]:
            driver.write_json(directory / "costs-table.json", table)
            stage["costs"] = table
    except Exception as error:
        stage.update(status="failed", correctness_pass=False, frozen_inputs_reverified=False,
                     failure_class="infrastructure-failure", error="Final source authentication or table publication: " + str(error))
    files = [driver.artifact(path) for path in sorted(directory.iterdir()) if path.is_file()]
    driver.write_json(directory / "artifacts.json", dict(complete=stage["correctness_pass"], files=files))
    driver.write_json(directory / "stage-decision.json", stage)
    print(json.dumps(dict(status=stage["status"], arms_closed=len(stage["arms"]),
                          native_phases=stage["native_phases"], repeat_scope=REPEAT_SCOPE)))
    return 0 if stage["correctness_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
