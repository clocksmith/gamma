"""Opt-in proposal families tested one at a time after literal repair:

- ``operation``: pure-operation substitution. For each active pure-operation
  slot, the two best alternative pure operations under the captured op logits.
- ``binding``: same-type binding rewiring. For each reference slot, the two
  best alternative bindings under the captured binding logits; combining two
  covers operand-order and effect-order swaps between references.

Each proposal changes a declared field value (op or binding); pointer
structure is never edited, and every candidate passes the full decoder
(scope, types, ports) before execution. Proposals are ranked by captured-logit
penalty and searched exactly like the literal stage: at most ``pool_size``
proposals, combinations of up to ``max_edits``, the shared execution budget
and wall time. Only captured logits order proposals; no target program or
expected value enters.
"""
from __future__ import annotations

import copy
import itertools
import math
import time

from . import typed_codec
from .typed_correction import INVALID, validate_codes, validate_codes_detailed
from .typed_prediction_codec import OPS, rejection_details

FAMILIES = ('operation', 'binding')


def _proposals(family, codes, logits):
    out = []
    for slot, op in enumerate(codes['op']):
        label = OPS[op]
        if family == 'operation' and label.startswith('pure:'):
            scores = logits['op'][slot]
            alternatives = sorted((i for i, name in enumerate(OPS) if name.startswith('pure:') and i != op),
                                  key=lambda i: (-scores[i], i))[:2]
            for after in alternatives:
                out.append((float(scores[op]) - float(scores[after]), 'op', slot, after))
        if family == 'binding' and label == 'ref':
            scores = logits['binding'][slot]
            current = int(codes['binding'][slot])
            alternatives = sorted((i for i in range(len(scores)) if i != current), key=lambda i: (-scores[i], i))[:2]
            for after in alternatives:
                out.append((float(scores[current]) - float(scores[after]), 'binding', slot, after))
    return sorted(out)


def family_search(family, encoding, codes, logits, params, config, evaluate, *, deadline, candidate_filter=None):
    if family not in FAMILIES:
        raise ValueError('Unknown repair family')
    started = time.perf_counter()
    deadline = min(deadline, started + config['wall_seconds'])
    if not (0 <= config['pool_size'] <= 8 and 0 <= config['max_executions'] <= 4
            and 1 <= config['max_edits'] <= 2 and 0 <= config['wall_seconds'] <= .25):
        raise ValueError('Family search exceeds the declared experiment envelope')
    result = dict(family=family, pool=[], attempts=[], edits=[], final_codes=None, graph=None, executions=0,
                  reason=f'no_public_passing_{family}', infrastructure_failure=False)
    try:
        for field in ('op', 'binding'):
            if any(not math.isfinite(float(v)) for row in logits[field] for v in row):
                raise ValueError('Nonfinite logits')
        _, error = validate_codes(encoding, codes, params)
        if error:
            raise ValueError('Family search requires a valid starting graph: ' + error)
        ranked = _proposals(family, codes, logits)
        result['pool_size_before_cut'] = len(ranked)
        pool = ranked[:config['pool_size']]
        result['pool'] = [dict(penalty=p, field=f, slot=s, after=OPS[a] if f == 'op' else a) for p, f, s, a in pool]
        combos = []
        for size in range(1, config['max_edits'] + 1):
            for combo in itertools.combinations(range(len(pool)), size):
                if len({pool[i][2] for i in combo}) != size:
                    continue
                combos.append((sum(pool[i][0] for i in combo), combo))
        combos.sort()
        result['proposal_order'] = [dict(penalty=p, proposals=list(c)) for p, c in combos]
        for penalty, combo in combos:
            if time.perf_counter() >= deadline:
                result['reason'] = f'{family}_budget'; break
            if result['executions'] >= config['max_executions']:
                result['reason'] = f'{family}_execution_budget'; break
            candidate = copy.deepcopy(codes)
            edits = []
            for i in combo:
                _, field, slot, after = pool[i]
                before = candidate[field][slot]
                candidate[field][slot] = after
                edits.append(dict(field=field, slot=slot, before=OPS[before] if field == 'op' else before,
                                  after=OPS[after] if field == 'op' else after,
                                  reason='captured model rank; no target values'))
            graph, details = validate_codes_detailed(encoding, candidate, params)
            failure = None if details is None else details['message']
            attempt = dict(edits=edits, logit_penalty=penalty, field_edits=len(edits),
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
                result['reason'] = f'{family}_budget'; break
            tick = time.perf_counter()
            verdict = evaluate(graph, remaining)
            attempt['execution_seconds'] = time.perf_counter() - tick
            attempt['public'] = verdict
            result['executions'] += 1
            if verdict['reason'] in ('sandbox_error', 'checker_error', 'no_tests'):
                result.update(reason=f'{family}_infrastructure_failure', infrastructure_failure=True); break
            if time.perf_counter() >= deadline:
                result['reason'] = f'{family}_budget'; break
            if verdict['passed']:
                result.update(final_codes=candidate, graph=graph, edits=edits, reason=f'{family}_public_passed'); break
    except INVALID as error:
        result.update(reason=f'invalid_{family}_capture', capture_failure=str(error),
                      capture_failure_details=rejection_details(error))
    result['seconds'] = time.perf_counter() - started
    return result
