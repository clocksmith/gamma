#!/usr/bin/env python3
"""Record driver results; --terminal-index records reviewed, closed arm sets.

The terminal index is an ordinary evidence file, created before reflection:
{"schema": "gamma.enwiki9.terminal-result-index.v1", "job": {"path": ..., "sha256": ...},
 "guard": {"path": ..., "sha256": ...}, "arms": [{"arm": "P", "result": {...},
 "artifacts": {"archive": {...}, "restored": {...}, "repeat": {...}}}], "evidence": []}
References are project-relative and hash-bound. The validated reflection must
list this index as evidence. Missing artifacts are allowed only for result claims
that do not require them; optional diagnostics may be absent explicitly.

Terminal calls serialize on the existing ledger inode and append without replacing
it. A retry fills missing rows, then atomically updates the metadata projection.
This is recoverable publication, not an atomic transaction across both files.
Legacy writers do not honor this lock: concurrent legacy recording must be
coordinated externally. A torn ledger line fails closed and is never truncated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import fcntl
import os
import pathlib
import re
import tempfile
from typing import Any

try:
    from projects.enwiki9.tools import enwiki9_reflections as reflections
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import enwiki9_reflections as reflections
    import research_contracts


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
RESULTS = ROOT / "results"


def rel(path: pathlib.Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: pathlib.Path, payload: Any) -> None:
    """Replace only this derived projection, after a complete durable write."""
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = pathlib.Path(name)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(json.dumps(payload, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def project_path(raw: str) -> pathlib.Path:
    if not isinstance(raw, str) or not raw or pathlib.Path(raw).is_absolute():
        raise ValueError("terminal references must use project-relative paths")
    path = (ROOT / raw).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError(f"terminal reference escapes project: {raw}")
    return path


def checked_reference(reference: Any, bindings: dict[pathlib.Path, str]) -> pathlib.Path:
    if not isinstance(reference, dict):
        raise ValueError("missing terminal evidence reference")
    path = project_path(reference.get("path"))
    expected = reference.get("sha256", "")
    if not isinstance(expected, str) or not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", expected):
        raise ValueError(f"missing SHA-256 binding: {path}")
    expected = expected.removeprefix("sha256:")
    if research_contracts.file_digest(path, "sha256") != expected:
        raise ValueError(f"terminal evidence identity differs: {path}")
    if "bytes" in reference and reference["bytes"] != path.stat().st_size:
        raise ValueError(f"terminal evidence size differs: {path}")
    if path in bindings and bindings[path] != expected:
        raise ValueError(f"conflicting terminal evidence binding: {path}")
    bindings[path] = expected
    return path


def _process_active(pid: int, start_ticks: int | None = None) -> bool:
    try:
        fields = pathlib.Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except FileNotFoundError:
        return False
    if start_ticks is not None and int(fields[19]) != start_ticks:
        return False
    return fields[0] not in {"Z", "X"}


def _closed_job(job_path: pathlib.Path, job: dict[str, Any]) -> str:
    job_id = job.get("job_id")
    if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", job_id):
        raise ValueError("missing or invalid job identity")
    canonical, _ = reflections.terminal_job(job_id)
    if canonical.resolve() != job_path or job.get("state") != job_path.parent.name:
        raise ValueError("job is not the canonical terminal record")
    for state in reflections.LIVE_STATES:
        for path in (reflections.ADAPTIVE / state).glob("*.json"):
            if load_json(path).get("job_id") == job_id:
                raise ValueError("job also has a live queue claim")
    resources = job.get("execution_resources") or {}
    if not job.get("finished_at") or resources.get("cleanup_complete") is not True:
        raise ValueError("terminal job has no completed resource cleanup")
    boot_path = pathlib.Path("/proc/sys/kernel/random/boot_id")
    boot_id = resources.get("boot_id")
    if boot_id == boot_path.read_text().strip():
        pid, ticks = job.get("worker_pid"), job.get("worker_proc_start_ticks")
        if isinstance(pid, int):
            if not isinstance(ticks, int):
                raise ValueError("terminal worker has no start identity")
            if _process_active(pid, ticks):
                raise ValueError("terminal worker identity remains live")
        cgroup = resources.get("cgroup_path")
        if cgroup and pathlib.Path(cgroup).exists():
            path = pathlib.Path(cgroup)
            if path.stat().st_ino == resources.get("cgroup_inode"):
                if any(_process_active(int(pid)) for pid in (path / "cgroup.procs").read_text().split()):
                    raise ValueError("terminal cgroup still contains live processes")
        return "same-boot-identities-checked"
    return "foreign-boot-terminal-evidence-only" if boot_id else "missing-boot-terminal-evidence-only"


def _guard_identity(job: dict[str, Any], guard: dict[str, Any]) -> None:
    if guard.get("label") != job["job_id"]:
        raise ValueError("guard label differs from terminal job")
    resources, cgroup = job["execution_resources"], guard.get("cgroup") or {}
    for job_field, guard_field in (("cgroup_path", "path"), ("cgroup_inode", "inode")):
        if resources.get(job_field) is not None and resources[job_field] != cgroup.get(guard_field):
            raise ValueError("guard cgroup identity differs from terminal job")
    command = guard.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(arg, str) for arg in command):
        raise ValueError("guard command is missing")
    digest = hashlib.sha256(b"\0".join(os.fsencode(arg) for arg in command)).hexdigest()
    if digest != guard.get("command_sha256"):
        raise ValueError("guard command digest differs")


def _validate_guard_receipt(path: pathlib.Path, job: dict[str, Any], guard: dict[str, Any]) -> str:
    """Bind discovery's allocated budget without relaxing prize qualification."""
    if job.get("execution_mode") != "discovery" or job.get("timing_authority") != "diagnostic":
        research_contracts.validate_artifact(path)
        return "canonical-guard-schema"
    if guard.get("schema") != "gamma.enwiki9.resource-guard-receipt.v3":
        raise ValueError("discovery recording requires the v3 resource guard")
    resources = job["execution_resources"]
    groups = [group for group in resources.get("groups", [])
              if group.get("path") == resources.get("cgroup_path")
              and group.get("inode") == resources.get("cgroup_inode")]
    if len(groups) != 1:
        raise ValueError("discovery guard has no unique allocated cgroup")
    allocation = groups[0].get("memory_bytes")
    ceiling = (job.get("resource_budget") or {}).get("memory_bytes")
    if type(allocation) is not int or type(ceiling) is not int or not 0 < allocation <= ceiling:
        raise ValueError("discovery allocation exceeds or lacks the frozen memory budget")
    if (guard.get("cgroup") or {}).get("requested_memory_max_bytes") != allocation:
        raise ValueError("discovery guard requested memory differs from allocated cgroup")
    # The existing v3 schema fixes this one field at the prize memory ceiling.
    # Its other structure/type checks also apply to bounded discovery receipts.
    schema = research_contracts.load_json(research_contracts.SCHEMA_PATHS[guard["schema"]])
    schema["$defs"]["cgroup"]["properties"]["requested_memory_max_bytes"] = {"const": allocation}
    research_contracts.jsonschema.Draft202012Validator(
        schema, format_checker=research_contracts.jsonschema.FormatChecker(),
    ).validate(guard)
    return "discovery-budget-schema"


def _artifact_claims(result: dict[str, Any], artifacts: dict[str, Any], bindings: dict[pathlib.Path, str]) -> None:
    if not isinstance(artifacts, dict):
        raise ValueError("arm artifacts must be a reference object")
    paths = {name: checked_reference(ref, bindings) for name, ref in artifacts.items()}
    requirements = {}
    if result.get("compressed_size") is not None:
        requirements["archive"] = (result.get("compressed_size"), result.get("compressed_sha256"))
    if result.get("roundtrip_ok") is True:
        requirements["restored"] = (result.get("data_size"), result.get("data_sha256"))
    if deterministic(result) is True:
        requirements["repeat"] = (result.get("compressed_size"), result.get("compressed_sha256"))
    for name, (size, digest) in requirements.items():
        path = paths.get(name)
        if path is None or size is None or digest is None:
            raise ValueError(f"missing {name} evidence for result claim")
        if path.stat().st_size != size or bindings[path] != digest:
            raise ValueError(f"{name} evidence differs from result claim")
    if "repeat" in requirements and paths.get("repeat") == paths.get("archive"):
        raise ValueError("repeat must be a separately retained artifact")


def _prepare_terminal(program_id: str, index_path: pathlib.Path, metadata: dict[str, Any]) -> dict[str, Any]:
    bindings: dict[pathlib.Path, str] = {}
    index_reference = reflections.reference(index_path)
    checked_reference(index_reference, bindings)
    index = load_json(index_path)
    if index.get("schema") != "gamma.enwiki9.terminal-result-index.v1":
        raise ValueError("unsupported terminal result index")
    job_path = checked_reference(index.get("job"), bindings)
    job = load_json(job_path)
    local_process_check = _closed_job(job_path, job)
    if job.get("candidate_id") != program_id:
        raise ValueError("terminal job identifies another candidate")
    job_id = job["job_id"]
    reflection = reflections.validated_terminal_reflection(
        program_id, {"jobId": job_id, "path": index["job"]["path"]}, metadata,
    )
    reflection_ref = metadata["measured"]["reflections"][job_id]
    checked_reference(reflection_ref, bindings)
    if index_reference not in reflection.get("evidence", []):
        raise ValueError("validated reflection does not bind this terminal index")
    for reference in reflection["evidence"]:
        checked_reference(reference, bindings)
    evidence = index.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("terminal evidence must be a reference array")
    for reference in evidence:
        checked_reference(reference, bindings)
    guard_path = checked_reference(index.get("guard"), bindings)
    if guard_path != project_path(job["execution_resources"].get("guard_path")):
        raise ValueError("guard differs from terminal job")
    guard = load_json(guard_path)
    validation_mode = _validate_guard_receipt(guard_path, job, guard)
    _guard_identity(job, guard)
    if guard.get("status") in {None, "running"} or type(guard.get("returncode")) is not int:
        raise ValueError("resource guard is not closed")
    arms = index.get("arms")
    if not isinstance(arms, list) or not arms:
        raise ValueError("terminal index requires explicit arms")
    rows, measurements, labels, result_paths = [], {}, set(), set()
    for entry in arms:
        arm = entry.get("arm")
        if not isinstance(arm, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", arm) or arm in labels:
            raise ValueError("duplicate or invalid arm identity")
        labels.add(arm)
        path = checked_reference(entry.get("result"), bindings)
        if path in result_paths:
            raise ValueError("arms must identify separate result receipts")
        result_paths.add(path)
        result = load_json(path)
        if result.get("program_id") != program_id or result.get("arm") != arm:
            raise ValueError("result candidate or arm identity differs")
        if result.get("candidate_revision") != reflection["candidateRevision"]:
            raise ValueError("result differs from the reflected candidate revision")
        if result.get("run_source") != index["job"]["path"]:
            raise ValueError("result does not bind the indexed job")
        source_tags = result.get("run_tags")
        if isinstance(source_tags, list) and any(
            isinstance(tag, str) and tag.startswith(
                ("terminal-job:", "terminal-index:", "terminal-reflection:")
            ) for tag in source_tags
        ):
            raise ValueError("result uses reserved terminal recorder identity tags")
        _artifact_claims(result, entry.get("artifacts", {}), bindings)
        row = research_contracts.build_driver_run_ledger_row(
            result, path, program_name=result.get("program_name") or program_id,
            recorded_utc=job["finished_at"],
        )
        row["run_id"] = f"{program_id}__{job_id}__{arm}"
        row["run_tags"] = list(dict.fromkeys([*row["run_tags"],
            f"terminal-job:{job_id}",
            f"terminal-index:{index_reference['sha256']}",
            f"terminal-reflection:{reflection_ref['sha256']}"]))
        research_contracts.validate_driver_run_ledger_row(row)
        rows.append(row)
        measurement = result_record(result, path)
        # Checkout mtimes are not evidence identity and must not break retries.
        measurement.pop("result_json_mtime_utc", None)
        measurement["missing_diagnostics"] = result.get("missing_diagnostics", [])
        measurements[arm] = {**measurement, "run_id": row["run_id"]}
    return {"job": job, "job_path": job_path, "bindings": bindings, "rows": rows,
            "local_process_check": local_process_check,
            "projection": {"index": index_reference, "reflection": reflection_ref,
                           "guard_validation_mode": validation_mode,
                           "qualification_authority": False,
                           "missing_diagnostics": job["execution_resources"].get("missing_diagnostics", []),
                           "arms": measurements}}


def _ledger_rows(stream: Any) -> list[dict[str, Any]]:
    stream.seek(0)
    data = stream.read()
    if data and not data.endswith(b"\n"):
        raise ValueError("ledger ends in an incomplete line; preserve it for repair")
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    if any(not isinstance(row, dict) or not isinstance(row.get("run_id"), str) for row in rows):
        raise ValueError("ledger has an invalid row identity")
    return rows


def _missing_rows(existing: list[dict[str, Any]], proposed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tags = set(proposed[0]["run_tags"])
    job_tag = next(tag for tag in tags if tag.startswith("terminal-job:"))
    identity_tags = {tag for tag in tags if tag.startswith(("terminal-index:", "terminal-reflection:"))}
    for row in existing:
        prior_tags = set(row.get("run_tags") or [])
        if job_tag in prior_tags and not identity_tags.issubset(prior_tags):
            raise ValueError("terminal job already has a different index or reflection claim")
    missing = []
    for row in proposed:
        claims = [old for old in existing if old["run_id"] == row["run_id"]
                  or old.get("result_path") == row["result_path"]]
        if not claims:
            missing.append(row)
        elif len(claims) != 1 or claims[0] != row:
            raise ValueError(f"conflicting or duplicated ledger claim: {row['run_id']}")
    return missing


def _recheck_bindings(bindings: dict[pathlib.Path, str], phase: str) -> None:
    for path, digest in bindings.items():
        if research_contracts.file_digest(path, "sha256") != digest:
            raise ValueError(f"evidence changed {phase}: {path}")


def record_terminal(program_id: str, index_path: pathlib.Path, *, check_only: bool = False) -> dict[str, Any]:
    """Validate an indexed closed job; resume interrupted publication safely."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", program_id):
        raise ValueError("invalid candidate identity")
    meta_path = PROGRAMS / program_id / "meta.json"
    # Validate before opening a ledger, so absent evidence creates no output.
    prepared = _prepare_terminal(program_id, index_path.resolve(), load_json(meta_path))
    ledger = RESULTS / "run_ledger.jsonl"
    if check_only:
        prior = ((load_json(meta_path).get("measured") or {}).get("terminal_results") or {}).get(prepared["job"]["job_id"])
        if prior is not None and prior != prepared["projection"]:
            raise ValueError("terminal recording differs from the existing projection")
        with ledger.open("rb") as stream:
            missing = _missing_rows(_ledger_rows(stream), prepared["rows"])
        _recheck_bindings(prepared["bindings"], "during check")
        return {"check_only": True, "job_id": prepared["job"]["job_id"],
                "local_process_check": prepared["local_process_check"],
                "arms": len(prepared["rows"]), "missing_rows": len(missing)}
    with ledger.open("a+b", buffering=0) as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        if ledger.stat().st_ino != os.fstat(stream.fileno()).st_ino:
            raise ValueError("ledger replaced while acquiring recording lock")
        meta_bytes = meta_path.read_bytes()
        metadata = json.loads(meta_bytes)
        prepared = _prepare_terminal(program_id, index_path.resolve(), metadata)
        job_id = prepared["job"]["job_id"]
        records = metadata.setdefault("measured", {}).setdefault("terminal_results", {})
        previous = records.get(job_id)
        if previous is not None and previous != prepared["projection"]:
            raise ValueError("terminal recording differs from the existing projection")
        missing = _missing_rows(_ledger_rows(stream), prepared["rows"])
        _recheck_bindings(prepared["bindings"], "during recording")
        _closed_job(prepared["job_path"], prepared["job"])
        for row in missing:
            payload = (json.dumps(row, sort_keys=True) + "\n").encode()
            if stream.write(payload) != len(payload):
                raise OSError("partial ledger append; evidence preserved for repair")
        os.fsync(stream.fileno())
        if _missing_rows(_ledger_rows(stream), prepared["rows"]):
            raise ValueError("ledger append did not persist the complete arm set")
        _recheck_bindings(prepared["bindings"], "after ledger append")
        if meta_path.read_bytes() != meta_bytes:
            raise ValueError("metadata changed concurrently; retry to merge the projection")
        if previous is None:
            records[job_id] = prepared["projection"]
            write_json(meta_path, metadata)
    return {"job_id": job_id, "arms": len(prepared["rows"]),
            "appended_rows": len(missing), "metadata_updated": previous is None,
            "reflection": prepared["projection"]["reflection"],
            "local_process_check": prepared["local_process_check"],
            "publication": "recoverable-append-then-projection"}


def artifact_metadata(path: pathlib.Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "bytes": stat.st_size,
        "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def latest_result(program_id: str) -> pathlib.Path:
    result_dir = RESULTS / program_id
    matches = sorted(result_dir.glob("*.json"), key=lambda path: path.stat().st_mtime)
    if not matches:
        raise SystemExit(f"no result JSON files found under {rel(result_dir)}")
    return matches[-1]


def deterministic(result: dict[str, Any]) -> bool | None:
    value = result.get("determinism")
    if not isinstance(value, dict):
        return None
    flag = value.get("single_host_byte_equal")
    return flag if isinstance(flag, bool) else None


def guard_record(guard: dict[str, Any], guard_path: pathlib.Path) -> dict[str, Any]:
    meta = artifact_metadata(guard_path)
    return {
        "rss_guard_json": rel(guard_path),
        "rss_guard_json_bytes": meta["bytes"],
        "rss_guard_json_mtime_utc": meta["mtime_utc"],
        "rss_guard_json_sha256": meta["sha256"],
        "rss_guard_kib": guard.get("limit_kib"),
        "rss_guard_limit_mode": guard.get("limit_mode", "max_single"),
        "max_sampled_single_rss_kib": guard.get("max_sampled_single_rss_kib"),
        "max_sampled_tree_rss_kib": guard.get("max_sampled_tree_rss_kib"),
        "rss_guard_exceeded": guard.get("rss_guard_exceeded"),
        "rss_guard_returncode": guard.get("returncode"),
        "rss_guard_status": guard.get("status"),
        "rss_sample_count": guard.get("sample_count"),
        "official_decimal_limit_kib": guard.get("official_decimal_limit_kib"),
        "official_decimal_over_limit_kib": guard.get(
            "official_decimal_over_limit_kib"
        ),
        "guard_failure": guard.get("failure"),
    }


def result_record(
    result: dict[str, Any],
    result_path: pathlib.Path,
    guard: dict[str, Any] | None = None,
    guard_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    meta = artifact_metadata(result_path)
    record = {
        "result_path": rel(result_path),
        "result_json_bytes": meta["bytes"],
        "result_json_mtime_utc": meta["mtime_utc"],
        "result_json_sha256": meta["sha256"],
        "data_size": result.get("data_size"),
        "data_md5": result.get("data_md5"),
        "data_sha256": result.get("data_sha256"),
        "compressed_size": result.get("compressed_size"),
        "program_size": result.get("program_size"),
        "hutter_score": result.get("hutter_score"),
        "bits_per_byte": result.get("bits_per_byte"),
        "roundtrip_ok": result.get("roundtrip_ok"),
        "determinism": deterministic(result),
        "compressed_sha256": result.get("compressed_sha256"),
        "compress_time_s": result.get("compress_time_s"),
        "decompress_time_s": result.get("decompress_time_s"),
    }
    if guard is not None and guard_path is not None:
        record.update(guard_record(guard, guard_path))
    return record


def guard_only_record(
    guard: dict[str, Any],
    guard_path: pathlib.Path,
    scope: int | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "guard_path": rel(guard_path),
        "data_size": scope,
        "roundtrip_ok": False,
        "determinism": False,
    }
    record.update(guard_record(guard, guard_path))
    max_rss = guard.get("max_sampled_single_rss_kib")
    limit = guard.get("limit_kib")
    if isinstance(max_rss, int) and isinstance(limit, int):
        record["single_rss_over_ceiling_kib"] = max_rss - limit
    if isinstance(guard.get("failure"), str):
        record["failure"] = guard["failure"]
    elif guard.get("rss_guard_exceeded") is True:
        record["failure"] = "compression_rss_crossed_local_guard_before_archive_or_roundtrip"
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program_id")
    parser.add_argument("--result", type=pathlib.Path)
    parser.add_argument("--guard-json", type=pathlib.Path)
    parser.add_argument("--guard-only", action="store_true")
    parser.add_argument("--scope", type=int)
    parser.add_argument("--label")
    parser.add_argument("--terminal-index", type=pathlib.Path,
                        help="closed arm index already bound by a validated reflection")
    parser.add_argument("--check", action="store_true",
                        help="validate --terminal-index without recording")
    parser.add_argument("--status")
    parser.add_argument("--verdict")
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="append a note string to the recorded result",
    )
    args = parser.parse_args()

    if args.terminal_index is not None:
        if any((args.result, args.guard_json, args.guard_only, args.scope is not None,
                args.label, args.status, args.verdict, args.note)):
            parser.error("--terminal-index cannot be combined with legacy result or status options")
        try:
            outcome = record_terminal(args.program_id, args.terminal_index, check_only=args.check)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.exit(1, f"terminal recording refused: {exc}\n")
        except research_contracts.jsonschema.ValidationError as exc:
            parser.exit(1, f"terminal recording refused by evidence schema: {exc.message}\n")
        print(json.dumps(outcome, indent=2))
        return 0
    if args.check:
        parser.error("--check requires --terminal-index")
    if not args.label:
        parser.error("--label is required for legacy result recording")

    meta_path = PROGRAMS / args.program_id / "meta.json"
    if not meta_path.exists():
        raise SystemExit(f"missing meta.json: {rel(meta_path)}")
    guard = None
    guard_path = args.guard_json
    if guard_path is not None:
        if not guard_path.exists():
            raise SystemExit(f"missing guard JSON: {guard_path}")
        guard = load_json(guard_path)
    if args.guard_only:
        if guard is None or guard_path is None:
            raise SystemExit("--guard-only requires --guard-json")
        result_path = None
        result = None
    else:
        result_path = args.result or latest_result(args.program_id)
        if not result_path.exists():
            raise SystemExit(f"missing result JSON: {result_path}")
        result = load_json(result_path)

    meta = load_json(meta_path)
    if not isinstance(meta, dict):
        raise SystemExit(f"invalid meta shape: {rel(meta_path)}")
    if result is not None and not isinstance(result, dict):
        raise SystemExit(f"invalid result shape: {result_path}")
    if result is not None and result.get("program_id") != args.program_id:
        raise SystemExit(
            f"result program_id {result.get('program_id')!r} does not match {args.program_id!r}"
        )

    measured = meta.setdefault("measured", {})
    if not isinstance(measured, dict):
        measured = {}
        meta["measured"] = measured
    if args.guard_only:
        record = guard_only_record(guard, guard_path, args.scope)
    else:
        record = result_record(result, result_path, guard, guard_path)
    if args.note:
        record["notes"] = args.note
    measured[args.label] = record
    if result_path is not None:
        meta["latest_result"] = rel(result_path)
    if args.status:
        meta["status"] = args.status
    if args.verdict:
        meta["verdict"] = args.verdict

    write_json(meta_path, meta)
    print(
        json.dumps(
            {
                "meta": rel(meta_path),
                "label": args.label,
                "result": rel(result_path) if result_path is not None else None,
                "guard": rel(guard_path) if guard_path is not None else None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
