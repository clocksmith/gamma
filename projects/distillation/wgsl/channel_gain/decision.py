"""Frozen decision arithmetic; does not execute models or select on held-out checks."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def paired_sign(candidate, control, minimum_discordant=5):
    if set(candidate) != set(control) or not candidate:
        raise ValueError("paired task identities must match and be nonempty")
    if any(type(v) is not bool for v in [*candidate.values(), *control.values()]):
        raise ValueError("pass outcomes must be explicit booleans")
    wins = sum(candidate[k] and not control[k] for k in candidate)
    losses = sum(control[k] and not candidate[k] for k in candidate)
    discordant = wins + losses
    p = sum(math.comb(discordant, k) for k in range(wins, discordant + 1)) / (2 ** discordant)
    status = "underpowered" if discordant < minimum_discordant else "pass" if p < .05 else "fail"
    return {"wins": wins, "losses": losses, "discordant": discordant, "pOneSided": p, "status": status}


def gap_closure(candidate_passes, base_passes, adapter_passes):
    gap = adapter_passes - base_passes
    if gap < 4:
        return {"gapTasks": gap, "fraction": None, "status": "uninformative"}
    fraction = (candidate_passes - base_passes) / gap
    return {"gapTasks": gap, "fraction": fraction, "status": "pass" if fraction >= .5 else "fail"}


def select_public_sample(samples):
    """Accept only public receipts. Earliest sample wins a tie, never hidden checks."""
    if not samples:
        raise ValueError("no samples")
    scores = []
    for row in samples:
        if set(row) != {"sampleId", "publicChecks"}:
            raise ValueError("sample selection accepts public checks only")
        checks = row["publicChecks"]
        if not isinstance(checks, list) or not checks:
            raise ValueError("public check receipts required")
        if any(set(c) != {"id", "passed", "visibility"} or c["visibility"] != "public" or type(c["passed"]) is not bool for c in checks):
            raise ValueError("hidden or malformed check rejected")
        scores.append(sum(c["passed"] for c in checks))
    return samples[max(range(len(samples)), key=lambda i: (scores[i], -i))]["sampleId"]


def freeze_confirmation(path, *, protocol_hash, task_hash, oracle_hash, selection_hash, candidate, submissions):
    """Write-once lock must precede any held-out oracle execution."""
    if not submissions or any(not isinstance(v, str) or len(v) != 64 for v in submissions.values()):
        raise ValueError("every task/arm needs its submitted source SHA-256")
    for value in (protocol_hash, task_hash, oracle_hash, selection_hash):
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError("exact immutable input hashes required")
    record = {"schema": "gamma.wgsl-channel-gain-confirmation-lock/v1", "protocolHash": protocol_hash, "taskHash": task_hash, "oracleHash": oracle_hash, "selectionHash": selection_hash, "candidate": candidate, "submissions": submissions}
    record["lockHash"] = canonical_hash(record)
    with Path(path).open("x", encoding="utf8") as out:
        json.dump(record, out, indent=2, allow_nan=False)
        out.write("\n")
    return record


def smoke_eta(measured_request_ms, remaining_requests):
    if not measured_request_ms or remaining_requests < 0 or any(not math.isfinite(v) or v <= 0 for v in measured_request_ms):
        raise ValueError("positive measured model request timings required")
    return {"remainingRequests": remaining_requests, "meanSeconds": sum(measured_request_ms) / len(measured_request_ms) * remaining_requests / 1000, "observedRangeSeconds": [min(measured_request_ms) * remaining_requests / 1000, max(measured_request_ms) * remaining_requests / 1000], "basis": "measured_model_smoke_requests_excluding_cold_load; not an engineering estimate"}
