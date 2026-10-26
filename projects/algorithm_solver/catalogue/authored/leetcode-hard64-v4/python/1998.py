"""1998. GCD Sort of an Array."""

from math import isqrt


def solve(nums: list[int]) -> bool:
    """Prime-factor connectivity and sorted-position comparison; O(M log log M+n log n+n log M*alpha(M)) time, O(M+n) space. Inputs are preserved."""
    maximum = max(nums)
    smallest = list(range(maximum + 1))
    for prime in range(2, isqrt(maximum) + 1):
        if smallest[prime] == prime:
            for multiple in range(prime * prime, maximum + 1, prime):
                if smallest[multiple] == multiple:
                    smallest[multiple] = prime
    parent = list(range(maximum + 1))
    sizes = [1] * (maximum + 1)

    def find(value):
        while value != parent[value]:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first, second):
        left, right = find(first), find(second)
        if left == right:
            return
        if sizes[left] < sizes[right]:
            left, right = right, left
        parent[right] = left
        sizes[left] += sizes[right]

    for value in nums:
        remaining = value
        while remaining > 1:
            prime = smallest[remaining]
            union(value, prime)
            while remaining % prime == 0:
                remaining //= prime
    return all(find(actual) == find(expected) for actual, expected in zip(nums, sorted(nums)))


class Solution:
    def gcdSort(self, nums: list[int]) -> bool:
        return solve(nums)
