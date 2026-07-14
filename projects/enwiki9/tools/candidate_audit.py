"""Audit enwiki9 candidate source, metadata, tracking, and evidence.

This script is intentionally read-only unless --write is passed. It creates a
tracked inventory from local source state while leaving raw corpora, build
artifacts, bytecode caches, and benchmark outputs ignored.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS_DIR = ROOT / "programs"
RESULTS_DIR = ROOT / "results"
INDEX_PATH = ROOT / "index.json"
INVENTORY_JSON = ROOT / "candidate_inventory.json"
INVENTORY_MD = ROOT / "CANDIDATE_INVENTORY.md"

LOCAL_ARTIFACT_PATTERNS = (
    "build/",
    "results/",
    "projects/enwiki9/data/enwik9",
    "projects/enwiki9/data/enwik9.zip",
    "__pycache__/",
)

TERMINAL_AUDIT_STATUSES = {
    "active",
    "blocked_dependency",
    "candidate",
    "measured_negative",
    "retired",
    "track_source_before_evolution",
}

STATUS_DESCRIPTIONS = {
    "active": (
        "Contract-valid, registered, source-tracked candidates with valid "
        "roundtrip evidence and an explicit active metadata status."
    ),
    "blocked_dependency": (
        "Candidates blocked by an external dependency, lock, runtime, or "
        "baseline requirement rather than by measured compression quality."
    ),
    "candidate": (
        "Contract-valid, registered, source-tracked candidates still awaiting "
        "Lane 0 measurement or a promotion decision."
    ),
    "measured_negative": (
        "Contract-valid candidates with valid roundtrip evidence that are kept "
        "as negative empirical evidence instead of active promotion work."
    ),
    "retired": (
        "Candidates with retired metadata or unrepaired contract/schema "
        "failures that should stay out of active sweeps."
    ),
    "track_source_before_evolution": (
        "Candidates with local source changes that must be serialized into a "
        "tracked patch or committed source before further evolution."
    ),
}


def rel(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


GENERATED_INVENTORY_PATHS = {
    rel(INVENTORY_JSON),
    rel(INVENTORY_MD),
}


def git_lines(*args: str) -> set[str]:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {line for line in proc.stdout.splitlines() if line}


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def load_index() -> dict[str, Any]:
    return load_json(INDEX_PATH)


def iter_file_entries(path: pathlib.Path) -> list[pathlib.Path]:
    entries: list[pathlib.Path] = []
    for child in path.rglob("*"):
        if "__pycache__" in child.parts:
            continue
        if child.is_file() or child.is_symlink():
            entries.append(child)
    return sorted(entries)


def count_file_entries(path: pathlib.Path) -> int:
    return len(iter_file_entries(path))


def count_dirs(path: pathlib.Path) -> int:
    return sum(1 for child in path.rglob("*") if child.is_dir()) + 1


def missing_payload_targets(program_dir: pathlib.Path) -> list[str]:
    return sorted(
        child.name
        for child in program_dir.iterdir()
        if child.is_symlink() and not child.exists()
    )


def driver_program_size(program_dir: pathlib.Path) -> int | None:
    size = 0
    for child in sorted(program_dir.iterdir()):
        if child.name in ("meta.json", "__pycache__") or child.name.startswith("."):
            continue
        if child.is_file() or child.is_symlink():
            try:
                size += child.stat().st_size
            except FileNotFoundError:
                return None
    return size


def parse_meta(program_dir: pathlib.Path) -> tuple[dict[str, Any] | None, str | None]:
    meta_path = program_dir / "meta.json"
    if not meta_path.exists():
        return None, None
    try:
        return load_json(meta_path), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json:{exc.lineno}:{exc.colno}"


def collect_results(program_id: str) -> dict[str, Any]:
    result_dir = RESULTS_DIR / program_id
    rows: list[dict[str, Any]] = []
    if result_dir.exists():
        for path in sorted(result_dir.glob("*.json")):
            try:
                row = load_json(path)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)

    valid = [
        row
        for row in rows
        if row.get("roundtrip_ok") is True
        and isinstance(row.get("data_size"), int)
        and isinstance(row.get("hutter_score"), int)
    ]
    best = None
    if valid:
        best = min(valid, key=lambda row: (-row["data_size"], row["hutter_score"]))

    return {
        "result_files": len(rows),
        "valid_result_files": len(valid),
        "best_valid_result": None
        if best is None
        else {
            "data_size": best["data_size"],
            "hutter_score": best["hutter_score"],
            "compressed_size": best.get("compressed_size"),
            "program_size": best.get("program_size"),
            "bits_per_byte": best.get("bits_per_byte"),
            "timestamp": best.get("timestamp"),
            "data_md5": best.get("data_md5"),
        },
    }


def gate_int(row: dict[str, Any], *names: str) -> int | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, int):
            return value
    return None


def gate_roundtrip_backed(label: str, row: dict[str, Any]) -> bool:
    if row.get("roundtrip_ok") is True or row.get("deterministic") is True:
        return True
    determinism = row.get("determinism")
    if isinstance(determinism, dict) and determinism.get("single_host_byte_equal") is True:
        return True
    if isinstance(determinism, bool) and determinism:
        return True
    if isinstance(row.get("roundtrip_basis"), str):
        return True
    return "inherited" in label or "identity" in label


def scope_from_label(label: str) -> int | None:
    parts = label.lower().replace("-", "_").split("_")
    scopes = {
        "1k": 1024,
        "64k": 65536,
        "250k": 250000,
        "1m": 1000000,
        "10m": 10000000,
        "100m": 100000000,
        "1g": 1000000000,
    }
    for part in parts:
        if part in scopes:
            return scopes[part]
    return None


def collect_meta_evidence(
    meta: dict[str, Any] | None,
    *,
    default_program_size: int | None,
) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {"valid_meta_evidence": 0, "best_valid_meta_evidence": None}

    rows: list[dict[str, Any]] = []
    for section_name in ("measured", "verified_gates"):
        section = meta.get(section_name)
        if not isinstance(section, dict):
            continue
        for label, row in section.items():
            if not isinstance(row, dict):
                continue
            data_size = gate_int(row, "data_size", "input_bytes")
            if data_size is None:
                data_size = scope_from_label(str(label))
            compressed_size = gate_int(row, "compressed_size", "archive", "archive_size")
            program_size = gate_int(row, "program_size")
            if program_size is None:
                program_size = default_program_size
            hutter_score = gate_int(row, "hutter_score")
            if (
                hutter_score is None
                and compressed_size is not None
                and program_size is not None
            ):
                hutter_score = compressed_size + program_size
            if (
                data_size is None
                or compressed_size is None
                or hutter_score is None
                or not gate_roundtrip_backed(str(label), row)
            ):
                continue
            rows.append(
                {
                    "section": section_name,
                    "label": str(label),
                    "data_size": data_size,
                    "hutter_score": hutter_score,
                    "compressed_size": compressed_size,
                    "program_size": program_size,
                    "bits_per_byte": row.get("bits_per_byte"),
                    "data_md5": row.get("data_md5"),
                    "source": "meta.json",
                }
            )

    best = None
    if rows:
        best = min(rows, key=lambda row: (-row["data_size"], row["hutter_score"]))

    return {
        "valid_meta_evidence": len(rows),
        "best_valid_meta_evidence": best,
    }


def classify_candidate(
    *,
    has_program: bool,
    has_meta: bool,
    meta_status: str | None,
    registered: bool,
    untracked_source_files: list[str],
    meta_error: str | None,
    meta_id_matches: bool | None,
    valid_evidence_count: int,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if meta_status == "retired":
        if registered:
            reasons.append("retired_but_still_in_index_json")
        if untracked_source_files:
            reasons.append("retired_has_untracked_source_files")
        return "retired", reasons

    if meta_status == "blocked_dependency":
        if untracked_source_files:
            reasons.append("has_untracked_source_files")
        return "blocked_dependency", reasons

    if not has_program:
        reasons.append("missing_program_py")
    if not has_meta:
        reasons.append("missing_meta_json")
    if meta_error:
        reasons.append(meta_error)
    if meta_id_matches is False:
        reasons.append("meta_id_mismatch")
    if not registered:
        reasons.append("not_in_index_json")
    if untracked_source_files:
        reasons.append("has_untracked_source_files")

    if untracked_source_files:
        return "track_source_before_evolution", reasons
    if not has_program or not has_meta or not registered or meta_error or meta_id_matches is False:
        return "retired", reasons
    if meta_status == "candidate":
        if valid_evidence_count == 0:
            return "candidate", ["awaiting_lane0_measurement"]
        return "candidate", ["awaiting_lane0_promotion_decision"]
    if meta_status == "measured_negative":
        if valid_evidence_count == 0:
            return "candidate", ["measured_negative_without_valid_evidence"]
        return "measured_negative", reasons
    if meta_status == "active":
        if valid_evidence_count == 0:
            return "candidate", ["active_without_valid_evidence"]
        return "active", reasons
    if valid_evidence_count == 0:
        return "candidate", ["awaiting_lane0_measurement"]
    if meta_status not in TERMINAL_AUDIT_STATUSES:
        reasons.append("metadata_status_missing_or_unknown")
    return "candidate", reasons or ["awaiting_lane0_promotion_decision"]


def audit() -> dict[str, Any]:
    index = load_index()
    registered_ids = {entry["id"] for entry in index.get("programs", [])}

    tracked = git_lines("ls-files", "--", rel(ROOT))
    untracked = git_lines("ls-files", "--others", "--exclude-standard", "--", rel(ROOT))
    ignored = git_lines(
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--",
        rel(ROOT),
    )
    modified = git_lines("ls-files", "--modified", "--", rel(ROOT))
    modified -= GENERATED_INVENTORY_PATHS

    candidates: list[dict[str, Any]] = []
    for program_dir in sorted(path for path in PROGRAMS_DIR.iterdir() if path.is_dir()):
        program_id = program_dir.name
        files = [rel(path) for path in iter_file_entries(program_dir)]
        source_files = [
            path
            for path in files
            if path not in ignored and not path.endswith(".pyc")
        ]
        untracked_source_files = [path for path in source_files if path in untracked]
        tracked_source_files = [path for path in source_files if path in tracked]

        meta, meta_error = parse_meta(program_dir)
        meta_id = meta.get("id") if isinstance(meta, dict) else None
        meta_id_matches = None if meta_id is None else meta_id == program_id
        results = collect_results(program_id)
        missing_payloads = missing_payload_targets(program_dir)
        program_size = driver_program_size(program_dir)
        meta_evidence = collect_meta_evidence(
            meta if isinstance(meta, dict) else None,
            default_program_size=program_size,
        )
        total_valid_evidence = (
            results["valid_result_files"] + meta_evidence["valid_meta_evidence"]
        )
        status, reasons = classify_candidate(
            has_program=(program_dir / "program.py").exists(),
            has_meta=(program_dir / "meta.json").exists(),
            meta_status=meta.get("status") if isinstance(meta, dict) else None,
            registered=program_id in registered_ids,
            untracked_source_files=untracked_source_files,
            meta_error=meta_error,
            meta_id_matches=meta_id_matches,
            valid_evidence_count=total_valid_evidence,
        )
        if missing_payloads:
            status = "candidate"
            reasons = [*reasons, "missing_payload_target"]
        results.update(meta_evidence)
        results["total_valid_evidence"] = total_valid_evidence

        candidates.append(
            {
                "id": program_id,
                "status": status,
                "reasons": reasons,
                "registered": program_id in registered_ids,
                "has_program_py": (program_dir / "program.py").exists(),
                "has_meta_json": (program_dir / "meta.json").exists(),
                "meta_id": meta_id,
                "meta_status": meta.get("status") if isinstance(meta, dict) else None,
                "meta_id_matches_directory": meta_id_matches,
                "description": meta.get("description") if isinstance(meta, dict) else None,
                "deps": meta.get("deps") if isinstance(meta, dict) else None,
                "driver_program_size": program_size,
                "missing_payload_targets": missing_payloads,
                "source_file_entries": len(source_files),
                "tracked_source_file_entries": len(tracked_source_files),
                "untracked_source_files": untracked_source_files,
                "results": results,
            }
        )

    status_counts = Counter(candidate["status"] for candidate in candidates)
    top_level_counts = Counter()
    for path in iter_file_entries(ROOT):
        parts = path.relative_to(ROOT).parts
        top_level_counts[parts[0] if len(parts) > 1 else "<root>"] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_root": rel(ROOT),
        "tracking_policy": {
            "tracked": [
                "candidate source under projects/enwiki9/programs/",
                "candidate metadata in meta.json",
                "registry in index.json",
                "audit tooling and generated inventory",
                "small corpus fixtures",
            ],
            "ignored_local_artifacts": list(LOCAL_ARTIFACT_PATTERNS),
            "status_definitions": dict(sorted(STATUS_DESCRIPTIONS.items())),
        },
        "summary": {
            "file_entries": count_file_entries(ROOT),
            "directories": count_dirs(ROOT),
            "tracked_entries": len(tracked),
            "modified_tracked_entries": len(modified),
            "untracked_nonignored_entries": len(untracked),
            "ignored_entries": len(ignored),
            "registered_programs": len(registered_ids),
            "program_directories": len(candidates),
            "candidate_status_counts": dict(sorted(status_counts.items())),
            "top_level_file_entries": dict(sorted(top_level_counts.items())),
        },
        "modified_tracked_entries": sorted(modified),
        "untracked_nonignored_entries": sorted(untracked),
        "ignored_entries": sorted(ignored),
        "candidates": candidates,
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    candidates = inventory["candidates"]
    by_status = Counter(candidate["status"] for candidate in candidates)

    lines = [
        "# enwiki9 Candidate Inventory",
        "",
        f"Generated: `{inventory['generated_at']}`",
        "",
        "This inventory is generated by `python3 projects/enwiki9/tools/candidate_audit.py --write`.",
        "It tracks source and metadata readiness while leaving local corpora, build outputs,",
        "bytecode caches, and benchmark result files ignored.",
        "",
        "## Summary",
        "",
        f"- File entries: `{summary['file_entries']}`",
        f"- Directories: `{summary['directories']}`",
        f"- Tracked entries: `{summary['tracked_entries']}`",
        f"- Modified tracked entries: `{summary['modified_tracked_entries']}`",
        f"- Untracked non-ignored entries: `{summary['untracked_nonignored_entries']}`",
        f"- Ignored entries: `{summary['ignored_entries']}`",
        f"- Program directories: `{summary['program_directories']}`",
        f"- Registered programs: `{summary['registered_programs']}`",
        "",
        "## Candidate Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(by_status.items()):
        lines.append(f"| `{status}` | {count} |")

    lines.extend(
        [
            "",
            "## Tracking Policy",
            "",
            "Track candidate source, `meta.json`, `index.json`, audit tools, inventory, docs,",
            "and small fixture corpora. Keep these local artifacts ignored:",
            "",
        ]
    )
    for pattern in inventory["tracking_policy"]["ignored_local_artifacts"]:
        lines.append(f"- `{pattern}`")

    lines.extend(
        [
            "",
            "## Status Definitions",
            "",
            "| Status | Meaning |",
            "|---|---|",
        ]
    )
    status_definitions = inventory["tracking_policy"].get("status_definitions", {})
    for status, description in sorted(status_definitions.items()):
        lines.append(f"| `{status}` | {description} |")

    problem_candidates = [
        candidate
        for candidate in candidates
        if candidate["status"] not in ("active", "retired") or candidate["reasons"]
    ]
    lines.extend(
        [
            "",
            "## Candidates Needing Action",
            "",
            "| Candidate | Status | Reasons |",
            "|---|---|---|",
        ]
    )
    if problem_candidates:
        for candidate in problem_candidates:
            reasons = ", ".join(candidate["reasons"]) or "none"
            lines.append(
                f"| `{candidate['id']}` | `{candidate['status']}` | `{reasons}` |"
            )
    else:
        lines.append("| none | `active` | none |")

    lines.extend(
        [
            "",
            "## Modified Tracked Entries",
            "",
        ]
    )
    if inventory["modified_tracked_entries"]:
        for path in inventory["modified_tracked_entries"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Untracked Non-Ignored Entries",
            "",
        ]
    )
    if inventory["untracked_nonignored_entries"]:
        for path in inventory["untracked_nonignored_entries"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Full per-candidate details are in `candidate_inventory.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def preserve_generated_at_if_unchanged(inventory: dict[str, Any]) -> dict[str, Any]:
    """Avoid dirtying generated files when only the timestamp would change."""
    if not INVENTORY_JSON.exists():
        return inventory
    try:
        previous = load_json(INVENTORY_JSON)
    except (json.JSONDecodeError, OSError):
        return inventory
    if not isinstance(previous, dict) or "generated_at" not in previous:
        return inventory

    current_without_stamp = dict(inventory)
    previous_without_stamp = dict(previous)
    current_without_stamp.pop("generated_at", None)
    previous_without_stamp.pop("generated_at", None)
    if current_without_stamp == previous_without_stamp:
        inventory = dict(inventory)
        inventory["generated_at"] = previous["generated_at"]
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write inventory files")
    parser.add_argument("--json", action="store_true", help="print JSON to stdout")
    args = parser.parse_args(argv)

    inventory = audit()

    if args.write:
        inventory = preserve_generated_at_if_unchanged(inventory)
        INVENTORY_JSON.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
        INVENTORY_MD.write_text(render_markdown(inventory))

    if args.json or not args.write:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(f"wrote {rel(INVENTORY_JSON)}")
        print(f"wrote {rel(INVENTORY_MD)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
