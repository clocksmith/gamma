"""1007. Minimum Domino Rotations For Equal Row (Medium).

Specification: https://leetcode.com/problems/minimum-domino-rotations-for-equal-row/description/
"""


def _count_for(tops, bottoms, target):
    rotations_top = 0
    rotations_bottom = 0
    for i in range(len(tops)):
        if tops[i] != target and bottoms[i] != target:
            return float('inf')
        if tops[i] != target:
            rotations_top += 1
        if bottoms[i] != target:
            rotations_bottom += 1
    return min(rotations_top, rotations_bottom)


def solve(tops: list[int], bottoms: list[int]) -> int:
    answer = min(_count_for(tops, bottoms, tops[0]), _count_for(tops, bottoms, bottoms[0]))
    return -1 if answer == float('inf') else answer


class Solution:
    def minDominoRotations(self, tops: list[int], bottoms: list[int]) -> int:
        return solve(tops, bottoms)
