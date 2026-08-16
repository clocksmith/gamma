#!/usr/bin/env python3
"""Derive the sparse-output forward from the promoted exact source."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "87bdeee848454db7fb071a43fb475a076569b57e5b770f34c242fe3f7869c4c1"
OLD = """static void write_f32(const fs::path & path, const std::vector<float> & values) {
    ensure_finite(values, path.filename().string());
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(values.data()), values.size() * sizeof(float));
    if (!output) throw std::runtime_error(\"cannot write tensor: \" + path.string());
}
"""
NEW = """static void write_f32(const fs::path & path, const std::vector<float> & values) {
    ensure_finite(values, path.filename().string());
    const std::string name = path.filename().string();
    if (name != \"output.f32\" && name != \"final_hidden.f32\" &&
        name.find(\"_attention_input.f32\") == std::string::npos) return;
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(values.data()), values.size() * sizeof(float));
    if (!output) throw std::runtime_error(\"cannot write tensor: \" + path.string());
}
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sha256(args.parent) != PARENT_SHA256:
        raise ValueError("promoted exact-forward source digest differs")
    source = args.parent.read_text()
    if source.count(OLD) != 1:
        raise ValueError("exact-forward write boundary is not unique")
    materialized = source.replace(OLD, NEW)
    args.output.write_text(materialized)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
