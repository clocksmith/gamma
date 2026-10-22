"""Explicit domain-successor route; no candidate code is imported or executed.

Legacy routing has an inline guard. This module's separate CLI uses
the unchanged canonical transaction and content-addressed snapshot machinery.
The pinned host replay is trusted reviewed tooling, never a candidate or oracle.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import stat

from . import corpus_campaign as campaign
from . import campaign_domain_contracts as contract_gate

POLICY = "domain_successor_policy"
INSTALLATION = "domain_successor_installation"
ENTRIES = {f"{number:04d}:{language}" for number in contract_gate.APPROVED_IDS
           for language in ("javascript", "python")}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def verified_bytes(reference, *, opaque=False):
    path = Path(reference["path"])
    need(path.is_absolute() and str(path) == os.path.normpath(str(path)) and
         not any(part.is_symlink() for part in (path, *path.parents)), "Ordinary artifact path required")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        need(stat.S_ISREG(before.st_mode), "Regular artifact required")
        hasher, chunks, total = hashlib.sha256(), [], 0
        while True:
            raw = os.read(descriptor, 1024 * 1024)
            if not raw:
                break
            hasher.update(raw)
            if not opaque:
                total += len(raw)
                need(total <= 32 * 1024**2, "Metadata size limit exceeded")
                chunks.append(raw)
        after = os.fstat(descriptor)
        names = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        need(all(getattr(before, name) == getattr(after, name) for name in names) and
             path.stat(follow_symlinks=False).st_ino == after.st_ino, "Artifact changed during verification")
        need(hasher.hexdigest() == reference["sha256"], "Artifact hash changed")
        return after.st_size if opaque else b"".join(chunks)
    finally:
        os.close(descriptor)


def checked(reference):
    return json.loads(verified_bytes(reference), object_pairs_hook=contract_gate.unique_object)


def plain(reference):
    return {name: reference[name] for name in ("path", "sha256")}


def required(data, entry):
    reference = data.get("inputs", {}).get(POLICY)
    if reference is None:
        need(INSTALLATION not in data.get("inputs", {}), "Incomplete domain policy installation")
        return False
    policy = checked(reference)
    need(policy.get("schema") == "gamma.domain-successor-policy.v1" and
         policy.get("profile_id") == contract_gate.PROFILE and
         policy.get("status") == "approved" and policy.get("approved_by") == "/root" and
         type(policy.get("entries")) is dict and set(policy["entries"]) == ENTRIES,
         "Domain policy must preserve exactly 15 approved pairs")
    need(INSTALLATION in data.get("inputs", {}), "Domain installation authority missing")
    return f"{entry['id']:04d}:{entry['language']}" in policy["entries"]


def reject_legacy(data, entry):
    need(not required(data, entry),
         "Registered domain-successor entry requires explicit domain route; legacy downgrade forbidden")


def authority(data):
    installation_ref = data["inputs"][INSTALLATION]
    installed = checked(installation_ref)
    need(installed.get("schema") == "gamma.domain-admission-installation.v1" and
         installed.get("status") == "approved" and installed.get("approved_by") == "/root",
         "Reviewed domain installation authority required")
    need(installed.get("policy_sha256") == data["inputs"][POLICY]["sha256"], "Installed policy drift")
    folder = Path(__file__).resolve().parent
    for name, wanted in installed["installed_modules"].items():
        need(Path(name).name == name and hashlib.sha256((folder / name).read_bytes()).hexdigest() == wanted,
             "Installed domain module drift")
    need(set(installed["installed_modules"]) == {
        "campaign_domain_successor.py", "campaign_domain_contracts.py", "campaign_868_dispatch.py",
        "corpus_campaign.py"}, "Incomplete domain module closure")
    review = checked(installed["independent_implementation_review"])
    need(review.get("schema") == "gamma.domain-admission.independent-integration-review.v1" and
         review.get("status") == "passed" and review.get("unresolved") == [] and
         review.get("admission_implementation_approved") is True and
         review.get("reviewer") not in (None, "", "/root", "/root/domain_successor_admission"),
         "Complete independent admission implementation review required")
    reviewed = {ref["sha256"] for ref in review.get("inputs", [])}
    need(set(installed["installed_modules"].values()) <= reviewed and
         installed["replay_validator_sha256"] in reviewed, "Implementation review module binding incomplete")
    raw_receipt = checked(installed["host_replay"]["replay_receipt"])
    raw_root = Path(installed["raw_evidence_root"])
    raw_hashes = raw_receipt.get("raw_evidence_sha256")
    need(type(raw_hashes) is dict and raw_hashes, "Raw replay evidence manifest missing")
    need(all(Path(name).name == name for name in raw_hashes), "Invalid raw evidence filename")
    need(installed["raw_evidence_files"] == [
        {"path": str(raw_root / name), "sha256": raw_hashes[name]} for name in sorted(raw_hashes)],
        "Raw evidence closure differs from reviewed replay manifest")
    policy = checked(data["inputs"][POLICY])
    expected = contract_gate.Authority(data["inputs"][POLICY]["sha256"],
        installed["approval_sha256"], installed["boundary_sha256"], installed["replay_validator_sha256"])
    return installed, policy, contract_gate.Store(installed["package_root"]), expected


def replay(installed, policy, bundle, store, key):
    """Run only the reviewed host verifier pinned by installed coordinator authority.

    All imports/dependencies must be frozen in the installed replay descriptor.
    Its exact adapter API accepts data references and returns a fresh verification
    result. No shell, subprocess, candidate, harness or oracle is loaded here.
    """
    spec = installed["host_replay"]
    need(spec["entrypoint"] == "verify_for_admission", "Unsupported host replay API")
    need(spec["module"]["sha256"] == installed["replay_validator_sha256"], "Replay authority mismatch")
    for reference in [spec["module"], *spec["dependencies"]]:
        store.bytes(reference)
    code = store.bytes(spec["module"])
    # This module is independent coordinator-reviewed tooling. Its hash cannot be
    # chosen by a source author through the evidence bundle.
    namespace = {"__name__": "_gamma_reviewed_domain_replay", "__file__": spec["module"]["path"]}
    exec(compile(code, spec["module"]["path"], "exec"), namespace)
    function = namespace.get("verify_for_admission")
    need(callable(function), "Reviewed replay entrypoint missing")
    result = function(policy["entries"][key], bundle, policy)
    need(type(result) is dict and result.get("schema") == "gamma.domain-live-replay.v1" and
         result.get("entry") == key and result.get("passed") is True and
         result.get("candidate_executed") is False and result.get("expected_values_changed") is False,
         "Fresh saved-output replay failed")
    execution = store.json(bundle["execution"])
    need(result.get("execution_sha256") == bundle["execution"]["sha256"] and
         result.get("case_identity_sha256") == execution["case_identity_sha256"] and
         type(result.get("successor_total")) is int and
         result["successor_total"] == execution["successor_total"] and
         type(result.get("public_total")) is int and result["public_total"] == execution["public_total"],
         "Fresh replay binding/count mismatch")
    for reference in [spec["module"], *spec["dependencies"]]:
        store.bytes(reference)
    return result


def verify_boundary(data, key, installed):
    """Recheck all identities behind the reviewed metadata-only clearance.

    A changed registry requires a new closure computation and independent review;
    this function never decodes protected source, statements or test payloads.
    Caller runs inside the unchanged canonical ledger transaction.
    """
    proof = installed["current_boundary"]
    assignment = checked(proof["assignment"])
    freeze = checked(proof["freeze"])
    need(assignment.get("schema") == "gamma.coordinator-assignment.public-safe.v1" and
         assignment.get("assignment_id") == "gamma-dot-assignment-20-v1" and
         assignment.get("problem_count") == 20 and len(assignment.get("problems", [])) == 20,
         "Wrong reviewed assignment")
    need(freeze.get("schema") == "gamma.coordinator-freeze.v1" and
         assignment["boundary_proof"]["freeze_sha256"] == proof["freeze"]["sha256"] and
         assignment["boundary_proof"].get("source_metadata_hashes_rechecked_before_claim") is True,
         "Assignment does not bind reviewed boundary closure")
    expected = {
        "contracts/js_corpus_reservations_v1.json", "contracts/sample_manifest.json",
        "contracts/typed_confirmation_v1.json", "data/derived/corpus_entries.jsonl",
        "data/derived/index_entries.jsonl", "data/derived/near_duplicates.json",
        "data/derived/problems.jsonl", "runs/typed-real-dev-v5/pairs.jsonl"}
    base = Path(proof["repository_root"])
    need(base.is_absolute() and not base.is_symlink(), "Ordinary boundary repository required")
    need(set(freeze["metadata_inputs"]) == {str(base / name) for name in expected},
         "Incomplete current protected registry closure")
    # Hash complete files as opaque bytes; none are parsed here. Installation
    # authority pins the approved projection/closure result represented above.
    for path, descriptor in freeze["metadata_inputs"].items():
        reference = {"path": path, "sha256": descriptor["sha256"]}
        need(verified_bytes(reference, opaque=True) == descriptor["bytes"], "Boundary registry size changed")
    reservation_path = str(base / "contracts/js_corpus_reservations_v1.json")
    need(plain(data["inputs"]["reservations"]) == {
        "path": reservation_path, "sha256": freeze["metadata_inputs"][reservation_path]["sha256"]},
        "Live reservation registry reference changed")
    entry = data["entries"][key]
    matches = [row for row in assignment["problems"] if row.get("id") == entry["id"]]
    need(len(matches) == 1, "Assignment ID is absent or duplicated")
    row = matches[0]
    need(row["key"] == entry["key"] and row["family"] == entry["family"] and
         row["key"] == "lc:" + row["slug"], "Reviewed ID/key/slug/family identity changed")
    need({(r["entry"], r["language"]) for r in row["entries"]} ==
         {(f"{entry['id']:04d}:" + language, language) for language in ("javascript", "python")},
         "Reviewed language entry identity changed")
    need(len(entry["independent_sets"]) == 1 and
         entry["independent_sets"][0]["uid"] == row["independent_test_identity"]["uid"] and
         entry["independent_sets"][0]["uid"] == "lcd:" + str(entry["id"]),
         "Reviewed record UID changed")
    need(row["boundary_clearance"] == {
        "id_key_slug_family_uid_checked": True, "protected_or_research_overlap": False,
        "external_reservation": False, "historical_claim_overlap": False,
        "dot_prior_draft_or_statement_exposure": False}, "Reviewed boundary clearance failed")
    need(entry.get("reservation") is None, "Live entry reservation changed")
    claim = entry.get("claim")
    need(type(claim) is dict and claim.get("owner") == assignment["owner"],
         "Live assignment owner changed")
    for other_key, other in data["entries"].items():
        if other_key == key or other.get("family") != entry["family"]:
            continue
        need(other.get("reservation") is None, "Live family reservation conflicts")
        if other.get("claim"):
            need(other["claim"].get("owner") == claim["owner"], "Live family owner conflicts")
    return {"assignment_sha256": proof["assignment"]["sha256"],
            "freeze_sha256": proof["freeze"]["sha256"], "registries": len(expected)}


def validate(data, key, owner, token, bundle_ref):
    need(required(data, data["entries"][key]), "Entry lacks domain authority")
    installed, policy, store, expected = authority(data)
    verify_boundary(data, key, installed)
    # Do not combine independently authorized comparison or numeric profiles.
    for name, reference in data.get("inputs", {}).items():
        if name in (POLICY, INSTALLATION) or "policy" not in name:
            continue
        other = checked(reference)
        entries = other.get("entries", {})
        need(key not in entries and data["entries"][key]["key"] not in entries,
             "Combined domain/public/integer profiles are unsupported")
    bundle = store.json(bundle_ref)
    # The canonical transaction snapshots authority into artifacts/<sha>.
    # Contracts retain the reviewed original reference; authorize its exact
    # bytes by the installed policy digest, not by the relocated file path.
    contract_policy = store.json(bundle["contract"])["policy"]
    need(contract_policy["sha256"] == data["inputs"][POLICY]["sha256"],
         "Contract policy differs from installed policy identity")
    store.bytes(contract_policy)
    result = contract_gate.plan(data, key, owner, token, data["revision"],
        contract_policy, bundle_ref, store, expected)
    live_replay = replay(installed, policy, bundle, store, key)
    campaign.verify_source(data["entries"][key].get("source"))
    return result, live_replay, store


def all_references(value):
    if isinstance(value, dict):
        if (set(value) in ({"path", "sha256"}, {"path", "sha256", "origin"}) and
                isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str)):
            yield {"path": value["path"], "sha256": value["sha256"]}
        else:
            for item in value.values():
                yield from all_references(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_references(item)


def required_artifacts(policy_ref, policy, installation_ref, installed, bundle_ref, bundle, store):
    """Typed current dependencies; historical path/hash citations stay opaque."""
    references = [policy_ref, installation_ref, bundle_ref,
        installed["independent_implementation_review"],
        installed["current_boundary"]["assignment"], installed["current_boundary"]["freeze"],
        installed["host_replay"]["module"], installed["host_replay"]["replay_receipt"],
        *installed["host_replay"]["dependencies"]]
    references.extend(policy[name] for name in ("approval", "decision", "protocol", "boundary", "v1_run"))
    references.extend(policy["v1_preservation_artifacts"])
    for entry in policy["entries"].values():
        references.extend(entry[name] for name in
            ("domain", "candidate", "successor_registry", "public_registry", "runtime", "standard"))
        for kind in ("successor", "public"):
            registry = store.json(entry[kind + "_registry"])
            references.extend(registry[name] for name in ("protocol", "generation_receipt", "oracle_review"))
    references.extend(bundle[name] for name in ("contract", "standard", "execution", "review", "replay"))
    for kind in ("standard", "execution", "review", "replay"):
        references.extend(store.json(bundle[kind])["artifacts"])
    references.extend(installed["raw_evidence_files"])
    return references


def snapshot_closure(root, roots, approved_closure, required, store):
    """Copy a root-reviewed immutable closure without following arbitrary JSON."""
    need(type(approved_closure) is list and approved_closure, "Missing reviewed artifact closure")
    by_path = {}
    for reference in approved_closure:
        need(reference["path"] not in by_path, "Duplicate/conflicting approved artifact identity")
        by_path[reference["path"]] = reference["sha256"]
    references = [*roots, *approved_closure]
    identities = {(ref["path"], ref["sha256"]) for ref in references}
    need(all((ref["path"], ref["sha256"]) in identities for ref in required),
         "Reviewed artifact closure omits a current typed dependency")
    for reference in references:
        need(reference["path"] not in by_path or by_path[reference["path"]] == reference["sha256"],
             "Root artifact conflicts with approved closure")
        store.bytes(reference)
    seen, result = set(), []
    for reference in references:
        identity = (reference["path"], reference["sha256"])
        if identity in seen:
            continue
        seen.add(identity)
        snapshot = campaign.snapshot(root, reference["path"])
        need(snapshot["sha256"] == reference["sha256"], "Artifact changed during snapshot")
        result.append(snapshot)
    return result


def stage(data, key, owner, token, bundle_ref, root):
    result, replay_result, store = validate(data, key, owner, token, bundle_ref)
    entry = data["entries"][key]
    installed = checked(data["inputs"][INSTALLATION])
    policy = checked(data["inputs"][POLICY])
    bundle = store.json(bundle_ref)
    roots = [data["inputs"][POLICY], data["inputs"][INSTALLATION], bundle_ref]
    required_refs = required_artifacts(roots[0], policy, roots[1], installed, bundle_ref, bundle, store)
    snapshots = snapshot_closure(root, roots, installed["artifact_closure"], required_refs, store)
    attempt = {"number": len(entry["attempts"]) + 1, "owner": owner, "created": campaign.now(),
        "status": "staged", "qualification_profile": contract_gate.PROFILE,
        "base_entry_sha256": result["old_entry_sha256"], "base_entry_revision": entry["revision"],
        "policy": deepcopy(data["inputs"][POLICY]), "installation": deepcopy(data["inputs"][INSTALLATION]),
        "bundle": deepcopy(bundle_ref), "snapshots": snapshots, "stage_replay": replay_result}
    entry["attempts"].append(attempt)
    entry["status"] = "staged"
    campaign.event(data, entry, "domain-stage", owner, attempt=attempt["number"], profile=contract_gate.PROFILE)
    return deepcopy(attempt)


def record(data, key, owner, token, root):
    entry = data["entries"][key]
    campaign.owned(entry, owner, token)
    need(entry["status"] == "staged" and entry["attempts"], "No domain attempt staged")
    staged = entry["attempts"][-1]
    need(staged.get("status") == "staged" and staged.get("qualification_profile") == contract_gate.PROFILE,
         "Wrong staged profile")
    need(staged["policy"] == data["inputs"][POLICY] and staged["installation"] == data["inputs"][INSTALLATION],
         "Staged domain authority changed")
    for reference in staged["snapshots"]:
        campaign.verify(reference)
    baseline = deepcopy(entry)
    baseline["attempts"].pop()
    baseline["status"] = "claimed"
    baseline["revision"] = staged["base_entry_revision"]
    need(entry["revision"] == baseline["revision"] + 1 and
         contract_gate.digest(baseline) == staged["base_entry_sha256"], "Staged entry changed")
    check_data = dict(data)
    check_data["entries"] = dict(data["entries"])
    check_data["entries"][key] = baseline
    result, replay_result, store = validate(check_data, key, owner, token, staged["bundle"])
    proposed = result["proposed_entry"]
    attempt = proposed["attempts"][-1]
    snapshots_by_hash = {reference["sha256"]: reference for reference in staged["snapshots"]}
    for field in ("normalized", "contract", "evidence"):
        attempt[field] = deepcopy(snapshots_by_hash[attempt[field]["sha256"]])
    proposed["normalized"] = deepcopy(attempt["normalized"])
    attempt.update(created=staged["created"], finished=campaign.now(),
                   snapshots=deepcopy(staged["snapshots"]), stage_replay=staged["stage_replay"],
                   admission_replay=replay_result)
    proposed["revision"] = entry["revision"]
    data["entries"][key] = proposed
    campaign.event(data, proposed, "domain-complete", owner,
                   attempt=attempt["number"], profile=contract_gate.PROFILE,
                   original_result="preserved; whole v1 run 3629/3720 with 91 failures")
    return {"status": "complete", "qualification_profile": contract_gate.PROFILE,
            "legacy_result_preserved": True}


def main():
    need(not sys.flags.optimize, "Optimized interpreter is not allowed")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--revision", type=int, required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--token", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    staged = commands.add_parser("stage")
    staged.add_argument("--bundle", type=Path, required=True)
    commands.add_parser("record")
    args = parser.parse_args()
    # The existing coordinator barrier must own this exact mutation child. This
    # complements the unchanged canonical ledger lock; it grants no authority.
    task = args.ledger.resolve().parent.parent
    state_path = task / "ledger-phase-state-v1.json"
    need(not state_path.is_symlink(), "Scheduling state must be ordinary")
    state = json.loads(state_path.read_bytes())
    active = state.get("active_mutation")
    need(state.get("phase") == "mutation-in-progress" and state.get("active") is None and
         type(active) is dict and active.get("child_pid") == os.getpid() and
         active.get("outcome") == "unknown", "Exact active mutation child required")
    lock = task / "ledger-phase-state-v1.lock"
    descriptor = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise ValueError("Scheduling mutation lock is not held")
    finally:
        os.close(descriptor)
    with campaign.transaction(args.ledger, args.revision) as data:
        if args.command == "stage":
            result = stage(data, args.entry, args.owner, args.token,
                           campaign.file_ref(args.bundle), args.ledger.parent)
        else:
            result = record(data, args.entry, args.owner, args.token, args.ledger.parent)
    print(json.dumps({"result": result, "ledger_revision": data["revision"]}, indent=2))


if __name__ == "__main__":
    main()
