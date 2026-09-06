#!/usr/bin/env python3
"""Build the browsing ledger from existing records; never launch or change a run."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import socket
import sys


ROOT = Path(__file__).resolve().parents[1]
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


def text(value):
    return value if isinstance(value, str) else ""


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Records:
    def __init__(self, root):
        self.root = root.resolve()
        self.issues = []
        self.cache = {}

    def relative(self, value):
        value = text(value)
        if value.startswith("projects/enwiki9/"):
            value = value[len("projects/enwiki9/"):]
        p = Path(value)
        if not value:
            return ""
        if not p.is_absolute():
            p = self.root / p
        try:
            return p.resolve().relative_to(self.root).as_posix()
        except (ValueError, OSError):
            return ""

    def read(self, value):
        rel = self.relative(str(value))
        if not rel:
            return {}
        if rel in self.cache:
            return self.cache[rel]
        p = self.root / rel
        if not p.is_file():
            return {}
        try:
            if p.stat().st_size > MAX_JSON:
                raise ValueError("JSON exceeds the browsing limit; open the source record")
            data = json.loads(p.read_text())
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
        except (OSError, ValueError) as exc:
            self.issues.append({"path": rel, "reason": str(exc)})
            data = {}
        self.cache[rel] = data
        return data

    def lines(self, rel):
        p = self.root / rel
        if not p.is_file():
            return
        with p.open() as handle:
            for number, line in enumerate(handle, 1):
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        yield value
                except ValueError:
                    self.issues.append({"path": rel, "reason": f"invalid JSON at line {number}"})

    def files(self, pattern):
        return sorted(self.root.glob(pattern))


def live_job(job, root=ROOT):
    try:
        from . import enwiki9_worker_identity as identity
    except ImportError:
        import enwiki9_worker_identity as identity
    if isinstance(job.get("execution_resources"), dict):
        try:
            from . import enwiki9_lab as lab
        except ImportError:
            import enwiki9_lab as lab
        matched = lab.worker_pid_matches_job(job)
    else:
        matched = identity.worker_pid_matches_job(root, root / "tools/candidate_triage.py", job)
    return {"state": "live" if matched else "unknown", "pid": job.get("worker_pid"),
            "observed_at": utc(), "detail": "Canonical worker identity matches on this host"
            if matched else "Recorded running; exact worker identity was not verified on this host"}


def metrics(data, definitions=None):
    definitions = definitions or {}
    found = []
    # Preserve units and absent values; a diagnostic is never turned into a score.
    for key in ("compressed_size", "program_size", "hutter_score", "archive_bytes",
                "payload_bytes", "net_bytes_saved", "scope_bytes"):
        if data.get(key) is not None and isinstance(data[key], (int, float)):
            if math.isfinite(data[key]):
                found.append({"label": key, "value": data[key], "unit": "bytes"})
    for group in ("measurements", "flat_measurements"):
        values = data.get(group)
        if not isinstance(values, dict):
            continue
        for key, value in values.items():
            if value is None or not isinstance(value, (int, float, bool)) or not math.isfinite(value):
                continue
            unit = definitions.get(key, "")
            if not unit:
                unit = "boolean" if isinstance(value, bool) else (
                    "bytes" if key.endswith("Bytes") or key == "netBytesSaved" else
                    "bits" if key.endswith("Bits") or key == "idealBitsSaved" else "reported value")
            found.append({"label": key, "value": value, "unit": unit})
    return found


def ledger_record(row, source):
    return {"source": source, "run_id": row.get("run_id"),
            "purpose": row.get("run_purpose"), "context": row.get("run_context"),
            "scope_bytes": row.get("data_size"), "roundtrip_ok": row.get("roundtrip_ok"),
            "deterministic_ok": row.get("determinism_ok"),
            **{key: row.get(key) for key in ("compressed_size", "program_size", "hutter_score")}}


def reflection_learning(reflection, issues=None, source=""):
    """Project recorded claims for search; their presence does not validate them."""
    def mapping(field):
        value = reflection.get(field)
        if isinstance(value, dict):
            return value
        if value is not None and issues is not None:
            issues.append({"path": source,
                           "reason": f"optional reflection field {field} must be an object; learning projection is missing"})
        return {}

    knowledge = mapping("knowledge")
    attribution = mapping("attribution")
    decision = mapping("decision")

    def strings(value):
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    return {"lessons": strings(knowledge.get("transferableLessons")),
            "localized_cause": text(attribution.get("localizedCause")),
            "failure_class": text(attribution.get("failureClass")),
            "retired_dimensions": strings(knowledge.get("retiredDimensions")),
            "uncertainties": strings(knowledge.get("uncertainties")),
            "next_action": {"verdict": decision.get("verdict"),
                            "rationale": text(decision.get("rationale")),
                            "next_gate_bytes": decision.get("nextGateBytes")}}


def project_browsing_state(algorithms, runs):
    """Hide recorded retired configurations, never infer scientific eligibility."""
    active = {r["candidate_id"] for r in runs if r["kind"] == "job"
              and r["state"] in ACTIVE_JOB_STATES}
    for algorithm in algorithms:
        status = algorithm["status"].lower().replace("-", "_")
        historical = (status in HISTORICAL_STATUSES
                      or status.startswith(("retired", "rejected", "merged_"))
                      or status.endswith("_superseded"))
        algorithm["browsing_state"] = "historical" if historical and algorithm["id"] not in active else "current"
        algorithm["has_active_job_record"] = algorithm["id"] in active
    by_id = {a["id"]: a for a in algorithms}
    for run in runs:
        run["browsing_state"] = by_id.get(run["candidate_id"], {}).get("browsing_state", "current")


def build(root):
    records = Records(root)
    inventory = records.read("candidate_inventory.json")
    indexed = {x["id"] for x in records.read("index.json").get("programs", []) if isinstance(x, dict) and "id" in x}
    algorithms, proposals, runs = {}, [], []

    def candidate(cid, kind="candidate"):
        if not isinstance(cid, str) or not cid or "/" in cid or cid in {".", ".."}:
            return None
        if cid not in algorithms:
            algorithms[cid] = {"id": cid, "name": cid, "description": "", "family": "unclassified",
                "status": "unrecorded", "kind": kind, "registered": cid in indexed,
                "parents": [], "children": [], "sources": [], "run_ids": [],
                "proposal_ids": [], "notes": [], "reflections": [], "updated_at": "", "coverage": []}
        return algorithms[cid]

    def parent(cid, pid, source, kind="recorded-parent"):
        a = candidate(cid)
        if a and isinstance(pid, str) and pid and pid != cid and "/" not in pid:
            edge = {"id": pid, "source": source, "kind": kind}
            if not any(x["id"] == pid for x in a["parents"]):
                a["parents"].append(edge)

    for row in inventory.get("candidates", []):
        a = candidate(row.get("id"))
        if a:
            a["status"] = row.get("meta_status") or row.get("status") or "unrecorded"
    for p in records.files("programs/*/meta.json"):
        m = records.read(p)
        a = candidate(p.parent.name)
        a.update(name=m.get("name") or a["id"],
                 description=m.get("hypothesis") or m.get("description") or "",
                 family=m.get("family") or "unclassified", status=m.get("status") or a["status"],
                 updated_at=text(m.get("added")))
        a["sources"].extend([records.relative(str(p)), "programs/" + a["id"] + "/"])
        a["summary"] = text(m.get("verdict")) or text(m.get("outcome"))
        for field in ("parent", "parent_candidate_id", "parent_program_id", "parentCandidateId"):
            parent(a["id"], m.get(field), records.relative(str(p)))
        predecessor = m.get("source_predecessor")
        if isinstance(predecessor, dict):
            parent(a["id"], predecessor.get("candidateId"), records.relative(str(p)), "source-predecessor")
    # Include source directories with missing metadata, as well as curated IDs.
    for p in records.files("programs/*"):
        if p.is_dir():
            candidate(p.name)
    for cid in indexed:
        candidate(cid)
    for row in records.lines("operations/adaptive/mutations.jsonl"):
        parent(row.get("candidate_id"), row.get("parent"), "operations/adaptive/mutations.jsonl")
    for p in records.files("operations/adaptive/candidate-revisions/*/*.json"):
        d = records.read(p)
        parent(d.get("candidateId"), (d.get("parentRevision") or {}).get("candidateId"), records.relative(str(p)))
    for p in records.files("operations/adaptive/proposals/*/*.json"):
        d = records.read(p)
        pid = d.get("proposal_id")
        if not pid:
            continue
        cid = d.get("candidate_id") or "proposal:" + pid
        a = candidate(cid, "proposal")
        if not a:
            continue
        proposal = {"id": pid, "candidate_id": d.get("candidate_id"), "title": d.get("title") or pid,
            "hypothesis": d.get("hypothesis") or "", "state": d.get("state") or p.parent.name,
            "directory_state": p.parent.name, "operational_status": d.get("operational_status", "actionable"),
            "owner": d.get("owner"), "activation_requirements": d.get("activation_requirements"),
            "parent": d.get("parent"), "parent_proposal_id": d.get("parent_proposal_id"),
            "path": records.relative(str(p))}
        if p.parent.name in {"proposed", "claimed", "developed", "rejected"} and proposal["state"] != proposal["directory_state"]:
            records.issues.append({"path": proposal["path"], "reason": "proposal state disagrees with directory; not a ready proposal"})
        proposals.append(proposal)
        a["proposal_ids"].append(pid)
        a["sources"].append(proposal["path"])
        if a["kind"] == "proposal":
            a.update(name=proposal["title"], description=proposal["hypothesis"], status=proposal["state"])
        if isinstance(d.get("parent"), str) and d["parent"] in algorithms:
            parent(cid, d["parent"], proposal["path"])

    reflections = {}
    for p in records.files("operations/adaptive/reflections/*.json"):
        d = records.read(p)
        jp = records.relative((d.get("job") or {}).get("path", ""))
        if jp:
            reflections[jp] = (records.relative(str(p)), d)
    jobs = []
    for state in STATES:
        for p in records.files(f"operations/adaptive/{state}/*.json"):
            d = records.read(p)
            if d.get("candidate_id") and d.get("job_id"):
                jobs.append((p, d))
    active = {d["candidate_id"] for _, d in jobs if d.get("state") == "running"}
    job_runs = {}
    for p, d in jobs:
        source = records.relative(str(p))
        reflection_path, reflection = reflections.get(source, ("", {}))
        exp_ref = d.get("experiment") or {}
        exp = records.read(exp_ref.get("path", "")) if isinstance(exp_ref, dict) else {}
        pop = exp.get("population") or {}
        scope = {"value": pop.get("scopeBytes"), "unit": "bytes (contract scope)"}
        if scope["value"] is None:
            scope = {"value": d.get("gate_size"), "unit": "gate units (see contract)"}
        scope["symbols"] = pop.get("scopeSymbols")
        scope["population"] = pop.get("unit", "")
        scope["coordinate"] = pop.get("coordinate")
        scope["selection"] = pop.get("selection")
        definitions = {item["id"]: item.get("unit", "reported value")
                       for item in exp.get("measurements", []) if isinstance(item, dict) and "id" in item}
        decision = reflection.get("decision") or {}
        run = {"id": d["job_id"], "candidate_id": d["candidate_id"], "kind": "job",
            "state": "held" if p.parent.name == "pending" and (d.get("held") or d.get("hold")) else d.get("state", p.parent.name),
            "date": d.get("finished_at") or d.get("cancelled_at") or d.get("started_at") or d.get("submitted_at") or "",
            "purpose": d.get("purpose", ""), "scope": scope, "source": source,
            "execution_mode": d.get("execution_mode", "legacy"),
            "resource_budget": d.get("resource_budget"), "timing_authority": d.get("timing_authority", "unverified"),
            "revision": d.get("candidate_revision"), "reflection_path": reflection_path or None,
            "outcome": decision.get("verdict", "unreviewed"),
            "validity": (reflection.get("validity") or {}).get("classification", "unreviewed"),
            "hypothesis": (reflection.get("hypothesis") or {}).get("verdict", "unreviewed"),
            "summary": decision.get("rationale") or text(d.get("hold_reason")) or "", "metrics": metrics(reflection, definitions),
            **reflection_learning(reflection, records.issues, reflection_path),
            "links": [{"label": "Job", "path": source}], "liveness": {}, "progress": {}}
        for label, path in (("Reflection", reflection_path), ("Log", d.get("log_path")),
                            ("Experiment", exp_ref.get("path") if isinstance(exp_ref, dict) else None)):
            rel = records.relative(path)
            if rel:
                run["links"].append({"label": label, "path": rel})
        for evidence in reflection.get("evidence", []):
            if isinstance(evidence, dict):
                rel = records.relative(evidence.get("path"))
                if rel:
                    run["links"].append({"label": Path(rel).name, "path": rel})
        if run["state"] == "running":
            run["liveness"] = live_job(d, root)
        runs.append(run)
        job_runs[run["id"]] = run

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
                        run["links"].append({"label": "Existing observer", "path": records.relative(observer["observer_progress_path"])})
                if source and observer.get("source_processes_live"):
                    source["liveness"] = {"state": "live", "observed_at": utc(), "pid": None,
                        "detail": "Existing observer plan binds live boot/PID/start/argv identities on this host"}
        except (OSError, ValueError, KeyError) as exc:
            records.issues.append({"path": "docs/status_receipt.json", "reason": f"observer binding unavailable: {exc}"})

    linked_results = set()
    for row in records.lines("results/run_ledger.jsonl"):
        cid = row.get("program_id")
        if not candidate(cid):
            continue
        source = records.relative(row.get("result_path"))
        linked_results.add(source)
        context_job = next((r for r in runs if r["source"] == records.relative(row.get("run_source"))), None)
        if context_job:
            context_job["links"].append({"label": "Run ledger receipt", "path": source})
            context_job.setdefault("ledger_records", []).append(ledger_record(row, source))
            continue
        runs.append({"id": row.get("run_id") or source, "candidate_id": cid, "kind": "driver",
            "state": "recorded", "date": row.get("timestamp") or "", "purpose": row.get("run_purpose", ""),
            "scope": {"value": row.get("data_size"), "unit": "input bytes",
                      "population": row.get("run_scope_label"), "selection": row.get("data_path")}, "source": source,
            "outcome": "roundtrip passed" if row.get("roundtrip_ok") is True else "roundtrip unproved",
            "validity": "recorded driver result", "hypothesis": "unreviewed", "revision": row.get("candidate_revision"),
            "summary": row.get("run_context") or "", "metrics": metrics(row),
            "links": [{"label": "Result", "path": source}], "liveness": {}, "progress": {},
            "ledger_records": [ledger_record(row, source)]})

    # Index retained result summaries even when they never entered the job queue.
    # Supporting artifacts stay linked through their directory, not invented runs.
    summary_names = {"decision.json", "receipt.json", "screen.json", "result.json", "summary.json", "migration.json"}
    job_evidence = {link["path"] for r in runs if r["kind"] == "job" for link in r["links"]}
    for directory in records.files("results/*"):
        if not directory.is_dir():
            continue
        cid = directory.name
        a = candidate(cid, "result collection")
        if not a:
            continue
        a["sources"].append(f"results/{cid}/")
        if cid in active:
            continue
        for p in sorted(directory.glob("*.json")):
            rel = records.relative(str(p))
            a["sources"].append(rel)
            if rel in linked_results or (p.name not in summary_names and not p.name.endswith("-receipt.json") and not re.match(r"\d{4}-\d{2}-\d{2}T", p.name)):
                continue
            if rel in job_evidence:
                continue
            d = records.read(p)
            if not d:
                continue
            status = d.get("status") or d.get("verdict")
            if not isinstance(status, str):
                status = "reported pass" if d.get("terminal_pass") is True or d.get("roundtrip_ok") is True else "recorded"
            runs.append({"id": "report:" + rel, "candidate_id": cid, "kind": "legacy report",
                "state": "recorded", "date": d.get("generatedUtc") or d.get("timestamp") or "",
                "purpose": "retained report", "scope": {"value": d.get("scope_bytes", d.get("data_size")), "unit": "reported bytes"},
                "outcome": status, "validity": "unreviewed report", "hypothesis": "unreviewed",
                "summary": text(d.get("next_action")) or text(d.get("claim_boundary")), "metrics": metrics(d),
                "source": rel, "links": [{"label": "Report", "path": rel}], "liveness": {}, "progress": {}})

    for directory in records.files("results_preserve/*"):
        if directory.is_dir():
            a = candidate(directory.name, "result collection")
            if a:
                a["sources"].append(records.relative(str(directory)) + "/")
    loose = [records.relative(str(p)) for p in records.files("results/*.json")]
    if loose:
        candidate("collection:unassigned_reports", "result collection").update(
            name="Unassigned result reports", description="Top-level retained reports without a candidate-directory identity.", sources=loose)

    for run in runs:
        a = candidate(run["candidate_id"])
        if a:
            a["run_ids"].append(run["id"])
            a["updated_at"] = max(a["updated_at"], text(run["date"]))
    for a in list(algorithms.values()):
        for edge in a["parents"]:
            if edge["id"] in algorithms:
                algorithms[edge["id"]]["children"].append(a["id"])
        a["sources"] = sorted(set(a["sources"]))
        a["proposal_ids"] = sorted(set(a["proposal_ids"]))

    mixes = []
    for p in records.files("operations/adaptive/composition/*.json"):
        d = records.read(p)
        mixes.append({"id": d.get("graphId") or p.stem, "scope": d.get("scope", ""),
            "path": records.relative(str(p)), "components": d.get("components", []),
            "interactions": d.get("interactions", []), "composition": d.get("composition", {}),
            "conclusion": d.get("conclusion", {})})
    portfolio_entries = {}
    # Source-local idea IDs are distinct from executable candidate identities.
    for p in records.files("docs/*portfolio*.json"):
        d = records.read(p)
        rel = records.relative(str(p))
        for field in ("candidates", "entries", "unranked_infrastructure"):
            entries = d.get(field)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or not entry.get("id"):
                    continue
                key = f"idea:{p.stem}:{entry['id']}"
                a = candidate(key, "portfolio idea")
                if not a:
                    continue
                a.update(name=entry.get("name") or entry["id"],
                    description=text(entry.get("assessment")) or text(entry.get("event_universe")) or text(entry.get("information_source")),
                    status=entry.get("status") or entry.get("state") or "idea", sources=[rel],
                    summary=text(entry.get("decision")) or text(entry.get("next_gate")))
                portfolio_entries[(rel, entry["id"])] = entry
        for probe in d.get("authorized_probes", []):
            if isinstance(probe, dict) and probe.get("candidate") in algorithms:
                algorithms[probe["candidate"]]["sources"].append(rel)
    for p in records.files("docs/*compositions*.json"):
        d = records.read(p)
        for comp in d.get("compositions", []):
            if not isinstance(comp, dict) or not comp.get("id"):
                continue
            registry = d.get("portfolio_registry", "")
            components = []
            for cid in comp.get("components", []):
                entry = portfolio_entries.get((registry, cid), {}) if isinstance(cid, str) else {}
                components.append({"id": cid, "role": entry.get("name") or "source-local idea", "state": entry.get("status", "unproved")})
            mixes.append({"id": f"{p.stem}:{comp['id']}", "scope": comp.get("name", ""),
                "path": records.relative(str(p)), "components": components, "interactions": [],
                "composition": {"status": comp.get("status"), "candidateId": None, "scoreCreditBytes": 0,
                                "portfolio": registry},
                "conclusion": {"description": comp.get("fusion", ""), "claim_boundary": d.get("claim_boundary", "")}})
    notes = []
    note_files = [root / "docs/research_register.md", *records.files("docs/research_register/archive/*.md"),
                  *records.files("docs/research/historical_candidate_notes/*.md")]
    for p in note_files:
        if not p.is_file():
            continue
        body = p.read_text(errors="replace")
        for number, match in enumerate(re.finditer(r"^## (.+)\n([\s\S]*?)(?=^## |\Z)", body, re.MULTILINE)):
            title, content = match.groups()
            rel = records.relative(str(p))
            note = {"id": f"{rel}:{number}", "title": title, "path": rel,
                    "line": body.count("\n", 0, match.start()) + 1,
                    "text": content.strip(), "excerpt": re.sub(r"\s+", " ", content.strip())[:900]}
            notes.append(note)
            for cid in set(re.findall(r"`([a-z0-9_]+)`", content)) & algorithms.keys():
                algorithms[cid]["notes"].append({"title": title, "path": rel})

    runs.sort(key=lambda r: (text(r["date"]), r["id"]), reverse=True)
    for run in runs:
        if run.get("reflection_path"):
            algorithms[run["candidate_id"]]["reflections"].append({
                "run_id": run["id"], "source": run["reflection_path"], "scope": run["scope"],
                **{key: run[key] for key in ("validity", "hypothesis", "outcome", "lessons",
                    "localized_cause", "failure_class", "retired_dimensions", "uncertainties", "next_action")}})
    for a in algorithms.values():
        if a["kind"] == "candidate" and not (root / "programs" / a["id"] / "meta.json").is_file():
            a["coverage"].append("metadata missing")
        if not a["run_ids"]:
            a["coverage"].append("no indexed run or result summary")
        if a["kind"] == "result collection":
            a["coverage"].append("artifact directory; algorithm identity unrecorded")
        if any(edge["id"] not in algorithms for edge in a["parents"]):
            a["coverage"].append("unresolved parent reference")
    project_browsing_state(list(algorithms.values()), runs)
    try:
        from .enwiki9_tool_catalogue import build_catalogue
    except ImportError:
        from enwiki9_tool_catalogue import build_catalogue
    catalogue = build_catalogue(root)
    objective_path = research_contracts.objective_binding()["objectivePath"]
    objective = records.read(objective_path)
    data = {"generated_at": utc(), "host": socket.gethostname(),
        "objective": {"targetScoreBytes": objective.get("score", {}).get("targetBytes"),
                      "corpusBytes": objective.get("corpus", {}).get("bytes"),
                      "path": objective_path},
        "algorithms": sorted(algorithms.values(), key=lambda a: a["id"]),
        "runs": runs, "proposals": proposals, "mixes": mixes, "notes": notes, "tools": catalogue,
        "issues": records.issues,
        "mix_candidates": sorted(a["id"] for a in algorithms.values()
            if a["kind"] == "candidate" and re.search(
                r"\b(mix(?:er|ing|ture|es|ed)?|blend(?:ing|ed)?|hybrid|ensemble|fusion|compos(?:ite|ition))\b",
                " ".join(text(a.get(k)) for k in ("id", "name", "description")).replace("_", " "), re.I))}
    data["counts"] = {"algorithms": len(algorithms), "programs": len([p for p in records.files("programs/*") if p.is_dir()]),
        "proposals": len(proposals), "runs": len(runs), "mixes": len(mixes), "notes": len(notes),
        "tools": len(catalogue),
        "current_algorithms": sum(a["browsing_state"] == "current" for a in algorithms.values()),
        "historical_algorithms": sum(a["browsing_state"] == "historical" for a in algorithms.values()),
        "running": sum(r["state"] == "running" and r["liveness"].get("state") == "live" for r in runs),
        "unverified_running": sum(r["state"] == "running" and r["liveness"].get("state") != "live" for r in runs),
        "jobs": dict(Counter(d.get("state") for _, d in jobs)), "read_issues": len(records.issues)}
    data["reviews"] = review_backlog(data)
    return data


def review_backlog(data):
    """Latest terminal job per candidate, with presence checks, not verdicts."""
    latest = {}
    # Match the adaptive lifecycle's job-identity ordering, not finish time:
    # an older cancelled job may have been reconciled after its successor.
    for run in sorted(data["runs"], key=lambda r: (r["id"], r["source"]), reverse=True):
        if run["kind"] == "job" and run["state"] in {"completed", "failed", "cancelled"}:
            latest.setdefault(run["candidate_id"], run)
    missing = [run for run in latest.values() if not run.get("reflection_path")]
    return sorted(missing, key=lambda r: (r["state"] == "cancelled", not bool(r.get("revision"))))


def record_options(parser):
    parser.add_argument("--search", help="case-insensitive search; all words must match")
    parser.add_argument("--view", choices=("algorithms", "runs", "notes", "mixes", "proposals", "reviews", "tools"),
                        help="record collection (default: algorithms; candidate detail: runs)")
    parser.add_argument("--candidate", help="exact candidate ID; include identity, lineage, sources, and history")
    parser.add_argument("--state", action="append", help="recorded state or status; repeat to include alternatives")
    parser.add_argument("--limit", type=int, default=20, help="records per page, 1–100 (default: 20)")
    parser.add_argument("--offset", type=int, default=0, help="skip this many matching records")
    parser.add_argument("--include-legacy", action="store_true", help="include unbound historical jobs in the reviews view")
    parser.add_argument("--history", action="store_true", help="include retired configurations and all run repeats; explicit search, state, or candidate also includes history")


def record_query(data, args):
    if not 1 <= args.limit <= 100 or args.offset < 0:
        raise ValueError("--limit must be 1–100 and --offset must be nonnegative")
    algorithm = None
    if args.candidate:
        algorithm = next((a for a in data["algorithms"] if a["id"] == args.candidate), None)
        if algorithm is None:
            raise ValueError(f"Candidate not found: {args.candidate}; use records --search to find an ID")
    view = args.view or ("runs" if algorithm else "algorithms")
    rows = review_backlog(data) if view == "reviews" else data[view]
    if view == "reviews" and not args.include_legacy:
        rows = [row for row in rows if row.get("revision")]
    if algorithm:
        def related(row):
            if view == "algorithms":
                return row["id"] == algorithm["id"]
            if view in {"runs", "reviews"}:
                return row.get("candidate_id") == algorithm["id"]
            if view == "proposals":
                return row["id"] in algorithm["proposal_ids"]
            if view == "notes":
                return any(n["path"] == row["path"] and n["title"] == row["title"] for n in algorithm["notes"])
            if view == "tools":
                return algorithm["id"] in row.get("candidate_ids", [])
            return (row.get("composition") or {}).get("candidateId") == algorithm["id"]
        rows = [row for row in rows if related(row)]
    history = bool(getattr(args, "history", False) or algorithm or args.search or args.state)
    hidden = 0
    if not history and view in {"algorithms", "runs"}:
        before = len(rows)
        rows = [row for row in rows if row.get("browsing_state") != "historical"]
        if view == "runs":
            latest, visible = set(), []
            for row in rows:
                # Running and queued records always remain visible, including
                # unknown process identities. Retain the latest result too.
                if row["state"] in ACTIVE_JOB_STATES:
                    visible.append(row)
                elif row["candidate_id"] not in latest:
                    latest.add(row["candidate_id"])
                    visible.append(row)
            rows = visible
        else:
            rows = sorted(rows, key=lambda row: (row.get("has_active_job_record", False), row.get("updated_at", ""), row["id"]), reverse=True)
        hidden = before - len(rows)
    if args.state:
        states = {state.casefold() for state in args.state}
        rows = [row for row in rows if text(row.get("state", row.get("status"))).casefold() in states]
    if args.search:
        terms = args.search.casefold().split()
        rows = [row for row in rows if all(term in json.dumps(row, ensure_ascii=False).casefold() for term in terms)]
    page = rows[args.offset:args.offset + args.limit]
    # Keep search over full research records, but bound what an agent receives.
    if view == "algorithms":
        keys = ("id", "name", "description", "kind", "family", "status", "parents", "coverage", "browsing_state")
        page = [{**{key: row.get(key) for key in keys}, "run_count": len(row["run_ids"]),
                 "reflection_count": len(row.get("reflections", [])),
                 "sources": row["sources"][:4]} for row in page]
    elif view == "notes":
        page = [{key: value for key, value in row.items() if key != "text"} for row in page]
    elif view == "tools":
        page = [{**{key: row.get(key) for key in ("id", "path", "purpose", "launch_capability",
                    "launch_authority", "artifact", "contract_count", "diagnostics")},
                 **{key: row.get(key, [])[:8] for key in ("inputs", "outputs", "resources", "arguments", "sources", "contract_outputs")},
                 "argument_count": len(row.get("arguments", [])),
                 "candidate_count": len(row.get("candidate_ids", []))} for row in page]
    result = {"schema": "enwiki9_record_query_v1", "generated_at": data["generated_at"],
              "host": data["host"], "view": view, "total": len(rows), "offset": args.offset,
              "limit": args.limit, "next_offset": args.offset + args.limit if args.offset + args.limit < len(rows) else None,
              "records": page, "source_issues": data["issues"],
              "reflection_authority": "Recorded claims and source links only; browsing does not validate reflection evidence or authorize the next action.",
              "history_included": history, "hidden_historical_records": hidden}
    if algorithm:
        result["candidate"] = algorithm
    if view == "reviews":
        result["meaning"] = "Latest terminal job per candidate without a linked reflection, ordered by the adaptive lifecycle's job identity. Unbound legacy jobs appear only with --include-legacy. Presence is not validation; inspect original evidence before reflect."
    return result


def start_payload(data, root):
    """Orient an agent without ranking, hashing evidence, or launching work."""
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
    if running and (old_active is False or operator.get("safe_to_launch_candidate_gate") is True):
        issues.append({"path": "docs/status_receipt.json", "reason": "operator receipt reports idle or safe launch while running jobs exist; inspect its timestamp and the existing observer before scheduling"})
    keys = ("id", "candidate_id", "state", "purpose", "scope", "source", "liveness", "progress",
            "execution_mode", "resource_budget", "timing_authority")
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
