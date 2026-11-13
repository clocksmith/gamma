"""Read-only guard for the owner's explicit retirement of one known provider.

Does not stop/start/signal the provider. Systemd observations and memory remain
live. Only the retired state replaces owner admission telemetry with proof that
the service has no main process. Original service_guard.py is unchanged.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import time

FLOOR = 32 * 1024 ** 3
FIELDS = ("ActiveState", "SubState", "MainPID", "NRestarts")


class RetirementGuard:
    def __init__(self, unit, known_pid, authorization, minimum_memory=FLOOR):
        if known_pid <= 0 or not authorization.strip() or minimum_memory < FLOOR:
            raise ValueError("known PID, explicit owner authorization and >=32GiB floor required")
        self.unit, self.known_pid = unit, known_pid
        self.authorization, self.minimum_memory = authorization, minimum_memory
        self.inactive_seen = False
        self.last_idle = None

    def assess(self, service, measurement, memory, now, observation_age=0):
        state, substate = service.get("ActiveState"), service.get("SubState")
        pid, restarts = int(service.get("MainPID", -1)), int(service.get("NRestarts", -1))
        reasons = []
        if not 0 <= observation_age <= 5:
            reasons.append("systemd_observation_stale")
        if memory < self.minimum_memory:
            reasons.append("memory_headroom_below_floor")
        if restarts != 0:
            reasons.append("provider_restart_counter_changed")
        count, source_at, age, basis = None, None, None, None
        if measurement:
            count, source_at = measurement.get("stageAdmitted"), measurement.get("at")
            if source_at:
                age = (now - dt.datetime.fromisoformat(source_at.replace("Z", "+00:00"))).total_seconds()
        if self.inactive_seen and (state != "inactive" or pid != 0):
            reasons.append("provider_restarted_after_retirement")
        if state == "active":
            basis = "fresh_owner_measurement_while_known_provider_active"
            if pid != self.known_pid:
                reasons.append("provider_pid_changed")
            if age is None or not 0 <= age <= 15:
                reasons.append("provider_observation_stale_or_missing")
            if type(count) is not int or count != 0:
                reasons.append("provider_admitted_work_since_idle_baseline")
            if not reasons:
                self.last_idle = {"stageAdmitted": 0, "at": source_at}
        elif state == "deactivating":
            basis = "authorized_drain_known_pid_with_last_observed_idle_count"
            if pid != self.known_pid:
                reasons.append("draining_provider_pid_changed")
            if not self.last_idle:
                reasons.append("no_valid_idle_observation_before_drain")
            # New owner telemetry, if present, must never override evidence of work.
            if count is not None and (type(count) is not int or count != 0):
                reasons.append("provider_admitted_work_during_drain")
            if self.last_idle:
                count, source_at = 0, self.last_idle["at"]
                age = (now - dt.datetime.fromisoformat(source_at.replace("Z", "+00:00"))).total_seconds()
        elif state == "inactive" and pid == 0 and substate == "dead":
            self.inactive_seen = True
            basis = "fresh_systemd_inactive_dead_MainPID0_no_provider_process_can_admit"
            count, source_at, age = 0, None, None
        else:
            reasons.append("unexpected_provider_state")
        return {"schema": "gamma.channel-gain-service-guard-retirement/v1",
                "checkedAt": now.isoformat(), "allowed": not reasons, "reasons": reasons,
                "unit": self.unit, "stageAdmitted": count, "baselineStageAdmitted": 0,
                "stageAdmittedBasis": basis, "sourceObservedAt": source_at, "sourceAgeSeconds": age,
                "sourceFreshnessRequired": state == "active", "systemdObservationAgeSeconds": observation_age,
                "providerState": state, "providerSubState": substate, "providerMainPID": pid,
                "knownProviderMainPID": self.known_pid, "providerNRestarts": restarts,
                "retirementObserved": self.inactive_seen, "lastKnownIdleMeasurement": self.last_idle,
                "availableMemoryBytes": memory, "minimumAvailableMemoryBytes": self.minimum_memory,
                "providerModified": True, "providerModificationBasis": "owner-authorized retirement; guard itself is read-only",
                "ownerRetirementAuthorization": self.authorization, "pollIntervalSeconds": 5}

    def observe(self):
        result = subprocess.run(["systemctl", "--user", "show", self.unit,
                                 *["--property=" + field for field in FIELDS]],
                                capture_output=True, text=True, timeout=5, check=True)
        sampled = time.monotonic()
        service = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        measurement = None
        if service.get("ActiveState") in ("active", "deactivating"):
            journal = subprocess.run(["journalctl", "--user", "-u", self.unit, "-n", "10", "--no-pager", "-o", "cat"],
                                     capture_output=True, text=True, timeout=5, check=True)
            for line in reversed(journal.stdout.splitlines()):
                try:
                    row = json.loads(line)
                    values = row.get("owner", {}).get("measurements", {})
                    if values:
                        measurement = {"at": row.get("at"), "stageAdmitted": values.get("stageAdmitted")}
                        break
                except (ValueError, TypeError, AttributeError):
                    continue
        mem = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        available = int(mem["MemAvailable"].split()[0]) * 1024
        return self.assess(service, measurement, available, dt.datetime.now(dt.timezone.utc), time.monotonic() - sampled)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--known-provider-pid", type=int, required=True)
    parser.add_argument("--owner-retirement-authorization", required=True)
    parser.add_argument("--minimum-memory-bytes", type=int, default=FLOOR)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=float, required=True)
    parser.add_argument("--once", action="store_true", help="Write one real observation for handover validation; no stopped row")
    args = parser.parse_args()
    guard = RetirementGuard(args.unit, args.known_provider_pid, args.owner_retirement_authorization, args.minimum_memory_bytes)
    # Persist retirement latch if this exact new guard's output is reused.
    if args.output.exists():
        prior = json.loads(args.output.read_text())
        if prior.get("schema") == "gamma.channel-gain-service-guard-retirement/v1":
            if prior.get("unit") != args.unit or prior.get("knownProviderMainPID") != args.known_provider_pid:
                raise ValueError("existing guard identity differs")
            guard.inactive_seen = bool(prior.get("retirementObserved"))
    stop = False
    def terminate(*_):
        nonlocal stop
        stop = True
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    def save(row):
        temporary = args.output.with_name(args.output.name + f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(row) + "\n")
        os.replace(temporary, args.output)
        with args.output.with_suffix(".jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
    deadline = time.monotonic() + args.duration_seconds
    last = None
    try:
        while not stop and time.monotonic() < deadline:
            started = time.monotonic()
            try:
                last = guard.observe()
            except Exception as error:
                last = {"schema": "gamma.channel-gain-service-guard-retirement/v1", "checkedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "allowed": False, "reasons": ["monitor_error"], "errorType": type(error).__name__,
                        "unit": args.unit, "knownProviderMainPID": args.known_provider_pid,
                        "retirementObserved": guard.inactive_seen, "providerModified": True,
                        "ownerRetirementAuthorization": args.owner_retirement_authorization}
            save(last)
            if args.once or not last["allowed"]:
                print(json.dumps(last), flush=True)
            if args.once:
                return
            time.sleep(max(0, 5 - (time.monotonic() - started)))
    finally:
        if not args.once:
            save({**(last or {}), "checkedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "allowed": False, "reasons": ["monitor_stopped"], "providerModified": True,
                  "ownerRetirementAuthorization": args.owner_retirement_authorization})


if __name__ == "__main__":
    main()
