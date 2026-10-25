"""Source-as-data and host-comparator tests. Never execute solution sources."""
import ast
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import variants
import qualify


class SourceContractTests(unittest.TestCase):
    def test_javascript_syntax_only(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node parser unavailable; no source execution attempted")
        with tempfile.TemporaryDirectory() as directory:
            for problem, versions in variants.build_sources()["javascript"].items():
                for variant, source in versions.items():
                    path = Path(directory) / f"{problem}-{variant}.js"
                    path.write_text(source)
                    result = subprocess.run([node,"--check",str(path)], capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode,0,result.stderr)

    def test_complete_sources_and_helper_cost(self):
        sources = variants.build_sources()
        self.assertEqual(set(sources), {"python", "javascript"})
        for language, problems in sources.items():
            helper = variants.PYTHON_HELPER if language == "python" else variants.JAVASCRIPT_HELPER
            self.assertEqual(set(problems), {"547", "841", "1091"})
            for problem, versions in problems.items():
                self.assertEqual(set(versions), {"original", "shared-breadth"})
                self.assertTrue(versions["shared-breadth"].startswith(helper))
                self.assertEqual(versions["shared-breadth"].count(helper), 1)
                self.assertIn(variants.METHODS[problem], versions["shared-breadth"])
                self.assertLessEqual(set(versions["shared-breadth"]), set(chr(i) for i in range(32,127)) | {"\n"})
                if language == "python":
                    ast.parse(versions["shared-breadth"])
        self.assertEqual(len(variants.provenance()), 12)
        for row in variants.provenance():
            source = sources[row["language"]][row["problem_id"]][row["variant"]]
            self.assertEqual(row["sha256"], variants.digest(source))
            self.assertEqual(row["source_utf8_bytes"], len(source.encode()))

    def test_originals_match_prior_qualification(self):
        previous = json.loads((HERE.parent/"readable-v1"/"qualification.json").read_text())
        known = {(row["language"],str(row["problem_id"])):row["source_sha256"] for row in previous["rows"]}
        for row in variants.provenance():
            if row["variant"] == "original":
                self.assertEqual(row["sha256"], known[row["language"],row["problem_id"]])


class OracleAndComparatorTests(unittest.TestCase):
    def test_independent_oracles_known_answers(self):
        self.assertEqual(qualify.component_oracle([[1,1,0],[1,1,0],[0,0,1]]), 2)
        self.assertTrue(qualify.rooms_oracle([[1],[2],[]]))
        self.assertFalse(qualify.rooms_oracle([[1],[],[]]))
        self.assertEqual(qualify.grid_oracle([[0,1],[1,0]]), 2)
        self.assertEqual(qualify.grid_oracle([[0,0],[0,1]]), -1)
        self.assertEqual(qualify.grid_oracle([[0]]), 1)

    def test_deterministic_cases_and_unmodified_oracle_inputs(self):
        first = qualify.build_cases()
        self.assertEqual(qualify.json_bytes(first), qualify.json_bytes(qualify.build_cases()))
        for problem, cases in first.items():
            self.assertGreater(len(cases), 500)
            for case in cases:
                before = copy.deepcopy(case)
                if case["expectation_mode"] == "independent-oracle":
                    self.assertEqual(case["expected"], qualify.ORACLES[problem](qualify.materialized_args(case)[0]))
                else:
                    self.assertEqual(problem, "1091")
                    self.assertNotIn("expected", case)
                self.assertEqual(before, case)

    def test_expected_outputs_excluded_from_payload(self):
        case = {"args":[[[0]]], "expected":1, "category":"sample", "alias_rows":[]}
        data = qualify.payload("shortestPathBinaryMatrix", [case])
        self.assertEqual(set(data["calls"][0]), {"args","alias_rows"})
        self.assertNotIn("expected", qualify.json_bytes(data).decode())

    def test_reject_wrong_value_type_mutation_and_identity(self):
        case = {"args":[[[1]]], "expected":True}
        good = {"i":0,"result":True,"result_type":"boolean","args_before":case["args"],"args_after":case["args"],"identities_preserved":True}
        self.assertTrue(qualify.judge_record("841",case,good))
        for key,value in (("result",1),("result",False),("result_type","number"),("args_after",[[[0]]]),("identities_preserved",False),("error","failure")):
            bad = {**good,key:value}
            self.assertFalse(qualify.judge_record("841",case,bad))

    def test_grid_exact_final_mutation_parity(self):
        case = {"args":[[[0,1],[1,0]]],"expected":2}
        good = {"i":0,"result":2,"result_type":"number","args_before":case["args"],"args_after":[[[1,1],[1,1]]],"identities_preserved":True}
        self.assertTrue(qualify.judge_record("1091",case,good,good))
        self.assertFalse(qualify.judge_record("1091",case,{**good,"args_after":[[[1,1],[1,0]]]},good))
        self.assertFalse(qualify.judge_record("1091",case,{**good,"args_after":[[[1,0],[1,1]]]}))
        self.assertFalse(qualify.judge_record("1091",case,{**good,"args_after":[[[True,1],[1,1]]]}))

    def test_alias_grid_is_compatibility_not_independent_distance(self):
        cases = [case for case in qualify.build_cases()["1091"] if case["category"] == "shared-row-identity"]
        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertEqual(case["expectation_mode"], "predecessor-effect-compatibility")
        self.assertNotIn("expected", case)
        self.assertEqual(qualify.grid_oracle(qualify.materialized_args(case)[0]), 2)
        predecessor = {"i":0,"result":-1,"result_type":"number","args_before":[[[0,0],[0,0]]],"args_after":[[[1,1],[1,1]]],"identities_preserved":True}
        self.assertTrue(qualify.judge_record("1091",case,predecessor))
        self.assertTrue(qualify.judge_record("1091",case,predecessor,predecessor))
        self.assertFalse(qualify.judge_record("1091",case,{**predecessor,"result":2},predecessor))

    def test_strict_output_protocol(self):
        self.assertEqual(qualify.parse_records(b'{"i":0}\n{"done":1}\n',1), [{"i":0}])
        for bad in (b'{"i":0,"i":0}\n{"done":1}\n', b'{"i":true}\n{"done":1}\n', b'{"i":0,"result":NaN}\n{"done":1}\n', b'{"i":0}\n', b'{"i":0}\n{"done":true}\n', b'[]\n{"done":1}\n'):
            with self.assertRaises(ValueError):
                qualify.parse_records(bad,1)

    def test_language_scope_rejects_invalid_or_duplicate_selection(self):
        for languages in ((), ("ruby",), ("python", "python")):
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                qualify.qualify(Path(directory)/"run", languages)

    def test_python_only_contract_cannot_claim_paired_coverage(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(qualify.sandbox,"run") as run:
            original_is_file = Path.is_file
            def exists(path):
                return False if str(path) == "/usr/bin/python3" else original_is_file(path)
            with patch.object(Path,"is_file",exists):
                receipt = qualify.qualify(Path(directory)/"run", ("python",))
            contract = json.loads((Path(directory)/"run"/"contract.json").read_text())
            self.assertEqual(contract["language_scope"], ["python"])
            self.assertEqual(set(contract["runtime_paths"]), {"python"})
            self.assertEqual(len(receipt["rows"]), 6)
            self.assertTrue(all(row["language"] == "python" for row in receipt["rows"]))
            self.assertEqual(receipt["status"], "blocked")
            run.assert_not_called()

    def test_runtime_blocker_cannot_qualify_or_launch_candidates(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(qualify.sandbox,"run") as run:
            original_is_file = Path.is_file
            def exists(path):
                return False if str(path) == "/usr/bin/node" else original_is_file(path)
            with patch.object(Path,"is_file",exists):
                receipt = qualify.qualify(Path(directory)/"run")
            self.assertEqual(receipt["status"], "blocked")
            self.assertFalse(receipt["success"])
            self.assertEqual(receipt["candidate_executions"],0)
            self.assertTrue(all(not row["passed"] for row in receipt["rows"]))
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
