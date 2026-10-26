"""3841. Palindromic Path Queries in a Tree."""
from __future__ import annotations


def solve(n: int, edges: list[list[int]], s: str, queries: list[str]) -> list[bool]:
    """O((n+q) log n) time and O(n log n) space; Euler subtree XOR updates plus binary-lifting LCA."""
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    parent = [0] * n
    depth = [0] * n
    entry = [0] * n
    exit_time = [0] * n
    letters = [1 << (ord(char) - 97) for char in s]
    original = [0] * n
    clock = 0
    stack = [(0, 0, False)]
    while stack:
        node, ancestor, leaving = stack.pop()
        if leaving:
            exit_time[node] = clock
            continue
        parent[node] = ancestor
        entry[node] = clock
        clock += 1
        original[node] = letters[node] ^ (original[ancestor] if node else 0)
        stack.append((node, ancestor, True))
        for child in graph[node]:
            if child != ancestor:
                depth[child] = depth[node] + 1
                stack.append((child, node, False))
    levels = [parent]
    for _ in range(1, n.bit_length()):
        before = levels[-1]
        levels.append([before[before[node]] for node in range(n)])

    def lca(left, right):
        if depth[left] < depth[right]:
            left, right = right, left
        difference = depth[left] - depth[right]
        for bit, ancestors in enumerate(levels):
            if difference & (1 << bit):
                left = ancestors[left]
        if left == right:
            return left
        for ancestors in reversed(levels):
            if ancestors[left] != ancestors[right]:
                left, right = ancestors[left], ancestors[right]
        return parent[left]

    fenwick = [0] * (n + 1)
    def toggle(index, value):
        index += 1
        while index <= n:
            fenwick[index] ^= value
            index += index & -index

    def prefix(node):
        value = original[node]
        index = entry[node] + 1
        while index:
            value ^= fenwick[index]
            index -= index & -index
        return value

    answer = []
    for command in queries:
        operation, first, second = command.split()
        node = int(first)
        if operation == 'update':
            value = 1 << (ord(second) - 97)
            delta = letters[node] ^ value
            letters[node] = value
            toggle(entry[node], delta)
            toggle(exit_time[node], delta)
        else:
            other = int(second)
            parity = prefix(node) ^ prefix(other) ^ letters[lca(node, other)]
            answer.append(parity & (parity - 1) == 0)
    return answer


class Solution:
    def palindromePath(self, n: int, edges: list[list[int]], s: str, queries: list[str]) -> list[bool]:
        return solve(n, edges, s, queries)
