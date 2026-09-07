"""Synthetic runner checks; canonical ownership is mocked, no corpus is read."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import fx2_causal_field_wrt_gate_v2 as gate_tool
import fx2_causal_field_replay_v1 as core
from causal_field_parent_coder_v1 import Encoder
from wrt_exact import wrt_byte_transform
from lib.artifacts import atomic_write_json, artifact_ref

SOURCE_NAMES = [gate_tool.CORE, "tools/causal_field_wrt_adapter_v1.py",
                "tools/causal_field_parent_coder_v1.py", "tools/causal_field_dependency_v1.py", "tools/wrt_exact.py"]


def ref(root, path):
    return artifact_ref(path, root)


def fixture(raw):
    modeled = bytearray([7])
    for value in raw:
        if value >= 128 or value in (6, 7, 12, 64):
            modeled.append(wrt_byte_transform(12))
        modeled.append(wrt_byte_transform(value))
    modeled = bytes(modeled)
    prefix = b"GFV1\x07" + len(raw).to_bytes(4, "big") + ((1 << 39) + len(modeled)).to_bytes(5, "big") + b"\xff" * 32
    coder = Encoder(max_bits=len(modeled) * 8)
    trace = bytearray()
    for i in range(len(modeled) * 8):
        q = 16000 + (i * 19) % 30000
        bit = (modeled[i // 8] >> (7 - i % 8)) & 1
        before = coder.low, coder.high
        coder.encode(bit, q)
        fp = struct.unpack("<I", struct.pack("<f", (q - 1) / 65534))[0]
        trace.extend(struct.pack("<7I", fp, q, *before, coder.low, coder.high, bit))
    stored = b"\x80\0\0\0\0\x07" + len(raw).to_bytes(4, "big") + modeled
    return stored, bytes(trace), prefix + coder.finish()


class SyntheticGate:
    """Test double only: this provides no canonical launch authority."""
    def __init__(self, root):
        self.root = Path(root)
        self.result = self.root / "results" / gate_tool.ID
        self.work = self.result / "work"
        self.work.mkdir(parents=True)
        self.inputs, self.buffers, self.commands, self.retained = {}, {}, [], {}
        self.reference = {"path": "synthetic-contract.json", "sha256": "sha256:" + "0" * 64}

    def bind(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.inputs[name] = ref(self.root, path)
        self.buffers[name] = data
        return self.inputs[name]

    def artifact(self, path):
        return ref(self.root, path)

    def write(self, name, value):
        atomic_write_json(self.result / name, value)

    def copy(self, source, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(self.buffers[source])

    def retain_sources(self):
        for name in self.buffers:
            if name.endswith(".py"):
                self.copy(name, self.work / "source" / name)

    def verify(self):
        for name, row in self.inputs.items():
            if gate_tool.file_sha(self.root / name) != row["sha256"]:
                raise ValueError("synthetic source/input replaced")

    def closure(self):
        pass

    def run(self, name, command, cap, env=None):
        start = time.monotonic()
        with (self.result / (name + ".stdout")).open("xb") as out, (self.result / (name + ".stderr")).open("xb") as err:
            process = subprocess.run(command, stdout=out, stderr=err, cwd=self.work,
                                     timeout=cap, env={**os.environ, **(env or {}), "PYTHONDONTWRITEBYTECODE": "1"})
        row = {"phase": name, "command": command, "returncode": process.returncode,
               "elapsed_seconds": time.monotonic() - start, "timing_authority": "synthetic test only"}
        self.commands.append(row)
        self.write(name + ".execution.json", row)
        if process.returncode:
            raise ValueError((self.result / (name + ".stderr")).read_text())
        return row


def report(arm="T"):
    value = {key: "a" * 64 for key in gate_tool.MEANINGFUL}
    value.update(arm=arm, raw_bytes=100, modeled_bytes=101, archive_bytes=100, payload_bytes=54,
                 prefix_bytes=46, synchronization_rows=101, changed_probability_bits=8,
                 donor_present_bits=10, adapter={"selected_values": 1}, operation="encode", pid=1,
                 exact_raw_inverse=True, standalone_decoder=False, objective_credit_bytes=0,
                 complete_package_bytes=None, full_corpus_score_bytes=None)
    return value


class GateTests(unittest.TestCase):
    def test_output_declarations_have_all_fifteen_independent_phases(self):
        paths = gate_tool.declared_outputs([{"path": name} for name in SOURCE_NAMES])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(sum(path.endswith(".execution.json") for path in paths), 15)
        self.assertEqual(sum(path.endswith(".sync") for path in paths), 15)
        self.assertEqual(sum(path.endswith("/result.json") for path in paths), 5)
        self.assertIn("work/source/tools/causal_field_dependency_v1.py", paths)

    def test_describe_outputs_opens_no_inputs(self):
        with patch.object(gate_tool, "authenticate", side_effect=AssertionError("must not authenticate")), patch("builtins.print"):
            self.assertEqual(gate_tool.main(["--describe-outputs"]), 0)

    def test_report_scope_identity_and_missing_mandatory_fields(self):
        source = report()
        gate_tool.checked_report(source, "encode", "T", {"raw_bytes": 100})
        for changes in ({"operation": "decode"}, {"arm": "S"}, {"standalone_decoder": True},
                        {"complete_package_bytes": 0}, {"objective_credit_bytes": 1},
                        {"synchronization_rows": 100}, {"payload_bytes": 53},
                        {"raw_bytes": 101}, {"donor_present_bits": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                gate_tool.checked_report({**source, **changes}, "encode", "T", {"raw_bytes": 100})
        del source["mixture_state_digest"]
        with self.assertRaises(ValueError):
            gate_tool.checked_report(source, "encode", "T", {})

    def test_complete_report_comparison_rejects_internal_state_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = SyntheticGate(tmp)
            codec = gate_tool.Codec(gate, {}, "T", b"", b"", b"", b"x")
            codec.reports = {phase: report() for phase in gate_tool.PHASES}
            codec.projections = copy.deepcopy(codec.reports)
            codec.syncs = {phase: b"a" * 32 for phase in gate_tool.PHASES}
            codec.projections["decode"]["mixture_state_digest"] = "b" * 64
            with self.assertRaisesRegex(ValueError, "state report differs"):
                codec.finish()

    def test_first_divergence_retains_state_record_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = SyntheticGate(tmp)
            with self.assertRaises(ValueError):
                gate_tool.compare_bytes(gate, b"x" * 64 + b"b" * 32, b"x" * 64 + b"a" * 32, "decode-state", 32)
            evidence = json.loads((gate.result / "first-divergence.json").read_text())
            self.assertEqual(evidence["first_record"], 2)
            self.assertEqual(evidence["first_byte"], 64)
            self.assertEqual(evidence["record_bytes"], 32)

    def comparison_reports(self):
        rows = {arm: report(arm) for arm in gate_tool.ARMS}
        for arm in ("P", "K"):
            rows[arm].update(changed_probability_bits=0, donor_present_bits=0, archive_bytes=120)
        rows["R"]["archive_bytes"] = rows["S"]["archive_bytes"] = 110
        return rows

    def test_conditional_gain_retains_dependency_and_no_score_credit(self):
        result = gate_tool.scientific_comparison(self.comparison_reports(), 30, 4000)
        self.assertEqual(result["archive_saved_bytes"], 20)
        self.assertFalse(result["local_source_paying"])
        self.assertEqual(result["external_decode_dependency_bytes"], 4000)
        self.assertEqual(result["failure_class"], "conditional_archive_gain")
        self.assertIsNone(result["complete_package_bytes"])
        self.assertEqual(result["objective_credit_bytes"], 0)

    def test_inactive_required_control_is_inconclusive(self):
        rows = self.comparison_reports()
        rows["R"]["changed_probability_bits"] = 0
        self.assertEqual(gate_tool.scientific_comparison(rows, 30, 1)["failure_class"],
                         "inconclusive_inactive_opportunities_or_controls")

    def test_failed_control_and_weak_compression_are_distinct(self):
        rows = self.comparison_reports()
        rows["R"]["archive_bytes"] = 99
        self.assertEqual(gate_tool.scientific_comparison(rows, 0, 0)["failure_class"], "failed_causal_controls")
        rows["R"]["archive_bytes"] = rows["S"]["archive_bytes"] = 140
        rows["T"]["archive_bytes"] = 121
        self.assertEqual(gate_tool.scientific_comparison(rows, 0, 0)["failure_class"], "weak_compression")

    def test_parent_bookkeeping_probability_identity_is_required(self):
        rows = self.comparison_reports()
        rows["K"]["probability_digest"] = "b" * 64
        with self.assertRaises(ValueError):
            gate_tool.scientific_comparison(rows, 0, 0)

    def test_final_authentication_failure_publishes_no_positive_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = SyntheticGate(tmp)
            with patch.object(gate_tool, "execute", return_value={"failure_class": "conditional_archive_gain"}), \
                 patch.object(gate_tool, "check_runtime"), \
                 patch.object(gate_tool, "authenticate", side_effect=ValueError("contract replaced")):
                outcome = gate_tool.finish_gate(gate, {})
            self.assertEqual(outcome["status"], "execution_failed")
            self.assertFalse((gate.result / "comparison.json").exists())
            self.assertTrue((gate.result / "stage-decision.json").exists())

    def test_post_write_fingerprint_failure_quarantines_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = SyntheticGate(tmp)
            original_artifact = gate.artifact
            def unavailable(path):
                if path.name == "comparison.json":
                    raise OSError("injected fingerprint failure")
                return original_artifact(path)
            with patch.object(gate_tool, "execute", return_value={"failure_class": "conditional_archive_gain"}), \
                 patch.object(gate_tool, "check_runtime"), patch.object(gate_tool, "authenticate"), \
                 patch.object(gate_tool, "index_artifacts", return_value=([], {"complete": True})), \
                 patch.object(gate, "artifact", side_effect=unavailable):
                outcome = gate_tool.finish_gate(gate, {})
            self.assertEqual(outcome["status"], "execution_failed")
            self.assertFalse((gate.result / "comparison.json").exists())
            self.assertTrue((gate.result / "unpublished-comparison.json").exists())

    def test_index_fingerprint_and_stage_write_failure_leave_no_published_table(self):
        for failure in ("artifacts.json", "stage-decision.json"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                gate = SyntheticGate(tmp)
                original_artifact, original_write = gate.artifact, gate.write
                def artifact(path):
                    if path.name == failure:
                        raise OSError("injected index fingerprint failure")
                    return original_artifact(path)
                def write(name, value):
                    if name == failure == "stage-decision.json":
                        raise OSError("injected final stage failure")
                    return original_write(name, value)
                with patch.object(gate_tool, "execute", return_value={"failure_class": "conditional_archive_gain"}), \
                     patch.object(gate_tool, "check_runtime"), patch.object(gate_tool, "authenticate"), \
                     patch.object(gate_tool, "index_artifacts", return_value=([], {"complete": True})), \
                     patch.object(gate, "artifact", side_effect=artifact), patch.object(gate, "write", side_effect=write):
                    if failure == "stage-decision.json":
                        with self.assertRaises(OSError):
                            gate_tool.finish_gate(gate, {})
                    else:
                        outcome = gate_tool.finish_gate(gate, {})
                        self.assertEqual(outcome["status"], "execution_failed")
                self.assertFalse((gate.result / "comparison.json").exists())

    def test_live_controller_rejects_vanished_zombie_and_terminal_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "run_logs/adaptive/synthetic.resources/phases.jsonl"
            guard_path = marker.parent / "guard.json"
            guard_path.parent.mkdir(parents=True)
            digest = "a" * 64
            revision = {"path": "synthetic-revision.json", "sha256": "sha256:" + digest}
            resources = {"boot_id": "boot", "guard_command_sha256": gate_tool.digest(b"guard"),
                         "cgroup_path": "synthetic-group", "cgroup_inode": 9,
                         "guard_path": guard_path.relative_to(root).as_posix()}
            job = {"job_id": "synthetic", "runner": {"path": gate_tool.SELF, "sha256": "sha256:" + digest},
                   "execution_guard": revision, "candidate_tree_sha256": digest, "candidate_revision": revision,
                   "worker_pid": 1234, "worker_proc_start_ticks": 456, "execution_resources": resources}
            invocation = {"candidateId": gate_tool.ID, "candidateTreeSha256": digest, "receipt": revision}
            active = {"status": "running", "label": "synthetic", "phase": "diagnostic", "guards": {},
                      "cgroup": {"path": "synthetic-group", "inode": 9, "requested_memory_max_bytes": gate_tool.CAPS["memory_bytes"]},
                      "temporary_disk_limit_bytes": gate_tool.CAPS["scratch_bytes"], "max_logical_cpus": 1,
                      "wall_time_limit_seconds": gate_tool.CAPS["wall_seconds"]}
            def proc_stat(pid, parent, state="S"):
                fields = [state, str(parent)] + ["0"] * 18
                fields[19] = "456"
                return str(pid) + " (synthetic) " + " ".join(fields)
            original = Path.read_text
            mode = "valid"
            def read_text(path, *args, **kwargs):
                if str(path) == "/proc/sys/kernel/random/boot_id":
                    return "foreign" if mode == "boot" else "boot"
                if str(path) == "/proc/1234/stat":
                    if mode == "vanished":
                        raise FileNotFoundError("guard vanished")
                    return proc_stat(1234, 1, "Z" if mode == "zombie" else "S")
                if str(path) == "/proc/5678/stat":
                    return proc_stat(5678, 1234)
                return original(path, *args, **kwargs)
            for mode in ("valid", "uncalibrated", "vanished", "zombie", "terminal", "boot", "flags", "wrong_wall", "outer_absent"):
                guard = copy.deepcopy(active)
                if mode in ("uncalibrated", "outer_absent"):
                    guard["wall_time_limit_seconds"] = None
                if mode == "wrong_wall":
                    guard["wall_time_limit_seconds"] = 800
                if mode == "terminal":
                    guard["status"] = "complete"
                if mode == "flags":
                    guard["guards"] = {"wall_time_guard_exceeded": True}
                guard_path.write_text(json.dumps(guard))
                with self.subTest(mode=mode), patch.object(gate_tool, "file_sha", return_value=digest), \
                     patch.object(gate_tool, "read_ref", return_value=b"{}"), patch.object(Path, "read_text", read_text), \
                     patch.object(Path, "read_bytes", return_value=b"guard\0"), patch.object(os, "getpid", return_value=5678), \
                     patch.object(gate_tool, "_ADMISSION_CONTEXT", None if mode == "outer_absent" else {"plan": {}, "inputs": {}}), \
                     patch.object(gate_tool, "check_outer_controller"), \
                     patch.dict(os.environ, {"GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON": json.dumps(invocation)}):
                    if mode in ("valid", "uncalibrated"):
                        gate_tool.check_live_controller(root, job, marker)
                    else:
                        with self.assertRaises((OSError, ValueError)):
                            gate_tool.check_live_controller(root, job, marker)

    def test_missing_admission_rejects_before_payload_reader_construction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "run_logs/adaptive/synthetic.resources/phases.jsonl"
            # If the eager NativeGate were reached it would fail the test.
            buffers = {"lib/fx2_native_gate_v1.py": b"raise AssertionError('payload reader reached')\n"}
            with patch.object(gate_tool, "ROOT", root), patch.object(gate_tool, "authenticate", return_value=({"inputs": []}, {}, buffers, {})), \
                 patch.object(os, "sched_getaffinity", return_value={2}), \
                 patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(marker)}), \
                 self.assertRaisesRegex(ValueError, "canonical running job"):
                gate_tool.main([])

    def test_observed_outer_lab_controller_binding_and_orphan_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = Path(sys.executable).resolve()
            runtime = {"path": str(executable), "bytes": executable.stat().st_size,
                       "sha256": gate_tool.file_sha(executable)}
            plan = {"python_executable": str(executable), "runtime_files": [runtime]}
            source = {"path": "tools/enwiki9_lab.py", "sha256": "a" * 64, "bytes": 9}
            job = {"job_id": "fixture", "worker_pid": 1234, "worker_proc_start_ticks": 456,
                   "execution_resources": {"boot_id": "boot"}}
            argv = [str(executable), str(root / "tools/enwiki9_lab.py"), "run", "--candidate", gate_tool.ID,
                    "--max-workers", "1", "--min-free-mib", "16384", "--max-load", "24"]
            encoded = b"\0".join(map(os.fsencode, argv)) + b"\0"
            def proc_stat(pid, parent, start, state="S"):
                fields = [state, str(parent)] + ["0"] * 18
                fields[19] = str(start)
                return str(pid) + " (python3.14) " + " ".join(fields)
            original_resolve = Path.resolve
            def resolve(path, *args, **kwargs):
                if str(path) == "/proc/4321/cwd":
                    return root / "foreign" if mode == "cwd" else root
                if str(path) == "/proc/4321/exe":
                    return Path("/usr/bin/false") if mode == "exe" else executable
                return original_resolve(path, *args, **kwargs)
            stat_reads = 0
            def read_text(path, *args, **kwargs):
                nonlocal stat_reads
                if str(path) == "/proc/sys/kernel/random/boot_id":
                    return "boot"
                if str(path) == "/proc/4321/stat":
                    stat_reads += 1
                    if mode == "vanished":
                        raise FileNotFoundError("outer controller vanished")
                    start = 999 if mode == "newer" or mode == "replaced" and stat_reads > 1 else 400
                    return proc_stat(4321, 1, start, "Z" if mode == "zombie" else "S")
                if str(path) == "/proc/1234/stat":
                    return proc_stat(1234, 1 if mode == "orphaned" else 4321, 456)
                raise AssertionError("unexpected metadata read: " + str(path))
            def read_bytes(path):
                self.assertEqual(str(path), "/proc/4321/cmdline")
                return encoded.replace(b"run\0", b"status\0") if mode == "argv" else encoded
            for mode in ("valid", "vanished", "zombie", "newer", "replaced", "orphaned", "cwd", "exe", "argv"):
                stat_reads = 0
                with self.subTest(mode=mode), patch.object(gate_tool, "_CONTROLLER_BINDING", None), \
                     patch.object(gate_tool, "read_ref", return_value=b"synthetic"), \
                     patch.object(Path, "resolve", resolve), patch.object(Path, "read_text", read_text), \
                     patch.object(Path, "read_bytes", read_bytes):
                    if mode == "valid":
                        result = gate_tool.check_outer_controller(root, job, 4321, plan, {source["path"]: source})
                        self.assertEqual(result["proc_start_ticks"], 400)
                        self.assertEqual(result["timer_owner"], "enwiki9_lab.wait_for_budgeted_worker")
                        self.assertEqual(result, gate_tool.check_outer_controller(root, job, 4321, plan, {source["path"]: source}))
                        gate_tool._CONTROLLER_BINDING = {**result, "proc_start_ticks": 399}
                        with self.assertRaisesRegex(ValueError, "binding changed"):
                            gate_tool.check_outer_controller(root, job, 4321, plan, {source["path"]: source})
                    else:
                        with self.assertRaises((OSError, ValueError)):
                            gate_tool.check_outer_controller(root, job, 4321, plan, {source["path"]: source})

    def test_mismatched_job_and_cgroup_reject_before_payload_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "run_logs/adaptive/synthetic.resources/phases.jsonl"
            path = root / "operations/adaptive/running/000_synthetic.json"
            path.parent.mkdir(parents=True)
            reference = {"path": "fixture", "sha256": "sha256:" + "a" * 64}
            job = {"job_id": "synthetic", "candidate_id": gate_tool.ID, "state": "running",
                   "experiment": reference, "execution_mode": "discovery", "resource_budget": gate_tool.CAPS,
                   "execution_resources": {"cgroup_path": "/not-the-current-group", "cgroup_inode": 1}}
            for field, value, message in (("candidate_id", "foreign", "job identity"), (None, None, "current cgroup")):
                changed = copy.deepcopy(job)
                if field:
                    changed[field] = value
                path.write_text(json.dumps(changed))
                with self.subTest(field=field), patch.object(os, "sched_getaffinity", return_value={2}), \
                     patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(marker)}), \
                     self.assertRaisesRegex(ValueError, message):
                    gate_tool.admit_before_payloads(root, reference)

    def test_missing_closed_output_prevents_positive_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = SyntheticGate(tmp)
            with patch.object(gate_tool, "execute", return_value={"failure_class": "conditional_archive_gain"}), \
                 patch.object(gate_tool, "check_runtime"), patch.object(gate_tool, "authenticate"):
                outcome = gate_tool.finish_gate(gate, {})
            self.assertEqual(outcome["failure_class"], "missing_or_unreadable_evidence")
            self.assertFalse((gate.result / "comparison.json").exists())

    def test_runtime_replacement_and_unbound_python_fail(self):
        executable = Path(sys.executable).resolve()
        plan = {"python_executable": str(executable), "runtime_files": [
            {"path": str(executable), "bytes": executable.stat().st_size, "sha256": gate_tool.file_sha(executable)}]}
        gate_tool.check_runtime(plan)
        plan["runtime_files"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            gate_tool.check_runtime(plan)
        plan["runtime_files"] = []
        with self.assertRaises(ValueError):
            gate_tool.check_runtime(plan)

    def test_metadata_preflight_never_opens_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = {}
            def add(name, value):
                data = value if isinstance(value, bytes) else json.dumps(value).encode()
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                row = ref(root, path)
                inputs[name] = row
                return row
            objective = {"targetScoreBytes": 99000000}
            guard_ref = add("run_logs/synthetic-guard.json", {"label": "fixture", "status": "complete", "returncode": 0,
                            "guards": {}, "cgroup": {"path": "synthetic-group", "inode": 1}, "command": ["synthetic"],
                            "command_sha256": gate_tool.digest(b"synthetic")})
            job_ref = add("operations/adaptive/completed/synthetic.json", {"state": "completed", "job_id": "fixture",
                          "candidate_id": gate_tool.ANCESTOR, "returncode": 0, "execution_resources": {
                              "cleanup_complete": True, "guard_path": guard_ref["path"],
                              "cgroup_path": "synthetic-group", "cgroup_inode": 1}})
            audit = {"candidate_id": gate_tool.ANCESTOR, "validity": "valid", "job_id": "fixture",
                     "source_bindings": {"all_inputs_match": True}, "resources": {
                         "cleanup_complete": True, "closed_process_list_empty": True, "guard_flags": {},
                         "job": job_ref, "guard": guard_ref}}
            audit["artifacts"] = [{"path": name, "bytes": size, "sha256": digest}
                                  for name, size, digest in gate_tool.POPULATION.values()]
            audit_ref = add(gate_tool.AUDIT, audit)
            reflection_ref = add(gate_tool.REFLECTION, {"candidateId": gate_tool.ANCESTOR,
                                 "validity": {"valid": True}, "decision": {"promotionPredicatesPass": True},
                                 "objective": objective, "job": job_ref, "evidence": [audit_ref]})
            for name in (gate_tool.SELF, gate_tool.CORE, "lib/fx2_native_gate_v1.py", "lib/artifacts.py", "lib/driver.py",
                         "tools/research_contracts.py", "tools/causal_field_dependency_v1.py", "tools/enwiki9_lab.py"):
                add(name, b"# synthetic source\n")
            add("tools/wrt_exact.py", b"# synthetic WRT source\n")
            pins = {name: inputs["tools/" + name]["sha256"] for name in ("causal_field_dependency_v1.py", "wrt_exact.py")}
            add("tools/causal_field_wrt_adapter_v1.py", ("PINS = " + repr(pins) + "\n").encode())
            add("tools/enwiki9_python_source_closure.py", b"def local_source_closure(entries):\n    return list(entries)\n")
            population = {"raw_bytes": 250000, "modeled_bytes": 151210}
            for field, (name, size, digest) in gate_tool.POPULATION.items():
                population[field] = name
                inputs[name] = {"path": name, "bytes": size, "sha256": digest}
                self.assertFalse((root / name).exists())
            plan = {"candidate_id": gate_tool.ID, "resources": gate_tool.CAPS, "population": population,
                    "antecedents": [job_ref], "local_package_files": [inputs[gate_tool.CORE],
                    inputs["tools/causal_field_dependency_v1.py"]]}
            plan_ref = add("operations/provenance/synthetic-execution.json", plan)
            plan_ref["id"] = gate_tool.PLAN_ID
            add("operations/adaptive/experiments/" + gate_tool.ID + ".json", {
                "experimentId": gate_tool.ID, "status": "frozen", "objective": objective, "inputs": list(inputs.values())})
            pins = {gate_tool.AUDIT: audit_ref["sha256"], gate_tool.REFLECTION: reflection_ref["sha256"]}
            with patch.object(gate_tool, "FIXED", pins), patch.object(gate_tool, "check_runtime"):
                _, observed, _, _ = gate_tool.authenticate(root)
            self.assertEqual(observed, plan)
            # Omitting an AST-loaded source cannot be hidden by the static
            # resolver's deliberate inability to follow its literal filename.
            contract_name = "operations/adaptive/experiments/" + gate_tool.ID + ".json"
            for omit_package in (True, False):
                changed = copy.deepcopy(plan)
                selected_inputs = copy.deepcopy(inputs)
                if omit_package:
                    changed["local_package_files"] = [inputs[gate_tool.CORE]]
                else:
                    del selected_inputs["tools/causal_field_dependency_v1.py"]
                plan_path = root / plan_ref["path"]
                plan_path.write_text(json.dumps(changed))
                selected_inputs[plan_ref["path"]] = {**ref(root, plan_path), "id": gate_tool.PLAN_ID}
                (root / contract_name).write_text(json.dumps({"experimentId": gate_tool.ID, "status": "frozen",
                    "objective": objective, "inputs": [v for k, v in selected_inputs.items() if k != contract_name]}))
                with self.subTest(omit_package=omit_package), patch.object(gate_tool, "FIXED", pins), \
                     patch.object(gate_tool, "check_runtime"), self.assertRaises(ValueError):
                    gate_tool.authenticate(root)

    def test_all_fifteen_real_cli_processes_and_unmodified_driver_rows(self):
        # Fresh short fixture, unrelated to the selected corpus. Canonical
        # authority/resource-group checks are deliberately mocked in this test.
        temporary = tempfile.TemporaryDirectory()
        with temporary as tmp:
            gate = SyntheticGate(tmp)
            for name in SOURCE_NAMES:
                gate.bind(name, (ROOT / name).read_bytes())
            raw = b"{{t|a=a|b=" + b"x" * 53 + b"}}\n{{t|a=b|b=" + b"y" * 53 + b"}}\n{{t|a=a|b=" + b"x" * 53 + b"}}"
            stored, trace, archive = fixture(raw)
            population = {"raw_bytes": len(raw), "modeled_bytes": len(stored) - 10}
            for field, name, payload in (("raw_path", "raw", raw), ("stored_path", "stored", stored),
                                         ("trace_path", "trace", trace), ("parent_archive_path", "archive", archive),
                                         ("dictionary_path", "dictionary", b"unused\n")):
                population[field] = "fixtures/" + name
                gate.bind(population[field], payload)
            executable = Path(sys.executable).resolve()
            plan = {"python_executable": str(executable), "population": population,
                    "runtime_files": [{"path": str(executable), "bytes": executable.stat().st_size,
                                       "sha256": gate_tool.file_sha(executable)}],
                    "local_package_files": [gate.inputs[name] for name in SOURCE_NAMES]}
            with patch.object(gate_tool, "CAPS", {**gate_tool.CAPS, "cpus": sorted(os.sched_getaffinity(0))}), \
                 patch.object(gate_tool, "admit_before_payloads"):
                result = gate_tool.execute(gate, plan)
            self.assertEqual(len(gate.commands), 15)
            self.assertTrue(result["exact_raw_inverse"])
            self.assertTrue(result["every_byte_state_synchronization"])
            self.assertTrue(result["parent_archive_identical"])
            self.assertGreater(result["reports"]["T"]["changed_probability_bits"], 0)
            for command in gate.commands:
                if command["phase"].endswith("-decode"):
                    argv = command["command"]
                    self.assertNotIn(str(gate.work / "modeled.bin"), argv)
                    self.assertNotIn(str(gate.work / "raw.bin"), argv)
                    self.assertNotIn(str(gate.root / "fixtures/trace"), argv)
            for arm in gate_tool.ARMS:
                path = gate.result / arm / "result.json"
                original = path.read_bytes()
                row = json.loads(original)
                self.assertIsNone(row["arm"])
                self.assertEqual(row["run_source"], "canonical-tool")
                self.assertEqual(row["run_tags"], ["arm:" + arm, "external-parent-q16-replay"])
                self.assertEqual(row["run_scope_label"], "opening250k-" + arm)
                self.assertEqual(row["program_stats"]["scope"], "external-parent-q16-replay")
                self.assertEqual(row["program_stats"]["phase"]["archive_bytes"], row["compressed_size"])
                self.assertEqual(path.read_bytes(), original)
            destination = os.environ.get("GAMMA_FIELD_GATE_SYNTHETIC_RETAIN")
            if destination:
                shutil.copytree(gate.root, destination)
                atomic_write_json(Path(destination) / "synthetic-comparison.json", result)


if __name__ == "__main__":
    unittest.main()
