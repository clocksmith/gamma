#!/usr/bin/env python3
"""Atomic managed-exclusive lease primitive for enwik9 experiment runners.

The lease begins without signaling authority. A runner may grant signaling
authority only after binding a live descendant codec PID, its proc start ticks,
and the codec command digest. Release first revokes authority and refuses to
remove the lease while that bound process identity remains live.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEASE_SCHEMA = "gamma.enwiki9.exclusive-full1g-lease.v1"
SHA256_LENGTH = 64


class LeaseError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def require_sha256(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != SHA256_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise LeaseError(f"{name} is not a lowercase SHA-256 digest")
    return value


def proc_identity(pid: int) -> tuple[int, int]:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    close = raw.rfind(")")
    if close < 0:
        raise LeaseError(f"malformed /proc/{pid}/stat")
    fields = raw[close + 2 :].split()
    if len(fields) <= 19:
        raise LeaseError(f"short /proc/{pid}/stat")
    return int(fields[1]), int(fields[19])


def identity_is_live(pid: int, start_ticks: int) -> bool:
    try:
        _, observed = proc_identity(pid)
    except (OSError, LeaseError):
        return False
    return observed == start_ticks


def is_descendant(pid: int, ancestor_pid: int) -> bool:
    seen: set[int] = set()
    cursor = pid
    while cursor > 1 and cursor not in seen:
        if cursor == ancestor_pid:
            return True
        seen.add(cursor)
        try:
            parent, _ = proc_identity(cursor)
        except (OSError, LeaseError):
            return False
        cursor = parent
    return cursor == ancestor_pid


def canonical_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_atomic(path: Path, raw: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, mode)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:
                    raise LeaseError(f"short write to {temporary}")
                offset += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LeaseError(f"cannot read managed lease {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LeaseError("managed lease root is not an object")
    return value


class ManagedExclusiveLease:
    def __init__(
        self,
        lease_path: Path,
        lock_path: Path,
        transition_path: Path,
        record: dict[str, Any],
    ) -> None:
        self.lease_path = lease_path
        self.lock_path = lock_path
        self.transition_path = transition_path
        self.record = record
        self.transitions: list[dict[str, Any]] = []
        self.closed = False

    @classmethod
    def acquire(
        cls,
        *,
        lease_path: Path,
        transition_path: Path,
        candidate_id: str,
        command_sha256: str,
        runner_sha256: str,
        guard_path: str,
        result_path: str,
        scratch_path: str,
        claim_boundary: str,
    ) -> "ManagedExclusiveLease":
        if not candidate_id or not all((guard_path, result_path, scratch_path, claim_boundary)):
            raise LeaseError("managed lease identity fields must be nonempty")
        require_sha256(command_sha256, "command_sha256")
        require_sha256(runner_sha256, "runner_sha256")
        if lease_path.exists():
            raise LeaseError(f"exclusive lease already exists: {lease_path}")
        if transition_path.exists():
            raise LeaseError(f"managed lease transition log already exists: {transition_path}")
        lock_path = lease_path.with_name(f"{lease_path.name}.lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
            try:
                lock_payload = f"{os.getpid()}\n".encode("ascii")
                offset = 0
                while offset < len(lock_payload):
                    written = os.write(lock_fd, lock_payload[offset:])
                    if written <= 0:
                        raise LeaseError(f"short write to {lock_path}")
                    offset += written
                os.fsync(lock_fd)
            finally:
                os.close(lock_fd)
        except Exception:
            try:
                lock_path.unlink()
                fsync_directory(lock_path.parent)
            except OSError:
                pass
            raise
        try:
            if lease_path.exists():
                raise LeaseError(f"exclusive lease appeared during acquisition: {lease_path}")
            _, runner_start_ticks = proc_identity(os.getpid())
            now = utc_now()
            record: dict[str, Any] = {
                "$schema": "exclusive_full1g.schema.json",
                "schema": LEASE_SCHEMA,
                "lease_id": secrets.token_hex(32),
                "candidate_id": candidate_id,
                "pid": os.getpid(),
                "proc_start_ticks": runner_start_ticks,
                "command_sha256": command_sha256,
                "runner_sha256": runner_sha256,
                "guard_path": guard_path,
                "result_path": result_path,
                "scratch_path": scratch_path,
                "resource_class": "exclusive_full1g",
                "started_utc": now,
                "heartbeat_utc": now,
                "lease_mode": "managed",
                "signal_authority": False,
                "claim_boundary": claim_boundary,
            }
            write_atomic(lease_path, canonical_json(record))
            lease = cls(lease_path, lock_path, transition_path, record)
            lease._append_transition("lease_acquired")
            return lease
        except Exception:
            try:
                lock_path.unlink()
                fsync_directory(lock_path.parent)
            except OSError:
                pass
            raise

    def _require_owner(self) -> None:
        if self.closed:
            raise LeaseError("managed lease is closed")
        _, observed_start = proc_identity(os.getpid())
        if self.record.get("pid") != os.getpid() or self.record.get("proc_start_ticks") != observed_start:
            raise LeaseError("managed lease owner identity mismatch")
        current = read_object(self.lease_path)
        if current.get("lease_id") != self.record.get("lease_id"):
            raise LeaseError("managed lease identity changed on disk")
        if current != self.record:
            raise LeaseError("managed lease was modified outside its owner")
        self._require_transition_log()

    def _transition_log(self, entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "schema_version": "managed-exclusive-lease-transition-log.v1",
            "candidate_id": self.record["candidate_id"],
            "lease_id": self.record["lease_id"],
            "entries": self.transitions if entries is None else entries,
        }

    def _require_transition_log(self) -> None:
        if not self.transitions:
            if self.transition_path.exists():
                raise LeaseError("managed lease transition log appeared before acquisition entry")
            return
        if not self.transition_path.exists():
            raise LeaseError("managed lease transition log disappeared")
        expected = canonical_json(self._transition_log())
        if self.transition_path.read_bytes() != expected:
            raise LeaseError("managed lease transition log was modified outside its owner")

    def _append_transition(self, event: str, terminal_evidence_sha256: str | None = None) -> None:
        self._require_transition_log()
        lease_snapshot = json.loads(canonical_json(self.record))
        lease_sha256 = hashlib.sha256(canonical_json(lease_snapshot)).hexdigest()
        payload: dict[str, Any] = {
            "sequence": len(self.transitions),
            "event": event,
            "event_utc": utc_now(),
            "previous_entry_sha256": (
                self.transitions[-1]["entry_sha256"] if self.transitions else "0" * SHA256_LENGTH
            ),
            "lease_sha256": lease_sha256,
            "lease": lease_snapshot,
        }
        if terminal_evidence_sha256 is not None:
            payload["terminal_evidence_sha256"] = require_sha256(
                terminal_evidence_sha256,
                "terminal_evidence_sha256",
            )
        entry_sha256 = hashlib.sha256(canonical_json(payload)).hexdigest()
        entry = dict(payload)
        entry["entry_sha256"] = entry_sha256
        proposed = [*self.transitions, entry]
        log = self._transition_log(proposed)
        write_atomic(self.transition_path, canonical_json(log))
        self.transitions = proposed

    def _commit(self, event: str | None = None) -> None:
        self.record["heartbeat_utc"] = utc_now()
        write_atomic(self.lease_path, canonical_json(self.record))
        if event is not None:
            self._append_transition(event)

    def heartbeat(self) -> None:
        self._require_owner()
        self._commit()

    def activate_codec(self, *, codec_pid: int, codec_proc_start_ticks: int, codec_command_sha256: str) -> None:
        self._require_owner()
        if self.record.get("signal_authority") is True:
            raise LeaseError("managed lease signaling authority is already active")
        if (
            isinstance(codec_pid, bool)
            or not isinstance(codec_pid, int)
            or codec_pid < 1
            or isinstance(codec_proc_start_ticks, bool)
            or not isinstance(codec_proc_start_ticks, int)
            or codec_proc_start_ticks < 1
        ):
            raise LeaseError("codec process identity is invalid")
        require_sha256(codec_command_sha256, "codec_command_sha256")
        existing_binding = (
            self.record.get("codec_pid"),
            self.record.get("codec_proc_start_ticks"),
            self.record.get("codec_command_sha256"),
        )
        requested_binding = (codec_pid, codec_proc_start_ticks, codec_command_sha256)
        if any(value is not None for value in existing_binding) and existing_binding != requested_binding:
            raise LeaseError("managed lease codec binding is immutable")
        if not identity_is_live(codec_pid, codec_proc_start_ticks):
            raise LeaseError("codec process identity is not live")
        if not is_descendant(codec_pid, os.getpid()):
            raise LeaseError("codec process is not a descendant of the managed runner")
        self.record["codec_pid"] = codec_pid
        self.record["codec_proc_start_ticks"] = codec_proc_start_ticks
        self.record["codec_command_sha256"] = codec_command_sha256
        self.record["signal_authority"] = True
        try:
            self._commit("codec_activated")
        except Exception:
            self.record["signal_authority"] = False
            try:
                self._commit("activation_rollback")
            except Exception:
                pass
            raise

    def deauthorize_signals(self) -> None:
        self._require_owner()
        if self.record.get("signal_authority") is False:
            return
        self.record["signal_authority"] = False
        self._commit("signals_deauthorized")

    def release(self, *, evidence_path: Path) -> None:
        self._require_owner()
        self.deauthorize_signals()
        codec_pid = self.record.get("codec_pid")
        codec_start = self.record.get("codec_proc_start_ticks")
        if isinstance(codec_pid, int) and isinstance(codec_start, int) and identity_is_live(codec_pid, codec_start):
            raise LeaseError("cannot release managed lease while codec identity is live")
        evidence_raw = canonical_json(self.record)
        if evidence_path.exists():
            if evidence_path.read_bytes() != evidence_raw:
                raise LeaseError(f"terminal lease evidence differs: {evidence_path}")
        else:
            write_atomic(evidence_path, evidence_raw, mode=0o644)
        evidence_sha256 = hashlib.sha256(evidence_raw).hexdigest()
        if not self.transitions or self.transitions[-1].get("event") != "terminal_evidence_frozen":
            self._append_transition("terminal_evidence_frozen", evidence_sha256)
        try:
            self.lock_path.unlink()
            fsync_directory(self.lock_path.parent)
        except FileNotFoundError:
            pass
        try:
            self.lease_path.unlink()
            fsync_directory(self.lease_path.parent)
        except FileNotFoundError:
            pass
        self.closed = True


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
