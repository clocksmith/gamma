"""
Debate-adjudicated Distillation (DaD) schema and provenance verifier (dadVersion: 0).

Implements the canonical JSON hashing and 5-part DaD validity invariant defined in
Doppler's Mixture-of-MoEs (MoM) specification:
1. Proposals (one per participating substrate, with proposalHash and substrateTranscriptRoot)
2. Critiques (at least one targeting each proposal)
3. Responses / rebuttals (at least one targeting each critique)
4. Adjudication record (with distillationWeights covering every proposal)
5. distillationWeightsHash matching the canonical hash of distillationWeights, bound
   to the same momTranscriptRoot.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

DAD_SUPPORTED_VERSION = 0
MOM_SUPPORTED_VERSION = 0
_SHA256_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class DadValidationError(ValueError):
    """Raised when a DaD record or MoM debate bundle fails schema or hash verification."""


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value into deterministic canonical JSON (sorted keys, no extra whitespace)."""
    if value is None or isinstance(value, (bool, str)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DadValidationError(f"Non-finite float is not allowed in canonical JSON: {value!r}")
        if value.is_integer():
            return json.dumps(int(value), separators=(",", ":"))
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, Mapping):
        parts: List[str] = []
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise DadValidationError(f"Canonical JSON object keys must be strings, got {key!r}")
            parts.append(f"{json.dumps(key, ensure_ascii=False, separators=(',', ':'))}:{canonical_json(value[key])}")
        return "{" + ",".join(parts) + "}"
    raise DadValidationError(f"Unsupported type for canonical JSON serialization: {type(value).__name__}")


def sha256_json(value: Any) -> str:
    """Compute canonical `sha256:<hex>` digest of a JSON-compatible value."""
    encoded = canonical_json(value).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def require_sha256_digest(value: Any, field_name: str) -> str:
    """Validate that `value` is a canonical `sha256:<64 lowercase hex>` string."""
    if not isinstance(value, str) or not _SHA256_DIGEST_RE.match(value):
        raise DadValidationError(f"Invalid or missing SHA-256 digest for '{field_name}': {value!r}")
    return value


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DadValidationError(f"Field '{field_name}' must be a non-empty string")
    return value


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DadValidationError(f"Field '{field_name}' must be a JSON object")
    return value


def _require_list(value: Any, field_name: str, *, allow_empty: bool = False) -> Sequence[Any]:
    if not isinstance(value, list):
        raise DadValidationError(f"Field '{field_name}' must be a list")
    if not allow_empty and len(value) == 0:
        raise DadValidationError(f"Field '{field_name}' must be a non-empty list")
    return value


@dataclass(frozen=True)
class DadProposalRecord:
    """Validated proposal entry in a MoM debate round."""

    substrate_id: str
    proposal_hash: str
    substrate_transcript_root: str
    confidence: Optional[float] = None
    payload_type: Optional[str] = None


@dataclass(frozen=True)
class DadCritiqueRecord:
    """Validated critique entry in a MoM debate round."""

    from_substrate_id: str
    target_proposal_hash: str
    critique_hash: str


@dataclass(frozen=True)
class DadResponseRecord:
    """Validated response/rebuttal entry in a MoM debate round."""

    from_substrate_id: str
    target_critique_hash: str
    response_hash: str


@dataclass(frozen=True)
class DadDebateRoundRecord:
    """Validated MoM debate round containing proposals, critiques, and responses."""

    round_index: int
    participants: Tuple[str, ...]
    proposals: Tuple[DadProposalRecord, ...]
    critiques: Tuple[DadCritiqueRecord, ...]
    responses: Tuple[DadResponseRecord, ...]
    round_hash: str


@dataclass(frozen=True)
class DadDistillationWeight:
    """Validated teacher distillation weight for a single proposal."""

    proposal_hash: str
    substrate_id: str
    weight: float


@dataclass(frozen=True)
class DadRejectRecord:
    """Validated rejected proposal entry in adjudication."""

    proposal_hash: str
    reason_codes: Tuple[str, ...]


@dataclass(frozen=True)
class DadAdjudicationRecord:
    """Validated MoM adjudication record."""

    winner_proposal_hash: str
    winner_substrate_id: str
    adjudicator_substrate_id: str
    policy_hash: str
    score_vector_hash: str
    distillation_weights: Tuple[DadDistillationWeight, ...]
    distillation_weights_hash: str
    rejects: Tuple[DadRejectRecord, ...]
    adjudication_hash: str


@dataclass(frozen=True)
class DadStudentTarget:
    """Student target specification in a DaD export record."""

    family: str
    adapter_id: str


@dataclass(frozen=True)
class DadExportRow:
    """Validated DaD export candidate row (`dadVersion: 0`)."""

    dad_version: int
    mom_transcript_root: str
    winner_proposal_hash: str
    winner_substrate_id: str
    teacher_set_hash: str
    distillation_weights_hash: str
    student_target: DadStudentTarget
    score_vector_hash: str
    accepted: bool


@dataclass(frozen=True)
class VerifiedDadBundle:
    """Complete verified DaD bundle bound to a single momTranscriptRoot."""

    export_row: DadExportRow
    debate_rounds: Tuple[DadDebateRoundRecord, ...]
    adjudication: DadAdjudicationRecord
    mom_transcript_root: str
    proposals_by_hash: Dict[str, DadProposalRecord]
    weights_by_proposal_hash: Dict[str, float]
    rejected_proposal_hashes: Tuple[str, ...]
    resolved_proposals: Dict[str, Any]
    request_payload: Optional[Mapping[str, Any]]


def validate_debate_round(
    raw_round: Mapping[str, Any],
    *,
    proposal_payloads: Optional[Mapping[str, Any]] = None,
    critique_payloads: Optional[Mapping[str, Any]] = None,
    response_payloads: Optional[Mapping[str, Any]] = None,
) -> DadDebateRoundRecord:
    """Validate a single MoM debate round (invariants 1, 2, and 3)."""
    raw_round = _require_mapping(raw_round, "round")
    round_idx = raw_round.get("round")
    if isinstance(round_idx, bool) or not isinstance(round_idx, int) or round_idx < 0:
        raise DadValidationError(f"round.round must be a non-negative integer, got {round_idx!r}")

    raw_participants = _require_list(raw_round.get("participants"), "round.participants")
    participants: List[str] = []
    seen_participants: set[str] = set()
    for idx, p in enumerate(raw_participants):
        sub_id = _require_non_empty_str(p, f"round.participants[{idx}]")
        if sub_id in seen_participants:
            raise DadValidationError(f"Duplicate participant substrateId in round {round_idx}: {sub_id!r}")
        seen_participants.add(sub_id)
        participants.append(sub_id)

    # Invariant 1: proposals (one per participating substrate, with proposalHash and substrateTranscriptRoot)
    raw_proposals = _require_list(raw_round.get("proposals"), "round.proposals")
    proposals: List[DadProposalRecord] = []
    proposals_by_hash: Dict[str, DadProposalRecord] = {}
    proposing_substrates: set[str] = set()

    for idx, item in enumerate(raw_proposals):
        entry = _require_mapping(item, f"round.proposals[{idx}]")
        substrate_id = _require_non_empty_str(entry.get("substrateId"), f"round.proposals[{idx}].substrateId")
        if substrate_id not in seen_participants:
            raise DadValidationError(
                f"Proposal substrateId '{substrate_id}' is not in round.participants {participants}"
            )
        if substrate_id in proposing_substrates:
            raise DadValidationError(
                f"Duplicate proposal from substrateId '{substrate_id}' in round {round_idx}"
            )
        proposing_substrates.add(substrate_id)

        proposal_hash = require_sha256_digest(
            entry.get("proposalHash"), f"round.proposals[{idx}].proposalHash"
        )
        if proposal_hash in proposals_by_hash:
            raise DadValidationError(f"Duplicate proposalHash in round {round_idx}: {proposal_hash}")

        substrate_root = require_sha256_digest(
            entry.get("substrateTranscriptRoot"),
            f"round.proposals[{idx}].substrateTranscriptRoot",
        )

        confidence = entry.get("confidence")
        if confidence is not None:
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence):
                raise DadValidationError(
                    f"round.proposals[{idx}].confidence must be a finite number, got {confidence!r}"
                )
            confidence = float(confidence)
            if not (0.0 <= confidence <= 1.0):
                raise DadValidationError(
                    f"round.proposals[{idx}].confidence must be in [0.0, 1.0], got {confidence}"
                )

        payload_type = entry.get("payloadType")
        if payload_type is not None:
            payload_type = _require_non_empty_str(payload_type, f"round.proposals[{idx}].payloadType")

        if proposal_payloads is not None and proposal_hash in proposal_payloads:
            computed_hash = sha256_json(proposal_payloads[proposal_hash])
            if computed_hash != proposal_hash:
                raise DadValidationError(
                    f"Proposal payload hash mismatch for {proposal_hash}: computed {computed_hash}"
                )

        rec = DadProposalRecord(
            substrate_id=substrate_id,
            proposal_hash=proposal_hash,
            substrate_transcript_root=substrate_root,
            confidence=confidence,
            payload_type=payload_type,
        )
        proposals.append(rec)
        proposals_by_hash[proposal_hash] = rec

    missing_proposers = [p for p in participants if p not in proposing_substrates]
    if missing_proposers:
        raise DadValidationError(
            f"Participating substrates missing proposals in round {round_idx}: {missing_proposers}"
        )

    # Invariant 2: critiques (at least one targeting each proposal)
    raw_critiques = _require_list(raw_round.get("critiques"), "round.critiques")
    critiques: List[DadCritiqueRecord] = []
    critiques_by_hash: Dict[str, DadCritiqueRecord] = {}
    critiqued_proposals: set[str] = set()

    for idx, item in enumerate(raw_critiques):
        entry = _require_mapping(item, f"round.critiques[{idx}]")
        from_sub = _require_non_empty_str(
            entry.get("fromSubstrateId"), f"round.critiques[{idx}].fromSubstrateId"
        )
        if from_sub not in seen_participants:
            raise DadValidationError(
                f"Critique fromSubstrateId '{from_sub}' is not a participant in round {round_idx}"
            )
        target_prop_hash = require_sha256_digest(
            entry.get("targetProposalHash"), f"round.critiques[{idx}].targetProposalHash"
        )
        if target_prop_hash not in proposals_by_hash:
            raise DadValidationError(
                f"Critique targets unknown proposalHash {target_prop_hash} in round {round_idx}"
            )
        critique_hash = require_sha256_digest(
            entry.get("critiqueHash"), f"round.critiques[{idx}].critiqueHash"
        )
        if critique_hash in critiques_by_hash:
            raise DadValidationError(f"Duplicate critiqueHash in round {round_idx}: {critique_hash}")

        if critique_payloads is not None and critique_hash in critique_payloads:
            computed_crit = sha256_json(critique_payloads[critique_hash])
            if computed_crit != critique_hash:
                raise DadValidationError(
                    f"Critique payload hash mismatch for {critique_hash}: computed {computed_crit}"
                )

        crit_rec = DadCritiqueRecord(
            from_substrate_id=from_sub,
            target_proposal_hash=target_prop_hash,
            critique_hash=critique_hash,
        )
        critiques.append(crit_rec)
        critiques_by_hash[critique_hash] = crit_rec
        critiqued_proposals.add(target_prop_hash)

    uncritiqued = [p.proposal_hash for p in proposals if p.proposal_hash not in critiqued_proposals]
    if uncritiqued:
        raise DadValidationError(
            f"MoM debate proposal(s) missing critique in round {round_idx}: {uncritiqued}"
        )

    # Invariant 3: responses / rebuttals (at least one per critique)
    raw_responses = _require_list(raw_round.get("responses"), "round.responses")
    responses: List[DadResponseRecord] = []
    responses_by_hash: Dict[str, DadResponseRecord] = {}
    responded_critiques: set[str] = set()

    for idx, item in enumerate(raw_responses):
        entry = _require_mapping(item, f"round.responses[{idx}]")
        from_sub = _require_non_empty_str(
            entry.get("fromSubstrateId"), f"round.responses[{idx}].fromSubstrateId"
        )
        if from_sub not in seen_participants:
            raise DadValidationError(
                f"Response fromSubstrateId '{from_sub}' is not a participant in round {round_idx}"
            )
        target_crit_hash = require_sha256_digest(
            entry.get("targetCritiqueHash"), f"round.responses[{idx}].targetCritiqueHash"
        )
        if target_crit_hash not in critiques_by_hash:
            raise DadValidationError(
                f"Response targets unknown critiqueHash {target_crit_hash} in round {round_idx}"
            )
        response_hash = require_sha256_digest(
            entry.get("responseHash"), f"round.responses[{idx}].responseHash"
        )
        if response_hash in responses_by_hash:
            raise DadValidationError(f"Duplicate responseHash in round {round_idx}: {response_hash}")

        if response_payloads is not None and response_hash in response_payloads:
            computed_resp = sha256_json(response_payloads[response_hash])
            if computed_resp != response_hash:
                raise DadValidationError(
                    f"Response payload hash mismatch for {response_hash}: computed {computed_resp}"
                )

        resp_rec = DadResponseRecord(
            from_substrate_id=from_sub,
            target_critique_hash=target_crit_hash,
            response_hash=response_hash,
        )
        responses.append(resp_rec)
        responses_by_hash[response_hash] = resp_rec
        responded_critiques.add(target_crit_hash)

    unanswered = [c.critique_hash for c in critiques if c.critique_hash not in responded_critiques]
    if unanswered:
        raise DadValidationError(
            f"MoM debate critique(s) missing response in round {round_idx}: {unanswered}"
        )

    return DadDebateRoundRecord(
        round_index=round_idx,
        participants=tuple(participants),
        proposals=tuple(proposals),
        critiques=tuple(critiques),
        responses=tuple(responses),
        round_hash=sha256_json(raw_round),
    )


def validate_adjudication_record(
    raw_adjudication: Mapping[str, Any],
    proposals_by_hash: Mapping[str, DadProposalRecord],
) -> DadAdjudicationRecord:
    """Validate MoM adjudication record and re-derive distillationWeightsHash (invariants 4 and 5)."""
    raw_adjudication = _require_mapping(raw_adjudication, "adjudication")

    winner_proposal_hash = require_sha256_digest(
        raw_adjudication.get("winnerProposalHash"), "adjudication.winnerProposalHash"
    )
    if winner_proposal_hash not in proposals_by_hash:
        raise DadValidationError(
            f"adjudication.winnerProposalHash {winner_proposal_hash} does not match any debate proposal"
        )
    winner_substrate_id = _require_non_empty_str(
        raw_adjudication.get("winnerSubstrateId"), "adjudication.winnerSubstrateId"
    )
    expected_winner_sub = proposals_by_hash[winner_proposal_hash].substrate_id
    if winner_substrate_id != expected_winner_sub:
        raise DadValidationError(
            f"adjudication.winnerSubstrateId '{winner_substrate_id}' does not match winner proposal "
            f"substrate '{expected_winner_sub}'"
        )

    adjudicator_substrate_id = _require_non_empty_str(
        raw_adjudication.get("adjudicatorSubstrateId"), "adjudication.adjudicatorSubstrateId"
    )
    policy_hash = require_sha256_digest(
        raw_adjudication.get("policyHash"), "adjudication.policyHash"
    )
    score_vector_hash = require_sha256_digest(
        raw_adjudication.get("scoreVectorHash"), "adjudication.scoreVectorHash"
    )

    raw_weights = _require_list(
        raw_adjudication.get("distillationWeights"), "adjudication.distillationWeights"
    )
    weights: List[DadDistillationWeight] = []
    seen_weighted_proposals: set[str] = set()

    for idx, item in enumerate(raw_weights):
        entry = _require_mapping(item, f"adjudication.distillationWeights[{idx}]")
        prop_hash = require_sha256_digest(
            entry.get("proposalHash"), f"adjudication.distillationWeights[{idx}].proposalHash"
        )
        if prop_hash not in proposals_by_hash:
            raise DadValidationError(
                f"adjudication.distillationWeights[{idx}] references unknown proposalHash {prop_hash}"
            )
        if prop_hash in seen_weighted_proposals:
            raise DadValidationError(
                f"Duplicate proposalHash in adjudication.distillationWeights: {prop_hash}"
            )
        seen_weighted_proposals.add(prop_hash)

        sub_id = _require_non_empty_str(
            entry.get("substrateId"), f"adjudication.distillationWeights[{idx}].substrateId"
        )
        if sub_id != proposals_by_hash[prop_hash].substrate_id:
            raise DadValidationError(
                f"adjudication.distillationWeights[{idx}].substrateId '{sub_id}' does not match "
                f"proposal substrate '{proposals_by_hash[prop_hash].substrate_id}'"
            )

        raw_w = entry.get("weight")
        if isinstance(raw_w, bool) or not isinstance(raw_w, (int, float)) or not math.isfinite(raw_w):
            raise DadValidationError(
                f"adjudication.distillationWeights[{idx}].weight must be a finite number, got {raw_w!r}"
            )
        w = float(raw_w)
        if w < 0.0:
            raise DadValidationError(
                f"adjudication.distillationWeights[{idx}].weight must be non-negative, got {w}"
            )
        weights.append(DadDistillationWeight(proposal_hash=prop_hash, substrate_id=sub_id, weight=w))

    missing_weights = [
        prop_hash for prop_hash in proposals_by_hash.keys() if prop_hash not in seen_weighted_proposals
    ]
    if missing_weights:
        raise DadValidationError(
            f"MoM adjudication missing distillationWeights for proposal(s): {missing_weights}"
        )

    # Invariant 5: distillationWeightsHash must match the canonical hash of distillationWeights
    declared_weights_hash = require_sha256_digest(
        raw_adjudication.get("distillationWeightsHash"), "adjudication.distillationWeightsHash"
    )
    computed_weights_hash = sha256_json(raw_weights)
    if declared_weights_hash != computed_weights_hash:
        raise DadValidationError(
            f"adjudication.distillationWeightsHash mismatch: declared {declared_weights_hash}, "
            f"computed {computed_weights_hash}"
        )

    raw_rejects = _require_list(
        raw_adjudication.get("rejects", []), "adjudication.rejects", allow_empty=True
    )
    rejects: List[DadRejectRecord] = []
    seen_rejects: set[str] = set()
    for idx, item in enumerate(raw_rejects):
        entry = _require_mapping(item, f"adjudication.rejects[{idx}]")
        rej_hash = require_sha256_digest(
            entry.get("proposalHash"), f"adjudication.rejects[{idx}].proposalHash"
        )
        if rej_hash not in proposals_by_hash:
            raise DadValidationError(
                f"adjudication.rejects[{idx}] references unknown proposalHash {rej_hash}"
            )
        if rej_hash == winner_proposal_hash:
            raise DadValidationError(
                f"adjudication.winnerProposalHash {winner_proposal_hash} cannot also appear in rejects"
            )
        if rej_hash in seen_rejects:
            raise DadValidationError(f"Duplicate proposalHash in adjudication.rejects: {rej_hash}")
        seen_rejects.add(rej_hash)

        raw_reasons = _require_list(
            entry.get("reasonCodes"), f"adjudication.rejects[{idx}].reasonCodes"
        )
        reasons = tuple(
            _require_non_empty_str(r, f"adjudication.rejects[{idx}].reasonCodes[{r_idx}]")
            for r_idx, r in enumerate(raw_reasons)
        )
        rejects.append(DadRejectRecord(proposal_hash=rej_hash, reason_codes=reasons))

    return DadAdjudicationRecord(
        winner_proposal_hash=winner_proposal_hash,
        winner_substrate_id=winner_substrate_id,
        adjudicator_substrate_id=adjudicator_substrate_id,
        policy_hash=policy_hash,
        score_vector_hash=score_vector_hash,
        distillation_weights=tuple(weights),
        distillation_weights_hash=declared_weights_hash,
        rejects=tuple(rejects),
        adjudication_hash=sha256_json(raw_adjudication),
    )


def validate_dad_export_row(raw_dad: Mapping[str, Any]) -> DadExportRow:
    """Validate the DaD export record shape (`dadVersion: 0`)."""
    raw_dad = _require_mapping(raw_dad, "dad")

    version = raw_dad.get("dadVersion")
    if isinstance(version, bool) or version != DAD_SUPPORTED_VERSION:
        raise DadValidationError(
            f"Unsupported or missing dadVersion: {version!r} (expected {DAD_SUPPORTED_VERSION})"
        )

    mom_root = require_sha256_digest(raw_dad.get("momTranscriptRoot"), "dad.momTranscriptRoot")
    winner_hash = require_sha256_digest(raw_dad.get("winnerProposalHash"), "dad.winnerProposalHash")
    winner_sub = _require_non_empty_str(raw_dad.get("winnerSubstrateId"), "dad.winnerSubstrateId")
    teacher_set_hash = require_sha256_digest(raw_dad.get("teacherSetHash"), "dad.teacherSetHash")
    weights_hash = require_sha256_digest(
        raw_dad.get("distillationWeightsHash"), "dad.distillationWeightsHash"
    )

    raw_student = _require_mapping(raw_dad.get("studentTarget"), "dad.studentTarget")
    student_family = _require_non_empty_str(
        raw_student.get("family"), "dad.studentTarget.family"
    )
    student_adapter = _require_non_empty_str(
        raw_student.get("adapterId"), "dad.studentTarget.adapterId"
    )

    score_vector_hash = require_sha256_digest(
        raw_dad.get("scoreVectorHash"), "dad.scoreVectorHash"
    )

    accepted = raw_dad.get("accepted")
    if not isinstance(accepted, bool):
        raise DadValidationError(f"dad.accepted must be a boolean, got {accepted!r}")

    return DadExportRow(
        dad_version=version,
        mom_transcript_root=mom_root,
        winner_proposal_hash=winner_hash,
        winner_substrate_id=winner_sub,
        teacher_set_hash=teacher_set_hash,
        distillation_weights_hash=weights_hash,
        student_target=DadStudentTarget(family=student_family, adapter_id=student_adapter),
        score_vector_hash=score_vector_hash,
        accepted=accepted,
    )


def verify_dad_bundle(
    bundle: Mapping[str, Any],
    *,
    require_accepted: bool = True,
    require_proposal_payloads: bool = False,
) -> VerifiedDadBundle:
    """Verify a complete DaD bundle against the 5-part DaD validity invariant and momTranscriptRoot."""
    bundle = _require_mapping(bundle, "bundle")

    raw_dad = bundle.get("dad")
    export_row = validate_dad_export_row(raw_dad)
    if require_accepted and not export_row.accepted:
        raise DadValidationError("DaD record has accepted=False and cannot be imported for training")

    raw_proposal_payloads = bundle.get("proposalPayloads")
    proposal_payloads: Dict[str, Any] = {}
    if raw_proposal_payloads is not None:
        raw_proposal_payloads = _require_mapping(raw_proposal_payloads, "proposalPayloads")
        proposal_payloads = dict(raw_proposal_payloads)

    raw_critique_payloads = bundle.get("critiquePayloads")
    critique_payloads = (
        dict(_require_mapping(raw_critique_payloads, "critiquePayloads"))
        if raw_critique_payloads is not None
        else None
    )

    raw_response_payloads = bundle.get("responsePayloads")
    response_payloads = (
        dict(_require_mapping(raw_response_payloads, "responsePayloads"))
        if raw_response_payloads is not None
        else None
    )

    # Support either `round` (single round) or `rounds` (list of rounds)
    raw_rounds = bundle.get("rounds")
    if raw_rounds is None and "round" in bundle:
        raw_rounds = [bundle["round"]]
    raw_rounds_list = _require_list(raw_rounds, "rounds")

    debate_rounds: List[DadDebateRoundRecord] = []
    proposals_by_hash: Dict[str, DadProposalRecord] = {}
    ordered_substrate_roots: List[str] = []

    for r_idx, raw_r in enumerate(raw_rounds_list):
        validated_round = validate_debate_round(
            raw_r,
            proposal_payloads=proposal_payloads if proposal_payloads else None,
            critique_payloads=critique_payloads,
            response_payloads=response_payloads,
        )
        if validated_round.round_index != r_idx:
            raise DadValidationError(
                f"Non-sequential debate round index {validated_round.round_index} at position {r_idx}"
            )
        debate_rounds.append(validated_round)
        for prop in validated_round.proposals:
            if prop.proposal_hash in proposals_by_hash:
                raise DadValidationError(
                    f"Duplicate proposalHash across rounds: {prop.proposal_hash}"
                )
            proposals_by_hash[prop.proposal_hash] = prop
            ordered_substrate_roots.append(prop.substrate_transcript_root)

    if require_proposal_payloads:
        missing_payloads = [
            p_hash for p_hash in proposals_by_hash.keys() if p_hash not in proposal_payloads
        ]
        if missing_payloads:
            raise DadValidationError(
                f"Missing resolved proposalPayloads for proposalHash(es): {missing_payloads}"
            )

    raw_adjudication = bundle.get("adjudication")
    adjudication = validate_adjudication_record(raw_adjudication, proposals_by_hash)

    # Verify export_row fields match adjudication
    if export_row.winner_proposal_hash != adjudication.winner_proposal_hash:
        raise DadValidationError(
            f"dad.winnerProposalHash ({export_row.winner_proposal_hash}) does not match "
            f"adjudication.winnerProposalHash ({adjudication.winner_proposal_hash})"
        )
    if export_row.winner_substrate_id != adjudication.winner_substrate_id:
        raise DadValidationError(
            f"dad.winnerSubstrateId ({export_row.winner_substrate_id}) does not match "
            f"adjudication.winnerSubstrateId ({adjudication.winner_substrate_id})"
        )
    if export_row.distillation_weights_hash != adjudication.distillation_weights_hash:
        raise DadValidationError(
            f"dad.distillationWeightsHash ({export_row.distillation_weights_hash}) does not match "
            f"re-derived adjudication.distillationWeightsHash ({adjudication.distillation_weights_hash})"
        )
    if export_row.score_vector_hash != adjudication.score_vector_hash:
        raise DadValidationError(
            f"dad.scoreVectorHash ({export_row.score_vector_hash}) does not match "
            f"adjudication.scoreVectorHash ({adjudication.score_vector_hash})"
        )

    # Verify MoM transcript envelope binding all 5 parts to momTranscriptRoot
    raw_transcript = _require_mapping(bundle.get("transcript"), "transcript")
    mom_version = raw_transcript.get("momVersion")
    if isinstance(mom_version, bool) or mom_version != MOM_SUPPORTED_VERSION:
        raise DadValidationError(
            f"Unsupported transcript.momVersion: {mom_version!r} (expected {MOM_SUPPORTED_VERSION})"
        )
    require_sha256_digest(raw_transcript.get("routePlanHash"), "transcript.routePlanHash")
    require_sha256_digest(raw_transcript.get("cfrPolicyHash"), "transcript.cfrPolicyHash")

    transcript_sub_roots = _require_list(
        raw_transcript.get("substrateTranscriptRoots"), "transcript.substrateTranscriptRoots"
    )
    if list(transcript_sub_roots) != ordered_substrate_roots:
        raise DadValidationError(
            f"transcript.substrateTranscriptRoots {transcript_sub_roots} does not match "
            f"debate proposal substrateTranscriptRoots {ordered_substrate_roots}"
        )

    transcript_round_hashes = _require_list(
        raw_transcript.get("debateRoundHashes"), "transcript.debateRoundHashes"
    )
    expected_round_hashes = [r.round_hash for r in debate_rounds]
    if list(transcript_round_hashes) != expected_round_hashes:
        raise DadValidationError(
            f"transcript.debateRoundHashes {transcript_round_hashes} does not match "
            f"computed round hashes {expected_round_hashes}"
        )

    transcript_adj_hash = require_sha256_digest(
        raw_transcript.get("adjudicationHash"), "transcript.adjudicationHash"
    )
    if transcript_adj_hash != adjudication.adjudication_hash:
        raise DadValidationError(
            f"transcript.adjudicationHash ({transcript_adj_hash}) does not match "
            f"computed adjudication hash ({adjudication.adjudication_hash})"
        )

    computed_mom_root = sha256_json(raw_transcript)
    if computed_mom_root != export_row.mom_transcript_root:
        raise DadValidationError(
            f"dad.momTranscriptRoot ({export_row.mom_transcript_root}) does not match "
            f"computed transcript root ({computed_mom_root})"
        )

    declared_mom_root = bundle.get("momTranscriptRoot")
    if declared_mom_root is not None and declared_mom_root != computed_mom_root:
        raise DadValidationError(
            f"bundle.momTranscriptRoot ({declared_mom_root}) does not match "
            f"computed transcript root ({computed_mom_root})"
        )

    # Optional routePlan cross-check when routePlan is included in the bundle
    raw_route_plan = bundle.get("routePlan")
    if raw_route_plan is not None:
        raw_route_plan = _require_mapping(raw_route_plan, "routePlan")
        if raw_route_plan.get("mode") != "escalated":
            raise DadValidationError(
                f"DaD requires routePlan.mode='escalated', got {raw_route_plan.get('mode')!r}"
            )
        if raw_route_plan.get("distillationMode") not in ("debate_adjudicated", None):
            raise DadValidationError(
                f"Incompatible routePlan.distillationMode: {raw_route_plan.get('distillationMode')!r}"
            )
        computed_plan_hash = sha256_json(raw_route_plan)
        if computed_plan_hash != raw_transcript.get("routePlanHash"):
            raise DadValidationError(
                f"transcript.routePlanHash ({raw_transcript.get('routePlanHash')}) does not match "
                f"computed routePlan hash ({computed_plan_hash})"
            )

    raw_request = bundle.get("request")
    request_payload: Optional[Mapping[str, Any]] = None
    if raw_request is not None:
        request_payload = _require_mapping(raw_request, "request")
        if raw_route_plan is not None and "inputHash" in raw_route_plan:
            expected_input_hash = require_sha256_digest(
                raw_route_plan.get("inputHash"), "routePlan.inputHash"
            )
            computed_input_hash = sha256_json(request_payload)
            if computed_input_hash != expected_input_hash:
                raise DadValidationError(
                    f"request payload hash ({computed_input_hash}) does not match "
                    f"routePlan.inputHash ({expected_input_hash})"
                )

    weights_map = {w.proposal_hash: w.weight for w in adjudication.distillation_weights}
    rejected_hashes = tuple(r.proposal_hash for r in adjudication.rejects)

    return VerifiedDadBundle(
        export_row=export_row,
        debate_rounds=tuple(debate_rounds),
        adjudication=adjudication,
        mom_transcript_root=computed_mom_root,
        proposals_by_hash=proposals_by_hash,
        weights_by_proposal_hash=weights_map,
        rejected_proposal_hashes=rejected_hashes,
        resolved_proposals=proposal_payloads,
        request_payload=request_payload,
    )
