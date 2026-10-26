"""Independent replay of identity-preserving tree/list operations.

Only admitted input values and observer pointer IDs are consumed. The execution
side's effect planner is deliberately not imported or consulted.
"""
from collections import deque
from math import gcd

IDS = {814, 2074, 2807}


def identical(left, right):
    if type(left) is not type(right): return False
    if type(left) is dict:
        return set(left) == set(right) and all(identical(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(identical(left[i], right[i]) for i in range(len(left)))
    return left == right


def decode_original(pid, args):
    if type(args) is not list or len(args) != 1 or type(args[0]) is not dict:
        raise ValueError('one encoded node argument required')
    marker = '__tree_node__' if pid == 814 else '__list_node__'
    if set(args[0]) != {marker}: raise ValueError('wrong input node shape')
    raw = args[0][marker]
    if type(raw) is not list or not raw or type(raw[0]) is not int:
        raise ValueError('nonempty node input required')
    if pid != 814:
        if any(type(value) is not int for value in raw): raise ValueError('integer list values required')
        return [{'value': value, 'next': i+1 if i+1 < len(raw) else None} for i, value in enumerate(raw)]
    states = [{'value': raw[0], 'left': None, 'right': None}]
    parents = deque([0]); cursor = 1
    while parents and cursor < len(raw):
        parent = parents.popleft()
        for edge in ('left', 'right'):
            if cursor == len(raw): break
            value = raw[cursor]; cursor += 1
            if value is not None:
                if type(value) is not int: raise ValueError('integer tree values required')
                states[parent][edge] = len(states)
                parents.append(len(states)); states.append({'value': value, 'left': None, 'right': None})
    if any(value is not None for value in raw[cursor:]): raise ValueError('unreachable input nodes')
    return states


def valid_states(states, tree):
    if type(states) is not list: return False
    fields = {'value', 'left', 'right'} if tree else {'value', 'next'}
    for node in states:
        if type(node) is not dict or set(node) != fields or type(node['value']) is not int: return False
        for name in fields - {'value'}:
            target = node[name]
            if target is not None and (type(target) is not int or not 0 <= target < len(states)): return False
    return True


def encode_graph(states, tree):
    values, visited = [], set()
    queue = deque([0])
    while queue:
        node = queue.popleft()
        if node is None:
            values.append(None); continue
        if node in visited: raise ValueError('cycle or repeated node')
        visited.add(node); values.append(states[node]['value'])
        if tree: queue.extend((states[node]['left'], states[node]['right']))
        elif states[node]['next'] is not None: queue.append(states[node]['next'])
    if tree:
        while values and values[-1] is None: values.pop()
    return {'__tree_node__' if tree else '__list_node__': values}


def expected_tree_links(before):
    # Explicit DFS postorder derives which original subtrees contain a one.
    keep, stack = {}, [(0, False)]
    while stack:
        index, expanded = stack.pop(); node = before[index]
        children = [node[side] for side in ('left', 'right') if node[side] is not None]
        if not expanded:
            stack.append((index, True)); stack.extend((child, False) for child in children)
        else:
            keep[index] = node['value'] == 1 or any(keep[child] for child in children)
    return keep


def check(pid, args, record):
    try:
        if pid not in IDS: raise ValueError('unsupported identity contract')
        before = decode_original(pid, args)
        witness = record.get('node_identity')
        if type(witness) is not dict or set(witness) != {'before', 'after', 'argument_roots', 'result_root'}:
            return 'node_identity_effects'
        if not identical(witness['before'], before) or not identical(witness['argument_roots'], [0]):
            return 'node_identity_effects'
        after = witness['after']; n = len(before); tree = pid == 814
        if not valid_states(after, tree): return 'node_identity_effects'
        if len(after) != (2*n-1 if pid == 2807 else n): return 'node_identity_effects'
        if any(after[i]['value'] != before[i]['value'] for i in range(n)):
            return 'node_identity_effects'
        result_root = 0
        if pid == 814:
            keep = expected_tree_links(before)
            result_root = 0 if keep[0] else None
            for i in range(n):
                for edge in ('left', 'right'):
                    original_child = before[i][edge]
                    allowed_child = original_child if original_child is not None and keep[original_child] else None
                    if not identical(after[i][edge], allowed_child): return 'node_identity_effects'
        elif pid == 2074:
            # Find the original position of each node in the output permutation
            # from triangular group starts and each final group's actual size.
            group, start, order = 1, 0, []
            while start < n:
                end = min(n, start+group)
                order.extend(range(end-1, start-1, -1) if (end-start) % 2 == 0 else range(start, end))
                start = end; group += 1
            for position, index in enumerate(order):
                following = order[position+1] if position+1 < n else None
                if not identical(after[index]['next'], following): return 'node_identity_effects'
        else:
            for i in range(n):
                following = n+i if i+1 < n else None
                if not identical(after[i]['next'], following): return 'node_identity_effects'
            for i in range(n-1):
                new = after[n+i]
                if new['value'] != gcd(before[i]['value'], before[i+1]['value']) or not identical(new['next'], i+1):
                    return 'node_identity_effects'
        if not identical(witness['result_root'], result_root): return 'node_identity_effects'
        if not identical(record.get('args_before'), [encode_graph(before, tree)]): return 'input_effects'
        if not identical(record.get('args_after'), [encode_graph(after, tree)]): return 'input_effects'
        aliases = [] if result_root is None else [['result', 'args.0']]
        if not identical(record.get('alias_edges'), aliases): return 'return_aliases'
        return None
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        return 'node_identity_effects'
