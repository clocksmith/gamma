"""CPU-only final quality/cost report from assembled confirmation evidence.

Run with python3 -m projects.distillation.wgsl.channel_gain.report_confirmation.
This module never opens oracle files, generates samples, or controls a GPU.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from .evaluate import evaluate_confirmation
from .environment_reporting import environment_markdown, load_environment


def build_report(protocol, evidence, environment=None):
    result = evaluate_confirmation(protocol, evidence)
    quality = {}
    for arm, outcome in result["cacheArms"].items():
        conditions = evidence["arms"][arm]
        quality[arm] = {
            "semanticPassCounts": outcome["semanticPassCounts"],
            "publicPassCounts": {name: sum(row["publicPass"] for row in rows.values()) for name, rows in conditions.items()},
            "hiddenPassCounts": {name: sum(row["hiddenPass"] for row in rows.values()) for name, rows in conditions.items()},
            "pairedComparisons": outcome["pairedComparisons"],
            "gapClosure": outcome["gapClosure"],
            "wrongAcceptances": outcome["wrongAcceptances"],
            "qualityCriteria": {key: outcome["checks"][key] for key in ("promptDependence", "gapClosure", "wrongAcceptances")},
            "qualityCriteriaAllMet": all(outcome["checks"][key] for key in ("promptDependence", "gapClosure", "wrongAcceptances")),
            "addedLatencyFractionRatioOfTotals": outcome["addedEndToEndLatencyFraction"],
            "latencyThresholdMet": outcome["addedEndToEndLatencyFraction"] <= protocol["criteria"]["maximumAddedEndToEndLatencyFraction"],
            "memoryCriterionStatus": evidence["memory"][arm]["memoryCriterionStatus"],
            "cacheMeasured": outcome["checks"]["cacheMeasured"],
            "originalJointDecision": outcome["decision"],
        }
    return {"schema": "gamma.channel-gain-confirmation-report/v1", "taskCount": len(evidence["taskIds"]),
            "confirmationEvaluated": True, "primaryCacheArm": protocol["selection"]["primaryCacheArm"],
            "originalJointDecision": result["decision"], "quality": quality,
            "setupEfficiency": evidence["setup"], "costs": evidence["costs"], "memory": evidence["memory"],
            "allProjections": "not_applicable", "evaluatorResult": result,
            "evidenceProvenance": evidence["provenance"], "limitations": evidence["limitations"],
            "environment": environment or {"provided": False, "isolationQualification": "unknown"},
            "decisionBoundary": "Quality outcomes are reported independently of setup efficiency and memory qualification. qualityCriteriaAllMet means the existing prompt-dependence, gap-closure and wrong-acceptance criteria all met; it is not a replacement for the original joint decision. Underpowered and uninformative comparisons remain so."}


def fmt(value):
    return f"{value:,.3f}" if isinstance(value, (int, float)) else "not recorded"


def markdown(report):
    lines = ["# Channel-gain confirmation results", "",
             f"Confirmation evaluated {report['taskCount']} tasks across both cache arms. Original joint decision: **{report['originalJointDecision']}**.",
             "Quality results and costs are separate below. The original 1% setup-efficiency target remains scored; the prior admission-stop outcome is preserved.", ""]
    for arm, q in report["quality"].items():
        lines += [f"## {arm}", "", "| Condition | Public pass | Hidden pass | Semantic pass (both) | Wrong acceptances | Attributed total ms |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for condition, count in q["semanticPassCounts"].items():
            lines.append(f"| {condition} | {q['publicPassCounts'][condition]} | {q['hiddenPassCounts'][condition]} | {count}/{report['taskCount']} | {q['wrongAcceptances'][condition]} | {fmt(report['costs']['attributedEndToEndMsByArm'][arm][condition])} |")
        lines += ["", "| Gain comparison | Wins | Losses | Discordant tasks | One-sided exact p | Status |", "| --- | ---: | ---: | ---: | ---: | --- |"]
        for name, comparison in q["pairedComparisons"].items():
            lines.append(f"| {name} | {comparison['wins']} | {comparison['losses']} | {comparison['discordant']} | {comparison['pOneSided']:.8g} | {comparison['status']} |")
        gap = q["gapClosure"]
        lines += ["", f"Adapter-minus-matched-base gap: {gap['gapTasks']} tasks; closure fraction: {gap['fraction']}; status: **{gap['status']}**.",
                  f"Existing quality criteria: `{json.dumps(q['qualityCriteria'], sort_keys=True)}`. All met: **{q['qualityCriteriaAllMet']}**.",
                  f"Added latency: **{q['addedLatencyFractionRatioOfTotals']:.2%}**, calculated as total gain E2E / total same-prompt base E2E − 1. This is the evaluator's ratio of totals, not the mean of per-task percentages used in the smoke description.",
                  f"Memory criterion: **{q['memoryCriterionStatus']}**; maximum measured retained increment {report['memory'][arm]['maximumRetainedIncrementBytes']:,} bytes. An isolated incremental peak was not measured.",
                  f"Matched-best-of-k / gain attributed total-cost ratio: {report['costs']['bestOfKToTransformRatios'][arm]:.6f}. All k samples are charged, including the selected one.", ""]
    setup, costs = report["setupEfficiency"], report["costs"]
    lines += ["## Costs and evidence", "",
              f"Selection allocated time: {fmt(costs['selectionAllocatedGpuMs']/1000)} seconds. Historical SFT denominator: {fmt(setup['seed47RecordedGpuHours'])} GPU-hours ({setup['denominatorEvidence']}).",
              f"Selection/SFT ratio: **{setup['selectionEfficiencyRatio']:.4%}**; frozen target: **{setup['selectionTargetRatio']:.2%}**; target met: **{setup['selectionTargetMet']}**. Offline training steps: {setup['offlineTrainingSteps']}.",
              f"Unique confirmation generations: {costs['uniqueGeneratedRequests']}; total physical request time: {fmt(costs['uniquePhysicalRequestMs']/1000)} seconds; public verification {fmt(costs['uniquePublicVerifierMs']/1000)} seconds; confirmation verifier intervals {fmt(costs['confirmationVerifierMs']/1000)} seconds.",
              f"Preparation: {fmt(costs['preparationMs']/1000)} seconds; cache diagnostics: {fmt(costs['cacheDiagnosticMs']/1000)} seconds. These are separately attributed components, not additional amounts to add to physical stage wall.",
              f"Confirmation physical stage before receipt serialization: {fmt(costs['confirmationPhysicalStageBeforeReceiptMs']/1000 if costs['confirmationPhysicalStageBeforeReceiptMs'] is not None else None)} seconds.", ""]
    for stage in ("selectionTiming", "confirmationTiming"):
        lines.append(f"- {stage}: `{json.dumps(costs[stage], sort_keys=True)}`.")
    lines += [""] + environment_markdown(report["environment"])
    lines += ["", report["decisionBoundary"], "", "## Limits", ""] + [f"- {value}" for value in report["limitations"]]
    lines += ["", "## Input provenance", ""]
    for name, record in report["evidenceProvenance"]["files"].items():
        lines.append(f"- {name}: `{record['path']}`; SHA256 `{record['sha256']}`.")
    lines += [f"- Evidence adapter SHA256 `{report['evidenceProvenance']['adapterSourceSha256']}`.",
              "- All-projections: not applicable. No new model execution or oracle-input reads occur during report rebuilding."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("protocol", "evidence", "json-output", "markdown-output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--environment", help="Optional append-only environment JSONL history; descriptive only")
    args = parser.parse_args()
    protocol_bytes = Path(args.protocol).read_bytes()
    evidence_bytes = Path(args.evidence).read_bytes()
    evidence = json.loads(evidence_bytes)
    if evidence.get("schema") != "gamma.channel-gain-authenticated-confirmation-evidence/v1" or evidence["protocolSha256"] != hashlib.sha256(protocol_bytes).hexdigest():
        raise ValueError("Assembled evidence must match the supplied frozen protocol")
    # Receipts use JavaScript canonical JSON numbers. Verify with that same
    # serialization, avoiding Python's different 1.0/exponent spelling.
    verifier = """import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const value=JSON.parse(await readFile(process.argv[1],'utf8'));
const {evidenceSha256,...body}=value;
if(createHash('sha256').update(JSON.stringify(canonical(body))).digest('hex')!==evidenceSha256)throw Error('Assembled evidence checksum mismatch');
"""
    subprocess.run(["node", "--input-type=module", "-e", verifier, str(Path(args.evidence).resolve())], check=True, capture_output=True)
    environment = load_environment(args.environment, evidence) if args.environment else None
    report = build_report(json.loads(protocol_bytes), evidence, environment)
    report["evidenceFileSha256"] = hashlib.sha256(evidence_bytes).hexdigest()
    report["reporterSha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["environmentReporterSha256"] = hashlib.sha256(Path(__file__).with_name("environment_reporting.py").read_bytes()).hexdigest()
    inputs = {Path(args.protocol).resolve(), Path(args.evidence).resolve()}
    if args.environment:
        inputs.add(Path(args.environment).resolve())
    outputs = [Path(args.json_output).resolve(), Path(args.markdown_output).resolve()]
    if len(set(outputs)) != 2 or any(path in inputs or path.exists() for path in outputs):
        raise ValueError("Report output paths must be new, distinct files")
    for path, content in zip(outputs, (json.dumps(report, indent=2, allow_nan=False) + "\n", markdown(report))):
        with path.open("x") as output:
            output.write(content)
    print(json.dumps({"tasks": report["taskCount"], "originalJointDecision": report["originalJointDecision"], "qualityCriteriaAllMet": {arm: row["qualityCriteriaAllMet"] for arm, row in report["quality"].items()}}))


if __name__ == "__main__":
    main()
