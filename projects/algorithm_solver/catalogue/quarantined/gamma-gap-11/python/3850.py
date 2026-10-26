"""3850. Count Sequences to K."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n S) time and O(S) space for S reachable exponent states; exact rational equality via prime exponents, counts <= 3^19."""
    needed = []
    remaining = k
    for prime in (2, 3, 5):
        exponent = 0
        while remaining % prime == 0:
            remaining //= prime
            exponent += 1
        needed.append(exponent)
    if remaining != 1 or needed[0] > 2 * len(nums) or needed[1] > len(nums) or needed[2] > len(nums):
        return 0
    base = 4 * len(nums) + 1
    weights = (0, 0, base * base, base, 2 * base * base, 1, base * base + base)
    states = {0: 1}
    for value in nums:
        delta = weights[value]
        following = {}
        for key, count in states.items():
            for next_key in (key, key + delta, key - delta):
                following[next_key] = following.get(next_key, 0) + count
        states = following
    target = needed[0] * base * base + needed[1] * base + needed[2]
    return states.get(target, 0)


class Solution:
    def countSequences(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
