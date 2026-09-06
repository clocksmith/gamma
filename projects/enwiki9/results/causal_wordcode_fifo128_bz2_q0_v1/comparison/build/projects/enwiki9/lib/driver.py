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
import ast
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import stat
import subprocess
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

def _run_local(
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
    package_inventory: tuple | None = None,
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
    rss_after_compress = sample()

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
    program_files, package_accounting = package_inventory or _program_package_inventory(
        program_dir, metadata,
    )
    program_size = sum(sz for _, sz in program_files)
    archive_md5 = hashlib.md5(compressed).hexdigest()
    archive_sha256 = hashlib.sha256(compressed).hexdigest()

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



def _comparison_source_closure(source: pathlib.Path) -> list[pathlib.Path]:
    """Collect local Python imports without executing candidate or tool code."""
    program = source.parent.resolve()
    paths = {source.resolve(), *[p.resolve() for p in (ROOT / "lib").glob("*.py")],
             *research_contracts.local_source_closure([ROOT / "tools/research_contracts.py"])}
    pending = [*paths, *program.rglob("*.py")]
    visited = set()
    while pending:
        path = pending.pop().resolve()
        if path in visited or path.suffix != ".py":
            continue
        visited.add(path)
        paths.add(path)
        for node in ast.walk(ast.parse(path.read_bytes(), filename=str(path))):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
                bases = [path.parent, program, ROOT, ROOT / "lib", ROOT / "tools", ROOT.parents[1]]
            elif isinstance(node, ast.ImportFrom):
                prefix = node.module or ""
                modules = [prefix, *[f"{prefix}.{alias.name}".strip(".") for alias in node.names]]
                bases = ([path.parents[node.level - 1]] if node.level
                         else [path.parent, program, ROOT, ROOT / "lib", ROOT / "tools", ROOT.parents[1]])
            else:
                continue
            for module in modules:
                if not module or "*" in module:
                    continue
                for base in bases:
                    target = base.joinpath(*module.split("."))
                    for candidate in (target.with_suffix(".py"), target / "__init__.py"):
                        resolved = candidate.resolve()
                        if candidate.is_file() and (resolved.is_relative_to(ROOT) or resolved.is_relative_to(program)):
                            pending.append(resolved)
    return sorted(paths)


def _freeze_comparison_build(program_id: str, source: pathlib.Path, output: pathlib.Path,
                             *, inventory: tuple | None = None,
                             source_hashes: dict | None = None) -> dict:
    """Retain exact input bytes; every phase imports only these local sources."""
    inventory = inventory or _program_package_inventory(source.parent, _load_program_metadata(program_id))
    closure = _comparison_source_closure(source)
    inputs = {path: pathlib.Path("projects/enwiki9") / path.relative_to(ROOT)
              for path in closure if path.is_relative_to(ROOT) and not path.is_relative_to(source.parent)}
    for record in inventory[1]["counted_files"]:
        path = source.parent / record["path"]
        inputs[path] = pathlib.Path("projects/enwiki9/programs") / program_id / record["path"]
    if (source.parent / "meta.json").is_file():
        inputs[source.parent / "meta.json"] = pathlib.Path("projects/enwiki9/programs") / program_id / "meta.json"
    expected = {str(path): _sha256_file(path) for path in inputs}
    expected.update({str(source.parent / record["path"]): record["sha256"]
                     for record in inventory[1]["counted_files"]})
    expected.update(source_hashes or {})
    build_root = output / "build"
    build_root.mkdir(parents=True, exist_ok=False)
    files = {}
    for path, relative in sorted(inputs.items()):
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected[str(path)]:
            raise ValueError(f"source changed while freezing comparison build: {path}")
        target = build_root / relative
        _write_atomic(target, payload)
        target.chmod(0o444 | (path.stat().st_mode & 0o111))
        files[relative.as_posix()] = {"bytes": len(payload), "sha256": digest}
    manifest = {"schema": "gamma.enwiki9.comparison-build.v1", "candidate_id": program_id,
                "files": files,
                "source_policy": "retained candidate files and hash-checked local Python imports; native/external executables, absolute-path inputs, third-party dependencies and filesystem isolation are not verified"}
    manifest_path = output / "build.json"
    _write_atomic(manifest_path, (json.dumps(manifest, indent=2) + "\n").encode())
    return {"root": build_root, "manifest_path": manifest_path, "manifest": manifest,
            "sha256": _sha256_file(manifest_path), "package_inventory": inventory,
            "source": build_root / "projects/enwiki9/programs" / program_id / "program.py"}


# This bootstrap is passed directly to Python. It verifies the frozen driver
# before executing it, then verifies the bytes of each imported local module.
_COMPARISON_BOOTSTRAP = r'''
import hashlib, importlib.abc, importlib.machinery, json, os, pathlib, sys
build, manifest_path, expected, receipt_path, original_root, *arguments = sys.argv[1:]
build, original_root = pathlib.Path(build).resolve(), pathlib.Path(original_root).resolve()
payload = pathlib.Path(manifest_path).read_bytes()
if hashlib.sha256(payload).hexdigest() != expected:
    raise ValueError("frozen build manifest changed")
manifest = json.loads(payload)
loaded = {}
def checked_code(path):
    path = pathlib.Path(path).resolve()
    relative = path.relative_to(build).as_posix()
    record = manifest["files"].get(relative)
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if record != {"bytes": len(payload), "sha256": digest}:
        raise ValueError("frozen source bytes changed: " + relative)
    loaded[relative] = digest
    return compile(payload, str(path), "exec")
class CheckedLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return checked_code(self.path)
class CheckedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec and spec.origin and spec.origin.endswith((".py", ".pyc")):
            origin = pathlib.Path(spec.origin).resolve()
            if origin.is_relative_to(build):
                if origin.suffix != ".py":
                    raise ImportError("local bytecode import lacks a source binding: " + str(origin))
                spec.loader = CheckedLoader(fullname, str(origin))
            elif origin.is_relative_to(original_root):
                raise ImportError("unfrozen project import: " + str(origin))
        return spec
sys.meta_path.insert(0, CheckedFinder())
sys.path.insert(0, str(build))
sys.path.insert(0, str(build / "projects/enwiki9/lib"))
sys.path.insert(0, str(pathlib.Path(arguments[1]).parent))
sys._gamma_checked_code = checked_code
driver = build / "projects/enwiki9/lib/driver.py"
sys.argv = [str(driver), *arguments]
try:
    exec(checked_code(driver), {"__name__": "__main__", "__file__": str(driver)})
finally:
    record = {"build_manifest_sha256": expected, "loaded_sources": loaded, "pid": os.getpid()}
    destination = pathlib.Path(receipt_path)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(destination)
'''


def _codec_phase_worker(arguments: list[str]) -> int:
    """Private child entry point: one source build, one operation, stdin bytes only."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("phase", choices=("encode", "decode", "repeat"))
    parser.add_argument("arm")
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("diagnostics", type=pathlib.Path)
    args = parser.parse_args(arguments)
    diagnostics = {"phase": args.phase, "pid": os.getpid(), "missing_diagnostics": []}
    try:
        source = args.source.resolve(strict=True)
        spec = importlib.util.spec_from_file_location("enwiki9_codec_phase", source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        checked_code = getattr(sys, "_gamma_checked_code", None)
        if not callable(checked_code):
            raise ValueError("codec phase requires a verified frozen build")
        exec(checked_code(source), module.__dict__)
        operation = "decompress_arm" if args.phase == "decode" else "compress_arm"
        function = getattr(module, operation, None)
        if not callable(function):
            raise ValueError(f"candidate lacks {operation} adapter")
        phase_input = sys.stdin.buffer.read()
        started = time.perf_counter()
        payload = function(phase_input, args.arm)
        diagnostics["codec_time_s"] = time.perf_counter() - started
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise TypeError("codec operation must return bytes")
        _write_atomic(args.output, payload)
        diagnostics["codec_complete"] = True
    except Exception as exc:
        diagnostics["codec_complete"] = False
        diagnostics["error"] = {"type": type(exc).__name__, "message": str(exc)}
    if diagnostics["codec_complete"] and args.phase != "decode":
        try:
            stats = getattr(module, "stats", None)
        except Exception as exc:
            stats = None
            diagnostics["missing_diagnostics"].append({"name": "program_stats", "reason": f"{type(exc).__name__}: {exc}"})
        if callable(stats):
            diagnostics["program_stats"] = _optional_diagnostic(stats, "program_stats", diagnostics["missing_diagnostics"])
    try:
        _write_atomic(args.diagnostics, (json.dumps(diagnostics, indent=2, allow_nan=False) + "\n").encode())
    except Exception as exc:
        # The closed codec output remains authoritative when optional telemetry
        # cannot be published. The parent records this explicit diagnostic gap.
        print(f"phase diagnostics unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0 if diagnostics["codec_complete"] else 1


def _artifact_binding(path: pathlib.Path) -> dict:
    return {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _verify_frozen_build(build: dict) -> list[str]:
    failures = []
    try:
        if _sha256_file(build["manifest_path"]) != build["sha256"]:
            failures.append("frozen build manifest changed")
    except OSError as exc:
        failures.append(f"frozen build manifest: {exc}")
    for relative, expected in build["manifest"]["files"].items():
        path = build["root"] / relative
        try:
            if (path.is_symlink() or path.stat().st_size != expected["bytes"]
                    or _sha256_file(path) != expected["sha256"]):
                failures.append(f"frozen build bytes changed: {relative}")
        except OSError as exc:
            failures.append(f"frozen build {relative}: {exc}")
    return failures


def _run_independent_arm(local_arguments: tuple, local_options: dict, directory: pathlib.Path) -> dict:
    from types import SimpleNamespace

    program_id = local_arguments[0] if local_arguments else local_options["program_id"]
    arm = local_options["arm"]
    directory.mkdir(parents=True, exist_ok=False)
    local_options = dict(local_options)
    build = local_options.pop("frozen_build", None)
    if build is None:
        build = _freeze_comparison_build(
            program_id, _candidate_program_dir(program_id) / "program.py", directory,
        )
    source = build["source"]
    context = {"active_phase": None, "artifacts": {}, "phases": {}, "missing_diagnostics": []}
    proxy = SimpleNamespace()
    encode_calls = 0

    def phase(operation: str, payload: bytes) -> bytes:
        context["active_phase"] = operation
        if operation == "encode":
            context.update(data_size=len(payload), data_sha256=hashlib.sha256(payload).hexdigest())
        filename = {"encode": "archive.bin", "decode": "restored.bin", "repeat": "repeat.bin"}[operation]
        artifact_name = {"encode": "archive", "decode": "restored", "repeat": "repeat_archive"}[operation]
        output = directory / filename
        diagnostics = directory / f"{operation}.json"
        source_receipt = directory / f"{operation}.sources.json"
        build_errors = _verify_frozen_build(build)
        if build_errors:
            raise ValueError("; ".join(build_errors))
        command = [sys.executable, "-c", _COMPARISON_BOOTSTRAP,
                   str(build["root"].resolve()), str(build["manifest_path"].resolve()),
                   build["sha256"], str(source_receipt.resolve()), str(ROOT.resolve()), "--_codec-phase",
                   str(source.resolve()), operation, arm, str(output.resolve()), str(diagnostics.resolve())]
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        with (directory / f"{operation}.stdout.log").open("xb") as stdout, (directory / f"{operation}.stderr.log").open("xb") as stderr:
            completed = subprocess.run(command, input=payload, stdout=stdout, stderr=stderr,
                                       cwd=build["root"] / "projects/enwiki9", env=environment)
        for suffix in ("stdout.log", "stderr.log"):
            context["artifacts"][f"{operation}_{suffix}"] = _artifact_binding(directory / f"{operation}.{suffix}")
        detail = {}
        try:
            detail = json.loads(diagnostics.read_text())
            if not isinstance(detail, dict):
                raise ValueError("phase diagnostics must be an object")
            context["artifacts"][f"{operation}_diagnostics"] = _artifact_binding(diagnostics)
        except (OSError, ValueError) as exc:
            context["missing_diagnostics"].append({"name": "phase_diagnostics", "phase": operation,
                                                     "reason": f"{type(exc).__name__}: {exc}"})
        context["phases"][operation] = {"returncode": completed.returncode, "pid": detail.get("pid"),
                                          "input_bytes": len(payload), "input_sha256": hashlib.sha256(payload).hexdigest(),
                                          "codec_time_s": detail.get("codec_time_s")}
        context["missing_diagnostics"].extend(detail.get("missing_diagnostics", []))
        if output.is_file():
            context["artifacts"][artifact_name] = _artifact_binding(output)
        # Loaded-source identity is mandatory evidence, unlike codec statistics.
        receipt = json.loads(source_receipt.read_text())
        loaded = receipt.get("loaded_sources")
        if receipt.get("build_manifest_sha256") != build["sha256"] or not isinstance(loaded, dict):
            raise ValueError("codec child has no valid loaded-source receipt")
        for relative, digest in loaded.items():
            if build["manifest"]["files"].get(relative, {}).get("sha256") != digest:
                raise ValueError(f"codec child loaded unbound source: {relative}")
        if completed.returncode == 0 and source.relative_to(build["root"]).as_posix() not in loaded:
            raise ValueError("codec child did not bind its loaded candidate source")
        context["artifacts"][f"{operation}_sources"] = _artifact_binding(source_receipt)
        context["phases"][operation]["loaded_sources"] = loaded
        context["phases"][operation]["build_manifest_sha256"] = build["sha256"]
        if completed.returncode != 0:
            error = detail.get("error") or {}
            raise RuntimeError(f"{operation} child exited {completed.returncode}: {error.get('type', 'codec failure')}: {error.get('message', '')}")
        if not output.is_file():
            raise RuntimeError(f"{operation} child exited without a closed output")
        if operation == "encode" and "program_stats" in detail and detail["program_stats"] is not None:
            proxy.stats = lambda: detail["program_stats"]
        context["active_phase"] = None
        return output.read_bytes()

    def compress(raw, _arm):
        nonlocal encode_calls
        operation = "encode" if encode_calls == 0 else "repeat"
        encode_calls += 1
        return phase(operation, raw)

    proxy.compress_arm = compress
    proxy.decompress_arm = lambda archive, _arm: phase("decode", archive)
    options = {**local_options, "module": proxy, "artifact_dir": None,
               "package_inventory": build["package_inventory"]}
    try:
        result = _run_local(*local_arguments, **options)
        result["failed_phase"] = None
    except Exception as exc:
        result = {"schema": "gamma.enwiki9.driver-arm-failure.v1", "program_id": program_id, "arm": arm,
                  "failed_phase": context["active_phase"] or "result-preparation",
                  "failure": {"type": type(exc).__name__, "message": str(exc)},
                  "data_size": context.get("data_size"), "data_sha256": context.get("data_sha256"),
                  "roundtrip_ok": False, "determinism": None,
                  "execution_mode": local_options.get("mode", "discovery"), "timing_authority": "diagnostic",
                  "resource_evidence_complete": False, "prize_claimable": False, "missing_diagnostics": []}
    result["artifacts"] = context["artifacts"]
    result["phase_execution"] = context["phases"]
    result["codec_process_state"] = "fresh-process-per-encode-decode-repeat"
    result["build_manifest_sha256"] = build["sha256"]
    result["codec_time_scope"] = "compress_time_s/decompress_time_s include child startup, initialization, codec execution and publication; phase_execution codec_time_s measures the child codec call only"
    result["missing_diagnostics"].extend(context["missing_diagnostics"])
    _write_atomic(directory / "result.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def run(*args, **kwargs) -> dict:
    """Preserve legacy calls; comparison arms use independent codec processes."""
    if kwargs.get("arm") is None:
        return _run_local(*args, **kwargs)
    directory = kwargs.get("artifact_dir")
    if directory is not None:
        return _run_independent_arm(args, kwargs, directory)
    with tempfile.TemporaryDirectory(prefix="enwiki9-arm-") as temporary:
        result = _run_independent_arm(args, kwargs, pathlib.Path(temporary) / "arm")
        result.pop("artifacts", None)
        return result


def _verify_arm_artifacts(directory: pathlib.Path, result: dict) -> list[str]:
    failures = []
    expected = (json.dumps(result, indent=2) + "\n").encode()
    result_path = directory / "result.json"
    try:
        if result_path.is_symlink() or result_path.read_bytes() != expected:
            failures.append("result.json differs from the closed arm result")
    except OSError as exc:
        failures.append(f"result.json: {exc}")
    for name, binding in result.get("artifacts", {}).items():
        path = directory / binding["path"]
        try:
            if (path.is_symlink() or path.resolve().parent != directory.resolve()
                    or path.stat().st_size != binding["bytes"] or _sha256_file(path) != binding["sha256"]):
                failures.append(f"{name}: retained artifact binding changed")
        except OSError as exc:
            failures.append(f"{name}: {exc}")
    return failures



def compare(program_id: str, data_path: pathlib.Path, limit: int, specification: dict,
            output: pathlib.Path, *, mode: str = "discovery", record_ledger: bool = False) -> dict:
    """Run all frozen arms from one build in fresh processes; close artifacts before decision.

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
    source = _candidate_program_dir(program_id) / "program.py"
    if not source.is_file():
        raise ValueError("candidate source is missing")
    metadata = _load_program_metadata(program_id)
    package_inventory_before = _program_package_inventory(source.parent, metadata)
    inventory_before = package_inventory_before[1]["counted_files"]
    implementation_paths = _comparison_source_closure(source)
    implementation_before = {str(path): _sha256_file(path) for path in implementation_paths}
    output.mkdir(parents=True, exist_ok=False)
    build = _freeze_comparison_build(program_id, source, output,
                                    inventory=package_inventory_before,
                                    source_hashes=implementation_before)
    specification_payload = (json.dumps(specification, indent=2) + "\n").encode()
    _write_atomic(output / "specification.json", specification_payload)
    rows = {}
    errors = {}
    for role, arm in arms.items():
        try:
            rows[role] = run(program_id, data_path, limit, True, run_purpose="control" if role != "treatment" else "candidate",
                             arm=arm, artifact_dir=output / arm, mode=mode, frozen_build=build)
            if rows[role].get("failed_phase"):
                errors[role] = {"phase": rows[role]["failed_phase"], **rows[role]["failure"]}
        except Exception as exc:
            errors[role] = {"type": type(exc).__name__, "message": str(exc)}
    try:
        source_stable = (inventory_before == _program_package_inventory(source.parent, metadata)[1]["counted_files"]
                         and implementation_before == {str(path): _sha256_file(path) for path in implementation_paths})
    except OSError as exc:
        source_stable = False
        errors["source"] = {"type": type(exc).__name__, "message": str(exc)}
    artifact_errors = {role: failures for role, row in rows.items()
                       if (failures := _verify_arm_artifacts(output / arms[role], row))}
    build_errors = _verify_frozen_build(build)
    if build_errors:
        artifact_errors["build"] = build_errors
    loaded_build_complete = len(rows) == len(arms) and all(
        all(phase in row.get("phase_execution", {})
            and row["phase_execution"][phase].get("build_manifest_sha256") == build["sha256"]
            and build["source"].relative_to(build["root"]).as_posix()
                in row["phase_execution"][phase].get("loaded_sources", {})
            for phase in ("encode", "decode", "repeat"))
        for row in rows.values()
    )
    specification_stable = (output / "specification.json").read_bytes() == specification_payload
    if not specification_stable:
        artifact_errors["specification"] = ["frozen specification changed during comparison"]
    population_stable = bool(rows) and len({(r["data_size"], r["data_sha256"]) for r in rows.values()}) == 1
    exact = not errors and not artifact_errors and loaded_build_complete and population_stable and all(r["roundtrip_ok"] is True and r["determinism"]["single_host_byte_equal"] is True for r in rows.values())
    identity = bool(exact and rows["parent"]["compressed_sha256"] == rows["bookkeeping"]["compressed_sha256"])
    treatment_bytes = rows.get("treatment", {}).get("compressed_size")
    parent_bytes = rows.get("parent", {}).get("compressed_size")
    delta = treatment_bytes - parent_bytes if isinstance(treatment_bytes, int) and isinstance(parent_bytes, int) else None
    decision = {
        "schema": "gamma.enwiki9.driver-comparison.v1", "objective": research_contracts.objective_binding(),
        "program_id": program_id, "specification_sha256": hashlib.sha256(specification_payload).hexdigest(),
        "source_files": inventory_before, "driver_sha256": _sha256_file(pathlib.Path(__file__)),
        "implementation_files": {str(pathlib.Path(path).relative_to(ROOT)) if pathlib.Path(path).is_relative_to(ROOT) else path: digest
                                 for path, digest in implementation_before.items()},
        "source_stable": source_stable, "same_candidate_build": source_stable and loaded_build_complete and not build_errors,
        "same_candidate_build_scope": "retained candidate files and loaded local Python source closure",
        "frozen_build": {"manifest": "build.json", "sha256": build["sha256"],
                         "source_policy": build["manifest"]["source_policy"]},
        "same_input_population": population_stable,
        "artifact_closure_valid": not artifact_errors, "artifact_validation_errors": artifact_errors,
        "codec_process_state": "fresh-process-per-arm-encode-decode-repeat",
        "exact_roundtrips_and_repeats": exact, "parent_bookkeeping_identity": identity,
        "treatment_minus_parent_bytes": delta, "execution_mode": mode, "timing_authority": "diagnostic",
        "qualification_complete": False, "promotion_authorized": False, "objective_credit": 0,
        "arms": {role: {"arm": arms[role], "result": f"{arms[role]}/result.json", "result_sha256": hashlib.sha256((json.dumps(rows[role], indent=2) + "\n").encode()).hexdigest()} for role in rows},
        "errors": errors,
        "verdict": "invalid" if not (exact and identity and source_stable) else "measured-improvement" if delta < 0 else "measured-no-improvement",
    }
    if record_ledger:
        for role, row in rows.items():
            if row.get("failed_phase") or role in artifact_errors:
                continue
            result_path = output / arms[role] / "result.json"
            _append_run_ledger(_build_run_ledger_row(row, result_path, row.get("program_name"), False))
    _write_atomic(output / "decision.json", (json.dumps(decision, indent=2) + "\n").encode())
    return decision


def main() -> int:
    if sys.argv[1:2] == ["--_codec-phase"]:
        return _codec_phase_worker(sys.argv[2:])
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
