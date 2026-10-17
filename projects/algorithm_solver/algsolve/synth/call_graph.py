"""Candidate v2: explicit calls to tested algorithms, with bounded glue.

V1 remains frozen. This compiler exposes its existing library functions as graph
nodes instead of hiding calls in generic formula holes. A graph is not accepted
because it compiles: assembled programs still require the Linux sandbox judge.
The only new algorithm here is fixed-width window sums. Library identity binds
both implementations and this compiler; no runtime source generation by a model.
"""
from __future__ import annotations

import ast
import hashlib
import json
import keyword
from dataclasses import dataclass
from pathlib import Path

from . import components, grammar, render

SCHEMA = 'algsolve.call-graph.v2'
MAX_NODES = 3
MAX_GLUE_NODES = 40

WINDOW_SOURCE = '''
def c_window_sums(values, width):
    if type(width) is not int or width < 0:
        raise ValueError('width must be a nonnegative integer')
    if width > len(values):
        return []
    total = sum(values[:width])
    result = [total]
    for right in range(width, len(values)):
        total += values[right] - values[right - width]
        result.append(total)
    return result
'''.strip() + '\n'

# Function identities are stable; contracts are inherited verbatim from v1.
# Constructors with mutable method protocols are deliberately not call nodes.
FUNCTIONS = {
    'prefix_sums': ('c_prefix_sums', 1, 'prefix'),
    'prefix_2d': ('c_prefix_2d', 1, 'prefix'),
    'lis_length': ('c_lis_length', 2, 'lis'),
    'merge_intervals': ('c_merge_intervals', 1, 'intervals'),
    'next_index': ('c_next_index', 2, 'monostack'),
    'prev_index': ('c_prev_index', 2, 'monostack'),
    'prefix_function': ('c_prefix_function', 1, 'kmp'),
    'find_all': ('c_find_all', 2, 'kmp'),
    'z_function': ('c_z_function', 1, 'zfunc'),
    'adjacency': ('c_adjacency', 4, 'graph'),
    'bfs': ('c_bfs', 3, 'graph'),
    'dijkstra': ('c_dijkstra', 3, 'graph'),
    'topo': ('c_topo', 2, 'graph'),
    'kruskal': ('c_kruskal', 2, 'kruskal'),
    'list_values': ('c_list_values', 1, 'structures'),
    'window_sums': ('c_window_sums', 2, 'window_sums'),
}


def vocabulary_hash():
    digest = hashlib.sha256()
    for name in ('call_graph.py', 'components.py', 'grammar.py', 'render.py'):
        digest.update(name.encode())
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def catalog():
    return {name: {'arity': arity, 'component': owner,
                  'contract': ('c_window_sums(values, width): all contiguous width-element sums; '
                               'integers, nonnegative width; zero width returns n+1 zeros; '
                               'width > n returns []; O(n) time/output; no input mutation.'
                               if owner == 'window_sums' else components.COMPONENTS[owner]['contract'])}
            for name, (_, arity, owner) in FUNCTIONS.items()}


# Glue may transform values, but algorithm calls must be visible graph nodes.
# Exclude mutating calls and combinatorial generators from this bounded target.
PURE_CALLS = frozenset({'min', 'max', 'abs', 'len', 'sum', 'sorted', 'reversed',
                        'range', 'enumerate', 'zip', 'any', 'all', 'int', 'str',
                        'list', 'tuple', 'set', 'dict', 'bool', 'ord', 'chr', 'float'})
PURE_METHODS = frozenset({'count', 'index', 'get', 'split', 'join', 'lower', 'upper'})


def identifier(name):
    if not isinstance(name, str) or keyword.iskeyword(name):
        raise ValueError('Invalid identifier')
    grammar.check_identifier(name)
    if name in PURE_CALLS or name.startswith(('c_', 'stage_')) or name == 'self':
        raise ValueError('Reserved identifier')


def expression(source, scope):
    """Validate lexical bindings, including lambda/comprehension local scopes."""
    if not isinstance(source, str) or len(source) > 4096:
        raise ValueError('Invalid glue expression')
    checked = grammar.check_expr(source)
    tree = ast.parse(source.strip(), mode='eval')
    dependencies = set()

    def walk(node, local):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and node.id not in local and node.id not in PURE_CALLS:
                raise ValueError(f'Unbound name: {node.id}')
            if isinstance(node.ctx, ast.Load) and node.id in scope:
                dependencies.add(node.id)
            return
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in PURE_CALLS:
                raise ValueError('Algorithm calls must be graph nodes')
            if isinstance(node.func, ast.Attribute) and node.func.attr not in PURE_METHODS:
                raise ValueError('Mutating or unknown method in glue')
        if isinstance(node, ast.Attribute) and node.attr not in PURE_METHODS:
            raise ValueError('Unknown attribute in glue')
        if isinstance(node, ast.Lambda):
            if node.args.defaults or node.args.kw_defaults or node.args.vararg or node.args.kwarg or node.args.kwonlyargs:
                raise ValueError('Only plain lambda parameters are supported')
            names = [a.arg for a in node.args.posonlyargs + node.args.args]
            for name in names:
                identifier(name)
            if len(set(names)) != len(names) or set(names) & set(scope):
                raise ValueError('Lambda bindings must not shadow graph values')
            walk(node.body, local | set(names))
            return
        if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
            gen = node.generators[0]
            if gen.is_async:
                raise ValueError('Async glue is unsupported')
            walk(gen.iter, local)
            targets = [n.id for n in ast.walk(gen.target) if isinstance(n, ast.Name)]
            if not isinstance(gen.target, (ast.Name, ast.Tuple, ast.List)) or not targets:
                raise ValueError('Invalid comprehension binding')
            for name in targets:
                identifier(name)
            if len(set(targets)) != len(targets) or set(targets) & set(scope):
                raise ValueError('Comprehension bindings must not shadow graph values')
            inner = local | set(targets)
            for condition in gen.ifs:
                walk(condition, inner)
            for child in ([node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]):
                walk(child, inner)
            return
        for child in ast.iter_child_nodes(node):
            walk(child, local)

    walk(tree, set(scope))
    return ast.unparse(tree), checked.nodes, dependencies


@dataclass(frozen=True)
class Compiled:
    source: str
    glue_nodes: int
    operators: tuple[str, ...]
    vocabulary_sha256: str


def compile_graph(graph, *, method, params):
    if set(graph) != {'schema', 'vocabulary_sha256', 'nodes', 'answer'} or graph['schema'] != SCHEMA:
        raise ValueError('Unknown graph schema or fields')
    identity = vocabulary_hash()
    if graph['vocabulary_sha256'] != identity:
        raise ValueError('Graph vocabulary changed')
    identifier(method)
    for param in params:
        identifier(param)
    if len(set(params)) != len(params):
        raise ValueError('Duplicate input parameter')
    nodes = graph['nodes']
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        raise ValueError('Graph requires one to three nodes')
    scope, dependencies, calls, owners, operators, total = set(params), {}, [], [], [], 0
    for node in nodes:
        if set(node) != {'operator', 'arguments', 'output'} or node['operator'] not in FUNCTIONS:
            raise ValueError('Unknown graph operator or fields')
        function, arity, owner = FUNCTIONS[node['operator']]
        if not isinstance(node['arguments'], list) or len(node['arguments']) != arity:
            raise ValueError('Wrong port count')
        output = node['output']
        identifier(output)
        if output in scope:
            raise ValueError('Output shadows an existing value')
        arguments, used = [], set()
        for source in node['arguments']:
            argument, count, refs = expression(source, scope)
            arguments.append(argument)
            total += count
            used.update(refs)
        calls.append(f'{output} = {function}({", ".join(arguments)})')
        dependencies[output] = used
        scope.add(output)
        owners.append(owner)
        operators.append(node['operator'])
    answer, count, live = expression(graph['answer'], scope)
    total += count
    if total > MAX_GLUE_NODES:
        raise ValueError(f'Graph has {total} glue AST nodes; maximum is {MAX_GLUE_NODES}')
    pending = list(live)
    while pending:
        for dependency in dependencies.get(pending.pop(), ()):
            if dependency not in live:
                live.add(dependency)
                pending.append(dependency)
    if not set(dependencies) <= live:
        raise ValueError('Unused algorithm nodes do not qualify as composition')
    needed = components.resolve([owner for owner in dict.fromkeys(owners) if owner != 'window_sums'])
    library = '\n'.join(components.COMPONENTS[owner]['source'] for owner in needed)
    if 'window_sums' in owners:
        library += '\n' + WINDOW_SOURCE
    body = '\n'.join('        ' + line for line in calls + ['return ' + answer])
    source = (render.PREAMBLE + '\n\n' + library + '\nclass Solution:\n'
              f'    def {method}(self{", " if params else ""}{", ".join(params)}):\n' + body + '\n')
    compile(source, '<call-graph>', 'exec')
    return Compiled(source, total, tuple(operators), identity)
