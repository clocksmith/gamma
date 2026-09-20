"""Freeze and restore explicit closures using the candidate revision blob store."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .artifacts import canonical_bytes, fingerprint, publish_immutable_artifact

BLOB_ROOT = Path("operations/adaptive/candidate-blobs/sha256")


@contextmanager
def original_input_sources(root: Path, references: list[dict]):
    """Verify original input identities and reconstruct Python import geometry.

For terminal interpretation only. Current checkout bytes or the existing blob
store must supply each exact declared digest. No hashes are repaired, no Git or
network recovery occurs, and this does not verify the original validator or
authorize a new execution. Only Python sources need a temporary tree for static
import analysis; all data identities are still checked.
"""
    with tempfile.TemporaryDirectory(prefix="gamma-original-inputs-") as directory:
        destination = Path(directory)
        for reference in references:
            name = safe_relative(reference["path"])
            expected = reference["sha256"].removeprefix("sha256:")
            # Validate digest syntax even when the current checkout matches.
            blob = blob_path(root, expected)
            source = root / name
            try:
                matches = fingerprint(source, root)["sha256"] == expected
            except (OSError, ValueError):
                matches = False
            if not matches:
                source = blob
            identity = fingerprint(source, root)
            if identity["sha256"] != expected or ("bytes" in reference and identity["bytes"] != reference["bytes"]):
                raise ValueError("missing or corrupt original input: " + str(name))
            if name.suffix == ".py":
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                    raise ValueError("original source changed while resolving: " + str(name))
                target.chmod(0o444)
        yield destination


def blob_path(root: Path, digest: str) -> Path:
    digest = digest.removeprefix("sha256:")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid SHA-256")
    return root / BLOB_ROOT / digest[:2] / digest


def safe_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or any(p in {"..", "."} for p in path.parts):
        raise ValueError(f"unsafe closure path: {value}")
    return path


def freeze(root: Path, files: dict[str, str], *, declaration: dict,
           destination: Path) -> dict:
    """Each file has an explicit role; freezing never changes a bound digest."""
    rows = []
    for name, role in sorted(files.items()):
        source = root / safe_relative(name)
        row = fingerprint(source, root)
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"source changed while freezing: {name}")
        blob = blob_path(root, row["sha256"])
        publish_immutable_artifact(blob, raw)
        rows.append({**row, "role": role, "blobPath": blob.relative_to(root).as_posix(),
                     "executable": bool(source.stat().st_mode & 0o111)})
    body = {"schema": "gamma.enwiki9.experiment-closure.v1", "files": rows,
            "declaration": declaration}
    manifest = {**body, "closure_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest()}
    publish_immutable_artifact(destination, canonical_bytes(manifest) + b"\n")
    return manifest


def validate_manifest(manifest: dict) -> None:
    body = {k: v for k, v in manifest.items() if k != "closure_sha256"}
    if manifest.get("schema") != "gamma.enwiki9.experiment-closure.v1" or (
        hashlib.sha256(canonical_bytes(body)).hexdigest() != manifest.get("closure_sha256")
    ):
        raise ValueError("closure manifest identity differs")
    seen = set()
    for row in manifest["files"]:
        name = safe_relative(row["path"]).as_posix()
        if name in seen:
            raise ValueError("duplicate closure path")
        seen.add(name)
        expected = blob_path(Path(), row["sha256"]).as_posix()
        if row["blobPath"] != expected:
            raise ValueError("closure blob path differs from identity")


def materialize(root: Path, manifest: dict, destination: Path, *, read_only=True) -> None:
    validate_manifest(manifest)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    # Authenticate all blobs before creating the destination; never use checkout fallbacks.
    for row in manifest["files"]:
        ref = fingerprint(blob_path(root, row["sha256"]), root)
        if ref["sha256"] != row["sha256"] or ref["bytes"] != row["bytes"]:
            raise ValueError(f"missing or corrupt closure blob: {row['path']}")
    destination.mkdir(parents=True)
    try:
        for row in manifest["files"]:
            output = destination / row["path"]
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(blob_path(root, row["sha256"]), output)
            if fingerprint(output, destination)["sha256"] != row["sha256"]:
                raise ValueError("materialized closure identity differs")
            output.chmod(0o555 if row["executable"] else 0o444)
        if read_only:
            for directory in sorted((p for p in destination.rglob("*") if p.is_dir()), reverse=True):
                directory.chmod(0o555)
            destination.chmod(0o555)
    except BaseException:
        # Keep incomplete materialization for diagnosis, never label it replayable.
        raise


@dataclass(frozen=True)
class HistoricalState:
    evidence_state: str
    compatible_with_current_launcher: bool
    authorized_for_new_execution: bool
    missing: tuple[str, ...]


def inspect(root: Path, manifest: dict, *, replay_verified=False,
            current_launcher_compatible=False) -> HistoricalState:
    validate_manifest(manifest)
    missing = []
    for row in manifest["files"]:
        try:
            actual = fingerprint(blob_path(root, row["sha256"]), root)
            if actual["sha256"] != row["sha256"] or actual["bytes"] != row["bytes"]:
                missing.append(row["path"])
        except (OSError, ValueError):
            missing.append(row["path"])
    complete = manifest["declaration"].get("complete") is True
    state = ("missing or corrupt evidence" if missing else
             "verified under original closure" if complete and replay_verified else
             "original artifacts present; replay unavailable")
    # A stored closure is evidence, never a scheduling grant.
    return HistoricalState(state, current_launcher_compatible, False, tuple(missing))


def retain_reference(root: Path, reference: dict, *, repository: Path,
                     maximum_bytes: int = 16 * 1024 * 1024) -> dict:
    """Recover exact bound bytes from the store, checkout, or local Git history.

    Git is consulted by path and every recovered blob is authenticated by the
    receipt SHA-256. Commit ancestry never substitutes for the bound identity.
    """
    name = safe_relative(reference["path"])
    digest = reference["sha256"].removeprefix("sha256:")
    blob = blob_path(root, digest)
    raw = None
    provenance = "existing content-addressed blob"
    for candidate in (blob, root / name):
        if candidate.is_file() and not candidate.is_symlink() and candidate.stat().st_size <= maximum_bytes:
            observed = fingerprint(candidate, root)
            if observed["sha256"] == digest:
                raw = candidate.read_bytes()
                provenance = "existing content-addressed blob" if candidate == blob else "authenticated checkout"
                break
    if raw is None:
        git_path = (root / name).relative_to(repository).as_posix()
        commits = subprocess.check_output(["git", "-C", str(repository), "log", "--format=%H", "--", git_path], text=True).splitlines()
        for commit in commits:
            obj = f"{commit}:{git_path}"
            size = subprocess.run(["git", "-C", str(repository), "cat-file", "-s", obj], capture_output=True, text=True)
            if size.returncode or int(size.stdout) > maximum_bytes:
                continue
            candidate = subprocess.check_output(["git", "-C", str(repository), "show", obj])
            if hashlib.sha256(candidate).hexdigest() == digest:
                raw, provenance = candidate, "git:" + obj
                break
    if raw is None or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"bound source unavailable: {name} ({digest})")
    publish_immutable_artifact(blob, raw)
    return {"path": name.as_posix(), "sha256": digest, "bytes": len(raw),
            "blobPath": blob.relative_to(root).as_posix(), "provenance": provenance,
            "role": reference.get("role", "bound_evidence"), "executable": False}


def bound_references(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value
        for child in value.values():
            yield from bound_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from bound_references(child)


def freeze_verification(root: Path, artifact: str, *, framework_manifest: dict,
                        destination: Path, repository: Path) -> dict:
    """Freeze a historical validation route and all recursively bound evidence.

    This is a verification closure, not authorization or an execution closure.
    The validator must be an explicit bound input, never guessed from today's code.
    """
    validate_manifest(framework_manifest)
    rows = {r["path"]: dict(r) for r in framework_manifest["files"]}
    pending = [fingerprint(root / safe_relative(artifact), root)]
    visited = {}
    while pending:
        ref = pending.pop()
        name = ref["path"]
        if Path(name).is_absolute():
            # Host tools in nested plans are declarations, not project artifacts.
            continue
        if Path(name).parts[0] not in {"tools", "lib", "src", "contracts", "programs", "results", "operations", "run_logs", "tests", "docs", "external", "patches"}:
            # Package-relative members are authenticated by their containing
            # package manifest; they are not project-root references.
            continue
        digest = ref["sha256"].removeprefix("sha256:")
        if name in visited:
            if visited[name] != digest:
                raise ValueError(f"historical closure needs conflicting bytes at {name}")
            continue
        visited[name] = digest
        row = retain_reference(root, ref, repository=repository)
        rows[name] = row
        if name.endswith(".json"):
            try:
                value = json.loads(blob_path(root, digest).read_bytes())
            except (ValueError, UnicodeError):
                # Some bound diagnostic files merely carry a .json suffix. Their
                # bytes remain authenticated; the original validator decides validity.
                continue
            pending.extend(bound_references(value))
    if "tools/research_contracts.py" not in visited:
        raise ValueError("historical evidence does not explicitly bind its validator")
    # Preserve original validator inputs, including versioned schemas captured
    # before extraction. Its own closure check verifies its imported source list.
    body = {"schema": "gamma.enwiki9.experiment-closure.v1", "files": sorted(rows.values(), key=lambda r: r["path"]),
            "declaration": {"complete": True, "kind": "verification", "artifact": artifact,
                "validator": "tools/research_contracts.py", "runtime_requirements": ["Python >=3.11", "jsonschema"],
                "scope": "original bound validator and recursively bound project evidence; no training or codec execution"}}
    manifest = {**body, "closure_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest()}
    publish_immutable_artifact(destination, canonical_bytes(manifest) + b"\n")
    return manifest
