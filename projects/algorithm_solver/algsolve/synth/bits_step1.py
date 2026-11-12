"""Gamma BITS step 1 driver: connect the allowlist, dataset adapter, planner,
isolated teacher and target builder that already exist.

Every subcommand reads the pinned dataset only through ``AllowlistDatasetAdapter``
(allowlist and reservation boundary enforced before any payload is kept) and the
authorization records file, which names the owner decisions this run relies on.
Outputs that contain third-party problem text (inventories, teacher inputs and
outputs, target builds) are written to a caller-chosen directory outside the
repository: the dataset licence allows local research use only.

Subcommands:
  inventory  Public fields of the allowlisted candidates, for family review.
  freeze     Reviewed families/holdouts -> metadata hashes -> write-once plan.
  build      Frozen plan + reviewed requirements + isolated teacher -> targets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import semantic_allowlist as allowlist_mod
from . import semantic_target_pipeline as pipeline

AUTHORIZATION_SCHEMA = "algsolve.bits-step1-authorizations.v1"


def load_authorizations(path):
    """The owner's authorization records for this step, as a hash-bound file."""
    raw = Path(path).read_bytes()
    records = json.loads(raw)
    if not isinstance(records, dict) or records.get("schema") != AUTHORIZATION_SCHEMA:
        raise ValueError("Unsupported BITS step 1 authorization records")
    for name in ("dataset_provisioning", "isolated_teacher_inference", "heldout_payload_hashing"):
        record = records.get(name)
        if not isinstance(record, dict) or record.get("authorized") is not True:
            raise PermissionError(f"Missing owner authorization: {name}")
    return records, hashlib.sha256(raw).hexdigest()


def open_adapter(dataset, authorizations):
    compiled = allowlist_mod.compile_committed_allowlist_and_boundary()
    adapter = allowlist_mod.AllowlistDatasetAdapter(
        Path(dataset),
        allowlist=compiled["allowlist"],
        boundary=compiled["boundary"],
        authorization=authorizations["dataset_provisioning"],
    )
    return compiled, adapter


def _write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def inventory(args):
    records, records_sha = load_authorizations(args.authorizations)
    compiled, adapter = open_adapter(args.dataset, records)
    audit = compiled["audit"]
    pools = {uid: "dev_fit" for uid in audit["functional_dev_fit_uids"]}
    pools.update({uid: "dev_val" for uid in audit["functional_dev_val_uids"]})
    rows = []
    for uid, pool in sorted(pools.items()):
        raw = adapter._sanitized_rows.get(uid)
        if raw is None:
            rows.append({"uid": uid, "pool": pool, "status": "absent_from_dataset"})
            continue
        status, reason = "parsed", ""
        try:
            adapter._parse_normalized_pair(raw)
        except (ValueError, KeyError, TypeError) as error:
            status, reason = "unusable", f"{type(error).__name__}: {error}"
        rows.append({
            "uid": uid, "key": f"lc:{raw['task_id']}", "slug": raw["task_id"], "pool": pool,
            "difficulty": raw["difficulty"], "tags": raw["tags"], "status": status, "reason": reason,
            # Public statement and starter code only; tests and references are not written.
            "statement": raw["problem_description"].strip(), "starter_code": raw["starter_code"],
        })
    _write_new(args.out, {
        "schema": "algsolve.bits-step1-inventory.v1",
        "authorizations_sha256": records_sha,
        "dataset_receipt": adapter.file_receipt,
        "allowlist_sha256": audit["allowlist_sha256"], "boundary_sha256": audit["boundary_sha256"],
        "counts": {"candidates": len(rows), "dev_fit": sum(r["pool"] == "dev_fit" for r in rows),
                   "dev_val": sum(r["pool"] == "dev_val" for r in rows),
                   "unusable": sum(r["status"] != "parsed" for r in rows)},
        "rows": rows,
    })
    print(json.dumps({"wrote": str(args.out), "candidates": len(rows),
                      "unusable": sum(r["status"] != "parsed" for r in rows)}))


def load_family_review(path):
    raw = Path(path).read_bytes()
    review = json.loads(raw)
    if not isinstance(review, dict) or review.get("schema") != "algsolve.bits-step1-family-review.v1":
        raise ValueError("Unsupported family review")
    for field in ("family_by_uid", "structural_groups_by_uid", "aliases_by_uid", "holdout_families", "recombination_uids"):
        if field not in review:
            raise ValueError(f"Family review lacks {field}")
    return review, hashlib.sha256(raw).hexdigest()


def freeze(args):
    """Hash the reviewed metadata through the adapter and write the frozen plan."""
    records, records_sha = load_authorizations(args.authorizations)
    review, review_sha = load_family_review(args.family_review)
    compiled, adapter = open_adapter(args.dataset, records)
    metadata, unusable = adapter.extract_allowlisted_metadata_hashes(
        review["family_by_uid"],
        structural_groups_by_uid=review["structural_groups_by_uid"],
        aliases_by_uid=review["aliases_by_uid"],
    )
    plan = pipeline.freeze_plan(
        metadata, compiled["boundary"], review["holdout_families"],
        allowlist=compiled["allowlist"], recombination_uids=review["recombination_uids"],
    )
    pipeline.write_plan(args.plan, plan)
    splits = {}
    for row in plan["rows"]:
        splits[row["split"]] = splits.get(row["split"], 0) + 1
    receipt = {
        "schema": "algsolve.bits-step1-plan-receipt.v1",
        "plan_sha256": plan["plan_sha256"],
        "plan_file_sha256": hashlib.sha256(Path(args.plan).read_bytes()).hexdigest(),
        "authorizations_sha256": records_sha, "family_review_sha256": review_sha,
        "dataset_receipt": adapter.file_receipt,
        "allowlist_sha256": compiled["audit"]["allowlist_sha256"],
        "boundary_sha256": compiled["audit"]["boundary_sha256"],
        "metadata_rows": len(metadata), "unusable_by_uid": unusable, "splits": dict(sorted(splits.items())),
        "development_fit_uids": sorted(row["uid"] for row in plan["rows"] if row["split"] == "development_fit"),
    }
    _write_new(args.receipt, receipt)
    print(json.dumps({key: receipt[key] for key in ("plan_sha256", "metadata_rows", "splits")}))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--dataset", required=True, type=Path)
    inv.add_argument("--authorizations", required=True, type=Path)
    inv.add_argument("--out", required=True, type=Path)
    inv.set_defaults(run=inventory)
    frz = sub.add_parser("freeze")
    frz.add_argument("--dataset", required=True, type=Path)
    frz.add_argument("--authorizations", required=True, type=Path)
    frz.add_argument("--family-review", required=True, type=Path)
    frz.add_argument("--plan", required=True, type=Path)
    frz.add_argument("--receipt", required=True, type=Path)
    frz.set_defaults(run=freeze)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
