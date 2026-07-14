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
            "human_review_rubric_and_threshold_absent",
            "matched_run_contract_absent",
            "gamma_bf16_selection_receipt_absent",
        ):
            self.assertIn(blocker, receipt["blockers"])

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
