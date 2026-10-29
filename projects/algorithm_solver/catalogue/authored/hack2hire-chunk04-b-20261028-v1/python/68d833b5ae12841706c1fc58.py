"""Hack2Hire 68d833b5ae12841706c1fc58 (Collatz Sequence Steps) over an INFERRED spec; qualification unknown."""


def solve(n):
    steps = 0
    while n != 1:
        if n & 1:
            n = 3 * n + 1
        else:
            n >>= 1
        steps += 1
    return steps


class Solution:
    def collatzSteps(self, n):
        return solve(n)
