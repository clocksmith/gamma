"""Selected permitted development targets, authored offline; no runtime teacher.

Each row includes a requirement review and a declared-maximum input probe.
These are training-label proposals until fresh sandbox qualification succeeds.
No protected problem is used here. Selection is not a coverage estimate.
"""
from . import typed_program as ir
from .typed_recipes import assign, branch, call, each, field, invoke, lit, program, pure, ref

PAIRS = ('list', ('tuple', 'int', 'int'))


def histogram(values='nums'):
    return [call('map.new', 'counts'), each('x', ref(values), [
        call('map.get', 'old', ref('counts'), ref('x'), lit(0)),
        call('map.set', 'stored', ref('counts'), ref('x'), pure('add', ref('old'), lit(1))),
    ])]


def proposed():
    rows = []
    def add(uid, tag, graph, complexity, bounds, probe, expected):
        rows.append({'uid': f'lcd:{uid}', 'variant': tag, 'program': graph,
                     'proposer': 'codex-offline-development-author',
                     'requirements': {'complexity_review': complexity, 'declared_input_bounds': bounds,
                                      'unsupported_requirements': [], 'scope': 'selected development problem'},
                     'bound_probe': {'args': probe, 'expected': expected}})
    p = program({'nums': ir.INTS}, [call('map.new', 'counts'), assign('total', lit(0), 'var'),
        each('x', ref('nums'), [call('map.get', 'old', ref('counts'), ref('x'), lit(0)),
            assign('total', pure('add', ref('total'), ref('old')), 'set'),
            call('map.set', 'stored', ref('counts'), ref('x'), pure('add', ref('old'), lit(1)))])], ref('total'), 'int')
    add(1512, 'frequency_map', p, 'O(n) expected time, O(distinct) state; no stricter requirement',
        'n <= 100, values 1..100', [[100]*100], 4950)
    p = program({'nums': ir.INTS}, [assign('prior', pure('empty_ints'), 'var'), assign('total', lit(0), 'var'),
        each('x', ref('nums'), [each('y', ref('prior'), [branch(pure('eq', ref('x'), ref('y')),
            [assign('total', pure('add', ref('total'), lit(1)), 'set')])]),
            assign('prior', pure('append', ref('prior'), ref('x')), 'set')])], ref('total'), 'int')
    add(1512, 'pair_scan', p, 'O(n^2) time, O(n) values; within n <= 100, no stricter requirement',
        'n <= 100, values 1..100', [[100]*100], 4950)
    p = program({'nums': ir.INTS}, [*histogram(), assign('total', lit(0), 'var'), each('x', ref('nums'), [
        call('map.get', 'count', ref('counts'), ref('x'), lit(0)), branch(pure('eq', ref('count'), lit(1)),
            [assign('total', pure('add', ref('total'), ref('x')), 'set')])])], ref('total'), 'int')
    add(1748, 'frequency_map', p, 'O(n) expected time, O(distinct) state; no stricter requirement',
        'n <= 100, values 1..100', [[100]*100], 0)
    p = program({'nums': ir.INTS}, [invoke('stable_unique', 'unique', ref('nums')), assign('total', lit(0), 'var'),
        each('x', ref('unique'), [assign('count', lit(0), 'var'), each('y', ref('nums'), [
            branch(pure('eq', ref('x'), ref('y')), [assign('count', pure('add', ref('count'), lit(1)), 'set')])]),
            branch(pure('eq', ref('count'), lit(1)), [assign('total', pure('add', ref('total'), ref('x')), 'set')])]
        )], ref('total'), 'int')
    add(1748, 'unique_then_count', p, 'O(n^2) time including copied list append; n <= 100, no stricter requirement',
        'n <= 100, values 1..100', [list(range(1,101))], 5050)
    p = program({'nums': ir.INTS}, [*histogram(), assign('best', lit(0), 'var'), assign('total', lit(0), 'var'),
        each('x', ref('nums'), [call('map.get', 'count', ref('counts'), ref('x'), lit(0)),
            branch(pure('lt', ref('best'), ref('count')), [assign('best', ref('count'), 'set')])]),
        each('y', ref('nums'), [call('map.get', 'frequency', ref('counts'), ref('y'), lit(0)),
            branch(pure('eq', ref('frequency'), ref('best')), [assign('total', pure('add', ref('total'), lit(1)), 'set')])])],
        ref('total'), 'int')
    add(3005, 'maximum_frequency', p, 'O(n) expected time, O(distinct) state; no stricter requirement',
        'n <= 100, values 1..100', [[1]*100], 100)
    p = program({'nums': ir.INTS}, [assign('total', pure('len', ref('nums')), 'var'), assign('i', lit(0), 'var'),
        each('x', ref('nums'), [assign('total', pure('sub', pure('add', ref('total'), ref('i')), ref('x')), 'set'),
                              assign('i', pure('add', ref('i'), lit(1)), 'set')])], ref('total'), 'int')
    add(268, 'accumulation', p, 'O(n) graph work and scalar state; runtime copies inputs, so no O(1)-total-space follow-up claim',
        'n <= 10000, distinct values 0..n', [list(range(10000))], 10000)
    p = program({'nums': ir.INTS}, [call('heap.new', 'h'), each('x', ref('nums'), [
        call('heap.push', 'pushed', ref('h'), pure('neg', ref('x')))]),
        call('heap.pop', 'first', ref('h')), call('heap.pop', 'second', ref('h'))],
        pure('mul', pure('sub', pure('neg', ref('first')), lit(1)), pure('sub', pure('neg', ref('second')), lit(1))), 'int')
    add(1464, 'max_heap', p, 'O(n log n) time, O(n) state; no stricter requirement',
        '2 <= n <= 500, values 1..1000', [[1000]*500], 998001)
    p = program({'nums': ir.INTS}, [invoke('heap_sort', 'ordered', ref('nums')),
        assign('previous', lit(0), 'var'), assign('last', lit(0), 'var'), each('x', ref('ordered'), [
            assign('previous', ref('last'), 'set'), assign('last', ref('x'), 'set')])],
        pure('mul', pure('sub', ref('previous'), lit(1)), pure('sub', ref('last'), lit(1))), 'int')
    add(1464, 'sorted_recipe', p, 'O(n^2) due to recipe append copying; n <= 500, no stricter requirement',
        '2 <= n <= 500, values 1..1000', [[1000]*500], 998001)
    p = program({'heights': ir.INTS}, [call('heap.new', 'h'), each('x', ref('heights'), [call('heap.push', 'pushed', ref('h'), ref('x'))]),
        assign('total', lit(0), 'var'), each('x', ref('heights'), [call('heap.pop', 'expected', ref('h')),
            branch(pure('not', pure('eq', ref('x'), ref('expected'))), [assign('total', pure('add', ref('total'), lit(1)), 'set')])])],
        ref('total'), 'int')
    add(1051, 'heap_compare', p, 'O(n log n) time, O(n) state; input preserved', 'n <= 100, values 1..100', [list(range(100,0,-1))], 100)
    p = program({'stones': ir.INTS}, [call('heap.new', 'h'), each('x', ref('stones'), [call('heap.push', 'pushed', ref('h'), pure('neg', ref('x')))]),
        assign('count', pure('len', ref('stones')), 'var'), assign('answer', lit(0), 'var'),
        each('unused', ref('stones'), [branch(pure('lt', lit(1), ref('count')), [
            call('heap.pop', 'heavy', ref('h')), call('heap.pop', 'light', ref('h')),
            assign('count', pure('sub', ref('count'), lit(2)), 'set'),
            branch(pure('not', pure('eq', ref('heavy'), ref('light'))), [
                call('heap.push', 'returned', ref('h'), pure('sub', ref('heavy'), ref('light'))),
                assign('count', pure('add', ref('count'), lit(1)), 'set')])])]),
        branch(pure('eq', ref('count'), lit(1)), [call('heap.pop', 'remaining', ref('h')),
            assign('answer', pure('neg', ref('remaining')), 'set')])], ref('answer'), 'int')
    add(1046, 'heap_state_machine', p, 'O(n log n) time, O(n) state; at most n iterations',
        'n <= 30, weights 1..1000', [[1000]*30], 0)
    p = program({'cost': ir.INTS}, [call('heap.new', 'h'), each('x', ref('cost'), [call('heap.push', 'pushed', ref('h'), pure('neg', ref('x')))]),
        assign('position', lit(0), 'var'), assign('total', lit(0), 'var'), each('unused', ref('cost'), [
            call('heap.pop', 'next', ref('h')), branch(pure('lt', ref('position'), lit(2)), [
                assign('total', pure('sub', ref('total'), ref('next')), 'set')]),
            assign('position', pure('add', ref('position'), lit(1)), 'set'),
            branch(pure('eq', ref('position'), lit(3)), [assign('position', lit(0), 'set')])])], ref('total'), 'int')
    add(2144, 'heap_grouping', p, 'O(n log n) time, O(n) state', 'n <= 100, costs 1..100', [[100]*100], 6700)
    p = program({'boxTypes': PAIRS, 'truckSize': 'int'}, [
        assign('ordered', pure('sort_by', ref('boxTypes'), lit(1), lit(True))),
        assign('remaining', ref('truckSize'), 'var'), assign('total', lit(0), 'var'),
        each('box', ref('ordered'), [assign('taken', field(ref('box'),0), 'var'),
            branch(pure('lt', ref('remaining'), ref('taken')), [assign('taken', ref('remaining'), 'set')]),
            assign('total', pure('add', ref('total'), pure('mul', ref('taken'), field(ref('box'),1))), 'set'),
            assign('remaining', pure('sub', ref('remaining'), ref('taken')), 'set')])], ref('total'), 'int')
    add(1710, 'sort_capacity', p, 'O(n log n) time, O(n) sorted values',
        'n <= 1000, counts/units <= 1000, truckSize <= 1000000', [[[1000,1000]]*1000,1000000], 1000000000)
    p = program({'n': 'int', 'edges': PAIRS}, [call('dsu.new', 'sets', ref('n')), assign('count', ref('n'), 'var'),
        each('edge', ref('edges'), [call('dsu.union', 'joined', ref('sets'), field(ref('edge'),0), field(ref('edge'),1)),
            branch(ref('joined'), [assign('count', pure('sub', ref('count'), lit(1)), 'set')])])], ref('count'), 'int')
    edges = [[i,i+1] for i in range(1999)]
    edges += [[a,b] for a in range(3) for b in range(a+2,2000)][:5000-len(edges)]
    add(323, 'union_count', p, 'O((n+m) log n) upper bound, O(n) DSU state',
        'n <= 2000, m <= 5000', [2000,edges], 1)
    p = program({'edges': PAIRS}, [call('dsu.new', 'sets', pure('add', pure('len', ref('edges')), lit(1))),
        assign('answer', pure('empty_ints'), 'var'), each('edge', ref('edges'), [
            call('dsu.union', 'joined', ref('sets'), field(ref('edge'),0), field(ref('edge'),1)),
            branch(pure('not', ref('joined')), [assign('answer', pure('append', pure('append', pure('empty_ints'),
                field(ref('edge'),0)), field(ref('edge'),1)), 'set')])])], ref('answer'), ir.INTS)
    add(684, 'last_rejected_edge', p, 'O(n log n) upper bound, O(n) DSU state; last rejected edge retained',
        'n <= 1000, endpoints 1..n', [[[i,i+1] for i in range(1,1000)]+[[1,1000]]], [1,1000])
    for alternative in (False, True):
        # Vertex zero is explicitly unused. Thus a connected 1-based graph has
        # two components in n+1 DSU slots. No external adapter rewrites inputs.
        body = [invoke('forest', 'forest', pure('add', ref('n'), lit(1)), ref('connections'), lit(False)),
                assign('answer', lit(-1), 'var')]
        if alternative:
            body += [invoke('cycle_weight', 'rejected', pure('add', ref('n'), lit(1)), ref('connections'), lit(False)),
                     assign('weight', lit(0), 'var'), each('edge', ref('connections'), [
                         assign('weight', pure('add', ref('weight'), field(ref('edge'),2)), 'set')])]
            cost = pure('sub', ref('weight'), ref('rejected'))
        else:
            cost = field(ref('forest'),0)
        body += [branch(pure('eq', field(ref('forest'),1), lit(2)), [assign('answer', cost, 'set')])]
        p = program({'n': 'int', 'connections': ir.EDGES}, body, ref('answer'), 'int')
        add(1135, 'removed_weight' if alternative else 'forest_recipe', p,
            'O(m log m + m log n) time, O(n+m) state; unused vertex zero accounted for explicitly',
            'n <= 10000, m <= 10000, 1-based vertices; n+1 DSU slots <= 20000',
            [10000,[[i,i+1,1] for i in range(1,10000)]+[[1,10000,1]]], 9999)
    return rows


def unsupported():
    return [
        {'uid': 'lcd:136', 'reason': 'required_complexity',
         'detail': 'Set-based decomposition violates mandatory constant extra space; no admitted XOR primitive.'},
        {'uid': 'lcd:287', 'reason': 'required_complexity_and_missing_operations',
         'detail': 'Map-based decomposition violates mandatory constant extra space; cycle traversal needs collection indexing.'},
        {'uid': 'lcd:912', 'reason': 'required_complexity',
         'detail': 'Current heap_sort recipe copies output on append (quadratic); cannot qualify required O(n log n).'},
        {'uid': 'lcd:1971', 'reason': 'runtime_input_bounds',
         'detail': 'Declared n and edges reach 200000; frozen resource/collection bound is 20000.'},
    ]
