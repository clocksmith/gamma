"""Reusable artifact fingerprints and atomic writes for new, unsealed tooling."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile


def sha256_file(path: Path) -> str:
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def artifact_ref(path: Path, root: Path) -> dict:
    """Fingerprint one regular file under root; reject aliases and escapes."""
    root, path = Path(root).resolve(), Path(os.path.abspath(path))
    relative = path.relative_to(root)
    if any(part.is_symlink() for part in (path, *path.parents[:len(relative.parts)])):
        raise ValueError("artifact path contains a symlink")
    if not path.is_file():
        raise ValueError("artifact is not a regular file")
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
        after = os.fstat(handle.fileno())
    signature = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if signature(before) != signature(after) or signature(after) != signature(path.stat()):
        raise ValueError("artifact changed while being fingerprinted")
    return {"path": relative.as_posix(), "bytes": after.st_size, "sha256": digest}


def atomic_write(path: Path, data: str | bytes) -> None:
    """Replace one disposable output only after its new bytes are closed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = data.encode("utf-8") if isinstance(data, str) else data
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def atomic_write_json(path: Path, value: object) -> None:
    atomic_write(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
