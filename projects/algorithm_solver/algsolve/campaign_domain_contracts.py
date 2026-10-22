"""Pure domain-successor admission planning; never writes a ledger or runs code.

This is a review prototype, not an installed campaign admission route. Artifact
hashes establish identity, not truth. A reviewed host replay and independent human
or agent review remain required; receipt strings are not cryptographic signatures.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

PROFILE = "assigned20-pinned-domain-v2"
APPROVED_IDS = frozenset((764, 765, 775, 777, 778, 779, 785, 787, 793,
                          795, 804, 807, 1260, 1275, 1287))
HISTORICAL = {"total": 3720, "passed": 3629, "failed": 91}
HEX = re.compile(r"[0-9a-f]{64}\Z")


class Rejected(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def count(value, label, minimum=0):
    require(type(value) is int and value >= minimum, "Invalid integer: " + label)
    return value


def identity(value):
    require(type(value) is str and value.strip() == value and value,
            "Missing or ambiguous actor identity")
    return value.casefold()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON field")
        result[key] = value
    return result


class Store:
    """A bounded, read-only content-addressed metadata store.

    The root is selected by the coordinator, not an artifact. References cannot
    traverse symlinks or escape it. Candidate source can be hash-verified as opaque
    bytes but is never imported, parsed as Python/JS, or executed.
    """
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)

    def bytes(self, ref):
        require(type(ref) is dict and {"path", "sha256"} <= set(ref) <= {"path", "sha256", "origin"}, "Invalid artifact reference")
        require(type(ref["sha256"]) is str and HEX.fullmatch(ref["sha256"]), "Invalid SHA256")
        path = Path(ref["path"])
        require(path.is_absolute() and ".." not in path.parts, "Nonabsolute or traversing artifact path")
        require(path.is_relative_to(self.root), "Artifact outside approved package root")
        for part in (path, *path.parents):
            if part == self.root:
                break
            require(not part.is_symlink(), "Symlink artifact rejected")
        require(path.is_file(), "Artifact is not a regular file")
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == ref["sha256"], "Artifact hash changed")
        return data

    def json(self, ref):
        data = self.bytes(ref)
        require(len(data) <= 16 * 1024 * 1024, "Metadata artifact too large")
        def invalid_constant(value):
            raise Rejected("Non-finite JSON constant")
        try:
            result = json.loads(data, object_pairs_hook=unique_object,
                                parse_constant=invalid_constant)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise Rejected("Invalid JSON artifact") from error
        require(type(result) is dict, "Metadata must be an object")
        return result


@dataclass(frozen=True)
class Authority:
    """Externally pinned by the coordinator; never accepted from the bundle."""
    policy_sha256: str
    approval_sha256: str
    boundary_sha256: str
    replay_validator_sha256: str


def exact_flags(value, fields):
    for name, expected in fields.items():
        require(type(value.get(name)) is bool and value[name] is expected,
                "Failed or missing boolean: " + name)


def check_manifest(store, ref, kind, problem_id, protocol_ref):
    manifest = store.json(ref)
    require(manifest.get("schema") == "gamma.domain-case-registry.v1", "Wrong case registry schema")
    require(manifest.get("kind") == kind and manifest.get("problem_id") == problem_id,
            "Wrong case registry identity")
    require(manifest.get("protocol") == protocol_ref, "Case protocol mismatch")
    require(manifest.get("population") == "exposed-development", "Population relabeled")
    exact_flags(manifest, {"expected_values_from_candidate": False,
                           "complete_frozen_suite": True,
                           "independent_oracle_reviewed": True})
    if kind == "successor":
        require(manifest.get("construction") == "fresh-generated-not-filtered-v1",
                "Filtered legacy cases cannot become successor qualification")
    else:
        require(manifest.get("construction") == "complete-pinned-statement-examples",
                "Public tests must recover the complete pinned examples")
    cases = manifest.get("cases")
    require(type(cases) is list and cases, "Empty case registry")
    require(count(manifest.get("count"), "case count", 1) == len(cases), "Case count mismatch")
    seen = set()
    for case in cases:
        require(set(case) == {"id", "input_sha256", "expected_sha256", "comparison_sha256"},
                "Incomplete or unexpected case identity")
        require(type(case["id"]) is str and case["id"] and case["id"] not in seen,
                "Duplicate or invalid case ID")
        seen.add(case["id"])
        for key in ("input_sha256", "expected_sha256", "comparison_sha256"):
            require(type(case[key]) is str and HEX.fullmatch(case[key]), "Invalid case hash")
    generation = store.json(manifest["generation_receipt"])
    review = store.json(manifest["oracle_review"])
    require(generation.get("schema") == "gamma.fresh-suite-generation.v1" and
            generation.get("protocol") == protocol_ref and
            generation.get("problem_id") == problem_id and
            generation.get("kind") == kind and
            generation.get("case_identity_sha256") == digest(cases), "Unbound suite generation")
    exact_flags(generation, {"expected_values_from_candidate": False,
                             "original_v1_tests_modified": False})
    require(review.get("schema") == "gamma.fresh-suite-review.v1" and
            review.get("status") == "passed" and review.get("unresolved") == [] and
            review.get("generation_receipt") == manifest["generation_receipt"],
            "Incomplete independent suite review")
    require(identity(review.get("reviewer")) != identity(generation.get("author")),
            "Suite author cannot independently review its oracle")
    exact_flags(review, {"pinned_domain_checked": True,
                        "independent_derivation_checked": True,
                        "all_generated_expected_values_cross_checked": True,
                        "candidate_reference_code_read": False})
    return manifest


def _plan(ledger, key, owner, token, expected_revision, policy_ref, bundle_ref,
          store, authority):
    require(ledger.get("schema") == "algsolve.corpus-campaign.v1", "Wrong ledger schema")
    require(count(ledger.get("revision"), "ledger revision") == expected_revision,
            "Stale ledger revision")
    require(policy_ref["sha256"] == authority.policy_sha256, "Unapproved policy")
    policy = store.json(policy_ref)
    require(policy.get("schema") == "gamma.domain-successor-policy.v1" and
            policy.get("profile_id") == PROFILE, "Wrong successor policy")
    require(set(policy.get("approved_ids", [])) == APPROVED_IDS, "Approval scope widened or narrowed")
    require(policy.get("population") == "exposed-development", "Policy population relabeled")
    require(policy["approval"]["sha256"] == authority.approval_sha256, "Wrong owner approval")
    approval = store.json(policy["approval"])
    require(approval.get("schema") == "gamma.assigned20.domain-successor-approval.v1" and
            approval.get("user_answer") == "Yes I approve" and
            set(approval.get("ids", [])) == APPROVED_IDS, "Invalid approved scope")
    invariant = approval["invariant"]
    require(invariant.get("original_v1_tests_and_hashes") == "unchanged" and
            {k: invariant.get("original_" + k) for k in HISTORICAL} == HISTORICAL,
            "Original failure history changed")
    require(policy.get("domain_resolutions") == {
        "765": "integer couple count 2..30 including odd",
        "787": "n>=1; distinct valid source/destination; n=1 legal slice empty",
        "764": "at least one mine"}, "Approved domain resolution changed")
    store.bytes(policy["decision"])
    protocol = store.json(policy["protocol"])
    require(protocol.get("status") == "frozen-before-execution", "Protocol was not frozen")
    require(protocol.get("population") == "exposed-development", "Protocol population changed")
    exact_flags(protocol, {"candidate_expected_values": False, "legacy_filtering": False})
    require(policy["boundary"]["sha256"] == authority.boundary_sha256, "Boundary registry changed")
    boundary = store.json(policy["boundary"])
    require(boundary.get("schema") == "gamma.domain-boundary-clearance.v1", "Wrong boundary registry")
    for ref in boundary.get("protected_registry_refs", []):
        store.bytes(ref)
    require(boundary.get("protected_registry_refs"), "Missing protected-registry closure")
    clear = boundary["entries"][key]
    exact_flags(clear, {"id_key_slug_family_uid_clear": True, "protected_overlap": False,
                       "other_owner_overlap": False, "development_eligible": True})
    e = ledger["entries"][key]
    require(e["id"] in APPROVED_IDS and e["status"] == "claimed", "Not an approved held claim")
    require(e["claim"] and e["claim"].get("owner") == owner and e["claim"].get("token") == token,
            "Claim owner/token mismatch")
    require(not e.get("reservation"), "External reservation requires separate reconciliation")
    require(not e["attempts"] or e["attempts"][-1]["status"] != "staged", "Existing staged attempt")
    for other_key, other in ledger["entries"].items():
        if other_key != key and other.get("family") == e["family"] and other.get("claim"):
            require(other["claim"]["owner"] == owner, "Family owned by another writer")
    entry_policy = policy["entries"][key]
    require(entry_policy["ledger_entry_sha256"] == digest(e), "Claim/entry changed since policy freeze")
    require(clear["entry_identity"] == {k: e[k] for k in ("id", "key", "language", "family")},
            "Boundary identity mismatch")
    source_sha = e["source"]["sha256"] if e.get("source") else None
    require(entry_policy["source_sha256"] == source_sha and
            entry_policy["independent_sets"] == e["independent_sets"], "Original pins changed")

    # The full v1 run stays a failing whole-run result. Per-entry compatibility is
    # retained regardless of whether this particular entry happened to pass v1.
    history = store.json(policy["v1_run"])
    require(history.get("status") == "completed", "Missing completed v1 history")
    old_rows = history.get("entries")
    require(type(old_rows) is list and len(old_rows) == 40, "Partial v1 history")
    require(len({r["entry"] for r in old_rows}) == 40, "Duplicate v1 entries")
    totals = {"total": sum(count(r["total"], "v1 total") for r in old_rows),
              "passed": sum(count(r["passed"], "v1 passed") for r in old_rows)}
    totals["failed"] = totals["total"] - totals["passed"]
    require(totals == HISTORICAL, "Full v1 counts changed")
    prior = next((r for r in old_rows if r["entry"] == key), None)
    require(prior is not None, "Missing entry v1 result")
    require(prior["total"] == sum(t["tests"] for t in e["independent_sets"]), "Partial entry v1 history")
    require(entry_policy["v1_entry_result_sha256"] == digest(prior), "Entry v1 history changed")
    require(policy["v1_run"]["sha256"] == entry_policy["v1_run_sha256"], "V1 history identity mismatch")
    require(policy.get("v1_preservation_artifacts"), "Missing original artifacts")
    for ref in policy["v1_preservation_artifacts"]:
        store.bytes(ref)

    bundle = store.json(bundle_ref)
    require(set(bundle) == {"schema", "contract", "standard", "execution", "review", "replay"} and
            bundle["schema"] == "gamma.domain-admission-bundle.v1", "Incomplete evidence bundle")
    c = store.json(bundle["contract"])
    require(c.get("schema") == "algsolve.campaign-contract.domain-successor.v1" and
            c.get("profile_id") == PROFILE and c.get("entry") == key, "Wrong contract identity")
    require(c.get("policy") == policy_ref and c.get("population") == "exposed-development",
            "Contract authority mismatch")
    require(c.get("independent_sets") == e["independent_sets"], "Contract changed legacy pins")
    require(c.get("comparison") == "fresh-pinned-domain-v2-with-preserved-v1" and
            c.get("interface") == "exact-public-adapter", "Contract/comparison weakened")
    require(c.get("domain") == entry_policy["domain"], "Pinned domain changed")
    store.bytes(c["domain"])
    require(c.get("source_sha256") == source_sha and
            c.get("candidate") == entry_policy["candidate"], "Candidate/source binding mismatch")
    store.bytes(c["candidate"])
    for field in ("mutation_contract", "alias_contract", "complexity_contract"):
        require(type(c.get(field)) is str and c[field].strip(), "Missing " + field)
    require(c.get("source_author") == entry_policy["source_author"], "Source author mismatch")
    author = identity(c["source_author"])
    require(identity(policy["coordinator"]) != author, "Source author cannot approve policy")
    require(c.get("successor_registry") == entry_policy["successor_registry"] and
            c.get("public_registry") == entry_policy["public_registry"], "Frozen registry changed")
    successor = check_manifest(store, c["successor_registry"], "successor", e["id"], policy["protocol"])
    public = check_manifest(store, c["public_registry"], "public", e["id"], policy["protocol"])
    require(c.get("runtime") == entry_policy["runtime"], "Runtime changed")
    store.bytes(c["runtime"])
    require(c.get("standard") == entry_policy["standard"], "Standard changed")
    store.bytes(c["standard"])
    receipts = {kind: store.json(bundle[kind]) for kind in ("standard", "execution", "review", "replay")}
    for kind, receipt in receipts.items():
        require(receipt.get("schema") == "gamma.domain-evidence.v1" and
                receipt.get("kind") == kind and receipt.get("entry") == key and
                receipt.get("status") == "passed" and receipt.get("contract") == bundle["contract"] and
                receipt.get("candidate_sha256") == c["candidate"]["sha256"] and
                receipt.get("policy_sha256") == policy_ref["sha256"], "Wrong or failed " + kind + " binding")
        require(type(receipt.get("artifacts")) is list and receipt["artifacts"], "No underlying artifacts")
        for ref in receipt["artifacts"]:
            store.bytes(ref)
    standard = receipts["standard"]
    require(standard.get("standard") == c["standard"] and standard.get("errors") == [], "Standard failed")
    exact_flags(standard, {"idempotent": True, "semantic_roles_complete": True})
    execution = receipts["execution"]
    require(execution.get("runtime") == c["runtime"], "Execution runtime changed")
    exact_flags(execution, {"sandboxed": True, "expected_outputs_in_sandbox": False,
                            "mutation_passed": True, "alias_passed": True,
                            "runtime_verified_before_after": True})
    require(count(execution.get("infrastructure_errors"), "infrastructure errors") == 0, "Infrastructure errors")
    expected_cases = [{"group": group, "case": case} for group, manifest in
                      (("successor", successor), ("public", public)) for case in manifest["cases"]]
    require(execution.get("case_identity_sha256") == digest(expected_cases), "Execution case order/identity mismatch")
    for group, manifest in (("successor", successor), ("public", public)):
        require(execution.get(group + "_registry") == c[group + "_registry"], "Execution registry mismatch")
        require(count(execution.get(group + "_total"), group + " total", 1) == manifest["count"] and
                count(execution.get(group + "_passed"), group + " passed") == manifest["count"],
                "Incomplete " + group + " evidence")
    replay = receipts["replay"]
    require(replay.get("execution") == bundle["execution"] and
            replay.get("validator", {}).get("sha256") == authority.replay_validator_sha256 and
            replay.get("case_identity_sha256") == digest(expected_cases), "Unbound saved-output replay")
    store.bytes(replay["validator"])
    exact_flags(replay, {"complete_contiguous_coverage": True, "raw_observations_rescored": True,
                        "candidate_execution": False, "all_controls_passed": True,
                        "source_runtime_test_hashes_verified": True})
    require(identity(replay.get("reviewer")) != author, "Source author cannot independently replay")
    review = receipts["review"]
    require(identity(review.get("reviewer")) not in (author, identity(owner)), "Reviewer not independent")
    require(review.get("unresolved") == [], "Unresolved review findings")
    exact_flags(review, {"semantic_role_mapping_reviewed": True, "complexity_reviewed": True,
                        "domain_coverage_reviewed": True, "mutation_alias_reviewed": True,
                        "v1_preservation_reviewed": True, "fresh_oracle_independence_reviewed": True})
    require(review.get("replay") == bundle["replay"], "Review does not bind completed replay")

    # A proposed entry only. Caller may inspect it, but no disk write or ledger
    # transaction is exposed. A future installed route must snapshot every input.
    result = deepcopy(e)
    result["attempts"].append({"number": len(e["attempts"]) + 1, "status": "passed",
        "qualification_profile": PROFILE, "owner": owner, "source_sha256": source_sha,
        "normalized": deepcopy(c["candidate"]), "contract": deepcopy(bundle["contract"]),
        "evidence": deepcopy(bundle_ref), "legacy_compatibility": {
            "run": deepcopy(policy["v1_run"]), "entry_result": deepcopy(prior),
            "whole_run": deepcopy(HISTORICAL), "relabeled": False}})
    result["normalized"] = deepcopy(c["candidate"])
    result["qualification_profile"] = PROFILE
    result["qualification_population"] = "exposed-development"
    result["status"] = "complete"
    result["claim"] = None
    result["blockers"] = []
    result["revision"] += 1
    require(result["independent_sets"] == e["independent_sets"] and
            result["attempts"][:-1] == e["attempts"], "Preservation invariant violated")
    return {"schema": "gamma.domain-transition-plan.v1", "operational": False,
            "entry": key, "expected_ledger_revision": expected_revision,
            "old_entry_sha256": digest(e), "proposed_entry": result,
            "qualification_profile": PROFILE, "legacy_whole_run": HISTORICAL.copy(),
            "requires": ["independent implementation review", "canonical downgrade guard",
                         "compatibility transition for pinned admission modules",
                         "content-addressed snapshotting", "atomic expected-revision transaction"],
            "ledger_mutated": False, "candidate_executed": False}


def plan(ledger, key, owner, token, expected_revision, policy_ref, bundle_ref,
         store, authority):
    """Return a proposal only; never mutate the supplied ledger, including failure."""
    try:
        return _plan(ledger, key, owner, token, expected_revision, policy_ref,
                     bundle_ref, store, authority)
    except Rejected:
        raise
    except (KeyError, TypeError, IndexError, OSError, ValueError) as error:
        raise Rejected("Malformed or missing evidence: " + str(error)) from error
