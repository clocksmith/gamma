"""Hand-authored development fixtures; no protected tasks or learned predictions.

Builders only construct JSON. All computation, including conditions and updates,
is represented in the typed graph. Changing recipe structure is inspectable.
"""
import json

from .typed_program import SCHEMA, INTS, EDGES


def ref(name): return {'ref': name}
def lit(value): return {'literal': value}
def pure(op, *args): return {'op': op, 'args': list(args)}
def field(value, index): return pure('field', value, lit(index))
def assign(name, value, op='let'): return {'op': op, 'name': name, 'value': value}
def call(operator, out, *args): return {'op': 'call', 'operator': operator, 'args': list(args), 'out': out}
def each(item, values, body): return {'op': 'for', 'item': item, 'in': values, 'body': body}
def branch(condition, yes, no=()): return {'op': 'if', 'condition': condition, 'then': yes, 'else': list(no)}
def invoke(recipe, out, *args): return {'op': 'recipe', 'recipe': recipe, 'args': list(args), 'out': out}


def program(inputs, body, answer, output):
    return json.loads(json.dumps({'schema': SCHEMA, 'inputs': inputs, 'body': body,
                                 'return': answer, 'output_type': output}))


def forest_recipe():
    """Kruskal expanded: sort, project, find, compare, join, accumulate.

    Supports disconnected graphs (forest), signed weights, parallel/self edges.
    descending chooses maximum instead of minimum forest. No opaque MST call.
    """
    return program({'n': 'int', 'edges': EDGES, 'descending': 'bool'}, [
        call('dsu.new', 'sets', ref('n')),
        assign('ordered', pure('sort_by', ref('edges'), lit(2), ref('descending'))),
        assign('total', lit(0), 'var'),
        assign('accepted', lit(0), 'var'),
        each('edge', ref('ordered'), [
            assign('u', field(ref('edge'), 0)),
            assign('v', field(ref('edge'), 1)),
            assign('weight', field(ref('edge'), 2)),
            call('dsu.find', 'left', ref('sets'), ref('u')),
            call('dsu.find', 'right', ref('sets'), ref('v')),
            branch(pure('not', pure('eq', ref('left'), ref('right'))), [
                call('dsu.union', 'joined', ref('sets'), ref('u'), ref('v')),
                assign('total', pure('add', ref('total'), ref('weight')), 'set'),
                assign('accepted', pure('add', ref('accepted'), lit(1)), 'set'),
            ]),
        ]),
    ], pure('tuple', ref('total'), pure('sub', ref('n'), ref('accepted'))), ('tuple', 'int', 'int'))


def cycle_weight_recipe():
    """Different wiring: join first; sum rejected edges, not accepted edges."""
    return program({'n': 'int', 'edges': EDGES, 'descending': 'bool'}, [
        call('dsu.new', 'sets', ref('n')),
        assign('ordered', pure('sort_by', ref('edges'), lit(2), ref('descending'))),
        assign('total', lit(0), 'var'),
        each('edge', ref('ordered'), [
            assign('u', field(ref('edge'), 0)),
            assign('v', field(ref('edge'), 1)),
            assign('weight', field(ref('edge'), 2)),
            call('dsu.union', 'joined', ref('sets'), ref('u'), ref('v')),
            branch(pure('not', ref('joined')), [
                assign('total', pure('add', ref('total'), ref('weight')), 'set'),
            ]),
        ]),
    ], ref('total'), 'int')


def heap_sort_recipe():
    return program({'values': INTS}, [
        call('heap.new', 'heap'),
        each('value', ref('values'), [call('heap.push', 'pushed', ref('heap'), ref('value'))]),
        assign('answer', pure('empty_ints'), 'var'),
        each('unused', ref('values'), [
            call('heap.pop', 'smallest', ref('heap')),
            assign('answer', pure('append', ref('answer'), ref('smallest')), 'set'),
        ]),
    ], ref('answer'), INTS)


def stable_unique_recipe():
    return program({'values': INTS}, [
        call('map.new', 'seen'),
        call('queue.new', 'queue'),
        each('value', ref('values'), [
            call('map.has', 'present', ref('seen'), ref('value')),
            branch(pure('not', ref('present')), [
                call('map.set', 'recorded', ref('seen'), ref('value'), lit(1)),
                call('queue.push', 'queued', ref('queue'), ref('value')),
            ]),
        ]),
        call('queue.size', 'count', ref('queue')),
        assign('answer', pure('empty_ints'), 'var'),
        each('unused', pure('range', ref('count')), [
            call('queue.pop', 'first', ref('queue')),
            assign('answer', pure('append', ref('answer'), ref('first')), 'set'),
        ]),
    ], ref('answer'), INTS)


def catalog():
    return {'forest': forest_recipe(), 'cycle_weight': cycle_weight_recipe(),
            'heap_sort': heap_sort_recipe(), 'stable_unique': stable_unique_recipe()}


def fixtures():
    result = {}
    for key, descending, slot in [('minimum_forest', False, 0), ('maximum_forest', True, 0),
                                  ('component_count', False, 1)]:
        result[key] = program({'n': 'int', 'edges': EDGES}, [
            invoke('forest', 'result', ref('n'), ref('edges'), lit(descending)),
        ], field(ref('result'), slot), 'int')
    result['rejected_edge_weight'] = program({'n': 'int', 'edges': EDGES}, [
        invoke('cycle_weight', 'result', ref('n'), ref('edges'), lit(False)),
    ], ref('result'), 'int')
    for key in ('heap_sort', 'stable_unique'):
        result[key] = program({'values': INTS}, [invoke(key, 'result', ref('values'))], ref('result'), INTS)
    result['sorted_unique'] = program({'values': INTS}, [
        invoke('stable_unique', 'unique', ref('values')),
        invoke('heap_sort', 'sorted', ref('unique')),
    ], ref('sorted'), INTS)
    # Same parts, reverse connections. Same value output on integer lists; tests
    # should accept this equivalent graph rather than enforce a preferred target.
    result['unique_sorted'] = program({'values': INTS}, [
        invoke('heap_sort', 'sorted', ref('values')),
        invoke('stable_unique', 'unique', ref('sorted')),
    ], ref('unique'), INTS)
    return result


def negative_fixtures():
    """Plausible mistakes paired with explicit counterexamples, not fake labels."""
    wrong_condition = forest_recipe()
    condition = wrong_condition['body'][-1]['body'][-1]
    condition['condition'] = condition['condition']['args'][0]  # join already-connected roots
    wrong_field = forest_recipe()
    wrong_field['body'][-1]['body'][2]['value']['args'][1] = lit(0)  # accumulate endpoint, not weight
    return [
        ('reversed_join_condition', wrong_condition, {'n': 2, 'edges': [[0, 1, 7]], 'descending': False}, (7, 1)),
        ('endpoint_instead_of_weight', wrong_field, {'n': 2, 'edges': [[0, 1, 7]], 'descending': False}, (7, 1)),
    ]
