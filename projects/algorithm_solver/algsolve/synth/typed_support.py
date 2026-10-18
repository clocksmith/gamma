"""Necessary feature support, not proof of learnability or protected novelty.

Audits use targets for partition qualification only, never prediction inputs.
Examined development targets cannot be promoted to fresh protected evaluation.
"""
from . import typed_program as ir, typed_recipes, typed_codec


def features(program):
    catalog = typed_recipes.catalog()
    ir.validate(program, catalog)
    found = set()
    def typ(t):
        found.add('type:' + ir.canonical(t))
        if ir.resource(t): found.add('resource:' + t)
    def expression(e, scope):
        if 'ref' in e:
            ty, mode = scope[e['ref']]
            found.add('binding:' + mode)
            if ir.resource(ty): found.add('binding:resource_handle')
        elif 'literal' in e:
            v = e['literal']
            ty = 'bool' if type(v) is bool else 'int'
            cls = str(v).lower() if ty == 'bool' else ('zero' if v == 0 else 'one' if v == 1 else 'negative' if v < 0 else 'positive')
            found.add('literal:' + ty + ':' + cls)
        else:
            found.add('pure:' + e['op'])
            ts = [expression(a, scope) for a in e['args']]
            ty = ir.pure_type(e['op'], ts, e['args'])
            for i, t in enumerate(ts): found.add(f'port:{e["op"]}:{i}:' + ir.canonical(t))
            if e['op'] in ('field', 'sort_by'): found.add('parameter:tuple_field_index')
        typ(ty)
        return ty
    def body(stmts, scope):
        for s in stmts:
            op = s['op']
            found.add('statement:' + op)
            if op in ('let', 'var', 'set'):
                t = expression(s['value'], scope)
                if op != 'set': scope[s['name']] = (t, 'mutable_cell' if op == 'var' else 'prior_output')
                else: found.add('binding:mutable_write')
            elif op == 'call':
                ins, out, effect = ir.EFFECTS[s['operator']]
                found.add('effect_operator:' + s['operator'])
                found.add('effect:' + effect)
                for arg in s['args']: expression(arg, scope)
                typ(out)
                scope[s['out']] = (out, 'prior_output')
            elif op == 'recipe':
                found.add('recipe:' + s['recipe'])
                found.add('mechanism:recipe_expansion')
                for arg in s['args']: expression(arg, scope)
                target = catalog[s['recipe']]
                scan(target)
                scope[s['out']] = (ir.dtype(target['output_type']), 'recipe_output')
            elif op == 'for':
                t = expression(s['in'], scope)
                body(s['body'], {**scope, s['item']: (t[1], 'loop_item')})
            elif op == 'if':
                expression(s['condition'], scope)
                body(s['then'], dict(scope))
                body(s['else'], dict(scope))
    def scan(p):
        scope = {k: (ir.dtype(t), 'input') for k, t in p['inputs'].items()}
        for ty, _ in scope.values(): typ(ty)
        body(p['body'], scope)
        expression(p['return'], scope)
    scan(program)
    return sorted(found)


def pattern(program):
    expanded, _ = ir.expanded(program, typed_recipes.catalog())
    # Alpha-renamed expansion preserves dataflow and input type order. Literal
    # values are omitted to keep scalar variants conservatively together.
    def shape(v):
        if type(v) is list: return [shape(x) for x in v]
        if type(v) is dict:
            if set(v) == {'literal'}:
                return {'literal_type': 'bool' if type(v['literal']) is bool else 'int'}
            return {k: shape(x) for k, x in v.items()}
        return v
    return typed_codec.digest(shape(expanded))


def audit(training, candidates):
    known = set().union(*(set(features(p['target']['program'])) for p in training))
    uids = {p['uid'] for p in training}
    families = {p['problem_family'] for p in training}
    patterns = {p['pattern_sha256'] for p in training}
    rows = []
    for p in candidates:
        needed = set(features(p['target']['program']))
        leakage = []
        if p['uid'] in uids: leakage.append('same_problem')
        if p['problem_family'] in families: leakage.append('same_family')
        if p['pattern_sha256'] in patterns: leakage.append('same_pattern')
        rows.append({'uid': p['uid'], 'target_sha256': typed_codec.digest(p['target']),
                     'missing_features': sorted(needed-known), 'overlap': leakage,
                     'supported': not (needed-known), 'partition_eligible': not (needed-known or leakage)})
    return {'training_features': sorted(known), 'candidates': rows,
            'all_supported': bool(rows) and all(r['supported'] for r in rows),
            'partition_eligible': bool(rows) and all(r['partition_eligible'] for r in rows),
            'protected_generalization': False,
            'limits': ['Support is necessary, not sufficient for prediction or semantic novelty.',
                       'Audit feature presence does not measure support frequency or learning quality.',
                       'Inspected development candidates remain debugging data even if partition-eligible.']}
