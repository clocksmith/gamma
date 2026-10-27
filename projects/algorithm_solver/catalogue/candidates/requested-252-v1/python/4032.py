"""4032. Longest Subarray With at Most K Distinct Prime Factors.

Specification: https://leetcode.com/problems/longest-subarray-with-at-most-k-distinct-prime-factors/description/
"""

from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(V log log V+n log V) time and O(V+n log V) space; cached distinct factors and a sliding window. Inputs are preserved."""
    maximum = max(nums)
    smallest = [0] * (maximum + 1)
    for prime in range(2, maximum + 1):
        if smallest[prime]:
            continue
        smallest[prime] = prime
        for multiple in range(prime * prime, maximum + 1, prime):
            if smallest[multiple] == 0:
                smallest[multiple] = prime
    cache = {}
    def factors(value):
        if value not in cache:
            result = []
            remaining = value
            while remaining > 1:
                prime = smallest[remaining]
                result.append(prime)
                while remaining % prime == 0:
                    remaining //= prime
            cache[value] = result
        return cache[value]
    counts = {}
    left = answer = 0
    for right, value in enumerate(nums):
        for prime in factors(value):
            counts[prime] = counts.get(prime, 0) + 1
        while len(counts) > k:
            for prime in factors(nums[left]):
                counts[prime] -= 1
                if counts[prime] == 0:
                    del counts[prime]
            left += 1
        answer = max(answer, right - left + 1)
    return answer
