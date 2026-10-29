"""Hack2Hire 69efd6f096981f58ae1f6dcf (Check Prefix Permutation) over an INFERRED spec; qualification unknown."""


def solve(p):
    n = len(p)
    position = [0] * (n + 1)
    for i, value in enumerate(p):
        position[value] = i
    low = high = position[1]
    result = []
    for k in range(1, n + 1):
        x = position[k]
        if x < low:
            low = x
        if x > high:
            high = x
        result.append(high - low + 1 == k)
    return result


class Solution:
    def prefixPermutations(self, p):
        return solve(p)
