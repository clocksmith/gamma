"""Active report targets must agree without changing historical proof bindings."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from projects.enwiki9.tools import enwiki9_best_results as best_results
from projects.enwiki9.tools import enwiki9_evidence_matrix as evidence
from projects.enwiki9.tools import hutter_upper_bound_certificate as certificate
from projects.enwiki9.tools import research_contracts


class ReportTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        # These tests exercise report evidence, without inspecting live workers.
        top_status = mock.patch.object(certificate, "build_top_status", return_value=[])
        top_status.start()
        self.addCleanup(top_status.stop)

    def result(self, score: int, **changes: object) -> certificate.Result:
        row = certificate.Result(
            path=certificate.ROOT / "results" / "report-target-fixture" / "result.json",
            program_id="report-target-fixture",
            data_size=certificate.FULL_INPUT_BYTES,
            data_sha256=certificate.OBJECTIVE_BINDING["corpusSha256"],
            compressed_size=score - 1000,
            program_size=1000,
            hutter_score=score,
            roundtrip_ok=True,
            determinism_ok=True,
            timestamp="fixture",
            objective_digest=certificate.OBJECTIVE_BINDING["objectiveDigest"],
            score_accounting_complete=True,
            dependency_closure_complete=True,
            resource_evidence_complete=True,
            independent_decode_ok=True,
            license_audit_ok=True,
            prize_claimable=True,
        )
        return replace(row, **changes)

    def matrix_row(self, row: certificate.Result) -> evidence.Row:
        return evidence.Row(
            path=row.path,
            program_id=row.program_id,
            data_size=row.data_size,
            compressed_size=row.compressed_size,
            program_size=row.program_size,
            score=row.hutter_score,
            roundtrip_ok=row.roundtrip_ok,
            determinism_ok=row.determinism_ok,
        )

    def markdown(self, cert: dict) -> str:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "certificate.md"
            certificate.write_markdown(cert, path)
            return path.read_text()

    def test_active_target_and_historical_digest_remain_distinct(self) -> None:
        active = research_contracts.validate_objective()
        historical = research_contracts.objective_binding(
            objective_path="contracts/research/v1/objective-contract.json"
        )
        self.assertEqual(active["score"]["targetBytes"], 99_000_000)
        self.assertEqual(historical["targetScoreBytes"], 105_000_000)
        self.assertEqual(historical["objectiveDigest"], active["migration"]["previousObjectiveDigest"])
        self.assertNotEqual(historical["objectiveDigest"], certificate.OBJECTIVE_BINDING["objectiveDigest"])
        self.assertEqual(evidence.FULL_INPUT_BYTES, active["corpus"]["bytes"])
        self.assertEqual(evidence.TARGET_10_95, active["score"]["targetBytes"])
        self.assertEqual(certificate.TARGET_10_95, evidence.TARGET_10_95)
        self.assertEqual(evidence.TARGET_PERCENT, 9.9)

    def test_100m_full_score_misses_active_target_despite_historical_margin(self) -> None:
        row = self.result(100_000_000)
        historical_target = certificate.OBJECTIVE["migration"]["historicalMilestoneBytes"]
        self.assertLess(row.hutter_score, historical_target)
        self.assertGreater(row.hutter_score, certificate.TARGET_10_95)
        cert = certificate.build_certificate([row])
        status = cert["proof_status"]
        self.assertTrue(status["has_full_corpus_constructive_result"])
        self.assertFalse(status["has_10_95_constructive_upper_bound"])
        self.assertIsNone(status["best_10_95_result"])
        self.assertEqual(status["best_full_corpus_result"]["hutter_score"], 100_000_000)
        self.assertEqual(cert["target"]["target_score_10_95"], 99_000_000)
        self.assertEqual(cert["objective"], certificate.OBJECTIVE_BINDING)
        self.assertIn(
            "`9.9000000%` target reached by this matrix: `False`",
            evidence.render([self.matrix_row(row)], 1),
        )

    def test_exact_target_boundary_remains_inclusive(self) -> None:
        for score, hit in ((99_000_000, True), (99_000_001, False)):
            with self.subTest(score=score):
                row = self.result(score)
                cert = certificate.build_certificate([row])
                self.assertEqual(cert["proof_status"]["has_10_95_constructive_upper_bound"], hit)
                self.assertIn(
                    f"`9.9000000%` target reached by this matrix: `{hit}`",
                    evidence.render([self.matrix_row(row)], 1),
                )

    def test_missing_evidence_and_historical_binding_still_block_certificate(self) -> None:
        disqualifiers = [
            {field: False} for field in (
                "roundtrip_ok", "determinism_ok", "score_accounting_complete",
                "dependency_closure_complete", "resource_evidence_complete",
                "independent_decode_ok", "license_audit_ok", "prize_claimable",
            )
        ] + [
            {"data_size": 100_000_000},
            {"data_sha256": "different-corpus"},
            {"objective_digest": certificate.OBJECTIVE["migration"]["previousObjectiveDigest"]},
        ]
        for changes in disqualifiers:
            with self.subTest(changes=changes):
                row = self.result(90_000_000, **changes)
                cert = certificate.build_certificate([row])
                self.assertFalse(cert["proof_status"]["has_full_corpus_constructive_result"])
                self.assertFalse(cert["proof_status"]["has_10_95_constructive_upper_bound"])
                if row.roundtrip_ok:
                    recorded, = cert["best_exact_upper_bounds_by_scope"]
                    self.assertEqual(recorded["objective_digest"], row.objective_digest)

    def test_matrix_prefix_and_failed_roundtrip_still_miss_target(self) -> None:
        for changes in ({"data_size": 100_000_000}, {"roundtrip_ok": False}):
            with self.subTest(changes=changes):
                row = self.matrix_row(self.result(9_000_000, **changes))
                self.assertIn(
                    "`9.9000000%` target reached by this matrix: `False`",
                    evidence.render([row], 1),
                )

    def test_all_reports_render_matching_active_target_and_notes(self) -> None:
        row = self.result(100_000_000)
        cert = certificate.build_certificate([row])
        reports = {
            "certificate": self.markdown(cert),
            "matrix": evidence.render([self.matrix_row(row)], 1),
            "best_results": best_results.render([self.matrix_row(row)], 1),
        }
        for name, rendered in reports.items():
            with self.subTest(report=name):
                self.assertIn("9.9000000%", rendered)
                self.assertIn("99,000,000", rendered)
                self.assertNotIn("10.5%", rendered)
                self.assertNotIn("10.5000000%", rendered)
                self.assertNotIn("105000000", rendered)
                self.assertNotIn("105,000,000", rendered)
        self.assertIn(
            "A 9.9000000% proof requires a full 1,000,000,000-byte result with score <= 99,000,000.",
            cert["notes"],
        )

    def test_historical_certificate_renders_its_own_bound_target(self) -> None:
        historical = research_contracts.objective_binding(
            objective_path="contracts/research/v1/objective-contract.json"
        )
        with mock.patch.multiple(
            certificate,
            OBJECTIVE_BINDING=historical,
            FULL_INPUT_BYTES=historical["corpusBytes"],
            TARGET_10_95=historical["targetScoreBytes"],
        ):
            cert = certificate.build_certificate([self.result(100_000_000)])
        rendered = self.markdown(cert)
        self.assertEqual(certificate.TARGET_10_95, 99_000_000)
        self.assertEqual(cert["objective"]["objectiveDigest"], historical["objectiveDigest"])
        self.assertTrue(cert["proof_status"]["has_10_95_constructive_upper_bound"])
        self.assertIn("10.5000000% target score: `105,000,000`", rendered)
        self.assertIn("score <= 105,000,000.", rendered)
        self.assertNotIn("9.9000000%", rendered)


if __name__ == "__main__":
    unittest.main()
