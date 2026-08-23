#!/usr/bin/env python3
"""Offline verifier for managed-exclusive lease transition evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA = "managed-exclusive-lease-verification.v1"
LOG_SCHEMA = "managed-exclusive-lease-transition-log.v1"
LEASE_SCHEMA = "gamma.enwiki9.exclusive-full1g-lease.v1"
ZERO_SHA256 = "0" * 64


class VerificationError(Exception):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root is not an object: {path}")
    return value, raw


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    log, log_raw = load_json(args.transition_log)
    terminal, terminal_raw = load_json(args.terminal_lease)
    require(log_raw == canonical_json(log), "transition log is not canonical JSON", errors)
    require(terminal_raw == canonical_json(terminal), "terminal lease is not canonical JSON", errors)
    require(log.get("schema_version") == LOG_SCHEMA, "transition log schema mismatch", errors)
    candidate_id = log.get("candidate_id")
    lease_id = log.get("lease_id")
    require(isinstance(candidate_id, str) and bool(candidate_id), "candidate_id is invalid", errors)
    require(valid_sha256(lease_id), "lease_id is invalid", errors)
    entries = log.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("transition entries are empty or invalid")
        entries = []

    previous_sha256 = ZERO_SHA256
    authority_active = False
    activation_count = 0
    deauthorization_count = 0
    terminal_count = 0
    bound_codec: tuple[Any, Any, Any] | None = None
    for index, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            errors.append(f"entry {index} is not an object")
            continue
        entry = dict(raw_entry)
        entry_sha256 = entry.pop("entry_sha256", None)
        computed_entry_sha256 = hashlib.sha256(canonical_json(entry)).hexdigest()
        require(entry_sha256 == computed_entry_sha256, f"entry {index} SHA-256 mismatch", errors)
        require(raw_entry.get("sequence") == index, f"entry {index} sequence mismatch", errors)
        require(raw_entry.get("previous_entry_sha256") == previous_sha256, f"entry {index} previous hash mismatch", errors)
        previous_sha256 = entry_sha256 if valid_sha256(entry_sha256) else ZERO_SHA256
        lease = raw_entry.get("lease")
        if not isinstance(lease, dict):
            errors.append(f"entry {index} lease is not an object")
            lease = {}
        computed_lease_sha256 = hashlib.sha256(canonical_json(lease)).hexdigest()
        require(raw_entry.get("lease_sha256") == computed_lease_sha256, f"entry {index} lease hash mismatch", errors)
        require(lease.get("schema") == LEASE_SCHEMA, f"entry {index} lease schema mismatch", errors)
        require(lease.get("candidate_id") == candidate_id, f"entry {index} candidate mismatch", errors)
        require(lease.get("lease_id") == lease_id, f"entry {index} lease_id mismatch", errors)
        require(lease.get("lease_mode") == "managed", f"entry {index} lease mode mismatch", errors)
        event = raw_entry.get("event")
        signal_authority = lease.get("signal_authority")
        if index == 0:
            require(event == "lease_acquired", "first transition is not lease_acquired", errors)
        elif event == "lease_acquired":
            errors.append(f"entry {index} repeats lease_acquired")
        if event == "lease_acquired":
            require(signal_authority is False, "acquired lease has signal authority", errors)
            authority_active = False
        elif event == "codec_activated":
            require(not authority_active, f"entry {index} activates an already active lease", errors)
            require(signal_authority is True, f"entry {index} activation lacks signal authority", errors)
            require(isinstance(lease.get("codec_pid"), int) and not isinstance(lease.get("codec_pid"), bool), f"entry {index} codec PID invalid", errors)
            require(isinstance(lease.get("codec_proc_start_ticks"), int) and not isinstance(lease.get("codec_proc_start_ticks"), bool), f"entry {index} codec start invalid", errors)
            require(valid_sha256(lease.get("codec_command_sha256")), f"entry {index} codec command hash invalid", errors)
            observed_binding = (
                lease.get("codec_pid"),
                lease.get("codec_proc_start_ticks"),
                lease.get("codec_command_sha256"),
            )
            if bound_codec is None:
                bound_codec = observed_binding
            else:
                require(observed_binding == bound_codec, f"entry {index} rebinds the codec identity", errors)
            authority_active = True
            activation_count += 1
        elif event == "activation_rollback":
            require(not authority_active, f"entry {index} rolls back an already active lease", errors)
            require(signal_authority is False, f"entry {index} rollback retains signal authority", errors)
            authority_active = False
        elif event == "signals_deauthorized":
            require(authority_active, f"entry {index} deauthorizes an inactive lease", errors)
            require(signal_authority is False, f"entry {index} deauthorization retains authority", errors)
            authority_active = False
            deauthorization_count += 1
        elif event == "terminal_evidence_frozen":
            terminal_count += 1
            require(index == len(entries) - 1, "terminal transition is not last", errors)
            require(not authority_active and signal_authority is False, "terminal transition retains authority", errors)
            terminal_sha256 = hashlib.sha256(terminal_raw).hexdigest()
            require(raw_entry.get("terminal_evidence_sha256") == terminal_sha256, "terminal evidence hash mismatch", errors)
            require(lease == terminal, "terminal transition lease differs from terminal evidence", errors)
        else:
            errors.append(f"entry {index} event is invalid")

    require(terminal_count == 1, "transition log does not contain exactly one terminal event", errors)
    require(not authority_active, "transition log ends with signal authority active", errors)
    require(terminal.get("signal_authority") is False, "terminal evidence retains signal authority", errors)
    require(terminal.get("candidate_id") == candidate_id, "terminal candidate mismatch", errors)
    require(terminal.get("lease_id") == lease_id, "terminal lease_id mismatch", errors)

    verified = not errors
    output = {
        "schema_version": SCHEMA,
        "candidate_id": candidate_id,
        "lease_id": lease_id,
        "verified": verified,
        "computed": {
            "entries": len(entries),
            "activations": activation_count,
            "deauthorizations": deauthorization_count,
            "terminal_events": terminal_count,
            "terminal_signal_authority": terminal.get("signal_authority"),
            "transition_log_sha256": hashlib.sha256(log_raw).hexdigest(),
            "terminal_lease_sha256": hashlib.sha256(terminal_raw).hexdigest(),
        },
        "errors": errors,
    }
    return output, verified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transition-log", required=True, type=Path)
    parser.add_argument("--terminal-lease", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output, verified = verify(args)
    except (OSError, VerificationError) as exc:
        output = {
            "schema_version": SCHEMA,
            "candidate_id": None,
            "lease_id": None,
            "verified": False,
            "computed": None,
            "errors": [str(exc)],
        }
        verified = False
    encoded = json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output is None:
        sys.stdout.write(encoded)
    else:
        args.output.write_text(encoded, encoding="utf-8")
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
