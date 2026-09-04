#!/usr/bin/env python3
"""Adopt and seal the orphaned Endpoint428 parent trace without reading science.

This is deliberately an observer, not a continuation of the original runner.
It never controls the frozen processes or writes their result namespace. The
only authority it can emit is permission for a separately frozen analyzer to
consume the immutable terminal trace. The missing resource-monitor interval is
permanent and is recorded as a failed resource proof in every outcome.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
import time
from typing import Any, BinaryIO


CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1"
SOURCE_CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_q0_v1"
SOURCE_JOB_ID = "20260830T224837Z_a120752fb5"
PLAN_REL = (
    "operations/planning/"
    "endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json"
)
PLAN_SHA256 = "6b39c52fce1eaf5b25a4e4552b9e24c6e1d59fb1367c72f39a59aa69502044c4"
EXPERIMENT_REL = (
    "operations/adaptive/experiments/"
    "endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json"
)
EXPERIMENT_SHA256 = (
    "2f94fdaecef558ae292eebe3315bbcc604b4d86ee2c7d3a38cc59fd064dd8aa2"
)
SOURCE_RESULT_REL = f"results/{SOURCE_CANDIDATE_ID}"
RESULT_REL = f"results/{CANDIDATE_ID}"
TRACE_REL = f"{SOURCE_RESULT_REL}/parent.p1"
ARCHIVE_REL = f"{SOURCE_RESULT_REL}/parent.archive"
GUARD_REL = f"{SOURCE_RESULT_REL}/parent-trace-guard.json"
GUARD_SHA256 = "99a5ec627250a0dbfa0c4d0d153569c89bc215f1b381d2ab7a5c7b8040289628"
TRACE_MAGIC = b"CMX21P1\0"
TRACE_ROWS = 5_182_388_736
TRACE_BYTES = 10_364_777_488
SAMPLE_INTERVAL_SECONDS = 10.0
STABILITY_SAMPLES = 3
STABILITY_INTERVAL_SECONDS = 10.0
MAX_JSON_BYTES = 64 * 1024 * 1024

PROCESS_SPECS = {
    "wrapper": {
        "pid": 2_965_314,
        "parent_pid": 1,
        "start_ticks": 122_694_560,
        "cmdline_sha256": (
            "59131140fe61229d68fc2b3593612b6c5e6abf3ad19c2e3eb335bca4c2e4c3b0"
        ),
    },
    "cmix": {
        "pid": 2_965_315,
        "parent_pid": 2_965_314,
        "start_ticks": 122_694_560,
        "cmdline_sha256": (
            "1765410b2430b4164065a71d1afa22d20abc8978ac289746af330884f22bc8ad"
        ),
    },
}
BOOT_ID = "3ce46712-27bc-4199-8e48-e2b3d23926cb"

STATIC_INPUTS = (
    (
        f"{SOURCE_RESULT_REL}/build.json",
        1_360,
        "7b7d2bb447794c796c67bbeca1778b964a5bdf15e865a518bba7922dc2563947",
    ),
    (
        f"{SOURCE_RESULT_REL}/manifest-a.bin",
        30_309_597,
        "33d382c511f106dfc6c7459f0220edae3a6a67a92bfbf07476652db2fc685d27",
    ),
    (
        f"{SOURCE_RESULT_REL}/manifest-b.bin",
        30_309_597,
        "33d382c511f106dfc6c7459f0220edae3a6a67a92bfbf07476652db2fc685d27",
    ),
    (
        f"{SOURCE_RESULT_REL}/scan-a.json",
        4_286,
        "df0cf2ce43680a1cd96d22ad0863c41f467ab37680ce5c9bf79ca0f200f1c01f",
    ),
    (
        f"{SOURCE_RESULT_REL}/scan-b.json",
        4_286,
        "df0cf2ce43680a1cd96d22ad0863c41f467ab37680ce5c9bf79ca0f200f1c01f",
    ),
)

REQUIRED_SOURCE_NAMES = frozenset(
    {
        "build.json",
        "compile-analyzer.log",
        "compile-manifest.log",
        "manifest-a-guard.json",
        "manifest-a.bin",
        "manifest-a.log",
        "manifest-b-guard.json",
        "manifest-b.bin",
        "manifest-b.log",
        "materialize.log",
        "parent-trace-guard.json",
        "parent-trace.log",
        "parent.archive",
        "parent.p1",
        "scan-a.json",
        "scan-b.json",
    }
)
EPHEMERAL_SOURCE_NAMES = frozenset(
    {".cmix9-PzZd3n", "parent.archive.cmix.temp"}
)


class ObserverError(RuntimeError):
    """The prospective recovery contract cannot be satisfied."""


class IdentityError(ObserverError):
    """An adopted process identity no longer denotes the frozen process."""


class SourceMutationError(ObserverError):
    """The source result namespace changed outside its frozen allowance."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any, *, compact: bool = False) -> bytes:
    options: dict[str, Any] = {
        "sort_keys": True,
        "ensure_ascii": True,
        "allow_nan": False,
    }
    if compact:
        options["separators"] = (",", ":")
    else:
        options["indent"] = 2
    return (json.dumps(value, **options) + "\n").encode("ascii")


def write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise ObserverError("short output write")
        offset += written


def create_new(path: Path, payload: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
        mode,
    )
    try:
        write_all(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def create_new_json(path: Path, value: Any) -> None:
    create_new(path, canonical_json(value))


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        create_new(temporary, canonical_json(value))
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def read_regular(path: Path, maximum: int | None = None) -> bytes:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ObserverError(f"expected regular non-symlink file: {path}")
        chunks: list[bytes] = []
        total = 0
        while True:
            request = 1024 * 1024
            if maximum is not None:
                request = min(request, maximum + 1 - total)
                if request <= 0:
                    raise ObserverError(f"input exceeds byte limit: {path}")
            chunk = os.read(descriptor, request)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if maximum is not None and total > maximum:
                raise ObserverError(f"input exceeds byte limit: {path}")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_identity != after_identity:
        raise ObserverError(f"input changed while being read: {path}")
    return b"".join(chunks)


def load_json(path: Path, maximum: int = MAX_JSON_BYTES) -> dict[str, Any]:
    try:
        value = json.loads(read_regular(path, maximum))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ObserverError(f"invalid JSON input: {path}") from error
    if not isinstance(value, dict):
        raise ObserverError(f"JSON root is not an object: {path}")
    return value


def relative(project: Path, path: Path) -> str:
    try:
        return path.absolute().relative_to(project.absolute()).as_posix()
    except ValueError as error:
        raise ObserverError(f"path escapes project root: {path}") from error


def digest_regular(path: Path) -> tuple[os.stat_result, str]:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    digest = hashlib.sha256()
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ObserverError(f"expected regular non-symlink file: {path}")
        while True:
            chunk = os.read(descriptor, 8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_identity != after_identity:
        raise ObserverError(f"file changed while being hashed: {path}")
    return after, digest.hexdigest()


def reference(
    project: Path, path: Path, identifier: str | None = None
) -> dict[str, str]:
    _, digest = digest_regular(path)
    result = {
        "path": relative(project, path),
        "sha256": f"sha256:{digest}",
    }
    if identifier is not None:
        result["id"] = identifier
    return result


def verify_file(
    project: Path, relative_path: str, expected_bytes: int, expected_sha256: str
) -> dict[str, Any]:
    path = project / relative_path
    info, digest = digest_regular(path)
    if info.st_size != expected_bytes or digest != expected_sha256:
        raise ObserverError(f"frozen input identity mismatch: {relative_path}")
    return {
        "path": relative_path,
        "bytes": info.st_size,
        "sha256": digest,
        "device": info.st_dev,
        "inode": info.st_ino,
        "mtimeNanoseconds": info.st_mtime_ns,
        "ctimeNanoseconds": info.st_ctime_ns,
    }


def file_snapshot(path: Path) -> dict[str, Any]:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return {"present": False}
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise SourceMutationError(f"expected regular source artifact: {path.name}")
    return {
        "present": True,
        "device": info.st_dev,
        "inode": info.st_ino,
        "bytes": info.st_size,
        "allocatedBytes": info.st_blocks * 512,
        "mtimeNanoseconds": info.st_mtime_ns,
        "ctimeNanoseconds": info.st_ctime_ns,
    }


def namespace_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    root_info = os.lstat(root)
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise SourceMutationError("source result root is not a regular directory")
    result: dict[str, dict[str, Any]] = {}
    with os.scandir(root) as entries:
        for entry in entries:
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise SourceMutationError(
                    f"source namespace contains symlink: {entry.name}"
                )
            if stat.S_ISREG(info.st_mode):
                kind = "file"
            elif stat.S_ISDIR(info.st_mode):
                kind = "directory"
            else:
                raise SourceMutationError(
                    f"source namespace contains special entry: {entry.name}"
                )
            result[entry.name] = {
                "kind": kind,
                "device": info.st_dev,
                "inode": info.st_ino,
                "bytes": info.st_size,
                "mtimeNanoseconds": info.st_mtime_ns,
                "ctimeNanoseconds": info.st_ctime_ns,
            }
    return dict(sorted(result.items()))


def check_namespace(
    baseline: dict[str, dict[str, Any]], observed: dict[str, dict[str, Any]]
) -> None:
    baseline_names = set(baseline)
    observed_names = set(observed)
    added = sorted(observed_names - baseline_names)
    removed = baseline_names - observed_names
    forbidden_removed = sorted(removed - EPHEMERAL_SOURCE_NAMES)
    missing_required = sorted(REQUIRED_SOURCE_NAMES - observed_names)
    if added or forbidden_removed or missing_required:
        raise SourceMutationError(
            "source namespace drift: "
            f"added={added} forbidden_removed={forbidden_removed} "
            f"missing_required={missing_required}"
        )
    for name in baseline_names & observed_names:
        if baseline[name]["kind"] != observed[name]["kind"]:
            raise SourceMutationError(f"source artifact kind changed: {name}")


def read_proc_file(pid: int, name: str, maximum: int) -> bytes | None:
    try:
        return read_regular(Path(f"/proc/{pid}/{name}"), maximum)
    except (FileNotFoundError, ProcessLookupError):
        return None


def parse_proc_stat(pid: int) -> dict[str, Any] | None:
    raw_bytes = read_proc_file(pid, "stat", 64 * 1024)
    if raw_bytes is None:
        return None
    try:
        raw = raw_bytes.decode("ascii")
        left = raw.find("(")
        right = raw.rfind(")")
        fields = raw[right + 2 :].split()
        if left <= 0 or right <= left or len(fields) < 20:
            raise ValueError
        return {
            "pid": pid,
            "comm": raw[left + 1 : right],
            "state": fields[0],
            "parentPid": int(fields[1]),
            "userTicks": int(fields[11]),
            "systemTicks": int(fields[12]),
            "startTicks": int(fields[19]),
        }
    except (UnicodeDecodeError, ValueError) as error:
        raise ObserverError(f"malformed /proc stat for PID {pid}") from error


def parse_proc_status(pid: int) -> dict[str, int] | None:
    raw = read_proc_file(pid, "status", 1024 * 1024)
    if raw is None:
        return None
    values: dict[str, int] = {}
    try:
        for line in raw.decode("ascii").splitlines():
            if ":" not in line:
                continue
            key, text = line.split(":", 1)
            parts = text.split()
            if key in {"VmRSS", "VmHWM", "VmSize"}:
                if len(parts) != 2 or parts[1] != "kB":
                    raise ValueError
                values[key] = int(parts[0]) * 1024
            elif key == "Threads":
                if len(parts) != 1:
                    raise ValueError
                values[key] = int(parts[0])
    except (UnicodeDecodeError, ValueError) as error:
        raise ObserverError(f"malformed /proc status for PID {pid}") from error
    if not {"VmRSS", "VmHWM", "VmSize", "Threads"}.issubset(values):
        raise ObserverError(f"incomplete /proc status for PID {pid}")
    return values


def process_snapshot(
    label: str, spec: dict[str, Any], *, require_initial_parent: bool
) -> dict[str, Any]:
    pid = int(spec["pid"])
    identity = parse_proc_stat(pid)
    if identity is None:
        return {"present": False, "pid": pid}
    if identity["startTicks"] != spec["start_ticks"]:
        raise IdentityError(f"{label} PID was reused")
    status = parse_proc_status(pid)
    if status is None:
        identity_again = parse_proc_stat(pid)
        if identity_again is None:
            return {"present": False, "pid": pid}
        raise ObserverError(f"lost {label} status while process remained present")
    command = read_proc_file(pid, "cmdline", 4 * 1024 * 1024)
    if command is None:
        identity_again = parse_proc_stat(pid)
        if identity_again is None:
            return {"present": False, "pid": pid}
        raise ObserverError(f"lost {label} command line while process remained present")
    command_digest = hashlib.sha256(command).hexdigest()
    if command_digest != spec["cmdline_sha256"]:
        current_identity = parse_proc_stat(pid)
        if current_identity is None:
            return {"present": False, "pid": pid}
        if current_identity["startTicks"] != spec["start_ticks"]:
            raise IdentityError(f"{label} PID was reused")
        if not (current_identity["state"] == "Z" and command == b""):
            raise IdentityError(f"{label} raw argv identity changed")
        identity = current_identity
    if require_initial_parent and identity["parentPid"] != spec["parent_pid"]:
        raise IdentityError(f"{label} parent identity changed before adoption")
    try:
        affinity = sorted(os.sched_getaffinity(pid))
    except ProcessLookupError:
        return {"present": False, "pid": pid}
    return {
        "present": True,
        **identity,
        "cmdlineSha256": command_digest,
        "rssBytes": status["VmRSS"],
        "peakRssBytes": status["VmHWM"],
        "virtualBytes": status["VmSize"],
        "threads": status["Threads"],
        "cpuAffinity": affinity,
    }


def read_trace_header(path: Path) -> dict[str, Any]:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size < 16:
            raise ObserverError("parent trace has no complete fixed header")
        header = os.read(descriptor, 16)
    finally:
        os.close(descriptor)
    if len(header) != 16:
        raise ObserverError("short parent trace header")
    magic = header[:8]
    rows = struct.unpack_from("<Q", header, 8)[0]
    return {
        "magicHex": magic.hex(),
        "declaredRows": rows,
        "magicValid": magic == TRACE_MAGIC,
        "terminalRowCountValid": rows == TRACE_ROWS,
        "valid": magic == TRACE_MAGIC and rows == TRACE_ROWS,
    }


def evaluate(
    predicates: list[dict[str, Any]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, Any]]:
    operations = {
        "eq": lambda observed, threshold: observed == threshold,
        "gt": lambda observed, threshold: observed > threshold,
        "gte": lambda observed, threshold: observed >= threshold,
        "lt": lambda observed, threshold: observed < threshold,
        "lte": lambda observed, threshold: observed <= threshold,
    }
    rows: list[dict[str, Any]] = []
    for predicate in predicates:
        observed = measurements[predicate["measurement"]]
        passed = bool(
            operations[predicate["operator"]](observed, predicate["threshold"])
        )
        rows.append({**predicate, "observed": observed, "passed": passed})
    return rows


class Observer:
    def __init__(self, project: Path, output: Path) -> None:
        self.project = project
        self.output = output
        self.source = project / SOURCE_RESULT_REL
        self.trace = project / TRACE_REL
        self.archive = project / ARCHIVE_REL
        self.experiment_path = project / EXPERIMENT_REL
        self.plan_path = project / PLAN_REL
        self.adoption_path = output / "adoption.json"
        self.progress_path = output / "progress.json"
        self.samples_path = output / "samples.jsonl"
        self.terminal_path = output / "terminal-source.json"
        self.result_path = output / "result.json"
        self.started_utc = utc_now()
        self.started_monotonic_ns = time.monotonic_ns()
        self.sequence = 0
        self.samples_stream: BinaryIO | None = None
        self.baseline_namespace: dict[str, dict[str, Any]] = {}
        self.initial_static: list[dict[str, Any]] = []
        self.last_sample: dict[str, Any] | None = None
        self.maximum_forward_rss_bytes = 0
        self.process_identity_adopted = False
        self.terminal_process_absence = False
        self.static_inputs_identity_pass = False
        self.source_mutation_detected = False
        self.science_accessed_before_terminal = False
        self.forward_observation_complete = False
        self.trace_rows = 0
        self.trace_bytes = 0
        self.trace_geometry_pass = False
        self.archive_bytes = 0
        self.recovery_integrity_pass = False
        self.experiment: dict[str, Any] = {}
        self.revision: dict[str, Any] = {}
        self.experiment_reference: dict[str, str] = {}
        self.failure_reason: str | None = None

    def validate_output_root(self) -> None:
        supplied_info = os.lstat(self.output)
        if stat.S_ISLNK(supplied_info.st_mode) or not stat.S_ISDIR(
            supplied_info.st_mode
        ):
            raise ObserverError("supplied output root is not a non-symlink directory")
        expected = (self.project / RESULT_REL).resolve(strict=True)
        actual = self.output.resolve(strict=True)
        if actual != expected:
            raise ObserverError(
                "output root differs from the frozen candidate result root"
            )
        info = os.lstat(actual)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ObserverError("output root is not a non-symlink directory")
        names = {entry.name for entry in os.scandir(actual)}
        if names:
            raise ObserverError(f"output root is not fresh: {sorted(names)}")
        if actual == self.source.resolve(strict=True):
            raise ObserverError("observer output aliases the source result namespace")

    def validate_job_and_candidate(self) -> None:
        raw_experiment = os.environ.get("GAMMA_ENWIKI9_EXPERIMENT_JSON")
        raw_revision = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
        snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
        snapshot_root = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
        if not all((raw_experiment, raw_revision, snapshot_id, snapshot_root)):
            raise ObserverError("adaptive job bindings are required")
        try:
            job_experiment = json.loads(raw_experiment)
            revision = json.loads(raw_revision)
        except json.JSONDecodeError as error:
            raise ObserverError("adaptive job binding is malformed JSON") from error
        if snapshot_id != CANDIDATE_ID:
            raise ObserverError("snapshot candidate ID mismatch")
        if Path(snapshot_root).resolve(strict=True) != Path(__file__).resolve().parent:
            raise ObserverError(
                "observer is not executing from the sealed candidate snapshot"
            )
        self.experiment_reference = reference(self.project, self.experiment_path)
        if self.experiment_reference != job_experiment:
            raise ObserverError("queued experiment binding mismatch")
        if self.experiment_reference["sha256"] != f"sha256:{EXPERIMENT_SHA256}":
            raise ObserverError("experiment digest differs from source binding")
        if revision.get("candidateId") != CANDIDATE_ID:
            raise ObserverError("candidate revision identifies another candidate")
        receipt = revision.get("receipt")
        if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256"}:
            raise ObserverError("candidate revision receipt reference is malformed")
        receipt_path = self.project / receipt["path"]
        if reference(self.project, receipt_path) != receipt:
            raise ObserverError("candidate revision receipt identity mismatch")
        full_revision = load_json(receipt_path)
        if (
            full_revision.get("candidateId") != CANDIDATE_ID
            or full_revision.get("candidateTreeSha256")
            != revision.get("candidateTreeSha256")
        ):
            raise ObserverError("candidate revision receipt content mismatch")
        program_rows = [
            row
            for row in full_revision.get("files", [])
            if row.get("path") == "program.py"
        ]
        if len(program_rows) != 1:
            raise ObserverError(
                "candidate revision does not bind exactly one program.py"
            )
        _, program_digest = digest_regular(Path(__file__).resolve())
        if program_rows[0].get("sha256") != program_digest:
            raise ObserverError("executing observer differs from candidate revision")
        self.revision = revision

    def validate_contracts_and_inputs(self) -> None:
        sys.path.insert(0, str(self.project / "tools"))
        import research_contracts  # pylint: disable=import-outside-toplevel

        research_contracts.validate_artifact(self.experiment_path)
        experiment = load_json(self.experiment_path)
        if (
            experiment.get("experimentId") != CANDIDATE_ID
            or experiment.get("proposalId") != CANDIDATE_ID
            or experiment.get("evidenceClass") != "infrastructure"
            or experiment.get("objectiveCreditBytes") != 0
        ):
            raise ObserverError("experiment semantics mismatch")
        inputs = {row["id"]: row for row in experiment.get("inputs", [])}
        for row in inputs.values():
            path = self.project / row["path"]
            if reference(self.project, path) != {
                "path": row["path"],
                "sha256": row["sha256"],
            }:
                raise ObserverError(f"experiment input drifted: {row['id']}")
        if (
            inputs.get("adoption-plan", {}).get("sha256")
            != f"sha256:{PLAN_SHA256}"
        ):
            raise ObserverError(
                "experiment no longer binds the frozen adoption plan"
            )
        plan = load_json(self.plan_path)
        if (
            plan.get("candidate_id") != CANDIDATE_ID
            or plan.get("source_job", {}).get("job_id") != SOURCE_JOB_ID
            or plan.get("adopted_processes", {}).get("boot_id") != BOOT_ID
            or plan.get("terminal_trace_contract", {}).get("expected_rows")
            != TRACE_ROWS
            or plan.get("terminal_trace_contract", {}).get("expected_bytes")
            != TRACE_BYTES
            or plan.get("original_guard_gap", {}).get(
                "continuous_resource_proof_recoverable"
            )
            is not False
        ):
            raise ObserverError("adoption plan semantics mismatch")
        self.experiment = experiment

    def validate_boot_and_processes(self) -> dict[str, dict[str, Any]]:
        boot = (
            read_regular(Path("/proc/sys/kernel/random/boot_id"), 256)
            .decode("ascii")
            .strip()
        )
        if boot != BOOT_ID:
            raise IdentityError("host boot ID changed before adoption")
        snapshots = {
            label: process_snapshot(label, spec, require_initial_parent=True)
            for label, spec in PROCESS_SPECS.items()
        }
        if not all(row["present"] for row in snapshots.values()):
            raise IdentityError("both exact frozen processes must be live at adoption")
        return snapshots

    def validate_source_inputs(self) -> tuple[dict[str, Any], dict[str, Any]]:
        self.baseline_namespace = namespace_snapshot(self.source)
        baseline_names = set(self.baseline_namespace)
        if not REQUIRED_SOURCE_NAMES.issubset(baseline_names):
            raise SourceMutationError(
                "source namespace lacks a required pre-adoption artifact"
            )
        unexpected = (
            baseline_names - REQUIRED_SOURCE_NAMES - EPHEMERAL_SOURCE_NAMES
        )
        if unexpected:
            raise SourceMutationError(
                f"unexpected pre-adoption source artifacts: {sorted(unexpected)}"
            )
        self.initial_static = [
            verify_file(self.project, path, size, digest)
            for path, size, digest in STATIC_INPUTS
        ]
        guard_info, guard_digest = digest_regular(self.project / GUARD_REL)
        if guard_digest != GUARD_SHA256:
            raise ObserverError("original stopped guard changed before adoption")
        guard = load_json(self.project / GUARD_REL)
        if (
            guard.get("status") != "running"
            or guard.get("sample_count") != 394_738
            or guard.get("max_sampled_tree_rss_kib") != 9_102_532
        ):
            raise ObserverError("original guard gap semantics changed")
        header = read_trace_header(self.trace)
        if header["magicValid"] is not True:
            raise ObserverError("fixed trace magic is invalid at adoption")
        if header["declaredRows"] not in {0, TRACE_ROWS}:
            raise ObserverError("live trace header has an inadmissible row count")
        return (
            {
                "path": GUARD_REL,
                "bytes": guard_info.st_size,
                "sha256": guard_digest,
                "recordedStatus": guard["status"],
                "recordedSampleCount": guard["sample_count"],
                "maximumRecordedTreeRssKiB": guard[
                    "max_sampled_tree_rss_kib"
                ],
                "continuousResourceProofRecoverable": False,
            },
            header,
        )

    def open_samples(self) -> None:
        self.samples_stream = self.samples_path.open("xb", buffering=0)

    def append_sample(self, sample: dict[str, Any]) -> None:
        if self.samples_stream is None:
            raise ObserverError("sample stream is not open")
        self.samples_stream.write(canonical_json(sample, compact=True))
        self.samples_stream.flush()
        os.fsync(self.samples_stream.fileno())
        self.last_sample = sample

    def close_samples(self) -> None:
        if self.samples_stream is not None:
            self.samples_stream.flush()
            os.fsync(self.samples_stream.fileno())
            self.samples_stream.close()
            self.samples_stream = None

    def collect_sample(self, phase: str) -> dict[str, Any]:
        processes = {
            label: process_snapshot(label, spec, require_initial_parent=False)
            for label, spec in PROCESS_SPECS.items()
        }
        current_namespace = namespace_snapshot(self.source)
        check_namespace(self.baseline_namespace, current_namespace)
        trace = file_snapshot(self.trace)
        archive = file_snapshot(self.archive)
        resident = sum(
            int(row.get("rssBytes", 0))
            for row in processes.values()
            if row["present"]
        )
        self.maximum_forward_rss_bytes = max(
            self.maximum_forward_rss_bytes, resident
        )
        self.trace_bytes = int(trace.get("bytes", 0))
        self.archive_bytes = int(archive.get("bytes", 0))
        monotonic = time.monotonic_ns()
        sample = {
            "schema": "gamma.enwiki9.endpoint428-horizon-orphan-forward-sample.v1",
            "sequence": self.sequence,
            "phase": phase,
            "utc": utc_now(),
            "monotonicNanoseconds": monotonic,
            "elapsedMonotonicNanoseconds": monotonic
            - self.started_monotonic_ns,
            "processes": processes,
            "observedTreeRssBytes": resident,
            "maximumObservedTreeRssBytes": self.maximum_forward_rss_bytes,
            "trace": trace,
            "archive": archive,
            "sourceNames": sorted(current_namespace),
            "scienceAccessed": False,
            "continuousResourceProof": False,
        }
        self.sequence += 1
        return sample

    def update_progress(self, state: str) -> None:
        progress = {
            "schema": "gamma.enwiki9.endpoint428-horizon-orphan-adoption-progress.v1",
            "candidateId": CANDIDATE_ID,
            "sourceJobId": SOURCE_JOB_ID,
            "state": state,
            "startedUtc": self.started_utc,
            "updatedUtc": utc_now(),
            "sampleCount": self.sequence,
            "lastSample": self.last_sample or {},
            "traceBytes": self.trace_bytes,
            "expectedTraceBytes": TRACE_BYTES,
            "maximumObservedTreeRssBytes": self.maximum_forward_rss_bytes,
            "scienceAccessedBeforeTerminal": False,
            "continuousResourceProofPass": False,
            "failureReason": self.failure_reason,
        }
        atomic_json(self.progress_path, progress)

    def stable_terminal_samples(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        identities: list[tuple[Any, ...]] = []
        for index in range(STABILITY_SAMPLES):
            sample = self.collect_sample("terminal-stability")
            if any(row["present"] for row in sample["processes"].values()):
                raise IdentityError(
                    "an adopted process reappeared during terminal stability"
                )
            self.append_sample(sample)
            self.update_progress("terminal-stability")
            trace = sample["trace"]
            archive = sample["archive"]
            identities.append(
                tuple(
                    (
                        row.get("present"),
                        row.get("device"),
                        row.get("inode"),
                        row.get("bytes"),
                        row.get("mtimeNanoseconds"),
                        row.get("ctimeNanoseconds"),
                    )
                    for row in (trace, archive)
                )
            )
            rows.append(sample)
            if index + 1 < STABILITY_SAMPLES:
                time.sleep(STABILITY_INTERVAL_SECONDS)
        if len(set(identities)) != 1:
            raise ObserverError("terminal trace/archive identities were not stable")
        return rows

    def seal_terminal_source(
        self, stability: list[dict[str, Any]]
    ) -> dict[str, Any]:
        observed_namespace = namespace_snapshot(self.source)
        check_namespace(self.baseline_namespace, observed_namespace)
        final_static = [
            verify_file(self.project, path, size, digest)
            for path, size, digest in STATIC_INPUTS
        ]
        self.static_inputs_identity_pass = final_static == self.initial_static
        if not self.static_inputs_identity_pass:
            raise SourceMutationError("a frozen pretrace input changed")
        _, final_guard_digest = digest_regular(self.project / GUARD_REL)
        if final_guard_digest != GUARD_SHA256:
            raise SourceMutationError("the stopped predecessor guard changed")
        trace_info, trace_digest = digest_regular(self.trace)
        archive_info, archive_digest = digest_regular(self.archive)
        header = read_trace_header(self.trace)
        self.trace_rows = int(header["declaredRows"])
        self.trace_bytes = trace_info.st_size
        self.archive_bytes = archive_info.st_size
        self.trace_geometry_pass = bool(
            header["valid"]
            and trace_info.st_size == TRACE_BYTES
            and self.trace_rows == TRACE_ROWS
            and archive_info.st_size > 0
        )
        if not self.trace_geometry_pass:
            raise ObserverError("terminal trace geometry or archive size failed")
        terminal = {
            "schema": "gamma.enwiki9.endpoint428-horizon-orphan-terminal-source.v1",
            "candidateId": CANDIDATE_ID,
            "sourceCandidateId": SOURCE_CANDIDATE_ID,
            "sourceJobId": SOURCE_JOB_ID,
            "status": "SEALED_IMMUTABLE_TRACE",
            "trace": {
                "path": TRACE_REL,
                "bytes": trace_info.st_size,
                "sha256": trace_digest,
                "device": trace_info.st_dev,
                "inode": trace_info.st_ino,
                "mtimeNanoseconds": trace_info.st_mtime_ns,
                "ctimeNanoseconds": trace_info.st_ctime_ns,
                "header": header,
            },
            "archive": {
                "path": ARCHIVE_REL,
                "bytes": archive_info.st_size,
                "sha256": archive_digest,
                "device": archive_info.st_dev,
                "inode": archive_info.st_ino,
                "mtimeNanoseconds": archive_info.st_mtime_ns,
                "ctimeNanoseconds": archive_info.st_ctime_ns,
            },
            "staticInputs": final_static,
            "sourceNamespace": observed_namespace,
            "stabilitySampleSequences": [
                row["sequence"] for row in stability
            ],
            "forwardSampleCount": self.sequence,
            "maximumObservedForwardTreeRssBytes": (
                self.maximum_forward_rss_bytes
            ),
            "scientificValuesAccessed": False,
            "continuousResourceProofPass": False,
            "analysisAuthority": (
                "one-separately-frozen-immutable-trace-analysis-only"
            ),
            "archiveAuthority": False,
            "scoreCreditBytes": 0,
            "generatedUtc": utc_now(),
        }
        create_new_json(self.terminal_path, terminal)
        return terminal

    def measurements(self) -> dict[str, bool | int | float]:
        return {
            "processIdentityAdopted": self.process_identity_adopted,
            "terminalProcessAbsence": self.terminal_process_absence,
            "traceBytes": self.trace_bytes,
            "traceRows": self.trace_rows,
            "traceGeometryPass": self.trace_geometry_pass,
            "archiveBytes": self.archive_bytes,
            "staticInputsIdentityPass": self.static_inputs_identity_pass,
            "sourceMutationDetected": self.source_mutation_detected,
            "scienceAccessedBeforeTerminal": (
                self.science_accessed_before_terminal
            ),
            "forwardObservationComplete": self.forward_observation_complete,
            "continuousResourceProofPass": False,
            "recoveryIntegrityPass": self.recovery_integrity_pass,
        }

    def finalize_result(self) -> dict[str, Any]:
        self.close_samples()
        self.update_progress(
            "authorized-immutable-trace-analysis"
            if self.recovery_integrity_pass
            else "recovery-integrity-failed"
        )
        measurements = self.measurements()
        promotion = evaluate(
            self.experiment["promotionPredicates"], measurements
        )
        kill = evaluate(self.experiment["killPredicates"], measurements)
        promotion_pass = all(row["passed"] for row in promotion)
        kill_pass = all(row["passed"] for row in kill)
        artifact_paths = (
            ("adoption", self.adoption_path),
            ("forward-samples", self.samples_path),
            ("terminal-source", self.terminal_path),
            ("final-progress", self.progress_path),
        )
        result = {
            "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
            "objective": self.experiment["objective"],
            "experiment": self.experiment_reference,
            "candidateId": CANDIDATE_ID,
            "candidateRevision": self.revision,
            "evidenceClass": "infrastructure",
            "objectiveCreditBytes": 0,
            "measurements": measurements,
            "promotionPredicates": promotion,
            "killPredicates": kill,
            "promotionPass": promotion_pass,
            "killPass": kill_pass,
            "decision": (
                "authorize-successor"
                if promotion_pass and not kill_pass
                else "retire"
                if kill_pass
                else "retry"
            ),
            "artifacts": [
                reference(self.project, path, identifier)
                for identifier, path in artifact_paths
            ],
            "generatedUtc": utc_now(),
        }
        create_new_json(self.result_path, result)
        sys.path.insert(0, str(self.project / "tools"))
        import research_contracts  # pylint: disable=import-outside-toplevel

        research_contracts.validate_artifact(self.result_path)
        print(
            json.dumps(
                {
                    "candidateId": CANDIDATE_ID,
                    "decision": result["decision"],
                    "promotionPass": promotion_pass,
                    "continuousResourceProofPass": False,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return result

    def write_failure_terminal(self) -> None:
        if self.terminal_path.exists():
            return
        terminal = {
            "schema": "gamma.enwiki9.endpoint428-horizon-orphan-terminal-source.v1",
            "candidateId": CANDIDATE_ID,
            "sourceCandidateId": SOURCE_CANDIDATE_ID,
            "sourceJobId": SOURCE_JOB_ID,
            "status": "RECOVERY_INTEGRITY_FAILED",
            "failureReason": self.failure_reason,
            "lastOperationalSample": self.last_sample or {},
            "scientificValuesAccessed": False,
            "continuousResourceProofPass": False,
            "analysisAuthority": "forbidden",
            "archiveAuthority": False,
            "scoreCreditBytes": 0,
            "generatedUtc": utc_now(),
        }
        create_new_json(self.terminal_path, terminal)

    def run(self) -> int:
        self.validate_output_root()
        self.validate_job_and_candidate()
        self.validate_contracts_and_inputs()
        initial_processes = self.validate_boot_and_processes()
        guard_gap, trace_header = self.validate_source_inputs()
        self.static_inputs_identity_pass = True
        self.process_identity_adopted = True
        adoption = {
            "schema": "gamma.enwiki9.endpoint428-horizon-orphan-adoption.v1",
            "candidateId": CANDIDATE_ID,
            "sourceCandidateId": SOURCE_CANDIDATE_ID,
            "sourceJobId": SOURCE_JOB_ID,
            "experiment": self.experiment_reference,
            "candidateRevision": self.revision,
            "adoptedUtc": utc_now(),
            "bootId": BOOT_ID,
            "processes": initial_processes,
            "traceHeader": trace_header,
            "traceAtAdoption": file_snapshot(self.trace),
            "archiveAtAdoption": file_snapshot(self.archive),
            "staticInputs": self.initial_static,
            "sourceNamespace": self.baseline_namespace,
            "originalGuardGap": guard_gap,
            "observerBoundary": {
                "processControl": False,
                "sourceNamespaceWrites": False,
                "scientificValuesBeforeTerminal": False,
                "continuousResourceProofRecoverable": False,
            },
            "scoreCreditBytes": 0,
        }
        create_new_json(self.adoption_path, adoption)
        self.open_samples()
        try:
            while True:
                sample = self.collect_sample("forward-observation")
                self.append_sample(sample)
                self.update_progress("observing")
                if not any(
                    row["present"] for row in sample["processes"].values()
                ):
                    self.terminal_process_absence = True
                    break
                time.sleep(SAMPLE_INTERVAL_SECONDS)
            stability = self.stable_terminal_samples()
            self.seal_terminal_source(stability)
            self.forward_observation_complete = True
            self.recovery_integrity_pass = True
        except Exception as error:  # fail closed after prospective adoption
            self.failure_reason = f"{type(error).__name__}: {error}"
            if isinstance(error, SourceMutationError):
                self.source_mutation_detected = True
            self.recovery_integrity_pass = False
            self.forward_observation_complete = False
            self.write_failure_terminal()
        result = self.finalize_result()
        return 0 if result["promotionPass"] and not result["killPass"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project_root.resolve(strict=True)
    output = args.output_dir
    if not output.is_absolute():
        output = project / output
    return Observer(project, output).run()


if __name__ == "__main__":
    raise SystemExit(main())
