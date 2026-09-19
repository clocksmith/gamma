"""Deterministic projection of an authenticated driver result."""
from pathlib import Path
from typing import Any
import datetime as dt
import hashlib


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def file_digest(path, algorithm):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def _driver_scope_label(data_size: Any) -> str:
    labels = {
        1024: "1k",
        250_000: "250k",
        1_000_000: "1m",
        10_000_000: "10m",
        1_000_000_000: "full",
    }
    return labels.get(data_size, f"{data_size}B" if isinstance(data_size, int) else "unknown")

def build_driver_run_ledger_row(
    result: dict[str, Any],
    result_path: Path,
    *,
    program_name: str | None,
    recorded_utc: str | None = None,
    project_root: Path,
    validate_row,
) -> dict[str, Any]:
    resolved = result_path.resolve()
    _require(
        project_root in resolved.parents and resolved.is_file(),
        f"driver result escapes project or is missing: {result_path}",
    )
    relative = resolved.relative_to(project_root).as_posix()
    determinism = result.get("determinism")
    determinism_ok = (
        determinism.get("single_host_byte_equal")
        if isinstance(determinism, dict)
        else None
    )
    data_size = result.get("data_size")
    purpose = result.get("run_purpose")
    if not isinstance(purpose, str) or not purpose:
        purpose = (
            "verification"
            if determinism_ok is not None
            else "smoke"
            if data_size in {1024, 250_000, 1_000_000, 10_000_000, 1_000_000_000}
            else "candidate"
        )
    scope = result.get("run_scope_label")
    if not isinstance(scope, str) or not scope:
        scope = _driver_scope_label(data_size)
    tags = result.get("run_tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        tags = []
    compressed_md5 = result.get("compressed_md5")
    run_suffix = compressed_md5[:8] if isinstance(compressed_md5, str) else "missing"
    timestamp = result.get("timestamp")
    _require(isinstance(timestamp, str) and timestamp, f"{result_path}: missing timestamp")
    program_id = result.get("program_id")
    _require(isinstance(program_id, str) and program_id, f"{result_path}: missing program_id")
    memory = result.get("memory_kib")
    if not isinstance(memory, dict):
        memory = {}
    stat = resolved.stat()
    row = {
        "schema": "gamma.enwiki9.driver-run-ledger-row.v2",
        "run_id": f"{program_id}__{timestamp.replace(':', '')}__{run_suffix}",
        "program_id": program_id,
        "candidate_revision": result.get("candidate_revision"),
        "algorithm_name": program_name or program_id,
        "data_path": result.get("data_path"),
        "data_size": data_size,
        "data_md5": result.get("data_md5"),
        "data_sha256": result.get("data_sha256"),
        "compressed_md5": compressed_md5,
        "compressed_sha256": result.get("compressed_sha256"),
        "compressed_size": result.get("compressed_size"),
        "program_size": result.get("program_size"),
        "hutter_score": result.get("hutter_score"),
        "bits_per_byte": result.get("bits_per_byte"),
        "compress_time_s": result.get("compress_time_s"),
        "decompress_time_s": result.get("decompress_time_s"),
        "run_time_s": result.get("run_time_s"),
        "run_purpose": purpose,
        "run_scope_label": scope,
        "run_context": result.get("run_context"),
        "run_source": result.get("run_source"),
        "run_tags": list(dict.fromkeys(tags)),
        "determinism_ok": determinism_ok,
        "roundtrip_ok": result.get("roundtrip_ok"),
        "result_path": relative,
        "result_bytes": stat.st_size,
        "result_sha256": file_digest(resolved, "sha256"),
        "archival_scope": "full",
        "timestamp": timestamp,
        "recorded_utc": recorded_utc
        or dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "host": result.get("host"),
        "memory_kib_before": memory.get("before"),
        "memory_kib_after": memory.get("after"),
        "memory_kib_peak": memory.get("peak"),
        "rss_sample_count": memory.get("sample_count"),
    }
    validate_row(row)
    return row
