"""Hack2Hire 69a361ab6e73e4abccc9bfd0 (Maximum Value of Valid Expression Path) over an INFERRED spec; qualification unknown."""

def solve(matrix):
    m, n = len(matrix), len(matrix[0])
    value = [[None] * n for _ in range(m)]  # digit cell: best expression ending here; operator cell: best digit predecessor
    best = None
    for r in range(m):
        for c in range(n):
            ch = matrix[r][c]
            if ch.isdigit():
                d, cur = int(ch), int(ch)
                for pr, pc in ((r - 1, c), (r, c - 1)):
                    if pr >= 0 and pc >= 0 and not matrix[pr][pc].isdigit() and value[pr][pc] is not None:
                        candidate = value[pr][pc] + d if matrix[pr][pc] == '+' else value[pr][pc] - d
                        if candidate > cur:
                            cur = candidate
                value[r][c] = cur
                if best is None or cur > best:
                    best = cur
            else:
                carried = None
                for pr, pc in ((r - 1, c), (r, c - 1)):
                    if pr >= 0 and pc >= 0 and matrix[pr][pc].isdigit():
                        if carried is None or value[pr][pc] > carried:
                            carried = value[pr][pc]
                value[r][c] = carried
    return best


class Solution:
    def maxExpressionPathValue(self, matrix):
        return solve(matrix)
