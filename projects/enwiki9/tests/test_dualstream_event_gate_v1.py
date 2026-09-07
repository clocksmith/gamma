"""Synthetic complete-run and failure-closed tests; no corpus input is opened."""
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
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_event_gate_v1 as gate
from tools import dualstream_event_coder_v1 as kernel
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_argtokens_v2 as new
from tools import dualstream_grammar_reserialize_v1 as rep

PROJECT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A caller-owned TMPDIR retains every synthetic input and child result.
        cls.root = Path(tempfile.mkdtemp(prefix="event_gate_synthetic_"))
        cls.raw = b"<title>Oak</title>Oak is a town.\xff\x00"
        cls.model = old.Model(structure=(("call", 0),), arguments=(b"Oak",),
            templates=((1, (b"<title>", old.Arg(0), b"</title>", old.Arg(0), b" is a town.\xff\x00")),))
        cls.b = old.HEADER.pack(old.MAGIC, old.MAX_FRAME, 1, len(cls.raw)) + old.frame_bytes(cls.raw, "parameter", cls.model)[0]
        cls.p = new.encode(cls.raw, mode="plain")[0]
        for source in {gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE}:
            target = cls.root / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / source, target)
        (cls.root / "inputs").mkdir()
        for name, data in (("raw.bin", cls.raw), ("P.d2g", cls.p), ("B.d2g", cls.b)):
            (cls.root / "inputs" / name).write_bytes(data)
        cls.plan = dict(schema=gate.SCHEMA, candidate_id="synthetic", stage="development", arms=gate.ARMS,
            population=cls.reference("inputs/raw.bin"), frame_size=65536,
            selected_archives={"plain": cls.reference("inputs/P.d2g"), "old": cls.reference("inputs/B.d2g")},
            resources=dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864, swap_bytes=0, wall_seconds=1200),
            phase_cpu_seconds=120, phase_wall_seconds=180, phase_address_bytes=536870912,
            model_spec=kernel.MODEL_SPEC, kernel_basis="synthetic fixture caps only; no corpus admission",
            runtime_files=[dict(path=str(Path(sys.executable).resolve()), bytes=Path(sys.executable).stat().st_size,
                                sha256=gate.driver.sha(Path(sys.executable)))],
            expected_frames=[dict(raw_bytes=len(cls.raw), raw_sha256=digest(cls.raw), model_sha256=rep.fingerprint(cls.model),
                                  repeated_argument_references=1)])
        cls.reference_contract = dict(path="operations/adaptive/experiments/synthetic.json", sha256="sha256:" + "a" * 64)
        cls.gold = cls.root / "results/gold"
        cls.gold.mkdir(parents=True)
        with patch.object(gate, "ROOT", cls.root), patch.object(gate.driver, "ROOT", cls.root), \
             patch.object(gate, "authenticate", return_value=({}, cls.reference_contract, cls.plan)), \
             patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(cls.root / "gold.phases.jsonl")}), \
             contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["--candidate", "gold"])
        if code != 0:
            raise AssertionError((cls.gold / "stage-decision.json").read_text())
        write_json(cls.root / "synthetic-recipe.json", dict(raw_bytes=len(cls.raw), raw_sha256=digest(cls.raw),
            selected_graph_sha256=rep.fingerprint(cls.model), repeated_argument_references=1,
            raw_recipe="<title>Oak</title>Oak is a town. followed by ff00",
            exact_source_copies=[cls.reference(path) for path in sorted({gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE})],
            synthetic_only=True, complete_package_bytes=None, full_corpus_score_bytes=None))

    @classmethod
    def reference(cls, path):
        data = (cls.root / path).read_bytes()
        return dict(path=path, bytes=len(data), sha256=digest(data))

    def setUp(self):
        self.name = self.id().rsplit(".", 1)[-1]
        self.output = self.root / "results" / self.name
        self.output.mkdir()

    def fake_phase(self, directory, phase, argv, plan, marker):
        """Replay retained test artifacts only, never execute another codec."""
        arm, operation = phase.split("-")
        source_suffix = ".raw" if operation == "decode" else ".repeat.d2g" if operation == "repeat" else ".d2g"
        Path(argv[4]).write_bytes((self.gold / (arm + source_suffix)).read_bytes())
        for suffix in (".stdout", ".stderr"):
            shutil.copyfile(self.gold / (phase + suffix), directory / (phase + suffix))
        record = json.loads((self.gold / (phase + ".execution.json")).read_text())
        record["argv"] = argv
        write_json(directory / (phase + ".execution.json"), record)
        return record

    def run_mocked(self, mutate=None, final_error=None):
        def phase(*args):
            record = self.fake_phase(*args)
            if mutate:
                mutate(args[0], args[1], args[2], record)
            return record
        replies = [({}, self.reference_contract, self.plan),
                   final_error if final_error else ({}, self.reference_contract, self.plan)]
        with patch.object(gate, "ROOT", self.root), patch.object(gate.driver, "ROOT", self.root), \
             patch.object(gate, "authenticate", side_effect=replies), patch.object(gate.driver, "run_phase", side_effect=phase), \
             patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(self.root / (self.name + ".phases.jsonl"))}), \
             contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["--candidate", self.name])
        stage = json.loads((self.output / "stage-decision.json").read_text())
        return code, stage

    def corrupt_reports(self, arm, change):
        def mutate(directory, phase, argv, record):
            if phase.startswith(arm + "-"):
                path = directory / (phase + ".stdout")
                wrapper = json.loads(path.read_text())
                change(wrapper["result"])
                write_json(path, wrapper)
        return mutate

    def assert_failed(self, mutation=None, message=None, final_error=None):
        code, stage = self.run_mocked(mutation, final_error)
        self.assertEqual(code, 1)
        self.assertFalse(stage["correctness_pass"])
        self.assertFalse((self.output / "costs-table.json").exists())
        self.assertNotIn("costs", stage)
        self.assertFalse(json.loads((self.output / "artifacts.json").read_text())["complete"])
        if message:
            self.assertIn(message, stage["error"])
        return stage

    def test_native_fifteen_phases_and_all_identities(self):
        stage = json.loads((self.gold / "stage-decision.json").read_text())
        self.assertTrue(stage["correctness_pass"])
        self.assertEqual(stage["native_phases"], 15)
        self.assertEqual((self.gold / "P.d2g").read_bytes(), self.p)
        self.assertEqual((self.gold / "B.d2g").read_bytes(), self.b)
        self.assertEqual(len((self.root / "gold.phases.jsonl").read_text().splitlines()), 30)
        for arm in ("P", "B", "R", "G", "X"):
            with self.subTest(arm=arm):
                self.assertEqual((self.gold / (arm + ".raw")).read_bytes(), self.raw)
                archive = (self.gold / (arm + ".d2g")).read_bytes()
                self.assertEqual(archive, (self.gold / (arm + ".repeat.d2g")).read_bytes())
                row = json.loads((self.gold / (arm + ".result.json")).read_text())
                self.assertEqual(sum(row["accounting"].values()), len(archive))
                self.assertEqual(row["raw_encoder_repeat_proved"], arm == "R")
                if arm in "RGX":
                    reports = [json.loads((self.gold / (arm + "-" + phase + ".stdout")).read_text())["result"]
                               for phase in ("encode", "decode", "repeat")]
                    self.assertEqual(reports[0], reports[1])
                    self.assertEqual(reports[0], reports[2])
                if arm in "BGX":
                    self.assertEqual(row["frames"][0]["model_sha256"], rep.fingerprint(self.model))
                    self.assertEqual(row["repeated_argument_references"], 1)
        repeat = next(row for row in stage["commands"] if row["phase"] == "R-repeat")
        self.assertEqual(Path(repeat["argv"][3]), self.gold / "R.raw")
        self.assertIsNone(stage["costs"]["complete_package_bytes"])
        self.assertIsNone(stage["costs"]["full_corpus_score_bytes"])
        indexed = {row["path"] for row in json.loads((self.gold / "artifacts.json").read_text())["files"]}
        actual = {str(path.relative_to(self.root)) for path in self.gold.iterdir()
                  if path.name not in ("artifacts.json", "stage-decision.json")}
        self.assertEqual(indexed, actual)

    def test_decode_state_drift_rejects(self):
        def mutate(directory, phase, argv, record):
            if phase == "X-decode":
                path = directory / (phase + ".stdout")
                data = json.loads(path.read_text())
                data["result"]["frames"][0]["synchronization"]["state_digest"] = "0" * 64
                write_json(path, data)
        self.assert_failed(mutate, "decoder report or synchronization differs")

    def test_graph_drift_rejects_even_when_three_reports_agree(self):
        self.assert_failed(self.corrupt_reports("G", lambda report: report["frames"][0].update(model_sha256="0" * 64)),
                           "selected frame graph")

    def test_repeated_binding_drift_rejects(self):
        self.assert_failed(self.corrupt_reports("X", lambda report: report["frames"][0].update(repeated_argument_references=0)),
                           "selected frame graph")

    def test_bad_complete_cost_rejects(self):
        self.assert_failed(self.corrupt_reports("G", lambda report: report["costs"].update(content=report["costs"]["content"] + 1)),
                           "complete archive accounting")

    def test_context_flag_drift_rejects(self):
        self.assert_failed(self.corrupt_reports("X", lambda report: report.update(context_enabled=False)), "context flag")

    def test_missing_canonical_reencode_rejects(self):
        self.assert_failed(self.corrupt_reports("X", lambda report: report["frames"][0]["synchronization"].update(canonical_reencode_pass=False)),
                           "synchronization evidence")

    def test_interpreter_schedule_drift_rejects(self):
        self.assert_failed(self.corrupt_reports("X", lambda report: report["frames"][0].update(interpreter_sha256="0" * 64)),
                           "execution schedule differs")

    def test_boundary_state_drift_rejects(self):
        self.assert_failed(self.corrupt_reports("X", lambda report: report["frames"][0].update(boundary_sha256="0" * 64)),
                           "execution schedule differs")

    def test_corrupt_repeat_rejects(self):
        def mutate(directory, phase, argv, record):
            if phase == "R-repeat":
                with Path(argv[4]).open("ab") as stream:
                    stream.write(b"x")
        self.assert_failed(mutate, "deterministic repeat differs")

    def test_failed_final_auth_never_publishes_costs(self):
        stage = self.assert_failed(final_error=ValueError("frozen source changed"), message="Final authentication")
        self.assertEqual(stage["native_phases"], 15)
        self.assertEqual(stage["failure_class"], "infrastructure-failure")
        self.assertFalse(stage["frozen_inputs_reverified"])

    def test_failed_child_classification(self):
        base = dict(timeout=False, error=None, argv=["child"], returncode=1)
        for changes, expected in (({}, "implementation-failure"), ({"timeout": True}, "budget-exhausted"),
                                  ({"error": "missing"}, "infrastructure-failure"), ({"returncode": -9}, "infrastructure-failure")):
            self.assertEqual(gate.classify_failure(ValueError("failure"), dict(base, **changes), self.plan), expected)

    def test_plan_model_spec_resources_and_reference_vector(self):
        plan = copy.deepcopy(self.plan)
        plan["candidate_id"] = "actual_shape"
        plan["population"]["bytes"] = 250000
        plan["expected_frames"] = [dict(raw_bytes=min(65536, 250000 - 65536 * i), raw_sha256="a" * 64,
             model_sha256="b" * 64, repeated_argument_references=[0, 0, 12, 0][i]) for i in range(4)]
        gate.validate_plan(plan, "actual_shape")
        for mutate in (lambda p: p["model_spec"].update(backoff_strength=9),
                       lambda p: p["expected_frames"][2].update(repeated_argument_references=0),
                       lambda p: p.update(phase_cpu_seconds=0), lambda p: p.update(phase_wall_seconds=1201),
                       lambda p: p["resources"].update(wall_seconds=True),
                       lambda p: p["selected_archives"]["old"].update(path="../unbound")):
            changed = copy.deepcopy(plan)
            mutate(changed)
            with self.assertRaises(ValueError):
                gate.validate_plan(changed, "actual_shape")

    def authentication_context(self, inputs=None, plan=None):
        if inputs is None:
            inputs = [dict(id=str(index), path=path, sha256="sha256:" + self.reference(path)["sha256"])
                      for index, path in enumerate({gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE,
                                                    "inputs/P.d2g", "inputs/B.d2g"})]
        contract = dict(inputs=inputs)
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(gate, "ROOT", self.root))
        stack.enter_context(patch.object(gate.driver, "read_json", return_value=contract))
        mocked = stack.enter_context(patch.object(gate.driver, "authenticate", return_value=(contract, self.reference_contract, plan or self.plan)))
        return stack, mocked

    def test_missing_source_rejects_before_legacy_authentication(self):
        for absent in (gate.CODER, gate.SHARED_DRIVER, gate.DECODER, gate.TESTS):
            rows = [dict(path=path) for path in {gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE} if path != absent]
            stack, mocked = self.authentication_context(rows)
            with stack, self.assertRaisesRegex(ValueError, "source closure unbound"):
                gate.authenticate("synthetic", True)
            mocked.assert_not_called()

    def test_frontend_runtime_and_selected_hash_binding(self):
        stack, _ = self.authentication_context()
        with stack:
            self.assertEqual(gate.authenticate("synthetic", True)[2], self.plan)
        for mutate, message in ((lambda p: p["selected_archives"]["plain"].update(sha256="0" * 64), "unbound"),
                                (lambda p: p["runtime_files"][0].update(path="/no/current/interpreter"), "interpreter"),
                                (lambda p: p["selected_archives"].update(plain=p["selected_archives"]["old"]), "frontend")):
            changed = copy.deepcopy(self.plan)
            mutate(changed)
            stack, _ = self.authentication_context(plan=changed)
            with stack, self.assertRaisesRegex(ValueError, message):
                gate.authenticate("synthetic", True)

    def test_validate_only_and_existing_output_do_not_launch(self):
        with patch.object(gate, "authenticate", return_value=({}, self.reference_contract, self.plan)), \
             patch.object(gate.driver, "run_phase") as child, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(["--candidate", "synthetic", "--validate-only"]), 0)
        child.assert_not_called()
        (self.output / "preexisting").write_bytes(b"preserve")
        with patch.object(gate, "ROOT", self.root), patch.object(gate, "authenticate", return_value=({}, self.reference_contract, self.plan)), \
             patch.object(gate.driver, "run_phase") as child, self.assertRaisesRegex(ValueError, "nonempty output"):
            gate.main(["--candidate", self.name])
        child.assert_not_called()
        self.assertEqual((self.output / "preexisting").read_bytes(), b"preserve")


if __name__ == "__main__":
    unittest.main()
