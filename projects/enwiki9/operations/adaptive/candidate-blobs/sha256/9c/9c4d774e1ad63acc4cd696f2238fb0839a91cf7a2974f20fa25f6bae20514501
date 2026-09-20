"""Lab recipe: aligned native capture, bounded full-model E training and replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_training_capture import adapt, source_members, expected_rows, validate_rows


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value) + b"\n")


def run(root, output, experiment_path, closure_path, plan_path):
    experiment = json.loads(experiment_path.read_bytes())
    plan = json.loads(plan_path.read_bytes())
    for row in experiment["inputs"]:
        if fingerprint(root / row["path"], root)["sha256"] != row["sha256"].removeprefix("sha256:"):
            raise ValueError("bound input differs: " + row["path"])
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / "snapshot"
    materialize(root, json.loads(closure_path.read_bytes()), snapshot)
    native = output / "native"
    native.mkdir()
    members, changes = adapt(source_members(snapshot / plan["native_source_zip"]))
    for name, data in members.items():
        path = native / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    write(output / "native-adaptation.json", {"changes": changes})
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(snapshot / "src"),
           "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
           "OPENBLAS_NUM_THREADS": "1", "TMPDIR": str(native), "PYTHONHASHSEED": "0"}
    caps = plan["caps"]
    context = ExecutionContext(experiment["experimentId"], snapshot, native,
        ResourceBudget(tuple(caps["cpus"]), caps["memory_bytes"], caps["scratch_bytes"], caps["wall_seconds"]),
        BuildProfile(tuple(plan["compile_command"]), tuple(map(tuple, plan["build_tools"]))),
        tuple(env.items()))
    executor = CommandExecutor(context)
    records = []

    def phase(name, argv, seconds=180):
        for tool, digest in plan["build_tools"]:
            if hashlib.sha256(Path(tool).read_bytes()).hexdigest() != digest:
                raise ValueError("build/runtime tool changed")
        outcome, row = executor.run(name, argv,
            PhaseLimits(seconds, seconds + 10, caps["memory_bytes"], caps["scratch_bytes"]))
        records.append(row)
        scratch = native / "ppm.temp"
        if scratch.exists():
            if scratch.is_symlink() or not scratch.is_file():
                raise ValueError("unexpected PPM scratch type")
            scratch.unlink()
        if outcome.classification != "completed":
            raise RuntimeError("phase failed: " + name)

    phase("build", plan["compile_command"], 300)
    model = native / "models/6m-q4-fp32.tfwc2"
    original_model = snapshot / plan["parent_packed"]
    if model.read_bytes() != original_model.read_bytes():
        raise ValueError("native ZIP's model differs from bound parent")
    raw = snapshot / plan["raw"]
    dictionary = native / "dictionary/english.dic"
    executable = str(native / "cmix")
    base = [executable, "-c", str(dictionary), str(raw)]
    capture = native / "priors.f16"
    phase("P-capture", base + [str(native / "P.arc"), "--transformer", str(model),
                               "--save-ppmd-probs", str(capture)])
    if (native / "P.arc").read_bytes() != (snapshot / plan["parent_archive"]).read_bytes():
        raise ValueError("capturing training data changed the frozen P archive")
    expected = expected_rows((snapshot / plan["stored"]).read_bytes(), 250000)
    actual = capture.with_suffix(".f16.tokens").read_bytes()
    if actual != expected:
        raise ValueError("native token/reset capture differs from independent WRT mapping")
    capture_report = validate_rows(actual, capture.stat().st_size)
    write(output / "capture.json", capture_report)
    phase("P-decode", [executable, "-d", str(dictionary), str(native / "P.arc"),
                       str(native / "P.raw"), "--transformer", str(model)])
    phase("P-repeat", [executable, "-c", str(dictionary), str(native / "P.raw"),
                       str(native / "P.repeat.arc"), "--transformer", str(model)])
    if (native / "P.raw").read_bytes() != raw.read_bytes() or (native / "P.repeat.arc").read_bytes() != (native / "P.arc").read_bytes():
        raise ValueError("native P inverse or repeat differs")
    entry = snapshot / "tools/fx2_entropy_gate_v1.py"
    phase("E-train", [plan["python"], str(entry), "--phase", "train", "--root", str(snapshot),
                      "--output", str(native / "E"), "--plan", str(snapshot / plan_path.relative_to(root)),
                      "--capture", str(capture)], 900)
    child_model = native / "E/weights.tfwc2"
    for name, mode, source, destination in (
        ("encode", "-c", raw, native / "E.arc"),
        ("decode", "-d", native / "E.arc", native / "E.raw"),
        ("repeat", "-c", native / "E.raw", native / "E.repeat.arc"),
    ):
        phase("E-" + name, [executable, mode, str(dictionary), str(source), str(destination),
                            "--transformer", str(child_model)])
    if (native / "E.raw").read_bytes() != raw.read_bytes() or (native / "E.repeat.arc").read_bytes() != (native / "E.arc").read_bytes():
        raise ValueError("native E inverse or repeat differs")
    archives = {arm: (native / (arm + ".arc")).stat().st_size for arm in ("P", "E")}
    weights = {"P": model.stat().st_size, "E": child_model.stat().st_size}
    result = {"schema": "gamma.enwiki9.fx2-entropy-comparison.v1", "candidate_id": experiment["experimentId"],
              "objective": experiment["objective"], "archive_bytes": archives, "packed_model_bytes": weights,
              "sample_archive_gain": archives["P"] - archives["E"],
              "two_copy_weight_gain": 2 * (weights["P"] - weights["E"]),
              "sample_plus_weight_delta": archives["P"] - archives["E"] + 2 * (weights["P"] - weights["E"]),
              "source_and_executable_delta": 0, "declared_option_delta": 0,
              "accounting_scope": "component differences in identical native implementation; final self-extracting delivery not constructed",
              "independent_inverse": True, "raw_repeat": True, "parent_archive_identity": True,
              "capture_alignment": True, "commands": records, "objective_credit_bytes": 0,
              "full_corpus_score_bytes": None, "promotion_authorized": False,
              "limitations": ["exposed 250KB development only", "CPU reference training surrogate",
                              "truncated warmup during training; fresh full prefix native inference",
                              "metadata arm and 1MB confirmation remain separate gates",
                              "no native full-state serialization or resource qualification"]}
    result["fixed_configuration_lost"] = result["sample_plus_weight_delta"] <= 0
    write(output / "comparison.json", result)
    write(output / "artifacts.json", {"artifacts": [fingerprint(p, root) for p in sorted(output.rglob("*")) if p.is_file()]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("run", "train"), default="run")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--experiment", type=Path)
    parser.add_argument("--closure", type=Path)
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    if args.phase == "train":
        from .fx2_entropy_development import train
        plan = json.loads(args.plan.read_bytes())
        print("[run-contract] lane=compression profile=fx2_cpu_reference_v1 device=cpu "
              "population=exposed-opening250k steps=" + str(plan["training"]["steps"]), flush=True)
        train(upstream=args.root / plan["upstream"], checkpoint=args.root / plan["checkpoint"],
              parent_packed=args.root / plan["parent_packed"], token_path=Path(str(args.capture) + ".tokens"),
              prior_path=args.capture, output=args.output, plan=plan["training"])
    else:
        result = run(args.root.resolve(), args.output.resolve(), args.experiment.resolve(),
                     args.closure.resolve(), args.plan.resolve())
        print(json.dumps({k: result[k] for k in ("archive_bytes", "packed_model_bytes", "sample_plus_weight_delta")}))


if __name__ == "__main__":
    main()
