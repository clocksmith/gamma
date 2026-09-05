#!/usr/bin/env python3
"""Prospective guarded weight-packing gate; no launch authority or full score."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_weight_pack_roundtrip_q0_v1"
RESULT = ROOT / "results" / ID
CONTRACT = "operations/adaptive/experiments/" + ID + ".json"
UPSTREAM = "external/fx2-cmix-transformer-v1/"
MODEL = UPSTREAM + "models/6m-q4-fp32.tfwc2"
MODEL_SHA = "7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860"
TOOLCHAIN = "operations/provenance/public_fx2_gcc15_toolchain_20260905.json"
PROBE = "tools/fx2_weight_pack_probe_v1.cpp"
FIXTURES = "tools/fx2_weight_pack_fixtures_v1.py"
HELPERS = "lib/artifacts.py"
CHECKER = [UPSTREAM + "cpp_infer/src/" + name for name in
           ("test_weights_compressed.cpp", "weights_io.cpp", "weights_io_compressed.cpp", "weights_io.h")]
FLAGS = ["-std=c++17", "-O2", "-Wall", "-Wextra", "-fno-fast-math", "-ffp-contract=off",
         "-fno-math-errno", "-march=x86-64-v3", "-mtune=generic", "-mrecip=none"]
CAPS = {"cpus": [2], "memory_bytes": 512 << 20, "scratch_bytes": 64 << 20,
        "swap_bytes": 0, "wall_seconds": 300}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "missing/aliased frozen input: " + str(path))
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    require(digest == expected.removeprefix("sha256:"), "frozen input changed: " + str(path))
    return digest


def child_usage():
    try: return resource.getrusage(resource.RUSAGE_CHILDREN)
    except OSError: return None


def bootstrap(validate_only=False):
    reference = ({"path": CONTRACT, "sha256": hashlib.sha256((ROOT / CONTRACT).read_bytes()).hexdigest()}
                 if validate_only else json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]))
    require(reference["path"] == CONTRACT, "unexpected bound experiment")
    checked(ROOT / CONTRACT, reference["sha256"])
    contract = json.loads((ROOT / CONTRACT).read_text())
    require(contract["experimentId"] == ID and contract["status"] == "frozen", "experiment is not frozen for this gate")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]), "duplicate frozen input paths")
    required = {"tools/" + ID + ".py", PROBE, FIXTURES, HELPERS, TOOLCHAIN, MODEL,
                UPSTREAM + "LICENSE", UPSTREAM + "pysrc/weights_compress.py", *CHECKER}
    require(required <= inputs.keys(), "incomplete frozen source/asset closure")
    for name, row in inputs.items():
        path = ROOT / name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and path.resolve() == path,
                "frozen input path escapes or aliases the project")
        checked(path, row["sha256"])
    require((ROOT / MODEL).stat().st_size == 2930652, "model byte count changed")
    checked(ROOT / MODEL, MODEL_SHA)
    toolchain = json.loads((ROOT / TOOLCHAIN).read_text())
    for row in toolchain["toolchain"]:
        require(Path(row["path"]).stat().st_size == row["bytes"], "toolchain byte count changed")
        checked(Path(row["path"]), row["sha256"])
    paths = {row["name"]: Path(row["path"]) for row in toolchain["toolchain"]}
    for name in ("g++", "python3", "timeout"):
        require(Path("/usr/bin/" + name).resolve() == paths[name], "toolchain executable redirected")
    for source in ("tools/" + ID + ".py", FIXTURES, HELPERS):
        tree = ast.parse((ROOT / source).read_bytes(), filename=source)
        names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names.update(node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module)
        require(names <= sys.stdlib_module_names, "unexpected non-standard Python dependency")
    for source in [PROBE, *CHECKER]:
        for include in re.findall(r'^\s*#include\s+"([^"\n]+)"', (ROOT / source).read_text(), re.M):
            require(str(Path(source).parent / include) in inputs, "unbound local C++ include")
    if validate_only:
        return {"status": "preflight_pass", "candidate_id": ID, "validated_input_count": len(inputs),
                "toolchain_verified": True, "static_source_references_verified": True, "model_decoded": False,
                "model_bytes": 2930652, "execution_authorized": False, "contract": reference}
    require(os.sched_getaffinity(0) == {2}, "canonical guard must assign CPU 2")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    job_id = marker.parent.name.removesuffix(".resources")
    require(marker == ROOT / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl"), "unexpected phase-marker owner")
    matches = list((ROOT / "operations/adaptive/running").glob("*" + job_id + ".json"))
    require(len(matches) == 1, "canonical running job is missing or ambiguous")
    job = json.loads(matches[0].read_text())
    require(job["candidate_id"] == ID and job["state"] == "running" and job["experiment"] == reference and job["execution_mode"] == "discovery", "job binding differs")
    require(all(job["resource_budget"].get(key) == value for key, value in CAPS.items()), "frozen resource caps differ")
    group = Path(job["execution_resources"]["cgroup_path"])
    membership = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
    require(group == Path("/sys/fs/cgroup" + membership) and group.stat().st_ino == job["execution_resources"]["cgroup_inode"], "cgroup identity differs")
    require((group / "memory.max").read_text().strip() == str(CAPS["memory_bytes"]) and
            (group / "memory.swap.max").read_text().strip() == "0", "cgroup memory/swap limits differ")
    # Execute the already verified helper bytes directly, avoiding stale pyc imports.
    helpers = {}
    sys.dont_write_bytecode = True
    helper_source = (ROOT / HELPERS).read_bytes()
    require(hashlib.sha256(helper_source).hexdigest() == inputs[HELPERS]["sha256"].removeprefix("sha256:"), "helper changed before import")
    exec(compile(helper_source, str(ROOT / HELPERS), "exec"), helpers)
    return inputs, reference, marker, group, helpers


class Gate:
    def __init__(self, inputs, marker, group, helpers, started):
        self.inputs, self.marker, self.group = inputs, marker, group
        self.artifact = lambda path: helpers["artifact_ref"](path, ROOT)
        self.write = helpers["atomic_write_json"]
        self.deadline, self.commands, self.binaries = started + 300, [], {}
        require(RESULT.is_dir() and not any(RESULT.iterdir()), "canonical executor must provide an empty result directory")
        self.work = RESULT / "work"
        (self.work / "tmp").mkdir(parents=True)
        self.env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(self.work / "tmp"), "PYTHONDONTWRITEBYTECODE": "1"}
        os.environ["TMPDIR"] = self.env["TMPDIR"]

    def closure(self):
        require({int(pid) for pid in (self.group / "cgroup.procs").read_text().split()} == {os.getpid()},
                "child closure incomplete; canonical outer guard must finish cleanup")

    def run(self, name, argv, cap, accepted=(0,), stdout=None):
        remaining = int(self.deadline - time.monotonic())
        require(remaining > 0 and cap > 0, "aggregate budget exhausted")
        cap = min(cap, remaining)
        if argv[0] in self.binaries:
            checked(Path(argv[0]), self.binaries[argv[0]])
        command = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=2", str(cap), *argv]
        with self.marker.open("a") as handle:
            handle.write(json.dumps({"phase": name, "event": "start"}) + "\n")
        begin, before = time.monotonic(), child_usage()
        output = stdout or RESULT / (name + ".stdout")
        with output.open("wb" if stdout else "xb") as out, (RESULT / (name + ".stderr")).open("xb") as err:
            completed = subprocess.run(command, cwd=self.work, env=self.env, stdout=out, stderr=err)
        after = child_usage()
        row = {"phase": name, "command": command, "returncode": completed.returncode, "stdout": str(output),
               "elapsed_seconds": time.monotonic() - begin, "elapsed_cap_seconds": cap,
               "user_cpu_seconds": after.ru_utime - before.ru_utime if before and after else None,
               "system_cpu_seconds": after.ru_stime - before.ru_stime if before and after else None,
               "missing_diagnostics": [] if before and after else ["optional child CPU telemetry unavailable"],
               "timing_authority": "shared-host diagnostic; outer guard closure still required"}
        self.write(RESULT / (name + ".execution.json"), row)
        self.commands.append(row)
        with self.marker.open("a") as handle:
            handle.write(json.dumps({"phase": name, "event": "end"}) + "\n")
        self.closure()
        require(completed.returncode in accepted, "phase failed or exhausted budget: " + name)
        if argv[0] in self.binaries:
            checked(Path(argv[0]), self.binaries[argv[0]])
        return completed.returncode

    def same(self, left, right):
        require(left.read_bytes() == right.read_bytes(), "exact bytes differ: " + left.name + " / " + right.name)

    def fixture(self, row):
        require(Path(row["path"]).name == row["path"], "fixture path escapes fixture directory")
        path = self.work / "fixtures" / row["path"]
        require(path.stat().st_size == row["bytes"], "fixture size changed")
        checked(path, row["sha256"])
        return path

    def native(self, phase, mode, source, output, cap, expected=None):
        self.run(phase, [str(self.work / "probe"), mode, str(source), str(output)], cap)
        row = json.loads((RESULT / (phase + ".stdout")).read_text())
        require(all(row.get(key) is True for key in ("original_stream_regeneration_ok", "inverse_ok", "repeat_ok")), "native proof fields missing")
        require(row["input_bytes"] == source.stat().st_size and row["output_bytes"] == output.stat().st_size, "native byte counts differ")
        if expected:
            require(len(row["tensors"]) == expected["tensor_count"] and all(row[key] == expected[key] for key in
                    ("tensor_payload_bytes", "regenerated_rope_bytes")), "native tensor counts differ")
        return row

    def execute(self):
        files = {PROBE: "probe.cpp", FIXTURES: "fixtures.py", UPSTREAM + "LICENSE": "LICENSE"}
        files.update({source: Path(source).name for source in CHECKER})
        for source, name in files.items():
            content = (ROOT / source).read_bytes()
            require(hashlib.sha256(content).hexdigest() == self.inputs[source]["sha256"].removeprefix("sha256:"),
                    "source changed before retention: " + source)
            with (self.work / name).open("xb") as handle:
                handle.write(content)
            (self.work / name).chmod(0o444)
        for source, name in files.items():
            checked(self.work / name, self.inputs[source]["sha256"])
        compile_start = time.monotonic()
        self.run("compile-probe", ["/usr/bin/g++", *FLAGS, "probe.cpp", "-o", "probe"], 120)
        self.run("compile-reference", ["/usr/bin/g++", *FLAGS, *[Path(p).name for p in CHECKER if p.endswith(".cpp")], "-o", "reference", "-lm"],
                 120 - int(time.monotonic() - compile_start))
        for name in ("probe", "reference"):
            path = self.work / name
            path.chmod(0o555)
            self.binaries[str(path)] = self.artifact(path)["sha256"]
        self.run("generate-fixtures", ["/usr/bin/python3", "fixtures.py", "--output-dir", "fixtures"], 15)
        manifest = json.loads((self.work / "fixtures/manifest.json").read_text())
        require(manifest["generator_sha256"] == self.inputs[FIXTURES]["sha256"].removeprefix("sha256:"), "fixture generator differs")
        require(len(manifest["valid"]) == 6, "synthetic population count differs")
        require(len(manifest["rejection"]) == 20 and {r["id"] for r in manifest["comparison_controls"]} ==
                {"missing_row_reset", "missing_tensor_reset", "bit_corruption"}, "negative population differs")
        for fixture in manifest["valid"]:
            label = fixture["id"]
            parent, golden, raw = [self.fixture(fixture[key]) for key in ("parent", "expected_treatment", "raw_reference")]
            self.run(label + "-reference", [str(self.work / "reference"), str(raw), str(parent)], 15)
            expected_line = f"OK: {fixture['tensor_count']} tensors, {fixture['tensor_payload_bytes'] + fixture['regenerated_rope_bytes']} payload bytes bit-identical\n"
            require((RESULT / (label + "-reference.stdout")).read_text() == expected_line, "upstream tensor comparison differs")
            for mode, source, expected, suffix in (("parent", parent, parent, "parent"), ("pack", parent, golden, "pack"),
                                                   ("unpack", golden, parent, "unpack"), ("pack", parent, golden, "repack")):
                output = self.work / (label + "." + suffix)
                self.native(label + "-" + suffix, mode, source, output, 15, fixture)
                self.same(output, expected)
        for fixture in manifest["rejection"]:
            output = self.work / (fixture["id"] + ".rejected")
            self.run(fixture["id"], [str(self.work / "probe"), "parent", str(self.fixture(fixture["input"])), str(output)], 15, (1,))
            require(not output.exists() and not Path(str(output) + ".partial").exists(), "rejected input published output or left scratch")
        original = self.fixture(next(row for row in manifest["valid"] if row["id"] == "all_tags_and_rows")["parent"])
        for control in manifest["comparison_controls"]:
            source = self.fixture(control["input"])
            if control["id"] == "bit_corruption":
                rejected = False
                try: checked(source, control["expected_parent_sha256"])
                except ValueError: rejected = True
                require(rejected, "corrupted input identity was admitted")
                continue
            output = self.work / (control["id"] + ".restored")
            code = self.run(control["id"], [str(self.work / "probe"), "unpack", str(source), str(output)], 15, (0, 1))
            require((code == 1 and not output.exists()) or (code == 0 and output.read_bytes() != original.read_bytes()), "reset control restored the original")
            require(not Path(str(output) + ".partial").exists(), "reset control left temporary output")
        sentinel = self.work / "preexisting"
        sentinel.write_bytes(b"preserve-existing-output\n")
        self.run("preexisting-output", [str(self.work / "probe"), "parent", str(original), str(sentinel)], 15, (1,))
        require(sentinel.read_bytes() == b"preserve-existing-output\n" and not Path(str(sentinel) + ".partial").exists(), "preexisting output changed")
        require("output publication failed" in (RESULT / "preexisting-output.stderr").read_text(), "preexisting-output control failed elsewhere")
        self.run("receipt-write-failure", [str(self.work / "probe"), "parent", str(original), str(self.work / "receipt-failure-model")], 15, (1,), Path("/dev/full"))
        require("receipt stdout flush failed" in (RESULT / "receipt-write-failure.stderr").read_text(), "stdout control failed elsewhere")
        self.same(self.work / "receipt-failure-model", original)
        synthetic = {"status": "passed", "valid_populations": 6, "rejection_cases": len(manifest["rejection"]),
                     "comparison_controls": len(manifest["comparison_controls"]), "upstream_raw_tensor_comparison": True,
                     "preexisting_output_preserved": True, "stdout_failure_detected": True, "corrupted_hash_admission_rejected": True}
        self.write(RESULT / "synthetic.json", synthetic)
        checked(ROOT / MODEL, MODEL_SHA)
        outputs = {name: self.work / ("model." + name) for name in ("parent", "packed", "restored", "repeat")}
        model_row = None
        for name, mode, source in (("parent", "parent", ROOT / MODEL), ("packed", "pack", ROOT / MODEL),
                                   ("restored", "unpack", outputs["packed"]), ("repeat", "pack", ROOT / MODEL)):
            checked(ROOT / MODEL, MODEL_SHA)
            row = self.native("model-" + name, mode, source, outputs[name], 45)
            require(len(row["tensors"]) == 434, "confirmation tensor count differs")
            if name == "packed": model_row = row
        self.same(outputs["parent"], ROOT / MODEL); self.same(outputs["restored"], ROOT / MODEL)
        self.same(outputs["packed"], outputs["repeat"])
        for source in files:
            checked(ROOT / source, self.inputs[source]["sha256"])
            checked(self.work / files[source], self.inputs[source]["sha256"])
        for source, reference in self.inputs.items():
            checked(ROOT / source, reference["sha256"])
        packed_bytes = outputs["packed"].stat().st_size
        options = "pack input.tfwc2 packed.model\nunpack packed.model output.tfwc2\n"
        package = {"runtime_members": [self.artifact(self.work / "probe"), self.artifact(outputs["packed"])],
                   "source_members": [self.artifact(self.work / "probe.cpp"), self.artifact(self.work / "LICENSE"), self.artifact(outputs["packed"])],
                   "option_text": options, "option_bytes": len(options.encode()), "source_package_archive_bytes": None,
                   "complete_submission_package": False, "full_corpus_score_bytes": None,
                   "two_copy_model_component_savings_bytes": 2 * (2930652 - packed_bytes),
                   "per_copy_model_component_savings_bytes": 2930652 - packed_bytes, "full_scored_gain_bytes": None,
                   "accounting_boundary": "Runtime/source are alternative incomplete inventories. Component arithmetic is not a scored gain; fresh native archives and complete loader/dependency/option accounting remain required.",
                   "unresolved": ["native loader integration", "transitive runtime dependency closure", "counted package form and options", "model licensing"],
                   "attribution": "Upstream model/parent coder; Gamma tensor/row-context packing; no corpus compression credit"}
        package["listed_runtime_bytes"] = sum(row["bytes"] for row in package["runtime_members"])
        package["listed_source_bytes"] = sum(row["bytes"] for row in package["source_members"])
        self.write(RESULT / "package.json", package)
        self.write(RESULT / "artifacts.json", [self.artifact(path) for path in sorted(RESULT.rglob("*")) if path.is_file()])
        return {"synthetic": synthetic, "model": model_row, "model_archive_saved_bytes": 2930652 - packed_bytes,
                "package": self.artifact(RESULT / "package.json"), "roundtrip_ok": True, "deterministic_ok": True}


def main():
    if sys.argv[1:] == ["--validate-only"]:
        print(json.dumps(bootstrap(True), indent=2))
        return 0
    require(len(sys.argv) == 1, "only --validate-only is accepted outside canonical execution")
    started = time.monotonic()
    inputs, reference, marker, group, helpers = bootstrap()
    gate = Gate(inputs, marker, group, helpers, started)
    stage = {"schema": "gamma.enwiki9.fx2-weight-pack-stage.v1", "candidate_id": ID, "experiment": reference,
             "objective_credit_bytes": 0, "full_corpus_score_bytes": None, "larger_gate_authorized": False,
             "continuous_guard_decision": "pending canonical outer guard closure", "confirmation": "one fixed public model; no parameter selection"}
    try:
        stage.update(gate.execute(), status="passed")
    except Exception as error:
        stage.update(status="execution_failed", error=type(error).__name__ + ": " + str(error))
    gate.closure()
    stage["commands"] = gate.commands
    gate.write(RESULT / "stage-decision.json", stage)
    return 0 if stage["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
