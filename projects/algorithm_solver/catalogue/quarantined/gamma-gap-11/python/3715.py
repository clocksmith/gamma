"""3715. Sum of Perfect Square Ancestors."""
from __future__ import annotations
from math import isqrt


def solve(n: int, edges: list[list[int]], nums: list[int]) -> int:
    """O(M log log M + n log M) time and O(n + M) space; iterative traversal counts matching square-free kernels."""
    maximum = max(nums)
    smallest = list(range(maximum + 1))
    for prime in range(2, isqrt(maximum) + 1):
        if smallest[prime] == prime:
            for multiple in range(prime * prime, maximum + 1, prime):
                if smallest[multiple] == multiple:
                    smallest[multiple] = prime
    kernels = []
    for value in nums:
        kernel = 1
        while value > 1:
            prime = smallest[value]
            parity = 0
            while value % prime == 0:
                value //= prime
                parity ^= 1
            if parity:
                kernel *= prime
        kernels.append(kernel)
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    active = {}
    answer = 0
    stack = [(0, -1, False)]
    while stack:
        node, parent, leaving = stack.pop()
        key = kernels[node]
        if leaving:
            active[key] -= 1
            continue
        answer += active.get(key, 0)
        active[key] = active.get(key, 0) + 1
        stack.append((node, parent, True))
        for child in graph[node]:
            if child != parent:
                stack.append((child, node, False))
    return answer


class Solution:
    def sumOfAncestors(self, n: int, edges: list[list[int]], nums: list[int]) -> int:
        return solve(n, edges, nums)
