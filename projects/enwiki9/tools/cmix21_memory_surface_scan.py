#!/usr/bin/env python3
"""Scan cmix21 result receipts for non-PPMD memory-surface evidence."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUT_MD = ROOT / "docs" / "cmix21_memory_surfaces.md"
CERT_PATH = ROOT / "upper_bound_certificate.json"

SCOPE_1M = 1_000_000
SCOPE_10M = 10_000_000
SCOPE_100M = 100_000_000
DECIMAL_10GB_GUARD_KIB = 10_000_000_000 // 1024

PPMD_RE = re.compile(r"ppmd(?P<cap>[0-9]+)(?P<unit>k|m)")
PAQ_RE = re.compile(r"paq(?P<level>[0-9]+)")
FXCMRCM_RE = re.compile(r"fxcmrcm(?P<value>[0-9]+)")
RCM_RE = re.compile(r"(?:^|_)rcm(?P<value>[0-9]+)(?:_|$)")
GUARD_SCOPE_RE = re.compile(r"_(?P<scope>[0-9]+).*rss_guard[.]json$")


@dataclass(frozen=True)
class ResultRow:
    path: pathlib.Path
    scope: int
    archive: int
    score: int
    determinism: bool | None


@dataclass(frozen=True)
class GuardRow:
    path: pathlib.Path
    scope: int
    limit_kib: int
    max_single_kib: int
    max_tree_kib: int
    exceeded: bool
    status: str

    @property
    def margin_kib(self) -> int:
        return self.limit_kib - self.max_single_kib

    @property
    def decimal_margin_kib(self) -> int:
        return DECIMAL_10GB_GUARD_KIB - self.max_single_kib


@dataclass
class Candidate:
    program_id: str
    knobs: dict[str, Any]
    best_prefix: ResultRow | None = None
    result_10m: ResultRow | None = None
    guards: dict[int, GuardRow] = field(default_factory=dict)


def as_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,}"


def fmt_signed(value: int | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else "-"
    return f"{sign}{abs(value):,}"


def rel(path: pathlib.Path | None) -> str:
    if path is None:
        return "n/a"
    return str(path.relative_to(ROOT))


def token_set(program_id: str) -> set[str]:
    return {token for token in program_id.split("_") if token}


def ppmd_cap_kib(program_id: str) -> int | None:
    match = PPMD_RE.search(program_id)
    if not match:
        return None
    value = int(match.group("cap"))
    return value * 1024 if match.group("unit") == "m" else value


def parse_knobs(program_id: str) -> dict[str, Any]:
    tokens = token_set(program_id)
    paq_match = PAQ_RE.search(program_id)
    fxcmrcm_match = FXCMRCM_RE.search(program_id)
    rcm_match = RCM_RE.search(program_id)
    buffer_tokens = sorted(token for token in tokens if token.startswith("buf"))
    guard_tokens = sorted(token for token in tokens if "guard" in token)
    match_tokens = sorted(token for token in tokens if token.startswith("match"))
    return {
        "ppmd_cap_kib": ppmd_cap_kib(program_id),
        "paq_level": int(paq_match.group("level")) if paq_match else None,
        "fxcmrcm": int(fxcmrcm_match.group("value")) if fxcmrcm_match else None,
        "rcm": int(rcm_match.group("value")) if rcm_match else None,
        "buffer": ",".join(buffer_tokens) if buffer_tokens else "n/a",
        "minmaps": "minmaps" in tokens,
        "guards": ",".join(guard_tokens) if guard_tokens else "n/a",
        "match": ",".join(match_tokens) if match_tokens else "n/a",
        "fxcmidx13div2": "fxcmidx13div2" in tokens,
    }


def load_result(path: pathlib.Path) -> tuple[str, ResultRow] | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    program_id = data.get("program_id")
    if not isinstance(program_id, str):
        return None
    if not program_id.startswith("cmix21_text_mmap_paq"):
        return None
    if data.get("roundtrip_ok") is not True:
        return None
    scope = as_int(data, "data_size")
    archive = as_int(data, "compressed_size")
    score = as_int(data, "hutter_score") or archive + as_int(data, "program_size")
    det = None
    if isinstance(data.get("determinism"), dict):
        value = data["determinism"].get("single_host_byte_equal")
        if isinstance(value, bool):
            det = value
    return program_id, ResultRow(path=path, scope=scope, archive=archive, score=score, determinism=det)


def load_guard(path: pathlib.Path) -> tuple[str, GuardRow] | None:
    match = GUARD_SCOPE_RE.search(path.name)
    if not match:
        return None
    program_id = path.parent.name
    if not program_id.startswith("cmix21_text_mmap_paq"):
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return program_id, GuardRow(
        path=path,
        scope=int(match.group("scope")),
        limit_kib=as_int(data, "limit_kib"),
        max_single_kib=as_int(data, "max_sampled_single_rss_kib"),
        max_tree_kib=as_int(data, "max_sampled_tree_rss_kib"),
        exceeded=data.get("rss_guard_exceeded") is True,
        status=str(data.get("status", "")),
    )


def preferred_guard(current: GuardRow | None, new: GuardRow) -> GuardRow:
    if current is None:
        return new
    current_det = "determinism" in current.path.name
    new_det = "determinism" in new.path.name
    if current_det != new_det:
        return new if new_det else current
    if new.max_single_kib > current.max_single_kib:
        return new
    return current


def load_candidates(results_dir: pathlib.Path) -> list[Candidate]:
    by_id: dict[str, Candidate] = {}
    for path in sorted(results_dir.glob("cmix21_text_mmap_paq*/*.json")):
        loaded_result = load_result(path)
        if loaded_result is not None:
            program_id, row = loaded_result
            cand = by_id.setdefault(program_id, Candidate(program_id=program_id, knobs=parse_knobs(program_id)))
            if row.scope == SCOPE_10M:
                if cand.result_10m is None or row.archive < cand.result_10m.archive:
                    cand.result_10m = row
            elif row.scope < SCOPE_10M:
                if cand.best_prefix is None or row.scope > cand.best_prefix.scope or (
                    row.scope == cand.best_prefix.scope and row.archive < cand.best_prefix.archive
                ):
                    cand.best_prefix = row
        loaded_guard = load_guard(path)
        if loaded_guard is not None:
            program_id, guard = loaded_guard
            cand = by_id.setdefault(program_id, Candidate(program_id=program_id, knobs=parse_knobs(program_id)))
            cand.guards[guard.scope] = preferred_guard(cand.guards.get(guard.scope), guard)
    return sorted(
        by_id.values(),
        key=lambda cand: (
            0 if cand.program_id == active_gate(CERT_PATH)[0] else 1,
            -(cand.best_prefix.scope if cand.best_prefix else 0),
            cand.best_prefix.archive if cand.best_prefix else 10**18,
            cand.program_id,
        ),
    )


def active_gate(cert_path: pathlib.Path = CERT_PATH) -> tuple[str | None, int | None]:
    try:
        cert = json.loads(cert_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None, None
    rows = cert.get("top_status", [])
    labels: dict[str, dict[str, Any]] = {}
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("label"), str):
                labels[row["label"]] = row
    row = labels.get("active gate") or labels.get("next gate") or labels.get("active candidate") or {}
    candidate = row.get("program_id")
    scope = row.get("scope_bytes")
    return candidate if isinstance(candidate, str) else None, scope if isinstance(scope, int) else None


def guard_status(guard: GuardRow | None) -> str:
    if guard is None:
        return "missing"
    if guard.status == "running":
        return (
            "running; "
            f"current bin {fmt_signed(guard.margin_kib)} KiB; "
            f"current dec {fmt_signed(guard.decimal_margin_kib)} KiB; "
            "terminal margin pending"
        )
    elif guard.exceeded:
        state = "fail"
    else:
        state = "pass"
    return f"{state}; bin {fmt_signed(guard.margin_kib)} KiB; dec {fmt_signed(guard.decimal_margin_kib)} KiB"


def knob_values(candidates: list[Candidate], key: str) -> str:
    values = sorted({cand.knobs.get(key) for cand in candidates if cand.knobs.get(key) not in {None, "n/a", ""}})
    if not values:
        return "n/a"
    return ", ".join(f"`{value}`" for value in values)


def render(candidates: list[Candidate]) -> str:
    active_candidate, active_scope = active_gate()
    rows = [
        cand for cand in candidates
        if cand.best_prefix is not None or cand.result_10m is not None or cand.guards
    ]
    lines = [
        "# cmix21 Memory Surface Scan",
        "",
        "Generated from saved cmix21 result JSONs and RSS guard receipts. This report",
        "is lock-safe: it does not launch compression and does not mutate candidates.",
        "",
        "Claim rule:",
        "",
        "```text",
        "Rows here identify existing evidence and missing evidence for memory surfaces.",
        "They do not prove a target result and do not replace exact gate promotion.",
        "```",
        "",
        "## Active Gate Context",
        "",
        f"- Active candidate: `{active_candidate or 'n/a'}`",
        f"- Active scope bytes: `{fmt_int(active_scope)}`",
        f"- cmix21 candidates with result or guard evidence: `{fmt_int(len(rows))}`",
        "",
        "## Observed Knob Values",
        "",
        f"- PPMD caps KiB: {knob_values(rows, 'ppmd_cap_kib')}",
        f"- PAQ levels: {knob_values(rows, 'paq_level')}",
        f"- FXCM-RCM values: {knob_values(rows, 'fxcmrcm')}",
        f"- RCM values: {knob_values(rows, 'rcm')}",
        f"- Buffer tokens: {knob_values(rows, 'buffer')}",
        f"- Guard token sets: {knob_values(rows, 'guards')}",
        f"- Match token sets: {knob_values(rows, 'match')}",
        "",
        "## Surface Evidence Rows",
        "",
        "| Candidate | PPMD KiB | PAQ | FXCM-RCM | RCM | Buffer | Guards | Latest prefix | Prefix archive | 10M archive | 10M RSS | 100M RSS |",
        "|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|",
    ]
    limited_rows = sorted(rows, key=row_sort_key)[:40]
    for cand in limited_rows:
        prefix = cand.best_prefix
        result_10m = cand.result_10m
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{cand.program_id}`",
                    fmt_int(cand.knobs.get("ppmd_cap_kib")),
                    fmt_int(cand.knobs.get("paq_level")),
                    fmt_int(cand.knobs.get("fxcmrcm")),
                    fmt_int(cand.knobs.get("rcm")),
                    str(cand.knobs.get("buffer") or "n/a"),
                    str(cand.knobs.get("guards") or "n/a"),
                    fmt_int(prefix.scope if prefix else None),
                    fmt_int(prefix.archive if prefix else None),
                    fmt_int(result_10m.archive if result_10m else None),
                    guard_status(cand.guards.get(SCOPE_10M)),
                    guard_status(cand.guards.get(SCOPE_100M)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Readout",
            "",
            "- PPMD cap is well-instrumented, but the decimal `10GB` gap is too large for PPMD-only cuts on current receipts.",
            "- Non-PPMD surfaces with existing evidence include PAQ level, FXCM-RCM depth, RCM size, buffer token, match tokens, and guard variants.",
            "- The next memory mutation after the active gate should use this scan with exact guard receipts; do not infer admissibility from names alone.",
        ]
    )
    return "\n".join(lines)


def row_sort_key(cand: Candidate) -> tuple[int, int, int, str]:
    active_candidate, _ = active_gate()
    active_rank = 0 if cand.program_id == active_candidate else 1
    prefix_scope = -(cand.best_prefix.scope if cand.best_prefix else 0)
    prefix_archive = cand.best_prefix.archive if cand.best_prefix else 10**18
    return active_rank, prefix_scope, prefix_archive, cand.program_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=pathlib.Path, default=RESULTS_DIR)
    parser.add_argument("--out", type=pathlib.Path, default=OUT_MD)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render(load_candidates(args.results_dir))
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
