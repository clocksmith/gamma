#!/usr/bin/env python3
"""Expose the exact layer-19 FF1 matrix input without changing computation."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "0f6e42ef6ef5d26653c7147a3be023685bf46295c4d1ec0732bdbe5914b8ea65"
OLD_FILTER = """        name != \"layer_19_ff1_output.f32\" &&
        name != \"layer_19_geglu_output.f32\" &&
        name.find(\"_attention_input.f32\") == std::string::npos) return;
"""
NEW_FILTER = """        name != \"layer_19_ff1_output.f32\" &&
        name != \"layer_19_geglu_output.f32\" &&
        name != \"layer_19_ff1_input.f32\" &&
        name.find(\"_attention_input.f32\") == std::string::npos) return;
"""
OLD_BOUNDARY = """            const std::vector<float> feedforward_input = rms_norm(
                attention_residual, ln_g2, ln_b2);
            const std::vector<float> ff1 = fixture.parameter(
"""
NEW_BOUNDARY = """            const std::vector<float> feedforward_input = rms_norm(
                attention_residual, ln_g2, ln_b2);
            write_f32(output_dir / (layer_prefix + \"_ff1_input.f32\"),
                      feedforward_input);
            const std::vector<float> ff1 = fixture.parameter(
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
        raise ValueError("exact top-FF1 forward parent digest differs")
    source = args.parent.read_text()
    if source.count(OLD_FILTER) != 1 or source.count(OLD_BOUNDARY) != 1:
        raise ValueError("layer-19 FF1 input patch boundary is not unique")
    source = source.replace(OLD_FILTER, NEW_FILTER)
    source = source.replace(OLD_BOUNDARY, NEW_BOUNDARY)
    args.output.write_text(source)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

