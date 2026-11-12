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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--dataset", required=True, type=Path)
    inv.add_argument("--authorizations", required=True, type=Path)
    inv.add_argument("--out", required=True, type=Path)
    inv.set_defaults(run=inventory)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
