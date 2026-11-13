"""Validate external environment history without reading workload/oracle inputs."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "gamma.reconfiguration-environment-event/v1"


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Environment timestamps require a timezone")
    return parsed


def sha(value):
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise ValueError("Environment provenance needs exact SHA256 values")
    return value


def load_environment(path, evidence):
    raw = Path(path).read_bytes()
    events, phases, ids = [], [], set()
    previous, latest = None, None
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.endswith(b"\n") or not line.strip():
            raise ValueError("Environment ledger needs complete nonempty JSONL lines")
        row = json.loads(line)
        if row.get("schema") != SCHEMA or row.get("status") != "observed":
            raise ValueError("Only observed environment events, never templates, may enter reports")
        if row.get("previousLineSha256") != previous:
            raise ValueError("Environment append-only hash chain mismatch")
        if not row.get("eventId") or row["eventId"] in ids:
            raise ValueError("Environment event IDs must be unique")
        ids.add(row["eventId"])
        at = timestamp(row["observedAt"])
        if latest is not None and at < latest:
            raise ValueError("Environment observations must be appended in time order")
        latest = at
        for key in ("runtimeLock", "stageLock"):
            supplied = sha(row["targetInputFileSha256"][key])
            if supplied != evidence["provenance"]["files"][key]["sha256"]:
                raise ValueError("Environment history belongs to a different runtime/stage")
        if not row.get("host") or not row.get("device") or not row.get("description"):
            raise ValueError("Environment event needs host, device and factual description")
        if row.get("kind") not in ("provider_retired", "workload_started", "workload_ended", "overlap", "phase_summary", "correction"):
            raise ValueError("Unknown environment event kind")
        references = row.get("sources")
        if not references:
            raise ValueError("Environment event needs a source receipt or journal hash")
        for source in references:
            if not source.get("path"):
                raise ValueError("Environment source path missing")
            sha(source["sha256"])
        isolation = row.get("isolationQualification", "unknown")
        if isolation not in ("unknown", "contended"):
            raise ValueError("This descriptive ledger cannot qualify isolated performance")
        if row.get("kind") in ("overlap", "phase_summary"):
            interval = row["interval"]
            start = timestamp(interval["startedAt"])
            end = timestamp(interval["endedAt"]) if interval.get("endedAt") else None
            if end is not None and end < start:
                raise ValueError("Negative environment phase duration")
            if start > at or end is not None and end > at:
                raise ValueError("Observed environment events cannot assert future intervals")
            if row["kind"] == "overlap" and isolation != "contended":
                raise ValueError("An observed overlap must be marked contended")
            if row["kind"] == "phase_summary":
                values = row["timingSummary"]
                if type(values["requestCount"]) is not int or values["requestCount"] < 0:
                    raise ValueError("Invalid phase request count")
                sha(values["requestIdsSha256"])
                for key in ("physicalRequestMs", "attributedEndToEndMs"):
                    if type(values[key]) not in (int, float) or not 0 <= values[key] < float("inf"):
                        raise ValueError("Invalid phase timing")
                phases.append(row)
        events.append(row)
        previous = hashlib.sha256(line).hexdigest()
    if not events:
        raise ValueError("Empty environment history")
    return {"provided": True, "path": str(Path(path)), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "eventCount": len(events), "lastLineSha256": previous,
            "isolationQualification": "contended" if any(e.get("isolationQualification") == "contended" for e in events) else "unknown",
            "events": events, "timingPhases": phases,
            "interpretation": "External observed environment history is byte-hashed and bound to runtime/stage identities. Referenced receipts are named and hashed by the recorder, not re-read here. Phase summaries are descriptive recorder-provided aggregates, not recomputed metrics or a randomized comparison. Frozen metrics and quality denominators are unchanged."}


def environment_markdown(environment):
    lines = ["## Environment and timing qualification", "",
             f"Isolation qualification: **{environment['isolationQualification']}**. Frozen latency/cost metrics above remain unchanged; they do not by themselves qualify isolated performance."]
    if not environment["provided"]:
        return lines + ["No external environment receipt was supplied. Isolation is unknown, not assumed.", ""]
    lines += [environment["interpretation"], "",
              "| Observed at | Kind | Environment change / observation | Timing qualification |",
              "| --- | --- | --- | --- |"]
    for event in environment["events"]:
        description = event["description"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {event['observedAt']} | {event['kind']} | {description} | {event.get('isolationQualification', 'unknown')} |")
    if environment["timingPhases"]:
        lines += ["", "Descriptive phase aggregates; spanning requests must remain in their own transition/overlap phase. Do not add attributed totals to physical intervals or compare phases causally.", "",
                  "| Phase | Interval | Requests | Physical request ms | Attributed E2E ms | Qualification |",
                  "| --- | --- | ---: | ---: | ---: | --- |"]
        for phase in environment["timingPhases"]:
            timing, interval = phase["timingSummary"], phase["interval"]
            lines.append(f"| {phase['eventId']} | {interval['startedAt']} to {interval.get('endedAt') or 'ongoing'} | {timing['requestCount']} | {timing['physicalRequestMs']:.3f} | {timing['attributedEndToEndMs']:.3f} | {phase.get('isolationQualification', 'unknown')} |")
    else:
        lines += ["", "No per-phase request aggregates supplied; the timeline alone cannot apportion observed request costs."]
    return lines + ["", f"Environment ledger: `{environment['path']}`; SHA256 `{environment['sha256']}`; {environment['eventCount']} observed events.", ""]
