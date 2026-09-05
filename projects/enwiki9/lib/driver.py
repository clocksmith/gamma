"""Run a single program against enwik9 and emit a result JSON.

Usage: python3 lib/driver.py <program_id> [--data PATH] [--limit BYTES]
                              [--run-purpose PURPOSE] [--run-scope-label LABEL]
                              [--run-context CONTEXT] [--run-source SOURCE]
                              [--run-tag TAG]
                              [--check-determinism]
                              [--archive-ceiling BYTES]
                              [--determinism-archive-ceiling BYTES] [--no-save]

The driver:
  1. loads programs/<program_id>/program.py
  2. reads the dataset (or a prefix when --limit is set)
  3. compresses, decompresses, verifies the roundtrip
  4. measures sizes, times, and bits/byte
  5. (optional) compresses a second time and verifies byte-equal output
  6. writes results/<program_id>/<timestamp>.json
  7. appends one row to results/run_ledger.jsonl (unless --no-ledger)
  8. prints the result
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import stat
import sys
import tempfile
import time
import uuid

from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DEFAULT = ROOT / "data" / "enwik9"
RESULT_LEDGER_PATH = ROOT / "results" / "run_ledger.jsonl"
SCOPE_LABELS = {
    1024: "1k",
    250_000: "250k",
    1_000_000: "1m",
    10_000_000: "10m",
}

try:
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "tools"))
    import research_contracts


def _load(program_id: str):
    path = _candidate_program_dir(program_id) / "program.py"
    if not path.exists():
        raise SystemExit(f"program not found: {path}")
    spec = importlib.util.spec_from_file_location(f"prog_{program_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("compress", "decompress"):
        if not callable(getattr(mod, name, None)):
            raise SystemExit(f"{program_id}: missing callable {name}()")
    return mod, path


def _candidate_program_dir(program_id: str) -> pathlib.Path:
    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    snapshot_root = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if snapshot_id == program_id and snapshot_root:
        path = pathlib.Path(snapshot_root)
        if not path.is_dir():
            raise ValueError(f"candidate snapshot is missing: {path}")
        return path
    return ROOT / "programs" / program_id


def _sample_rss_kib() -> int | None:
    try:
        status = pathlib.Path("/proc/self/status")
        with status.open() as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
        return None
    except OSError:
        pass

    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(usage) if platform.system() != "Darwin" else int(usage // 1024)
    except Exception:
        return None


def _optional_diagnostic(callback, name: str, missing: list[dict]):
    try:
        value = callback()
        if value is None:
            missing.append({"name": name, "reason": "unavailable"})
        else:
            json.dumps(value, allow_nan=False)
        return value
    except Exception as exc:
        missing.append({"name": name, "reason": f"{type(exc).__name__}: {exc}"})
        return None


def _first_divergence(left: bytes, right: bytes) -> int | None:
    if left == right:
        return None
    return next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), min(len(left), len(right)))


def _write_atomic(path: pathlib.Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = pathlib.Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _load_program_metadata(program_id: str) -> dict[str, Any]:
    meta = _candidate_program_dir(program_id) / "meta.json"
    if not meta.exists():
        return {}
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_program_name(metadata: dict[str, Any]) -> str | None:
    data = metadata
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    desc = data.get("description")
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    return None


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _program_package_inventory(
    program_dir: pathlib.Path,
    metadata: dict[str, Any],
) -> tuple[list[tuple[str, int]], dict[str, Any]]:
    program_files: list[tuple[str, int]] = []
    receipts: list[dict[str, Any]] = []
    incomplete_reasons = [
        "driver package score is a local tree proxy, not a materialized submission dependency closure"
    ]
    for child in sorted(program_dir.rglob("*")):
        relative = child.relative_to(program_dir)
        if relative == pathlib.Path("meta.json"):
            continue
        if any(part == "__pycache__" or part.startswith(".") for part in relative.parts):
            continue
        try:
            mode = child.lstat().st_mode
        except OSError as exc:
            incomplete_reasons.append(f"cannot stat {relative.as_posix()}: {exc}")
            continue
        if stat.S_ISDIR(mode):
            continue
        if child.is_symlink():
            try:
                target = child.resolve(strict=True)
                size = target.stat().st_size
                digest = _sha256_file(target)
            except OSError as exc:
                incomplete_reasons.append(
                    f"unresolvable symlink {relative.as_posix()}: {exc}"
                )
                continue
            program_files.append((relative.as_posix(), size))
            receipts.append(
                {
                    "path": relative.as_posix(),
                    "bytes": size,
                    "sha256": digest,
                    "kind": "symlink-target-content",
                    "link_target": child.readlink().as_posix(),
                }
            )
            incomplete_reasons.append(
                f"submission closure cannot contain unresolved packaging semantics for symlink {relative.as_posix()}"
            )
            continue
        if not stat.S_ISREG(mode):
            incomplete_reasons.append(
                f"unsupported special package member {relative.as_posix()}"
            )
            continue
        size = child.stat().st_size
        program_files.append((relative.as_posix(), size))
        receipts.append(
            {
                "path": relative.as_posix(),
                "bytes": size,
                "sha256": _sha256_file(child),
                "kind": "regular-file",
            }
        )

    dependencies = metadata.get("deps")
    declared_dependencies = dependencies if isinstance(dependencies, list) else []
    if not isinstance(dependencies, list):
        incomplete_reasons.append("meta.json does not declare a deps array")
    package = {
        "accounting_class": "local-program-tree-proxy",
        "recursive": True,
        "counted_files": receipts,
        "declared_dependencies": declared_dependencies,
        "dependency_closure_complete": False,
        "dependency_closure_failure_reasons": incomplete_reasons,
    }
    return program_files, package


def _normalize_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _bound_candidate_revision(program_id: str) -> dict[str, Any] | None:
    raw = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    if raw is None:
        return None
    try:
        binding = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid candidate revision binding JSON") from exc
    if not isinstance(binding, dict) or binding.get("candidateId") != program_id:
        raise ValueError("candidate revision binding identifies another candidate")
    tree_digest = binding.get("candidateTreeSha256")
    receipt = binding.get("receipt")
    if (
        not isinstance(tree_digest, str)
        or not tree_digest.startswith("sha256:")
        or not isinstance(receipt, dict)
        or not isinstance(receipt.get("path"), str)
        or not isinstance(receipt.get("sha256"), str)
    ):
        raise ValueError("candidate revision binding is incomplete")
    return binding


def _infer_scope_label(limit: int | None) -> str:
    if limit is None:
        return "full"
    return SCOPE_LABELS.get(limit, f"{limit}B")


def _infer_run_purpose(
    run_purpose: str | None,
    limit: int | None,
    check_determinism: bool,
) -> str:
    if run_purpose is not None:
        return run_purpose
    if check_determinism:
        return "verification"
    if limit in SCOPE_LABELS:
        return "smoke"
    if limit is None:
        return "replay"
    return "candidate"


def _parse_run_tags(raw: list[str]) -> list[str]:
    values: list[str] = []
    for item in raw:
        for part in item.split(","):
            token = part.strip()
            if token:
                values.append(token)
    deduped: list[str] = []
    seen: set[str] = set()
    for token in values:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return deduped


def _append_run_ledger(row: dict[str, Any]) -> None:
    research_contracts.validate_driver_run_ledger_row(row)
    RESULT_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_LEDGER_PATH.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, sort_keys=True) + "\n")


def _build_run_ledger_row(
    result: dict[str, Any],
    result_path: pathlib.Path | None,
    program_name: str | None,
    no_save: bool,
) -> dict[str, Any]:
    if result_path is None or no_save:
        raise ValueError("ledger rows require one persisted result JSON")
    return research_contracts.build_driver_run_ledger_row(
        result,
        result_path,
        program_name=program_name,
        recorded_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    )

def run(
    program_id: str,
    data_path: pathlib.Path,
    limit: int | None,
    check_determinism: bool = False,
    archive_ceiling: int | None = None,
    determinism_archive_ceiling: int | None = None,
    run_purpose: str | None = None,
    run_scope_label: str | None = None,
    run_context: str | None = None,
    run_source: str | None = None,
    run_tags: list[str] | None = None,
    *,
    arm: str | None = None,
    module=None,
    artifact_dir: pathlib.Path | None = None,
    mode: str = "discovery",
) -> dict:
    run_started = time.perf_counter()
    objective = research_contracts.objective_binding()
    inferred_purpose = _infer_run_purpose(
        run_purpose=_normalize_text(run_purpose),
        limit=limit,
        check_determinism=check_determinism,
    )
    inferred_scope_label = _normalize_text(run_scope_label) or _infer_scope_label(limit)
    normalized_context = _normalize_text(run_context)
    normalized_source = _normalize_text(run_source)
    normalized_tags = run_tags or []
    if mode not in {"discovery", "qualification"}:
        raise ValueError("unknown execution mode")
    mod, src_path = _load(program_id) if module is None else (module, _candidate_program_dir(program_id) / "program.py")
    compress = mod.compress if arm is None else lambda raw: mod.compress_arm(raw, arm)
    decompress = mod.decompress if arm is None else lambda archive: mod.decompress_arm(archive, arm)
    metadata = _load_program_metadata(program_id)
    program_name = _load_program_name(metadata)
    if limit is not None and limit <= 0:
        raise ValueError("input limit must be positive")
    with data_path.open("rb") as stream:
        raw = stream.read() if limit is None else stream.read(limit)
    data_md5 = hashlib.md5(raw).hexdigest()
    data_sha256 = hashlib.sha256(raw).hexdigest()
    missing_diagnostics = []
    sample = lambda: _optional_diagnostic(_sample_rss_kib, "rss", missing_diagnostics)
    rss_before = sample()

    compress_started = time.perf_counter()
    compressed = compress(raw)
    t_compress = time.perf_counter() - compress_started
    stats_fn = getattr(mod, "stats", None)
    program_stats = _optional_diagnostic(stats_fn, "program_stats", missing_diagnostics) if callable(stats_fn) else None
    compressed_size = len(compressed)

    archive_ceiling_missed = archive_ceiling is not None and compressed_size > archive_ceiling
    if archive_ceiling_missed:
        t_decompress = 0.0
        ok = None
    else:
        decompress_started = time.perf_counter()
        decompressed = decompress(compressed)
        t_decompress = time.perf_counter() - decompress_started
        ok = decompressed == raw
    program_dir = src_path.parent
    program_files, package_accounting = _program_package_inventory(
        program_dir,
        metadata,
    )
    program_size = sum(sz for _, sz in program_files)
    archive_md5 = hashlib.md5(compressed).hexdigest()
    archive_sha256 = hashlib.sha256(compressed).hexdigest()
    rss_after_compress = sample()

    determinism: dict | None = None
    should_check_determinism = (
        check_determinism
        and not archive_ceiling_missed
        and (
            determinism_archive_ceiling is None
            or compressed_size <= determinism_archive_ceiling
        )
    )
    if should_check_determinism:
        compressed2 = compress(raw)
        det_ok = compressed == compressed2
        det_md5 = hashlib.md5(compressed2).hexdigest()
        det_sha256 = hashlib.sha256(compressed2).hexdigest()
        determinism = {
            "single_host_byte_equal": det_ok,
            "first_run_md5": archive_md5,
            "second_run_md5": det_md5,
            "first_run_sha256": archive_sha256,
            "second_run_sha256": det_sha256,
            "first_divergence_byte": None
            if det_ok
            else next(
                (i for i, (a, b) in enumerate(zip(compressed, compressed2)) if a != b),
                min(len(compressed), len(compressed2)),
            ),
        }
    elif check_determinism:
        determinism = {
            "single_host_byte_equal": None,
            "skipped": True,
            "reason": "archive_ceiling_missed"
            if archive_ceiling_missed
            else "determinism_archive_ceiling_missed",
            "archive_ceiling": archive_ceiling,
            "determinism_archive_ceiling": determinism_archive_ceiling,
        }

    bits_per_byte = (compressed_size * 8 / len(raw)) if raw else 0.0
    t_total = time.perf_counter() - run_started
    rss_after = sample()
    rss_samples = [v for v in (rss_before, rss_after_compress, rss_after) if isinstance(v, int)]
    rss_peak = max(rss_samples) if rss_samples else None

    result = {
        "schema": "gamma.enwiki9.driver-result.v2",
        "objective": objective,
        "program_id": program_id,
        "candidate_revision": _bound_candidate_revision(program_id),
        "data_path": str(data_path),
        "data_size": len(raw),
        "data_md5": data_md5,
        "data_sha256": data_sha256,
        "compressed_size": compressed_size,
        "compressed_md5": archive_md5,
        "compressed_sha256": archive_sha256,
        "program_size": program_size,
        "program_files": program_files,
        "package_accounting": package_accounting,
        "hutter_score": compressed_size + program_size,
        "hutter_score_kind": "local-tree-proxy-incomplete-dependency-closure",
        "score_accounting_complete": False,
        "prize_claimable": False,
        "bits_per_byte": round(bits_per_byte, 6),
        "compress_time_s": round(t_compress, 4),
        "decompress_time_s": round(t_decompress, 4),
        "roundtrip_ok": ok,
        "first_divergence_byte": None if archive_ceiling_missed else _first_divergence(raw, decompressed),
        "arm": arm,
        "execution_mode": mode,
        "timing_authority": "diagnostic",
        "qualification_status": "not-certified-missing-isolation-calibration-and-continuous-resource-evidence",
        "missing_diagnostics": missing_diagnostics,
        "roundtrip_skipped": {
            "reason": "archive_ceiling_missed",
            "archive_ceiling": archive_ceiling,
        }
        if archive_ceiling_missed
        else None,
        "run_purpose": inferred_purpose,
        "run_scope_label": inferred_scope_label,
        "run_context": normalized_context,
        "run_source": normalized_source,
        "run_tags": normalized_tags,
        "determinism": determinism,
        "host": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
            "node": platform.node(),
        },
        "program_name": program_name,
        "memory_kib": {
            "measurement_scope": "driver-process-boundary-samples",
            "measurement_complete": False,
            "before": rss_before,
            "during_compress": rss_after_compress,
            "after": rss_after,
            "peak": rss_peak,
            "sample_count": len(rss_samples),
        },
        "resource_evidence_complete": False,
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    result["run_time_s"] = round(t_total, 4)
    result["run_time_scope"] = (
        "driver invocation through input read, module load, compression, decompression, "
        "optional deterministic re-encode, package hashing, and boundary resource sampling"
    )
    if program_stats is not None:
        result["program_stats"] = program_stats
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=False)
        artifacts = {"archive": ("archive.bin", compressed)}
        if not archive_ceiling_missed:
            artifacts["restored"] = ("restored.bin", decompressed)
        if should_check_determinism:
            artifacts["repeat_archive"] = ("repeat.bin", compressed2)
        result["artifacts"] = {}
        for name, (filename, payload) in artifacts.items():
            path = artifact_dir / filename
            _write_atomic(path, payload)
            result["artifacts"][name] = {"path": filename, "bytes": len(payload), "sha256": _sha256_file(path)}
        _write_atomic(artifact_dir / "result.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def compare(program_id: str, data_path: pathlib.Path, limit: int, specification: dict,
            output: pathlib.Path, *, mode: str = "discovery", record_ledger: bool = False) -> dict:
    """Run all frozen arms from one module/build; close artifacts before decision.

    Qualification timing remains uncertified here: the isolated queue and release
    resource verifier supply that evidence. Neither this mode flag nor a byte win
    grants automatic promotion.
    """
    required = ("hypothesis", "parent", "changed_mechanism", "development_budget",
                "selection_population", "sealed_confirmation", "stop_rule", "arms")
    if any(key not in specification or not specification[key] for key in required):
        raise ValueError("comparison requires a complete bounded mutation specification")
    arms = specification["arms"]
    if not isinstance(arms, dict) or not {"parent", "bookkeeping", "treatment"} <= set(arms):
        raise ValueError("comparison needs parent, bookkeeping and treatment arms")
    if len(set(arms.values())) != len(arms) or any(not isinstance(a, str) or not a.replace("_", "").isalnum() for a in arms.values()):
        raise ValueError("arm identifiers must be unique safe names")
    if not 0 < limit <= 10_000_000:
        raise ValueError("comparison needs an explicit bounded input scope <=10MB")
    if record_ledger and not output.resolve().is_relative_to((ROOT / "results").resolve()):
        raise ValueError("canonical comparisons must retain artifacts under project results/")
    module, source = _load(program_id)
    if not all(callable(getattr(module, name, None)) for name in ("compress_arm", "decompress_arm")):
        raise ValueError("candidate must implement explicit compress_arm/decompress_arm adapters")
    metadata = _load_program_metadata(program_id)
    inventory_before = _program_package_inventory(source.parent, metadata)[1]["counted_files"]
    implementation_paths = [source, *sorted((ROOT / "lib").glob("*.py")),
                            *research_contracts.local_source_closure([ROOT / "tools/research_contracts.py"])]
    implementation_before = {str(path): _sha256_file(path) for path in implementation_paths}
    output.mkdir(parents=True, exist_ok=False)
    _write_atomic(output / "specification.json", (json.dumps(specification, indent=2) + "\n").encode())
    rows = {}
    errors = {}
    for role, arm in arms.items():
        try:
            rows[role] = run(program_id, data_path, limit, True, run_purpose="control" if role != "treatment" else "candidate",
                             arm=arm, module=module, artifact_dir=output / arm, mode=mode)
        except Exception as exc:
            errors[role] = {"type": type(exc).__name__, "message": str(exc)}
    source_stable = (inventory_before == _program_package_inventory(source.parent, metadata)[1]["counted_files"]
                     and implementation_before == {str(path): _sha256_file(path) for path in implementation_paths})
    population_stable = len({(r["data_size"], r["data_sha256"]) for r in rows.values()}) == 1
    exact = not errors and population_stable and all(r["roundtrip_ok"] is True and r["determinism"]["single_host_byte_equal"] is True for r in rows.values())
    identity = bool(exact and rows["parent"]["compressed_sha256"] == rows["bookkeeping"]["compressed_sha256"])
    delta = rows["treatment"]["compressed_size"] - rows["parent"]["compressed_size"] if "treatment" in rows and "parent" in rows else None
    decision = {
        "schema": "gamma.enwiki9.driver-comparison.v1", "objective": research_contracts.objective_binding(),
        "program_id": program_id, "specification_sha256": _sha256_file(output / "specification.json"),
        "source_files": inventory_before, "driver_sha256": _sha256_file(pathlib.Path(__file__)),
        "implementation_files": {str(pathlib.Path(path).relative_to(ROOT)) if pathlib.Path(path).is_relative_to(ROOT) else path: digest
                                 for path, digest in implementation_before.items()},
        "source_stable": source_stable, "same_candidate_build": source_stable,
        "same_input_population": population_stable,
        "exact_roundtrips_and_repeats": exact, "parent_bookkeeping_identity": identity,
        "treatment_minus_parent_bytes": delta, "execution_mode": mode, "timing_authority": "diagnostic",
        "qualification_complete": False, "promotion_authorized": False, "objective_credit": 0,
        "arms": {role: {"arm": arms[role], "result": f"{arms[role]}/result.json", "result_sha256": _sha256_file(output / arms[role] / "result.json")} for role in rows},
        "errors": errors,
        "verdict": "invalid" if not (exact and identity and source_stable) else "measured-improvement" if delta < 0 else "measured-no-improvement",
    }
    if record_ledger:
        for role, row in rows.items():
            result_path = output / arms[role] / "result.json"
            _append_run_ledger(_build_run_ledger_row(row, result_path, row.get("program_name"), False))
    _write_atomic(output / "decision.json", (json.dumps(decision, indent=2) + "\n").encode())
    return decision


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("program_id")
    ap.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only use the first N bytes (smoke testing)",
    )
    ap.add_argument(
        "--check-determinism",
        action="store_true",
        help="compress twice and verify byte-equal output (single-host determinism)",
    )
    ap.add_argument(
        "--archive-ceiling",
        type=int,
        default=None,
        help="skip roundtrip and determinism when the first archive misses this byte ceiling",
    )
    ap.add_argument(
        "--determinism-archive-ceiling",
        type=int,
        default=None,
        help="skip the second compression when the first archive misses this byte ceiling",
    )
    ap.add_argument(
        "--run-purpose",
        default=None,
        help=(
            "provenance label for this run (for example: smoke|gate|control|"
            "verification|rebaseline|replay)"
        ),
    )
    ap.add_argument(
        "--run-scope-label",
        default=None,
        help="override inferred scope label (for example: full|1k|250k|1m|10m)",
    )
    ap.add_argument(
        "--run-context",
        default=None,
        help="short workflow/lane context label (for example: cmix21_1m_queue)",
    )
    ap.add_argument(
        "--run-source",
        default=None,
        help="how this run was launched (manual|queue|script|gate|normalized)",
    )
    ap.add_argument(
        "--run-tag",
        action="append",
        default=[],
        help="repeatable provenance tag (or comma-separated list)",
    )
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--mode", choices=("discovery", "qualification"), default=os.environ.get("GAMMA_ENWIKI9_EXECUTION_MODE", "discovery"))
    ap.add_argument("--comparison", type=pathlib.Path, help="frozen same-build arm and mutation specification")
    ap.add_argument("--output", type=pathlib.Path, help="new comparison artifact directory")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"dataset missing at {args.data} — run bench.py --setup first")

    if args.comparison:
        if args.output is None or args.limit is None:
            ap.error("--comparison requires --output and --limit")
        decision = compare(args.program_id, args.data, args.limit, json.loads(args.comparison.read_text()), args.output,
                           mode=args.mode, record_ledger=not args.no_ledger)
        print(json.dumps(decision, indent=2))
        return 1 if decision["verdict"] == "invalid" else 0

    result = run(
        args.program_id,
        args.data,
        args.limit,
        args.check_determinism,
        args.archive_ceiling,
        args.determinism_archive_ceiling,
        run_purpose=args.run_purpose,
        run_scope_label=args.run_scope_label,
        run_context=args.run_context,
        run_source=args.run_source,
        run_tags=_parse_run_tags(args.run_tag),
        mode=args.mode,
    )

    if not args.no_save:
        out_dir = ROOT / "results" / args.program_id
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = result["timestamp"].replace(":", "") + "_" + uuid.uuid4().hex[:12]
        result_path = out_dir / f"{stamp}.json"
        _write_atomic(result_path, (json.dumps(result, indent=2) + "\n").encode())
        if not args.no_ledger:
            ledger_row = _build_run_ledger_row(
                result,
                result_path=result_path,
                program_name=result.get("program_name"),
                no_save=args.no_save,
            )
            _append_run_ledger(ledger_row)

    print(json.dumps(result, indent=2))
    return 0 if result["roundtrip_ok"] is not False else 1


if __name__ == "__main__":
    sys.exit(main())
