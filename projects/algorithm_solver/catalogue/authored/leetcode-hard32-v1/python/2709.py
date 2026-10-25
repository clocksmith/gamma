"""2709. Greatest Common Divisor Traversal."""

from math import isqrt


def solve(nums: list[int]) -> bool:
    """Sieve plus union-find: O(M log log M + n log M*alpha(n)) time, O(M+n) space."""
    size = len(nums)
    if size == 1:
        return True
    if 1 in nums:
        return False
    maximum = max(nums)
    smallest = list(range(maximum + 1))
    for prime in range(2, isqrt(maximum) + 1):
        if smallest[prime] == prime:
            for multiple in range(prime * prime, maximum + 1, prime):
                if smallest[multiple] == multiple:
                    smallest[multiple] = prime
    parent = list(range(size))
    weight = [1] * size

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def unite(first: int, second: int) -> None:
        first, second = find(first), find(second)
        if first == second:
            return
        if weight[first] < weight[second]:
            first, second = second, first
        parent[second] = first
        weight[first] += weight[second]

    owner = {}
    for index, value in enumerate(nums):
        remaining = value
        while remaining > 1:
            prime = smallest[remaining]
            if prime in owner:
                unite(index, owner[prime])
            else:
                owner[prime] = index
            while remaining % prime == 0:
                remaining //= prime
    root = find(0)
    return all(find(index) == root for index in range(1, size))


class Solution:
    def canTraverseAllPairs(self, nums: list[int]) -> bool:
        return solve(nums)
