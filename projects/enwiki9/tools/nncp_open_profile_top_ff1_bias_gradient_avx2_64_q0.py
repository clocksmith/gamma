#!/usr/bin/env python3
"""Run the complete top-FF1 backward with exact AVX2 GEGLU arithmetic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import nncp_open_profile_top_ff1_bias_gradient_64_q0_v1 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
PARENT_ID = "nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2"
PARENT_PROGRAM = ROOT / "programs" / PARENT_ID
PARENT_RESULT = ROOT / "results" / PARENT_ID
PARENT_DECISION = PARENT_RESULT / "decision.json"
PARENT_EXECUTION = PARENT_RESULT / "execution.json"
PARENT_GUARD = PARENT_RESULT / "guard.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T095147Z_8ddedba49c.json"
)
PARENT_REDUCER = PARENT_PROGRAM / "top_ff1_bias_gradient.cpp"
BLOCK_RESULT = ROOT / "results/nncp_libnc_ff2_transpose_block128_64_q0_v1"
BLOCK_DECISION = BLOCK_RESULT / "decision.json"
BLOCK_EXECUTION = BLOCK_RESULT / "execution.json"
BLOCK_GUARD = BLOCK_RESULT / "guard.json"
BLOCK_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json"
)
BLOCK_ADJOINT = BLOCK_RESULT / "block128-ff2-input-adjoint.bf16"
SOURCE_FF2_RESULT = ROOT / "results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1"
SOURCE_FF2_DECISION = SOURCE_FF2_RESULT / "decision.json"
SOURCE_FF2_ADJOINT = SOURCE_FF2_RESULT / "source-ff2-input-adjoint.bf16"
AVX2_ID = "nncp_libnc_geglu_gate_avx2_64_q0_v1"
AVX2_RESULT = ROOT / "results" / AVX2_ID
AVX2_DECISION = AVX2_RESULT / "decision.json"
AVX2_EXECUTION = AVX2_RESULT / "execution.json"
AVX2_GUARD = AVX2_RESULT / "guard.json"
AVX2_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T104055Z_2c469fd001.json"
)
AVX2_GATE_ADJOINT = AVX2_RESULT / "avx2-geglu-gate-adjoint.bf16"
AVX2_VALUE_CONTROL = AVX2_RESULT / "value-branch-control.bf16"
SOURCE_BRANCH_RESULT = ROOT / (
    "results/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2"
)
SOURCE_GATE_ADJOINT = SOURCE_BRANCH_RESULT / "source-geglu-gate-adjoint.bf16"
SOURCE_VALUE_ADJOINT = SOURCE_BRANCH_RESULT / "source-geglu-value-adjoint.bf16"
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_materializer.py"
)
INNER = 3072
SAMPLES = 64 * 32


OLD_DERIVATIVE = """float gelu_derivative(float value) {
    const float square = value * value;
    const float argument = kGeluScale *
        (value + kGeluCubic * value * square);
    const float tanh_value = argument >= 8.0F ? 1.0F : std::tanh(argument);
    const float argument_derivative = kGeluScale *
        (1.0F + 3.0F * kGeluCubic * square);
    return 0.5F * (1.0F + tanh_value) +
        0.5F * value * (1.0F - tanh_value * tanh_value) *
            argument_derivative;
}
"""

NEW_DERIVATIVE = """__m256 libnc_exp8(__m256 value) {
    const __m256 upper = _mm256_set1_ps(87.0F);
    const __m256 lower = _mm256_set1_ps(-88.0F);
    const __m256 log2e = _mm256_set1_ps(1.4426950216293335F);
    const __m256 minus_ln2_high = _mm256_set1_ps(-0.693359375F);
    const __m256 ln2_low = _mm256_set1_ps(0.00021219444170128554F);
    __m256 reduced = _mm256_min_ps(value, upper);
    reduced = _mm256_max_ps(reduced, lower);
    const __m256i exponent = _mm256_cvtps_epi32(
        _mm256_mul_ps(log2e, reduced));
    const __m256 exponent_float = _mm256_cvtepi32_ps(exponent);
    reduced = _mm256_fmadd_ps(minus_ln2_high, exponent_float, reduced);
    reduced = _mm256_fmadd_ps(ln2_low, exponent_float, reduced);
    __m256 polynomial = _mm256_set1_ps(0.00019841270113829523F);
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.0013888889225199819F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.008333333767950535F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.0416666679084301F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.1666666716337204F));
    polynomial = _mm256_fmadd_ps(
        polynomial, reduced, _mm256_set1_ps(0.5F));
    polynomial = _mm256_fmadd_ps(
        polynomial, _mm256_mul_ps(reduced, reduced), reduced);
    polynomial = _mm256_add_ps(polynomial, _mm256_set1_ps(1.0F));
    return _mm256_castsi256_ps(_mm256_add_epi32(
        _mm256_castps_si256(polynomial),
        _mm256_slli_epi32(exponent, 23)));
}

float gelu_backward(float value, float incoming) {
    const __m256 input = _mm256_set1_ps(value);
    const __m256 one = _mm256_set1_ps(1.0F);
    const __m256 scale = _mm256_set1_ps(0.7978845834732056F);
    __m256 argument = _mm256_mul_ps(
        input, _mm256_set1_ps(0.035677406936883926F));
    argument = _mm256_fmadd_ps(argument, input, scale);
    argument = _mm256_mul_ps(argument, input);
    const __m256 exponential = libnc_exp8(
        _mm256_mul_ps(argument, _mm256_set1_ps(-2.0F)));
    const __m256 tanh_value = _mm256_sub_ps(
        _mm256_div_ps(
            _mm256_set1_ps(2.0F), _mm256_add_ps(exponential, one)),
        one);
    __m256 argument_derivative = _mm256_mul_ps(
        input, _mm256_set1_ps(0.10703222453594208F));
    argument_derivative = _mm256_fmadd_ps(
        argument_derivative, input, scale);
    const __m256 one_plus_tanh = _mm256_add_ps(tanh_value, one);
    const __m256 one_minus_tanh_square = _mm256_fnmadd_ps(
        tanh_value, tanh_value, one);
    __m256 derivative = _mm256_mul_ps(input, one_minus_tanh_square);
    derivative = _mm256_fmadd_ps(
        derivative, argument_derivative, one_plus_tanh);
    derivative = _mm256_mul_ps(derivative, _mm256_set1_ps(0.5F));
    const __m256 output = _mm256_mul_ps(
        derivative, _mm256_set1_ps(incoming));
    return _mm_cvtss_f32(_mm256_castps256_ps128(output));
}
"""

OLD_CALL = """                    ff1_residual[inner] = round_bf16(
                        gate_upstream * gelu_derivative(gate));
"""

NEW_CALL = """                    ff1_residual[inner] = round_bf16(
                        gelu_backward(gate, gate_upstream));
"""


original_execute = parent.base.execute
original_evaluate = parent.base.evaluate
patch_receipt: dict[str, Any] | None = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_reducer(path: Path) -> dict[str, Any]:
    source = path.read_text()
    if source.count(OLD_DERIVATIVE) != 1 or source.count(OLD_CALL) != 1:
        raise ValueError("exact AVX2 GEGLU patch boundary differs")
    source = source.replace(OLD_DERIVATIVE, NEW_DERIVATIVE)
    source = source.replace(OLD_CALL, NEW_CALL)
    path.write_text(source)
    return {
        "parentSha256": sha256(PARENT_REDUCER),
        "derivedSha256": sha256(path),
        "derivativeReplacementCount": 1,
        "callReplacementCount": 1,
    }


def execute(
    command: list[str],
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    global patch_receipt
    is_configure = len(command) >= 2 and command[0] == "cmake" and command[1] == "-S"
    if is_configure:
        if patch_receipt is not None:
            raise ValueError("exact AVX2 reducer was patched more than once")
        patch_receipt = patch_reducer(
            RESULT / "work/source/top_ff1_bias_gradient.cpp"
        )
    receipt = original_execute(command, cwd, environment)
    if is_configure:
        receipt["derivedReducer"] = patch_receipt
    return receipt


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    bound = (
        ("tail-decision", parent.TAIL_DECISION),
        ("tail-execution", parent.TAIL_EXECUTION),
        ("tail-guard", parent.TAIL_GUARD),
        ("tail-reflection", parent.TAIL_REFLECTION),
        ("promoted-final-rms-input-residual", parent.PROMOTED_RESIDUAL),
        ("parent-decision", PARENT_DECISION),
        ("parent-execution", PARENT_EXECUTION),
        ("parent-guard", PARENT_GUARD),
        ("parent-reflection", PARENT_REFLECTION),
        ("parent-reducer-source", PARENT_REDUCER),
        ("block128-decision", BLOCK_DECISION),
        ("block128-execution", BLOCK_EXECUTION),
        ("block128-guard", BLOCK_GUARD),
        ("block128-reflection", BLOCK_REFLECTION),
        ("block128-ff2-input-adjoint", BLOCK_ADJOINT),
        ("source-ff2-input-adjoint-decision", SOURCE_FF2_DECISION),
        ("source-ff2-input-adjoint", SOURCE_FF2_ADJOINT),
        ("avx2-decision", AVX2_DECISION),
        ("avx2-execution", AVX2_EXECUTION),
        ("avx2-guard", AVX2_GUARD),
        ("avx2-reflection", AVX2_REFLECTION),
        ("avx2-gate-adjoint", AVX2_GATE_ADJOINT),
        ("avx2-value-control", AVX2_VALUE_CONTROL),
        ("source-geglu-gate-adjoint", SOURCE_GATE_ADJOINT),
        ("source-geglu-value-adjoint", SOURCE_VALUE_ADJOINT),
    )
    for identifier, path in bound:
        if inputs.get(identifier) != parent.base.reference(path, identifier):
            raise ValueError(f"experiment input drifted: {identifier}")
    tail = json.loads(parent.TAIL_DECISION.read_text())
    tail_reflection = json.loads(parent.TAIL_REFLECTION.read_text())
    tail_guard = json.loads(parent.TAIL_GUARD.read_text())
    opened = json.loads(PARENT_DECISION.read_text())
    open_reflection = json.loads(PARENT_REFLECTION.read_text())
    open_guard = json.loads(PARENT_GUARD.read_text())
    block = json.loads(BLOCK_DECISION.read_text())
    block_reflection = json.loads(BLOCK_REFLECTION.read_text())
    block_guard = json.loads(BLOCK_GUARD.read_text())
    source_ff2 = json.loads(SOURCE_FF2_DECISION.read_text())
    avx2 = json.loads(AVX2_DECISION.read_text())
    avx2_reflection = json.loads(AVX2_REFLECTION.read_text())
    avx2_guard = json.loads(AVX2_GUARD.read_text())
    if not (
        tail["promotionPass"] is True
        and tail["measurements"]["sourceFinalNormResidualMismatchCount"] == 0
        and tail["measurements"]["topFf2MismatchCount"] == 0
        and tail_reflection["validity"]["valid"] is True
        and tail_guard["returncode"] == 0
        and opened["promotionPass"] is False
        and opened["killPass"] is True
        and opened["measurements"]["sourceFf2InputResidualMismatchCount"] == 0
        and opened["measurements"]["topFf1BiasMismatchCount"] == 4708
        and open_reflection["validity"]["valid"] is True
        and open_reflection["decision"]["verdict"] == "mutate"
        and open_guard["returncode"] == 0
        and block["promotionPass"] is True
        and block["measurements"]["block128SourceMismatchCount"] == 0
        and block_reflection["validity"]["valid"] is True
        and block_guard["returncode"] == 0
        and source_ff2["measurements"]["sourceCaptureDeterministic"] is True
        and BLOCK_ADJOINT.read_bytes() == SOURCE_FF2_ADJOINT.read_bytes()
        and avx2["promotionPass"] is True
        and avx2["measurements"]["avx2GateMismatchCount"] == 0
        and avx2["measurements"]["valueControlMismatchCount"] == 0
        and avx2_reflection["validity"]["valid"] is True
        and avx2_reflection["hypothesis"]["verdict"] == "supported"
        and avx2_reflection["decision"]["verdict"] == "mutate"
        and avx2_guard["returncode"] == 0
        and avx2_guard["rss_guard_exceeded"] is False
        and avx2_guard["temporary_disk_guard_exceeded"] is False
        and AVX2_GATE_ADJOINT.read_bytes() == SOURCE_GATE_ADJOINT.read_bytes()
        and AVX2_VALUE_CONTROL.read_bytes() == SOURCE_VALUE_ADJOINT.read_bytes()
    ):
        raise ValueError("complete exact-AVX2 top-FF1 antecedents are not satisfied")


def compare_split_bf16(
    combined: Path, gate_source: Path, value_source: Path
) -> tuple[tuple[int, float], tuple[int, float]]:
    combined_bytes = combined.read_bytes()
    gate_bytes = gate_source.read_bytes()
    value_bytes = value_source.read_bytes()
    branch_bytes = SAMPLES * INNER * 2
    if (
        len(combined_bytes) != 2 * branch_bytes
        or len(gate_bytes) != branch_bytes
        or len(value_bytes) != branch_bytes
    ):
        raise ValueError("GEGLU split comparison geometry differs")
    results: list[tuple[int, float]] = []
    for branch, source in ((0, gate_bytes), (1, value_bytes)):
        mismatches = 0
        maximum = 0.0
        for sample in range(SAMPLES):
            combined_start = (sample * 2 * INNER + branch * INNER) * 2
            source_start = sample * INNER * 2
            observed = combined_bytes[combined_start : combined_start + INNER * 2]
            expected = source[source_start : source_start + INNER * 2]
            for index in range(0, len(observed), 2):
                left_word = int.from_bytes(observed[index : index + 2], "little")
                right_word = int.from_bytes(expected[index : index + 2], "little")
                if left_word == right_word:
                    continue
                mismatches += 1
                left = struct.unpack("<f", struct.pack("<I", left_word << 16))[0]
                right = struct.unpack("<f", struct.pack("<I", right_word << 16))[0]
                maximum = max(maximum, abs(left - right))
        results.append((mismatches, maximum))
    return results[0], results[1]


def evaluate(
    predicates: list[dict[str, Any]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, Any]]:
    if "sourceFf2InputResidualMismatchCount" not in measurements:
        comparison = parent.base.parent.compare_bf16(
            RESULT / "open-ff2-input-residual.bf16", SOURCE_FF2_ADJOINT
        )
        measurements["sourceFf2InputResidualMismatchCount"] = comparison[0]
        measurements["maximumSourceFf2InputResidualAbsoluteError"] = comparison[1]
    if "sourceGateAdjointMismatchCount" not in measurements:
        gate, value = compare_split_bf16(
            RESULT / "open-ff1-output-residual.bf16",
            SOURCE_GATE_ADJOINT,
            SOURCE_VALUE_ADJOINT,
        )
        measurements["sourceGateAdjointMismatchCount"] = gate[0]
        measurements["maximumSourceGateAdjointAbsoluteError"] = gate[1]
        measurements["sourceValueAdjointMismatchCount"] = value[0]
        measurements["maximumSourceValueAdjointAbsoluteError"] = value[1]
    return original_evaluate(predicates, measurements)


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PROGRAM = PROGRAM
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.MATERIALIZER = PARENT_PROGRAM / "materialize_forward.py"
    parent.CMAKE = PARENT_PROGRAM / "CMakeLists.txt"
    parent.REDUCER = PARENT_REDUCER
    parent.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    parent.RUNNER = RUNNER
    parent.FREEZER = FREEZER
    parent.require_inputs = require_inputs
    parent.base.execute = execute
    parent.base.evaluate = evaluate
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
