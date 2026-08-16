#!/usr/bin/env python3
"""Inject payload writes into the canonical exact open Adam replay."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "programs/nncp_open_profile_adam_replay_64_q0_retry_v2/adam_replay.cpp"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"canonical Adam patch marker is not unique: {old[:80]!r}")
    return source.replace(old, new, 1)


def materialize() -> str:
    source = SOURCE.read_text()
    source = replace_once(
        source,
        "namespace {\n\nconstexpr std::uint32_t kFileMagic",
        "namespace {\n\nfs::path payload_output_directory;\n\n"
        "constexpr std::uint32_t kFileMagic",
    )
    source = replace_once(
        source,
        "    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};\n"
        "    alignas(32) std::array<std::uint32_t, 8> predicted_variance {};\n\n"
        "    for (std::uint64_t index = 0; index < count; index += 8) {",
        "    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};\n"
        "    alignas(32) std::array<std::uint32_t, 8> predicted_variance {};\n"
        "    const fs::path payload_path = payload_output_directory / (name + \".bin\");\n"
        "    std::ofstream payload_output(payload_path, std::ios::binary);\n"
        "    if (!payload_output)\n"
        "        throw std::runtime_error(\"cannot write open payload \" + payload_path.string());\n\n"
        "    for (std::uint64_t index = 0; index < count; index += 8) {",
    )
    source = replace_once(
        source,
        "            const std::uint16_t predicted_v = static_cast<std::uint16_t>(\n"
        "                predicted_variance[lane]);\n"
        "            if (predicted_high != parameter_out[item]) {",
        "            const std::uint16_t predicted_v = static_cast<std::uint16_t>(\n"
        "                predicted_variance[lane]);\n"
        "            payload_output.write(\n"
        "                reinterpret_cast<const char *>(&predicted_high),\n"
        "                sizeof(predicted_high));\n"
        "            if (!payload_output)\n"
        "                throw std::runtime_error(\"cannot write open payload \" +\n"
        "                                         payload_path.string());\n"
        "            if (predicted_high != parameter_out[item]) {",
    )
    source = replace_once(
        source,
        "    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};\n"
        "    alignas(32) std::array<std::uint32_t, 8> predicted_variance {};\n"
        "    for (std::uint64_t index = 0; index < count; index += 8) {",
        "    alignas(32) std::array<std::uint32_t, 8> predicted_parameter {};\n"
        "    alignas(32) std::array<std::uint32_t, 8> predicted_variance {};\n"
        "    const fs::path payload_path = payload_output_directory / (name + \".bin\");\n"
        "    std::ofstream payload_output(payload_path, std::ios::binary);\n"
        "    if (!payload_output)\n"
        "        throw std::runtime_error(\"cannot write open payload \" + payload_path.string());\n"
        "    for (std::uint64_t index = 0; index < count; index += 8) {",
    )
    source = replace_once(
        source,
        "        for (std::uint64_t lane = 0; lane < 8; ++lane) {\n"
        "            const std::uint64_t item = index + lane;\n"
        "            if (predicted_parameter[lane] != parameter_out[item]) {",
        "        for (std::uint64_t lane = 0; lane < 8; ++lane) {\n"
        "            const std::uint64_t item = index + lane;\n"
        "            payload_output.write(\n"
        "                reinterpret_cast<const char *>(&predicted_parameter[lane]),\n"
        "                sizeof(predicted_parameter[lane]));\n"
        "            if (!payload_output)\n"
        "                throw std::runtime_error(\"cannot write open payload \" +\n"
        "                                         payload_path.string());\n"
        "            if (predicted_parameter[lane] != parameter_out[item]) {",
    )
    source = replace_once(
        source,
        "        if (argc != 3) {\n"
        "            throw std::runtime_error(\"usage: adam_replay FIXTURE REPORT\");\n"
        "        }\n"
        "        const fs::path fixture = fs::canonical(argv[1]);\n"
        "        const fs::path report = fs::absolute(argv[2]);",
        "        if (argc != 4) {\n"
        "            throw std::runtime_error(\n"
        "                \"usage: adam_replay FIXTURE REPORT OUTPUT_DIRECTORY\");\n"
        "        }\n"
        "        const fs::path fixture = fs::canonical(argv[1]);\n"
        "        const fs::path report = fs::absolute(argv[2]);\n"
        "        payload_output_directory = fs::absolute(argv[3]);\n"
        "        if (!fs::create_directory(payload_output_directory) ||\n"
        "            !fs::is_empty(payload_output_directory)) {\n"
        "            throw std::runtime_error(\n"
        "                \"open payload output directory is not fresh\");\n"
        "        }",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f"output already exists: {args.output}")
    args.output.write_text(materialize())
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
