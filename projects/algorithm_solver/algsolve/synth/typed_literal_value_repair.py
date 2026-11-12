"""Value-coherent literal proposals (policy ``literal-value-v1``): a separately
versioned alternative to the bit-flip literal search in typed_literal_repair.

A proposal changes literal values, not individual bits:
- single-slot: one integer literal slot takes a value from a frozen small set
  (SMALL_VALUES) or a value one captured low-margin bit flip away;
- coherent group: every free integer literal slot holding the same value v
  takes one new value w together.
Only captured logits rank proposals: the cost of a proposal is the summed
|logit| of every bit it flips. Witness literals, target programs and expected
outputs never enter the pool. Each attempt records its origin, the values,
the number of field (slot) edits and the number of bit changes, so a nominally
equal edit limit cannot hide a wider search. Envelope and stopping rules match
literal_search: at most 8 proposals, 2 combined proposals per candidate,
4 public executions and 0.25 s.
"""
from __future__ import annotations

import copy
import itertools
import math
import time

from . import typed_codec
from .typed_correction import INVALID, validate_codes, validate_codes_detailed
from .typed_prediction_codec import BITS, OPS, rejection_details

POLICY = "literal-value-v1"
SMALL_VALUES = (-1, 0, 1, 2)


def _value(bits):
    magnitude = sum(int(b) << k for k, b in enumerate(bits[1:]))
    return -magnitude if bits[0] else magnitude


def _bits(value):
    magnitude = abs(value)
    if magnitude.bit_length() > BITS - 1:
        raise ValueError("Value outside the declared integer domain")
    return [1 if value < 0 else 0] + [(magnitude >> k) & 1 for k in range(BITS - 1)]


def _cost(logits_row, before, after):
    flips = [k for k in range(BITS) if before[k] != after[k]]
    return sum(abs(float(logits_row[k])) for k in flips), len(flips)


def literal_value_search(encoding, codes, logits, params, config, evaluate, *, deadline,
                         candidate_filter=None, captured_bits=None, frozen_slots=()):
    started = time.perf_counter()
    deadline = min(deadline, started + config['wall_seconds'])
    if not (0 <= config['pool_size'] <= 8 and 0 <= config['max_executions'] <= 4
            and 1 <= config['max_edits'] <= 2 and 0 <= config['wall_seconds'] <= .25):
        raise ValueError('Literal search exceeds the declared experiment envelope')
    result = dict(policy=POLICY, pool=[], attempts=[], edits=[], final_codes=None, graph=None,
                  executions=0, reason='no_public_passing_literal', infrastructure_failure=False)
    try:
        if len(logits) != encoding.slots or any(len(row) != BITS for row in logits):
            raise ValueError('Literal logit dimensions differ')
        if any(not math.isfinite(float(v)) for row in logits for v in row):
            raise ValueError('Nonfinite literal logits')
        frozen_slots = set(frozen_slots)
        original_bits = codes['bits'] if captured_bits is None else captured_bits
        if original_bits != [[int(v >= 0) for v in row] for row in logits]:
            raise ValueError('Literal decisions differ from captured logits')
        _, error = validate_codes(encoding, codes, params)
        if error:
            raise ValueError('Literal search requires a valid starting graph: ' + error)
        slots = [s for s, op in enumerate(codes['op']) if OPS[op] == 'int' and s not in frozen_slots]
        current = {s: _value(codes['bits'][s]) for s in slots}
        proposals = {}
        def propose(origin, assignment):
            changes = {s: _bits(v) for s, v in assignment.items() if v != current[s]}
            if not changes:
                return
            key = tuple(sorted((s, tuple(b)) for s, b in changes.items()))
            cost = bit_changes = 0
            for s, after in changes.items():
                c, n = _cost(logits[s], codes['bits'][s], after)
                cost += c; bit_changes += n
            if key not in proposals or cost < proposals[key]['cost']:
                proposals[key] = dict(origin=origin, cost=cost, bit_changes=bit_changes,
                                      changes={s: dict(before=current[s], after=_value(b)) for s, b in changes.items()},
                                      bits={s: b for s, b in changes.items()})
        for s in slots:
            margins = sorted(range(BITS), key=lambda k: (abs(float(logits[s][k])), k))[:2]
            flipped = []
            for k in margins:
                bits = list(codes['bits'][s]); bits[k] = 1 - bits[k]
                flipped.append(_value(bits))
            for value in sorted(set(SMALL_VALUES) | set(flipped)):
                propose('single_slot', {s: value})
        groups = {}
        for s in slots:
            groups.setdefault(current[s], []).append(s)
        for value, members in groups.items():
            if len(members) < 2:
                continue
            for target in sorted(set(SMALL_VALUES) - {value}):
                propose('coherent_group', {s: target for s in members})
        ranked = sorted(proposals.values(), key=lambda p: (p['cost'], sorted(p['changes'])))
        result['pool_size_before_cut'] = len(ranked)
        pool = ranked[:config['pool_size']]
        result['pool'] = [dict(origin=p['origin'], cost=p['cost'], bit_changes=p['bit_changes'],
                               field_edits=len(p['changes']),
                               changes={str(s): c for s, c in sorted(p['changes'].items())}) for p in pool]
        combos = []
        for size in range(1, config['max_edits'] + 1):
            for combo in itertools.combinations(range(len(pool)), size):
                touched = [s for i in combo for s in pool[i]['changes']]
                if len(touched) != len(set(touched)):
                    continue
                combos.append((sum(pool[i]['cost'] for i in combo), combo))
        combos.sort()
        result['proposal_order'] = [dict(cost=c, proposals=list(combo)) for c, combo in combos]
        for cost, combo in combos:
            if time.perf_counter() >= deadline:
                result['reason'] = 'literal_budget'; break
            if result['executions'] >= config['max_executions']:
                result['reason'] = 'literal_execution_budget'; break
            candidate = copy.deepcopy(codes)
            edits = []
            for i in combo:
                for s, after in pool[i]['bits'].items():
                    candidate['bits'][s] = list(after)
                    edits.append(dict(slot=s, before=pool[i]['changes'][s]['before'],
                                      after=pool[i]['changes'][s]['after'], origin=pool[i]['origin'],
                                      reason='captured model margin; no target values'))
            graph, details = validate_codes_detailed(encoding, candidate, params)
            failure = None if details is None else details['message']
            attempt = dict(edits=edits, proposals=list(combo), logit_penalty=cost,
                           field_edits=len(edits), bit_changes=sum(pool[i]['bit_changes'] for i in combo),
                           validation_failure=failure, validation_details=details, public=None, execution_seconds=0.)
            result['attempts'].append(attempt)
            if failure:
                continue
            if candidate_filter is not None:
                attempt['proposal_filter_failure'] = candidate_filter(graph)
                if attempt['proposal_filter_failure'] is not None:
                    continue
            attempt['graph_sha256'] = typed_codec.digest(graph)
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                result['reason'] = 'literal_budget'; break
            tick = time.perf_counter()
            verdict = evaluate(graph, remaining)
            attempt['execution_seconds'] = time.perf_counter() - tick
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
    result['seconds'] = time.perf_counter() - started
    return result
