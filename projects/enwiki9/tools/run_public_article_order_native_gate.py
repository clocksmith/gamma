#!/usr/bin/env python3
"""Exact same-page native Gamma gate for the public cmix-lex article order."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time


IDENTITY_STREAM_BYTES = 999_988_851
IDENTITY_STREAM_SHA256 = "d8fda2925aac0c2da67672dfc2ceded02a4f4e1e13565789a33a56f7206cc634"
PUBLIC_STREAM_BYTES = 999_988_851
PUBLIC_STREAM_SHA256 = "9284d618f69dfc0adb119c64bfe0326a422d151812844a5406128fdc7a131107"
ORDER_BYTES = 1_094_862
GAMMA_FORECAST = 109_524_268
PUBLIC_ONE_PERCENT_THRESHOLD = 108_574_923
DESIGN_TARGET = 108_000_000
PRIZE_GROSS_REQUIRED = (
    GAMMA_FORECAST - PUBLIC_ONE_PERCENT_THRESHOLD + ORDER_BYTES
)
DESIGN_GROSS_REQUIRED = GAMMA_FORECAST - DESIGN_TARGET + ORDER_BYTES
TARGET_SAMPLE_BYTES = 1_000_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def index_pages(path: Path) -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    with path.open("rb") as handle:
        start: int | None = None
        digest: hashlib._Hash | None = None
        while True:
            offset = handle.tell()
            line = handle.readline()
            if not line:
                break
            stripped = line.strip()
            if start is None:
                if stripped == b"<page>":
                    start = offset
                    digest = hashlib.sha256()
                    digest.update(line)
                continue
            assert digest is not None
            digest.update(line)
            if stripped == b"</page>":
                end = handle.tell()
                pages.append(
                    {
                        "ordinal": len(pages),
                        "offset": start,
                        "length": end - start,
                        "sha256": digest.hexdigest(),
                    }
                )
                start = None
                digest = None
    if start is not None:
        raise RuntimeError(f"unterminated page in {path}")
    if not pages:
        raise RuntimeError(f"no pages found in {path}")
    return pages


def bind_public_to_identity(
    identity_pages: list[dict[str, object]],
    public_pages: list[dict[str, object]],
) -> None:
    buckets: dict[tuple[str, int], deque[int]] = defaultdict(deque)
    for page in identity_pages:
        key = (str(page["sha256"]), int(page["length"]))
        buckets[key].append(int(page["ordinal"]))
    for page in public_pages:
        key = (str(page["sha256"]), int(page["length"]))
        if not buckets[key]:
            raise RuntimeError(f"public page has no identity instance: {key}")
        page["identity_ordinal"] = buckets[key].popleft()
    leftovers = sum(len(values) for values in buckets.values())
    if leftovers:
        raise RuntimeError(f"identity multiset has {leftovers} unmatched records")


def select_forward(
    pages: list[dict[str, object]], start: int, target: int
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    total = 0
    for page in pages[start:]:
        selected.append(page)
        total += int(page["length"])
        if total >= target:
            return selected
    raise RuntimeError("forward population cannot reach target bytes")


def select_backward(
    pages: list[dict[str, object]], target: int
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    total = 0
    for page in reversed(pages):
        selected.append(page)
        total += int(page["length"])
        if total >= target:
            selected.reverse()
            return selected
    raise RuntimeError("backward population cannot reach target bytes")


def copy_pages(
    source: Path,
    pages: list[dict[str, object]],
    destination: Path,
) -> None:
    with source.open("rb") as src, destination.open("wb") as dst:
        for page in pages:
            src.seek(int(page["offset"]))
            remaining = int(page["length"])
            while remaining:
                chunk = src.read(min(1 << 20, remaining))
                if not chunk:
                    raise RuntimeError(f"short page read from {source}")
                dst.write(chunk)
                remaining -= len(chunk)


def load_parent(path: Path):
    spec = importlib.util.spec_from_file_location("article_order_parent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import parent {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "compress") or not hasattr(module, "decompress"):
        raise RuntimeError("parent lacks compress/decompress interface")
    return module


def ceil_ratio(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-stream", type=Path, required=True)
    parser.add_argument("--public-stream", type=Path, required=True)
    parser.add_argument(
        "--parent",
        type=Path,
        default=Path(
            "programs/cmix21_b2_source_closure_rawlzma2_v1/program.py"
        ),
    )
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()

    identity_stream = args.identity_stream.resolve()
    public_stream = args.public_stream.resolve()
    parent_path = args.parent.resolve()
    result_dir = args.result_dir.resolve()
    result_dir.mkdir(parents=True, exist_ok=True)
    artifacts = (
        Path("/home/x/enwiki9-nonproof/public_article_order_native_gate")
        / result_dir.name
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    decision_path = result_dir / "decision.json"
    started = int(time.time())
    verdict = "invalid"
    decision: dict[str, object] = {
        "schema": "gamma.public_article_order_native_decision.v1",
        "candidate_id": "b2_public_article_order_same_page_v1",
        "proposal_id": "public_article_order_native_transfer_v1",
        "score_credit_bytes": 0,
        "parent": "cmix21_b2_source_closure_rawlzma2_v1",
        "constants": {
            "order_bytes": ORDER_BYTES,
            "gamma_forecast": GAMMA_FORECAST,
            "public_one_percent_threshold": PUBLIC_ONE_PERCENT_THRESHOLD,
            "design_target": DESIGN_TARGET,
            "prize_gross_required": PRIZE_GROSS_REQUIRED,
            "design_gross_required": DESIGN_GROSS_REQUIRED,
            "target_population_bytes": TARGET_SAMPLE_BYTES,
        },
    }
    try:
        if (
            identity_stream.stat().st_size != IDENTITY_STREAM_BYTES
            or sha256_file(identity_stream) != IDENTITY_STREAM_SHA256
        ):
            raise RuntimeError("identity page-stream receipt mismatch")
        if (
            public_stream.stat().st_size != PUBLIC_STREAM_BYTES
            or sha256_file(public_stream) != PUBLIC_STREAM_SHA256
        ):
            raise RuntimeError("public page-stream receipt mismatch")

        identity_pages = index_pages(identity_stream)
        public_pages = index_pages(public_stream)
        if len(identity_pages) != len(public_pages):
            raise RuntimeError("page-count mismatch")
        bind_public_to_identity(identity_pages, public_pages)

        selections = [
            ("start", select_forward(public_pages, 0, TARGET_SAMPLE_BYTES)),
            (
                "middle",
                select_forward(
                    public_pages, len(public_pages) // 2, TARGET_SAMPLE_BYTES
                ),
            ),
            ("end", select_backward(public_pages, TARGET_SAMPLE_BYTES)),
        ]
        populations: list[dict[str, object]] = []
        sample_total = 0
        for name, public_selection in selections:
            identity_ordinals = sorted(
                int(page["identity_ordinal"]) for page in public_selection
            )
            identity_selection = [
                identity_pages[ordinal] for ordinal in identity_ordinals
            ]
            public_path = artifacts / f"{name}_public.bin"
            identity_path = artifacts / f"{name}_identity.bin"
            copy_pages(public_stream, public_selection, public_path)
            copy_pages(identity_stream, identity_selection, identity_path)
            if public_path.stat().st_size != identity_path.stat().st_size:
                raise RuntimeError(f"{name} population byte-count mismatch")
            public_multiset = sorted(
                (str(page["sha256"]), int(page["length"]))
                for page in public_selection
            )
            identity_multiset = sorted(
                (str(page["sha256"]), int(page["length"]))
                for page in identity_selection
            )
            if public_multiset != identity_multiset:
                raise RuntimeError(f"{name} page multiset mismatch")
            raw_bytes = public_path.stat().st_size
            sample_total += raw_bytes
            populations.append(
                {
                    "name": name,
                    "page_count": len(public_selection),
                    "raw_bytes": raw_bytes,
                    "identity_path": str(identity_path),
                    "identity_sha256": sha256_file(identity_path),
                    "public_path": str(public_path),
                    "public_sha256": sha256_file(public_path),
                    "multiset_identity": True,
                }
            )

        parent = load_parent(parent_path)
        for population in populations:
            row_start = time.monotonic()
            for variant in ("identity", "public"):
                input_path = Path(str(population[f"{variant}_path"]))
                data = input_path.read_bytes()
                archive = parent.compress(data)
                archive_path = artifacts / f"{population['name']}_{variant}.archive"
                archive_path.write_bytes(archive)
                population[f"{variant}_archive_path"] = str(archive_path)
                population[f"{variant}_archive_bytes"] = len(archive)
                population[f"{variant}_archive_sha256"] = hashlib.sha256(
                    archive
                ).hexdigest()
            population["gross_gain_bytes"] = (
                int(population["identity_archive_bytes"])
                - int(population["public_archive_bytes"])
            )
            population["first_archive_elapsed_seconds"] = (
                time.monotonic() - row_start
            )

        aggregate_gain = sum(
            int(population["gross_gain_bytes"]) for population in populations
        )
        prize_gate = ceil_ratio(
            sample_total * PRIZE_GROSS_REQUIRED, 1_000_000_000
        )
        design_gate = ceil_ratio(
            sample_total * DESIGN_GROSS_REQUIRED, 1_000_000_000
        )
        positive_populations = sum(
            int(population["gross_gain_bytes"]) > 0 for population in populations
        )
        first_archive_pass = (
            aggregate_gain >= prize_gate and positive_populations >= 2
        )
        roundtrip_pass = False
        deterministic_pass = False
        if first_archive_pass:
            roundtrip_pass = True
            deterministic_pass = True
            for population in populations:
                for variant in ("identity", "public"):
                    data = Path(str(population[f"{variant}_path"])).read_bytes()
                    archive = Path(
                        str(population[f"{variant}_archive_path"])
                    ).read_bytes()
                    decoded = parent.decompress(archive)
                    exact = decoded == data
                    population[f"{variant}_roundtrip_exact"] = exact
                    roundtrip_pass = roundtrip_pass and exact
                public_data = Path(str(population["public_path"])).read_bytes()
                second = parent.compress(public_data)
                first = Path(str(population["public_archive_path"])).read_bytes()
                exact_determinism = second == first
                population["public_deterministic_reencode"] = exact_determinism
                deterministic_pass = deterministic_pass and exact_determinism

        child_rss_kib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        memory_ok = child_rss_kib * 1024 < 10_000_000_000
        passes = (
            first_archive_pass
            and roundtrip_pass
            and deterministic_pass
            and memory_ok
        )
        verdict = "authorize_reversible_wrapper" if passes else "retire_transfer"
        decision.update(
            {
                "verdict": verdict,
                "identity": {
                    "identity_stream_bytes": IDENTITY_STREAM_BYTES,
                    "identity_stream_sha256": IDENTITY_STREAM_SHA256,
                    "public_stream_bytes": PUBLIC_STREAM_BYTES,
                    "public_stream_sha256": PUBLIC_STREAM_SHA256,
                    "page_count": len(public_pages),
                    "complete_page_multiset_identity": True,
                },
                "populations": populations,
                "aggregate": {
                    "sample_raw_bytes": sample_total,
                    "identity_archive_bytes": sum(
                        int(population["identity_archive_bytes"])
                        for population in populations
                    ),
                    "public_archive_bytes": sum(
                        int(population["public_archive_bytes"])
                        for population in populations
                    ),
                    "gross_gain_bytes": aggregate_gain,
                    "gross_gain_bpm": aggregate_gain * 1_000_000 / sample_total,
                    "prize_gate_bytes": prize_gate,
                    "design_gate_bytes": design_gate,
                    "positive_populations": positive_populations,
                    "first_archive_pass": first_archive_pass,
                    "roundtrip_pass": roundtrip_pass,
                    "deterministic_pass": deterministic_pass,
                    "child_peak_rss_kib": child_rss_kib,
                    "memory_ok": memory_ok,
                },
                "interpretation": (
                    "Zero-credit same-page native transfer gate. A pass "
                    "authorizes a reversible wrapper, not a score claim."
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
    return 0 if verdict in {"authorize_reversible_wrapper", "retire_transfer"} else 1


if __name__ == "__main__":
    sys.exit(main())

