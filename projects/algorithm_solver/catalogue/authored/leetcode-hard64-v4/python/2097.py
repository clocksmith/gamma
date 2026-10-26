"""2097. Valid Arrangement of Pairs."""

from collections import Counter, defaultdict


def solve(pairs: list[list[int]]) -> list[list[int]]:
    """Iterative Hierholzer traversal of the guaranteed Euler trail; O(E) time and space. Inputs are preserved."""
    neighbors = defaultdict(list)
    balance = Counter()
    for first, second in pairs:
        neighbors[first].append(second)
        balance[first] += 1
        balance[second] -= 1
    start = pairs[0][0]
    for node, difference in balance.items():
        if difference == 1:
            start = node
            break
    stack = [start]
    reverse_path = []
    while stack:
        node = stack[-1]
        if neighbors[node]:
            stack.append(neighbors[node].pop())
        else:
            reverse_path.append(stack.pop())
    path = reverse_path[::-1]
    return [[path[index], path[index + 1]] for index in range(len(path) - 1)]


class Solution:
    def validArrangement(self, pairs: list[list[int]]) -> list[list[int]]:
        return solve(pairs)
