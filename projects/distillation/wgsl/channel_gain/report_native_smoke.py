#!/usr/bin/env python3
"""Rebuild descriptive native-smoke reports without loading models or oracles.

Example (outputs are new files; --overwrite replaces only this reporter's outputs):
  python3 report_native_smoke.py --smoke native-smoke-03.jsonl \
    --attempt native-smoke-01.jsonl --attempt native-smoke-02.jsonl \
    --integration-probe adapter-probe-03.json \
    --public-replay public-verifier-replay-03.json \
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
            "coldLoads": ([{k: e.get(k) for k in ("coldModelLoadMs", "coldAdapterLoadMs")} for e in events if e.get("kind") == "cold-load"]
                          or ([{k: summary.get(k) for k in ("coldModelLoadMs", "coldAdapterLoadMs")}]
                              if any(k in summary for k in ("coldModelLoadMs", "coldAdapterLoadMs")) else []))}


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


def validate_reporting_replay(original, original_input, replay):
    """Check report bindings; the execution-stage validator also checks the seal/code.

    This reader never substitutes for validatePublicReplay in native_experiment.
    It consumes already executed receipts and reads no oracle or runtime modules.
    """
    if not isinstance(original, dict) or original.get("schema") != "gamma.channel-gain-native-smoke/v1" or original.get("status") != "smoke_complete":
        raise ValueError("Public replay requires the original complete native smoke JSON receipt, not a journal")
    if not isinstance(replay, dict) or replay.get("schema") != "gamma.channel-gain-public-verifier-replay/v1" or replay.get("status") != "smoke_public_replay_complete":
        raise ValueError("Expected a completed public-verifier replay receipt")
    generation = replay.get("generation", {})
    if (generation.get("originalSmokeFileSha256") != original_input["sha256"]
            or not original.get("runtimeLockSha256") or generation.get("runtimeLockSha256") != original["runtimeLockSha256"]
            or not original.get("receiptSha256") or generation.get("originalSmokeReceiptSha256") != original["receiptSha256"]
            or generation.get("allSourcesAndTokenSequencesPreserved") is not True):
        raise ValueError("Replay does not bind the supplied original smoke file/runtime/receipt")
    corrected = replay.get("corrected", {})
    k = original.get("k")
    if not isinstance(k, int) or isinstance(k, bool) or k < 1 or corrected.get("k") != k or corrected.get("derivedK") != k:
        raise ValueError("Replay changed the frozen smoke k")
    if corrected.get("modelRequestsAdded") != 0 or corrected.get("confirmationEvaluated") is not False:
        raise ValueError("Public replay must add no model requests or confirmation")
    old_results, results = original.get("results", []), corrected.get("results", [])
    if not old_results or len(results) != len(old_results) or original.get("requestCount") != len(old_results):
        raise ValueError("Replay request set changed")
    for old, new in zip(old_results, results):
        receipt, timing = new.get("publicReceipt", {}), new.get("timing", {})
        before = old.get("timing", {})
        for value in (before.get("verifier_ms"), before.get("end_to_end_ms"), timing.get("verifier_ms"), receipt.get("verifierMs")):
            if not number(value) or value < 0:
                raise ValueError("Invalid original/replayed verifier timing")
        if before["end_to_end_ms"] < before["verifier_ms"]:
            raise ValueError("Original E2E excludes verifier timing")
        expected_replay = {"originalPublicReceipt": old["publicReceipt"], "originalOuterVerifierMs": before["verifier_ms"],
                           "originalEndToEndMs": before["end_to_end_ms"], "replayOuterVerifierMs": timing["verifier_ms"]}
        if "verifier_dispatch_ms" in before:
            expected_replay["originalDispatchVerifierMs"] = before["verifier_dispatch_ms"]
        expected = {**old, "publicReceipt": receipt, "timing": {**before, "verifier_ms": timing["verifier_ms"],
                    "verifier_dispatch_ms": receipt["verifierMs"],
                    "end_to_end_ms": before["end_to_end_ms"] - before["verifier_ms"] + timing["verifier_ms"]},
                    "verifierReplay": expected_replay}
        if new != expected:
            raise ValueError("Replay changed generation or non-verifier timing/state")
        tasks = receipt.get("tasks", [])
        old_receipt = old["publicReceipt"]
        if (receipt.get("scope") != "public" or receipt.get("confirmationEvaluated") is not False or len(tasks) != 1
                or tasks[0].get("taskId") != old["taskId"] or tasks[0].get("sourceSha256") != digest(old["source"].encode())
                or receipt.get("inputHashes") != old_receipt.get("inputHashes")
                or receipt.get("deviceInfo") != old_receipt.get("deviceInfo")
                or receipt.get("deviceInfo") != replay.get("verifier", {}).get("device")
                or [c.get("id") for c in tasks[0].get("checks", [])] != [c.get("id") for c in old_receipt["tasks"][0].get("checks", [])]
                or any(c.get("visibility") != "public" for c in tasks[0].get("checks", []))):
            raise ValueError("Replay changed public check/source/device identities")
        rp = receipt.get("provenance", {})
        if (rp.get("replaySealSha256") != replay.get("sealSha256") or rp.get("generationRuntimeLockSha256") != original["runtimeLockSha256"]
                or rp.get("layoutRepair") != replay.get("verifier", {}).get("repair")):
            raise ValueError("Replay request verifier provenance mismatch")
    for key in ("preparation", "diagnostics", "resetDiagnostics"):
        if corrected.get(key) != original.get(key):
            raise ValueError(f"Replay changed original {key}")
    if corrected.get("originalPhysicalSmokeWallMs") != original.get("physicalSmokeWallMs") or corrected.get("originalBestOfK") != original.get("bestOfK"):
        raise ValueError("Replay lost original wall cost or best-of-k evidence")
    base = [r for r in results if r["condition"] == "base"]
    gained = [r for r in results if r["condition"] == "channel_gain" and r["arm"] == "mlp_base_cache"]
    if not base or len(base) != len(gained) or sum(r["timing"]["end_to_end_ms"] for r in base) <= 0:
        raise ValueError("Replay lacks matched base/gain timing")
    derived = max(1, math.ceil(sum(r["timing"]["end_to_end_ms"] for r in gained) / sum(r["timing"]["end_to_end_ms"] for r in base)))
    if derived != k:
        raise ValueError("Replayed timings change k")
    best = []
    for baseline in base:
        samples = sorted([r for r in results if r["taskId"] == baseline["taskId"] and r["condition"] in ("base", "base_matched_best_of_k")], key=lambda r: r["sampleIndex"])
        if [r["sampleIndex"] for r in samples] != list(range(k)):
            raise ValueError("Replay changed existing best-of-k samples")
        winner = max(samples, key=lambda r: sum(c.get("passed") is True for t in r["publicReceipt"]["tasks"] for c in t["checks"]))
        best.append({"taskId": baseline["taskId"], "k": k, "selectedId": winner["id"], "selectedSourceSha256": digest(winner["source"].encode()),
                     "actualComputeMs": sum(r["timing"]["end_to_end_ms"] for r in samples),
                     "transformComputeMs": next(r for r in gained if r["taskId"] == baseline["taskId"])["timing"]["end_to_end_ms"]})
    if corrected.get("bestOfK") != best:
        raise ValueError("Replayed best-of-k ranking/cost is not reproducible from existing public samples")
    return corrected


def build_report(smoke, provenance, attempts, selection, selection_provenance, label, integration_probes=(), public_replay=None, replay_provenance=None):
    run = unpack(smoke)
    if provenance.get("warnings"):
        run["status"] = "smoke_incomplete"
    raw_requests = run["requests"]
    corrected = validate_reporting_replay(smoke, provenance, public_replay) if public_replay is not None else None
    if corrected is not None:
        run = {**run, "requests": corrected["results"]}
    requests = [request_summary(r) for r in run["requests"]]
    if corrected is not None:
        for request, original in zip(requests, raw_requests):
            request["originalPublicOutcome"] = request_summary(original)["publicOutcome"]
            request["originalVerifierMs"] = original["timing"]["verifier_ms"]
            request["originalAttributedEndToEndMs"] = original["timing"]["end_to_end_ms"]
    bases = {r["taskId"]: r for r in requests if r["condition"] == "base"}
    for r in requests:
        base = bases.get(r["taskId"])
        actual, baseline = r["timing"].get("end_to_end_ms"), (base or {}).get("timing", {}).get("end_to_end_ms")
        r["descriptiveMatchedBaseOverheadFraction"] = actual / baseline - 1 if base and number(actual) and number(baseline) and baseline > 0 else None
    grouped = {}
    for r in requests:
        grouped.setdefault((r["condition"], r["arm"]), []).append(r)
    groups = [{"condition": condition, "arm": arm, "requests": len(rows),
               "displayLabel": "additional base samples" if condition == "base_matched_best_of_k" else condition,
               "sampleScope": "additional_samples_only" if condition == "base_matched_best_of_k" else "individual_requests",
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
    best_of_k = corrected if corrected is not None else summary
    requests_by_id = {r["id"]: r for r in requests}
    best_tasks = []
    for task in best_of_k.get("bestOfK", []):
        outcome = requests_by_id.get(task.get("selectedId"), {}).get("publicOutcome")
        best_tasks.append({**task, "selectedPublicPassed": outcome == "passed" if outcome in ("passed", "failed") else None,
                           "fullSampleComputeMs": task.get("actualComputeMs")})
    preparations = [{k: v for k, v in p.items() if k != "memory"} | {"memory": compact_memory(p.get("memory", {}))} for p in run["preparation"]]
    probes, seen_probes = [], set()
    for value, source in integration_probes:
        identity = source["sha256"] or source["path"]
        if identity not in seen_probes:
            probes.append(summarize_probe(value, source))
            seen_probes.add(identity)
    return {"schema": SCHEMA, "label": label, "evidenceClass": "descriptive_smoke_only",
            "inputs": {"smoke": provenance, "selection": selection_provenance, "publicReplay": replay_provenance},
            "publicReplay": ({"status": public_replay["status"], "generation": public_replay["generation"], "verifier": public_replay["verifier"],
                              "sealSha256": public_replay["sealSha256"], "receiptSha256": public_replay.get("receiptSha256"),
                              "replayPhysicalWallMs": public_replay.get("replayPhysicalWallMs"), "provenanceStatement": public_replay.get("provenanceStatement"),
                              "reportValidation": "Original raw file/runtime/receipt binding, preserved generation/non-verifier timing and diagnostics, public identities, unchanged k and existing-sample reranking; full seal/code validation belongs to the execution-stage validator."}
                             if corrected is not None else None),
            "smoke": {"status": run["status"], "completedRequests": len(requests), "observedTasks": len({r["taskId"] for r in requests}), "errors": run["errors"]},
            "attempts": {"suppliedUniqueAttempts": len(attempt_rows), "failedAttempts": sum(a["failed"] for a in attempt_rows), "records": attempt_rows},
            "groups": groups, "requests": requests, "sameGainPairs": pairs,
            "cacheDiagnostics": run["diagnostics"], "resetDiagnostics": run["resetDiagnostics"], "preparation": preparations,
            "integrationProbes": probes,
            "costs": {"coldLoads": run["coldLoads"], "physicalSmokeWallMs": summary.get("physicalSmokeWallMs"),
                      "actualPreparationMs": stats([p.get("actualPreparationMs") for p in preparations]),
                      "completedPhysicalRequestMs": stats([r["physicalRequestMs"] for r in requests]),
                      "completedVerifierMs": stats([r["timing"].get("verifier_ms") for r in raw_requests]),
                      "replayedVerifierMs": stats([r["timing"].get("verifier_ms") for r in requests]) if corrected is not None else None,
                      "cacheDiagnosticMs": stats([d.get("diagnosticMs") for d in run["diagnostics"]]),
                      "resetDiagnosticMs": stats([d.get("resetDiagnosticMs") for d in run["resetDiagnostics"]]),
                      "attributedTimingBreakdownMs": {key: stats([r["timing"].get(key) for r in requests]) for key in EXTRA_TIMING_FIELDS},
                      "selectionGpuMsCharged": summary.get("selectionGpuMsCharged"),
                      "bestOfK": {"status": "recorded" if "bestOfK" in best_of_k else "pending", "k": best_of_k.get("k"), "tasks": best_tasks},
                      "originalBestOfK": summary.get("bestOfK") if corrected is not None else None,
                      "eta": summary.get("eta") if run["status"] == "smoke_complete" else None},
            "selection": selected, "confirmation": {"status": "not_evaluated" if selected.get("status") == "selection_not_admitted" else "not_established_by_these_inputs", "statisticalConfirmationClaim": False},
            "limitations": [
                "Public smoke checks are descriptive observations, not held-out semantic confirmation, selection evidence, or a test of the frozen success criteria.",
                "When public replay is supplied, request scores, attributed verifier/E2E timings and best-of-k reflect the repaired verifier over unchanged samples. Original physical smoke wall, cold load and original verifier costs remain original observations; replay wall/browser startup are separate incurred costs, not replacements for historical compute. The retained ETA is the original smoke forecast, not recomputed from replay.",
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
    if report["publicReplay"]:
        statement = report["publicReplay"].get("provenanceStatement") or ""
        if statement.lower().startswith("mixed provenance:"):
            statement = statement.split(":", 1)[1].lstrip()
        lines[5:5] = ["Displayed public scores, attributed verifier/E2E timings and best-of-k use the separately recorded repaired-verifier replay over unchanged original samples.",
                      f"Mixed provenance: {statement}", ""]
    for g in report["groups"]:
        o = g["publicOutcomes"]
        overhead = g["descriptiveMatchedBaseOverheadFraction"]["mean"]
        change = f"{100 * overhead:+.2f}%" if number(overhead) else "not recorded"
        lines.append(f"| {cell(g['displayLabel'])} / {cell(g['arm'])} | {g['requests']} | {o['passed']} / {o['failed']} / {o['unmeasured']} | {fmt(g['tokens']['mean'])} | {fmt(g['attributedEndToEndMs']['mean'])} | {fmt(g['physicalRequestMs']['mean'])} | {change} |")
    lines += ["", "The additional-base-samples row summarizes only extra generated samples. Selected best-of-k public outcomes and total compute across all k samples appear below."]
    lines += ["", "## Costs and completeness", "", f"Physical smoke wall: {fmt(report['costs']['physicalSmokeWallMs'])} ms.", ""]
    for key in ("actualPreparationMs", "completedPhysicalRequestMs", "completedVerifierMs", "cacheDiagnosticMs", "resetDiagnosticMs"):
        s = report["costs"][key]
        lines.append(f"- {key}: {fmt(s['sum'])} ms ({s['observed']} recorded, {s['missing']} missing).")
    for load in report["costs"]["coldLoads"]:
        lines.append(f"- Cold model load: {fmt(load['coldModelLoadMs'])} ms; cold adapter load: {fmt(load['coldAdapterLoadMs'])} ms.")
    if report["publicReplay"]:
        replay = report["publicReplay"]
        lines += [f"- Original completed verifier cost remains {fmt(report['costs']['completedVerifierMs']['sum'])} ms.",
                  f"- Separate replay wall: {fmt(replay['replayPhysicalWallMs'])} ms; browser startup: {fmt(replay['verifier'].get('browserStartupMs'))} ms; replayed request-verifier intervals: {fmt(report['costs']['replayedVerifierMs']['sum'])} ms."]
    lines += [f"- Best-of-k: {report['costs']['bestOfK']['status']}; k={report['costs']['bestOfK']['k']}."]
    for task in report["costs"]["bestOfK"]["tasks"]:
        lines.append(f"- {cell(task['taskId'])}: selected `{cell(task.get('selectedId'))}`; selected public pass={json.dumps(task.get('selectedPublicPassed'))}; full compute across all {task.get('k')} base samples {fmt(task.get('fullSampleComputeMs'))} ms; transform {fmt(task.get('transformComputeMs'))} ms.")
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
    for role, source in report["inputs"].items():
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
    parser.add_argument("--public-replay", help="Completed sealed public replay; requires --smoke to be the original complete JSON receipt")
    parser.add_argument("--integration-probe", action="append", default=[], help="Optional diagnostic receipt; repeat for separate probes")
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--label", default="Native smoke report")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    inputs = {Path(p).resolve() for p in [args.smoke, *args.attempt, *args.integration_probe, *([args.selection] if args.selection else []), *([args.public_replay] if args.public_replay else [])]}
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
    replay, replay_source = load(args.public_replay) if args.public_replay else (None, None)
    report = build_report(smoke, source, attempts, selection, selection_source, args.label, probes, replay, replay_source)
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
