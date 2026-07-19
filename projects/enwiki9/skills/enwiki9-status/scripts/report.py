#!/usr/bin/env python3
"""Render a validated, evidence-tiered enwiki9 Hutter frontier."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any


ALLOWED_TIERS = {
    "idea",
    "proxy",
    "oracle",
    "causal_shadow",
    "constructive_prefix",
    "full_corpus_official",
}
ALLOWED_STATUSES = {
    "active",
    "promotable",
    "retired_unchanged",
    "quarantined",
    "historical_control",
}
NONCONSTRUCTIVE_TIERS = {"idea", "proxy", "oracle", "causal_shadow"}


def find_project_root(explicit: Path | None) -> Path:
    if explicit is not None:
        root = explicit.resolve()
        if not (root / "AGENTS.md").is_file():
            raise ValueError(f"not an enwiki9 project root: {root}")
        return root
    for base in (Path.cwd(), *Path.cwd().parents):
        direct = base if base.name == "enwiki9" else base / "projects" / "enwiki9"
        if (direct / "AGENTS.md").is_file():
            return direct.resolve()
    raise ValueError("unable to locate projects/enwiki9; pass --project-root")


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def git_state(project_root: Path) -> dict[str, Any]:
    repo = project_root.parents[1]
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1"], cwd=repo, text=True
        ).splitlines()
        return {"head": head, "dirty": bool(status), "changed_paths": status}
    except (OSError, subprocess.CalledProcessError):
        return {"head": None, "dirty": None, "changed_paths": []}


def source_audit(project_root: Path, paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        resolved = path if path.is_absolute() else project_root / path
        rows.append(
            {
                "path": raw,
                "resolved": str(resolved.resolve()),
                "present": resolved.exists(),
                "bytes": resolved.stat().st_size if resolved.is_file() else None,
            }
        )
    return rows


def json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer must start with /")
    current = value
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current[token]
        elif isinstance(current, list):
            current = current[int(token)]
        else:
            raise KeyError(token)
    return current


def assertion_audit(
    project_root: Path, row: dict[str, Any], errors: list[str]
) -> list[dict[str, Any]]:
    audits: list[dict[str, Any]] = []
    for assertion in row.get("metric_assertions", []):
        source_text = assertion.get("source")
        pointer = assertion.get("pointer")
        field = assertion.get("candidate_field")
        audit = {
            "source": source_text,
            "pointer": pointer,
            "candidate_field": field,
            "pass": False,
        }
        try:
            source = Path(source_text)
            resolved = source if source.is_absolute() else project_root / source
            observed = json_pointer(load_object(resolved), pointer)
            expected = row[field]
            audit.update({"observed": observed, "expected": expected})
            audit["pass"] = observed == expected
            if not audit["pass"]:
                errors.append(
                    f"{row['id']}: {field} disagrees with {source_text}{pointer}"
                )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            audit["error"] = str(error)
            errors.append(f"{row['id']}: metric assertion could not be verified")
        audits.append(audit)
    return audits


def validate_and_normalize(
    project_root: Path,
    ledger: dict[str, Any],
    operational: dict[str, Any],
    live_observation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if ledger.get("schema") != "enwiki9_hutter_frontier_v1":
        errors.append("unsupported frontier schema")
    target = ledger.get("target", {})
    target_score = target.get("score_bytes")
    target_input = target.get("input_bytes")
    if target_score != 109_500_000 or target_input != 1_000_000_000:
        errors.append("target must be exact full enwik9 at score 109500000")
    if operational.get("target_score_10_95") != target_score:
        errors.append("operational receipt and frontier target disagree")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in ledger.get("candidates", []):
        row = dict(raw)
        candidate_id = row.get("id")
        if not isinstance(candidate_id, str) or candidate_id in seen:
            errors.append(f"missing or duplicate candidate id: {candidate_id!r}")
            continue
        seen.add(candidate_id)
        tier = row.get("evidence_tier")
        status = row.get("status")
        if tier not in ALLOWED_TIERS:
            errors.append(f"{candidate_id}: invalid evidence tier {tier!r}")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{candidate_id}: invalid status {status!r}")
        if tier in NONCONSTRUCTIVE_TIERS and row.get("score_credit_bytes", 0) != 0:
            errors.append(f"{candidate_id}: nonconstructive evidence has score credit")
        score = row.get("forecast_score")
        if score is not None:
            if not isinstance(score, int):
                errors.append(f"{candidate_id}: forecast_score must be an integer")
            else:
                row["forecast_margin_bytes"] = target_score - score
                row["forecast_debt_bytes"] = max(score - target_score, 0)
        sources = source_audit(project_root, row.get("source_paths", []))
        row["source_audit"] = sources
        if row.get("source_required", True) and (
            not sources or any(not source["present"] for source in sources)
        ):
            errors.append(f"{candidate_id}: required evidence source missing")
        row["metric_assertion_audit"] = assertion_audit(
            project_root, row, errors
        )
        normalized.append(row)

    quarantine: list[dict[str, Any]] = []
    for raw in ledger.get("quarantine", []):
        row = dict(raw)
        row["source_audit"] = source_audit(project_root, row.get("source_paths", []))
        if row.get("source_required", True) and (
            not row["source_audit"]
            or any(not source["present"] for source in row["source_audit"])
        ):
            errors.append(f"quarantine {row.get('id')}: required source missing")
        quarantine.append(row)

    canonical_id = ledger.get("canonical_best_forecast_id")
    by_id = {row["id"]: row for row in normalized}
    canonical = by_id.get(canonical_id)
    if canonical is None or canonical.get("forecast_score") is None:
        errors.append("canonical best forecast is missing or has no score")
    operational_forecast = operational.get("best_forecast", {})
    if canonical is not None and operational_forecast.get("projected_score") != canonical.get("forecast_score"):
        errors.append("canonical frontier forecast disagrees with operational receipt")

    official = operational.get("best_full_1g", {})
    official_verified = bool(
        official.get("scope_bytes") == target_input
        and official.get("roundtrip_ok") is True
        and isinstance(official.get("hutter_score"), int)
    )
    official_win = bool(
        official_verified and official["hutter_score"] <= target_score
    )
    if official_win and not operational.get("has_10_95_constructive_upper_bound"):
        errors.append("official win conflicts with operational proof flag")

    return (
        {
            "schema": "enwiki9_hutter_status_v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "target": target,
            "official": {
                "verified_full_corpus_result": official_verified,
                "won": official_win,
                "result": official,
                "distance_bytes": (
                    official["hutter_score"] - target_score
                    if official_verified
                    else None
                ),
            },
            "canonical_forecast": canonical,
            "candidates": sorted(
                normalized, key=lambda row: (row.get("rank", 1_000_000), row["id"])
            ),
            "quarantine": quarantine,
            "operational": {
                "generated_at_utc": operational.get("generated_at_utc"),
                "active_gate": operational.get("active_gate"),
                "active_processes": operational.get("active_processes"),
                "heavy_lock": operational.get("heavy_lock"),
                "operator_action": operational.get("operator_action"),
                "live_observation": live_observation,
            },
            "repository": git_state(project_root),
            "validation": {"ok": not errors, "errors": errors},
        },
        errors,
    )


def fmt_int(value: Any) -> str:
    return "unknown" if value is None else f"{int(value):,}"


def render_markdown(status: dict[str, Any]) -> str:
    official = status["official"]
    forecast = status.get("canonical_forecast") or {}
    target_score = status["target"]["score_bytes"]
    lines = ["# enwiki9 Hutter Status", "", "## Score Status", ""]
    lines.append(f"- Target score: `{fmt_int(target_score)}` bytes.")
    if official["won"]:
        lines.append(
            f"- Verified official full-1G score: "
            f"`{fmt_int(official['result']['hutter_score'])}`; target achieved."
        )
    elif official["verified_full_corpus_result"]:
        lines.append(
            f"- Verified official full-1G score: "
            f"`{fmt_int(official['result']['hutter_score'])}`; distance above target "
            f"`{fmt_int(official['distance_bytes'])}` bytes."
        )
    else:
        lines.append(
            "- Verified official full-1G score: `unknown`; no exact result exists."
        )
        lines.append("- Official distance: `unknown`.")
    forecast_score = forecast.get("forecast_score")
    forecast_debt = forecast.get("forecast_debt_bytes")
    lines.append(
        f"- Best counted forecast: `{fmt_int(forecast_score)}`; "
        f"distance above target `{fmt_int(forecast_debt)}` bytes."
    )
    active = next(
        (
            row
            for row in status["candidates"]
            if row.get("status") in {"active", "promotable"}
        ),
        None,
    )
    active_score = active.get("forecast_score") if active else None
    active_debt = active.get("forecast_debt_bytes") if active else None
    active_margin = active.get("forecast_margin_bytes") if active else None
    if active_score is None:
        lines.append("- Active candidate projection: `unknown`; not receipt-backed yet.")
    else:
        distance_label = "margin below target" if active_margin >= 0 else "distance above target"
        distance_value = active_margin if active_margin >= 0 else active_debt
        lines.append(
            f"- Active candidate provisional projection: `{fmt_int(active_score)}`; "
            f"{distance_label} `{fmt_int(distance_value)}` bytes."
        )
    live = status["operational"].get("live_observation") or {}
    if live:
        decimal_limit = live.get("official_decimal_limit_kib")
        single_rss = live.get("max_sampled_single_rss_kib")
        decimal_margin = (
            decimal_limit - single_rss
            if isinstance(decimal_limit, int) and isinstance(single_rss, int)
            else None
        )
        lines.append(
            f"- Live gate: `{live.get('candidate', 'unknown')}` at scope "
            f"`{fmt_int(live.get('scope_bytes'))}`; progress "
            f"`{live.get('progress_percent', 'unknown')}%`; guard "
            f"`{live.get('guard_status', 'unknown')}`; terminal "
            f"`{bool(live.get('terminal'))}`."
        )
        lines.append(
            f"- Live RSS: process-tree `{fmt_int(live.get('max_sampled_tree_rss_kib'))}` KiB; "
            f"decimal single-process margin `{fmt_int(decimal_margin)}` KiB; "
            f"breach `{bool(live.get('rss_guard_exceeded'))}`."
        )
    lines.extend(
        [
            "",
            "## Canonical Counted Forecast",
            "",
            (
                f"- `{forecast.get('name', 'unknown')}`: score "
                f"`{fmt_int(forecast.get('forecast_score'))}`, margin "
                f"`{fmt_int(forecast.get('forecast_margin_bytes'))}` bytes "
                "(positive is below target)."
            ),
            f"- Evidence: `{forecast.get('evidence_tier', 'unknown')}`; status `{forecast.get('status', 'unknown')}`.",
            f"- Decision: {forecast.get('decision', 'unknown')}",
            "",
            "## Candidate Frontier",
            "",
            "| Rank | Candidate | Tier | Status | Forecast | Margin | Measured Gain | Next Gate |",
            "|---:|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in status["candidates"]:
        measured = row.get("gain_bytes_per_1m")
        measured_text = f"{measured:,.3f} B/M" if isinstance(measured, (int, float)) else "n/a"
        lines.append(
            f"| {row.get('rank', '')} | {row['name']} | `{row['evidence_tier']}` | "
            f"`{row['status']}` | {fmt_int(row.get('forecast_score'))} | "
            f"{fmt_int(row.get('forecast_margin_bytes'))} | {measured_text} | "
            f"{row.get('next_gate', '')} |"
        )
    lines.extend(["", "## Live State", ""])
    lock = status["operational"].get("heavy_lock") or {}
    processes = status["operational"].get("active_processes") or {}
    lines.append(f"- Heavy lock held: `{bool(lock.get('held'))}`.")
    lines.append(
        f"- Active scorer observed: `{bool(processes.get('active_scorer_observed'))}`."
    )
    lines.extend(["", "## Quarantine", ""])
    if status["quarantine"]:
        for row in status["quarantine"]:
            lines.append(f"- `{row['id']}`: {row['reason']}")
    else:
        lines.append("- None recorded.")
    errors = status["validation"]["errors"]
    lines.extend(["", "## Validation", ""])
    lines.append(f"- Source and arithmetic validation: `{'PASS' if not errors else 'FAIL'}`.")
    for error in errors:
        lines.append(f"- {error}")
    lines.extend(
        [
            "",
            "Only an exact 1,000,000,000-byte replay with complete accounting, "
            "roundtrip, and score at or below 109,500,000 is a win.",
        ]
    )
    if official["won"]:
        continuation = (
            "Hutter target achieved. Preserve the exact proof, reproduce it from "
            "the counted package, and complete submission packaging."
        )
    else:
        active = next(
            (
                row
                for row in status["candidates"]
                if row.get("status") in {"active", "promotable"}
            ),
            None,
        )
        next_gate = active.get("next_gate") if active else None
        continuation = "Continue toward the Hutter Prize."
        if next_gate:
            continuation += f" Highest-value next gate: {next_gate}"
    lines.extend(["", "## Continue", "", continuation, ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--operational-status", type=Path)
    parser.add_argument("--live-observation", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = find_project_root(args.project_root)
    ledger_path = args.ledger or root / "docs" / "hutter_frontier.json"
    operational_path = (
        args.operational_status or root / "docs" / "status_receipt.json"
    )
    live_observation = (
        load_object(args.live_observation)
        if args.live_observation is not None
        else None
    )
    status, errors = validate_and_normalize(
        root,
        load_object(ledger_path),
        load_object(operational_path),
        live_observation,
    )
    markdown = render_markdown(status)
    encoded = json.dumps(status, indent=2, sort_keys=True) + "\n"
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(encoded)
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown)
    print(encoded if args.format == "json" else markdown, end="")
    return 1 if args.strict and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
