"""Reproduce a pinned external donor through Gamma's existing execution services.

This adapter changes no donor prediction, preprocessing, weight or kernel.
External reproduction grants no Gamma objective or resource qualification credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.evidence.resolver import ArtifactResolver
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_package_gate import sandbox


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value) + b"\n")


def layout(data, *, archive):
    """The archive's trailer retains order length although it omits order bytes."""
    if len(data) < 16:
        raise ValueError("truncated donor trailer")
    dictionary, order, payload, weights = struct.unpack("<4i", data[-16:])
    if min(dictionary, order, payload, weights) < 0 or not dictionary or not weights:
        raise ValueError("invalid donor component lengths")
    if (archive and not payload) or (not archive and payload):
        raise ValueError("wrong donor role")
    stub = len(data) - dictionary - weights - payload - 16 - (0 if archive else order)
    if stub <= 0:
        raise ValueError("donor components exceed file")
    start = stub + dictionary + (0 if archive else order)
    return {"stub_bytes": stub, "dictionary_bytes": dictionary,
            "order_bytes": 0 if archive else order, "payload_bytes": payload,
            "weights_bytes": weights, "trailer_bytes": 16,
            "weight_sha256": hashlib.sha256(data[start:start + weights]).hexdigest()}


def accounting(compressor, archive, option_bytes):
    c, a = layout(compressor, archive=False), layout(archive, archive=True)
    if c["weights_bytes"] != a["weights_bytes"] or c["weight_sha256"] != a["weight_sha256"]:
        raise ValueError("donor weight copies differ")
    if c["stub_bytes"] != a["stub_bytes"] or compressor[:c["stub_bytes"]] != archive[:a["stub_bytes"]]:
        raise ValueError("donor stubs differ")
    if type(option_bytes) is not int or option_bytes < 0:
        raise ValueError("missing or invalid paid option count")
    A, W = a["payload_bytes"], a["weights_bytes"]
    total = len(compressor) + len(archive) + option_bytes
    C = total - A - 2 * W
    return {"A": A, "W": W, "C": C, "S": total, "formula": "S=A+2W+C",
            "compressor": c, "archive": a, "required_option_bytes": option_bytes,
            "file_only_total_bytes": len(compressor) + len(archive)}


def donor_sandbox(runtime, work):
    command = sandbox(runtime, work, ["./archive9"])
    separator = command.index("--")
    # The unchanged self-extractor calls system() to decode its paid dictionary.
    # Mount only the pinned shell in addition to the pinned ELF providers.
    return command[:separator] + ["--dir", "/bin", "--ro-bind",
        runtime["shell"]["resolved_path"], "/bin/sh"] + command[separator:]


def run(root, output, experiment_path, closure_path, plan_path):
    experiment = json.loads(experiment_path.read_bytes())
    expected = {"path": experiment_path.relative_to(root).as_posix(),
                "sha256": "sha256:" + hashlib.sha256(experiment_path.read_bytes()).hexdigest()}
    if json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) != expected:
        raise ValueError("lab experiment binding differs")
    for row in experiment["inputs"]:
        if fingerprint(root / row["path"], root)["sha256"] != row["sha256"].removeprefix("sha256:"):
            raise ValueError("bound input changed: " + row["path"])
    if any(output.iterdir()):
        raise ValueError("reproduction output must be fresh")
    snapshot = output / "snapshot"
    materialize(root, json.loads(closure_path.read_bytes()), snapshot)
    plan = json.loads((snapshot / plan_path.relative_to(root)).read_bytes())
    runtime = json.loads((snapshot / plan["runtime"]).read_bytes())
    for row in [runtime["bwrap"], runtime["shell"], *runtime["providers"].values()]:
        provider = Path(row["resolved_path"])
        if fingerprint(provider, provider.parent)["sha256"] != row["sha256"]:
            raise ValueError("runtime provider changed")
    resolver = ArtifactResolver(root, tuple(plan["assets"]))
    comp = resolver.verify(plan["compressor"]).read_bytes()
    arc = resolver.verify(plan["archive"]).read_bytes()
    score = accounting(comp, arc, plan["required_option_bytes"])
    if score["file_only_total_bytes"] != 99313750 or score["W"] != 2978039:
        raise ValueError("released donor accounting differs")
    write(output / "accounting.json", score)
    work = output / "decode"
    work.mkdir()
    resolver.copy(plan["archive"], work / "archive9")
    (work / "archive9").chmod(0o755)
    caps = plan["caps"]
    context = ExecutionContext(experiment["experimentId"], snapshot, output,
        ResourceBudget(tuple(caps["cpus"]), caps["memory_bytes"], caps["scratch_bytes"], caps["wall_seconds"]),
        BuildProfile((), ()), (("PATH", "/usr/bin:/bin"), ("LC_ALL", "C")))
    command = donor_sandbox(runtime, work)
    write(output / "launch.json", {"experiment": expected, "command": command,
        "caps": caps, "accounting": score, "decode_corpus_access": False,
        "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
        "qualification": False, "timing_authority": "shared-host diagnostic"})
    print(json.dumps({"phase": "independent-offline-decode", "command": command}), flush=True)
    with CgroupMemoryGuard.current(caps["memory_bytes"]) as guard:
        outcome, record = CommandExecutor(context, resident_guard=guard).run(
            "decode", command, PhaseLimits(plan["decode_seconds"], plan["decode_seconds"],
                                          plan["address_space_bytes"], caps["scratch_bytes"]))
    result = {"schema": "gamma.enwiki9.external-donor-reproduction.v1",
        "candidate_id": experiment["experimentId"], "experiment": expected,
        "accounting": score, "command": record, "decode_corpus_access": False,
        "status": "incomplete", "exact_inverse": False,
        "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
        "qualification": False, "rebuild_reproduced": False,
        "deterministic_recompression_reproduced": False}
    if outcome.classification == "completed":
        restored = fingerprint(work / "enwik9_uncompressed", root)
        result["restored"] = restored
        result["exact_inverse"] = (restored["bytes"] == experiment["objective"]["corpusBytes"] and
            restored["sha256"] == experiment["objective"]["corpusSha256"])
        if result["exact_inverse"]:
            result["status"] = "decode_reproduced"
    for row in plan["assets"]:
        resolver.verify(row["path"])
    write(output / "result.json", result)
    write(output / "artifacts.json", {"files": [fingerprint(p, root)
        for p in sorted(output.rglob("*")) if p.is_file()]})
    print(json.dumps({k: result[k] for k in ("status", "exact_inverse", "qualification")}), flush=True)
    return 0 if result["exact_inverse"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("root", "output", "experiment", "closure", "plan"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    return run(*(getattr(args, key).resolve() for key in ("root", "output", "experiment", "closure", "plan")))
