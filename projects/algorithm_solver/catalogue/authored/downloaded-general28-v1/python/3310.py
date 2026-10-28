"""3310. Remove Methods From Project (Medium).

Specification: https://leetcode.com/problems/remove-methods-from-project/description/
"""


def solve(n: int, k: int, invocations: list[list[int]]) -> list[int]:
    adj = [[] for _ in range(n)]
    for a, b in invocations:
        adj[a].append(b)
    suspicious = {k}
    stack = [k]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in suspicious:
                suspicious.add(v)
                stack.append(v)
    for a, b in invocations:
        if a not in suspicious and b in suspicious:
            return list(range(n))
    return [i for i in range(n) if i not in suspicious]


class Solution:
    def remainingMethods(self, n: int, k: int, invocations: list[list[int]]) -> list[int]:
        return solve(n, k, invocations)
