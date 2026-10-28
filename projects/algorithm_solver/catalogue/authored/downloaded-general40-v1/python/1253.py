"""1253. Reconstruct a 2-Row Binary Matrix (Medium).

Specification: https://leetcode.com/problems/reconstruct-a-2-row-binary-matrix/description/
"""


def solve(upper: int, lower: int, colsum: list[int]) -> list[list[int]]:
    top = [0] * len(colsum)
    bottom = [0] * len(colsum)
    for i, value in enumerate(colsum):
        if value == 2:
            if upper == 0 or lower == 0:
                return []
            top[i] = 1
            bottom[i] = 1
            upper -= 1
            lower -= 1
    for i, value in enumerate(colsum):
        if value == 1:
            if upper > 0:
                top[i] = 1
                upper -= 1
            elif lower > 0:
                bottom[i] = 1
                lower -= 1
            else:
                return []
    if upper != 0 or lower != 0:
        return []
    return [top, bottom]


class Solution:
    def reconstructMatrix(self, upper: int, lower: int, colsum: list[int]) -> list[list[int]]:
        return solve(upper, lower, colsum)
