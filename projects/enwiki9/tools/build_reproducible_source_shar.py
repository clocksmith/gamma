#!/usr/bin/env python3
"""Bundle a text-only source tree into one readable deterministic shell source."""

from __future__ import annotations

import argparse
import pathlib
import zipfile


PACKAGE_MAKEFILE = b""".PHONY: all clean

all: comp9a-decomp9

comp9a-decomp9: source_bundle.sh
\trm -rf build
\tsh source_bundle.sh build
\t$(MAKE) -C build
\tcp build/comp9a-decomp9 $@

clean:
\trm -rf build comp9a-decomp9 comp9a decomp9
"""
PACKAGE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def source_names(path: pathlib.Path) -> list[str]:
    names = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(names) != len(set(names)):
        raise ValueError("file list contains duplicate names")
    for name in names:
        candidate = pathlib.PurePosixPath(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"unsafe source path: {name}")
    return names


def delimiter(name: str, payload: bytes) -> str:
    lines = set(payload.splitlines())
    marker = "__ENWIKI9_SOURCE_EOF__"
    if marker.encode() not in lines:
        return marker
    for index in range(1, 1_000):
        candidate = f"__ENWIKI9_SOURCE_EOF_{index}__"
        if candidate.encode() not in lines:
            return candidate
    raise ValueError(f"could not find heredoc delimiter for {name}")


def build_shar(root: pathlib.Path, names: list[str], output: pathlib.Path) -> None:
    chunks = [b"#!/bin/sh\nset -eu\nroot=${1:-build}\nmkdir -p \"$root\"\n"]
    directories = sorted(
        {
            str(pathlib.PurePosixPath(name).parent)
            for name in names
            if str(pathlib.PurePosixPath(name).parent) != "."
        }
    )
    for directory in directories:
        chunks.append(f"mkdir -p \"$root/{directory}\"\n".encode())
    for name in names:
        payload = (root / pathlib.PurePosixPath(name)).read_bytes()
        if b"\0" in payload or not payload.endswith(b"\n"):
            raise ValueError(f"source bundle requires newline-terminated text: {name}")
        payload.decode("utf-8")
        marker = delimiter(name, payload)
        chunks.append(f"cat > \"$root/{name}\" <<'{marker}'\n".encode())
        chunks.append(payload)
        chunks.append(f"{marker}\n".encode())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(chunks))
    output.chmod(0o755)


def build_package(bundle: pathlib.Path, output: pathlib.Path) -> None:
    """Write the counted two-entry source package deterministically."""

    output.parent.mkdir(parents=True, exist_ok=True)
    entries = (
        ("Makefile", PACKAGE_MAKEFILE, 0o100644),
        ("source_bundle.sh", bundle.read_bytes(), 0o100755),
    )
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_BZIP2,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for name, payload, mode in entries:
            info = zipfile.ZipInfo(name, date_time=PACKAGE_TIMESTAMP)
            info.compress_type = zipfile.ZIP_BZIP2
            info.create_system = 3
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, payload)
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"ZIP integrity failure at {bad}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--file-list", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument(
        "--package-zip",
        type=pathlib.Path,
        help="optional deterministic ZIP containing Makefile and source bundle",
    )
    args = parser.parse_args()
    names = source_names(args.file_list)
    build_shar(args.root, names, args.output)
    print(f"source_shar={args.output} bytes={args.output.stat().st_size}")
    if args.package_zip is not None:
        build_package(args.output, args.package_zip)
        print(f"source_zip={args.package_zip} bytes={args.package_zip.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
