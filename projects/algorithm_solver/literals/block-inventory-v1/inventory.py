"""Inventory complete Python AST blocks as conditional contract proposals.

Source is parsed, never executed. Matching shapes do not establish equivalence.
The existing authoring catalog owns source/contract identity and path validation.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

CATALOG_SHA = 'c0c2880039759734b59cc00ddc2660e6f7b841218c48e0010941e46cbf59f3ef'
SCHEMA = 'gamma.source-bound-block-inventory.v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value).encode()).hexdigest()


def same(left, right):
    return ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False)


def name(node):
    return node.id if isinstance(node, ast.Name) else None


def integer(node, value):
    return isinstance(node, ast.Constant) and type(node.value) is int and node.value == value


def assignment(node):
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.targets[0], node.value
    return None, None


def append(node):
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if (isinstance(call.func, ast.Attribute) and call.func.attr == 'append'
            and len(call.args) == 1 and not call.keywords):
        return call.func.value, call.args[0]
    return None


def subscript(node):
    if isinstance(node, ast.Subscript) and name(node.value):
        return node.value.id, node.slice
    return None


def increment(node):
    return isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add) and integer(node.value, 1)


def lists_in_scope(fn):
    """Yield each statement list once; nested callable/class scopes are excluded."""
    def visit(node, context):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list) and value and all(isinstance(x, ast.stmt) for x in value):
                yield value, context + [type(node).__name__ + '.' + field]
            children = value if isinstance(value, list) else [value]
            for child in children:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue
                if isinstance(child, ast.AST):
                    yield from visit(child, context + [type(node).__name__ + '.' + field])
    yield from visit(fn, [])


COMMON = {
    'status': 'conditional proposal; not verified against enclosing source contract',
    'assumptions': [
        'Referenced built-ins and container methods have their standard behavior; no subclass or monkey patch effects.',
        'Expression evaluation and exception behavior remain source-specific; unknown calls and aliases require review.',
        'No concurrent mutation. Control-flow reachability and caller obligations are not inferred.',
    ],
    'qualification_needed': [
        'Bind types, bounds, numeric domain, aliases and effects to this exact source and problem contract.',
        'Independently test the component contract and every rewritten whole-program variant before qualification.',
        'Review binding hygiene, exception paths and dependency closure before parameterized composition.',
    ],
}

CONTRACTS = {
    'dense_counter_init': dict(family='counting', inputs=['size'], outputs=['counter'],
        effects=['Bind a fresh zero-filled list; no input container mutation.'],
        domain=['size is a nonnegative built-in integer; allocation fits resources.'],
        dependencies=['built-in list repetition'], complexity='O(size) time and storage'),
    'dense_counter_increment': dict(family='counting', inputs=['counter', 'index'], outputs=['counter'],
        effects=['Read and increment exactly one indexed cell; existing aliases observe the mutation.'],
        domain=['counter is a list of nonnegative integers; 0 <= index < len(counter).',
                'Index expression is stable and has no side effects; language numeric limits remain explicit.'],
        dependencies=['built-in list indexing; integer addition'], complexity='O(1) container operations; arithmetic cost depends on integer size'),
    'sparse_counter_init': dict(family='counting', inputs=[], outputs=['counter'],
        effects=['Bind a fresh empty dictionary.'], domain=['No existing alias to the newly allocated dictionary.'],
        dependencies=['built-in dict'], complexity='O(1) allocation'),
    'sparse_counter_increment': dict(family='counting', inputs=['counter', 'key'], outputs=['counter'],
        effects=['Read default zero without insertion, then set only that key to the old count plus one.'],
        domain=['counter is a built-in dictionary of nonnegative integer counts.',
                'key is hashable with stable, side-effect-free equality/hash; repeated key expression is stable.',
                'This is not a dense bounded-array implementation, and iteration order remains observable.'],
        dependencies=['dict.get; dict.__setitem__; integer addition'], complexity='Expected O(1) dictionary operations; key/arithmetic costs excluded'),
    'queue_read_advance': dict(family='head_index_queue', inputs=['queue', 'head'], outputs=['item', 'head'],
        effects=['Bind the indexed element and advance head by one; do not remove or copy the element.'],
        domain=['queue is a built-in list; head is an integer with 0 <= head < len(queue).',
                'Returned item may alias the element; consumed prefix remains allocated.',
                'Queue/head/item bindings must be distinct; the caller maintains queue discipline.'],
        dependencies=['built-in list indexing; integer addition'], complexity='O(1) container operations; consumed storage retained'),
    'queue_init': dict(family='head_index_queue', inputs=['initial_elements'], outputs=['queue'],
        effects=['Bind a fresh list; contained mutable elements may alias inputs.'],
        domain=['Elements evaluated left-to-right; their effects require source review.'],
        dependencies=['list construction'], complexity='O(number of initial elements)'),
    'queue_head_init': dict(family='head_index_queue', inputs=[], outputs=['head'],
        effects=['Bind head to zero.'], domain=['Must refer to the intended queue, whose consumed prefix is empty.'],
        dependencies=['integer zero'], complexity='O(1)'),
    'queue_append': dict(family='head_index_queue', inputs=['queue', 'item'], outputs=['queue'],
        effects=['Append one element; aliases observe mutation; no copy of the element.'],
        domain=['queue is a built-in list; item evaluation effects and memory bound need review.'],
        dependencies=['list.append'], complexity='Amortized O(1) container operation; resizing may allocate'),
    'adjacency_init': dict(family='adjacency', inputs=['size'], outputs=['adjacency', 'loop_index'],
        effects=['Bind a fresh outer list and append a fresh empty bucket each iteration.',
                 'Loop index is assigned if size > 0; otherwise its previous binding is unchanged.'],
        domain=['size is a nonnegative integer and allocation fits resources; buckets are distinct.'],
        dependencies=['built-in range; list.append'], complexity='O(size) time and storage'),
    'arc_unweighted': dict(family='adjacency', inputs=['adjacency', 'source_vertex', 'target_vertex'], outputs=['adjacency'],
        effects=['Append one target to one bucket; duplicates and insertion order are preserved.'],
        domain=['Adjacency is a list of lists; endpoints are in-range integer vertex IDs.',
                'This inserts one directed arc, not proof that the enclosing graph is directed.'],
        dependencies=['list indexing; list.append'], complexity='Amortized O(1) container operation'),
    'arc_weighted': dict(family='adjacency', inputs=['adjacency', 'source_vertex', 'target_vertex', 'weight'], outputs=['adjacency'],
        effects=['Append a fresh [target, weight] list to one bucket; duplicate arcs/order preserved.'],
        domain=['Adjacency is a list of lists; endpoints are in-range integer IDs.',
                'Weight type/range/sign are source-specific; no nonnegative-weight algorithm guarantee.'],
        dependencies=['list indexing; construction; append'], complexity='Amortized O(1) container operation'),
    'edge_unweighted_pair': dict(family='adjacency', inputs=['adjacency', 'left_vertex', 'right_vertex'], outputs=['adjacency'],
        effects=['Append both orientations in source order; self-loops append twice and duplicates persist.'],
        domain=['Distinct adjacency buckets, in-range integer endpoints, stable side-effect-free expressions.',
                'Both appends must complete; there is no transactional rollback on failure.'],
        dependencies=['two ordered list.append operations'], complexity='Amortized O(1) container operations'),
    'edge_weighted_pair': dict(family='adjacency', inputs=['adjacency', 'left_vertex', 'right_vertex', 'weight'], outputs=['adjacency'],
        effects=['Append fresh [neighbor, weight] lists in both orientations; duplicates/order preserved.'],
        domain=['Distinct buckets, in-range integer endpoints; weight domain remains unverified.',
                'Repeated endpoint/weight expressions are stable and side-effect-free; no transactional rollback.'],
        dependencies=['two ordered list constructions/appends'], complexity='Amortized O(1) container operations'),
}


def matches(fn):
    bodies = list(lists_in_scope(fn))
    flat = [node for body, _ in bodies for node in body]
    dense = {subscript(n.target)[0] for n in flat if increment(n) and subscript(n.target)}
    queues, heads = set(), set()
    for body, context in bodies:
        for left, right in zip(body, body[1:]):
            target, value = assignment(left)
            indexed = subscript(value)
            if (name(target) and indexed and name(indexed[1]) and increment(right)
                    and name(right.target) == name(indexed[1])
                    and len({name(target), indexed[0], name(indexed[1])}) == 3):
                queues.add(indexed[0]); heads.add(name(indexed[1]))
                yield 'queue_read_advance', [left, right], context, {'queue': indexed[0], 'head': name(indexed[1]), 'item': name(target)}
            receiver, initial = assignment(left)
            if (name(receiver) and isinstance(initial, ast.List) and not initial.elts
                    and isinstance(right, ast.For) and not right.orelse and name(right.target)
                    and isinstance(right.iter, ast.Call) and name(right.iter.func) == 'range'
                    and len(right.iter.args) == 1 and not right.iter.keywords and len(right.body) == 1):
                call = append(right.body[0])
                if call and name(call[0]) == name(receiver) and isinstance(call[1], ast.List) and not call[1].elts and name(right.target) != name(receiver):
                    yield 'adjacency_init', [left, right], context, {'adjacency': name(receiver), 'size': ast.unparse(right.iter.args[0]), 'loop_index': name(right.target)}
            first, second = append(left), append(right)
            if first and second:
                a, b = subscript(first[0]), subscript(second[0])
                if a and b and a[0] == b[0]:
                    x, y = first[1], second[1]
                    weighted = isinstance(x, ast.List) and isinstance(y, ast.List) and len(x.elts) == len(y.elts) == 2
                    if weighted:
                        tx, ty = x.elts[0], y.elts[0]
                        weight_ok = same(x.elts[1], y.elts[1])
                    else:
                        tx, ty, weight_ok = x, y, not isinstance(x, (ast.List, ast.Tuple)) and not isinstance(y, (ast.List, ast.Tuple))
                    if same(a[1], ty) and same(b[1], tx) and weight_ok:
                        roles = {'adjacency': a[0], 'left_vertex': ast.unparse(a[1]), 'right_vertex': ast.unparse(b[1])}
                        if weighted: roles['weight'] = ast.unparse(x.elts[1])
                        yield 'edge_weighted_pair' if weighted else 'edge_unweighted_pair', [left, right], context, roles
    for body, context in bodies:
        for node in body:
            target, value = assignment(node)
            if name(target):
                key = name(target)
                if key in dense and isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mult) and isinstance(value.left, ast.List) and len(value.left.elts) == 1 and integer(value.left.elts[0], 0):
                    yield 'dense_counter_init', [node], context, {'counter': key, 'size': ast.unparse(value.right)}
                if isinstance(value, ast.Dict) and not value.keys:
                    yield 'sparse_counter_init', [node], context, {'counter': key}
                if key in queues and isinstance(value, ast.List):
                    yield 'queue_init', [node], context, {'queue': key, 'initial_elements': ast.unparse(value)}
                if key in heads and integer(value, 0):
                    yield 'queue_head_init', [node], context, {'head': key}
            if increment(node) and subscript(node.target):
                container, index = subscript(node.target)
                # An actual same-scope zero-filled list initializer is required.
                initializers = [assignment(n) for n in flat]
                if any(name(t) == container and isinstance(v, ast.BinOp) and isinstance(v.op, ast.Mult) and isinstance(v.left, ast.List) and len(v.left.elts) == 1 and integer(v.left.elts[0], 0) for t, v in initializers):
                    yield 'dense_counter_increment', [node], context, {'counter': container, 'index': ast.unparse(index)}
            indexed = subscript(target)
            if indexed and isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add) and integer(value.right, 1):
                call = value.left
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'get'
                        and name(call.func.value) == indexed[0] and len(call.args) == 2 and not call.keywords
                        and same(call.args[0], indexed[1]) and integer(call.args[1], 0)):
                    yield 'sparse_counter_increment', [node], context, {'counter': indexed[0], 'key': ast.unparse(indexed[1])}
            call = append(node)
            if not call: continue
            receiver, item = call
            if name(receiver) in queues:
                yield 'queue_append', [node], context, {'queue': name(receiver), 'item': ast.unparse(item)}
            indexed = subscript(receiver)
            if indexed:
                weighted = isinstance(item, ast.List) and len(item.elts) == 2
                if isinstance(item, (ast.List, ast.Tuple)) and not weighted: continue
                roles = {'adjacency': indexed[0], 'source_vertex': ast.unparse(indexed[1]), 'target_vertex': ast.unparse(item.elts[0] if weighted else item)}
                if weighted: roles['weight'] = ast.unparse(item.elts[1])
                yield 'arc_weighted' if weighted else 'arc_unweighted', [node], context, roles


def shape(nodes):
    """Proposal key only: constants/attributes/operators stay; names become slots."""
    slots = {}
    class Rename(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in {'range', 'len', 'ord'}:
                return node
            slots.setdefault(node.id, 'slot_' + str(len(slots)))
            return ast.copy_location(ast.Name(id=slots[node.id], ctx=node.ctx), node)
    tree = Rename().visit(copy.deepcopy(ast.Module(body=nodes, type_ignores=[])))
    return ast.dump(tree, include_attributes=False), slots


def occurrences(raw, identity):
    if digest(raw) != identity['source_sha256'] or identity['language'] != 'python':
        raise ValueError('Source identity mismatch')
    text = raw.decode('utf-8')
    tree = ast.parse(text)
    starts, offset = [], 0
    for line in raw.splitlines(keepends=True):
        starts.append(offset); offset += len(line)
    result = []
    # Nested callables are separate scopes; no matching across scope boundaries.
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
        for operation, nodes, context, roles in matches(fn):
            # A first-occurrence name map is not binder-aware. Fail closed on
            # nested expression scopes rather than merging captures with locals.
            scopes = (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp,
                      ast.GeneratorExp, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            if any(isinstance(n, scopes) for node in nodes for n in ast.walk(node)):
                continue
            first, last = nodes[0], nodes[-1]
            start = starts[first.lineno - 1] + first.col_offset
            end = starts[last.end_lineno - 1] + last.end_col_offset
            literal = raw[start:end].decode('utf-8')
            structure, slots = shape(nodes)
            contract = {**COMMON, **CONTRACTS[operation]}
            contract_id = 'contract-v1:' + digest({'operation': operation, 'contract': contract})
            literal_id = 'literal-v1:' + digest({'language': 'python', 'literal': literal})
            macro_id = 'macro-proposal-v1:' + digest({'language': 'python', 'operation': operation, 'contract_id': contract_id, 'shape': structure})
            loads = sorted({n.id for node in nodes for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)})
            writes = sorted({n.id for node in nodes for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)})
            # AugAssign(Name) also reads its old value, which AST marks Store.
            read_modify = {n.target.id for node in nodes for n in ast.walk(node) if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name)}
            calls = sorted({ast.unparse(n.func) for node in nodes for n in ast.walk(node) if isinstance(n, ast.Call)})
            occurrence_id = 'occurrence-v1:' + digest({'variant_id': identity['variant_id'], 'start_byte': start, 'end_byte': end, 'operation': operation})
            result.append({'occurrence_id': occurrence_id, 'operation': operation, 'family': CONTRACTS[operation]['family'],
                'literal_id': literal_id, 'macro_proposal_id': macro_id, 'contract_id': contract_id,
                'literal': literal, 'literal_utf8_bytes': end - start, 'shape': structure, 'slots': slots, 'roles': roles,
                'span': {'start_byte': start, 'end_byte': end, 'start_line': first.lineno, 'end_line': last.end_lineno,
                         'node_types': [type(n).__name__ for n in nodes]},
                'context': {'function': fn.name, 'function_line': fn.lineno, 'ancestors': context,
                            'leading_bytes_not_in_literal': raw[starts[first.lineno-1]:start].decode('utf-8')},
                'bindings': {'syntactic_reads': sorted(set(loads) | read_modify), 'syntactic_writes': writes,
                             'calls_needing_resolution': calls, 'liveness': 'not inferred; outputs are writes/effects, not proven live-out'},
                'contract': contract, 'provenance': identity,
                'qualification': 'unknown; source-as-data only',
                'encoding': {'literal': 'exact span only; surrounding bytes must also be encoded',
                             'macro': 'proposal only; bindings/constants/control/dependencies are not free and no cost is claimed'}})
    return sorted(result, key=lambda row: (row['span']['start_byte'], row['span']['end_byte'], row['operation']))


def build(rows):
    witnesses = []
    identities = set()
    for raw, identity in rows:
        if identity['variant_id'] in identities:
            raise ValueError('Duplicate variant ID')
        identities.add(identity['variant_id'])
        witnesses.extend(occurrences(raw, identity))
    witnesses.sort(key=lambda r: (r['provenance']['problem_id'], r['provenance']['variant_id'], r['span']['start_byte'], r['operation']))
    operations = {}
    for operation in CONTRACTS:
        matches_ = [r for r in witnesses if r['operation'] == operation]
        operations[operation] = {'occurrences': len(matches_), 'problems': len({r['provenance']['problem_id'] for r in matches_}),
            'literal_ids': len({r['literal_id'] for r in matches_}), 'macro_proposal_ids': len({r['macro_proposal_id'] for r in matches_})}
    return {'schema': SCHEMA, 'language': 'python', 'source_variants': len(identities), 'occurrences': witnesses,
            'operations': operations, 'candidate_executions': 0, 'new_qualifications': 0, 'admissions': 0,
            'coverage': None, 'encoded_bits': None, 'semantic_equivalence': 'not established',
            'data_role': 'explicitly supplied development source-as-data; not protected evaluation'}


def load_sources(manifests, catalog_path):
    if digest(catalog_path.read_bytes()) != CATALOG_SHA:
        raise ValueError('Authoring catalog implementation identity changed')
    spec = importlib.util.spec_from_file_location('block_inventory_authoring_catalog', catalog_path)
    catalog = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(catalog)
    document = catalog.build(manifests)
    roots = {digest(path.read_bytes()): path.parent for path in manifests}
    rows = []
    for identity in document['variants']:
        if identity['qualification']['status'] != 'unknown':
            raise ValueError('Unexpected source qualification')
        if identity['language'] != 'python': continue
        origin = identity['provenance'][0]
        raw = catalog.read_pinned(roots[origin['manifest_sha256']], origin['source_path'], identity['source_sha256'])
        rows.append((raw, identity))
    return rows, document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', action='append', required=True, type=Path)
    parser.add_argument('--catalog-module', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists(): raise ValueError('Refusing to overwrite output')
    rows, catalog = load_sources(args.manifest, args.catalog_module)
    result = build(rows)
    result['inputs'] = {'manifest_sha256': sorted(digest(p.read_bytes()) for p in args.manifest),
        'catalog_sha256': digest(catalog), 'catalog_module_sha256': CATALOG_SHA,
        'inventory_code_sha256': digest(Path(__file__).read_bytes())}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'inventory.json').write_text(canonical(result)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: value for key, value in result.items() if key not in {'occurrences','inputs'}}, indent=2))


if __name__ == '__main__':
    main()
