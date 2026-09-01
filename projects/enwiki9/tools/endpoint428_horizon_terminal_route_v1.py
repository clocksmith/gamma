#!/usr/bin/env python3
"""Route one reflected terminal Endpoint428 HORIZON v1 job, fail closed.

Before terminality this program inspects only the adaptive pending/running
namespaces.  Every project path is traversed with openat/O_NOFOLLOW.  After a
single reflected terminal job is established, declared outputs are hashed as
opaque bytes and only decision.json is semantically decoded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import jsonschema


PROJECT = Path(__file__).absolute().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_q0_v1"
PROPOSAL_ID = CANDIDATE_ID
RECEIPT_SCHEMA = "gamma.enwiki9.endpoint428-horizon-terminal-route.v1"
RECEIPT_PATH = (
    "operations/evidence/endpoint428_horizon_retained_parent_trace_terminal_route_q0_v1.json"
)
JSON_MAX_BYTES = 64 * 1024 * 1024
JOB_ID = "20260830T224837Z_a120752fb5"
JOB_FILE = f"000_{JOB_ID}.json"
JOB_GATE_SIZE = 647_798_592
JOB_PRIORITY = 1700
JOB_PURPOSE = "diagnostic"
JOB_TAGS = ["endpoint428", "full-wrt", "horizon", "retained-parent"]
JOB_SCRATCH_DIRECTORIES = [f"results/{CANDIDATE_ID}"]
JOB_TOOL_ARGS: list[str] = []
JOB_SUBMITTED_AT = "2026-08-30T22:48:37+00:00"
JOB_STARTED_AT = "2026-08-30T22:51:59+00:00"

EXPERIMENT_PATH = (
    "operations/adaptive/experiments/"
    "endpoint428_horizon_retained_parent_trace_q0_v1.json"
)
EXPERIMENT_SHA256 = "sha256:1ee83f431531f05654ac0990de302acbbbde36fa4ac42acd3bebbd9dd26f20aa"
PROPOSAL_PATH = (
    "operations/adaptive/proposals/developed/"
    "000_endpoint428_horizon_retained_parent_trace_q0_v1.json"
)
PROPOSAL_SHA256 = "sha256:5df724d51eb28e7ebaaea782210960e32ad95ad7fac374f6ccfff597f1eaaa62"
REVISION_PATH = (
    "operations/adaptive/candidate-revisions/"
    "endpoint428_horizon_retained_parent_trace_q0_v1/"
    "20260830T224806838440Z_565130472695.json"
)
REVISION_SHA256 = "sha256:f27573bb08cac47dfe9ed0915617a692c72d8fa5f0c406c0517e3664574013f4"
CANDIDATE_TREE_SHA256 = "sha256:5651304726959ad418741f2b0754723aaff7d1cf260f67f716b5ced77c06ceeb"
RUNNER_PATH = "tools/endpoint428_horizon_retained_parent_trace_q0_v1.py"
RUNNER_SHA256 = "sha256:f1f309dfc58f704d316af840b91cdefedbe277da87347a05fbed5c10121645a1"

RESULT_ROOT = f"results/{CANDIDATE_ID}"
DECISION_PATH = f"{RESULT_ROOT}/decision.json"
EXPECTED_OUTPUTS = [
    f"{RESULT_ROOT}/manifest-a.bin",
    f"{RESULT_ROOT}/manifest-b.bin",
    f"{RESULT_ROOT}/parent.p1",
    f"{RESULT_ROOT}/parent.archive",
    f"{RESULT_ROOT}/analysis-a.json",
    f"{RESULT_ROOT}/analysis-b.json",
    DECISION_PATH,
]
EXPECTED_OUTPUT_NAMES = [PurePosixPath(path).name for path in EXPECTED_OUTPUTS]

BRANCH_CORRECTION = "CORRECTION_RETRY_ONLY"
BRANCH_QUARANTINE = "QUARANTINE_AND_CORRECT"
BRANCH_RETIRE = "RETIRE_PHYSICAL_HORIZON"
BRANCH_REPRICE = "EXACT_REPRICE_Q0_V2"
TERMINAL_BRANCHES = {
    BRANCH_CORRECTION,
    BRANCH_QUARANTINE,
    BRANCH_RETIRE,
    BRANCH_REPRICE,
}

EXPECTED_PROMOTION_PREDICATES = [
    ("complete-active-population", "activeBytes", "eq", 2_331_505),
    ("complete-parent-trace", "parentTraceRows", "eq", 5_182_388_736),
    ("target-bearing-mixture", "treatmentMixtureGainBits", "gte", 40_163_160),
    ("every-third-positive", "minimumThirdMixtureGainBits", "gt", 0),
    ("controls-separated", "minimumControlMarginBits", "gt", 0),
    ("manifest-repeat", "manifestRepeatIdentityPass", "eq", True),
    ("analysis-repeat", "analysisRepeatIdentityPass", "eq", True),
    ("read-only-parent", "parentReadOnlyPass", "eq", True),
]
EXPECTED_KILL_PREDICATES = [
    ("subscale", "treatmentMixtureGainBits", "lt", 40_163_160),
    ("third-failure", "minimumThirdMixtureGainBits", "lte", 0),
    ("control-failure", "minimumControlMarginBits", "lte", 0),
    ("trace-or-repeat-failure", "parentReadOnlyPass", "eq", False),
]
EXPECTED_GATE_MEASUREMENTS = {
    "targetBearingMixturePass": "treatmentMixtureGainBits",
    "everyThirdPositivePass": "minimumThirdMixtureGainBits",
    "controlsSeparatedPass": "minimumControlMarginBits",
    "manifestRepeatPass": "manifestRepeatIdentityPass",
    "analysisRepeatPass": "analysisRepeatIdentityPass",
    "parentReadOnlyPass": "parentReadOnlyPass",
}
PROMOTION_BY_MEASUREMENT = {
    measurement: (operator, threshold)
    for _identifier, measurement, operator, threshold in EXPECTED_PROMOTION_PREDICATES
}
INTEGRITY_PREDICATE_IDS = {
    "complete-active-population",
    "complete-parent-trace",
    "manifest-repeat",
    "analysis-repeat",
    "read-only-parent",
}
SCIENTIFIC_KILL_PREDICATE_IDS = {"subscale", "third-failure", "control-failure"}

SCHEMA_PATHS = {
    "job": "contracts/research/v1/adaptive-job.schema.json",
    "proposal": "contracts/research/v1/algorithm-proposal.schema.json",
    "experiment": "contracts/research/v1/adaptive-experiment-contract.schema.json",
    "revision": "contracts/research/v1/candidate-revision.schema.json",
    "reflection": "contracts/research/v1/reflection-receipt.schema.json",
    "receipt": "contracts/research/v1/endpoint428-horizon-terminal-route.schema.json",
}


class RouteError(RuntimeError):
    """Evidence is unavailable, malformed, drifted, or contradictory."""


def _safe_parts(relative: str) -> tuple[str, ...]:
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RouteError(f"unsafe project-relative path: {relative!r}")
    return path.parts


class ProjectReader:
    """Race-resistant, no-follow reader confined below one non-symlink root."""

    def __init__(self, root: Path):
        self.root = Path(os.path.abspath(os.fspath(root)))
        try:
            metadata = os.lstat(self.root)
        except OSError as error:
            raise RouteError(f"project root is unavailable: {self.root}") from error
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise RouteError(f"project root is not a non-symlink directory: {self.root}")
        try:
            self._root_fd = os.open(
                self.root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            )
        except OSError as error:
            raise RouteError(f"cannot open project root without following links: {self.root}") from error

    def close(self) -> None:
        if self._root_fd >= 0:
            os.close(self._root_fd)
            self._root_fd = -1

    def __enter__(self) -> "ProjectReader":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _open_dir(self, relative: str) -> int:
        parts = _safe_parts(relative)
        descriptor = os.dup(self._root_fd)
        try:
            for part in parts:
                next_descriptor = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=descriptor,
                )
                os.close(descriptor)
                descriptor = next_descriptor
                if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    raise RouteError(f"path component is not a directory: {relative}")
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def list_dir(self, relative: str) -> list[str]:
        descriptor = self._open_dir(relative)
        try:
            return sorted(os.listdir(descriptor))
        finally:
            os.close(descriptor)

    def entry_mode(self, directory: str, name: str) -> int:
        if name in {"", ".", ".."} or "/" in name:
            raise RouteError(f"unsafe directory entry: {name!r}")
        descriptor = self._open_dir(directory)
        try:
            return os.stat(name, dir_fd=descriptor, follow_symlinks=False).st_mode
        finally:
            os.close(descriptor)

    def _open_regular(self, relative: str) -> int:
        parts = _safe_parts(relative)
        parent = "/".join(parts[:-1])
        parent_fd = os.dup(self._root_fd) if not parent else self._open_dir(parent)
        try:
            descriptor = os.open(
                parts[-1],
                os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent_fd,
            )
        except BaseException:
            os.close(parent_fd)
            raise
        os.close(parent_fd)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            raise RouteError(f"artifact is not a regular non-symlink file: {relative}")
        return descriptor

    def read_file(self, relative: str, *, max_bytes: int = JSON_MAX_BYTES) -> bytes:
        descriptor = self._open_regular(relative)
        try:
            size = os.fstat(descriptor).st_size
            if size > max_bytes:
                raise RouteError(f"artifact exceeds bounded read limit: {relative}")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise RouteError(f"artifact exceeds bounded read limit: {relative}")
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(descriptor)

    @staticmethod
    def _identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
        return (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )

    def artifact_snapshot(
        self, relative: str
    ) -> tuple[dict[str, Any], tuple[int, int, int, int, int]]:
        descriptor = self._open_regular(relative)
        digest = hashlib.sha256()
        size = 0
        try:
            before = os.fstat(descriptor)
            while True:
                chunk = os.read(descriptor, 4 * 1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                digest.update(chunk)
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        if self._identity(before) != self._identity(after):
            raise RouteError(f"artifact changed while it was hashed: {relative}")
        if size != after.st_size:
            raise RouteError(f"artifact size changed while it was hashed: {relative}")
        identity = self._identity(after)
        self.assert_identity(relative, identity)
        return (
            {
                "path": relative,
                "bytes": size,
                "sha256": "sha256:" + digest.hexdigest(),
            },
            identity,
        )

    def artifact(self, relative: str) -> dict[str, Any]:
        artifact, _identity = self.artifact_snapshot(relative)
        return artifact

    def assert_identity(
        self, relative: str, expected: tuple[int, int, int, int, int]
    ) -> None:
        descriptor = self._open_regular(relative)
        try:
            observed = self._identity(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        if observed != expected:
            raise RouteError(f"artifact pathname changed after hashing: {relative}")

    def write_new_json(self, relative: str, value: dict[str, Any]) -> None:
        parts = _safe_parts(relative)
        parent = "/".join(parts[:-1])
        parent_fd = os.dup(self._root_fd) if not parent else self._open_dir(parent)
        temporary_name = f".{parts[-1]}.tmp-{os.getpid()}"
        descriptor = -1
        linked = False
        try:
            payload = (
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).encode("utf-8")
            descriptor = os.open(
                temporary_name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | os.O_CLOEXEC,
                0o644,
                dir_fd=parent_fd,
            )
            offset = 0
            while offset < len(payload):
                offset += os.write(descriptor, payload[offset:])
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.link(
                temporary_name,
                parts[-1],
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
            linked = True
            os.unlink(temporary_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except FileExistsError as error:
            raise RouteError(f"receipt path already exists: {relative}") from error
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if not linked:
                try:
                    os.unlink(temporary_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
            os.close(parent_fd)


def _reject_nonfinite_json(token: str) -> None:
    raise RouteError(f"nonfinite JSON number is forbidden: {token}")


def _parse_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, parse_constant=_reject_nonfinite_json)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RouteError(f"invalid JSON artifact: {label}") from error
    if not isinstance(value, dict):
        raise RouteError(f"JSON root is not an object: {label}")
    return value


def _artifact(path: str, raw: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "bytes": len(raw),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }


def _read_json(reader: ProjectReader, path: str) -> tuple[dict[str, Any], bytes]:
    raw = reader.read_file(path)
    return _parse_json(raw, path), raw


_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


def _schema(kind: str) -> dict[str, Any]:
    if kind not in _SCHEMA_CACHE:
        with ProjectReader(PROJECT) as reader:
            value, _raw = _read_json(reader, SCHEMA_PATHS[kind])
        jsonschema.Draft202012Validator.check_schema(value)
        _SCHEMA_CACHE[kind] = value
    return _SCHEMA_CACHE[kind]


def _validate(value: Any, kind: str, label: str) -> None:
    validator = jsonschema.Draft202012Validator(
        _schema(kind), format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(validator.iter_errors(value), key=lambda row: list(row.absolute_path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise RouteError(f"{label} fails canonical {kind} schema at {location}: {errors[0].message}")


def _finish(receipt: dict[str, Any]) -> dict[str, Any]:
    _validate(receipt, "receipt", "router receipt")
    try:
        json.dumps(receipt, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise RouteError("router receipt is not finite canonical JSON") from error
    return receipt


def _reference(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise RouteError(f"malformed {label} reference")
    path, digest = value.get("path"), value.get("sha256")
    if not isinstance(path, str):
        raise RouteError(f"malformed {label} path")
    _safe_parts(path)
    if (
        not isinstance(digest, str)
        or len(digest) != 71
        or not digest.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in digest[7:])
    ):
        raise RouteError(f"malformed {label} digest")
    return {"path": path, "sha256": digest}


def _verify_reference(
    reader: ProjectReader,
    value: Any,
    label: str,
    *,
    expected_path: str,
    expected_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    reference = _reference(value, label)
    if reference["path"] != expected_path:
        raise RouteError(f"{label} path mismatch")
    raw = reader.read_file(expected_path)
    artifact = _artifact(expected_path, raw)
    if artifact["sha256"] != reference["sha256"]:
        raise RouteError(f"{label} SHA-256 mismatch")
    if expected_sha256 is not None and artifact["sha256"] != expected_sha256:
        raise RouteError(f"frozen {label} SHA-256 mismatch")
    return _parse_json(raw, label), artifact


def _active_records(reader: ProjectReader) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for state in ("pending", "running"):
        directory = f"operations/adaptive/{state}"
        try:
            names = reader.list_dir(directory)
        except (OSError, RouteError):
            blockers.append(
                {
                    "path": directory,
                    "state": state,
                    "job_id": None,
                    "reason": "unsafe-active-namespace",
                }
            )
            continue
        if JOB_FILE not in names:
            continue
        path = f"{directory}/{JOB_FILE}"
        try:
            if not stat.S_ISREG(reader.entry_mode(directory, JOB_FILE)):
                raise RouteError("nonregular active record")
            value, _raw = _read_json(reader, path)
            _validate(value, "job", "active job")
        except (OSError, RouteError):
            blockers.append(
                {
                    "path": path,
                    "state": state,
                    "job_id": None,
                    "reason": "unreadable-active-record",
                }
            )
            continue
        job_id = value.get("job_id")
        if value.get("candidate_id") != CANDIDATE_ID or job_id != JOB_ID:
            blockers.append(
                {
                    "path": path,
                    "state": state,
                    "job_id": job_id if isinstance(job_id, str) else None,
                    "reason": "frozen-job-identity-drift",
                }
            )
            continue
        blockers.append(
            {
                "path": path,
                "state": state,
                "job_id": job_id,
                "reason": "candidate-nonterminal",
            }
        )
    return blockers


def _blocked_receipt(active: list[dict[str, Any]]) -> dict[str, Any]:
    return _finish(
        {
            "schema": RECEIPT_SCHEMA,
            "candidate_id": CANDIDATE_ID,
            "status": "BLOCKED_NONTERMINAL",
            "active_jobs": active,
            "decision_accessed": False,
            "result_root_accessed": False,
            "claim_authority": "none",
        }
    )


def _one_terminal_job(
    reader: ProjectReader,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    matches: list[tuple[str, str, dict[str, Any], bytes]] = []
    for state in ("completed", "failed", "cancelled"):
        directory = f"operations/adaptive/{state}"
        try:
            names = reader.list_dir(directory)
        except (OSError, RouteError) as error:
            raise RouteError(f"unsafe terminal namespace: {directory}") from error
        if JOB_FILE not in names:
            continue
        path = f"{directory}/{JOB_FILE}"
        try:
            if not stat.S_ISREG(reader.entry_mode(directory, JOB_FILE)):
                raise RouteError(f"nonregular terminal job record: {path}")
            value, raw = _read_json(reader, path)
        except (OSError, RouteError) as error:
            raise RouteError(f"unreadable terminal job record: {path}") from error
        matches.append((state, path, value, raw))
    if len(matches) != 1:
        raise RouteError(f"expected exactly one terminal HORIZON job, observed {len(matches)}")
    state, path, job, raw = matches[0]
    _validate(job, "job", "terminal job")
    if path != f"operations/adaptive/{state}/{JOB_FILE}":
        raise RouteError("terminal job path differs from the frozen live job")
    if (
        job.get("state") != state
        or job.get("job_id") != JOB_ID
        or job.get("priority") != JOB_PRIORITY
        or job.get("purpose") != JOB_PURPOSE
        or job.get("tags") != JOB_TAGS
        or job.get("scratch_directories") != JOB_SCRATCH_DIRECTORIES
        or job.get("tool") != RUNNER_PATH
        or job.get("tool_args") != JOB_TOOL_ARGS
        or job.get("submitted_at") != JOB_SUBMITTED_AT
        or job.get("started_at") != JOB_STARTED_AT
    ):
        raise RouteError("terminal job lifecycle differs from the frozen live job")
    returncode = job.get("returncode")
    if state == "completed" and (isinstance(returncode, bool) or returncode != 0):
        raise RouteError("completed terminal job must have returncode 0")
    if state == "failed" and (
        isinstance(returncode, bool) or not isinstance(returncode, int) or returncode == 0
    ):
        raise RouteError("failed terminal job must have nonzero integer returncode")
    if state == "cancelled" and returncode is not None:
        raise RouteError("cancelled terminal job must have null returncode")
    terminal_timestamp = "cancelled_at" if state == "cancelled" else "finished_at"
    if not isinstance(job.get(terminal_timestamp), str) or not job[terminal_timestamp]:
        raise RouteError(f"terminal job lacks {terminal_timestamp}")
    return path, job, _artifact(path, raw)


def _verify_frozen_inputs(
    reader: ProjectReader, job: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if (
        job.get("candidate_id") != CANDIDATE_ID
        or job.get("candidate_tree_sha256") != CANDIDATE_TREE_SHA256
        or job.get("proposal_id") != PROPOSAL_ID
        or job.get("gate_size") != JOB_GATE_SIZE
    ):
        raise RouteError("terminal job candidate, tree, proposal, or gate identity mismatch")

    experiment, experiment_artifact = _verify_reference(
        reader,
        job.get("experiment"),
        "experiment",
        expected_path=EXPERIMENT_PATH,
        expected_sha256=EXPERIMENT_SHA256,
    )
    _validate(experiment, "experiment", "frozen experiment")
    observed_promotion = [
        (row.get("id"), row.get("measurement"), row.get("operator"), row.get("threshold"))
        for row in experiment.get("promotionPredicates", [])
        if isinstance(row, dict)
    ]
    observed_kill = [
        (row.get("id"), row.get("measurement"), row.get("operator"), row.get("threshold"))
        for row in experiment.get("killPredicates", [])
        if isinstance(row, dict)
    ]
    if (
        experiment.get("experimentId") != CANDIDATE_ID
        or experiment.get("proposalId") != PROPOSAL_ID
        or experiment.get("status") != "frozen"
        or experiment.get("registrationTiming") != "prospective"
        or experiment.get("outputs") != EXPECTED_OUTPUTS
        or experiment.get("outputManifestPolicy") != "complete-result-artifacts-v1"
        or observed_promotion != EXPECTED_PROMOTION_PREDICATES
        or observed_kill != EXPECTED_KILL_PREDICATES
    ):
        raise RouteError("frozen v1 experiment identity or predicates mismatch")

    proposal, proposal_artifact = _verify_reference(
        reader,
        job.get("proposal"),
        "proposal",
        expected_path=PROPOSAL_PATH,
        expected_sha256=PROPOSAL_SHA256,
    )
    _validate(proposal, "proposal", "frozen proposal")
    if (
        proposal.get("proposal_id") != PROPOSAL_ID
        or proposal.get("candidate_id") != CANDIDATE_ID
        or proposal.get("state") != "developed"
        or proposal.get("experiment")
        != {"path": EXPERIMENT_PATH, "sha256": EXPERIMENT_SHA256}
    ):
        raise RouteError("frozen proposal identity mismatch")

    revision, revision_artifact = _verify_reference(
        reader,
        job.get("candidate_revision"),
        "candidate revision",
        expected_path=REVISION_PATH,
        expected_sha256=REVISION_SHA256,
    )
    _validate(revision, "revision", "frozen candidate revision")
    if (
        revision.get("candidateId") != CANDIDATE_ID
        or revision.get("candidateTreeSha256") != CANDIDATE_TREE_SHA256
    ):
        raise RouteError("frozen candidate revision identity mismatch")

    runner_reference = _reference(job.get("runner"), "runner")
    if runner_reference != {"path": RUNNER_PATH, "sha256": RUNNER_SHA256}:
        raise RouteError("frozen runner reference mismatch")
    runner_raw = reader.read_file(RUNNER_PATH)
    runner_artifact = _artifact(RUNNER_PATH, runner_raw)
    if runner_artifact["sha256"] != RUNNER_SHA256:
        raise RouteError("frozen runner SHA-256 mismatch")
    return experiment_artifact, proposal_artifact, revision_artifact, runner_artifact


def _verify_reflection(
    reader: ProjectReader,
    job: dict[str, Any],
    job_artifact: dict[str, Any],
    experiment_artifact: dict[str, Any],
    revision_artifact: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str] | None]:
    path = f"operations/adaptive/reflections/{job['job_id']}.json"
    reflection, raw = _read_json(reader, path)
    _validate(reflection, "reflection", "terminal reflection")
    candidate_revision = reflection.get("candidateRevision")
    if (
        reflection.get("candidateId") != CANDIDATE_ID
        or _reference(reflection.get("job"), "reflection job")
        != {"path": job_artifact["path"], "sha256": job_artifact["sha256"]}
        or _reference(reflection.get("experiment"), "reflection experiment")
        != {
            "path": experiment_artifact["path"],
            "sha256": experiment_artifact["sha256"],
        }
        or not isinstance(candidate_revision, dict)
        or candidate_revision.get("candidateId") != CANDIDATE_ID
        or candidate_revision.get("candidateTreeSha256") != CANDIDATE_TREE_SHA256
        or _reference(candidate_revision.get("receipt"), "reflection revision")
        != {"path": revision_artifact["path"], "sha256": revision_artifact["sha256"]}
    ):
        raise RouteError("reflection does not bind the exact terminal job and frozen inputs")
    evidence = reflection.get("evidence")
    assert isinstance(evidence, list)  # guaranteed by the canonical schema
    decisions = [
        _reference(row, "reflection decision evidence")
        for row in evidence
        if isinstance(row, dict) and row.get("path") == DECISION_PATH
    ]
    state = job["state"]
    if state == "completed" and len(decisions) != 1:
        raise RouteError("completed scientific job must bind exactly one final decision")
    if state in {"failed", "cancelled"} and decisions:
        raise RouteError("failed or cancelled reflection must not claim a scientific decision")
    return reflection, _artifact(path, raw), decisions[0] if decisions else None


def _opaque_output_closure(reader: ProjectReader) -> dict[str, Any]:
    try:
        names = reader.list_dir(RESULT_ROOT)
        namespace_safe = True
    except (OSError, RouteError):
        names = []
        namespace_safe = False
    expected = set(EXPECTED_OUTPUT_NAMES)
    observed = set(names)
    missing = sorted(expected - observed)
    extras = sorted(observed - expected)
    nonregular: list[str] = []
    artifacts: list[dict[str, Any]] = []
    identities: dict[str, tuple[int, int, int, int, int]] = {}
    for path, name in zip(EXPECTED_OUTPUTS, EXPECTED_OUTPUT_NAMES):
        if name not in observed:
            continue
        try:
            if not stat.S_ISREG(reader.entry_mode(RESULT_ROOT, name)):
                raise RouteError("nonregular output")
            artifact, identity = reader.artifact_snapshot(path)
        except (OSError, RouteError):
            nonregular.append(name)
            continue
        artifacts.append(artifact)
        identities[path] = identity
    try:
        final_names = reader.list_dir(RESULT_ROOT)
    except (OSError, RouteError) as error:
        raise RouteError("result namespace changed during output closure") from error
    if final_names != names:
        raise RouteError("result namespace changed during output closure")
    for path, identity in identities.items():
        reader.assert_identity(path, identity)
    failure_class: str | None = None
    if not namespace_safe or missing or nonregular:
        failure_class = "nonregular-or-missing"
    elif extras:
        failure_class = "undeclared-extras"
    artifact_names = [PurePosixPath(row["path"]).name for row in artifacts]
    return {
        "complete": failure_class is None and len(artifacts) == len(EXPECTED_OUTPUTS),
        "failure_class": failure_class,
        "namespace_safe": namespace_safe,
        "declared_output_count": len(EXPECTED_OUTPUTS),
        "bound_output_count": len(artifacts),
        "artifact_names": artifact_names,
        "missing": missing,
        "nonregular": sorted(nonregular),
        "extras": extras,
        "artifacts": artifacts,
    }


def _operator(operator: str, observed: Any, threshold: Any) -> bool:
    for value in (observed, threshold):
        if isinstance(value, float) and not math.isfinite(value):
            raise RouteError("nonfinite predicate number is forbidden")
    if operator == "eq":
        return observed == threshold and type(observed) is type(threshold)
    if (
        isinstance(observed, bool)
        or not isinstance(observed, (int, float))
        or isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
    ):
        raise RouteError(f"nonnumeric value for operator {operator}")
    if operator == "gte":
        return observed >= threshold
    if operator == "gt":
        return observed > threshold
    if operator == "lt":
        return observed < threshold
    if operator == "lte":
        return observed <= threshold
    raise RouteError(f"unsupported frozen predicate operator: {operator}")


def _evaluate(
    rows: Iterable[tuple[str, str, str, Any]], measurements: dict[str, Any]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for identifier, measurement, operator, threshold in rows:
        if measurement not in measurements:
            raise RouteError(f"decision measurement is missing: {measurement}")
        observed = measurements[measurement]
        result.append(
            {
                "predicate_id": identifier,
                "measurement_id": measurement,
                "operator": operator,
                "threshold": threshold,
                "observed": observed,
                "result": _operator(operator, observed, threshold),
            }
        )
    return result


def _decision_consistency(
    decision: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, bool]]:
    if (
        decision.get("schema")
        != "gamma.enwiki9.endpoint428-horizon-retained-parent-trace-decision.v1"
        or decision.get("candidate_id") != CANDIDATE_ID
        or decision.get("evidence_class") != "causal-shadow"
        or decision.get("archive_authority") is not False
        or decision.get("score_credit_bytes") != 0
        or decision.get("verified_full_1g_score_bytes") is not None
    ):
        raise RouteError("terminal decision identity or claim boundary mismatch")
    measurements, gates = decision.get("measurements"), decision.get("gates")
    if not isinstance(measurements, dict) or not isinstance(gates, dict):
        raise RouteError("terminal decision measurements or gates are missing")
    promotion = _evaluate(EXPECTED_PROMOTION_PREDICATES, measurements)
    kill = _evaluate(EXPECTED_KILL_PREDICATES, measurements)
    promotion_pass = all(row["result"] for row in promotion)
    kill_pass = any(row["result"] for row in kill)
    expected_gates = {
        gate: _operator(
            PROMOTION_BY_MEASUREMENT[measurement][0],
            measurements[measurement],
            PROMOTION_BY_MEASUREMENT[measurement][1],
        )
        for gate, measurement in EXPECTED_GATE_MEASUREMENTS.items()
    }
    consistency = {
        "decision_gates_match_recomputed": gates == expected_gates,
        "decision_promotion_matches_recomputed": decision.get("promotion_authorized")
        is promotion_pass,
        "decision_verdict_matches_recomputed": decision.get("verdict")
        == (
            "authorize_one_native_horizon_pkd_finite_coder"
            if promotion_pass
            else "retire_endpoint428_physical_horizon_a"
        ),
        "promotion_predicates_pass": promotion_pass,
        "kill_predicates_pass": kill_pass,
    }
    if not all(
        consistency[key]
        for key in (
            "decision_gates_match_recomputed",
            "decision_promotion_matches_recomputed",
            "decision_verdict_matches_recomputed",
        )
    ):
        raise RouteError("terminal decision contradicts recomputed frozen predicates")
    return promotion, kill, consistency


def _failure_branch(reflection: dict[str, Any]) -> tuple[str, str]:
    validity = reflection["validity"]
    hypothesis = reflection["hypothesis"]
    attribution = reflection["attribution"]
    decision = reflection["decision"]
    classification = validity["classification"]
    failure_class = attribution["failureClass"]
    expected = {
        "implementation-failure": "implementation-failure",
        "infrastructure-failure": "infrastructure-failure",
        "incomplete-evidence": "inconclusive",
    }
    common = (
        validity["valid"] is False
        and hypothesis["verdict"] in {"not-tested", "inconclusive"}
        and decision["verdict"] == "retry"
        and decision["promotionPredicatesPass"] is None
        and decision["killPredicatesPass"] is None
        and decision["nextGateBytes"] is None
    )
    if classification in expected:
        if not common or failure_class != expected[classification] or attribution["controlsEquivalent"] is not None:
            raise RouteError("conflicting correction failure classifiers")
        return BRANCH_CORRECTION, "reflected terminal implementation, infrastructure, or evidence failure"
    if classification == "invalid-experiment":
        if (
            not common
            or failure_class not in {"causal-failure", "invalid-experiment"}
            or attribution["controlsEquivalent"] is not False
        ):
            raise RouteError("conflicting causal-invalidity classifiers")
        return BRANCH_QUARANTINE, "reflected terminal causal or provenance invalidity"
    raise RouteError("failed or cancelled reflection has unsupported classifiers")


def _scientific_branch(
    reflection: dict[str, Any],
    promotion: list[dict[str, Any]],
    kill: list[dict[str, Any]],
    consistency: dict[str, bool],
) -> tuple[str, str]:
    validity = reflection["validity"]
    hypothesis = reflection["hypothesis"]
    attribution = reflection["attribution"]
    decision = reflection["decision"]
    if (
        validity["valid"] is not True
        or validity["classification"] != "valid"
        or attribution["controlsEquivalent"] is not True
    ):
        raise RouteError("scientific branch requires valid equivalent controls")
    promotion_pass = consistency["promotion_predicates_pass"]
    kill_pass = consistency["kill_predicates_pass"]
    integrity_pass = all(
        row["result"]
        for row in promotion
        if row["predicate_id"] in INTEGRITY_PREDICATE_IDS
    )
    scientific_kill_pass = any(
        row["result"]
        for row in kill
        if row["predicate_id"] in SCIENTIFIC_KILL_PREDICATE_IDS
    )
    if (
        decision["promotionPredicatesPass"] is not promotion_pass
        or decision["killPredicatesPass"] is not kill_pass
    ):
        raise RouteError("reflection predicate tri-state contradicts recomputation")
    if promotion_pass:
        if (
            hypothesis["verdict"] != "supported"
            or attribution["failureClass"] != "algorithmic-gain"
            or decision["verdict"] != "next-gate"
            or decision["nextGateBytes"] is None
        ):
            raise RouteError("positive reflection fields are contradictory")
        return BRANCH_REPRICE, "valid terminal treatment passes every frozen predicate"
    if not integrity_pass:
        raise RouteError("scientific reflection cannot treat an integrity failure as algorithmic loss")
    if not scientific_kill_pass or not kill_pass:
        raise RouteError("scientific reflection has neither promotion nor a scientific kill predicate")
    if (
        hypothesis["verdict"] != "refuted"
        or attribution["failureClass"] != "algorithmic-loss"
        or decision["verdict"] != "retire"
        or decision["nextGateBytes"] is not None
    ):
        raise RouteError("negative reflection fields are contradictory")
    return BRANCH_RETIRE, "valid terminal treatment fails a frozen predicate"


def _failure_receipt(
    job: dict[str, Any],
    branch: str,
    reason: str,
    bindings: dict[str, Any],
) -> dict[str, Any]:
    return _finish(
        {
            "schema": RECEIPT_SCHEMA,
            "candidate_id": CANDIDATE_ID,
            "status": "TERMINAL_ROUTED",
            "terminal_state": job["state"],
            "terminal_returncode": job.get("returncode"),
            "branch": branch,
            "branch_reason": reason,
            "host_lane_release": True,
            "bindings": bindings,
            "decision_accessed": False,
            "result_root_accessed": False,
            "opaque_outputs_semantically_parsed": [],
            "claim_authority": "zero-credit-terminal-routing-only",
        }
    )


def _missing_decision_receipt(
    job: dict[str, Any],
    bindings: dict[str, Any],
    closure: dict[str, Any],
) -> dict[str, Any]:
    return _finish(
        {
            "schema": RECEIPT_SCHEMA,
            "candidate_id": CANDIDATE_ID,
            "status": "TERMINAL_ROUTED",
            "terminal_state": job["state"],
            "terminal_returncode": job.get("returncode"),
            "branch": BRANCH_CORRECTION,
            "branch_reason": "declared terminal decision is missing or nonregular",
            "host_lane_release": True,
            "bindings": bindings,
            "output_closure": closure,
            "decision_accessed": False,
            "result_root_accessed": True,
            "opaque_outputs_semantically_parsed": [],
            "claim_authority": "zero-credit-terminal-routing-only",
        }
    )


def route(root: Path) -> dict[str, Any]:
    with ProjectReader(root) as reader:
        active = _active_records(reader)
        if active:
            return _blocked_receipt(active)

        _job_path, job, job_artifact = _one_terminal_job(reader)
        experiment_artifact, proposal_artifact, revision_artifact, runner_artifact = (
            _verify_frozen_inputs(reader, job)
        )
        reflection, reflection_artifact, decision_reference = _verify_reflection(
            reader, job, job_artifact, experiment_artifact, revision_artifact
        )
        base_bindings = {
            "terminal_job": job_artifact,
            "reflection": reflection_artifact,
            "experiment": experiment_artifact,
            "proposal": proposal_artifact,
            "candidate_revision": revision_artifact,
            "runner": runner_artifact,
        }

        if job["state"] in {"failed", "cancelled"}:
            branch, reason = _failure_branch(reflection)
            return _failure_receipt(job, branch, reason, base_bindings)

        assert decision_reference is not None
        # This is the first result-root access.  Non-decision outputs stay opaque.
        closure = _opaque_output_closure(reader)
        closure_decisions = [
            row for row in closure["artifacts"] if row["path"] == DECISION_PATH
        ]
        if len(closure_decisions) != 1:
            return _missing_decision_receipt(job, base_bindings, closure)
        decision, decision_artifact = _verify_reference(
            reader,
            decision_reference,
            "terminal decision",
            expected_path=DECISION_PATH,
        )
        if closure_decisions[0] != decision_artifact:
            raise RouteError("decision binding disagrees with complete output accounting")
        promotion, kill, consistency = _decision_consistency(decision)
        branch, reason = _scientific_branch(reflection, promotion, kill, consistency)
        if closure["failure_class"] == "nonregular-or-missing":
            branch = BRANCH_CORRECTION
            reason = "declared terminal output is missing or nonregular"
        elif closure["failure_class"] == "undeclared-extras":
            branch = BRANCH_CORRECTION
            reason = "terminal result root contains undeclared artifacts"
        if branch not in TERMINAL_BRANCHES:
            raise RouteError("terminal branch is outside the exact route set")
        bindings = dict(base_bindings)
        bindings["decision"] = decision_artifact
        return _finish(
            {
                "schema": RECEIPT_SCHEMA,
                "candidate_id": CANDIDATE_ID,
                "status": "TERMINAL_ROUTED",
                "terminal_state": "completed",
                "terminal_returncode": 0,
                "branch": branch,
                "branch_reason": reason,
                "host_lane_release": True,
                "bindings": bindings,
                "output_closure": closure,
                "predicate_evaluations": {"promotion": promotion, "kill": kill},
                "consistency": consistency,
                "decision_accessed": True,
                "result_root_accessed": True,
                "opaque_outputs_semantically_parsed": [],
                "claim_authority": "zero-credit-terminal-routing-only",
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT)
    parser.add_argument(
        "--receipt",
        default=RECEIPT_PATH,
        help="project-relative no-clobber terminal receipt path",
    )
    arguments = parser.parse_args()
    try:
        receipt = route(arguments.project_root)
    except (OSError, RouteError) as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    if receipt["status"] == "BLOCKED_NONTERMINAL":
        print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
        return 3
    try:
        with ProjectReader(arguments.project_root) as reader:
            reader.write_new_json(arguments.receipt, receipt)
    except (OSError, RouteError) as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
