#!/usr/bin/env python3
"""Run the zero-credit cmix-lex payload_lex transfer gate.

This intentionally avoids a full-corpus arithmetic compression. It constructs
the exact public transformed stream, proves the public inverse, and compares
three reset-state regime-1 slices under the same pinned cmix-lex model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


PINNED_COMMIT = "370e698f7ea62168cc64326ff97950c3dc212691"
TAIL_START = 541_126_651
REGIME1_START = 13_599_801
REGIME2_START = 30_372_888
REGIME1_ABSOLUTE = TAIL_START + REGIME1_START
REGIME1_LENGTH = REGIME2_START - REGIME1_START
SLICE_BYTES = 250_000
PUBLIC_COMPRESSED_SIDE_BYTES = 346_948
GAMMA_FORECAST = 109_524_268
PUBLIC_ONE_PERCENT_THRESHOLD = 108_574_923
DESIGN_TARGET = 108_000_000
PRIZE_GROSS_REQUIRED = (
    GAMMA_FORECAST - PUBLIC_ONE_PERCENT_THRESHOLD + PUBLIC_COMPRESSED_SIDE_BYTES
)
DESIGN_GROSS_REQUIRED = GAMMA_FORECAST - DESIGN_TARGET + PUBLIC_COMPRESSED_SIDE_BYTES
PRIZE_REQUIRED_BPM = (
    PRIZE_GROSS_REQUIRED * 1_000_000 + REGIME1_LENGTH - 1
) // REGIME1_LENGTH
DESIGN_REQUIRED_BPM = (
    DESIGN_GROSS_REQUIRED * 1_000_000 + REGIME1_LENGTH - 1
) // REGIME1_LENGTH
SAMPLED_BYTES = SLICE_BYTES * 3
SAMPLE_PRIZE_GATE = (
    PRIZE_REQUIRED_BPM * SAMPLED_BYTES + 1_000_000 - 1
) // 1_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    log_path: Path,
    time_path: Path | None = None,
) -> None:
    full_command = command
    if time_path is not None:
        full_command = ["/usr/bin/time", "-v", "-o", str(time_path), *command]
    with log_path.open("wb") as log:
        result = subprocess.run(
            full_command,
            cwd=cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with status {result.returncode}: {' '.join(command)}; "
            f"see {log_path}"
        )


def parse_peak_rss_kib(path: Path) -> int | None:
    if not path.exists():
        return None
    match = re.search(
        r"Maximum resident set size \(kbytes\):\s*(\d+)",
        path.read_text(errors="replace"),
    )
    return int(match.group(1)) if match else None


def patch_observation_source(source: Path) -> dict[str, str]:
    self_extract = source / "src/readalike_prepr/self_extract.h"
    runner = source / "src/runner.cpp"

    self_text = self_extract.read_text()
    if "#include <fstream>" not in self_text:
        self_text = self_text.replace("#include <string>\n", "#include <string>\n#include <fstream>\n")
    seed_marker = "int selfextract_comp() {\n"
    if seed_marker not in self_text:
        raise RuntimeError("selfextract_comp patch anchor missing")
    seed_patch = r'''int selfextract_comp() {
  const char* source_root = getenv("FX_PREPARE_SOURCE_ROOT");
  if (source_root) {
    auto copy_seed = [](const std::string& from, const std::string& to) {
      std::ifstream input(from, std::ios::binary);
      std::ofstream output(to, std::ios::binary | std::ios::trunc);
      output << input.rdbuf();
      return input.good() || input.eof() ? output.good() : false;
    };
    const std::string root(source_root);
    if (!copy_seed(root + "/dictionary/english.dic", ".dict") ||
        !copy_seed(root + "/src/readalike_prepr/data/new_article_order",
                   ".new_article_order")) {
      fprintf(stderr, "prepare source seeding failed\n");
      return 1;
    }
    return 0;
  }
'''
    self_text = self_text.replace(seed_marker, seed_patch, 1)
    self_extract.write_text(self_text)

    runner_text = runner.read_text()
    reorder_marker = (
        "  if (post_wrt_side_path &&\n"
        "      !r1_reorder::ReorderEncodedTailFile(temp_path, post_wrt_side_path)) {"
    )
    if reorder_marker not in runner_text:
        raise RuntimeError("payload reorder patch anchor missing")
    copy_patch = r'''  if (const char* original_copy = std::getenv("FX_PREPARE_ORIGINAL_COPY")) {
    std::ifstream source(temp_path, std::ios::binary);
    std::ofstream target(original_copy, std::ios::binary | std::ios::trunc);
    target << source.rdbuf();
    if (!(source.good() || source.eof()) || !target.good()) {
      fprintf(stderr, "prepare original-copy failed\n");
      return false;
    }
  }

'''
    runner_text = runner_text.replace(reorder_marker, copy_patch + reorder_marker, 1)
    runner.write_text(runner_text)
    return {
        "self_extract_sha256": sha256(self_extract),
        "runner_sha256": sha256(runner),
    }


def build_observation_binaries(
    source: Path, compiler: Path, logs: Path
) -> tuple[Path, Path]:
    build_env = os.environ.copy()
    build_env["PATH"] = f"{compiler.parent}:{build_env.get('PATH', '')}"
    build_env["CC"] = str(compiler)
    run(
        [
            "make",
            "-j2",
            f"CC={compiler}",
            "LFLAGS=-m64 -fuse-ld=bfd -Wl,--gc-sections -std=c++17",
            "cmix",
        ],
        cwd=source,
        env=build_env,
        log_path=logs / "build_cmix.log",
    )
    cmix = source / "cmix"
    if not cmix.is_file():
        raise RuntimeError("cmix build produced no binary")

    helper_source = source / "payload_restore_helper.cpp"
    helper_source.write_text(
        r'''#include "src/r1_reorder_transform.h"
#include <cstdio>

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: helper TRANSFORMED EXTRACTED_SIDE\n");
    return 2;
  }
  if (!r1_reorder::ExtractSideFromFile(argv[1], argv[2])) return 3;
  if (!r1_reorder::RestoreEncodedTailFile(argv[1], argv[2])) return 4;
  return 0;
}
'''
    )
    helper = source / "payload_restore_helper"
    run(
        [
            str(compiler),
            "-std=c++17",
            "-O2",
            str(helper_source),
            str(source / "src/r1_reorder_transform.cpp"),
            "-o",
            str(helper),
        ],
        cwd=source,
        env=build_env,
        log_path=logs / "build_restore_helper.log",
    )
    return cmix, helper


def find_transformed_ready(work: Path, expected_original: Path) -> Path:
    candidates = []
    for path in work.iterdir():
        if not path.is_file() or path == expected_original:
            continue
        size = path.stat().st_size
        if 580_000_000 <= size <= 600_000_000:
            candidates.append(path)
    if len(candidates) != 1:
        rendered = [(str(path), path.stat().st_size) for path in candidates]
        raise RuntimeError(f"expected one transformed ready stream, found {rendered}")
    return candidates[0]


def copy_range(source: Path, target: Path, offset: int, length: int) -> None:
    remaining = length
    with source.open("rb") as src, target.open("wb") as dst:
        src.seek(offset)
        while remaining:
            chunk = src.read(min(8 << 20, remaining))
            if not chunk:
                raise RuntimeError(f"short read from {source} at {offset}")
            dst.write(chunk)
            remaining -= len(chunk)


def prepare_streams(
    *,
    source_root: Path,
    input_path: Path,
    work: Path,
    artifacts: Path,
    cmix: Path,
    helper: Path,
    logs: Path,
) -> dict[str, object]:
    work_cmix = work / "cmix"
    shutil.copy2(cmix, work_cmix)
    work_cmix.chmod(0o755)
    original = artifacts / "original_ready.bin"
    output = work / "prepare_only.archive"
    prepare_env = os.environ.copy()
    prepare_env["FX_PREPARE_SOURCE_ROOT"] = str(source_root)
    prepare_env["FX_PREPARE_ORIGINAL_COPY"] = str(original)
    prepare_env["FX_PREPARE_ONLY"] = "1"
    prepare_time = logs / "prepare.time"
    run(
        [str(work_cmix), "-e", str(input_path), str(output)],
        cwd=work,
        env=prepare_env,
        log_path=logs / "prepare.log",
        time_path=prepare_time,
    )
    if not original.is_file():
        raise RuntimeError("prepare run did not preserve original ready stream")
    transformed_in_work = find_transformed_ready(work, original)
    transformed = artifacts / "transformed_ready.bin"
    shutil.move(str(transformed_in_work), transformed)

    restored = artifacts / "restored_ready.bin"
    shutil.copy2(transformed, restored)
    extracted_side = artifacts / "extracted_payload_side.bin"
    run(
        [str(helper), str(restored), str(extracted_side)],
        cwd=source_root,
        log_path=logs / "restore.log",
    )
    original_hash = sha256(original)
    restored_hash = sha256(restored)
    inversion_exact = (
        original.stat().st_size == restored.stat().st_size
        and original_hash == restored_hash
    )
    if not inversion_exact:
        raise RuntimeError("public payload transform failed exact inversion")
    restored.unlink()

    return {
        "input_bytes": input_path.stat().st_size,
        "input_sha256": sha256(input_path),
        "original_ready_path": str(original),
        "original_ready_bytes": original.stat().st_size,
        "original_ready_sha256": original_hash,
        "transformed_ready_path": str(transformed),
        "transformed_ready_bytes": transformed.stat().st_size,
        "transformed_ready_sha256": sha256(transformed),
        "extracted_side_path": str(extracted_side),
        "extracted_side_bytes": extracted_side.stat().st_size,
        "extracted_side_sha256": sha256(extracted_side),
        "inversion_exact": inversion_exact,
        "prepare_peak_rss_kib": parse_peak_rss_kib(prepare_time),
    }


def compare_slices(
    *,
    cmix: Path,
    work: Path,
    artifacts: Path,
    logs: Path,
    original: Path,
    transformed: Path,
) -> tuple[list[dict[str, object]], int, int | None]:
    starts = [
        0,
        (REGIME1_LENGTH - SLICE_BYTES) // 2,
        REGIME1_LENGTH - SLICE_BYTES,
    ]
    rows: list[dict[str, object]] = []
    peak_rss = 0
    for index, relative_start in enumerate(starts):
        absolute_start = REGIME1_ABSOLUTE + relative_start
        row: dict[str, object] = {
            "index": index,
            "relative_start": relative_start,
            "absolute_start": absolute_start,
            "input_bytes": SLICE_BYTES,
        }
        sizes: dict[str, int] = {}
        for variant, stream in (("original", original), ("transformed", transformed)):
            slice_path = artifacts / f"slice_{index}_{variant}.bin"
            archive_path = artifacts / f"slice_{index}_{variant}.cmix"
            copy_range(stream, slice_path, absolute_start, SLICE_BYTES)
            time_path = logs / f"slice_{index}_{variant}.time"
            run(
                [str(cmix), "-n", str(slice_path), str(archive_path)],
                cwd=work,
                log_path=logs / f"slice_{index}_{variant}.log",
                time_path=time_path,
            )
            sizes[variant] = archive_path.stat().st_size
            measured_rss = parse_peak_rss_kib(time_path)
            if measured_rss is not None:
                peak_rss = max(peak_rss, measured_rss)
            row[f"{variant}_input_sha256"] = sha256(slice_path)
            row[f"{variant}_archive_bytes"] = sizes[variant]
            row[f"{variant}_archive_sha256"] = sha256(archive_path)
            row[f"{variant}_peak_rss_kib"] = measured_rss
        row["gross_gain_bytes"] = sizes["original"] - sizes["transformed"]
        rows.append(row)
    aggregate_gain = sum(int(row["gross_gain_bytes"]) for row in rows)
    return rows, aggregate_gain, peak_rss or None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/external/cmix-lex"),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/home/x/enwiki9-nonproof/enwik9"),
    )
    parser.add_argument(
        "--compiler",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin/clang++-17"
        ),
    )
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    input_path = args.input.resolve()
    result_dir = args.result_dir.resolve()
    logs = result_dir / "logs"
    artifacts = Path("/home/x/enwiki9-nonproof/cmix_lex_payload_gate") / result_dir.name
    work = artifacts / "work"
    source_copy = artifacts / "source"
    for directory in (result_dir, logs, artifacts, work):
        directory.mkdir(parents=True, exist_ok=True)

    if not input_path.is_file() or input_path.stat().st_size != 1_000_000_000:
        raise SystemExit(f"expected exact 1G input at {input_path}")
    if not args.compiler.is_file():
        raise SystemExit(f"missing host-local compiler: {args.compiler}")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source, text=True
    ).strip()
    if source_commit != PINNED_COMMIT:
        raise SystemExit(
            f"cmix-lex source must be {PINNED_COMMIT}, found {source_commit}"
        )
    if not source_copy.exists():
        shutil.copytree(source, source_copy, ignore=shutil.ignore_patterns(".git", "cmix", "*.o"))

    started = int(time.time())
    verdict = "invalid"
    decision: dict[str, object] = {
        "schema": "gamma.cmix_lex_payload_transfer_decision.v1",
        "candidate_id": "cmix_lex_payload_external_v1",
        "proposal_id": "cmix_lex_payload_transfer_v1",
        "score_credit_bytes": 0,
        "source_repository": "https://github.com/blahem/cmix-lex",
        "source_commit": source_commit,
        "constants": {
            "tail_start": TAIL_START,
            "regime1_start": REGIME1_START,
            "regime1_absolute": REGIME1_ABSOLUTE,
            "regime1_length": REGIME1_LENGTH,
            "slice_bytes": SLICE_BYTES,
            "sampled_bytes": SAMPLED_BYTES,
            "public_compressed_side_bytes": PUBLIC_COMPRESSED_SIDE_BYTES,
            "gamma_forecast": GAMMA_FORECAST,
            "public_one_percent_threshold": PUBLIC_ONE_PERCENT_THRESHOLD,
            "design_target": DESIGN_TARGET,
            "prize_gross_required": PRIZE_GROSS_REQUIRED,
            "design_gross_required": DESIGN_GROSS_REQUIRED,
            "prize_required_bpm": PRIZE_REQUIRED_BPM,
            "design_required_bpm": DESIGN_REQUIRED_BPM,
            "sample_prize_gate_bytes": SAMPLE_PRIZE_GATE,
        },
    }
    decision_path = result_dir / "decision.json"
    try:
        patch_hashes = patch_observation_source(source_copy)
        cmix, helper = build_observation_binaries(source_copy, args.compiler, logs)
        construction = prepare_streams(
            source_root=source,
            input_path=input_path,
            work=work,
            artifacts=artifacts,
            cmix=cmix,
            helper=helper,
            logs=logs,
        )
        rows, aggregate_gain, compare_peak_rss = compare_slices(
            cmix=cmix,
            work=work,
            artifacts=artifacts,
            logs=logs,
            original=Path(str(construction["original_ready_path"])),
            transformed=Path(str(construction["transformed_ready_path"])),
        )
        all_nonnegative = all(int(row["gross_gain_bytes"]) >= 0 for row in rows)
        memory_values = [
            value
            for value in (
                construction.get("prepare_peak_rss_kib"),
                compare_peak_rss,
            )
            if isinstance(value, int)
        ]
        peak_rss_kib = max(memory_values) if memory_values else None
        memory_ok = peak_rss_kib is not None and peak_rss_kib * 1024 < 10_000_000_000
        passes = (
            bool(construction["inversion_exact"])
            and all_nonnegative
            and aggregate_gain >= SAMPLE_PRIZE_GATE
            and memory_ok
        )
        verdict = "authorize_native_integration" if passes else "retire_transfer"
        decision.update(
            {
                "verdict": verdict,
                "observation_patch": patch_hashes,
                "construction": construction,
                "slices": rows,
                "aggregate": {
                    "original_archive_bytes": sum(
                        int(row["original_archive_bytes"]) for row in rows
                    ),
                    "transformed_archive_bytes": sum(
                        int(row["transformed_archive_bytes"]) for row in rows
                    ),
                    "gross_gain_bytes": aggregate_gain,
                    "gross_gain_bpm": aggregate_gain * 1_000_000 / SAMPLED_BYTES,
                    "all_slices_nonnegative": all_nonnegative,
                    "peak_rss_kib": peak_rss_kib,
                    "memory_ok": memory_ok,
                    "passes_prize_scale_gate": aggregate_gain >= SAMPLE_PRIZE_GATE,
                },
                "interpretation": (
                    "Zero-credit reset-state oracle. A pass authorizes only a "
                    "state-faithful native integration; it is not a score result."
                ),
            }
        )
    except Exception as exc:
        decision.update({"verdict": verdict, "error": str(exc)})
    finally:
        decision["started_unix"] = started
        decision["finished_unix"] = int(time.time())
        decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")

    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if verdict in {"authorize_native_integration", "retire_transfer"} else 1


if __name__ == "__main__":
    sys.exit(main())
