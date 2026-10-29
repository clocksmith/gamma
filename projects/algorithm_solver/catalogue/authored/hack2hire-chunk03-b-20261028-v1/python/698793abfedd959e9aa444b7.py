"""Hack2Hire 698793abfedd959e9aa444b7 (Minimum Operations to Reduce to Zero) over an INFERRED spec; qualification unknown."""


def solve(n):
    steps = 0
    while n > 0:
        if n % 2 == 0: n //= 2
        elif n == 1 or n == 3 or n % 4 == 1: n -= 1
        else: n += 1
        steps += 1
    return steps


class Solution:
    def minOperations(self, n):
        return solve(n)
