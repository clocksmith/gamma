"""Bounded stage/AST targets for parallel composition prediction.

This is a target representation and deterministic compiler, not a learned model.
V1 skeleton semantics remain frozen; stage edges point only to inputs/earlier
outputs. Hole ASTs expose remaining logic instead of hiding it in source strings.
"""
from __future__ import annotations
import ast
import hashlib

from . import grammar, render, skeletons

SCHEMA = 'algsolve.graph-target.v1'
MAX_HOLE_NODES = 40


def tree_data(node):
    if isinstance(node, ast.AST):
        return {'op': type(node).__name__, 'fields': {k: tree_data(v) for k, v in ast.iter_fields(node)}}
    if isinstance(node, list):
        return [tree_data(v) for v in node]
    if node is None or type(node) in (str, int, float, bool):
        return node
    raise ValueError(f'Unsupported AST literal: {type(node).__name__}')


def tree_from_data(value, budget=None, depth=0):
    budget = budget if budget is not None else [512]
    budget[0] -= 1
    if budget[0] < 0 or depth > 64:
        raise ValueError('AST target exceeds structural bound')
    if isinstance(value, list):
        return [tree_from_data(v, budget, depth + 1) for v in value]
    if isinstance(value, dict):
        if set(value) != {'op', 'fields'} or not isinstance(value['fields'], dict):
            raise ValueError('Invalid AST target')
        cls = getattr(ast, value['op'], None) if isinstance(value['op'], str) else None
        if not isinstance(cls, type) or not issubclass(cls, ast.AST) or set(value['fields']) != set(cls._fields):
            raise ValueError('Unknown AST operator or fields')
        return cls(**{k: tree_from_data(v, budget, depth + 1) for k, v in value['fields'].items()})
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError('Invalid AST literal')


def ast_parameter(text, kind):
    tree = ast.parse(str(text).strip() or 'pass', mode='eval' if kind == 'expr' else 'exec')
    return {'kind': kind, 'ast': tree_data(tree)}


def parameter_source(parameter, kind):
    if parameter.get('kind') != kind:
        raise ValueError('Parameter kind mismatch')
    if kind == 'choice':
        if set(parameter) != {'kind', 'value'} or not isinstance(parameter['value'], str):
            raise ValueError('Invalid choice')
        return parameter['value']
    if set(parameter) != {'kind', 'ast'}:
        raise ValueError('Invalid AST parameter')
    tree = tree_from_data(parameter['ast'])
    if not isinstance(tree, ast.Expression if kind == 'expr' else ast.Module):
        raise ValueError('Wrong AST root')
    return ast.unparse(ast.fix_missing_locations(tree))


def encode(composition, *, method, params, vocabulary_sha256):
    compiled = render.render(composition, method=method, params=params)
    if compiled.nodes > MAX_HOLE_NODES or not set(compiled.families) - {'generic'}:
        raise ValueError('Target requires algorithm-specific structure and <=40 hole AST nodes')
    if composition.get('io', {}).get('mode', 'functional') != 'functional':
        raise ValueError('Initial graph targets require functional IO; stdin is not qualified')
    scope = {name: {'input': i} for i, name in enumerate(params)}
    slots = []
    for i, stage in enumerate(composition['stages']):
        spec = skeletons.SKELETONS[stage['skeleton']]
        bindings = []
        for name in stage.get('inputs', []):
            if name not in scope:
                raise ValueError('Binding refers to unavailable input or future output')
            bindings.append({'name': name, 'source': dict(scope[name])})
        output = stage.get('output') or f'out_{i}'
        if output in scope:
            raise ValueError('Graph target outputs must have unique identities')
        parameters = {}
        for name, hole in spec['holes'].items():
            value = (stage.get('holes') or {}).get(name, hole.get('default'))
            parameters[name] = ({'kind': 'choice', 'value': str(value)} if hole['kind'] == 'choice'
                                else ast_parameter(value, hole['kind']))
        slots.append({'component': stage['skeleton'], 'bindings': bindings,
                      'parameters': parameters, 'output': output})
        scope[output] = {'slot': i}
    slots.extend({'component': 'EMPTY'} for _ in range(render.MAX_STAGES - len(slots)))
    return {'schema': SCHEMA, 'vocabulary_sha256': vocabulary_sha256, 'slots': slots,
            'components': compiled.components, 'answer': ast_parameter(composition['answer'], 'expr')}


def decode(target, *, params, vocabulary_sha256):
    if set(target) != {'schema', 'vocabulary_sha256', 'slots', 'components', 'answer'}:
        raise ValueError('Unknown graph target fields')
    if target['schema'] != SCHEMA or target['vocabulary_sha256'] != vocabulary_sha256:
        raise ValueError('Graph target vocabulary or schema mismatch')
    slots = target['slots']
    if not isinstance(slots, list) or len(slots) != render.MAX_STAGES:
        raise ValueError('Wrong graph slot count')
    scope = {name: {'input': i} for i, name in enumerate(params)}
    stages, empty = [], False
    for i, slot in enumerate(slots):
        if slot.get('component') == 'EMPTY':
            if set(slot) != {'component'}:
                raise ValueError('EMPTY slot carries executable content')
            empty = True
            continue
        if empty or set(slot) != {'component', 'bindings', 'parameters', 'output'}:
            raise ValueError('Invalid active slot or nontrailing EMPTY')
        spec = skeletons.SKELETONS.get(slot['component'])
        if spec is None or set(slot['parameters']) != set(spec['holes']):
            raise ValueError('Unknown component or incomplete parameters')
        inputs = []
        for binding in slot['bindings']:
            name = binding.get('name')
            if set(binding) != {'name', 'source'} or name not in scope or binding['source'] != scope[name]:
                raise ValueError('Invalid input binding')
            inputs.append(name)
        if len(set(inputs)) != len(inputs):
            raise ValueError('Duplicate input binding')
        output = slot['output']
        grammar.check_identifier(output)
        if output in scope:
            raise ValueError('Duplicate graph output')
        stages.append({'skeleton': slot['component'], 'inputs': inputs, 'output': output,
                       'holes': {name: parameter_source(slot['parameters'][name], hole['kind'])
                                 for name, hole in spec['holes'].items()}})
        scope[output] = {'slot': i}
    answer = parameter_source(target['answer'], 'expr')
    if any(isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in scope
           for n in ast.walk(ast.parse(answer, mode='eval'))):
        raise ValueError('Answer references an unavailable graph output')
    return {'stages': stages, 'answer': answer, 'components': target['components']}


def compile_target(target, *, method, params, vocabulary_sha256):
    composition = decode(target, params=params, vocabulary_sha256=vocabulary_sha256)
    compiled = render.render(composition, method=method, params=params)
    if compiled.nodes > MAX_HOLE_NODES or not set(compiled.families) - {'generic'}:
        raise ValueError('Compiled target exceeds the qualified structure bound')
    return compiled


def source_hash(compiled):
    return hashlib.sha256(compiled.source.encode()).hexdigest()
