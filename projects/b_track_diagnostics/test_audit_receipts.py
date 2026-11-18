import unittest
from audit_receipts import paired_b2, summarize_b1

def fixture():
    return {"completed": True, "protocol": {"lineage_seeds": [1, 2]}, "rows": [
        {"lineage_seed": seed, "family": "cls", "task_id": str(seed),
         "arm": arm, "budget": "exact", "generation": 4,
         "loss_type": "cross_entropy", "query_accuracy": value}
        for seed in (1, 2) for arm, value in
        (("exact_gen4", 0.5), ("fixed_proposer_gen4", 0.75))]}

class AuditTests(unittest.TestCase):
    def test_pairing(self):
        r = paired_b2(fixture(), "fixed_proposer_gen4", "exact")["cls"]
        self.assertEqual(r["negative_lineages"], 2)
        self.assertEqual(r["focal_minus_reference"], -0.25)
    def test_duplicate(self):
        d = fixture(); d["rows"].append(d["rows"][0])
        with self.assertRaises(ValueError): paired_b2(d, "fixed_proposer_gen4", "exact")
    def test_missing_pair(self):
        d = fixture(); d["rows"].pop()
        with self.assertRaises(ValueError): paired_b2(d, "fixed_proposer_gen4", "exact")
    def test_missing_lineage(self):
        d = fixture(); d["rows"] = d["rows"][:2]
        with self.assertRaises(ValueError): paired_b2(d, "fixed_proposer_gen4", "exact")
    def test_incomplete(self):
        d = fixture(); d["completed"] = False
        with self.assertRaises(ValueError): paired_b2(d, "fixed_proposer_gen4", "exact")
    def test_nonfinite(self):
        d = fixture(); d["rows"][0]["query_accuracy"] = float("nan")
        with self.assertRaises(ValueError): paired_b2(d, "fixed_proposer_gen4", "exact")
    def test_b1_empty(self):
        d = {"completed": True, "rows": [{"task_id": 1, "domain": "multi",
             "regime_a": {"focal": {"correct": False, "output": ""}},
             "regime_b": {"focal": {"correct": True, "output": "a"}}}]}
        self.assertEqual(summarize_b1(d)["multi"]["regime_a"]["focal"]["empty"], 1)
        d["rows"].append(d["rows"][0])
        with self.assertRaises(ValueError): summarize_b1(d)
