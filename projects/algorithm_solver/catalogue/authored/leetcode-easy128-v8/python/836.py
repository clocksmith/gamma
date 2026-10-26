"""836. Rectangle Overlap (Easy).

Specification: https://leetcode.com/problems/rectangle-overlap/description/
"""


def solve(rec1: list[int], rec2: list[int]) -> bool:
    """O(1) time and space; shared edges or corners do not count as positive-area overlap."""
    return (max(rec1[0], rec2[0]) < min(rec1[2], rec2[2])
            and max(rec1[1], rec2[1]) < min(rec1[3], rec2[3]))


class Solution:
    def isRectangleOverlap(self, rec1: list[int], rec2: list[int]) -> bool:
        return solve(rec1, rec2)
