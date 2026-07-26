#!/usr/bin/env python3
"""Tests for counted prefix-forecast selection."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from projects.enwiki9.tools import hutter_upper_bound_certificate as certificate


class BestForecastRecordTests(unittest.TestCase):
    def test_falls_back_to_calibrated_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            selected = certificate.best_forecast_record(Path(temp_dir))

        self.assertEqual(selected, certificate.BASELINE_FORECAST)

    def test_selects_exact_counted_10m_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            candidate_dir = results_dir / "endpoint428"
            candidate_dir.mkdir()
            (candidate_dir / "receipt.json").write_text(
                json.dumps(
                    {
                        "evidence_level": "exact_guarded_10m_archive_screen",
                        "scope": {"raw_bytes": 10_000_000},
                        "economics": {
                            "candidate_archive_bytes_10m": 1_635_695,
                            "conservative_projected_margin_bytes": -57_404,
                            "conservative_projected_score_bytes": 109_557_404,
                            "target_score_bytes": 109_000_000,
                        },
                        "decision": {"verdict": "retire_economics_miss"},
                    }
                )
            )

            selected = certificate.best_forecast_record(results_dir)

        self.assertEqual(selected["program_id"], "endpoint428")
        self.assertEqual(selected["projected_score"], 109_557_404)
        self.assertEqual(selected["projected_margin_bytes"], -57_404)
        self.assertEqual(selected["scope_bytes"], 10_000_000)
        self.assertIn("retire_economics_miss", selected["evidence"])

    def test_rejects_opening_prefix_forecast(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            candidate_dir = results_dir / "opening_only"
            candidate_dir.mkdir()
            (candidate_dir / "receipt.json").write_text(
                json.dumps(
                    {
                        "evidence_level": "exact_guarded_1m_archive_screen",
                        "scope": {"raw_bytes": 1_000_000},
                        "economics": {
                            "conservative_projected_score_bytes": 109_000_000,
                            "target_score_bytes": 109_000_000,
                        },
                        "decision": {"verdict": "opening_pass"},
                    }
                )
            )

            selected = certificate.best_forecast_record(results_dir)

        self.assertEqual(selected, certificate.BASELINE_FORECAST)

    def test_selects_pair_layer0_terminal_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            candidate_dir = results_dir / "endpoint428_pair_layer0"
            candidate_dir.mkdir()
            (candidate_dir / "receipt.json").write_text(
                json.dumps(
                    {
                        "evidence_level": "guarded_exact_10m_archive_screen",
                        "scope": {"raw_bytes": 10_000_000},
                        "economics": {
                            "candidate_archive_bytes_10m": 1_635_174,
                            "conservative_provisional_score_bytes": 109_524_268,
                            "provisional_target_margin_bytes": -24_268,
                        },
                        "decision": {
                            "verdict": "retire_unchanged_exact_10m_economics_miss"
                        },
                    }
                )
            )

            selected = certificate.best_forecast_record(results_dir)

        self.assertEqual(selected["program_id"], "endpoint428_pair_layer0")
        self.assertEqual(selected["projected_score"], 109_524_268)
        self.assertEqual(selected["projected_margin_bytes"], -24_268)
        self.assertEqual(selected["archive_bytes"], 1_635_174)

    def test_lzma_replay_projection_supersedes_bzip2_miss(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            bzip2_dir = results_dir / "endpoint428_pair_layer0_bzip2"
            bzip2_dir.mkdir()
            (bzip2_dir / "receipt.json").write_text(
                json.dumps(
                    {
                        "evidence_level": "guarded_exact_10m_archive_screen",
                        "scope": {"raw_bytes": 10_000_000},
                        "economics": {
                            "candidate_archive_bytes_10m": 1_635_174,
                            "conservative_provisional_score_bytes": 109_524_268,
                            "provisional_target_margin_bytes": -24_268,
                        },
                        "decision": {"verdict": "bzip2_economics_miss"},
                    }
                )
            )
            bridge_dir = results_dir / "endpoint428_pair_layer0_lzma_bridge"
            bridge_dir.mkdir()
            (bridge_dir / "receipt.json").write_text(
                json.dumps(
                    {
                        "evidence_level": (
                            "counted_lzma_zip_package_plus_guarded_exact_10m_archive"
                        ),
                        "scope": {"raw_bytes": 10_000_000},
                        "economics": {
                            "candidate_archive_bytes_10m": 1_635_174,
                            "conservative_provisional_score_bytes": 109_452_151,
                            "provisional_target_margin_bytes": 47_849,
                            "target_score_bytes": 109_000_000,
                        },
                        "proof": {"roundtrip_ok": False, "determinism_ok": False},
                        "decision": {"verdict": "replay_pending"},
                    }
                )
            )
            lzma_dir = results_dir / "endpoint428_pair_layer0_lzma_replay"
            lzma_dir.mkdir()
            (lzma_dir / "receipt.json").write_text(
                json.dumps(
                    {
                        "evidence_level": (
                            "constructive_counted_exact_10m_lzma_package_and_codec_proof"
                        ),
                        "scope": {"raw_bytes": 10_000_000},
                        "economics": {
                            "candidate_archive_bytes_10m": 1_635_174,
                            "conservative_provisional_score_bytes": 109_452_151,
                            "provisional_target_margin_bytes": 47_849,
                            "target_score_bytes": 109_000_000,
                        },
                        "decision": {
                            "verdict": "constructive_exact_10m_lzma_pass"
                        },
                        "proof": {"roundtrip_ok": True, "determinism_ok": True},
                    }
                )
            )

            selected = certificate.best_forecast_record(results_dir)

        self.assertEqual(
            selected["program_id"], "endpoint428_pair_layer0_lzma_replay"
        )
        self.assertEqual(selected["projected_score"], 109_452_151)
        self.assertEqual(selected["projected_margin_bytes"], 47_849)
        self.assertIs(selected["codec_replay_complete"], True)


if __name__ == "__main__":
    unittest.main()
