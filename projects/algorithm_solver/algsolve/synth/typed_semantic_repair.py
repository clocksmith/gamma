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
from .typed_correction import INVALID, validate_codes
from .typed_literal_repair import literal_search
from .typed_prediction_codec import OPS


def semantic_search(encoding, codes, raw_codes, logits, params, config, evaluate, *, deadline, literal_filter=None):
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
            graph, failure = validate_codes(encoding, candidate, params)
            attempt = dict(edits=edits, logit_penalty=penalty, validation_failure=failure,
                           public=None, execution_seconds=0.)
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
        if (result['graph'] is None and not result['infrastructure_failure']
                and time.perf_counter() < deadline and result['executions'] < config['max_executions']):
            remaining_config = {**config, 'max_executions': config['max_executions']-result['executions']}
            literal = literal_search(encoding, codes, logits['bits'], params, remaining_config,
                                     evaluate, deadline=deadline, candidate_filter=literal_filter)
            result['literal_repair'] = {k:v for k,v in literal.items() if k not in ('graph','final_codes')}
            result['attempts'].extend(literal['attempts'])
            result['executions'] += literal['executions']
            for k in ['reason','infrastructure_failure','graph','final_codes','edits']:
                result[k] = literal[k]
    except INVALID as error:
        result.update(reason='invalid_semantic_capture', capture_failure=str(error))
    result['seconds'] = time.perf_counter()-started
    return result


def run_semantic_route(control, problem, logits, encoding, identity, config, budget,
                       *, judge=validate.judge_problem, literal_filter=None):
    started = time.perf_counter()
    result = copy.deepcopy(control)
    result.update(route='semantic_constrained', semantic_repair=None)
    def finish():
        elapsed = time.perf_counter()-started
        result['timing']['semantic_seconds'] = elapsed
        result['timing']['total_seconds'] = control['timing']['total_seconds']+elapsed
        if (result['timing']['total_seconds'] > budget or
                (result['semantic_repair'] is not None and elapsed > config['wall_seconds'])):
            result.update(decision='abstain', reason='semantic_budget')
        return result
    if (control['decision'] == 'answered' or not control['structurally_valid']
            or control['infrastructure_failure'] or control['reason'] != 'public_failure'
            or not problem.public_tests):
        return finish()
    remaining = budget-control['timing']['total_seconds']
    if remaining <= 0:
        return finish()
    def render(graph):
        return typed_codec.render(typed_codec.encode(graph, identity), identity,
                                  method=problem.entry['method'], params=[p[0] for p in problem.params])
    def evaluate(graph, seconds):
        return judge(problem, render(graph), problem.public_tests, wall_seconds=seconds).to_dict()
    repair = semantic_search(encoding, control['correction']['final_codes'], control['raw_codes'],
                             logits, [p[0] for p in problem.params], config, evaluate,
                             deadline=started+remaining, literal_filter=literal_filter)
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
