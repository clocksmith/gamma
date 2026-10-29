"""Hack2Hire 67a574f4b571d6ff0a4bd23a (Maximum Stability) over an INFERRED spec; qualification unknown."""


def solve(availability, reliability):
    order = sorted(range(len(availability)), key=lambda i: -availability[i])
    best = running = 0
    for i in order:
        running += reliability[i]
        if availability[i] * running > best:
            best = availability[i] * running
    return best


class Solution:
    def maxStability(self, availability, reliability):
        return solve(availability, reliability)
