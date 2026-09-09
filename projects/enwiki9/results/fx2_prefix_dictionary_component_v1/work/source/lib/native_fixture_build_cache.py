"""Content-addressed, bounded local GCC-compatible C++ fixture builds.

This is build reuse, not a package, scientific result, or resource certificate.
Every request reruns compiler dependency discovery (including system headers and
included .cpp files), hashes the resulting contents, and verifies a cache hit's
binary. A per-identity POSIX flock excludes duplicate builds; publication uses
an atomic directory rename. Corrupt entries are preserved under ``quarantine``.

Only the documented compile flags below are accepted: no response files,
arbitrary linker inputs, plugins, output redirection, or ambient compiler flags.
The environment is sanitized, temporal preprocessor macros are rejected, and
native CPU autodetection flags are unsupported. Toolchain files are bound, but
this is not a hermetic toolchain or runtime-library package. Inputs must not be
edited during a request; a second dependency/content scan detects ordinary
concurrent edits and fails closed rather than publishing a mismatched entry.

Linux/POSIX, GCC-compatible dependency output, and the existing ``prlimit``
utility are required. No dependency installation, cache eviction, or corpus
execution is performed. Callers own and may separately clean their cache.
"""

from __future__ import annotations

import contextlib
import dataclasses
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from typing import Iterator, Sequence
import uuid


SCHEMA = "gamma.native_fixture_build_cache.v1"
MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_INPUT_BYTES = 512 * 1024 * 1024
MAX_DEPENDENCIES = 8192
MAX_TOOL_OUTPUT_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
ADDRESS_SPACE_BYTES = 2 * 1024 * 1024 * 1024
BUILD_ENVIRONMENT = {
    "PATH": os.defpath,
    "LANG": "C",
    "LC_ALL": "C",
    "SOURCE_DATE_EPOCH": "0",
}


class BuildCacheError(RuntimeError):
    """A bounded build or cache-integrity precondition failed."""


class BuildCacheTimeout(BuildCacheError):
    """The request exhausted its explicit elapsed stop."""


@dataclasses.dataclass(frozen=True)
class CachedCppBuild:
    binary: Path
    cache_hit: bool
    cache_reason: str
    manifest: dict


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_record(path: Path, *, limit: int = MAX_FILE_BYTES) -> dict:
    path = path.resolve(strict=True)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise BuildCacheError(f"Not a bounded regular input file: {path}")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise BuildCacheError(f"Input exceeds byte ceiling: {path}")
            digest.update(chunk)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ) or size != before.st_size:
        raise BuildCacheError(f"Input changed while hashing: {path}")
    return {"path": str(path), "sha256": digest.hexdigest(), "bytes": size}


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise BuildCacheTimeout("Native build request elapsed stop reached")
    return remaining


def _inherited_ceiling(kind: int, requested: int) -> int:
    """Never raise a caller's soft or hard resource limit."""
    return min([requested, *(value for value in resource.getrlimit(kind) if value != resource.RLIM_INFINITY)])


def _run(command: Sequence[str], *, cwd: Path, deadline: float, prlimit: str) -> str:
    remaining = _remaining(deadline)
    bounded = [
        prlimit,
        f"--as={_inherited_ceiling(resource.RLIMIT_AS, ADDRESS_SPACE_BYTES)}",
        f"--cpu={_inherited_ceiling(resource.RLIMIT_CPU, max(1, math.ceil(remaining)))}",
        f"--fsize={_inherited_ceiling(resource.RLIMIT_FSIZE, MAX_FILE_BYTES)}",
        f"--core={_inherited_ceiling(resource.RLIMIT_CORE, 0)}",
        "--",
        *command,
    ]
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            bounded, cwd=cwd, env=BUILD_ENVIRONMENT.copy(), stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            # The driver may have cc1plus/as/ld children; stop the whole owned group.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise BuildCacheTimeout("Native build subprocess elapsed stop reached") from error
        output.seek(0)
        raw = output.read(MAX_TOOL_OUTPUT_BYTES + 1)
        if len(raw) > MAX_TOOL_OUTPUT_BYTES:
            raise BuildCacheError("Compiler diagnostic output exceeds byte ceiling")
        text = raw.decode("utf-8", errors="replace")
        if returncode != 0:
            raise BuildCacheError(f"Compiler command failed ({returncode}): {text.rstrip()}")
        _remaining(deadline)
        return text.strip()


def _validated_flags(flags: Sequence[str]) -> list[str]:
    if isinstance(flags, (str, bytes)) or len(flags) > 128:
        raise ValueError("flags must be a bounded sequence of compiler arguments")
    result = list(flags)
    paired = {"-I", "-iquote", "-isystem", "-include", "-D", "-U"}
    exact = {
        "-pthread", "-fno-fast-math", "-ffast-math", "-fno-omit-frame-pointer",
        "-fomit-frame-pointer", "-fno-exceptions", "-fno-rtti", "-fPIC", "-fPIE",
        "-mavx", "-mavx2", "-mfma", "-msse2", "-msse4.1", "-msse4.2",
        "-mno-avx", "-mno-avx2", "-mno-fma", "-mtune=generic",
    }
    index = 0
    while index < len(result):
        flag = result[index]
        if not isinstance(flag, str) or not flag or any(c in flag for c in "\x00\n\r"):
            raise ValueError("Compiler arguments must be nonempty single-line strings")
        if flag in paired:
            index += 1
            if index == len(result) or not isinstance(result[index], str) or not result[index] or (
                result[index].startswith("-") or any(c in result[index] for c in "\x00\n\r")
            ):
                raise ValueError(f"Missing or invalid argument for {flag}")
        elif flag in exact or re.fullmatch(
            r"(?:-std=(?:c\+\+|gnu\+\+)(?:11|14|17|20|23|26)|-O[0-3gsz]|-g[0-3]?|"
            r"-W(?:no-)?[A-Za-z][A-Za-z0-9_=\-]*|-ffp-contract=(?:off|on|fast)|"
            r"-march=x86-64(?:-v[234])?|-fsanitize=(?:address|undefined)(?:,(?:address|undefined))?)",
            flag,
        ):
            pass
        elif flag.startswith(("-I", "-D", "-U")) and len(flag) > 2:
            pass
        else:
            raise ValueError(f"Unsupported fixture compiler flag: {flag}")
        index += 1
    # __TIMESTAMP__ otherwise depends on mtimes rather than bound contents.
    return [*result, "-Werror=date-time"]


def _compiler_identity(compiler: str, *, cwd: Path, deadline: float, prlimit: str) -> dict:
    executable = shutil.which(compiler)
    if not executable:
        raise BuildCacheError(f"Compiler not found: {compiler}")
    # Preserve the invocation name: clang++ and clang may be the same inode.
    invocation = str(Path(executable).absolute())
    run = lambda *args: _run([invocation, *args], cwd=cwd, deadline=deadline, prlimit=prlimit)
    identity = {
        "invocation": invocation,
        "executable": _file_record(Path(invocation)),
        "version": run("--version"),
        "target": run("-dumpmachine"),
        "toolchain_files": [],
    }
    seen = {identity["executable"]["path"]}
    queries = [("-print-prog-name=", name) for name in ("cc1plus", "as", "ld")]
    queries += [("-print-file-name=", name) for name in (
        "Scrt1.o", "crti.o", "crtbeginS.o", "crtendS.o", "crtn.o", "libstdc++.so",
        "libgcc.a", "libgcc_s.so", "libgcc_s.so.1", "libc.so", "libc.so.6",
        "libc_nonshared.a", "libm.so", "libm.so.6", "libasan.so", "libubsan.so",
    )]
    for option, name in queries:
        reported = run(option + name)
        candidate = Path(reported)
        if not candidate.is_absolute():
            located = shutil.which(reported, path=BUILD_ENVIRONMENT["PATH"])
            if located:
                candidate = Path(located)
            elif (cwd / candidate).is_file():
                candidate = cwd / candidate
            else:
                # Optional runtime libraries are not installed on every host.
                identity["toolchain_files"].append({"query": name, "unresolved": reported})
                continue
        record = _file_record(candidate)
        if record["path"] not in seen:
            identity["toolchain_files"].append({"query": name, **record})
            seen.add(record["path"])
    return identity


def _make_dependencies(text: str) -> list[str]:
    """Read one GCC -M rule, including escaped whitespace, #, backslash and $."""
    text = text.replace("\\\n", "")
    marker = "native_fixture_cache:"
    if not text.startswith(marker):
        raise BuildCacheError("Unexpected compiler dependency rule")
    text = text[len(marker):]
    words: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            end = index
            while end < len(text) and text[end] == "\\":
                end += 1
            count = end - index
            if end < len(text) and text[end] in " \t":
                # GCC doubles existing backslashes before escaping whitespace.
                current.extend("\\" * (count // 2))
                if count % 2:
                    current.append(text[end])
                    index = end
                else:
                    index = end - 1
            elif end < len(text) and text[end] == "#":
                current.extend("\\" * (count - 1))
                current.append("#")
                index = end
            else:
                # Ordinary filename backslashes are literal in GCC -M output.
                current.extend("\\" * count)
                index = end - 1
        elif char == "$" and index + 1 < len(text) and text[index + 1] == "$":
            current.append("$")
            index += 1
        elif char.isspace():
            if current:
                words.append("".join(current))
                current = []
        else:
            current.append(char)
        index += 1
    if current:
        words.append("".join(current))
    if not words or len(words) > MAX_DEPENDENCIES:
        raise BuildCacheError("Empty or oversized compiler dependency set")
    return words


def _dependencies(sources: list[Path], flags: list[str], compiler: str, *, cwd: Path,
                  scratch: Path, deadline: float, prlimit: str) -> list[dict]:
    paths = set(sources)
    for index, source in enumerate(sources):
        depfile = scratch / f"dependencies-{index}.mk"
        _run([compiler, *flags, "-M", "-MT", "native_fixture_cache", "-MF", str(depfile), str(source)],
             cwd=cwd, deadline=deadline, prlimit=prlimit)
        if depfile.stat().st_size > MAX_TOOL_OUTPUT_BYTES:
            raise BuildCacheError("Compiler dependency output exceeds byte ceiling")
        for name in _make_dependencies(depfile.read_text()):
            path = Path(name)
            paths.add((path if path.is_absolute() else cwd / path).resolve(strict=True))
        if len(paths) > MAX_DEPENDENCIES:
            raise BuildCacheError("Dependency count exceeds ceiling")
    records = []
    total = 0
    for path in sorted(paths):
        _remaining(deadline)
        if path.with_name(path.name + ".gch").exists():
            raise BuildCacheError(f"Implicit precompiled headers are unsupported: {path}")
        record = _file_record(path)
        total += record["bytes"]
        if total > MAX_INPUT_BYTES:
            raise BuildCacheError("Dependency bytes exceed ceiling")
        records.append(record)
    return records


@contextlib.contextmanager
def _lock(path: Path, deadline: float) -> Iterator[None]:
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        while True:
            _remaining(deadline)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(min(0.025, _remaining(deadline)))
        yield
    finally:
        os.close(descriptor)


def _cached(entry: Path, identity: dict, key: str) -> tuple[dict | None, str]:
    if not entry.exists() and not entry.is_symlink():
        return None, "absent"
    if entry.is_symlink() or not entry.is_dir():
        return None, "invalid_entry"
    manifest_path = entry / "manifest.json"
    binary = entry / "program"
    try:
        if manifest_path.is_symlink() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            return None, "invalid_manifest"
        manifest = json.loads(manifest_path.read_text())
        if not isinstance(manifest, dict) or set(manifest) != {
            "schema", "key", "identity", "binary", "bounds", "manifest_sha256"
        }:
            return None, "invalid_manifest"
        if manifest["schema"] != SCHEMA or manifest["key"] != key or manifest["identity"] != identity:
            return None, "manifest_identity_mismatch"
        bounds = manifest["bounds"]
        if not isinstance(bounds, dict) or set(bounds) != {
            "address_space_bytes", "per_file_bytes", "request_elapsed_stop_seconds", "cpu_seconds_per_process_ceiling"
        } or any(type(bounds[field]) is not int or not 1 <= bounds[field] <= ceiling for field, ceiling in (
            ("address_space_bytes", ADDRESS_SPACE_BYTES), ("per_file_bytes", MAX_FILE_BYTES),
            ("cpu_seconds_per_process_ceiling", 3600)
        )) or (
            type(bounds["request_elapsed_stop_seconds"]) is not int
            or not 1 <= bounds["request_elapsed_stop_seconds"] <= 3600
        ):
            return None, "invalid_manifest_bounds"
        if manifest["manifest_sha256"] != _sha256(_json_bytes(
            {field: value for field, value in manifest.items() if field != "manifest_sha256"}
        )):
            return None, "manifest_digest_mismatch"
        if binary.is_symlink() or not binary.is_file() or not os.access(binary, os.X_OK):
            return None, "invalid_binary"
        record = _file_record(binary)
        if manifest["binary"] != {"sha256": record["sha256"], "bytes": record["bytes"]}:
            return None, "binary_digest_mismatch"
        return manifest, "verified"
    except (OSError, ValueError, BuildCacheError):
        return None, "invalid_manifest_or_binary"


def build_cpp_cached(*, sources: Sequence[Path], flags: Sequence[str], cache_dir: Path,
                     compiler: str = "g++", timeout_seconds: int = 120) -> CachedCppBuild:
    """Build/reuse one executable; the elapsed stop covers locks, scans and build.

    ``sources`` are ordered C++ translation units. Relative includes/flags use
    the caller's working directory, which is part of the identity. Source and
    transitive dependency hashes are exposed in ``manifest['identity']``.
    A changed dependency creates a new key, never overwrites a previous build.
    Corruption produces ``cache_hit=False`` and a specific ``cache_reason``.

    Each compiler process receives a 2 GiB address-space ceiling, a 128 MiB
    per-file ceiling and a CPU stop rounded up from the remaining request stop.
    Stricter inherited soft/hard limits are preserved, never raised.
    These are implementation-test stops, not prize resource qualification.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 3600:
        raise ValueError("timeout_seconds must be an integer in [1, 3600]")
    if isinstance(sources, (str, bytes)) or not 1 <= len(sources) <= 128:
        raise ValueError("sources must contain 1 through 128 ordered C++ paths")
    source_paths = [Path(source).resolve(strict=True) for source in sources]
    if any(path.suffix not in {".cpp", ".cc", ".cxx", ".C"} for path in source_paths):
        raise ValueError("Only C++ source translation units are supported")
    if any(any(c in str(path) for c in "\x00\n\r") for path in source_paths):
        raise ValueError("Source paths must be single-line strings")
    effective_flags = _validated_flags(flags)
    prlimit = shutil.which("prlimit", path=BUILD_ENVIRONMENT["PATH"])
    if not prlimit:
        raise BuildCacheError("Existing prlimit utility is required for bounded builds")
    deadline = time.monotonic() + timeout_seconds
    bounds = {
        "address_space_bytes": _inherited_ceiling(resource.RLIMIT_AS, ADDRESS_SPACE_BYTES),
        "per_file_bytes": _inherited_ceiling(resource.RLIMIT_FSIZE, MAX_FILE_BYTES),
        "cpu_seconds_per_process_ceiling": _inherited_ceiling(resource.RLIMIT_CPU, timeout_seconds),
        "request_elapsed_stop_seconds": timeout_seconds,
    }
    if any(value <= 0 for value in bounds.values()):
        raise BuildCacheError("Inherited build resource ceiling is zero")
    cwd = Path.cwd().resolve()
    root = Path(cache_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("entries", "locks", "quarantine"):
        child = root / directory
        if child.is_symlink():
            raise BuildCacheError(f"Cache internal directory may not be a symlink: {child}")
        child.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".build-", dir=root) as temporary:
        scratch = Path(temporary)
        compiler_identity = _compiler_identity(compiler, cwd=cwd, deadline=deadline, prlimit=prlimit)
        invocation = compiler_identity["invocation"]
        identity = {
            "schema": SCHEMA,
            "compiler": compiler_identity,
            "environment": BUILD_ENVIRONMENT.copy(),
            "cwd": str(cwd),
            "flags": effective_flags,
            "sources": [str(path) for path in source_paths],
            "dependencies": _dependencies(source_paths, effective_flags, invocation, cwd=cwd,
                                          scratch=scratch, deadline=deadline, prlimit=prlimit),
        }
        key = _sha256(_json_bytes(identity))
        entry = root / "entries" / key
        with _lock(root / "locks" / f"{key}.lock", deadline):
            manifest, reason = _cached(entry, identity, key)
            if manifest is not None:
                after = _dependencies(source_paths, effective_flags, invocation, cwd=cwd,
                                      scratch=scratch, deadline=deadline, prlimit=prlimit)
                if after != identity["dependencies"] or _compiler_identity(
                    compiler, cwd=cwd, deadline=deadline, prlimit=prlimit
                ) != compiler_identity:
                    raise BuildCacheError("Source dependencies or compiler changed during cache verification")
                _remaining(deadline)
                return CachedCppBuild(entry / "program", True, reason, manifest)
            _run([invocation, *effective_flags, *map(str, source_paths), "-o", str(scratch / "program")],
                 cwd=cwd, deadline=deadline, prlimit=prlimit)
            after = _dependencies(source_paths, effective_flags, invocation, cwd=cwd,
                                  scratch=scratch, deadline=deadline, prlimit=prlimit)
            if after != identity["dependencies"] or _compiler_identity(
                compiler, cwd=cwd, deadline=deadline, prlimit=prlimit
            ) != compiler_identity:
                raise BuildCacheError("Source dependencies or compiler changed during build")
            binary = _file_record(scratch / "program")
            manifest = {
                "schema": SCHEMA, "key": key, "identity": identity,
                "binary": {"sha256": binary["sha256"], "bytes": binary["bytes"]},
                "bounds": bounds,
            }
            manifest["manifest_sha256"] = _sha256(_json_bytes(manifest))
            publication = scratch / "publish"
            publication.mkdir()
            os.replace(scratch / "program", publication / "program")
            (publication / "program").chmod(0o500)
            manifest_bytes = _json_bytes(manifest) + b"\n"
            if len(manifest_bytes) > MAX_MANIFEST_BYTES:
                raise BuildCacheError("Build manifest exceeds byte ceiling")
            with (publication / "manifest.json").open("xb") as output:
                output.write(manifest_bytes)
                output.flush()
                os.fsync(output.fileno())
            with (publication / "program").open("rb") as output:
                os.fsync(output.fileno())
            _remaining(deadline)
            if entry.exists() or entry.is_symlink():
                os.replace(entry, root / "quarantine" / f"{key}-{uuid.uuid4().hex}")
            os.replace(publication, entry)
            directory_fd = os.open(entry.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            return CachedCppBuild(entry / "program", False, reason, manifest)
