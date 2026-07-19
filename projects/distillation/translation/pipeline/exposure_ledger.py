"""Clocksmith exposure-ledger hashing and fail-closed validation."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


EXPOSURE_LEDGER_SCHEMA = "clocksmith.exposure-ledger/v1"
EXPOSURE_LEDGER_SCHEMA_SHA256 = "sha256:5262a2ed29dd97d163c49f21ab69b54103dc524c68959dc0561defb128fdc038"
EXPOSURE_ROLES = frozenset({"training", "development", "selection", "confirmation", "one_use_promotion"})


def canonicalize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            token = "NaN"
        elif value > 0:
            token = "Infinity"
        else:
            token = "-Infinity"
        return {"$number": token}
    if isinstance(value, list):
        return [canonicalize(entry) for entry in value]
    if isinstance(value, dict):
        return {key: canonicalize(value[key]) for key in sorted(value)}
    return value


def hash_evidence(value: Any) -> str:
    payload = json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def find_nonfinite(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, float) and not math.isfinite(value):
        findings.append(path)
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            findings.extend(find_nonfinite(entry, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, entry in value.items():
            findings.extend(find_nonfinite(entry, f"{path}.{key}"))
    return findings


def seal_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sealed: list[dict[str, Any]] = []
    previous_event_hash: str | None = None
    for sequence, source in enumerate(events):
        core = {**source, "sequence": sequence, "previousEventHash": previous_event_hash}
        event_hash = hash_evidence(core)
        sealed.append({**core, "eventHash": event_hash})
        previous_event_hash = event_hash
    return sealed


def validate_ledger(ledger: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if ledger.get("schema") != EXPOSURE_LEDGER_SCHEMA:
        reasons.append("exposure ledger schema mismatch")
    if ledger.get("schemaSha256") != EXPOSURE_LEDGER_SCHEMA_SHA256:
        reasons.append("exposure ledger schema digest mismatch")
    repository = ledger.get("repository")
    previous_event_hash: str | None = None
    event_ids: set[str] = set()
    for index, event in enumerate(ledger.get("events", [])):
        event_id = event.get("eventId")
        if event.get("sequence") != index:
            reasons.append(f"events[{index}].sequence mismatch")
        if event.get("repository") != repository:
            reasons.append(f"events[{index}].repository mismatch")
        if not event_id or event_id in event_ids:
            reasons.append(f"events[{index}].eventId must be unique")
        event_ids.add(str(event_id))
        if event.get("previousEventHash") != previous_event_hash:
            reasons.append(f"events[{index}].previousEventHash mismatch")
        core = {key: value for key, value in event.items() if key != "eventHash"}
        if hash_evidence(core) != event.get("eventHash"):
            reasons.append(f"events[{index}].eventHash mismatch")
        if find_nonfinite(event):
            reasons.append(f"events[{index}] contains nonfinite evidence")
        if event.get("role") is not None and event.get("role") not in EXPOSURE_ROLES:
            reasons.append(f"events[{index}].role is invalid")
        previous_event_hash = event.get("eventHash")
    return reasons
