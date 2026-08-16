#!/usr/bin/env python3
"""Materialize pre-FF residual conversion-order variants."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "3cc3e11f52fc976e7ac68a9e6d6c96fd274c37314ec9c6fecf7b8c541e0db187"
OLD_READERS = """std::vector<float> read_f32(const fs::path & path, std::size_t count) {
    const std::uintmax_t expected = count * sizeof(float);
    if (!fs::is_regular_file(path) || fs::file_size(path) != expected) {
        throw std::runtime_error("F32 tensor geometry differs: " + path.string());
    }
    std::vector<float> values(count);
    std::ifstream input(path, std::ios::binary);
    input.read(reinterpret_cast<char *>(values.data()),
               static_cast<std::streamsize>(expected));
    if (!input || !std::all_of(values.begin(), values.end(),
            [](float value) { return std::isfinite(value); })) {
        throw std::runtime_error("invalid F32 tensor: " + path.string());
    }
    return values;
}

std::vector<float> read_norm_inputs(const fs::path & root) {
    std::vector<float> result(kSamples * kWidth);
    for (std::size_t stream = 0; stream < kStreams; ++stream) {
        char name[32];
        std::snprintf(name, sizeof(name), "stream_%02zu", stream);
        const std::vector<float> current = read_f32(
            root / name / "layer_19_pre_ff_hidden.f32", kStates * kWidth);
        for (std::size_t state = 0; state < kStates; ++state) {
            const std::size_t sample = stream + kStreams * state;
            std::copy_n(current.data() + state * kWidth, kWidth,
                        result.data() + sample * kWidth);
        }
    }
    for (float value : result) {
        std::uint32_t bits;
        std::memcpy(&bits, &value, sizeof(bits));
        if ((bits & 0xffffU) != 0) {
            throw std::runtime_error("pre-FF normalization input is not BF16-exact");
        }
    }
    return result;
}
"""
NEW_READERS = """std::vector<float> read_norm_inputs(const fs::path & path) {
    return read_bf16(path, kSamples * kWidth);
}
"""
OLD_BRANCH_ROUND = """            destination[feature] = round_bf16(destination[feature]);
            result.input_bias_projection[feature] += destination[feature];
"""
NEW_BRANCH_ROUND = """            result.input_bias_projection[feature] +=
                round_bf16(destination[feature]);
"""
OLD_NAMESPACE_END = """
}  // namespace

int main(int argc, char ** argv) {
"""
NEW_NAMESPACE_END = """
std::vector<float> merge_preconverted_residuals(
    const std::vector<float> & normalized_branch,
    const std::vector<float> & direct_branch
) {
    if (normalized_branch.size() != direct_branch.size()) {
        throw std::runtime_error("preconverted residual geometry differs");
    }
    std::vector<float> result(normalized_branch.size());
    for (std::size_t index = 0; index < result.size(); ++index) {
        result[index] = round_bf16(
            round_bf16(normalized_branch[index]) + direct_branch[index]);
    }
    return result;
}

}  // namespace

int main(int argc, char ** argv) {
"""
OLD_MAIN = """        if (argc != 11) {
            throw std::runtime_error(
                "usage: pre_ff_backward PARAMETERS OPEN_ROOT NORM_ADJOINT "
                "DIRECT_ADJOINT OUT_LN_G OUT_LN_B OUT_NORM_INPUT "
                "OUT_TOTAL OUT_DIRECT_ONLY OUT_NEGATED_TOTAL");
        }
        const std::vector<float> gain = read_gain(argv[1]);
        const std::vector<float> norm_input = read_norm_inputs(argv[2]);
        const std::vector<float> incoming = read_bf16(
            argv[3], kSamples * kWidth);
        const std::vector<float> direct = read_bf16(
            argv[4], kSamples * kWidth);
        const BackwardResult observed = backward(norm_input, incoming, gain);
        std::vector<float> negated(incoming.size());
        std::transform(incoming.begin(), incoming.end(), negated.begin(),
                       [](float value) { return -value; });
        const BackwardResult control = backward(norm_input, negated, gain);
        const std::vector<float> total = merge_residuals(
            observed.input_residual, direct);
        const std::vector<float> control_total = merge_residuals(
            control.input_residual, direct);
        write_bf16(argv[5], observed.gain_gradient);
        write_bf16(argv[6], observed.bias_gradient);
        write_bf16(argv[7], observed.input_residual);
        write_bf16(argv[8], total);
        write_bf16(argv[9], direct);
        write_bf16(argv[10], control_total);
"""
NEW_MAIN = """        if (argc != 12) {
            throw std::runtime_error(
                "usage: conversion_probe PARAMETERS HIDDEN NORM_ADJOINT "
                "DIRECT_ADJOINT OUT_LN_G OUT_LN_B OUT_NORM_INPUT "
                "OUT_FUSED_TOTAL OUT_PRECONVERTED_TOTAL OUT_DIRECT_ONLY "
                "OUT_NEGATED_TOTAL");
        }
        const std::vector<float> gain = read_gain(argv[1]);
        const std::vector<float> norm_input = read_norm_inputs(argv[2]);
        const std::vector<float> incoming = read_bf16(
            argv[3], kSamples * kWidth);
        const std::vector<float> direct = read_bf16(
            argv[4], kSamples * kWidth);
        const BackwardResult observed = backward(norm_input, incoming, gain);
        std::vector<float> negated(incoming.size());
        std::transform(incoming.begin(), incoming.end(), negated.begin(),
                       [](float value) { return -value; });
        const BackwardResult control = backward(norm_input, negated, gain);
        const std::vector<float> fused_total = merge_residuals(
            observed.input_residual, direct);
        const std::vector<float> preconverted_total =
            merge_preconverted_residuals(observed.input_residual, direct);
        const std::vector<float> control_total = merge_residuals(
            control.input_residual, direct);
        write_bf16(argv[5], observed.gain_gradient);
        write_bf16(argv[6], observed.bias_gradient);
        write_bf16(argv[7], observed.input_residual);
        write_bf16(argv[8], fused_total);
        write_bf16(argv[9], preconverted_total);
        write_bf16(argv[10], direct);
        write_bf16(argv[11], control_total);
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"conversion-order {label} boundary is not unique")
    return source.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sha256(args.parent) != PARENT_SHA256:
        raise ValueError("state-reduced pre-FF backward digest differs")
    source = args.parent.read_text()
    source = replace_once(source, OLD_READERS, NEW_READERS, "input-reader")
    source = replace_once(
        source, OLD_BRANCH_ROUND, NEW_BRANCH_ROUND, "branch-conversion"
    )
    source = replace_once(
        source, OLD_NAMESPACE_END, NEW_NAMESPACE_END, "namespace"
    )
    source = replace_once(source, OLD_MAIN, NEW_MAIN, "main")
    args.output.write_text(source)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
