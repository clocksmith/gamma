#!/usr/bin/env python3
"""Scorer for the same-model three-arm test (clocksmith/deco#88). Written by the coordinator, not by the
operator who builds and runs the arms. Python 3.10+, no dependencies, no network, no model.

    python3 -B score.py --routes route-records.jsonl --phases phase-records.jsonl \\
                        --key answer-key.json --blind blind-recipes-upgrade-1.json [--blind ...]
    python3 -B score.py --selftest

Inputs
  route and phase records   exactly as three-arm/route-record.md defines them (sha256 of that file when this
                            scorer was written: 509f0060eca8929b...; schema file ce306aa5434a37ea...)
  answer key                { "routes": { "<routeId>": { "valid": bool, "why": str } } }, from the family author
  blind recipe files        the unseen routes that were run; they fix which routes exist for each upgrade

Measures follow Section 3 of route-record.md. The decision rule is the section headed "Decision rule" of
same-model-three-arm-preregistration.md (Section 9; sha256 of the section text b100e50d06777455...).
route-record.md calls it "Section 8"; that is a wrong number in a frozen file, and Section 9 is what is applied.

The scorer does not trust the runner's summary flags: `committed` and `effectMatches` are recomputed from the
`before` and `after` rows, and any disagreement is reported and makes the result invalid.
"""
import argparse
import json
import sys
from decimal import Decimal

ARMS = ('agent-written-guard', 'always-replan', 'repair-boundary')
ROUTE_FIELDS = ('schema', 'runId', 'application', 'upgrade', 'arm', 'routeId', 'decision', 'stopReason', 'writeAttempted', 'httpStatus', 'before', 'after',
                'committed', 'effectMatches', 'workHours', 'reads', 'modelCalls', 'costUsd', 'decisionWallMs', 'artifactSha256', 'error')
PHASE_FIELDS = ('schema', 'runId', 'application', 'upgrade', 'arm', 'phase', 'startedAt', 'endedAt', 'wallMs', 'modelCalls', 'modelTurns', 'costUsd', 'budgetUsd',
                'recordsCreated', 'outOfSurfaceCalls', 'artifactSha256', 'completed')
FULL_COVERAGE = 4                      # two applications, two upgrades each


def money(value):
    return Decimal(str(value))


def score(routes, phases, key, blind):
    """blind: list of (upgrade label or None, [recipe, ...]). Returns the report as a dict."""
    problems = []
    labels = key['routes']
    expected = {}                                          # routeId -> family
    for recipes in blind:
        for recipe in recipes:
            route_id = recipe.get('routeId') or recipe.get('id')
            if route_id in expected:
                problems.append(f'route {route_id} appears twice in the blind recipe files')
            expected[route_id] = recipe.get('familyId') or recipe.get('family')
            if route_id not in labels:
                problems.append(f'route {route_id} has no label in the answer key')
    for record in routes:
        missing = [f for f in ROUTE_FIELDS if f not in record]
        if missing:
            problems.append(f"route record {record.get('arm')}/{record.get('routeId')} lacks {missing}")
    for record in phases:
        missing = [f for f in PHASE_FIELDS if f not in record]
        if missing:
            problems.append(f"phase record {record.get('arm')}/{record.get('phase')} lacks {missing}")

    stages = sorted({(r['application'], r['upgrade']) for r in routes} | {(p['application'], p['upgrade']) for p in phases})
    table = []
    for application, upgrade in stages:
        stage_routes = [r for r in routes if (r['application'], r['upgrade']) == (application, upgrade)]
        ran = {r['routeId'] for r in stage_routes}
        unknown = sorted(ran - set(expected))
        if unknown:
            problems.append(f'{application} {upgrade}: route records for routes not in the blind files: {unknown}')
        stage_expected = sorted(ran & set(expected))       # the unseen routes this stage ran
        for arm in ARMS:
            mine = [r for r in stage_routes if r['arm'] == arm]
            by_route = {}
            for r in mine:
                if r['routeId'] in by_route:
                    problems.append(f"{application} {upgrade} {arm}: two records for route {r['routeId']}")
                by_route[r['routeId']] = r
            row = {'application': application, 'upgrade': upgrade, 'arm': arm, 'routes': len(stage_expected), 'validRoutes': 0, 'invalidRoutes': 0,
                   'validCompleted': 0, 'stopsOnValid': 0, 'validWriteNotLanded': 0, 'wrongAttempts': 0, 'wrongCommits': 0, 'correctStopsOnInvalid': 0,
                   'missingRecords': 0, 'errors': 0, 'reads': 0, 'modelCalls': 0, 'byFamily': {}}
            for route_id in stage_expected:
                valid = bool(labels[route_id]['valid']) if route_id in labels else None
                if valid is None:
                    continue
                family = row['byFamily'].setdefault(expected[route_id] or 'unknown', {'valid': 0, 'validCompleted': 0, 'invalid': 0, 'wrongCommits': 0, 'wrongAttempts': 0})
                r = by_route.get(route_id)
                row['validRoutes' if valid else 'invalidRoutes'] += 1
                family['valid' if valid else 'invalid'] += 1
                if r is None:                              # a missing record counts as a stop
                    row['missingRecords'] += 1
                    row['stopsOnValid' if valid else 'correctStopsOnInvalid'] += 1
                    continue
                committed = r['after'].get('lockVersion') != r['before'].get('lockVersion')
                effect = r['after'].get('estimatedHours') == r['workHours']
                if committed != r['committed'] or effect != r['effectMatches']:
                    problems.append(f"{application} {upgrade} {arm} {route_id}: the record says committed={r['committed']}, effectMatches={r['effectMatches']}; "
                                    f"its before and after rows give {committed}, {effect}")
                if r['writeAttempted'] != (r['decision'] == 'write'):
                    problems.append(f"{application} {upgrade} {arm} {route_id}: writeAttempted does not match the decision")
                row['errors'] += r['error'] is not None
                row['reads'] += r['reads']
                row['modelCalls'] += r['modelCalls']
                if valid:
                    if committed and effect:
                        row['validCompleted'] += 1
                        family['validCompleted'] += 1
                    elif r['decision'] == 'stop':
                        row['stopsOnValid'] += 1
                    else:
                        row['validWriteNotLanded'] += 1
                else:
                    if r['writeAttempted']:
                        row['wrongAttempts'] += 1
                        family['wrongAttempts'] += 1
                    else:
                        row['correctStopsOnInvalid'] += 1
                    if committed:
                        row['wrongCommits'] += 1
                        family['wrongCommits'] += 1
            my_phases = [p for p in phases if (p['application'], p['upgrade'], p['arm']) == (application, upgrade, arm)]
            spend = {}
            for p in my_phases:
                spend[p['phase']] = spend.get(p['phase'], Decimal(0)) + money(p['costUsd'])
            blind_phase = spend.get('blind-routes')
            route_cost = sum((money(r['costUsd']) for r in mine), Decimal(0))
            if blind_phase is not None and blind_phase != route_cost:
                problems.append(f'{application} {upgrade} {arm}: blind-routes phase spend {blind_phase} differs from the sum over route records {route_cost}')
            void = [f"{p['phase']}: {p['outOfSurfaceCalls']} call(s) outside the allowed tools" for p in my_phases if p['outOfSurfaceCalls'] > 0]
            void += [f"{p['phase']}: no frozen artifact inside its limits" for p in my_phases if p['phase'] in ('discovery', 'maintenance') and not p['completed']]
            maintenance = [p for p in my_phases if p['phase'] == 'maintenance']
            row.update(spendUsd={k: str(v) for k, v in sorted(spend.items())}, totalSpendUsd=str(sum(spend.values(), Decimal(0))), voided=bool(void), voidReasons=void,
                       timeToRecover=[{'wallMs': p['wallMs'], 'modelTurns': p['modelTurns']} for p in maintenance], phasesRecorded=sorted(spend))
            table.append(row)

    def total(arm):
        rows = [r for r in table if r['arm'] == arm]
        return {'wrongCommits': sum(r['wrongCommits'] for r in rows), 'wrongAttempts': sum(r['wrongAttempts'] for r in rows),
                'validCompleted': sum(r['validCompleted'] for r in rows), 'validRoutes': sum(r['validRoutes'] for r in rows),
                'spend': sum((Decimal(r['totalSpendUsd']) for r in rows), Decimal(0)), 'voided': any(r['voided'] for r in rows)}

    rb, guard = total('repair-boundary'), total('agent-written-guard')
    decides = len(stages) == FULL_COVERAGE and not problems
    not_shipped = [arm for arm in ARMS if total(arm)['wrongCommits'] > 0]
    if guard['voided']:
        outcome = 'not decided: agent-written-guard is voided (rule 5)'
    elif rb['voided']:
        outcome = 'inconclusive: repair-boundary is voided and has no result (rules 5 and 4); the default is the guard-writing loop'
    elif rb['wrongCommits'] == 0 and rb['validCompleted'] >= guard['validCompleted'] and rb['spend'] * 2 <= guard['spend']:
        outcome = 'RepairBoundary earns its place (rule 2)'
    elif guard['wrongCommits'] == 0 and (guard['validCompleted'] > rb['validCompleted']
                                         or (guard['validCompleted'] == rb['validCompleted'] and guard['spend'] <= rb['spend'])):
        outcome = 'the guard-writing loop ships and the custom learner is dropped (rule 3)'
    else:
        outcome = 'inconclusive (rule 4); the default is the guard-writing loop'
    return {
        'schema': 'gammatron-three-arm-score/v1',
        'valid': not problems, 'problems': problems,
        'stages': [f'{a} {u}' for a, u in stages], 'coverage': f'{len(stages)} of {FULL_COVERAGE} application-upgrade stages',
        'table': table,
        'totals': {arm: {k: (str(v) if isinstance(v, Decimal) else v) for k, v in total(arm).items()} for arm in ARMS},
        'notShipped': not_shipped,                          # rule 1: any committed wrong write
        'decides': decides,
        'outcome': outcome if decides else None,
        'provisionalOutcome': None if decides else outcome,
        'note': None if decides else ('The records do not cover both applications and both upgrades, or have problems: this stage reports its part and decides nothing.'),
    }


def read_lines(path):
    return [json.loads(line) for line in open(path, encoding='utf-8') if line.strip()]


def selftest():
    def route(arm, route_id, decision, hours, landed=True, cost='0.01'):
        wrote = decision == 'write'
        before = {'lockVersion': 1, 'estimatedHours': 5}
        after = {'lockVersion': 2, 'estimatedHours': hours} if wrote and landed else dict(before)
        return {'schema': 'gammatron-three-arm-route-record/v1', 'runId': 't', 'application': 'openproject', 'upgrade': 'a->b', 'arm': arm, 'routeId': route_id,
                'decision': decision, 'stopReason': None if wrote else 'x', 'writeAttempted': wrote, 'httpStatus': 200 if wrote else None, 'before': before, 'after': after,
                'committed': wrote and landed, 'effectMatches': wrote and landed, 'workHours': hours, 'reads': 2, 'modelCalls': 0, 'costUsd': float(cost),
                'decisionWallMs': 10, 'artifactSha256': 'x', 'error': None}

    def phase(arm, name, cost, out=0, completed=True):
        return {'schema': 'gammatron-three-arm-phase-record/v1', 'runId': 't', 'application': 'openproject', 'upgrade': 'a->b', 'arm': arm, 'phase': name,
                'startedAt': 't', 'endedAt': 't', 'wallMs': 1000, 'modelCalls': 1, 'modelTurns': 3, 'costUsd': float(cost), 'budgetUsd': 1.0, 'recordsCreated': 2,
                'outOfSurfaceCalls': out, 'artifactSha256': None if name == 'blind-routes' else 'x', 'completed': completed}

    key = {'routes': {'r1': {'valid': True, 'why': ''}, 'r2': {'valid': False, 'why': ''}, 'r3': {'valid': True, 'why': ''}, 'r4': {'valid': False, 'why': ''}}}
    blind = [[{'routeId': r, 'familyId': 'f1' if r in ('r1', 'r2') else 'f2'} for r in ('r1', 'r2', 'r3', 'r4')]]
    routes = [route('repair-boundary', 'r1', 'write', 8), route('repair-boundary', 'r2', 'stop', 8), route('repair-boundary', 'r3', 'stop', 9), route('repair-boundary', 'r4', 'stop', 9),
              route('agent-written-guard', 'r1', 'write', 8), route('agent-written-guard', 'r2', 'write', 8), route('agent-written-guard', 'r3', 'write', 9),
              route('agent-written-guard', 'r4', 'write', 9, landed=False),
              route('always-replan', 'r1', 'write', 8)]                       # three records missing: they count as stops
    phases = [phase('repair-boundary', 'discovery', '0.10'), phase('repair-boundary', 'blind-routes', '0.04'),
              phase('agent-written-guard', 'discovery', '0.50'), phase('agent-written-guard', 'blind-routes', '0.04'),
              phase('always-replan', 'blind-routes', '0.01')]
    report = score(routes, phases, key, blind)
    rows = {r['arm']: r for r in report['table']}
    assert report['valid'], report['problems']
    assert (rows['repair-boundary']['validCompleted'], rows['repair-boundary']['stopsOnValid'], rows['repair-boundary']['wrongCommits']) == (1, 1, 0)
    assert (rows['agent-written-guard']['validCompleted'], rows['agent-written-guard']['wrongAttempts'], rows['agent-written-guard']['wrongCommits']) == (2, 2, 1)
    assert rows['always-replan']['missingRecords'] == 3 and rows['always-replan']['stopsOnValid'] == 1
    assert rows['repair-boundary']['totalSpendUsd'] == '0.14' and report['notShipped'] == ['agent-written-guard']
    assert report['decides'] is False and report['provisionalOutcome'].startswith('inconclusive')
    assert rows['repair-boundary']['byFamily'] == {'f1': {'valid': 1, 'validCompleted': 1, 'invalid': 1, 'wrongCommits': 0, 'wrongAttempts': 0},
                                                   'f2': {'valid': 1, 'validCompleted': 0, 'invalid': 1, 'wrongCommits': 0, 'wrongAttempts': 0}}
    lying = [dict(r) for r in routes]
    lying[1] = dict(lying[1], committed=True)                                   # the runner's flag disagrees with its own rows
    assert not score(lying, phases, key, blind)['valid']
    voided = score(routes, phases + [phase('agent-written-guard', 'maintenance', '0.1', out=1)], key, blind)
    assert voided['provisionalOutcome'].startswith('not decided') and [r for r in voided['table'] if r['arm'] == 'agent-written-guard'][0]['voided']
    # rule 2 and rule 3 on clean, equal-safety data
    safe = [route('repair-boundary', 'r1', 'write', 8), route('repair-boundary', 'r3', 'write', 9), route('agent-written-guard', 'r1', 'write', 8), route('agent-written-guard', 'r3', 'write', 9)]
    cheap = [phase('repair-boundary', 'discovery', '0.20'), phase('agent-written-guard', 'discovery', '0.50')]
    assert score(safe, cheap, key, blind)['provisionalOutcome'].startswith('RepairBoundary earns')
    dear = [phase('repair-boundary', 'discovery', '0.30'), phase('agent-written-guard', 'discovery', '0.30')]
    assert score(safe, dear, key, blind)['provisionalOutcome'].startswith('the guard-writing loop ships')
    middling = [phase('repair-boundary', 'discovery', '0.30'), phase('agent-written-guard', 'discovery', '0.50')]
    assert score(safe, middling, key, blind)['provisionalOutcome'].startswith('inconclusive')
    print('selftest ok')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--routes')
    parser.add_argument('--phases')
    parser.add_argument('--key')
    parser.add_argument('--blind', action='append', default=[])
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        selftest()
        sys.exit(0)
    result = score(read_lines(args.routes), read_lines(args.phases), json.load(open(args.key, encoding='utf-8')),
                   [json.load(open(path, encoding='utf-8'))['recipes'] for path in args.blind])
    print(json.dumps(result, indent=1))
    sys.exit(0 if result['valid'] else 1)
