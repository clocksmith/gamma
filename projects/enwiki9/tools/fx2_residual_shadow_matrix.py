#!/usr/bin/env python3
"""Generate a matrix of cached FX2 residual/SSE shadow evidence."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIRS = [
    ROOT / "results" / "fx2_residual_probe",
    ROOT / "results" / "hierarchical_retrieval_shadow",
    ROOT / "results" / "streaming_retrieval_shadow",
]
OUT_MD = ROOT / "docs" / "residual_shadow_matrix.md"


@dataclass(frozen=True)
class ShadowRow:
    path: pathlib.Path
    family: str
    model: str
    key: str
    encoded_rows: int | None
    coverage_fraction: float | None
    saved_bits: float | None
    saved_bytes: float | None
    heldout_saved_bits: float | None
    heldout_saved_bytes: float | None
    code_bytes: float | None
    constructive: bool
    verdict: str

    @property
    def best_bytes(self) -> float:
        if self.heldout_saved_bytes is not None:
            return self.heldout_saved_bytes
        if self.saved_bytes is not None:
            return self.saved_bytes
        return -math.inf

    @property
    def rel_path(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def family_name(path: pathlib.Path) -> str:
    if path.parent.name == "sweep":
        return f"{path.parent.parent.name}/sweep"
    return path.parent.name


def load_json(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    num = as_float(value)
    if num is None:
        return None
    return int(num)


def join_key(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    if isinstance(value, str):
        return value
    return "n/a"


def verdict(saved: float | None, heldout: float | None, constructive: bool) -> str:
    if constructive:
        return "constructive"
    value = heldout if heldout is not None else saved
    if value is None:
        return "incomplete"
    if value > 0:
        return "positive_shadow_only"
    if value < 0:
        return "negative_shadow"
    return "flat_shadow"


def row_from_shadow(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    exact = data.get("exact_shadow_arithmetic")
    if not isinstance(exact, dict):
        return None
    delta = exact.get("same_coder_delta") if isinstance(exact.get("same_coder_delta"), dict) else {}
    saved_bits = as_float(delta.get("saved_bits"))
    saved_bytes = as_float(delta.get("saved_bytes"))
    if saved_bits is None:
        saved_bits = as_float(exact.get("saved_bits"))
    if saved_bytes is None:
        saved_bytes = as_float(exact.get("saved_bytes"))
    heldout_bits = as_float(exact.get("heldout_saved_bits"))
    heldout_bytes = as_float(exact.get("heldout_saved_bytes"))
    counters = exact.get("row_counters") if isinstance(exact.get("row_counters"), dict) else {}
    model = data.get("model") if isinstance(data.get("model"), dict) else {}
    coverage = data.get("coverage") if isinstance(data.get("coverage"), dict) else {}
    upper = data.get("score_upper_bound") if isinstance(data.get("score_upper_bound"), dict) else {}
    constructive = upper.get("constructive_10_95_certificate") is True
    return ShadowRow(
        path=path,
        family=family_name(path),
        model=str(model.get("name") or path.stem),
        key=join_key(model.get("key_fields")),
        encoded_rows=as_int(counters.get("encoded_rows") or exact.get("encoded_rows")),
        coverage_fraction=as_float(coverage.get("coverage_fraction")),
        saved_bits=saved_bits,
        saved_bytes=saved_bytes,
        heldout_saved_bits=heldout_bits,
        heldout_saved_bytes=heldout_bytes,
        code_bytes=as_float((data.get("decoder_cost") or {}).get("patch_bytes"))
        if isinstance(data.get("decoder_cost"), dict)
        else None,
        constructive=constructive,
        verdict=verdict(saved_bytes, heldout_bytes, constructive),
    )


def row_from_gain_certificate(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    gate = data.get("gate")
    if not isinstance(gate, dict):
        return None
    cost = data.get("model_cost") if isinstance(data.get("model_cost"), dict) else {}
    constructive = gate.get("constructive_residual_certificate") is True
    saved_bits = as_float(gate.get("measured_net_gain_bits"))
    saved_bytes = as_float(gate.get("measured_net_gain_bytes"))
    return ShadowRow(
        path=path,
        family=family_name(path),
        model="residual_gain_certificate",
        key=str(gate.get("split", "n/a")),
        encoded_rows=as_int((data.get("row_counters") or {}).get("exact_rows"))
        if isinstance(data.get("row_counters"), dict)
        else None,
        coverage_fraction=as_float(gate.get("coverage_fraction")),
        saved_bits=saved_bits,
        saved_bytes=saved_bytes,
        heldout_saved_bits=None,
        heldout_saved_bytes=None,
        code_bytes=as_float(cost.get("total_code_cost_bytes")),
        constructive=constructive,
        verdict=verdict(saved_bytes, None, constructive),
    )


def best_ranked_shadow(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    ranked = data.get("shadow_ranked")
    if not isinstance(ranked, list) or not ranked:
        return None
    best_item: dict[str, Any] | None = None
    best_score = -math.inf
    for item in ranked:
        if not isinstance(item, dict):
            continue
        exact = item.get("exact_shadow_arithmetic")
        if not isinstance(exact, dict):
            continue
        score = as_float(exact.get("heldout_saved_bytes"))
        if score is None:
            score = as_float(exact.get("saved_bytes"))
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_item = item
    if best_item is None:
        return None
    exact = best_item.get("exact_shadow_arithmetic")
    model_cost = best_item.get("model_cost") if isinstance(best_item.get("model_cost"), dict) else {}
    splits = best_item.get("splits") if isinstance(best_item.get("splits"), dict) else {}
    test = splits.get("test") if isinstance(splits.get("test"), dict) else {}
    return ShadowRow(
        path=path,
        family=family_name(path),
        model=str(data.get("candidate_family", {}).get("id") if isinstance(data.get("candidate_family"), dict) else path.stem),
        key=str(best_item.get("key", "n/a")),
        encoded_rows=as_int(exact.get("encoded_rows")),
        coverage_fraction=None,
        saved_bits=as_float(exact.get("saved_bits")),
        saved_bytes=as_float(exact.get("saved_bytes")),
        heldout_saved_bits=as_float(exact.get("heldout_saved_bits") or test.get("gain_bits")),
        heldout_saved_bytes=as_float(exact.get("heldout_saved_bytes") or test.get("gain_bytes")),
        code_bytes=as_float(model_cost.get("added_code_bytes_estimate")),
        constructive=False,
        verdict=verdict(as_float(exact.get("saved_bytes")), as_float(exact.get("heldout_saved_bytes") or test.get("gain_bytes")), False),
    )


def row_from_hierarchical_retrieval(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    if data.get("mode") != "fx2_residual_hierarchical_retrieval_shadow":
        return None
    ranked = data.get("top")
    if not isinstance(ranked, list) or not ranked:
        return None
    rank_split = data.get("rank_split") if isinstance(data.get("rank_split"), str) else "test"
    best_item: dict[str, Any] | None = None
    best_score = -math.inf
    for item in ranked:
        if not isinstance(item, dict):
            continue
        splits = item.get("splits") if isinstance(item.get("splits"), dict) else {}
        split = splits.get(rank_split) if isinstance(splits.get(rank_split), dict) else {}
        score = as_float(split.get("gain_bytes"))
        if score is None:
            score = as_float(item.get("rank_projected_net_bytes_non_proof"))
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_item = item
    if best_item is None:
        return None

    splits = best_item.get("splits") if isinstance(best_item.get("splits"), dict) else {}
    split = splits.get(rank_split) if isinstance(splits.get(rank_split), dict) else {}
    all_split = splits.get("all") if isinstance(splits.get("all"), dict) else {}
    target = data.get("target") if isinstance(data.get("target"), dict) else {}
    scope_bytes = as_float(data.get("data_bytes_loaded") or target.get("scope_bytes"))
    encoded_rows = as_int(split.get("rows"))
    all_rows = as_float(all_split.get("rows"))
    coverage = None
    if scope_bytes and all_rows is not None and scope_bytes > 0:
        coverage = all_rows / (scope_bytes * 8.0)
    return ShadowRow(
        path=path,
        family="hierarchical_retrieval_shadow",
        model="causal_schema_retrieval",
        key=str(best_item.get("key", "n/a")),
        encoded_rows=encoded_rows,
        coverage_fraction=coverage,
        saved_bits=as_float(all_split.get("gain_bits")),
        saved_bytes=as_float(all_split.get("gain_bytes")),
        heldout_saved_bits=as_float(split.get("gain_bits")),
        heldout_saved_bytes=as_float(split.get("gain_bytes")),
        code_bytes=as_float(target.get("code_cost_bytes_assumed")),
        constructive=False,
        verdict=verdict(
            as_float(all_split.get("gain_bytes")),
            as_float(split.get("gain_bytes")),
            False,
        ),
    )


def row_from_streaming_retrieval(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    if data.get("receipt_type") != "streaming_retrieval_shadow":
        return None
    schema = data.get("sketch_schema") if isinstance(data.get("sketch_schema"), dict) else {}
    target = data.get("target") if isinstance(data.get("target"), dict) else {}
    scope_bytes = as_float(data.get("scope_bytes") or target.get("scope_bytes"))
    encoded_rows = as_int(data.get("encoded_rows"))
    coverage = None
    if scope_bytes and encoded_rows is not None and scope_bytes > 0:
        coverage = encoded_rows / (scope_bytes * 8.0)
    code_bytes = as_float(data.get("added_code_bytes_estimate")) or 0.0
    table_bytes = as_float(data.get("added_static_table_bytes")) or 0.0
    receipt_verdict = str(data.get("verdict") or "")
    saved_bytes = as_float(data.get("shadow_saved_bytes"))
    heldout_saved_bytes = as_float(data.get("heldout_shadow_saved_bytes"))
    if receipt_verdict == "incomplete" and heldout_saved_bytes is None:
        saved_bytes = None
    return ShadowRow(
        path=path,
        family="streaming_retrieval_shadow",
        model=str(data.get("method") or "streaming_retrieval_shadow"),
        key=(
            f"blend={schema.get('blend_ppm', 'n/a')},"
            f"support={schema.get('min_support', 'n/a')},"
            f"suffix={schema.get('suffix_len', 'n/a')},"
            f"sketch={schema.get('sketch_len', 'n/a')}"
        ),
        encoded_rows=encoded_rows,
        coverage_fraction=coverage,
        saved_bits=None,
        saved_bytes=saved_bytes,
        heldout_saved_bits=None,
        heldout_saved_bytes=heldout_saved_bytes,
        code_bytes=code_bytes + table_bytes,
        constructive=False,
        verdict=receipt_verdict or verdict(saved_bytes, heldout_saved_bytes, False),
    )


def row_from_mwcc_router(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    if data.get("method") != "mwcc_router_residual_bias_shadow":
        return None
    params = data.get("params") if isinstance(data.get("params"), dict) else {}
    key = params.get("experts")
    encoded_rows = as_int(data.get("rows"))
    return ShadowRow(
        path=path,
        family=family_name(path),
        model="mwcc_router_residual_bias_shadow",
        key=str(key) if isinstance(key, str) else "n/a",
        encoded_rows=encoded_rows,
        coverage_fraction=None,
        saved_bits=as_float(data.get("saved_bits")),
        saved_bytes=as_float(data.get("saved_bytes")),
        heldout_saved_bits=as_float(data.get("heldout_saved_bits")),
        heldout_saved_bytes=as_float(data.get("heldout_saved_bytes")),
        code_bytes=None,
        constructive=False,
        verdict=verdict(
            as_float(data.get("saved_bytes")),
            as_float(data.get("heldout_saved_bytes")),
            False,
        ),
    )


def row_from_issa_shadow(path: pathlib.Path, data: dict[str, Any]) -> ShadowRow | None:
    if data.get("method") != "issa_residual_bias_shadow":
        return None
    params = data.get("params") if isinstance(data.get("params"), dict) else {}
    best = data.get("best") if isinstance(data.get("best"), dict) else {}
    projection = best.get("projection") if isinstance(best.get("projection"), dict) else {}
    key = (
        "state_count="
        + str(params.get("state_count", "n/a"))
        + ",state_buckets="
        + str(params.get("state_buckets", "n/a"))
        + ",seed="
        + str(projection.get("seed", "n/a"))
    )
    return ShadowRow(
        path=path,
        family=family_name(path),
        model="issa_residual_bias_shadow",
        key=key,
        encoded_rows=as_int(best.get("rows") or data.get("rows_scored")),
        coverage_fraction=None,
        saved_bits=as_float(best.get("saved_bits")),
        saved_bytes=as_float(best.get("saved_bytes")),
        heldout_saved_bits=as_float(best.get("heldout_saved_bits")),
        heldout_saved_bytes=as_float(best.get("heldout_saved_bytes")),
        code_bytes=None,
        constructive=False,
        verdict=verdict(
            as_float(best.get("saved_bytes")),
            as_float(best.get("heldout_saved_bytes")),
            False,
        ),
    )


def load_rows(results_dirs: list[pathlib.Path]) -> list[ShadowRow]:
    rows: list[ShadowRow] = []
    for results_dir in results_dirs:
        if not results_dir.exists():
            continue
        for path in sorted(results_dir.rglob("*.json")):
            data = load_json(path)
            if data is None:
                continue
            for loader in (
                row_from_streaming_retrieval,
                row_from_shadow,
                row_from_gain_certificate,
                best_ranked_shadow,
                row_from_mwcc_router,
                row_from_issa_shadow,
                row_from_hierarchical_retrieval,
            ):
                row = loader(path, data)
                if row is not None:
                    rows.append(row)
                    break
    return rows


def fmt_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    if math.isinf(value) or math.isnan(value):
        return "n/a"
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:.7g}"


def fmt_int(value: int | None) -> str:
    return "n/a" if value is None else f"{value:,}"


def render(rows: list[ShadowRow]) -> str:
    sorted_rows = sorted(rows, key=lambda row: (row.constructive is not True, -row.best_bytes, row.rel_path))
    positive = [row for row in rows if row.best_bytes > 0]
    constructive = [row for row in rows if row.constructive]
    best = max(rows, key=lambda row: row.best_bytes, default=None)
    lines: list[str] = [
        "# FX2 Residual Shadow Matrix",
        "",
        "Generated from cached residual/SSE JSON receipts under `results/fx2_residual_probe/`",
        "`results/hierarchical_retrieval_shadow/`, and",
        "`results/streaming_retrieval_shadow/`.",
        "",
        "Claim rule:",
        "",
        "```text",
        "Positive shadow bytes are not a Hutter proof.",
        "A residual/SSE lane promotes only after full coverage, counted decoder bytes,",
        "roundtrip, determinism, and official accounting all pass.",
        "```",
        "",
        "## Summary",
        "",
        f"- Cached JSON receipts scanned into rows: `{len(rows)}`",
        f"- Rows with positive measured or held-out shadow bytes: `{len(positive)}`",
        f"- Constructive residual certificates: `{len(constructive)}`",
        (
            f"- Best cached shadow-only byte delta: `{fmt_float(best.best_bytes)}` from "
            f"`{best.family}` / `{best.model}`."
            if best is not None and best.best_bytes > -math.inf
            else "- Best cached shadow-only byte delta: `n/a`"
        ),
        "- Current interpretation: useful signal exists, but no cached residual row is complete enough to become a Hutter-target candidate.",
        "",
        "## Rows",
        "",
        "| Family | Model | Key | Encoded rows | Coverage | Saved bytes | Held-out saved bytes | Code bytes | Verdict | Receipt |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in sorted_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.family}`",
                    f"`{row.model}`",
                    f"`{row.key}`",
                    fmt_int(row.encoded_rows),
                    fmt_float(row.coverage_fraction),
                    fmt_float(row.saved_bytes),
                    fmt_float(row.heldout_saved_bytes),
                    fmt_float(row.code_bytes),
                    f"`{row.verdict}`",
                    f"`{row.rel_path}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Reading The Matrix",
            "",
            "- `positive_shadow_only` means the cached same-coder or held-out shadow result saved bytes, but the row still lacks full target coverage and counted decoder bytes.",
            "- `negative_shadow` means the causal correction hurt the measured shadow coder and should not be promoted as-is.",
            "- `constructive` is reserved for a full-coverage, counted-byte residual certificate. No current row has that status unless the source receipt says so.",
            "- A displayed code-byte value of `0` means the source receipt reported no extra patch/table bytes; it is not an official decompressor-size audit.",
            "- Coverage is the coverage reported by the cached source receipt. It should not be read as full `enwik9` coverage unless the receipt explicitly asserts that.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-dir",
        type=pathlib.Path,
        action="append",
        default=None,
        help="directory to scan; repeat to override the default residual directories",
    )
    parser.add_argument("--out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--check", action="store_true", help="verify output is up to date")
    args = parser.parse_args()

    rows = load_rows(args.results_dir or DEFAULT_RESULTS_DIRS)
    rendered = render(rows)
    if args.check:
        try:
            current = args.out.read_text()
        except OSError:
            print(f"missing {args.out}")
            return 1
        if current != rendered:
            print(f"stale {args.out}")
            return 1
        print(f"up_to_date {args.out}")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
