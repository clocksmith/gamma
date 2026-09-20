#!/usr/bin/env python3
"""Optimized CRG2 driver: native prediction plus integrity-checked Python framing.

This is a corrected research implementation, NOT a Hutter Prize winner.
`auto` selects the smallest actually generated archive, including its header.
Selection does not turn a standard-library codec into a novel compressor.
Build the native payload engine explicitly: python crg_fast.py build
No corpus downloads, package installations, or Gamma job launches are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import crg_reference as ref

HERE = Path(__file__).resolve().parent
NATIVE = HERE / "crg_core"
ARM = {"parent": "P", "bookkeeping": "K", "independent": "I", "shared": "S", "wrong": "W"}
MAX_BYTES = 1_000_000_000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_checked(source: Path, target: Path, limit: int) -> tuple[int, bytes]:
    h = hashlib.sha256()
    n = 0
    with source.open("rb") as inp, target.open("xb") as out:
        before = os.fstat(inp.fileno())
        for chunk in iter(lambda: inp.read(1 << 20), b""):
            n += len(chunk)
            if n > limit:
                raise ValueError("input exceeds configured byte limit")
            out.write(chunk)
            h.update(chunk)
        after = os.fstat(inp.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("source changed during snapshot")
    return n, h.digest()


def run_native(arguments: list[str], timeout: float, binary: Path = NATIVE) -> dict:
    if not binary.is_file():
        raise ValueError("native engine absent; run: python crg_fast.py build")
    result = subprocess.run([str(binary), *arguments], check=True, capture_output=True,
                            text=True, timeout=timeout)
    return json.loads(result.stdout)


def publish(temp: Path, output: Path, force: bool) -> None:
    # All callers create the temporary file beside the output, on one filesystem.
    if force:
        os.replace(temp, output)
    else:
        os.link(temp, output)
        temp.unlink()


def check_paths(source: Path, output: Path, force: bool) -> None:
    if source.resolve() == output.resolve():
        raise ValueError("input and output must differ")
    if output.exists() and not force:
        raise FileExistsError(f"refusing overwrite: {output}")
    if not output.parent.is_dir():
        raise ValueError("output parent directory must already exist")


def encode(source: Path, output: Path, *, arm="parent", profile=1,
           backend="native", force=False, timeout=120.0,
           max_input=MAX_BYTES, binary=NATIVE) -> dict:
    source, output = Path(source), Path(output)
    check_paths(source, output, force)
    if arm not in ARM or profile not in (0, 1):
        raise ValueError("unsupported arm/profile")
    if backend in ref.BACKEND_ID:
        return ref.compress(source, output, backend=backend, force=force, time_limit=timeout)
    if backend not in ("native", "auto"):
        raise ValueError("unknown backend")
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=".crg-work-", dir=output.parent) as work:
        work = Path(work)
        n, raw_hash = copy_checked(source, work / "source", max_input)
        if backend == "auto":
            # Whole-file selection; only the selected mode and payload are stored.
            candidates = []
            for name in ("stored", "deflate", "lzma"):
                path = work / (name + ".crg")
                result = ref.compress(work / "source", path, backend=name, time_limit=timeout)
                candidates.append((path.stat().st_size, name, path, result))
            for a in ("parent",):
                path = work / ("native-" + a + ".crg")
                result = encode(work / "source", path, arm=a, profile=profile,
                                timeout=timeout, binary=binary)
                candidates.append((path.stat().st_size, "native-" + a, path, result))
            best = min(candidates, key=lambda row: (row[0], row[1]))
            result = dict(best[3])
            result.update(selection=[{"name": name, "archive_bytes": size} for size, name, _, _ in candidates],
                          selected_backend=best[1], selection_is_compression_gain=False,
                          total_elapsed_seconds=time.monotonic() - start)
            publish(best[2], output, force)
            return result
        payload = work / "payload"
        detail = run_native(["encode", str(work / "source"), str(payload), ARM[arm],
                             str(profile), str(max_input)], timeout, Path(binary))
        bits = detail["payload_bits"]
        size = payload.stat().st_size
        if detail["raw_bytes"] != n or size != (bits + 7) // 8 or size != detail["payload_bytes"]:
            raise ValueError("native output geometry mismatch")
        mode = ref.ARM_ID[arm] + (7 if profile else 0)
        result_path = work / "complete.crg"
        with result_path.open("xb") as out:
            out.write(ref.HEADER.pack(ref.MAGIC, ref.VERSION, mode, 0, n, bits, size,
                                      raw_hash, bytes.fromhex(digest(payload))))
            with payload.open("rb") as inp:
                shutil.copyfileobj(inp, out)
            out.flush()
            os.fsync(out.fileno())
        archive_hash = digest(result_path)
        publish(result_path, output, force)
        return {"operation": "encode", "backend": "native", "arm": arm, "profile": profile,
                "raw_bytes": n, "raw_sha256": raw_hash.hex(), "archive_bytes": ref.HEADER.size + size,
                "archive_sha256": archive_hash, "payload_bytes": size, "payload_bits": bits,
                "framing_bytes": ref.HEADER.size, "elapsed_seconds": time.monotonic() - start,
                "active_bits": detail["active_bits"], "mentions": detail["mentions"],
                "hutter_qualified": False, "complete_package_bytes": None}


def decode(source: Path, output: Path, *, force=False, timeout=120.0,
           max_output=MAX_BYTES, binary=NATIVE) -> dict:
    source, output = Path(source), Path(output)
    check_paths(source, output, force)
    start = time.monotonic()
    with source.open("rb") as inp:
        mode, n, bits, size, raw_hash = ref.read_header(inp, max_output)
        if mode in ref.BACKEND_ID.values():
            return ref.decompress(source, output, force=force, time_limit=timeout, max_output=max_output)
        with tempfile.TemporaryDirectory(prefix=".crg-work-", dir=output.parent) as work:
            work = Path(work)
            payload = work / "payload"
            with payload.open("xb") as out:
                shutil.copyfileobj(inp, out)
            detail = run_native(["decode", str(payload), str(work / "restored"), ARM[ref.ID_ARM[mode]],
                                 str(int(mode >= 7)), str(n), str(bits), str(max_output)], timeout, Path(binary))
            restored = work / "restored"
            if detail["raw_bytes"] != n or restored.stat().st_size != n or bytes.fromhex(digest(restored)) != raw_hash:
                raise ref.FormatError("independent native decode failed length/hash check")
            publish(restored, output, force)
    return {"operation": "decode", "raw_bytes": n, "raw_sha256": raw_hash.hex(),
            "archive_bytes": ref.HEADER.size + size, "elapsed_seconds": time.monotonic() - start,
            "hutter_qualified": False}


def build(compiler="g++", output=NATIVE, sanitize=False):
    flags = ["-std=c++17", "-O1" if sanitize else "-O3", "-Wall", "-Wextra", "-Werror"]
    if sanitize:
        flags += ["-fsanitize=undefined", "-fno-sanitize-recover=all"]
    command = [compiler, *flags, str(HERE / "crg_core.cpp"), "-o", str(output)]
    subprocess.run(command, check=True, timeout=90)
    return {"command": command, "binary_bytes": Path(output).stat().st_size,
            "binary_sha256": digest(Path(output)), "source_sha256": digest(HERE / "crg_core.cpp")}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build"); b.add_argument("--compiler", default="g++")
    b.add_argument("--sanitize", action="store_true")
    e = commands.add_parser("compress"); e.add_argument("input", type=Path); e.add_argument("output", type=Path)
    e.add_argument("--arm", choices=ref.ARMS, default="parent")
    e.add_argument("--profile", choices=(0, 1), type=int, default=1)
    e.add_argument("--backend", choices=("native", "deflate", "lzma", "stored", "auto"), default="auto")
    d = commands.add_parser("decompress"); d.add_argument("input", type=Path); d.add_argument("output", type=Path)
    d.add_argument("--max-output", type=int, default=MAX_BYTES)
    for sub in (e, d):
        sub.add_argument("--force", action="store_true")
        sub.add_argument("--timeout", type=float, default=120.0,
                         help="seconds per native subprocess/backend, not aggregate auto budget")
    args = p.parse_args(argv)
    try:
        if args.command == "build":
            result = build(args.compiler, sanitize=args.sanitize)
        elif args.command == "compress":
            if args.timeout <= 0:
                p.error("timeout must be positive")
            result = encode(args.input, args.output, arm=args.arm, profile=args.profile,
                            backend=args.backend, force=args.force, timeout=args.timeout)
        else:
            if args.timeout <= 0 or args.max_output < 0:
                p.error("invalid resource limit")
            result = decode(args.input, args.output, force=args.force,
                            timeout=args.timeout, max_output=args.max_output)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        p.exit(2, f"error: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
