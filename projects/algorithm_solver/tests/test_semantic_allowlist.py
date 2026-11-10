"""Tests for explicit allowlist closure, fail-closed Linux gating, and isolated adapters."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from algsolve.records import LANE_ROOT
from algsolve.synth import semantic_allowlist as allowlist_mod
from algsolve.synth import semantic_target_pipeline as pipeline


def _meta(uid: str, family: str, *, key: str | None = None, aliases: list[str] | None = None,
          groups: list[str] | None = None) -> dict:
    return {
        "uid": uid,
        "key": key or f"lc:{uid}",
        "family": family,
        "aliases": aliases or [],
        "structural_groups": groups or [],
        "problem_sha256": "1" * 64,
        "independent_tests_sha256": "2" * 64,
    }


def _boundary(**updates) -> dict:
    base = {
        "uids": [],
        "keys": [],
        "families": [],
        "structural_groups": [],
        "sources_sha256": {"synthetic-boundary": "3" * 64},
    }
    base.update(updates)
    return base


def _allowlist(uids: list[str], keys: list[str]) -> dict:
    return {
        "uids": uids,
        "keys": keys,
        "sources_sha256": {"synthetic-allowlist": "4" * 64},
    }


class AllowlistAndRecombinationPlanTests(unittest.TestCase):
    def test_legacy_three_arg_freeze_plan_remains_unchanged(self):
        rows = [_meta("fit", "fit"), _meta("held", "held"), _meta("protected", "secret")]
        plan = pipeline.freeze_plan(rows, _boundary(uids=["protected"]), ["held"])
        self.assertNotIn("allowlist", plan)
        self.assertNotIn("recombination_uids", plan)
        self.assertEqual(
            {row["uid"]: row["split"] for row in plan["rows"]},
            {"fit": "development_fit", "held": "heldout_family", "protected": "excluded_existing"},
        )
        self.assertEqual(pipeline.validate_plan(plan), plan)

    def test_unallowlisted_rows_and_connected_components_are_excluded(self):
        rows = [
            _meta("lcd:10", "clean-fit", key="lc:clean-fit"),
            _meta("lcd:11", "clean-held", key="lc:clean-held"),
            _meta("lcd:12", "shared-fam", key="lc:shared-a"),
            _meta("lcd:13", "shared-fam", key="lc:shared-b"),  # Not in allowlist -> taints lcd:12.
            _meta("lcd:14", "struct-clean", key="lc:struct-a", groups=["grp-1"]),
            _meta("lcd:15", "struct-unknown", key="lc:struct-b", groups=["grp-1"]),  # Not in allowlist -> taints lcd:14.
            _meta("lcd:16", "alias-leak", key="lc:alias-leak", aliases=["lcd:999"]),  # Unallowlisted alias -> taints lcd:16.
            _meta("lcd:17", "reserved-fam", key="lc:reserved-i"),
        ]
        allowed = _allowlist(
            uids=["lcd:10", "lcd:11", "lcd:12", "lcd:14", "lcd:16", "lcd:17"],
            keys=["lc:clean-fit", "lc:clean-held", "lc:shared-a", "lc:struct-a", "lc:alias-leak", "lc:reserved-i"],
        )
        plan = pipeline.freeze_plan(
            rows,
            _boundary(keys=["lc:reserved-ii"]),
            ["clean-held"],
            allowlist=allowed,
        )
        splits = {row["uid"]: row["split"] for row in plan["rows"]}
        self.assertEqual(splits["lcd:10"], "development_fit")
        self.assertEqual(splits["lcd:11"], "heldout_family")
        self.assertEqual(splits["lcd:12"], "excluded_unallowlisted")
        self.assertEqual(splits["lcd:13"], "excluded_unallowlisted")
        self.assertEqual(splits["lcd:14"], "excluded_unallowlisted")
        self.assertEqual(splits["lcd:15"], "excluded_unallowlisted")
        self.assertEqual(splits["lcd:16"], "excluded_unallowlisted")
        self.assertEqual(splits["lcd:17"], "excluded_existing")
        self.assertEqual(pipeline.validate_plan(plan), plan)

    def test_recombination_uids_require_populated_seen_family(self):
        rows = [
            _meta("lcd:1", "seen-family", key="lc:alpha"),
            _meta("lcd:2", "seen-family", key="lc:beta"),
            _meta("lcd:3", "unseen-family", key="lc:gamma"),
            _meta("lcd:4", "other-seen-family", key="lc:delta"),
        ]
        allowed = _allowlist(
            uids=["lcd:1", "lcd:2", "lcd:3", "lcd:4"],
            keys=["lc:alpha", "lc:beta", "lc:gamma", "lc:delta"],
        )
        plan = pipeline.freeze_plan(
            rows,
            _boundary(),
            ["unseen-family"],
            allowlist=allowed,
            recombination_uids=["lcd:2"],
        )
        splits = {row["uid"]: row["split"] for row in plan["rows"]}
        self.assertEqual(splits, {
            "lcd:1": "development_fit",
            "lcd:2": "heldout_combination",
            "lcd:3": "heldout_family",
            "lcd:4": "development_fit",
        })
        self.assertEqual(pipeline.validate_plan(plan), plan)

        # Taking all members of seen-family into recombination_uids must fail closed even when another family fits.
        with self.assertRaisesRegex(ValueError, "retain at least one"):
            pipeline.freeze_plan(
                rows,
                _boundary(),
                ["unseen-family"],
                allowlist=allowed,
                recombination_uids=["lcd:1", "lcd:2"],
            )
        # Targeting a heldout_family UID for recombination_uids must fail closed.
        with self.assertRaisesRegex(ValueError, "cannot target"):
            pipeline.freeze_plan(
                rows,
                _boundary(),
                ["unseen-family"],
                allowlist=allowed,
                recombination_uids=["lcd:3"],
            )


class CommittedAllowlistCompilerTests(unittest.TestCase):
    def test_committed_allowlist_compiler_is_deterministic_and_excludes_all_reservations(self):
        first = allowlist_mod.compile_committed_allowlist_and_boundary(LANE_ROOT)
        second = allowlist_mod.compile_committed_allowlist_and_boundary(LANE_ROOT)
        self.assertEqual(first, second)
        audit = first["audit"]
        self.assertEqual(audit["problem_index_total"], 5144)
        self.assertEqual(audit["previously_authorized_400"], 400)
        self.assertEqual(audit["non_allowlisted_problem_index_rows"], 4744)
        self.assertEqual(audit["contaminated_authorized_rows"], 103)
        self.assertEqual(audit["self_contained_allowlisted_rows"], 297)
        self.assertEqual(audit["excluded_design_or_paid_rows"], 61)
        self.assertEqual(audit["functional_non_paid_candidates"], 236)
        self.assertEqual(audit["functional_dev_fit_candidates"], 175)
        self.assertEqual(audit["functional_dev_val_candidates"], 61)
        self.assertEqual(audit["payload_files_opened"], 0)

        allowed_uids = set(first["allowlist"]["uids"])
        allowed_keys = set(first["allowlist"]["keys"])
        # Protected and JS-wave entries (including lcd:6 zigzag-conversion inside auth400 & W001) stay excluded.
        for forbidden_uid in ("lcd:1", "lcd:2", "lcd:3", "lcd:4", "lcd:6", "lcd:561", "lcd:3335", "lcd:268"):
            self.assertNotIn(forbidden_uid, allowed_uids)
        for forbidden_key in ("lc:two-sum", "lc:zigzag-conversion", "lc:array-partition", "lc:missing-number"):
            self.assertNotIn(forbidden_key, allowed_keys)


class AdapterAndLinuxGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset_path = self.root / "fixture-lcd.jsonl"
        rows = [
            {
                "question_id": 9001,
                "task_id": "count-items-alpha",
                "entry_point": "Solution().countItems",
                "starter_code": "class Solution:\n    def countItems(self, values: List[int]) -> int:\n        ",
                "problem_description": "Count items.\n\nExample 1:\nInput: values = [4, 5]\nOutput: 2\n",
                "test": "def check(candidate):\n    assert candidate([4, 5, 6]) == 3\n",
                "completion": "SECRET_REFERENCE_SOLUTION_9001",
                "difficulty": "Easy",
                "tags": ["Array"],
            },
            {
                "question_id": 9002,
                "task_id": "count-items-beta",
                "entry_point": "Solution().countItems",
                "starter_code": "class Solution:\n    def countItems(self, values: List[int]) -> int:\n        ",
                "problem_description": "Count beta.\n\nExample 1:\nInput: values = [9]\nOutput: 1\n",
                "test": "def check(candidate):\n    assert candidate([9, 8]) == 2\n",
                "completion": "SECRET_REFERENCE_SOLUTION_9002",
                "difficulty": "Easy",
                "tags": ["Array"],
            },
            {
                "question_id": 9003,
                "task_id": "unseen-family-gamma",
                "entry_point": "Solution().countItems",
                "starter_code": "class Solution:\n    def countItems(self, values: List[int]) -> int:\n        ",
                "problem_description": "Gamma.\n\nExample 1:\nInput: values = [1]\nOutput: 1\n",
                "test": "def check(candidate):\n    assert candidate([1, 2]) == 2\n",
                "completion": "SECRET_REFERENCE_SOLUTION_9003",
                "difficulty": "Easy",
                "tags": ["Array"],
            },
            {
                "question_id": 1,
                "task_id": "two-sum",
                "entry_point": "Solution().twoSum",
                "starter_code": "BROKEN STARTER MUST NEVER BE PARSED",
                "problem_description": "PROTECTED PAYLOAD MUST NEVER BE EXPOSED",
                "test": "SYNTAX ERROR IF PARSED (",
                "completion": "PROTECTED_REFERENCE",
            },
        ]
        with self.dataset_path.open("w", encoding="utf-8") as stream:
            for item in rows:
                stream.write(json.dumps(item) + "\n")

        self.allowlist = _allowlist(
            uids=["lcd:9001", "leetcode:9001", "doocs:9001", "lcd:9002", "leetcode:9002", "doocs:9002",
                  "lcd:9003", "leetcode:9003", "doocs:9003"],
            keys=["lc:count-items-alpha", "lc:count-items-beta", "lc:unseen-family-gamma"],
        )
        self.boundary = _boundary(uids=["lcd:1"], keys=["lc:two-sum"], families=["two-sum"])
        self.dataset_auth = {
            "authorized": True,
            "authority": "unit-test-authority",
            "scope": "synthetic-allowlist-fixture",
        }

    def test_non_linux_native_judge_fails_closed_before_creating_output(self):
        meta = [_meta("fit", "fit"), _meta("held", "held")]
        plan = pipeline.freeze_plan(meta, _boundary(), ["held"])
        plan_path = self.root / "plan.json"
        pipeline.write_plan(plan_path, plan)
        out_dir = self.root / "never-created"
        with mock.patch.object(pipeline.sys, "platform", "darwin"):
            with self.assertRaisesRegex(RuntimeError, "no macOS fallback"):
                pipeline.build_targets(
                    plan_path,
                    out_dir,
                    codec_path=LANE_ROOT / "contracts/typed_codec_v1.json",
                    teacher_identity="none",
                    load_problem=lambda row: (_ for _ in ()).throw(AssertionError("must not load")),
                    propose=lambda *args: (_ for _ in ()).throw(AssertionError("must not propose")),
                    load_independent_tests=lambda row: (_ for _ in ()).throw(AssertionError("must not load tests")),
                    judge=None,
                )
        self.assertFalse(out_dir.exists())

    def test_dataset_adapter_enforces_authorization_canonical_hash_and_allowlist_before_parsing(self):
        with self.assertRaises(PermissionError):
            allowlist_mod.AllowlistDatasetAdapter(
                self.dataset_path,
                allowlist=self.allowlist,
                boundary=self.boundary,
                authorization={"authorized": False, "authority": "none", "scope": "none"},
                verify_canonical_file=False,
            )
        with self.assertRaises(ValueError):
            allowlist_mod.AllowlistDatasetAdapter(
                self.dataset_path,
                allowlist=self.allowlist,
                boundary=self.boundary,
                authorization=self.dataset_auth,
                verify_canonical_file=True,
            )

        adapter = allowlist_mod.AllowlistDatasetAdapter(
            self.dataset_path,
            allowlist=self.allowlist,
            boundary=self.boundary,
            authorization=self.dataset_auth,
            verify_canonical_file=False,
        )
        self.assertEqual(adapter.skipped_non_allowlisted, 1)
        with self.assertRaises(PermissionError):
            adapter.extract_allowlisted_metadata_hashes({"lcd:1": "two-sum"})

        metadata_rows, unusable = adapter.extract_allowlisted_metadata_hashes({
            "lcd:9001": "count-family",
            "lcd:9002": "count-family",
            "lcd:9003": "gamma-family",
        })
        self.assertEqual(unusable, {})
        self.assertEqual(len(metadata_rows), 3)

        plan = pipeline.freeze_plan(
            metadata_rows,
            self.boundary,
            ["gamma-family"],
            allowlist=self.allowlist,
            recombination_uids=["lcd:9002"],
        )
        adapter.bind_plan(plan)

        # Only lcd:9001 (development_fit) may load payloads; heldout_combination, heldout_family, and protected fail closed.
        row_by_uid = {row["uid"]: row for row in plan["rows"]}
        fit_problem = adapter.load_problem(row_by_uid["lcd:9001"])
        self.assertEqual(fit_problem.reference_solutions, [])
        self.assertNotIn("SECRET_REFERENCE", fit_problem.to_json())
        for blocked_uid in ("lcd:9002", "lcd:9003"):
            with self.assertRaises(PermissionError):
                adapter.load_problem(row_by_uid[blocked_uid])
            with self.assertRaises(PermissionError):
                adapter.load_independent_tests(row_by_uid[blocked_uid])
        with self.assertRaises(PermissionError):
            adapter.load_problem({"uid": "lcd:1", "key": "lc:two-sum"})

    def test_end_to_end_isolated_teacher_and_allowlist_adapter_build_only_development_fit(self):
        adapter = allowlist_mod.AllowlistDatasetAdapter(
            self.dataset_path,
            allowlist=self.allowlist,
            boundary=self.boundary,
            authorization=self.dataset_auth,
            verify_canonical_file=False,
        )
        metadata_rows, _ = adapter.extract_allowlisted_metadata_hashes({
            "lcd:9001": "count-family",
            "lcd:9002": "count-family",
            "lcd:9003": "gamma-family",
        })
        plan = pipeline.freeze_plan(
            metadata_rows,
            self.boundary,
            ["gamma-family"],
            allowlist=self.allowlist,
            recombination_uids=["lcd:9002"],
        )
        plan_path = self.root / "plan.json"
        pipeline.write_plan(plan_path, plan)
        adapter.bind_plan(plan)

        # Unauthorized teacher fails closed.
        with self.assertRaises(PermissionError):
            allowlist_mod.IsolatedTeacherAdapter(
                lambda *args: [],
                authorization={"authorized": False},
            )

        seen_calls = []

        def teacher_fn(uid, public_input, plan_sha256, config):
            seen_calls.append((uid, set(public_input), plan_sha256, config["max_proposals"]))
            public_input["public_examples"][0]["expected"] = -1  # Mutation must stay isolated.
            return [{
                "variant": "len-v1",
                "requirements": {"unsupported_requirements": []},
                "bound_probe": {"args": [[1, 2]], "expected": 2},
                "program": {
                    "schema": "algsolve.typed-program.v2",
                    "parameters": ["values"],
                    "inputs": {"values": ["list", "int"]},
                    "body": [],
                    "return": {"op": "len", "args": [{"ref": "values"}]},
                    "output_type": "int",
                },
            }]

        teacher = allowlist_mod.IsolatedTeacherAdapter(
            teacher_fn,
            authorization={
                "authorized": True,
                "authority": "unit-test-teacher-authority",
                "model_id": "pinned-offline-teacher",
                "model_revision": "rev-0001",
                "prompt_sha256": "a" * 64,
                "max_proposals": 4,
            },
        )
        # Leaked fields into IsolatedTeacherAdapter are rejected immediately.
        with self.assertRaises(PermissionError):
            teacher.propose(
                "lcd:9001",
                {"statement": "s", "starter_code": "c", "params": [], "public_examples": [], "reference_solutions": []},
                plan["plan_sha256"],
            )
        with self.assertRaises(PermissionError):
            teacher.propose(
                "lcd:9001",
                {"statement": "s", "starter_code": "c", "params": [], "public_examples": [{"verdict": "leaked"}]},
                plan["plan_sha256"],
            )

        summary = pipeline.build_targets(
            plan_path,
            self.root / "build-out",
            codec_path=LANE_ROOT / "contracts/typed_codec_v1.json",
            teacher_identity=teacher.teacher_identity,
            load_problem=adapter.load_problem,
            propose=teacher.propose,
            load_independent_tests=adapter.load_independent_tests,
            judge=lambda problem, source, cases: SimpleNamespace(
                to_dict=lambda: {
                    "passed": True,
                    "tests_passed": len(cases),
                    "tests_total": len(cases),
                    "reason": "passed",
                }
            ),
        )
        self.assertEqual(len(seen_calls), 1)
        self.assertEqual(seen_calls[0][0], "lcd:9001")
        self.assertEqual(summary["emitted_pairs"], 1)
        self.assertEqual(summary["training_eligible_pairs"], 0)
        self.assertEqual(summary["counts"]["heldout_combination"], 1)
        self.assertEqual(summary["counts"]["heldout_family"], 1)
        self.assertEqual(summary["counts"]["qualified_test_double"], 1)


if __name__ == "__main__":
    unittest.main()
