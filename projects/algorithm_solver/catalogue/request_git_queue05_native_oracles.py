"""Public-spec state-machine traces, not a native candidate adapter.

The existing [operations, arguments] oracle wire has no actual solve binding.
No candidate sources are loaded or executed. Persistent observation is unresolved.
"""
from collections import Counter
from itertools import product
import hashlib
import json
import random
import re

from . import imported_qualification as q

IDS = (2502, 2526, 2642, 2671)
CLASSES = {2502: 'Allocator', 2526: 'DataStream', 2642: 'Graph', 2671: 'FrequencyTracker'}
TITLES = {2502: 'Design Memory Allocator', 2526: 'Find Consecutive Integers from a Data Stream',
          2642: 'Design Graph With Shortest Path Calculator', 2671: 'Frequency Tracker'}
STATEMENT_SHA256 = {
    2502: 'c42f637813cd499c19468640f4c83e7a405f2ddc7794c7c5881fc6c7b1f6bfcd',
    2526: '0cdacf98f5d75338cc2a7cadd2d5c27cbeebae5c92f500d9ce1e2d6c15fd4a1d',
    2642: '39e6bde73335e8364c3d584390cbdcc26e0e6204ef01d1696dad5f9dc1e4337f',
    2671: '49e2c8d4dde5ff937d92cef7f127c7e00b3401b87a662792008b7a2b7df92d20',
}
CASE_COUNT = {2502: 2407, 2526: 1085, 2642: 795, 2671: 1640}
CASES_SHA256 = {2502: '84501442c66e1d9e38b91783889773ae0b327019ec692142b14dfa7398bc14d9',
                2526: 'b65e0285e3fed838416871afda756b8597c204927223fe2ad38f6da5e3f23337',
                2642: '62f05ec3105f414ba27d0245c57b1fd8095efc35637956a9862a8c11d344e0d6',
                2671: 'acacd15f45d7466873357807e46d1fd4abc8661033d69c648a179e806b5643cb'}
CONSTRUCTOR_PARAMETERS = {2502: ('n',), 2526: ('value', 'k'), 2642: ('n', 'edges'), 2671: ()}
METHODS = {2502: {'allocate': ('size', 'mID'), 'freeMemory': ('mID',)},
           2526: {'consec': ('num',)}, 2642: {'addEdge': ('edge',), 'shortestPath': ('node1', 'node2')},
           2671: {'add': ('number',), 'deleteOne': ('number',), 'hasFrequency': ('frequency',)}}
MAX_CALLS = {2502: 1000, 2526: 100000, 2642: 200, 2671: 200000}
COMMON_CONTRACT = {
    'wire': 'Existing queue02/03 [operations,arguments] semantic-only wire, one constructor at index0; constructor and void results are null. No source solve wrapper or actual export/method binding is claimed.',
    'effects': 'Prescribed state evolution, leftmost allocation, failed allocation no-op, absent deletion no-op and directed edge insertion are semantic obligations. Caller argument preservation, receiver/method dispatch, result aliases, persistent instance isolation, external IO and internal snapshots require a later independent native observer policy.',
    'numeric': 'Exact integers exclude bool and float. Boolean results remain bool, void results remain null. Largest graph result is 99*1000000; counts stay <=200000. No unsafe integer values.',
    'complexity': 'Complete validators admit all official shapes. Literal reference budgets are separate. Analytic maximum families do not establish candidate time, space, or resource compliance.',
    'transport': 'Reuse unchanged q.encoded, q.batches, q.MAX_PACKET1100000, q.MAX_FILE8388608 and q.LIMITS. Packet accounting is semantic-wire accounting only, not a native projection approval.',
    'status': 'Exposed-development semantic traces, not fresh holdout, source review, native interface qualification, execution or promotion.',
}
CONTRACTS = {
    2502: 'n,size,mID exact1..1000; at most1000 methods. Same ID can own multiple blocks. Allocate leftmost consecutive free cells or-1; freeMemory frees every matching cell and returns count. Literal n<=30,calls<=100; O(calls*n*size) time/O(n) state.',
    2526: 'value,num1..1e9,k1..100000; at most100000 consec methods. Append then test lastk exact target values, false before k entries. Literal history slices with calls<=100, O(calls*k) time/O(calls) state.',
    2642: 'n1..100; initial0..n(n-1) directed edges, unique ordered endpoints and no selfloops; cost1..1e6. At most100 addEdge and100 shortestPath methods, no duplicate edge at any time. Nonnegative shortest cost,0 for same node,-1 unreachable. Literal Bellman-Ford n<=12,initialedges<=100,calls<=100; O(queries*n*edges) time/O(n+edges) state.',
    2671: 'number,frequency1..100000; at most200000 methods. add one,deleteOne one if present,hasFrequency asks whether any distinct number occurs exactly frequency times. Zero frequency is outside domain. Literal list calls<=100; O(calls^3) worst-case time/O(calls) state.',
}
OMITTED_MAXIMUM_SHAPES = {
    2502: 'Arbitrary maximum allocator histories omitted; selected full1000-slot and1000-call analytic fill/free/failure families retained.',
    2526: 'A full100000-call even minimum-size consec trace exceeds unchanged packet cap. Retain70000-call constant/reset families, maximal k100000 and maximal values separately. Full-domain validator remains100000.',
    2642: 'Retain maximum100-node dense9900-edge constructor with100 queries; separate100 adds plus100 queries. Arbitrary maximal weighted dynamic graphs omitted.',
    2671: 'Any full200000-call minimum add trace exceeds unchanged packet cap. Retain100000-call add and30000-query families plus maximum numbers/frequencies. Arbitrary maximal histories omitted.',
}


def integer(x, low, high):
    return type(x) is int and low <= x <= high


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != 2:
        raise ValueError('state-machine identity/wire')
    ops, argv = args
    if not (type(ops) is list and type(argv) is list and 1 <= len(ops) == len(argv) <= MAX_CALLS[pid]+1
            and type(ops[0]) is str and ops[0] == CLASSES[pid] and type(argv[0]) is list
            and len(argv[0]) == len(CONSTRUCTOR_PARAMETERS[pid])):
        raise ValueError('constructor or method-count envelope')
    init = argv[0]
    if pid == 2502:
        ok = integer(init[0], 1, 1000)
    elif pid == 2526:
        ok = integer(init[0], 1, 10**9) and integer(init[1], 1, 100000)
    elif pid == 2642:
        ok = integer(init[0], 1, 100) and type(init[1]) is list and len(init[1]) <= init[0]*(init[0]-1)
    else:
        ok = True
    if not ok:
        raise ValueError('constructor domain')
    edges = set()
    def add_edge(edge):
        if not (type(edge) is list and len(edge) == 3 and all(integer(v, 0, init[0]-1) for v in edge[:2])
                and edge[0] != edge[1] and integer(edge[2], 1, 10**6) and tuple(edge[:2]) not in edges):
            raise ValueError('directed edge domain or duplicate')
        edges.add(tuple(edge[:2]))
    if pid == 2642:
        for edge in init[1]:
            add_edge(edge)
    counts = Counter()
    for op, a in zip(ops[1:], argv[1:]):
        if not (type(op) is str and op in METHODS[pid] and type(a) is list and len(a) == len(METHODS[pid][op])):
            raise ValueError('method name or argument arity')
        counts[op] += 1
        if pid == 2502:
            ok = all(integer(v, 1, 1000) for v in a)
        elif pid == 2526:
            ok = integer(a[0], 1, 10**9)
        elif pid == 2642:
            if counts[op] > 100:
                raise ValueError('per-method graph call maximum')
            if op == 'addEdge':
                add_edge(a[0]); ok = True
            else:
                ok = all(integer(v, 0, init[0]-1) for v in a)
        else:
            ok = integer(a[0], 1, 100000)
        if not ok:
            raise ValueError('method argument domain')


def expected(pid, args):
    validate(pid, args)
    ops, argv = args
    init = argv[0]
    if len(ops) > 101 or (pid == 2502 and init[0] > 30) or (pid == 2642 and (init[0] > 12 or len(init[1]) > 100)):
        raise ValueError('literal reference budget, not normative domain restriction')
    if pid == 2502:
        memory = [0]*init[0]
    elif pid == 2526:
        stream = []
    elif pid == 2642:
        n = init[0]; edges = [tuple(edge) for edge in init[1]]
    else:
        values = []
    output = [None]
    for op, a in zip(ops[1:], argv[1:]):
        result = None
        if pid == 2502:
            if op == 'allocate':
                size, identity = a
                result = next((i for i in range(len(memory)-size+1) if all(v == 0 for v in memory[i:i+size])), -1)
                if result != -1:
                    memory[result:result+size] = [identity]*size
            else:
                result = sum(v == a[0] for v in memory)
                memory = [0 if v == a[0] else v for v in memory]
        elif pid == 2526:
            stream.append(a[0]); result = len(stream) >= init[1] and all(v == init[0] for v in stream[-init[1]:])
        elif pid == 2642:
            if op == 'addEdge':
                edges.append(tuple(a[0]))
            else:
                distance = [10**20]*n; distance[a[0]] = 0
                for _ in range(n-1):
                    changed = False
                    for u, v, w in edges:
                        if distance[u]+w < distance[v]:
                            distance[v] = distance[u]+w; changed = True
                    if not changed:
                        break
                result = -1 if distance[a[1]] == 10**20 else distance[a[1]]
        elif op == 'add':
            values.append(a[0])
        elif op == 'deleteOne':
            if a[0] in values:
                values.remove(a[0])
        else:
            result = any(values.count(v) == a[0] for v in set(values))
        output.append(result)
    return output


def valid_answer(pid, args, answer):
    if type(answer) is not list or len(answer) != len(args[0]) or answer[0] is not None:
        return False
    for op, result in zip(args[0][1:], answer[1:]):
        if op in ('consec', 'hasFrequency'):
            ok = type(result) is bool
        elif op in ('add', 'deleteOne', 'addEdge'):
            ok = result is None
        elif op == 'allocate':
            ok = integer(result, -1, args[1][0][0]-1)
        elif op == 'freeMemory':
            ok = integer(result, 0, args[1][0][0])
        else:
            ok = integer(result, -1, 99000000)
        if not ok:
            return False
    return True


def public_examples(pid, statement):
    if type(statement) is not bytes or hashlib.sha256(statement).hexdigest() != STATEMENT_SHA256[pid]:
        raise ValueError('freshly gated exact definition required')
    text = re.sub(r'^L\d+: ?', '', json.loads(statement), flags=re.MULTILINE)
    if f'{pid}. {TITLES[pid]}' not in text:
        raise ValueError('definition identity')
    matches = re.findall(r'Input\s*\n\s*(\[[^\n]+\])\s*\n\s*(\[[^\n]+\])\s*\n\s*Output\s*\n\s*(\[[^\n]+\])', text)
    if len(matches) != (3 if pid == 2671 else 1):
        raise ValueError('prescribed example extraction count')
    rows = []
    for ops, argv, output in matches:
        args = [json.loads(ops), json.loads(argv)]; answer = json.loads(output)
        if not q.exact(expected(pid, args), answer):
            raise AssertionError('prescribed example mismatch')
        rows.append((args, answer))
    return rows


def build_cases(pid, statement):
    examples = public_examples(pid, statement)
    cases, categories, seen = [], [], {}
    rng = random.Random(202610272016+pid)
    missing = object()
    def add(init, steps, category, answer=missing):
        args = [[CLASSES[pid]]+[op for op, _ in steps], [init]+[a for _, a in steps]]
        validate(pid, args)
        result = expected(pid, args) if answer is missing else answer
        if not valid_answer(pid, args, result):
            raise AssertionError('invalid typed result')
        key = q.encoded(args)
        if key in seen:
            if not q.exact(cases[seen[key]]['expected'], result):
                raise AssertionError('duplicate conflict')
            return
        seen[key] = len(cases); cases.append({'args': args, 'expected': result, 'compare': 'return'}); categories.append(category)
    for args, answer in examples:
        add(args[1][0], list(zip(args[0][1:], args[1][1:])), 'pinned_public_example', answer)
    if pid == 2502:
        actions = [('allocate', [1, 1]), ('allocate', [2, 1]), ('allocate', [1, 2]), ('freeMemory', [1]), ('freeMemory', [2])]
        for n in (1, 2, 4):
            for length in range(5):
                for steps in product(actions, repeat=length):
                    add([n], list(steps), 'exhaustive_small_allocator_histories')
        for _ in range(60):
            n = rng.randint(1, 30)
            steps = [(('allocate', [rng.randint(1, n+1), rng.choice((1, 2, 1000))]) if rng.randrange(3) else ('freeMemory', [rng.choice((1, 2, 1000))])) for _ in range(40)]
            add([n], steps, 'seeded_allocator_interactions')
        add([1000], [('allocate', [1, 1000])]*999+[('freeMemory', [1000])], 'analytic_maximum_count_fill_and_free', [None]+list(range(999))+[999])
        add([1000], [('allocate', [1000, 1000]), ('allocate', [1, 1]), ('freeMemory', [1000]), ('allocate', [1000, 1])], 'analytic_full_block_failure_rollback', [None, 0, -1, 1000, 0])
        add([1], [('allocate', [1000, 1000])]*1000, 'analytic_maximum_oversized_failures', [None]+[-1]*1000)
    elif pid == 2526:
        for k in range(1, 5):
            for length in range(8):
                for values in product((1, 2), repeat=length):
                    add([1, k], [('consec', [v]) for v in values], 'exhaustive_small_stream_histories')
        for _ in range(60):
            target = rng.choice((1, 10**9)); k = rng.randint(1, 20)
            add([target, k], [('consec', [rng.choice((1, 2, 10**9))]) for _ in range(50)], 'seeded_stream_resets')
        add([1, 1], [('consec', [1])]*70000, 'analytic_long_all_true_stream', [None]+[True]*70000)
        add([1, 100000], [('consec', [1])]*70000, 'analytic_maximum_k_shorter_stream', [None]+[False]*70000)
        add([1, 2], [('consec', [1])]*34999+[('consec', [2])]+[('consec', [1])]*35000, 'analytic_long_reset_boundary', [None, False]+[True]*34998+[False, False]+[True]*34999)
        add([10**9, 100000], [('consec', [10**9])], 'maximum_value_k', [None, False])
    elif pid == 2642:
        endpoints = [(i, j) for i in range(3) for j in range(3) if i != j]
        for weights in product((0, 1, 3), repeat=6):
            edges = [[i, j, w] for (i, j), w in zip(endpoints, weights) if w]
            add([3, edges], [('shortestPath', [i, j]) for i in range(3) for j in range(3)], 'exhaustive_three_node_directed_weighted_graphs')
        add([1, []], [], 'singleton_zero_method_trace')
        add([1, []], [('shortestPath', [0, 0])], 'singleton_empty_path')
        for _ in range(60):
            n = rng.randint(2, 8); pool = [(i, j) for i in range(n) for j in range(n) if i != j]; rng.shuffle(pool)
            edges = [[*pool.pop(), rng.choice((1, 2, 10**6))] for _ in range(rng.randrange(min(6, len(pool))+1))]
            steps = []
            for _ in range(40):
                if pool and rng.randrange(3) == 0:
                    steps.append(('addEdge', [[*pool.pop(), rng.choice((1, 3, 10**6))]]))
                else:
                    steps.append(('shortestPath', [rng.randrange(n), rng.randrange(n)]))
            add([n, edges], steps, 'seeded_dynamic_graph_histories')
        dense = [[i, j, 10**6] for i in range(100) for j in range(100) if i != j]
        add([100, dense], [('shortestPath', [0, j]) for j in range(100)], 'analytic_maximum_dense_constructor_queries', [None, 0]+[10**6]*99)
        add([100, [[i, i+1, 10**6] for i in range(99)]], [('shortestPath', [0, 99]), ('shortestPath', [99, 0]), ('shortestPath', [99, 99])], 'analytic_maximum_simple_path_cost', [None, 99000000, -1, 0])
        new_edges = [[0, j, 1] for j in range(1, 100)]+[[1, 0, 1]]
        add([100, []], [step for edge in new_edges for step in (('addEdge', [edge]), ('shortestPath', edge[:2]))], 'analytic_both_method_call_maxima', [None]+[x for _ in range(100) for x in (None, 1)])
    else:
        actions = [('add', [1]), ('add', [2]), ('deleteOne', [1]), ('deleteOne', [2]), ('hasFrequency', [1]), ('hasFrequency', [2])]
        for length in range(5):
            for steps in product(actions, repeat=length):
                add([], list(steps), 'exhaustive_small_frequency_histories')
        for _ in range(80):
            steps = [(rng.choice(('add', 'deleteOne')), [rng.choice((1, 2, 100000))]) if rng.randrange(3) else ('hasFrequency', [rng.choice((1, 2, 3, 100000))]) for _ in range(50)]
            add([], steps, 'seeded_frequency_transition_histories')
        add([], [('add', [1])]*99999+[('hasFrequency', [99999])], 'analytic_long_repeated_add_history', [None]+[None]*99999+[True])
        add([], [('hasFrequency', [100000])]*30000, 'analytic_long_absent_maximum_frequency', [None]+[False]*30000)
        add([], [('add', [100000])]*100+[('hasFrequency', [100]), ('deleteOne', [100000]), ('hasFrequency', [100]), ('hasFrequency', [99])], 'analytic_maximum_number_threshold_transition', [None]+[None]*100+[True, None, False, True])
    if len(cases) != CASE_COUNT[pid] or q.sha(q.encoded(cases)) != CASES_SHA256[pid]:
        raise AssertionError('frozen semantic population drift')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('unchanged file cap')
    for _, batch in q.batches(cases):
        if len(q.encoded(q.packet(batch))) > q.MAX_PACKET:
            raise ValueError('unchanged packet cap')
        for lang in ('javascript', 'python'):
            if expected_observation_bytes(batch, lang) > q.LIMITS['max_output_bytes']:
                raise ValueError('unchanged projected output cap')
    return cases, categories


def expected_observation_bytes(batch, language):
    return sum(len(q.encoded({'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], language),
                             'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))+1
               for i, c in enumerate(batch))+len(q.encoded({'done': len(batch)}))+1
