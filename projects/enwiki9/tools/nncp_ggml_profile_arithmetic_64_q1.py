#!/usr/bin/env python3
"""Retry open arithmetic identity with the LibNC block-sum reduction."""

from __future__ import annotations

import lzma
from pathlib import Path
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_ggml_profile_arithmetic_64_q0 as q0


CANDIDATE_ID = "nncp_ggml_profile_arithmetic_64_q1_v1"
_BASE_EXTRACT = q0.extract


SUM_REDUCTION = r'''
static float libnc_sum_values(const float * source, int count) {
    if (count <= 0)
        throw std::runtime_error("invalid LibNC sum width");
    std::array<float, 16> partials{};
    int blocks = 0;
    int index = 0;
    for (; index + 64 <= count; index += 64, blocks++) {
        std::array<__m256, 8> values;
        for (int lane = 0; lane < 8; lane++)
            values[lane] = _mm256_loadu_ps(source + index + lane * 8);
        float block_sum = libnc_sum64(values);
        int slot = 0;
        while (blocks & (1 << slot)) {
            block_sum += partials[slot];
            partials[slot++] = 0.0f;
        }
        partials[slot] = block_sum;
    }
    if (index < count) {
        alignas(32) std::array<float, 64> tail{};
        std::copy_n(source + index, count - index, tail.data());
        std::array<__m256, 8> values;
        for (int lane = 0; lane < 8; lane++)
            values[lane] = _mm256_load_ps(tail.data() + lane * 8);
        float block_sum = libnc_sum64(values);
        int slot = 0;
        while (blocks & (1 << slot)) {
            block_sum += partials[slot];
            partials[slot++] = 0.0f;
        }
        partials[slot] = block_sum;
        blocks++;
    }
    float total = 0.0f;
    int slots = 0;
    for (int count_left = blocks; count_left; count_left >>= 1) slots++;
    for (int slot = 0; slot < slots; slot++) total += partials[slot];
    return total;
}

'''


def patch_open_source(source_root: Path) -> None:
    path = source_root / "profile_forward_parity.cpp"
    source = path.read_text()
    insertion = "static std::vector<float> softmax_rows(std::vector<float> values, int row_width) {"
    if source.count(insertion) != 1:
        raise ValueError("open source has no unique softmax insertion boundary")
    source = source.replace(insertion, SUM_REDUCTION + insertion, 1)
    scalar = """            float total0 = 0.0f;
            for (int index = 0; index < range0; index++) total0 += table[start + index];"""
    replacement = """            const float total0 = libnc_sum_values(table + start, range0);"""
    if source.count(scalar) != 1:
        raise ValueError("open source has no unique scalar tree reduction")
    path.write_text(source.replace(scalar, replacement, 1))


def extract(archive: Path, destination: Path) -> dict[str, Any]:
    receipt = _BASE_EXTRACT(archive, destination)
    if archive.resolve() == q0.Q18_SOURCE.resolve():
        patch_open_source(destination)
    return receipt


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = local_source_closure((Path(__file__),))
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(q0.ROOT).as_posix()
        observed = q0.reference(member)
        expected = declared.get(relative)
        if expected is None or any(
            observed[key] != expected.get(key) for key in ("path", "sha256")
        ):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(q0.ROOT).as_posix()
            )
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    compressed = lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    if len(compressed) > experiment["budget"]["maximumAddedPackageBytes"]:
        raise ValueError("incremental source closure exceeds the frozen package budget")
    path.write_bytes(compressed)
    tar_path.unlink()


q0.CANDIDATE_ID = CANDIDATE_ID
q0.extract = extract
q0.source_package = source_package


if __name__ == "__main__":
    raise SystemExit(q0.main())
