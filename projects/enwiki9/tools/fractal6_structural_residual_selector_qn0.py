#!/usr/bin/env python3
"""Build and gate a native structural residual selector against Endpoint428."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal6_structural_residual_selector_qn0_v1"
DEFAULT_SOURCE = Path("/home/x/enwiki9-nonproof/results/endpoint428_pair_layer0_gate_dot_fuse_output_update_loop_minified_lzma_source_package_v1/clean-build-a/build")
GUARD = ROOT / "tools/run_with_rss_guard.py"


REPLACEMENTS = {
    "src/online-residual-mixer.h": [
        (
            "  std::uint16_t Predict(std::uint16_t base,\n"
            "      const std::array<std::uint16_t, kEndpointCount>& endpoints);\n",
            "  std::uint16_t Predict(std::uint16_t base,\n"
            "      const std::array<std::uint16_t, kEndpointCount>& endpoints,\n"
            "      std::uint32_t structural_context);\n",
        ),
        (
            "  static const unsigned int kContextCount = 256;\n",
            "  static const unsigned int kBaseContextCount = 256;\n"
            "  static const unsigned int kStructuralContextCount = 8;\n"
            "  static const unsigned int kContextCount =\n"
            "      kBaseContextCount * kStructuralContextCount;\n",
        ),
    ],
    "src/online-residual-mixer.cpp": [
        (
            "std::uint16_t OnlineResidualMixer::Predict(std::uint16_t base,\n"
            "    const std::array<std::uint16_t, kEndpointCount>& endpoints) {\n",
            "std::uint16_t OnlineResidualMixer::Predict(std::uint16_t base,\n"
            "    const std::array<std::uint16_t, kEndpointCount>& endpoints,\n"
            "    std::uint32_t structural_context) {\n",
        ),
        (
            "  context_ = (((row_ & 7) * 8 + ByteClass(previous_byte_)) * 4) +\n"
            "      ConfidenceBin(base);\n",
            "  const unsigned int base_context =\n"
            "      (((row_ & 7) * 8 + ByteClass(previous_byte_)) * 4) +\n"
            "      ConfidenceBin(base);\n"
            "  structural_context ^= structural_context >> 16;\n"
            "  structural_context *= 0x7feb352dU;\n"
            "  structural_context ^= structural_context >> 15;\n"
            "  const unsigned int structural_bin =\n"
            "      structural_context & (kStructuralContextCount - 1);\n"
            "  context_ = base_context * kStructuralContextCount + structural_bin;\n",
        ),
        (
            "  return seen_[context_] >= 256 && regret_[context_] > 0\n",
            "  return seen_[context_] >= 64 && regret_[context_] > 0\n",
        ),
    ],
    "src/predictor.cpp": [
        (
            "  const std::uint16_t final_p1 =\n"
            "      online_residual_mixer_.Predict(mixed_p1, residual_endpoints);\n",
            "#ifdef FRACTAL_STRUCTURAL_CONTROL\n"
            "  const std::uint32_t residual_context =\n"
            "      static_cast<std::uint32_t>(manager_.recent_bytes_[0])\n"
            "      ^ (static_cast<std::uint32_t>(manager_.recent_bytes_[1]) << 8)\n"
            "      ^ (static_cast<std::uint32_t>(manager_.recent_bytes_[2]) << 16);\n"
            "#else\n"
            "  const std::uint32_t residual_context = manager_.sidecar_direct_\n"
            "      ^ (manager_.sidecar_direct2_ << 8)\n"
            "      ^ (manager_.sidecar_direct3_ << 16)\n"
            "      ^ (manager_.sidecar_direct4_ << 24);\n"
            "#endif\n"
            "  const std::uint16_t final_p1 = online_residual_mixer_.Predict(\n"
            "      mixed_p1, residual_endpoints, residual_context);\n",
        ),
    ],
    "Makefile": [
        (
            "\t-DCMIX_FXCM_CMC2_IDX13_DIV=1\n",
            "\t-DCMIX_FXCM_CMC2_IDX13_DIV=1 \\\n"
            "\t$(FRACTAL_DEFINES)\n",
        ),
    ],
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def mutate_source(source: Path, arm: str, output_dir: Path) -> None:
    diff_parts: list[str] = []
    for relative, replacements in REPLACEMENTS.items():
        path = source / relative
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in replacements:
            if updated.count(old) != 1:
                raise RuntimeError(f"replacement contract failed for {relative}")
            updated = updated.replace(old, new)
        path.write_text(updated, encoding="utf-8")
        diff_parts.extend(difflib.unified_diff(
            original.splitlines(keepends=True), updated.splitlines(keepends=True),
            fromfile=f"a/{relative}", tofile=f"b/{relative}",
        ))
    (output_dir / f"{arm}.patch").write_text("".join(diff_parts), encoding="utf-8")


def run_command(command: list[str], cwd: Path, log_path: Path,
                env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")


def guarded_run(label: str, binary: Path, mode: str, source: Path, target: Path,
                output_dir: Path) -> dict[str, object]:
    guard_path = output_dir / f"{label}.guard.json"
    log_path = output_dir / f"{label}.log"
    command = [
        sys.executable, str(GUARD),
        "--limit-kib", "10485760",
        "--limit-mode", "max_single",
        "--official-decimal-limit-kib", "9765625",
        "--sample-interval", "0.5",
        "--guard-json", str(guard_path),
        "--label", label,
        str(binary), mode, str(source), str(target),
    ]
    run_command(command, output_dir, log_path)
    return json.loads(guard_path.read_text(encoding="utf-8"))


def run_arm(arm: str, binary: Path, input_path: Path,
            output_dir: Path) -> dict[str, object]:
    archive = output_dir / f"{arm}.archive"
    restored = output_dir / f"{arm}.restored"
    repeat = output_dir / f"{arm}.repeat.archive"
    encode_guard = guarded_run(f"{arm}_encode", binary, "c", input_path, archive, output_dir)
    decode_guard = guarded_run(f"{arm}_decode", binary, "d", archive, restored, output_dir)
    repeat_guard = guarded_run(f"{arm}_repeat", binary, "c", input_path, repeat, output_dir)
    input_bytes = input_path.read_bytes()
    restored_bytes = restored.read_bytes()
    archive_bytes = archive.read_bytes()
    repeat_bytes = repeat.read_bytes()
    return {
        "binary_bytes": binary.stat().st_size,
        "binary_sha256": sha256_file(binary),
        "archive_bytes": len(archive_bytes),
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "repeat_archive_sha256": hashlib.sha256(repeat_bytes).hexdigest(),
        "roundtrip_exact": restored_bytes == input_bytes,
        "deterministic_reencode": repeat_bytes == archive_bytes,
        "encode_guard": encode_guard,
        "decode_guard": decode_guard,
        "repeat_guard": repeat_guard,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--input", type=Path, default=ROOT / "data/enwik9")
    parser.add_argument("--prefix-bytes", type=int, default=250000)
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / f"results/{CANDIDATE_ID}")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    input_data = args.input.read_bytes()[:args.prefix_bytes]
    input_path = args.output_dir / "input.bin"
    input_path.write_bytes(input_data)
    binaries: dict[str, Path] = {"B0": args.source_root / "comp9a-decomp9"}
    source_hashes: dict[str, dict[str, str]] = {}

    with tempfile.TemporaryDirectory(prefix=f"{CANDIDATE_ID}_") as temporary:
        temporary_root = Path(temporary)
        for arm, define in (("C0", "-DFRACTAL_STRUCTURAL_CONTROL=1"), ("J0", "")):
            build = temporary_root / arm
            shutil.copytree(args.source_root, build)
            run_command(["make", "clean"], build, args.output_dir / f"{arm}.clean.log")
            mutate_source(build, arm, args.output_dir)
            run_command(["make", "-j2", f"FRACTAL_DEFINES={define}"], build,
                        args.output_dir / f"{arm}.build.log")
            preserved = args.output_dir / f"{arm}.comp9a-decomp9"
            shutil.copy2(build / "comp9a-decomp9", preserved)
            binaries[arm] = preserved
            source_hashes[arm] = {
                relative: sha256_file(build / relative) for relative in REPLACEMENTS
            }

    arms = {arm: run_arm(arm, binaries[arm], input_path, args.output_dir)
            for arm in ("B0", "C0", "J0")}
    source_delta_blob = (args.output_dir / "J0.patch").read_bytes() + Path(__file__).read_bytes()
    source_delta = lzma.compress(source_delta_blob, preset=9 | lzma.PRESET_EXTREME)
    (args.output_dir / "source_delta.lzma").write_bytes(source_delta)

    b0 = int(arms["B0"]["archive_bytes"])
    c0 = int(arms["C0"]["archive_bytes"])
    j0 = int(arms["J0"]["archive_bytes"])
    gains = {"J0_vs_B0": b0 - j0, "J0_vs_C0": c0 - j0}
    failed: list[str] = []
    if gains["J0_vs_B0"] < 1500:
        failed.append("J0_gain_vs_B0_below_1500_bytes")
    if gains["J0_vs_C0"] < 500:
        failed.append("J0_gain_vs_C0_below_500_bytes")
    if len(source_delta) > 20000:
        failed.append("compressed_source_delta_above_20000_bytes")
    for arm, row in arms.items():
        if not row["roundtrip_exact"]:
            failed.append(f"{arm}_roundtrip_failed")
        if not row["deterministic_reencode"]:
            failed.append(f"{arm}_determinism_failed")
        for phase in ("encode_guard", "decode_guard", "repeat_guard"):
            if int(row[phase].get("official_decimal_over_limit_kib", 0)) > 0:
                failed.append(f"{arm}_{phase}_decimal_memory_failed")

    decision = {
        "schema": "enwiki9_fractal6_structural_residual_selector_qn0_v1",
        "candidate_id": CANDIDATE_ID,
        "scope": {
            "raw_bytes": len(input_data),
            "raw_sha256": hashlib.sha256(input_data).hexdigest(),
        },
        "source": {
            "receipt_source_root": str(args.source_root),
            "parent_binary_sha256": sha256_file(binaries["B0"]),
            "modified_source_sha256": source_hashes,
            "compressed_delta_bytes": len(source_delta),
            "structural_bins": 8,
            "activation_rows": 64,
        },
        "arms": arms,
        "gains_bytes": gains,
        "proof": {
            "matched_capacity_and_activation_C0_J0": True,
            "only_context_source_differs_C0_J0": True,
            "parent_source_unmodified": True,
        },
        "failed_conditions": failed,
        "verdict": "promote_native_structural_selector" if not failed else "retire_native_structural_selector",
        "score_credit_bytes": 0,
    }
    (args.output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_id": CANDIDATE_ID,
        "archive_bytes": {arm: arms[arm]["archive_bytes"] for arm in arms},
        "gains_bytes": gains,
        "compressed_source_delta_bytes": len(source_delta),
        "failed_conditions": failed,
        "verdict": decision["verdict"],
        "output": str(args.output_dir / "decision.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
