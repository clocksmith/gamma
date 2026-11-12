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


def review_inputs(args):
    """Public inputs (the teacher's view) for the plan's development_fit rows, for review."""
    records, _ = load_authorizations(args.authorizations)
    compiled, adapter = open_adapter(args.dataset, records)
    plan = pipeline.validate_plan(json.loads(Path(args.plan).read_bytes()))
    adapter.bind_plan(plan)
    out = []
    for row in plan["rows"]:
        if row["split"] != "development_fit":
            continue
        problem = adapter.load_problem(row)
        out.append({"uid": row["uid"], "slug": problem.slug, "family": row["family"],
                    "problem_sha256": row["problem_sha256"], "method": problem.entry["method"],
                    **pipeline._public_input(problem)})
    _write_new(args.out, {"schema": "algsolve.bits-step1-review-inputs.v1",
                          "plan_sha256": plan["plan_sha256"], "rows": out})
    print(json.dumps({"wrote": str(args.out), "rows": len(out)}))


def teach(args):
    """Run the frozen teacher over the plan's development_fit public inputs (no dataset access).

    The public inputs come from `review-inputs`; each record is bound to the
    SHA-256 of its exact public input so `build --teacher-outputs` replays it
    only when the adapter reproduces that input. Rows the reviewer marked
    unsupported are skipped, as the builder blocks them before the teacher.
    """
    from concurrent.futures import ThreadPoolExecutor
    import platform
    from .bits_step1_teacher import make_generate_fn, public_input_sha256, template_sha256
    records, _ = load_authorizations(args.authorizations)
    teacher_auth = records["isolated_teacher_inference"]
    prompt_sha = template_sha256(args.prompt)
    if teacher_auth.get("prompt_sha256") != prompt_sha:
        raise PermissionError("Teacher prompt file differs from the authorized prompt_sha256")
    inputs = json.loads(Path(args.review_inputs).read_text())
    reviewed = json.loads(Path(args.reviewed_requirements).read_text())
    if inputs["plan_sha256"] != reviewed["plan_sha256"]:
        raise ValueError("Review inputs and reviewed requirements belong to different plans")
    out = Path(args.out)
    done = set()
    if out.exists():
        done = {json.loads(line)["uid"] for line in out.read_text().splitlines() if line.strip()}
    generate, version = make_generate_fn(args.prompt, model=teacher_auth["model_id"],
                                         log_path=out.with_suffix(".calls.jsonl"))
    rows = [r for r in inputs["rows"] if r["uid"] not in done
            and not reviewed["rows"][r["uid"]]["unsupported_requirements"]]
    def one(row):
        public = {k: row[k] for k in allowlist_mod.IsolatedTeacherAdapter.REQUIRED_INPUT_FIELDS}
        public = allowlist_mod.IsolatedTeacherAdapter._verify_isolated_input(public)
        config = {"model_id": teacher_auth["model_id"], "model_revision": teacher_auth["model_revision"],
                  "prompt_sha256": prompt_sha, "max_proposals": teacher_auth["max_proposals"]}
        record = {"uid": row["uid"], "plan_sha256": inputs["plan_sha256"], "prompt_sha256": prompt_sha,
                  "public_input_sha256": public_input_sha256(public), "model": teacher_auth["model_id"],
                  "cli_version": version, "host": "Mars", "machine": platform.machine()}
        try:
            record["proposals"] = generate(row["uid"], public, inputs["plan_sha256"], config)
        except Exception as error:
            record["error"] = f"{type(error).__name__}: {str(error)[:300]}"
        return record
    with ThreadPoolExecutor(max_workers=args.workers) as pool, out.open("a", encoding="utf-8") as stream:
        for record in pool.map(one, rows):
            stream.write(json.dumps(record, sort_keys=True) + "\n"); stream.flush()
            print(json.dumps({"uid": record["uid"], "proposals": len(record.get("proposals") or []),
                              "error": record.get("error")}), flush=True)


def build(args):
    """Frozen plan + reviewed requirements + isolated Opus teacher -> qualified targets (Linux sandbox)."""
    from .bits_step1_teacher import make_generate_fn, template_sha256
    records, records_sha = load_authorizations(args.authorizations)
    teacher_auth = records["isolated_teacher_inference"]
    if teacher_auth.get("prompt_sha256") != template_sha256(args.prompt):
        raise PermissionError("Teacher prompt file differs from the authorized prompt_sha256")
    compiled, adapter = open_adapter(args.dataset, records)
    plan_path = Path(args.plan)
    adapter.bind_plan(pipeline.validate_plan(json.loads(plan_path.read_bytes())))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.teacher_outputs:
        from .bits_step1_teacher import make_recorded_fn
        generate, recorded = make_recorded_fn(args.teacher_outputs)
        cli_version = sorted({r["cli_version"] + " on " + r["host"] for r in recorded.values()})
    else:
        generate, cli_version = make_generate_fn(args.prompt, model=teacher_auth["model_id"],
                                                 log_path=output.parent / (output.name + "-teacher-calls.jsonl"))
    teacher = allowlist_mod.IsolatedTeacherAdapter(generate, authorization=teacher_auth)
    summary = pipeline.build_targets(
        plan_path, output,
        codec_path=Path(pipeline.__file__).parents[2] / "contracts/typed_codec_v1.json",
        teacher_identity=teacher.teacher_identity,
        load_problem=adapter.load_problem, propose=teacher.propose,
        load_independent_tests=adapter.load_independent_tests,
        reviewed_requirements=args.reviewed_requirements,
        max_proposals=teacher.max_proposals,
        authorizations={"records_sha256": records_sha, "records": records,
                        "dataset_receipt": adapter.file_receipt, "teacher_cli_version": cli_version,
                        "teacher_outputs_sha256": (hashlib.sha256(Path(args.teacher_outputs).read_bytes()).hexdigest()
                                                   if args.teacher_outputs else None)},
    )
    print(json.dumps({key: summary[key] for key in ("counts", "emitted_pairs", "training_eligible_pairs")}))


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
    rin = sub.add_parser("review-inputs")
    rin.add_argument("--dataset", required=True, type=Path)
    rin.add_argument("--authorizations", required=True, type=Path)
    rin.add_argument("--plan", required=True, type=Path)
    rin.add_argument("--out", required=True, type=Path)
    rin.set_defaults(run=review_inputs)
    bld = sub.add_parser("build")
    bld.add_argument("--dataset", required=True, type=Path)
    bld.add_argument("--authorizations", required=True, type=Path)
    bld.add_argument("--plan", required=True, type=Path)
    bld.add_argument("--reviewed-requirements", required=True, type=Path)
    bld.add_argument("--prompt", required=True, type=Path)
    bld.add_argument("--output", required=True, type=Path)
    bld.add_argument("--teacher-outputs", type=Path, default=None,
                     help="Replay hash-bound teacher outputs recorded by `teach` instead of calling the CLI")
    bld.set_defaults(run=build)
    tch = sub.add_parser("teach")
    tch.add_argument("--authorizations", required=True, type=Path)
    tch.add_argument("--review-inputs", required=True, type=Path)
    tch.add_argument("--reviewed-requirements", required=True, type=Path)
    tch.add_argument("--prompt", required=True, type=Path)
    tch.add_argument("--out", required=True, type=Path)
    tch.add_argument("--workers", type=int, default=4)
    tch.set_defaults(run=teach)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
