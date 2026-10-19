"""Matched route execution and independent development reporting, without training."""
from __future__ import annotations

import ast
import copy
import time

import numpy as np

from .. import validate, values
from . import typed_codec
from .typed_correction import correct, validate_codes


def interface(pair):
    """Compare declared public signatures, never teacher target types or outputs."""
    tree = values._stub_tree(pair['input']['starter_code'])
    methods = [fn for cls in tree.body if isinstance(cls, ast.ClassDef) and cls.name == 'Solution'
               for fn in cls.body if isinstance(fn, ast.FunctionDef) and fn.name != '__init__']
    if len(methods) != 1:
        return None
    fn = methods[0]
    def annotation(node):
        if node is None:
            return None
        return ast.unparse(node).replace('typing.', '').replace(' ', '').lower()
    inputs = tuple(annotation(arg.annotation) for arg in fn.args.args if arg.arg != 'self')
    output = annotation(fn.returns)
    if not output or any(t is None for t in inputs):
        return None
    return inputs, output


def nearest_graph(request, fit, similarities, encoding):
    if any(p['learning_split'] != 'development_fit' for p in fit):
        raise ValueError('Baseline library contains a non-fit target')
    if len(similarities) != len(fit) or not np.isfinite(similarities).all():
        raise ValueError('Invalid baseline similarities')
    key = interface(request)
    if key is None:
        return None, None, 'unsupported_interface'
    candidates = sorted(range(len(fit)), key=lambda i: (-float(similarities[i]), fit[i]['graph_sha256']))
    for i in candidates:
        pair = fit[i]
        if interface(pair) == key:
            # Encoded references use positional input indices. Decoding only
            # alpha-renames ports/locals; literals and algorithm remain unchanged.
            codes = encoding.encode(pair['target']['program'])
            params = [p[0] for p in request['input']['params']]
            graph = encoding.decode(codes, params)
            return graph, pair['graph_sha256'], None
    return None, None, 'no_compatible_training_graph'


def run_route(route, problem, raw, logits, encoding, identity, shared_seconds,
              correction_config, budget, *, baseline_graph=None, baseline_hash=None,
              baseline_reason=None, baseline_seconds=0., baseline_construction_seconds=0.,
              judge=validate.judge_problem):
    started = time.perf_counter()
    inherited = (shared_seconds if route != 'nearest_training_graph' else
                 baseline_seconds+baseline_construction_seconds)
    result = {'route': route, 'raw_codes': copy.deepcopy(raw) if route != 'nearest_training_graph' else None,
              'raw_sha256': typed_codec.digest(raw) if route != 'nearest_training_graph' else None,
              'final_graph': None, 'graph_sha256': None, 'source': None,
              'validation_failures': [], 'correction': None, 'structurally_valid': False,
              'decision': 'abstain', 'reason': None, 'public': None, 'infrastructure_failure': False,
              'baseline_graph_sha256': baseline_hash,
              'timing': {'shared_inference_seconds': (shared_seconds if route != 'nearest_training_graph' else baseline_seconds),
                         'construction_seconds': baseline_construction_seconds if route == 'nearest_training_graph' else 0.,
                         'correction_seconds': 0., 'assembly_seconds': 0., 'execution_seconds': 0.}}
    params = [p[0] for p in problem.params]
    phase = time.perf_counter()
    if route == 'raw':
        graph, failure = validate_codes(encoding, raw, params)
        if failure:
            result['validation_failures'].append(failure)
        result['reason'] = 'invalid_prediction' if graph is None else None
        result['timing']['construction_seconds'] = time.perf_counter()-phase
    elif route == 'constrained':
        repair = correct(encoding, raw, logits, params, correction_config,
                         deadline=started+max(0., budget-inherited))
        graph = repair.pop('graph')
        result['correction'] = repair
        result['timing']['correction_seconds'] = time.perf_counter()-phase
        result['validation_failures'] = [v for v in [repair['raw_validation_failure'],
            *[a['validation_failure'] for a in repair['attempts']]] if v is not None]
        result['reason'] = repair['reason'] if graph is None else None
    elif route == 'nearest_training_graph':
        graph = baseline_graph
        result['reason'] = baseline_reason
    else:
        raise ValueError('Unknown comparison route')
    if graph is not None:
        phase = time.perf_counter()
        # Baseline and repaired programs receive the same strict IR validation.
        target = typed_codec.encode(graph, identity)
        result.update(structurally_valid=True, final_graph=graph, graph_sha256=typed_codec.digest(target))
        result['timing']['construction_seconds'] += time.perf_counter()-phase
        phase = time.perf_counter()
        source = typed_codec.render(target, identity, method=problem.entry['method'], params=params)
        result['source'] = source
        result['source_sha256'] = typed_codec.digest(source)
        result['timing']['assembly_seconds'] = time.perf_counter()-phase
        remaining = budget-inherited-(time.perf_counter()-started)
        if remaining > 0:
            phase = time.perf_counter()
            verdict = judge(problem, source, problem.public_tests, wall_seconds=remaining)
            result['timing']['execution_seconds'] = time.perf_counter()-phase
            result['public'] = verdict.to_dict()
            result['infrastructure_failure'] = verdict.reason in ('sandbox_error', 'checker_error')
            result['decision'] = 'answered' if verdict.passed else 'abstain'
            result['reason'] = 'public_passed' if verdict.passed else 'public_failure'
        else:
            result['reason'] = 'decision_budget'
    result['timing']['total_seconds'] = inherited+time.perf_counter()-started
    if result['timing']['total_seconds'] > budget:
        result.update(decision='abstain', reason='decision_budget')
    return result


def score_fixed(result, problem, independent_tests, *, judge=validate.judge_problem):
    """Independent tests are supplied only after every route decision is written."""
    result = copy.deepcopy(result)
    result.update(independent=None, independently_correct=None, accepted_correct=False,
                  wrong_acceptance=False, independent_scoring_seconds=0.)
    if result['source'] is not None:
        started = time.perf_counter()
        verdict = judge(problem, result['source'], independent_tests)
        unscorable = verdict.reason in ('sandbox_error', 'checker_error', 'no_tests')
        result.update(independent=verdict.to_dict(), independently_correct=None if unscorable else verdict.passed,
                      independent_scoring_seconds=time.perf_counter()-started,
                      accepted_correct=result['decision']=='answered' and not unscorable and verdict.passed,
                      wrong_acceptance=result['decision']=='answered' and not unscorable and not verdict.passed)
        result['infrastructure_failure'] |= unscorable
    return result


def correction_outcome(raw, fixed):
    if raw['infrastructure_failure'] or fixed['infrastructure_failure']:
        return 'unknown'
    if raw['accepted_correct'] and not fixed['accepted_correct']:
        return 'harmful'
    if fixed['wrong_acceptance'] and not raw['wrong_acceptance']:
        return 'harmful'
    if fixed['accepted_correct'] and not raw['accepted_correct']:
        return 'useful'
    if (raw['decision'], raw['accepted_correct'], raw['structurally_valid'], raw['graph_sha256']) == (
            fixed['decision'], fixed['accepted_correct'], fixed['structurally_valid'], fixed['graph_sha256']):
        return 'unchanged'
    return 'neutral'


def summarize(rows, rule):
    summary = {'splits': {}, 'corrections': {}, 'development_qualified': False, 'selection_checks': {}}
    for split in ('development_fit', 'development_audit'):
        cases = [r for r in rows if r['split'] == split]
        summary['splits'][split] = {}
        outcomes = [correction_outcome(r['routes']['raw'], r['routes']['constrained']) for r in cases]
        summary['corrections'][split] = {key: outcomes.count(key) for key in ('useful','harmful','unchanged','neutral','unknown')}
        for route in ('raw','constrained','nearest_training_graph'):
            values_ = [r['routes'][route] for r in cases]
            times = [r['timing']['total_seconds'] for r in values_]
            summary['splits'][split][route] = {
                'cases': len(values_), 'valid': sum(r['structurally_valid'] for r in values_),
                'accepted_correct': sum(r['accepted_correct'] for r in values_),
                'independently_correct': sum(r['independently_correct'] is True for r in values_),
                'wrong_acceptances': sum(r['wrong_acceptance'] for r in values_),
                'abstentions': sum(r['decision']=='abstain' for r in values_),
                'infrastructure_failures': sum(r['infrastructure_failure'] for r in values_),
                'latency': {name: float(np.percentile(times, q)) if times else None
                            for name,q in [('p50',50),('p95',95),('maximum',100)]}}
    audit = summary['splits']['development_audit']; fit = summary['splits']['development_fit']
    raw, fixed = audit['raw'], audit['constrained']
    checks = summary['selection_checks']
    checks['nonempty_partitions'] = bool(raw['cases'] and fit['raw']['cases'])
    checks['correctness_gain'] = fixed['accepted_correct']-raw['accepted_correct'] >= rule['minimum_additional_correct']
    checks['no_harm'] = all(v['harmful'] <= rule['maximum_harmful_corrections'] for v in summary['corrections'].values())
    checks['wrong_acceptances'] = all(s['constrained']['wrong_acceptances'] <= rule['maximum_wrong_acceptances'] for s in summary['splits'].values())
    checks['validity'] = fixed['valid'] >= raw['valid']
    checks['abstention'] = fixed['abstentions'] <= raw['abstentions']
    checks['latency'] = (fixed['latency']['p95'] is not None and
        fixed['latency']['p95'] <= rule['maximum_complete_p95_seconds'] and
        fixed['latency']['p95']-raw['latency']['p95'] <= rule['maximum_p95_increase_seconds'])
    checks['fit_preserved'] = all(not r['routes']['raw']['accepted_correct'] or r['routes']['constrained']['accepted_correct']
                                  for r in rows if r['split']=='development_fit')
    checks['infrastructure'] = not any(r['infrastructure_failure'] for c in rows for r in c['routes'].values())
    summary['development_qualified'] = all(checks.values())
    summary['disposition'] = 'development_qualified' if summary['development_qualified'] else 'rejected_or_incomplete; protected_scoring_closed'
    return summary


def report(summary):
    lines = ['# Matched typed-composer development comparison', '',
             'Candidate: `' + summary['candidate_sha256'] + '`.', '',
             'Disposition: **' + summary['disposition'] + '**.', '',
             '| Partition | Route | Cases | Valid | Accepted correct | Wrong accepted | Abstained | Total p50 / p95 (s) |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for split,routes in summary['splits'].items():
        for route,r in routes.items():
            latency = r['latency']
            times = f"{latency['p50']:.4f} / {latency['p95']:.4f}" if latency['p50'] is not None else 'unmeasured'
            lines.append(f"| {split} | {route} | {r['cases']} | {r['valid']} | {r['accepted_correct']} | "
                         f"{r['wrong_acceptances']} | {r['abstentions']} | {times} |")
    lines.extend(['', 'Correction outcomes (useful / harmful / unchanged / neutral / unknown):', ''])
    for split,counts in summary['corrections'].items():
        lines.append('- '+split+': '+' / '.join(str(counts[k]) for k in ('useful','harmful','unchanged','neutral','unknown')))
    lines.extend(['', 'Selection checks:', ''])
    lines.extend('- '+key+': '+('pass' if passed else 'fail') for key,passed in summary['selection_checks'].items())
    lines.extend(['', 'Reproduce on the qualified Linux host with the sealed dependencies and original assets:', '',
                  '```sh', 'PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.synth.compare_typed --name NEW-UNUSED-RUN',
                  '```', '', 'The runner refuses changed checkpoints or codecs. `candidate.json` pins the complete source, dependency, '
                  'data and configuration identity. `captures.jsonl` retains raw predictions and logits. `decisions.jsonl` '
                  'fixes every route response before independent scoring; `scores.jsonl` adds separate execution verdicts. '
                  '`summary.json` retains artifact hashes and phase setup costs. Each completed route score is retained '
                  'under `scoring/`. Resume an interrupted scoring stage with the same `--name` and `--resume-scoring`; '
                  'changed candidates, decisions or scoring identities are rejected.', '',
                  'No protected cases or fresh 2b variants were scored. This report does not authorize the autonomous loop.'])
    return '\n'.join(lines)+'\n'
