#!/usr/bin/env python3
"""Build a deterministic direct-entry ZIP from a source tree and file list."""

from __future__ import annotations

import argparse
import pathlib
import zipfile


METHODS = {
    "bzip2": zipfile.ZIP_BZIP2,
    "deflate": zipfile.ZIP_DEFLATED,
    "lzma": zipfile.ZIP_LZMA,
    "store": zipfile.ZIP_STORED,
}


def source_names(path: pathlib.Path) -> list[str]:
    names = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(names) != len(set(names)):
        raise ValueError("file list contains duplicate names")
    for name in names:
        candidate = pathlib.PurePosixPath(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"unsafe source path: {name}")
    return names


def build_zip(
    root: pathlib.Path,
    names: list[str],
    output: pathlib.Path,
    method: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        "w",
        compression=method,
        compresslevel=9 if method in {zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2} else None,
        strict_timestamps=True,
    ) as archive:
        for name in names:
            path = root / pathlib.PurePosixPath(name)
            if not path.is_file():
                raise FileNotFoundError(path)
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = method
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--file-list", type=pathlib.Path, required=True)
    parser.add_argument("--method", choices=sorted(METHODS), required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    build_zip(args.root, source_names(args.file_list), args.output, METHODS[args.method])
    with zipfile.ZipFile(args.output) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"ZIP integrity failure at {bad}")
    print(f"source_zip={args.output} bytes={args.output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
