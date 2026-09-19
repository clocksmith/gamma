"""Recoverable multi-record publication without a new queue or database."""
from __future__ import annotations
import fcntl
import json
import os
from pathlib import Path

from gamma_enwiki9.evidence.artifacts import canonical_bytes, publish_immutable_artifact


def begin(directory: Path, intent: dict) -> None:
    publish_immutable_artifact(directory / ".creation-intent.json", canonical_bytes(intent) + b"\n")


def reconcile(directory: Path, *, revision, mutation, register) -> None:
    """Callbacks must be idempotent: revision tree identity, event ID, index ID.

    Progress markers follow each action. A crash between action and marker
    repeats that action safely. Candidate source stays present after any failure.
    """
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        intent = json.loads((directory / ".creation-intent.json").read_bytes())
        if (directory / ".creation-committed.json").exists():
            return
        for name, action in (("revision", revision), ("mutation", mutation), ("index", register)):
            marker = directory / (".creation-" + name + ".json")
            if not marker.exists():
                action(intent)
                publish_immutable_artifact(marker, canonical_bytes({"transaction_id": intent["transaction_id"], "step": name}) + b"\n")
        publish_immutable_artifact(directory / ".creation-committed.json",
            canonical_bytes({"transaction_id": intent["transaction_id"], "committed": True}) + b"\n")
    finally:
        os.close(fd)


def require_committed(directory: Path) -> None:
    if (directory / ".creation-intent.json").exists() and not (directory / ".creation-committed.json").exists():
        raise ValueError("candidate creation is incomplete; reconcile its transaction before use")
