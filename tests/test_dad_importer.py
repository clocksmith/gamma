"""
Unit tests for Step 2 (DaD record schema & verifier) and Step 3 (DaD importer,
explicit training-weight semantics, and evaluation contamination checks).
"""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from projects.distillation.shared.dad_importer import (
    ContaminationFilter,
    DadImportError,
    DadWeightSemanticsConfig,
    import_dad_bundles,
    import_dad_jsonl,
)
from projects.distillation.shared.dad_schema import (
    DadValidationError,
    canonical_json,
    sha256_json,
    verify_dad_bundle,
)


def _make_valid_dad_bundle(
    *,
    prompt: str = "Explain why cooperative GEMV reduces subgroup reduction overhead on RDNA3.",
    winner_text: str = "Cooperative GEMV assigns multiple threads per quantized row and reduces in shared memory.",
    critic_text: str = "A single thread per row is simpler and avoids workgroup barriers.",
    winner_weight: float = 0.75,
    critic_weight: float = 0.25,
    include_reject: bool = True,
    student_family: str = "gemma4",
    student_adapter: str = "route-adapter-v0",
) -> Dict[str, Any]:
    """Construct a complete, cryptographically consistent MoM/DaD bundle (`dadVersion: 0`)."""
    request = {
        "prompt": prompt,
        "src_lang": "en",
        "tgt_lang": "en",
    }
    input_hash = sha256_json(request)
    cfr_policy_hash = sha256_json({"policyId": "cfr.default.v0", "version": 0})
    budget_policy_hash = sha256_json({"budgetPolicy": "mom.budget.v0"})
    candidate_set_hash = sha256_json(["gemma4-moe-local", "qwen-moe-remote"])
    adj_policy_hash = sha256_json({"adjudicatorPolicy": "judge.v0"})

    route_plan = {
        "momVersion": 0,
        "requestId": "req_001",
        "inputHash": input_hash,
        "mode": "escalated",
        "distillationMode": "debate_adjudicated",
        "receiptBudget": {
            "units": 8,
            "spent": 2,
            "policyHash": budget_policy_hash,
        },
        "cfr": {
            "policyId": "cfr.default.v0",
            "policyHash": cfr_policy_hash,
            "tiePolicy": "stable-choice",
            "topK": 2,
            "candidateSetHash": candidate_set_hash,
            "selected": [
                {"substrateId": "gemma4-moe-local", "role": "proposer", "weight": 0.61},
                {"substrateId": "qwen-moe-remote", "role": "critic", "weight": 0.39},
            ],
        },
        "debate": {
            "rounds": [],
            "adjudicator": {
                "substrateId": "judge-local",
                "policyHash": adj_policy_hash,
            },
        },
        "recursion": {
            "parentMomTranscriptRoot": None,
            "childMomTranscriptRoots": [],
        },
    }

    prop_a_payload = {"text": winner_text}
    prop_b_payload = {"text": critic_text}
    prop_a_hash = sha256_json(prop_a_payload)
    prop_b_hash = sha256_json(prop_b_payload)

    sub_root_a = sha256_json({"substrate": "gemma4-moe-local", "trace": 1})
    sub_root_b = sha256_json({"substrate": "qwen-moe-remote", "trace": 2})

    crit_1_payload = {"claim": "Proposal B ignores bank conflicts on RDNA3."}
    crit_2_payload = {"claim": "Proposal A should bound shared-memory occupancy."}
    crit_1_hash = sha256_json(crit_1_payload)
    crit_2_hash = sha256_json(crit_2_payload)

    resp_1_payload = {"rebuttal": "Shared-memory tile is 128 floats, preserving occupancy."}
    resp_2_payload = {"rebuttal": "Acknowledged; serial per-row loop stalls on global loads."}
    resp_1_hash = sha256_json(resp_1_payload)
    resp_2_hash = sha256_json(resp_2_payload)

    debate_round = {
        "round": 0,
        "participants": ["gemma4-moe-local", "qwen-moe-remote"],
        "proposals": [
            {
                "substrateId": "gemma4-moe-local",
                "payloadType": "text/plain",
                "proposalHash": prop_a_hash,
                "substrateTranscriptRoot": sub_root_a,
                "confidence": 0.84,
            },
            {
                "substrateId": "qwen-moe-remote",
                "payloadType": "text/plain",
                "proposalHash": prop_b_hash,
                "substrateTranscriptRoot": sub_root_b,
                "confidence": 0.52,
            },
        ],
        "critiques": [
            {
                "fromSubstrateId": "gemma4-moe-local",
                "targetProposalHash": prop_b_hash,
                "critiqueHash": crit_1_hash,
            },
            {
                "fromSubstrateId": "qwen-moe-remote",
                "targetProposalHash": prop_a_hash,
                "critiqueHash": crit_2_hash,
            },
        ],
        "responses": [
            {
                "fromSubstrateId": "gemma4-moe-local",
                "targetCritiqueHash": crit_2_hash,
                "responseHash": resp_1_hash,
            },
            {
                "fromSubstrateId": "qwen-moe-remote",
                "targetCritiqueHash": crit_1_hash,
                "responseHash": resp_2_hash,
            },
        ],
    }

    distillation_weights = [
        {
            "proposalHash": prop_a_hash,
            "substrateId": "gemma4-moe-local",
            "weight": winner_weight,
        },
        {
            "proposalHash": prop_b_hash,
            "substrateId": "qwen-moe-remote",
            "weight": critic_weight,
        },
    ]
    weights_hash = sha256_json(distillation_weights)
    score_vector_hash = sha256_json([winner_weight, critic_weight])

    rejects = (
        [{"proposalHash": prop_b_hash, "reasonCodes": ["low-evidence"]}]
        if include_reject
        else []
    )

    adjudication = {
        "winnerProposalHash": prop_a_hash,
        "winnerSubstrateId": "gemma4-moe-local",
        "adjudicatorSubstrateId": "judge-local",
        "policyHash": adj_policy_hash,
        "scoreVectorHash": score_vector_hash,
        "distillationWeights": distillation_weights,
        "distillationWeightsHash": weights_hash,
        "rejects": rejects,
    }

    transcript = {
        "momVersion": 0,
        "routePlanHash": sha256_json(route_plan),
        "cfrPolicyHash": cfr_policy_hash,
        "substrateTranscriptRoots": [sub_root_a, sub_root_b],
        "debateRoundHashes": [sha256_json(debate_round)],
        "adjudicationHash": sha256_json(adjudication),
        "recursion": route_plan["recursion"],
        "dadExportHash": None,
    }
    mom_transcript_root = sha256_json(transcript)

    dad_export = {
        "dadVersion": 0,
        "momTranscriptRoot": mom_transcript_root,
        "winnerProposalHash": prop_a_hash,
        "winnerSubstrateId": "gemma4-moe-local",
        "teacherSetHash": candidate_set_hash,
        "distillationWeightsHash": weights_hash,
        "studentTarget": {
            "family": student_family,
            "adapterId": student_adapter,
        },
        "scoreVectorHash": score_vector_hash,
        "accepted": True,
    }

    return {
        "request": request,
        "routePlan": route_plan,
        "round": debate_round,
        "adjudication": adjudication,
        "transcript": transcript,
        "momTranscriptRoot": mom_transcript_root,
        "dad": dad_export,
        "proposalPayloads": {
            prop_a_hash: prop_a_payload,
            prop_b_hash: prop_b_payload,
        },
        "critiquePayloads": {
            crit_1_hash: crit_1_payload,
            crit_2_hash: crit_2_payload,
        },
        "responsePayloads": {
            resp_1_hash: resp_1_payload,
            resp_2_hash: resp_2_payload,
        },
    }


def _rebind_transcript_and_dad(bundle: Dict[str, Any]) -> None:
    """Recompute round/adjudication/transcript hashes when testing inner invariant failures."""
    bundle["transcript"]["debateRoundHashes"] = [sha256_json(bundle["round"])]
    bundle["transcript"]["adjudicationHash"] = sha256_json(bundle["adjudication"])
    root = sha256_json(bundle["transcript"])
    bundle["momTranscriptRoot"] = root
    bundle["dad"]["momTranscriptRoot"] = root


class TestStep2DadSchemaAndVerifier(unittest.TestCase):
    """Tests for Step 2: DaD record schema and 5-part validity invariant verification."""

    def test_valid_dad_bundle_passes_verification(self):
        bundle = _make_valid_dad_bundle()
        verified = verify_dad_bundle(bundle, require_accepted=True, require_proposal_payloads=True)
        self.assertEqual(verified.export_row.dad_version, 0)
        self.assertEqual(verified.mom_transcript_root, bundle["momTranscriptRoot"])
        self.assertEqual(len(verified.proposals_by_hash), 2)
        self.assertEqual(
            verified.adjudication.distillation_weights_hash,
            bundle["dad"]["distillationWeightsHash"],
        )

    def test_invariant_1_missing_proposal_or_substrate_transcript_root_fails(self):
        # Missing proposal from second participant
        bundle = _make_valid_dad_bundle()
        bundle["round"]["proposals"].pop()
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle)

        # Missing substrateTranscriptRoot on a proposal
        bundle2 = _make_valid_dad_bundle()
        bundle2["round"]["proposals"][0]["substrateTranscriptRoot"] = None
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle2)

        # Tampered proposal payload fails proposalHash verification
        bundle3 = _make_valid_dad_bundle()
        winner_hash = bundle3["dad"]["winnerProposalHash"]
        bundle3["proposalPayloads"][winner_hash] = {"text": "Tampered text payload"}
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle3, require_proposal_payloads=True)

    def test_invariant_2_proposal_missing_critique_fails(self):
        bundle = _make_valid_dad_bundle()
        # Keep only the first critique so proposal A is uncritiqued
        bundle["round"]["critiques"] = [bundle["round"]["critiques"][0]]
        bundle["round"]["responses"] = [bundle["round"]["responses"][1]]
        _rebind_transcript_and_dad(bundle)
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle)

    def test_invariant_3_critique_missing_response_fails(self):
        bundle = _make_valid_dad_bundle()
        # Drop one response so one critique has no response
        bundle["round"]["responses"].pop()
        _rebind_transcript_and_dad(bundle)
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle)

    def test_invariant_4_adjudication_missing_proposal_weight_or_winner_in_rejects_fails(self):
        # Missing weight for second proposal
        bundle = _make_valid_dad_bundle()
        bundle["adjudication"]["distillationWeights"].pop()
        bundle["adjudication"]["distillationWeightsHash"] = sha256_json(
            bundle["adjudication"]["distillationWeights"]
        )
        bundle["dad"]["distillationWeightsHash"] = bundle["adjudication"]["distillationWeightsHash"]
        _rebind_transcript_and_dad(bundle)
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle)

        # Winner listed in rejects
        bundle2 = _make_valid_dad_bundle()
        winner_hash = bundle2["adjudication"]["winnerProposalHash"]
        bundle2["adjudication"]["rejects"].append(
            {"proposalHash": winner_hash, "reasonCodes": ["contradiction"]}
        )
        _rebind_transcript_and_dad(bundle2)
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle2)

    def test_invariant_5_tampered_distillation_weights_hash_or_transcript_root_fails(self):
        # Mutate weight without updating distillationWeightsHash
        bundle = _make_valid_dad_bundle()
        bundle["adjudication"]["distillationWeights"][0]["weight"] = 0.99
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle)

        # Mutate dad.momTranscriptRoot so it does not match transcript
        bundle2 = _make_valid_dad_bundle()
        bundle2["dad"]["momTranscriptRoot"] = "sha256:" + ("0" * 64)
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle2)

        # Route-only plan with debate_adjudicated mode is rejected
        bundle3 = _make_valid_dad_bundle()
        bundle3["routePlan"]["mode"] = "route_only"
        bundle3["transcript"]["routePlanHash"] = sha256_json(bundle3["routePlan"])
        _rebind_transcript_and_dad(bundle3)
        with self.assertRaises(DadValidationError):
            verify_dad_bundle(bundle3)


class TestStep3DadImporterWeightSemanticsAndContamination(unittest.TestCase):
    """Tests for Step 3: DaD importer training-weight semantics and contamination checks."""

    def test_winner_sft_mode_emits_normalized_winner_row(self):
        bundle = _make_valid_dad_bundle(
            winner_weight=0.80,
            critic_weight=0.0,
            include_reject=True,
        )
        config = DadWeightSemanticsConfig(
            loss_mode="winner_sft",
            expected_student_family="gemma4",
            expected_student_adapter_id="route-adapter-v0",
            emit_translation_compat=True,
        )
        result = import_dad_bundles([bundle], config=config, strict=True)
        self.assertEqual(result.available_bundles, 1)
        self.assertEqual(result.accepted_bundles, 1)
        self.assertEqual(result.rejected_bundles, 0)
        self.assertEqual(len(result.emitted_rows), 1)

        row = result.emitted_rows[0]
        self.assertEqual(row["loss_mode"], "winner_sft")
        self.assertEqual(row["mom_transcript_root"], bundle["momTranscriptRoot"])
        self.assertEqual(row["winner_proposal_hash"], bundle["dad"]["winnerProposalHash"])
        self.assertAlmostEqual(row["sample_weight"], 1.0, places=6)
        self.assertEqual(row["prompt"], bundle["request"]["prompt"])
        self.assertIn("Cooperative GEMV", row["target_pos"])
        # Translation compatibility keys populated when requested
        self.assertEqual(row["pair"], "en-en")
        self.assertEqual(row["query"], bundle["request"]["prompt"])

    def test_weighted_sft_normalizes_non_rejected_proposals_and_blocks_positive_rejected_weight(self):
        # Two non-rejected proposals with weights 0.60 and 0.20 -> normalized to 0.75 and 0.25
        bundle = _make_valid_dad_bundle(
            winner_weight=0.60,
            critic_weight=0.20,
            include_reject=False,
        )
        config = DadWeightSemanticsConfig(
            loss_mode="weighted_sft",
            min_proposal_weight=0.05,
        )
        result = import_dad_bundles([bundle], config=config, strict=True)
        self.assertEqual(len(result.emitted_rows), 2)
        weights = [r["sample_weight"] for r in result.emitted_rows]
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        self.assertAlmostEqual(weights[0], 0.75, places=6)
        self.assertAlmostEqual(weights[1], 0.25, places=6)

        # If a rejected proposal still carries positive weight in SFT mode, reject the bundle
        bad_bundle = _make_valid_dad_bundle(
            winner_weight=0.75,
            critic_weight=0.25,
            include_reject=True,  # critic is in rejects but has weight 0.25 > 0.0
        )
        with self.assertRaises(DadImportError):
            import_dad_bundles([bad_bundle], config=config, strict=True)

    def test_contrastive_preference_mode_emits_margin_weighted_pairs(self):
        bundle = _make_valid_dad_bundle(
            winner_weight=0.75,
            critic_weight=0.25,
            include_reject=True,
        )
        config = DadWeightSemanticsConfig(
            loss_mode="contrastive_preference",
            min_weight_margin=0.20,
            emit_translation_compat=True,
        )
        result = import_dad_bundles([bundle], config=config, strict=True)
        self.assertEqual(len(result.emitted_rows), 1)
        row = result.emitted_rows[0]
        self.assertEqual(row["loss_mode"], "contrastive_preference")
        self.assertAlmostEqual(row["raw_weight_margin"], 0.50, places=6)
        self.assertAlmostEqual(row["sample_weight"], 0.50, places=6)
        self.assertTrue(row["neg_explicitly_rejected"])
        self.assertNotEqual(row["target_pos"], row["target_neg"])

        # Margin below threshold fails closed
        strict_margin_cfg = DadWeightSemanticsConfig(
            loss_mode="contrastive_preference",
            min_weight_margin=0.60,
        )
        with self.assertRaises(DadImportError):
            import_dad_bundles([bundle], config=strict_margin_cfg, strict=True)

    def test_student_target_mismatch_rejected(self):
        bundle = _make_valid_dad_bundle(student_family="qwen3", student_adapter="adapter-qwen")
        config = DadWeightSemanticsConfig(
            loss_mode="winner_sft",
            expected_student_family="gemma4",
        )
        with self.assertRaises(DadImportError):
            import_dad_bundles([bundle], config=config, strict=True)

    def test_contamination_filter_rejects_exact_and_ngram_overlaps(self):
        eval_prompt = "Explain why cooperative GEMV reduces subgroup reduction overhead on RDNA3."
        eval_completion = (
            "Cooperative GEMV assigns multiple threads per quantized row and reduces in shared memory."
        )

        # 1. Exact prompt match rejected
        bundle_exact = _make_valid_dad_bundle(
            prompt=eval_prompt,
            winner_weight=0.8,
            critic_weight=0.0,
        )
        c_filter = ContaminationFilter([eval_prompt])
        config = DadWeightSemanticsConfig(loss_mode="winner_sft")
        with self.assertRaises(DadImportError):
            import_dad_bundles([bundle_exact], config=config, contamination_filter=c_filter, strict=True)

        # 2. High 5-gram overlap on proposal completion rejected
        bundle_ngram = _make_valid_dad_bundle(
            prompt="How does RDNA3 handle quantized matrix-vector multiplication?",
            winner_text=(
                "In WebGPU, cooperative GEMV assigns multiple threads per quantized row "
                "and reduces in shared memory for speed."
            ),
            winner_weight=0.8,
            critic_weight=0.0,
        )
        c_filter_comp = ContaminationFilter([eval_completion], ngram_size=5, max_ngram_overlap=0.7)
        with self.assertRaises(DadImportError):
            import_dad_bundles(
                [bundle_ngram], config=config, contamination_filter=c_filter_comp, strict=True
            )

    def test_non_strict_mode_separates_available_and_accepted_bundles_and_jsonl_roundtrip(self):
        clean_bundle = _make_valid_dad_bundle(
            prompt="Derive the online softmax rescaling update for two attention blocks.",
            winner_text="Track running max m and normalizer l, rescaling l by exp(m_old - m_new).",
            critic_text="Materialize all attention scores in global memory before softmax.",
            winner_weight=0.9,
            critic_weight=0.0,
        )
        contaminated_bundle = _make_valid_dad_bundle(
            prompt="Benchmark leaked prompt from WMT13 evaluation set.",
            winner_weight=0.9,
            critic_weight=0.0,
        )
        tampered_bundle = copy.deepcopy(clean_bundle)
        tampered_bundle["dad"]["distillationWeightsHash"] = "sha256:" + ("f" * 64)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            eval_jsonl = tmp_path / "eval.jsonl"
            eval_jsonl.write_text(
                json.dumps({"prompt": "Benchmark leaked prompt from WMT13 evaluation set."}) + "\n",
                encoding="utf-8",
            )
            c_filter = ContaminationFilter.from_jsonl_files([eval_jsonl])

            in_jsonl = tmp_path / "dad_bundles.jsonl"
            out_jsonl = tmp_path / "imported_rows.jsonl"
            with in_jsonl.open("w", encoding="utf-8") as handle:
                for b in (clean_bundle, contaminated_bundle, tampered_bundle):
                    handle.write(canonical_json(b) + "\n")

            config = DadWeightSemanticsConfig(loss_mode="winner_sft")
            result = import_dad_jsonl(
                in_jsonl,
                out_jsonl,
                config=config,
                contamination_filter=c_filter,
                strict=False,
            )

            self.assertEqual(result.available_bundles, 3)
            self.assertEqual(result.accepted_bundles, 1)
            self.assertEqual(result.rejected_bundles, 2)
            self.assertEqual(len(result.emitted_rows), 1)
            self.assertEqual(result.rejections[0].stage, "semantics_and_decontamination")
            self.assertEqual(result.rejections[1].stage, "schema_and_provenance")

            written_lines = [
                json.loads(line)
                for line in out_jsonl.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(written_lines), 1)
            self.assertEqual(written_lines[0]["mom_transcript_root"], clean_bundle["momTranscriptRoot"])


if __name__ == "__main__":
    unittest.main()
