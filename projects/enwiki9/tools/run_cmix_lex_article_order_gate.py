#!/usr/bin/env python3
"""Run the zero-credit public cmix-lex article-order transfer gate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from run_cmix_lex_payload_gate import (
    PINNED_COMMIT,
    build_observation_binaries,
    copy_range,
    parse_peak_rss_kib,
    patch_observation_source,
    run,
    sha256,
)


ORDER_BYTES = 1_094_862
ORDER_SHA256 = "eecd462c29319bab185b48229c4d09ab52f16ca9c582e8e32eff9a7c2a7de39e"
PUBLIC_READY_BYTES = 586_459_321
PUBLIC_READY_SHA256 = "cb466004e5d76000ba7d44a1a4a47245c203f4e8fbb62ffca7799692c966ff4f"
GAMMA_FORECAST = 109_524_268
PUBLIC_ONE_PERCENT_THRESHOLD = 108_574_923
DESIGN_TARGET = 108_000_000
SLICE_BYTES = 1_000_000
SAMPLED_BYTES = 3 * SLICE_BYTES
PRIZE_GROSS_REQUIRED = (
    GAMMA_FORECAST - PUBLIC_ONE_PERCENT_THRESHOLD + ORDER_BYTES
)
DESIGN_GROSS_REQUIRED = GAMMA_FORECAST - DESIGN_TARGET + ORDER_BYTES
PRIZE_REQUIRED_BPM = (
    PRIZE_GROSS_REQUIRED * 1_000_000 + PUBLIC_READY_BYTES - 1
) // PUBLIC_READY_BYTES
DESIGN_REQUIRED_BPM = (
    DESIGN_GROSS_REQUIRED * 1_000_000 + PUBLIC_READY_BYTES - 1
) // PUBLIC_READY_BYTES
SAMPLE_PRIZE_GATE = (
    PRIZE_REQUIRED_BPM * SAMPLED_BYTES + 1_000_000 - 1
) // 1_000_000
SAMPLE_DESIGN_GATE = (
    DESIGN_REQUIRED_BPM * SAMPLED_BYTES + 1_000_000 - 1
) // 1_000_000


def patch_article_control(source: Path) -> dict[str, str]:
    runner = source / "src/runner.cpp"
    runner_text = runner.read_text()
    marker = "  if (post_wrt_side_path &&\n"
    replacement = (
        "  if (post_wrt_side_path && "
        "!std::getenv(\"FX_SKIP_PAYLOAD_LEX\") &&\n"
    )
    if marker not in runner_text:
        raise RuntimeError("payload skip patch anchor missing")
    runner.write_text(runner_text.replace(marker, replacement, 1))

    article = source / "src/readalike_prepr/article_reorder.h"
    article_text = article.read_text()
    if "#include <algorithm>" not in article_text:
        article_text = article_text.replace(
            "#include <fstream>\n", "#include <fstream>\n#include <algorithm>\n"
        )
    fallback_marker = '''    if (positions.size() < NUM_OF_ARTICLES) {
        for (int i = 0; i < NUM_OF_ARTICLES; i++) {
            if (used[i] == 0) {
                positions.push_back(i);
            }
       }
    }
'''
    identity_patch = fallback_marker + '''    if (std::getenv("FX_IDENTITY_ARTICLE_ORDER")) {
      std::stable_sort(positions.begin(), positions.end());
    }
'''
    if fallback_marker not in article_text:
        raise RuntimeError("article identity patch anchor missing")
    article.write_text(article_text.replace(fallback_marker, identity_patch, 1))
    return {
        "runner_sha256": sha256(runner),
        "article_reorder_sha256": sha256(article),
    }


def prepare_identity(
    *,
    source_root: Path,
    input_path: Path,
    cmix: Path,
    work: Path,
    identity: Path,
    logs: Path,
) -> int | None:
    work_cmix = work / "cmix"
    shutil.copy2(cmix, work_cmix)
    work_cmix.chmod(0o755)
    env = os.environ.copy()
    env["FX_PREPARE_SOURCE_ROOT"] = str(source_root)
    env["FX_PREPARE_ORIGINAL_COPY"] = str(identity)
    env["FX_PREPARE_ONLY"] = "1"
    env["FX_IDENTITY_ARTICLE_ORDER"] = "1"
    env["FX_SKIP_PAYLOAD_LEX"] = "1"
    time_path = logs / "prepare_identity.time"
    run(
        [str(work_cmix), "-e", str(input_path), str(work / "identity.archive")],
        cwd=work,
        env=env,
        log_path=logs / "prepare_identity.log",
        time_path=time_path,
    )
    if not identity.is_file():
        raise RuntimeError("identity-order prepare produced no ready stream")
    return parse_peak_rss_kib(time_path)


def compare(
    *,
    cmix: Path,
    work: Path,
    artifacts: Path,
    logs: Path,
    identity: Path,
    public: Path,
    population_bytes: int,
) -> tuple[list[dict[str, object]], int, int | None]:
    starts = [
        0,
        (population_bytes - SLICE_BYTES) // 2,
        population_bytes - SLICE_BYTES,
    ]
    rows: list[dict[str, object]] = []
    peak_rss = 0
    for index, start in enumerate(starts):
        row: dict[str, object] = {
            "index": index,
            "absolute_start": start,
            "input_bytes": SLICE_BYTES,
        }
        sizes: dict[str, int] = {}
        for variant, stream in (("identity", identity), ("public", public)):
            slice_path = artifacts / f"slice_{index}_{variant}.bin"
            archive_path = artifacts / f"slice_{index}_{variant}.cmix"
            copy_range(stream, slice_path, start, SLICE_BYTES)
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
        row["gross_gain_bytes"] = sizes["identity"] - sizes["public"]
        rows.append(row)
    gain = sum(int(row["gross_gain_bytes"]) for row in rows)
    return rows, gain, peak_rss or None


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
        default=Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9"),
    )
    parser.add_argument(
        "--public-ready",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
            "cmix_lex_payload_transfer_v1_retry2/original_ready.bin"
        ),
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
    public = args.public_ready.resolve()
    result_dir = args.result_dir.resolve()
    logs = result_dir / "logs"
    artifacts = (
        Path("/home/x/enwiki9-nonproof/cmix_lex_article_order_gate")
        / result_dir.name
    )
    source_copy = artifacts / "source"
    work = artifacts / "work"
    identity = artifacts / "identity_ready.bin"
    for directory in (result_dir, logs, artifacts, work):
        directory.mkdir(parents=True, exist_ok=True)

    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source, text=True
    ).strip()
    if source_commit != PINNED_COMMIT:
        raise SystemExit(f"expected {PINNED_COMMIT}, found {source_commit}")
    order = source / "src/readalike_prepr/data/new_article_order"
    if order.stat().st_size != ORDER_BYTES or sha256(order) != ORDER_SHA256:
        raise SystemExit("public article-order identity mismatch")
    if public.stat().st_size != PUBLIC_READY_BYTES or sha256(public) != PUBLIC_READY_SHA256:
        raise SystemExit("prior public ready-stream identity mismatch")
    if not input_path.is_file() or input_path.stat().st_size != 1_000_000_000:
        raise SystemExit("exact 1G input missing")
    if not args.compiler.is_file():
        raise SystemExit(f"missing compiler {args.compiler}")

    if not source_copy.exists():
        shutil.copytree(
            source,
            source_copy,
            ignore=shutil.ignore_patterns(".git", "cmix", "*.o"),
        )

    started = int(time.time())
    verdict = "invalid"
    decision: dict[str, object] = {
        "schema": "gamma.cmix_lex_article_order_decision.v1",
        "candidate_id": "cmix_lex_article_order_external_v1",
        "proposal_id": "cmix_lex_article_order_transfer_v1",
        "score_credit_bytes": 0,
        "source_repository": "https://github.com/blahem/cmix-lex",
        "source_commit": source_commit,
        "constants": {
            "order_bytes": ORDER_BYTES,
            "order_sha256": ORDER_SHA256,
            "public_ready_bytes": PUBLIC_READY_BYTES,
            "public_ready_sha256": PUBLIC_READY_SHA256,
            "gamma_forecast": GAMMA_FORECAST,
            "public_one_percent_threshold": PUBLIC_ONE_PERCENT_THRESHOLD,
            "design_target": DESIGN_TARGET,
            "prize_gross_required": PRIZE_GROSS_REQUIRED,
            "design_gross_required": DESIGN_GROSS_REQUIRED,
            "prize_required_bpm": PRIZE_REQUIRED_BPM,
            "design_required_bpm": DESIGN_REQUIRED_BPM,
            "sampled_bytes": SAMPLED_BYTES,
            "sample_prize_gate_bytes": SAMPLE_PRIZE_GATE,
            "sample_design_gate_bytes": SAMPLE_DESIGN_GATE,
        },
    }
    decision_path = result_dir / "decision.json"
    try:
        base_patch = patch_observation_source(source_copy)
        article_patch = patch_article_control(source_copy)
        cmix, _helper = build_observation_binaries(source_copy, args.compiler, logs)
        prepare_rss = prepare_identity(
            source_root=source,
            input_path=input_path,
            cmix=cmix,
            work=work,
            identity=identity,
            logs=logs,
        )
        identity_bytes = identity.stat().st_size
        identity_hash = sha256(identity)
        population_bytes = min(identity_bytes, PUBLIC_READY_BYTES)
        if population_bytes < SLICE_BYTES:
            raise RuntimeError("article-order common population is too small")
        rows, aggregate_gain, compare_rss = compare(
            cmix=cmix,
            work=work,
            artifacts=artifacts,
            logs=logs,
            identity=identity,
            public=public,
            population_bytes=population_bytes,
        )
        positive_slices = sum(int(row["gross_gain_bytes"]) > 0 for row in rows)
        rss_values = [
            value for value in (prepare_rss, compare_rss) if isinstance(value, int)
        ]
        peak_rss = max(rss_values) if rss_values else None
        memory_ok = peak_rss is not None and peak_rss * 1024 < 10_000_000_000
        passes = (
            aggregate_gain >= SAMPLE_PRIZE_GATE
            and positive_slices >= 2
            and memory_ok
        )
        verdict = "authorize_native_integration" if passes else "retire_transfer"
        decision.update(
            {
                "verdict": verdict,
                "observation_patch": {**base_patch, **article_patch},
                "construction": {
                    "input_bytes": input_path.stat().st_size,
                    "input_sha256": sha256(input_path),
                    "identity_ready_path": str(identity),
                    "identity_ready_bytes": identity_bytes,
                    "identity_ready_sha256": identity_hash,
                    "ready_length_delta_public_minus_identity": (
                        PUBLIC_READY_BYTES - identity_bytes
                    ),
                    "sample_common_population_bytes": population_bytes,
                    "public_ready_path": str(public),
                    "public_ready_bytes": public.stat().st_size,
                    "public_ready_sha256": PUBLIC_READY_SHA256,
                    "prepare_peak_rss_kib": prepare_rss,
                },
                "slices": rows,
                "aggregate": {
                    "identity_archive_bytes": sum(
                        int(row["identity_archive_bytes"]) for row in rows
                    ),
                    "public_archive_bytes": sum(
                        int(row["public_archive_bytes"]) for row in rows
                    ),
                    "gross_gain_bytes": aggregate_gain,
                    "gross_gain_bpm": aggregate_gain * 1_000_000 / SAMPLED_BYTES,
                    "positive_slices": positive_slices,
                    "peak_rss_kib": peak_rss,
                    "memory_ok": memory_ok,
                    "passes_prize_scale_gate": aggregate_gain >= SAMPLE_PRIZE_GATE,
                    "passes_design_scale_gate": aggregate_gain >= SAMPLE_DESIGN_GATE,
                },
                "interpretation": (
                    "Zero-credit reset-state order oracle. A pass authorizes "
                    "only exact native replay with counted order representation."
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
