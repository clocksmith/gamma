"""Separate immutable publication, disposable replacement and canonical events."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import stat


def canonical_bytes(value) -> bytes:
    # research_contracts.canonical_bytes v1: these bytes are evidence identities.
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def regular_file(path: Path, label: str, *, root: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    fingerprint(absolute, root)
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError(f"{label}: expected single-link regular file")
    return absolute


def fingerprint(path: Path, root: Path) -> dict:
    root, path = root.resolve(), Path(os.path.abspath(path))
    relative = path.relative_to(root)
    if any(p.is_symlink() for p in (path, *path.parents[:len(relative.parts)])):
        raise ValueError("artifact path contains a symlink")
    if not path.is_file():
        raise ValueError("artifact is not a regular file")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or signature(after) != signature(path.stat()):
        raise ValueError("artifact changed while being fingerprinted")
    return {"path": relative.as_posix(), "bytes": after.st_size, "sha256": digest}


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _stage(path: Path, raw: bytes, mode: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
    except BaseException:
        temporary.unlink()
        raise
    return temporary


def publish_immutable_artifact(path: Path, raw: bytes, *, mode: int = 0o444) -> None:
    """Publish complete durable bytes once; identical retries are idempotent."""
    temporary = _stage(path, raw, mode)
    try:
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
                raise ValueError(f"immutable artifact collision: {path}")
        sync_directory(path.parent)
    finally:
        temporary.unlink()


def replace_derived_view(path: Path, raw: bytes) -> None:
    """Atomically replace regenerable data; it never grants evidence authority."""
    temporary = _stage(path, raw, 0o644)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def append_canonical_event(path: Path, value: dict, *, event_id: str | None = None) -> None:
    """Durable serialized append, optionally idempotent by an explicit event ID.

    An incomplete tail is an error requiring reconciliation, never silently
    truncated. Lock the directory so replacing a log cannot split writer locks.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        payload = dict(value)
        if event_id is not None:
            payload["event_id"] = event_id
        raw = canonical_bytes(payload) + b"\n"
        fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "r+b") as stream:
            already_present = False
            for line in stream:
                if not line.endswith(b"\n"):
                    raise ValueError("canonical event log has an incomplete tail")
                existing = json.loads(line)
                if event_id is not None and existing.get("event_id") == event_id:
                    if existing != payload:
                        raise ValueError("canonical event identity collision")
                    already_present = True
            if already_present:
                return
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory)
    finally:
        os.close(directory)
