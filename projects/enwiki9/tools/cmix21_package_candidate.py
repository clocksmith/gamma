#!/usr/bin/env python3
"""Build and package a score-counted cmix21 mmap candidate.

The cmix21 Hutter experiments are sensitive to small compile-time memory
divisors.  This helper keeps each generated program directory reproducible:
it records the exact build flags, payload sizes, and payload hashes in
meta.json while reusing the parent dictionary payload.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAMS = ROOT / "programs"
SOURCE = ROOT / "external" / "cmix21-sidecar"

PROGRAM_TEMPLATE = '''"""Score-honest wrapper around disk-backed cmix version 21 text mode.

The counted binary is built from the vendored cmix21 source with a file-backed
allocator for large adaptive tables. Compression uses cmix forced text mode;
decompression uses the normal dictionary-aware decode path.
"""

from __future__ import annotations

import gzip
import os
import pathlib
import stat
import subprocess
import tempfile

_DIR = pathlib.Path(__file__).resolve().parent
_BIN_GZ = _DIR / "cmix.bin.gz"
_DICT_GZ = _DIR / "english.dic.gz"
_extracted_bin: pathlib.Path | None = None
_extracted_dict: pathlib.Path | None = None


def _extract(src: pathlib.Path, prefix: str, executable: bool) -> pathlib.Path:
    fd, path = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    out = pathlib.Path(path)
    with gzip.open(src, "rb") as inp:
        out.write_bytes(inp.read())
    if executable:
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return out


def _binary() -> pathlib.Path:
    global _extracted_bin
    if _extracted_bin is None or not _extracted_bin.exists():
        _extracted_bin = _extract(_BIN_GZ, "cmix21-mmap-bin-", True)
    return _extracted_bin


def _dictionary() -> pathlib.Path:
    global _extracted_dict
    if _extracted_dict is None or not _extracted_dict.exists():
        _extracted_dict = _extract(_DICT_GZ, "cmix21-mmap-dict-", False)
    return _extracted_dict


def _run(args: list[str], data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        env = os.environ.copy()
        env.setdefault("CMIX_MMAP_ALLOC", "1")
        env.setdefault("CMIX_MMAP_DIR", td)
        subprocess.run(
            [str(_binary()), *args, str(_dictionary()), src, dst],
            cwd=td,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


def compress(data: bytes) -> bytes:
    return _run(["-t"], data)


def decompress(data: bytes) -> bytes:
    return _run(["-d"], data)
'''


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def gzip_file(src: pathlib.Path, dst: pathlib.Path) -> None:
    with src.open("rb") as inp, dst.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as out:
            shutil.copyfileobj(inp, out)


def parse_define(raw: str) -> str:
    if not raw.startswith("-D"):
        raw = "-D" + raw
    if "=" not in raw:
        raise argparse.ArgumentTypeError("defines must use NAME=VALUE form")
    return raw


def payload_manifest(program_dir: pathlib.Path) -> tuple[dict[str, int], dict[str, str]]:
    sizes: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for name in ("cmix.bin.gz", "english.dic.gz", "program.py"):
        path = program_dir / name
        sizes[name] = path.stat().st_size
        hashes[name] = sha256(path)
    return sizes, hashes


def build_cmix(cxx: str, cxxflags: list[str], defines: list[str]) -> str:
    subprocess.run(["make", "-C", str(SOURCE), "clean"], check=True)
    lflags = ["-std=c++14", "-Wall", *cxxflags, *defines]
    cmd = ["make", "-C", str(SOURCE), f"CXX={cxx}", "LFLAGS=" + " ".join(lflags), "cmix"]
    subprocess.run(cmd, check=True)
    return f"{cxx} {' '.join(lflags)}"


def base_pgsg(ppmd_mb: int | None, defines: list[str]) -> dict[str, Any]:
    parsed: dict[str, str] = {}
    for item in defines:
        name, value = item[2:].split("=", 1)
        parsed[name] = value
    return {
        "nodes": [
            {
                "id": "cmix21_text",
                "type": "codec",
                "payload": {"discrete": {"mode": "forced_text", "codec": "cmix21"}},
            },
            {
                "id": "compile_defines",
                "type": "memory_policy",
                "payload": {"discrete": parsed},
            },
            {
                "id": "mmap_allocator",
                "type": "memory_policy",
                "payload": {"discrete": {"mode": "file_backed_large_tables"}},
            },
        ],
        "edges": [
            {"from": "compile_defines", "to": "cmix21_text", "stream": "memory_shape"},
            {"from": "mmap_allocator", "to": "cmix21_text", "stream": "state_storage"},
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--hypothesis", required=True)
    ap.add_argument("--status", default="candidate")
    ap.add_argument("--cxx", default="g++")
    ap.add_argument("--cxxflag", action="append", default=["-O3"])
    ap.add_argument("--define", action="append", type=parse_define, default=[])
    ap.add_argument("--dictionary-from", default=None)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    program_dir = PROGRAMS / args.id
    if program_dir.exists() and not args.overwrite:
        raise SystemExit(f"candidate already exists: {program_dir}")
    program_dir.mkdir(parents=True, exist_ok=True)

    parent_dir = PROGRAMS / (args.dictionary_from or args.parent)
    parent_dict = parent_dir / "english.dic.gz"
    if not parent_dict.exists():
        raise SystemExit(f"parent dictionary missing: {parent_dict}")

    build_summary = build_cmix(args.cxx, args.cxxflag, args.define)
    gzip_file(SOURCE / "cmix", program_dir / "cmix.bin.gz")
    shutil.copy2(parent_dict, program_dir / "english.dic.gz")
    (program_dir / "program.py").write_text(PROGRAM_TEMPLATE)

    sizes, hashes = payload_manifest(program_dir)
    program_size = sum(sizes.values())
    ppmd_mb = None
    for define in args.define:
        if define.startswith("-DCMIX_PPMD_MEMORY_MB="):
            ppmd_mb = int(define.split("=", 1)[1])

    meta = {
        "id": args.id,
        "family": "cmix21_mmap",
        "status": args.status,
        "description": args.description,
        "parent": args.parent,
        "hypothesis": args.hypothesis,
        "deps": [
            "C++ runtime for the vendored cmix binary",
            "POSIX mmap and temporary filesystem space",
        ],
        "source": {
            "tree": "projects/enwiki9/external/cmix21-sidecar",
            "binary": f"projects/enwiki9/programs/{args.id}/cmix.bin.gz",
            "dictionary": f"projects/enwiki9/programs/{args.id}/english.dic.gz",
            "build": build_summary,
            "defines": args.define,
        },
        "build": {
            "payload_files": sizes,
            "program_size": program_size,
            "payload_sha256": hashes,
        },
        "pgsg": base_pgsg(ppmd_mb, args.define),
        "measured": {},
        "verdict": "Unmeasured cmix21 memory-shaping candidate.",
    }
    (program_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({"candidate": args.id, "program_size": program_size}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
