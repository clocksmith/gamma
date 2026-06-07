#!/usr/bin/env python3
"""Run frontier-relevant enwiki9 program pipelines at 10 MB and 100 MB.

This is the empirical promotion harness for algorithm/pipeline combinations
that already exist as programs/<id>. It screens candidates on 10 MB, promotes
the best exact-roundtrip rows to 100 MB, and writes machine-readable rows plus
a compact Markdown summary.

The Pareto report follows FX2_SC.md: it separates destructive preprocessing
lanes from the raw-stream sidecar lane, records which FX2-SC concepts a program
actually implements, and computes same-scope score ledgers against a named
baseline before declaring a winner.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIB = ROOT / "lib"
sys.path.insert(0, str(LIB))
import driver  # noqa: E402

DEFAULT_DATA = ROOT / "data" / "enwik9"
DEFAULT_OUT = ROOT / "results" / "frontier_strategy_search"

DEFAULT_PROGRAMS = [
    "fx2_schema_template_only_v1",
    "fx2_geometry_sort_dictcmix_xz_min_v1",
    "fx2cmix_geometry_sort_dictcmix_xz_v1",
    "fx2cmix_wrapped_dictcmix_xz_min_v1",
    "fx2_topic_sort_dictcmix_xz_min_v1",
    "fx2_struct_top_dictcmix_xz_min_v1",
    "fx2_geometry_suffix_sort_dictcmix_xz_bcj_min_v2",
    "fx2_geometry_suffix_sort_dict3000_bcj_zlibpy_min_v1",
    "fx2_geometry_sort_dict3920_bcj_zlibpy_min_v3",
    "geometry_receipt_schema_selector_v1",
    "named_opcode_lzma2_1g_v1",
    "graph_fim_opcode_xz_selector_v4",
    "xml_skel_wc3tier_jpvi_z_lzma2_1g_v1",
    "xz_lzma2_1g",
    "baseline_lzma",
]

FX2_SC_CONCEPTS: dict[str, str] = {
    "raw_stream_preserved": "raw byte stream is not rewritten or reordered",
    "score_ledger": "same-scope archive/program/S deltas are reported",
    "schema_template_ctx": "template hash plus argument/slot coordinate",
    "soft_symbol_reduction": "value-class/URL/numeric/table soft bias contexts",
    "lexical_priming": "page-local title/ref/link/entity priming",
    "namespace_page_kind": "namespace or page-kind partitioning",
    "active_geometry_context": "page-family geometry as stream-order context",
    "reversible_geometry_sort": "physical page ordering with recovery ledger",
    "role_copy_hints": "role-local copy/match hints without explicit events",
    "shallow_grammar": "word shape/suffix/punctuation contexts in prose",
    "fixed_point_ssm": "bounded deterministic recurrent trajectory bucket",
    "custom_backend_events": "explicit literal/copy/macro event backend",
    "sse_gating": "sidecar-gated secondary symbol estimation",
    "rate_ledger": "lossless rate selection among reversible modes",
    "epsilon_safe_mask": "schema bias keeps every byte legal",
    "table_coordinates": "table depth/row/column/cell-class coordinates",
    "title_body_priming": "title token prefix state in body contexts",
    "numeric_successor": "numeric successor/delta sidecar state",
    "citation_anchor_mtf": "page-local citation name move-to-front state",
    "timestamp_model": "XML timestamp position/value-class model",
}

PROGRAM_CONCEPTS: dict[str, dict] = {
    "baseline_lzma": {
        "lane": "baseline",
        "concepts": [],
        "notes": "Stdlib LZMA baseline.",
    },
    "xz_lzma2_1g": {
        "lane": "baseline",
        "concepts": [],
        "notes": "External xz LZMA2 baseline.",
    },
    "fx2_schema_template_only_v1": {
        "lane": "fx2_sc_sidecar",
        "concepts": ["raw_stream_preserved", "schema_template_ctx"],
        "notes": "Phase 1 isolated Indirect context; no transform or hard mask.",
    },
    "fx2_structural_sidecar_v1": {
        "lane": "fx2_sc_sidecar",
        "concepts": [
            "raw_stream_preserved",
            "schema_template_ctx",
            "soft_symbol_reduction",
            "lexical_priming",
            "namespace_page_kind",
            "table_coordinates",
            "citation_anchor_mtf",
        ],
        "notes": "Existing broad sidecar stack; useful control but attribution is mixed.",
    },
    "fx2_sidecar_byte_split_direct_extra_page_match_v1": {
        "lane": "fx2_sc_sidecar",
        "concepts": [
            "raw_stream_preserved",
            "schema_template_ctx",
            "soft_symbol_reduction",
            "lexical_priming",
            "namespace_page_kind",
            "table_coordinates",
            "role_copy_hints",
            "citation_anchor_mtf",
        ],
        "notes": "Broad sidecar, byte models, direct inputs, and match contexts.",
    },
    "cmix21_sidecar_direct_page_v1": {
        "lane": "fx2_sc_sidecar",
        "concepts": [
            "raw_stream_preserved",
            "schema_template_ctx",
            "namespace_page_kind",
            "active_geometry_context",
        ],
        "notes": "cmix21 sidecar direct/page control.",
    },
    "fx2_geometry_sort_dictcmix_xz_min_v1": {
        "lane": "destructive_geometry",
        "concepts": ["reversible_geometry_sort"],
        "notes": "Best recorded 100 MB archive, but uses physical page sorting.",
    },
    "fx2_geometry_opcode_dictcmix_xz_v1": {
        "lane": "destructive_transform",
        "concepts": ["reversible_geometry_sort"],
        "notes": "Geometry sort plus opcode rewrite selector; kept out of FX2-SC sidecar lane.",
    },
    "fx2cmix_geometry_sort_dictcmix_xz_v1": {
        "lane": "destructive_geometry",
        "concepts": ["reversible_geometry_sort"],
        "notes": "Geometry sort around fx2cmix backend.",
    },
    "fx2_topic_sort_dictcmix_xz_min_v1": {
        "lane": "destructive_geometry",
        "concepts": ["reversible_geometry_sort"],
        "notes": "Topic page ordering with id-sort restoration.",
    },
    "schema_title_streams_lzma2_1g_v1": {
        "lane": "destructive_structural_lzma",
        "concepts": ["soft_symbol_reduction", "namespace_page_kind"],
        "notes": "Typed stream decomposition for LZMA2, not raw-stream sidecar.",
    },
    "ast_opcode_lzma_v1": {
        "lane": "destructive_opcode_lzma",
        "concepts": [],
        "notes": "Small syntax opcode transform; not FX2-SC compatible by itself.",
    },
    "typed_anchor_chain_ppmc_v1": {
        "lane": "custom_backend",
        "concepts": [
            "raw_stream_preserved",
            "custom_backend_events",
            "rate_ledger",
            "role_copy_hints",
            "lexical_priming",
        ],
        "notes": "Custom event backend with structural copy ideas.",
    },
    "graph_fim_opcode_xz_selector_v4": {
        "lane": "destructive_selector",
        "concepts": ["rate_ledger"],
        "notes": "Selector over structural transforms and backends.",
    },
    "geometry_receipt_schema_selector_v1": {
        "lane": "destructive_selector",
        "concepts": ["rate_ledger", "reversible_geometry_sort"],
        "notes": "Measured-union selector over existing structural programs.",
    },
}

SCHEMA_SCALE_RE = re.compile(r"^fx2_schema_template_s(\d+)_v1$")

RECORDED_CONTROLS: dict[str, dict[int, dict]] = {
    "fx2_geometry_sort_dictcmix_xz_min_v1": {
        10_000_000: {
            "compressed_size": 1_642_858,
            "program_size": 183_761,
            "hutter_score": 1_826_619,
            "roundtrip_ok": True,
            "source": "program meta inherited 10m gate",
        },
        100_000_000: {
            "compressed_size": 14_857_781,
            "program_size": 183_761,
            "hutter_score": 15_041_542,
            "roundtrip_ok": True,
            "source": "program meta inherited 100m gate",
        },
    },
}


def ensure_prefix(data_path: pathlib.Path, size: int) -> pathlib.Path:
    out = data_path.with_name(f"{data_path.name}_{size}.bin")
    if out.exists() and out.stat().st_size == size:
        return out
    with data_path.open("rb") as src, out.open("wb") as dst:
        remaining = size
        while remaining:
            chunk = src.read(min(1 << 20, remaining))
            if not chunk:
                raise SystemExit(f"{data_path} ended before {size} bytes")
            dst.write(chunk)
            remaining -= len(chunk)
    return out


def write_jsonl(path: pathlib.Path, row: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def run_one(
    program_id: str,
    scope_path: pathlib.Path,
    phase: str,
    as_limit_bytes: int | None,
) -> dict:
    prior_limit = os.environ.get("FX2_SC_AS_LIMIT_BYTES")
    if as_limit_bytes:
        os.environ["FX2_SC_AS_LIMIT_BYTES"] = str(as_limit_bytes)
    else:
        os.environ.pop("FX2_SC_AS_LIMIT_BYTES", None)
    try:
        result = driver.run(program_id, scope_path, None, False)
        result["phase"] = phase
        result["error"] = None
        if as_limit_bytes:
            result["as_limit_bytes"] = as_limit_bytes
        attach_fx2_sc_metadata(result, None)
        return result
    except Exception as exc:
        result = {
            "phase": phase,
            "program_id": program_id,
            "data_path": str(scope_path),
            "data_size": scope_path.stat().st_size if scope_path.exists() else None,
            "roundtrip_ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        if as_limit_bytes:
            result["as_limit_bytes"] = as_limit_bytes
        attach_fx2_sc_metadata(result, None)
        return result
    finally:
        if prior_limit is None:
            os.environ.pop("FX2_SC_AS_LIMIT_BYTES", None)
        else:
            os.environ["FX2_SC_AS_LIMIT_BYTES"] = prior_limit


def recorded_row(program_id: str, scope: int, phase: str) -> dict | None:
    control = RECORDED_CONTROLS.get(program_id, {}).get(scope)
    if control is None:
        return None
    row = {
        "phase": phase,
        "program_id": program_id,
        "data_size": scope,
        "data_path": f"recorded:{program_id}:{scope}",
        "compressed_size": control["compressed_size"],
        "program_size": control["program_size"],
        "hutter_score": control["hutter_score"],
        "bits_per_byte": round(control["compressed_size"] * 8 / scope, 6),
        "roundtrip_ok": bool(control.get("roundtrip_ok")),
        "error": None,
        "recorded_control": True,
        "recorded_source": control.get("source"),
    }
    attach_fx2_sc_metadata(row, None)
    return row


def attach_fx2_sc_metadata(row: dict, baseline: dict | None) -> None:
    program_id = row.get("program_id")
    meta = PROGRAM_CONCEPTS.get(program_id, {})
    schema_scale = SCHEMA_SCALE_RE.match(str(program_id or ""))
    if not meta and schema_scale:
        scale = int(schema_scale.group(1))
        meta = {
            "lane": "fx2_sc_sidecar",
            "concepts": ["raw_stream_preserved", "schema_template_ctx"],
            "notes": (
                "Generated Phase 1 schema-template-only Indirect context "
                f"with SIDECAR_SCHEMA_TEMPLATE_SCALE={scale}."
            ),
        }
    concepts = sorted(set(meta.get("concepts", [])))
    row["fx2_sc"] = {
        "lane": meta.get("lane", "unknown"),
        "concepts": concepts,
        "notes": meta.get("notes", ""),
        "raw_stream_preserved": "raw_stream_preserved" in concepts,
        "destructive_transform": meta.get("lane", "").startswith("destructive"),
    }
    if baseline and rankable(row) and rankable(baseline):
        archive_delta = baseline["compressed_size"] - row["compressed_size"]
        program_delta = row["program_size"] - baseline["program_size"]
        score_delta = baseline["hutter_score"] - row["hutter_score"]
        row["fx2_sc"]["ledger"] = {
            "baseline_program": baseline["program_id"],
            "archive_delta": archive_delta,
            "program_delta": program_delta,
            "score_delta": score_delta,
            "verdict": "PREPROCESSOR_WINS" if score_delta > 0 else "PREPROCESSOR_LOSES",
        }


def rankable(row: dict) -> bool:
    return bool(row.get("roundtrip_ok")) and row.get("hutter_score") is not None


def pareto_rows(rows: Iterable[dict]) -> list[dict]:
    valid = [row for row in rows if rankable(row)]
    frontier = []
    for row in valid:
        dominated = False
        for other in valid:
            if other is row:
                continue
            no_worse = (
                other["hutter_score"] <= row["hutter_score"]
                and other["compressed_size"] <= row["compressed_size"]
                and other["program_size"] <= row["program_size"]
            )
            strictly_better = (
                other["hutter_score"] < row["hutter_score"]
                or other["compressed_size"] < row["compressed_size"]
                or other["program_size"] < row["program_size"]
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(row)
    frontier.sort(key=lambda row: (row["hutter_score"], row["compressed_size"]))
    return unique_rows(frontier)


def unique_rows(rows: Iterable[dict]) -> list[dict]:
    seen = set()
    unique = []
    for row in rows:
        key = (
            row.get("program_id"),
            row.get("data_size"),
            row.get("hutter_score"),
            row.get("compressed_size"),
            row.get("program_size"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def concept_coverage(rows: Iterable[dict]) -> dict[str, list[str]]:
    covered: dict[str, list[str]] = {name: [] for name in FX2_SC_CONCEPTS}
    if any(row.get("fx2_sc", {}).get("ledger") for row in rows):
        covered["score_ledger"].append("frontier_strategy_search")
    for row in rows:
        if not rankable(row):
            continue
        for concept in row.get("fx2_sc", {}).get("concepts", []):
            covered.setdefault(concept, []).append(row["program_id"])
    return {k: sorted(set(v)) for k, v in covered.items()}


def summarize(rows: Iterable[dict], out_dir: pathlib.Path) -> None:
    rows = list(rows)
    scopes = sorted({row.get("data_size") for row in rows if row.get("data_size")})
    lines = [
        "# Frontier Strategy Search",
        "",
        "FX2-SC concept ledger from `FX2_SC.md` is included below. Destructive transforms may remain useful controls, but they are not counted as raw-stream FX2-SC sidecar implementations.",
        "",
        f"Tracked FX2-SC concepts: {len(FX2_SC_CONCEPTS)}. A concept marked uncovered means no measured program in this run currently implements it.",
        "",
    ]
    for scope in scopes:
        scoped = unique_rows(row for row in rows if row.get("data_size") == scope)
        valid = [row for row in scoped if rankable(row)]
        valid.sort(key=lambda row: row["hutter_score"])
        lines.append(f"## scope={scope}")
        lines.append("")
        lines.append(
            "| rank | phase | program | lane | hutter_score | archive | program_size | b/B | score_delta | ok |"
        )
        lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---|")
        for rank, row in enumerate(valid, 1):
            ledger = row.get("fx2_sc", {}).get("ledger", {})
            score_delta = ledger.get("score_delta", "")
            lines.append(
                f"| {rank} | {row['phase']} | `{row['program_id']}` | "
                f"{row.get('fx2_sc', {}).get('lane', 'unknown')} | "
                f"{row['hutter_score']} | {row['compressed_size']} | "
                f"{row['program_size']} | {row['bits_per_byte']} | "
                f"{score_delta} | "
                f"{row['roundtrip_ok']} |"
            )
        frontier = pareto_rows(valid)
        if frontier:
            lines.append("")
            lines.append("Pareto frontier:")
            for row in frontier:
                lines.append(
                    f"- `{row['program_id']}`: S={row['hutter_score']} "
                    f"archive={row['compressed_size']} program={row['program_size']} "
                    f"lane={row.get('fx2_sc', {}).get('lane', 'unknown')}"
                )
        failed = [row for row in scoped if not rankable(row)]
        if failed:
            lines.append("")
            lines.append("Failures:")
            for row in failed:
                lines.append(f"- `{row['program_id']}`: {row.get('error')}")
        lines.append("")
    coverage = concept_coverage(rows)
    lines.append("## FX2-SC Concept Coverage")
    lines.append("")
    lines.append("| concept | status | programs |")
    lines.append("|---|---|---|")
    for concept, description in FX2_SC_CONCEPTS.items():
        programs = coverage.get(concept, [])
        status = "covered" if programs else "uncovered"
        lines.append(
            f"| `{concept}` | {status} | "
            f"{', '.join(f'`{p}`' for p in programs) or description} |"
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--program", action="append", dest="programs")
    parser.add_argument("--baseline-program", default="fx2_geometry_sort_dictcmix_xz_min_v1")
    parser.add_argument("--include-recorded-controls", action="store_true")
    parser.add_argument("--promote", type=int, default=4)
    parser.add_argument("--screen-size", type=int, default=10_000_000)
    parser.add_argument("--promote-size", type=int, default=100_000_000)
    parser.add_argument("--as-limit-bytes", type=int, default=10_000_000_000)
    parser.add_argument("--summarize-existing", action="store_true")
    parser.add_argument("--merge-jsonl", action="append", type=pathlib.Path)
    args = parser.parse_args()

    jsonl = args.out_dir / "runs.jsonl"
    if args.summarize_existing or args.merge_jsonl:
        sources = args.merge_jsonl or [jsonl]
        rows = []
        for source in sources:
            if not source.exists():
                raise SystemExit(f"runs missing: {source}")
            rows.extend(json.loads(line) for line in source.read_text().splitlines() if line)
        baselines = {
            row.get("data_size"): row
            for row in rows
            if row.get("program_id") == args.baseline_program and rankable(row)
        }
        for row in rows:
            baseline = baselines.get(row.get("data_size"))
            attach_fx2_sc_metadata(row, None if row is baseline else baseline)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        with jsonl.open("w") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        summarize(rows, args.out_dir)
        print(f"[done] summary={args.out_dir / 'summary.md'} jsonl={jsonl}", flush=True)
        return 0

    if not args.data.exists():
        raise SystemExit(f"data missing: {args.data}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if jsonl.exists():
        jsonl.unlink()

    programs = args.programs or DEFAULT_PROGRAMS
    if args.baseline_program not in programs and not args.include_recorded_controls:
        programs = [args.baseline_program] + list(programs)
    screen_path = ensure_prefix(args.data, args.screen_size)
    promote_path = ensure_prefix(args.data, args.promote_size)

    rows: list[dict] = []
    baselines: dict[int, dict] = {}
    print(
        f"[frontier] screen={screen_path} promote={promote_path} "
        f"programs={len(programs)}"
    )
    if args.include_recorded_controls:
        recorded_scopes = [
            (args.screen_size, "screen_recorded"),
            (args.promote_size, "promote_recorded"),
        ]
        seen_recorded_scopes = set()
        for scope, phase in recorded_scopes:
            if scope in seen_recorded_scopes:
                continue
            seen_recorded_scopes.add(scope)
            row = recorded_row(args.baseline_program, scope, phase)
            if row:
                rows.append(row)
                write_jsonl(jsonl, row)
                baselines[scope] = row
                print(
                    f"[recorded] {args.baseline_program} scope={scope} "
                    f"S={row['hutter_score']} archive={row['compressed_size']}",
                    flush=True,
                )
    for program_id in programs:
        if args.include_recorded_controls and program_id == args.baseline_program:
            continue
        print(f"[screen] {program_id}", flush=True)
        row = run_one(program_id, screen_path, "screen", args.as_limit_bytes)
        if program_id == args.baseline_program and rankable(row):
            baselines[args.screen_size] = row
        baseline = baselines.get(args.screen_size)
        if baseline and row is not baseline:
            attach_fx2_sc_metadata(row, baseline)
        rows.append(row)
        write_jsonl(jsonl, row)
        if rankable(row):
            print(
                f"[screen] {program_id} S={row['hutter_score']} "
                f"archive={row['compressed_size']} bpb={row['bits_per_byte']} "
                f"ok={row['roundtrip_ok']}",
                flush=True,
            )
        else:
            print(f"[screen] {program_id} ERROR {row.get('error')}", flush=True)

    winners = [
        row for row in rows
        if rankable(row) and row.get("phase") == "screen" and not row.get("recorded_control")
    ]
    winners.sort(key=lambda row: row["hutter_score"])
    promoted = [row["program_id"] for row in winners[: max(0, args.promote)]]
    print(f"[promote] {promoted}", flush=True)
    for program_id in promoted:
        print(f"[promote] {program_id}", flush=True)
        row = run_one(program_id, promote_path, "promote", args.as_limit_bytes)
        if program_id == args.baseline_program and rankable(row):
            baselines[args.promote_size] = row
        baseline = baselines.get(args.promote_size)
        if baseline and row is not baseline:
            attach_fx2_sc_metadata(row, baseline)
        rows.append(row)
        write_jsonl(jsonl, row)
        if rankable(row):
            print(
                f"[promote] {program_id} S={row['hutter_score']} "
                f"archive={row['compressed_size']} bpb={row['bits_per_byte']} "
                f"ok={row['roundtrip_ok']}",
                flush=True,
            )
        else:
            print(f"[promote] {program_id} ERROR {row.get('error')}", flush=True)

    summarize(rows, args.out_dir)
    print(f"[done] summary={args.out_dir / 'summary.md'} jsonl={jsonl}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
