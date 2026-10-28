"""2192. All Ancestors of a Node in a Directed Acyclic Graph (Medium).

Specification: https://leetcode.com/problems/all-ancestors-of-a-node-in-a-directed-acyclic-graph/description/
"""


def solve(n: int, edges: list[list[int]]) -> list[list[int]]:
    reverse = [[] for _ in range(n)]
    for src, dst in edges:
        reverse[dst].append(src)
    result = []
    for node in range(n):
        seen = set()
        stack = list(reverse[node])
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(reverse[current])
        result.append(sorted(seen))
    return result


class Solution:
    def getAncestors(self, n: int, edges: list[list[int]]) -> list[list[int]]:
        return solve(n, edges)
