#!/usr/bin/env python3
"""Remove C/C++ comments without changing tokens or source line numbers."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


CPP_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}


def _raw_literal_end(source: str, start: int) -> int | None:
    """Return the offset after a raw string beginning at ``R\"``, if valid."""

    if not source.startswith('R"', start):
        return None
    delimiter_end = source.find("(", start + 2, start + 19)
    if delimiter_end < 0:
        return None
    delimiter = source[start + 2 : delimiter_end]
    if any(char.isspace() or char in "()\\" for char in delimiter):
        return None
    terminator = ")" + delimiter + '"'
    literal_end = source.find(terminator, delimiter_end + 1)
    return None if literal_end < 0 else literal_end + len(terminator)


def strip_comments(source: str) -> str:
    """Strip comments while preserving literals, token separation, and newlines."""

    output: list[str] = []
    index = 0
    size = len(source)
    while index < size:
        char = source[index]

        raw_end = _raw_literal_end(source, index)
        if raw_end is not None:
            output.append(source[index:raw_end])
            index = raw_end
            continue

        if char in {'"', "'"}:
            quote = char
            literal_start = index
            index += 1
            while index < size:
                if source[index] == "\\":
                    index = min(size, index + 2)
                elif source[index] == quote:
                    index += 1
                    break
                else:
                    index += 1
            output.append(source[literal_start:index])
            continue

        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            if newline < 0:
                break
            output.append("\n")
            index = newline + 1
            continue

        if source.startswith("/*", index):
            comment_end = source.find("*/", index + 2)
            if comment_end < 0:
                raise ValueError("unterminated block comment")
            comment = source[index : comment_end + 2]
            output.append(" " + "\n" * comment.count("\n"))
            index = comment_end + 2
            continue

        output.append(char)
        index += 1

    result = "".join(output)
    if result.count("\n") != source.count("\n"):
        raise AssertionError("comment stripping changed source line count")
    return result


def source_names(path: Path) -> list[str]:
    names = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not names or len(names) != len(set(names)):
        raise ValueError("source list must be nonempty and unique")
    for name in names:
        candidate = Path(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"unsafe source path: {name}")
    return names


def minify_tree(root: Path, file_list: Path, output_root: Path) -> dict[str, int]:
    names = source_names(file_list)
    before = 0
    after = 0
    transformed = 0
    for name in names:
        source_path = root / name
        output_path = output_root / name
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        before += source_path.stat().st_size
        if source_path.suffix.lower() in CPP_SUFFIXES:
            source = source_path.read_text()
            output_path.write_text(strip_comments(source))
            transformed += 1
        else:
            shutil.copyfile(source_path, output_path)
        after += output_path.stat().st_size
    return {
        "files": len(names),
        "transformed_files": transformed,
        "source_bytes_before": before,
        "source_bytes_after": after,
        "source_bytes_removed": before - after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--file-list", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = minify_tree(args.root, args.file_list, args.output_root)
    print(" ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
