#!/usr/bin/env python3
"""Audit recorded result/guard receipt fingerprints in candidate meta rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import datetime as dt
from dataclasses import dataclass
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS = ROOT / "programs"
OUT_JSON = ROOT / "docs" / "artifact_fingerprint_audit.json"
OUT_MD = ROOT / "docs" / "artifact_fingerprint_audit.md"


@dataclass
class ArtifactCheck:
    candidate: str
    label: str
    field: str
    path: str
    hash_field: str
    expected_sha256: str | None
    actual_sha256: str | None
    status: str


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def rel(path: pathlib.Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def resolve_artifact(raw_path: str) -> pathlib.Path:
    path = pathlib.Path(raw_path)
    if path.is_absolute():
        return path
    repo_path = REPO_ROOT / path
    if repo_path.exists():
        return repo_path
    return ROOT / path


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_metadata(path: pathlib.Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "bytes": stat.st_size,
        "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sha256": sha256_file(path),
    }


def check_artifact(
    *,
    candidate: str,
    label: str,
    row: dict[str, Any],
    path_field: str,
    hash_field: str,
) -> ArtifactCheck | None:
    raw_path = row.get(path_field)
    if not isinstance(raw_path, str) or not raw_path:
        return None
    expected = row.get(hash_field)
    if expected is not None and not isinstance(expected, str):
        expected = None
    path = resolve_artifact(raw_path)
    actual: str | None = None
    if not path.exists():
        status = "missing_artifact"
    else:
        actual = sha256_file(path)
        if expected is None:
            status = "missing_recorded_hash"
        elif actual == expected:
            status = "match"
        else:
            status = "hash_mismatch"
    return ArtifactCheck(
        candidate=candidate,
        label=label,
        field=path_field,
        path=raw_path,
        hash_field=hash_field,
        expected_sha256=expected,
        actual_sha256=actual,
        status=status,
    )


def repair_missing_hashes() -> dict[str, Any]:
    touched_files = 0
    repaired_fields = 0
    repaired_rows = 0
    for meta_path in sorted(PROGRAMS.glob("*/meta.json")):
        try:
            meta = load_json(meta_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta, dict):
            continue
        measured = meta.get("measured")
        if not isinstance(measured, dict):
            continue
        changed = False
        for row in measured.values():
            if not isinstance(row, dict):
                continue
            row_changed = False
            for path_field, prefix in (
                ("result_path", "result_json"),
                ("rss_guard_json", "rss_guard_json"),
                ("guard_path", "rss_guard_json"),
            ):
                raw_path = row.get(path_field)
                if not isinstance(raw_path, str) or not raw_path:
                    continue
                path = resolve_artifact(raw_path)
                if not path.exists():
                    continue
                metadata = artifact_metadata(path)
                updates = {
                    f"{prefix}_bytes": metadata["bytes"],
                    f"{prefix}_mtime_utc": metadata["mtime_utc"],
                    f"{prefix}_sha256": metadata["sha256"],
                }
                for key, value in updates.items():
                    if row.get(key) != value:
                        row[key] = value
                        changed = True
                        row_changed = True
                        repaired_fields += 1
            if row_changed:
                repaired_rows += 1
        if changed:
            meta_path.write_text(json.dumps(meta, indent=2) + "\n")
            touched_files += 1
    return {
        "touched_meta_files": touched_files,
        "repaired_rows": repaired_rows,
        "repaired_fields": repaired_fields,
    }


def iter_checks() -> list[ArtifactCheck]:
    checks: list[ArtifactCheck] = []
    for meta_path in sorted(PROGRAMS.glob("*/meta.json")):
        candidate = meta_path.parent.name
        try:
            meta = load_json(meta_path)
        except (OSError, json.JSONDecodeError):
            continue
        measured = meta.get("measured")
        if not isinstance(measured, dict):
            continue
        for label, row in sorted(measured.items()):
            if not isinstance(label, str) or not isinstance(row, dict):
                continue
            for path_field, hash_field in (
                ("result_path", "result_json_sha256"),
                ("rss_guard_json", "rss_guard_json_sha256"),
                ("guard_path", "rss_guard_json_sha256"),
            ):
                check = check_artifact(
                    candidate=candidate,
                    label=label,
                    row=row,
                    path_field=path_field,
                    hash_field=hash_field,
                )
                if check is not None:
                    checks.append(check)
    return checks


def payload(checks: list[ArtifactCheck]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for check in checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    mismatches = [check for check in checks if check.status == "hash_mismatch"]
    missing_artifacts = [check for check in checks if check.status == "missing_artifact"]
    missing_hashes = [check for check in checks if check.status == "missing_recorded_hash"]
    missing_by_candidate: dict[str, int] = {}
    for check in missing_hashes:
        missing_by_candidate[check.candidate] = missing_by_candidate.get(check.candidate, 0) + 1
    duplicate_refs: dict[str, list[ArtifactCheck]] = {}
    for check in checks:
        duplicate_refs.setdefault(check.path, []).append(check)
    duplicates = [
        {
            "path": path,
            "reference_count": len(rows),
            "references": [
                {
                    "candidate": row.candidate,
                    "label": row.label,
                    "field": row.field,
                    "status": row.status,
                }
                for row in rows[:10]
            ],
        }
        for path, rows in sorted(duplicate_refs.items())
        if len(rows) > 1
    ]
    return {
        "receipt_type": "artifact_fingerprint_audit",
        "project": "enwiki9",
        "artifact_checks": len(checks),
        "status_counts": counts,
        "hash_mismatches": [check.__dict__ for check in mismatches[:20]],
        "missing_artifacts": [check.__dict__ for check in missing_artifacts[:20]],
        "missing_recorded_hash_examples": [check.__dict__ for check in missing_hashes[:20]],
        "missing_recorded_hash_by_candidate": [
            {"candidate": candidate, "count": count}
            for candidate, count in sorted(
                missing_by_candidate.items(),
                key=lambda item: (-item[1], item[0]),
            )[:25]
        ],
        "duplicate_artifact_references": duplicates[:25],
        "ok": not mismatches,
        "artifact_set_complete": not missing_artifacts,
        "rule": (
            "Present artifacts with recorded receipt hashes must match. Missing local "
            "artifacts remain explicit provenance gaps and cannot support proof claims, "
            "but do not block regeneration of views from a partial checkout. Rows "
            "without hashes are legacy evidence and should be repaired when re-recorded."
        ),
    }


def render_md(data: dict[str, Any]) -> str:
    counts = data.get("status_counts", {})
    lines = [
        "# enwiki9 Artifact Fingerprint Audit",
        "",
        "This lock-safe audit checks candidate `meta.json` receipt references.",
        "It does not launch compression and does not score a candidate.",
        "",
        f"- Artifact checks: `{data.get('artifact_checks', 0):,}`",
        f"- Present artifact integrity OK: `{str(data.get('ok')).lower()}`",
        f"- Local artifact set complete: `{str(data.get('artifact_set_complete')).lower()}`",
        f"- Rule: `{data.get('rule', '')}`",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    if isinstance(counts, dict) and counts:
        for key in sorted(counts):
            value = counts[key]
            lines.append(f"| `{key}` | {value:,} |")
    else:
        lines.append("| n/a | 0 |")

    for section, title in (
        ("hash_mismatches", "Hash Mismatches"),
        ("missing_artifacts", "Missing Artifacts"),
        ("missing_recorded_hash_examples", "Legacy Rows Missing Recorded Hashes"),
    ):
        rows = data.get(section)
        lines.extend(["", f"## {title}", "", "| Candidate | Label | Field | Path |", "|---|---|---|---|"])
        if isinstance(rows, list) and rows:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    f"| `{row.get('candidate', '')}` | "
                    f"`{row.get('label', '')}` | "
                    f"`{row.get('field', '')}` | "
                    f"`{row.get('path', '')}` |"
                )
        else:
            lines.append("| n/a | n/a | n/a | n/a |")
    rows = data.get("missing_recorded_hash_by_candidate")
    lines.extend(
        [
            "",
            "## Legacy Repair Queue By Candidate",
            "",
            "| Candidate | Missing Hash Rows |",
            "|---|---:|",
        ]
    )
    if isinstance(rows, list) and rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"| `{row.get('candidate', '')}` | {int(row.get('count', 0)):,} |")
    else:
        lines.append("| n/a | 0 |")
    duplicates = data.get("duplicate_artifact_references")
    lines.extend(
        [
            "",
            "## Duplicate Artifact References",
            "",
            "These are not failures; they show receipt files reused by multiple meta labels.",
            "",
            "| Path | Reference Count |",
            "|---|---:|",
        ]
    )
    if isinstance(duplicates, list) and duplicates:
        for row in duplicates:
            if not isinstance(row, dict):
                continue
            lines.append(f"| `{row.get('path', '')}` | {int(row.get('reference_count', 0)):,} |")
    else:
        lines.append("| n/a | 0 |")
    lines.append("")
    return "\n".join(lines)


def write_outputs(data: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_md(data))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--repair-missing-hashes",
        action="store_true",
        help="backfill receipt byte, mtime, and SHA-256 fields in candidate meta rows",
    )
    args = parser.parse_args()

    repair_summary: dict[str, Any] | None = None
    if args.repair_missing_hashes:
        repair_summary = repair_missing_hashes()

    data = payload(iter_checks())
    if repair_summary is not None:
        data["repair_summary"] = repair_summary
    rendered_json = json.dumps(data, indent=2, sort_keys=True) + "\n"
    rendered_md = render_md(data)

    if args.check:
        if not OUT_JSON.exists() or OUT_JSON.read_text() != rendered_json:
            print(f"stale {rel(OUT_JSON)}", file=sys.stderr)
            return 1
        if not OUT_MD.exists() or OUT_MD.read_text() != rendered_md:
            print(f"stale {rel(OUT_MD)}", file=sys.stderr)
            return 1
        if data.get("ok") is not True:
            print("artifact_fingerprint_audit_found_hard_failures", file=sys.stderr)
            return 1
        print(f"up_to_date {OUT_MD}")
        return 0

    write_outputs(data)
    if args.json:
        print(rendered_json, end="")
    else:
        print(f"wrote {OUT_MD}")
        print(f"wrote {OUT_JSON}")
    return 0 if data.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
