import datetime as dt
import unittest
from service_guard_retired import FLOOR, RetirementGuard


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.guard = RetirementGuard("provider.service", 42, "owner explicitly retires provider")
        self.now = dt.datetime(2026, 11, 13, 16, tzinfo=dt.timezone.utc)

    def row(self, state="active", pid=42, count=0, age=1, memory=FLOOR, **kw):
        service = {"ActiveState": state, "SubState": "dead" if state == "inactive" else "running", "MainPID": pid, "NRestarts": kw.pop("restarts", 0)}
        measurement = {"at": (self.now - dt.timedelta(seconds=age)).isoformat(), "stageAdmitted": count}
        return self.guard.assess(service, measurement, memory, self.now, **kw)

    def test_authorized_active_drain_retired_and_restart(self):
        self.assertTrue(self.row()["allowed"])
        drain = self.row("deactivating", age=100)
        self.assertTrue(drain["allowed"])
        self.assertFalse(drain["sourceFreshnessRequired"])
        retired = self.row("inactive", pid=0, age=100)
        self.assertTrue(retired["allowed"])
        self.assertIsNone(retired["sourceObservedAt"])
        self.assertIn("no_provider_process", retired["stageAdmittedBasis"])
        self.assertTrue(retired["providerModified"])
        self.assertFalse(self.row()["allowed"])

    def test_active_freshness_idle_identity_and_memory(self):
        for options in ({"age": 16}, {"age": -1}, {"count": 1}, {"pid": 43},
                        {"memory": FLOOR - 1}, {"restarts": 1}, {"observation_age": 6}):
            with self.subTest(options=options):
                self.assertFalse(self.row(**options)["allowed"])

    def test_drain_requires_observed_idle_and_known_pid(self):
        self.assertFalse(self.row("deactivating")["allowed"])
        self.assertTrue(self.row()["allowed"])
        self.assertFalse(self.row("deactivating", pid=0)["allowed"])
        self.assertFalse(self.row("deactivating", count=1)["allowed"])

    def test_inactive_floor_and_reactivation_fail(self):
        self.assertFalse(self.row("inactive", pid=0, memory=FLOOR - 1)["allowed"])
        self.assertTrue(self.row("inactive", pid=0)["allowed"])
        self.assertFalse(self.row("activating", pid=42)["allowed"])
        self.assertFalse(self.row("deactivating", pid=42)["allowed"])


if __name__ == "__main__":
    unittest.main()
