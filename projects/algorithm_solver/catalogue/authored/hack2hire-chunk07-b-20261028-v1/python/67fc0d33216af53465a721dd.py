"""Hack2Hire 67fc0d33216af53465a721dd (Minimum Swaps for Ball Grouping) over an INFERRED spec; qualification unknown."""

def solve(balls):
    shifted = []
    for i, c in enumerate(balls):
        if c == 'R':
            shifted.append(i - len(shifted))
    if len(shifted) <= 1:
        return 0
    median = shifted[len(shifted) // 2]
    return sum(abs(s - median) for s in shifted)


class Solution:
    def minSwaps(self, balls):
        return solve(balls)
