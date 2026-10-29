"""Original LeetCode 679 candidate; qualification unknown."""

from fractions import Fraction

def solve(cards):
    def search(values):
        if len(values) == 1: return values[0] == 24
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                a, b = values[i], values[j]
                rest = [v for k, v in enumerate(values) if k not in (i,j)]
                options = {a+b, a-b, b-a, a*b}
                if b: options.add(a/b)
                if a: options.add(b/a)
                if any(search(rest + [value]) for value in options): return True
        return False
    return search([Fraction(v) for v in cards])


class Solution:
    def judgePoint24(self, cards):
        return solve(cards)
