"""Hack2Hire 686b0a7af56e0403f35f23ee (Unequal Elements) over an INFERRED spec; qualification unknown."""


def solve(elements, k):
    best = {}
    top = [0] * (k + 1)
    for x in elements:
        row = best.get(x)
        if row is None:
            row = [0] * (k + 1)
            best[x] = row
        for j in range(k, -1, -1):
            value = row[j] + 1
            if j > 0 and top[j - 1] + 1 > value:
                value = top[j - 1] + 1
            row[j] = value
            if value > top[j]:
                top[j] = value
    return max(top)


class Solution:
    def maximumLength(self, elements, k):
        return solve(elements, k)
