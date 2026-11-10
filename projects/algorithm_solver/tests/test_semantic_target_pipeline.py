"""Synthetic family-boundary and target-builder tests, not solving evidence."""
import copy
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest

from algsolve.records import LANE_ROOT, Problem
from algsolve.synth import semantic_target_pipeline as pipeline


def metadata(uid, family, *, key=None, aliases=None, groups=None):
    return {
        "uid": uid, "key": key or "lc:" + uid, "family": family,
        "aliases": aliases or [], "structural_groups": groups or [],
        "problem_sha256": "1" * 64, "independent_tests_sha256": "2" * 64,
    }


def boundary(**updates):
    value = {"uids": [], "keys": [], "families": [], "structural_groups": [],
             "sources_sha256": {"synthetic-reservation-metadata": "3" * 64}}
    value.update(updates)
    return value


class FamilyPlanTests(unittest.TestCase):
    def fixture(self):
        return [metadata("fit", "fit"), metadata("held", "held"),
                metadata("protected", "secret", key="lc:secret-ii")]

    def test_metadata_only_split_is_deterministic_and_does_not_mutate_inputs(self):
        rows = self.fixture()
        saved = copy.deepcopy(rows)
        limits = boundary(keys=["lc:secret"])
        plan = pipeline.freeze_plan(rows, limits, ["held"])
        self.assertEqual(rows, saved)
        self.assertEqual(plan, pipeline.freeze_plan(list(reversed(rows)), limits, ["held"]))
        self.assertEqual({row["uid"]: row["split"] for row in plan["rows"]},
                         {"fit": "development_fit", "held": "heldout_family", "protected": "excluded_existing"})
        self.assertEqual(pipeline.validate_plan(plan), plan)

    def test_alias_family_and_predeclared_structure_closure_precedes_generation(self):
        rows = self.fixture() + [
            metadata("alias", "other", aliases=["protected"], groups=["shape-a"]),
            metadata("shape", "shape-family", groups=["shape-a"]),
            metadata("relative", "shape-family"),
            metadata("held-variant", "held"),
        ]
        plan = pipeline.freeze_plan(rows, boundary(uids=["protected"]), ["held"])
        splits = {row["uid"]: row["split"] for row in plan["rows"]}
        for uid in ("protected", "alias", "shape", "relative"):
            self.assertEqual(splits[uid], "excluded_existing")
        self.assertEqual(splits["held-variant"], "heldout_family")
        self.assertEqual(splits["fit"], "development_fit")

    def test_roman_suffix_cannot_hide_protected_family(self):
        rows = self.fixture()
        rows[-1]["family"] = "misleading-independent-label"
        plan = pipeline.freeze_plan(rows, boundary(keys=["lc:secret-iii"]), ["held"])
        self.assertEqual(plan["rows"][-1]["split"], "excluded_existing")

    def test_existing_reservations_take_precedence_over_new_holdout(self):
        rows = self.fixture() + [metadata("second-held", "second-held")]
        plan = pipeline.freeze_plan(rows, boundary(families=["held"]), ["held", "second-held"])
        self.assertEqual(next(row["split"] for row in plan["rows"] if row["uid"] == "held"), "excluded_existing")

    def test_payload_fields_and_missing_authority_are_rejected(self):
        for field in ("statement", "reference_solutions", "tests", "program"):
            rows = self.fixture()
            rows[0][field] = "not identity metadata"
            with self.assertRaisesRegex(ValueError, "no payloads"):
                pipeline.freeze_plan(rows, boundary(), ["held"])
        with self.assertRaisesRegex(ValueError, "source hashes"):
            pipeline.freeze_plan(self.fixture(), boundary(sources_sha256={}), ["held"])

    def test_unknown_empty_or_all_connected_holdouts_fail_closed(self):
        for holdouts in ([], ["missing"], ["fit", "held", "secret"]):
            with self.assertRaises(ValueError):
                pipeline.freeze_plan(self.fixture(), boundary(), holdouts)
        rows = self.fixture()
        rows[0]["aliases"] = ["held"]
        with self.assertRaises(ValueError):
            pipeline.freeze_plan(rows, boundary(families=["secret"]), ["held"])

    def test_duplicate_uid_and_assignment_tampering_are_rejected(self):
        rows = self.fixture()
        with self.assertRaisesRegex(ValueError, "unique"):
            pipeline.freeze_plan(rows + [rows[0]], boundary(), ["held"])
        plan = pipeline.freeze_plan(rows, boundary(), ["held"])
        plan["rows"][1]["split"] = "development_fit"
        with self.assertRaisesRegex(ValueError, "changed"):
            pipeline.validate_plan(plan)

    def test_plan_is_write_once(self):
        plan = pipeline.freeze_plan(self.fixture(), boundary(), ["held"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            pipeline.write_plan(path, plan)
            with self.assertRaises(FileExistsError):
                pipeline.write_plan(path, plan)


class TargetBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.problem = Problem("fit", "synthetic", "fit", "Count values", "fit", "Count values.", "functional",
                               entry={"class": "Solution", "method": "length"}, params=[["values", "List[int]"]],
                               evidence_ceiling="independent_tests_passed",
                               reference_solutions=["NEVER SEND REFERENCE TO TEACHER"],
                               public_tests=[{"args": [[1]], "expected": 1}], license="synthetic",
                               attribution="synthetic unit test")
        self.tests = [{"args": [[1, 2, 3]], "expected": 3}]
        self.proposal = {
            "variant": "length", "requirements": {"unsupported_requirements": []},
            "bound_probe": {"args": [[1, 2]], "expected": 2},
            "program": {"schema": "algsolve.typed-program.v2", "parameters": ["values"],
                        "inputs": {"values": ["list", "int"]}, "body": [],
                        "return": {"op": "len", "args": [{"ref": "values"}]}, "output_type": "int"},
        }
        rows = [metadata("fit", "fit"), metadata("held", "held"), metadata("protected", "secret")]
        rows[0]["problem_sha256"] = pipeline.digest(json.loads(self.problem.to_json()))
        rows[0]["independent_tests_sha256"] = pipeline.digest(self.tests)
        self.plan = pipeline.freeze_plan(rows, boundary(families=["secret"]), ["held"])
        self.plan_path = self.root / "plan.json"
        pipeline.write_plan(self.plan_path, self.plan)
        self.events = []

    def load_problem(self, row):
        self.assertEqual(row["uid"], "fit")
        self.events.append("payload")
        return copy.deepcopy(self.problem)

    def propose(self, uid, model_input, plan_sha):
        self.assertTrue(self.plan_path.exists())
        self.assertEqual(uid, "fit")
        self.assertEqual(plan_sha, self.plan["plan_sha256"])
        self.assertEqual(set(model_input), {"statement", "starter_code", "params", "public_examples"})
        self.assertNotIn("NEVER SEND REFERENCE", json.dumps(model_input))
        self.assertNotIn(self.tests[0], model_input["public_examples"])
        self.events.append("teacher")
        return [copy.deepcopy(self.proposal)]

    def load_tests(self, row):
        self.assertEqual(row["uid"], "fit")
        self.assertEqual(self.events[:2], ["payload", "teacher"])
        self.events.append("tests")
        return copy.deepcopy(self.tests)

    def judge(self, problem, source, cases):
        self.assertIn("def length", source)
        compile(source, "<test-target>", "exec")
        self.events.append("judge")
        return SimpleNamespace(to_dict=lambda: {"passed": True, "tests_passed": len(cases),
                                               "tests_total": len(cases), "reason": "passed"})

    def build(self, **updates):
        args = {"codec_path": LANE_ROOT / "contracts/typed_codec_v1.json", "teacher_identity": "synthetic-unit-test",
                "load_problem": self.load_problem, "propose": self.propose,
                "load_independent_tests": self.load_tests, "judge": self.judge}
        args.update(updates)
        return pipeline.build_targets(self.plan_path, self.root / "output", **args)

    def receipt(self):
        return json.loads(next((self.root / "output/attempts").glob("*-receipt.json")).read_text())

    def test_freezes_before_any_payload_and_never_calls_adapters_for_holdouts(self):
        summary = self.build()
        self.assertEqual(self.events, ["payload", "teacher", "tests", "judge", "judge", "judge"])
        self.assertEqual(summary["emitted_pairs"], 1)
        self.assertEqual(summary["training_eligible_pairs"], 0)  # Mock receipts never authorize training.
        self.assertEqual(summary["counts"]["excluded_existing"], 1)
        self.assertEqual(summary["counts"]["heldout_family"], 1)
        pair = json.loads((self.root / "output/pairs.jsonl").read_text())
        self.assertEqual(pair["learning_split"], "development_fit")
        self.assertNotIn("independent_tests", pair["input"])
        self.assertFalse(pair["training_eligible"])
        self.assertEqual(self.receipt()["proposals"][0]["reason"], "qualified_test_double")

    def test_problem_hash_drift_blocks_before_teacher(self):
        self.problem.statement = "changed"
        summary = self.build()
        self.assertEqual(self.events, ["payload"])
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertEqual(self.receipt()["stage"], "load_problem")

    def test_independent_test_hash_drift_preserves_proposal_and_blocks_execution(self):
        self.tests[0]["expected"] = 99
        summary = self.build()
        self.assertEqual(self.events, ["payload", "teacher", "tests"])
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertEqual(self.receipt()["raw_proposals"], [self.proposal])

    def test_compiler_rejects_bad_ast_without_execution(self):
        self.proposal["program"]["return"] = {"ref": "unbound"}
        summary = self.build()
        self.assertEqual(summary["counts"]["rejected"], 1)
        self.assertNotIn("judge", self.events)
        self.assertEqual(self.receipt()["proposals"][0]["stage"], "compile")

    def test_independent_failure_stops_before_bound_and_keeps_rejection(self):
        def judge(problem, source, cases):
            self.events.append("judge")
            passed = cases != self.tests
            return SimpleNamespace(to_dict=lambda: {"passed": passed, "tests_passed": len(cases) if passed else 0,
                                                   "tests_total": len(cases), "reason": "passed" if passed else "wrong_answer"})
        summary = self.build(judge=judge)
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertEqual(self.events.count("judge"), 2)
        self.assertEqual(self.receipt()["proposals"][0]["stage"], "independent")

    def test_unavailable_sandbox_has_no_unsandboxed_fallback(self):
        def unavailable(*args):
            raise RuntimeError("sandbox unavailable")
        summary = self.build(judge=unavailable)
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertIn("sandbox unavailable", self.receipt()["proposals"][0]["error"])

    def test_incomplete_truthy_or_wrong_test_count_receipts_fail_closed(self):
        for verdict in ({"passed": True}, {"passed": 1, "tests_passed": 1, "tests_total": 1},
                        {"passed": True, "tests_passed": 0, "tests_total": 1}):
            self.assertFalse(pipeline._passed(verdict, [self.tests[0]]))

    def test_teacher_inputs_are_copied_and_cannot_rewrite_public_tests(self):
        def teacher(uid, model_input, plan_sha):
            proposals = self.propose(uid, model_input, plan_sha)
            model_input["public_examples"][0]["expected"] = 999
            return proposals
        summary = self.build(propose=teacher)
        self.assertEqual(summary["emitted_pairs"], 1)
        pair = json.loads((self.root / "output/pairs.jsonl").read_text())
        self.assertEqual(pair["input"]["public_examples"][0]["expected"], 1)

    def test_teacher_exception_is_retained_without_private_test_loading(self):
        def unavailable(*args):
            raise RuntimeError("offline teacher not provisioned")
        summary = self.build(propose=unavailable)
        self.assertEqual(self.events, ["payload"])
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertEqual(self.receipt()["stage"], "offline_teacher")

    def test_plan_drift_aborts_before_training_pairs_are_published(self):
        def teacher(uid, model_input, plan_sha):
            proposals = self.propose(uid, model_input, plan_sha)
            self.plan_path.write_text("{}")
            return proposals
        with self.assertRaisesRegex(ValueError, "changed"):
            self.build(propose=teacher)
        self.assertNotIn("tests", self.events)
        self.assertFalse((self.root / "output/pairs.jsonl").exists())

    def test_existing_output_is_not_overwritten(self):
        self.build()
        before = (self.root / "output/summary.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual((self.root / "output/summary.json").read_bytes(), before)

    def test_proposal_budget_blocks_before_independent_tests(self):
        def teacher(uid, model_input, plan_sha):
            return self.propose(uid, model_input, plan_sha) * 5
        summary = self.build(propose=teacher)
        self.assertEqual(self.events, ["payload", "teacher"])
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertEqual(self.receipt()["reason"], "blocked")

    def test_unsupported_requirements_cannot_become_targets(self):
        self.proposal["requirements"]["unsupported_requirements"] = ["mutation"]
        summary = self.build()
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertNotIn("judge", self.events)

    def test_missing_bound_probe_cannot_become_target(self):
        self.proposal["bound_probe"] = {}
        summary = self.build()
        self.assertEqual(summary["emitted_pairs"], 0)
        self.assertNotIn("judge", self.events)

    def test_bad_limits_fail_before_creating_output(self):
        for limit in (0, 33, True, 1.5):
            with self.assertRaisesRegex(ValueError, "max_proposals"):
                self.build(max_proposals=limit)
        self.assertFalse((self.root / "output").exists())


@unittest.skipUnless(sys.platform == "linux" and Path("/usr/bin/bwrap").exists()
                     and Path("/usr/bin/prlimit").exists(),
                     "Native target qualification requires Linux bubblewrap/prlimit")
class NativeTargetBuilderTests(unittest.TestCase):
    """Authored integration controls, not a trained-composer result or corpus."""

    def setUp(self):
        self.fixture = TargetBuilderTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_native_qualification_emits_only_after_all_three_stages(self):
        summary = self.fixture.build(judge=None)
        receipt = self.fixture.receipt()
        self.assertEqual(summary["emitted_pairs"], 1, receipt)
        self.assertEqual(summary["training_eligible_pairs"], 1)
        pair = json.loads((self.fixture.root / "output/pairs.jsonl").read_text())
        self.assertEqual(pair["provenance"]["verification_authority"], "repository-sandbox")
        candidate = receipt["proposals"][0]
        self.assertEqual(candidate["reason"], "qualified")
        self.assertEqual(set(candidate["verdicts"]), {"public", "independent", "declared_bound_probe"})
        self.assertTrue(all(verdict["passed"] for verdict in candidate["verdicts"].values()))
        self.assertEqual(self.fixture.events, ["payload", "teacher", "tests"])

    def test_native_independent_rejection_never_emits_a_pair(self):
        # This constant passes the public one-element example but fails length 3.
        self.fixture.proposal["program"]["return"] = {"literal": 1}
        summary = self.fixture.build(judge=None)
        receipt = self.fixture.receipt()
        self.assertEqual(summary["emitted_pairs"], 0, receipt)
        self.assertEqual(summary["training_eligible_pairs"], 0)
        self.assertEqual((self.fixture.root / "output/pairs.jsonl").read_text(), "")
        candidate = receipt["proposals"][0]
        self.assertTrue(candidate["verdicts"]["public"]["passed"])
        self.assertFalse(candidate["verdicts"]["independent"]["passed"])
        self.assertEqual(candidate["reason"], "rejected")
        self.assertEqual(candidate["stage"], "independent")
        self.assertNotIn("declared_bound_probe", candidate["verdicts"])
        self.assertEqual(self.fixture.events, ["payload", "teacher", "tests"])


if __name__ == "__main__":
    unittest.main()
