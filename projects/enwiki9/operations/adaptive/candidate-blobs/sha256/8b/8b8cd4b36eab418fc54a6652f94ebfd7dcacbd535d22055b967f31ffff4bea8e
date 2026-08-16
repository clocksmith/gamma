#!/usr/bin/env python3
"""Retarget the exact final RMSNorm backward to layer 19 pre-FF."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PARENT_SHA256 = "e4dea5eb25530581447a32463bac5bb2f063d376501b62733ddbf45e081a3fb5"
OLD_NAMESPACE_END = """
}  // namespace

int main(int argc, char ** argv) {
"""
NEW_NAMESPACE_END = """
std::vector<float> merge_residuals(
    const std::vector<float> & normalized_branch,
    const std::vector<float> & direct_branch
) {
    if (normalized_branch.size() != direct_branch.size()) {
        throw std::runtime_error("pre-FF residual geometry differs");
    }
    std::vector<float> result(normalized_branch.size());
    for (std::size_t index = 0; index < result.size(); ++index) {
        result[index] = round_bf16(
            normalized_branch[index] + direct_branch[index]);
    }
    return result;
}

}  // namespace

int main(int argc, char ** argv) {
"""
OLD_MAIN = """        if (argc != 9) {
            throw std::runtime_error(
                "usage: final_norm_backward PARAMETERS OPEN_ROOT HIDDEN_RESIDUAL "
                "OUT_LN_G OUT_LN_B OUT_INPUT_RESIDUAL OUT_FF_BIAS CONTROL_FF_BIAS");
        }
        const std::vector<float> gain = read_gain(argv[1]);
        const std::vector<float> norm_input = read_norm_inputs(argv[2]);
        const std::vector<float> incoming = read_bf16(
            argv[3], kSamples * kWidth);
        const BackwardResult observed = backward(norm_input, incoming, gain);
        std::vector<float> negated(incoming.size());
        std::transform(incoming.begin(), incoming.end(), negated.begin(),
                       [](float value) { return -value; });
        const BackwardResult control = backward(norm_input, negated, gain);
        write_bf16(argv[4], observed.gain_gradient);
        write_bf16(argv[5], observed.bias_gradient);
        write_bf16(argv[6], observed.input_residual);
        write_bf16(argv[7], observed.input_bias_projection);
        write_bf16(argv[8], control.input_bias_projection);
"""
NEW_MAIN = """        if (argc != 11) {
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"pre-FF backward {label} boundary is not unique")
    return source.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sha256(args.parent) != PARENT_SHA256:
        raise ValueError("exact final RMSNorm backward parent digest differs")
    source = args.parent.read_text()
    source = replace_once(source, '"ln_g_40"', '"ln_g_39"', "gain")
    source = replace_once(
        source,
        '"final_norm_input.f32"',
        '"layer_19_pre_ff_hidden.f32"',
        "input",
    )
    source = replace_once(
        source, OLD_NAMESPACE_END, NEW_NAMESPACE_END, "namespace"
    )
    source = replace_once(source, OLD_MAIN, NEW_MAIN, "main")
    source = source.replace("final RMSNorm", "pre-FF RMSNorm")
    args.output.write_text(source)
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
