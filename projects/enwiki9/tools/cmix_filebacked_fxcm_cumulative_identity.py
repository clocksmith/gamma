#!/usr/bin/env python3
"""Run the guarded cumulative opening-1M parent/q1 identity gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

import cmix_filebacked_fxcm_scope_identity as scope


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-cumulative-identity.v1"
OFFSET = 0
LENGTH = 1_000_000


def guard_values(arm: dict[str, Any]) -> list[dict[str, Any]]:
    values = []
    for phase in ("encode", "decode"):
        _, value = scope.load_json(Path(arm[f"{phase}_guard"]["path"]), f"{phase} guard")
        values.append(value)
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--program-lock-verification", type=Path, required=True)
    parser.add_argument("--allocator-controls", type=Path, required=True)
    parser.add_argument("--allocator-positive-fixture", type=Path, required=True)
    parser.add_argument("--scope-identity-receipt", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args()

    build_path, build = scope.load_json(args.build_receipt, "scope build receipt")
    lock_path, lock = scope.load_json(args.program_lock_verification, "program lock verification")
    controls_path, controls = scope.load_json(args.allocator_controls, "allocator controls")
    positive_path, positive = scope.load_json(args.allocator_positive_fixture, "allocator positive fixture")
    prior_path, prior = scope.load_json(args.scope_identity_receipt, "scope identity receipt")
    corpus = scope.existing_regular(args.corpus, "canonical corpus")
    guard_tool = scope.existing_regular(args.resource_guard, "resource guard")
    packages, _ = scope.package_paths(build)
    head_blob = scope.verify_artifact_record(build.get("head_blob"), "head blob")
    if lock.get("schema") != scope.LOCK_SCHEMA or lock.get("candidate_id") != scope.CANDIDATE_ID or lock.get("verified") is not True:
        raise RuntimeError("program lock verification did not pass")
    if controls.get("schema") != scope.CONTROL_SCHEMA or not scope.controls_pass(controls):
        raise RuntimeError("allocator negative controls did not pass")
    if positive.get("pass") is not True or positive.get("return_code") != 0:
        raise RuntimeError("allocator positive fixture did not pass")
    if prior.get("schema") != "gamma.enwiki9.cmix-filebacked-fxcm-scope-identity.v2" or prior.get("terminal_pass") is not True:
        raise RuntimeError("three-scope v2 antecedent did not pass")
    if corpus.stat().st_size != scope.CANONICAL_BYTES or scope.sha256_file(corpus) != scope.CANONICAL_SHA256:
        raise RuntimeError("canonical enwik9 identity mismatch")
    result_root, result_fs = scope.absent_root(args.result_root, "cumulative result root")
    scratch_root, scratch_fs = scope.absent_root(args.scratch_root, "cumulative scratch root")
    if result_root == scratch_root or result_root in scratch_root.parents or scratch_root in result_root.parents:
        raise RuntimeError("result and scratch roots must be disjoint")
    result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    receipt_path = result_root / "cumulative-identity-receipt.json"
    cpu = min(os.sched_getaffinity(0))
    arms: list[dict[str, Any]] = []
    errors: list[str] = []
    slice_sha256 = "0" * 64
    aggregate = {name: hashlib.sha256() for name in ("parent", "candidate")}
    try:
        for name in aggregate:
            aggregate[name].update(OFFSET.to_bytes(8, "little"))
            aggregate[name].update(LENGTH.to_bytes(8, "little"))
        parent_slice, parent = scope.run_arm(
            "parent", packages["parent"], corpus, OFFSET, LENGTH, result_root,
            scratch_root, guard_tool, head_blob, cpu, aggregate["parent"],
        )
        slice_sha256 = parent_slice
        arms.append(parent)
        candidate_slice, candidate = scope.run_arm(
            "candidate", packages["candidate"], corpus, OFFSET, LENGTH, result_root,
            scratch_root, guard_tool, head_blob, cpu, aggregate["candidate"],
        )
        arms.append(candidate)
        if parent_slice != candidate_slice:
            raise RuntimeError("parent/candidate cumulative slice identity mismatch")
        if next(scratch_root.iterdir(), None) is not None:
            raise RuntimeError("cumulative scratch root is not empty")
        scratch_root.rmdir()
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    complete = len(arms) == 2
    probability_pass = complete and arms[0]["trace"]["integer_probability_stream_sha256"] == arms[1]["trace"]["integer_probability_stream_sha256"]
    trace_pass = complete and arms[0]["trace"]["residual_trace"]["sha256"] == arms[1]["trace"]["residual_trace"]["sha256"] and arms[0]["trace"]["byte_trace"]["sha256"] == arms[1]["trace"]["byte_trace"]["sha256"]
    payload_pass = complete and arms[0]["payload"]["sha256"] == arms[1]["payload"]["sha256"]
    inverse_pass = (
        complete
        and all(arm["raw_slice_inverse_pass"] for arm in arms)
        and arms[0]["restored"]["sha256"] == arms[1]["restored"]["sha256"] == slice_sha256
    )
    cleanup_pass = complete and not scratch_root.exists() and all(arm["backing_cleanup_pass"] for arm in arms)
    resource_pass = complete and all(arm["encode_guard_pass"] and arm["decode_guard_pass"] for arm in arms)
    terminal_pass = not errors and probability_pass and trace_pass and payload_pass and inverse_pass and cleanup_pass and resource_pass
    guards = [value for arm in arms for value in guard_values(arm)] if complete else []
    resource_summary = {
        "guard_count": len(guards),
        "maximum_tree_rss_kib": max((value["max_sampled_tree_rss_kib"] for value in guards), default=0),
        "maximum_temporary_disk_bytes": max((value["max_sampled_temporary_disk_bytes"] for value in guards), default=0),
        "maximum_allowed_cpu_count": max((value["max_sampled_allowed_cpu_count"] for value in guards), default=0),
        "all_guards_pass": resource_pass,
    }
    receipt = {
        "schema": SCHEMA,
        "candidate_id": scope.CANDIDATE_ID,
        "authoritative_parent_id": scope.PARENT_ID,
        "population": scope.artifact(corpus),
        "offset": OFFSET,
        "bytes": LENGTH,
        "slice_sha256": slice_sha256,
        "result_filesystem_type": result_fs,
        "scratch_filesystem_type": scratch_fs,
        "selected_logical_cpu": cpu,
        "runner": scope.artifact(Path(__file__).resolve(strict=True)),
        "scope_primitive": scope.artifact(Path(scope.__file__).resolve(strict=True)),
        "antecedents": {
            "scope_build_receipt": scope.artifact(build_path),
            "program_lock_verification": scope.artifact(lock_path),
            "allocator_negative_controls": scope.artifact(controls_path),
            "allocator_positive_fixture": scope.artifact(positive_path),
            "scope_identity_receipt": scope.artifact(prior_path),
        },
        "arms": arms,
        "aggregate": {
            "parent_probability_stream_sha256": aggregate["parent"].hexdigest(),
            "candidate_probability_stream_sha256": aggregate["candidate"].hexdigest(),
            "identity_pass": complete and aggregate["parent"].digest() == aggregate["candidate"].digest(),
        },
        "resources": resource_summary,
        "decisions": {
            "exact_integer_probability_identity_pass": probability_pass,
            "full_trace_identity_pass": trace_pass,
            "payload_identity_pass": payload_pass,
            "both_arms_exact_inverse_pass": inverse_pass,
            "candidate_backing_cleanup_pass": cleanup_pass,
            "resource_guard_pass": resource_pass,
            "cumulative_1m_identity_pass": terminal_pass,
            "full_stream_identity_established": False,
            "memory_safe_parent_qualified": False,
            "promotion_authorized": False,
        },
        "errors": errors,
        "terminal_pass": terminal_pass,
        "claim_authority": "cumulative_opening_1m_identity_only",
        "claim_boundary": "Exact cumulative opening-1M probability, full-trace, payload, two-arm inverse, guarded resource, and cleanup evidence. This is not full-stream or prize qualification and grants no compression credit.",
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    scope.write_new(receipt_path, receipt)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
