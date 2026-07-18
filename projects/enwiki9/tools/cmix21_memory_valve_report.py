#!/usr/bin/env python3
"""Generate the cmix21 PPMD memory-valve report from saved receipts."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUT_MD = ROOT / "docs" / "cmix21_memory_valves.md"
CERT_PATH = ROOT / "upper_bound_certificate.json"
SCOPE_10M = 10_000_000
SCOPE_100M = 100_000_000
SCOPE_1M = 1_000_000
DECIMAL_10GB_GUARD_KIB = 10_000_000_000 // 1024
PPMD_RE = re.compile(r"cmix21_text_mmap_paq5_ppmd(?P<cap>[0-9]+)(?P<unit>k|m)_.*fxcmrcm20_.*_v1$")
GUARD_SCOPE_RE = re.compile(r"_(?P<scope>[0-9]+).*rss_guard[.]json$")


@dataclass(frozen=True)
class ResultRow:
    path: pathlib.Path
    scope: int
    archive: int
    program: int
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
    def tree_margin_kib(self) -> int:
        return self.limit_kib - self.max_tree_kib

    @property
    def decimal_margin_kib(self) -> int:
        return DECIMAL_10GB_GUARD_KIB - self.max_single_kib

    @property
    def decimal_tree_margin_kib(self) -> int:
        return DECIMAL_10GB_GUARD_KIB - self.max_tree_kib


@dataclass
class Candidate:
    program_id: str
    cap_kib: int
    result_pre10m: ResultRow | None = None
    result_10m: ResultRow | None = None
    guard_1m: GuardRow | None = None
    guard_10m: GuardRow | None = None
    guard_100m: GuardRow | None = None


def as_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def cap_kib(program_id: str) -> int | None:
    match = PPMD_RE.match(program_id)
    if not match:
        return None
    value = int(match.group("cap"))
    if match.group("unit") == "m":
        return value * 1024
    return value


def load_result(path: pathlib.Path) -> tuple[str, ResultRow] | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    program_id = data.get("program_id")
    if not isinstance(program_id, str):
        return None
    scope = as_int(data, "data_size")
    if scope <= 0:
        return None
    if data.get("roundtrip_ok") is not True:
        return None
    det = None
    if isinstance(data.get("determinism"), dict):
        value = data["determinism"].get("single_host_byte_equal")
        if isinstance(value, bool):
            det = value
    archive = as_int(data, "compressed_size")
    program = as_int(data, "program_size")
    score = as_int(data, "hutter_score") or archive + program
    return program_id, ResultRow(path=path, scope=scope, archive=archive, program=program, score=score, determinism=det)


def load_guard(path: pathlib.Path) -> GuardRow | None:
    match = GUARD_SCOPE_RE.search(path.name)
    if not match:
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return GuardRow(
        path=path,
        scope=int(match.group("scope")),
        limit_kib=as_int(data, "limit_kib"),
        max_single_kib=as_int(data, "max_sampled_single_rss_kib"),
        max_tree_kib=as_int(data, "max_sampled_tree_rss_kib"),
        exceeded=data.get("rss_guard_exceeded") is True,
        status=str(data.get("status", "")),
    )


def load_candidates(results_dir: pathlib.Path) -> list[Candidate]:
    by_id: dict[str, Candidate] = {}
    for result_path in sorted(results_dir.glob("cmix21_text_mmap_paq5_ppmd*fxcmrcm20*/*.json")):
        program_id = result_path.parent.name
        cap = cap_kib(program_id)
        if cap is None:
            continue
        cand = by_id.setdefault(program_id, Candidate(program_id=program_id, cap_kib=cap))
        loaded_result = load_result(result_path)
        if loaded_result is not None:
            _, row = loaded_result
            if row.scope == SCOPE_10M:
                current = cand.result_10m
                if current is None or row.archive < current.archive:
                    cand.result_10m = row
            elif row.scope < SCOPE_10M:
                current = cand.result_pre10m
                if current is None or row.scope > current.scope or (
                    row.scope == current.scope and row.archive < current.archive
                ):
                    cand.result_pre10m = row
        guard = load_guard(result_path)
        if guard is not None:
            if guard.scope == SCOPE_1M:
                cand.guard_1m = preferred_guard(cand.guard_1m, guard)
            elif guard.scope == SCOPE_10M:
                cand.guard_10m = preferred_guard(cand.guard_10m, guard)
            elif guard.scope == SCOPE_100M:
                cand.guard_100m = preferred_guard(cand.guard_100m, guard)
    evidence_bearing = [
        cand
        for cand in by_id.values()
        if cand.result_pre10m is not None
        or cand.result_10m is not None
        or cand.guard_1m is not None
        or cand.guard_10m is not None
        or cand.guard_100m is not None
    ]
    return sorted(evidence_bearing, key=lambda cand: cand.cap_kib, reverse=True)


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


def fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,}"


def fmt_float(value: float | None) -> str:
    if value is None or math.isnan(value) or math.isinf(value):
        return "n/a"
    return f"{value:.7g}"


def fmt_signed_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else "-"
    return f"{sign}{abs(value):,}"


def rel(path: pathlib.Path | None) -> str:
    if path is None:
        return "n/a"
    return str(path.relative_to(ROOT))


def guard_status(guard: GuardRow | None) -> str:
    if guard is None:
        return "missing"
    tree_note = ""
    if guard.max_tree_kib > 0 and guard.tree_margin_kib < 0:
        tree_note = f"; tree {fmt_int(-guard.tree_margin_kib)} KiB over"
    if guard.status == "running":
        return "rss running (terminal margin pending)"
    if guard.exceeded:
        return f"rss fail ({fmt_int(-guard.margin_kib)} KiB over{tree_note})"
    return f"rss pass ({fmt_int(guard.margin_kib)} KiB margin{tree_note})"


def decimal_guard_status(guard: GuardRow | None) -> str:
    if guard is None:
        return "missing"
    if guard.status == "running":
        return "running (terminal margin pending)"
    state = "running" if guard.status == "running" else "over" if guard.decimal_margin_kib < 0 else "within"
    if guard.decimal_margin_kib < 0:
        single = f"{fmt_int(-guard.decimal_margin_kib)} KiB over"
    else:
        single = f"{fmt_int(guard.decimal_margin_kib)} KiB margin"
    tree_note = ""
    if guard.max_tree_kib > 0:
        if guard.decimal_tree_margin_kib < 0:
            tree_note = f"; tree {fmt_int(-guard.decimal_tree_margin_kib)} KiB over"
        else:
            tree_note = f"; tree {fmt_int(guard.decimal_tree_margin_kib)} KiB margin"
    return f"{state} ({single}{tree_note})"


def load_active_gate(cert_path: pathlib.Path = CERT_PATH) -> tuple[str | None, int | None]:
    try:
        cert = json.loads(cert_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None, None
    labels: dict[str, dict[str, Any]] = {}
    rows = cert.get("top_status", [])
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("label"), str):
                labels[row["label"]] = row
    row = labels.get("active gate") or labels.get("next gate") or labels.get("active candidate") or {}
    candidate = row.get("program_id")
    scope = row.get("scope_bytes")
    return (candidate if isinstance(candidate, str) else None, scope if isinstance(scope, int) else None)


def render(candidates: list[Candidate]) -> str:
    active_gate = load_active_gate()
    measured = [cand for cand in candidates if cand.result_10m is not None]
    lines: list[str] = [
        "# cmix21 PPMD Memory-Valve Report",
        "",
        "Generated from saved result JSONs and RSS guard receipts.",
        "",
        "Claim rule:",
        "",
        "```text",
        "This report measures one memory surface: the PPMD cap.",
        "Rows are exact only for the measured scope.",
        "A 100M RSS pass would still not prove a full 1G target result.",
        "```",
        "",
        "## Candidate Ladder",
        "",
        "| PPMD cap KiB | Candidate | Latest sub-10M scope | Latest sub-10M score | 1M RSS | 10M archive | 10M score | 10M determinism | 10M RSS | 100M RSS | 10M result |",
        "|---:|---|---:|---:|---|---:|---:|---|---|---|---|",
    ]
    for cand in candidates:
        result = cand.result_10m
        pre = cand.result_pre10m
        if pre is None:
            pre_scope = pre_score = "n/a"
        else:
            pre_scope = fmt_int(pre.scope)
            pre_score = fmt_int(pre.score)
        if result is None:
            archive = score = "n/a"
            det = "n/a"
            result_path = "n/a"
        else:
            archive = fmt_int(result.archive)
            score = fmt_int(result.score)
            det = "true" if result.determinism is True else "false" if result.determinism is False else "not recorded"
            result_path = f"`{rel(result.path)}`"
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt_int(cand.cap_kib),
                    f"`{cand.program_id}`",
                    pre_scope,
                    pre_score,
                    guard_status(cand.guard_1m),
                    archive,
                    score,
                    det,
                    guard_status(cand.guard_10m),
                    guard_status(cand.guard_100m),
                    result_path,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Decimal 10GB Risk",
            "",
            "The local runner enforces the binary `10GiB` single-process guard. This table",
            "recomputes the same receipts against a stricter decimal `10GB` ceiling:",
            "",
            "```text",
            f"decimal_10gb_guard_kib = {fmt_int(DECIMAL_10GB_GUARD_KIB)}",
            "```",
            "",
            "| PPMD cap KiB | Candidate | 1M decimal RSS | 10M decimal RSS | 100M decimal RSS |",
            "|---:|---|---|---|---|",
        ]
    )
    for cand in candidates:
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt_int(cand.cap_kib),
                    f"`{cand.program_id}`",
                    decimal_guard_status(cand.guard_1m),
                    decimal_guard_status(cand.guard_10m),
                    decimal_guard_status(cand.guard_100m),
                ]
            )
            + " |"
        )

    lines.extend(ppmd_decimal_feasibility_section(candidates, active_gate))

    lines.extend(
        [
            "",
            "## Adjacent Archive Delta",
            "",
            "| High cap KiB | Low cap KiB | Archive delta at 10M | Cap cut KiB | Bytes per KiB | Verdict |",
            "|---:|---:|---:|---:|---:|---|",
        ]
    )
    for high, low in zip(measured, measured[1:]):
        assert high.result_10m is not None
        assert low.result_10m is not None
        cap_cut = high.cap_kib - low.cap_kib
        penalty = low.result_10m.archive - high.result_10m.archive
        per_kib = penalty / cap_cut if cap_cut else math.inf
        if low.guard_100m is None:
            verdict = "await 100M receipt"
        elif low.guard_100m.status == "running":
            verdict = "100M RSS gate running"
        elif low.guard_100m.exceeded:
            verdict = "lower cap still failed 100M RSS"
        else:
            verdict = "lower cap passed recorded 100M RSS"
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt_int(high.cap_kib),
                    fmt_int(low.cap_kib),
                    fmt_int(penalty),
                    fmt_int(cap_cut),
                    fmt_float(per_kib),
                    verdict,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Current Read",
            "",
            current_read(candidates, active_gate),
            "",
        ]
    )
    return "\n".join(lines)


def ppmd_decimal_feasibility_section(
    candidates: list[Candidate],
    active_gate: tuple[str | None, int | None],
) -> list[str]:
    rows = [
        cand
        for cand in candidates
        if cand.guard_10m is not None and cand.guard_10m.max_single_kib > 0
        and "_fxcmidx13div2_" in cand.program_id
    ]
    active_candidate, active_scope = active_gate
    active = next((cand for cand in rows if cand.program_id == active_candidate), None)
    if active is None:
        active = next((cand for cand in rows if guard_is_running(cand.guard_10m)), None)
    if active is None:
        active = next((cand for cand in rows if cand.guard_10m is not None), None)

    lines = [
        "",
        "## PPMD-Only Decimal Feasibility",
        "",
        "This section asks whether the measured PPMD cap ladder alone can close the",
        "decimal `10GB` memory gap. It uses `10M` single-process RSS guard receipts",
        "when those receipts are available.",
        "",
    ]
    if len(rows) < 2 or active is None or active.guard_10m is None:
        lines.append("- Not enough `10M` guard receipts exist to estimate a PPMD-only memory slope.")
        return lines

    highest_cap = max(rows, key=lambda cand: cand.cap_kib)
    lowest_cap = min(rows, key=lambda cand: cand.cap_kib)
    assert highest_cap.guard_10m is not None
    assert lowest_cap.guard_10m is not None
    cap_span_kib = highest_cap.cap_kib - lowest_cap.cap_kib
    rss_drop_kib = highest_cap.guard_10m.max_single_kib - lowest_cap.guard_10m.max_single_kib
    slope = (rss_drop_kib / cap_span_kib) if cap_span_kib > 0 else math.nan
    active_decimal_over_kib = -active.guard_10m.decimal_margin_kib if active.guard_10m.decimal_margin_kib < 0 else 0
    required_cap_cut: int | None
    projected_cap: int | None
    if slope > 0:
        required_cap_cut = math.ceil(active_decimal_over_kib / slope)
        projected_cap = active.cap_kib - required_cap_cut
    else:
        required_cap_cut = None
        projected_cap = None

    lines.extend(
        [
            f"- Active/reference cap: `{short_cap(active.program_id)}` at `{fmt_int(active.cap_kib)}` KiB.",
            f"- Active/reference `10M` max single RSS: `{fmt_int(active.guard_10m.max_single_kib)}` KiB.",
            f"- Active/reference decimal `10GB` margin: `{fmt_signed_int(active.guard_10m.decimal_margin_kib)}` KiB.",
            f"- Observed cap span: `{fmt_int(highest_cap.cap_kib)}` -> `{fmt_int(lowest_cap.cap_kib)}` KiB.",
            f"- Observed RSS drop across that span: `{fmt_signed_int(rss_drop_kib)}` KiB.",
            f"- Observed RSS drop per KiB cap cut: `{fmt_float(slope)}` KiB/KiB.",
        ]
    )
    if required_cap_cut is None or projected_cap is None:
        lines.append(
            "- PPMD-only feasibility verdict: `not feasible`; observed RSS did not "
            "decrease across the measured cap span, so decimal admissibility needs "
            "another memory surface or an official accounting decision that accepts "
            "binary `10GiB`."
        )
    elif projected_cap <= 0:
        lines.extend(
            [
                f"- PPMD-only cap cut needed for decimal `10GB`: `{fmt_int(required_cap_cut)}` KiB.",
                f"- Projected PPMD cap after that cut: `{fmt_signed_int(projected_cap)}` KiB.",
                "- PPMD-only feasibility verdict: `not feasible`; decimal admissibility needs another memory surface or an official accounting decision that accepts binary `10GiB`.",
            ]
        )
    else:
        lines.extend(
            [
                f"- PPMD-only cap cut needed for decimal `10GB`: `{fmt_int(required_cap_cut)}` KiB.",
                f"- Projected PPMD cap after that cut: `{fmt_int(projected_cap)}` KiB.",
                "- PPMD-only feasibility verdict: `possible by slope`; validate with exact gates before promotion.",
            ]
        )
    if active_scope is not None:
        lines.append(f"- Certificate active scope at render time: `{fmt_int(active_scope)}` bytes.")
    return lines


def current_read(candidates: list[Candidate], active_gate: tuple[str | None, int | None]) -> str:
    measured = [cand for cand in candidates if cand.result_10m is not None]
    restart_candidates = [cand for cand in candidates if cand_has_pre10m_without_10m(cand)]
    active_candidate, active_scope = active_gate
    active_known = next((cand for cand in candidates if cand.program_id == active_candidate), None)
    active_restart = next((cand for cand in restart_candidates if cand.program_id == active_candidate), None)
    if active_restart is None:
        active_restart = next((cand for cand in restart_candidates if guard_is_running(cand.guard_10m)), None)
    if active_restart is None:
        active_restart = next((cand for cand in restart_candidates if guard_is_running(cand.guard_1m)), None)
    if active_restart is None:
        active_restart = next(iter(sorted(restart_candidates, key=lambda item: item.cap_kib)), None)
    lines: list[str] = []
    if measured:
        best_archive = min(measured, key=lambda cand: cand.result_10m.archive if cand.result_10m else math.inf)
        assert best_archive.result_10m is not None
        lines.append(
            f"- `{short_cap(best_archive.program_id)}` has the best exact `10M` archive in this ladder: "
            f"`{fmt_int(best_archive.result_10m.archive)}`."
        )
    for cand in measured:
        if cand.guard_100m is not None and cand.guard_100m.exceeded:
            decimal_note = ""
            if cand.guard_100m.decimal_margin_kib < 0:
                decimal_note = f" Decimal `10GB` overage would be `{fmt_int(-cand.guard_100m.decimal_margin_kib)}` KiB."
            lines.append(
                f"- `{short_cap(cand.program_id)}` has exact `10M` replay evidence but failed recorded `100M` RSS "
                f"by `{fmt_int(-cand.guard_100m.margin_kib)}` KiB.{decimal_note}"
            )
    lines.extend(same_cap_historical_notes(candidates))
    if active_known is not None and active_scope is not None:
        gate_guard = {
            SCOPE_1M: active_known.guard_1m,
            SCOPE_10M: active_known.guard_10m,
            SCOPE_100M: active_known.guard_100m,
        }.get(active_scope)
        if active_known.result_10m is not None:
            lines.append(
                f"- `{short_cap(active_known.program_id)}` is the active promotion lane: exact `10M` "
                f"archive `{fmt_int(active_known.result_10m.archive)}`, score "
                f"`{fmt_int(active_known.result_10m.score)}`; active gate is "
                f"`{fmt_int(active_scope)}` bytes with RSS status {guard_status(gate_guard)}."
            )
            if (
                gate_guard is not None
                and gate_guard.status != "running"
                and gate_guard.decimal_margin_kib < 0
            ):
                lines.append(
                    f"- `{short_cap(active_known.program_id)}` is over the stricter decimal `10GB` read "
                    f"by `{fmt_int(-gate_guard.decimal_margin_kib)}` KiB on the same guard receipt."
                )
            lines.extend(same_cap_successor_note(candidates, active_known))
            lines.append("- The next mutation should wait until this active promotion gate records a terminal receipt.")
            return "\n".join(lines)
        if gate_guard is not None and gate_guard.status == "running":
            lines.append(
                f"- `{short_cap(active_known.program_id)}` is the active restarted ladder: active gate is "
                f"`{fmt_int(active_scope)}` bytes with RSS status {guard_status(gate_guard)}."
            )
            if gate_guard.decimal_margin_kib < 0:
                lines.append(
                    f"- `{short_cap(active_known.program_id)}` is over the stricter decimal `10GB` read "
                    f"by `{fmt_int(-gate_guard.decimal_margin_kib)}` KiB on the live guard receipt."
                )
            lines.extend(same_cap_successor_note(candidates, active_known))
            lines.append("- The next mutation should wait until this live guard records a terminal receipt.")
            return "\n".join(lines)
    if active_restart is not None and active_restart.result_pre10m is not None:
        pre = active_restart.result_pre10m
        active_note = ""
        if active_restart.program_id == active_candidate and active_scope is not None:
            active_note = f" Certificate active gate is `{fmt_int(active_scope)}` bytes."
        gate_guard = active_restart.guard_10m if active_scope == SCOPE_10M else active_restart.guard_1m
        lines.append(
            f"- `{short_cap(active_restart.program_id)}` is the active restarted ladder: latest exact prefix "
            f"`{fmt_int(pre.scope)}` scored `{fmt_int(pre.score)}`; active gate RSS status is "
            f"{guard_status(gate_guard)}.{active_note}"
        )
        if (
            gate_guard is not None
            and gate_guard.status != "running"
            and gate_guard.decimal_margin_kib < 0
        ):
            lines.append(
                f"- `{short_cap(active_restart.program_id)}` is over the stricter decimal `10GB` read "
                f"by `{fmt_int(-gate_guard.decimal_margin_kib)}` KiB on the same guard receipt."
            )
        lines.extend(same_cap_successor_note(candidates, active_restart))
        lines.append("- The next mutation should wait until the active restarted ladder records its current gate.")
    else:
        lines.append(
            "- No certificate active gate exists. Select the next mutation from recorded "
            "cumulative archive economics before assigning a new candidate identity."
        )
    return "\n".join(lines)


def same_cap_successor_note(candidates: list[Candidate], active: Candidate) -> list[str]:
    lower_cap = active.cap_kib
    same_cap = [
        cand
        for cand in candidates
        if cand.cap_kib == lower_cap and cand.program_id != active.program_id
    ]
    if not same_cap:
        return []
    aliases = ", ".join(f"`{short_cap(cand.program_id)}`" for cand in same_cap)
    return [
        f"- The next lower cap `{fmt_int(lower_cap)}` KiB already has historical package rows ({aliases}). "
        "A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates."
    ]


def same_cap_historical_notes(candidates: list[Candidate]) -> list[str]:
    by_cap: dict[int, list[Candidate]] = {}
    for cand in candidates:
        by_cap.setdefault(cand.cap_kib, []).append(cand)
    notes: list[str] = []
    for cap, rows in sorted(by_cap.items(), reverse=True):
        if len(rows) < 2:
            continue
        short_rows = [(cand, short_cap(cand.program_id)) for cand in rows]
        historical = [short for _cand, short in short_rows if short.endswith("m")]
        if historical:
            aliases = ", ".join(f"`{short}`" for short in historical)
        else:
            aliases = ", ".join(f"`{short}`" for _cand, short in short_rows)
        notes.append(
            f"- The next lower cap `{fmt_int(cap)}` KiB already has historical package rows ({aliases}). "
            "A newly packaged same-cap candidate is a separate evidence lineage and must restart prefix gates."
        )
    return notes


def cand_has_pre10m_without_10m(cand: Candidate) -> bool:
    return cand.result_10m is None and (
        cand.result_pre10m is not None
        or cand.guard_1m is not None
        or cand.guard_10m is not None
    )


def guard_is_running(guard: GuardRow | None) -> bool:
    return guard is not None and guard.status == "running"


def short_cap(program_id: str) -> str:
    match = PPMD_RE.match(program_id)
    if not match:
        return program_id
    return f"ppmd{match.group('cap')}{match.group('unit')}"


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
