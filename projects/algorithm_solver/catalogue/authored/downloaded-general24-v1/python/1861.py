"""1861. Rotating the Box (Medium).

Specification: https://leetcode.com/problems/rotating-the-box/description/
"""


def _settle_row(row):
    result = row[:]
    write = len(result) - 1
    for i in range(len(result) - 1, -1, -1):
        if result[i] == '*':
            write = i - 1
        elif result[i] == '#':
            result[i] = '.'
            result[write] = '#'
            write -= 1
    return result


def solve(box: list[list[str]]) -> list[list[str]]:
    settled = [_settle_row(row) for row in box]
    rows, cols = len(settled), len(settled[0])
    result = []
    for c in range(cols):
        row = []
        for r in range(rows - 1, -1, -1):
            row.append(settled[r][c])
        result.append(row)
    return result


class Solution:
    def rotateTheBox(self, box: list[list[str]]) -> list[list[str]]:
        return solve(box)
