"""Tests for SAME-R Approach Selector and Saturation Engine."""

import unittest
from projects.samer.selector import (
    ApproachEntry,
    ApproachRegistry,
    ApproachSelector,
    ApproachStatus,
    SaturationEngine,
    SaturationRule,
    TrialDisposition,
    TrialHistory,
    TrialRecord,
)


class TestSamerSelector(unittest.TestCase):
    def setUp(self):
        self.registry = ApproachRegistry()
        self.registry.register(
            ApproachEntry(
                approach_id="teacher_distill_v1",
                approach_revision="1.0.0",
                mechanism_type="teacher_assisted_distillation",
                implementation_pointer="projects/distillation/translation",
                eligible_domains=["translation", "general_nlp"],
                eligible_capabilities=["en_es_translation", "span_extraction"],
                required_inputs=["teacher_model", "training_pairs"],
                produced_artifacts=["student_checkpoint", "eval_scoreboard"],
                allowed_roles=["teacher", "executor", "evaluator"],
                priority_weight=1.5,
            )
        )
        self.registry.register(
            ApproachEntry(
                approach_id="construction_gold_v1",
                approach_revision="1.0.0",
                mechanism_type="construction_gold_training",
                implementation_pointer="projects/samer/domains/tinker",
                eligible_domains=["translation", "code"],
                eligible_capabilities=["en_es_translation", "syntax_repair"],
                required_inputs=["grammar_templates"],
                produced_artifacts=["constructed_dataset"],
                allowed_roles=["generator", "evaluator"],
                priority_weight=1.0,
            )
        )
        self.history = TrialHistory()
        self.selector = ApproachSelector()

    def test_cold_start_selection(self):
        frozen_contract = {
            "domain": "translation",
            "capability": "en_es_translation",
            "objective": "maximize BLEU",
        }
        receipt = self.selector.select_approach(
            self.registry, self.history, frozen_contract, selector_budget=50.0
        )
        self.assertIsNotNone(receipt.selected_approach_id)
        # Should pick the higher priority weight approach first on cold start
        self.assertEqual(receipt.selected_approach_id, "teacher_distill_v1")
        self.assertTrue(receipt.receipt_hash)
        self.assertEqual(receipt.budget_debit, 1.0)
        self.assertEqual(len(receipt.candidates_considered), 2)

    def test_saturation_on_no_improvement_window(self):
        frozen_contract = {
            "domain": "translation",
            "capability": "en_es_translation",
        }
        # Record 5 trials with zero improvement
        for i in range(5):
            self.history.record(
                TrialRecord(
                    trial_id=f"trial_td_{i}",
                    domain="translation",
                    capability="en_es_translation",
                    population="clean_eval_128",
                    approach_id="teacher_distill_v1",
                    intervention_id=f"int_{i}",
                    causal_contract_hash=f"hash_{i}",
                    run_contract_hash=f"run_hash_{i}",
                    disposition=TrialDisposition.REJECTED,
                    effect_vs_anchor=-0.05,
                    effect_vs_random_control=-0.02,
                    budget_spent=2.0,
                    receipt_hashes=[f"rec_{i}"],
                )
            )

        rule = SaturationRule(
            rule_id="test_sat",
            no_improvement_window=5,
        )

        receipt = self.selector.select_approach(
            self.registry,
            self.history,
            frozen_contract,
            selector_budget=50.0,
            saturation_rule=rule,
        )

        # teacher_distill_v1 should be saturated, so construction_gold_v1 must be selected
        self.assertEqual(receipt.selected_approach_id, "construction_gold_v1")
        self.assertIn("teacher_distill_v1", receipt.candidates_rejected_with_reasons)
        self.assertIn("saturated", receipt.candidates_rejected_with_reasons["teacher_distill_v1"])

    def test_global_saturation_when_all_approaches_exhausted(self):
        frozen_contract = {
            "domain": "translation",
            "capability": "en_es_translation",
        }
        # Exhaust budget for both approaches
        for app_id in ["teacher_distill_v1", "construction_gold_v1"]:
            for i in range(3):
                self.history.record(
                    TrialRecord(
                        trial_id=f"trial_{app_id}_{i}",
                        domain="translation",
                        capability="en_es_translation",
                        population="clean_eval_128",
                        approach_id=app_id,
                        intervention_id=f"int_{app_id}_{i}",
                        causal_contract_hash=f"hash_{i}",
                        run_contract_hash=f"run_hash_{i}",
                        disposition=TrialDisposition.REJECTED,
                        effect_vs_anchor=-0.01,
                        effect_vs_random_control=-0.01,
                        budget_spent=10.0,
                        receipt_hashes=[f"rec_{i}"],
                    )
                )

        rule = SaturationRule(
            rule_id="budget_exhaust",
            budget_limit=25.0,  # each has spent 30.0
        )

        receipt = self.selector.select_approach(
            self.registry,
            self.history,
            frozen_contract,
            selector_budget=50.0,
            saturation_rule=rule,
        )

        # All approaches are saturated -> selected_approach_id must be None
        self.assertIsNone(receipt.selected_approach_id)
        self.assertEqual(receipt.budget_debit, 0.0)
        self.assertEqual(len(receipt.candidates_rejected_with_reasons), 2)


if __name__ == "__main__":
    unittest.main()
