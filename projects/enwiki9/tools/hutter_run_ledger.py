#!/usr/bin/env python3
"""Generate a normalized, source-bound ledger of enwiki9 candidate runs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import research_contracts


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "docs" / "hutter_frontier.json"
OUT_JSON = ROOT / "docs" / "hutter_run_ledger.json"
OUT_MD = ROOT / "docs" / "hutter_run_ledger.md"
TIERS = {
    "idea",
    "proxy",
    "oracle",
    "causal_shadow",
    "constructive_prefix",
    "full_corpus_official",
}


def pointer_get(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer {pointer!r}")
    value = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise KeyError(pointer)
    return value


def source_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else project_root / path


def primary_run(candidate: dict[str, Any]) -> dict[str, Any]:
    scope = candidate.get("scope_bytes")
    return {
        "run_id": candidate.get("run_id") or f"{candidate['id']}__{scope or 'unscoped'}",
        "candidate_id": candidate["id"],
        "parent_candidate_id": candidate.get("parent_candidate_id"),
        "candidate_name": candidate["name"],
        "rank": candidate["rank"],
        "status": candidate["status"],
        "evidence_tier": candidate["evidence_tier"],
        "primary_frontier_run": True,
        "scope_bytes": scope,
        "offset_bytes": candidate.get("offset_bytes", 0),
        "population": candidate.get("population", "unspecified"),
        "baseline_archive_bytes": candidate.get("baseline_archive_bytes"),
        "archive_bytes": candidate.get("archive_bytes"),
        "program_bytes": candidate.get("program_bytes"),
        "incremental_program_bytes": candidate.get("incremental_program_bytes"),
        "measured_gain_bytes": candidate.get("measured_gain_bytes"),
        "gain_bytes_per_1m": candidate.get("gain_bytes_per_1m"),
        "forecast_score_bytes": candidate.get("forecast_score"),
        "roundtrip_ok": candidate.get("roundtrip_ok"),
        "determinism_ok": candidate.get("deterministic_reencode_ok"),
        "max_sampled_tree_rss_kib": candidate.get("max_sampled_tree_rss_kib"),
        "score_credit_bytes": candidate.get("score_credit_bytes", 0),
        "decision": candidate.get("decision"),
        "next_gate": candidate.get("next_gate"),
        "disqualifiers": candidate.get("disqualifiers", []),
        "source_paths": candidate.get("source_paths", []),
    }


def additional_run(candidate: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    row = {
        "run_id": run["run_id"],
        "candidate_id": candidate["id"],
        "parent_candidate_id": candidate.get("parent_candidate_id"),
        "candidate_name": candidate["name"],
        "rank": candidate["rank"],
        "status": run.get("status", candidate["status"]),
        "evidence_tier": run.get("evidence_tier", candidate["evidence_tier"]),
        "primary_frontier_run": False,
        "scope_bytes": run.get("scope_bytes"),
        "offset_bytes": run.get("offset_bytes", 0),
        "population": run.get("population", "unspecified"),
        "baseline_archive_bytes": run.get("baseline_archive_bytes"),
        "archive_bytes": run.get("archive_bytes"),
        "program_bytes": run.get("program_bytes", candidate.get("program_bytes")),
        "incremental_program_bytes": run.get("incremental_program_bytes"),
        "measured_gain_bytes": run.get("measured_gain_bytes"),
        "gain_bytes_per_1m": run.get("gain_bytes_per_1m"),
        "forecast_score_bytes": run.get("forecast_score_bytes"),
        "roundtrip_ok": run.get("roundtrip_ok"),
        "determinism_ok": run.get("determinism_ok"),
        "max_sampled_tree_rss_kib": run.get("max_sampled_tree_rss_kib"),
        "score_credit_bytes": run.get("score_credit_bytes", 0),
        "decision": run.get("decision", candidate.get("decision")),
        "next_gate": run.get("next_gate", candidate.get("next_gate")),
        "disqualifiers": run.get("disqualifiers", candidate.get("disqualifiers", [])),
        "source_paths": run.get("source_paths", []),
    }
    return row


def validate_additional_run(
    project_root: Path, candidate_id: str, raw: dict[str, Any], row: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    for field in ("run_id", "scope_bytes", "population", "source_paths"):
        if not raw.get(field):
            errors.append(f"{candidate_id}: additional run missing {field}")
    for raw_path in raw.get("source_paths", []):
        if not source_path(project_root, raw_path).is_file():
            errors.append(
                f"{candidate_id}/{raw.get('run_id')}: missing source {raw_path}"
            )
    for assertion in raw.get("metric_assertions", []):
        try:
            path = source_path(project_root, assertion["source"])
            document = json.loads(path.read_text())
            actual = pointer_get(document, assertion["pointer"])
            field = assertion["run_field"]
            expected = row.get(field)
        except (KeyError, ValueError, OSError, json.JSONDecodeError, IndexError) as exc:
            errors.append(f"{candidate_id}/{raw.get('run_id')}: invalid assertion: {exc}")
            continue
        if actual != expected:
            errors.append(
                f"{candidate_id}/{raw.get('run_id')}: {field}={expected!r} "
                f"does not match {assertion['source']}#{assertion['pointer']}={actual!r}"
            )
    return errors


def normalize_row(row: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    scope = row.get("scope_bytes")
    full_scope = target["input_bytes"]
    row["scope_percent_of_corpus"] = (
        round(scope / full_scope * 100, 7)
        if isinstance(scope, int) and scope > 0
        else None
    )
    forecast = row.get("forecast_score_bytes")
    if isinstance(forecast, int):
        row["forecast_percent"] = round(forecast / full_scope * 100, 7)
        row["forecast_margin_bytes"] = target["score_bytes"] - forecast
    else:
        row["forecast_percent"] = None
        row["forecast_margin_bytes"] = None
    return row


def build_ledger(project_root: Path, frontier: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    objective = research_contracts.objective_binding()
    target = frontier.get("target", {})
    if (
        target.get("input_bytes") != objective["corpusBytes"]
        or target.get("score_bytes") != objective["targetScoreBytes"]
    ):
        errors.append("frontier target is not the canonical enwiki9 target")
    if frontier.get("objective") != objective:
        errors.append("frontier objective binding is missing or stale")

    rows: list[dict[str, Any]] = []
    seen_run_ids: set[str] = set()
    candidates = frontier.get("candidates", [])
    candidate_ids = {candidate.get("id") for candidate in candidates}
    for candidate in candidates:
        candidate_id = candidate.get("id", "<missing>")
        parent_id = candidate.get("parent_candidate_id")
        if parent_id == candidate_id:
            errors.append(f"{candidate_id}: candidate cannot be its own parent")
        elif parent_id is not None and parent_id not in candidate_ids:
            errors.append(f"{candidate_id}: missing parent candidate {parent_id}")
        tier = candidate.get("evidence_tier")
        if tier not in TIERS:
            errors.append(f"{candidate_id}: invalid evidence tier {tier!r}")
        candidate_rows = [primary_run(candidate)]
        for raw in candidate.get("additional_runs", []):
            row = additional_run(candidate, raw)
            errors.extend(validate_additional_run(project_root, candidate_id, raw, row))
            candidate_rows.append(row)
        for row in candidate_rows:
            run_id = row["run_id"]
            if run_id in seen_run_ids:
                errors.append(f"duplicate run_id {run_id}")
            seen_run_ids.add(run_id)
            if row["evidence_tier"] in {"idea", "proxy", "oracle", "causal_shadow"} and row["score_credit_bytes"]:
                errors.append(f"{run_id}: nonconstructive run has score credit")
            baseline = row.get("baseline_archive_bytes")
            archive = row.get("archive_bytes")
            gain = row.get("measured_gain_bytes")
            scope = row.get("scope_bytes")
            rate = row.get("gain_bytes_per_1m")
            if all(isinstance(value, int) for value in (baseline, archive, gain)):
                if baseline - archive != gain:
                    errors.append(
                        f"{run_id}: archive gain mismatch: {baseline} - {archive} != {gain}"
                    )
            if (
                isinstance(scope, int)
                and scope > 0
                and isinstance(gain, (int, float))
                and isinstance(rate, (int, float))
            ):
                expected_rate = gain * 1_000_000 / scope
                if abs(expected_rate - rate) > 1e-9:
                    errors.append(
                        f"{run_id}: gain rate mismatch: {expected_rate} != {rate}"
                    )
            rows.append(normalize_row(row, target))

    for candidate in candidates:
        origin = candidate.get("id")
        current = origin
        visited: set[str] = set()
        while current is not None:
            if current in visited:
                errors.append(f"{origin}: candidate lineage contains a cycle")
                break
            visited.add(current)
            match = next((row for row in candidates if row.get("id") == current), None)
            current = match.get("parent_candidate_id") if match else None

    rows.sort(
        key=lambda row: (
            -(row["scope_bytes"] or 0),
            row["rank"],
            not row["primary_frontier_run"],
            row["run_id"],
        )
    )
    summary = {
        "run_count": len(rows),
        "candidate_count": len({row["candidate_id"] for row in rows}),
        "runs_by_scope": {
            str(key): value
            for key, value in sorted(Counter(row["scope_bytes"] for row in rows).items(), key=lambda item: (item[0] is None, item[0] or 0))
        },
        "runs_by_evidence_tier": dict(sorted(Counter(row["evidence_tier"] for row in rows).items())),
        "runs_by_status": dict(sorted(Counter(row["status"] for row in rows).items())),
    }
    ledger = {
        "schema": "enwiki9_hutter_run_ledger_v1",
        "source_frontier": "docs/hutter_frontier.json",
        "objective": objective,
        "target": target,
        "summary": summary,
        "runs": rows,
    }
    return ledger, errors


def fmt_int(value: Any) -> str:
    return "unknown" if not isinstance(value, int) else f"{value:,}"


def render_markdown(ledger: dict[str, Any]) -> str:
    target = ledger["target"]
    lines = [
        "# enwiki9 Hutter Run Ledger",
        "",
        "Generated from the validated candidate frontier. Each row is evidence only for its measured scope and tier.",
        "",
        f"- Objective: `{ledger['objective']['objectiveId']}` (`{ledger['objective']['objectiveDigest']}`).",
        f"- Target: `{target['score_bytes']:,}` bytes (`{target['score_bytes'] / target['input_bytes'] * 100:.7f}%`).",
        f"- Candidate runs indexed: `{ledger['summary']['run_count']}`.",
        f"- Candidate lineages indexed: `{ledger['summary']['candidate_count']}`.",
        "",
    ]
    scopes: list[int | None] = sorted(
        {row["scope_bytes"] for row in ledger["runs"]},
        key=lambda value: (value is None, -(value or 0)),
    )
    for scope in scopes:
        title = "Unscoped" if scope is None else f"{scope:,} Bytes"
        lines.extend(
            [
                f"## {title}",
                "",
                "| Candidate run | Tier | Status | Population | Archive | Gain | B/M | Package | Forecast | Margin | Proof |",
                "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in (item for item in ledger["runs"] if item["scope_bytes"] == scope):
            forecast = "unknown"
            if isinstance(row["forecast_score_bytes"], int):
                forecast = f"{row['forecast_score_bytes']:,} ({row['forecast_percent']:.7f}%)"
            proof_parts = []
            if row["roundtrip_ok"] is not None:
                proof_parts.append(f"RT={str(row['roundtrip_ok']).lower()}")
            if row["determinism_ok"] is not None:
                proof_parts.append(f"DET={str(row['determinism_ok']).lower()}")
            proof = ", ".join(proof_parts) or "not recorded"
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row['run_id']}`",
                        f"`{row['evidence_tier']}`",
                        f"`{row['status']}`",
                        str(row["population"]),
                        fmt_int(row["archive_bytes"]),
                        fmt_int(row["measured_gain_bytes"]),
                        "unknown" if row["gain_bytes_per_1m"] is None else f"{row['gain_bytes_per_1m']:.3f}",
                        fmt_int(row["program_bytes"]),
                        forecast,
                        fmt_int(row["forecast_margin_bytes"]),
                        proof,
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--frontier", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    frontier_path = args.frontier or project_root / "docs" / "hutter_frontier.json"
    json_out = args.json_out or project_root / "docs" / "hutter_run_ledger.json"
    markdown_out = args.markdown_out or project_root / "docs" / "hutter_run_ledger.md"
    frontier = json.loads(frontier_path.read_text())
    ledger, errors = build_ledger(project_root, frontier)
    if errors:
        for error in errors:
            print(error)
        return 1
    json_text = json.dumps(ledger, indent=2, sort_keys=False) + "\n"
    markdown_text = render_markdown(ledger)
    if args.check:
        stale = []
        for path, expected in ((json_out, json_text), (markdown_out, markdown_text)):
            try:
                current = path.read_text()
            except OSError:
                current = None
            if current != expected:
                stale.append(path)
        if stale:
            for path in stale:
                print(f"stale {path}")
            return 1
        print(f"up_to_date {json_out}")
        print(f"up_to_date {markdown_out}")
        return 0
    json_out.write_text(json_text)
    markdown_out.write_text(markdown_text)
    print(f"wrote {json_out}")
    print(f"wrote {markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
