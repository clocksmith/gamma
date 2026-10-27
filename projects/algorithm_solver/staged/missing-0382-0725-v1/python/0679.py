"""679. 24 Game. Enumerate binary expression trees with exact rational arithmetic."""

from fractions import Fraction

def solve(cards: list[int]) -> bool:
    def search(values):
        if len(values) == 1:
            return values[0] == 24
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                a, b = values[i], values[j]
                rest = [value for k, value in enumerate(values) if k != i and k != j]
                candidates = {a + b, a - b, b - a, a * b}
                if b:
                    candidates.add(a / b)
                if a:
                    candidates.add(b / a)
                for candidate in candidates:
                    if search(rest + [candidate]):
                        return True
        return False
    return search([Fraction(value) for value in cards])


class Solution:
    def judgePoint24(self, cards: list[int]) -> bool:
        return solve(cards)
