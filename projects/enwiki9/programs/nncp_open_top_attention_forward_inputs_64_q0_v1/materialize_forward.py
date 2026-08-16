#!/usr/bin/env python3
"""Expose exact layer-19 probability, value, and attended tensors."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "87bdeee848454db7fb071a43fb475a076569b57e5b770f34c242fe3f7869c4c1"
WRITE_OLD = """static void write_f32(const fs::path & path, const std::vector<float> & values) {
    ensure_finite(values, path.filename().string());
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(values.data()), values.size() * sizeof(float));
    if (!output) throw std::runtime_error(\"cannot write tensor: \" + path.string());
}
"""
WRITE_NEW = """static void write_f32(const fs::path & path, const std::vector<float> & values) {
    ensure_finite(values, path.filename().string());
    const std::string name = path.filename().string();
    if (name != \"layer_19_pre_w_o_input.f32\" &&
        name != \"layer_19_value_state.f32\" &&
        name != \"layer_19_attention_probability.f32\" &&
        name.find(\"_attention_input.f32\") == std::string::npos) return;
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char *>(values.data()), values.size() * sizeof(float));
    if (!output) throw std::runtime_error(\"cannot write tensor: \" + path.string());
}
"""
PRE_W_O_OLD = """                    }
            std::vector<float> attention_output = engine.multiply_libnc(
"""
PRE_W_O_NEW = """                    }
            if (layer == 19)
                write_f32(output_dir / \"layer_19_pre_w_o_input.f32\", merged_attention);
            std::vector<float> attention_output = engine.multiply_libnc(
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"top-attention {label} boundary is not unique")
    return source.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sha256(args.parent) != PARENT_SHA256:
        raise ValueError("promoted exact-forward source digest differs")
    source = args.parent.read_text()
    source = replace_once(source, WRITE_OLD, WRITE_NEW, "write")
    source = replace_once(source, PRE_W_O_OLD, PRE_W_O_NEW, "pre-w_o")
    args.output.write_text(source)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
