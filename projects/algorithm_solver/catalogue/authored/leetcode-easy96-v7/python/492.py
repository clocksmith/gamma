"""492. Construct the Rectangle (Easy).

Specification: https://leetcode.com/problems/construct-the-rectangle/description/
"""


def solve(area: int) -> list[int]:
    """O(sqrt(area)) time, O(1) auxiliary space; return the closest factor pair, length first."""
    low = 1
    high = area
    while low < high:
        middle = (low + high + 1) // 2
        if middle * middle <= area:
            low = middle
        else:
            high = middle - 1
    width = low
    while area % width:
        width -= 1
    return [area // width, width]


class Solution:
    def constructRectangle(self, area: int) -> list[int]:
        return solve(area)
