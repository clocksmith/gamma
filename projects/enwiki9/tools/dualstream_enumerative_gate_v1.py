#!/usr/bin/env python3
"""Five fixed-representation comparisons using the existing bounded gate driver."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SHARED_DRIVER = "tools/dualstream_grammar_gate_v1.py"
spec = importlib.util.spec_from_file_location(__name__ + "_driver", ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF = "tools/dualstream_enumerative_gate_v1.py"
driver.CODEC = "tools/dualstream_enumerative_v1.py"
RESERIALIZER = "tools/dualstream_grammar_reserialize_v1.py"
DECODER = "tools/dualstream_grammar_v1.py"
PACKAGE = [driver.CODEC, DECODER, RESERIALIZER, "tools/dualstream_grammar_argtokens_v2.py"]
ARMS = [dict(id=i, selection=s, backend=b, storage=t) for i, s, b, t in (
    ("P", "plain", "deflate", "old"), ("B", "old", "deflate", "old"),
    ("E", "old", "enumerative", "old"), ("T", "old", "enumerative", "new"),
    ("R", "plain", "enumerative", "old"))]
require = driver.require


def validate_plan(plan, candidate):
    require(plan["schema"] == "gamma.enwiki9.enumerative-gate-plan.v1" and plan["candidate_id"] == candidate,
            "plan identity differs")
    require(plan["arms"] == ARMS and plan["stage"] == "development" and plan["chunk_bytes"] == 4096,
            "frozen comparison differs")
    require(plan["population"]["bytes"] == 250000 and plan["frame_size"] == 65536, "population differs")
    require(plan["resources"] == dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864,
                                      swap_bytes=0, wall_seconds=600), "resource policy differs")
    require(plan["phase_cpu_seconds"] == 60 and plan["phase_wall_seconds"] == 90 and
            plan["phase_address_bytes"] == 536870912, "phase policy differs")
    require(plan["runtime_files"] and plan["kernel_basis"], "kernel/runtime evidence absent")


driver.validate_plan = validate_plan


def authenticate(candidate, validate_only=False):
    contract, reference, plan = driver.authenticate(candidate, validate_only)
    inputs = {r["path"]: r for r in contract["inputs"]}
    require(all(path in inputs for path in PACKAGE + [SHARED_DRIVER]), "package source unbound")
    for selected in plan["selected_archives"].values():
        require(selected["path"] in inputs and
                inputs[selected["path"]]["sha256"] == "sha256:" + selected["sha256"] and
                (ROOT / selected["path"]).stat().st_size == selected["bytes"], "selected archive unbound")
    return contract, reference, plan


def checked_cost(report, size, enumerative):
    if enumerative:
        expected = {n + "_rank_bytes" for n in ("literal_definitions", "grammar_programs", "structure", "content", "arguments")}
        expected |= {"count_table_bytes", "stream_header_bytes", "framing_bytes", "exception_bytes"}
        costs = report["costs"]
        require(set(costs) == expected, "cost categories differ")
    else:
        costs = {key: report[key] for key in ("literal_definition_bytes", "structure_bytes", "content_bytes",
                                             "argument_reference_bytes", "exception_bytes", "framing_bytes")}
    require(all(type(v) is int and v >= 0 for v in costs.values()) and
            sum(costs.values()) == size == report["complete_archive_bytes"], "complete cost differs")
    require(report["raw_encoder_repeat_proved"] is False, "unsupported raw discovery repeat")
    return costs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    _, reference, plan = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status="preflight_pass", executed=False, native_phases=15)))
        return 0
    directory = ROOT / "results" / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), "nonempty output")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    raw = (ROOT / plan["population"]["path"]).read_bytes()
    stage = dict(schema="gamma.enwiki9.enumerative-stage.v1", candidate_id=args.candidate, experiment=reference,
                 status="running", arms=[], commands=[], objective_credit_bytes=0,
                 complete_package_bytes=None, full_corpus_score_bytes=None, resource_qualified=False)
    last = None
    try:
        for arm in ARMS:
            selected = plan["selected_archives"][arm["selection"]]
            source = ROOT / selected["path"]
            paths = {key: directory / (arm["id"] + suffix) for key, suffix in
                     (("archive", ".d2g"), ("restored", ".raw"), ("repeat", ".repeat.d2g"))}
            enum = arm["backend"] == "enumerative"
            for phase, operation, inp, out in (("encode", "encode", source, paths["archive"]),
                    ("decode", "decode", paths["archive"], paths["restored"]),
                    ("repeat", "encode", source, paths["repeat"])):
                tool = driver.CODEC if enum else RESERIALIZER if operation == "encode" else DECODER
                command = [sys.executable, str(ROOT / tool), operation, str(inp), str(out)]
                if operation == "encode":
                    command += ["--storage", arm["storage"]]
                last = driver.run_phase(directory, arm["id"] + "-" + phase, command, plan, marker)
                stage["commands"].append(last)
                require(last["returncode"] == 0 and not last["timeout"] and last["error"] is None, "phase failed: " + last["phase"])
            require(paths["restored"].read_bytes() == raw, "independent inverse differs")
            require(paths["archive"].read_bytes() == paths["repeat"].read_bytes(), "repeat differs")
            reports = {phase: driver.read_json(directory / (arm["id"] + "-" + phase + ".stdout"))
                       for phase in ("encode", "decode", "repeat")}
            report = reports["encode"]["result"]
            require(report == reports["repeat"]["result"], "repeat report differs")
            costs = checked_cost(report, paths["archive"].stat().st_size, enum)
            require(report["raw_bytes"] == len(raw) and report["raw_sha256"] == plan["population"]["sha256"], "raw report differs")
            if enum:
                require(report["section_hashes"] == reports["decode"]["result"]["section_hashes"], "decoded section identity differs")
            else:
                require(paths["archive"].read_bytes() == source.read_bytes(), "unchanged baseline differs")
            row = dict(arm=arm, archive_bytes=report["complete_archive_bytes"], accounting=costs,
                       encode_cpu_seconds=reports["encode"]["cpu_seconds"], decode_cpu_seconds=reports["decode"]["cpu_seconds"],
                       encode_peak_rss_kib=reports["encode"]["peak_process_rss_kib"],
                       decode_peak_rss_kib=reports["decode"]["peak_process_rss_kib"], frames=report["frames"],
                       exact_inverse=True, deterministic_reserialization_repeat=True,
                       raw_encoder_repeat_proved=False, repeat_scope="fixed-program-reserialization",
                       artifacts={k: driver.artifact(p) for k, p in paths.items()})
            driver.write_json(directory / (arm["id"] + ".result.json"), row)
            stage["arms"].append(row)
        rows = {r["arm"]["id"]: r for r in stage["arms"]}
        for identity in ("E", "T"):
            require([f["model_sha256"] for f in rows[identity]["frames"]] ==
                    [f["model_sha256"] for f in rows["B"]["frames"]], "fixed graph differs")
        table = dict(raw_bytes=len(raw), archive_bytes={a: r["archive_bytes"] for a, r in rows.items()},
                     enum_vs_fixed_deflate_saved_bytes=rows["B"]["archive_bytes"] - rows["E"]["archive_bytes"],
                     token_argument_saved_bytes=rows["E"]["archive_bytes"] - rows["T"]["archive_bytes"],
                     enum_vs_plain_deflate_saved_bytes=rows["P"]["archive_bytes"] - rows["E"]["archive_bytes"],
                     package_source=[driver.artifact(ROOT / p) for p in PACKAGE],
                     complete_package_bytes=None, full_corpus_score_bytes=None,
                     package_gaps=["runtime dependency/distribution closure", "license closure", "complete accepted source/options accounting"],
                     evidence_scope="byte-alphabet fixed-program serialization; no raw grammar search or full-corpus bound")
        driver.write_json(directory / "costs-table.json", table)
        stage.update(status="passed", correctness_pass=True, accounting_pass=True, paired_program_identity_pass=True,
                     native_phases=len(stage["commands"]), costs=table)
    except Exception as error:
        classified = subprocess.TimeoutExpired(last["argv"], 90) if last and last["timeout"] else error
        stage.update(status="failed", correctness_pass=False, native_phases=len(stage["commands"]),
                     failure_class=driver.classification(classified, last["returncode"] if last else None),
                     error=type(error).__name__ + ": " + str(error))
    try:
        authenticate(args.candidate)
        stage["frozen_inputs_reverified"] = True
    except Exception as error:
        stage.update(status="failed", correctness_pass=False, frozen_inputs_reverified=False,
                     failure_class="infrastructure-failure", error=str(error))
    files = [driver.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]
    driver.write_json(directory / "artifacts.json", dict(complete=stage["correctness_pass"], files=files))
    driver.write_json(directory / "stage-decision.json", stage)
    print(json.dumps(dict(status=stage["status"], arms_closed=len(stage["arms"]), native_phases=stage["native_phases"])))
    return 0 if stage["correctness_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
