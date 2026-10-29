"""Hack2Hire 69bf17cc21f6ab4226963dc2 (ATM Queue) over an INFERRED spec; qualification unknown."""


def solve(amounts, k):
    order = sorted(range(len(amounts)), key=lambda i: ((amounts[i] + k - 1) // k, i))
    return [i + 1 for i in order]


class Solution:
    def atmOrder(self, amounts, k):
        return solve(amounts, k)
