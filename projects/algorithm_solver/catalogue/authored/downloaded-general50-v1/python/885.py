"""885. Spiral Matrix III (Medium).

Specification: https://leetcode.com/problems/spiral-matrix-iii/description/
"""


def solve(rows: int, cols: int, rStart: int, cStart: int) -> list[list[int]]:
    result = []
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c = rStart, cStart
    step = 1
    direction = 0
    result.append([r, c])
    while len(result) < rows * cols:
        for _repeat in range(2):
            for _i in range(step):
                r += dirs[direction][0]
                c += dirs[direction][1]
                if 0 <= r < rows and 0 <= c < cols:
                    result.append([r, c])
            direction = (direction + 1) % 4
        step += 1
    return result


class Solution:
    def spiralMatrixIII(self, rows: int, cols: int, rStart: int, cStart: int) -> list[list[int]]:
        return solve(rows, cols, rStart, cStart)
