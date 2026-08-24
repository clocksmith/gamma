#!/usr/bin/env python3
"""Managed full-1G lease with descriptor-proven acquisition and cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEASE_SCHEMA = "gamma.enwiki9.exclusive-full1g-lease.v1"
LOCK_SCHEMA = "gamma.enwiki9.exclusive-full1g-owned-lock.v1"
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
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def _validate_parent(path: Path) -> Path:
    absolute = _absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parent.parts[1:]:
        current /= component
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise LeaseError(f"managed lease parent is missing: {current}") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise LeaseError(f"unsafe managed lease parent: {current}")
    return absolute


def _open_parent(path: Path) -> tuple[Path, int, os.stat_result]:
    absolute = _validate_parent(path)
    descriptor = os.open(
        absolute.parent,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    identity = os.fstat(descriptor)
    current = os.stat(absolute.parent, follow_symlinks=False)
    if (
        not stat.S_ISDIR(identity.st_mode)
        or identity.st_dev != current.st_dev
        or identity.st_ino != current.st_ino
    ):
        os.close(descriptor)
        raise LeaseError("managed lease directory identity changed")
    return absolute, descriptor, identity


def _present_at(directory_descriptor: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _write_all(descriptor: int, raw: bytes) -> None:
    offset = 0
    while offset < len(raw):
        written = os.write(descriptor, raw[offset:])
        if written <= 0:
            raise LeaseError("short managed lease write")
        offset += written


def _read_named_owned(
    directory_descriptor: int,
    name: str,
    expected: os.stat_result,
) -> bytes:
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
        dir_fd=directory_descriptor,
    )
    try:
        before = os.fstat(descriptor)
        named = os.stat(
            name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_dev != expected.st_dev
            or before.st_ino != expected.st_ino
            or named.st_dev != expected.st_dev
            or named.st_ino != expected.st_ino
        ):
            raise LeaseError("managed lease lock identity changed")
        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, 4096)
            if not block:
                break
            chunks.append(block)
        after = os.fstat(descriptor)
        if (
            before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            raise LeaseError("managed lease lock changed while read")
        raw = b"".join(chunks)
        if len(raw) != after.st_size:
            raise LeaseError("managed lease lock length changed while read")
        return raw
    finally:
        os.close(descriptor)


def _read_regular(path: Path, label: str) -> bytes:
    absolute, directory_descriptor, _ = _open_parent(path)
    try:
        descriptor = os.open(
            absolute.name,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=directory_descriptor,
        )
        try:
            before = os.fstat(descriptor)
            named = os.stat(
                absolute.name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_dev != named.st_dev
                or before.st_ino != named.st_ino
            ):
                raise LeaseError(f"{label} is not a single-link regular file")
            blocks: list[bytes] = []
            while True:
                block = os.read(descriptor, 1 << 20)
                if not block:
                    break
                blocks.append(block)
            after = os.fstat(descriptor)
            if (
                before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
            ):
                raise LeaseError(f"{label} changed while read")
            raw = b"".join(blocks)
            if len(raw) != after.st_size:
                raise LeaseError(f"{label} length changed while read")
            return raw
        finally:
            os.close(descriptor)
    finally:
        os.close(directory_descriptor)


def _unlink_exact_named(
    directory_descriptor: int,
    name: str,
    expected_raw: bytes,
    label: str,
) -> None:
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
        dir_fd=directory_descriptor,
    )
    try:
        identity = os.fstat(descriptor)
        raw = _read_named_owned(directory_descriptor, name, identity)
        if raw != expected_raw:
            raise LeaseError(f"{label} bytes changed before unlink")
        current = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_nlink != 1
            or current.st_dev != identity.st_dev
            or current.st_ino != identity.st_ino
        ):
            raise LeaseError(f"{label} identity changed before unlink")
        os.unlink(name, dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
    finally:
        os.close(descriptor)


def fsync_directory(path: Path) -> None:
    _, descriptor, _ = _open_parent(path / "placeholder")
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_atomic(path: Path, raw: bytes, mode: int = 0o600) -> None:
    absolute = _absolute(path)
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute, directory_descriptor, _ = _open_parent(absolute)
    temporary_name = f".{absolute.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    created = False
    try:
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            mode,
            dir_fd=directory_descriptor,
        )
        created = True
        try:
            _write_all(descriptor, raw)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(
            temporary_name,
            absolute.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
        created = False
        os.fsync(directory_descriptor)
    finally:
        if created:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
                os.fsync(directory_descriptor)
            except (OSError, LeaseError):
                pass
        os.close(directory_descriptor)


def _write_new_at(
    directory_descriptor: int,
    name: str,
    raw: bytes,
    mode: int,
) -> os.stat_result:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
        dir_fd=directory_descriptor,
    )
    try:
        _write_all(descriptor, raw)
        os.fsync(descriptor)
        identity = os.fstat(descriptor)
        if not stat.S_ISREG(identity.st_mode) or identity.st_nlink != 1:
            raise LeaseError("new managed lease file is not single-link regular")
        return identity
    finally:
        os.close(descriptor)


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_read_regular(path, "managed lease"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LeaseError(f"cannot read managed lease {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LeaseError("managed lease root is not an object")
    return value


class _OwnedLock:
    def __init__(
        self,
        lease_path: Path,
        lock_path: Path,
        directory_descriptor: int,
        directory_identity: os.stat_result,
        descriptor: int,
        identity: os.stat_result,
        payload: bytes,
    ) -> None:
        self.lease_path = lease_path
        self.lock_path = lock_path
        self.directory_descriptor = directory_descriptor
        self.directory_identity = directory_identity
        self.descriptor = descriptor
        self.identity = identity
        self.payload = payload
        self.closed = False

    @classmethod
    def acquire(cls, lease_path: Path) -> "_OwnedLock":
        lease, directory_descriptor, directory_identity = _open_parent(lease_path)
        lock = lease.with_name(f"{lease.name}.lock")
        if (
            _present_at(directory_descriptor, lease.name)
            or _present_at(directory_descriptor, lock.name)
        ):
            os.close(directory_descriptor)
            raise LeaseError(f"exclusive lease namespace already occupied: {lease}")
        payload = canonical_json(
            {
                "pid": os.getpid(),
                "schema": LOCK_SCHEMA,
                "token": secrets.token_hex(32),
            }
        )
        try:
            descriptor = os.open(
                lock.name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_descriptor,
            )
        except Exception:
            os.close(directory_descriptor)
            raise
        payload_committed = False
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
            identity = os.fstat(descriptor)
            if not stat.S_ISREG(identity.st_mode) or identity.st_nlink != 1:
                raise LeaseError("owned lease lock is not single-link regular")
            os.fsync(directory_descriptor)
            payload_committed = True
            owned = cls(
                lease,
                lock,
                directory_descriptor,
                directory_identity,
                descriptor,
                identity,
                payload,
            )
            if _present_at(directory_descriptor, lease.name):
                owned.unlink_owned_lock()
                raise LeaseError("exclusive lease appeared during acquisition")
            owned.assert_owned()
            return owned
        except Exception:
            try:
                descriptor_identity = os.fstat(descriptor)
                if payload_committed:
                    raw = _read_named_owned(
                        directory_descriptor,
                        lock.name,
                        descriptor_identity,
                    )
                    if raw == payload:
                        os.unlink(lock.name, dir_fd=directory_descriptor)
                        os.fsync(directory_descriptor)
            except (OSError, LeaseError):
                pass
            for open_descriptor in (descriptor, directory_descriptor):
                try:
                    os.close(open_descriptor)
                except OSError:
                    pass
            raise

    def _assert_directory(self) -> None:
        observed = os.fstat(self.directory_descriptor)
        current = os.stat(self.lock_path.parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(observed.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or observed.st_dev != self.directory_identity.st_dev
            or observed.st_ino != self.directory_identity.st_ino
            or current.st_dev != self.directory_identity.st_dev
            or current.st_ino != self.directory_identity.st_ino
        ):
            raise LeaseError("managed lease namespace directory changed")

    def assert_owned(self) -> None:
        if self.closed:
            raise LeaseError("managed lease lock witness is closed")
        self._assert_directory()
        raw = _read_named_owned(
            self.directory_descriptor,
            self.lock_path.name,
            self.identity,
        )
        if raw != self.payload:
            raise LeaseError("managed lease lock token changed")

    def lease_absent(self) -> bool:
        self.assert_owned()
        return not _present_at(self.directory_descriptor, self.lease_path.name)

    def publish_lease(self, raw: bytes) -> None:
        if not self.lease_absent():
            raise LeaseError("exclusive lease appeared before publication")
        _write_new_at(
            self.directory_descriptor,
            self.lease_path.name,
            raw,
            0o600,
        )
        os.fsync(self.directory_descriptor)
        self.assert_owned()

    def unlink_owned_lock(self) -> None:
        self.assert_owned()
        os.unlink(self.lock_path.name, dir_fd=self.directory_descriptor)
        os.fsync(self.directory_descriptor)
        os.close(self.descriptor)
        os.close(self.directory_descriptor)
        self.closed = True

    def detach_without_unlink(self) -> None:
        if self.closed:
            return
        os.close(self.descriptor)
        os.close(self.directory_descriptor)
        self.closed = True


class ManagedExclusiveLease:
    def __init__(
        self,
        lease_path: Path,
        lock_path: Path,
        transition_path: Path,
        record: dict[str, Any],
        owned_lock: _OwnedLock,
    ) -> None:
        self.lease_path = lease_path
        self.lock_path = lock_path
        self.transition_path = transition_path
        self.record = record
        self.owned_lock = owned_lock
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
        if not candidate_id or not all(
            (guard_path, result_path, scratch_path, claim_boundary)
        ):
            raise LeaseError("managed lease identity fields must be nonempty")
        require_sha256(command_sha256, "command_sha256")
        require_sha256(runner_sha256, "runner_sha256")
        transition = _absolute(transition_path)
        if transition.exists() or transition.is_symlink():
            raise LeaseError(f"managed lease transition log already exists: {transition}")
        owned = _OwnedLock.acquire(lease_path)
        published = False
        try:
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
            owned.publish_lease(canonical_json(record))
            published = True
            lease = cls(
                owned.lease_path,
                owned.lock_path,
                transition,
                record,
                owned,
            )
            lease._append_transition("lease_acquired")
            return lease
        except Exception:
            if published:
                owned.detach_without_unlink()
            else:
                try:
                    owned.unlink_owned_lock()
                except Exception:
                    owned.detach_without_unlink()
            raise

    def _require_owner(self) -> None:
        if self.closed:
            raise LeaseError("managed lease is closed")
        self.owned_lock.assert_owned()
        _, observed_start = proc_identity(os.getpid())
        if (
            self.record.get("pid") != os.getpid()
            or self.record.get("proc_start_ticks") != observed_start
        ):
            raise LeaseError("managed lease owner identity mismatch")
        current = read_object(self.lease_path)
        if current.get("lease_id") != self.record.get("lease_id"):
            raise LeaseError("managed lease identity changed on disk")
        if current != self.record:
            raise LeaseError("managed lease was modified outside its owner")
        self._require_transition_log()

    def _transition_log(
        self,
        entries: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": "managed-exclusive-lease-transition-log.v1",
            "candidate_id": self.record["candidate_id"],
            "lease_id": self.record["lease_id"],
            "entries": self.transitions if entries is None else entries,
        }

    def _require_transition_log(self) -> None:
        if not self.transitions:
            if self.transition_path.exists() or self.transition_path.is_symlink():
                raise LeaseError(
                    "managed lease transition log appeared before acquisition entry"
                )
            return
        if not self.transition_path.exists() or self.transition_path.is_symlink():
            raise LeaseError("managed lease transition log disappeared")
        expected = canonical_json(self._transition_log())
        if _read_regular(self.transition_path, "managed lease transition log") != expected:
            raise LeaseError("managed lease transition log was modified outside its owner")

    def _append_transition(
        self,
        event: str,
        terminal_evidence_sha256: str | None = None,
    ) -> None:
        self.owned_lock.assert_owned()
        self._require_transition_log()
        lease_snapshot = json.loads(canonical_json(self.record))
        lease_sha256 = hashlib.sha256(canonical_json(lease_snapshot)).hexdigest()
        payload: dict[str, Any] = {
            "sequence": len(self.transitions),
            "event": event,
            "event_utc": utc_now(),
            "previous_entry_sha256": (
                self.transitions[-1]["entry_sha256"]
                if self.transitions
                else "0" * SHA256_LENGTH
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
        write_atomic(self.transition_path, canonical_json(self._transition_log(proposed)))
        self.transitions = proposed
        self.owned_lock.assert_owned()

    def _commit(self, event: str | None = None) -> None:
        self.owned_lock.assert_owned()
        self.record["heartbeat_utc"] = utc_now()
        write_atomic(self.lease_path, canonical_json(self.record))
        self.owned_lock.assert_owned()
        if event is not None:
            self._append_transition(event)

    def heartbeat(self) -> None:
        self._require_owner()
        self._commit()

    def activate_codec(
        self,
        *,
        codec_pid: int,
        codec_proc_start_ticks: int,
        codec_command_sha256: str,
    ) -> None:
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
        requested_binding = (
            codec_pid,
            codec_proc_start_ticks,
            codec_command_sha256,
        )
        if (
            any(value is not None for value in existing_binding)
            and existing_binding != requested_binding
        ):
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
        if (
            isinstance(codec_pid, int)
            and isinstance(codec_start, int)
            and identity_is_live(codec_pid, codec_start)
        ):
            raise LeaseError("cannot release managed lease while codec identity is live")
        evidence_raw = canonical_json(self.record)
        evidence = _absolute(evidence_path)
        if evidence.exists() or evidence.is_symlink():
            if _read_regular(evidence, "terminal lease evidence") != evidence_raw:
                raise LeaseError(f"terminal lease evidence differs: {evidence}")
        else:
            write_atomic(evidence, evidence_raw, mode=0o644)
        evidence_sha256 = hashlib.sha256(evidence_raw).hexdigest()
        if (
            not self.transitions
            or self.transitions[-1].get("event") != "terminal_evidence_frozen"
        ):
            self._append_transition("terminal_evidence_frozen", evidence_sha256)
        self._require_owner()
        self.owned_lock.assert_owned()
        _unlink_exact_named(
            self.owned_lock.directory_descriptor,
            self.lease_path.name,
            canonical_json(self.record),
            "managed lease",
        )
        self.owned_lock.unlink_owned_lock()
        self.closed = True


def file_sha256(path: Path) -> str:
    return hashlib.sha256(_read_regular(path, "hashed file")).hexdigest()
