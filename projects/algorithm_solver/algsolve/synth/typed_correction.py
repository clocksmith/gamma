"""Bounded, score-ordered schema repair. No tasks, examples or solutions enter here."""
from __future__ import annotations

import copy
import heapq
import math
import time

from .typed_prediction_codec import INPUTS, OPS

INVALID = (ValueError, TypeError, KeyError, IndexError, RecursionError)


def validate_codes(encoding, codes, params):
    try:
        return encoding.decode(codes, params), None
    except INVALID as error:
        return None, str(error)


def correct(encoding, raw, logits, params, config, *, deadline=None):
    """Try sealed alternative scalar decisions; return the first strictly valid graph.

    Candidate order minimizes summed logit loss from the original prediction.
    Ties use field, slot and value. Only schema validity selects a candidate.
    The finite pool and search bounds deliberately do not promise completeness.
    """
    started = time.perf_counter()
    deadline = min(deadline if deadline is not None else math.inf,
                   started + config['wall_seconds'])
    graph, error = validate_codes(encoding, raw, params)
    result = {'raw_validation_failure': error, 'attempts': [], 'edits': [],
              'final_codes': None, 'graph': None, 'reason': 'unresolved_invalid_graph'}
    if graph is not None:
        return {**result, 'graph': graph, 'final_codes': copy.deepcopy(raw),
                'reason': 'already_valid', 'seconds': time.perf_counter()-started}
    # Explicit dimensions and finite scores prevent malformed captures from
    # escaping the request budget or influencing ordering through NaN.
    expected = {'op': (encoding.slots, len(OPS)),
                'first': (encoding.slots, encoding.slots+1),
                'next': (encoding.slots, encoding.slots+1),
                'binding': (encoding.slots, INPUTS+encoding.slots),
                'types': (INPUTS+1, len(encoding.types))}
    try:
        for field, (rows, columns) in expected.items():
            if len(logits[field]) != rows or any(len(row) != columns for row in logits[field]):
                raise ValueError('Logit dimensions differ')
            if any(not math.isfinite(float(v)) for row in logits[field] for v in row):
                raise ValueError('Nonfinite logits')
        if any(len(raw[field]) != rows for field, (rows, _) in expected.items()):
            raise ValueError('Raw prediction dimensions differ')
        # Preserve the real model argmax, including deterministic lowest-index
        # ties. A caller cannot pair a different raw prediction with these scores.
        for field, (rows, _) in expected.items():
            for slot in range(rows):
                scores = logits[field][slot]
                best = max(range(len(scores)), key=lambda value: (scores[value], -value))
                if int(raw[field][slot]) != best:
                    raise ValueError('Raw prediction does not match captured logits')
        active = [i for i, value in enumerate(raw['op']) if value != 0]
        frontier = min(len(active), encoding.slots-1)
        pool = []
        for field in config['fields']:
            for slot, scores in enumerate(logits[field]):
                if time.perf_counter() >= deadline:
                    return {**result, 'reason': 'correction_budget', 'seconds': time.perf_counter()-started}
                if field == 'types':
                    if slot not in [*range(len(params)), INPUTS]:
                        continue
                elif field == 'op':
                    if slot not in active and slot != frontier:
                        continue
                elif slot not in active:
                    continue
                if field == 'binding' and OPS[raw['op'][slot]] not in ('ref', 'set'):
                    continue
                original = int(raw[field][slot])
                ranked = sorted(range(len(scores)), key=lambda v: (-scores[v], v))
                for value in [v for v in ranked if v != original][:config['alternatives_per_field']]:
                    penalty = float(scores[original])-float(scores[value])
                    pool.append((penalty, field, slot, value))
        pool.sort()
        pool = pool[:config['max_edit_options']]
        queue = [(edit[0], (i,)) for i, edit in enumerate(pool)]
        heapq.heapify(queue)
        while queue and len(result['attempts']) < config['max_candidates']:
            if time.perf_counter() >= deadline:
                result['reason'] = 'correction_budget'
                break
            penalty, indices = heapq.heappop(queue)
            candidate = copy.deepcopy(raw)
            edits = []
            for index in indices:
                _, field, slot, value = pool[index]
                edits.append({'field': field, 'slot': slot, 'from': raw[field][slot], 'to': value,
                              'reason': 'model-ranked alternative subject to schema/type/scope/effect validation'})
                candidate[field][slot] = value
            graph, failure = validate_codes(encoding, candidate, params)
            result['attempts'].append({'edits': edits, 'logit_penalty': penalty,
                                       'validation_failure': failure})
            if graph is not None and time.perf_counter() < deadline:
                result.update(graph=graph, final_codes=candidate, edits=edits, reason='schema_repaired')
                break
            if len(indices) < config['max_edits']:
                occupied = {(pool[i][1], pool[i][2]) for i in indices}
                for index in range(indices[-1]+1, len(pool)):
                    edit = pool[index]
                    if (edit[1], edit[2]) not in occupied:
                        heapq.heappush(queue, (penalty+edit[0], (*indices, index)))
        else:
            result['reason'] = 'candidate_budget' if queue else 'no_valid_correction'
    except INVALID as failure:
        result['reason'] = 'invalid_capture'
        result['capture_failure'] = str(failure)
    result['seconds'] = time.perf_counter()-started
    return result
