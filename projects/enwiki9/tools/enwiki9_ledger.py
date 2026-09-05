#!/usr/bin/env python3
"""Build the browsing ledger from existing records; never launch or change a run."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import socket
import tempfile


ROOT = Path(__file__).resolve().parents[1]
STATES = ("pending", "running", "completed", "failed", "cancelled")
MAX_JSON = 8 * 1024 * 1024


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


def process_identity(pid, start=None, command=None):
    """A bounded metadata observation, never a compressor or trace reader."""
    try:
        p = Path("/proc") / str(int(pid))
        stat = p.joinpath("stat").read_text().rsplit(")", 1)[1].split()
        if stat[0] in {"Z", "X", "x"}:
            return False
        if start is not None and int(stat[19]) != int(start):
            return False
        if command:
            argv = p.joinpath("cmdline").read_bytes().split(b"\0")
            if not any(x.decode(errors="replace") == command or
                       x.decode(errors="replace").endswith("/" + command) for x in argv):
                return False
        return True
    except (OSError, ValueError, IndexError, TypeError):
        return False


def live_job(job):
    pid = job.get("worker_pid")
    runner = job.get("tool") or job.get("runner", {}).get("path")
    matched = bool(runner and process_identity(pid, command=runner))
    if not matched and process_identity(pid):
        # Lab workers execute their immutable, job-specific candidate snapshot.
        pattern = r"/tmp/gamma-enwiki9-" + re.escape(text(job.get("job_id"))) + r"-[^/]+/" + re.escape(text(job.get("candidate_id"))) + r"/program\.py"
        try:
            argv = (Path("/proc") / str(int(pid)) / "cmdline").read_bytes().split(b"\0")
            matched = any(re.fullmatch(pattern, arg.decode(errors="replace")) for arg in argv)
        except (OSError, ValueError, TypeError):
            pass
    return {"state": "observed" if matched else "unverified", "pid": pid,
            "observed_at": utc(), "detail": "Worker PID and runner or job-specific snapshot command observed on this host"
            if matched else "Recorded running; matching worker was not verified on this host"}


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
                "proposal_ids": [], "notes": [], "updated_at": "", "coverage": []}
        return algorithms[cid]

    def parent(cid, pid, source):
        a = candidate(cid)
        if a and isinstance(pid, str) and pid and pid != cid and "/" not in pid:
            edge = {"id": pid, "source": source}
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
            "hypothesis": d.get("hypothesis") or "", "state": p.parent.name,
            "parent": d.get("parent"), "parent_proposal_id": d.get("parent_proposal_id"),
            "path": records.relative(str(p))}
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
            "date": d.get("finished_at") or d.get("started_at") or d.get("submitted_at") or "",
            "purpose": d.get("purpose", ""), "scope": scope, "source": source,
            "revision": d.get("candidate_revision"),
            "outcome": decision.get("verdict", "unreviewed"),
            "validity": (reflection.get("validity") or {}).get("classification", "unreviewed"),
            "hypothesis": (reflection.get("hypothesis") or {}).get("verdict", "unreviewed"),
            "summary": decision.get("rationale") or text(d.get("hold_reason")) or "", "metrics": metrics(reflection, definitions),
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
            run["liveness"] = live_job(d)
        runs.append(run)
        job_runs[run["id"]] = run

    # Show the existing observer's receipt; never open active scientific output.
    for cid in active:
        rel = f"results/{cid}/progress.json"
        progress = records.read(rel)
        if progress.get("schema") != "gamma.enwiki9.endpoint428-horizon-orphan-adoption-progress.v1":
            continue
        stamp = progress.get("updatedUtc")
        sample = progress.get("lastSample") or {}
        processes = sample.get("processes") or {}
        try:
            fresh = 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds() <= 120
        except (TypeError, ValueError, AttributeError):
            fresh = False
        identity_pass = bool(processes) and all(process_identity(v.get("pid"), v.get("startTicks")) for v in processes.values())
        source = job_runs.get(progress.get("sourceJobId"))
        summary = {k: progress.get(k) for k in ("state", "updatedUtc", "traceBytes", "expectedTraceBytes", "sampleCount", "maximumObservedTreeRssBytes", "scienceAccessedBeforeTerminal", "failureReason")}
        for run in runs:
            if run["candidate_id"] == cid or run is source:
                run["progress"] = summary
                run["links"].append({"label": "Existing observer", "path": rel})
        if source and fresh and identity_pass:
            source["liveness"] = {"state": "observed", "observed_at": utc(), "pid": None,
                "detail": "Existing observer receipt is fresh; recorded process identities match this host"}

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
                    "excerpt": re.sub(r"\s+", " ", content.strip())[:900]}
            notes.append(note)
            for cid in set(re.findall(r"`([a-z0-9_]+)`", content)) & algorithms.keys():
                algorithms[cid]["notes"].append({"title": title, "path": rel})

    runs.sort(key=lambda r: (text(r["date"]), r["id"]), reverse=True)
    for a in algorithms.values():
        if a["kind"] == "candidate" and not (root / "programs" / a["id"] / "meta.json").is_file():
            a["coverage"].append("metadata missing")
        if not a["run_ids"]:
            a["coverage"].append("no indexed run or result summary")
        if a["kind"] == "result collection":
            a["coverage"].append("artifact directory; algorithm identity unrecorded")
        if any(edge["id"] not in algorithms for edge in a["parents"]):
            a["coverage"].append("unresolved parent reference")
    objective = records.read("contracts/research/v1/objective-contract.json")
    data = {"generated_at": utc(), "host": socket.gethostname(),
        "objective": {"targetScoreBytes": objective.get("score", {}).get("targetBytes"),
                      "corpusBytes": objective.get("corpus", {}).get("bytes"),
                      "path": "contracts/research/v1/objective-contract.json"},
        "algorithms": sorted(algorithms.values(), key=lambda a: a["id"]),
        "runs": runs, "proposals": proposals, "mixes": mixes, "notes": notes, "issues": records.issues,
        "mix_candidates": sorted(a["id"] for a in algorithms.values()
            if a["kind"] == "candidate" and re.search(
                r"\b(mix(?:er|ing|ture|es|ed)?|blend(?:ing|ed)?|hybrid|ensemble|fusion|compos(?:ite|ition))\b",
                " ".join(text(a.get(k)) for k in ("id", "name", "description")).replace("_", " "), re.I))}
    data["counts"] = {"algorithms": len(algorithms), "programs": len([p for p in records.files("programs/*") if p.is_dir()]),
        "proposals": len(proposals), "runs": len(runs), "mixes": len(mixes), "notes": len(notes),
        "running": sum(r["state"] == "running" and r["liveness"].get("state") == "observed" for r in runs),
        "unverified_running": sum(r["state"] == "running" and r["liveness"].get("state") != "observed" for r in runs),
        "jobs": dict(Counter(d.get("state") for _, d in jobs)), "read_issues": len(records.issues)}
    return data


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False, encoding="utf-8") as f:
        temp = Path(f.name)
        f.write(content)
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="print coverage without writing the browsing files")
    args = parser.parse_args()
    data = build(ROOT)
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
