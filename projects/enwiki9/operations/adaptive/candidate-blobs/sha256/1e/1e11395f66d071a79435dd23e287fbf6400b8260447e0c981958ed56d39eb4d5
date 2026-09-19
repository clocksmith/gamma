"""Synthetic fixed-program runner checks; authentication is mocked only for fixtures."""
import copy
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_reserialize_gate_v1 as gate
from tools import dualstream_grammar_gate_v1 as legacy_gate


class ReserializeGateTests(unittest.TestCase):
    def plan(self):
        return json.loads((ROOT / "operations/provenance/dualstream_grammar_reserialize250k_q0_v1_plan.json").read_text())

    def test_frozen_four_cells_and_resource_bounds_are_required(self):
        plan = self.plan()
        gate.validate_plan(plan, plan["candidate_id"])
        for field, value in (("arms", plan["arms"][:-1]), ("stage", "confirmation"),
                             ("phase_cpu_seconds", 16), ("phase_wall_seconds", 21),
                             ("frame_size", 1), ("selected_archives", {})):
            with self.subTest(field=field):
                modified = copy.deepcopy(plan)
                modified[field] = value
                with self.assertRaises(gate.driver.codec.CodecError):
                    gate.validate_plan(modified, plan["candidate_id"])
        self.assertEqual(legacy_gate.CODEC, "tools/dualstream_grammar_v1.py")
        self.assertEqual(legacy_gate.SELF, "tools/dualstream_grammar_gate_v1.py")

    def test_shared_driver_cannot_be_omitted_from_frozen_inputs(self):
        contract = {"inputs": [dict(path=path, sha256="sha256:" + "0" * 64)
                               for path in gate.DECODERS.values()]}
        with patch.object(gate.driver, "authenticate", return_value=(contract, {}, self.plan())):
            with self.assertRaisesRegex(gate.driver.codec.CodecError, "shared driver"):
                gate.authenticate("fixture", validate_only=True)

    def fixture(self, stack, actual=False):
        root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        (root / "tools").symlink_to(ROOT / "tools", target_is_directory=True)
        directory = root / "results/fixture"
        directory.mkdir(parents=True)
        raw = b'<page><title>Oak</title><text>Oak is a town.</text></page>\r\n' * 4
        (root / "raw").write_bytes(raw)
        plan = self.plan()
        plan.update(candidate_id="fixture", population=dict(path="raw", bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        if actual:
            from tools import dualstream_grammar_v1 as old
            from tools import dualstream_grammar_argtokens_v2 as new
            archives = {name: codec.encode(raw, mode="parameter", config=codec.Config(
                max_rule_length=4, grammar_budget=16, min_benefit=1, shortlist=4))[0]
                        for name, codec in (("old", old), ("new", new))}
            archives["plain"] = old.encode(raw, mode="plain")[0]
        else:
            archives = {"old": b"old-selected-archive", "new": b"new-selected-archive", "plain": b"plain"}
        for name, value in archives.items():
            path = root / (name + ".d2g")
            path.write_bytes(value)
            plan["selected_archives"][name] = dict(path=path.name, bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
        stack.enter_context(patch.object(gate, "ROOT", root))
        stack.enter_context(patch.object(gate.driver, "ROOT", root))
        authentication = stack.enter_context(patch.object(gate, "authenticate", return_value=(
            {}, {"path": "fixture-contract.json", "sha256": "sha256:" + "0" * 64}, plan)))
        stack.enter_context(patch.dict(os.environ, {"GAMMA_RESOURCE_PHASE_MARKERS": str(root / "phases.jsonl")}))
        return root, directory, raw, plan, authentication

    def fake_phase(self, raw, plan, mutation=None, failed_phase=None):
        def run(directory, phase, argv, active_plan, marker):
            arm_id, operation = phase.split("-")
            arm = next(row for row in plan["arms"] if row["id"] == arm_id)
            source, output = Path(argv[3]), Path(argv[4])
            if phase == failed_phase:
                return dict(phase=phase, argv=argv, returncode=-9, timeout=True, error=None)
            if operation == "decode":
                output.write_bytes(raw)
                report = {"raw_bytes": len(raw)}
            else:
                payload = source.read_bytes() if arm["selection"] == arm["storage"] else (
                    arm_id.encode() + source.read_bytes())
                output.write_bytes(payload)
                report = dict(repeat_scope=gate.REPEAT_SCOPE, selection_version=arm["selection"],
                              storage_version=arm["storage"], input_archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                              program_identity_pass=True, fixed_sections_pass=True,
                              raw_encoder_repeat_proved=False, frame_size=plan["frame_size"],
                              raw_sha256=hashlib.sha256(raw).hexdigest(),
                              complete_archive_bytes=len(payload), raw_bytes=len(raw),
                              frames=[dict(model_sha256=hashlib.sha256(arm["selection"].encode()).hexdigest(),
                                           mode="parameter", raw_offset=0, raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
                                           fixed_sections_sha256={key: "a" * 64 for key in ("programs", "structure", "content")},
                                           repeated_argument_references=2, supplied_arguments=1, templates=1)],
                              **{key: len(payload) if key == "framing_bytes" else 0 for key in gate.ACCOUNTING})
            if mutation:
                mutation(phase, output, report)
            (directory / (phase + ".stdout")).write_text(json.dumps(dict(result=report, cpu_seconds=0.01, peak_process_rss_kib=100)))
            return dict(phase=phase, argv=argv, returncode=0, timeout=False, error=None)
        return run

    def test_fixed_archives_source_all_encode_and_repeat_commands(self):
        with ExitStack() as stack:
            root, directory, raw, plan, authentication = self.fixture(stack)
            stack.enter_context(patch.object(gate.driver, "run_phase", side_effect=self.fake_phase(raw, plan)))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["--candidate", "fixture"]), 0)
            stage = gate.driver.read_json(directory / "stage-decision.json")
            self.assertEqual(stage["native_phases"], 12)
            self.assertEqual(authentication.call_count, 2)
            self.assertTrue(stage["paired_program_identity_pass"])
            for command in stage["commands"]:
                arm_id, phase = command["phase"].split("-")
                arm = next(row for row in plan["arms"] if row["id"] == arm_id)
                argv = command["argv"]
                if phase == "decode":
                    self.assertEqual(argv[1], str(root / gate.DECODERS[arm["storage"]]))
                else:
                    self.assertEqual(argv[3], str(root / plan["selected_archives"][arm["selection"]]["path"]))
                    self.assertEqual(argv[-2:], ["--storage", arm["storage"]])
            table = gate.driver.read_json(directory / "costs-table.json")
            self.assertFalse(table["promotion_authority"])
            self.assertFalse(table["plain_reference_redecoded_here"])
            self.assertIsNone(stage["full_corpus_score_bytes"])

    def test_program_fixed_section_and_accounting_failure_block_table(self):
        for mutation_name in ("model", "sections", "accounting", "identity", "raw", "repeat", "diagonal",
                              "mode", "frame_offset", "raw_repeat"):
            with self.subTest(mutation=mutation_name), ExitStack() as stack:
                _, directory, raw, plan, _ = self.fixture(stack)

                def mutate(phase, output, report):
                    if mutation_name == "model" and phase.startswith("ON-") and "frames" in report:
                        report["frames"][0]["model_sha256"] = "b" * 64
                    if mutation_name == "sections" and phase.startswith("ON-") and "frames" in report:
                        report["frames"][0]["fixed_sections_sha256"]["programs"] = "b" * 64
                    if mutation_name == "accounting" and phase in ("OO-encode", "OO-repeat"):
                        report["framing_bytes"] += 1
                    if mutation_name == "identity" and phase in ("OO-encode", "OO-repeat"):
                        report["program_identity_pass"] = False
                    if mutation_name == "raw" and phase == "OO-decode":
                        output.write_bytes(raw + b"x")
                    if mutation_name == "repeat" and phase == "OO-repeat":
                        output.write_bytes(output.read_bytes() + b"x")
                    if mutation_name == "diagonal" and phase in ("OO-encode", "OO-repeat"):
                        output.write_bytes(b"X" + output.read_bytes()[1:])
                    if mutation_name == "mode" and phase.startswith("ON-") and "frames" in report:
                        report["frames"][0]["mode"] = "split"
                    if mutation_name == "frame_offset" and phase in ("OO-encode", "OO-repeat"):
                        report["frames"][0]["raw_offset"] = 1
                    if mutation_name == "raw_repeat" and phase in ("OO-encode", "OO-repeat"):
                        report["raw_encoder_repeat_proved"] = True

                stack.enter_context(patch.object(gate.driver, "run_phase", side_effect=self.fake_phase(raw, plan, mutate)))
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(gate.main(["--candidate", "fixture"]), 1)
                stage = gate.driver.read_json(directory / "stage-decision.json")
                self.assertFalse(stage["correctness_pass"])
                self.assertEqual(stage["failure_class"], "implementation-failure")
                self.assertFalse((directory / "costs-table.json").exists())
                self.assertFalse(gate.driver.read_json(directory / "artifacts.json")["complete"])

    def test_child_budget_failure_keeps_closed_phase_and_blocks_followups(self):
        with ExitStack() as stack:
            _, directory, raw, plan, _ = self.fixture(stack)
            stack.enter_context(patch.object(gate.driver, "run_phase", side_effect=self.fake_phase(raw, plan, failed_phase="OO-repeat")))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["--candidate", "fixture"]), 1)
            stage = gate.driver.read_json(directory / "stage-decision.json")
            self.assertEqual(stage["native_phases"], 3)
            self.assertEqual(stage["arms"], [])
            self.assertEqual(stage["failure_class"], "budget-exhausted")

    def test_final_authentication_failure_blocks_stage(self):
        with ExitStack() as stack:
            _, directory, raw, plan, authentication = self.fixture(stack)
            authenticated = authentication.return_value
            authentication.side_effect = [authenticated, ValueError("changed frozen source")]
            stack.enter_context(patch.object(gate.driver, "run_phase", side_effect=self.fake_phase(raw, plan)))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["--candidate", "fixture"]), 1)
            stage = gate.driver.read_json(directory / "stage-decision.json")
            self.assertFalse(stage["frozen_inputs_reverified"])
            self.assertEqual(stage["failure_class"], "infrastructure-failure")
            self.assertFalse((directory / "costs-table.json").exists())
            self.assertNotIn("costs", stage)

    def test_real_synthetic_fixed_program_subprocess_roundtrips(self):
        if not (ROOT / gate.driver.CODEC).exists():
            self.skipTest("adapter implementation is not yet available")
        with ExitStack() as stack:
            root, directory, raw, plan, _ = self.fixture(stack, actual=True)
            before = {name: (root / row["path"]).read_bytes() for name, row in plan["selected_archives"].items()}
            with redirect_stdout(io.StringIO()):
                result = gate.main(["--candidate", "fixture"])
            stage = gate.driver.read_json(directory / "stage-decision.json")
            self.assertEqual(result, 0, stage.get("error"))
            self.assertEqual(stage["native_phases"], 12)
            for arm in gate.ARMS:
                self.assertEqual((directory / (arm["id"] + ".raw")).read_bytes(), raw)
                self.assertEqual((directory / (arm["id"] + ".d2g")).read_bytes(),
                                 (directory / (arm["id"] + ".repeat.d2g")).read_bytes())
            self.assertEqual({name: (root / row["path"]).read_bytes() for name, row in plan["selected_archives"].items()}, before)
            self.assertEqual(len((root / "phases.jsonl").read_text().splitlines()), 24)


if __name__ == "__main__":
    unittest.main()
