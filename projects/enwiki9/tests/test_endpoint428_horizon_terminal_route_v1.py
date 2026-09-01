from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

import jsonschema
import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOL = PROJECT / "tools/endpoint428_horizon_terminal_route_v1.py"
RESEARCH_CONTRACTS_TOOL = PROJECT / "tools/research_contracts.py"
RECEIPT_SCHEMA_PATH = (
    PROJECT / "contracts/research/v1/endpoint428-horizon-terminal-route.schema.json"
)

spec = importlib.util.spec_from_file_location("horizon_terminal_route_v1", TOOL)
assert spec is not None and spec.loader is not None
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)

contracts_spec = importlib.util.spec_from_file_location(
    "horizon_terminal_route_research_contracts", RESEARCH_CONTRACTS_TOOL
)
assert contracts_spec is not None and contracts_spec.loader is not None
research_contracts = importlib.util.module_from_spec(contracts_spec)
sys.path.insert(0, str(PROJECT / "tools"))
contracts_spec.loader.exec_module(research_contracts)


def write_json(path: Path, value: dict[str, Any], *, allow_nan: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=allow_nan) + "\n"
    )


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    assert isinstance(value, dict)
    return value


def reference(root: Path, path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }


def validate_receipt(value: dict[str, Any]) -> None:
    schema = load_json(RECEIPT_SCHEMA_PATH)
    jsonschema.Draft202012Validator(schema).validate(value)


def frozen_source(relative: str) -> Path:
    return PROJECT / relative


def copy_frozen(root: Path, relative: str) -> Path:
    source = frozen_source(relative)
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    return target


def adaptive_namespaces(root: Path) -> None:
    for state in ("pending", "running", "completed", "failed", "cancelled"):
        (root / "operations/adaptive" / state).mkdir(parents=True, exist_ok=True)


def exact_job(root: Path, state: str, job_id: str) -> dict[str, Any]:
    return {
        "schema": "gamma.enwiki9.adaptive-job.v3",
        "job_id": job_id,
        "candidate_id": router.CANDIDATE_ID,
        "candidate_tree_sha256": router.CANDIDATE_TREE_SHA256,
        "candidate_revision": {
            "path": router.REVISION_PATH,
            "sha256": router.REVISION_SHA256,
        },
        "experiment": {
            "path": router.EXPERIMENT_PATH,
            "sha256": router.EXPERIMENT_SHA256,
        },
        "proposal": {
            "path": router.PROPOSAL_PATH,
            "sha256": router.PROPOSAL_SHA256,
        },
        "proposal_id": router.PROPOSAL_ID,
        "runner": {"path": router.RUNNER_PATH, "sha256": router.RUNNER_SHA256},
        "scratch_directories": router.JOB_SCRATCH_DIRECTORIES,
        "gate_size": router.JOB_GATE_SIZE,
        "priority": router.JOB_PRIORITY,
        "purpose": router.JOB_PURPOSE,
        "state": state,
        "tags": router.JOB_TAGS,
        "submitted_at": router.JOB_SUBMITTED_AT,
        "started_at": router.JOB_STARTED_AT,
        "tool": router.RUNNER_PATH,
        "tool_args": router.JOB_TOOL_ARGS,
    }


def positive_decision() -> dict[str, Any]:
    return {
        "schema": "gamma.enwiki9.endpoint428-horizon-retained-parent-trace-decision.v1",
        "candidate_id": router.CANDIDATE_ID,
        "evidence_class": "causal-shadow",
        "measurements": {
            "activeBytes": 2_331_505,
            "parentTraceRows": 5_182_388_736,
            "treatmentMixtureGainBits": 40_163_160,
            "minimumThirdMixtureGainBits": 1,
            "minimumControlMarginBits": 1,
            "manifestRepeatIdentityPass": True,
            "analysisRepeatIdentityPass": True,
            "parentReadOnlyPass": True,
        },
        "gates": {
            "targetBearingMixturePass": True,
            "everyThirdPositivePass": True,
            "controlsSeparatedPass": True,
            "manifestRepeatPass": True,
            "analysisRepeatPass": True,
            "parentReadOnlyPass": True,
        },
        "verdict": "authorize_one_native_horizon_pkd_finite_coder",
        "promotion_authorized": True,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "verified_full_1g_score_bytes": None,
    }


def negative_decision() -> dict[str, Any]:
    value = positive_decision()
    value["measurements"]["treatmentMixtureGainBits"] = 40_163_159
    value["gates"]["targetBearingMixturePass"] = False
    value["verdict"] = "retire_endpoint428_physical_horizon_a"
    value["promotion_authorized"] = False
    return value


def reflection_fields(branch: str) -> tuple[dict[str, Any], ...]:
    if branch == router.BRANCH_REPRICE:
        return (
            {"valid": True, "classification": "valid", "reasons": ["all frozen predicates evaluated"]},
            {"verdict": "supported", "rationale": "all exact treatment predicates passed"},
            {
                "failureClass": "algorithmic-gain",
                "localizedCause": "the frozen treatment",
                "causalConfidence": "high",
                "controlsEquivalent": True,
            },
            {
                "verdict": "next-gate",
                "promotionPredicatesPass": True,
                "killPredicatesPass": False,
                "nextGateBytes": 1_000_000_000,
                "rationale": "reprice the exact frozen q0 successor",
            },
        )
    if branch == router.BRANCH_RETIRE:
        return (
            {"valid": True, "classification": "valid", "reasons": ["all frozen predicates evaluated"]},
            {"verdict": "refuted", "rationale": "the treatment missed its frozen scale"},
            {
                "failureClass": "algorithmic-loss",
                "localizedCause": "the frozen treatment",
                "causalConfidence": "high",
                "controlsEquivalent": True,
            },
            {
                "verdict": "retire",
                "promotionPredicatesPass": False,
                "killPredicatesPass": True,
                "nextGateBytes": None,
                "rationale": "retire the physical HORIZON mechanism",
            },
        )
    if branch == router.BRANCH_CORRECTION:
        return (
            {"valid": False, "classification": "infrastructure-failure", "reasons": ["runner exited before decision"]},
            {"verdict": "not-tested", "rationale": "no scientific decision was produced"},
            {
                "failureClass": "infrastructure-failure",
                "localizedCause": "terminal runner failure",
                "causalConfidence": "none",
                "controlsEquivalent": None,
            },
            {
                "verdict": "retry",
                "promotionPredicatesPass": None,
                "killPredicatesPass": None,
                "nextGateBytes": None,
                "rationale": "correct the runner without interpreting science",
            },
        )
    if branch == router.BRANCH_QUARANTINE:
        return (
            {"valid": False, "classification": "invalid-experiment", "reasons": ["control identity was not equivalent"]},
            {"verdict": "not-tested", "rationale": "causal validity was not established"},
            {
                "failureClass": "causal-failure",
                "localizedCause": "non-equivalent control",
                "causalConfidence": "none",
                "controlsEquivalent": False,
            },
            {
                "verdict": "retry",
                "promotionPredicatesPass": None,
                "killPredicatesPass": None,
                "nextGateBytes": None,
                "rationale": "quarantine and correct causal identity",
            },
        )
    raise AssertionError(branch)


def build_terminal_fixture(
    root: Path,
    *,
    branch: str,
    state: str | None = None,
    extra_output: bool = False,
    missing_output: str | None = None,
    mutate_decision: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Path]:
    adaptive_namespaces(root)
    experiment = copy_frozen(root, router.EXPERIMENT_PATH)
    proposal = copy_frozen(root, router.PROPOSAL_PATH)
    revision = copy_frozen(root, router.REVISION_PATH)
    runner = copy_frozen(root, router.RUNNER_PATH)
    assert reference(root, experiment)["sha256"] == router.EXPERIMENT_SHA256
    assert reference(root, proposal)["sha256"] == router.PROPOSAL_SHA256
    assert reference(root, revision)["sha256"] == router.REVISION_SHA256
    assert reference(root, runner)["sha256"] == router.RUNNER_SHA256

    if state is None:
        state = "completed" if branch in {router.BRANCH_REPRICE, router.BRANCH_RETIRE} else (
            "failed" if branch == router.BRANCH_CORRECTION else "cancelled"
        )
    job_id = router.JOB_ID
    job = exact_job(root, state, job_id)
    job["cancelled_at" if state == "cancelled" else "finished_at"] = (
        "2026-08-31T01:00:00+00:00"
    )
    job["returncode"] = 0 if state == "completed" else (2 if state == "failed" else None)
    job_path = root / f"operations/adaptive/{state}/{router.JOB_FILE}"
    write_json(job_path, job)

    evidence: list[dict[str, str]] = []
    result = root / router.RESULT_ROOT
    decision_path = result / "decision.json"
    if state == "completed":
        result.mkdir(parents=True)
        decision_value = negative_decision() if branch == router.BRANCH_RETIRE else positive_decision()
        if mutate_decision is not None:
            mutate_decision(decision_value)
        write_json(decision_path, decision_value, allow_nan=True)
        for output in router.EXPECTED_OUTPUTS:
            name = Path(output).name
            if name == "decision.json" or name == missing_output:
                continue
            (result / name).write_bytes(f"opaque-{name}".encode())
        if extra_output:
            (result / "undeclared.log").write_bytes(b"extra")
        evidence.append(reference(root, decision_path))

    validity, hypothesis, attribution, reflected_decision = reflection_fields(branch)
    objective = load_json(frozen_source(router.EXPERIMENT_PATH))["objective"]
    reflection = {
        "schema": "gamma.enwiki9.reflection-receipt.v1",
        "objective": objective,
        "reflectionId": f"r-{router.JOB_ID.lower()}",
        "candidateId": router.CANDIDATE_ID,
        "candidateRevision": {
            "candidateId": router.CANDIDATE_ID,
            "candidateTreeSha256": router.CANDIDATE_TREE_SHA256,
            "receipt": reference(root, revision),
        },
        "job": reference(root, job_path),
        "experiment": reference(root, experiment),
        "evidence": evidence,
        "validity": validity,
        "hypothesis": hypothesis,
        "attribution": attribution,
        "measurements": {
            "scopeBytes": None,
            "scopeSymbols": None,
            "netBytesSaved": None,
            "idealBitsSaved": None,
            "sourceBytesDelta": None,
            "runtimeRatio": None,
            "memoryRatio": None,
            "transferRetention": None,
            "positiveSegmentFraction": None,
            "minimumPartitionIdealBitsSaved": None,
        },
        "measurementAssertions": [],
        "knowledge": {
            "transferableLessons": ["route only reflected terminal evidence"],
            "retiredDimensions": [],
            "uncertainties": ["no archive claim is made"],
        },
        "decision": reflected_decision,
        "generatedUtc": "2026-08-31T01:01:00+00:00",
    }
    reflection_path = root / f"operations/adaptive/reflections/{job_id}.json"
    write_json(reflection_path, reflection)
    return {
        "decision": decision_path,
        "reflection": reflection_path,
        "job": job_path,
        "result": result,
    }


def rewrite_reflection_job_binding(root: Path, paths: dict[str, Path]) -> None:
    reflection = load_json(paths["reflection"])
    reflection["job"] = reference(root, paths["job"])
    write_json(paths["reflection"], reflection)


def rewrite_reflection_decision_binding(root: Path, paths: dict[str, Path]) -> None:
    reflection = load_json(paths["reflection"])
    reflection["evidence"] = [reference(root, paths["decision"])]
    write_json(paths["reflection"], reflection)


def test_nonterminal_blocks_before_decision_or_result_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adaptive_namespaces(tmp_path)
    active = exact_job(tmp_path, "running", router.JOB_ID)
    write_json(tmp_path / f"operations/adaptive/running/{router.JOB_FILE}", active)
    original = router.ProjectReader.read_file
    accessed: list[str] = []

    def observe(reader: Any, relative: str) -> bytes:
        if relative.startswith(router.RESULT_ROOT):
            accessed.append(relative)
            raise AssertionError("result artifact accessed before terminality")
        return original(reader, relative)

    monkeypatch.setattr(router.ProjectReader, "read_file", observe)
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["status"] == "BLOCKED_NONTERMINAL"
    assert receipt["active_jobs"][0]["job_id"] == router.JOB_ID
    assert receipt["decision_accessed"] is False
    assert receipt["result_root_accessed"] is False
    assert "host_lane_release" not in receipt
    assert not accessed


@pytest.mark.parametrize("namespace", ["pending", "running"])
def test_symlink_active_namespace_returns_schema_valid_blocked(
    tmp_path: Path, namespace: str
) -> None:
    adaptive = tmp_path / "operations/adaptive"
    adaptive.mkdir(parents=True)
    other = tmp_path / "other"
    other.mkdir()
    (adaptive / namespace).symlink_to(other, target_is_directory=True)
    (adaptive / ("running" if namespace == "pending" else "pending")).mkdir()
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    row = next(row for row in receipt["active_jobs"] if row["state"] == namespace)
    assert row["reason"] == "unsafe-active-namespace"
    assert row["job_id"] is None


def test_nonregular_active_namespace_returns_schema_valid_blocked(
    tmp_path: Path,
) -> None:
    adaptive = tmp_path / "operations/adaptive"
    adaptive.mkdir(parents=True)
    (adaptive / "pending").write_bytes(b"not a directory")
    (adaptive / "running").mkdir()
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["active_jobs"] == [
        {
            "path": "operations/adaptive/pending",
            "state": "pending",
            "job_id": None,
            "reason": "unsafe-active-namespace",
        }
    ]


def test_symlink_active_record_returns_schema_valid_blocked(tmp_path: Path) -> None:
    adaptive_namespaces(tmp_path)
    target = tmp_path / "outside.json"
    write_json(target, exact_job(tmp_path, "running", router.JOB_ID))
    (tmp_path / f"operations/adaptive/running/{router.JOB_FILE}").symlink_to(target)
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["active_jobs"] == [
        {
            "path": f"operations/adaptive/running/{router.JOB_FILE}",
            "state": "running",
            "job_id": None,
            "reason": "unreadable-active-record",
        }
    ]


def test_unrelated_legacy_active_records_do_not_block_frozen_job_route(
    tmp_path: Path,
) -> None:
    build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    (tmp_path / "operations/adaptive/pending/legacy.json").write_bytes(b"{}")
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["status"] == "TERMINAL_ROUTED"


def test_exact_active_filename_with_drifted_identity_blocks(tmp_path: Path) -> None:
    adaptive_namespaces(tmp_path)
    active = exact_job(tmp_path, "running", "different-job-id")
    write_json(tmp_path / f"operations/adaptive/running/{router.JOB_FILE}", active)
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["active_jobs"][0]["reason"] == "frozen-job-identity-drift"


def test_unrelated_malformed_terminal_records_do_not_block_frozen_job_route(
    tmp_path: Path,
) -> None:
    build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    (tmp_path / "operations/adaptive/failed/unrelated.json").write_bytes(b"not json")
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["branch"] == router.BRANCH_REPRICE


def test_exact_terminal_record_symlink_is_rejected(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    outside = tmp_path / "outside-terminal.json"
    paths["job"].replace(outside)
    paths["job"].symlink_to(outside)
    with pytest.raises(router.RouteError, match="terminal job record"):
        router.route(tmp_path)


@pytest.mark.parametrize(
    ("branch", "state"),
    [
        (router.BRANCH_CORRECTION, "failed"),
        (router.BRANCH_QUARANTINE, "cancelled"),
        (router.BRANCH_RETIRE, "completed"),
        (router.BRANCH_REPRICE, "completed"),
    ],
)
def test_exact_four_terminal_branches_are_schema_valid(
    tmp_path: Path, branch: str, state: str
) -> None:
    build_terminal_fixture(tmp_path, branch=branch, state=state)
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["status"] == "TERMINAL_ROUTED"
    assert receipt["branch"] == branch
    assert receipt["terminal_state"] == state
    assert receipt["host_lane_release"] is True
    if state == "completed":
        assert receipt["decision_accessed"] is True
        assert receipt["output_closure"]["complete"] is True
        assert receipt["output_closure"]["bound_output_count"] == 7
    else:
        assert receipt["decision_accessed"] is False
        assert receipt["result_root_accessed"] is False
        assert "decision" not in receipt["bindings"]


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("runner", {"path": "tools/other.py", "sha256": router.RUNNER_SHA256}),
        ("candidate_revision", {"path": router.REVISION_PATH, "sha256": "sha256:" + "0" * 64}),
        ("proposal", {"path": router.PROPOSAL_PATH, "sha256": "sha256:" + "0" * 64}),
        ("candidate_tree_sha256", "sha256:" + "0" * 64),
    ],
)
def test_frozen_job_identity_drift_is_rejected(
    tmp_path: Path, field: str, bad_value: Any
) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    job = load_json(paths["job"])
    job[field] = bad_value
    write_json(paths["job"], job)
    rewrite_reflection_job_binding(tmp_path, paths)
    with pytest.raises(router.RouteError, match="mismatch"):
        router.route(tmp_path)


def test_terminal_job_is_validated_against_canonical_schema(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    job = load_json(paths["job"])
    del job["purpose"]
    write_json(paths["job"], job)
    rewrite_reflection_job_binding(tmp_path, paths)
    with pytest.raises(router.RouteError, match="canonical job schema"):
        router.route(tmp_path)


def test_reflection_is_validated_against_canonical_schema(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    reflection = load_json(paths["reflection"])
    del reflection["hypothesis"]["rationale"]
    write_json(paths["reflection"], reflection)
    with pytest.raises(router.RouteError, match="canonical reflection schema"):
        router.route(tmp_path)


def test_valid_scientific_branch_requires_equivalent_controls(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    reflection = load_json(paths["reflection"])
    reflection["attribution"]["controlsEquivalent"] = False
    write_json(paths["reflection"], reflection)
    with pytest.raises(router.RouteError, match="equivalent controls"):
        router.route(tmp_path)


def test_conflicting_failure_classifiers_are_rejected(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_CORRECTION)
    reflection = load_json(paths["reflection"])
    reflection["attribution"]["failureClass"] = "causal-failure"
    write_json(paths["reflection"], reflection)
    with pytest.raises(router.RouteError, match="conflicting correction"):
        router.route(tmp_path)


def test_nonfinite_predicate_number_is_rejected(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    decision = load_json(paths["decision"])
    decision["measurements"]["treatmentMixtureGainBits"] = float("nan")
    write_json(paths["decision"], decision, allow_nan=True)
    rewrite_reflection_decision_binding(tmp_path, paths)
    with pytest.raises(router.RouteError, match="nonfinite JSON number"):
        router.route(tmp_path)


@pytest.mark.parametrize(
    ("state", "returncode", "message"),
    [
        ("completed", 2, "completed terminal job"),
        ("failed", 0, "failed terminal job"),
        ("cancelled", 143, "cancelled terminal job"),
    ],
)
def test_terminal_state_and_returncode_are_cross_checked(
    tmp_path: Path, state: str, returncode: int, message: str
) -> None:
    branch = router.BRANCH_REPRICE if state == "completed" else (
        router.BRANCH_CORRECTION if state == "failed" else router.BRANCH_QUARANTINE
    )
    paths = build_terminal_fixture(tmp_path, branch=branch, state=state)
    job = load_json(paths["job"])
    job["returncode"] = returncode
    write_json(paths["job"], job)
    rewrite_reflection_job_binding(tmp_path, paths)
    with pytest.raises(router.RouteError, match=message):
        router.route(tmp_path)


def test_failed_reflection_cannot_claim_scientific_decision(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_CORRECTION)
    fake = tmp_path / router.DECISION_PATH
    fake.parent.mkdir(parents=True)
    write_json(fake, positive_decision())
    reflection = load_json(paths["reflection"])
    reflection["evidence"] = [reference(tmp_path, fake)]
    write_json(paths["reflection"], reflection)
    with pytest.raises(router.RouteError, match="must not claim"):
        router.route(tmp_path)


def test_undeclared_output_routes_correction(tmp_path: Path) -> None:
    build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE, extra_output=True)
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["branch"] == router.BRANCH_CORRECTION
    assert receipt["output_closure"]["failure_class"] == "undeclared-extras"


def test_opaque_outputs_are_streamed_instead_of_bounded_json_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    original = router.ProjectReader.read_file

    def reject_opaque_read(reader: Any, relative: str, **kwargs: Any) -> bytes:
        if relative == f"{router.RESULT_ROOT}/parent.p1":
            raise AssertionError("opaque parent trace entered the bounded JSON reader")
        return original(reader, relative, **kwargs)

    monkeypatch.setattr(router.ProjectReader, "read_file", reject_opaque_read)
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["branch"] == router.BRANCH_REPRICE
    parent = next(
        row
        for row in receipt["output_closure"]["artifacts"]
        if row["path"].endswith("/parent.p1")
    )
    assert parent["bytes"] == len(b"opaque-parent.p1")


def test_output_path_replacement_after_hash_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    target = tmp_path / router.RESULT_ROOT / "manifest-a.bin"
    original = router.ProjectReader.artifact_snapshot
    replaced = False

    def replace_after_hash(reader: Any, relative: str) -> Any:
        nonlocal replaced
        result = original(reader, relative)
        if relative.endswith("/manifest-b.bin") and not replaced:
            replacement = target.with_name("replacement.bin")
            replacement.write_bytes(b"replacement")
            replacement.replace(target)
            replaced = True
        return result

    monkeypatch.setattr(
        router.ProjectReader, "artifact_snapshot", replace_after_hash
    )
    with pytest.raises(router.RouteError, match="pathname changed after hashing"):
        router.route(tmp_path)


def test_terminal_receipt_write_is_durable_and_no_clobber(tmp_path: Path) -> None:
    adaptive_namespaces(tmp_path)
    (tmp_path / "operations/evidence").mkdir()
    relative = "operations/evidence/terminal.json"
    value = {"status": "TERMINAL_ROUTED"}
    with router.ProjectReader(tmp_path) as reader:
        reader.write_new_json(relative, value)
    assert load_json(tmp_path / relative) == value
    with router.ProjectReader(tmp_path) as reader:
        with pytest.raises(router.RouteError, match="already exists"):
            reader.write_new_json(relative, value)


def test_missing_output_routes_correction(tmp_path: Path) -> None:
    build_terminal_fixture(
        tmp_path, branch=router.BRANCH_REPRICE, missing_output="manifest-b.bin"
    )
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["branch"] == router.BRANCH_CORRECTION
    assert receipt["output_closure"]["failure_class"] == "nonregular-or-missing"


def test_missing_decision_routes_correction_without_scientific_claim(
    tmp_path: Path,
) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    paths["decision"].unlink()
    receipt = router.route(tmp_path)
    validate_receipt(receipt)
    assert receipt["branch"] == router.BRANCH_CORRECTION
    assert receipt["decision_accessed"] is False
    assert "decision" not in receipt["bindings"]
    assert "predicate_evaluations" not in receipt


def test_decision_hash_drift_is_rejected(tmp_path: Path) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    paths["decision"].write_bytes(paths["decision"].read_bytes() + b" ")
    with pytest.raises(router.RouteError, match="terminal decision SHA-256 mismatch"):
        router.route(tmp_path)


def test_recomputed_predicates_reject_claim_mismatch(tmp_path: Path) -> None:
    def contradict(value: dict[str, Any]) -> None:
        value["promotion_authorized"] = False

    build_terminal_fixture(
        tmp_path, branch=router.BRANCH_REPRICE, mutate_decision=contradict
    )
    with pytest.raises(router.RouteError, match="contradicts recomputed frozen predicates"):
        router.route(tmp_path)


def test_parent_identity_failure_cannot_be_reflected_as_algorithmic_loss(
    tmp_path: Path,
) -> None:
    def break_parent_identity(value: dict[str, Any]) -> None:
        value["measurements"]["parentReadOnlyPass"] = False
        value["gates"]["parentReadOnlyPass"] = False
        value["promotion_authorized"] = False
        value["verdict"] = "retire_endpoint428_physical_horizon_a"

    build_terminal_fixture(
        tmp_path, branch=router.BRANCH_RETIRE, mutate_decision=break_parent_identity
    )
    with pytest.raises(router.RouteError, match="integrity failure"):
        router.route(tmp_path)


def test_receipt_schema_rejects_duplicate_or_wrong_predicate_artifacts(
    tmp_path: Path,
) -> None:
    build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    receipt = router.route(tmp_path)
    schema = load_json(RECEIPT_SCHEMA_PATH)
    broken = copy.deepcopy(receipt)
    broken["output_closure"]["artifacts"][1] = copy.deepcopy(
        broken["output_closure"]["artifacts"][0]
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(broken)
    broken = copy.deepcopy(receipt)
    broken["predicate_evaluations"]["promotion"][0]["predicate_id"] = "wrong"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(broken)


def test_research_contracts_registration_verifies_terminal_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = build_terminal_fixture(tmp_path, branch=router.BRANCH_REPRICE)
    receipt = router.route(tmp_path)
    receipt_path = tmp_path / "terminal-route.json"
    write_json(receipt_path, receipt)
    monkeypatch.setattr(research_contracts, "PROJECT_ROOT", tmp_path)
    validation = research_contracts.validate_artifact(receipt_path, verify_files=True)
    assert validation["valid"] is True
    assert validation["filesVerified"] is True

    broken = copy.deepcopy(receipt)
    broken["bindings"]["terminal_job"]["bytes"] += 1
    broken_path = tmp_path / "terminal-route-wrong-bytes.json"
    write_json(broken_path, broken)
    with pytest.raises(ValueError, match="binding byte count differs"):
        research_contracts.validate_artifact(broken_path, verify_files=True)

    paths["decision"].write_bytes(paths["decision"].read_bytes() + b" ")
    with pytest.raises(ValueError, match="digest differs"):
        research_contracts.validate_artifact(receipt_path, verify_files=True)
