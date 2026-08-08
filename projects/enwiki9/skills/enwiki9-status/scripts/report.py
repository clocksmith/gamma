#!/usr/bin/env python3
"""Render a validated, evidence-tiered enwiki9 Hutter frontier."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from pathlib import Path
import subprocess
import shlex
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


def _scope_from_label_suffix(raw_label: str) -> int | None:
    match = re.search(r"_(\d+)([kmg])?_determinism$", raw_label)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if unit is None:
        return value
    if unit == "k":
        return value * 1_000
    if unit == "m":
        return value * 1_000_000
    if unit == "g":
        return value * 1_000_000_000
    return None


def _canonical_candidate_from_label(raw_label: str) -> str:
    return re.sub(r"_\d+(?:[kmg])?_determinism$", "", raw_label)


def _read_live_guard_row(project_root: Path) -> dict[str, Any] | None:
    """Recover the running guard process and its live command state."""

    proc = subprocess.run(
        ["pgrep", "-af", "run_with_rss_guard.py|projects/enwiki9/lib/driver.py"],
        cwd=project_root.parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    best: dict[str, Any] | None = None
    for line in proc.stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        pid_text, raw_args = parts
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if "run_with_rss_guard.py" not in raw_args:
            continue
        try:
            args = shlex.split(raw_args)
        except ValueError:
            args = raw_args.split()
        if "--guard-json" not in args or "--label" not in args or "--" not in args:
            continue
        guard_index = args.index("--guard-json")
        label_index = args.index("--label")
        dash_index = args.index("--")
        if (
            guard_index + 1 >= len(args)
            or label_index + 1 >= len(args)
            or dash_index + 1 >= len(args)
        ):
            continue
        guard_path = args[guard_index + 1]
        label = args[label_index + 1]
        command = args[dash_index + 1 :]
        candidate = None
        scope = None
        check_determinism = "--check-determinism" in command
        driver_index = next(
            (
                index
                for index, token in enumerate(command)
                if token.endswith("projects/enwiki9/lib/driver.py")
            ),
            None,
        )
        if driver_index is not None:
            if driver_index + 1 < len(command):
                candidate = command[driver_index + 1]
            if "--limit" in command:
                idx = command.index("--limit")
                if idx + 1 < len(command):
                    try:
                        scope = int(command[idx + 1])
                    except ValueError:
                        scope = None
        if not isinstance(candidate, str):
            candidate = _canonical_candidate_from_label(label)
        if isinstance(scope, type(None)):
            scope = _scope_from_label_suffix(label)

        resolved_guard_path = (
            _resolve_candidate_path(project_root, guard_path) or Path(guard_path)
        )
        telemetry = (
            load_object(resolved_guard_path) if resolved_guard_path.exists() else {}
        )
        row = {
            "pid": pid,
            "label": label,
            "candidate": _canonical_candidate_from_label(candidate),
            "candidate_with_scope": candidate,
            "scope_bytes": scope,
            "check_determinism": check_determinism,
            "command": command,
            "rss_guard_json": str(resolved_guard_path),
            "guard_json_token": str(guard_path),
            "guard_status": telemetry.get("status"),
            "guard_elapsed_s": telemetry.get("elapsed_s"),
            "sample_count": telemetry.get("sample_count"),
            "max_sampled_single_rss_kib": telemetry.get("max_sampled_single_rss_kib"),
            "max_sampled_tree_rss_kib": telemetry.get("max_sampled_tree_rss_kib"),
            "official_decimal_limit_kib": telemetry.get("official_decimal_limit_kib"),
            "official_decimal_over_limit_kib": telemetry.get("official_decimal_over_limit_kib"),
            "rss_guard_exceeded": telemetry.get("rss_guard_exceeded"),
            "returncode": telemetry.get("returncode"),
        }
        if best is None:
            best = row
        elif best.get("pid") is None:
            best = row
    return best


def _resolve_candidate_path(project_root: Path, raw_path: str) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    candidates: list[Path] = [candidate]
    if not candidate.is_absolute():
        candidates.extend(
            [
                project_root / candidate,
                project_root.parent / candidate,
                project_root.parent.parent / candidate,
                Path.cwd() / candidate,
            ]
        )
        if raw_path.startswith("gamma/"):
            stripped = Path(raw_path.removeprefix("gamma/"))
            candidates.extend(
                [
                    project_root.parent.parent / stripped,
                    Path.cwd() / stripped,
                ]
            )
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_live_observation(project_root: Path) -> dict[str, Any]:
    row = _read_live_guard_row(project_root)
    if row is None:
        return {}
    return row


def _bind_live_observation_to_operational(
    live: dict[str, Any], operational: dict[str, Any]
) -> dict[str, Any]:
    """Bind nested guard telemetry to the matching canonical active gate."""

    active = operational.get("active_gate")
    liveness = operational.get("gate_liveness")
    if not isinstance(active, dict) or not isinstance(liveness, dict):
        return live
    if active.get("status") != "running" or liveness.get("is_live") is not True:
        return live
    active_guard = active.get("rss_guard_json")
    live_guard = live.get("rss_guard_json")
    if not isinstance(active_guard, str) or not isinstance(live_guard, str):
        return live
    if Path(active_guard).resolve() != Path(live_guard).resolve():
        return live
    program_id = active.get("program_id")
    scope_bytes = active.get("scope_bytes")
    if not isinstance(program_id, str) or not isinstance(scope_bytes, int):
        return live
    bound = dict(live)
    bound["guard_label_candidate"] = live.get("candidate")
    bound["guard_inferred_scope_bytes"] = live.get("scope_bytes")
    bound["candidate"] = program_id
    bound["scope_bytes"] = scope_bytes
    bound["identity_source"] = active.get("source")
    return bound


def _resolve_scope_text(value: Any) -> str:
    return fmt_int(value) if value is not None else "unknown"


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
    source_required = row.get("source_required", True)
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
            if not source_required and not resolved.exists():
                audit.update(
                    {
                        "pass": None,
                        "skipped": True,
                        "reason": "optional source absent",
                    }
                )
                audits.append(audit)
                continue
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
    if target_score != 105_000_000 or target_input != 1_000_000_000:
        errors.append("target must be exact full enwik9 at score 105000000")
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


def fmt_score_percent(score: Any, input_bytes: Any = 1_000_000_000) -> str:
    if not isinstance(score, int) or not isinstance(input_bytes, int) or input_bytes <= 0:
        return "unknown"
    return f"{score * 100 / input_bytes:.7f}%"


def fmt_point_distance(byte_distance: Any, input_bytes: int = 1_000_000_000) -> str:
    if not isinstance(byte_distance, int):
        return "unknown"
    return f"{byte_distance * 100 / input_bytes:.7f} percentage points"


def render_live_state(status: dict[str, Any]) -> list[str]:
    lines: list[str] = ["## Live Run State", ""]
    live = status["operational"].get("live_observation") or {}
    if live:
        decimal_limit = live.get("official_decimal_limit_kib")
        over_limit = live.get("official_decimal_over_limit_kib")
        single_rss = live.get("max_sampled_single_rss_kib")
        guard_status = live.get("guard_status", "running")
        guard_elapsed = live.get("guard_elapsed_s")
        sample_count = live.get("sample_count")
        lines.extend(
            [
                f"- Running command: `{live.get('candidate', 'unknown')}` "
                f"`--limit {live.get('scope_bytes') or 'unknown'}` "
                f"`--check-determinism {str(bool(live.get('check_determinism'))).lower()}`; "
                f"guard `{guard_status}`.",
                f"- Command PID: `{live.get('pid', 'unknown')}`; candidate label: `{live.get('label', 'unknown')}`.",
            ]
        )
        if isinstance(guard_elapsed, (int, float)):
            lines.append(
                f"- Guard elapsed: `{guard_elapsed:.4f}` seconds; samples `{fmt_int(sample_count)}`."
            )
        else:
            lines.append(
                f"- Guard elapsed: `{guard_elapsed}`; samples `{fmt_int(sample_count)}`."
            )
        lines.append(f"- Guard JSON: `{live.get('rss_guard_json', 'unknown')}`.")
        lines.append(
            f"- Live RSS: single `{fmt_int(single_rss)}` KiB, tree `{fmt_int(live.get('max_sampled_tree_rss_kib'))}` KiB; "
            f"official decimal over-limit `{fmt_int(over_limit)} KiB`."
        )
        if isinstance(decimal_limit, int):
            lines.append(f"- Decimal guard limit: `{fmt_int(decimal_limit)}` KiB.")
            lines.append(f"- Official decimal over-limit KiB: `{fmt_int(over_limit)}`.")
    else:
        lines.append("- No live resource-guarded run was observed.")
    lines.append("")
    return lines


def render_markdown(status: dict[str, Any]) -> str:
    official = status["official"]
    forecast = status.get("canonical_forecast") or {}
    target_score = status["target"]["score_bytes"]
    lines = ["# enwiki9 Hutter Status", ""]
    lines.extend(render_live_state(status))
    lines.extend(["## Score Status", ""])
    lines.append(
        f"- Target score: `{fmt_int(target_score)}` bytes "
        f"(`{fmt_score_percent(target_score)}`)."
    )
    if official["won"]:
        lines.append(
            f"- Verified official full-1G score: "
            f"`{fmt_int(official['result']['hutter_score'])}` "
            f"(`{fmt_score_percent(official['result']['hutter_score'])}`); "
            "target achieved."
        )
    elif official["verified_full_corpus_result"]:
        lines.append(
            f"- Verified official full-1G score: "
            f"`{fmt_int(official['result']['hutter_score'])}` "
            f"(`{fmt_score_percent(official['result']['hutter_score'])}`); "
            f"distance above target `{fmt_int(official['distance_bytes'])}` bytes "
            f"(`{fmt_point_distance(official['distance_bytes'])}`)."
        )
    else:
        lines.append(
            "- Verified official full-1G score: `unknown`; no exact result exists."
        )
        lines.append("- Official distance: `unknown`.")
    forecast_score = forecast.get("forecast_score")
    forecast_debt = forecast.get("forecast_debt_bytes")
    forecast_margin = forecast.get("forecast_margin_bytes")
    forecast_distance_label = (
        "margin below target"
        if isinstance(forecast_margin, int) and forecast_margin >= 0
        else "distance above target"
    )
    forecast_distance = (
        forecast_margin
        if isinstance(forecast_margin, int) and forecast_margin >= 0
        else forecast_debt
    )
    lines.append(
        f"- Best counted forecast: `{fmt_int(forecast_score)}` "
        f"(`{fmt_score_percent(forecast_score)}`); {forecast_distance_label} "
        f"`{fmt_int(forecast_distance)}` bytes "
        f"(`{fmt_point_distance(forecast_distance)}`)."
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
            f"- Active candidate provisional projection: `{fmt_int(active_score)}` "
            f"(`{fmt_score_percent(active_score)}`); {distance_label} "
            f"`{fmt_int(distance_value)}` bytes "
            f"(`{fmt_point_distance(distance_value)}`)."
        )
        disjoint_score = active.get("disjoint_forecast_score")
        disjoint_margin = active.get("disjoint_forecast_margin_bytes")
        if isinstance(disjoint_score, int) and isinstance(disjoint_margin, int):
            lines.append(
                f"- Disjoint-slice diagnostic extrapolation: "
                f"`{fmt_int(disjoint_score)}` "
                f"(`{fmt_score_percent(disjoint_score)}`); provisional margin "
                f"`{fmt_int(disjoint_margin)}` bytes."
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
            "roundtrip, and score at or below 105,000,000 is a win.",
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
    operational = load_object(operational_path)
    if args.live_observation is not None:
        live_observation = load_object(args.live_observation)
    else:
        live_observation = _load_live_observation(root)
    if isinstance(live_observation, dict) and live_observation:
        live_observation = _bind_live_observation_to_operational(
            live_observation,
            operational,
        )
    if not live_observation:
        handoff = operational.get("handoff") if isinstance(operational, dict) else {}
        if isinstance(handoff, dict):
            fallback_candidate = handoff.get("candidate")
            if fallback_candidate:
                live_observation = {
                    "candidate": fallback_candidate,
                    "scope_bytes": handoff.get("scope_bytes"),
                    "guard_status": "unknown",
                }
    live_observation = (
        live_observation if isinstance(live_observation, dict) else None
    )
    status, errors = validate_and_normalize(
        root,
        load_object(ledger_path),
        operational,
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
