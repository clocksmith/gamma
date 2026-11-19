"""CPU tests for the B1 v5 gate (`projects/reconfiguration/query_swiglu_fastweight_v5/gate_v5.py`)."""
from __future__ import annotations

import fractions
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import tempfile
import unittest

GATE_PATH = Path(__file__).resolve().parents[1] / "projects" / "reconfiguration" / "query_swiglu_fastweight_v5" / "gate_v5.py"
_spec = importlib.util.spec_from_file_location("gate_v5", GATE_PATH)
gate_v5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate_v5)
Fr = fractions.Fraction


def brute_force_p(xs, two_sided=False):
    observed = sum(xs)
    hits = 0
    for signs in itertools.product((1, -1), repeat=len(xs)):
        s = sum(a * b for a, b in zip(signs, xs))
        hits += (abs(s) >= abs(observed)) if two_sided else (s >= observed)
    return hits / 2 ** len(xs)


def receipt(model, tables, shots=20, arms=("base_ctx", "top2_bare")):
    """tables: list of (table id, groups, {arm: list of booleans, one per question})."""
    rows = []
    task = 0
    for table, groups, answers in tables:
        n = len(answers[arms[0]])
        for q in range(n):
            for arm, right in answers.items():
                rows.append({"task_id": task, "specialty_id": table, "group": groups[q % len(groups)], "arm": arm,
                             "correct": bool(right[q]), "generated_tokens": [1, 2] if arm != "kv_ctx" or right[q] is not None else [9],
                             "total_ms": 10.0})
            task += 1
    return {"model": model, "shots_per_group": shots, "rows": rows, "specialties_compiled": []}


class ExactSignFlip(unittest.TestCase):
    def test_matches_enumeration_including_ties_and_zeros(self):
        rng = random.Random(3)
        for _ in range(40):
            n = rng.randint(1, 11)
            xs = [Fr(rng.randint(-6, 8), 16) + (Fr(1, 20) if rng.random() < 0.5 else 0) for _ in range(n)]
            if rng.random() < 0.3:
                xs[rng.randrange(n)] = Fr(0)
            self.assertAlmostEqual(gate_v5.exact_sign_flip_p(xs), brute_force_p(xs), places=12)
            self.assertAlmostEqual(gate_v5.exact_sign_flip_p(xs, two_sided=True), brute_force_p(xs, True), places=12)

    def test_all_zero_differences_cannot_pass(self):
        self.assertEqual(gate_v5.exact_sign_flip_p([Fr(0)] * 5), 1.0)

    def test_ninety_six_tables_is_exact_and_fast(self):
        rng = random.Random(4)
        xs = [Fr(rng.randint(-3, 3), 16) + Fr(1, 20) for _ in range(96)]
        p = gate_v5.exact_sign_flip_p(xs)
        self.assertTrue(0 < p < 1)


class GroupAware(unittest.TestCase):
    def test_without_shared_groups_it_is_the_ordinary_standard_error(self):
        values = [0.1, -0.05, 0.0, 0.2, -0.1, 0.05]
        groups = [{f"g{i}"} for i in range(len(values))]
        out = gate_v5.group_aware(values, groups)
        self.assertFalse(out["group_share_estimable"])
        self.assertAlmostEqual(out["se_group_aware"], out["se_over_tables_only"])
        mean = sum(values) / len(values)
        sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
        self.assertAlmostEqual(out["se_over_tables_only"], sd / math.sqrt(len(values)))

    def test_planted_group_effects_widen_the_standard_error(self):
        rng = random.Random(5)
        names = [f"g{i}" for i in range(8)]
        effect = {g: rng.gauss(0, 0.08) for g in names}
        groups = [set(rng.sample(names, 4)) for _ in range(96)]
        values = [sum(effect[g] for g in gs) + rng.gauss(0, 0.03) for gs in groups]
        out = gate_v5.group_aware(values, groups)
        self.assertTrue(out["group_share_estimable"])
        self.assertGreater(out["group_share_of_table_variance"], 0.5)
        self.assertGreater(out["se_group_aware"], 2 * out["se_over_tables_only"])

    def test_no_group_effect_leaves_the_standard_error_near_ordinary(self):
        rng = random.Random(6)
        names = [f"g{i}" for i in range(37)]
        groups = [set(rng.sample(names, 4)) for _ in range(96)]
        values = [rng.gauss(0, 0.1) for _ in groups]
        out = gate_v5.group_aware(values, groups)
        self.assertLess(out["se_group_aware"], 1.6 * out["se_over_tables_only"])


class EndToEnd(unittest.TestCase):
    def run_gate(self, receipts):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i, r in enumerate(receipts):
                p = Path(d) / f"r{i}.json"
                p.write_text(json.dumps(r))
                paths.append(str(p))
            by_model, compiled = gate_v5.load_tables(paths)
            return {m: (gate_v5.gate(t, 20), gate_v5.controls(t, compiled[m], 20)) for m, t in by_model.items()}

    def tables(self, adapter_right, base_right, n_tables=24, extra=None):
        names = [f"g{i}" for i in range(37)]
        rng = random.Random(7)
        out = []
        for t in range(n_tables):
            groups = rng.sample(names, 4)
            answers = {"base_ctx": [q < base_right for q in range(16)], "top2_bare": [q < adapter_right for q in range(16)]}
            for arm, right in (extra or {}).items():
                answers[arm] = [q < right for q in range(16)]
            out.append((f"t{t}", groups, answers))
        return out

    def test_equal_accuracy_passes_and_a_ten_point_deficit_does_not(self):
        same = self.run_gate([receipt("m", self.tables(12, 12))])["m"][0]
        self.assertTrue(same["primary"]["passes_for_these_groups"])
        self.assertTrue(same["verdict"].startswith("PASS"))
        worse = self.run_gate([receipt("m", self.tables(10, 12))])["m"][0]
        self.assertFalse(worse["primary"]["passes_for_these_groups"])
        self.assertTrue(worse["verdict"].startswith("NOT CONFIRMED"))

    def test_a_deficit_just_beyond_the_margin_does_not_pass(self):
        # Every table 1/16 = 6.25 points worse: beyond the 5-point margin.
        out = self.run_gate([receipt("m", self.tables(11, 12))])["m"][0]
        self.assertFalse(out["primary"]["passes_for_these_groups"])

    def test_models_are_never_pooled_and_other_table_sizes_stay_out_of_the_gate(self):
        res = self.run_gate([receipt("a", self.tables(12, 12)), receipt("b", self.tables(8, 12)),
                             receipt("a", self.tables(0, 16, n_tables=6), shots=3)])
        self.assertTrue(res["a"][0]["primary"]["passes_for_these_groups"])
        self.assertEqual(res["a"][0]["tables"], 24)
        self.assertFalse(res["b"][0]["primary"]["passes_for_these_groups"])

    def test_controls_are_reported(self):
        tables = self.tables(12, 12, extra={"mfc_bare": 4, "probe_bare": 12})
        gate, controls = self.run_gate([receipt("m", tables)])["m"]
        self.assertTrue(controls["most_frequent_code"]["exactly_one_in_four_on_every_table"])
        rule = controls["adapter_vs_plain_classifier"]["tie_rule"]
        self.assertTrue(rule["true_tie_interval_inside_margin"])
        self.assertTrue(rule["reading"].startswith("STOP: the classifier matches or beats"))
        tables = self.tables(14, 12, extra={"probe_bare": 9})
        _, controls = self.run_gate([receipt("m", tables)])["m"]
        rule = controls["adapter_vs_plain_classifier"]["tie_rule"]
        self.assertFalse(rule["true_tie_interval_inside_margin"])
        self.assertTrue(rule["reading"].startswith("ADVANCE"))

    def test_tie_rule_separates_a_tie_from_an_underpowered_comparison(self):
        base = {"mean_difference_points": 1.0}
        self.assertTrue(gate_v5.tie_rule({**base, "bootstrap_interval_90_points": [-1.5, 3.5]})["reading"].startswith("STOP unless"))
        self.assertTrue(gate_v5.tie_rule({**base, "bootstrap_interval_90_points": [-1.5, 3.5]})["true_tie_interval_inside_margin"])
        wide = gate_v5.tie_rule({**base, "bootstrap_interval_90_points": [-6.0, 8.0]})
        self.assertFalse(wide["true_tie_interval_inside_margin"])
        self.assertTrue(wide["reading"].startswith("INCONCLUSIVE"))
        small_win = gate_v5.tie_rule({"mean_difference_points": 2.5, "bootstrap_interval_90_points": [0.5, 4.5]})
        self.assertTrue(small_win["reading"].startswith("STOP unless"))
        loss = gate_v5.tie_rule({"mean_difference_points": -0.5, "bootstrap_interval_90_points": [-9.0, 8.0]})
        self.assertTrue(loss["reading"].startswith("STOP: the classifier"))


if __name__ == "__main__":
    unittest.main()
