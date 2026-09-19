#!/usr/bin/env python3
"""Build the browsing ledger from existing records; never launch or change a run."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import time


try:
    from . import _enwiki9_bootstrap
except ImportError:
    import _enwiki9_bootstrap
from gamma_enwiki9.reporting.projection import (
    text, Records, metrics, ledger_record, reflection_learning, project_browsing_state,
    review_backlog, record_options, record_query,
)
from gamma_enwiki9.reporting.host import (
    utc, cpu_ticks, cpu_usage, visible_cgroup_limits, timestamp, job_timeline,
)

ROOT = Path(__file__).resolve().parents[1]


def resource_snapshot(proc=Path("/proc")):
    from gamma_enwiki9.reporting.host import resource_snapshot as observe_resources
    return observe_resources(proc, scratch=ROOT / "results")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from lib.artifacts import atomic_write
try:
    from . import research_contracts
except ImportError:
    import research_contracts
STATES = ("pending", "running", "completed", "failed", "cancelled")
MAX_JSON = 8 * 1024 * 1024
HISTORICAL_STATUSES = {"failed", "failure", "cancelled", "superseded", "merged",
                       "parked", "archive_miss", "measured_negative"}
ACTIVE_JOB_STATES = {"running", "pending", "queued", "held"}




















def live_job(job, root=ROOT):
    try:
        from . import enwiki9_worker_identity as identity
        from . import enwiki9_lab as lab
    except ImportError:
        import enwiki9_worker_identity as identity
        import enwiki9_lab as lab
    if root.resolve() == lab.ROOT.resolve():
        state = lab.running_job_liveness(job)
    elif isinstance(job.get("execution_resources"), dict):
        matched = lab.worker_pid_matches_job(job)
        state = "live" if matched else "unknown"
    else:
        matched = identity.worker_pid_matches_job(root, root / "tools/candidate_triage.py", job)
        state = "live" if matched else "unknown"
    details = {"live": "Canonical worker identity matches on this host",
               "terminal": "Canonical terminal counterpart and exact recorded reflection validate; original running record preserved",
               "unknown": "Recorded running; exact worker identity and terminal reflection were not verified on this host"}
    return {"state": state, "pid": job.get("worker_pid"),
            "observed_at": utc(), "detail": details[state]}










def build(root, *, observe=True):
    from gamma_enwiki9.reporting import projection
    try:
        from .enwiki9_tool_catalogue import build_catalogue
    except ImportError:
        from enwiki9_tool_catalogue import build_catalogue
    records = Records(root)
    jobs = [(p, records.read(p)) for p in records.files("operations/adaptive/*/*.json")
            if p.parent.name in STATES]
    liveness = {d.get("job_id"): live_job(d, root) for _, d in jobs if d.get("state") == "running"} if observe else {}
    data = projection.build(root, catalogue_builder=build_catalogue,
        objective_path=research_contracts.objective_binding()["objectivePath"], liveness=liveness)
    if not observe:
        return data
    data.update(generated_at=utc(), host=socket.gethostname())
    runs = data["runs"]
    job_runs = {run["id"]: run for run in runs if run["kind"] == "job"}
    # Reuse the existing authoritative observer binding; no independent monitor.
    if root.resolve() == ROOT.resolve():
        try:
            try:
                from . import enwiki9_status_receipt as status_reader
            except ImportError:
                import enwiki9_status_receipt as status_reader
            status_jobs = [{**job, "path": records.relative(str(path)),
                            "worker_pid_live": job_runs.get(job.get("job_id"), {}).get("liveness", {}).get("state") == "live"}
                           for path, job in jobs if job.get("state") == "running"]
            observer = status_reader.existing_horizon_observer_state({"running_jobs": status_jobs})
            if observer:
                source = job_runs.get(observer.get("adaptive_job_id"))
                for run in runs:
                    if run.get("id") in {observer.get("observer_job_id"), observer.get("adaptive_job_id")}:
                        run["progress"] = observer["observer_progress"]
                        run["progress_observation"] = {key: observer.get(key) for key in (
                            "source", "adaptive_job_id", "adaptive_job_path", "observer_job_id", "observer_candidate",
                            "observer_progress_path", "observer_progress_fresh", "observer_sample_identities_match",
                            "source_processes_live", "observer_worker_live", "observer_progress")}
                        run["links"].append({"label": "Existing observer", "path": records.relative(observer["observer_progress_path"])})
                if source and observer.get("source_processes_live"):
                    source["liveness"] = {"state": "live", "observed_at": utc(), "pid": None,
                        "detail": "Existing observer plan binds live boot/PID/start/argv identities on this host"}
        except (OSError, ValueError, KeyError) as exc:
            records.issues.append({"path": "docs/status_receipt.json", "reason": f"observer binding unavailable: {exc}"})

    prior_observation = records.read("docs/status_receipt.json").get("gate_decision") or {}
    for run in runs:
        if run["state"] == "running":
            run["timeline"] = job_timeline(run, prior_observation)

    data["issues"].extend(records.issues)
    data["counts"]["running"] = sum(r["state"] == "running" and r["liveness"].get("state") == "live" for r in runs)
    data["counts"]["unverified_running"] = sum(r["state"] == "running" and r["liveness"].get("state") == "unknown" for r in runs)
    return data









def start_payload(data, root):
    """Orient an agent using canonical liveness without authorizing work."""
    records = Records(root)
    objective = records.read(data["objective"]["path"])
    corpus_ref = text(objective.get("corpus", {}).get("repositoryPath")).removeprefix("projects/enwiki9/")
    if not corpus_ref or Path(corpus_ref).is_absolute() or ".." in Path(corpus_ref).parts:
        corpus_ref = "data/enwik9"
    corpus = root / corpus_ref if corpus_ref else root / "data/enwik9"
    try:
        corpus_size = corpus.stat().st_size if corpus.is_file() else None
    except OSError:
        corpus_size = None
    running = [r for r in data["runs"] if r["kind"] == "job" and r["state"] == "running"]
    reviews = review_backlog(data)
    bound_reviews = [r for r in reviews if r.get("revision")]
    proposed = [p for p in data["proposals"] if p["state"] == p["directory_state"] == "proposed"
                and p["operational_status"] == "actionable"]
    lease_path = "operations/runtime/exclusive_full1g.json"
    lease_present = (root / lease_path).exists()
    issues = list(data["issues"])
    expected = objective.get("corpus", {}).get("bytes")
    if corpus_size != expected or expected is None:
        issues.append({"path": corpus_ref or "data/enwik9", "reason": "canonical corpus is missing or its byte count differs; verify inputs before benchmarking"})
    dependencies = {name: importlib.util.find_spec(name) is not None for name in ("jsonschema",)}
    if not all(dependencies.values()):
        issues.append({"path": "../../requirements.txt", "reason": "lab dependencies missing from this interpreter; use the provisioned project environment"})
    status = records.read("docs/status_receipt.json")
    operator = status.get("operator_summary") or {}
    old_active = (status.get("gate_liveness") or {}).get("is_live")
    if any(r["liveness"].get("state", "unknown") != "terminal" for r in running) and (
            old_active is False or operator.get("safe_to_launch_candidate_gate") is True):
        issues.append({"path": "docs/status_receipt.json", "reason": "operator receipt reports idle or safe launch while live or unverified jobs exist; inspect its timestamp and the existing observer before scheduling"})
    keys = ("id", "candidate_id", "state", "purpose", "scope", "source", "liveness", "progress",
            "execution_mode", "resource_budget", "timing_authority", "timeline")
    return {"schema": "enwiki9_agent_start_v1", "generated_at": data["generated_at"], "host": data["host"],
        "project_root": str(root.resolve()), "objective": data["objective"],
        "go": "Inspect evidence and ownership, choose one justified experiment or research question, use the adaptive workflow, record its outcome, and continue from the evidence.",
        "entry_points": {"instructions": "AGENTS.md", "workbench": "workbench/README.md",
            "prompts": "workbench/PROMPTS.md", "workflow": "ADAPTIVE_WORKFLOW.md", "record_map": "ledger/README.md",
            "tool_catalogue": "docs/tooling_inventory.md"},
        "environment": {"python": sys.executable, "python_version": sys.version.split()[0], "modules": dependencies,
            "tools": {name: shutil.which(name) for name in ("git", "make", "g++", "bzip2")},
            "corpus": {"path": corpus_ref, "bytes": corpus_size, "expected_bytes": expected, "hash_verified": False},
            "note": "Availability only; each candidate declares its own dependencies and validates corpus hashes."},
        "resources": resource_snapshot(),
        "records": data["counts"], "running_jobs": [{key: run.get(key) for key in keys} for run in running],
        "queue": {"held": sum(r["state"] == "held" for r in data["runs"]),
            "pending_unheld": sum(r["state"] == "pending" for r in data["runs"]),
            "exclusive_lease_file": lease_path if lease_present else None,
            "launch_authorized": False,
            "meaning": "This entry report grants no launch permission. Existing lease, guard, dependency, and proposal checks govern execution; preserve current observers."},
        "review_backlog": {"latest_bound_jobs_without_reflection": len(bound_reviews),
            "bound_by_state": dict(Counter(r["state"] for r in bound_reviews)),
            "latest_legacy_jobs_without_reflection": len(reviews) - len(bound_reviews),
            "meaning": "File-presence inventory, not validated scientific verdicts. Review relevant parent evidence; the entire historical backlog is not a prerequisite for independent research.",
            "inspect": "python3 tools/enwiki9_lab.py records --view reviews --limit 10"},
        "proposed_work": {"count": len(proposed), "examples": proposed[:5],
            "meaning": "Recorded as proposed and actionable, not ranked or launch-qualified. Inspect parent evidence, exclusions, and dependencies before claiming."},
        "next_commands": {"search": "python3 tools/enwiki9_lab.py records --search YOUR_MECHANISM",
            "resources_and_timelines": "python3 tools/enwiki9_lab.py start",
            "tools": "python3 tools/enwiki9_lab.py records --view tools --search YOUR_TASK",
            "running": "python3 tools/enwiki9_lab.py records --view runs --state running",
            "history": "python3 tools/enwiki9_lab.py records --candidate CANDIDATE_ID",
            "research": "python3 tools/enwiki9_lab.py records --view notes --search YOUR_MECHANISM",
            "benchmark": "python3 tools/enwiki9_lab.py enqueue --help",
            "simulation": "python3 tools/enwiki9_lab.py enqueue-tool --help",
            "record_result": "python3 tools/enwiki9_lab.py reflect --help"},
        "competition": {"meaning": "The objective is a research target; check live rules and competing submissions before prize-facing promotion.",
            "rules": "https://www.hutter1.net/prize/hrules.htm", "submissions": "https://mattmahoney.net/dc/text.html"},
        "issues": issues + records.issues}


def write_atomic(path, content):
    atomic_write(path, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="print coverage without writing the browsing files")
    parser.add_argument("--start", action="store_true", help="print agent entry report without writing files")
    record_options(parser)
    args = parser.parse_args()
    data = build(ROOT)
    try:
        if args.start:
            print(json.dumps(start_payload(data, ROOT), ensure_ascii=False, allow_nan=False, indent=2))
            return 0
        if args.search is not None or args.view or args.candidate or args.state or args.include_legacy or args.history:
            print(json.dumps(record_query(data, args), ensure_ascii=False, allow_nan=False, indent=2))
            return 0
    except ValueError as exc:
        parser.error(str(exc))
    if not args.summary:
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        template = (ROOT / "tools/enwiki9_ledger.html").read_text()
        if template.count("__LEDGER_DATA__") != 1:
            raise SystemExit("HTML template must contain exactly one data placeholder")
        write_atomic(ROOT / "ledger/index.html", template.replace("__LEDGER_DATA__", payload.replace("<", "\\u003c")))
        write_atomic(ROOT / "ledger/ledger.json", json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2) + "\n")
    print(json.dumps({"generated_at": data["generated_at"], **data["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
