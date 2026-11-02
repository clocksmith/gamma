"""Declared result comparators for the development cohorts (official acceptance rules).

A problem's semantics `comparator` names how a result is accepted when the official
problem accepts more than one answer or a tolerance. Without a declaration callers
keep their own exact comparison. Validators recompute validity from the case
arguments; they never consult a candidate's source. Every validator must also accept
the reference's expected value (enforced by test_comparators.py and the checker).

Kinds:
- float_abs_tolerance: element-wise |got - expected| <= abs_tol; Python results must
  be float when python_result_type is "float".
- unordered_multiset: same elements in any order.
- unordered_nested: outer list in any order, each inner list in any order.
- ordered_groups_unordered_members: group order fixed, members in any order.
- valid_wiggle: a permutation of args[0] with r[0] <= r[1] >= r[2] <= ...
- valid_nearest_leaf: a leaf value at minimum edge distance from the node valued
  args[1] in the level-order tree args[0] (values unique).
- valid_alien_order: "" exactly when no order exists; otherwise every distinct letter
  once, respecting every first-difference constraint of adjacent words.
- valid_k_distance_rearrangement: "" exactly when the reference finds none;
  otherwise a permutation of args[0] with equal characters at least args[1] apart.
Strings are compared by Unicode code point.
"""
from collections import Counter, deque
import json

KINDS = ('float_abs_tolerance', 'unordered_multiset', 'unordered_nested', 'ordered_groups_unordered_members',
         'valid_wiggle', 'valid_nearest_leaf', 'valid_alien_order', 'valid_k_distance_rearrangement')


def _key(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _bag(items):
    return Counter(_key(x) for x in items)


def _float_close(got, expected, comparator, language):
    tol = comparator['abs_tol']
    if isinstance(expected, list):
        return isinstance(got, list) and len(got) == len(expected) and all(
            _float_close(a, b, comparator, language) for a, b in zip(got, expected))
    if isinstance(got, bool) or not isinstance(got, (int, float)):
        return False
    if language == 'python' and comparator.get('python_result_type') == 'float' and not isinstance(got, float):
        return False
    return abs(got - expected) <= tol + 1e-12


def _wiggle(got, args):
    nums = args[0]
    if not isinstance(got, list) or _bag(got) != _bag(nums):
        return False
    return all((got[i] <= got[i + 1]) if i % 2 == 0 else (got[i] >= got[i + 1]) for i in range(len(got) - 1))


def _nearest_leaf(got, args):
    level, k = args[0], args[1]
    if not level or level[0] is None:
        return False
    nodes = [None if v is None else {'val': v, 'kids': []} for v in level]
    parent = {}
    idx = 1
    for i, node in enumerate(nodes):
        if node is None:
            continue
        for _ in range(2):
            if idx < len(nodes):
                child = nodes[idx]
                if child is not None:
                    node['kids'].append(idx)
                    parent[idx] = i
                idx += 1
    start = next((i for i, n in enumerate(nodes) if n is not None and n['val'] == k), None)
    if start is None:
        return False
    dist, queue, leaves = {start: 0}, deque([start]), {}
    while queue:
        i = queue.popleft()
        if not nodes[i]['kids']:
            leaves[nodes[i]['val']] = dist[i]
        for j in nodes[i]['kids'] + ([parent[i]] if i in parent else []):
            if j not in dist:
                dist[j] = dist[i] + 1
                queue.append(j)
    return got in leaves and leaves[got] == min(leaves.values())


def _alien_order(got, expected, args):
    words = args[0]
    if not isinstance(got, str):
        return False
    letters = {ch for w in words for ch in w}
    edges = set()
    for a, b in zip(words, words[1:]):
        for x, y in zip(a, b):
            if x != y:
                edges.add((x, y))
                break
        else:
            if len(a) > len(b):
                return got == '' and expected == ''
    if expected == '':
        return got == ''
    order = list(got)
    if len(order) != len(letters) or set(order) != letters:
        return False
    pos = {ch: i for i, ch in enumerate(order)}
    return all(pos[x] < pos[y] for x, y in edges)


def _k_distance(got, expected, args):
    s, k = args[0], args[1]
    if not isinstance(got, str):
        return False
    if expected == '':
        return got == ''
    chars = list(got)
    if Counter(chars) != Counter(s):
        return False
    last = {}
    for i, ch in enumerate(chars):
        if k > 1 and ch in last and i - last[ch] < k:
            return False
        last[ch] = i
    return True


def compare(got, expected, comparator, args, language, exact):
    """Apply the declared comparator; fall back to the caller's exact comparison."""
    kind = (comparator or {}).get('kind')
    if kind is None:
        return exact(got, expected)
    if kind == 'float_abs_tolerance':
        return _float_close(got, expected, comparator, language)
    if kind == 'unordered_multiset':
        return isinstance(got, list) and _bag(got) == _bag(expected)
    if kind == 'unordered_nested':
        return (isinstance(got, list) and all(isinstance(g, list) for g in got) and
                Counter(_key(sorted(map(_key, g))) for g in got) == Counter(_key(sorted(map(_key, e))) for e in expected))
    if kind == 'ordered_groups_unordered_members':
        return (isinstance(got, list) and len(got) == len(expected) and
                all(isinstance(g, list) and _bag(g) == _bag(e) for g, e in zip(got, expected)))
    if kind == 'valid_wiggle':
        return _wiggle(got, args)
    if kind == 'valid_nearest_leaf':
        return _nearest_leaf(got, args)
    if kind == 'valid_alien_order':
        return _alien_order(got, expected, args)
    if kind == 'valid_k_distance_rearrangement':
        return _k_distance(got, expected, args)
    raise ValueError(f'Unknown comparator kind: {kind}')
