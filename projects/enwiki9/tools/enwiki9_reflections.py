#!/usr/bin/env python3
"""Create validated terminal reflections and rank successor proposals."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
from typing import Any

try:
    from projects.enwiki9.tools import enwiki9_candidate_revisions
    from projects.enwiki9.tools import enwiki9_omega
    from projects.enwiki9.tools import research_contracts
except ModuleNotFoundError:
    import enwiki9_candidate_revisions
    import enwiki9_omega
    import research_contracts


ROOT = pathlib.Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "operations" / "adaptive"
REFLECTIONS = ADAPTIVE / "reflections"
TERMINAL_STATES = ("completed", "failed", "cancelled")
MEASUREMENT_FIELDS = {
    "idealBitsSaved",
    "minimumPartitionIdealBitsSaved",
    "positiveSegmentFraction",
    "scopeBytes",
    "scopeSymbols",
    "netBytesSaved",
    "sourceBytesDelta",
    "runtimeRatio",
    "memoryRatio",
    "transferRetention",
}
STATUS_BY_DECISION = {
    "promote": "active",
    "next-gate": "active",
    "retire": "retired",
    "retry": "candidate",
    "mutate": "measured_negative",
    "hold": "blocked_dependency",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def reference(path: pathlib.Path) -> dict[str, str]:
    resolved = path.resolve()
    project_root = ROOT.resolve()
    if project_root not in resolved.parents:
        raise ValueError(f"reflection reference escapes project: {path}")
    if not resolved.is_file():
        raise FileNotFoundError(f"reflection evidence not found: {path}")
    return {
        "path": resolved.relative_to(project_root).as_posix(),
        "sha256": f"sha256:{research_contracts.file_digest(resolved, 'sha256')}",
    }


def terminal_job(job_id: str) -> tuple[pathlib.Path, dict[str, Any]]:
    matches: list[pathlib.Path] = []
    for state in TERMINAL_STATES:
        for path in (ADAPTIVE / state).glob("*.json"):
            try:
                if _load_json(path).get("job_id") == job_id:
                    matches.append(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    if not matches:
        raise FileNotFoundError(f"terminal job not found: {job_id}")
    if len(matches) != 1:
        raise ValueError(f"job identity is duplicated across terminal states: {job_id}")
    return matches[0], _load_json(matches[0])


def _parse_measurement_assertions(
    specifications: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[pathlib.Path]]:
    measurements = {field: None for field in sorted(MEASUREMENT_FIELDS)}
    assertions: list[dict[str, Any]] = []
    sources: list[pathlib.Path] = []
    for specification in specifications:
        if "=" not in specification or "#" not in specification:
            raise ValueError(
                "--measurement must use FIELD=project/path.json#/json/pointer"
            )
        field, source_pointer = specification.split("=", 1)
        source_text, pointer = source_pointer.rsplit("#", 1)
        if field not in MEASUREMENT_FIELDS or not pointer.startswith("/"):
            raise ValueError(f"invalid measurement assertion: {specification}")
        if measurements[field] is not None:
            raise ValueError(f"duplicate measurement field: {field}")
        source = (ROOT / source_text).resolve()
        source_value = _load_json(source)
        measured_value = research_contracts.json_pointer(
            source_value,
            pointer,
            specification,
        )
        if isinstance(measured_value, bool) or not isinstance(
            measured_value, (int, float)
        ):
            raise ValueError(f"measurement pointer is not numeric: {specification}")
        measurements[field] = measured_value
        assertions.append(
            {
                "field": field,
                "source": reference(source),
                "pointer": pointer,
            }
        )
        sources.append(source)
    return measurements, assertions, sources


def _tri_state(value: str) -> bool | None:
    return {"true": True, "false": False, "unknown": None}[value]


def create_reflection(
    *,
    job_id: str,
    valid: bool,
    validity_classification: str,
    validity_reasons: list[str],
    hypothesis_verdict: str,
    hypothesis_rationale: str,
    failure_class: str,
    localized_cause: str,
    causal_confidence: str,
    controls_equivalent: str,
    measurements: list[str],
    lessons: list[str],
    retired_dimensions: list[str],
    uncertainties: list[str],
    decision: str,
    promotion_pass: str,
    kill_pass: str,
    next_gate_bytes: int | None,
    decision_rationale: str,
    evidence: list[pathlib.Path],
    experiment: pathlib.Path | None,
) -> tuple[pathlib.Path, dict[str, Any]]:
    REFLECTIONS.mkdir(parents=True, exist_ok=True)
    reflection_path = REFLECTIONS / f"{job_id}.json"
    if reflection_path.exists():
        raise FileExistsError(f"job already has a reflection: {job_id}")
    job_path, job = terminal_job(job_id)
    if job.get("schema") not in {
        "enwiki9_adaptive_job_v2",
        "gamma.enwiki9.adaptive-job.v3",
    }:
        raise ValueError("legacy unbound jobs cannot receive scientific reflection")
    candidate_id = job.get("candidate_id")
    if not isinstance(candidate_id, str):
        raise ValueError("job has no candidate identity")
    revision_path, revision = enwiki9_candidate_revisions.verify_job_binding(job)
    if job.get("schema") == "gamma.enwiki9.adaptive-job.v3":
        job_experiment = job.get("experiment")
        if not isinstance(job_experiment, dict):
            raise ValueError("v3 job has no experiment binding")
        if experiment is not None and reference(experiment) != job_experiment:
            raise ValueError("reflection experiment differs from the job binding")
        experiment_reference = job_experiment
    else:
        if experiment is None:
            raise ValueError("v2 job reflection requires an explicit experiment")
        experiment_reference = reference(experiment)
    measurement_values, assertions, assertion_sources = (
        _parse_measurement_assertions(measurements)
    )
    evidence_paths = sorted(
        {path.resolve() for path in [*evidence, *assertion_sources]},
        key=str,
    )
    receipt = {
        "schema": "gamma.enwiki9.reflection-receipt.v1",
        "objective": research_contracts.objective_binding(),
        "reflectionId": f"r-{job_id.lower()}",
        "candidateId": candidate_id,
        "candidateRevision": {
            "candidateId": candidate_id,
            "candidateTreeSha256": revision["candidateTreeSha256"],
            "receipt": reference(revision_path),
        },
        "job": reference(job_path),
        "experiment": experiment_reference,
        "evidence": [reference(path) for path in evidence_paths],
        "validity": {
            "valid": valid,
            "classification": validity_classification,
            "reasons": sorted(set(validity_reasons)),
        },
        "hypothesis": {
            "verdict": hypothesis_verdict,
            "rationale": hypothesis_rationale,
        },
        "attribution": {
            "failureClass": failure_class,
            "localizedCause": localized_cause,
            "causalConfidence": causal_confidence,
            "controlsEquivalent": _tri_state(controls_equivalent),
        },
        "measurements": measurement_values,
        "measurementAssertions": assertions,
        "knowledge": {
            "transferableLessons": sorted(set(lessons)),
            "retiredDimensions": sorted(set(retired_dimensions)),
            "uncertainties": sorted(set(uncertainties)),
        },
        "decision": {
            "verdict": decision,
            "promotionPredicatesPass": _tri_state(promotion_pass),
            "killPredicatesPass": _tri_state(kill_pass),
            "nextGateBytes": next_gate_bytes,
            "rationale": decision_rationale,
        },
        "generatedUtc": utc_now(),
    }
    _atomic_json(reflection_path, receipt)
    try:
        research_contracts.validate_artifact(reflection_path)
    except Exception:
        reflection_path.unlink(missing_ok=True)
        raise
    exclusion_path = (
        enwiki9_omega.EXCLUSIONS / f"reflection-{receipt['reflectionId']}.json"
        if receipt["knowledge"]["retiredDimensions"]
        else None
    )
    exclusion_existed = exclusion_path.is_file() if exclusion_path else False
    try:
        sync_reflection_exclusion(reflection_path, receipt)
        _apply_reflection(candidate_id, job_id, reflection_path, receipt)
    except Exception:
        if exclusion_path is not None and not exclusion_existed:
            exclusion_path.unlink(missing_ok=True)
        reflection_path.unlink(missing_ok=True)
        raise
    return reflection_path, receipt


def _apply_reflection(
    candidate_id: str,
    job_id: str,
    reflection_path: pathlib.Path,
    receipt: dict[str, Any],
) -> None:
    meta_path = ROOT / "programs" / candidate_id / "meta.json"
    metadata = _load_json(meta_path)
    measured = metadata.setdefault("measured", {})
    if not isinstance(measured, dict):
        measured = {}
        metadata["measured"] = measured
    reflections = measured.setdefault("reflections", {})
    if not isinstance(reflections, dict):
        reflections = {}
        measured["reflections"] = reflections
    reflections[job_id] = {
        **reference(reflection_path),
        "decision": receipt["decision"]["verdict"],
        "valid": receipt["validity"]["valid"],
    }
    metadata["status"] = STATUS_BY_DECISION[receipt["decision"]["verdict"]]
    metadata["verdict"] = receipt["decision"]["rationale"]
    _atomic_json(meta_path, metadata)


def iter_reflections() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(REFLECTIONS.glob("*.json")):
        value = _load_json(path)
        research_contracts.validate_artifact(path, verify_files=False)
        rows.append({"_path": path.relative_to(ROOT).as_posix(), **value})
    return rows


def sync_reflection_exclusion(
    reflection_path: pathlib.Path,
    reflection: dict[str, Any],
) -> dict[str, Any] | None:
    retired = reflection["knowledge"]["retiredDimensions"]
    if not retired:
        return None
    experiment_reference = reflection["experiment"]
    experiment_path = ROOT / experiment_reference["path"]
    if reference(experiment_path) != experiment_reference:
        raise ValueError("reflection experiment binding has drifted")
    experiment = _load_json(experiment_path)
    population = experiment["population"]
    if experiment["schema"] == "gamma.enwiki9.adaptive-experiment-contract.v1":
        mechanism = experiment["changedMechanism"]
        scope_bytes = population["scopeBytes"]
        scope_symbols = population["scopeSymbols"]
    else:
        mechanism = "; ".join(experiment["changedVariables"])
        scope_bytes = None
        scope_symbols = population["rowCount"]
    exclusion_id = f"reflection-{reflection['reflectionId']}"
    expected = {
        "schema": "enwiki9_omega_exclusion_v1",
        "exclusion_id": exclusion_id,
        "mechanism": mechanism,
        "population": (
            f"{population['unit']}; {population['selection']}; "
            f"scopeBytes={scope_bytes}; scopeSymbols={scope_symbols}"
        ),
        "failure": reflection["attribution"]["localizedCause"],
        "retired_dimensions": retired,
        "unsettled_successors": [],
        "evidence": [reflection_path.relative_to(ROOT).as_posix()],
    }
    destination = enwiki9_omega.EXCLUSIONS / f"{exclusion_id}.json"
    if destination.is_file():
        existing = _load_json(destination)
        observed = {key: existing.get(key) for key in expected}
        if observed != expected:
            raise ValueError(
                f"reflection-derived exclusion differs from authority: {destination}"
            )
        return existing
    return enwiki9_omega.record_exclusion(
        exclusion_id=exclusion_id,
        mechanism=expected["mechanism"],
        population=expected["population"],
        failure=expected["failure"],
        retired_dimensions=expected["retired_dimensions"],
        unsettled_successors=expected["unsettled_successors"],
        evidence=expected["evidence"],
    )


def sync_reflection_exclusions() -> dict[str, int]:
    reflected = 0
    projected = 0
    for reflection in iter_reflections():
        reflected += 1
        reflection_path = ROOT / reflection.pop("_path")
        if sync_reflection_exclusion(reflection_path, reflection) is not None:
            projected += 1
    return {"reflections": reflected, "projectedExclusions": projected}


def rank_proposals(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy = research_contracts.validate_search_policy()
    latest: dict[str, dict[str, Any]] = {}
    for reflection in iter_reflections():
        latest[reflection["candidateId"]] = reflection
    rows: list[dict[str, Any]] = []
    for proposal in proposals:
        experiment: dict[str, Any] | None = None
        experiment_error: str | None = None
        experiment_reference = proposal.get("experiment")
        try:
            if proposal.get("schema") != "gamma.enwiki9.algorithm-proposal.v2":
                raise ValueError("proposal has no structured v2 experiment")
            if not isinstance(experiment_reference, dict):
                raise ValueError("proposal has no experiment reference")
            _experiment_path, experiment = research_contracts.validate_project_reference(
                experiment_reference,
                {"gamma.enwiki9.adaptive-experiment-contract.v1"},
                f"proposal {proposal.get('proposal_id')}",
            )
            if experiment["proposalId"] != proposal.get("proposal_id"):
                raise ValueError("proposal and experiment identities differ")
        except Exception as exc:
            experiment = None
            experiment_error = str(exc)
        parent = proposal.get("parent")
        reflection = latest.get(parent) if isinstance(parent, str) else None
        decision = (
            reflection["decision"]["verdict"] if reflection is not None else "missing"
        )
        net_saved = (
            reflection["measurements"]["netBytesSaved"]
            if reflection is not None
            else None
        )
        transfer_retention = (
            reflection["measurements"]["transferRetention"]
            if reflection is not None
            else None
        )
        runtime_ratio = (
            reflection["measurements"]["runtimeRatio"]
            if reflection is not None
            else None
        )
        memory_ratio = (
            reflection["measurements"]["memoryRatio"]
            if reflection is not None
            else None
        )
        budget = experiment["budget"] if experiment is not None else {}
        search = experiment["search"] if experiment is not None else {}
        expected_net = int(
            budget.get(
                "expectedNetSavingsBytes",
                int(proposal.get("expected_savings_bytes", 0))
                - int(proposal.get("max_program_bytes", 0)),
            )
        )
        maximum_package = int(
            budget.get("maximumAddedPackageBytes", proposal.get("max_program_bytes", 0))
        )
        uncertainty_risk = float(search.get("uncertaintyRisk", 1.0))
        interaction_risk = float(search.get("interactionRisk", 1.0))
        operational = proposal.get("operational_status", "actionable") == "actionable"
        parent_evidence_valid = (
            parent is None
            or (reflection is not None and reflection["validity"]["valid"])
        )
        experiment_valid = experiment is not None
        eligible = operational and experiment_valid and parent_evidence_valid
        rank_key = (
            int(eligible),
            int(experiment_valid),
            int(reflection is not None and reflection["validity"]["valid"]),
            policy["decisionRank"][decision],
            int(net_saved is not None),
            float(net_saved or 0),
            int(transfer_retention is not None),
            float(transfer_retention or 0),
            int(runtime_ratio is not None),
            -float(runtime_ratio or search.get("expectedRuntimeRatio", 1.0)),
            int(memory_ratio is not None),
            -float(memory_ratio or search.get("expectedMemoryRatio", 1.0)),
            expected_net,
            -maximum_package,
            -uncertainty_risk,
            -interaction_risk,
            int(proposal.get("search_priority", proposal.get("priority", 0))),
            str(proposal.get("proposal_id", "")),
        )
        rows.append(
            {
                "proposalId": proposal.get("proposal_id"),
                "parentCandidateId": parent,
                "parentReflection": reflection.get("_path") if reflection else None,
                "parentDecision": decision,
                "assertedNetBytesSaved": net_saved,
                "assertedTransferRetention": transfer_retention,
                "assertedRuntimeRatio": runtime_ratio,
                "assertedMemoryRatio": memory_ratio,
                "expectedNetBytes": expected_net,
                "maximumAddedPackageBytes": maximum_package,
                "uncertaintyRisk": uncertainty_risk,
                "interactionRisk": interaction_risk,
                "experimentValid": experiment_valid,
                "experimentError": experiment_error,
                "eligible": eligible,
                "operationalStatus": proposal.get(
                    "operational_status", "actionable"
                ),
                "rankKey": list(rank_key[:-1]),
                "searchPriority": proposal.get(
                    "search_priority", proposal.get("priority", 0)
                ),
            }
        )
        rows[-1]["_sort"] = (
            *(-value for value in rank_key[:-1]),
            rank_key[-1],
        )
    rows.sort(key=lambda row: row["_sort"])
    for index, row in enumerate(rows, start=1):
        row.pop("_sort")
        row["rank"] = index
    return rows


def select_next_experiment(proposals: list[dict[str, Any]]) -> dict[str, Any]:
    policy_path = research_contracts.CONTRACT_ROOT / "search-policy.json"
    ranked = rank_proposals(proposals)
    selected = next((row for row in ranked if row["eligible"]), None)
    return {
        "policy": reference(policy_path),
        "selected": selected,
        "ranked": ranked,
    }
