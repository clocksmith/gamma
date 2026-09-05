#!/usr/bin/env python3
"""Prospective guarded P/K/D/G weight gate; no launch authority or full score."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ID = "fx2_weight_marginal_roundtrip_q0_v1"
RESULT = ROOT / "results" / ID
CONTRACT = "operations/adaptive/experiments/" + ID + ".json"
UPSTREAM = "external/fx2-cmix-transformer-v1/"
MODEL = UPSTREAM + "models/6m-q4-fp32.tfwc2"
MODEL_SHA = "7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860"
MODEL_BYTES = 2930652
MODEL_COUNTS = {"tensor_count": 434, "tensor_payload_bytes": 6034374,
                "regenerated_rope_bytes": 33554432}
MODEL_METADATA = "results/fx2_weight_pack_roundtrip_q0_v1/model-parent.stdout"
TOOLCHAIN = "operations/provenance/public_fx2_gcc15_toolchain_20260905.json"
PROBE = "tools/fx2_weight_marginal_probe_v1.cpp"
HEADER = "lib/fx2_weight_format_v1.hpp"
FIXTURES = "tools/fx2_weight_marginal_fixtures_v1.py"
HELPERS = "lib/artifacts.py"
CHECKER = [UPSTREAM + "cpp_infer/src/" + name for name in
           ("test_weights_compressed.cpp", "weights_io.cpp", "weights_io_compressed.cpp", "weights_io.h")]
FLAGS = ["-std=c++17", "-O2", "-Wall", "-Wextra", "-fno-fast-math", "-ffp-contract=off",
         "-fno-math-errno", "-march=x86-64-v3", "-mtune=generic", "-mrecip=none"]
CAPS = {"cpus": [2], "memory_bytes": 512 << 20, "scratch_bytes": 64 << 20,
        "swap_bytes": 0, "wall_seconds": 300}
VALID_POPULATIONS = {"zero_tensors", "uniform_marginal", "skewed_marginal", "heterogeneous_tensors",
                     "empty_and_scalar", "all_tags_and_rows", "range_adaptation_stress", "maximum_native_dimensions"}
TENSOR_FIELDS = ("name", "dtype", "encoding", "elements", "represented_bytes", "stored_payload_bytes", "row_width")


class GateFailure(ValueError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "missing/aliased frozen input: " + str(path))
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    require(digest == expected.removeprefix("sha256:"), "frozen input changed: " + str(path))
    return digest


def bound_bytes(path, reference):
    require(path.is_file() and not path.is_symlink(), "missing/aliased frozen input: " + str(path))
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        content = handle.read()
        after = os.fstat(handle.fileno())
    signature = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    require(signature(before) == signature(after) == signature(path.stat()), "input changed while reading: " + str(path))
    require(hashlib.sha256(content).hexdigest() == reference["sha256"].removeprefix("sha256:"),
            "frozen input changed: " + str(path))
    require("bytes" not in reference or len(content) == reference["bytes"], "frozen input size changed: " + str(path))
    return content


def child_usage():
    try:
        return resource.getrusage(resource.RUSAGE_CHILDREN)
    except OSError:
        return None


def bootstrap(validate_only=False):
    contract_bytes = (ROOT / CONTRACT).read_bytes()
    reference = ({"path": CONTRACT, "sha256": hashlib.sha256(contract_bytes).hexdigest()}
                 if validate_only else json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]))
    require(reference["path"] == CONTRACT, "unexpected bound experiment")
    require(hashlib.sha256(contract_bytes).hexdigest() == reference["sha256"].removeprefix("sha256:"),
            "bound experiment changed")
    contract = json.loads(contract_bytes)
    require(contract["experimentId"] == ID and contract["status"] == "frozen", "experiment is not frozen for this gate")
    inputs = {row["path"]: row for row in contract["inputs"]}
    require(len(inputs) == len(contract["inputs"]), "duplicate frozen input paths")
    required = {"tools/" + ID + ".py", PROBE, HEADER, FIXTURES, HELPERS, TOOLCHAIN, MODEL, MODEL_METADATA,
                UPSTREAM + "LICENSE", UPSTREAM + "pysrc/weights_compress.py", *CHECKER}
    require(required <= inputs.keys(), "incomplete frozen source/asset closure")
    buffers = {}
    for name, row in inputs.items():
        path = ROOT / name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and path.resolve() == path,
                "frozen input path escapes or aliases the project")
        buffers[name] = bound_bytes(path, row)
    require(len(buffers[MODEL]) == MODEL_BYTES and hashlib.sha256(buffers[MODEL]).hexdigest() == MODEL_SHA,
            "fixed model identity differs")
    toolchain = json.loads(buffers[TOOLCHAIN])
    for row in toolchain["toolchain"]:
        require(Path(row["path"]).stat().st_size == row["bytes"], "toolchain byte count changed")
        checked(Path(row["path"]), row["sha256"])
    paths = {row["name"]: Path(row["path"]) for row in toolchain["toolchain"]}
    for name in ("g++", "python3", "timeout"):
        require(Path("/usr/bin/" + name).resolve() == paths[name], "toolchain executable redirected")
    for source in ("tools/" + ID + ".py", FIXTURES, HELPERS):
        tree = ast.parse(buffers[source], filename=source)
        names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names.update(node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module)
        require(names <= sys.stdlib_module_names, "unexpected non-standard Python dependency")
    # Preserve project-relative paths in retention. Normalize ../lib/header.hpp
    # before checking the exact frozen closure; never flatten include paths.
    for source in inputs:
        if Path(source).suffix not in (".cpp", ".h", ".hpp"):
            continue
        for include in re.findall(r'^\s*#\s*include\s+"([^"\n]+)"', buffers[source].decode(), re.M):
            require(not Path(include).is_absolute(), "absolute local C++ include")
            target = os.path.normpath(str(Path(source).parent / include))
            require(target in inputs and ".." not in Path(target).parts, "unbound local C++ include: " + target)
    if validate_only:
        return {"status": "preflight_pass", "candidate_id": ID, "validated_input_count": len(inputs),
                "toolchain_verified": True, "static_source_references_verified": True, "model_decoded": False,
                "model_bytes": MODEL_BYTES, "execution_authorized": False, "contract": reference}
    require(os.sched_getaffinity(0) == {2}, "canonical guard must assign CPU 2")
    marker = Path(os.environ["GAMMA_RESOURCE_PHASE_MARKERS"])
    job_id = marker.parent.name.removesuffix(".resources")
    require(bool(job_id) and marker == ROOT / "run_logs/adaptive" / (job_id + ".resources/phases.jsonl"),
            "unexpected phase-marker owner")
    require(marker.is_file() and marker.resolve() == marker, "phase-marker file is missing or aliased")
    matches = list((ROOT / "operations/adaptive/running").glob("*" + job_id + ".json"))
    require(len(matches) == 1, "canonical running job is missing or ambiguous")
    job = json.loads(matches[0].read_text())
    require(job["job_id"] == job_id and job["candidate_id"] == ID and job["state"] == "running"
            and job["experiment"] == reference and job["execution_mode"] == "discovery", "job binding differs")
    require(all(job["resource_budget"].get(key) == value for key, value in CAPS.items()), "frozen resource caps differ")
    group = Path(job["execution_resources"]["cgroup_path"])
    membership = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
    require(group == Path("/sys/fs/cgroup" + membership) and group.stat().st_ino == job["execution_resources"]["cgroup_inode"],
            "cgroup identity differs")
    require((group / "memory.max").read_text().strip() == str(CAPS["memory_bytes"])
            and (group / "memory.swap.max").read_text().strip() == "0", "cgroup memory/swap limits differ")
    helpers = {}
    sys.dont_write_bytecode = True
    exec(compile(buffers[HELPERS], str(ROOT / HELPERS), "exec"), helpers)
    return inputs, buffers, reference, marker, group, helpers, toolchain


class Gate:
    def __init__(self, inputs, buffers, marker, group, helpers, toolchain, started):
        self.inputs, self.buffers, self.marker, self.group = inputs, buffers, marker, group
        self.toolchain = toolchain
        self.artifact = lambda path: helpers["artifact_ref"](path, ROOT)
        self.write = helpers["atomic_write_json"]
        self.deadline, self.commands, self.binaries = started + CAPS["wall_seconds"], [], {}
        require(RESULT.is_dir() and RESULT.resolve() == RESULT and not any(RESULT.iterdir()),
                "canonical executor must provide an empty result directory")
        self.work = RESULT / "work"
        (self.work / "tmp").mkdir(parents=True)
        self.retained = {}
        self.env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(self.work / "tmp"), "PYTHONDONTWRITEBYTECODE": "1"}
        os.environ["TMPDIR"] = self.env["TMPDIR"]

    def closure(self):
        require({int(pid) for pid in (self.group / "cgroup.procs").read_text().split()} == {os.getpid()},
                "child closure incomplete; canonical outer guard must finish cleanup")

    def run(self, name, argv, cap, accepted=(0,), stdout=None):
        require(re.fullmatch(r"[A-Za-z0-9_-]+", name) is not None, "invalid phase name")
        require(all(row["phase"] != name for row in self.commands), "duplicate phase name")
        remaining = int(self.deadline - time.monotonic())
        if remaining <= 0 or cap <= 0:
            raise GateFailure("budget_exhausted", "aggregate or compile budget exhausted before " + name)
        cap = min(cap, remaining)
        if argv[0] in self.binaries:
            checked(Path(argv[0]), self.binaries[argv[0]])
        command = ["/usr/bin/timeout", "--signal=TERM", "--kill-after=2", str(cap), *argv]
        with self.marker.open("a") as handle:
            handle.write(json.dumps({"phase": name, "event": "start"}) + "\n")
        begin, before = time.monotonic(), child_usage()
        output = stdout or RESULT / (name + ".stdout")
        returncode, launch_error = None, None
        try:
            with output.open("wb" if stdout else "xb") as out, (RESULT / (name + ".stderr")).open("xb") as err:
                returncode = subprocess.run(command, cwd=self.work, env=self.env, stdout=out, stderr=err).returncode
        except OSError as error:
            launch_error = type(error).__name__ + ": " + str(error)
        after = child_usage()
        row = {"phase": name, "command": command, "returncode": returncode, "stdout": str(output),
               "elapsed_seconds": time.monotonic() - begin, "elapsed_cap_seconds": cap,
               "user_cpu_seconds": after.ru_utime - before.ru_utime if before and after else None,
               "system_cpu_seconds": after.ru_stime - before.ru_stime if before and after else None,
               "missing_diagnostics": [] if before and after else ["optional child CPU telemetry unavailable"],
               "timing_authority": "shared-host diagnostic; outer guard closure still required"}
        if launch_error is not None:
            row["launch_error"] = launch_error
        self.write(RESULT / (name + ".execution.json"), row)
        self.commands.append(row)
        with self.marker.open("a") as handle:
            handle.write(json.dumps({"phase": name, "event": "end"}) + "\n")
        self.closure()
        if launch_error is not None or returncode not in accepted:
            category = ("budget_exhausted" if returncode == 124 else
                        "resource_or_signal_stop" if returncode == 137 else "execution_failed")
            raise GateFailure(category, "phase failed: " + name)
        if argv[0] in self.binaries:
            checked(Path(argv[0]), self.binaries[argv[0]])
        return returncode

    def same(self, left, right):
        require(left.read_bytes() == right.read_bytes(), "exact bytes differ: " + left.name + " / " + right.name)

    def fixture(self, row):
        require(Path(row["path"]).name == row["path"], "fixture path escapes fixture directory")
        path = self.work / "fixtures" / row["path"]
        require(path.stat().st_size == row["bytes"], "fixture size changed")
        checked(path, row["sha256"])
        return path

    def retain_sources(self):
        for source in self.inputs:
            if Path(source).suffix not in (".py", ".cpp", ".h", ".hpp") and source != UPSTREAM + "LICENSE":
                continue
            content = self.buffers[source]
            require(hashlib.sha256(content).hexdigest() == self.inputs[source]["sha256"].removeprefix("sha256:"),
                    "verified source buffer differs: " + source)
            path = self.work / "source" / source
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(content)
            path.chmod(0o444)
            self.retained[source] = path
        self.verify_sources()

    def verify_sources(self):
        for source, reference in self.inputs.items():
            checked(ROOT / source, reference["sha256"])
        for source, path in self.retained.items():
            checked(path, self.inputs[source]["sha256"])
        for row in self.toolchain["toolchain"]:
            require(Path(row["path"]).stat().st_size == row["bytes"], "toolchain byte count changed")
            checked(Path(row["path"]), row["sha256"])
        paths = {row["name"]: Path(row["path"]) for row in self.toolchain["toolchain"]}
        for name in ("g++", "python3", "timeout"):
            require(Path("/usr/bin/" + name).resolve() == paths[name], "toolchain executable redirected")

    def envelope(self, path, expected_format, tensors):
        data = path.read_bytes()
        require(len(data) >= 17, "missing model header/range flush")
        count = int.from_bytes(data[8:12], "little")
        require(count == len(tensors), "model header tensor count differs")
        if expected_format == "FX2TFWC2":
            require(data[:8] == b"FX2TFWC2" and data[12] == 0, "parent format differs")
            return 12
        require(expected_format in ("GFX2MAR1-D", "GFX2MAR1-G"), "unexpected model format")
        require(data[:8] == b"GFX2MAR1" and data[12] == (1 if expected_format.endswith("D") else 2),
                "marginal format differs")
        indices = [index for index, tensor in enumerate(tensors) if tensor["encoding"] == 1]
        require(int.from_bytes(data[13:17], "little") == len(indices), "marginal record count differs")
        offset = 77 + 64 * len(indices)
        require(len(data) >= offset + 5 and data[offset] == 0, "marginal header/range flush differs")
        global_counts = [int.from_bytes(data[17 + 4 * k:21 + 4 * k], "little") for k in range(15)]
        totals = [0] * 15
        for number, index in enumerate(indices):
            start = 77 + 64 * number
            require(int.from_bytes(data[start:start + 4], "little") == index, "marginal tensor index differs")
            local = [int.from_bytes(data[start + 4 + 4 * k:start + 8 + 4 * k], "little") for k in range(15)]
            require(sum(local) == tensors[index]["elements"], "marginal local histogram size differs")
            totals = [a + b for a, b in zip(totals, local)]
        require(totals == global_counts, "marginal global histogram differs from local sums")
        return offset

    def native(self, phase, mode, source, output, cap, expected, source_format="FX2TFWC2"):
        self.run(phase, [str(self.work / "probe"), mode, str(source), str(output)], cap)
        row = json.loads((RESULT / (phase + ".stdout")).read_text())
        output_format = "GFX2MAR1-" + mode if mode in ("D", "G") else "FX2TFWC2"
        require(row.get("schema") == "gamma.fx2-weight-marginal-probe.v1" and row.get("mode") == mode,
                "native receipt schema/mode differs")
        require(row.get("input_format") == source_format and row.get("output_format") == output_format,
                "native receipt format differs")
        require(all(row.get(key) is True for key in ("original_stream_regeneration_ok", "inverse_ok", "repeat_ok")),
                "native proof fields missing")
        require(row.get("objective_credit_bytes") == 0, "native receipt claims objective credit")
        require(row["input_bytes"] == source.stat().st_size and row["output_bytes"] == output.stat().st_size,
                "native byte counts differ")
        tensors = row["tensors"]
        require(isinstance(tensors, list) and len(tensors) == expected["tensor_count"], "native tensor count differs")
        require(all(row[key] == expected[key] for key in ("tensor_payload_bytes", "regenerated_rope_bytes")),
                "native tensor payload totals differ")
        names, payload_bytes, rope_bytes, int4_count = set(), 0, 0, 0
        for tensor in tensors:
            require(set(tensor) == {*TENSOR_FIELDS, "shape"}, "unexpected tensor metadata fields")
            require(isinstance(tensor["name"], str) and tensor["name"] not in names, "duplicate tensor name")
            names.add(tensor["name"])
            shape = tensor["shape"]
            require(isinstance(shape, list) and len(shape) <= 8 and all(type(n) is int and n >= 0 for n in shape),
                    "invalid tensor shape")
            elements = 1
            for n in shape:
                elements *= n
            require(tensor["elements"] == elements and tensor["row_width"] == (shape[-1] if shape else 1),
                    "tensor shape and element count differ")
            require(tensor["dtype"] in (0, 1, 2, 3) and tensor["encoding"] in range(6), "invalid tensor type/encoding")
            represented = elements * (1 if tensor["dtype"] == 0 else 2 if tensor["dtype"] == 1 else 4)
            generated = tensor["encoding"] in (4, 5)
            require(tensor["represented_bytes"] == represented and tensor["stored_payload_bytes"] == (0 if generated else represented),
                    "tensor represented/stored bytes differ")
            payload_bytes += tensor["stored_payload_bytes"]
            rope_bytes += represented if generated else 0
            int4_count += tensor["encoding"] == 1
        require(payload_bytes == row["tensor_payload_bytes"] and rope_bytes == row["regenerated_rope_bytes"],
                "tensor rows do not sum to receipt totals")
        if "int4_tensor_count" in expected:
            require(int4_count == expected["int4_tensor_count"], "INT4 tensor population differs")
        if "tensors" in expected:
            require([{key: tensor[key] for key in TENSOR_FIELDS} for tensor in tensors]
                    == [{key: tensor[key] for key in TENSOR_FIELDS} for tensor in expected["tensors"]],
                    "tensor metadata differs from bound original receipt")
        require(row["bookkeeping_int4_tensors"] == (int4_count if mode in ("K", "D", "G") else 0),
                "bookkeeping arm activation differs")
        self.envelope(source, source_format, tensors)
        header_bytes = self.envelope(output, output_format, tensors)
        require(row["header_bytes"] == header_bytes and row["side_information_bytes"] == header_bytes - 12,
                "native header/side-information accounting differs")
        require(not Path(str(output) + ".partial").exists(), "native output left partial scratch")
        return row

    def compare_metadata(self, rows):
        require(all(row["tensors"] == rows[0]["tensors"] for row in rows), "tensor metadata differs between arms or repeats")

    def compare_side_information(self, d_path, g_path, offset):
        d, g = d_path.read_bytes(), g_path.read_bytes()
        require(d[:12] == g[:12] and d[13:offset] == g[13:offset], "D/G side information differs beyond mode")

    def synthetic(self):
        self.run("generate-fixtures", ["/usr/bin/python3", str(self.retained[FIXTURES]), "--output-dir", "fixtures"], 15)
        manifest = json.loads((self.work / "fixtures/manifest.json").read_text())
        require(manifest["schema"] == "gamma.fx2-weight-marginal-synthetic-fixtures.v1"
                and manifest["generator_sha256"] == self.inputs[FIXTURES]["sha256"].removeprefix("sha256:"),
                "fixture generator/schema differs")
        require(manifest["real_model_accessed"] is False and manifest["objective_credit_bytes"] == 0, "fixture scope differs")
        require(len(manifest["valid"]) == 8 and {row["id"] for row in manifest["valid"]} == VALID_POPULATIONS,
                "synthetic population differs")
        require(len(manifest["rejection"]) == 40 and len({row["id"] for row in manifest["rejection"]}) == 40,
                "negative population differs")
        require(len(manifest["comparison_controls"]) == 3 and {row["id"] for row in manifest["comparison_controls"]}
                == {"wrong_model_D", "wrong_model_G", "bit_corruption"}, "comparison population differs")
        require(len(manifest["output_controls"]) == 4 and {row["id"] for row in manifest["output_controls"]}
                == {"preexisting_output", "preexisting_partial", "missing_output_directory", "stdout_failure"},
                "output control population differs")
        for fixture in manifest["valid"]:
            label = fixture["id"]
            parent, raw = self.fixture(fixture["parent"]), self.fixture(fixture["raw_reference"])
            goldens = {arm: self.fixture(fixture["expected_" + arm]) for arm in ("D", "G")}
            require(fixture["P_K_bytes_identical"] is True and fixture["D_G_side_information_identical_except_mode"] is True,
                    "fixture identity predicates differ")
            offset = 77 + 64 * fixture["int4_tensor_count"]
            require(fixture["range_stream_offset"] == offset and fixture["side_information_bytes"] == offset - 12,
                    "fixture side-information count differs")
            self.run(label + "-reference", [str(self.work / "reference"), str(raw), str(parent)], 15)
            expected_line = f"OK: {fixture['tensor_count']} tensors, {fixture['tensor_payload_bytes'] + fixture['regenerated_rope_bytes']} payload bytes bit-identical\n"
            require((RESULT / (label + "-reference.stdout")).read_text() == expected_line, "upstream tensor comparison differs")
            rows, outputs = [], {}
            for arm in ("P", "K", "D", "G"):
                output = self.work / (label + "." + arm)
                rows.append(self.native(label + "-" + arm, arm, parent, output, 15, fixture))
                outputs[arm] = output
                self.same(output, parent if arm in ("P", "K") else goldens[arm])
                if arm in ("D", "G"):
                    restored, repeat = self.work / (label + "." + arm + ".restored"), self.work / (label + "." + arm + ".repeat")
                    rows.append(self.native(label + "-" + arm + "-restore", "restore", output, restored, 15, fixture, "GFX2MAR1-" + arm))
                    rows.append(self.native(label + "-" + arm + "-repeat", arm, parent, repeat, 15, fixture))
                    self.same(restored, parent)
                    self.same(repeat, goldens[arm])
            self.same(outputs["P"], outputs["K"])
            self.compare_metadata(rows)
            self.compare_side_information(outputs["D"], outputs["G"], offset)
            if label == "heterogeneous_tensors":
                require(outputs["D"].read_bytes()[offset:] != outputs["G"].read_bytes()[offset:],
                        "heterogeneous control does not distinguish D/G range streams")
        for fixture in manifest["rejection"]:
            require(fixture["mode"] in ("P", "restore") and fixture["expected_exit"] == 1
                    and fixture["output_must_be_absent"] is True and fixture["partial_must_be_absent"] is True,
                    "negative-case predicate differs")
            output = self.work / (fixture["id"] + ".rejected")
            self.run(fixture["id"], [str(self.work / "probe"), fixture["mode"], str(self.fixture(fixture["input"])), str(output)], 15, (1,))
            require(not output.exists() and not Path(str(output) + ".partial").exists(), "rejected input published output or left scratch")
        for control in manifest["comparison_controls"]:
            source = self.fixture(control["input"])
            if control["id"] == "bit_corruption":
                require(control["mode"] == "hash_admission", "corruption control mode differs")
                require(hashlib.sha256(source.read_bytes()).hexdigest() != control["expected_parent_sha256"],
                        "corrupted input identity was admitted")
                continue
            require(control["mode"] == "restore", "wrong-model control mode differs")
            output = self.work / (control["id"] + ".restored")
            code = self.run(control["id"], [str(self.work / "probe"), "restore", str(source), str(output)], 15, (0, 1))
            require((code == 1 and not output.exists()) or
                    (code == 0 and hashlib.sha256(output.read_bytes()).hexdigest() != control["expected_parent_sha256"]),
                    "wrong-model control restored the original")
            require(not Path(str(output) + ".partial").exists(), "wrong-model control left temporary output")
        for control in manifest["output_controls"]:
            require(control["mode"] == "P" and control["expected_exit"] == 1, "output-control predicate differs")
            name, source = control["id"], self.fixture(control["input"])
            sentinel = self.fixture(control["sentinel"]).read_bytes()
            output = self.work / (name + ".model")
            partial = Path(str(output) + ".partial")
            if name == "preexisting_output":
                with output.open("xb") as handle:
                    handle.write(sentinel)
            elif name == "preexisting_partial":
                with partial.open("xb") as handle:
                    handle.write(sentinel)
            elif name == "missing_output_directory":
                output = self.work / "missing-output-directory" / "model"
                partial = Path(str(output) + ".partial")
                require(not output.parent.exists(), "missing-directory control already exists")
            self.run(name, [str(self.work / "probe"), "P", str(source), str(output)], 15, (1,),
                     Path("/dev/full") if name == "stdout_failure" else None)
            error = (RESULT / (name + ".stderr")).read_text()
            if name == "preexisting_output":
                require(output.read_bytes() == sentinel and not partial.exists()
                        and "output publication failed" in error, "preexisting output control failed")
            elif name == "preexisting_partial":
                require(not output.exists() and partial.read_bytes() == sentinel
                        and "temporary output exists or cannot be created exclusively" in error, "preexisting partial control failed")
            elif name == "missing_output_directory":
                require(not output.parent.exists() and not output.exists() and not partial.exists()
                        and "temporary output exists or cannot be created exclusively" in error, "missing output directory control failed")
            else:
                require("receipt stdout flush failed" in error and not partial.exists(), "stdout control failed elsewhere")
                self.same(output, source)
        result = {"status": "passed", "valid_populations": 8, "rejection_cases": 40, "comparison_controls": 3,
                  "output_controls": 4, "upstream_raw_tensor_comparison": True, "pk_identity": True,
                  "D_G_independent_goldens": True, "D_G_restore_and_repeat": True,
                  "D_G_side_information_identical_except_mode": True, "heterogeneous_D_G_streams_differ": True,
                  "corrupted_hash_admission_rejected": True, "stdout_failure_detected": True,
                  "preexisting_output_and_partial_preserved": True, "missing_output_directory_rejected": True,
                  "fixture_manifest": self.artifact(self.work / "fixtures/manifest.json")}
        self.write(RESULT / "synthetic.json", result)
        return result

    def package(self, outputs, controls):
        arms = {}
        for arm in ("D", "G"):
            options = f"{arm} input.tfwc2 packed.model\nrestore packed.model output.tfwc2\n"
            runtime = [self.artifact(self.work / "probe"), self.artifact(self.retained[UPSTREAM + "LICENSE"]), self.artifact(outputs[arm])]
            source = [self.artifact(self.retained[name]) for name in (PROBE, HEADER, UPSTREAM + "LICENSE")]
            source.append(self.artifact(outputs[arm]))
            runtime_bytes, source_bytes = sum(row["bytes"] for row in runtime), sum(row["bytes"] for row in source)
            option_bytes = len(options.encode("utf-8"))
            arms[arm] = {"runtime_members": runtime, "source_members": source, "option_text": options,
                         "option_bytes": option_bytes, "listed_runtime_member_bytes": runtime_bytes,
                         "listed_source_member_bytes": source_bytes,
                         "listed_runtime_with_options_bytes": runtime_bytes + option_bytes,
                         "listed_source_with_options_bytes": source_bytes + option_bytes,
                         "parent_model_bytes": MODEL_BYTES, "packed_model_bytes": outputs[arm].stat().st_size,
                         "per_copy_model_component_savings_bytes": MODEL_BYTES - outputs[arm].stat().st_size,
                         "standalone_runtime_delta_vs_original_model_bytes": runtime_bytes + option_bytes - MODEL_BYTES,
                         "standalone_source_delta_vs_original_model_bytes": source_bytes + option_bytes - MODEL_BYTES,
                         "side_information_embedded_bytes": controls[arm]["side_information_bytes"],
                         "side_information_already_in_packed_model": True,
                         "source_package_archive_bytes": None, "full_scored_gain_bytes": None}
        package = {"arms": arms, "complete_submission_package": False, "full_corpus_score_bytes": None,
                   "full_scored_gain_bytes": None,
                   "accounting_boundary": "D/G are separate alternatives. Runtime/source inventories include the new executable or probe/header source, license, packed model (including every histogram byte), and explicit options. Deltas compare these incomplete standalone inventories with the original model alone; they are not integrated package gains or a summed prize gain.",
                   "unresolved": ["native loader integration", "transitive runtime dependency closure", "counted package form and options", "model licensing"],
                   "attribution": "Upstream model/parent coder; Gamma fixed marginal INT4 coding and explicit histograms; no corpus compression credit"}
        self.write(RESULT / "package.json", package)
        return self.artifact(RESULT / "package.json")

    def execute(self):
        self.retain_sources()
        compile_start = time.monotonic()
        self.run("compile-probe", ["/usr/bin/g++", *FLAGS, str(self.retained[PROBE]), "-o", "probe"], 120)
        self.run("compile-reference", ["/usr/bin/g++", *FLAGS, *[str(self.retained[p]) for p in CHECKER if p.endswith(".cpp")], "-o", "reference", "-lm"],
                 120 - int(time.monotonic() - compile_start))
        for name in ("probe", "reference"):
            path = self.work / name
            path.chmod(0o555)
            self.binaries[str(path)] = self.artifact(path)["sha256"]
        synthetic = self.synthetic()
        self.verify_sources()
        prior = json.loads(self.buffers[MODEL_METADATA])
        require(prior["schema"] == "gamma.fx2-weight-pack-probe.v1" and prior["mode"] == "parent"
                and prior["input_bytes"] == MODEL_BYTES and prior["output_bytes"] == MODEL_BYTES,
                "bound model metadata reference differs")
        require(all(prior.get(key) is True for key in ("original_stream_regeneration_ok", "inverse_ok", "repeat_ok")),
                "bound model metadata proof is incomplete")
        expected = {**MODEL_COUNTS, "tensors": prior["tensors"]}
        require(len(prior["tensors"]) == MODEL_COUNTS["tensor_count"] and all(prior[key] == MODEL_COUNTS[key]
                for key in ("tensor_payload_bytes", "regenerated_rope_bytes")), "bound model metadata totals differ")
        outputs, controls, rows = {}, {}, []
        for arm in ("P", "K", "D", "G"):
            checked(ROOT / MODEL, MODEL_SHA)
            output = self.work / ("model." + arm)
            row = self.native("model-" + arm, arm, ROOT / MODEL, output, 45, expected)
            rows.append(row)
            controls[arm], outputs[arm] = row, output
            if arm in ("P", "K"):
                self.same(output, ROOT / MODEL)
            else:
                for suffix, mode, source, source_format in (("restored", "restore", output, "GFX2MAR1-" + arm),
                                                             ("repeat", arm, ROOT / MODEL, "FX2TFWC2")):
                    checked(ROOT / MODEL, MODEL_SHA)
                    path = self.work / ("model." + arm + "." + suffix)
                    rows.append(self.native("model-" + arm + "-" + suffix, mode, source, path, 45, expected, source_format))
                    self.same(path, ROOT / MODEL if suffix == "restored" else output)
                    outputs[arm + "_" + suffix] = path
        self.same(outputs["P"], outputs["K"])
        self.compare_metadata(rows)
        require(controls["D"]["header_bytes"] == controls["G"]["header_bytes"], "D/G header sizes differ")
        self.compare_side_information(outputs["D"], outputs["G"], controls["D"]["header_bytes"])
        self.verify_sources()
        package = self.package(outputs, controls)
        return {"synthetic": synthetic, "controls": controls, "model_artifacts": {name: self.artifact(path) for name, path in outputs.items()},
                "model_saved_bytes": {arm: MODEL_BYTES - outputs[arm].stat().st_size for arm in ("D", "G")},
                "roundtrip_ok": True, "deterministic_ok": True, "pk_identity": True,
                "metadata_reference": self.inputs[MODEL_METADATA], "package": package}


def main():
    if sys.argv[1:] == ["--validate-only"]:
        print(json.dumps(bootstrap(True), indent=2))
        return 0
    require(len(sys.argv) == 1, "only --validate-only is accepted outside canonical execution")
    started = time.monotonic()
    inputs, buffers, reference, marker, group, helpers, toolchain = bootstrap()
    gate = Gate(inputs, buffers, marker, group, helpers, toolchain, started)
    stage = {"schema": "gamma.enwiki9.fx2-weight-marginal-stage.v1", "candidate_id": ID, "experiment": reference,
             "objective_credit_bytes": 0, "full_corpus_score_bytes": None, "larger_gate_authorized": False,
             "continuous_guard_decision": "pending canonical outer guard closure",
             "confirmation": "one fixed public model; P/K bookkeeping control and two frozen D/G arms; no parameter tuning; fresh restore and repeat for each arm"}
    try:
        stage.update(gate.execute(), status="passed")
    except Exception as error:
        category = error.category if isinstance(error, GateFailure) else (
            "missing_or_unreadable_evidence" if isinstance(error, (OSError, KeyError, json.JSONDecodeError)) else "invariant_failed")
        stage.update(status="execution_failed", failure_class=category, error=type(error).__name__ + ": " + str(error))
    try:
        gate.closure()
        gate.verify_sources()
        stage["child_closure_ok"] = True
        stage["frozen_inputs_and_retained_sources_unchanged"] = True
    except Exception as error:
        stage.update(status="execution_failed", closure_error=type(error).__name__ + ": " + str(error))
    stage["commands"] = gate.commands
    try:
        gate.write(RESULT / "artifacts.json", [gate.artifact(path) for path in sorted(RESULT.rglob("*")) if path.is_file()])
        stage["artifacts"] = gate.artifact(RESULT / "artifacts.json")
    except Exception as error:
        stage.update(status="execution_failed", artifact_error=type(error).__name__ + ": " + str(error))
    gate.write(RESULT / "stage-decision.json", stage)
    return 0 if stage["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
