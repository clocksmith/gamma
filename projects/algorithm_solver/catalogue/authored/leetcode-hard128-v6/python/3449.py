"""3449. Maximize the Minimum Game Score.

Binary-search the score and greedily count visits supplied by consecutive edge bounces; O(n log(m*min(points))) time and O(1) space. Inputs are preserved.
"""

def solve(points: list[int], m: int) -> int:
    def possible(score):
        moves = carry = 0
        for index, value in enumerate(points):
            required = (score + value - 1) // value - carry
            if required > 0:
                moves += 2 * required - 1
                carry = required - 1
            else:
                if index + 1 < len(points):
                    moves += 1
                carry = 0
            if moves > m:
                return False
        return True

    lower, upper = 0, min(points) * m
    while lower < upper:
        middle = (lower + upper + 1) // 2
        if possible(middle):
            lower = middle
        else:
            upper = middle - 1
    return lower


class Solution:
    def maxScore(self, points: list[int], m: int) -> int:
        return solve(points, m)
