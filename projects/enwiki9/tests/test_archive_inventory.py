"""CPU-only conservative classification checks; no corpus, stores or network."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "enwiki9_archive_inventory", Path(__file__).resolve().parents[1] / "tools/archive_inventory.py")
INVENTORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INVENTORY)


class ClassificationTests(unittest.TestCase):
    def row(self, name, kind="blob"):
        return {"path": INVENTORY.PREFIX + name, "git_type": kind}

    def test_output_directory_does_not_prove_output_role(self):
        for name in ("results/work/source.py", "results_preserve/model.bin", "programs/old/model.dat"):
            category, rule, review = INVENTORY.classify(self.row(name), {}, {}, {})
            self.assertEqual(category, "unresolved")
            self.assertTrue(review)

    def test_explicit_inputs_win_over_output_declarations(self):
        row = self.row("results/measured/out.bin")
        path = row["path"]
        self.assertEqual(INVENTORY.classify(row, {}, {path: ["original"]}, {path: ["producer"]}),
                         ("indispensable_inputs", "bound_input", True))
        self.assertEqual(INVENTORY.classify(row, {}, {}, {path: ["producer"]}),
                         ("retained_outputs", "bound_output", False))

    def test_frozen_source_role_is_not_reclassified_as_maintained_code(self):
        name = "tools/raw_reverse_bz2_v1.py"
        self.assertEqual(INVENTORY.classify(self.row(name), {name: "frozen_snapshot"}, {}, {})[:2],
                         ("indispensable_inputs", "frozen_role"))

    def test_gitlink_and_canonical_records_stay_protected(self):
        self.assertEqual(INVENTORY.classify(self.row("external/upstream", "commit"), {}, {}, {})[0],
                         "indispensable_inputs")
        self.assertEqual(INVENTORY.classify(self.row("operations/adaptive/reflections/old.json"), {}, {}, {})[0],
                         "indispensable_inputs")

    def test_original_reference_text_is_not_used_to_escape_project(self):
        self.assertIsNone(INVENTORY.project_path("../outside"))
        self.assertIsNone(INVENTORY.project_path("/outside"))
        self.assertEqual(INVENTORY.project_path("candidate.json", "old_candidate"),
                         INVENTORY.PREFIX + "programs/old_candidate/candidate.json")
        original = {"path": "tools/original.py", "sha256": "sha256:abc"}
        self.assertEqual(list(INVENTORY.references({"input": original})), [original])


if __name__ == "__main__":
    unittest.main()
