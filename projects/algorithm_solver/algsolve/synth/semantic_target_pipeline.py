"""Freeze family exclusions before offline teacher target construction.

This is a development-data builder, not a training or evaluation runner. The
planner accepts identity metadata only. The builder calls payload/teacher/test
adapters only for the frozen training partition, and uses the existing typed
compiler and fail-closed sandbox judge. Nothing loads a reserved target.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys

from ..records import Problem
from ..splits import sibling_base
from . import typed_codec, typed_support


SCHEMA = "algsolve.semantic-target-plan.v1"
METADATA_FIELDS = {
    "uid", "key", "family", "aliases", "structural_groups",
    "problem_sha256", "independent_tests_sha256",
}


def digest(value):
    return typed_codec.digest(value)


def _string(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label}")
    return value


def _strings(values, label):
    if not isinstance(values, list):
        raise ValueError(f"{label} must be a list")
    return sorted({_string(value, label) for value in values})


def _hash(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("Expected a lowercase SHA-256 digest")
    return value


def _identities(row):
    aliases = [row["uid"], row["key"], *row["aliases"]]
    families = {row["family"], sibling_base(row["key"].removeprefix("lc:"))}
    families.update(sibling_base(a[3:]) for a in aliases if a.startswith("lc:"))
    return ({"identity:" + value for value in aliases}
            | {"family:" + value for value in families}
            | {"structure:" + value for value in row["structural_groups"]})


def _validate_allowlist(allowlist):
    if not isinstance(allowlist, dict) or set(allowlist) != {"uids", "keys", "sources_sha256"}:
        raise ValueError("Allowlist must contain uids, keys and sources_sha256")
    cleaned = copy.deepcopy(allowlist)
    for field in ("uids", "keys"):
        cleaned[field] = _strings(cleaned[field], f"allowlist.{field}")
    if not cleaned["uids"] and not cleaned["keys"]:
        raise ValueError("Allowlist must declare at least one authorized uid or key")
    sources = cleaned["sources_sha256"]
    if not isinstance(sources, dict) or not sources:
        raise ValueError("Allowlist must name its source hashes")
    for name, value in sources.items():
        _string(name, "allowlist source")
        _hash(value)
    return cleaned


def _row_is_allowlisted(row, allowlist):
    uid_set = set(allowlist["uids"])
    key_set = set(allowlist["keys"])
    if uid_set and row["uid"] not in uid_set:
        return False
    if key_set and row["key"] not in key_set:
        return False
    for alias in row["aliases"]:
        if key_set and alias.startswith("lc:") and alias not in key_set:
            return False
        if uid_set and not alias.startswith("lc:") and alias not in uid_set:
            return False
    return True


def require_linux_unchanged_sandbox():
    if sys.platform != "linux":
        raise RuntimeError("Native qualification requires the unchanged Linux sandbox; no macOS fallback")
    from ..judge import sandbox
    sandbox.check_available()


def freeze_plan(metadata, boundary, holdout_families, *, allowlist=None, recombination_uids=None):
    """Return a sealed plan using metadata, never statements, sources or tests.

    ``boundary`` is the caller's metadata-only union of existing reservations,
    including recorded aliases and structural groups. Its source hashes bind
    the existing authority; this function never edits or supersedes it.
    When ``allowlist`` is provided, unknown/unallowlisted entries and every
    connected alias, family or structural-group component stay excluded.
    When ``recombination_uids`` is provided, those fitting UIDs are held out
    for unfamiliar-combination testing while keeping seen families populated.
    Family labels must include known semantic relatedness, not just slug stems.
    """
    if set(boundary) != {"uids", "keys", "families", "structural_groups", "sources_sha256"}:
        raise ValueError("Incomplete reservation boundary")
    boundary = copy.deepcopy(boundary)
    for field in ("uids", "keys", "families", "structural_groups"):
        boundary[field] = _strings(boundary[field], field)
    sources = boundary["sources_sha256"]
    if not isinstance(sources, dict) or not sources:
        raise ValueError("Reservation boundary must name its source hashes")
    for name, value in sources.items():
        _string(name, "boundary source")
        _hash(value)
    if allowlist is not None:
        allowlist = _validate_allowlist(allowlist)
    if recombination_uids is not None:
        recombination_uids = _strings(recombination_uids, "recombination_uids")
        if not recombination_uids:
            raise ValueError("Declare nonempty recombination_uids when enabled")
    rows = []
    for original in metadata:
        if set(original) != METADATA_FIELDS:
            raise ValueError("Identity metadata must have exactly the declared fields; no payloads")
        row = copy.deepcopy(original)
        for field in ("uid", "key", "family"):
            _string(row[field], field)
        for field in ("aliases", "structural_groups"):
            row[field] = _strings(row[field], field)
        for field in ("problem_sha256", "independent_tests_sha256"):
            _hash(row[field])
        rows.append(row)
    rows.sort(key=lambda row: row["uid"])
    uid_set = {row["uid"] for row in rows}
    if not rows or len(uid_set) != len(rows):
        raise ValueError("Metadata must contain unique problem UIDs")
    if recombination_uids is not None and not set(recombination_uids) <= uid_set:
        raise ValueError("recombination_uids must reference metadata UIDs")
    holdouts = _strings(holdout_families, "holdout_families")
    known = set().union(*(_identities(row) for row in rows))
    if not holdouts or not {"family:" + f for f in holdouts} <= known:
        raise ValueError("Declare nonempty holdout families present in the metadata")

    # Connected components preserve aliases, semantic families and predeclared
    # structural sharing transitively, before any examples are generated.
    parent = {}

    def root(key):
        parent.setdefault(key, key)
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for row in rows:
        identities = sorted(_identities(row))
        for identity in identities[1:]:
            left, right = root(identities[0]), root(identity)
            parent[max(left, right)] = min(left, right)
    protected = {"identity:" + v for v in boundary["uids"] + boundary["keys"]}
    protected |= {"family:" + v for v in boundary["families"]}
    protected |= {"family:" + sibling_base(k[3:]) for k in boundary["keys"] if k.startswith("lc:")}
    protected |= {"structure:" + v for v in boundary["structural_groups"]}
    protected_roots = {root(value) for value in protected & known}
    unallowlisted_roots = set()
    if allowlist is not None:
        for row in rows:
            if not _row_is_allowlisted(row, allowlist):
                unallowlisted_roots.add(root("identity:" + row["uid"]))
    held_roots = {root("family:" + value) for value in holdouts}
    recomb_set = set(recombination_uids or ())
    members = {}
    for value in sorted(known):
        members.setdefault(root(value), []).append(value)
    assignments = []
    for row in rows:
        group = root("identity:" + row["uid"])
        split = (
            "excluded_existing" if group in protected_roots else
            "excluded_unallowlisted" if group in unallowlisted_roots else
            "heldout_family" if group in held_roots else
            "heldout_combination" if row["uid"] in recomb_set else
            "development_fit"
        )
        assignments.append({**row, "split": split, "split_group_sha256": digest(members[group])})
    counts = Counter(row["split"] for row in assignments)
    if not counts["development_fit"] or not counts["heldout_family"]:
        raise ValueError("Plan needs both training and newly held-out family components")
    if recombination_uids is not None:
        if counts["heldout_combination"] != len(recomb_set):
            raise ValueError("recombination_uids cannot target excluded or heldout_family rows")
        fit_families = {row["family"] for row in assignments if row["split"] == "development_fit"}
        recomb_families = {row["family"] for row in assignments if row["split"] == "heldout_combination"}
        if not recomb_families <= fit_families:
            raise ValueError("heldout_combination families must retain at least one development_fit example")
    body = {
        "schema": SCHEMA, "metadata_sha256": digest(rows),
        "boundary": boundary, "holdout_families": holdouts,
        "rows": assignments, "counts": dict(counts),
        "policy": "freeze before payload loading or generation; never build held-out or existing protected rows",
        "protected_scoring": False, "training": False,
    }
    if allowlist is not None:
        body["allowlist"] = allowlist
    if recombination_uids is not None:
        body["recombination_uids"] = recombination_uids
    return {**body, "plan_sha256": digest(body)}


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        raise ValueError("Unsupported semantic target plan")
    metadata = [{k: v for k, v in row.items() if k in METADATA_FIELDS} for row in plan["rows"]]
    expected = freeze_plan(
        metadata,
        plan["boundary"],
        plan["holdout_families"],
        allowlist=plan.get("allowlist"),
        recombination_uids=plan.get("recombination_uids"),
    )
    if plan != expected:
        raise ValueError("Frozen family plan changed or has inconsistent assignments")
    return expected


def write_plan(path, plan):
    validate_plan(plan)
    path = Path(path)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _public_input(problem):
    return copy.deepcopy({"statement": problem.statement, "starter_code": problem.starter_code,
                          "params": problem.params, "public_examples": problem.public_tests})


def _write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _passed(verdict, cases):
    # A generic truthy 'passed' or an empty/incomplete test receipt is not evidence.
    return (verdict.get("passed") is True and type(verdict.get("tests_passed")) is int
            and verdict["tests_passed"] == len(cases)
            and type(verdict.get("tests_total")) is int and verdict["tests_total"] == len(cases))


def _implementation_hashes():
    root = Path(__file__).parents[1]
    names = ["synth/semantic_target_pipeline.py", "synth/typed_support.py", "validate.py", "records.py"]
    paths = [root / name for name in names] + sorted((root / "judge").glob("*.py"))
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def build_targets(plan_path, output, *, codec_path, teacher_identity, load_problem,
                  propose, load_independent_tests, max_proposals=4, judge=None):
    """Build only the preselected development partition through lazy adapters.

    ``propose(uid, public_input, plan_sha256)`` returns a bounded list of offline
    typed proposals. It receives no reference solution or independent tests.
    ``load_problem(row)`` and ``load_independent_tests(row)`` must use already
    authorized local data. Their contents are checked against frozen hashes.
    Injecting ``judge`` is for unit tests only and disables training eligibility.
    A caller must separately authorize teacher compute or student training.
    """
    if type(max_proposals) is not int or not 1 <= max_proposals <= 32:
        raise ValueError("max_proposals must be between 1 and 32")
    _string(teacher_identity, "teacher identity")
    plan_path = Path(plan_path)
    plan_bytes = plan_path.read_bytes()
    plan = validate_plan(json.loads(plan_bytes))
    codec_path = Path(codec_path)
    identity = typed_codec.frozen(codec_path)
    test_double = judge is not None
    if judge is None:
        require_linux_unchanged_sandbox()
        from ..validate import judge_problem
        judge = judge_problem
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    binding = {
        "schema": "algsolve.semantic-target-build.v1", "plan_sha256": plan["plan_sha256"],
        "plan_file_sha256": hashlib.sha256(plan_bytes).hexdigest(), "codec_sha256": identity,
        "teacher": teacher_identity, "max_proposals_per_problem": max_proposals,
        "sources_sha256": _implementation_hashes(),
        "verification_authority": "injected-test-double" if test_double else "repository-sandbox",
        "training": False, "protected_scoring": False,
    }
    if "allowlist" in plan:
        binding["allowlist_sources_sha256"] = copy.deepcopy(plan["allowlist"]["sources_sha256"])
    _write_json(output / "contract.json", binding)
    (output / "attempts").mkdir()
    counts = Counter()
    pairs = []

    def unchanged():
        if (plan_path.read_bytes() != plan_bytes or typed_codec.frozen(codec_path) != identity
                or _implementation_hashes() != binding["sources_sha256"]):
            raise ValueError("Frozen plan, codec or implementation changed during target construction")

    for index, row in enumerate(plan["rows"]):
        if row["split"] != "development_fit":
            counts[row["split"]] += 1
            continue
        unchanged()  # Before any next payload/teacher callback.
        attempt = {"uid": row["uid"], "split_group_sha256": row["split_group_sha256"], "proposals": []}
        stage = "load_problem"
        try:
            if plan.get("allowlist") is not None and not _row_is_allowlisted(row, plan["allowlist"]):
                raise PermissionError(f"Row {row['uid']} is not in the frozen development allowlist")
            problem = load_problem(copy.deepcopy(row))
            if not isinstance(problem, Problem) or problem.uid != row["uid"]:
                raise ValueError("Problem adapter returned a different identity")
            if digest(json.loads(problem.to_json())) != row["problem_sha256"]:
                raise ValueError("Problem payload differs from the pre-generation metadata")
            if problem.io_mode != "functional" or not problem.public_tests or problem.evidence_ceiling != "independent_tests_passed":
                raise ValueError("Need functional public and independent test authority")
            stage = "offline_teacher"
            proposals = propose(row["uid"], _public_input(problem), plan["plan_sha256"])
            if not isinstance(proposals, list) or not 1 <= len(proposals) <= max_proposals:
                raise ValueError("Teacher must return a nonempty bounded proposal list")
            # Retain all raw attempts before compilation or private-test loading.
            attempt["raw_proposals"] = copy.deepcopy(proposals)
            _write_json(output / "attempts" / f"{index:06d}-proposals.json", attempt["raw_proposals"])
            unchanged()
            stage = "load_independent_tests"
            independent = load_independent_tests(copy.deepcopy(row))
            if not isinstance(independent, list) or not independent or digest(independent) != row["independent_tests_sha256"]:
                raise ValueError("Independent tests absent or changed from the frozen authority")
            variants = set()
            for proposal in proposals:
                record = {"reason": "rejected", "stage": "compile"}
                attempt["proposals"].append(record)
                try:
                    if not isinstance(proposal, dict) or set(proposal) != {"variant", "program", "requirements", "bound_probe"}:
                        raise ValueError("Malformed offline teacher proposal")
                    variant = _string(proposal["variant"], "variant")
                    if variant in variants:
                        raise ValueError("Duplicate proposal variant")
                    variants.add(variant)
                    record["variant"] = variant
                    requirements = proposal["requirements"]
                    if not isinstance(requirements, dict) or requirements.get("unsupported_requirements") != []:
                        raise ValueError("Missing or unsupported semantic requirements")
                    probe = proposal["bound_probe"]
                    if not isinstance(probe, dict) or not {"args", "expected"} <= set(probe):
                        raise ValueError("Missing declared-bound probe")
                    target = typed_codec.encode(proposal["program"], identity)
                    source = typed_codec.render(target, identity, method=problem.entry["method"],
                                                params=[p[0] for p in problem.params])
                    # Compile only; never execute generated code outside the judge.
                    compile(source, "<semantic-target>", "exec")
                    record["target_sha256"] = digest(target)
                    record["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
                    record["verdicts"] = {}
                    for label, cases in (("public", problem.public_tests), ("independent", independent),
                                         ("declared_bound_probe", [probe])):
                        record["stage"] = label
                        verdict = judge(problem, source, cases).to_dict()
                        record["verdicts"][label] = verdict
                        if not _passed(verdict, cases):
                            raise ValueError(f"{label} qualification failed: {verdict.get('reason', 'incomplete receipt')}")
                    record["reason"] = "qualified_test_double" if test_double else "qualified"
                    features = typed_support.features(proposal["program"])
                    pair = {
                        "schema": "algsolve.typed-pair.v1", "uid": row["uid"], "key": row["key"],
                        "variant": variant, "problem_family": row["family"], "input": _public_input(problem),
                        "target": target, "graph_sha256": digest(target),
                        "pattern_sha256": typed_support.pattern(proposal["program"]),
                        "required_features": features,
                        "recipe_usage": [feature.removeprefix("recipe:") for feature in features if feature.startswith("recipe:")],
                        "requirements": requirements, "learning_split": "development_fit",
                        "split_group_sha256": row["split_group_sha256"], "training_eligible": not test_double,
                        "provenance": {**binding, "problem_sha256": row["problem_sha256"],
                                       "independent_tests_sha256": row["independent_tests_sha256"],
                                       "source_sha256": record["source_sha256"],
                                       "license": problem.license, "attribution": problem.attribution,
                                       "public_tests_passed": len(problem.public_tests),
                                       "independent_tests_passed": len(independent),
                                       "declared_bound_probe_passed": True,
                                       "qualification": "finite public/independent tests and declared probe; not formal proof or benchmark acceptance"},
                    }
                    pairs.append(pair)
                except PermissionError:
                    raise
                except (ValueError, KeyError, TypeError, SyntaxError, RuntimeError, OSError) as error:
                    record["error"] = f"{type(error).__name__}: {error}"
                counts[record["reason"]] += 1
            attempt["reason"] = "processed"
        except PermissionError:
            raise
        except (ValueError, KeyError, TypeError, RuntimeError, OSError) as error:
            attempt.update(reason="blocked", stage=stage, error=f"{type(error).__name__}: {error}")
            counts["blocked"] += 1
        _write_json(output / "attempts" / f"{index:06d}-receipt.json", attempt)
        unchanged()

    unchanged()
    with (output / "pairs.jsonl").open("x", encoding="utf-8") as stream:
        for pair in pairs:
            stream.write(json.dumps(pair, sort_keys=True, allow_nan=False) + "\n")
    summary = {
        "schema": "algsolve.semantic-target-summary.v1", "plan_sha256": plan["plan_sha256"],
        "counts": dict(counts), "emitted_pairs": len(pairs),
        "training_eligible_pairs": sum(pair["training_eligible"] for pair in pairs),
        "training": False, "protected_scoring": False, "heldout_payloads_loaded": 0,
        "limits": ["This build supplies labels, not student or generalization evidence.",
                   "Held-out families remain unopened; no protected target coverage is inferred.",
                   "Semantic family and structural metadata completeness requires independent review.",
                   "Teacher compute authority and future training/evaluation are separate decisions."],
    }
    summary["artifacts_sha256"] = {
        str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*")) if path.is_file()
    }
    _write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True, help="Identity-only JSON array")
    parser.add_argument("--boundary", type=Path, required=True, help="Existing reservation metadata union")
    parser.add_argument("--allowlist", type=Path, default=None, help="Explicit authorized development allowlist JSON")
    parser.add_argument("--holdout-family", action="append", required=True)
    parser.add_argument("--recombination-uid", action="append", default=None, help="Fitting UID held out for unfamiliar combinations")
    parser.add_argument("--output", type=Path, required=True, help="New immutable plan file")
    args = parser.parse_args()
    allowlist = json.loads(args.allowlist.read_text()) if args.allowlist else None
    plan = freeze_plan(
        json.loads(args.metadata.read_text()),
        json.loads(args.boundary.read_text()),
        args.holdout_family,
        allowlist=allowlist,
        recombination_uids=args.recombination_uid,
    )
    write_plan(args.output, plan)
    print(json.dumps({"plan_sha256": plan["plan_sha256"], "counts": plan["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
