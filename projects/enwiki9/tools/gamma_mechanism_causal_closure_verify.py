#!/usr/bin/env python3
"""Verify the causal/state closure paired with a frozen Gamma Mechanism IR."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


IR_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir.v1"
CLOSURE_SCHEMA = "gamma.enwiki9.gamma-mechanism-causal-closure.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-causal-closure-verification.v1"


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def regular_file(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SystemExit(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def unique_by(values: Any, key: str, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(values, list):
        errors.append(f"{label} must be an array")
        return result
    for index, value in enumerate(values):
        if not isinstance(value, dict) or not isinstance(value.get(key), str) or not value[key]:
            errors.append(f"{label}[{index}] lacks {key}")
            continue
        identifier = value[key]
        if identifier in result:
            errors.append(f"{label} contains duplicate {key} {identifier}")
            continue
        result[identifier] = value
    return result


def id_set(values: Any, label: str, errors: list[str]) -> set[str]:
    if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
        errors.append(f"{label} must be an array of nonempty strings")
        return set()
    result = set(values)
    if len(result) != len(values):
        errors.append(f"{label} contains duplicate identifiers")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ir", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    ir_path = regular_file(args.ir, "IR")
    closure_path = regular_file(args.closure, "closure")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt path already exists")
    ir_raw = ir_path.read_bytes()
    closure_raw = closure_path.read_bytes()
    try:
        ir = json.loads(ir_raw.decode("utf-8"))
        closure = json.loads(closure_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"JSON parse failure: {exc}") from exc
    if not isinstance(ir, dict) or not isinstance(closure, dict):
        raise SystemExit("IR and closure must be JSON objects")

    errors: list[str] = []
    checks = {
        "identity_pass": True,
        "event_order_pass": True,
        "source_closure_pass": True,
        "state_closure_pass": True,
        "arm_authority_pass": True,
        "causal_use_pass": True,
        "matched_control_access_pass": True,
        "raw_treatment_posterior_isolation_pass": True,
        "join_closure_pass": True,
    }

    if ir.get("schema") != IR_SCHEMA or closure.get("schema") != CLOSURE_SCHEMA:
        errors.append("unexpected IR or closure schema")
        checks["identity_pass"] = False
    if ir.get("mechanism_id") != closure.get("mechanism_id"):
        errors.append("mechanism identity mismatch")
        checks["identity_pass"] = False
    if closure.get("operational_status") != "design_only" or closure.get("execution_authority") is not False:
        errors.append("closure must remain design-only with no execution authority")
        checks["identity_pass"] = False
    declared_ir = Path(str(closure.get("mechanism_ir", "")))
    if declared_ir != args.ir and declared_ir.resolve() != ir_path:
        errors.append("closure mechanism_ir path does not identify supplied IR")
        checks["identity_pass"] = False

    events = unique_by(closure.get("events"), "id", "events", errors)
    ordered_events = closure.get("events") if isinstance(closure.get("events"), list) else []
    ordinals = [event.get("ordinal") for event in ordered_events if isinstance(event, dict)]
    if ordinals != list(range(len(ordered_events))) or len(events) != len(ordered_events):
        errors.append("events must be unique and listed in contiguous ordinal order")
        checks["event_order_pass"] = False
    event_ordinals = {identifier: value.get("ordinal") for identifier, value in events.items()}

    ir_sources = unique_by(ir.get("information_sources"), "id", "IR information_sources", errors)
    sources = unique_by(closure.get("source_availability"), "source_id", "source_availability", errors)
    if set(sources) != set(ir_sources):
        errors.append("source availability does not close the IR information-source set")
        checks["source_closure_pass"] = False
    for source_id, source in sources.items():
        available = source.get("available_at_event")
        first_use = source.get("first_use_event")
        if available not in events or first_use not in events:
            errors.append(f"source {source_id} names an unknown availability/use event")
            checks["source_closure_pass"] = False
        elif event_ordinals[available] > event_ordinals[first_use]:
            errors.append(f"source {source_id} is used before decoder-visible availability")
            checks["causal_use_pass"] = False

    ir_reads = unique_by(ir.get("state_reads"), "id", "IR state_reads", errors)
    ir_writes = unique_by(ir.get("state_writes"), "id", "IR state_writes", errors)
    ir_state_ids = set(ir_reads) | set(ir_writes)
    roles = unique_by(closure.get("state_roles"), "state_id", "state_roles", errors)
    if set(roles) != ir_state_ids:
        errors.append("state roles do not close the union of IR read and write states")
        checks["state_closure_pass"] = False
    for state_id, role in roles.items():
        ir_state = ir_reads.get(state_id, ir_writes.get(state_id, {}))
        if role.get("lifetime") != ir_state.get("lifetime"):
            errors.append(f"state {state_id} lifetime differs from IR")
            checks["state_closure_pass"] = False

    arms = unique_by(closure.get("arms"), "arm", "arms", errors)
    expected_arms = {"P", "K", "D", "M", "R", "S"} if isinstance(ir.get("mixture"), dict) and ir.get("revision", 0) >= 2 else {"P", "K", "D", "R", "S"}
    if set(arms) != expected_arms:
        errors.append("arm set does not match the IR treatment model")
        checks["arm_authority_pass"] = False

    arm_write_sets: dict[str, set[str]] = {}
    arm_read_sets: dict[str, set[str]] = {}
    source_use_ordinals: dict[str, list[int]] = {source_id: [] for source_id in sources}
    for arm_id, arm in arms.items():
        read_union: set[str] = set()
        write_union: set[str] = set()
        accesses = arm.get("event_access")
        if not isinstance(accesses, list) or not accesses:
            errors.append(f"arm {arm_id} lacks event access")
            checks["arm_authority_pass"] = False
            continue
        seen_events: set[str] = set()
        for index, access in enumerate(accesses):
            if not isinstance(access, dict):
                errors.append(f"arm {arm_id} event_access[{index}] is not an object")
                checks["arm_authority_pass"] = False
                continue
            event_id = access.get("event")
            if event_id not in events or event_id in seen_events:
                errors.append(f"arm {arm_id} has unknown or duplicate event {event_id}")
                checks["event_order_pass"] = False
                continue
            seen_events.add(event_id)
            used_sources = id_set(access.get("source_ids"), f"arm {arm_id}/{event_id} source_ids", errors)
            reads = id_set(access.get("read_state_ids"), f"arm {arm_id}/{event_id} read_state_ids", errors)
            writes = id_set(access.get("write_state_ids"), f"arm {arm_id}/{event_id} write_state_ids", errors)
            if not used_sources <= set(sources) or not reads <= set(ir_reads) or not writes <= set(ir_writes):
                errors.append(f"arm {arm_id}/{event_id} accesses an undeclared source or state")
                checks["state_closure_pass"] = False
            for source_id in used_sources & set(sources):
                source_use_ordinals[source_id].append(event_ordinals[event_id])
                available = sources[source_id].get("available_at_event")
                if available in event_ordinals and event_ordinals[available] > event_ordinals[event_id]:
                    errors.append(f"arm {arm_id} uses source {source_id} before availability")
                    checks["causal_use_pass"] = False
            for state_id in reads & set(roles):
                if arm_id not in id_set(roles[state_id].get("readable_arms"), f"state {state_id} readable_arms", errors):
                    errors.append(f"arm {arm_id} is not authorized to read state {state_id}")
                    checks["arm_authority_pass"] = False
            for state_id in writes & set(roles):
                if arm_id not in id_set(roles[state_id].get("writable_arms"), f"state {state_id} writable_arms", errors):
                    errors.append(f"arm {arm_id} is not authorized to write state {state_id}")
                    checks["arm_authority_pass"] = False
            read_union |= reads
            write_union |= writes
        arm_read_sets[arm_id] = read_union
        arm_write_sets[arm_id] = write_union

    for source_id, uses in source_use_ordinals.items():
        if not uses:
            errors.append(f"source {source_id} is never used by an arm")
            checks["source_closure_pass"] = False
            continue
        declared_first = sources[source_id].get("first_use_event")
        if declared_first in event_ordinals and min(uses) != event_ordinals[declared_first]:
            errors.append(f"source {source_id} first-use declaration is not exact")
            checks["causal_use_pass"] = False

    matched = [arm_write_sets.get(arm_id, set()) for arm_id in ("K", "M", "R", "S") if arm_id in arms]
    if matched and any(value != matched[0] for value in matched[1:]):
        errors.append("K/M/R/S write sets are not matched")
        checks["matched_control_access_pass"] = False
    matched_reads = [arm_read_sets.get(arm_id, set()) for arm_id in ("K", "M", "R", "S") if arm_id in arms]
    if matched_reads and any(value != matched_reads[0] for value in matched_reads[1:]):
        errors.append("K/M/R/S read sets are not matched")
        checks["matched_control_access_pass"] = False

    posterior_ids = {state_id for state_id, role in roles.items() if role.get("authority") == "mechanism_persistent"}
    if "D" in arms and arm_write_sets.get("D", set()) & posterior_ids:
        errors.append("raw D writes persistent mixture state")
        checks["raw_treatment_posterior_isolation_pass"] = False
    if "M" in arms and not posterior_ids <= arm_write_sets.get("M", set()):
        errors.append("mixed M does not write every declared persistent mixture state")
        checks["raw_treatment_posterior_isolation_pass"] = False

    join = closure.get("join") if isinstance(closure.get("join"), dict) else {}
    if join.get("event") not in events:
        errors.append("join names an unknown event")
        checks["join_closure_pass"] = False
    retain = id_set(join.get("retain_state_ids"), "join retain_state_ids", errors)
    discard = id_set(join.get("discard_state_ids"), "join discard_state_ids", errors)
    if retain & discard or not (retain | discard) <= set(roles):
        errors.append("join retain/discard sets overlap or reference unknown states")
        checks["join_closure_pass"] = False
    authoritative = {state_id for state_id, role in roles.items() if role.get("authority") in {"authoritative_parent", "authoritative_coder", "mechanism_persistent"}}
    ephemeral = {state_id for state_id, role in roles.items() if role.get("authority") in {"mechanism_ephemeral", "causal_evidence"}}
    if not authoritative <= retain or not ephemeral <= discard:
        errors.append("join does not retain all authoritative state and discard all ephemeral/evidence state")
        checks["join_closure_pass"] = False
    pairs = join.get("forbidden_copy_pairs")
    expected_pairs = {(source, target) for source in ephemeral for target in authoritative if roles[target].get("authority") == "authoritative_parent"}
    actual_pairs: set[tuple[str, str]] = set()
    if isinstance(pairs, list):
        for pair in pairs:
            if isinstance(pair, dict) and isinstance(pair.get("from"), str) and isinstance(pair.get("to"), str):
                actual_pairs.add((pair["from"], pair["to"]))
    if not expected_pairs <= actual_pairs:
        errors.append("join does not forbid every ephemeral/evidence to authoritative-parent copy")
        checks["join_closure_pass"] = False

    output = {
        "schema": OUTPUT_SCHEMA,
        "mechanism_id": str(ir.get("mechanism_id", "invalid")),
        "verified": not errors,
        "errors": errors,
        "mechanism_ir_sha256": sha256_bytes(ir_raw),
        "closure_sha256": sha256_bytes(closure_raw),
        "checks": checks,
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(json_bytes(output))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if output["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
