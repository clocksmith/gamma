"""Bounded, example-conditioned search over base-v2 typed programs: the
non-neural comparator for the BITS pilot (route ``direct_bits_search``).

The grammar is fixed and generic; no task identity, target, reference or
independent test enters. Candidates are enumerated in a fixed order (size
first), validated by the typed IR and run by its interpreter; the first
candidate that reproduces every public example is frozen. Supported
signatures: integer and integer-list parameters, with an integer, Boolean or
integer-list result. Anything else is reported unsupported and stays in the
denominator. The search stops at the wall deadline or the candidate limit.
"""
from __future__ import annotations

import itertools
import json
import time

from . import typed_program as ir
from . import typed_recipes

SCHEMA = 'algsolve.base-v2-bounded-search.v1'
MAX_CANDIDATES = 20000
EXECUTION_BUDGET = 200000
LITERALS = (0, 1, 2, -1)
INTS = ['list', 'int']


def ref(n): return {'ref': n}
def lit(v): return {'literal': v}
def op(o, *a): return {'op': o, 'args': list(a)}
def var(n, v): return {'op': 'var', 'name': n, 'value': v}
def put(n, v): return {'op': 'set', 'name': n, 'value': v}
def each(item, values, body): return {'op': 'for', 'item': item, 'in': values, 'body': body}
def branch(c, yes, no=()): return {'op': 'if', 'condition': c, 'then': list(yes), 'else': list(no)}


def _type(annotation):
    a = str(annotation).replace(' ', '')
    return {'int': 'int', 'bool': 'bool', 'List[int]': INTS}.get(a)


def _folds(lists, scalars, counter):
    """(statements, result-name) pairs for generic folds over each list parameter."""
    out = []
    for name in lists:
        def new():
            counter[0] += 1
            return f'acc{counter[0]}', f'v{counter[0]}'
        for init, step in ((0, lambda a, v: op('add', ref(a), ref(v))), (0, lambda a, v: op('add', ref(a), lit(1))),
                           (1, lambda a, v: op('mul', ref(a), ref(v))),
                           (0, lambda a, v: op('add', ref(a), op('mul', ref(v), ref(v))))):
            a, v = new()
            out.append(([var(a, lit(init)), each(v, ref(name), [put(a, step(a, v))])], a))
        for init in (-(1 << 40), 1 << 40):  # running maximum / minimum
            a, v = new()
            better = op('lt', ref(a), ref(v)) if init < 0 else op('lt', ref(v), ref(a))
            out.append(([var(a, lit(init)), each(v, ref(name), [branch(better, [put(a, ref(v))])])], a))
        for threshold in [*(ref(s) for s in scalars), *(lit(k) for k in LITERALS)]:
            for cond in (lambda v: op('lt', ref(v), threshold), lambda v: op('lt', threshold, ref(v)),
                         lambda v: op('eq', ref(v), threshold)):
                for counted in ('count', 'sum'):
                    a, v = new()
                    inc = op('add', ref(a), lit(1) if counted == 'count' else ref(v))
                    out.append(([var(a, lit(0)), each(v, ref(name), [branch(cond(v), [put(a, inc)])])], a))
    return out


def candidates(params, output):
    """Fixed-order candidate programs for a supported signature."""
    names = [p for p, _ in params]
    types = {p: t for p, t in params}
    scalars = [p for p in names if types[p] == 'int']
    lists = [p for p in names if types[p] == INTS]
    counter = [0]
    terms = [([], ref(s)) for s in scalars] + [([], lit(k)) for k in LITERALS] + [([], op('len', ref(l))) for l in lists]
    terms += [(body, ref(name)) for body, name in _folds(lists, scalars, counter)]
    def program(body, result, out_type):
        return {'schema': ir.SCHEMA, 'parameters': names, 'inputs': {p: types[p] for p in names},
                'body': body, 'return': result, 'output_type': out_type}
    if output == 'int':
        for body, term in terms:
            yield program(body, term, 'int')
        for (b1, t1), (b2, t2) in itertools.product(terms, repeat=2):
            for o in ('add', 'sub', 'mul'):
                yield program(_rename(b1, '_l') + _rename(b2, '_r'), op(o, _rename_expr(t1, '_l'), _rename_expr(t2, '_r')), 'int')
    elif output == 'bool':
        for (b1, t1), (b2, t2) in itertools.product(terms, repeat=2):
            for o in ('eq', 'lt'):
                yield program(_rename(b1, '_l') + _rename(b2, '_r'), op(o, _rename_expr(t1, '_l'), _rename_expr(t2, '_r')), 'bool')
                yield program(_rename(b1, '_l') + _rename(b2, '_r'), op('not', op(o, _rename_expr(t1, '_l'), _rename_expr(t2, '_r'))), 'bool')
    elif output == INTS:
        for s in scalars:
            yield program([], op('range', ref(s)), INTS)
        for l in lists:
            yield program([], ref(l), INTS)
            for threshold in [*(ref(s) for s in scalars), *(lit(k) for k in LITERALS)]:
                for cond in (lambda v: op('lt', ref(v), threshold), lambda v: op('lt', threshold, ref(v)),
                             lambda v: op('eq', ref(v), threshold), lambda v: op('not', op('eq', ref(v), threshold))):
                    body = [var('out', op('empty_ints')), each('v', ref(l), [branch(cond('v'), [put('out', op('append', ref('out'), ref('v')))])])]
                    yield program(body, ref('out'), INTS)
                for o in ('add', 'sub', 'mul'):
                    body = [var('out', op('empty_ints')), each('v', ref(l), [put('out', op('append', ref('out'), op(o, ref('v'), threshold)))])]
                    yield program(body, ref('out'), INTS)


def _rename_expr(e, suffix):
    if isinstance(e, dict):
        if 'ref' in e and e['ref'].startswith(('acc', 'v')) and e['ref'][1:].lstrip('cc').isdigit():
            return {'ref': e['ref'] + suffix}
        return {k: _rename_expr(v, suffix) for k, v in e.items()}
    if isinstance(e, list):
        return [_rename_expr(x, suffix) for x in e]
    return e


def _rename(body, suffix):
    out = []
    for s in body:
        s = _rename_expr(s, suffix)
        for key in ('name', 'item'):
            if key in s and (s[key].startswith('acc') or s[key].startswith('v')) and s[key][1:].lstrip('cc').isdigit():
                s[key] = s[key] + suffix
        out.append(s)
    return out


def search(params, return_annotation, public_examples, *, deadline, candidate_limit=MAX_CANDIDATES):
    """Return the first public-consistent candidate, or a reason, with complete costs."""
    started = time.perf_counter()
    typed = [(p, _type(a)) for p, a in params]
    output = _type(return_annotation)
    result = {'schema': SCHEMA, 'graph': None, 'candidates': 0, 'invalid': 0, 'executions': 0, 'reason': None}
    if any(t is None for _, t in typed) or output is None or not public_examples:
        result['reason'] = 'unsupported_signature' if public_examples else 'no_public_examples'
        result['seconds'] = time.perf_counter() - started
        return result
    recipes = typed_recipes.catalog()
    for program in candidates(typed, output):
        if time.perf_counter() >= deadline:
            result['reason'] = 'search_budget'; break
        if result['candidates'] >= candidate_limit:
            result['reason'] = 'candidate_limit'; break
        result['candidates'] += 1
        try:
            ir.validate(program, recipes)
        except ir.Invalid:
            result['invalid'] += 1
            continue
        passed = True
        for example in public_examples:
            result['executions'] += 1
            try:
                got = ir.execute(program, dict(zip([p for p, _ in params], example['args'])))
            except (ir.Invalid, ValueError, TypeError, ZeroDivisionError, RecursionError):
                passed = False; break
            if json.loads(json.dumps(got)) != example['expected']:
                passed = False; break
        if passed:
            result.update(graph=program, reason='public_consistent'); break
    else:
        result['reason'] = result['reason'] or 'exhausted'
    result['seconds'] = time.perf_counter() - started
    return result
