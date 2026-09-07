"""Two predetermined synthetic populations; no corpus or selector search."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import random
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_literal_first_gate_v1 as gate
from tools import dualstream_literal_first_v1 as codec
from tools import dualstream_grammar_argtokens_v2 as plain

PROJECT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def favorable():
    # Exact previously selected codec-author fixture; no local sweep.
    rng = random.Random(712)
    records = []
    for _ in range(96):
        value = bytes(rng.choice(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for _ in range(180))
        records.append(b"<page><title>" + value + b"</title><text>" + value
                       + b" is an exact repeated field.</text></page>\n")
    return b"".join(records)


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="literal_first_gate_"))
        for source in {gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE}:
            target = cls.root / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / source, target)
        cls.raws = dict(favorable=favorable(), fallback=random.Random(491).randbytes(2048))
        cls.plans, cls.golds = {}, {}
        cls.contract_ref = dict(path="operations/adaptive/experiments/synthetic.json", sha256="sha256:" + "a" * 64)
        for name, raw in cls.raws.items():
            inputs = cls.root / "inputs" / name
            inputs.mkdir(parents=True)
            (inputs / "raw.bin").write_bytes(raw)
            (inputs / "P.d2g").write_bytes(plain.encode(raw, mode="plain")[0])
            plan = dict(schema=gate.SCHEMA, candidate_id=name, stage="development", arms=gate.ARMS,
                population=cls.ref(inputs / "raw.bin"), plain_archive=cls.ref(inputs / "P.d2g"), frame_size=65536,
                resources=dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864, swap_bytes=0, wall_seconds=300),
                phase_cpu_seconds=60, phase_wall_seconds=90, phase_address_bytes=536870912,
                search_spec=codec.SEARCH_SPEC, kernel_basis="predetermined synthetic author fixtures; no corpus admission",
                runtime_files=[dict(path=str(Path(sys.executable).resolve()), bytes=Path(sys.executable).stat().st_size,
                                    sha256=gate.driver.sha(Path(sys.executable)))])
            gold = cls.root / "results" / ("gold_" + name)
            gold.mkdir(parents=True)
            with patch.object(gate, "ROOT", cls.root), patch.object(gate.driver, "ROOT", cls.root), \
                 patch.object(gate, "authenticate", return_value=({}, cls.contract_ref, plan)), \
                 patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(cls.root / (name + ".phases.jsonl"))}), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = gate.main(["--candidate", gold.name])
            if code:
                raise AssertionError((gold / "stage-decision.json").read_text())
            cls.plans[name], cls.golds[name] = plan, gold
        write(cls.root / "recipe.json", dict(fixtures={name: dict(raw_bytes=len(raw), raw_sha256=sha(raw))
            for name, raw in cls.raws.items()}, favorable="Random712;96 page records;180 ASCII alnum bytes repeated in title and text",
            fallback="Random491.randbytes(2048)", corpus_bytes_opened=0, synthetic_only=True,
            source_copies=[cls.ref(cls.root / path) for path in sorted({gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE})]))

    @classmethod
    def ref(cls, path):
        data = path.read_bytes()
        return dict(path=str(path.relative_to(cls.root)), bytes=len(data), sha256=sha(data))

    def setUp(self):
        self.name = self.id().rsplit(".", 1)[-1]
        self.output = self.root / "results" / self.name
        self.output.mkdir()
        self.plan = self.plans["favorable"]
        self.gold = self.golds["favorable"]

    def fake_phase(self, directory, phase, argv, plan, marker):
        arm, operation = phase.split("-")
        suffix = ".raw" if operation == "decode" else ".repeat.d2g" if operation == "repeat" else ".d2g"
        Path(argv[4]).write_bytes((self.gold / (arm + suffix)).read_bytes())
        for suffix in (".stdout", ".stderr"):
            shutil.copyfile(self.gold / (phase + suffix), directory / (phase + suffix))
        record = json.loads((self.gold / (phase + ".execution.json")).read_text())
        record["argv"] = argv
        write(directory / (phase + ".execution.json"), record)
        return record

    def run_mocked(self, mutation=None, final_error=None):
        def phase(*args):
            record = self.fake_phase(*args)
            if mutation:
                mutation(args[0], args[1], args[2], record)
            return record
        replies = [({}, self.contract_ref, self.plan), final_error if final_error else ({}, self.contract_ref, self.plan)]
        with patch.object(gate, "ROOT", self.root), patch.object(gate.driver, "ROOT", self.root), \
             patch.object(gate, "authenticate", side_effect=replies), patch.object(gate.driver, "run_phase", side_effect=phase), \
             patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(self.root / (self.name + ".phases.jsonl"))}), \
             contextlib.redirect_stdout(io.StringIO()):
            code = gate.main(["--candidate", self.name])
        stage = json.loads((self.output / "stage-decision.json").read_text())
        return code, stage

    def mutate_reports(self, arm, change):
        def mutation(directory, phase, argv, record):
            if phase.startswith(arm + "-"):
                path = directory / (phase + ".stdout")
                wrapper = json.loads(path.read_text())
                change(wrapper["result"])
                write(path, wrapper)
        return mutation

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

    def test_actual_eighteen_phases_strict_gain_and_exact_fallback(self):
        for name, gold in self.golds.items():
            stage = json.loads((gold / "stage-decision.json").read_text())
            self.assertTrue(stage["correctness_pass"])
            self.assertTrue(stage["raw_encoder_repeat_proved"])
            self.assertEqual(stage["native_phases"], 9)
            self.assertEqual((gold / "P.d2g").read_bytes(), (gold / "K.d2g").read_bytes())
            self.assertEqual(len((self.root / (name + ".phases.jsonl")).read_text().splitlines()), 18)
            table = stage["costs"]
            self.assertEqual(table["strict_d_improvement"], name == "favorable")
            self.assertEqual(table["confirmation_eligible"], name == "favorable")
            self.assertFalse(table["fallback_equality_authorizes_confirmation"])
            self.assertIsNone(table["complete_package_bytes"])
            self.assertIsNone(table["full_corpus_score_bytes"])
            for arm in ("P", "K", "D"):
                self.assertEqual((gold / (arm + ".raw")).read_bytes(), self.raws[name])
                self.assertEqual((gold / (arm + ".d2g")).read_bytes(), (gold / (arm + ".repeat.d2g")).read_bytes())
                row = json.loads((gold / (arm + ".result.json")).read_text())
                self.assertEqual(sum(row["accounting"].values()), row["archive_bytes"])
                repeat = next(row for row in stage["commands"] if row["phase"] == arm + "-repeat")
                self.assertEqual(Path(repeat["argv"][3]), gold / (arm + ".raw"))
                self.assertEqual(repeat["argv"][5:], ["--mode", "plain" if arm == "P" else arm, "--frame-size", "65536"])
            indexed = {row["path"] for row in json.loads((gold / "artifacts.json").read_text())["files"]}
            self.assertEqual(indexed, {str(path.relative_to(self.root)) for path in gold.iterdir()
                                      if path.name not in ("artifacts.json", "stage-decision.json")})
        favorable_d = json.loads((self.golds["favorable"] / "D.result.json").read_text())
        self.assertGreater(favorable_d["selected_rules"], 0)
        self.assertGreater(favorable_d["repeated_argument_references"], 0)
        self.assertEqual((self.golds["fallback"] / "D.d2g").read_bytes(), (self.golds["fallback"] / "P.d2g").read_bytes())

    def test_p_k_mismatch_rejects(self):
        def mutation(directory, phase, argv, record):
            if phase in ("K-encode", "K-repeat"):
                with Path(argv[4]).open("ab") as stream:
                    stream.write(b"x")
        self.assert_failed(mutation, "P/K archive identity")

    def test_search_repeat_drift_rejects(self):
        def mutation(directory, phase, argv, record):
            if phase == "D-repeat":
                path = directory / (phase + ".stdout")
                wrapper = json.loads(path.read_text())
                wrapper["result"]["frames"][0]["search"]["proposal_sha256"] = "0" * 64
                write(path, wrapper)
        self.assert_failed(mutation, "raw-discovery repeat report")

    def test_independent_boundary_state_drift_rejects(self):
        def mutation(directory, phase, argv, record):
            if phase == "D-decode":
                path = directory / (phase + ".stdout")
                wrapper = json.loads(path.read_text())
                wrapper["result"]["frames"][0]["boundary_sha256"] = "0" * 64
                write(path, wrapper)
        self.assert_failed(mutation, "independent decoder projection")

    def test_corrupt_inverse_rejects(self):
        def mutation(directory, phase, argv, record):
            if phase == "K-decode":
                Path(argv[4]).write_bytes(b"wrong")
        self.assert_failed(mutation, "independent inverse")

    def test_bad_joint_cost_rejects(self):
        self.assert_failed(self.mutate_reports("D", lambda report: report["costs"].update(
            deflate_payload=report["costs"]["deflate_payload"] + 1)), "complete archive accounting")

    def test_representation_cost_domain_rejects(self):
        self.assert_failed(self.mutate_reports("D", lambda report: report["frames"][0]["representation_costs"].update(
            guessed_compressed_argument_bytes=1)), "pre-Deflate representation costs")

    def test_frozen_search_spec_rejects(self):
        def mutation(directory, phase, argv, record):
            if phase in ("D-encode", "D-repeat"):
                path = directory / (phase + ".stdout")
                wrapper = json.loads(path.read_text())
                wrapper["result"]["search_spec"]["min_frame_benefit"] = 0
                write(path, wrapper)
        self.assert_failed(mutation, "search or report scope")

    def test_mismatched_proposal_pool_rejects(self):
        def mutation(directory, phase, argv, record):
            if phase in ("D-encode", "D-repeat"):
                path = directory / (phase + ".stdout")
                wrapper = json.loads(path.read_text())
                wrapper["result"]["frames"][0]["search"]["proposal_sha256"] = "0" * 64
                write(path, wrapper)
        self.assert_failed(mutation, "proposal pool differs")

    def test_non_strict_or_discontinuous_admission_rejects(self):
        rows = [json.loads((self.gold / (arm + ".result.json")).read_text()) for arm in ("P", "K", "D")]
        changed = copy.deepcopy(rows)
        chosen = next(row for row in changed[2]["frames"][0]["search"]["evaluations"] if row["accepted"])
        chosen["delta"] = 0
        with patch.object(gate, "ROOT", self.root), self.assertRaisesRegex(ValueError, "complete-cost measurements|non-strict"):
            gate.comparison_table(changed, self.plan)

    def test_final_auth_failure_never_publishes_costs(self):
        stage = self.assert_failed(final_error=ValueError("source replaced"), message="Final authentication")
        self.assertEqual(stage["native_phases"], 9)
        self.assertFalse(stage["frozen_inputs_reverified"])
        self.assertEqual(stage["failure_class"], "infrastructure-failure")

    def test_projection_excludes_only_declared_encoder_evidence(self):
        encode = json.loads((self.gold / "D-encode.stdout").read_text())["result"]
        decode = json.loads((self.gold / "D-decode.stdout").read_text())["result"]
        self.assertEqual(gate.common_report(encode), decode)
        changed = copy.deepcopy(encode)
        changed["unexpected_decoder_dependency"] = "unbound"
        self.assertNotEqual(gate.common_report(changed), decode)
        self.assertFalse(encode["raw_encoder_repeat_proved"])
        self.assertNotIn("mode", decode)

    def test_plan_shape_bounds_and_search_binding(self):
        plan = copy.deepcopy(self.plan)
        plan["candidate_id"] = "actual_shape"
        plan["population"]["bytes"] = 250000
        plan["plain_archive"]["bytes"] = 89041
        gate.validate_plan(plan, "actual_shape")
        for mutate in (lambda p: p["search_spec"].update(min_frame_benefit=0),
                       lambda p: p["plain_archive"].update(bytes=89040), lambda p: p.update(phase_cpu_seconds=0),
                       lambda p: p["resources"].update(wall_seconds=True),
                       lambda p: p["population"].update(path="../corpus")):
            changed = copy.deepcopy(plan)
            mutate(changed)
            with self.assertRaises(ValueError):
                gate.validate_plan(changed, "actual_shape")

    def auth_context(self, inputs=None, plan=None):
        if inputs is None:
            paths = {gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE, self.plan["plain_archive"]["path"]}
            inputs = [dict(path=path, sha256="sha256:" + self.ref(self.root / path)["sha256"]) for path in paths]
        contract = dict(inputs=inputs)
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(gate, "ROOT", self.root))
        stack.enter_context(patch.object(gate.driver, "read_json", return_value=contract))
        mocked = stack.enter_context(patch.object(gate.driver, "authenticate", return_value=(contract, self.contract_ref, plan or self.plan)))
        return stack, mocked

    def test_missing_source_and_runtime_or_baseline_drift_reject(self):
        for absent in (gate.PLAIN, gate.CODEC, gate.SHARED_DRIVER, gate.TESTS):
            rows = [dict(path=path) for path in {gate.SELF, gate.SHARED_DRIVER, gate.TESTS, *gate.PACKAGE} if path != absent]
            stack, mocked = self.auth_context(rows)
            with stack, self.assertRaisesRegex(ValueError, "source closure"):
                gate.authenticate("synthetic", True)
            mocked.assert_not_called()
        stack, _ = self.auth_context()
        with stack:
            self.assertEqual(gate.authenticate("synthetic", True)[2], self.plan)
        for mutate, message in ((lambda p: p["plain_archive"].update(sha256="0" * 64), "unbound"),
                                (lambda p: p["runtime_files"][0].update(path="/not/current/interpreter"), "interpreter")):
            changed = copy.deepcopy(self.plan)
            mutate(changed)
            stack, _ = self.auth_context(plan=changed)
            with stack, self.assertRaisesRegex(ValueError, message):
                gate.authenticate("synthetic", True)

    def test_validate_only_and_preexisting_output_do_not_launch(self):
        with patch.object(gate, "authenticate", return_value=({}, self.contract_ref, self.plan)), \
             patch.object(gate.driver, "run_phase") as child, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(["--candidate", "synthetic", "--validate-only"]), 0)
        child.assert_not_called()
        (self.output / "existing").write_bytes(b"preserve")
        with patch.object(gate, "ROOT", self.root), patch.object(gate, "authenticate", return_value=({}, self.contract_ref, self.plan)), \
             patch.object(gate.driver, "run_phase") as child, self.assertRaisesRegex(ValueError, "nonempty output"):
            gate.main(["--candidate", self.name])
        child.assert_not_called()
        self.assertEqual((self.output / "existing").read_bytes(), b"preserve")

    def test_failure_classification(self):
        base = dict(timeout=False, error=None, argv=["child"], returncode=1)
        for changes, expected in (({}, "implementation-failure"), ({"timeout": True}, "budget-exhausted"),
                                  ({"error": "missing"}, "infrastructure-failure"), ({"returncode": -9}, "infrastructure-failure")):
            self.assertEqual(gate.classify_failure(ValueError("failure"), dict(base, **changes), self.plan), expected)


if __name__ == "__main__":
    unittest.main()
