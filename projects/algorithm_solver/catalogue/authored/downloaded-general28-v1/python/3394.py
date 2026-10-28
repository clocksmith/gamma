"""3394. Check if Grid can be Cut into Sections (Medium).

Specification: https://leetcode.com/problems/check-if-grid-can-be-cut-into-sections/description/
"""


def solve(n: int, rectangles: list[list[int]]) -> bool:
    def groups(intervals):
        intervals = sorted(intervals)
        count = 0
        cur_end = float('-inf')
        for s, e in intervals:
            if s >= cur_end:
                count += 1
                cur_end = e
            elif e > cur_end:
                cur_end = e
        return count

    xs = [[r[0], r[2]] for r in rectangles]
    ys = [[r[1], r[3]] for r in rectangles]
    return groups(xs) >= 3 or groups(ys) >= 3


class Solution:
    def checkIfGridCanBeCutIntoSections(self, n: int, rectangles: list[list[int]]) -> bool:
        return solve(n, rectangles)
