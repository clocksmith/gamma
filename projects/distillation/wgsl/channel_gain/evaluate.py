"""Decision from hash-bound experiment receipts. Missing evidence never passes.

This reducer neither generates shaders nor opens oracle files. Its input must be
receipts from the frozen run; unit fixtures are not experiment evidence.
"""
from __future__ import annotations
import json
import math
import re
from .decision import paired_sign, gap_closure


def evaluate_confirmation(protocol, evidence):
    expected = set(evidence["taskIds"])
    if len(expected) != protocol["populations"]["confirmationFamilies"]:
        raise ValueError("confirmation task population incomplete or duplicated")
    if len(evidence["taskIds"]) != len(expected):
        raise ValueError("duplicate tasks")
    required = {"base", "base_matched_best_of_k", "trained_seed47_adapter",
                "channel_gain", "shuffled_context", "random_z", "permuted_gain"}
    arms = evidence.get("arms", {})
    if set(arms) != set(protocol["cacheArms"]):
        raise ValueError("both frozen cache arms required")
    for name in ("protocolSha256", "selectionLockSha256", "submissionLockSha256",
                 "runtimeReceiptSha256", "oracleReceiptSha256"):
        if not isinstance(evidence.get(name), str) or not re.fullmatch(r"[a-f0-9]{64}", evidence[name]):
            raise ValueError(f"missing receipt identity: {name}")
    criteria = protocol["criteria"]
    gain_hashes = evidence.get("gainHashes", {})
    if set(gain_hashes) != set(protocol["cacheArms"]):
        raise ValueError("frozen gain identities required for both arms")
    first, second = [gain_hashes[a] for a in protocol["cacheArms"]]
    expected_gains = {f"{t}/{c}" for t in expected for c in ("channel_gain", "shuffled_context", "random_z", "permuted_gain")}
    if first != second or set(first) != expected_gains or any(not isinstance(v,str) or not re.fullmatch(r"[a-f0-9]{64}",v) for v in first.values()):
        raise ValueError("cache arms must reuse identical frozen gains for every task/control")
    result = {"cacheArms": {}, "allProjections": "not_applicable"}
    for arm_id, controls in arms.items():
        if set(controls) != required:
            raise ValueError("all controls and comparators required")
        for name, rows in controls.items():
            if set(rows) != expected:
                raise ValueError(f"task identities differ: {arm_id}/{name}")
            for row in rows.values():
                for flag in ("semanticPass", "publicPass"):
                    if type(row.get(flag)) is not bool:
                        raise ValueError("explicit pass outcomes required")
                if not isinstance(row.get("endToEndMs"), (int,float)) or not math.isfinite(row["endToEndMs"]) or row["endToEndMs"] <= 0:
                    raise ValueError("measured request latency required")
        outcomes = {name: {task: row["semanticPass"] for task, row in rows.items()}
                    for name, rows in controls.items()}
        count = {name: sum(rows.values()) for name, rows in outcomes.items()}
        comparisons = {name: paired_sign(outcomes["channel_gain"], outcomes[name],
                       criteria["promptDependence"]["minimumDiscordantTasks"])
                       for name in ("shuffled_context", "random_z", "permuted_gain")}
        gap = gap_closure(count["channel_gain"], count["base_matched_best_of_k"],
                          count["trained_seed47_adapter"])
        total = {name: sum(r["endToEndMs"] for r in rows.values())
                 for name, rows in controls.items()}
        overhead = total["channel_gain"] / total["base"] - 1
        wrong = {name: sum(r["publicPass"] and not r["semanticPass"] for r in rows.values())
                 for name, rows in controls.items()}
        prompt_status = "pass" if all(comparisons[n]["status"] == "pass" for n in criteria["promptDependence"]["requiredControls"]) else "not_confirmed"
        memory = evidence.get("peakTransformBytes", {}).get(arm_id)
        memory_ok = isinstance(memory, int) and 0 <= memory <= criteria["maximumPerRequestTransformBytes"]
        serving_ok = overhead <= criteria["maximumAddedEndToEndLatencyFraction"] and memory_ok
        cache = evidence.get("cacheDiagnostics", {}).get(arm_id)
        cache_ok = isinstance(cache, dict) and cache.get("measured") is True and cache.get("sameTeacherForcedPrefix") is True
        setup = evidence.get("setup", {})
        hours = setup.get("seed47RecordedGpuHours")
        spent = setup.get("selectionGpuHours")
        budget_ok = isinstance(hours, (int,float)) and hours > 0 and isinstance(spent, (int,float)) and 0 <= spent <= hours * criteria["selectionGpuHoursFractionOfSeed47Sft"]
        setup_ok = setup.get("offlineTrainingSteps") == 0 and budget_ok
        checks = {"promptDependence": prompt_status == "pass", "gapClosure": gap["status"] == "pass",
                  "setup": setup_ok, "serving": serving_ok,
                  "wrongAcceptances": wrong["channel_gain"] - wrong["base"] <= criteria["maximumAdditionalWrongAcceptancesVsBase"],
                  "cacheMeasured": cache_ok}
        result["cacheArms"][arm_id] = {"semanticPassCounts": count, "pairedComparisons": comparisons,
            "gapClosure": gap, "addedEndToEndLatencyFraction": overhead, "wrongAcceptances": wrong,
            "checks": checks, "decision": "confirmed" if all(checks.values()) else "not_confirmed"}
    result["decision"] = result["cacheArms"][protocol["selection"]["primaryCacheArm"]]["decision"]
    return result

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--protocol',required=True);p.add_argument('--evidence',required=True)
    a=p.parse_args()
    with open(a.protocol) as f: protocol=json.load(f)
    with open(a.evidence) as f: evidence=json.load(f)
    print(json.dumps(evaluate_confirmation(protocol,evidence),indent=2,allow_nan=False))
