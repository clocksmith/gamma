"""Hack2Hire 6772e85ddd9437f8aa275b02 (Find Path in N-ary Tree, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def parse(tree):
    values = [tree[0]]
    children = [[]]
    parent = -1
    for x in tree[1:]:
        if x is None:
            parent += 1
        else:
            children[parent].append(len(values))
            values.append(x)
            children.append([])
    return values, children


def solve(tree, path):
    values, children = parse(tree)
    m = len(path)
    fail = [0] * m
    k = 0
    for i in range(1, m):
        while k > 0 and path[i] != path[k]:
            k = fail[k - 1]
        if path[i] == path[k]:
            k += 1
        fail[i] = k
    memo = {}
    in_path = set(path)

    def step(state, value):
        # automaton transition from state (< m) on value, memoized per pair
        if value not in in_path:
            return 0
        chain = []
        while True:
            key = state * 100001 + value
            if key in memo:
                result = memo[key]
                break
            if path[state] == value:
                result = state + 1
                break
            if state == 0:
                result = 0
                break
            chain.append(key)
            state = fail[state - 1]
        memo[key] = result
        for key in chain:
            memo[key] = result
        return result

    stack = [(0, 0)]
    while stack:
        v, state = stack.pop()
        s = step(state, values[v])
        if s == m:
            return True
        for c in children[v]:
            stack.append((c, s))
    return False


class Solution:
    def pathExistsAnywhere(self, tree, path):
        return solve(tree, path)
