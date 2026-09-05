#!/usr/bin/env python3
"""Tests for counted prefix-forecast selection."""

from __future__ import annotations

import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from projects.enwiki9.tools import hutter_upper_bound_certificate as certificate


class BestForecastRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        canonical = mock.patch.object(
            certificate, "canonical_frontier_forecast_record", return_value=None
        )
        canonical.start()
        self.addCleanup(canonical.stop)

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
                            "conservative_projected_margin_bytes": -4_557_404,
                            "conservative_projected_score_bytes": 109_557_404,
                            "target_score_bytes": 105_000_000,
                        },
                        "decision": {"verdict": "retire_economics_miss"},
                    }
                )
            )

            selected = certificate.best_forecast_record(results_dir)

        self.assertEqual(selected["program_id"], "endpoint428")
        self.assertEqual(selected["projected_score"], 109_557_404)
        self.assertEqual(selected["projected_margin_bytes"], certificate.TARGET_10_95 - 109_557_404)
        self.assertEqual(selected["source_projected_margin_bytes"], -4_557_404)
        self.assertEqual(selected["source_target_score_bytes"], 105_000_000)
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
                            "conservative_projected_score_bytes": 108_000_000,
                            "target_score_bytes": 105_000_000,
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
                            "provisional_target_margin_bytes": -4_524_268,
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
        self.assertEqual(selected["projected_margin_bytes"], certificate.TARGET_10_95 - 109_524_268)
        self.assertEqual(selected["source_projected_margin_bytes"], -4_524_268)
        self.assertIsNone(selected["source_target_score_bytes"])
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
                            "provisional_target_margin_bytes": -4_524_268,
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
                            "provisional_target_margin_bytes": -4_452_151,
                            "target_score_bytes": 105_000_000,
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
                            "provisional_target_margin_bytes": -4_452_151,
                            "target_score_bytes": 105_000_000,
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
        self.assertEqual(selected["projected_margin_bytes"], certificate.TARGET_10_95 - 109_452_151)
        self.assertEqual(selected["source_projected_margin_bytes"], -4_452_151)
        self.assertIs(selected["codec_replay_complete"], True)


class ActiveCandidateContextTests(unittest.TestCase):
    def test_existing_observer_uses_raw_scope_and_preserves_resource_gap(self) -> None:
        import enwiki9_status_receipt as status
        observer = {"candidate": "source", "scope_bytes": 1_000_000_000,
                    "scope_symbols": 647_798_592, "source_processes_live": True,
                    "observer_job_id": "existing-observer"}
        with (
            mock.patch.object(status, "adaptive_running_jobs_state", return_value={}),
            mock.patch.object(status, "existing_horizon_observer_state", return_value=observer),
        ):
            candidate, scope, source = certificate.active_candidate_context()
        self.assertEqual((candidate, scope), ("source", 1_000_000_000))
        self.assertIn("continuous resource proof remains missing", source)

    def test_vanished_saved_worker_does_not_establish_idle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            running = root / "operations/adaptive/running"
            running.mkdir(parents=True)
            (running / "job.json").write_text(json.dumps({"candidate_id": "source", "gate_size": 17, "worker_pid": 1234}))
            with (mock.patch.object(certificate, "ROOT", root),
                  mock.patch.object(certificate.worker_identity, "worker_pid_matches_job", return_value=False)):
                candidate, scope, source = certificate.active_candidate_context()
        self.assertIsNone(candidate)
        self.assertIsNone(scope)
        self.assertIn("unknown", source)

    def test_uses_shared_managed_worker_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            running = root / "operations" / "adaptive" / "running"
            running.mkdir(parents=True)
            job = {
                "job_id": "job-id",
                "candidate_id": "candidate-id",
                "gate_size": 17,
                "worker_pid": 1234,
            }
            receipt = running / "job.json"
            receipt.write_text(json.dumps(job) + "\n")
            with (
                mock.patch.object(certificate, "ROOT", root),
                mock.patch.object(
                    certificate.worker_identity,
                    "worker_pid_matches_job",
                    return_value=True,
                ) as matches,
            ):
                candidate, scope, source = certificate.active_candidate_context()

        self.assertEqual(candidate, "candidate-id")
        self.assertEqual(scope, 17)
        self.assertIn("job.json", source)
        matches.assert_called_once_with(
            root, root / "tools" / "candidate_triage.py", job
        )


if __name__ == "__main__":
    unittest.main()
