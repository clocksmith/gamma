#!/usr/bin/env python3
"""Inventory a committed enwiki9 tree without walking sparse or live outputs.

Classification is a candidate, never authority to remove, edit or move a file.
Only the nine independently reviewed raw-reverse binaries are pilot eligible.
Unresolved output-looking paths stay unresolved. Git lazy fetches are disabled.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import hashlib
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
    "reviewed_probability_trace": "Exact original artifact-manifest entry, original producer trace-write contract and retained neural-comparison identity agree; no input binding.",
}


def trace_manifest_entries(manifest: dict, family: str, rows: int) -> dict:
    """Select eight explicit entries, never an entire mixed results directory."""
    if manifest.get("errors") != []:
        raise ValueError("Trace family has original artifact errors")
    selected = {}
    for arm in "PKDS":
        for phase in ("encode", "repeat"):
            path = f"results/{family}/work/native/{arm}-{phase}.probs"
            matches = [entry for entry in manifest["files"] if entry["path"] == path]
            if len(matches) != 1 or matches[0]["bytes"] != rows * 205 * 2:
                raise ValueError(f"Missing, duplicate or wrong-size trace entry: {path}")
            selected[path] = matches[0]
    return selected


def reviewed_trace_families(repo: Path, revision: str, by_path: dict, inputs: dict) -> list[dict]:
    """Two manually inspected original producers; no other families inferred."""
    result = []
    for family in ("fx2_attention_anchor250k_v1", "fx2_attention_anchor250k_v2"):
        bindings = []

        def read(relative):
            row = by_path[PREFIX + relative]
            data = git(repo, "cat-file", "blob", row["git_oid"])
            bindings.append(dict(path=PREFIX + relative, git_oid=row["git_oid"],
                                 bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
            return data

        experiment_path = f"operations/adaptive/experiments/{family}.json"
        experiment = json.loads(read(experiment_path))
        producer_path = f"tools/{family}.py"
        producer = read(producer_path)
        source_ref = next(ref for ref in experiment["inputs"] if ref["path"] == producer_path)
        if hashlib.sha256(producer).hexdigest() != source_ref["sha256"].removeprefix("sha256:"):
            raise ValueError(f"Original trace producer changed: {producer_path}")
        syntax = ast.parse(producer)
        row_count = next(node.value.value for node in syntax.body if isinstance(node, ast.Assign)
                         and any(isinstance(target, ast.Name) and target.id == "N" for target in node.targets))
        if row_count != 151210 or not any(isinstance(node, ast.FunctionDef) and node.name == "neural_compare" for node in syntax.body):
            raise ValueError("Original trace comparison contract differs")
        if b"--save-transformer-probs" not in producer:
            raise ValueError("Inspected producer no longer declares trace writes")
        artifact_path = f"results/{family}/artifacts.json"
        entries = trace_manifest_entries(json.loads(read(artifact_path)), family, row_count)
        decision = json.loads(read(f"results/{family}/decision.json"))
        comparison = json.loads(read(f"results/{family}/neural-comparison.json"))
        if decision.get("status") != "passed" or decision.get("child_closure_ok") is not True:
            raise ValueError("Original trace family correctness closure is incomplete")
        validity_path = "results/fx2_residual_features250k_v3/closure/feature_validity.json"
        validity = read(validity_path)
        validity_ref = next(ref for ref in experiment["inputs"] if ref["path"] == validity_path)
        if hashlib.sha256(validity).hexdigest() != validity_ref["sha256"].removeprefix("sha256:"):
            raise ValueError("Original trace population/prefix input changed")
        selected = []
        for relative, entry in entries.items():
            path = PREFIX + relative
            row = by_path.get(path)
            if row is None:
                continue  # A later archived tree may already externalize a family.
            if inputs.get(path) or row["bytes"] != entry["bytes"]:
                raise ValueError(f"Trace is bound input or its recorded size differs: {path}")
            selected.append({**row, "expected_sha256": entry["sha256"], "original_receipt": PREFIX + artifact_path,
                             "classification": "retained_outputs", "input_binding_count": 0})
        def identity(arm, phase="encode"):
            return entries[f"results/{family}/work/native/{arm}-{phase}.probs"]["sha256"]
        if identity("P") != identity("K") or any(identity(arm) != identity(arm, "repeat") for arm in "PKDS"):
            raise ValueError("Original P/K or repeat trace identity differs")
        for arm in "KDS":
            record = comparison[arm]
            if record["parent_sha256"] != identity("P") or record["treatment_sha256"] != identity(arm) or record["rows"] != row_count:
                raise ValueError("Original comparison is not bound to selected trace identities")
        result.append(dict(family=family, source_revision=revision, files=selected,
                           logical_bytes=sum(row["bytes"] for row in selected), bindings=bindings,
                           row_count=row_count, distribution_width=205, element_bytes=2,
                           producer=PREFIX + producer_path, artifact_manifest=PREFIX + artifact_path,
                           comparison_receipt=PREFIX + f"results/{family}/neural-comparison.json",
                           validity_input=PREFIX + validity_path,
                           proof="Original producer emits these exact streams; exact manifest and comparison identities agree. No model, archive, source or JSON receipt is selected.",
                           cpu_recheck="Run only original neural_compare on restored trace streams and retained prefix coordinates; never execute producer main/train/encode."))
    return result


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
    trace_families = reviewed_trace_families(repo, revision, by_path, inputs)
    reviewed = {entry["path"]: entry for family in trace_families for entry in family["files"]}
    for path, entry in reviewed.items():
        outputs[path].append(entry["original_receipt"])
    for row in rows:
        category, rule, review = classify(row, roles, inputs, outputs)
        if row["path"] in reviewed:
            rule, review = "reviewed_probability_trace", False
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
                   metadata_files_inspected=len(inspected), metadata_scope="frozen declarations, source roles and two explicitly reviewed probability-trace families",
                   reviewed_trace_bindings_verified=len({binding["path"] for family in trace_families for binding in family["bindings"]}),
                   reviewed_trace_families=trace_families,
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
