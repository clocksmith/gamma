"""Boundary cases for the four Q review gaps: 126, 129, 140 and 144.

Every expected value here comes from a method different from the cohort oracle
(continuation-q-20261028-v1/oracles.py):

- 126: distances from both ends over the explicit pairwise Hamming graph, then
  enumeration through vertices with d_begin + d_end = D. Grid rows are also
  checked against a closed-form multinomial path count.
- 129: the sum as a linear form, sum of digit * weight, with weights built
  bottom-up from leaf depths. No root-to-leaf string is formed.
- 140: suffix feasibility, then a forward prefix-sentence table restricted to
  positions that can still finish, plus a separate count recurrence.
- 144: Morris threaded preorder over copied child arrays.

The cohort oracle uses partial-path BFS (126), path strings (129), cut-mask
enumeration (140) and recursive preorder (144). test_boundary.py checks the two
against each other on small inputs. Nothing here reads or runs a candidate.

Output promise: the pinned statements bound 126's shortest sequences and
140's answer at 10**5. Rows stay at most 10**5 total words over all returned
ladders (126) and at most 10**5 total returned sentence characters including
spaces (140), which satisfies either reading of each bound.
"""
from __future__ import annotations
import importlib.util
import json
from math import factorial
from pathlib import Path
import random

AUTHORED = Path(__file__).resolve().parents[1]/'authored'
IDS = (126, 129, 140, 144)
LADDER_OUTPUT_WORDS_MAX = 10**5
SENTENCE_OUTPUT_CHARS_MAX = 10**5
SUM_LIMIT = 2**31-1


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


Q_ORACLES = _load(AUTHORED/'continuation-q-20261028-v1'/'oracles.py', 'q_boundary_cohort_oracles')


def validate(pid, args):
    if pid not in IDS:
        raise ValueError('boundary population')
    Q_ORACLES.validate_domain(pid, args)


def _key(args):
    return json.dumps(args, sort_keys=True, separators=(',', ':'))


# 126 -----------------------------------------------------------------------

def _hamming_one(a, b):
    return sum(x != y for x, y in zip(a, b)) == 1


def ladders_two_sided(begin, end, words):
    """All shortest ladders: BFS from both ends on the pairwise Hamming graph."""
    if end not in words:
        return []
    vertices = [begin]+[w for w in words if w != begin]
    n = len(vertices); adjacency = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            if _hamming_one(vertices[i], vertices[j]):
                adjacency[i].append(j); adjacency[j].append(i)
    def distances(source):
        dist = [None]*n; dist[source] = 0; queue = [source]
        for v in queue:
            for u in adjacency[v]:
                if dist[u] is None:
                    dist[u] = dist[v]+1; queue.append(u)
        return dist
    target = vertices.index(end)
    from_begin, from_end = distances(0), distances(target)
    if from_begin[target] is None:
        return []
    depth = from_begin[target]
    on_path = [from_begin[v] is not None and from_end[v] is not None and from_begin[v]+from_end[v] == depth for v in range(n)]
    forward = [[u for u in adjacency[v] if on_path[u] and from_begin[u] == from_begin[v]+1] for v in range(n)]
    answers = []; path = [0]; cursors = [0]
    while path:
        v = path[-1]
        if v == target:
            answers.append([vertices[i] for i in path]); path.pop(); cursors.pop(); continue
        if cursors[-1] < len(forward[v]):
            u = forward[v][cursors[-1]]; cursors[-1] += 1; path.append(u); cursors.append(0)
        else:
            path.pop(); cursors.pop()
    return sorted(answers)


def chain_word(k):
    """Two-letter induced path aa, ba, bb, cb, cc, ..., zz (51 vertices, index 0..50)."""
    if not 0 <= k <= 50:
        raise ValueError('chain index')
    letter = k//2+k % 2
    return chr(97+letter)+chr(97+k//2)


def grid_word(x, y, z=None):
    return chain_word(x)+chain_word(y)+('' if z is None else z)


def multinomial(*parts):
    total = factorial(sum(parts))
    for part in parts:
        total //= factorial(part)
    return total


def grid_case(rng, width, height, begin, end, letters=None, include_begin=False):
    """Words chain[x]+chain[y](+z). The Hamming graph is the grid (x, y) times K_letters."""
    zs = [None] if letters is None else list(letters)
    cells = [(x, y, z) for x in range(width) for y in range(height) for z in zs]
    words = [grid_word(*cell) for cell in cells if include_begin or cell != begin]
    rng.shuffle(words)
    args = [grid_word(*begin), grid_word(*end), words]
    steps = [abs(end[0]-begin[0]), abs(end[1]-begin[1])]+([] if letters is None else [int(end[2] != begin[2])])
    return args, multinomial(*steps)


def ladder_shortest_prefixes(args):
    """Partial paths a per-edge path-copy BFS holds before reaching the end layer."""
    begin, end, words = args
    vertices = [begin]+[w for w in words if w != begin]
    index = {w: i for i, w in enumerate(vertices)}
    dist = {begin: 0}; ways = {begin: 1}; queue = [begin]
    for v in queue:
        for i in range(len(v)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                u = v[:i]+c+v[i+1:]
                if u in index and u != v:
                    if u not in dist:
                        dist[u] = dist[v]+1; ways[u] = 0; queue.append(u)
                    if dist[u] == dist[v]+1:
                        ways[u] += ways[v]
    depth = dist.get(end)
    return sum(ways[v] for v in dist if depth is None or dist[v] < depth)


# 129 -----------------------------------------------------------------------

def leaf_weights(packet):
    """w(v) = sum over leaves l below v of 10**(depth(l)-depth(v)), built bottom-up."""
    left, right, root = packet['left'], packet['right'], packet['root']
    order = [root]
    for v in order:
        order.extend(c for c in (left[v], right[v]) if c is not None)
    weight = [0]*len(packet['values'])
    for v in reversed(order):
        children = [c for c in (left[v], right[v]) if c is not None]
        weight[v] = 1 if not children else 10*sum(weight[c] for c in children)
    return weight


def root_leaf_sum_linear(packet):
    return sum(d*w for d, w in zip(packet['values'], leaf_weights(packet)))


def tune_digits(packet, target, rng):
    """Random digits, then lower/raise heaviest-weight digits so the sum ends at or below target."""
    values = [rng.randrange(10) for _ in packet['values']]
    weight = leaf_weights(packet); order = sorted(range(len(values)), key=lambda v: -weight[v])
    total = sum(d*w for d, w in zip(values, weight))
    for v in order:
        if total <= target:
            break
        cut = min(values[v], -(-(total-target)//weight[v])); values[v] -= cut; total -= cut*weight[v]
    for v in order:
        add = min(9-values[v], (target-total)//weight[v]); values[v] += add; total += add*weight[v]
    packet['values'] = values
    return total


def random_shape(n, rng, max_depth, right_bias, deep_bias):
    """Random binary-tree shape on nodes 0..n-1 (root 0) with at most max_depth levels."""
    left = [None]*n; right = [None]*n; depth = [1]+[0]*(n-1); open_nodes = [0] if max_depth > 1 else []
    for i in range(1, n):
        if not open_nodes:
            raise ValueError('shape budget')
        parent = open_nodes[-1] if rng.random() < deep_bias else open_nodes[rng.randrange(len(open_nodes))]
        free = [side for side, array in (('R', right), ('L', left)) if array[parent] is None]
        side = free[0] if len(free) == 1 else ('R' if rng.random() < right_bias else 'L')
        (right if side == 'R' else left)[parent] = i; depth[i] = depth[parent]+1
        if left[parent] is not None and right[parent] is not None:
            open_nodes.remove(parent)
        if depth[i] < max_depth:
            open_nodes.append(i)
    return left, right


def path_shape(sides):
    """Chain following sides ('L'/'R') from root 0."""
    n = len(sides)+1; left = [None]*n; right = [None]*n
    for i, side in enumerate(sides):
        (left if side == 'L' else right)[i] = i+1
    return left, right


def relabel(values, left, right, rng):
    """Physically permute pool indices so the root is not index 0 and children are unordered."""
    n = len(values); perm = list(range(n)); rng.shuffle(perm)
    new_values = [None]*n; new_left = [None]*n; new_right = [None]*n
    for old in range(n):
        new = perm[old]; new_values[new] = values[old]
        new_left[new] = None if left[old] is None else perm[left[old]]
        new_right[new] = None if right[old] is None else perm[right[old]]
    return {'values': new_values, 'left': new_left, 'right': new_right, 'root': perm[0]}


def tree_packet(values, left, right, rng=None):
    if rng is None:
        return {'values': list(values), 'left': list(left), 'right': list(right), 'root': 0}
    return relabel(values, left, right, rng)


# 140 -----------------------------------------------------------------------

def sentences_forward_feasible(s, words):
    """Suffix feasibility, then a forward prefix-sentence table over finishing positions only."""
    dictionary = set(words); n = len(s); longest = max(map(len, words))
    finish = [False]*(n+1); finish[n] = True
    for i in range(n-1, -1, -1):
        finish[i] = any(finish[j] and s[i:j] in dictionary for j in range(i+1, min(n, i+longest)+1))
    if not finish[0]:
        return []
    prefixes = [None]*(n+1); prefixes[0] = ['']
    for j in range(1, n+1):
        if not finish[j]:
            continue
        rows = []
        for i in range(max(0, j-longest), j):
            if prefixes[i] and s[i:j] in dictionary:
                rows.extend((p+' ' if p else '')+s[i:j] for p in prefixes[i])
        prefixes[j] = rows
    return sorted(prefixes[n])


def sentence_count(s, words):
    dictionary = set(words); n = len(s); ways = [1]+[0]*n
    for j in range(1, n+1):
        ways[j] = sum(ways[i] for i in range(max(0, j-10), j) if s[i:j] in dictionary)
    return ways[n]


def unpruned_dfs_nodes(s, words):
    """DFS calls an unpruned backtracking search makes: one per segmentation of each reachable prefix."""
    dictionary = set(words); n = len(s); ways = [1]+[0]*n
    for j in range(1, n+1):
        ways[j] = sum(ways[i] for i in range(max(0, j-10), j) if s[i:j] in dictionary)
    return sum(ways)


def noise_words(rng, count, banned, letters='defghijklmnopqrstuvwxyz'):
    out = set()
    while len(out) < count:
        w = ''.join(rng.choice(letters) for _ in range(rng.randint(1, 10)))
        if w not in banned:
            out.add(w)
    return sorted(out)


def padded(rng, words, size=1000, letters='defghijklmnopqrstuvwxyz'):
    words = list(dict.fromkeys(words))
    words += noise_words(rng, size-len(words), set(words), letters)
    rng.shuffle(words)
    return words


# 144 -----------------------------------------------------------------------

def preorder_morris(packet):
    """Morris preorder: threads predecessor right links in copied arrays, no stack."""
    if packet['root'] is None:
        return []
    values = packet['values']; left = list(packet['left']); right = list(packet['right'])
    out = []; current = packet['root']
    while current is not None:
        if left[current] is None:
            out.append(values[current]); current = right[current]
            continue
        pred = left[current]
        while right[pred] is not None and right[pred] != current:
            pred = right[pred]
        if right[pred] is None:
            out.append(values[current]); right[pred] = current; current = left[current]
        else:
            right[pred] = None; current = right[current]
    return out


# Independent expected values -------------------------------------------------

_CACHE = {}


def independent_expected(pid, args):
    validate(pid, args)
    key = (pid, _key(args))
    if key not in _CACHE:
        if pid == 126:
            value = ladders_two_sided(*args)
        elif pid == 140:
            value = sentences_forward_feasible(*args)
        elif pid == 129:
            value = root_leaf_sum_linear(args[0])
        else:
            value = preorder_morris(args[0])
        _CACHE[key] = value
    return _CACHE[key]


# Rows ------------------------------------------------------------------------

def boundary_rows(pid):
    rng = random.Random(20261028*11+pid); rows = []
    def add(args, isolate=False, **checks):
        expected = independent_expected(pid, args)
        if 'paths' in checks and len(expected) != checks['paths']:
            raise ValueError('closed-form ladder count disagrees with two-sided enumeration')
        if 'count' in checks and len(expected) != checks['count']:
            raise ValueError('sentence count recurrence disagrees with forward table')
        if 'value' in checks and expected != checks['value']:
            raise ValueError('analytic value disagrees with independent reference')
        if pid == 126 and sum(map(len, expected)) > LADDER_OUTPUT_WORDS_MAX:
            raise ValueError('ladder output above conservative promise')
        if pid == 140 and sum(map(len, expected)) > SENTENCE_OUTPUT_CHARS_MAX:
            raise ValueError('sentence output above conservative promise')
        row = {'args': args, 'expected': expected, 'category': 'boundary-independent-reference'}
        if isolate:
            row['isolate'] = True
        rows.append(row)
    if pid == 126:
        # Max-size grid dictionaries: C(14,7)=3432 ladders of 15 words; begin in and out of the list.
        for include in (False, True):
            args, paths = grid_case(rng, 25, 20, (0, 0), (7, 7), include_begin=include)
            add(args, True, paths=paths)
        # Grid times {a,b,...}: 12!/(5!6!1!) = 5544 ladders of 13 words.
        args, paths = grid_case(rng, 20, 12, (0, 0, 'a'), (5, 6, 'b'), letters='ab'); add(args, True, paths=paths)
        # Long strip: C(52,2) = 1326 ladders of 53 words, depth 52.
        args, paths = grid_case(rng, 51, 9, (0, 0), (50, 2)); add(args, True, paths=paths)
        # Deep reachable graphs with few answers and about 2**24 shortest prefixes to dead ends.
        for end in ((24, 0), (22, 2), (23, 1)):
            args, paths = grid_case(rng, 25, 20, (0, 0), end); add(args, True, paths=paths)
        # Interior begin/end, both directions on the grid: C(12,6)=924 ladders.
        args, paths = grid_case(rng, 25, 20, (15, 12), (9, 6)); add(args, True, paths=paths)
        # Hypercube Q5 inside {a,b,c}^5: 5! = 120 ladders; c letters only add longer routes.
        cube = [''.join(w) for w in __import__('itertools').product('abc', repeat=5)]
        rng.shuffle(cube)
        add(['aaaaa', 'bbbbb', [w for w in cube if w != 'aaaaa']], True, paths=120)
        add(['abcab', 'cabca', cube], True, paths=120)
        # 26 one-letter words: every pair adjacent.
        letters = [chr(97+i) for i in range(26)]
        add(['a', 'z', letters], value=[['a', 'z']])
        add(['q', 'm', [c for c in letters if c != 'q']], value=[['q', 'm']])
        # Max-size dictionaries whose end is present but unreachable.
        dense = [''.join(w) for w in __import__('itertools').product('abcd', repeat=5)]
        rng.shuffle(dense)
        add(['aaaaa', 'zzzzz', dense[:499]+['zzzzz']], True, value=[])
        lonely = [w for w in dense if w != 'aaaaa'][:499]+['aaaaa']
        add(['zzzzz', lonely[0], lonely], True, value=[])
        # Random dense reachable graphs over small alphabets, 500 words.
        for alphabet, length in (('abcde', 4), ('abcd', 5), ('abc', 5), ('abcdefgh', 3)):
            universe = [''.join(w) for w in __import__('itertools').product(alphabet, repeat=length)]
            for _ in range(2):
                words = rng.sample(universe, min(500, len(universe)-1))
                begin = rng.choice([w for w in universe if w not in words] or universe)
                end = max(words, key=lambda w: (sum(a != b for a, b in zip(w, begin)), w))
                add([begin, end, words], True)
        # Sparse random three-letter dictionaries; end chosen far from begin in its component.
        for _ in range(3):
            words = sorted({''.join(rng.choice('abcdefghijklm') for _ in range(3)) for _ in range(700)})[:500]
            rng.shuffle(words)
            begin = words[0]; dist = {begin: 0}; queue = [begin]; present = set(words)
            for v in queue:
                for i in range(3):
                    for c in 'abcdefghijklm':
                        u = v[:i]+c+v[i+1:]
                        if u in present and u not in dist:
                            dist[u] = dist[v]+1; queue.append(u)
            end = max(dist, key=lambda w: (dist[w], w))
            add([begin, end, words], True)
        # Small cross-checkable rows (at most 15 words) with letters a..e.
        for _ in range(40):
            length = rng.randint(1, 4)
            universe = sorted({''.join(rng.choice('abcde') for _ in range(length)) for _ in range(40)})
            if len(universe) < 3:
                continue
            words = rng.sample(universe, min(len(universe), rng.randint(2, 15)))
            begin = rng.choice(universe); end = rng.choice([w for w in words if w != begin] or [w for w in universe if w != begin])
            if end not in words and rng.random() < 0.8:
                continue
            add([begin, end, words])
    elif pid == 129:
        # Right-only chains, including the exact 2**31-1 bound.
        add([tree_packet([2, 1, 4, 7, 4, 8, 3, 6, 4, 7], *path_shape('R'*9))], value=SUM_LIMIT)
        add([tree_packet([2, 1, 4, 7, 4, 8, 3, 6, 4, 7], *path_shape('R'*9), rng)], value=SUM_LIMIT)
        add([tree_packet([1, 9, 9, 9, 9, 9, 9, 9, 9, 9], *path_shape('R'*9))], value=1999999999)
        add([tree_packet([0, 0, 0, 0, 0, 0, 0, 0, 0, 9], *path_shape('R'*9))], value=9)
        add([tree_packet([9, 0], *path_shape('R'))], value=90)
        add([tree_packet([5, 0, 0], *path_shape('RL'))], value=500)
        for length in range(2, 11):
            for sides in ('R'*(length-1), ('RL'*5)[:length-1], ('LR'*5)[:length-1], ''.join(rng.choice('LR') for _ in range(length-1))):
                digits = [rng.randrange(10) for _ in range(length)]
                if length == 10:
                    digits[0] = rng.randrange(2)
                add([tree_packet(digits, *path_shape(sides), rng if rng.random() < 0.5 else None)],
                    value=int(''.join(map(str, digits))))
        # Right child only at the root, then a bushy left-free subtree.
        add([tree_packet([3, 4, 5, 6], [None, 2, None, None], [1, 3, None, None])], value=345+346)
        # Sparse random trees, right-biased and left-biased, digits 0..9.
        for n, right_bias, deep_bias in ((12, 0.9, 0.7), (25, 0.8, 0.5), (60, 0.7, 0.6), (120, 0.85, 0.4), (300, 0.5, 0.3)):
            for _ in range(3):
                left, right = random_shape(n, rng, 10, right_bias, deep_bias)
                packet = tree_packet([0]*n, left, right, rng); tune_digits(packet, rng.randrange(SUM_LIMIT//2, SUM_LIMIT+1), rng)
                add([packet], n >= 300)
        # Maximum-size sparse trees with sums tuned to the 32-bit bound and just below it.
        for target, right_bias in ((SUM_LIMIT, 0.8), (SUM_LIMIT, 0.5), (SUM_LIMIT-1, 0.9), (SUM_LIMIT-7, 0.3), (2**31-10**6, 0.95)):
            left, right = random_shape(1000, rng, 10, right_bias, 0.35)
            packet = tree_packet([0]*1000, left, right, rng); total = tune_digits(packet, target, rng)
            add([packet], True, value=total)
        # Every internal node has only a right child except a left-only spine node.
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
        add([tree_packet(values, [None, None, None, None, 5, None, None, None, None, None], [1, 2, 3, 4, None, 6, 7, 8, 9, None], None)], value=1234567891)
    elif pid == 140:
        a = ['a'*k for k in range(1, 11)]
        # No full segmentation, 2**19-scale partial ones; blocker present only inside unusable words.
        add(['a'*19+'b', padded(rng, a+['bb', 'abb', 'bab', 'bba'])], True, value=[])
        add(['a'*19+'b', a], True, value=[])
        bits = ''.join(rng.choice('ab') for _ in range(19))
        binary = [''.join(w) for k in range(1, 9) for w in __import__('itertools').product('ab', repeat=k)]
        longer = sorted({bits[i:i+k] for k in (9, 10) for i in range(len(bits)-k+1)})
        add([bits+'c', padded(rng, binary+longer+['cc', 'ca', 'cb'])], True, value=[])
        add(['a'*10+'b'+'a'*9, padded(rng, a+['bb'])], True, value=[])
        # Feasible only through one late word, with 2**19-scale dead partials.
        add(['a'*19+'b', padded(rng, a+['a'*9+'b'])], True, count=512)
        add(['a'*19+'b', padded(rng, a[1:]+['ab'])], True, count=sentence_count('a'*19+'b', a[1:]+['ab']))
        # High-but-bounded multiplicity at the conservative 10**5-character bound.
        add(['a'*20, padded(rng, a[1:])], True, count=3996)
        add(['a'*20, padded(rng, ['a', 'aaa', 'a'*6, 'a'*9])], True, count=3304)
        for parts in ((2, 3, 4, 5, 6, 7, 8, 9, 10), (1, 4, 5, 6, 8), (2, 3, 5)):
            s = ''.join(rng.choice('ab') for _ in range(20))
            words = sorted({s[i:i+k] for k in parts for i in range(len(s)-k+1)})
            extra = [w for w in (''.join(rng.choice('ab') for _ in range(rng.choice(parts))) for _ in range(300)) if w not in words]
            add([s, padded(rng, words+extra)], True, count=sentence_count(s, words))
        # Maximum word length and string length, one answer.
        add(['a'*20, padded(rng, ['a'*10])], value=['aaaaaaaaaa aaaaaaaaaa'])
        add(['abcdefghijabcdefghij', padded(rng, ['abcdefghij', 'abcde', 'fghij', 'abc', 'defghij'], letters='klmnopqrstuvwxyz')], True,
            count=sentence_count('abcdefghijabcdefghij', ['abcdefghij', 'abcde', 'fghij', 'abc', 'defghij']))
        # Random strings over four letters with random substring dictionaries, rejection-sampled into bounds.
        made = 0
        while made < 10:
            s = ''.join(rng.choice('abcd') for _ in range(rng.randint(14, 20)))
            subs = sorted({s[i:j] for i in range(len(s)) for j in range(i+1, min(len(s), i+10)+1)})
            words = rng.sample(subs, max(1, len(subs)//rng.randint(3, 8)))
            count = sentence_count(s, words)
            if 0 < count <= 2500 and sum(map(len, sentences_forward_feasible(s, words))) <= SENTENCE_OUTPUT_CHARS_MAX:
                add([s, padded(rng, words, 1000 if made % 2 else rng.randint(len(words), 400), letters='efghijklmnop')], True, count=count)
                made += 1
        # Small cross-checkable rows: strings up to 16 characters.
        for _ in range(40):
            s = ''.join(rng.choice('abc') for _ in range(rng.randint(1, 16)))
            subs = sorted({s[i:j] for i in range(len(s)) for j in range(i+1, min(len(s), i+10)+1)})
            words = rng.sample(subs, max(1, len(subs)//rng.randint(2, 6)))+[w for w in ('ca', 'bab', 'cccc') if rng.random() < 0.5]
            add([s, sorted(set(words))])
        # 64 distinct small dead-end rows, left un-isolated so the unchanged batch policy packs
        # 32 per process. Each forces about 5*10**5 unpruned DFS calls and almost no pruned work.
        pairs = [(base, block) for base in 'abcdefghijklmnopqrstuvwxyz' for block in 'zyxw' if block != base][:64]
        for base, block in pairs:
            add([base*19+block, [base*k for k in range(1, 11)]+[block*2, base+block+block]], value=[])
    elif pid == 144:
        def values(n):
            return [rng.choice((-100, 100, 0, rng.randint(-100, 100))) for _ in range(n)]
        add([tree_packet(values(100), *path_shape('R'*99))], True)
        add([tree_packet(values(100), *path_shape('R'*99), rng)], True)
        add([tree_packet(values(100), *path_shape('RL'*49+'R'))], True)
        add([tree_packet(values(100), *path_shape('LR'*49+'L'), rng)], True)
        add([tree_packet(values(100), *path_shape(''.join(rng.choice('LR') for _ in range(99))), rng)], True)
        add([tree_packet([1, 2], *path_shape('R'))], value=[1, 2])
        add([tree_packet([1, 2, 3], *path_shape('RL'))], value=[1, 2, 3])
        # Right spine with left leaves, and left spine with right leaves.
        n = 99; left = [None]*n; right = [None]*n
        for i in range(0, n-2, 2):
            right[i] = i+2; left[i] = i+1
        add([tree_packet(values(n), left, right, rng)], True)
        left = [None]*n; right = [None]*n
        for i in range(0, n-2, 2):
            left[i] = i+2; right[i] = i+1
        add([tree_packet(values(n), left, right, rng)], True)
        # Sparse random trees at max size, right-biased, left-biased and bushy.
        for right_bias, deep_bias in ((0.9, 0.8), (0.8, 0.5), (0.5, 0.9), (0.1, 0.8), (0.5, 0.0), (0.95, 0.2)):
            for _ in range(2):
                left, right = random_shape(100, rng, 100, right_bias, deep_bias)
                add([tree_packet(values(100), left, right, rng)], True)
        # Small sparse trees of every size 2..40 with random sides.
        for n in range(2, 41):
            left, right = random_shape(n, rng, n, 0.7, 0.5)
            add([tree_packet(values(n), left, right, rng if n % 2 else None)])
    return rows


def build_boundary(pid, existing_args):
    """Boundary rows whose args do not repeat an existing row."""
    seen = {_key(args) for args in existing_args}; out = []
    for row in boundary_rows(pid):
        key = _key(row['args'])
        if key not in seen:
            seen.add(key); out.append(row)
    return out
