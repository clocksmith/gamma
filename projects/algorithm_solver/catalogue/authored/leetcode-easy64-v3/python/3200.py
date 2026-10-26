"""3200. Maximum Height of a Triangle (Easy).

Specification: https://leetcode.com/problems/maximum-height-of-a-triangle/description/
"""


def solve(red: int, blue: int) -> int:
    """O(sqrt(red + blue)) time, O(1) space; try both starting colors."""
    def height(first: int, second: int) -> int:
        row = 1
        while True:
            if row % 2 == 1:
                if first < row:
                    break
                first -= row
            else:
                if second < row:
                    break
                second -= row
            row += 1
        return row - 1

    return max(height(red, blue), height(blue, red))


class Solution:
    def maxHeightOfTriangle(self, red: int, blue: int) -> int:
        return solve(red, blue)
