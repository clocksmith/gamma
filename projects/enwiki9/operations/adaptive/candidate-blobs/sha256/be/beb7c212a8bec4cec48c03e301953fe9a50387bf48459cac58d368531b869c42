#!/usr/bin/env python3
"""Synthetic-only actual-driver integration; no canonical population is opened."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import causal_wordcode_fifo128_gate_v1 as gate

SHIM = '''import json
import signal
from projects.enwiki9.tools import causal_wordcode_fifo128_bz2_v1 as codec

def compress_arm(data, arm):
    signal.alarm(180)
    try:
        return codec.compress_arm(data, arm)
    finally:
        signal.alarm(0)

def decompress_arm(data, arm):
    signal.alarm(180)
    try:
        raw = codec.decompress_arm(data, arm)
        print("CAUSAL_WORDCODE_DECODE " + json.dumps(codec.stats(), sort_keys=True))
        return raw
    finally:
        signal.alarm(0)

stats = codec.stats
'''


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


class ActualDriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="gamma-wordcode-driver-synthetic-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.candidate = "causal_wordcode_gate_synthetic_unit"
        cls.source = cls.root / "relocated_candidate"
        cls.source.mkdir()
        (cls.source / "program.py").write_text(SHIM)
        write(cls.source / "meta.json", {"id": cls.candidate, "deps": ["python3", "bz2"]})
        cls.population = cls.root / "synthetic.raw"
        cls.population.write_bytes((b"<page><title>ExactAlpha</title><text>ExactAlpha canonicalWord "
                                    b"RepeatedToken canonicalWord\x00\xff\r\n</text></page>\n") * 12)
        cls.plan = {"candidate_id": cls.candidate, "population": {"path": str(cls.population),
                    "bytes": cls.population.stat().st_size, "sha256": gate.sha(cls.population)},
                    "specification": {key: "synthetic fixture only" for key in ("hypothesis", "parent", "changed_mechanism",
                        "development_budget", "selection_population", "sealed_confirmation", "stop_rule")},
                    "measured_local_package_bytes": sum((ROOT / path).stat().st_size for path in (gate.CORE, gate.PARENT))
                    + (cls.source / "program.py").stat().st_size, "historical_parent_program_bytes": 1448}
        cls.plan["specification"]["arms"] = gate.ARMS.copy()
        cls.result = cls.root / "result"
        cls.result.mkdir()
        cls.authority = mock.Mock()
        environment = {"GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID": cls.candidate,
                       "GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT": str(cls.source)}
        ledger = gate.sha(ROOT / "results/run_ledger.jsonl")
        with mock.patch.dict(os.environ, environment), contextlib.redirect_stdout(io.StringIO()):
            cls.stage = gate.run_comparison(cls.candidate, cls.population, cls.result, cls.plan,
                {"synthetic": True}, reauthenticate=cls.authority, synthetic=True)
        if gate.sha(ROOT / "results/run_ledger.jsonl") != ledger:
            raise AssertionError("driver modified canonical ledger")
        if not cls.stage["correctness_pass"]:
            raise AssertionError(cls.stage)
        if os.environ.get("GAMMA_WORDCODE_GATE_UNIT_RETAIN"):
            shutil.copytree(cls.root, Path(os.environ["GAMMA_WORDCODE_GATE_UNIT_RETAIN"]))

    def test_actual_relocated_build_and_twelve_processes(self):
        self.assertEqual(self.stage["processes"], 12)
        manifest = gate.read(self.result / "comparison/build.json")
        for path, expected in gate.PINS.items():
            if path != gate.PLAN:
                self.assertEqual(manifest["files"]["projects/enwiki9/" + path]["sha256"], expected)
        for arm in "PKTL":
            for phase in ("encode", "decode", "repeat"):
                receipt = gate.read(self.result / "comparison" / arm / (phase + ".sources.json"))
                self.assertIn("projects/enwiki9/" + gate.CORE, receipt["loaded_sources"])
                self.assertIn("projects/enwiki9/programs/" + self.candidate + "/program.py", receipt["loaded_sources"])
        self.assertEqual(self.authority.call_count, 2)

    def test_no_package_or_qualification_credit(self):
        self.assertFalse(self.stage["local_cost_predicate_pass"])
        self.assertFalse(self.stage["promotion_authorized"])
        self.assertIsNone(self.stage["complete_package_bytes"])
        self.assertEqual(self.stage["objective_credit_bytes"], 0)
        self.assertEqual(gate.read(self.result / "stage-decision.json"), self.stage)

    @contextlib.contextmanager
    def changed_artifact(self, arm, filename, transform):
        """Rebind fabricated synthetic evidence to test semantic checks, then restore."""
        directory = self.result / "comparison"
        artifact, row_path, decision_path = directory / arm / filename, directory / arm / "result.json", directory / "decision.json"
        originals = {p: p.read_bytes() for p in (artifact, row_path, decision_path)}
        try:
            artifact.write_bytes(transform(originals[artifact]))
            row = gate.read(row_path)
            for value in row["artifacts"].values():
                if value["path"] == filename:
                    value.update(bytes=artifact.stat().st_size, sha256=gate.sha(artifact))
            write(row_path, row)
            decision = gate.read(decision_path)
            role = next(role for role, value in gate.ARMS.items() if value == arm)
            decision["arms"][role]["result_sha256"] = gate.sha(row_path)
            write(decision_path, decision)
            yield directory
        finally:
            for path, payload in originals.items():
                path.write_bytes(payload)

    def test_decoder_state_is_mandatory(self):
        with self.changed_artifact("T", "decode.stdout.log", lambda _: b"") as directory:
            with self.assertRaisesRegex(ValueError, "decoder state"):
                gate.close_comparison(directory, self.plan, historical=False)

    def test_duplicate_decoder_state_rejected(self):
        with self.changed_artifact("T", "decode.stdout.log", lambda raw: raw + raw) as directory:
            with self.assertRaisesRegex(ValueError, "decoder state"):
                gate.close_comparison(directory, self.plan, historical=False)

    def test_decoder_transition_disagreement_rejected(self):
        def mutate(raw):
            row = json.loads(raw.decode().removeprefix(gate.DECODE_MARKER))
            row["transition_digest"] = "0" * 64
            return (gate.DECODE_MARKER + json.dumps(row) + "\n").encode()
        with self.changed_artifact("T", "decode.stdout.log", mutate) as directory:
            with self.assertRaisesRegex(ValueError, "state agreement"):
                gate.close_comparison(directory, self.plan, historical=False)

    def test_bad_header_accounting_rejected(self):
        def mutate(raw):
            row = json.loads(raw)
            row["program_stats"]["framing_bytes"] = 4
            return json.dumps(row).encode()
        with self.changed_artifact("L", "encode.json", mutate) as directory:
            with self.assertRaisesRegex(ValueError, "byte accounting"):
                gate.close_comparison(directory, self.plan, historical=False)

    def test_historical_hash_cannot_be_waived_for_corpus(self):
        with self.assertRaisesRegex(ValueError, "historical P archive"):
            gate.close_comparison(self.result / "comparison", self.plan)

    def test_failed_reauthentication_closes_without_promotion(self):
        output = self.root / "auth_failure"
        output.mkdir()
        def compare(*args, **kwargs):
            self.assertFalse(kwargs["record_ledger"])
            shutil.copytree(self.result / "comparison", args[4])
        with mock.patch.object(gate.driver, "compare", side_effect=compare):
            outcome = gate.run_comparison(self.candidate, self.population, output, self.plan, {}, synthetic=True,
                reauthenticate=mock.Mock(side_effect=[None, ValueError("source replaced")]))
        self.assertFalse(outcome["correctness_pass"])
        self.assertFalse(outcome["promotion_authorized"])
        self.assertIn("source replaced", outcome["error"])

    def test_existing_results_are_never_overwritten(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            gate.run_comparison(self.candidate, self.population, self.result, self.plan, {},
                                reauthenticate=lambda: None, synthetic=True)

    def test_missing_authority_prevents_compare(self):
        output = self.root / "no_authority"
        output.mkdir()
        with mock.patch.object(gate.driver, "compare") as compare:
            with self.assertRaisesRegex(ValueError, "unowned"):
                gate.run_comparison(self.candidate, self.population, output, self.plan, {},
                    reauthenticate=mock.Mock(side_effect=ValueError("unowned")), synthetic=True)
            compare.assert_not_called()

    def test_synthetic_interface_rejects_large_inputs_before_reading(self):
        output = self.root / "large_rejected"
        output.mkdir()
        source = self.root / "large_synthetic.raw"
        source.write_bytes(b"x" * 32769)
        plan = copy.deepcopy(self.plan)
        plan["population"]["bytes"] = source.stat().st_size
        with mock.patch.object(gate, "sha", side_effect=AssertionError("must not read bytes")):
            with self.assertRaisesRegex(ValueError, "population bound"):
                gate.run_comparison(self.candidate, source, output, plan, {},
                                    reauthenticate=lambda: None, synthetic=True)

    def test_missing_comparison_source_fails_closed(self):
        path = self.result / "comparison/build/projects/enwiki9" / gate.PARENT
        original = path.read_bytes()
        try:
            path.chmod(0o644)
            path.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ValueError, "frozen build"):
                gate.close_comparison(self.result / "comparison", self.plan, historical=False)
        finally:
            path.write_bytes(original)
            path.chmod(0o444)

    def test_budget_exit_is_not_compression_rejection(self):
        output = self.root / "budget_failure"
        output.mkdir()
        def compare(*args, **kwargs):
            folder = args[4] / "P"
            folder.mkdir(parents=True)
            write(folder / "result.json", {"phase_execution": {"encode": {"returncode": -gate.signal.SIGXCPU}}})
        with mock.patch.object(gate.driver, "compare", side_effect=compare):
            stage = gate.run_comparison(self.candidate, self.population, output, self.plan, {},
                reauthenticate=lambda: None, synthetic=True)
        self.assertEqual(stage["failure_class"], "budget-exhausted")
        self.assertFalse(stage["correctness_pass"])


class AuthenticationTests(unittest.TestCase):
    """Small synthetic contracts and mocked process observations grant no launch."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gamma-wordcode-auth-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.candidate = "wordcode_auth_synthetic"
        self.candidate_dir = self.root / "programs" / self.candidate
        self.candidate_dir.mkdir(parents=True)
        (self.candidate_dir / "program.py").write_text(SHIM)
        write(self.candidate_dir / "meta.json", {"deps": []})
        for name in (*gate.PINS, gate.SELF):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        raw = self.root / "synthetic.raw"
        raw.write_bytes(b"ExactWords ExactWords\n")
        self.population = {"path": "synthetic.raw", "bytes": raw.stat().st_size, "sha256": gate.sha(raw)}
        import _bz2
        self.plan = {"candidate_id": self.candidate, "population": self.population, "resources": gate.CAPS.copy(),
            "specification": {"arms": gate.ARMS.copy()}, "historical_parent_program_bytes": 1448,
            "candidate_source": {"path": "programs/" + self.candidate + "/program.py",
                                 "sha256": gate.sha(self.candidate_dir / "program.py"), "bytes": len(SHIM.encode())},
            "runtime_files": [{"path": str(p), "bytes": p.stat().st_size, "sha256": gate.sha(p)}
                for p in (Path(sys.executable).resolve(), Path(_bz2.__file__).resolve())],
            "local_package_files": [gate.CORE, gate.PARENT, "programs/" + self.candidate + "/program.py"]}
        self.plan_path = self.root / "execution-plan.json"
        write(self.plan_path, self.plan)
        names = [*gate.PINS, gate.SELF, "synthetic.raw", "execution-plan.json"]
        self.contract = {"experimentId": self.candidate, "status": "frozen", "registrationTiming": "prospective",
            "objectiveCreditBytes": 0, "population": {"scopeBytes": raw.stat().st_size},
            "inputs": [{"id": "wordcode-gate-plan" if name == "execution-plan.json" else "input-" + str(i),
                        "path": name, "sha256": "sha256:" + gate.sha(self.root / name)} for i, name in enumerate(names)]}
        self.contract_path = self.root / "operations/adaptive/experiments" / (self.candidate + ".json")
        self.contract_path.parent.mkdir(parents=True)
        write(self.contract_path, self.contract)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target, value in (("ROOT", self.root), ("POPULATION", self.population)):
            self.stack.enter_context(mock.patch.object(gate, target, value))
        self.validate = self.stack.enter_context(mock.patch.object(gate.driver.research_contracts, "validate_artifact"))
        self.stack.enter_context(mock.patch.object(gate.driver, "_candidate_program_dir", return_value=self.candidate_dir))
        self.stack.enter_context(mock.patch.object(gate.driver, "_comparison_source_closure", side_effect=lambda path:
            [] if path == self.root / "lib/driver.py" else [self.root / gate.CORE, self.root / gate.PARENT, self.candidate_dir / "program.py"]))

    def update_plan(self):
        write(self.plan_path, self.plan)
        for row in self.contract["inputs"]:
            if row["id"] == "wordcode-gate-plan":
                row["sha256"] = "sha256:" + gate.sha(self.plan_path)
        write(self.contract_path, self.contract)

    def test_preflight_requires_existing_contract_validation(self):
        plan, _, job_id = gate.authenticate(self.candidate, live=False)
        self.validate.assert_called_once_with(self.contract_path)
        self.assertIsNone(job_id)
        self.assertEqual(plan["measured_local_package_bytes"], sum((self.root / p).stat().st_size for p in self.plan["local_package_files"]))

    def test_changed_source_is_rejected_before_execution(self):
        with (self.root / gate.CORE).open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "changed input"):
            gate.authenticate(self.candidate, live=False)

    def test_unbound_driver_source_rejected(self):
        with mock.patch.object(gate.driver, "_comparison_source_closure", return_value=[self.root / "unbound.py"]):
            with self.assertRaisesRegex(ValueError, "unbound actual driver source"):
                gate.authenticate(self.candidate, live=False)

    def test_controls_cannot_change(self):
        self.plan["specification"]["arms"]["literal_control"] = "X"
        self.update_plan()
        with self.assertRaisesRegex(ValueError, "P/K/T/L"):
                gate.authenticate(self.candidate, live=False)

    def test_future_candidate_binding_rejects_changed_source(self):
        with (self.candidate_dir / "program.py").open("a") as stream:
            stream.write("# changed\n")
        with self.assertRaisesRegex(ValueError, "candidate source differs"):
            gate.authenticate(self.candidate, live=False)

    def test_runtime_cannot_change(self):
        self.plan["runtime_files"][0]["sha256"] = "0" * 64
        self.update_plan()
        with self.assertRaisesRegex(ValueError, "runtime changed"):
            gate.authenticate(self.candidate, live=False)

    def test_package_cannot_omit_core(self):
        self.plan["local_package_files"].remove(gate.CORE)
        self.update_plan()
        with self.assertRaisesRegex(ValueError, "accounting is incomplete"):
            gate.authenticate(self.candidate, live=False)

    @contextlib.contextmanager
    def live_fixture(self):
        reference = {"path": str(self.contract_path.relative_to(self.root)), "sha256": "sha256:" + gate.sha(self.contract_path)}
        marker = self.root / "run_logs/adaptive/synthetic_job.resources/phases.jsonl"
        marker.parent.mkdir(parents=True)
        marker.touch()
        guard_source = self.root / "tools/mock_guard.py"
        guard_source.write_text("# synthetic identity only\n")
        revision = self.root / "mock_revision.json"
        write(revision, {"synthetic": True})
        group = Path("/sys/fs/cgroup/gamma-wordcode-synthetic")
        command = b"python\0synthetic_guard"
        self.job = {"job_id": "synthetic_job", "candidate_id": self.candidate, "experiment": reference, "state": "running",
            "execution_mode": "discovery", "resource_budget": gate.CAPS.copy(),
            "runner": {"path": gate.SELF, "sha256": "sha256:" + gate.sha(self.root / gate.SELF)},
            "execution_guard": {"path": "tools/mock_guard.py", "sha256": "sha256:" + gate.sha(guard_source)},
            "candidate_tree_sha256": "sha256:" + "1" * 64,
            "candidate_revision": {"path": "mock_revision.json", "sha256": "sha256:" + gate.sha(revision)},
            "worker_pid": 1337, "worker_proc_start_ticks": 123,
            "execution_resources": {"boot_id": "synthetic-boot", "guard_command_sha256": hashlib.sha256(command).hexdigest(),
                "cgroup_path": str(group), "cgroup_inode": 555, "guard_path": str((marker.parent / "guard.json").relative_to(self.root))}}
        self.job_path = self.root / "operations/adaptive/running/000_synthetic_job.json"
        self.job_path.parent.mkdir(parents=True)
        write(self.job_path, self.job)
        self.guard_path = marker.parent / "guard.json"
        self.guard = {"status": "running", "label": "synthetic_job", "phase": "diagnostic", "max_logical_cpus": 1,
            "temporary_disk_limit_bytes": gate.CAPS["scratch_bytes"], "guards": {"exceeded": False},
            "cgroup": {"path": str(group), "inode": 555, "requested_memory_max_bytes": gate.CAPS["memory_bytes"]}}
        write(self.guard_path, self.guard)
        environment = {"GAMMA_ENWIKI9_EXPERIMENT_JSON": json.dumps(reference), "GAMMA_RESOURCE_PHASE_MARKERS": str(marker),
            "GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON": json.dumps({"candidateId": self.candidate,
                "candidateTreeSha256": self.job["candidate_tree_sha256"], "receipt": self.job["candidate_revision"]})}
        old_text, old_bytes, old_stat = Path.read_text, Path.read_bytes, Path.stat
        observations = {"/proc/sys/kernel/random/boot_id": "synthetic-boot\n", "/proc/self/cgroup": "0::/gamma-wordcode-synthetic\n",
            "/proc/1337/stat": "1337 (guard) " + " ".join(["S", "1"] + ["0"] * 17 + ["123"]),
            "/proc/1338/stat": "1338 (runner) " + " ".join(["S", "1337"] + ["0"] * 17 + ["124"]),
            str(group / "memory.max"): str(gate.CAPS["memory_bytes"]), str(group / "memory.swap.max"): "0"}
        def text(path, *args, **kwargs):
            return observations[str(path)] if str(path) in observations else old_text(path, *args, **kwargs)
        def binary(path):
            return command + b"\0" if str(path) == "/proc/1337/cmdline" else old_bytes(path)
        def stat(path, *args, **kwargs):
            return SimpleNamespace(st_ino=555) if path == group else old_stat(path, *args, **kwargs)
        with mock.patch.dict(os.environ, environment), mock.patch.object(gate.os, "getpid", return_value=1338), \
             mock.patch.object(gate.os, "sched_getaffinity", return_value={4}), \
             mock.patch.object(Path, "read_text", text), mock.patch.object(Path, "read_bytes", binary), mock.patch.object(Path, "stat", stat):
            yield reference

    def test_live_job_guard_and_group_must_agree(self):
        with self.live_fixture() as reference:
            self.assertEqual(gate.authenticate_live(self.candidate, reference, self.plan), "synthetic_job")

    def test_missing_controller_never_authorizes_launch(self):
        with self.live_fixture() as reference:
            self.job_path.unlink()
            with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
                gate.authenticate_live(self.candidate, reference, self.plan)

    def test_replaced_guard_pid_rejected(self):
        with self.live_fixture() as reference:
            self.job["worker_proc_start_ticks"] = 999
            write(self.job_path, self.job)
            with self.assertRaisesRegex(ValueError, "guard process identity"):
                gate.authenticate_live(self.candidate, reference, self.plan)

    def test_terminal_guard_rejected(self):
        with self.live_fixture() as reference:
            self.guard["status"] = "completed"
            write(self.guard_path, self.guard)
            with self.assertRaisesRegex(ValueError, "active guard"):
                gate.authenticate_live(self.candidate, reference, self.plan)

    def test_other_cpu_rejected(self):
        with self.live_fixture() as reference, mock.patch.object(gate.os, "sched_getaffinity", return_value={2}):
            with self.assertRaisesRegex(ValueError, "CPU4"):
                gate.authenticate_live(self.candidate, reference, self.plan)


if __name__ == "__main__":
    unittest.main()
