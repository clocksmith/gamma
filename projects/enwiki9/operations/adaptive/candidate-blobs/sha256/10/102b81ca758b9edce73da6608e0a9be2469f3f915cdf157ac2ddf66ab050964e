"""Atomic ownership of the canonical managed-lease acquisition namespace."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
from types import ModuleType
from typing import Any


SCHEMA = "gamma.enwiki9.mechanism-ir-managed-lane-lock.v1"
INHERITED_DIRECTORY_FD = "GAMMA_MECHANISM_IR_MANAGED_LANE_DIRECTORY_FD"
INHERITED_LOCK_FD = "GAMMA_MECHANISM_IR_MANAGED_LANE_LOCK_FD"
INHERITED_LEASE = "GAMMA_MECHANISM_IR_MANAGED_LANE_LEASE"
INHERITED_PAYLOAD_SHA256 = "GAMMA_MECHANISM_IR_MANAGED_LANE_PAYLOAD_SHA256"


class LaneError(RuntimeError):
    pass


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def validate_namespace(path: Path) -> tuple[Path, Path]:
    lease = _absolute(path)
    parent = lease.parent
    current = Path(parent.anchor)
    for component in parent.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise LaneError(f"unsafe lease parent component: {current}")
    lock = lease.with_name(f"{lease.name}.lock")
    return lease, lock


def require_clear(path: Path) -> tuple[Path, Path]:
    lease, lock = validate_namespace(path)
    if _present(lease) or _present(lock):
        raise LaneError(f"managed lease namespace occupied: {lease}")
    return lease, lock


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
            raise LaneError("short managed-lane lock write")
        offset += written


def _read_exact_at(
    directory_descriptor: int, name: str, expected: os.stat_result
) -> bytes:
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
        dir_fd=directory_descriptor,
    )
    try:
        observed = os.fstat(descriptor)
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_nlink != 1
            or observed.st_dev != expected.st_dev
            or observed.st_ino != expected.st_ino
        ):
            raise LaneError("managed-lane lock identity changed")
        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, 4096)
            if not block:
                break
            chunks.append(block)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


class OwnedNamespaceLock:
    def __init__(
        self,
        lease: Path,
        lock: Path,
        directory_descriptor: int,
        directory_identity: os.stat_result,
        descriptor: int,
        identity: os.stat_result,
        payload: bytes,
    ) -> None:
        self.lease = lease
        self.lock = lock
        self.directory_descriptor = directory_descriptor
        self.directory_identity = directory_identity
        self.descriptor = descriptor
        self.identity = identity
        self.payload = payload
        self.closed = False

    @classmethod
    def acquire(cls, path: Path) -> "OwnedNamespaceLock":
        lease, lock = require_clear(path)
        directory_descriptor = os.open(
            lock.parent,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
        )
        directory_identity = os.fstat(directory_descriptor)
        if (
            _present_at(directory_descriptor, lease.name)
            or _present_at(directory_descriptor, lock.name)
        ):
            os.close(directory_descriptor)
            raise LaneError(f"managed lease namespace occupied: {lease}")
        token = secrets.token_hex(32)
        payload = (
            json.dumps(
                {"pid": os.getpid(), "schema": SCHEMA, "token": token},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")
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
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
            identity = os.fstat(descriptor)
            if not stat.S_ISREG(identity.st_mode) or identity.st_nlink != 1:
                raise LaneError("managed-lane lock is not a single-link regular file")
            os.fsync(directory_descriptor)
            guard = cls(
                lease,
                lock,
                directory_descriptor,
                directory_identity,
                descriptor,
                identity,
                payload,
            )
            if _present_at(directory_descriptor, lease.name):
                try:
                    guard.release()
                finally:
                    raise LaneError("managed lease appeared during lock acquisition")
            guard.assert_owned(path)
            return guard
        except Exception:
            try:
                current = os.stat(
                    lock.name,
                    dir_fd=directory_descriptor,
                    follow_symlinks=False,
                )
                if current.st_dev == os.fstat(descriptor).st_dev and current.st_ino == os.fstat(descriptor).st_ino:
                    os.unlink(lock.name, dir_fd=directory_descriptor)
                    os.fsync(directory_descriptor)
            except OSError:
                pass
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                os.close(directory_descriptor)
            except OSError:
                pass
            raise

    def _assert_directory_owned(self) -> None:
        observed = os.fstat(self.directory_descriptor)
        current = os.stat(self.lock.parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(observed.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or observed.st_dev != self.directory_identity.st_dev
            or observed.st_ino != self.directory_identity.st_ino
            or current.st_dev != self.directory_identity.st_dev
            or current.st_ino != self.directory_identity.st_ino
        ):
            raise LaneError("managed-lane namespace directory identity changed")

    def assert_owned(self, path: Path) -> None:
        lease, lock = validate_namespace(path)
        if lease != self.lease or lock != self.lock:
            raise LaneError("wrapped operation changed managed lease namespace")
        if self.closed:
            raise LaneError("managed lease namespace is no longer exclusively owned")
        self._assert_directory_owned()
        if _present_at(self.directory_descriptor, self.lease.name):
            raise LaneError("managed lease namespace is no longer exclusively owned")
        raw = _read_exact_at(
            self.directory_descriptor, self.lock.name, self.identity
        )
        if raw != self.payload:
            raise LaneError("managed-lane lock ownership token changed")

    def child_environment(self) -> dict[str, str]:
        self.assert_owned(self.lease)
        return {
            INHERITED_DIRECTORY_FD: str(self.directory_descriptor),
            INHERITED_LOCK_FD: str(self.descriptor),
            INHERITED_LEASE: os.fspath(self.lease),
            INHERITED_PAYLOAD_SHA256: hashlib.sha256(self.payload).hexdigest(),
        }

    def child_descriptors(self) -> tuple[int, int]:
        self.assert_owned(self.lease)
        return self.directory_descriptor, self.descriptor

    def release(self) -> None:
        if self.closed:
            raise LaneError("managed-lane lock already released")
        try:
            self._assert_directory_owned()
            lease_appeared = _present_at(
                self.directory_descriptor, self.lease.name
            )
            raw = _read_exact_at(
                self.directory_descriptor, self.lock.name, self.identity
            )
            if raw != self.payload:
                raise LaneError(
                    "refusing to unlink lock with changed ownership token"
                )
            current = os.stat(
                self.lock.name,
                dir_fd=self.directory_descriptor,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(current.st_mode)
                or current.st_nlink != 1
                or current.st_dev != self.identity.st_dev
                or current.st_ino != self.identity.st_ino
            ):
                raise LaneError(
                    "refusing to unlink replacement managed-lane lock"
                )
        except Exception:
            os.close(self.descriptor)
            os.close(self.directory_descriptor)
            self.closed = True
            raise
        os.unlink(self.lock.name, dir_fd=self.directory_descriptor)
        os.fsync(self.directory_descriptor)
        os.close(self.descriptor)
        os.close(self.directory_descriptor)
        self.closed = True
        if lease_appeared:
            raise LaneError("managed lease appeared while wrapper held the acquisition lock")

    def __enter__(self) -> "OwnedNamespaceLock":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        self.release()
        return False


class BorrowedNamespaceLock:
    """A subprocess view of a lock retained and released by its parent."""

    def __init__(
        self,
        lease: Path,
        lock: Path,
        directory_descriptor: int,
        directory_identity: os.stat_result,
        descriptor: int,
        identity: os.stat_result,
        payload_sha256: str,
    ) -> None:
        self.lease = lease
        self.lock = lock
        self.directory_descriptor = directory_descriptor
        self.directory_identity = directory_identity
        self.descriptor = descriptor
        self.identity = identity
        self.payload_sha256 = payload_sha256
        self.closed = False

    @classmethod
    def from_environment(cls, path: Path) -> "BorrowedNamespaceLock | None":
        names = (
            INHERITED_DIRECTORY_FD,
            INHERITED_LOCK_FD,
            INHERITED_LEASE,
            INHERITED_PAYLOAD_SHA256,
        )
        values = [os.environ.get(name) for name in names]
        if all(value is None for value in values):
            return None
        if any(value is None for value in values):
            raise LaneError("incomplete inherited managed-lane witness")
        assert all(value is not None for value in values)
        lease, lock = validate_namespace(path)
        if os.fspath(lease) != values[2]:
            raise LaneError("inherited managed-lane path mismatch")
        try:
            directory_descriptor = int(values[0])
            descriptor = int(values[1])
        except ValueError as exc:
            raise LaneError("invalid inherited managed-lane descriptor") from exc
        payload_sha256 = values[3]
        if (
            len(payload_sha256) != 64
            or any(character not in "0123456789abcdef" for character in payload_sha256)
        ):
            raise LaneError("invalid inherited managed-lane payload digest")
        directory_identity = os.fstat(directory_descriptor)
        identity = os.fstat(descriptor)
        if not stat.S_ISDIR(directory_identity.st_mode):
            raise LaneError("inherited namespace descriptor is not a directory")
        if not stat.S_ISREG(identity.st_mode) or identity.st_nlink != 1:
            raise LaneError("inherited lock descriptor is not a single-link regular file")
        raw = _read_exact_at(directory_descriptor, lock.name, identity)
        if hashlib.sha256(raw).hexdigest() != payload_sha256:
            raise LaneError("inherited managed-lane payload digest mismatch")
        try:
            payload = json.loads(raw.decode("ascii"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise LaneError("invalid inherited managed-lane payload") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != SCHEMA
            or payload.get("pid") != os.getppid()
        ):
            raise LaneError("inherited managed-lane parent identity mismatch")
        borrowed = cls(
            lease,
            lock,
            directory_descriptor,
            directory_identity,
            descriptor,
            identity,
            payload_sha256,
        )
        borrowed.assert_owned(path)
        return borrowed

    def assert_owned(self, path: Path) -> None:
        lease, lock = validate_namespace(path)
        if lease != self.lease or lock != self.lock:
            raise LaneError("borrowed operation changed managed lease namespace")
        if self.closed:
            raise LaneError("borrowed managed-lane witness is closed")
        directory_identity = os.fstat(self.directory_descriptor)
        if (
            not stat.S_ISDIR(directory_identity.st_mode)
            or directory_identity.st_dev != self.directory_identity.st_dev
            or directory_identity.st_ino != self.directory_identity.st_ino
        ):
            raise LaneError("borrowed namespace directory identity changed")
        if _present_at(self.directory_descriptor, self.lease.name):
            raise LaneError("managed lease appeared under borrowed ownership")
        raw = _read_exact_at(self.directory_descriptor, self.lock.name, self.identity)
        if hashlib.sha256(raw).hexdigest() != self.payload_sha256:
            raise LaneError("borrowed managed-lane payload changed")

    def close(self) -> None:
        if self.closed:
            raise LaneError("borrowed managed-lane witness already closed")
        self.assert_owned(self.lease)
        os.close(self.descriptor)
        os.close(self.directory_descriptor)
        self.closed = True


def load_tool(project: Path, filename: str, module_name: str) -> ModuleType:
    path = project / "tools" / filename
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise LaneError(f"cannot load frozen tool: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if Path(str(module.__file__)).resolve(strict=True) != path.resolve(strict=True):
        raise LaneError(f"loaded tool identity mismatch: {path}")
    return module


def argument_path(flag: str) -> Path:
    import sys

    positions = [index for index, value in enumerate(sys.argv) if value == flag]
    if len(positions) != 1 or positions[0] + 1 >= len(sys.argv):
        raise LaneError(f"exactly one {flag} argument is required")
    return Path(sys.argv[positions[0] + 1])
