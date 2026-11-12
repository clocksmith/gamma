"""Opt-in bounded literal repair using captured logits and public checks only.

No target programs, expected literal values or independent tests enter search.
The finite proposal order is fixed before executing any candidate.
"""
from __future__ import annotations

import copy
import itertools
import math
import time

from .. import validate
from . import typed_codec
from .typed_correction import INVALID, validate_codes, validate_codes_detailed
from .typed_prediction_codec import BITS, OPS, rejection_details


def literal_search(encoding, codes, logits, params, config, evaluate, *, deadline, candidate_filter=None, captured_bits=None, frozen_slots=()):
    started = time.perf_counter()
    deadline = min(deadline, started + config['wall_seconds'])
    if not (0 <= config['pool_size'] <= 8 and 0 <= config['max_executions'] <= 4
            and 1 <= config['max_edits'] <= 2 and 0 <= config['wall_seconds'] <= .25):
        raise ValueError('Literal search exceeds the declared experiment envelope')
    result = dict(pool=[], attempts=[], edits=[], final_codes=None, graph=None,
                  executions=0, reason='no_public_passing_literal', infrastructure_failure=False)
    try:
        if len(logits) != encoding.slots or any(len(row) != BITS for row in logits):
            raise ValueError('Literal logit dimensions differ')
        if any(not math.isfinite(float(v)) for row in logits for v in row):
            raise ValueError('Nonfinite literal logits')
        frozen_slots = set(frozen_slots)
        if any(type(s) is not int or not 0 <= s < encoding.slots for s in frozen_slots):
            raise ValueError('Invalid frozen literal slot')
        original_bits = codes['bits'] if captured_bits is None else captured_bits
        if original_bits != [[int(v >= 0) for v in row] for row in logits]:
            raise ValueError('Literal decisions differ from captured logits')
        if any(row != original_bits[i] and i not in frozen_slots for i,row in enumerate(codes['bits'])):
            raise ValueError('Unbound literal differs from captured logits')
        if any(OPS[codes['op'][i]] not in ('int','bool') for i in frozen_slots):
            raise ValueError('Frozen slot is not a literal')
        graph, error = validate_codes(encoding, codes, params)
        if error:
            raise ValueError('Literal search requires a valid starting graph: ' + error)
        pool = []
        for slot, operation in enumerate(codes['op']):
            if slot in frozen_slots:
                continue
            label = OPS[operation]
            # Boolean decoding only permits a zero sign and magnitude0/1.
            bits = range(BITS) if label == 'int' else [1] if label == 'bool' else []
            for bit in bits:
                pool.append((abs(float(logits[slot][bit])), slot, bit))
        result['pool_size_before_cut'] = len(pool)
        pool = sorted(pool)[:config['pool_size']]
        result['pool'] = [dict(penalty=p, slot=s, bit=b, logit=logits[s][b]) for p,s,b in pool]
        proposals = []
        for size in range(1, config['max_edits']+1):
            for combo in itertools.combinations(pool, size):
                coordinates = tuple(sorted((s,b) for _,s,b in combo))
                proposals.append((sum(p for p,_,_ in combo), coordinates))
        proposals = sorted(proposals)
        # Diagnostic only: the complete proposal order, fixed before any execution.
        result['proposal_order'] = [dict(penalty=penalty, coordinates=[list(c) for c in coordinates])
                                    for penalty, coordinates in proposals]
        for penalty, coordinates in proposals:
            if time.perf_counter() >= deadline:
                result['reason'] = 'literal_budget'; break
            if result['executions'] >= config['max_executions']:
                result['reason'] = 'literal_execution_budget'; break
            candidate = copy.deepcopy(codes)
            edits = []
            for slot, bit in coordinates:
                before = codes['bits'][slot][bit]
                candidate['bits'][slot][bit] = 1-before
                edits.append(dict(slot=slot, bit=bit, before=before, after=1-before,
                                  logit=logits[slot][bit], reason='captured model margin; no target values'))
            graph, details = validate_codes_detailed(encoding, candidate, params)
            failure = None if details is None else details['message']
            attempt = dict(edits=edits, logit_penalty=penalty, validation_failure=failure,
                           validation_details=details, public=None, execution_seconds=0.)
            result['attempts'].append(attempt)
            if failure:
                continue
            if candidate_filter is not None:
                attempt['proposal_filter_failure'] = candidate_filter(graph)
                if attempt['proposal_filter_failure'] is not None:
                    continue
            attempt['graph_sha256'] = typed_codec.digest(graph)
            remaining = deadline-time.perf_counter()
            if remaining <= 0:
                result['reason'] = 'literal_budget'; break
            tick = time.perf_counter()
            verdict = evaluate(graph, remaining)
            attempt['execution_seconds'] = time.perf_counter()-tick
            attempt['public'] = verdict
            result['executions'] += 1
            if verdict['reason'] in ('sandbox_error', 'checker_error', 'no_tests'):
                result.update(reason='literal_infrastructure_failure', infrastructure_failure=True); break
            if time.perf_counter() >= deadline:
                result['reason'] = 'literal_budget'; break
            if verdict['passed']:
                result.update(final_codes=candidate, graph=graph, edits=edits, reason='literal_public_passed'); break
    except INVALID as error:
        result.update(reason='invalid_literal_capture', capture_failure=str(error),
                      capture_failure_details=rejection_details(error))
    result['seconds'] = time.perf_counter()-started
    return result


def _skip_reason(control, problem):
    """Why repair does not run for this control (None when it runs); same conditions as before."""
    if control['decision'] == 'answered':
        return 'control_answered'
    if not control['structurally_valid']:
        return 'control_invalid'
    if control['infrastructure_failure']:
        return 'control_infrastructure_failure'
    if control['reason'] != 'public_failure':
        return 'control_' + str(control['reason'])
    if not problem.public_tests:
        return 'no_public_tests'
    return None


def run_literal_route(control, problem, bit_logits, encoding, identity, config, budget,
                      *, judge=validate.judge_problem):
    """Share the measured control prefix; charge all additional repair work."""
    started = time.perf_counter()
    result = copy.deepcopy(control)
    result['route'] = 'literal_constrained'
    result['literal_repair'] = None
    result['timing']['literal_seconds'] = 0.
    result['literal_stage'] = {'skipped': None, 'budget_override': None}
    def finish():
        result['timing']['literal_seconds'] = time.perf_counter()-started
        result['timing']['total_seconds'] = control['timing']['total_seconds'] + result['timing']['literal_seconds']
        over_total = result['timing']['total_seconds'] > budget
        over_repair = result['literal_repair'] is not None and result['timing']['literal_seconds'] > config['wall_seconds']
        if over_total or over_repair:
            result['literal_stage']['budget_override'] = 'total_budget' if over_total else 'repair_wall'
            result.update(decision='abstain', reason='literal_budget')
        return result
    skip = _skip_reason(control, problem)
    if skip:
        result['literal_stage']['skipped'] = skip
        return finish()
    remaining = budget-control['timing']['total_seconds']
    if remaining <= 0:
        result['literal_stage']['skipped'] = 'no_remaining_budget'
        return finish()
    def evaluate(graph, seconds):
        target = typed_codec.encode(graph, identity)
        code = typed_codec.render(target, identity, method=problem.entry['method'],
                                  params=[p[0] for p in problem.params])
        return judge(problem, code, problem.public_tests, wall_seconds=seconds).to_dict()
    repair = literal_search(encoding, control['correction']['final_codes'], bit_logits,
                            [p[0] for p in problem.params], config, evaluate,
                            deadline=started+remaining)
    graph = repair.pop('graph')
    result['literal_repair'] = repair
    result['infrastructure_failure'] |= repair['infrastructure_failure']
    if graph is not None:
        target = typed_codec.encode(graph, identity)
        source = typed_codec.render(target, identity, method=problem.entry['method'],
                                    params=[p[0] for p in problem.params])
        result.update(final_graph=graph, graph_sha256=typed_codec.digest(target), source=source,
                      source_sha256=typed_codec.digest(source), public=repair['attempts'][-1]['public'],
                      decision='answered', reason='literal_public_passed')
    else:
        result['reason'] = repair['reason']
    return finish()
