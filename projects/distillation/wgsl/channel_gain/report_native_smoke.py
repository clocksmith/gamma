#!/usr/bin/env python3
"""Rebuild descriptive native-smoke reports without loading models or oracles.

Example (outputs are new files; --overwrite replaces only this reporter's outputs):
  python3 report_native_smoke.py --smoke native-smoke-03.jsonl \
    --attempt native-smoke-01.jsonl --attempt native-smoke-02.jsonl \
    --integration-probe adapter-probe-03.json \
    --selection selection-receipt.json --json-output summary.json \
    --markdown-output report.md
Missing optional selection receipts remain pending. Incomplete JSONL tails are
reported and ignored; malformed complete lines fail. No confirmation is inferred.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path


SCHEMA = "gamma.channel-gain-native-smoke-report/v1"
MARKER = "<!-- gamma.channel-gain-native-smoke-report/v1 -->"
EXTRA_TIMING_FIELDS = ("input_contract_ms", "setup_other_ms", "setup_cleanup_ms", "request_cleanup_ms")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def stats(values):
    valid = [value for value in values if number(value)]
    return {"observed": len(valid), "missing": len(values) - len(valid),
            "sum": sum(valid) if valid else None,
            "mean": sum(valid) / len(valid) if valid else None,
            "min": min(valid) if valid else None, "max": max(valid) if valid else None}


def load(path, optional=False):
    path = Path(path).resolve()
    if optional and not path.exists():
        return None, {"path": str(path), "status": "absent", "sha256": None}
    data = path.read_bytes()
    provenance = {"path": str(path), "status": "read", "sha256": digest(data), "bytes": len(data)}
    try:
        value = json.loads(data)
        if isinstance(value, dict):
            return [value] if "kind" in value else value, provenance
    except json.JSONDecodeError:
        pass
    events, warnings = [], []
    lines = data.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("Journal event must be an object")
            events.append(event)
        except json.JSONDecodeError:
            if index == len(lines) - 1 and not line.endswith(b"\n"):
                warnings.append("Ignored incomplete final JSONL line; source hash covers its bytes.")
            else:
                raise ValueError(f"Malformed complete JSONL line {index + 1}: {path}")
    if not events:
        raise ValueError(f"No readable receipt/events: {path}")
    provenance["warnings"] = warnings
    return events, provenance


def unpack(value):
    events = value if isinstance(value, list) else []
    terminal = [e["record"] for e in events if e.get("kind") in ("smoke-summary", "smoke-blocker")]
    summary = terminal[-1] if terminal else (value if isinstance(value, dict) else {})
    if not events and summary.get("status") not in ("smoke_complete", "smoke_incomplete"):
        raise ValueError("Expected native smoke summary or event journal")
    requests = [e["record"] for e in events if e.get("kind") == "request"] or summary.get("results", [])
    if len({r["id"] for r in requests}) != len(requests):
        raise ValueError("Duplicate request IDs in one attempt; refusing double counting")
    if terminal and summary.get("requestCount") != len(requests):
        raise ValueError("Terminal requestCount disagrees with journal requests")
    errors = [e.get("error", "") for e in events if e.get("kind") in ("execution-error", "stage-error")]
    if summary.get("reason"):
        errors.insert(0, summary["reason"])
    status = summary.get("status", "smoke_incomplete")
    if errors or (events and terminal == []):
        status = "smoke_incomplete"
    return {"status": status, "errors": list(dict.fromkeys(errors)), "summary": summary,
            "requests": requests,
            "preparation": [e["record"] for e in events if e.get("kind") == "preparation"] or summary.get("preparation", []),
            "diagnostics": [e["record"] for e in events if e.get("kind") == "cache-diagnostic"] or summary.get("diagnostics", []),
            "resetDiagnostics": [e["record"] for e in events if e.get("kind") == "reset-diagnostic"] or summary.get("resetDiagnostics", []),
            "coldLoads": [{k: e.get(k) for k in ("coldModelLoadMs", "coldAdapterLoadMs")} for e in events if e.get("kind") == "cold-load"]}


def compact_memory(memory):
    result = {k: v for k, v in memory.items() if not isinstance(v, (dict, list))}
    for key in ("baseSnapshot", "baseRequestSnapshot", "matchedBaselineSnapshot"):
        if key in memory:
            result[key] = memory[key]
    for key in ("deviceAtRequestStart", "deviceAtRequestEnd", "deviceAfterRequestCleanup", "deviceAtPreparationStart", "deviceAtPreparationEnd"):
        if memory.get(key):
            result[key] = {k: v for k, v in memory[key].items() if not isinstance(v, (dict, list))}
    return result


def request_summary(request):
    receipt = request.get("publicReceipt", {})
    tasks = receipt.get("tasks", [])
    checks = [c for task in tasks for c in task.get("checks", [])]
    if receipt.get("scope") != "public" or receipt.get("confirmationEvaluated") is True or any(c.get("visibility") != "public" for c in checks):
        raise ValueError("Smoke report requires explicitly public-only request receipts")
    outcome = "unmeasured"
    if tasks and all(isinstance(t.get("passed"), bool) for t in tasks):
        outcome = "passed" if all(t["passed"] for t in tasks) else "failed"
    return {k: request.get(k) for k in ("id", "taskId", "condition", "arm", "sampleIndex", "candidate", "tokenCount", "gainHash", "physicalRequestMs")} | {
        "publicOutcome": outcome, "publicChecksPassed": sum(c.get("passed") is True for c in checks),
        "publicChecksObserved": len(checks),
        "contractViolations": sorted({v for c in checks for v in c.get("contractViolations", [])}),
        "timing": request.get("timing", {}), "memory": compact_memory(request.get("memory", {}))}


def summarize_probe(value, source):
    if value is None:
        return {"input": source, "status": "pending"}
    if not isinstance(value, dict) or value.get("schema") != "gamma.channel-gain-adapter-integration-probe/v1":
        raise ValueError("Expected an adapter integration-probe receipt")
    if any(value.get(k) is not False for k in ("candidateSelection", "shaderChecksEvaluated", "confirmationEvaluated")):
        raise ValueError("Integration probes must explicitly exclude selection, shader scoring and confirmation")
    request = value.get("request", {})
    return {"input": source, "evidenceClass": "integration_diagnostic_only",
            **{k: value.get(k) for k in ("status", "purpose", "taskId", "inputSha256", "generation", "overriddenForDiagnosticOnly", "candidateSelection", "shaderChecksEvaluated", "confirmationEvaluated", "coldModelLoadMs", "coldAdapterLoadMs", "totalWallMs", "error")},
            "request": {"tokenCount": request.get("tokenCount"), "physicalRequestMs": request.get("physicalRequestMs"),
                        "timing": request.get("timing", {}), "memory": compact_memory(request.get("memory", {}))}}


def build_report(smoke, provenance, attempts, selection, selection_provenance, label, integration_probes=()):
    run = unpack(smoke)
    if provenance.get("warnings"):
        run["status"] = "smoke_incomplete"
    requests = [request_summary(r) for r in run["requests"]]
    bases = {r["taskId"]: r for r in requests if r["condition"] == "base"}
    for r in requests:
        base = bases.get(r["taskId"])
        actual, baseline = r["timing"].get("end_to_end_ms"), (base or {}).get("timing", {}).get("end_to_end_ms")
        r["descriptiveMatchedBaseOverheadFraction"] = actual / baseline - 1 if base and number(actual) and number(baseline) and baseline > 0 else None
    grouped = {}
    for r in requests:
        grouped.setdefault((r["condition"], r["arm"]), []).append(r)
    groups = [{"condition": condition, "arm": arm, "requests": len(rows),
               "publicOutcomes": {name: sum(r["publicOutcome"] == name for r in rows) for name in ("passed", "failed", "unmeasured")},
               "tokens": stats([r["tokenCount"] for r in rows]),
               "attributedEndToEndMs": stats([r["timing"].get("end_to_end_ms") for r in rows]),
               "descriptiveMatchedBaseOverheadFraction": stats([r["descriptiveMatchedBaseOverheadFraction"] for r in rows]),
               "physicalRequestMs": stats([r["physicalRequestMs"] for r in rows])}
              for (condition, arm), rows in grouped.items()]
    gain_groups = {}
    for r in requests:
        if r["gainHash"] is not None:
            gain_groups.setdefault((r["taskId"], r["condition"], r["sampleIndex"]), []).append(r)
    pairs = []
    for (task, condition, sample), rows in gain_groups.items():
        arms = {r["arm"]: r["gainHash"] for r in rows}
        complete = {"mlp_base_cache", "mlp_frozen_gain_reprefill"} <= arms.keys()
        pairs.append({"taskId": task, "condition": condition, "sampleIndex": sample, "armHashes": arms,
                      "status": ("same_gain" if len(set(arms.values())) == 1 else "gain_mismatch") if complete else "pair_incomplete"})
    attempt_rows, seen = [], set()
    for value, source in [(smoke, provenance), *attempts]:
        if source["sha256"] in seen:
            continue
        seen.add(source["sha256"])
        parsed = unpack(value)
        if source.get("warnings"):
            parsed["status"] = "smoke_incomplete"
        attempt_rows.append({"input": source, "status": parsed["status"], "failed": bool(parsed["errors"]),
                             "completedRequests": len(parsed["requests"]), "errors": parsed["errors"],
                             "physicalSmokeWallMs": parsed["summary"].get("physicalSmokeWallMs"),
                             "coldLoads": parsed["coldLoads"]})
    selected = {"status": "pending", "reason": "Selection receipt absent; no selection result inferred."}
    if selection is not None:
        if not isinstance(selection, dict) or selection.get("schema") != "gamma.channel-gain-native-selection/v1":
            raise ValueError("Expected a native selection receipt")
        selected = {k: selection.get(k) for k in ("status", "selectedCandidate", "candidates", "admission", "budget", "selectionChecksEvaluated", "confirmationPopulationRead", "confirmationEvaluated", "extraModelRequests", "runtimeLockSha256", "stageLockSha256", "receiptSha256")}
        lock = run["summary"].get("runtimeLockSha256")
        selected["smokeRuntimeBinding"] = "matching" if lock and lock == selection.get("runtimeLockSha256") else "not_verified_from_supplied_smoke"
        if lock and lock != selection.get("runtimeLockSha256"):
            raise ValueError("Selection/smoke runtime identities differ")
    summary = run["summary"]
    preparations = [{k: v for k, v in p.items() if k != "memory"} | {"memory": compact_memory(p.get("memory", {}))} for p in run["preparation"]]
    probes, seen_probes = [], set()
    for value, source in integration_probes:
        identity = source["sha256"] or source["path"]
        if identity not in seen_probes:
            probes.append(summarize_probe(value, source))
            seen_probes.add(identity)
    return {"schema": SCHEMA, "label": label, "evidenceClass": "descriptive_smoke_only",
            "inputs": {"smoke": provenance, "selection": selection_provenance},
            "smoke": {"status": run["status"], "completedRequests": len(requests), "observedTasks": len({r["taskId"] for r in requests}), "errors": run["errors"]},
            "attempts": {"suppliedUniqueAttempts": len(attempt_rows), "failedAttempts": sum(a["failed"] for a in attempt_rows), "records": attempt_rows},
            "groups": groups, "requests": requests, "sameGainPairs": pairs,
            "cacheDiagnostics": run["diagnostics"], "resetDiagnostics": run["resetDiagnostics"], "preparation": preparations,
            "integrationProbes": probes,
            "costs": {"coldLoads": run["coldLoads"], "physicalSmokeWallMs": summary.get("physicalSmokeWallMs"),
                      "actualPreparationMs": stats([p.get("actualPreparationMs") for p in preparations]),
                      "completedPhysicalRequestMs": stats([r["physicalRequestMs"] for r in requests]),
                      "completedVerifierMs": stats([r["timing"].get("verifier_ms") for r in requests]),
                      "cacheDiagnosticMs": stats([d.get("diagnosticMs") for d in run["diagnostics"]]),
                      "resetDiagnosticMs": stats([d.get("resetDiagnosticMs") for d in run["resetDiagnostics"]]),
                      "attributedTimingBreakdownMs": {key: stats([r["timing"].get(key) for r in requests]) for key in EXTRA_TIMING_FIELDS},
                      "selectionGpuMsCharged": summary.get("selectionGpuMsCharged"),
                      "bestOfK": {"status": "recorded" if "bestOfK" in summary else "pending", "k": summary.get("k"), "tasks": summary.get("bestOfK", [])},
                      "eta": summary.get("eta") if run["status"] == "smoke_complete" else None},
            "selection": selected, "confirmation": {"status": "not_evaluated" if selected.get("status") == "selection_not_admitted" else "not_established_by_these_inputs", "statisticalConfirmationClaim": False},
            "limitations": [
                "Public smoke checks are descriptive observations, not held-out semantic confirmation, selection evidence, or a test of the frozen success criteria.",
                "Incomplete smoke does not establish all-control throughput or a full-batch ETA. Missing requests, comparator results and diagnostics remain missing.",
                "Failure counts cover only unique supplied attempt files. An incomplete file without a recorded error is not called a failed process.",
                "Attributed end-to-end latency includes each request's reference/instruction prefill and gain work plus verification. Shared preparation is attributed to multiple arms; summing attributed latencies is not physical batch cost.",
                "Physical request latency excludes separately recorded preparation/verification. Physical smoke wall time, cold model/adapter load, setup, cache diagnostics and best-of-k costs are reported separately; missing or failed-request cost is not invented.",
                "Gain logical bytes, allocated GPU bytes and baseline-subtracted retained snapshot tensor bytes are distinct. Owned snapshots include CPU cache/recurrent/logit backing buffers and GPU cache buffers, excluding JS metadata.",
                "Device counters cover GPUBuffer allocations on the model device, including allocator-retained buffers. Process-lifetime peaks are not per-request incremental peaks, physical VRAM, RSS or total host memory; no peak subtraction is inferred.",
                "Same gain hashes support identical stored gain state across cache arms; they do not establish equal cache states or outputs. Per-layer diagnostics compare the recorded teacher-forced prefix only.",
                "Reset diagnostics compare original base-prefill logits with an unmodified prefill after transform discard for identical input tokens; they do not sample or score an additional shader. These observations do not establish general concurrent-request isolation.",
                "Retained baseline logits used only for reset diagnostics have separately reported storage bytes; diagnostic storage is not silently counted as serving transform state. Device-after-cleanup observations are preserved when recorded.",
                "Integration probes use their recorded diagnostic generation settings (including any four-token limit). Their requests, tokens and costs remain separate from scored smoke, failed smoke attempt counts, candidate selection and confirmation; they establish no shader quality result.",
                "New input-contract/setup/cleanup timing fields are reported when present. Earlier attempts lacking these fields remain explicitly missing; attributed breakdown totals are components of E2E latency and must not be added to it again.",
                "Admission estimates extrapolate observed smoke timings; they are not mathematical lower bounds or proof that all implementations cannot fit the frozen budget."]}


def fmt(value):
    return f"{value:.3f}" if number(value) else "not recorded"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def delta(value):
    return f"{value:.9g}" if number(value) else "not recorded"


def markdown(report):
    lines = [MARKER, "# Native channel-gain smoke report", "", f"{report['label']}: **{report['smoke']['status']}**. Descriptive smoke evidence only; no statistical confirmation.", "",
             f"Completed requests: {report['smoke']['completedRequests']}; observed tasks: {report['smoke']['observedTasks']}; recorded failed attempts: {report['attempts']['failedAttempts']}/{report['attempts']['suppliedUniqueAttempts']} supplied unique attempts.",
             f"Selection: **{report['selection']['status']}**. Confirmation: **{report['confirmation']['status']}**.", "",
             "| Condition / cache arm | Requests | Public pass / fail / unmeasured | Mean tokens | Mean attributed E2E ms | Mean physical request ms | Mean E2E change vs same-task base |",
             "| --- | ---: | --- | ---: | ---: | ---: | ---: |"]
    for g in report["groups"]:
        o = g["publicOutcomes"]
        overhead = g["descriptiveMatchedBaseOverheadFraction"]["mean"]
        change = f"{100 * overhead:+.2f}%" if number(overhead) else "not recorded"
        lines.append(f"| {cell(g['condition'])} / {cell(g['arm'])} | {g['requests']} | {o['passed']} / {o['failed']} / {o['unmeasured']} | {fmt(g['tokens']['mean'])} | {fmt(g['attributedEndToEndMs']['mean'])} | {fmt(g['physicalRequestMs']['mean'])} | {change} |")
    lines += ["", "## Costs and completeness", "", f"Physical smoke wall: {fmt(report['costs']['physicalSmokeWallMs'])} ms.", ""]
    for key in ("actualPreparationMs", "completedPhysicalRequestMs", "completedVerifierMs", "cacheDiagnosticMs", "resetDiagnosticMs"):
        s = report["costs"][key]
        lines.append(f"- {key}: {fmt(s['sum'])} ms ({s['observed']} recorded, {s['missing']} missing).")
    for load in report["costs"]["coldLoads"]:
        lines.append(f"- Cold model load: {fmt(load['coldModelLoadMs'])} ms; cold adapter load: {fmt(load['coldAdapterLoadMs'])} ms.")
    lines += [f"- Best-of-k: {report['costs']['bestOfK']['status']}; k={report['costs']['bestOfK']['k']}."]
    for task in report["costs"]["bestOfK"]["tasks"]:
        lines.append(f"- {cell(task['taskId'])}: base samples {fmt(task.get('actualComputeMs'))} ms; transform {fmt(task.get('transformComputeMs'))} ms.")
    lines += ["", "Per-request attributed timing components (already included in E2E, not additional costs):", "",
              "| Request | Input contract ms | Other setup ms | Setup cleanup ms | Request cleanup ms |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for request in report["requests"]:
        lines.append("| " + cell(request["id"]) + " | " + " | ".join(fmt(request["timing"].get(k)) for k in EXTRA_TIMING_FIELDS) + " |")
    lines += ["", "## Integration probes (separate diagnostic cost)", ""]
    if not report["integrationProbes"]:
        lines.append("No integration-probe receipt supplied.")
    for probe in report["integrationProbes"]:
        request = probe.get("request", {})
        lines.append(f"- `{probe['input']['path']}`: {probe['status']}; tokens={request.get('tokenCount')}; diagnostic token limit={probe.get('generation', {}).get('maxNewTokens') if probe.get('generation') else None}.")
        lines.append(f"  - Total wall {fmt(probe.get('totalWallMs'))} ms; cold model {fmt(probe.get('coldModelLoadMs'))} ms; cold adapter {fmt(probe.get('coldAdapterLoadMs'))} ms; physical request {fmt(request.get('physicalRequestMs'))} ms; attributed E2E {fmt(request.get('timing', {}).get('end_to_end_ms'))} ms.")
    lines += ["", "These probes are excluded from smoke request/outcome totals, selection and confirmation; no shader quality claim follows."]
    lines += ["", "## Gain pairs", ""]
    for pair in report["sameGainPairs"]:
        lines.append(f"- {cell(pair['taskId'])} / {cell(pair['condition'])}: {pair['status']}; " + "; ".join(f"{arm} `{value}`" for arm, value in pair["armHashes"].items()))
    if not report["sameGainPairs"]:
        lines.append("No paired gain observations recorded.")
    lines += ["", "## Cache diagnostics", ""]
    if not report["cacheDiagnostics"]:
        lines.append("No completed cache diagnostics recorded.")
    for d in report["cacheDiagnostics"]:
        lines += [f"{cell(d.get('taskId'))}: measured={d.get('measured')}; prefix={d.get('teacherForcedPrefix')}; gain `{d.get('gainHash')}`.", "",
                  "| State / layer | Component | Measured | Relative L2 | Max absolute delta | Top-1 changed | Sequence length matches |",
                  "| --- | --- | --- | ---: | ---: | --- | --- |"]
        for kind in ("kv", "recurrent"):
            for layer, state in d.get(kind, {}).items():
                for component, v in state.items():
                    if isinstance(v, dict):
                        lines.append(f"| {kind} / {layer} | {component} | {v.get('measured')} | {delta(v.get('relativeL2'))} | {delta(v.get('maxAbsolute'))} | {v.get('top1Changed')} | {state.get('sequenceLengthMatches')} |")
        v = d.get("logits", {})
        lines += [f"| logits | output | {v.get('measured')} | {delta(v.get('relativeL2'))} | {delta(v.get('maxAbsolute'))} | {v.get('top1Changed')} | n/a |", ""]
    lines += ["## Reset diagnostics", ""]
    if not report["resetDiagnostics"]:
        lines.append("No completed reset diagnostics recorded.")
    else:
        lines += ["| Task | Measured | Same input tokens | Transform discarded | Clean prefill state | Exact logits equal | Logit relative L2 | Logit max delta | Sampling performed | Cost ms |",
                  "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |"]
        for reset in report["resetDiagnostics"]:
            before = reset.get("before", {})
            clean = before.get("gainAbsent") is True and before.get("adapterAbsent") is True and before.get("seqLen") == 0 if before else "not recorded"
            logits = reset.get("logits", {})
            lines.append(f"| {cell(reset.get('taskId'))} | {reset.get('measured')} | {reset.get('identicalInputTokens')} | {reset.get('transformDiscarded')} | {clean} | {reset.get('exactLogitsEqual')} | {delta(logits.get('relativeL2'))} | {delta(logits.get('maxAbsolute'))} | {reset.get('samplingPerformed')} | {fmt(reset.get('resetDiagnosticMs'))} |")
    lines += ["", "## Memory observations", "", "| Request | Logical gain bytes | Allocated gain bytes | Incremental retained tensor bytes | Model-device process peak bytes |", "| --- | ---: | ---: | ---: | ---: |"]
    for r in report["requests"]:
        m = r["memory"]
        lines.append(f"| {cell(r['id'])} | {fmt(m.get('selectedGainLogicalBytes'))} | {fmt(m.get('selectedGainAllocatedBytes'))} | {fmt(m.get('incrementalRetainedTensorBytes'))} | {fmt(m.get('deviceAtRequestEnd', {}).get('peakBytes'))} |")
    lines += ["", "## Attempts and blockers", ""]
    for attempt in report["attempts"]["records"]:
        lines.append(f"- `{attempt['input']['path']}`: {attempt['status']}, {attempt['completedRequests']} completed requests; wall {fmt(attempt['physicalSmokeWallMs'])} ms.")
        lines.extend(f"  - {cell(error.splitlines()[0])}" for error in attempt["errors"])
    if report["selection"].get("admission"):
        lines += ["", "Admission observation: `" + json.dumps(report["selection"]["admission"], sort_keys=True) + "`."]
    lines += ["", "## Evidence limits", ""] + [f"- {text}" for text in report["limitations"]]
    lines += ["", "## Input provenance", ""]
    for role, source in [("smoke", report["inputs"]["smoke"]), ("selection", report["inputs"]["selection"])]:
        if source:
            lines.append(f"- {role}: `{source['path']}`; {source['status']}; SHA256 `{source['sha256']}`.")
            lines.extend(f"  - {warning}" for warning in source.get("warnings", []))
    for attempt in report["attempts"]["records"]:
        lines.append(f"- Attempt `{attempt['input']['path']}`; SHA256 `{attempt['input']['sha256']}`.")
    for probe in report["integrationProbes"]:
        lines.append(f"- Integration probe `{probe['input']['path']}`; {probe['input']['status']}; SHA256 `{probe['input']['sha256']}`.")
    lines.append(f"- Reporter SHA256 `{report.get('reporterSha256')}`. Exact per-request timing/memory observations are retained in the JSON summary.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--smoke", required=True)
    parser.add_argument("--attempt", action="append", default=[])
    parser.add_argument("--selection")
    parser.add_argument("--integration-probe", action="append", default=[], help="Optional diagnostic receipt; repeat for separate probes")
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--label", default="Native smoke report")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    inputs = {Path(p).resolve() for p in [args.smoke, *args.attempt, *args.integration_probe, *([args.selection] if args.selection else [])]}
    outputs = [Path(args.json_output).resolve(), Path(args.markdown_output).resolve()]
    if len(set(outputs)) != 2 or any(p in inputs for p in outputs):
        parser.error("Output paths must be distinct from each other and all inputs")
    for index, path in enumerate(outputs):
        if path.exists():
            owned = json.loads(path.read_text()).get("schema") == SCHEMA if index == 0 else path.read_text().startswith(MARKER)
            if not args.overwrite or not owned:
                parser.error(f"Refusing existing output (requires --overwrite and this reporter's marker): {path}")
    smoke, source = load(args.smoke)
    attempts = [load(p) for p in args.attempt]
    selection, selection_source = load(args.selection, optional=True) if args.selection else (None, None)
    probes = [load(p, optional=True) for p in args.integration_probe]
    report = build_report(smoke, source, attempts, selection, selection_source, args.label, probes)
    report["reporterSha256"] = digest(Path(__file__).read_bytes())
    for path, content in zip(outputs, (json.dumps(report, indent=2, allow_nan=False) + "\n", markdown(report))):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w" if args.overwrite else "x") as output:
            output.write(content)
    print(json.dumps({"smokeStatus": report["smoke"]["status"], "selectionStatus": report["selection"]["status"],
                      "completedRequests": report["smoke"]["completedRequests"], "failedAttempts": report["attempts"]["failedAttempts"],
                      "outputs": [str(p) for p in outputs]}))


if __name__ == "__main__":
    main()
