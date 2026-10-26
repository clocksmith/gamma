"""Independent host replay of statement-defined results and local effects.

This module deliberately does not import the execution comparator. It accepts
only the already domain-admitted case and retained sandbox observation.
"""
from collections import Counter, deque
import math

SET_RESULTS = {282: str, 472: str, 784: str, 884: str, 2933: str, 1606: int, 2951: int, 2951: int}
APPROXIMATE = {813: 1e-6, 1377: 1e-5, 1701: 1e-5, 3194: 0.0}
NODES = {814: 'TreeNode', 876: 'ListNode', 998: 'TreeNode', 1008: 'TreeNode',
         1382: 'TreeNode', 2074: 'ListNode', 2196: 'TreeNode', 2807: 'ListNode', 2816: 'ListNode'}


def normalized(value):
    if isinstance(value, dict):
        keys = set(value)
        if keys == {'__tree_node__'}:
            sequence = value['__tree_node__']
            if type(sequence) is not list:
                raise ValueError('invalid tree encoding')
            end = len(sequence)
            while end and sequence[end - 1] is None:
                end -= 1
            return {'__tree_node__': normalized(sequence[:end])} if end else None
        if keys == {'__list_node__'} and value['__list_node__'] == []:
            return None
        return {key: normalized(item) for key, item in value.items()}
    if type(value) is list:
        return [normalized(item) for item in value]
    if type(value) is int and not -(2**53 - 1) <= value <= 2**53 - 1:
        return {'__gamma_bigint_v1__': str(value)}
    return value


def identical(left, right):
    if type(left) != type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(identical(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(identical(left[i], right[i]) for i in range(len(left)))
    return left == right


def integer_list(value):
    return type(value) is list and all(type(x) is int for x in value)


def unique_collection(got, expected, element):
    return (type(got) is list and all(type(x) is element for x in got) and
            len(got) == len(set(got)) and Counter(got) == Counter(expected))


def balanced_bst(encoded, original):
    def unpack(raw):
        if type(raw) is not dict or set(raw) != {'__tree_node__'}:
            raise ValueError('tree wrapper required')
        values = raw['__tree_node__']
        if type(values) is not list or not values or type(values[0]) is not int:
            raise ValueError('root required')
        # Each node stores value, left index, right index. BFS decoding uses
        # independently tracked live parent slots rather than numeric padding.
        nodes = [[values[0], None, None]]
        parents = deque([0]); cursor = 1
        while parents and cursor < len(values):
            parent = parents.popleft()
            for side in (1, 2):
                if cursor == len(values): break
                item = values[cursor]; cursor += 1
                if item is not None:
                    if type(item) is not int: raise ValueError('integer node required')
                    nodes[parent][side] = len(nodes)
                    parents.append(len(nodes)); nodes.append([item, None, None])
        if any(x is not None for x in values[cursor:]):
            raise ValueError('unreachable node')
        return nodes
    nodes, previous = unpack(encoded), unpack(original)
    if Counter(n[0] for n in nodes) != Counter(n[0] for n in previous): return False
    heights, minimum, maximum = {}, {}, {}
    for i in reversed(range(len(nodes))):
        value, left, right = nodes[i]
        if left is not None and maximum[left] >= value: return False
        if right is not None and minimum[right] <= value: return False
        lh, rh = heights.get(left, 0), heights.get(right, 0)
        if abs(lh - rh) > 1: return False
        heights[i] = 1 + max(lh, rh)
        minimum[i] = minimum.get(left, value); maximum[i] = maximum.get(right, value)
    return True


def has_cycle(vertices, edges):
    adjacency = {v: set() for v in vertices}
    incoming = {v: 0 for v in vertices}
    for before, after in edges:
        if after not in adjacency[before]:
            adjacency[before].add(after); incoming[after] += 1
    ready = deque(v for v in vertices if incoming[v] == 0)
    removed = 0
    while ready:
        vertex = ready.popleft(); removed += 1
        for child in adjacency[vertex]:
            incoming[child] -= 1
            if incoming[child] == 0: ready.append(child)
    return removed != len(incoming)


def stamp_possible(stamp, target):
    # A window becomes usable when every mismatching target location has
    # already been erased. Propagate erased positions through those blockers.
    blocked_by = [set() for _ in target]
    blockers, covered = [], []
    ready = deque()
    for start in range(len(target) - len(stamp) + 1):
        mismatch = {start+i for i, char in enumerate(stamp) if target[start+i] != char}
        blockers.append(len(mismatch)); covered.append(range(start, start+len(stamp)))
        for position in mismatch: blocked_by[position].add(start)
        if not mismatch: ready.append(start)
    erased = set()
    while ready:
        window = ready.popleft()
        for position in covered[window]:
            if position in erased: continue
            erased.add(position)
            for waiting in blocked_by[position]:
                blockers[waiting] -= 1
                if blockers[waiting] == 0: ready.append(waiting)
    return len(erased) == len(target)


def groups_possible(n, groups, prerequisites):
    group_of = [value if value >= 0 else ('ungrouped', item) for item, value in enumerate(groups)]
    item_edges = [(before, item) for item, values in enumerate(prerequisites) for before in values]
    cross_group = [(group_of[a], group_of[b]) for a, b in item_edges if group_of[a] != group_of[b]]
    return not has_cycle(list(range(n)), item_edges) and not has_cycle(list(dict.fromkeys(group_of)), cross_group)


def result_valid(pid, args, answer, expected):
    if pid in SET_RESULTS:
        return unique_collection(answer, expected, SET_RESULTS[pid])
    if pid in APPROXIMATE:
        if type(answer) not in (int, float) or not math.isfinite(answer): return False
        delta = abs(answer - expected); tolerance = APPROXIMATE[pid]
        return delta <= tolerance
    if pid == 767:
        if type(answer) is not str: return False
        if not answer:
            counts = Counter(args[0]); return max(counts.values()) > (len(args[0]) + 1) // 2
        return sorted(answer) == sorted(args[0]) and not any(answer[i] == answer[i-1] for i in range(1, len(answer)))
    if pid == 936:
        if not integer_list(answer) or len(answer) > 10 * len(args[1]): return False
        if not answer: return not stamp_possible(*args)
        stamp, target = args
        written = {}
        for start in answer:
            if start < 0 or start + len(stamp) > len(target): return False
            written.update({start + index: character for index, character in enumerate(stamp)})
        return all(written.get(index) == character for index, character in enumerate(target))
    if pid == 1203:
        if not integer_list(answer): return False
        n, _, groups, dependencies = args
        if not answer: return not groups_possible(n, groups, dependencies)
        if len(answer) != n or set(answer) != set(range(n)): return False
        seen, finished_groups, active_group = set(), set(), None
        for item in answer:
            if any(before not in seen for before in dependencies[item]): return False
            group = groups[item] if groups[item] >= 0 else ('ungrouped', item)
            if group != active_group:
                if group in finished_groups: return False
                finished_groups.add(active_group); active_group = group
            seen.add(item)
        return True
    if pid == 1382:
        return balanced_bst(answer, args[0])
    if pid == 1489:
        return type(answer) is list and len(answer) == 2 and all(unique_collection(answer[i], expected[i], int) for i in (0, 1))
    if pid == 1548:
        count, roads, names, target = args
        if not integer_list(answer) or len(answer) != len(target) or any(x < 0 or x >= count for x in answer): return False
        neighbors = [set() for _ in range(count)]
        for left, right in roads:
            neighbors[left].add(right); neighbors[right].add(left)
        if any(answer[i] not in neighbors[answer[i-1]] for i in range(1, len(answer))): return False
        # Backwards optimal suffix costs, independently of the candidate path.
        cost = [int(name != target[-1]) for name in names]
        for index in range(len(target) - 2, -1, -1):
            cost = [int(names[node] != target[index]) + min((cost[n] for n in neighbors[node]), default=len(target)+1)
                    for node in range(count)]
        return sum(names[node] != target[index] for index, node in enumerate(answer)) == min(cost)
    if pid == 1901:
        if not integer_list(answer) or len(answer) != 2: return False
        row, column = answer; matrix = args[0]
        if row < 0 or row >= len(matrix) or column < 0 or column >= len(matrix[0]): return False
        adjacent = []
        if row: adjacent.append(matrix[row-1][column])
        if row+1 < len(matrix): adjacent.append(matrix[row+1][column])
        if column: adjacent.append(matrix[row][column-1])
        if column+1 < len(matrix[0]): adjacent.append(matrix[row][column+1])
        return all(value < matrix[row][column] for value in adjacent)
    if pid == 1948:
        if type(answer) is not list or any(type(path) is not list or any(type(part) is not str for part in path) for path in answer): return False
        paths = [tuple(path) for path in answer]
        return len(set(paths)) == len(paths) and Counter(paths) == Counter(tuple(path) for path in expected)
    if pid == 1982:
        n, subset_sums = args
        if not integer_list(answer) or len(answer) != n or any(abs(x) > 10000 for x in answer): return False
        frequencies = Counter({0: 1})
        for item in answer:
            more = Counter({total + item: multiplicity for total, multiplicity in frequencies.items()})
            frequencies.update(more)
        return frequencies == Counter(subset_sums)
    if pid == 2007:
        changed = args[0]
        if not integer_list(answer) or any(x < 0 or x > 100000 for x in answer): return False
        if answer:
            return Counter(answer + [2*x for x in answer]) == Counter(changed)
        # Nonnegative inputs: the smallest remaining value has to be original,
        # with one separate double occurrence (two occurrences for zero).
        remaining = Counter(changed)
        for value in sorted(remaining):
            count = remaining[value]
            if not count: continue
            if value == 0:
                if count % 2: return True
                remaining[value] = 0
            else:
                if remaining[2*value] < count: return True
                remaining[2*value] -= count; remaining[value] = 0
        return False
    if pid == 2392:
        if type(answer) is not list: return False
        k, above, left = args
        if not answer: return has_cycle(list(range(1, k+1)), above) or has_cycle(list(range(1, k+1)), left)
        if len(answer) != k or any(not integer_list(row) or len(row) != k for row in answer): return False
        coordinates = {}
        for row in range(k):
            for column in range(k):
                value = answer[row][column]
                if value == 0: continue
                if value in coordinates or value < 1 or value > k: return False
                coordinates[value] = (row, column)
        if set(coordinates) != set(range(1, k+1)): return False
        return all(coordinates[a][axis] < coordinates[b][axis] for axis, edges in enumerate((above, left)) for a, b in edges)
    if pid == 2733:
        if type(answer) is not int: return False
        values = sorted(args[0])
        return answer == -1 if len(values) < 3 else answer in values[1:-1]
    return identical(normalized(answer), normalized(expected))


def compare(pid, case, record, language):
    if 'error' in record: return 'candidate_error'
    expected = normalized(case['expected'])
    reported_type = record.get('result_type')
    if pid in APPROXIMATE:
        allowed = {'int', 'float'} if language == 'python' else {'number'}
    elif pid in NODES and expected is not None:
        allowed = {NODES[pid] if language == 'python' else 'object'}
    elif type(expected) is dict and set(expected) == {'__gamma_bigint_v1__'}:
        allowed = {'int' if language == 'python' else 'bigint'}
    elif language == 'python':
        allowed = {type(expected).__name__}
    else:
        allowed = {{'NoneType': 'object', 'dict': 'object', 'list': 'object', 'int': 'number',
                    'float': 'number', 'bool': 'boolean', 'str': 'string'}[type(expected).__name__]}
    if reported_type not in allowed: return 'result_type'
    try:
        valid = result_valid(pid, case['args'], record.get('result'), case['expected'])
    except (TypeError, ValueError, KeyError, IndexError, OverflowError):
        valid = False
    if not valid: return 'result_value'
    if pid in (814, 2074, 2807):
        from .verify_node_identity import check
        return check(pid, case['args'], record)
    for field in ('args_before', 'args_after'):
        if not identical(record.get(field), normalized(case['args'])): return 'input_effects'
    required_aliases = []
    if pid == 876:
        middle = len(case['args'][0]['__list_node__']) // 2
        required_aliases = [['result', 'args.0' + '.next' * middle]]
    if not identical(record.get('alias_edges'), required_aliases): return 'return_aliases'
    return None
