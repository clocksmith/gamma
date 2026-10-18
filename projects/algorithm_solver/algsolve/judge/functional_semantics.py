"""Host-owned validators for functional tasks with non-unique valid outputs."""


def topological_order(args, observed):
    if (len(args) != 2 or type(args[0]) is not int or args[0] < 0
            or not isinstance(args[1], list)):
        raise ValueError('Invalid course-order input')
    n, edges = args
    adjacency, indegree = [[] for _ in range(n)], [0] * n
    for edge in edges:
        if (not isinstance(edge, list) or len(edge) != 2
                or any(type(v) is not int or not 0 <= v < n for v in edge)):
            raise ValueError('Invalid course prerequisite')
        course, prerequisite = edge
        adjacency[prerequisite].append(course)
        indegree[course] += 1
    # An empty answer is valid only when no complete order exists (or n == 0).
    ready = [i for i in range(n) if indegree[i] == 0]
    for vertex in ready:
        for neighbor in adjacency[vertex]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
    if len(ready) != n:
        return observed == []
    if (not isinstance(observed, list) or len(observed) != n
            or any(type(v) is not int or not 0 <= v < n for v in observed)
            or len(set(observed)) != n):
        return False
    position = {vertex: i for i, vertex in enumerate(observed)}
    return all(position[prerequisite] < position[course] for course, prerequisite in edges)


def alphabet_board_path(args, observed):
    if (len(args) != 1 or type(args[0]) is not str or not 1 <= len(args[0]) <= 100
            or any(not 'a' <= ch <= 'z' for ch in args[0])):
        raise ValueError('Invalid alphabet-board target')
    if type(observed) is not str:
        return False
    row = col = minimum = 0
    for ch in args[0]:
        r, c = divmod(ord(ch)-ord('a'), 5)
        minimum += abs(row-r) + abs(col-c) + 1
        row, col = r, c
    if len(observed) != minimum:
        return False
    row = col = 0
    produced = []
    for move in observed:
        if move == '!':
            produced.append(chr(ord('a')+5*row+col))
            continue
        if move not in 'UDLR':
            return False
        dr, dc = {'U':(-1,0),'D':(1,0),'L':(0,-1),'R':(0,1)}[move]
        row, col = row+dr, col+dc
        if not (0 <= row <= 5 and 0 <= col < 5 and (row < 5 or col == 0)):
            return False
    return ''.join(produced) == args[0]


def nonaverage_neighbors(args, observed):
    from collections import Counter
    if (len(args) != 1 or type(args[0]) is not list or not 3 <= len(args[0]) <= 100000
            or any(type(v) is not int or not 0 <= v <= 100000 for v in args[0])
            or len(set(args[0])) != len(args[0])):
        raise ValueError('Invalid distinct nonnegative integer array')
    return (type(observed) is list and all(type(v) is int for v in observed)
            and Counter(observed) == Counter(args[0])
            and all(2*observed[i] != observed[i-1]+observed[i+1] for i in range(1,len(observed)-1)))


VALIDATORS = {'topological_order': topological_order, 'alphabet_board_path': alphabet_board_path,
              'nonaverage_neighbors': nonaverage_neighbors}


def unordered_outer(expected, observed):
    """Only outer order is free; retain inner order, types and multiplicity."""
    import json
    from collections import Counter
    if type(expected) is not list:
        raise ValueError('Expected an outer list')
    encode = lambda v: json.dumps(v, sort_keys=True, allow_nan=False, separators=(',', ':'))
    wanted = Counter(encode(v) for v in expected)
    if type(observed) is not list:
        return False
    return wanted == Counter(encode(v) for v in observed)


def edge_index_groups(args, expected, observed):
    """Compare critical/pseudo-critical sets without changing group identity.

    This checks agreement with the host's expected membership, not an independent
    proof of the MST classification. Duplicates and bool-as-int indices fail.
    """
    if len(args) != 2 or type(args[1]) is not list:
        raise ValueError('Invalid edge-classification input')
    count = len(args[1])

    def groups(value):
        if type(value) is not list or len(value) != 2 or any(type(g) is not list for g in value):
            return None
        flat = [i for group in value for i in group]
        if (any(type(i) is not int or not 0 <= i < count for i in flat)
                or len(set(flat)) != len(flat)):
            return None
        return [set(group) for group in value]

    wanted = groups(list(expected) if type(expected) is tuple else expected)
    if wanted is None:
        raise ValueError('Invalid expected edge-index groups')
    actual = groups(observed)
    return actual is not None and actual == wanted
