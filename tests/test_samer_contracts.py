"""Fail-closed contract tests for SAME-R machine-readable evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT_DIR = _ROOT / "projects" / "samer" / "contracts"
_VALIDATOR_PATH = _CONTRACT_DIR / "validate_same_r_contract.py"
_EXAMPLE_PATH = _CONTRACT_DIR / "example.same-r-contract-suite.json"
_SPEC = importlib.util.spec_from_file_location("validate_same_r_contract", _VALIDATOR_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _VALIDATOR
_SPEC.loader.exec_module(_VALIDATOR)


class SameRContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example = json.loads(_EXAMPLE_PATH.read_text(encoding="utf-8"))

    def assert_invalid(self, suite: dict[str, object], message: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid-suite.json"
            path.write_text(json.dumps(suite), encoding="utf-8")
            with self.assertRaisesRegex(_VALIDATOR.ContractValidationError, message):
                _VALIDATOR.validate_contract_suite(path)

    def test_checked_in_schema_and_suite_validate(self) -> None:
        schema = _VALIDATOR.validate_schema_alignment()
        suite = _VALIDATOR.validate_contract_suite()
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(suite["runContracts"]), 3)
        self.assertFalse(suite["saturationDecision"]["saturated"])

    def test_typed_approach_histories_must_be_disjoint(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["approachRegistry"]["history"]["rejected"].append(
            "trial.synthetic.accepted"
        )
        self.assert_invalid(suite, "appears in both")

    def test_approach_must_be_eligible_for_domain_and_capability(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["approachRegistry"]["entries"][0]["eligibleCapabilities"] = [
            "translation_quality"
        ]
        self.assert_invalid(suite, "eligible capabilities")

    def test_label_authority_must_be_scoped_to_owning_teacher(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["labelAuthorities"][0]["participantId"] = "gemini.proposer"
        self.assert_invalid(suite, "belongs to another participant")

    def test_teacher_must_acknowledge_its_label_authority(self) -> None:
        suite = copy.deepcopy(self.example)
        claude = next(
            participant
            for participant in suite["participantRegistry"]["participants"]
            if participant["participantId"] == "claude.proposer"
        )
        claude["labelAuthorityIds"] = []
        self.assert_invalid(suite, "must be listed by its owning participant")

    def test_downstream_label_manifest_must_exist(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["labelAuthorities"][0]["downstreamManifestIds"] = ["manifest.hidden"]
        self.assert_invalid(suite, "unknown run manifests")

    def test_exact_model_revision_must_match_baseline(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][1]["student"]["modelRevision"] = "different-revision"
        self.assert_invalid(suite, "does not match baselineArtifact")

    def test_adapter_initial_parameters_cannot_drift_between_lanes(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][2]["student"]["adapter"][
            "initialParametersSha256"
        ] = "9" * 64
        self.assert_invalid(suite, "lineage drifted")

    def test_training_or_evaluator_lineage_cannot_drift_between_lanes(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][1]["training"]["optimizerHash"] = "9" * 64
        self.assert_invalid(suite, "lineage drifted")

    def test_row_count_must_match_ordered_row_ids(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][0]["data"]["rowCount"] = 5
        self.assert_invalid(suite, "orderedRowIds length")

    def test_targeted_and_random_lanes_must_change_declared_positions_only(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][1]["data"]["orderedRowIds"][2] = "row.extra"
        self.assert_invalid(suite, "changed positions")

    def test_partial_row_consumption_requires_resume_cursor(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][0]["data"]["consumedRowCount"] = 3
        self.assert_invalid(suite, "required for partial consumption")

    def test_checkpoint_denominator_cannot_omit_an_expected_checkpoint(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][0]["evaluation"]["checkpointDenominator"][
            "evaluated"
        ].remove("checkpoint.002")
        self.assert_invalid(suite, "not fully accounted")

    def test_trial_scoreboard_must_aggregate_all_lane_denominators(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["trialReceipt"]["checkpointScoreboard"]["expected"] = 5
        self.assert_invalid(suite, "does not aggregate")

    def test_item_denominator_must_reconcile(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["metricEvidence"][0]["denominator"]["missing"] = 1
        self.assert_invalid(suite, "scored/missing/malformed/excluded total")

    def test_unknown_contamination_access_cannot_pass(self) -> None:
        suite = copy.deepcopy(self.example)
        access = suite["contaminationAudit"]["accessAudit"][0]
        access["accessType"] = "unknown"
        self.assert_invalid(suite, "unknown access cannot pass")

    def test_overall_contamination_pass_cannot_hide_blocked_access(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["contaminationAudit"]["accessAudit"][0]["status"] = "blocked"
        self.assert_invalid(suite, "pass conflicts")

    def test_every_run_attempt_must_be_retained(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["trialReceipt"]["attempts"] = suite["trialReceipt"]["attempts"][1:]
        self.assert_invalid(suite, "has no retained attempt")

    def test_retry_attempt_numbers_must_be_contiguous_and_bounded(self) -> None:
        suite = copy.deepcopy(self.example)
        retry = copy.deepcopy(suite["trialReceipt"]["attempts"][0])
        retry["attemptId"] = "attempt.anchor.3"
        retry["attemptNumber"] = 3
        suite["trialReceipt"]["attempts"].append(retry)
        self.assert_invalid(suite, "not contiguous")

    def test_invalidated_contract_requires_an_invalidation_receipt(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["runContracts"][0]["contractValidity"]["status"] = "invalidated"
        self.assert_invalid(suite, "lacks an invalidation receipt")

    def test_rejected_proposal_must_have_been_considered(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["selectionReceipt"]["candidatesRejected"][0][
            "proposalId"
        ] = "proposal.unseen"
        self.assert_invalid(suite, "was not considered")

    def test_every_nonselected_proposal_requires_a_rejection_reason(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["selectionReceipt"]["candidatesRejected"] = []
        self.assert_invalid(suite, "must explain every non-selected proposal")

    def test_selector_cannot_choose_an_invalid_candidate(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["selectionReceipt"]["candidatesConsidered"][0]["valid"] = False
        self.assert_invalid(suite, "one valid considered candidate")

    def test_selection_budget_must_reconcile(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["selectionReceipt"]["budgetRemaining"]["proposalCalls"] = 1
        self.assert_invalid(suite, r"declared 4 != spent 2 \+ remaining 1")

    def test_participant_token_budget_cannot_name_an_unregistered_model(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["selectionReceipt"]["budgetBefore"]["modelTokensByParticipant"][
            "unknown.model"
        ] = 1
        self.assert_invalid(suite, "unknown participant")

    def test_recursive_selector_path_cannot_cycle(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["selectionReceipt"]["recursivePath"] = [
            "example.wgsl.repair",
            "example.wgsl.repair",
        ]
        self.assert_invalid(suite, "must contain unique items")

    def test_false_saturation_requires_an_eligible_next_approach(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["saturationDecision"]["eligibleUntriedApproachIds"] = []
        self.assert_invalid(suite, "requires an eligible next approach")

    def test_pending_work_is_a_valid_false_saturation_decision(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["saturationDecision"]["reasonCode"] = "required_evaluations_pending"
        suite["saturationDecision"]["eligibleUntriedApproachIds"] = []
        suite["saturationDecision"]["pendingRequiredTrialIds"] = ["trial.pending"]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pending-suite.json"
            path.write_text(json.dumps(suite), encoding="utf-8")
            validated = _VALIDATOR.validate_contract_suite(path)
        self.assertFalse(validated["saturationDecision"]["saturated"])

    def test_blocked_or_nonterminal_reason_cannot_claim_saturation(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["saturationDecision"]["saturated"] = True
        suite["saturationDecision"]["reasonCode"] = "eligible_candidates_remain"
        suite["saturationDecision"]["eligibleUntriedApproachIds"] = []
        self.assert_invalid(suite, "not a terminal saturation reason")

    def test_pending_required_evaluation_prevents_saturation(self) -> None:
        suite = copy.deepcopy(self.example)
        suite["saturationDecision"]["saturated"] = True
        suite["saturationDecision"]["reasonCode"] = "domain_owner_stop"
        suite["saturationDecision"]["eligibleUntriedApproachIds"] = []
        suite["saturationDecision"]["pendingRequiredTrialIds"] = ["trial.pending"]
        self.assert_invalid(suite, "pending work prevents saturation")


if __name__ == "__main__":
    unittest.main()
