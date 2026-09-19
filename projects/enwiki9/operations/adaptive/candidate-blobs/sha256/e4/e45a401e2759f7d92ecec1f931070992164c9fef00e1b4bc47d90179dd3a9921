#!/usr/bin/env python3
"""OMEGA archive operations for the enwiki9 adaptive search loop."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
from collections import defaultdict
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "operations" / "adaptive"
EXCLUSIONS = ADAPTIVE / "exclusions"
MUTATIONS = ADAPTIVE / "mutations.jsonl"
PROGRAMS = ROOT / "programs"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

MECHANISM_BONUSES = {
    "delete_predictor_work": 20,
    "change_coded_alphabet": 20,
    "change_update_schedule": 15,
    "replace_representation": 18,
    "add_state_coordinate": 10,
    "compile_state_machine": 18,
    "add_macro_family": 15,
    "parameter_tuning": -20,
    "mixture_expansion": -15,
    "other": 0,
    "unspecified": 0,
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def ensure_layout() -> None:
    EXCLUSIONS.mkdir(parents=True, exist_ok=True)


def validate_id(value: str) -> None:
    if not ID_RE.fullmatch(value):
        raise ValueError(
            "id must start with a lowercase letter or digit and contain only "
            "lowercase letters, digits, dots, dashes, or underscores"
        )


def atomic_json(path: pathlib.Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def proposal_search_fields(
    *,
    priority: int,
    mechanism_change: str | None,
    interfaces_exposed: list[str] | None,
    retired_neighborhoods: list[str] | None,
    parent_proposal_id: str | None,
) -> dict[str, Any]:
    mechanism = mechanism_change or "unspecified"
    if mechanism not in MECHANISM_BONUSES:
        raise ValueError(f"unknown mechanism change: {mechanism}")
    if parent_proposal_id is not None:
        validate_id(parent_proposal_id)
    bonus = MECHANISM_BONUSES[mechanism]
    return {
        "mechanism_change": mechanism,
        "mechanism_change_bonus": bonus,
        "search_priority": priority + bonus,
        "interfaces_exposed": interfaces_exposed or [],
        "retired_neighborhoods": retired_neighborhoods or [],
        "parent_proposal_id": parent_proposal_id,
    }


def record_exclusion(
    *,
    exclusion_id: str,
    mechanism: str,
    population: str,
    failure: str,
    retired_dimensions: list[str],
    unsettled_successors: list[str],
    evidence: list[str],
) -> dict[str, Any]:
    ensure_layout()
    validate_id(exclusion_id)
    path = EXCLUSIONS / f"{exclusion_id}.json"
    if path.exists():
        raise FileExistsError(f"exclusion already exists: {exclusion_id}")
    row = {
        "schema": "enwiki9_omega_exclusion_v1",
        "exclusion_id": exclusion_id,
        "mechanism": mechanism,
        "population": population,
        "failure": failure,
        "retired_dimensions": retired_dimensions,
        "unsettled_successors": unsettled_successors,
        "evidence": evidence,
        "recorded_at": utc_now(),
    }
    atomic_json(path, row)
    return row


def iter_exclusions() -> list[dict[str, Any]]:
    ensure_layout()
    rows = []
    for path in sorted(EXCLUSIONS.glob("*.json")):
        try:
            row = json.loads(path.read_text())
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(row, dict):
            row["_path"] = path.relative_to(ROOT).as_posix()
            rows.append(row)
    return rows


def _candidate_status(candidate_id: str) -> tuple[str, bool]:
    path = PROGRAMS / candidate_id / "meta.json"
    if not path.is_file():
        return "missing", False
    try:
        meta = json.loads(path.read_text())
    except (OSError, ValueError, json.JSONDecodeError):
        return "invalid", False
    if not isinstance(meta, dict):
        return "invalid", False
    measured = bool(meta.get("measured") or meta.get("latest_result"))
    return str(meta.get("status", "unknown")), measured


def descendant_productivity() -> list[dict[str, Any]]:
    children: dict[str, set[str]] = defaultdict(set)
    all_candidates: set[str] = set()
    if MUTATIONS.is_file():
        for line in MUTATIONS.read_text().splitlines():
            try:
                row = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            if not isinstance(row, dict):
                continue
            child = row.get("candidate_id")
            parent = row.get("parent")
            if isinstance(child, str):
                all_candidates.add(child)
            if isinstance(child, str) and isinstance(parent, str):
                children[parent].add(child)
                all_candidates.add(parent)

    def descendants(root: str) -> set[str]:
        found: set[str] = set()
        stack = list(children.get(root, ()))
        while stack:
            candidate = stack.pop()
            if candidate in found:
                continue
            found.add(candidate)
            stack.extend(children.get(candidate, ()))
        return found

    rows = []
    for candidate in sorted(all_candidates):
        lineage = descendants(candidate)
        measured = 0
        promoted = 0
        for descendant in lineage:
            status, is_measured = _candidate_status(descendant)
            measured += int(is_measured)
            promoted += int(status in {"active", "promoted", "frontier"})
        score = len(lineage) + 2 * measured + 10 * promoted
        rows.append(
            {
                "candidate_id": candidate,
                "direct_children": len(children.get(candidate, ())),
                "descendants": len(lineage),
                "measured_descendants": measured,
                "promoted_descendants": promoted,
                "descendant_productivity": score,
            }
        )
    rows.sort(
        key=lambda row: (
            -row["descendant_productivity"],
            -row["descendants"],
            row["candidate_id"],
        )
    )
    return rows
