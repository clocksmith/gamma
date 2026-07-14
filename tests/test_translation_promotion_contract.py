"""Contract tests for the EN/ES single-student promotion target."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import chdir

import jsonschema


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMOTION_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "promotion"
CONTRACT_PATH = PROMOTION_ROOT / "promotion-contract.v1.json"
CONTRACT_SCHEMA_PATH = PROMOTION_ROOT / "promotion-contract.schema.json"
LEDGER_PATH = PROMOTION_ROOT / "error-ledger.wmt13-nativekd2.v1.json"
LEDGER_SCHEMA_PATH = PROMOTION_ROOT / "error-ledger.schema.json"
CATALOG_PATH = PROMOTION_ROOT / "data-license-catalog.v1.json"
PUBLIC_SOURCE_RECEIPT_PATH = PROMOTION_ROOT / "public-source-candidate-verification-2026-07-14.json"
POPULATION_PROCUREMENT_PATH = PROMOTION_ROOT / "population-procurement-contract.v1.json"
POPULATION_PROCUREMENT_SCHEMA_PATH = PROMOTION_ROOT / "population-procurement-contract.schema.json"

BUILDER_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "build_translation_error_ledger.py"
)
_SPEC = importlib.util.spec_from_file_location("build_translation_error_ledger", BUILDER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_BUILDER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BUILDER
_SPEC.loader.exec_module(_BUILDER)

_REVIEW_PACKAGE_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "build_translation_error_review_package.py"
)
_REVIEW_PACKAGE_SPEC = importlib.util.spec_from_file_location(
    "build_translation_error_review_package_contract",
    _REVIEW_PACKAGE_PATH,
)
assert _REVIEW_PACKAGE_SPEC is not None and _REVIEW_PACKAGE_SPEC.loader is not None
_REVIEW_PACKAGE = importlib.util.module_from_spec(_REVIEW_PACKAGE_SPEC)
sys.modules[_REVIEW_PACKAGE_SPEC.name] = _REVIEW_PACKAGE
_REVIEW_PACKAGE_SPEC.loader.exec_module(_REVIEW_PACKAGE)

_BASELINE_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "eval"
    / "run_translation_baseline_eval.py"
)
_BASELINE_SPEC = importlib.util.spec_from_file_location("run_translation_baseline_eval_contract", _BASELINE_PATH)
assert _BASELINE_SPEC is not None and _BASELINE_SPEC.loader is not None
_BASELINE = importlib.util.module_from_spec(_BASELINE_SPEC)
sys.modules[_BASELINE_SPEC.name] = _BASELINE
_BASELINE_SPEC.loader.exec_module(_BASELINE)

_READINESS_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "check_translation_promotion_readiness.py"
)
_READINESS_SPEC = importlib.util.spec_from_file_location(
    "check_translation_promotion_readiness_contract",
    _READINESS_PATH,
)
assert _READINESS_SPEC is not None and _READINESS_SPEC.loader is not None
_READINESS = importlib.util.module_from_spec(_READINESS_SPEC)
sys.modules[_READINESS_SPEC.name] = _READINESS
_READINESS_SPEC.loader.exec_module(_READINESS)


class TranslationPromotionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_contract_matches_schema(self) -> None:
        jsonschema.Draft202012Validator(self.schema).validate(self.contract)

    def test_target_is_future_promotion_not_present_claim(self) -> None:
        self.assertEqual(self.contract["presentClaim"]["status"], "feasibility_only")
        self.assertEqual(self.contract["promotionDecision"]["status"], "blocked")
        self.assertIn("sealed_one_use_promotion_evaluation", self.contract["presentClaim"]["absentEvidence"])

    def test_single_artifact_bidirectional_target(self) -> None:
        target = self.contract["promotionTarget"]
        self.assertEqual(target["checkpointCount"], 1)
        self.assertFalse(target["routerAllowed"])
        self.assertLessEqual(target["maximumParameters"], 1_000_000_000)
        self.assertEqual(target["directions"], ["en-es", "es-en"])
        self.assertEqual(target["evaluatedArtifact"], "exact_hosted_doppler_browser_artifact")

    def test_population_procurement_contract_is_frozen_but_not_materialized(self) -> None:
        procurement = json.loads(POPULATION_PROCUREMENT_PATH.read_text(encoding="utf-8"))
        schema = json.loads(POPULATION_PROCUREMENT_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(procurement)
        self.assertEqual(procurement["status"], "frozen_requirements_awaiting_materialization")
        self.assertTrue(all(role["status"] == "unmaterialized" for role in procurement["roles"]))
        self.assertEqual(
            {role["role"]: role["totalDistinctItems"] for role in procurement["roles"]},
            {
                "calibration": 300,
                "checkpoint_selection": 1200,
                "seed_confirmation": 1200,
                "promotion": 1500,
            },
        )
        self.assertEqual(
            self.contract["populationPolicy"]["procurementContractSha256"],
            hashlib.sha256(POPULATION_PROCUREMENT_PATH.read_bytes()).hexdigest(),
        )

    def test_current_bf16_artifact_is_baseline_not_winner(self) -> None:
        handoff = self.contract["baselineHandoff"]
        self.assertEqual(handoff["status"], "baseline_frozen_not_selected")
        self.assertEqual(handoff["selectionAuthority"], "clocksmith/gamma")
        self.assertIsNone(handoff["selectionReceipt"])
        self.assertIn("declare_bf16_winner", handoff["preGammaSelectionForbidden"])
        self.assertIn("run_doppler_artifact_competition", handoff["preGammaSelectionForbidden"])
        self.assertIn("Gamma alone selects", self.contract["matchedCampaign"]["bf16SelectionRule"])
        self.assertIn(
            "gamma_bf16_selection_receipt_absent",
            self.contract["promotionDecision"]["blockers"],
        )

    def test_wmt13_is_diagnostic_only(self) -> None:
        self.assertEqual(self.contract["populationPolicy"]["wmt13Role"], "diagnostic_only")
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        wmt13 = next(entry for entry in catalog["entries"] if entry["sourceId"] == "wmt13-enes-128-legacy")
        self.assertEqual(wmt13["newCampaignRoles"], ["diagnostic_only"])
        self.assertFalse(wmt13["selectionEligible"])
        self.assertFalse(wmt13["promotionEligible"])

    def test_blocking_comparators_and_metrics_are_immutable(self) -> None:
        blocking = [entry for entry in self.contract["comparators"] if entry["role"] == "blocking"]
        self.assertEqual(
            {entry["modelId"] for entry in blocking},
            {
                "google/translategemma-4b-it",
                "facebook/nllb-200-distilled-600M",
                "facebook/m2m100_1.2B",
            },
        )
        for entry in blocking:
            self.assertRegex(entry["revision"], r"^[0-9a-f]{40}$")
            self.assertRegex(entry["tokenizerRevision"], r"^[0-9a-f]{40}$")
        self.assertEqual({metric["metricId"] for metric in self.contract["metrics"]}, {"bleu", "chrf", "comet"})
        comet = next(metric for metric in self.contract["metrics"] if metric["metricId"] == "comet")
        self.assertRegex(comet["implementation"]["modelRevision"], r"^[0-9a-f]{40}$")

        registered = {entry.model_id: entry for entry in _BASELINE.load_baselines()}
        for expected in blocking:
            entry = registered[expected["modelId"]]
            self.assertEqual(entry.revision, expected["revision"])
            self.assertEqual(entry.tokenizer_revision, expected["tokenizerRevision"])

    def test_baseline_evaluator_forwards_registry_revisions(self) -> None:
        baseline = _BASELINE.BaselineEntry(
            model_id="example/model",
            display_name="Example",
            arch="nllb_seq2seq",
            execution_mode="seq2seq",
            prompt_adapter="nllb",
            directions=["en-es"],
            license="test",
            params="1B",
            revision="1" * 40,
            tokenizer_id="example/tokenizer",
            tokenizer_revision="2" * 40,
            notes="",
            quality_tier=0,
            enabled=True,
        )
        rows = [_BASELINE.EvalRow("en", "es", "hello", "hola", "en-es")]
        from unittest.mock import patch

        with patch.object(_BASELINE, "generate_seq2seq", return_value=["hola"]) as generate:
            _BASELINE.evaluate_model(baseline, rows)

        self.assertEqual(generate.call_args.kwargs["revision"], "1" * 40)
        self.assertEqual(generate.call_args.kwargs["tokenizer_id"], "example/tokenizer")
        self.assertEqual(generate.call_args.kwargs["tokenizer_revision"], "2" * 40)

    def test_license_unknown_blocks_new_campaign_use(self) -> None:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        for entry in catalog["entries"]:
            if entry["licenseStatus"] != "verified":
                self.assertFalse(entry["trainingEligible"])
                self.assertFalse(entry["selectionEligible"])
                self.assertFalse(entry["confirmationEligible"])
                self.assertFalse(entry["promotionEligible"])

    def test_new_external_domain_sources_are_exact_candidates_not_admitted_data(self) -> None:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        observed = {entry["sourceId"]: entry for entry in catalog["entries"]}
        expected = {
            "massive-1.0-en-us-es-es-candidate": (
                "conversational_assistant",
                "ff6bd8e4b27c3543e4f8fe2108f32bb95a6f8740",
                "CC-BY-4.0",
            ),
            "tico19-en-es-la-candidate": (
                "medical_public_health",
                "55d70dc0b1d1d0b2151c5e22815d823fedac3f2f",
                "CC0-1.0",
            ),
            "flores-plus-en-es-candidate": (
                "general_informational",
                "b3a5298db5721c8a682e7ef00a37fcc9ab522757",
                "CC-BY-SA-4.0",
            ),
        }
        for source_id, (domain, revision, license_id) in expected.items():
            entry = observed[source_id]
            self.assertEqual(entry["domain"], domain)
            self.assertEqual(entry["sourceRevision"], revision)
            self.assertEqual(entry["licenseId"], license_id)
            self.assertNotEqual(entry["licenseStatus"], "verified")
            self.assertIsNone(entry["humanApprovalReceipt"])
            self.assertFalse(entry["trainingEligible"])
            self.assertFalse(entry["selectionEligible"])
            self.assertFalse(entry["confirmationEligible"])
            self.assertFalse(entry["promotionEligible"])

        flores = observed["flores-plus-en-es-candidate"]
        self.assertEqual(flores["allowedUse"], "evaluation_candidate_only; never_training")
        self.assertIn("gated_auto", flores["accessPolicy"])

    def test_public_source_verification_receipt_is_immutable_and_non_admitting(self) -> None:
        receipt = json.loads(PUBLIC_SOURCE_RECEIPT_PATH.read_text(encoding="utf-8"))
        receipt_hash = receipt.pop("receiptHash")
        canonical = json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), receipt_hash)
        self.assertEqual(receipt["status"], "pass_source_identity_only")
        self.assertFalse(receipt["campaignEligibilityGranted"])
        self.assertTrue(all(source["sourceIdentityMatched"] for source in receipt["sources"]))
        self.assertTrue(all(source["campaignEligible"] is False for source in receipt["sources"]))

        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        candidates = {
            entry["sourceId"]: entry
            for entry in catalog["entries"]
            if entry.get("sourceVerificationReceipt")
        }
        self.assertEqual({source["sourceId"] for source in receipt["sources"]}, set(candidates))
        for source in receipt["sources"]:
            entry = candidates[source["sourceId"]]
            self.assertEqual(entry["sourceRevision"], source["sourceRevision"])
            self.assertEqual(entry["sourceVerificationReceiptHash"], receipt_hash)

    def test_materialized_error_ledger_matches_schema(self) -> None:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        schema = json.loads(LEDGER_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(ledger)
        self.assertEqual(ledger["population"]["rows"], 128)
        self.assertEqual(len(ledger["rows"]), 128)
        self.assertTrue(all(row["adjudication"]["status"] == "pending" for row in ledger["rows"]))
        for row in ledger["rows"]:
            self.assertNotIn("source", row)
            self.assertNotIn("reference", row)
            self.assertNotIn("labels", row["adjudication"])
            self.assertEqual(row["adjudication"]["inputAssessment"]["status"], "pending")
            self.assertEqual(
                set(row["adjudication"]["systemAssessments"]),
                set(row["systems"]),
            )
            self.assertTrue(
                all(
                    assessment["status"] == "pending"
                    for assessment in row["adjudication"]["systemAssessments"].values()
                )
            )
            for system in row["systems"].values():
                self.assertNotIn("prediction", system)

    def test_materialized_error_ledger_replays_from_bound_prediction_bytes(self) -> None:
        committed = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        systems = [
            (entry["systemId"], Path(entry["predictionsPath"]))
            for entry in committed["systems"]
        ]
        with chdir(REPO_ROOT):
            replayed = _BUILDER.build_error_ledger(
                Path(committed["population"]["path"]),
                systems,
                ledger_id=committed["ledgerId"],
            )

        self.assertEqual(replayed, committed)

    def test_error_ledger_builder_rejects_misaligned_sources(self) -> None:
        population = {"pair": "en-es", "source": "Hello 12", "target_pos": "Hola 12", "tgt_lang": "es"}
        system_a = {**population, "pred": "Hola 12"}
        system_b = {**population, "source": "Different", "pred": "Hola"}
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            population_path = root / "population.jsonl"
            a_path = root / "a.jsonl"
            b_path = root / "b.jsonl"
            population_path.write_text(json.dumps(population) + "\n", encoding="utf-8")
            a_path.write_text(json.dumps(system_a) + "\n", encoding="utf-8")
            b_path.write_text(json.dumps(system_b) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "source mismatch"):
                _BUILDER.build_error_ledger(
                    population_path,
                    [("a", a_path), ("b", b_path)],
                    ledger_id="test-ledger",
                )

    def test_diagnostic_review_package_blinds_systems_and_replays(self) -> None:
        population = {
            "pair": "en-es",
            "source": "Keep number 12",
            "target_pos": "Conserva el número 12",
            "tgt_lang": "es",
        }
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            population_path = root / "population.jsonl"
            alpha_path = root / "alpha.jsonl"
            beta_path = root / "beta.jsonl"
            ledger_path = root / "ledger.json"
            population_path.write_text(json.dumps(population) + "\n", encoding="utf-8")
            alpha_path.write_text(
                json.dumps({**population, "pred": "Conserva el número 12"}) + "\n",
                encoding="utf-8",
            )
            beta_path.write_text(
                json.dumps({**population, "pred": "Conserva el número"}) + "\n",
                encoding="utf-8",
            )
            ledger = _BUILDER.build_error_ledger(
                population_path,
                [("system-alpha", alpha_path), ("system-beta", beta_path)],
                ledger_id="diagnostic-ledger-with-hidden-system-names",
            )
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            key = b"fixed-test-key-material-32-bytes!!"

            first_worklist, first_mapping = _REVIEW_PACKAGE.build_review_package(
                ledger_path,
                key,
                worklist_id="blinded-review-v1",
            )
            second_worklist, second_mapping = _REVIEW_PACKAGE.build_review_package(
                ledger_path,
                key,
                worklist_id="blinded-review-v1",
            )

            self.assertEqual(first_worklist, second_worklist)
            self.assertEqual(first_mapping, second_mapping)
            visible = json.dumps(first_worklist)
            self.assertNotIn("system-alpha", visible)
            self.assertNotIn("system-beta", visible)
            custodied = json.dumps(first_mapping)
            self.assertIn("system-alpha", custodied)
            self.assertIn("system-beta", custodied)
            self.assertEqual(first_worklist["rowCount"], 1)
            self.assertEqual(first_worklist["systemCount"], 2)

            alpha_path.write_text(
                json.dumps({**population, "pred": "tampered"}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "prediction bytes do not match"):
                _REVIEW_PACKAGE.build_review_package(
                    ledger_path,
                    key,
                    worklist_id="blinded-review-v1",
                )

    def test_current_campaign_readiness_fails_closed_without_selecting_a_winner(self) -> None:
        receipt = _READINESS.build_readiness_receipt()

        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["presentClaim"], "feasibility_only")
        self.assertEqual(receipt["selection"]["status"], "not_selected")
        self.assertIsNone(receipt["selection"]["receipt"])
        self.assertFalse(receipt["admission"]["matchedTrainingAllowed"])
        self.assertFalse(receipt["admission"]["bf16WinnerDeclarationAllowed"])
        self.assertFalse(receipt["admission"]["dopplerArtifactCompetitionAllowed"])
        self.assertFalse(receipt["admission"]["promotionAllowed"])
        for blocker in (
            "population_calibration_unmaterialized",
            "population_checkpoint_selection_unmaterialized",
            "population_seed_confirmation_unmaterialized",
            "population_promotion_unmaterialized",
            "license_catalog_contains_unverified_sources",
            "matched_run_contract_absent",
            "gamma_bf16_selection_receipt_absent",
        ):
            self.assertIn(blocker, receipt["blockers"])
        self.assertNotIn("human_review_rubric_and_threshold_absent", receipt["blockers"])
        self.assertNotIn("population_materialization_contract_absent", receipt["blockers"])
        self.assertTrue(receipt["humanReview"]["identityBound"])
        self.assertTrue(receipt["populationProcurement"]["identityBound"])

    def test_post_training_evidence_does_not_circularly_block_matched_training(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        for population in contract["populationPolicy"]["roles"]:
            population["status"] = "frozen"
            population["manifestPath"] = f"custody/{population['role']}.manifest.json"
            population["populationHash"] = "a" * 64
        contract["humanReview"]["thresholdStatus"] = "frozen"
        contract["matchedCampaign"]["runContract"] = "promotion/matched-run-contract.v1.json"
        contract["promotionDecision"]["blockers"] = [
            "comet_evidence_absent",
            "matched_lane_receipts_absent",
            "seed_confirmation_absent",
            "gamma_bf16_selection_receipt_absent",
            "bf16_quality_target_not_met",
            "hosted_artifact_quality_target_not_met",
            "one_use_promotion_receipt_absent",
        ]

        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        catalog["status"] = "ready"
        catalog["entries"][0].update({
            "licenseStatus": "verified",
            "trainingEligible": True,
            "selectionEligible": True,
            "confirmationEligible": True,
            "promotionEligible": True,
        })
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        for row in ledger["rows"]:
            adjudication = row["adjudication"]
            adjudication["status"] = "complete"
            adjudication["inputAssessment"]["status"] = "usable"
            adjudication["reviewerIds"] = ["reviewer-1", "reviewer-2"]
            adjudication["adjudicatorId"] = "adjudicator-1"
            adjudication["reviewerSubmissionSha256s"] = ["a" * 64, "b" * 64]
            adjudication["adjudicatorSubmissionSha256"] = "c" * 64
            adjudication["worklistReceiptHash"] = "d" * 64
            adjudication["mappingReceiptHash"] = "e" * 64
            for assessment in adjudication["systemAssessments"].values():
                assessment["status"] = "complete"

        with tempfile.TemporaryDirectory(dir=PROMOTION_ROOT) as temp_dir:
            root = Path(temp_dir)
            contract_path = root / "contract.json"
            schema_path = root / "schema.json"
            catalog_path = root / "catalog.json"
            ledger_path = root / "ledger.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            schema_path.write_text(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            receipt = _READINESS.build_readiness_receipt(
                contract_path=contract_path,
                schema_path=schema_path,
                catalog_path=catalog_path,
                ledger_path=ledger_path,
            )

        self.assertTrue(receipt["admission"]["matchedTrainingAllowed"])
        self.assertFalse(receipt["admission"]["checkpointSelectionAllowed"])
        self.assertFalse(receipt["admission"]["bf16WinnerDeclarationAllowed"])
        self.assertFalse(receipt["admission"]["dopplerArtifactCompetitionAllowed"])
        self.assertFalse(receipt["admission"]["promotionAllowed"])
        self.assertEqual(receipt["admissionBlockers"]["matchedTraining"], [])
        self.assertIn(
            "matched_lane_receipts_absent",
            receipt["admissionBlockers"]["checkpointSelection"],
        )

    def test_committed_readiness_receipt_matches_current_inputs(self) -> None:
        committed = json.loads(
            (PROMOTION_ROOT / "promotion-readiness.v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(committed, _READINESS.build_readiness_receipt())

    def test_upstream_identity_receipt_binds_every_pinned_revision(self) -> None:
        receipt = json.loads(
            (PROMOTION_ROOT / "upstream-model-identity-verification-2026-07-13.json").read_text(
                encoding="utf-8"
            )
        )
        receipt_hash = receipt.pop("receiptHash")
        canonical = json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), receipt_hash)
        self.assertEqual(receipt["status"], "pass")
        observed = {entry["modelId"]: entry for entry in receipt["models"]}
        expected = {
            entry["modelId"]: entry["revision"]
            for entry in self.contract["comparators"]
        }
        expected.update({
            entry["modelId"]: entry["revision"]
            for entry in self.contract["baseModelComparison"]["candidates"]
        })
        comet = next(metric for metric in self.contract["metrics"] if metric["metricId"] == "comet")
        expected[comet["implementation"]["modelId"]] = comet["implementation"]["modelRevision"]

        self.assertEqual(set(observed), set(expected))
        for model_id, revision in expected.items():
            self.assertEqual(observed[model_id]["pinnedRevision"], revision)
            self.assertEqual(observed[model_id]["observedRevision"], revision)
            self.assertTrue(observed[model_id]["matched"])


if __name__ == "__main__":
    unittest.main()
