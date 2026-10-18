"""Separate hierarchical-composition experiment: typed data, never Python holes.

Programs are structured graphs. Recipes expand into the same representation;
effects are explicit statements and cannot hide inside pure expressions. This is
a bounded interpreter for repository-owned development fixtures, not a sandbox
qualification or a trained predictor. No eval/exec, imports, or user callbacks.
"""
from __future__ import annotations

import copy
from collections import deque
import heapq
import json

SCHEMA = 'algsolve.typed-program.v2'
INTS = ('list', 'int')
EDGE = ('tuple', 'int', 'int', 'int')
EDGES = ('list', EDGE)
RESOURCES = {'dsu', 'heap_int', 'queue_int', 'map_int_int'}
MAX_GRAPH_NODES = 4096
MAX_DEPTH = 48
MAX_COLLECTION = 20000
MAX_INTEGER_BITS = 128


class Invalid(ValueError):
    pass


class BudgetExceeded(Invalid):
    pass


def require(ok, message):
    if not ok:
        raise Invalid(message)


def fields(value, *keys):
    require(type(value) is dict and set(value) == set(keys), f'Expected fields: {keys}')


def name(value):
    require(type(value) is str and value.isidentifier() and not value.startswith('_'), 'Invalid binding')
    return value


def dtype(value):
    if type(value) is str:
        require(value in {'int', 'bool', 'unit'} | RESOURCES, 'Unknown type')
        return value
    require(type(value) in (tuple, list) and len(value) >= 2, 'Invalid compound type')
    tag, *args = value
    require(tag in ('list', 'tuple') and (tag != 'list' or len(args) == 1), 'Invalid type constructor')
    args = tuple(dtype(a) for a in args)
    require(not any(resource(a) for a in args), 'Resources cannot be stored in values')
    return (tag, *args)


def resource(t):
    return type(t) is str and t in RESOURCES


def check_value(value, t):
    if t == 'int':
        require(type(value) is int and value.bit_length() <= MAX_INTEGER_BITS, 'Expected bounded integer')
    elif t == 'bool':
        require(type(value) is bool, 'Expected boolean')
    elif t == 'unit':
        require(value is None, 'Expected unit')
    elif type(t) is tuple:
        require(type(value) in (list, tuple) and len(value) <= MAX_COLLECTION, 'Expected bounded collection')
        if t[0] == 'list':
            for item in value:
                check_value(item, t[1])
        else:
            require(len(value) == len(t) - 1, 'Tuple width mismatch')
            for item, ty in zip(value, t[1:]):
                check_value(item, ty)
    else:
        raise Invalid('Resource values cannot cross the program boundary')


# Arguments, result, observable effect. Resource identities are lexical bindings.
EFFECTS = {
    'dsu.new': (('int',), 'dsu', 'allocate'),
    'dsu.find': (('dsu', 'int'), 'int', 'read'),
    'dsu.union': (('dsu', 'int', 'int'), 'bool', 'write'),
    'heap.new': ((), 'heap_int', 'allocate'),
    'heap.push': (('heap_int', 'int'), 'unit', 'write'),
    'heap.pop': (('heap_int',), 'int', 'write'),
    'queue.new': ((), 'queue_int', 'allocate'),
    'queue.push': (('queue_int', 'int'), 'unit', 'write'),
    'queue.pop': (('queue_int',), 'int', 'write'),
    'queue.size': (('queue_int',), 'int', 'read'),
    'map.new': ((), 'map_int_int', 'allocate'),
    'map.has': (('map_int_int', 'int'), 'bool', 'read'),
    'map.get': (('map_int_int', 'int', 'int'), 'int', 'read'),
    'map.set': (('map_int_int', 'int', 'int'), 'unit', 'write'),
}
PURE = {'add', 'sub', 'mul', 'eq', 'lt', 'not', 'neg', 'len', 'range',
        'tuple', 'field', 'empty_ints', 'append', 'sort_by'}


def pure_type(op, ts, raw):
    if op in {'add', 'sub', 'mul'}:
        require(ts == ['int', 'int'], 'Arithmetic requires integers')
        return 'int'
    if op in {'eq', 'lt'}:
        require(len(ts) == 2 and ts[0] == ts[1] and ts[0] in ('int', 'bool'), 'Invalid comparison')
        return 'bool'
    if op in {'not', 'neg'}:
        t = 'bool' if op == 'not' else 'int'
        require(ts == [t], 'Invalid unary operation')
        return t
    if op == 'empty_ints':
        require(not ts, 'Empty list has no arguments')
        return INTS
    if op == 'tuple':
        require(bool(ts) and not any(resource(t) for t in ts), 'Invalid tuple')
        return ('tuple', *ts)
    if op in {'field', 'sort_by'}:
        require(len(ts) == (2 if op == 'field' else 3), 'Wrong projection arity')
        t = ts[0]
        if op == 'sort_by':
            require(type(t) is tuple and t[0] == 'list' and ts[2] == 'bool', 'Sort needs list and direction')
            t = t[1]
        require(type(t) is tuple and t[0] == 'tuple', 'Projection requires tuple')
        require(type(raw[1]) is dict and set(raw[1]) == {'literal'} and type(raw[1]['literal']) is int,
                'Field index must be a literal integer')
        i = raw[1]['literal']
        require(0 <= i < len(t) - 1, 'Field index outside tuple')
        require(op != 'sort_by' or t[i + 1] in ('int', 'bool'), 'Sort key must be scalar')
        return t[i + 1] if op == 'field' else ts[0]
    if op == 'len':
        require(len(ts) == 1 and type(ts[0]) is tuple and ts[0][0] == 'list', 'Length requires list')
        return 'int'
    if op == 'range':
        require(ts == ['int'], 'Range requires integer')
        return INTS
    if op == 'append':
        require(len(ts) == 2 and ts[0] == ('list', ts[1]), 'Append element mismatch')
        return ts[0]
    raise Invalid('Unknown pure operator')


def bounded_tree(value, depth=0):
    require(depth <= MAX_DEPTH, 'Graph nesting limit exceeded')
    require(type(value) in (dict, list, str, int, bool, type(None)), 'Graph must be JSON data')
    if type(value) in (dict, list):
        children = value.values() if type(value) is dict else value
        n = 1 + sum(bounded_tree(child, depth + 1) for child in children)
    else:
        n = 1
        if type(value) is str:
            require(len(value) <= 256, 'Text is a binding/operator, not source code')
    require(n <= MAX_GRAPH_NODES, 'Graph size limit exceeded')
    return n


def validate(program, recipes=None, stack=(), _remaining=None):
    recipes = recipes or {}
    # Bound total recipe traversal as well as each individual graph. Otherwise
    # a small branching recipe DAG could demand exponential validation work.
    _remaining = [MAX_GRAPH_NODES] if _remaining is None else _remaining
    _remaining[0] -= bounded_tree(program)
    require(_remaining[0] >= 0, 'Expanded recipe validation size limit exceeded')
    fields(program, 'schema', 'parameters', 'inputs', 'body', 'return', 'output_type')
    require(program['schema'] == SCHEMA and type(program['inputs']) is dict, 'Invalid program schema')
    parameters = program['parameters']
    require(type(parameters) is list and all(type(p) is str for p in parameters), 'Ordered signature required')
    require(len(parameters) == len(set(parameters)) and set(parameters) == set(program['inputs']),
            'Signature must cover each input exactly once')
    env = {name(k): (dtype(program['inputs'][k]), False) for k in parameters}
    require(not any(resource(t) for t, _ in env.values()), 'Resource inputs are not supported')
    output = dtype(program['output_type'])
    require(not resource(output), 'Resource outputs are not supported')

    def expr(e, scope):
        require(type(e) is dict, 'Expressions must be structured objects')
        if set(e) == {'ref'}:
            require(e['ref'] in scope, 'Unbound reference')
            return scope[e['ref']][0]
        if set(e) == {'literal'}:
            v = e['literal']
            t = 'bool' if type(v) is bool else 'int'
            check_value(v, t)
            return t
        fields(e, 'op', 'args')
        require(type(e['args']) is list and e['op'] in PURE, 'Unknown pure expression')
        ts = [expr(a, scope) for a in e['args']]
        return pure_type(e['op'], ts, e['args'])

    def bind(scope, key, ty, mutable=False):
        name(key)
        require(key not in scope, 'Shadowing/rebinding requires explicit set')
        scope[key] = (ty, mutable)

    def block(body, scope):
        require(type(body) is list, 'Block must be a list')
        for s in body:
            require(type(s) is dict and 'op' in s, 'Invalid statement')
            op = s['op']
            if op in ('let', 'var', 'set'):
                fields(s, 'op', 'name', 'value')
                ty = expr(s['value'], scope)
                require(not resource(ty), 'Resource aliasing is not supported')
                if op == 'set':
                    require(scope.get(s['name']) == (ty, True), 'Set requires matching mutable binding')
                else:
                    bind(scope, s['name'], ty, op == 'var')
            elif op == 'call':
                fields(s, 'op', 'operator', 'args', 'out')
                require(s['operator'] in EFFECTS and type(s['args']) is list, 'Unknown effect')
                ins, out, _ = EFFECTS[s['operator']]
                require(tuple(expr(a, scope) for a in s['args']) == ins, 'Effect port type mismatch')
                bind(scope, s['out'], out)
            elif op == 'recipe':
                fields(s, 'op', 'recipe', 'args', 'out')
                key = s['recipe']
                require(key in recipes and key not in stack and len(stack) < 8, 'Unknown/recursive recipe')
                target = recipes[key]
                ins, out = validate(target, recipes, (*stack, key), _remaining)
                require(type(s['args']) is list and [expr(a, scope) for a in s['args']] == list(ins.values()),
                        'Recipe port type mismatch')
                bind(scope, s['out'], out)
            elif op == 'for':
                fields(s, 'op', 'item', 'in', 'body')
                ty = expr(s['in'], scope)
                require(type(ty) is tuple and ty[0] == 'list', 'Iteration requires list')
                child = dict(scope)
                bind(child, s['item'], ty[1])
                block(s['body'], child)
            elif op == 'if':
                fields(s, 'op', 'condition', 'then', 'else')
                require(expr(s['condition'], scope) == 'bool', 'Condition requires boolean')
                block(s['then'], dict(scope))
                block(s['else'], dict(scope))
            else:
                raise Invalid('Unknown statement')
    block(program['body'], env)
    require(expr(program['return'], env) == output, 'Return type mismatch')
    return {k: dtype(program['inputs'][k]) for k in parameters}, output


class Cell:
    def __init__(self, value):
        self.value = value


class Budget:
    def __init__(self, remaining=100000):
        self.remaining = remaining

    def spend(self, amount=1):
        self.remaining -= amount
        if self.remaining < 0:
            raise BudgetExceeded('Execution operation budget exhausted')


def _pure(op, a, budget):
    if op == 'add': return a[0] + a[1]
    if op == 'sub': return a[0] - a[1]
    if op == 'mul': return a[0] * a[1]
    if op == 'eq': return a[0] == a[1]
    if op == 'lt': return a[0] < a[1]
    if op == 'not': return not a[0]
    if op == 'neg': return -a[0]
    if op == 'tuple': return tuple(a)
    if op == 'field': return a[0][a[1]]
    if op == 'empty_ints': return []
    if op == 'len': return len(a[0])
    n = a[0] if op == 'range' else len(a[0]) + (op == 'append')
    require(0 <= n <= MAX_COLLECTION, 'Collection size limit exceeded')
    budget.spend(n * max(1, n.bit_length()) if op == 'sort_by' else n)
    if op == 'range': return list(range(n))
    if op == 'append': return [*a[0], a[1]]
    if op == 'sort_by': return sorted(a[0], key=lambda x: x[a[1]], reverse=a[2])
    raise Invalid('Unknown operation')


def _effect(op, a, budget):
    if op == 'dsu.new':
        require(0 <= a[0] <= MAX_COLLECTION, 'Invalid disjoint-set size')
        budget.spend(a[0])
        return [list(range(a[0])), [1] * a[0]]
    if op in ('dsu.find', 'dsu.union'):
        parent, sizes = a[0]
        def root(i):
            require(0 <= i < len(parent), 'Vertex outside disjoint sets')
            while parent[i] != i:
                budget.spend()
                i = parent[i]
            return i
        x = root(a[1])
        if op == 'dsu.find': return x
        y = root(a[2])
        if x == y: return False
        if sizes[x] < sizes[y]: x, y = y, x
        parent[y] = x
        sizes[x] += sizes[y]
        return True
    if op == 'heap.new': return []
    if op == 'queue.new': return deque()
    if op == 'map.new': return {}
    obj = a[0]
    if op.endswith('.push') or op == 'map.set':
        require(len(obj) < MAX_COLLECTION or (op == 'map.set' and a[1] in obj), 'Resource capacity exceeded')
    if op.startswith('heap.'):
        budget.spend(max(1, len(obj).bit_length()))
    if op == 'heap.push': heapq.heappush(obj, a[1])
    elif op == 'heap.pop':
        require(bool(obj), 'Pop from empty heap')
        return heapq.heappop(obj)
    elif op == 'queue.push': obj.append(a[1])
    elif op == 'queue.pop':
        require(bool(obj), 'Pop from empty queue')
        return obj.popleft()
    elif op == 'queue.size': return len(obj)
    elif op == 'map.has': return a[1] in obj
    elif op == 'map.get': return obj.get(a[1], a[2])
    elif op == 'map.set': obj[a[1]] = a[2]
    else: raise Invalid('Unknown effect')
    return None


def _run(program, arguments, recipes, budget):
    env = dict(zip(program['parameters'], arguments))
    def expr(e, scope):
        budget.spend()
        if 'ref' in e:
            v = scope[e['ref']]
            return v.value if isinstance(v, Cell) else v
        if 'literal' in e: return e['literal']
        result = _pure(e['op'], [expr(a, scope) for a in e['args']], budget)
        if type(result) is int:
            check_value(result, 'int')
        return result
    def block(body, scope):
        for s in body:
            budget.spend()
            op = s['op']
            if op in ('let', 'var', 'set'):
                value = expr(s['value'], scope)
                if op == 'set': scope[s['name']].value = value
                else: scope[s['name']] = Cell(value) if op == 'var' else value
            elif op == 'call':
                scope[s['out']] = _effect(s['operator'], [expr(a, scope) for a in s['args']], budget)
            elif op == 'recipe':
                scope[s['out']] = _run(recipes[s['recipe']], [expr(a, scope) for a in s['args']], recipes, budget)
            elif op == 'for':
                for item in expr(s['in'], scope):
                    budget.spend()
                    block(s['body'], {**scope, s['item']: item})
            elif op == 'if':
                block(s['then'] if expr(s['condition'], scope) else s['else'], dict(scope))
    block(program['body'], env)
    return expr(program['return'], env)


def execute(program, arguments, *, recipes=None, budget=100000):
    """Validate before execution; each call owns fresh state, including on failure."""
    recipes = recipes or {}
    ins, out = validate(program, recipes)
    require(type(arguments) is dict and set(arguments) == set(ins), 'Input names mismatch')
    for key, ty in ins.items(): check_value(arguments[key], ty)
    require(type(budget) is int and budget > 0, 'Invalid execution budget')
    result = _run(program, [copy.deepcopy(arguments[k]) for k in ins], recipes, Budget(budget))
    check_value(result, out)
    return result


def expanded(program, recipes):
    """Inspectable hygienic inlining; recipe result becomes an ordinary let.

    No closures, hidden state, or opaque algorithm calls remain after expansion.
    """
    validate(program, recipes)
    serial = [0]
    def expand(p, mapping):
        def expression(e, names):
            if 'ref' in e: return {'ref': names[e['ref']]}
            if 'literal' in e: return dict(e)
            return {'op': e['op'], 'args': [expression(a, names) for a in e['args']]}
        def fresh():
            serial[0] += 1
            return f'v{serial[0]}'
        def block(body, names):
            result = []
            for s in body:
                op = s['op']
                if op == 'recipe':
                    target = recipes[s['recipe']]
                    child = {}
                    for key, arg in zip(target['parameters'], s['args']):
                        child[key] = fresh()
                        result.append({'op': 'let', 'name': child[key], 'value': expression(arg, names)})
                    sub, answer = expand(target, child)
                    result.extend(sub)
                    names[s['out']] = fresh()
                    result.append({'op': 'let', 'name': names[s['out']], 'value': answer})
                elif op in ('let', 'var', 'set'):
                    value = expression(s['value'], names)
                    if op != 'set': names[s['name']] = fresh()
                    result.append({'op': op, 'name': names[s['name']], 'value': value})
                elif op == 'call':
                    args = [expression(a, names) for a in s['args']]
                    names[s['out']] = fresh()
                    result.append({'op': op, 'operator': s['operator'], 'args': args, 'out': names[s['out']]})
                elif op == 'for':
                    child = dict(names)
                    child[s['item']] = fresh()
                    result.append({'op': op, 'item': child[s['item']], 'in': expression(s['in'], names),
                                   'body': block(s['body'], child)})
                elif op == 'if':
                    result.append({'op': op, 'condition': expression(s['condition'], names),
                                   'then': block(s['then'], dict(names)), 'else': block(s['else'], dict(names))})
            return result
        body = block(p['body'], mapping)
        return body, expression(p['return'], mapping)
    # Prefix inputs so fresh local names cannot collide with external bindings.
    mapping = {k: f'input{i}' for i, k in enumerate(program['parameters'])}
    body, answer = expand(program, dict(mapping))
    result = {'schema': SCHEMA, 'parameters': [mapping[k] for k in program['parameters']],
              'inputs': {mapping[k]: v for k, v in program['inputs'].items()},
              'body': body, 'return': answer, 'output_type': program['output_type']}
    validate(result)
    return result, mapping


def operation_counts(program):
    from collections import Counter
    counts = Counter()
    def visit(v):
        if type(v) is dict:
            if 'op' in v: counts[v.get('operator', v['op'])] += 1
            for child in v.values(): visit(child)
        elif type(v) is list:
            for child in v: visit(child)
    visit(program)
    return dict(sorted(counts.items()))


def canonical(program):
    # Positional ports live in the explicit parameters array, never map order.
    return json.dumps(program, sort_keys=True, separators=(',', ':'), allow_nan=False)
