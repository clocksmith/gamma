#!/usr/bin/env python3
"""Materialize and verify a relocatable source bundle for default open MIDAS.

No corpus launch, executable auto-run, complete-package credit or qualification.
Extraction requires a separately retained SHA-256 and never replaces a target.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import midas_open_codec_v1 as codec
from tools.build_reproducible_source_zip import build_zip

SCHEMA = "midas_open_source_bundle_v1"
MANIFEST = "SOURCE_MANIFEST.json"
LIMIT = 16 * 1024**2
MAX_FILES = 512


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("unsafe bundle path")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("unsafe bundle path")
    return name


def read_regular(path: Path, ceiling: int = LIMIT) -> bytes:
    # Avoid FIFO blocking; reject aliases and files changing during the read.
    path = Path(os.path.abspath(path))
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("bundle input path contains a symlink")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > ceiling:
            raise ValueError("bundle input is not a bounded regular file")
        data = handle.read(ceiling + 1)
        after = os.fstat(handle.fileno())
    signature = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns)
    if len(data) > ceiling or signature(before) != signature(after) or signature(after) != signature(path.lstat()):
        raise ValueError("bundle input changed while reading")
    return data


def manifest_for(files: dict[str, bytes]) -> dict:
    return {
        "schema": SCHEMA,
        "files": [{"path": name, "bytes": len(data), "sha256": digest(data)}
                  for name, data in sorted(files.items())],
        "project_directory": "projects/enwiki9",
        "build_entry": "projects/enwiki9/tools/midas_open_codec_v1.py",
        "backend": "unchanged default incremental; reference build not bundled",
        "build_flags": list(codec.FLAGS),
        "runtime_prerequisites": ["Linux/POSIX", "Python 3.11+ standard library",
                                  "GCC-compatible C++20 compiler and system headers",
                                  "AVX2/FMA CPU", "resolved ELF loader and libraries",
                                  "prlimit utility", "/usr/bin/ldd for inventory"],
        "trained_model_assets": [],
        "scope": "relocatable local source closure, not a hermetic toolchain or runtime package",
        "complete_package_bytes": None,
        "complete_package_qualified": False,
        "objective_credit_bytes": 0,
        "remaining_accounting": ["compiler/runtime/OS distribution and license closure",
                                  "accepted submission form and program/options accounting",
                                  "qualified composite resources and full-corpus inverse"],
    }


def collect(built) -> dict[str, bytes]:
    inventory = codec.inventory(built)  # Revalidates binary and every build dependency.
    gamma = ROOT.parent.parent
    files = {}

    def append(path: Path, expected: dict | None = None) -> None:
        name = safe_name(path.relative_to(gamma).as_posix())
        if name in files:
            raise ValueError("duplicate source closure path")
        if len(files) + 1 >= MAX_FILES:
            raise ValueError("source closure exceeds member bound")
        remaining = LIMIT - sum(map(len, files.values()))
        data = read_regular(path, remaining)
        if expected is not None and (len(data) != expected["bytes"] or digest(data) != expected["sha256"]):
            raise ValueError("source changed after inventory")
        files[name] = data

    for row in inventory["local_source_files"]:
        append(Path(row["path"]), row)
    for relative in ("tools/midas_open_source_bundle_v1.py", "tools/build_reproducible_source_zip.py",
                     "docs/midas_open_source_bundle_v1.md"):
        append(ROOT / relative)
    return files


def encode_bundle(files: dict[str, bytes]) -> bytes:
    if not files or len(files) >= MAX_FILES or MANIFEST in files:
        raise ValueError("invalid source member set")
    if sum(map(len, files.values())) > LIMIT:
        raise ValueError("source closure exceeds bundle bounds")
    manifest = manifest_for(files)
    members = {**files, MANIFEST: (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()}
    with tempfile.TemporaryDirectory(prefix="gamma-midas-source-pack-") as directory:
        root = Path(directory) / "source"
        root.mkdir()
        for name, data in members.items():
            safe_name(name)
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(data)
        archive = Path(directory) / "source.zip"
        build_zip(root, sorted(members), archive, zipfile.ZIP_DEFLATED)
        data = read_regular(archive)
    verify_bytes(data, digest(data))
    return data


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = value
    return result


def verify_bytes(data: bytes, expected_sha256: str) -> tuple[dict, dict[str, bytes]]:
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64
            or any(c not in "0123456789abcdef" for c in expected_sha256)):
        raise ValueError("expected SHA-256 must be 64 lowercase hex characters")
    if len(data) > LIMIT or digest(data) != expected_sha256:
        raise ValueError("bundle SHA-256 or size mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        names = [safe_name(info.filename) for info in infos]
        if (not infos or len(infos) > MAX_FILES or len(set(names)) != len(names)
                or names != sorted(names) or MANIFEST not in names or archive.comment):
            raise ValueError("invalid bundle member set")
        all_names = set(names)
        if any("/".join(name.split("/")[:end]) in all_names
               for name in names for end in range(1, len(name.split("/")))):
            raise ValueError("bundle file/directory prefix collision")
        if sum(info.file_size for info in infos) > LIMIT:
            raise ValueError("expanded bundle exceeds bound")
        members = {}
        for info in infos:
            if (info.is_dir() or info.compress_type != zipfile.ZIP_DEFLATED
                    or info.create_system != 3 or info.external_attr != 0o100644 << 16
                    or info.date_time != (1980, 1, 1, 0, 0, 0) or info.extra or info.comment
                    or info.flag_bits & 1):
                raise ValueError("noncanonical bundle member metadata")
            with archive.open(info) as handle:
                payload = handle.read(min(info.file_size, LIMIT) + 1)
            if len(payload) != info.file_size:
                raise ValueError("expanded member size mismatch")
            members[info.filename] = payload
    manifest_bytes = members.pop(MANIFEST)
    try:
        manifest = json.loads(manifest_bytes, object_pairs_hook=unique_json)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid source manifest") from error
    # Exact comparison binds every member and rejects unknown/missing metadata.
    if manifest != manifest_for(members):
        raise ValueError("source manifest or member digest mismatch")
    if manifest_bytes != (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode():
        raise ValueError("noncanonical manifest bytes")
    return manifest, members


def publish_file(output: Path, data: bytes) -> None:
    # Same-filesystem hard link gives exclusive publication, including symlinks.
    descriptor, temporary = tempfile.mkstemp(prefix=".midas-source-", dir=output.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def pack(built, output: Path) -> dict:
    data = encode_bundle(collect(built))
    publish_file(output, data)
    manifest, members = verify_bytes(data, digest(data))
    return {"schema": SCHEMA + "_receipt", "bundle_bytes": len(data), "bundle_sha256": digest(data),
            "source_files": len(members), "uncompressed_source_bytes": sum(map(len, members.values())),
            "manifest": manifest, "complete_package_bytes": None,
            "complete_package_qualified": False, "objective_credit_bytes": 0}


def extract(bundle: Path, output: Path, expected_sha256: str) -> dict:
    data = read_regular(bundle)
    manifest, members = verify_bytes(data, expected_sha256)
    members[MANIFEST] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    # No shell archive or extractall: only checked regular members are written.
    with tempfile.TemporaryDirectory(prefix=".midas-source-extract-", dir=output.parent) as directory:
        staging = Path(directory) / "source"
        staging.mkdir()
        for name, payload in members.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(payload)
            target.chmod(0o644)
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(staging), -100, os.fsencode(output), 1):
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(output))
    return {"bundle_sha256": expected_sha256, "extracted_files": len(members),
            "source_identity_verified": True, "code_executed": False,
            "complete_package_qualified": False, "objective_credit_bytes": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    command = sub.add_parser("pack")
    command.add_argument("--cache-dir", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    for name in ("verify", "extract"):
        command = sub.add_parser(name)
        command.add_argument("--bundle", type=Path, required=True)
        command.add_argument("--expected-sha256", required=True)
        if name == "extract":
            command.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "pack":
            result = pack(codec.build(args.cache_dir), args.output)
        elif args.action == "extract":
            result = extract(args.bundle, args.output_dir, args.expected_sha256)
        else:
            manifest, _ = verify_bytes(read_regular(args.bundle), args.expected_sha256)
            result = {"verified": True, "manifest": manifest, "code_executed": False}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, codec.BuildCacheError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
