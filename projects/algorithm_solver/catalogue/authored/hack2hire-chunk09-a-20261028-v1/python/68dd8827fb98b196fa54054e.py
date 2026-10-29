"""Hack2Hire 68dd8827fb98b196fa54054e (Build Smallest Number, variant 2 of 2) over an INFERRED spec; qualification unknown."""

from functools import cmp_to_key


def order(a, b):
    ab, ba = a + b, b + a
    return -1 if ab < ba else (1 if ab > ba else 0)


def solve(nums):
    parts = sorted((str(x) for x in nums), key=cmp_to_key(order))
    if parts[0] != '0':
        return ''.join(parts)
    if all(p == '0' for p in parts):
        return '0'
    best = None
    tried = set()
    for i, p in enumerate(parts):
        if p == '0' or p in tried:
            continue
        tried.add(p)
        candidate = p + ''.join(parts[:i]) + ''.join(parts[i + 1:])
        if best is None or candidate < best:
            best = candidate
    return best


class Solution:
    def smallestConcatenation(self, nums):
        return solve(nums)
