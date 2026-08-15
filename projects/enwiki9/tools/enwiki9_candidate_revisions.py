#!/usr/bin/env python3
"""Content-address and bind enwiki9 candidate source revisions."""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import shutil
import stat
from typing import Any

try:
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import research_contracts


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"
ADAPTIVE = ROOT / "operations" / "adaptive"
REVISIONS = ADAPTIVE / "candidate-revisions"
BLOBS = ADAPTIVE / "candidate-blobs" / "sha256"
LOCK = ADAPTIVE / "candidate-revisions.lock"
QUEUE_STATES = ("pending", "running", "completed", "failed", "cancelled")
IGNORED_PARTS = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
DERIVED_META_FIELDS = {
    "added",
    "decision",
    "latest_result",
    "measured",
    "promotion",
    "proof",
    "status",
    "triage",
    "verdict",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def compact_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _sha256(path: pathlib.Path) -> str:
    return research_contracts.file_digest(path, "sha256")


def _reference(path: pathlib.Path) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": f"sha256:{_sha256(path)}",
    }


def receipt_reference(path: pathlib.Path) -> dict[str, str]:
    return _reference(path)


def _ignored(relative_path: pathlib.Path) -> bool:
    return (
        any(part in IGNORED_PARTS or part.startswith(".") for part in relative_path.parts)
        or relative_path.suffix in IGNORED_SUFFIXES
    )


def candidate_files(
    candidate_id: str,
    programs_root: pathlib.Path | None = None,
) -> list[tuple[pathlib.Path, pathlib.Path]]:
    candidate_root = (PROGRAMS if programs_root is None else programs_root) / candidate_id
    if not candidate_root.is_dir():
        raise FileNotFoundError(f"candidate not found: {candidate_id}")
    files: list[tuple[pathlib.Path, pathlib.Path]] = []
    for path in sorted(candidate_root.rglob("*")):
        relative_path = path.relative_to(candidate_root)
        if _ignored(relative_path):
            continue
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(
                f"candidate revision cannot contain symlink: {relative_path}"
            )
        if not stat.S_ISREG(mode):
            raise ValueError(
                f"candidate revision cannot contain special file: {relative_path}"
            )
        files.append((relative_path, path))
    if not files:
        raise ValueError(f"candidate has no revision-addressable files: {candidate_id}")
    return files


def candidate_manifest(
    candidate_id: str,
    programs_root: pathlib.Path | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative_path, path in candidate_files(candidate_id, programs_root):
        if relative_path == pathlib.Path("meta.json"):
            metadata = _load_json(path)
            semantic_metadata = {
                key: value
                for key, value in metadata.items()
                if key not in DERIVED_META_FIELDS
            }
            content = research_contracts.canonical_bytes(semantic_metadata)
            digest = hashlib.sha256(content).hexdigest()
            size = len(content)
            normalization = "semantic-meta-v1"
        else:
            digest = _sha256(path)
            size = path.stat().st_size
            normalization = "verbatim"
        records.append(
            {
                "path": relative_path.as_posix(),
                "bytes": size,
                "sha256": digest,
                "blobPath": (
                    pathlib.Path("operations/adaptive/candidate-blobs/sha256")
                    / digest[:2]
                    / digest
                ).as_posix(),
                "normalization": normalization,
            }
        )
    return records


def candidate_tree_digest(records: list[dict[str, Any]]) -> str:
    return research_contracts.candidate_tree_digest(records)


def revision_paths(candidate_id: str) -> list[pathlib.Path]:
    return sorted((REVISIONS / candidate_id).glob("*.json"))


def latest_revision(candidate_id: str) -> tuple[pathlib.Path, dict[str, Any]] | None:
    paths = revision_paths(candidate_id)
    if not paths:
        return None
    path = paths[-1]
    return path, _load_json(path)


def candidate_has_evidence(candidate_id: str) -> bool:
    results = ROOT / "results" / candidate_id
    if results.is_dir() and any(results.rglob("*.json")):
        return True
    for state in QUEUE_STATES:
        for path in (ADAPTIVE / state).glob("*.json"):
            try:
                if _load_json(path).get("candidate_id") == candidate_id:
                    return True
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    return False


def _store_blobs(candidate_id: str, records: list[dict[str, Any]]) -> None:
    source_by_path = dict(candidate_files(candidate_id))
    for record in records:
        source = source_by_path[pathlib.Path(record["path"])]
        blob = ROOT / record["blobPath"]
        blob.parent.mkdir(parents=True, exist_ok=True)
        if blob.exists():
            if blob.stat().st_size != record["bytes"] or _sha256(blob) != record["sha256"]:
                raise ValueError(f"content-addressed blob is corrupt: {blob}")
            continue
        temporary = blob.with_name(f".{blob.name}.{os.getpid()}.tmp")
        if record["normalization"] == "semantic-meta-v1":
            metadata = _load_json(source)
            semantic_metadata = {
                key: value
                for key, value in metadata.items()
                if key not in DERIVED_META_FIELDS
            }
            temporary.write_bytes(
                research_contracts.canonical_bytes(semantic_metadata)
            )
        else:
            shutil.copyfile(source, temporary)
        if temporary.stat().st_size != record["bytes"] or _sha256(temporary) != record["sha256"]:
            temporary.unlink(missing_ok=True)
            raise ValueError(f"candidate changed while snapshotting: {source}")
        os.replace(temporary, blob)


def _parent_reference(parent_id: str | None) -> dict[str, Any] | None:
    if parent_id is None:
        return None
    parent_path, parent = ensure_current_revision(parent_id)
    return {
        "candidateId": parent_id,
        "candidateTreeSha256": parent["candidateTreeSha256"],
        "receipt": _reference(parent_path),
    }


def record_revision(
    *,
    candidate_id: str,
    kind: str,
    hypothesis: str,
    summary: list[str],
    evidence: list[str] | None = None,
    replacements: list[dict[str, str]] | None = None,
    parent_id: str | None = None,
    provenance_class: str = "native",
    allow_measured_legacy_adoption: bool = False,
) -> tuple[pathlib.Path, dict[str, Any]]:
    if not hypothesis.strip():
        raise ValueError("candidate revision requires a hypothesis")
    if not summary or any(not item.strip() for item in summary):
        raise ValueError("candidate revision requires a non-empty change summary")
    parent_revision = _parent_reference(parent_id)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        records = candidate_manifest(candidate_id)
        tree_digest = candidate_tree_digest(records)
        previous = latest_revision(candidate_id)
        if previous is not None and previous[1]["candidateTreeSha256"] == tree_digest:
            return previous
        if (
            previous is not None
            and candidate_has_evidence(candidate_id)
            and not allow_measured_legacy_adoption
        ):
            raise ValueError(
                f"candidate {candidate_id} already has queued or measured evidence; "
                "create a new candidate with mutate"
            )
        _store_blobs(candidate_id, records)
        receipt = {
            "schema": "gamma.enwiki9.candidate-revision.v1",
            "objective": research_contracts.objective_binding(),
            "candidateId": candidate_id,
            "candidateTreeSha256": tree_digest,
            "treeDigestAlgorithm": "sha256-canonical-counted-files-v1",
            "files": records,
            "parentRevision": parent_revision,
            "previousRevision": _reference(previous[0]) if previous else None,
            "change": {
                "kind": kind,
                "hypothesis": hypothesis.strip(),
                "summary": sorted(set(summary)),
                "evidence": sorted(set(evidence or [])),
                "replacements": replacements or [],
            },
            "provenanceClass": provenance_class,
            "immutableBlobsComplete": True,
            "generatedUtc": utc_now(),
        }
        path = (
            REVISIONS
            / candidate_id
            / f"{compact_utc()}_{tree_digest.removeprefix('sha256:')[:12]}.json"
        )
        _atomic_json(path, receipt)
        try:
            research_contracts.validate_artifact(path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return path, receipt


def ensure_current_revision(candidate_id: str) -> tuple[pathlib.Path, dict[str, Any]]:
    latest = latest_revision(candidate_id)
    if latest is None:
        metadata = _load_json(PROGRAMS / candidate_id / "meta.json")
        hypothesis = str(
            metadata.get("hypothesis")
            or metadata.get("description")
            or "Legacy candidate state adopted without retroactive provenance"
        )
        return record_revision(
            candidate_id=candidate_id,
            kind="legacy-adoption",
            hypothesis=hypothesis,
            summary=["Captured current legacy source state; not retroactive evidence."],
            parent_id=(
                metadata.get("parent")
                if isinstance(metadata.get("parent"), str)
                else None
            ),
            provenance_class="legacy-current-state",
            allow_measured_legacy_adoption=True,
        )
    records = candidate_manifest(candidate_id)
    current_digest = candidate_tree_digest(records)
    if latest[1]["candidateTreeSha256"] != current_digest:
        raise ValueError(
            f"candidate {candidate_id} differs from its latest revision; run "
            "enwiki9_lab.py seal before first measurement or mutate to a new ID"
        )
    research_contracts.validate_artifact(latest[0])
    return latest


def seal_candidate(
    candidate_id: str,
    *,
    hypothesis: str,
    summary: list[str],
    evidence: list[str],
) -> tuple[pathlib.Path, dict[str, Any]]:
    metadata = _load_json(PROGRAMS / candidate_id / "meta.json")
    parent_id = metadata.get("parent")
    return record_revision(
        candidate_id=candidate_id,
        kind="implementation",
        hypothesis=hypothesis,
        summary=summary,
        evidence=evidence,
        parent_id=parent_id if isinstance(parent_id, str) else None,
    )


def verify_job_binding(job: dict[str, Any]) -> tuple[pathlib.Path, dict[str, Any]]:
    candidate_id = job.get("candidate_id")
    if not isinstance(candidate_id, str):
        raise ValueError("job lacks candidate_id")
    binding = job.get("candidate_revision")
    if not isinstance(binding, dict):
        raise ValueError("unbound legacy job cannot execute; enqueue a revision-bound retry")
    path, receipt = ensure_current_revision(candidate_id)
    expected = _reference(path)
    if binding != expected:
        raise ValueError(f"job binds a different candidate revision: {candidate_id}")
    if job.get("candidate_tree_sha256") != receipt["candidateTreeSha256"]:
        raise ValueError(f"job candidate tree digest differs: {candidate_id}")
    return path, receipt


def materialize_revision(
    receipt: dict[str, Any],
    destination: pathlib.Path,
) -> pathlib.Path:
    if destination.exists():
        raise FileExistsError(f"snapshot destination already exists: {destination}")
    destination.mkdir(parents=True)
    for record in receipt["files"]:
        blob = ROOT / record["blobPath"]
        if not blob.is_file() or _sha256(blob) != record["sha256"]:
            raise ValueError(f"candidate snapshot blob is missing or corrupt: {blob}")
        output = destination / record["path"]
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(blob, output)
        output.chmod(0o444)
    materialized = candidate_manifest_from_root(destination)
    if candidate_tree_digest(materialized) != receipt["candidateTreeSha256"]:
        raise ValueError("materialized candidate snapshot differs from its receipt")
    return destination


def candidate_manifest_from_root(candidate_root: pathlib.Path) -> list[dict[str, Any]]:
    return candidate_manifest(candidate_root.name, candidate_root.parent)
