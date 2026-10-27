"""Source-blind queue02 definitions and bounded host-side reference oracles.

No candidate loader or execution engine. Finite tests are not full-domain proof.
Callers must authorize every statement-file read before supplying its bytes.
"""
from itertools import product, combinations_with_replacement, groupby, permutations
from collections import deque
from functools import lru_cache
from math import comb, prod
import re

from . import imported_qualification as q

IDS = (2080, 2095, 2096, 2102, 2110, 2117, 2130, 2156, 2166, 2209, 2213, 2221)
PARAMETERS = {2110: ('prices',), 2221: ('nums',)}
TITLES = {2110: 'Number of Smooth Descent Periods of a Stock',
          2221: 'Find Triangular Sum of an Array'}
SLUGS = {2110: 'number-of-smooth-descent-periods-of-a-stock',
         2221: 'find-triangular-sum-of-an-array'}
STATEMENT_SHA256 = {
    2110: 'd9225e9b06ce4516f289b9c03d13d1d4586c2cf98caaa3863d7022f273408f08',
    2221: '4d4fac1970f1138b0ff61144648602443bfa5d0e9e8e399a65a3f206ed6fe377',
}
SMALL_BUDGET = {2110: 50, 2221: 40}
OBLIGATIONS = {
    2110: {'domain': '1..100000 prices, each exact integer 1..100000',
           'result': 'exact integer 1..5000050000; reject bool/float coercion',
           'complexity': 'linear-time target; 100000-item descent and plateaus included',
           'mutation_alias': 'No required input mutation; record before/after and returned aliases. Qualification requires explicitly chosen effect policy.',
           'unknown': 'Public rendering gives ordered prices parameter, not language-specific exported entrypoint.'},
    2221: {'domain': '1..1000 digits, each exact integer 0..9',
           'result': 'exact integer 0..9',
           'complexity': 'quadratic-time target permitted; length-1000 mixed and uniform arrays included',
           'mutation_alias': 'Statement describes conceptual replacement, not a required caller mutation. Record effects; explicit effect policy required.',
           'unknown': 'Public rendering gives ordered nums parameter, not language-specific exported entrypoint.'},
}

PARAMETERS.update({2117: ('left', 'right'), 2156: ('s', 'power', 'modulo', 'k', 'hashValue'),
                   2209: ('floor', 'numCarpets', 'carpetLen'), 2213: ('s', 'queryCharacters', 'queryIndices')})
TITLES.update({2117: 'Abbreviating the Product of a Range', 2156: 'Find Substring With Given Hash Value',
               2209: 'Minimum White Tiles After Covering With Carpets', 2213: 'Longest Substring of One Repeating Character'})
SLUGS.update({2117: 'abbreviating-the-product-of-a-range', 2156: 'find-substring-with-given-hash-value',
              2209: 'minimum-white-tiles-after-covering-with-carpets', 2213: 'longest-substring-of-one-repeating-character'})
STATEMENT_SHA256.update({2117: '05318d336992bd023dc80cc6e1c1ffc455d4569c66e7961fb74796d134e45af2',
 2156: '63540b2cfaeff3e39c73111a71ced716feb535b1ab74c850b798fc13488f1c64',
 2209: 'bf7ac9574e0dab1d592ccae9ec1ffc314bb343d0f73917f521abd9f49b37f060',
 2213: '0e74c2d36fedd54fcd7c2633ea689f497433ad21128cf51455f757d41a0879b9'})
EXAMPLE_COUNT = {2110: 3, 2117: 3, 2156: 2, 2209: 2, 2213: 2, 2221: 2}
for _pid, _domain, _numeric, _complexity in [
 (2117, 'exact integers 1 <= left <= right <= 10000', 'exact decimal strings with leading/trailing five digits and trailing-zero exponent', 'range-size bounded arithmetic; near-full-range cases exercise precision without floating logarithm oracle'),
 (2156, 'lowercase ASCII string length 1..20000; 1<=k<=length; power/modulo 1..1e9; hashValue in [0,modulo); matching substring required', 'exact modular arithmetic, including products above IEEE-754 safe-integer range', 'linear-time target; length-20000 windows and k boundaries'),
 (2209, 'binary string length 1..1000; carpetLen 1..length; numCarpets 1..1000', 'exact integer 0..floor length', 'polynomial target; maximum floor/carpet counts; no full placement enumeration at large bounds'),
 (2213, 'lowercase ASCII s length 1..100000; queryCharacters length k 1..100000; k valid exact integer indices', 'array of exact integers 1..s length', 'subquadratic per-stream target; 100000 updates and length100000 shapes')]:
    OBLIGATIONS[_pid] = {'domain': _domain, 'result': _numeric, 'complexity': _complexity,
        'mutation_alias': 'No required argument mutation. Observe before/after and aliases under an explicitly declared effect policy.',
        'unknown': 'Candidate exported interface is unknown; ordered public parameters are definition-only evidence.'}

STRUCTURED_IDS = (2080, 2095, 2096, 2102, 2130, 2166)
STATEFUL_IDS = (2080, 2102, 2166)
PARAMETERS.update({2080: ('operations', 'arguments'), 2095: ('head',), 2096: ('root', 'startValue', 'destValue'),
                   2102: ('operations', 'arguments'), 2130: ('head',), 2166: ('operations', 'arguments')})
TITLES.update({2080: 'Range Frequency Queries', 2095: 'Delete the Middle Node of a Linked List',
               2096: 'Step-By-Step Directions From a Binary Tree Node to Another', 2102: 'Sequentially Ordinal Rank Tracker',
               2130: 'Maximum Twin Sum of a Linked List', 2166: 'Design Bitset'})
SLUGS.update({2080: 'range-frequency-queries', 2095: 'delete-the-middle-node-of-a-linked-list',
              2096: 'step-by-step-directions-from-a-binary-tree-node-to-another', 2102: 'sequentially-ordinal-rank-tracker',
              2130: 'maximum-twin-sum-of-a-linked-list', 2166: 'design-bitset'})
STATEMENT_SHA256.update({2080: '8d8c02a8cd369a7a81da1fb77f7670ddb1b31e058f9d02f5ee383e729d34dcba',
 2095: 'f9b35f7f17ff1675c0bf672f93b5834296b5cc151a0104a7518f8f65290a250b',
 2096: 'b903a9afe332f5c46c454a840ffdf8df43d20df0b20cc48685b4b9a50d134985',
 2102: 'd826c8485d80751979f5ec5963433b1fe023fa8f15d6d0463b391f64b14597eb',
 2130: '20f6684c9637931e71b84bba00381d107aad3493d7de0436c95314cf39d7a4ee',
 2166: '3a5e5646e700409124aa8abdacd1f8d6dd454284f4e03f30c6ab18a8ae7d0281'})
EXAMPLE_COUNT.update({2080: 1, 2095: 3, 2096: 2, 2102: 1, 2130: 3, 2166: 1})
for _pid, _domain, _interface, _effects, _complexity in [
 (2080, 'arr length1..100000 integer1..10000; at most100000 inclusive-range queries with value1..10000',
  'RangeFreqQuery(arr); query(left,right,value)', 'Construction snapshots values; queries do not change the modeled array. Later adapter must observe constructor argument mutation and per-instance state separation.', 'preprocess then sublinear query target'),
 (2095, 'acyclic linked list of1..100000 nodes with integer values1..100000', 'head argument, returned head',
  'Required list deletion; returned node identity, retained-node order, edge mutation and detached middle must be observed, not inferred from value arrays.', 'linear-time target'),
 (2096, 'binary tree with2..100000 nodes labeled by permutation1..n; distinct start/destination1..n', 'root,startValue,destValue',
  'Read-only tree service policy not yet selected. Observe graph mutation and node identity; string directions are scalar.', 'linear-time target, depth100000 iterative safety'),
 (2102, 'unique lowercase ASCII names length1..10; scores1..100000; total add/get calls<=40000; gets never exceed adds',
  'SORTracker(); add(name,score); get()', 'Stateful ranking and get ordinal persist per instance. No source instance simulation counts as execution.', 'logarithmic add/get target, max40000 calls'),
 (2130, 'acyclic linked list even length2..100000; integer values1..100000', 'head argument; integer result',
  'Definition does not mandate mutation. Any stronger no-mutation service policy must be frozen before source access; observe original graph identities and edges.', 'linear-time target'),
 (2166, 'size1..100000; idx0..size-1; <=100000 calls; >=1 all/one/count/toString; toString<=5',
  'Bitset(size); fix(idx); unfix(idx); flip(); all(); one(); count(); toString()',
  'State transitions and queries persist per instance; no cross-instance state; actual operation observer remains undeclared.', 'constant-time operations except linear toString target')]:
    OBLIGATIONS[_pid] = {'domain': _domain, 'definition_interface': _interface, 'mutation_alias': _effects,
        'complexity': _complexity, 'unknown': 'Candidate source export/adapter unknown. Existing observer extension must be declared, tested and separately frozen before execution.',
        'adapter_gap': 'Pure JSON oracle model only; packet batching is sizing evidence, NOT an implemented stateful/node observer and NOT qualification.'}
STRUCTURED_ENCODING = {
 'stateful': 'Two oracle transport arrays operations/arguments encode the public example operation sequence; constructor is first. These are not a candidate single-call interface.',
 'linked': 'A JSON value array models one finite acyclic list; identity and mutation are intentionally not simulated as a passing observation.',
 'tree': 'Canonical compact breadth-first non-null-parent expansion with null missing children and no trailing null. Every normative tree is representable; serialized aliases/cycles are rejected.'}
OMITTED_MAXIMUM_SHAPES = {
 2080: '100000 query calls cannot fit unchanged JSON operation packet cap. Keep 20000-query fitting stream and separate100000-element arrays; no maximum query-stream execution claim.',
 2095: 'Maximum node count covered by value-model only; real node serialization/identity observer cost remains unknown.',
 2096: 'Maximum depth/node count covered by canonical value-model; actual node observer payload/identity budget must be measured later.',
 2102: '40000-operation stream fits abstract JSON packet; actual stateful adapter has not been implemented or measured.',
 2130: 'Maximum node count covered by value-model only; source-node effect observation remains an explicit gap.',
 2166: '100000-operation flip stream fits; varying-index maximum fix stream exceeds unchanged cap. Size100000 and at most5 toString calls separately covered.'}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _text(x, alphabet, minimum, maximum):
    return type(x) is str and minimum <= len(x) <= maximum and all(c in alphabet for c in x)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered arguments')
    if pid in STRUCTURED_IDS:
        _validate_structured(pid, args)
        return
    if pid in (2110, 2221):
        values = args[0]
        lo, hi, maximum = (1, 100000, 100000) if pid == 2110 else (0, 9, 1000)
        valid = type(values) is list and 1 <= len(values) <= maximum and all(_integer(v, lo, hi) for v in values)
    elif pid == 2117:
        left, right = args
        valid = _integer(left, 1, 10000) and _integer(right, left, 10000)
    elif pid == 2156:
        s, power, modulo, k, value = args
        valid = (_text(s, 'abcdefghijklmnopqrstuvwxyz', 1, 20000) and _integer(power, 1, 10**9)
                 and _integer(modulo, 1, 10**9) and _integer(k, 1, len(s)) and _integer(value, 0, modulo - 1))
        if valid:
            valid = value in _window_hashes(s, power, modulo, k)
    elif pid == 2209:
        floor, count, length = args
        valid = _text(floor, '01', 1, 1000) and _integer(count, 1, 1000) and _integer(length, 1, len(floor))
    else:
        s, chars, indices = args
        valid = (_text(s, 'abcdefghijklmnopqrstuvwxyz', 1, 100000) and _text(chars, 'abcdefghijklmnopqrstuvwxyz', 1, 100000)
                 and type(indices) is list and len(indices) == len(chars) and all(_integer(i, 0, len(s) - 1) for i in indices))
    if not valid:
        raise ValueError('arguments outside pinned full input domain')


def _ints(a, low, high, minimum=1, maximum=100000):
    return type(a) is list and minimum <= len(a) <= maximum and all(_integer(x, low, high) for x in a)


def _tree_edges(root):
    if type(root) is not list or not root or root[0] is None or root[-1] is None or len(root) > 199999:
        raise ValueError('noncanonical compact tree encoding')
    n = sum(x is not None for x in root)
    if not 2 <= n <= 100000 or any(x is not None and not _integer(x, 1, n) for x in root):
        raise ValueError('tree node count/value domain')
    values = [x for x in root if x is not None]
    if len(set(values)) != n:
        raise ValueError('tree labels must be unique permutation')
    queue, index, edges = deque([root[0]]), 1, {x: [] for x in values}
    while queue and index < len(root):
        parent = queue.popleft()
        for letter in 'LR':
            if index == len(root):
                break
            child = root[index]; index += 1
            if child is not None:
                edges[parent].append((child, letter)); edges[child].append((parent, 'U')); queue.append(child)
    if index != len(root):
        raise ValueError('orphan compact tree tokens')
    return edges


def _validate_structured(pid, args):
    if pid in (2095, 2130):
        if not _ints(args[0], 1, 100000, 1 if pid == 2095 else 2) or (pid == 2130 and len(args[0]) % 2):
            raise ValueError('linked-list value model domain')
        return
    if pid == 2096:
        root, start, end = args; edges = _tree_edges(root)
        if not _integer(start, 1, len(edges)) or not _integer(end, 1, len(edges)) or start == end:
            raise ValueError('tree endpoints outside domain')
        return
    operations, arguments = args
    constructor = {2080: 'RangeFreqQuery', 2102: 'SORTracker', 2166: 'Bitset'}[pid]
    maximum = 40000 if pid == 2102 else 100000
    if (type(operations) is not list or type(arguments) is not list or not 1 <= len(operations) <= maximum+1
            or len(operations) != len(arguments) or operations[0] != constructor
            or any(type(op) is not str for op in operations) or any(type(a) is not list for a in arguments)):
        raise ValueError('stateful operation envelope')
    init = arguments[0]
    if pid == 2080:
        if len(init) != 1 or not _ints(init[0], 1, 10000):
            raise ValueError('range frequency constructor domain')
        n = len(init[0])
        for op, a in zip(operations[1:], arguments[1:]):
            if (op != 'query' or len(a) != 3 or not _integer(a[0], 0, n-1)
                    or not _integer(a[1], a[0], n-1) or not _integer(a[2], 1, 10000)):
                raise ValueError('range frequency query domain')
    elif pid == 2102:
        if init:
            raise ValueError('rank constructor takes no arguments')
        names, gets = set(), 0
        for op, a in zip(operations[1:], arguments[1:]):
            if op == 'add':
                if (len(a) != 2 or not _text(a[0], 'abcdefghijklmnopqrstuvwxyz', 1, 10)
                        or a[0] in names or not _integer(a[1], 1, 100000)):
                    raise ValueError('rank addition domain')
                names.add(a[0])
            elif op == 'get' and not a:
                gets += 1
                if gets > len(names):
                    raise ValueError('rank query lacks added locations')
            else:
                raise ValueError('rank operation domain')
    else:
        if len(init) != 1 or not _integer(init[0], 1, 100000):
            raise ValueError('bitset constructor domain')
        queries = strings = 0
        for op, a in zip(operations[1:], arguments[1:]):
            if op in ('fix', 'unfix'):
                if len(a) != 1 or not _integer(a[0], 0, init[0]-1):
                    raise ValueError('bitset index domain')
            elif op in ('flip', 'all', 'one', 'count', 'toString') and not a:
                queries += op != 'flip'; strings += op == 'toString'
            else:
                raise ValueError('bitset operation domain')
        if queries < 1 or strings > 5:
            raise ValueError('bitset query count domain')


def _structured_expected(pid, args):
    if pid == 2095:
        values = args[0]
        return [x for i, x in enumerate(values) if i != len(values)//2]
    if pid == 2130:
        values = args[0]
        return max(x+y for x,y in zip(values[:len(values)//2], reversed(values)))
    if pid == 2096:
        root, start, end = args; edges = _tree_edges(root)
        if len(edges) > 100:
            raise ValueError('tree reference budget exceeded')
        frontier = deque([(start, '')]); seen = {start}
        while frontier:
            node, path = frontier.popleft()
            if node == end:
                return path
            for neighbor, letter in edges[node]:
                if neighbor not in seen:
                    seen.add(neighbor); frontier.append((neighbor, path+letter))
        raise AssertionError('validated tree disconnected')
    operations, arguments = args
    if pid == 2080:
        array = arguments[0][0]
        if sum(a[1]-a[0]+1 for a in arguments[1:]) > 1000000:
            raise ValueError('frequency reference budget exceeded')
        return [None]+[sum(x == value for x in array[left:right+1]) for left,right,value in arguments[1:]]
    if pid == 2102:
        if len(operations) > 201:
            raise ValueError('rank reference budget exceeded')
        locations, ordinal, results = [], 0, [None]
        for op, a in zip(operations[1:], arguments[1:]):
            if op == 'add':
                locations.append((a[0], a[1]));results.append(None)
            else:
                ranked=sorted(locations,key=lambda x:(-x[1],x[0]));results.append(ranked[ordinal][0]);ordinal+=1
        return results
    size = arguments[0][0]
    if size * len(operations) > 1000000:
        raise ValueError('bitset reference budget exceeded')
    bits, result = [False]*size, [None]
    for op, a in zip(operations[1:], arguments[1:]):
        value = None
        if op == 'fix':bits[a[0]] = True
        elif op == 'unfix':bits[a[0]] = False
        elif op == 'flip':bits = [not x for x in bits]
        elif op == 'all':value = all(bits)
        elif op == 'one':value = any(bits)
        elif op == 'count':value = sum(bits)
        else:value = ''.join('1' if x else '0' for x in bits)
        result.append(value)
    return result


def _window_hashes(s, power, modulo, k):
    # Right-to-left rolling evaluator used only for full-domain existence validation.
    value = 0
    high = pow(power, k, modulo)
    result = [0] * (len(s) - k + 1)
    for i in range(len(s) - 1, -1, -1):
        value = (value * power + ord(s[i]) - 96) % modulo
        if i + k < len(s):
            value = (value - (ord(s[i + k]) - 96) * high) % modulo
        if i <= len(s) - k:
            result[i] = value
    return result


def _abbreviate_integer(value):
    zeros = 0
    while value % 10 == 0:
        value //= 10
        zeros += 1
    # Bounded 9-digit conversions avoid altering interpreter-wide numeric limits.
    blocks = []
    while value:
        value, block = divmod(value, 10**9)
        blocks.append(block)
    digits = str(blocks[-1]) + ''.join(f'{b:09d}' for b in blocks[-2::-1])
    return (digits if len(digits) <= 10 else digits[:5] + '...' + digits[-5:]) + 'e' + str(zeros)


def expected(pid, args):
    """Small reference: enumerate all intervals or simulate successive rows."""
    validate(pid, args)
    if pid in STRUCTURED_IDS:
        return _structured_expected(pid, args)
    if pid == 2117:
        return _abbreviate_integer(prod(range(args[0], args[1] + 1)))
    if pid == 2156:
        s, power, modulo, k, value = args
        if len(s) > 60:
            raise ValueError('reference budget exceeded')
        return next(s[i:i+k] for i in range(len(s)-k+1)
                    if sum((ord(s[i+j])-96) * pow(power, j, modulo) for j in range(k)) % modulo == value)
    if pid == 2209:
        floor, count, length = args
        if len(floor) > 12:
            raise ValueError('reference budget exceeded')
        if count * length >= len(floor):
            return 0
        white = sum((c == '1') << i for i, c in enumerate(floor))
        placements = [((1 << length) - 1) << i for i in range(len(floor) - length + 1)]
        best = len(floor)
        for selected in combinations_with_replacement(placements, count):
            covered = 0
            for mask in selected:
                covered |= mask
            best = min(best, (white & ~covered).bit_count())
        return best
    if pid == 2213:
        s, chars, indices = args
        if len(s) * len(chars) > 10000:
            raise ValueError('reference budget exceeded')
        row, result = list(s), []
        for c, i in zip(chars, indices):
            row[i] = c
            result.append(max(sum(1 for _ in run) for _, run in groupby(row)))
        return result
    values = args[0]
    if len(values) > SMALL_BUDGET[pid]:
        raise ValueError('reference budget exceeded; input may remain valid')
    if pid == 2110:
        return sum(all(values[k] - values[k + 1] == 1 for k in range(i, j))
                   for i in range(len(values)) for j in range(i, len(values)))
    row = values[:]
    while len(row) > 1:
        row = [(row[i] + row[i + 1]) % 10 for i in range(len(row) - 1)]
    return row[0]


def analytic(pid, args):
    """Separate large reference: maximal descent runs or binomial coefficients."""
    validate(pid, args)
    if pid == 2117:
        left, right = args
        primes = []
        composite = bytearray(right + 1)
        for x in range(2, right + 1):
            if not composite[x]:
                primes.append(x)
                for multiple in range(x*x, right + 1, x):
                    composite[multiple] = 1
        value = 1
        for prime in primes:
            factor, exponent = prime, 0
            while factor <= right:
                exponent += right // factor - (left - 1) // factor
                factor *= prime
            value *= pow(prime, exponent)
        return _abbreviate_integer(value)
    if pid not in (2110, 2221):
        raise ValueError('large oracle requires explicit constructive case witness')
    a = args[0]
    if pid == 2221:
        return sum(comb(len(a) - 1, i) * x for i, x in enumerate(a)) % 10
    breaks = [-1] + [i for i in range(len(a) - 1) if a[i] != a[i + 1] + 1] + [len(a) - 1]
    return sum((b - a) * (b - a + 1) // 2 for a, b in zip(breaks, breaks[1:]))


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact gated pinned definition required')
    text = re.sub(r'(?m)^L\d+: ?', '', raw.decode())
    if f'{pid}. {TITLES[pid]}' not in text or f'https://leetcode.com/problems/{SLUGS[pid]}/' not in text:
        raise ValueError('numeric/title/slug identity mismatch')
    import ast
    import json
    cases = []
    if pid in STATEFUL_IDS:
        match = re.search(r'Input\s*\n\s*(\[[^\n]+)\n\s*(\[[^\n]+)\n\s*Output\s*\n\s*(\[[^\n]+)', text)
        if match is None:
            raise ValueError('complete public operation example required')
        args = [json.loads(match[1]), json.loads(match[2])]
        answer = json.loads(match[3])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('stateful public example disagreement')
        return [{'args': args, 'expected': answer, 'compare': 'return'}]
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*([^\n]+)', text, re.S):
        call = ast.parse('f(' + re.sub(r'\bnull\b', 'None', match[1].strip()) + ')', mode='eval').body
        if call.args or tuple(k.arg for k in call.keywords) != PARAMETERS[pid]:
            raise ValueError('public ordered parameter mismatch')
        args = [ast.literal_eval(x.value) for x in call.keywords]
        answer = ast.literal_eval(match[2])
        if not q.exact(answer, expected(pid, args)):
            raise ValueError('public example disagreement')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('incomplete public examples')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement)
    categories = ['pinned_public_example'] * len(cases)
    sentinel = object()
    def add_args(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)
    def add(a, category, large=False):
        add_args([a], category, analytic(pid, [a]) if large else sentinel)
    if pid == 2110:
        for n in range(1, 7):
            for values in product((1, 2, 3), repeat=n):
                add(list(values), 'exhaustive_small_three_values')
        for a in ([1] * 100000, list(range(100000, 0, -1)), list(range(1, 100001)), [1, 2] * 50000, [100000, 99999] * 50000):
            add(a, 'analytic_maximum_length', True)
        add([100000, 99999, 99998, 1], 'numeric_boundaries')
    elif pid == 2221:
        for n in range(1, 4):
            for values in product(range(10), repeat=n):
                add(list(values), 'exhaustive_small_all_digits')
        for n in range(4, 9):
            for values in product((0, 1), repeat=n):
                add(list(values), 'exhaustive_binary_longer')
        for a in ([0] * 1000, [9] * 1000, [i % 10 for i in range(1000)], [1] + [0] * 999, [0] * 999 + [9]):
            add(a, 'analytic_maximum_length', True)
    elif pid == 2117:
        for left in range(1, 61):
            for right in range(left, 61):
                add_args([left, right], 'exhaustive_small_ranges')
        for args in ([1, 10000], [2, 9999], [9000, 10000], [9999, 10000], [999, 1000], [371, 375]):
            add_args(args, 'exact_big_integer_large_boundary', analytic(pid, args))
    elif pid == 2156:
        for n in range(1, 6):
            for letters in product('ab', repeat=n):
                s = ''.join(letters)
                for k in range(1, n + 1):
                    for power, modulo in ((1, 1), (2, 5), (3, 8)):
                        hashes = {sum((ord(s[i+j])-96) * pow(power, j, modulo) for j in range(k)) % modulo for i in range(n-k+1)}
                        for value in sorted(hashes):
                            add_args([s, power, modulo, k, value], 'exhaustive_small_hashes')
        for k in (1, 9999, 20000):
            power, modulo = 999999999, 1000000000
            value = sum(26 * pow(power, j, modulo) for j in range(k)) % modulo
            add_args(['z' * 20000, power, modulo, k, value], 'analytic_uniform_maximum', 'z' * k)
        add_args(['a' * 19999 + 'z', 10**9, 999999937, 1, 26], 'analytic_last_match', 'z')
        add_args(['ab' * 10000, 1, 1, 10000, 0], 'analytic_collision_first_match', 'ab' * 5000)
    elif pid == 2209:
        for n in range(1, 7):
            for bits in product('01', repeat=n):
                for length in range(1, n + 1):
                    for count in range(1, min(3, n) + 1):
                        add_args([''.join(bits), count, length], 'exhaustive_small_placements')
        for floor, count, length, answer in [('0'*1000, 1, 1, 0), ('1'*1000, 1, 999, 1),
                ('1'*1000, 1000, 1, 0), ('1'*1000, 1, 1, 999), ('10'*500, 1, 500, 250),
                ('1'*1000, 999, 1, 1), ('0'*999+'1', 1, 1, 0)]:
            add_args([floor, count, length], 'analytic_maximum_floor', answer)
    elif pid == 2213:
        for n in range(1, 6):
            for letters in product('ab', repeat=n):
                s = ''.join(letters)
                for indices in product(range(n), repeat=2):
                    for chars in ('aa', 'ab', 'ba', 'bb'):
                        add_args([s, chars, list(indices)], 'exhaustive_two_updates')
        add_args(['a'*100000, 'a'*100000, [0]*100000], 'analytic_maximum_noops', [100000]*100000)
        add_args(['a'*100000, 'ba'*50000, [50000]*100000], 'analytic_maximum_split_rejoin', [50000, 100000]*50000)
        add_args(['ab'*50000, 'ba'*50000, [0]*100000], 'analytic_maximum_endpoint_toggle', [2, 1]*50000)
    elif pid in (2095, 2130):
        lengths = range(1, 8) if pid == 2095 else range(2, 9, 2)
        for n in lengths:
            for values in product((1, 2), repeat=n):
                add_args([list(values)], 'exhaustive_linked_value_models')
        for values in ([1]*100000, list(range(1, 100001)), [100000]*100000):
            answer = values[:50000]+values[50001:] if pid == 2095 else (100001 if values[0] == 1 and values[-1] == 100000 else 2*values[0])
            add_args([values], 'analytic_maximum_linked_value_model', answer)
    elif pid == 2096:
        for n in range(2, 5):
            for shape in _tree_shapes(n):
                for labels in permutations(range(1, n+1)):
                    root = _shape_serialization(shape, iter(labels))
                    for start in range(1,n+1):
                        for end in range(1,n+1):
                            if start != end:
                                add_args([root, start, end], 'exhaustive_labeled_small_binary_trees')
        left_chain=[1]
        for i in range(2,100001):left_chain.extend([i,None])
        left_chain.pop()
        add_args([left_chain,1,100000], 'analytic_maximum_depth_left', 'L'*99999)
        add_args([left_chain,100000,1], 'analytic_maximum_depth_up', 'U'*99999)
        add_args([list(range(1,100001)),1,65535], 'analytic_maximum_nodes_heap_shape', 'R'*15)
    elif pid == 2080:
        for n in range(1,6):
            for values in product((1,2),repeat=n):
                queries=[[a,b,v] for a in range(n) for b in range(a,n) for v in (1,2,3)]
                add_args([['RangeFreqQuery']+['query']*len(queries), [[list(values)]]+queries], 'exhaustive_small_range_query_traces')
        add_args([['RangeFreqQuery'], [[[10000]]]], 'zero_query_trace')
        add_args([['RangeFreqQuery','query','query'], [[[10000]*100000],[0,99999,10000],[0,99999,1]]], 'analytic_maximum_array', [None,100000,0])
        count=20000
        add_args([['RangeFreqQuery']+['query']*count, [[[1]*1000]]+[[0,999,i%2+1] for i in range(count)]], 'analytic_fitting_long_query_stream', [None]+[1000 if i%2==0 else 0 for i in range(count)])
    elif pid == 2102:
        for n in range(1,5):
            for order in permutations('abcd'[:n]):
                for scores in product((1,2),repeat=n):
                    ops=['SORTracker']+['add']*n+['get']*n
                    args=[[]]+[[name,score] for name,score in zip(order,scores)]+[[] for _ in range(n)]
                    add_args([ops,args], 'exhaustive_small_rank_ties_and_orders')
        for scores in product((1,2,3),repeat=5):
            ops=['SORTracker'];args=[[]]
            for i,score in enumerate(scores):ops.extend(['add','get']);args.extend([[chr(97+i),score],[]])
            add_args([ops,args], 'exhaustive_alternating_add_get_scores')
        names=[''.join(chr(97+(i//(26**p))%26) for p in (3,2,1,0)) for i in range(20000)]
        add_args([['SORTracker']+['add']*20000+['get']*20000, [[]]+[[name,1] for name in reversed(names)]+[[] for _ in names]], 'analytic_maximum_rank_operations', [None]*20001+names)
    elif pid == 2166:
        for size in range(1,4):
            actions=[('fix',[i]) for i in range(size)]+[('unfix',[i]) for i in range(size)]+[('flip',[])]
            for count in range(4):
                for selected in product(actions,repeat=count):
                    ops=['Bitset']+[x[0] for x in selected]+['all','one','count','toString']
                    args=[[size]]+[x[1] for x in selected]+[[],[],[],[]]
                    add_args([ops,args], 'exhaustive_small_bitset_transitions')
        add_args([['Bitset','fix','toString','flip','toString','count'], [[100000],[99999],[],[],[],[]]], 'analytic_maximum_bitset_size', [None,None,'0'*99999+'1',None,'1'*99999+'0',99999])
        add_args([['Bitset']+['flip']*99999+['all'], [[100000]]+[[] for _ in range(100000)]], 'analytic_maximum_flip_stream', [None]*100000+[True])
    return cases, categories


@lru_cache(maxsize=None)
def _tree_shapes(n):
    if n == 0:
        return (None,)
    return tuple((left,right) for i in range(n) for left in _tree_shapes(i) for right in _tree_shapes(n-1-i))


def _shape_serialization(shape, labels):
    def bind(node):
        if node is None:return None
        value=next(labels)
        return (value,bind(node[0]),bind(node[1]))
    queue=deque([bind(shape)]);root=[]
    while queue:
        node=queue.popleft()
        if node is None:root.append(None)
        else:root.append(node[0]);queue.extend(node[1:])
    while root[-1] is None:root.pop()
    return root


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported language')
    return sum(len(q.encoded({'i': i, 'result': c['expected'],
                             'result_type': q.expected_type(c['expected'], language),
                             'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))
               for i, c in enumerate(batch)) + len(q.encoded({'done': len(batch)})) + (language == 'python')


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('unchanged case-file budget exceeded')
    for _, batch in q.batches(cases):
        for language in ('python', 'javascript'):
            if expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes']:
                raise ValueError('unchanged output budget exceeded')
    return cases, categories
