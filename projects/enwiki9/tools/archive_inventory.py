#!/usr/bin/env python3
"""Inventory a committed enwiki9 tree without walking sparse or live outputs.

Classification is a candidate, never authority to remove, edit or move a file.
Only the nine independently reviewed raw-reverse binaries are pilot eligible.
Unresolved output-looking paths stay unresolved. Git lazy fetches are disabled.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

PREFIX = "projects/enwiki9/"
PILOT = "results/raw_reverse_bz2250k_q0_v1/"
RULES = {
    "declared_maintained": "Current maintained/compatibility role in docs/architecture/source_roles.json; historical bindings remain separate.",
    "frozen_role": "Explicit frozen source role; preserve original bytes and source identities.",
    "historical_blob": "Content-addressed historical input/source store; never infer disposable output from file extension.",
    "bound_input": "An original experiment, source closure or candidate revision names this exact input path.",
    "bound_output": "An original experiment outputs list names this exact path; later input use is recorded separately.",
    "fixture": "Explicit bounded fixture/test package, not inferred from a filename alone.",
    "corpus_asset": "Provisioned corpus/input family documented in project .gitignore and consumed by recovery tools.",
    "canonical_record": "Original contract, revision, provenance or operational evidence record; retain in Git for this pilot.",
    "source_surface": "Maintained framework/tool/library/test implementation surface; explicit frozen roles take precedence.",
    "reference_document": "Documentation/reference surface retained in Git; generated-versus-authored status may need review.",
    "unresolved": "No inspected producer/input declaration establishes the role; protected pending family review.",
    "gitlink": "Pinned upstream Git revision, not a blob or generated output.",
}


def git(repo: Path, *args) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], env={**os.environ, "GIT_NO_LAZY_FETCH": "1"})


def tree(repo: Path, revision: str) -> list[dict]:
    rows = []
    for record in git(repo, "ls-tree", "-rzl", revision, "--", PREFIX).split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, kind, oid, size = metadata.decode().split()
        rows.append(dict(path=path.decode("utf-8", "surrogateescape"), git_mode=mode,
                         git_type=kind, git_oid=oid, bytes=None if size == "-" else int(size)))
    return rows


def project_path(value: str, candidate: str | None = None) -> str | None:
    if not isinstance(value, str) or value.startswith("/") or ".." in PurePosixPath(value).parts:
        return None
    if value.startswith(PREFIX):
        return value
    if candidate:
        return PREFIX + "programs/" + candidate + "/" + value
    return PREFIX + value


def references(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def classify(row: dict, roles: dict, inputs: dict, outputs: dict) -> tuple[str, str, bool]:
    path = row["path"]
    relative = path[len(PREFIX):]
    role = roles.get(relative)
    if row["git_type"] != "blob":
        return "indispensable_inputs", "gitlink", False
    if role == "frozen_snapshot":
        return "indispensable_inputs", "frozen_role", False
    if role in ("maintained", "compatibility_entrypoint"):
        return "maintained_source", "declared_maintained", False
    if relative.startswith("operations/adaptive/candidate-blobs/"):
        return "indispensable_inputs", "historical_blob", False
    if relative.startswith("tests/fixtures/") or relative == "operations/evidence/fixtures/dualstream_opening250k_v1.raw":
        return "fixtures", "fixture", False
    if path in inputs:
        return "indispensable_inputs", "bound_input", path in outputs
    if path in outputs:
        return "retained_outputs", "bound_output", False
    if relative.startswith("data/"):
        return "indispensable_inputs", "corpus_asset", True
    if relative.startswith(("operations/", "contracts/")) and Path(relative).suffix in (".json", ".jsonl"):
        return "indispensable_inputs", "canonical_record", False
    if relative.startswith(("src/gamma_enwiki9/", "tools/", "lib/", "tests/")) and Path(relative).suffix in (".py", ".cpp", ".hpp", ".h", ".c"):
        return "maintained_source", "source_surface", True
    if relative.startswith(("docs/", "workbench/", "agents/", "skills/")) or "/" not in relative:
        return "maintained_source", "reference_document", True
    return "unresolved", "unresolved", True


def inventory(repo: Path, revision: str):
    revision = git(repo, "rev-parse", revision + "^{commit}").decode().strip()
    rows = tree(repo, revision)
    by_path = {row["path"]: row for row in rows}
    inputs, outputs = defaultdict(list), defaultdict(list)
    roles = {}
    inspected = []
    # Read only original metadata, never the large result/checkpoint bodies.
    selections = [row for row in rows if row["git_type"] == "blob" and row["bytes"] <= 2_000_000
                  and row["path"].endswith(".json") and (
                      row["path"].startswith(PREFIX + "operations/adaptive/experiments/") or
                      row["path"].startswith(PREFIX + "operations/adaptive/candidate-revisions/") or
                      row["path"].startswith(PREFIX + "operations/adaptive/source-closures/") or
                      row["path"].startswith(PREFIX + "operations/adaptive/python-runtime-closures/") or
                      row["path"].startswith(PREFIX + "operations/adaptive/framework-closures/") or
                      row["path"] == PREFIX + "docs/architecture/source_roles.json")]
    for row in selections:
        value = json.loads(git(repo, "cat-file", "blob", row["git_oid"]))
        inspected.append(row["path"])
        if row["path"].endswith("source_roles.json"):
            roles = {entry["path"]: entry["role"] for entry in value["files"]}
            continue
        is_revision = "/candidate-revisions/" in row["path"]
        candidate = value.get("candidateId") if is_revision else None
        if is_revision:
            bound = value.get("files", [])
        elif "/experiments/" in row["path"]:
            bound = [value.get("inputs", []), value.get("population", {})]
            for output in value.get("outputs", []):
                original = output if isinstance(output, str) else output.get("path")
                target = project_path(original)
                if target in by_path:
                    outputs[target].append(row["path"])
        else:
            bound = value
        for ref in references(bound):
            target = project_path(ref["path"], candidate)
            identity = dict(declaration=row["path"], declared_path=ref["path"], sha256=ref["sha256"])
            if target in by_path:
                inputs[target].append(identity)
            if ref.get("blobPath"):
                blob = project_path(ref["blobPath"])
                if blob in by_path:
                    inputs[blob].append(identity)
    for row in rows:
        category, rule, review = classify(row, roles, inputs, outputs)
        row.update(classification=category, reason_code=rule, needs_review=review,
                   input_binding_count=len(inputs[row["path"]]), output_binding_count=len(outputs[row["path"]]),
                   binding_examples=inputs[row["path"]][:2], output_declarations=outputs[row["path"]][:2],
                   pilot_eligible=False)
    artifact_path = PREFIX + PILOT + "artifacts.json"
    receipt = json.loads(git(repo, "cat-file", "blob", by_path[artifact_path]["git_oid"]))
    if receipt.get("complete") is not True:
        raise ValueError("Original pilot artifact receipt is incomplete")
    pilot, absent = [], []
    for arm in ("P", "K", "D"):
        for suffix in ("raw", "rbz", "repeat.rbz"):
            relative = PILOT + arm + "." + suffix
            if PREFIX + relative not in by_path:
                absent.append(PREFIX + relative)
                continue
            row = by_path[PREFIX + relative]
            ref = next(ref for ref in receipt["files"] if ref["path"] == relative)
            if row["bytes"] != ref["bytes"] or row["path"] not in outputs or inputs[row["path"]]:
                raise ValueError(f"Pilot does not match its original declaration: {relative}")
            row["pilot_eligible"] = True
            pilot.append({**row, "expected_sha256": ref["sha256"], "original_receipt": artifact_path})
    if absent:
        for row in pilot:
            row["pilot_eligible"] = False
            by_path[row["path"]]["pilot_eligible"] = False
    counts = Counter(row["classification"] for row in rows)
    sizes = Counter()
    for row in rows:
        sizes[row["classification"]] += row["bytes"] or 0
    summary = dict(schema="gamma.enwiki9.archive-classification-candidate/v1", source_revision=revision,
                   scope=PREFIX, tracked_entries=len(rows), tracked_blob_bytes=sum(row["bytes"] or 0 for row in rows),
                   counts=dict(counts), bytes_by_classification=dict(sizes), rules=RULES,
                   metadata_files_inspected=len(inspected), metadata_scope="frozen declarations and source roles only",
                   limitations=["Classification is not edit/removal authority.",
                                "Unresolved families have not been invented as outputs from directory names.",
                                "A bound input may also be a previous output; that overlap is protected.",
                                "All original path strings, receipts and source bindings remain unmodified.",
                                "No large result bodies were read for this inventory; byte counts and Git IDs are exact tree metadata."],
                   pilot=dict(files=pilot, absent_paths=absent,
                              status="complete-in-source-tree" if not absent else "not-complete-in-source-tree",
                              logical_bytes=sum(row["bytes"] for row in pilot),
                              canonical_population="operations/evidence/fixtures/dualstream_opening250k_v1.raw",
                              preserve_all_other_files=True))
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--inventory", type=Path, help="Optional full JSONL; summary-only is the default")
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary, rows = inventory(args.repo, args.revision)
    if args.inventory:
        with args.inventory.open("x") as stream:
            stream.write(json.dumps({key: summary[key] for key in ("schema", "source_revision", "scope")}) + "\n")
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
    with args.summary.open("x") as stream:
        json.dump(summary, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: summary[key] for key in ("source_revision", "tracked_entries", "tracked_blob_bytes", "counts", "bytes_by_classification")}))


if __name__ == "__main__":
    main()
