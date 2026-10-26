"""3444. Minimum Increments for Target Multiples in an Array.

Subset-LCM coverage dynamic programming with a feasible distinct-element upper bound; O(n*4^m+m*2^m log V) time and O(2^m) space, m<=4. Inputs are preserved.
"""

from math import gcd


def solve(nums: list[int], target: list[int]) -> int:
    size = 1 << len(target)
    upper = sum(value - 1 for value in target)
    cap = max(nums) + upper
    multiples = [1] * size
    for mask in range(1, size):
        bit = mask & -mask
        previous = multiples[mask ^ bit]
        value = target[bit.bit_length() - 1]
        multiples[mask] = cap + 1 if previous > cap else min(cap + 1, previous // gcd(previous, value) * value)
    best = [float('inf')] * size
    best[0] = 0
    for value in nums:
        following = best.copy()
        for covered in range(size):
            if best[covered] > upper:
                continue
            for mask in range(1, size):
                multiple = multiples[mask]
                if multiple > cap:
                    continue
                extra = (-value) % multiple
                combined = covered | mask
                following[combined] = min(following[combined], best[covered] + extra)
        best = following
        if best[-1] == 0:
            return 0
    return best[-1]


class Solution:
    def minimumIncrements(self, nums: list[int], target: list[int]) -> int:
        return solve(nums, target)
