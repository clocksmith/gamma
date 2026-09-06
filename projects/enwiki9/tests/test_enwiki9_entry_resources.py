"""Resource diagnostics must not invent capacity, completion, or launch authority."""

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import enwiki9_ledger as ledger


NOW = datetime(2026, 9, 6, 12, 10, tzinfo=timezone.utc)


def observations():
    previous = {
        "source": "bound_existing_horizon_observer", "adaptive_job_id": "source",
        "adaptive_job_path": "operations/adaptive/running/source.json",
        "observer_job_id": "observer", "observer_candidate": "observer-candidate",
        "observer_progress_path": "results/observer-candidate/progress.json",
        "observer_progress_fresh": True, "observer_sample_identities_match": True,
        "source_processes_live": True, "observer_worker_live": True,
        "observer_progress": {"state": "observing", "updatedUtc": "2026-09-06T12:00:00Z",
                              "traceBytes": 100, "expectedTraceBytes": 1000, "sampleCount": 10}}
    current = copy.deepcopy(previous)
    current["observer_progress"].update(updatedUtc="2026-09-06T12:10:00Z", traceBytes=400, sampleCount=20)
    run = {"id": "source", "state": "running", "liveness": {"state": "live"},
           "submitted_at": "2026-09-06T10:59:00Z", "started_at": "2026-09-06T11:00:00Z",
           "worker_started_at": "2026-09-06T11:00:01Z", "resource_budget": {"wall_seconds": 7200},
           "progress_observation": current}
    return run, previous


class TimelineTests(unittest.TestCase):
    def test_phase_prediction_is_distinct_from_stop_and_job_finish(self):
        run, previous = observations()
        result = ledger.job_timeline(run, previous, NOW)
        self.assertEqual(result["elapsed_since_recorded_start_seconds"], 4200)
        self.assertEqual(result["budget_stop_reference_at"], "2026-09-06T13:00:00+00:00")
        self.assertIsNone(result["expected_job_finish_at"])
        estimate = result["phase_estimate"]
        self.assertEqual(estimate["bytes_per_second"], 0.5)
        self.assertEqual(estimate["expected_phase_finish_at"], "2026-09-06T12:30:00+00:00")
        self.assertEqual(estimate["units"], "transformed trace bytes")
        self.assertEqual(estimate["remaining_bytes"], 600)

    def test_identity_mismatch_or_unverified_occupancy_suppresses_estimate(self):
        for target in ("current", "previous"):
            for key, value in (("observer_job_id", "replacement"), ("adaptive_job_path", "replaced.json"),
                               ("source", "unbound"), ("source_processes_live", False),
                               ("observer_sample_identities_match", False), ("observer_progress_fresh", False),
                               ("observer_worker_live", False)):
                with self.subTest(target=target, key=key):
                    run, previous = observations()
                    (run["progress_observation"] if target == "current" else previous)[key] = value
                    self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "unknown")
        for key, value in (("state", "completed"), ("id", "unrelated"), ("liveness", {"state": "unknown"})):
            run, previous = observations()
            run[key] = value
            self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "unknown")

    def test_invalid_or_changed_counters_do_not_predict(self):
        for key, value in (("traceBytes", 100), ("traceBytes", 99), ("traceBytes", 1000),
                           ("traceBytes", True), ("traceBytes", "400"), ("traceBytes", -1),
                           ("expectedTraceBytes", 2000), ("sampleCount", 10),
                           ("state", "terminal"), ("updatedUtc", "2026-09-06T12:00:00Z"),
                           ("updatedUtc", "2026-09-06T11:59:00Z"), ("updatedUtc", "invalid"),
                           ("updatedUtc", "2026-09-06T12:10:00")):
            with self.subTest(key=key, value=value):
                run, previous = observations()
                run["progress_observation"]["observer_progress"][key] = value
                self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "unknown")

    def test_stale_future_and_overwide_samples_do_not_predict(self):
        for now in (datetime(2026, 9, 6, 12, 13, tzinfo=timezone.utc),
                    datetime(2026, 9, 6, 12, 9, tzinfo=timezone.utc)):
            run, previous = observations()
            self.assertEqual(ledger.job_timeline(run, previous, now)["phase_estimate"]["state"], "unknown")
        run, previous = observations()
        previous["observer_progress"]["updatedUtc"] = "2026-09-06T10:00:00Z"
        self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "unknown")

    def test_missing_progress_is_unknown_without_hiding_recorded_start(self):
        run, _ = observations()
        run.pop("progress_observation")
        run["resource_budget"] = None
        result = ledger.job_timeline(run, now=NOW)
        self.assertEqual(result["started_at"], run["started_at"])
        self.assertEqual(result["phase_estimate"]["state"], "unknown")
        self.assertIsNone(result["budget_stop_reference_at"])

    def test_repository_and_project_relative_observer_paths_match(self):
        run, previous = observations()
        for key in ("adaptive_job_path", "observer_progress_path"):
            previous[key] = "projects/enwiki9/" + previous[key]
        self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "estimated")

    def test_malformed_optional_observations_remain_unknown(self):
        run, previous = observations()
        for malformed in ([1], "invalid"):
            self.assertEqual(ledger.job_timeline(run, malformed, NOW)["phase_estimate"]["state"], "unknown")
            run["progress_observation"] = malformed
            self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "unknown")
        run, previous = observations()
        run["progress_observation"]["observer_progress"] = [1]
        self.assertEqual(ledger.job_timeline(run, previous, NOW)["phase_estimate"]["state"], "unknown")

    def test_invalid_start_and_budget_never_become_deadlines(self):
        for started in (None, "bad", "2026-09-06T11:00:00", "2026-09-07T11:00:00Z"):
            run, _ = observations()
            run["started_at"] = started
            result = ledger.job_timeline(run, now=NOW)
            self.assertIsNone(result["elapsed_since_recorded_start_seconds"])
            self.assertIsNone(result["budget_stop_reference_at"])
        for budget in (True, -1, "7200", float("nan"), float("inf"), 1e100):
            run, _ = observations()
            run["resource_budget"]["wall_seconds"] = budget
            self.assertIsNone(ledger.job_timeline(run, now=NOW)["budget_stop_reference_at"])


class ResourceTests(unittest.TestCase):
    def test_cpu_guest_ticks_not_double_counted_and_iowait_separate(self):
        before = ledger.cpu_ticks("cpu0 10 0 0 90 0 0 0 0 8 0\n")
        after = ledger.cpu_ticks("cpu0 20 0 0 100 20 0 0 0 18 0\n")
        self.assertEqual(ledger.cpu_usage(before, after, [0]),
                         [{"cpu": 0, "busy_percent": 25, "iowait_percent": 50}])

    def test_cpu_reset_missing_or_no_ticks_remain_unknown(self):
        before = ledger.cpu_ticks("cpu0 10 0 0 90 0 0 0 0\n")
        reset = ledger.cpu_ticks("cpu0 5 0 0 100 0 0 0 0\n")
        for after in (before, reset, {}):
            self.assertIsNone(ledger.cpu_usage(before, after, [0])[0]["busy_percent"])
        self.assertEqual(len(ledger.cpu_usage(before, before, [2])), 1)
        self.assertIsNone(ledger.cpu_usage(before, before, [2])[0]["busy_percent"])

    def fixture(self, root):
        proc = root / "proc"
        (proc / "self").mkdir(parents=True)
        mount = root / "cgroup"
        leaf = mount / "parent/leaf"
        leaf.mkdir(parents=True)
        for path in (mount, leaf.parent, leaf):
            (path / "cgroup.controllers").write_text("cpu memory")
        (proc / "self/cgroup").write_text("0::/parent/leaf\n")
        (proc / "self/mountinfo").write_text(f"36 28 0:30 / {mount} rw - cgroup2 cgroup rw\n")
        for path, limit, used, cpu in ((leaf, 600000, 100000, "200000 100000"),
                                      (leaf.parent, 500000, 400000, "50000 100000")):
            (path / "memory.max").write_text(str(limit))
            (path / "memory.current").write_text(str(used))
            (path / "cpu.max").write_text(cpu)
        (proc / "meminfo").write_text("MemTotal: 1000 kB\nMemAvailable: 800 kB\n")
        (proc / "stat").write_text("cpu0 10 0 0 90 0 0 0 0\n")
        return proc, leaf

    def test_parent_cgroup_caps_and_affinity_limit_headroom(self):
        with tempfile.TemporaryDirectory() as directory:
            proc, _ = self.fixture(Path(directory))
            with patch.object(ledger.os, "sched_getaffinity", return_value={0}), \
                    patch.object(ledger.time, "sleep", side_effect=lambda _: (proc / "stat").write_text("cpu0 20 0 0 100 0 0 0 0\n")):
                report = ledger.resource_snapshot(proc)
            self.assertEqual(report["allowed_cpus"], [0])
            self.assertEqual(report["cpu_usage"][0]["busy_percent"], 50)
            self.assertEqual(report["host_memory_available_bytes"], 819200)
            self.assertEqual(report["visible_memory_headroom_bytes"], 100000)
            self.assertEqual(report["visible_cpu_capacity_ceiling"], 0.5)
            self.assertFalse(report["launch_authorized"])

    def test_missing_nonroot_limit_is_unknown_not_unlimited(self):
        with tempfile.TemporaryDirectory() as directory:
            proc, leaf = self.fixture(Path(directory))
            (leaf.parent / "memory.max").unlink()
            with patch.object(ledger.time, "sleep"):
                report = ledger.resource_snapshot(proc)
            self.assertEqual(report["cgroup"]["state"], "unknown")
            self.assertIsNone(report["visible_memory_headroom_bytes"])
            self.assertIsNone(report["visible_cpu_capacity_ceiling"])
            self.assertTrue(any("cgroup limits" in issue for issue in report["issues"]))

    def test_controller_disabled_below_parent_retains_parent_cpu_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            proc, leaf = self.fixture(Path(directory))
            (leaf / "cpu.max").unlink()
            (leaf / "cgroup.controllers").write_text("memory")
            with patch.object(ledger.time, "sleep"), patch.object(ledger.os, "sched_getaffinity", return_value={0}):
                report = ledger.resource_snapshot(proc)
            self.assertEqual(report["cgroup"]["state"], "observed")
            self.assertEqual(report["visible_cpu_capacity_ceiling"], 0.5)
            self.assertEqual(report["visible_memory_headroom_bytes"], 100000)

    def test_missing_probes_do_not_report_free_capacity(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ledger.time, "sleep"), \
                patch.object(ledger.os, "sched_getaffinity", side_effect=OSError("unavailable")), \
                patch.object(ledger.os, "getloadavg", side_effect=OSError("unavailable")):
            report = ledger.resource_snapshot(Path(directory))
            for field in ("allowed_cpus", "host_memory_available_bytes", "load_average_1_5_15",
                          "visible_cpu_capacity_ceiling", "visible_memory_headroom_bytes"):
                self.assertIsNone(report[field])
            self.assertFalse(report["launch_authorized"])
            self.assertTrue(report["issues"])

    def test_cgroup_unlimited_memory_still_respects_host_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            proc, leaf = self.fixture(Path(directory))
            for path in (leaf, leaf.parent):
                (path / "memory.max").write_text("max")
                (path / "cpu.max").write_text("max 100000")
            with patch.object(ledger.time, "sleep"), patch.object(ledger.os, "sched_getaffinity", return_value={0}):
                report = ledger.resource_snapshot(proc)
            self.assertEqual(report["visible_memory_headroom_bytes"], 819200)
            self.assertEqual(report["visible_cpu_capacity_ceiling"], 1)

    def test_entry_exposes_timeline_and_resources_without_mutating_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "operations/adaptive/running/job.json"
            path.parent.mkdir(parents=True)
            value = {"job_id": "job", "candidate_id": "example", "state": "running",
                     "started_at": "2026-09-06T11:00:00Z", "resource_budget": {"wall_seconds": 120}}
            path.write_text(json.dumps(value))
            original = path.read_bytes()
            with patch.object(ledger, "live_job", return_value={"state": "unknown"}), \
                    patch.object(ledger, "resource_snapshot", return_value={"launch_authorized": False}):
                data = ledger.build(root)
                report = ledger.start_payload(data, root)
            self.assertEqual(report["running_jobs"][0]["timeline"]["started_at"], value["started_at"])
            self.assertEqual(report["running_jobs"][0]["timeline"]["phase_estimate"]["state"], "unknown")
            self.assertFalse(report["queue"]["launch_authorized"])
            self.assertFalse(report["resources"]["launch_authorized"])
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
