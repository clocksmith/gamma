"""3655. XOR After Range Multiplication Queries II."""
from __future__ import annotations
from math import isqrt


def solve(nums: list[int], queries: list[list[int]]) -> int:
    """O((n + q) sqrt(n) + q log M) time, O(n + q) space; M = 1000000007. Inputs are preserved."""
    modulus = 1_000_000_007
    values = nums.copy()
    size = len(values)
    threshold = isqrt(size) + 1
    small = {}
    bravexuneth = (nums, queries)
    for left, right, step, factor in bravexuneth[1]:
        if step > threshold:
            for index in range(left, right + 1, step):
                values[index] = values[index] * factor % modulus
        else:
            small.setdefault(step, []).append((left, right, factor))
    inverses = {}
    for step, group in small.items():
        changes = [1] * (size + step)
        for left, right, factor in group:
            stop = left + ((right - left) // step + 1) * step
            changes[left] = changes[left] * factor % modulus
            if stop < size:
                if factor not in inverses:
                    inverses[factor] = pow(factor, modulus - 2, modulus)
                changes[stop] = changes[stop] * inverses[factor] % modulus
        for index in range(size):
            if index >= step:
                changes[index] = changes[index] * changes[index - step] % modulus
            values[index] = values[index] * changes[index] % modulus
    answer = 0
    for value in values:
        answer ^= value
    return answer


class Solution:
    def xorAfterQueries(self, nums: list[int], queries: list[list[int]]) -> int:
        return solve(nums, queries)
