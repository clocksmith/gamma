"""SAME-R Approach Selector and Saturation Engine.

Implements the canonical selector, saturation evaluator, approach registry,
and selection-receipt generation according to SELECTOR_AND_SATURATION.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ApproachStatus(str, Enum):
    ELIGIBLE = "eligible"
    DISABLED = "disabled"
    BLOCKED = "blocked"
    SATURATED_FOR_SCOPE = "saturated_for_scope"
    SUPERSEDED = "superseded"


class TrialDisposition(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    INVALIDATED = "invalidated"
    SATURATED = "saturated"
    PROMOTED = "promoted"


@dataclass
class ApproachEntry:
    approach_id: str
    approach_revision: str
    mechanism_type: str
    implementation_pointer: str
    eligible_domains: List[str]
    eligible_capabilities: List[str]
    required_inputs: List[str]
    produced_artifacts: List[str]
    allowed_roles: List[str]
    status: ApproachStatus = ApproachStatus.ELIGIBLE
    accepted_trial_ids: List[str] = field(default_factory=list)
    rejected_trial_ids: List[str] = field(default_factory=list)
    blocked_trial_ids: List[str] = field(default_factory=list)
    saturated_scope_ids: List[str] = field(default_factory=list)
    priority_weight: float = 1.0


@dataclass
class ParticipantEntry:
    participant_id: str
    kind: str  # human | model | script | deterministic_program
    allowed_roles: List[str]  # proposer | critic | teacher | executor | evaluator | selector
    allowed_domains: List[str]
    budget_limit: float = 1000.0
    budget_spent: float = 0.0


@dataclass
class TrialRecord:
    trial_id: str
    domain: str
    capability: str
    population: str
    approach_id: str
    intervention_id: str
    causal_contract_hash: str
    run_contract_hash: str
    disposition: TrialDisposition
    effect_vs_anchor: float
    effect_vs_random_control: float
    budget_spent: float
    receipt_hashes: List[str]
    guardrail_status: str = "pass"
    uncertainty: float = 0.0


@dataclass
class SaturationRule:
    rule_id: str
    minimum_effect: Optional[float] = None
    no_improvement_window: Optional[int] = None
    budget_limit: Optional[float] = None


@dataclass
class SelectionReceipt:
    selector_id: str
    selector_revision: str
    history_hash: str
    registry_hash: str
    frozen_contract_hash: str
    budget_before: float
    candidates_considered: List[str]
    candidates_rejected_with_reasons: Dict[str, str]
    selected_approach_id: Optional[str]
    selected_intervention_id: Optional[str]
    causal_contract_hash: Optional[str]
    budget_debit: float
    saturation_check: Dict[str, Any]
    receipt_hash: str = ""


def compute_sha256(data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ApproachRegistry:
    def __init__(self):
        self._approaches: Dict[str, ApproachEntry] = {}

    def register(self, entry: ApproachEntry) -> None:
        self._approaches[entry.approach_id] = entry

    def get(self, approach_id: str) -> Optional[ApproachEntry]:
        return self._approaches.get(approach_id)

    def list_eligible(self, domain: str, capability: str) -> List[ApproachEntry]:
        return [
            app
            for app in self._approaches.values()
            if app.status == ApproachStatus.ELIGIBLE
            and (not app.eligible_domains or domain in app.eligible_domains)
            and (not app.eligible_capabilities or capability in app.eligible_capabilities)
        ]

    def hash(self) -> str:
        serialized = [asdict(a) for a in sorted(self._approaches.values(), key=lambda x: x.approach_id)]
        return compute_sha256(serialized)


class TrialHistory:
    def __init__(self):
        self._trials: List[TrialRecord] = []

    def record(self, trial: TrialRecord) -> None:
        self._trials.append(trial)

    def get_by_approach(self, approach_id: str) -> List[TrialRecord]:
        return [t for t in self._trials if t.approach_id == approach_id]

    def get_by_scope(self, domain: str, capability: str) -> List[TrialRecord]:
        return [t for t in self._trials if t.domain == domain and t.capability == capability]

    def total_budget_spent(self) -> float:
        return sum(t.budget_spent for t in self._trials)

    def hash(self) -> str:
        serialized = [asdict(t) for t in self._trials]
        return compute_sha256(serialized)


class SaturationEngine:
    @staticmethod
    def evaluate(
        approach: ApproachEntry,
        history: TrialHistory,
        rule: SaturationRule,
        domain: str,
        capability: str,
    ) -> Tuple[bool, str]:
        """Evaluates whether an approach or scope has reached a saturation boundary."""
        trials = [
            t
            for t in history.get_by_approach(approach.approach_id)
            if t.domain == domain and t.capability == capability
        ]

        if not trials:
            return False, "no_prior_trials"

        # 1. Check budget exhaustion
        if rule.budget_limit is not None:
            spent = sum(t.budget_spent for t in trials)
            if spent >= rule.budget_limit:
                return True, f"budget_limit_exhausted: spent={spent} >= limit={rule.budget_limit}"

        # 2. Check no-improvement window
        if rule.no_improvement_window is not None and len(trials) >= rule.no_improvement_window:
            recent = trials[-rule.no_improvement_window :]
            # If no recent trial observed a positive delta over anchor and control
            improvements = [
                t for t in recent if t.effect_vs_anchor > 0 and t.effect_vs_random_control > 0
            ]
            if not improvements:
                return True, f"no_improvement_in_window_{rule.no_improvement_window}"

        # 3. Check minimum effect threshold
        if rule.minimum_effect is not None and len(trials) >= 3:
            recent_effects = [t.effect_vs_anchor for t in trials[-3:]]
            avg_effect = sum(recent_effects) / len(recent_effects)
            if avg_effect < rule.minimum_effect:
                return True, f"effect_below_minimum_threshold: avg={avg_effect:.4f} < min={rule.minimum_effect}"

        return False, "active"


class ApproachSelector:
    def __init__(
        self,
        selector_id: str = "samer-selector-v1",
        selector_revision: str = "1.0.0",
        saturation_engine: Optional[SaturationEngine] = None,
    ):
        self.selector_id = selector_id
        self.selector_revision = selector_revision
        self.saturation_engine = saturation_engine or SaturationEngine()

    def select_approach(
        self,
        registry: ApproachRegistry,
        history: TrialHistory,
        frozen_contract: Dict[str, Any],
        selector_budget: float,
        saturation_rule: Optional[SaturationRule] = None,
    ) -> SelectionReceipt:
        domain = frozen_contract.get("domain", "")
        capability = frozen_contract.get("capability", "")
        frozen_contract_hash = compute_sha256(frozen_contract)
        registry_hash = registry.hash()
        history_hash = history.hash()
        rule = saturation_rule or SaturationRule(
            rule_id="default_saturation",
            no_improvement_window=5,
            minimum_effect=0.001,
            budget_limit=selector_budget,
        )

        eligible = registry.list_eligible(domain, capability)
        candidates_considered = [a.approach_id for a in eligible]
        candidates_rejected: Dict[str, str] = {}
        viable_approaches: List[Tuple[ApproachEntry, float]] = []
        saturation_checks: Dict[str, Any] = {}

        for app in eligible:
            is_sat, sat_reason = self.saturation_engine.evaluate(
                app, history, rule, domain, capability
            )
            saturation_checks[app.approach_id] = {
                "saturated": is_sat,
                "reason": sat_reason,
            }

            if is_sat:
                candidates_rejected[app.approach_id] = f"saturated: {sat_reason}"
                continue

            # Compute selection score based on historical effect vs anchor and uncertainty
            app_trials = history.get_by_approach(app.approach_id)
            if not app_trials:
                # Cold start exploration boost
                score = 100.0 * app.priority_weight
            else:
                avg_effect = sum(t.effect_vs_anchor for t in app_trials) / len(app_trials)
                score = (avg_effect + 1.0) * app.priority_weight

            viable_approaches.append((app, score))

        if not viable_approaches:
            receipt = SelectionReceipt(
                selector_id=self.selector_id,
                selector_revision=self.selector_revision,
                history_hash=history_hash,
                registry_hash=registry_hash,
                frozen_contract_hash=frozen_contract_hash,
                budget_before=selector_budget,
                candidates_considered=candidates_considered,
                candidates_rejected_with_reasons=candidates_rejected,
                selected_approach_id=None,
                selected_intervention_id=None,
                causal_contract_hash=None,
                budget_debit=0.0,
                saturation_check=saturation_checks,
            )
            receipt.receipt_hash = compute_sha256(asdict(receipt))
            return receipt

        # Sort by score descending
        viable_approaches.sort(key=lambda x: x[1], reverse=True)
        selected_app, _ = viable_approaches[0]
        selected_intervention_id = f"intervention_{selected_app.approach_id}_{len(history.get_by_approach(selected_app.approach_id)) + 1}"

        causal_contract = {
            "domain": domain,
            "capability": capability,
            "approach_id": selected_app.approach_id,
            "intervention_id": selected_intervention_id,
            "frozen_contract_hash": frozen_contract_hash,
        }
        causal_contract_hash = compute_sha256(causal_contract)

        receipt = SelectionReceipt(
            selector_id=self.selector_id,
            selector_revision=self.selector_revision,
            history_hash=history_hash,
            registry_hash=registry_hash,
            frozen_contract_hash=frozen_contract_hash,
            budget_before=selector_budget,
            candidates_considered=candidates_considered,
            candidates_rejected_with_reasons=candidates_rejected,
            selected_approach_id=selected_app.approach_id,
            selected_intervention_id=selected_intervention_id,
            causal_contract_hash=causal_contract_hash,
            budget_debit=1.0,
            saturation_check=saturation_checks,
        )
        receipt.receipt_hash = compute_sha256(asdict(receipt))
        return receipt
