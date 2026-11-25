#!/usr/bin/env python3
"""Rung 2 lifecycle cost & break-even analyzer for Gammatron (clocksmith/deco#88).

Decomposes every arm's total cost across setup, upgrade maintenance, and per-route
execution (including 100% of `always-replan` fallback spend on abstentions):

    C_arm(V; r) = C_setup(r) + C_maint(r) + V * c_route

where:
  - C_setup(r) = spend_setup_usd + r * (adapter_authoring_min + guard_authoring_min + setup_learner_wall_min)
  - C_maint(r) = spend_maint_usd + r * (adapter_maintenance_min + guard_maintenance_min + maint_learner_wall_min)
  - c_route    = own_decision_per_route_usd + p_abstain * fallback_per_abstention_usd

Computes exact pairwise break-even workflow volumes V*(0), V*(r), and V*(2r) between
the primary learned arm (`repair-boundary`) and every safety-eligible comparator
(`expert-guard`, `agent-written-guard`, `rule-selector`, `always-replan`), identifying
when no positive break-even volume exists (`no-break-even`).

Also audits historical Stage A / draft OpenProject and ERPNext adapter files and labels
them `unmeasured_historical_code` (`usableForRung2EffortClaim: false`) so declared or
pre-existing code is never mistaken for prospective Rung 2 effort measurements.

Read-only, Python 3.10+, zero external dependencies, $0 model spend.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from score_after_fallback import (
    FALLBACK_ARM,
    LEARNED_VARIANTS,
    MAINT_PHASES,
    SETUP_PHASES,
    SIMPLE_GUARD_ARMS,
    money,
    read_jsonl,
    score_after_fallback,
)

HERE = Path(__file__).resolve().parent
QUALIFICATION_DIR = HERE.parent.parent
DEFAULT_VOLUMES = (10, 25, 50, 100, 250, 500, 1000)


def count_non_comment_js_loc(text: str) -> int:
    count = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            continue
        count += 1
    return count


def extract_exported_fn_loc(source: str, fn_name: str) -> int:
    marker = f'export function {fn_name}'
    start = source.find(marker)
    if start < 0:
        return 0
    depth = 0
    begun = False
    end = len(source)
    for idx in range(start, len(source)):
        ch = source[idx]
        if ch == '{':
            depth += 1
            begun = True
        elif ch == '}':
            depth -= 1
            if begun and depth == 0:
                end = idx + 1
                break
    return count_non_comment_js_loc(source[start:end])


def audit_legacy_adapters(qualification_dir: Path = QUALIFICATION_DIR) -> list[dict[str, Any]]:
    """Audit historical OpenProject/ERPNext adapter & learner glue as unmeasured historical code."""
    qual_mjs = qualification_dir / 'repair-boundary-qualification.mjs'
    op_arm_mjs = qualification_dir / 'three-arm' / 'repair-boundary-arm.mjs'
    erp_arm_mjs = qualification_dir / 'three-arm-erpnext' / 'erp-learner.mjs'

    entries: list[dict[str, Any]] = []
    if qual_mjs.exists():
        src = qual_mjs.read_text(encoding='utf-8')
        entries.append({
            'application': 'openproject',
            'component': 'projectOpenProjectHalScalars',
            'file': str(qual_mjs.relative_to(qualification_dir.parent.parent)),
            'nonCommentLoc': extract_exported_fn_loc(src, 'projectOpenProjectHalScalars'),
            'status': 'unmeasured_historical_code',
            'usableForRung2EffortClaim': False,
            'note': 'Authored during Gates 3-4 before Stage A; authoring time was not metered.',
        })
        entries.append({
            'application': 'erpnext',
            'component': 'projectFrappeResourceScalars',
            'file': str(qual_mjs.relative_to(qualification_dir.parent.parent)),
            'nonCommentLoc': extract_exported_fn_loc(src, 'projectFrappeResourceScalars'),
            'status': 'unmeasured_historical_code',
            'usableForRung2EffortClaim': False,
            'note': 'Authored during Gate 4 before ERPNext screen; authoring time was not metered.',
        })
    if op_arm_mjs.exists():
        entries.append({
            'application': 'openproject',
            'component': 'repair-boundary-arm-readplan-glue',
            'file': str(op_arm_mjs.relative_to(qualification_dir.parent.parent)),
            'nonCommentLoc': count_non_comment_js_loc(op_arm_mjs.read_text(encoding='utf-8')),
            'status': 'unmeasured_historical_code',
            'usableForRung2EffortClaim': False,
            'note': 'Stage A read-plan validator and HAL link follower; frozen historical code.',
        })
    if erp_arm_mjs.exists():
        entries.append({
            'application': 'erpnext',
            'component': 'erp-learner-readplan-glue',
            'file': str(erp_arm_mjs.relative_to(qualification_dir.parent.parent)),
            'nonCommentLoc': count_non_comment_js_loc(erp_arm_mjs.read_text(encoding='utf-8')),
            'status': 'unmeasured_historical_code',
            'usableForRung2EffortClaim': False,
            'note': 'Draft ERPNext read-plan validator and resource follower; unmeasured historical code.',
        })
    return entries


def split_phase_effort(phases: list[dict[str, Any]], arm: str) -> dict[str, Decimal]:
    """Separate setup vs. maintenance effort minutes and model spend from phase records."""
    setup_spend = Decimal(0)
    maint_spend = Decimal(0)
    setup_adapter_min = Decimal(0)
    maint_adapter_min = Decimal(0)
    setup_guard_min = Decimal(0)
    maint_guard_min = Decimal(0)
    setup_learner_min = Decimal(0)
    maint_learner_min = Decimal(0)

    disagg_keys = (
        'adapterAuthoringMinutes',
        'adapterMaintenanceMinutes',
        'guardAuthoringMinutes',
        'guardMaintenanceMinutes',
        'learnerWallMinutes',
    )
    for p in phases:
        if p.get('arm') != arm:
            continue
        ph = p.get('phase')
        if ph in SETUP_PHASES:
            setup_spend += money(p.get('costUsd'))
            if any(k in p and p[k] is not None for k in disagg_keys):
                setup_adapter_min += money(p.get('adapterAuthoringMinutes')) + money(p.get('adapterMaintenanceMinutes'))
                setup_guard_min += money(p.get('guardAuthoringMinutes')) + money(p.get('guardMaintenanceMinutes'))
                setup_learner_min += money(p.get('learnerWallMinutes'))
            elif p.get('authoringMinutes') is not None:
                m = money(p['authoringMinutes'])
                if arm in SIMPLE_GUARD_ARMS:
                    setup_guard_min += m
                elif arm in LEARNED_VARIANTS:
                    setup_learner_min += m
            elif p.get('wallMs') is not None:
                setup_learner_min += money(p['wallMs']) / Decimal(60000)
        elif ph in MAINT_PHASES:
            maint_spend += money(p.get('costUsd'))
            if any(k in p and p[k] is not None for k in disagg_keys):
                maint_adapter_min += money(p.get('adapterAuthoringMinutes')) + money(p.get('adapterMaintenanceMinutes'))
                maint_guard_min += money(p.get('guardAuthoringMinutes')) + money(p.get('guardMaintenanceMinutes'))
                maint_learner_min += money(p.get('learnerWallMinutes'))
            elif p.get('authoringMinutes') is not None:
                m = money(p['authoringMinutes'])
                if arm in SIMPLE_GUARD_ARMS:
                    maint_guard_min += m
                elif arm in LEARNED_VARIANTS:
                    maint_learner_min += m
            elif p.get('wallMs') is not None:
                maint_learner_min += money(p['wallMs']) / Decimal(60000)

    setup_min = setup_adapter_min + setup_guard_min + setup_learner_min
    maint_min = maint_adapter_min + maint_guard_min + maint_learner_min
    return {
        'setupSpendUsd': setup_spend,
        'maintSpendUsd': maint_spend,
        'setupAdapterMinutes': setup_adapter_min,
        'maintAdapterMinutes': maint_adapter_min,
        'setupGuardMinutes': setup_guard_min,
        'maintGuardMinutes': maint_guard_min,
        'setupLearnerWallMinutes': setup_learner_min,
        'maintLearnerWallMinutes': maint_learner_min,
        'setupMinutesTotal': setup_min,
        'maintMinutesTotal': maint_min,
    }


def build_arm_curve(
    arm_summary: dict[str, Any],
    phases: list[dict[str, Any]],
    rate_r: Decimal,
    volumes: tuple[int, ...] = DEFAULT_VOLUMES,
) -> dict[str, Any]:
    arm = arm_summary['arm']
    effort = split_phase_effort(phases, arm)

    total_routes = int(arm_summary['validCount']) + int(arm_summary['invalidCaseCount'])
    abstentions = int(arm_summary['abstentionsOnValid']) + int(arm_summary['abstentionsOnInvalid'])
    own_spend = money(arm_summary['spendDecisionOwnUsd'])
    fb_spend = money(arm_summary['spendFallbackUsd'])

    if total_routes > 0:
        own_per_route = own_spend / Decimal(total_routes)
        fb_per_route = fb_spend / Decimal(total_routes)
        abstain_rate = Decimal(abstentions) / Decimal(total_routes)
    else:
        own_per_route = Decimal(0)
        fb_per_route = Decimal(0)
        abstain_rate = Decimal(0)

    fb_per_abstention = (fb_spend / Decimal(abstentions)) if abstentions > 0 else Decimal(0)
    marginal_per_route = own_per_route + fb_per_route

    rates = {
        'zero': Decimal(0),
        'r': rate_r,
        'doubleR': Decimal(2) * rate_r,
    }
    by_rate: dict[str, Any] = {}
    for label, rate_val in rates.items():
        setup_cost = effort['setupSpendUsd'] + rate_val * effort['setupMinutesTotal']
        maint_cost = effort['maintSpendUsd'] + rate_val * effort['maintMinutesTotal']
        fixed_cost = setup_cost + maint_cost
        curve = {
            str(v): str((fixed_cost + Decimal(v) * marginal_per_route).quantize(Decimal('0.0001')))
            for v in volumes
        }
        by_rate[label] = {
            'ratePerMinuteUsd': str(rate_val),
            'setupCostUsd': str(setup_cost.quantize(Decimal('0.0001'))),
            'maintenanceCostUsd': str(maint_cost.quantize(Decimal('0.0001'))),
            'fixedCostUsd': str(fixed_cost.quantize(Decimal('0.0001'))),
            'marginalPerRouteUsd': str(marginal_per_route.quantize(Decimal('0.000001'))),
            'costAtVolumeUsd': curve,
            '_fixed': fixed_cost,
            '_marginal': marginal_per_route,
        }

    return {
        'arm': arm,
        'voided': arm_summary['voided'],
        'meetsSafetyBar': arm_summary['meetsSafetyBar'],
        'validCompletedAfterFallback': arm_summary['validCompletedAfterFallback'],
        'validCount': arm_summary['validCount'],
        'evaluatedRoutes': total_routes,
        'abstentionsTotal': abstentions,
        'abstentionRate': round(float(abstain_rate), 6),
        'ownDecisionPerRouteUsd': str(own_per_route.quantize(Decimal('0.000001'))),
        'fallbackPerAbstentionUsd': str(fb_per_abstention.quantize(Decimal('0.000001'))),
        'expectedFallbackPerRouteUsd': str(fb_per_route.quantize(Decimal('0.000001'))),
        'marginalPerRouteUsd': str(marginal_per_route.quantize(Decimal('0.000001'))),
        'effortBreakdown': {k: str(v) for k, v in effort.items()},
        'byRate': {
            k: {ik: iv for ik, iv in v.items() if not ik.startswith('_')}
            for k, v in by_rate.items()
        },
        '_rawByRate': by_rate,
    }


def pairwise_breakeven_at_rate(
    learned_raw: dict[str, Any],
    comp_raw: dict[str, Any],
) -> dict[str, Any]:
    """Solve C_learned(V) < C_comp(V) <=> fixed_L + V * marg_L < fixed_C + V * marg_C."""
    fixed_l: Decimal = learned_raw['_fixed']
    marg_l: Decimal = learned_raw['_marginal']
    fixed_c: Decimal = comp_raw['_fixed']
    marg_c: Decimal = comp_raw['_marginal']

    delta_fixed = fixed_l - fixed_c          # >0 means learned costs more upfront
    marginal_saving = marg_c - marg_l        # >0 means learned saves money on each route

    if delta_fixed == 0 and marginal_saving == 0:
        return {
            'regime': 'tie-at-all-volumes',
            'deltaFixedUsd': '0.0000',
            'marginalSavingPerRouteUsd': '0.000000',
            'breakEvenVolumeRoutes': None,
            'rulePrediction': 'use-comparator',
        }
    if delta_fixed <= 0 and marginal_saving >= 0:
        return {
            'regime': 'dominates-at-all-volumes',
            'deltaFixedUsd': str(delta_fixed.quantize(Decimal('0.0001'))),
            'marginalSavingPerRouteUsd': str(marginal_saving.quantize(Decimal('0.000001'))),
            'breakEvenVolumeRoutes': 0.0,
            'rulePrediction': 'use-learned',
        }
    if delta_fixed > 0 and marginal_saving > 0:
        v_star = float((delta_fixed / marginal_saving).quantize(Decimal('0.01')))
        return {
            'regime': 'break-even-above-V*',
            'deltaFixedUsd': str(delta_fixed.quantize(Decimal('0.0001'))),
            'marginalSavingPerRouteUsd': str(marginal_saving.quantize(Decimal('0.000001'))),
            'breakEvenVolumeRoutes': v_star,
            'rulePrediction': f'use-learned-if-V-gt-{v_star:.2f}',
        }
    if delta_fixed < 0 and marginal_saving < 0:
        v_cap = float(((-delta_fixed) / (-marginal_saving)).quantize(Decimal('0.01')))
        return {
            'regime': 'loses-above-V*',
            'deltaFixedUsd': str(delta_fixed.quantize(Decimal('0.0001'))),
            'marginalSavingPerRouteUsd': str(marginal_saving.quantize(Decimal('0.000001'))),
            'breakEvenVolumeRoutes': v_cap,
            'rulePrediction': f'use-learned-only-if-V-lt-{v_cap:.2f}',
        }
    return {
        'regime': 'no-break-even',
        'deltaFixedUsd': str(delta_fixed.quantize(Decimal('0.0001'))),
        'marginalSavingPerRouteUsd': str(marginal_saving.quantize(Decimal('0.000001'))),
        'breakEvenVolumeRoutes': None,
        'rulePrediction': 'use-comparator',
    }


def generate_cost_report(
    routes: list[dict[str, Any]],
    phases: list[dict[str, Any]],
    key_doc: dict[str, Any],
    blind_files: list[dict[str, Any]],
    *,
    primary_learned: str = 'repair-boundary',
    rate_per_minute_usd: str | float | Decimal = '0.50',
    volumes: tuple[int, ...] = DEFAULT_VOLUMES,
    require_measured_adapter: bool = True,
    qualification_dir: Path = QUALIFICATION_DIR,
) -> dict[str, Any]:
    rate_r = money(rate_per_minute_usd)
    scored = score_after_fallback(
        routes=routes,
        phases=phases,
        key_doc=key_doc,
        blind_files=blind_files,
        primary_learned=primary_learned,
        rate_per_minute_usd=rate_r,
        require_measured_adapter=require_measured_adapter,
    )
    arm_models = {
        arm: build_arm_curve(summary, phases, rate_r, volumes=volumes)
        for arm, summary in scored.get('arms', {}).items()
    }

    comparisons: dict[str, Any] = {}
    learned_model = arm_models.get(primary_learned)
    if learned_model is not None:
        for comp_arm, comp_model in arm_models.items():
            if comp_arm == primary_learned:
                continue
            by_rate_cmp = {
                rate_key: pairwise_breakeven_at_rate(
                    learned_model['_rawByRate'][rate_key],
                    comp_model['_rawByRate'][rate_key],
                )
                for rate_key in ('zero', 'r', 'doubleR')
            }
            comparisons[comp_arm] = {
                'comparator': comp_arm,
                'comparatorMeetsSafetyBar': comp_model['meetsSafetyBar'],
                'learnedMeetsSafetyBar': learned_model['meetsSafetyBar'],
                'completionParityHolds': (
                    learned_model['validCompletedAfterFallback'] >= comp_model['validCompletedAfterFallback']
                ),
                'byRate': by_rate_cmp,
            }

    public_arm_models = {
        arm: {k: v for k, v in model.items() if not k.startswith('_')}
        for arm, model in arm_models.items()
    }
    return {
        'schema': 'gammatron-rung2-cost-breakeven-report/v1',
        'valid': scored['valid'],
        'problems': scored['problems'],
        'verdict': scored['verdict'],
        'primaryLearnedVariant': primary_learned,
        'authoringRatePerMinuteUsd': str(rate_r),
        'volumesEvaluated': list(volumes),
        'legacyAdapterProvenance': audit_legacy_adapters(qualification_dir),
        'arms': public_arm_models,
        'pairwiseBreakEven': comparisons,
    }


def selftest() -> None:
    legacy = audit_legacy_adapters(QUALIFICATION_DIR)
    assert len(legacy) >= 4, f'expected >=4 legacy adapter audit entries, got {len(legacy)}'
    assert all(e['status'] == 'unmeasured_historical_code' for e in legacy)
    assert all(e['usableForRung2EffortClaim'] is False for e in legacy)
    assert all(e['nonCommentLoc'] > 0 for e in legacy)

    # Synthetic 100-invalid + 100-valid holdout exercising all break-even regimes
    key_routes: dict[str, Any] = {}
    recipes: list[dict[str, Any]] = []
    for i in range(50):
        rid_op = f'op-inv-{i:02d}'
        recipes.append({'routeId': rid_op, 'familyId': 'op-fam'})
        key_routes[rid_op] = {
            'valid': False, 'why': 'hold', 'application': 'openproject',
            'familyId': 'op-fam', 'failureId': f'op-f-{i:02d}', 'confidence': 'sure',
        }
        rid_erp = f'erp-inv-{i:02d}'
        recipes.append({'routeId': rid_erp, 'familyId': 'erp-fam'})
        key_routes[rid_erp] = {
            'valid': False, 'why': 'draft', 'application': 'erpnext',
            'familyId': 'erp-fam', 'failureId': f'erp-f-{i:02d}', 'confidence': 'sure',
        }
    for i in range(50):
        rid_op = f'op-val-{i:02d}'
        recipes.append({'routeId': rid_op, 'familyId': 'op-fam'})
        key_routes[rid_op] = {'valid': True, 'why': 'ok', 'application': 'openproject', 'familyId': 'op-fam', 'confidence': 'sure'}
        rid_erp = f'erp-val-{i:02d}'
        recipes.append({'routeId': rid_erp, 'familyId': 'erp-fam'})
        key_routes[rid_erp] = {'valid': True, 'why': 'ok', 'application': 'erpnext', 'familyId': 'erp-fam', 'confidence': 'sure'}

    def route_rec(app: str, arm: str, rid: str, decision: str, cost: float) -> dict[str, Any]:
        wrote = decision == 'write'
        if app == 'openproject':
            before = {'lockVersion': 1, 'estimatedHours': 4}
            after = {'lockVersion': 2, 'estimatedHours': 12} if wrote else dict(before)
            extra = {'workHours': 12}
        else:
            before = {'modified': '2026-02-01 10:00:00.000000', 'terms': ''}
            after = {'modified': '2026-02-01 10:00:01.000000', 'terms': 'Confirmed CONF-1'} if wrote else dict(before)
            extra = {'reference': 'CONF-1'}
        return {
            'schema': 'gammatron-next-route-record/v1',
            'runId': 'r',
            'application': app,
            'upgrade': 'u1',
            'arm': arm,
            'routeId': rid,
            'decision': decision,
            'stopReason': None if wrote else 'abstain',
            'writeAttempted': wrote,
            'httpStatus': 200 if wrote else None,
            'before': before,
            'after': after,
            'committed': wrote,
            'effectMatches': wrote,
            **extra,
            'reads': 2,
            'modelCalls': 1 if arm == FALLBACK_ARM else 0,
            'costUsd': cost,
            'decisionWallMs': 5,
            'artifactSha256': 'a' * 64,
            'error': None,
        }

    routes: list[dict[str, Any]] = []
    for idx, r in enumerate(recipes):
        rid = r['routeId']
        meta = key_routes[rid]
        app = meta['application']
        is_val = meta['valid']
        # repair-boundary abstains on 10% of valid cases (conservative guard) + 100% of invalid cases
        rb_dec = ('stop' if idx % 10 == 0 else 'write') if is_val else 'stop'
        routes.append(route_rec(app, 'repair-boundary', rid, rb_dec, 0.0))
        # expert-guard writes 100% of valid cases + stops 100% of invalid cases
        routes.append(route_rec(app, 'expert-guard', rid, 'write' if is_val else 'stop', 0.0))
        # rule-selector abstains on 50% of valid cases + 100% of invalid cases
        rs_dec = ('stop' if idx % 2 == 0 else 'write') if is_val else 'stop'
        routes.append(route_rec(app, 'rule-selector', rid, rs_dec, 0.0))
        # always-replan costs $0.08 on every route
        routes.append(route_rec(app, FALLBACK_ARM, rid, 'write' if is_val else 'stop', 0.08))

    def phase_rec(
        app: str, arm: str, phase: str, cost: float,
        *, src: str = 'none', aa: float = 0.0, am: float = 0.0, ga: float = 0.0, gm: float = 0.0, lw: float = 0.0,
    ) -> dict[str, Any]:
        return {
            'schema': 'gammatron-three-arm-phase-record/v1',
            'runId': 'r',
            'application': app,
            'upgrade': 'u1',
            'arm': arm,
            'phase': phase,
            'adapterSource': src,
            'startedAt': '2026-11-24T00:00:00Z',
            'endedAt': '2026-11-24T00:01:00Z',
            'wallMs': int(lw * 60000),
            'adapterAuthoringMinutes': aa,
            'adapterMaintenanceMinutes': am,
            'guardAuthoringMinutes': ga,
            'guardMaintenanceMinutes': gm,
            'learnerWallMinutes': lw,
            'authoringMinutes': aa + am + ga + gm + lw,
            'adapterOrGuardLoc': 20 if src == 'human' or arm != FALLBACK_ARM else 0,
            'modelCalls': 0,
            'modelTurns': 0,
            'costUsd': cost,
            'budgetUsd': 0.0,
            'recordsCreated': 4,
            'outOfSurfaceCalls': 0,
            'artifactSha256': 'a' * 64,
            'completed': True,
        }

    phases = [
        # repair-boundary: 4 min adapter authoring + 1 min maintenance per app (10 min total -> $5.00 at r=$0.50)
        phase_rec('openproject', 'repair-boundary', 'discovery', 0.0, src='human', aa=4.0, lw=0.0),
        phase_rec('openproject', 'repair-boundary', 'maintenance', 0.0, src='human', am=1.0, lw=0.0),
        phase_rec('erpnext', 'repair-boundary', 'discovery', 0.0, src='human', aa=4.0, lw=0.0),
        phase_rec('erpnext', 'repair-boundary', 'maintenance', 0.0, src='human', am=1.0, lw=0.0),
        # expert-guard: 8 min authoring + 4 min maintenance per app (24 min total -> $12.00 at r=$0.50)
        phase_rec('openproject', 'expert-guard', 'discovery', 0.0, ga=8.0),
        phase_rec('openproject', 'expert-guard', 'maintenance', 0.0, gm=4.0),
        phase_rec('erpnext', 'expert-guard', 'discovery', 0.0, ga=8.0),
        phase_rec('erpnext', 'expert-guard', 'maintenance', 0.0, gm=4.0),
        # rule-selector: 6 min authoring + 2 min maintenance per app (16 min total -> $8.00 at r=$0.50)
        phase_rec('openproject', 'rule-selector', 'discovery', 0.0, ga=6.0),
        phase_rec('openproject', 'rule-selector', 'maintenance', 0.0, gm=2.0),
        phase_rec('erpnext', 'rule-selector', 'discovery', 0.0, ga=6.0),
        phase_rec('erpnext', 'rule-selector', 'maintenance', 0.0, gm=2.0),
        # always-replan: $0 setup, $0.08/route
        phase_rec('openproject', FALLBACK_ARM, 'discovery', 0.0),
        phase_rec('erpnext', FALLBACK_ARM, 'discovery', 0.0),
    ]

    report = generate_cost_report(
        routes=routes,
        phases=phases,
        key_doc={'routes': key_routes},
        blind_files=[{'recipes': recipes}],
        rate_per_minute_usd='0.50',
    )
    assert report['valid'] is True, report['problems']
    assert report['arms']['repair-boundary']['voided'] is False

    # 1. vs always-replan at r=$0.50:
    #    fixed_L = $5.00, marg_L = (110/200)*$0.08 = $0.044; fixed_C = $0, marg_C = $0.08 -> saving $0.036/route
    #    V*(r) = 5.00 / 0.036 = 138.89 routes (break-even-above-V*)
    vs_replan_r = report['pairwiseBreakEven'][FALLBACK_ARM]['byRate']['r']
    assert vs_replan_r['regime'] == 'break-even-above-V*', vs_replan_r
    assert abs(vs_replan_r['breakEvenVolumeRoutes'] - 138.89) < 0.02, vs_replan_r

    # 2. vs expert-guard:
    #    At rate 0: fixed_L = 0 == fixed_C = 0, marg_L = $0.044 > marg_C = $0.040 -> no-break-even!
    #    At rate r=$0.50: fixed_L = $5.00 < fixed_C = $12.00 (delta = -$7.00), marg_L - marg_C = +$0.004 -> loses-above-V* at V* = 1750!
    vs_expert_0 = report['pairwiseBreakEven']['expert-guard']['byRate']['zero']
    assert vs_expert_0['regime'] == 'no-break-even', vs_expert_0
    vs_expert_r = report['pairwiseBreakEven']['expert-guard']['byRate']['r']
    assert vs_expert_r['regime'] == 'loses-above-V*', vs_expert_r
    assert abs(vs_expert_r['breakEvenVolumeRoutes'] - 1750.0) < 0.02, vs_expert_r

    # 3. vs rule-selector at r=$0.50:
    #    fixed_L = $5.00 < fixed_C = $8.00 AND marg_L = $0.044 < marg_C = (150/200)*$0.08 = $0.060 -> dominates-at-all-volumes!
    vs_rs_r = report['pairwiseBreakEven']['rule-selector']['byRate']['r']
    assert vs_rs_r['regime'] == 'dominates-at-all-volumes', vs_rs_r
    assert vs_rs_r['breakEvenVolumeRoutes'] == 0.0
    print('cost_report selftest ok')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--routes')
    parser.add_argument('--phases')
    parser.add_argument('--key')
    parser.add_argument('--blind', action='append', default=[])
    parser.add_argument('--primary-learned', default='repair-boundary')
    parser.add_argument('--rate-per-minute', default='0.50')
    parser.add_argument('--volumes', default=','.join(str(v) for v in DEFAULT_VOLUMES))
    parser.add_argument('--allow-legacy-unmetered-adapter', action='store_true')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    vols = tuple(int(x.strip()) for x in args.volumes.split(',') if x.strip())
    report = generate_cost_report(
        routes=read_jsonl(args.routes) if args.routes else [],
        phases=read_jsonl(args.phases) if args.phases else [],
        key_doc=json.load(open(args.key, encoding='utf-8')) if args.key else {'routes': {}},
        blind_files=[json.load(open(p, encoding='utf-8')) for p in args.blind],
        primary_learned=args.primary_learned,
        rate_per_minute_usd=args.rate_per_minute,
        volumes=vols,
        require_measured_adapter=not args.allow_legacy_unmetered_adapter,
    )
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
