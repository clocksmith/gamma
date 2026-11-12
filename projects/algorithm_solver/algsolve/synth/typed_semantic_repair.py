"""Opt-in recipe and literal alternatives under one public-execution budget.

Only frozen model logits order proposals. Typed validation rejects incompatible
ports; independent tests and target graphs never enter this module.
"""
from __future__ import annotations

import copy
import math
import time

from .. import validate
from . import typed_codec
from .typed_correction import INVALID, validate_codes, validate_codes_detailed
from .typed_literal_repair import _skip_reason, literal_search
from .typed_prediction_codec import OPS, rejection_details


def semantic_search(encoding, codes, raw_codes, logits, params, config, evaluate, *, deadline, literal_filter=None,
                    literal_policy=None):
    literal_policy = literal_policy or literal_search
    started = time.perf_counter()
    deadline = min(deadline, started + config['wall_seconds'])
    if not (0 <= config['pool_size'] <= 8 and 0 <= config['max_executions'] <= 4
            and 1 <= config['max_edits'] <= 2 and 0 <= config['wall_seconds'] <= .25):
        raise ValueError('Semantic search exceeds the declared experiment envelope')
    result = dict(pool=[], attempts=[], edits=[], final_codes=None, graph=None,
                  executions=0, reason='no_public_passing_semantic', infrastructure_failure=False,
                  literal_repair=None)
    try:
        op_logits = logits['op']
        if len(op_logits) != encoding.slots or any(len(row) != len(OPS) for row in op_logits):
            raise ValueError('Operation logit dimensions differ')
        if any(not math.isfinite(float(v)) for row in op_logits for v in row):
            raise ValueError('Nonfinite operation logits')
        if raw_codes['op'] != [max(range(len(row)), key=row.__getitem__) for row in op_logits]:
            raise ValueError('Raw operation decisions differ from captured logits')
        _, error = validate_codes(encoding, codes, params)
        if error:
            raise ValueError('Semantic search requires valid starting graph: ' + error)
        recipes = [i for i, name in enumerate(OPS) if name.startswith('recipe:')]
        proposals = []
        for slot, before in enumerate(codes['op']):
            if before not in recipes:
                continue
            alternatives = sorted((i for i in recipes if i != before),
                                  key=lambda i: (-op_logits[slot][i], i))[:2]
            for after in alternatives:
                proposals.append((op_logits[slot][before]-op_logits[slot][after], slot, after))
        result['pool_size_before_cut'] = len(proposals)
        proposals = sorted(proposals)[:4]
        result['pool'] = [dict(penalty=p, slot=s, after=OPS[a]) for p,s,a in proposals]
        for penalty, slot, after in proposals:
            if time.perf_counter() >= deadline:
                result['reason'] = 'semantic_budget'; break
            if result['executions'] >= config['max_executions']:
                result['reason'] = 'semantic_execution_budget'; break
            candidate = copy.deepcopy(codes)
            before = candidate['op'][slot]; candidate['op'][slot] = after
            edits = [dict(slot=slot, field='op', before=OPS[before], after=OPS[after],
                          reason='captured model recipe rank; no target values')]
            graph, details = validate_codes_detailed(encoding, candidate, params)
            failure = None if details is None else details['message']
            attempt = dict(edits=edits, logit_penalty=penalty, validation_failure=failure,
                           validation_details=details, public=None, execution_seconds=0.)
            result['attempts'].append(attempt)
            if failure:
                continue
            attempt['graph_sha256'] = typed_codec.digest(graph)
            remaining = deadline-time.perf_counter()
            if remaining <= 0:
                result['reason'] = 'semantic_budget'; break
            tick = time.perf_counter(); verdict = evaluate(graph, remaining)
            attempt['execution_seconds'] = time.perf_counter()-tick
            attempt['public'] = verdict; result['executions'] += 1
            if verdict['reason'] in ('sandbox_error', 'checker_error', 'no_tests'):
                result.update(reason='semantic_infrastructure_failure', infrastructure_failure=True); break
            if time.perf_counter() >= deadline:
                result['reason'] = 'semantic_budget'; break
            if verdict['passed']:
                result.update(final_codes=candidate, graph=graph, edits=edits, reason='recipe_public_passed'); break
        # Diagnostic only: the recipe stage's own outcome, and whether literal search follows.
        result['recipe_stage_reason'] = result['reason']
        handoff = (result['graph'] is None and not result['infrastructure_failure']
                   and time.perf_counter() < deadline and result['executions'] < config['max_executions'])
        result['literal_handoff'] = 'literal_search' if handoff else (
            'recipe_passed' if result['graph'] is not None else
            'infrastructure_failure' if result['infrastructure_failure'] else
            'execution_budget' if result['executions'] >= config['max_executions'] else 'deadline')
        if handoff:
            remaining_config = {**config, 'max_executions': config['max_executions']-result['executions']}
            literal = literal_policy(encoding, codes, logits['bits'], params, remaining_config,
                                     evaluate, deadline=deadline, candidate_filter=literal_filter)
            result['literal_repair'] = {k:v for k,v in literal.items() if k not in ('graph','final_codes')}
            result['attempts'].extend(literal['attempts'])
            result['executions'] += literal['executions']
            for k in ['reason','infrastructure_failure','graph','final_codes','edits']:
                result[k] = literal[k]
    except INVALID as error:
        result.update(reason='invalid_semantic_capture', capture_failure=str(error),
                      capture_failure_details=rejection_details(error))
    result['seconds'] = time.perf_counter()-started
    return result


def run_semantic_route(control, problem, logits, encoding, identity, config, budget,
                       *, judge=validate.judge_problem, literal_filter=None, literal_policy=None):
    started = time.perf_counter()
    result = copy.deepcopy(control)
    result.update(route='semantic_constrained', semantic_repair=None)
    result['semantic_stage'] = {'skipped': None, 'budget_override': None}
    def finish():
        elapsed = time.perf_counter()-started
        result['timing']['semantic_seconds'] = elapsed
        result['timing']['total_seconds'] = control['timing']['total_seconds']+elapsed
        over_total = result['timing']['total_seconds'] > budget
        over_repair = result['semantic_repair'] is not None and elapsed > config['wall_seconds']
        if over_total or over_repair:
            result['semantic_stage']['budget_override'] = 'total_budget' if over_total else 'repair_wall'
            result.update(decision='abstain', reason='semantic_budget')
        return result
    skip = _skip_reason(control, problem)
    if skip:
        result['semantic_stage']['skipped'] = skip
        return finish()
    remaining = budget-control['timing']['total_seconds']
    if remaining <= 0:
        result['semantic_stage']['skipped'] = 'no_remaining_budget'
        return finish()
    def render(graph):
        return typed_codec.render(typed_codec.encode(graph, identity), identity,
                                  method=problem.entry['method'], params=[p[0] for p in problem.params])
    def evaluate(graph, seconds):
        return judge(problem, render(graph), problem.public_tests, wall_seconds=seconds).to_dict()
    repair = semantic_search(encoding, control['correction']['final_codes'], control['raw_codes'],
                             logits, [p[0] for p in problem.params], config, evaluate,
                             deadline=started+remaining, literal_filter=literal_filter,
                             literal_policy=literal_policy)
    graph = repair.pop('graph'); result['semantic_repair'] = repair
    result['infrastructure_failure'] |= repair['infrastructure_failure']
    if graph is not None:
        source = render(graph)
        result.update(final_graph=graph, graph_sha256=typed_codec.digest(typed_codec.encode(graph, identity)),
                      source=source, source_sha256=typed_codec.digest(source),
                      public=repair['attempts'][-1]['public'], decision='answered', reason=repair['reason'])
    else:
        result['reason'] = repair['reason']
    return finish()
